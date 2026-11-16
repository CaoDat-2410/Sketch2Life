"""Organization, class, managed-profile, enrollment and pending-consent endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import (
    Be1PilotProfileListResponse,
    CreateAssignmentRequest,
    CreateClassRequest,
    CreateProfileRequest,
    RecordConsentRequest,
)
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.domain.eligibility import PROOF_VERSION
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ConsentRecordModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    get_db,
    get_runtime,
    get_verified_adult,
)
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    audit,
    commit,
    consent_is_effective,
    event,
    failure,
    get_class,
    get_session,
    require_assignment,
)

router = APIRouter(prefix="/api/be1/v1", tags=["BE1 registry"], responses=BE1_ERROR_RESPONSES)


def _scope_denied() -> HTTPException:
    return failure(403, "SCOPE_DENIED", "Access to this resource is not permitted")


def _require_m2_assignment(
    db: Session,
    principal: VerifiedPrincipal,
    organization_id: str,
    *,
    roles: set[str],
    class_id: str | None = None,
) -> tuple[OrganizationAssignmentModel, ...]:
    try:
        return require_assignment(
            db,
            principal,
            organization_id,
            roles=roles,
            class_id=class_id,
        )
    except HTTPException as exc:
        detail = exc.detail
        code = detail.get("code") if isinstance(detail, dict) else None
        if exc.status_code == 403 and code in {"ADULT_NOT_ASSIGNED", "SCOPE_DENIED"}:
            raise _scope_denied() from None
        raise


@router.get("/organizations/{organization_id}")
def read_organization(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id)
    row = db.scalar(
        select(OrganizationModel).where(
            OrganizationModel.organization_id == organization_id,
            OrganizationModel.state == "active",
        )
    )
    if row is None:
        raise failure(404, "ORGANIZATION_NOT_FOUND", "Organization was not found")
    return {
        "contract": "Be1OrganizationV1",
        "organization_id": row.organization_id,
        "display_name": row.display_name,
    }


@router.get("/organizations/{organization_id}/me")
def current_assignments(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _ = require_assignment(db, principal, organization_id)
    rows = db.scalars(
        select(OrganizationAssignmentModel).where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.subject == principal.subject,
            OrganizationAssignmentModel.active.is_(True),
        )
    ).all()
    return {
        "contract": "Be1AdultAssignmentsV1",
        "subject": principal.subject,
        "organization_id": organization_id,
        "assignments": [{"role": row.role, "class_id": row.class_id} for row in rows],
    }


@router.post("/classes/{class_id}/assignments", status_code=status.HTTP_201_CREATED)
def assign_class_teacher(
    class_id: str,
    payload: CreateAssignmentRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    classroom = db.scalar(
        select(ClassroomModel)
        .where(ClassroomModel.class_id == class_id, ClassroomModel.state == "active")
        .with_for_update()
    )
    if classroom is None:
        raise _scope_denied()
    organization_id = classroom.organization_id
    _require_m2_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin"},
        class_id=class_id,
    )
    active_teacher_count = db.scalar(
        select(func.count())
        .select_from(OrganizationAssignmentModel)
        .where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.class_id == class_id,
            OrganizationAssignmentModel.role == "teacher",
            OrganizationAssignmentModel.active.is_(True),
        )
    )
    if active_teacher_count:
        raise failure(
            409,
            "CLASS_TEACHER_EXISTS",
            "Class already has an active Teacher",
        )
    existing_identity = db.get(AdultIdentityModel, payload.subject)
    if existing_identity is None:
        db.add(AdultIdentityModel(subject=payload.subject, issuer=principal.issuer, state="active"))
        db.flush()
    elif existing_identity.issuer != principal.issuer:
        raise failure(409, "IDENTITY_ISSUER_MISMATCH", "Identity belongs to a different provider")
    assignment_id = str(uuid4())
    row = OrganizationAssignmentModel(
        assignment_id=assignment_id,
        organization_id=organization_id,
        subject=payload.subject,
        class_id=class_id,
        role="teacher",
        active=True,
    )
    db.add(row)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="identity.assignment.create",
        resource_type="adult_assignment",
        resource_id=assignment_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=organization_id,
        event_type="be1.identity.assignment_created.v1",
        payload={"assignment_id": assignment_id, "role": "teacher"},
    )
    commit(db)
    return {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": assignment_id,
        "subject": payload.subject,
        "role": "teacher",
        "class_id": class_id,
        "active": True,
    }


@router.get("/organizations/{organization_id}/classes")
def list_classes(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assignments = require_assignment(db, principal, organization_id)
    allowed_class_ids = {row.class_id for row in assignments if row.class_id is not None}
    org_wide = any(row.class_id is None for row in assignments)
    statement = select(ClassroomModel).where(
        ClassroomModel.organization_id == organization_id,
        ClassroomModel.state == "active",
    )
    if not org_wide:
        statement = statement.where(ClassroomModel.class_id.in_(allowed_class_ids))
    rows = db.scalars(statement.order_by(ClassroomModel.created_at)).all()
    return {
        "contract": "Be1ClassListV1",
        "items": [
            {"class_id": row.class_id, "display_name": row.display_name, "state": row.state}
            for row in rows
        ],
    }


@router.post("/organizations/{organization_id}/classes", status_code=status.HTTP_201_CREATED)
def create_class(
    organization_id: str,
    payload: CreateClassRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_m2_assignment(db, principal, organization_id, roles={"school_admin"})
    class_id = str(uuid4())
    record = ClassroomModel(
        class_id=class_id,
        organization_id=organization_id,
        display_name=payload.display_name,
        created_by=principal.subject,
    )
    db.add(record)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="class.create",
        resource_type="class",
        resource_id=class_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=class_id,
        event_type="be1.class.created.v1",
        payload={"class_id": class_id},
    )
    commit(db)
    return {"contract": "Be1ClassV1", "class_id": class_id, "display_name": record.display_name}


@router.get("/organizations/{organization_id}/classes/{class_id}/profiles")
def list_profiles(
    organization_id: str,
    class_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, class_id=class_id)
    get_class(db, organization_id, class_id)
    rows = db.scalars(
        select(ManagedProfileModel)
        .where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.state == "active",
        )
        .order_by(ManagedProfileModel.created_at)
    ).all()
    if any(
        not consent_is_effective(
            db,
            organization_id=organization_id,
            class_id=class_id,
            child_id=row.child_id,
            purpose_ref=row.consent_purpose_ref,
        )
        for row in rows
    ):
        audit(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            action="profile.list",
            resource_type="class",
            resource_id=class_id,
            decision="denied_consent_pending",
        )
        commit(db)
        raise failure(
            409, "CONSENT_NOT_EFFECTIVE", "Child profiles are blocked while consent is pending"
        )
    return {
        "contract": "Be1ManagedProfileListV1",
        "items": [
            {
                "child_id": row.child_id,
                "class_id": row.class_id,
                "display_name": row.display_name,
                "age_months": row.age_months,
            }
            for row in rows
        ],
    }


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
    response_model=Be1PilotProfileListResponse,
)
def list_pilot_profiles(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = get_session(db, organization_id, session_id)
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"teacher", "school_admin"},
        class_id=session.class_id,
    )
    if (
        runtime.settings.env not in {"local", "test"}
        or not runtime.settings.synthetic_pilot_enabled
    ):
        raise failure(
            409,
            "PILOT_PROFILE_LOOKUP_UNAVAILABLE",
            "Synthetic pilot profile lookup is unavailable",
        )
    if session.state != "lobby":
        raise failure(409, "SESSION_NOT_IN_LOBBY", "Pilot profiles are available only in the lobby")

    purpose_ref = session.configuration.get("purpose_ref")
    profiles: list[ManagedProfileModel] = []
    if isinstance(purpose_ref, str) and purpose_ref:
        now = datetime.now(UTC)
        valid_proof = (
            select(SyntheticEligibilityProofModel.evidence_id)
            .where(
                SyntheticEligibilityProofModel.organization_id == organization_id,
                SyntheticEligibilityProofModel.class_id == session.class_id,
                SyntheticEligibilityProofModel.child_profile_id == ManagedProfileModel.child_id,
                SyntheticEligibilityProofModel.purpose_ref == purpose_ref,
                SyntheticEligibilityProofModel.session_id == session_id,
                SyntheticEligibilityProofModel.schema_version == PROOF_VERSION,
                SyntheticEligibilityProofModel.data_origin == "SYNTHETIC_DEV",
                SyntheticEligibilityProofModel.issued_at <= now,
                SyntheticEligibilityProofModel.expires_at > now,
                SyntheticEligibilityProofModel.revoked_at.is_(None),
            )
            .exists()
        )
        profiles = list(
            db.scalars(
                select(ManagedProfileModel)
                .where(
                    ManagedProfileModel.organization_id == organization_id,
                    ManagedProfileModel.class_id == session.class_id,
                    ManagedProfileModel.state == "active",
                    ManagedProfileModel.data_origin == "SYNTHETIC_DEV",
                    valid_proof,
                )
                .order_by(ManagedProfileModel.created_at)
            ).all()
        )
    return {
        "contract": "Be1PilotProfileListV1",
        "items": [
            {"child_id": profile.child_id, "display_name": profile.display_name}
            for profile in profiles
        ],
    }


@router.post(
    "/organizations/{organization_id}/classes/{class_id}/profiles",
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    organization_id: str,
    class_id: str,
    payload: CreateProfileRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if payload.class_id != class_id:
        raise failure(422, "CLASS_SCOPE_MISMATCH", "Class in body must match the route")
    if (
        runtime.settings.env not in {"local", "test"}
        or not runtime.settings.synthetic_pilot_enabled
    ):
        raise failure(
            409,
            "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE",
            "Synthetic profile creation is unavailable",
        )
    classroom = db.scalar(
        select(ClassroomModel).where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.class_id == class_id,
            ClassroomModel.state == "active",
        )
    )
    if classroom is None:
        raise _scope_denied()
    assignments = _require_m2_assignment(
        db,
        principal,
        organization_id,
        roles={"teacher"},
        class_id=class_id,
    )
    if not any(row.class_id == class_id and row.role == "teacher" for row in assignments):
        raise _scope_denied()
    try:
        validate_age_months(payload.age_months, maximum_months=120)
    except CoreRuleViolation as exc:
        raise failure(422, exc.code.value, str(exc)) from None
    child_id = f"synthetic-{secrets.token_hex(12)}"
    profile = ManagedProfileModel(
        child_id=child_id,
        organization_id=organization_id,
        class_id=class_id,
        display_name=payload.display_name,
        age_months=payload.age_months,
        age_revision=1,
        age_source="SYNTHETIC_FIXTURE",
        consent_id=None,
        consent_purpose_ref=None,
        data_origin="SYNTHETIC_DEV",
        created_by=principal.subject,
    )
    enrollment = EnrollmentModel(
        enrollment_id=str(uuid4()),
        organization_id=organization_id,
        class_id=class_id,
        child_id=child_id,
        created_by=principal.subject,
    )
    db.add_all([profile, enrollment])
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="profile.enroll",
        resource_type="child_profile",
        resource_id=child_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=child_id,
        event_type="be1.profile.enrolled.v1",
        payload={"class_id": class_id, "child_id": child_id},
    )
    commit(db)
    return {
        "contract": "Be1ManagedProfileV1",
        "child_id": child_id,
        "class_id": class_id,
        "display_name": profile.display_name,
        "age_months": profile.age_months,
        "data_origin": profile.data_origin,
    }


@router.post(
    "/organizations/{organization_id}/classes/{class_id}/consents",
    status_code=status.HTTP_201_CREATED,
)
def record_consent(
    organization_id: str,
    class_id: str,
    payload: RecordConsentRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if payload.class_id != class_id:
        raise failure(422, "CLASS_SCOPE_MISMATCH", "Class in body must match the route")
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=class_id
    )
    consent_id = str(uuid4())
    record = ConsentRecordModel(
        consent_id=consent_id,
        organization_id=organization_id,
        class_id=class_id,
        child_id=payload.child_id,
        purpose_ref=payload.purpose_ref,
        evidence_ref=payload.evidence_ref,
        state="pending",
        recorded_by=principal.subject,
    )
    db.add(record)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="consent.record_pending",
        resource_type="consent",
        resource_id=consent_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=payload.child_id,
        event_type="be1.consent.pending.v1",
        payload={"child_id": payload.child_id, "consent_id": consent_id},
    )
    commit(db)
    return {
        "contract": "Be1ConsentV1",
        "consent_id": consent_id,
        "child_id": payload.child_id,
        "purpose_ref": payload.purpose_ref,
        "state": "pending",
        "effective": False,
    }


@router.get("/organizations/{organization_id}/classes/{class_id}/consents")
def list_consents(
    organization_id: str,
    class_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=class_id
    )
    get_class(db, organization_id, class_id)
    rows = db.scalars(
        select(ConsentRecordModel)
        .where(
            ConsentRecordModel.organization_id == organization_id,
            ConsentRecordModel.class_id == class_id,
        )
        .order_by(ConsentRecordModel.recorded_at.desc())
    ).all()
    return {
        "contract": "Be1ConsentListV1",
        "items": [
            {
                "consent_id": row.consent_id,
                "child_id": row.child_id,
                "purpose_ref": row.purpose_ref,
                "state": row.state,
                "effective": False,
            }
            for row in rows
        ],
    }


@router.post("/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke")
def revoke_consent(
    organization_id: str,
    class_id: str,
    consent_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=class_id
    )
    row = db.scalar(
        select(ConsentRecordModel).where(
            ConsentRecordModel.organization_id == organization_id,
            ConsentRecordModel.class_id == class_id,
            ConsentRecordModel.consent_id == consent_id,
        )
    )
    if row is None:
        raise failure(404, "CONSENT_NOT_FOUND", "Consent record was not found")
    if row.state == "revoked":
        return {
            "contract": "Be1ConsentV1",
            "consent_id": consent_id,
            "state": "revoked",
            "effective": False,
        }
    row.state = "revoked"
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="consent.revoke",
        resource_type="consent",
        resource_id=consent_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=row.child_id,
        event_type="be1.consent.revoked.v1",
        payload={"child_id": row.child_id, "consent_id": consent_id},
    )
    commit(db)
    return {
        "contract": "Be1ConsentV1",
        "consent_id": consent_id,
        "state": "revoked",
        "effective": False,
    }


__all__ = ["router"]
