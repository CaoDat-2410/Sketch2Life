"""Platform Admin account provisioning and server-managed role changes."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import re
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, select
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
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
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
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> AccountPageResponse:
    _require_platform_admin(db, principal)
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
    if not search_all:
        statement = statement.limit(limit).offset(offset)
    rows = list(db.scalars(statement))
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    profiles = _load_profiles(provisioner, [row.subject for row in rows])
    if search_all:
        matching_rows = [
            row
            for row in rows
            if (
                (profile := profiles.get(row.subject)) is not None
                and (
                    search_term in (profile.email or "").casefold()
                    or search_term in (profile.display_name or "").casefold()
                )
            )
        ]
        total = len(matching_rows)
        rows = matching_rows[offset : offset + limit]
    return AccountPageResponse(
        items=[_response(row, profiles.get(row.subject)) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Firebase account and assign its application role",
)
def create_account(
    payload: AccountCreateRequest,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> AccountResponse:
    _require_platform_admin(db, principal)
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        try:
            provisioner.delete_account(provisioned.subject)
        except IdentityAccountProvisioningUnavailable:
            pass
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
    return _response(
        identity,
        IdentityAccountProfile(
            subject=provisioned.subject,
            email=payload.email,
            display_name=payload.display_name,
        ),
    )


@router.patch(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    summary="Change account role or access state",
)
def update_account(
    account_id: str,
    payload: AccountUpdateRequest,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> AccountResponse:
    _require_platform_admin(db, principal)
    identity = db.scalar(
        select(AdultIdentityModel).where(AdultIdentityModel.account_id == account_id)
    )
    if identity is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "ACCOUNT_NOT_FOUND", "message": "Account was not found"},
        )
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    profile = _load_profiles(provisioner, [identity.subject]).get(identity.subject)

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
    return _response(identity, profile)


__all__ = ["router"]
