"""Public Parent account registration through Firebase Authentication."""

from __future__ import annotations

import logging

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008
import re
import time
from collections import OrderedDict, deque
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioner,
    IdentityAccountProvisioningUnavailable,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/auth/v1", tags=["authentication"])

_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_REGISTRATION_LIMIT = 5
_REGISTRATION_WINDOW_SECONDS = 15 * 60
_MAX_TRACKED_CLIENTS = 128
_LOGGER = logging.getLogger(__name__)


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


class CurrentAccountResponse(BaseModel):
    role: Literal["parent", "teacher", "school_manager", "platform_admin"]
    state: Literal["active"] = "active"
    role_revision: int = Field(ge=1)


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
    if request.app.state.be1_runtime.settings.env not in {"local", "test"}:
        raise HTTPException(
            status_code=404,
            detail={"code": "REGISTRATION_UNAVAILABLE", "message": "Registration is unavailable"},
        )
    client_key = request.client.host if request.client else "unknown-client"
    request_id = getattr(request.state, "be1_request_id", "unknown")
    if not request.app.state.registration_rate_limiter.allow(client_key):
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMITED",
                "message": "Too many registration attempts; try again later",
            },
            headers={"Retry-After": str(_REGISTRATION_WINDOW_SECONDS)},
        )

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
    except IdentityAccountProvisioningUnavailable as exc:
        _LOGGER.error(
            "parent_registration_failed stage=firebase_create request_id=%s "
            "error_type=%s error_module=%s",
            request_id,
            type(exc).__name__,
            type(exc).__module__,
        )
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
        # A connection failure during COMMIT has an unknown outcome: PostgreSQL may
        # have committed before the acknowledgement was lost. Deleting Firebase here
        # could leave a committed BE1 row pointing to a deleted identity. Keep the
        # Firebase identity so the next authenticated sign-in can reconcile via
        # /registrations/complete once the database is reachable again.
        _log_registration_database_failure(
            "commit_outcome_unknown", exc, request_id=request_id, compensation_ok=None
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ACCOUNT_SETUP_UNAVAILABLE",
                "message": "Account setup is temporarily unavailable",
            },
        ) from None

    return RegistrationCreated()


@router.post(
    "/registrations/complete",
    response_model=CurrentAccountResponse,
    summary="Synchronize the authenticated Parent identity with BE1",
    description=(
        "Uses the verified Firebase issuer and subject to idempotently ensure a server-assigned "
        "Parent identity row. The request accepts no role, UID, or account scope from the client."
    ),
    responses={
        401: {"description": "A valid Firebase identity token is required"},
        403: {"description": "Account setup is unavailable"},
        409: {"description": "Account setup is unavailable"},
        503: {"description": "Identity or database service is unavailable"},
    },
)
def complete_parent_registration(
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> CurrentAccountResponse:
    settings = request.app.state.be1_runtime.settings
    if settings.env not in {"local", "test"}:
        raise HTTPException(
            status_code=404,
            detail={"code": "REGISTRATION_UNAVAILABLE", "message": "Registration is unavailable"},
        )
    expected_issuer = f"https://securetoken.google.com/{settings.firebase_project_id}"
    request_id = getattr(request.state, "be1_request_id", "unknown")
    if not settings.firebase_project_id or principal.issuer != expected_issuer:
        raise _account_setup_unavailable(status_code=403)

    current = db.get(AdultIdentityModel, principal.subject)
    if current is not None:
        if (
            current.issuer == principal.issuer
            and current.state == "active"
            and current.account_role == "parent"
        ):
            return CurrentAccountResponse(
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
    try:
        db.commit()
    except IntegrityError as exc:
        _rollback_registration(db, request_id=request_id, stage="completion_conflict")
        # A concurrent completion may have committed the same Parent row. Re-read and
        # treat only that exact issuer/subject/role as an idempotent success.
        current = db.get(AdultIdentityModel, principal.subject)
        if (
            current is not None
            and current.issuer == principal.issuer
            and current.state == "active"
            and current.account_role == "parent"
        ):
            return CurrentAccountResponse(
                role="parent", state="active", role_revision=current.role_revision
            )
        _log_registration_database_failure(
            "completion_conflict", exc, request_id=request_id, compensation_ok=None
        )
        raise _account_setup_unavailable(status_code=409) from None
    except SQLAlchemyError as exc:
        _rollback_registration(db, request_id=request_id, stage="completion_commit_failed")
        _log_registration_database_failure(
            "completion_commit_failed", exc, request_id=request_id, compensation_ok=None
        )
        raise _account_setup_unavailable(status_code=503) from None

    return CurrentAccountResponse(role="parent", state="active", role_revision=1)


@router.get("/me", response_model=CurrentAccountResponse, summary="Resolve current account role")
def current_account(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> CurrentAccountResponse:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role is None
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ACCOUNT_SETUP_UNAVAILABLE",
                "message": "Account setup is unavailable",
            },
        )
    return CurrentAccountResponse(
        role=identity.account_role,
        state="active",
        role_revision=identity.role_revision,
    )


__all__ = ["RegistrationRateLimiter", "router"]


def _account_setup_unavailable(*, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": "ACCOUNT_SETUP_UNAVAILABLE",
            "message": "Account setup is unavailable",
        },
    )


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
    sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    if not isinstance(sqlstate, str) or len(sqlstate) != 5 or not sqlstate.isalnum():
        sqlstate = None
    _LOGGER.error(
        "parent_registration_failed stage=%s request_id=%s error_type=%s error_module=%s "
        "driver_error_type=%s driver_error_module=%s sqlstate=%s compensation_ok=%s",
        stage,
        request_id,
        type(error).__name__,
        type(error).__module__,
        type(original).__name__ if original is not None else "unknown",
        type(original).__module__ if original is not None else "unknown",
        sqlstate,
        compensation_ok,
    )


def _rollback_registration(db: Session, *, request_id: str, stage: str) -> None:
    try:
        db.rollback()
    except SQLAlchemyError as exc:
        _LOGGER.error(
            "parent_registration_rollback_failed stage=%s request_id=%s "
            "error_type=%s error_module=%s",
            stage,
            request_id,
            type(exc).__name__,
            type(exc).__module__,
        )
