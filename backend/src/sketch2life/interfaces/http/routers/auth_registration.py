"""Public Parent account registration through Firebase Authentication."""

from __future__ import annotations

import logging
import re
import time
from collections import OrderedDict, deque
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioner,
    IdentityAccountProvisioningUnavailable,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.account_scope import GrantedScope, load_granted_scope
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/auth/v1", tags=["authentication"])

_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_REGISTRATION_LIMIT = 5
_REGISTRATION_WINDOW_SECONDS = 15 * 60
_MAX_TRACKED_CLIENTS = 128
_LOGGER = logging.getLogger(__name__)
# TD-25 (T0.2): SRS l.866 lists ACCOUNT_SETUP_UNAVAILABLE under 409, but the Parent client
# (apps/ui-mobile ParentAuth.ts, status 403 branch) shows its "no role yet" message only for
# 403. Keep 403 until that client also accepts 409, then change this one constant.
ME_SETUP_REFUSAL_STATUS = 403


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("invalid email")
        return normalized


class RegistrationCreated(BaseModel):
    status: Literal["IDENTITY_CREATED"] = "IDENTITY_CREATED"
    role: Literal["parent"] = "parent"
    email_verified: Literal[False] = False


class RegistrationCompletionReceipt(BaseModel):
    role: Literal["parent"] = "parent"
    state: Literal["active"] = "active"
    role_revision: int = Field(ge=1)


class ScopeOrganizationResponse(BaseModel):
    organization_id: str
    display_name: str
    roles: list[Literal["school_admin", "teacher", "guide", "observer"]] = Field(
        description=(
            "Assignment roles the account holds in this organization, organization-wide or "
            "class-bound, sorted. `guide` and `observer` are assignment roles, not product roles."
        )
    )


class ScopeClassResponse(BaseModel):
    organization_id: str
    class_id: str
    display_name: str
    role: Literal["school_admin", "teacher", "guide", "observer"]
    state: str = Field(description="Stored classroom state, passed through unchanged.")


class ScopeAccountsResponse(BaseModel):
    account_id: str = Field(description="The caller's own internal account id (never the UID).")
    managed: Literal["NONE", "PLATFORM"] = Field(
        description=(
            "Provisional. `PLATFORM` for a Platform Admin, otherwise `NONE`. "
            "Clients must treat an unknown value as `NONE`."
        )
    )


class GrantedScopeResponse(BaseModel):
    organizations: list[ScopeOrganizationResponse]
    classes: list[ScopeClassResponse]
    accounts: ScopeAccountsResponse
    permissions: list[str] = Field(
        default_factory=list,
        description="Always empty until the Content Admin permission store exists (TD-11).",
    )
    truncated: bool = Field(
        description=(
            "True when the organization (100) or class (500) cap cut the lists; use the paged "
            "per-organization routes to see the rest."
        )
    )


class CurrentAccountResponse(BaseModel):
    role: Literal["parent", "teacher", "school_manager", "platform_admin"]
    state: Literal["active"] = "active"
    role_revision: int = Field(ge=1)
    scope: GrantedScopeResponse


def _scope_response(scope: GrantedScope) -> GrantedScopeResponse:
    return GrantedScopeResponse.model_validate(
        {
            "organizations": [
                {
                    "organization_id": item.organization_id,
                    "display_name": item.display_name,
                    "roles": list(item.roles),
                }
                for item in scope.organizations
            ],
            "classes": [
                {
                    "organization_id": item.organization_id,
                    "class_id": item.class_id,
                    "display_name": item.display_name,
                    "role": item.role,
                    "state": item.state,
                }
                for item in scope.classes
            ],
            "accounts": {"account_id": scope.account_id, "managed": scope.managed},
            "permissions": [],
            "truncated": scope.truncated,
        }
    )


