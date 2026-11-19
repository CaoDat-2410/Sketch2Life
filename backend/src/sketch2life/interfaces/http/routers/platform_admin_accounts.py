"""Platform Admin account provisioning and server-managed role changes."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProfile,
    IdentityAccountProvisioner,
    IdentityAccountProvisioningUnavailable,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.api_conventions import limit_query, parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/platform-admin/v1", tags=["Platform Admin accounts"])

AccountRole = Literal["parent", "teacher", "school_manager", "platform_admin"]
AccountState = Literal["active", "disabled"]
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=1, max_length=200)
    role: AccountRole
    organization_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("invalid email")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display name is required")
        return normalized

    @model_validator(mode="after")
    def validate_organization_scope(self) -> AccountCreateRequest:
        if (self.role == "school_manager") != (self.organization_id is not None):
            raise ValueError("organization_id is required only for school_manager accounts")
        return self


class AccountUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: AccountRole | None = None
    state: AccountState | None = None
    organization_id: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_update_scope(self) -> AccountUpdateRequest:
        if self.role is None and self.state is None:
            raise ValueError("at least one of role or state is required")
        if self.organization_id is not None and self.role != "school_manager":
            raise ValueError("organization_id can be changed only with school_manager role")
        if self.role == "school_manager" and self.organization_id is None:
            raise ValueError("organization_id is required for school_manager role")
        return self


class AccountResponse(BaseModel):
    account_id: str
    email: str | None
    display_name: str | None
    role: AccountRole | None
    state: AccountState
    revision: int = Field(ge=1)


class AccountPageResponse(BaseModel):
    items: list[AccountResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    # FEAT-066 C5 (SRS §21.1 line 1640): opaque cursor of the next page; null at the end.
    next_cursor: str | None = None


# FEAT-066 C5 (SRS §21.4 line 1697): the key is read by `parse_idempotency_key`; the optional
# declaration only publishes the header in the runtime OpenAPI (review C5-R2-06).
_IDEMPOTENCY_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": (
            "The request is invalid (`INVALID_REQUEST`, also for a missing or malformed "
            "`Idempotency-Key`), or the Idempotency-Key was reused with a different payload "
            "(`INVALID_IDEMPOTENCY_KEY`)."
        )
    }
}
_CREATE_SCOPE = "POST /accounts"


def _invalid_field(field: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            "code": "INVALID_REQUEST",
            "field_errors": [{"field": field, "code": "INVALID_FORMAT"}],
        },
    )


def _encode_cursor(created_at: datetime, account_id: str) -> str:
    payload = json.dumps(
        {"account_id": account_id, "created_at": created_at.isoformat(), "v": 1},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        if not cursor or len(cursor) > 2048:
            raise ValueError
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != {"account_id", "created_at", "v"}:
            raise ValueError
        if type(decoded["v"]) is not int or decoded["v"] != 1:
            raise ValueError
        if not isinstance(decoded["account_id"], str) or not isinstance(decoded["created_at"], str):
            raise ValueError
        created_at = datetime.fromisoformat(decoded["created_at"])
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError
        if not 1 <= len(decoded["account_id"]) <= 36:
            raise ValueError
        return created_at, decoded["account_id"]
    except (binascii.Error, json.JSONDecodeError, UnicodeEncodeError, ValueError):
        raise _invalid_field("cursor") from None


def _after_cursor(row: AdultIdentityModel, position: tuple[datetime, str]) -> bool:
    created_at, account_id = position
    return row.created_at < created_at or (
        row.created_at == created_at and row.account_id > account_id
    )


def _fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _stored_values(response: AccountResponse) -> dict[str, Any]:
    """Receipt body without email or display name (plan Draft 2 §3 step 1)."""
    return {
        "account_id": response.account_id,
        "role": response.role,
        "state": response.state,
        "revision": response.revision,
    }


def _replay(
    db: Session, *, principal_ref: str, scope: str, key: str, fingerprint: str
) -> dict[str, Any] | None:
    receipt = db.get(Be1CommandReceiptModel, (principal_ref, scope, key))
    if receipt is None:
        return None
    if receipt.request_fingerprint != fingerprint:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_IDEMPOTENCY_KEY",
                "message": "Idempotency-Key was already used for another request",
            },
        )
    return dict(receipt.response_json)


def _replayed_response(
    stored: dict[str, Any], *, email: str | None, display_name: str | None
) -> AccountResponse:
    return AccountResponse(
        account_id=stored["account_id"],
        email=email,
        display_name=display_name,
        role=stored["role"],
        state=stored["state"],
        revision=stored["revision"],
    )


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "FORBIDDEN", "message": "Platform Admin authority is required"},
    )


def _require_platform_admin(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "platform_admin"
        or identity.issuer != principal.issuer
    ):
        raise _forbidden()
    return identity


def _record_account_event(
    db: Session,
    *,
    actor: str,
    account_id: str,
    action: str,
    organization_id: str | None = None,
) -> None:
    db.add(
        CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id=organization_id or "platform",
            actor_ref=actor,
            action=action,
            resource_type="adult_account",
            resource_id=account_id,
            decision="allowed",
        )
    )


def _get_organization(db: Session, organization_id: str) -> OrganizationModel:
    organization = db.get(OrganizationModel, organization_id)
    if organization is None or organization.state != "active":
        raise HTTPException(
            status_code=422,
            detail={"code": "ORGANIZATION_UNAVAILABLE", "message": "Organization is unavailable"},
        )
    return organization


def _ensure_school_manager_assignment(
    db: Session, *, organization_id: str, subject: str
) -> None:
    assignment = db.scalar(
        select(OrganizationAssignmentModel).where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.subject == subject,
            OrganizationAssignmentModel.class_id.is_(None),
            OrganizationAssignmentModel.role == "school_admin",
        )
    )
    if assignment is None:
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=subject,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )
    else:
        assignment.active = True


def _revoke_assignments(
    db: Session,
    *,
    subject: str,
    except_school_manager_org: str | None = None,
    preserve_teacher_assignments: bool = False,
) -> None:
    rows = db.scalars(
        select(OrganizationAssignmentModel).where(
            OrganizationAssignmentModel.subject == subject,
            OrganizationAssignmentModel.active.is_(True),
        )
    )
    for assignment in rows:
        if (
            assignment.role == "school_admin"
            and assignment.organization_id == except_school_manager_org
            and assignment.class_id is None
        ):
            continue
        if preserve_teacher_assignments and assignment.role in {"teacher", "guide", "observer"}:
            continue
        assignment.active = False


def _response(
    identity: AdultIdentityModel,
    profile: IdentityAccountProfile | None = None,
) -> AccountResponse:
    return AccountResponse(
        account_id=identity.account_id,
        email=profile.email if profile is not None else None,
        display_name=profile.display_name if profile is not None else None,
        role=identity.account_role,  # type: ignore[arg-type]
        state=identity.state,  # type: ignore[arg-type]
        revision=identity.role_revision,
    )


def _load_profiles(
    provisioner: IdentityAccountProvisioner, subjects: list[str]
) -> dict[str, IdentityAccountProfile]:
    profiles: dict[str, IdentityAccountProfile] = {}
    try:
        for start in range(0, len(subjects), 100):
            profiles.update(provisioner.get_account_profiles(subjects[start : start + 100]))
    except IdentityAccountProvisioningUnavailable:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "IDENTITY_PROVIDER_UNAVAILABLE",
                "message": "Identity service is temporarily unavailable",
            },
        ) from None
    return profiles


@router.get("/accounts", response_model=AccountPageResponse, summary="List application accounts")
def list_accounts(
    request: Request,
    role: AccountRole | None = Query(default=None),
    state: AccountState | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = limit_query(),
    offset: int = Query(
        default=0,
        ge=0,
        deprecated=True,
        description="Deprecated compatibility paging; use `cursor` (SRS §21.1).",
    ),
    cursor: str | None = Query(
        default=None,
        min_length=1,
        max_length=2048,
        description="Opaque cursor from `next_cursor`; valid only with the same filters.",
    ),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> AccountPageResponse:
    _require_platform_admin(db, principal)
    if cursor is not None and offset > 0:
        raise _invalid_field("offset")
    position = _decode_cursor(cursor) if cursor is not None else None
    conditions = []
    if role is not None:
        conditions.append(AdultIdentityModel.account_role == role)
    if state is not None:
        conditions.append(AdultIdentityModel.state == state)
    total = db.scalar(select(func.count()).select_from(AdultIdentityModel).where(*conditions)) or 0
    statement = (
        select(AdultIdentityModel)
        .where(*conditions)
        .order_by(AdultIdentityModel.created_at.desc(), AdultIdentityModel.account_id)
    )
    search_term = search.strip().casefold() if search is not None else ""
    search_all = bool(search_term)
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    if not search_all:
        # Keyset page (FEAT-066 C5): order created_at desc, account_id asc; read one extra row.
        if position is not None:
            statement = statement.where(
                or_(
                    AdultIdentityModel.created_at < position[0],
                    and_(
                        AdultIdentityModel.created_at == position[0],
                        AdultIdentityModel.account_id > position[1],
                    ),
                )
            )
        else:
            statement = statement.offset(offset)
        rows = list(db.scalars(statement.limit(limit + 1)))
        has_more = len(rows) > limit
        rows = rows[:limit]
        profiles = _load_profiles(provisioner, [row.subject for row in rows])
    else:
        # Search keeps the full ordered scan so `total` counts every match (review C5-R1-03).
        scanned = list(db.scalars(statement))
        profiles = _load_profiles(provisioner, [row.subject for row in scanned])
        matching_rows = [
            row
            for row in scanned
            if (
                (profile := profiles.get(row.subject)) is not None
                and (
                    search_term in (profile.email or "").casefold()
                    or search_term in (profile.display_name or "").casefold()
                )
            )
        ]
        total = len(matching_rows)
        start = offset
        if position is not None:
            # Locate the cursor by position in the database order (review C5-R2-05).
            scan_index = {row.account_id: index for index, row in enumerate(scanned)}
            cursor_index = scan_index.get(position[1])
            start = next(
                (
                    index
                    for index, row in enumerate(matching_rows)
                    if (
                        scan_index[row.account_id] > cursor_index
                        if cursor_index is not None
                        else _after_cursor(row, position)
                    )
                ),
                len(matching_rows),
            )
        rows = matching_rows[start : start + limit]
        has_more = start + limit < len(matching_rows)
    next_cursor = (
        _encode_cursor(rows[-1].created_at, rows[-1].account_id) if has_more and rows else None
    )
    return AccountPageResponse(
        items=[_response(row, profiles.get(row.subject)) for row in rows],
        total=total,
        limit=limit,
        offset=0 if position is not None else offset,
        next_cursor=next_cursor,
    )


@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Firebase account and assign its application role",
    responses=_IDEMPOTENCY_RESPONSES,
)
def create_account(
    payload: AccountCreateRequest,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    idempotency_key_header: str | None = Header(
        default=None, alias="Idempotency-Key", description="Required; 1–128 printable characters."
    ),
) -> AccountResponse:
    _require_platform_admin(db, principal)
    key = parse_idempotency_key(request)
    fingerprint = _fingerprint(payload.model_dump(mode="json"))
    stored = _replay(
        db,
        principal_ref=principal.subject,
        scope=_CREATE_SCOPE,
        key=key,
        fingerprint=fingerprint,
    )
    if stored is not None:
        # Same fingerprint means the same payload: no provider call, no audit row.
        return _replayed_response(stored, email=payload.email, display_name=payload.display_name)
    if payload.organization_id is not None:
        _get_organization(db, payload.organization_id)
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    try:
        provisioned = provisioner.create_account(
            email=payload.email, display_name=payload.display_name
        )
    except IdentityAccountConflict:
        raise HTTPException(
            status_code=409,
            detail={"code": "ACCOUNT_SETUP_UNAVAILABLE", "message": "Account setup is unavailable"},
        ) from None
    except IdentityAccountProvisioningUnavailable:
        raise HTTPException(
            status_code=503,
            detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": "Identity service is unavailable"},
        ) from None

    identity = AdultIdentityModel(
        account_id=str(uuid4()),
        subject=provisioned.subject,
        issuer=provisioned.issuer,
        state="active",
        account_role=payload.role,
        role_revision=1,
    )
    db.add(identity)
    if payload.role == "school_manager" and payload.organization_id is not None:
        _ensure_school_manager_assignment(
            db, organization_id=payload.organization_id, subject=provisioned.subject
        )
    _record_account_event(
        db,
        actor=principal.subject,
        account_id=identity.account_id,
        action="ACCOUNT_CREATED",
        organization_id=payload.organization_id,
    )
    created = _response(
        identity,
        IdentityAccountProfile(
            subject=provisioned.subject,
            email=payload.email,
            display_name=payload.display_name,
        ),
    )
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=_CREATE_SCOPE,
            idempotency_key=key,
            organization_id=payload.organization_id,
            request_fingerprint=fingerprint,
            response_json=_stored_values(created),
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        try:
            provisioner.delete_account(provisioned.subject)
        except IdentityAccountProvisioningUnavailable:
            pass
        # A concurrent request may have stored this key first (review C5-R1-06).
        stored = _replay(
            db,
        principal_ref=principal.subject,
        scope=_CREATE_SCOPE,
        key=key,
        fingerprint=fingerprint,
        )
        if stored is not None:
            return _replayed_response(
                stored, email=payload.email, display_name=payload.display_name
            )
        raise HTTPException(
            status_code=409,
            detail={"code": "ACCOUNT_SETUP_UNAVAILABLE", "message": "Account setup is unavailable"},
        ) from None
    except SQLAlchemyError:
        db.rollback()
        try:
            provisioner.delete_account(provisioned.subject)
        except IdentityAccountProvisioningUnavailable:
            pass
        raise HTTPException(
            status_code=503,
            detail={"code": "ACCOUNT_SETUP_UNAVAILABLE", "message": "Account setup is temporarily unavailable"},
        ) from None
    return created


@router.patch(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    summary="Change account role or access state",
    responses=_IDEMPOTENCY_RESPONSES,
)
def update_account(
    account_id: str,
    payload: AccountUpdateRequest,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    idempotency_key_header: str | None = Header(
        default=None, alias="Idempotency-Key", description="Required; 1–128 printable characters."
    ),
) -> AccountResponse:
    _require_platform_admin(db, principal)
    key = parse_idempotency_key(request)
    # FEAT-066 C5 (review C5-R1-04, C5-R2-01): lock the active Platform Admin rows in subject
    # order, then the target, so concurrent updates serialise without deadlock and the
    # last-admin count is stable; populate_existing refreshes an already loaded row (C5-R2-02).
    db.execute(
        select(AdultIdentityModel.subject)
        .where(
            AdultIdentityModel.account_role == "platform_admin",
            AdultIdentityModel.state == "active",
        )
        .order_by(AdultIdentityModel.subject)
        # NO KEY UPDATE: does not block foreign-key inserts that reference these rows (C5-IMPL-R1).
        .with_for_update(key_share=True)
    ).all()
    identity = db.scalar(
        select(AdultIdentityModel)
        .where(AdultIdentityModel.account_id == account_id)
        .with_for_update(key_share=True)
        .execution_options(populate_existing=True)
    )
    if identity is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "ACCOUNT_NOT_FOUND", "message": "Account was not found"},
        )
    scope = f"PATCH /accounts/{account_id}"
    fingerprint = _fingerprint({"account_id": account_id, **payload.model_dump(mode="json")})
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    stored = _replay(
        db, principal_ref=principal.subject, scope=scope, key=key, fingerprint=fingerprint
    )
    profile = _load_profiles(provisioner, [identity.subject]).get(identity.subject)
    if stored is not None:
        db.rollback()
        return _replayed_response(
            stored,
            email=profile.email if profile is not None else None,
            display_name=profile.display_name if profile is not None else None,
        )

    next_role = payload.role if payload.role is not None else identity.account_role
    next_state = payload.state or identity.state
    org_id = payload.organization_id
    if payload.role == "school_manager" and org_id is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "ORGANIZATION_REQUIRED", "message": "Select an organization"},
        )
    if org_id is not None:
        _get_organization(db, org_id)
    if identity.subject == principal.subject and next_role != "platform_admin":
        raise HTTPException(
            status_code=409,
            detail={"code": "SELF_ROLE_CHANGE_DENIED", "message": "You cannot remove your own Platform Admin role"},
        )

    if identity.account_role == "platform_admin" and identity.state == "active":
        admin_count = db.scalar(
            select(func.count())
            .select_from(AdultIdentityModel)
            .where(
                AdultIdentityModel.account_role == "platform_admin",
                AdultIdentityModel.state == "active",
            )
        ) or 0
        if admin_count <= 1 and (next_role != "platform_admin" or next_state != "active"):
            raise HTTPException(
                status_code=409,
                detail={"code": "LAST_PLATFORM_ADMIN", "message": "At least one active Platform Admin is required"},
            )

    previous_role = identity.account_role
    previous_state = identity.state
    role_changed = next_role != previous_role or (
        next_role == "school_manager" and org_id is not None
    )
    state_changed = next_state != previous_state
    if next_role != previous_role:
        if next_role == "school_manager":
            _revoke_assignments(db, subject=identity.subject, except_school_manager_org=org_id)
            assert org_id is not None
            _ensure_school_manager_assignment(db, organization_id=org_id, subject=identity.subject)
        elif next_role == "teacher":
            _revoke_assignments(
                db,
                subject=identity.subject,
                preserve_teacher_assignments=previous_role == "teacher",
            )
        else:
            _revoke_assignments(db, subject=identity.subject)
        identity.account_role = next_role
    elif next_role == "school_manager" and org_id is not None:
        _revoke_assignments(db, subject=identity.subject, except_school_manager_org=org_id)
        _ensure_school_manager_assignment(db, organization_id=org_id, subject=identity.subject)

    if role_changed or state_changed:
        identity.role_revision += 1
    identity.state = next_state
    action = "ACCOUNT_ROLE_CHANGED" if role_changed else "ACCOUNT_STATE_CHANGED"
    _record_account_event(
        db,
        actor=principal.subject,
        account_id=identity.account_id,
        action=action,
        organization_id=org_id,
    )
    updated = _response(identity, profile)
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=scope,
            idempotency_key=key,
            organization_id=org_id,
            request_fingerprint=fingerprint,
            response_json=_stored_values(updated),
        )
    )

    if state_changed:
        try:
            provisioner.set_account_disabled(identity.subject, next_state == "disabled")
        except IdentityAccountProvisioningUnavailable:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": "Identity service is unavailable"},
            ) from None
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        if state_changed:
            try:
                provisioner.set_account_disabled(identity.subject, previous_state == "disabled")
            except IdentityAccountProvisioningUnavailable:
                pass
        raise HTTPException(
            status_code=503,
            detail={"code": "ACCOUNT_UPDATE_UNAVAILABLE", "message": "Account update is temporarily unavailable"},
        ) from None
    return updated


__all__ = ["router"]