class RegistrationRateLimiter:
    """Small bounded process-local sliding-window limiter for local development only."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()

    def allow(self, client_key: str, *, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - _REGISTRATION_WINDOW_SECONDS
        with self._lock:
            requests = self._requests.get(client_key)
            if requests is None:
                if len(self._requests) >= _MAX_TRACKED_CLIENTS:
                    self._requests.popitem(last=False)
                requests = deque()
                self._requests[client_key] = requests
            else:
                self._requests.move_to_end(client_key)
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= _REGISTRATION_LIMIT:
                return False
            requests.append(current)
            return True


@router.post(
    "/registrations",
    response_model=RegistrationCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Parent account",
    description=(
        "Creates an unverified Firebase email/password identity and assigns the Parent role "
        "server-side. It does not create a Parent or child profile."
    ),
    responses={
        409: {"description": "Account setup is unavailable"},
        422: {"description": "The registration request is invalid"},
        429: {"description": "The local registration rate limit was reached"},
        503: {"description": "Firebase Authentication is unavailable"},
    },
)
def register_account(
    payload: RegistrationRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RegistrationCreated:
    client_key = request.client.host if request.client else "unknown-client"
    if not request.app.state.registration_rate_limiter.allow(client_key):
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMITED",
                "message": "Too many registration attempts; try again later",
            },
            headers={"Retry-After": str(_REGISTRATION_WINDOW_SECONDS)},
        )

    request_id = getattr(request.state, "be1_request_id", "unknown")
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    try:
        provisioned = provisioner.create_password_account(
            email=payload.email,
            password=payload.password.get_secret_value(),
        )
    except IdentityAccountConflict:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ACCOUNT_SETUP_UNAVAILABLE",
                "message": "Account setup is unavailable",
            },
        ) from None
    except IdentityAccountProvisioningUnavailable:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "IDENTITY_PROVIDER_UNAVAILABLE",
                "message": "Identity service is temporarily unavailable",
            },
        ) from None

    identity = AdultIdentityModel(
        account_id=str(uuid4()),
        subject=provisioned.subject,
        issuer=provisioned.issuer,
        state="active",
        account_role="parent",
        role_revision=1,
    )
    db.add(identity)
    try:
        db.commit()
    except IntegrityError as exc:
        _rollback_registration(db, request_id=request_id, stage="integrity_conflict")
        compensation_ok = _compensate_firebase_identity(
            provisioner, provisioned.subject, request_id=request_id
        )
        _log_registration_database_failure(
            "integrity_conflict", exc, request_id=request_id, compensation_ok=compensation_ok
        )
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ACCOUNT_SETUP_UNAVAILABLE",
                "message": "Account setup is unavailable",
            },
        ) from None
    except SQLAlchemyError as exc:
        _rollback_registration(db, request_id=request_id, stage="commit_failed")
        # A connection failure while committing can leave the database outcome unknown. Keep the
        # Firebase identity so the verified completion route can reconcile it on retry.
        _log_registration_database_failure(
            "commit_failed", exc, request_id=request_id, compensation_ok=None
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ACCOUNT_SETUP_UNAVAILABLE",
                "message": "Account setup is temporarily unavailable",
            },
        ) from None

    return RegistrationCreated()


def _complete_registration_guard(request: Request) -> None:
    """Cheap gate that runs before the token verifier: setting first, then the shared limiter."""
    settings = request.app.state.be1_runtime.settings
    if not settings.parent_self_registration_enabled:
        raise _account_setup_unavailable(status_code=403)
    client_key = request.client.host if request.client else "unknown-client"
    if not request.app.state.registration_rate_limiter.allow(client_key):
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMITED",
                "message": "Too many registration attempts; try again later",
            },
            headers={"Retry-After": str(_REGISTRATION_WINDOW_SECONDS)},
        )


@router.post(
    "/registrations/complete",
    response_model=RegistrationCompletionReceipt,
    summary="Complete the authenticated Parent identity",
    description=(
        "Uses the verified Firebase issuer and subject to ensure a server-assigned "
        "Parent identity. The request accepts no role, UID, or account scope from the client."
    ),
    responses={
        401: {"description": "A valid Firebase identity token is required"},
        403: {"description": "Account setup is unavailable"},
        409: {"description": "Account setup is unavailable"},
        429: {"description": "The registration rate limit was reached"},
        503: {"description": "Identity or database service is unavailable"},
    },
)
def complete_parent_registration(
    request: Request,
    _guard: None = Depends(_complete_registration_guard),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> RegistrationCompletionReceipt:
    settings = request.app.state.be1_runtime.settings
    if not principal.email_verified:
        raise _account_setup_unavailable(status_code=403)
    expected_issuer = f"https://securetoken.google.com/{settings.firebase_project_id}"
    if not settings.firebase_project_id or principal.issuer != expected_issuer:
        raise _account_setup_unavailable(status_code=403)

    request_id = getattr(request.state, "be1_request_id", "unknown")
    stage = "completion_lookup"
    try:
        current = db.get(AdultIdentityModel, principal.subject)
        if current is not None:
            if (
                current.issuer == principal.issuer
                and current.state == "active"
                and current.account_role == "parent"
            ):
                return RegistrationCompletionReceipt(
                    role="parent", state="active", role_revision=current.role_revision
                )
            raise _account_setup_unavailable(status_code=409)

        db.add(
            AdultIdentityModel(
                account_id=str(uuid4()),
                subject=principal.subject,
                issuer=principal.issuer,
                state="active",
                account_role="parent",
                role_revision=1,
            )
        )
        stage = "completion_commit"
        db.commit()
    except IntegrityError as exc:
        try:
            _rollback_registration(db, request_id=request_id, stage="completion_conflict")
        except Exception:
            raise _account_setup_unavailable(status_code=503) from None

        try:
            current = db.get(AdultIdentityModel, principal.subject)
        except SQLAlchemyError as reread_error:
            _log_registration_database_failure(
                "completion_conflict_reread_failed",
                reread_error,
                request_id=request_id,
                compensation_ok=None,
            )
            raise _account_setup_unavailable(status_code=503) from None
        if (
            current is not None
            and current.issuer == principal.issuer
            and current.state == "active"
            and current.account_role == "parent"
        ):
            return RegistrationCompletionReceipt(
                role="parent", state="active", role_revision=current.role_revision
            )

        _log_registration_database_failure(
            "completion_conflict", exc, request_id=request_id, compensation_ok=None
        )
        raise _account_setup_unavailable(status_code=409) from None
    except SQLAlchemyError as exc:
        failure_stage = f"{stage}_failed"
        try:
            _rollback_registration(db, request_id=request_id, stage=failure_stage)
        except Exception:
            raise _account_setup_unavailable(status_code=503) from None
        _log_registration_database_failure(
            failure_stage, exc, request_id=request_id, compensation_ok=None
        )
        raise _account_setup_unavailable(status_code=503) from None

    return RegistrationCompletionReceipt(role="parent", state="active", role_revision=1)


@router.get(
    "/me",
    response_model=CurrentAccountResponse,
    summary="Resolve current account role and granted scope",
    description=(
        "Resolves the verified identity to its role and the scope it was granted: organizations "
        "and classes with an active assignment, plus the caller's own account reference. "
        "The scope is informational for client routing; every route still re-authorises on the "
        "server. Only active assignments in active organizations are listed; an organization-wide "
        "`school_admin` assignment appears in `organizations[].roles` and never enumerates "
        "classes. Lists are capped (100 organizations, 500 classes); `truncated` is true when a "
        "cap cut them, then use the paged per-organization routes. The refusal is one identical "
        "body for a missing, disabled, role-less or issuer-mismatched identity and never "
        "reveals a UID. The response is `Cache-Control: private, no-store`."
    ),
    responses={
        401: {"description": "No valid bearer token"},
        ME_SETUP_REFUSAL_STATUS: {"description": "Account setup is unavailable"},
        503: {"description": "Identity or database service is unavailable"},
    },
)
def current_account(
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> CurrentAccountResponse:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is not None
        and identity.issuer == principal.issuer
        and identity.email_verification_required
        and identity.state != "disabled"
    ):
        if not principal.email_verified:
            raise HTTPException(
                403,
                detail={
                    "code": "EMAIL_VERIFICATION_REQUIRED",
                    "message": "Verify your email before signing in",
                },
            )
        identity.email_verification_required = False
        identity.state = "active"
        identity.role_revision += 1
        for assignment in db.scalars(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.subject == identity.subject,
                OrganizationAssignmentModel.pending_activation.is_(True),
            )
        ):
            assignment.pending_activation = False
            assignment.active = True
        db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id="platform",
                actor_ref=principal.subject,
                action="ACCOUNT_EMAIL_VERIFIED",
                resource_type="adult_account",
                resource_id=identity.account_id,
                decision="allowed",
            )
        )
        db.commit()
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role is None
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(
            status_code=ME_SETUP_REFUSAL_STATUS,
            detail={
                "code": "ACCOUNT_SETUP_UNAVAILABLE",
                "message": "Account setup is unavailable",
            },
            headers={"Cache-Control": "private, no-store"},
        )
    scope = load_granted_scope(db, identity)
    response.headers["Cache-Control"] = "private, no-store"
    return CurrentAccountResponse(
        role=identity.account_role,
        state="active",
        role_revision=identity.role_revision,
        scope=_scope_response(scope),
    )


def _account_setup_unavailable(*, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": "ACCOUNT_SETUP_UNAVAILABLE",
            "message": "Account setup is unavailable",
        },
    )


def _rollback_registration(db: Session, *, request_id: str, stage: str) -> None:
    try:
        db.rollback()
    except Exception as exc:
        _LOGGER.error(
            "parent_registration_rollback_failed stage=%s request_id=%s "
            "error_type=%s error_module=%s",
            stage,
            request_id,
            type(exc).__name__,
            type(exc).__module__,
        )
        raise


def _compensate_firebase_identity(
    provisioner: IdentityAccountProvisioner, subject: str, *, request_id: str
) -> bool:
    try:
        provisioner.delete_account(subject)
        return True
    except IdentityAccountProvisioningUnavailable as exc:
        _LOGGER.error(
            "parent_registration_compensation_failed request_id=%s "
            "error_type=%s error_module=%s",
            request_id,
            type(exc).__name__,
            type(exc).__module__,
        )
        return False


def _log_registration_database_failure(
    stage: str,
    error: SQLAlchemyError,
    *,
    request_id: str,
    compensation_ok: bool | None,
) -> None:
    original = getattr(error, "orig", None)
    sqlstate = None
    if original is not None:
        for attribute in ("sqlstate", "pgcode"):
            try:
                candidate = getattr(original, attribute, None)
            except Exception:
                continue
            if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z0-9]{5}", candidate):
                sqlstate = candidate
                break

    fields = [
        "parent_registration_database_failure",
        "stage=%s",
        "request_id=%s",
        "error_type=%s",
        "error_module=%s",
        "driver_error_type=%s",
        "driver_error_module=%s",
        "compensation_ok=%s",
    ]
    values: list[object] = [
        stage,
        request_id,
        type(error).__name__,
        type(error).__module__,
        type(original).__name__ if original is not None else "unknown",
        type(original).__module__ if original is not None else "unknown",
        compensation_ok,
    ]
    if sqlstate is not None:
        fields.append("sqlstate=%s")
        values.append(sqlstate)
    _LOGGER.error(" ".join(fields), *values)


__all__ = ["RegistrationRateLimiter", "router"]
