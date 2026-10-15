"""Organization, class, managed-profile, enrollment and pending-consent endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import (
    CreateAssignmentRequest,
    CreateClassRequest,
    CreateProfileRequest,
    RecordConsentRequest,
)
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ConsentRecordModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    audit,
    commit,
    consent_is_effective,
    deny_pending_consent,
    event,
    failure,
    get_class,
    require_assignment,
)

router = APIRouter(
    prefix="/api/be1/v1", tags=["BE1 registry"], responses=BE1_ERROR_RESPONSES
)


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


@router.post("/organizations/{organization_id}/assignments", status_code=status.HTTP_201_CREATED)
def create_assignment(
    organization_id: str,
    payload: CreateAssignmentRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"school_admin"})
    if payload.class_id is not None:
        get_class(db, organization_id, payload.class_id)
    existing_identity = db.get(AdultIdentityModel, payload.subject)
    if existing_identity is None:
        db.add(AdultIdentityModel(subject=payload.subject, issuer=principal.issuer, state="active"))
        db.flush()
    elif existing_identity.issuer != principal.issuer:
        raise failure(409, "IDENTITY_ISSUER_MISMATCH", "Identity belongs to a different provider")
    duplicate = db.scalar(
        select(OrganizationAssignmentModel.assignment_id).where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.subject == payload.subject,
            OrganizationAssignmentModel.class_id.is_(None)
            if payload.class_id is None
            else OrganizationAssignmentModel.class_id == payload.class_id,
            OrganizationAssignmentModel.role == payload.role,
            OrganizationAssignmentModel.active.is_(True),
        )
    )
    if duplicate is not None:
        raise failure(409, "ASSIGNMENT_EXISTS", "Active assignment already exists")
    assignment_id = str(uuid4())
    row = OrganizationAssignmentModel(
        assignment_id=assignment_id,
        organization_id=organization_id,
        subject=payload.subject,
        class_id=payload.class_id,
        role=payload.role,
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
        payload={"assignment_id": assignment_id, "role": payload.role},
    )
    commit(db)
    return {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": assignment_id,
        "subject": payload.subject,
        "role": payload.role,
        "class_id": payload.class_id,
        "active": True,
    }


@router.delete("/organizations/{organization_id}/assignments/{assignment_id}")
def revoke_assignment(
    organization_id: str,
    assignment_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"school_admin"})
    row = db.scalar(
        select(OrganizationAssignmentModel).where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.assignment_id == assignment_id,
            OrganizationAssignmentModel.active.is_(True),
        )
    )
    if row is None:
        raise failure(404, "ASSIGNMENT_NOT_FOUND", "Active assignment was not found")
    row.active = False
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="identity.assignment.revoke",
        resource_type="adult_assignment",
        resource_id=assignment_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=organization_id,
        event_type="be1.identity.assignment_revoked.v1",
        payload={"assignment_id": assignment_id},
    )
    commit(db)
    return {"contract": "Be1AdultAssignmentV1", "assignment_id": assignment_id, "active": False}


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
    require_assignment(db, principal, organization_id, roles={"school_admin"})
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


@router.post(
    "/organizations/{organization_id}/classes/{class_id}/profiles",
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    organization_id: str,
    class_id: str,
    payload: CreateProfileRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if payload.class_id != class_id:
        raise failure(422, "CLASS_SCOPE_MISMATCH", "Class in body must match the route")
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=class_id
    )
    get_class(db, organization_id, class_id)
    consent = db.scalar(
        select(ConsentRecordModel).where(
            ConsentRecordModel.organization_id == organization_id,
            ConsentRecordModel.class_id == class_id,
            ConsentRecordModel.child_id == payload.child_id,
            ConsentRecordModel.consent_id == payload.consent_id,
            ConsentRecordModel.purpose_ref == payload.purpose_ref,
            ConsentRecordModel.state == "effective",
        )
    )
    if consent is None:
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="child_profile",
            resource_id=payload.child_id,
            action="profile.create",
        )
    try:
        validate_age_months(payload.age_months)
    except CoreRuleViolation as exc:
        raise failure(422, exc.code.value, str(exc)) from None
    child_id = payload.child_id
    profile = ManagedProfileModel(
        child_id=child_id,
        organization_id=organization_id,
        class_id=class_id,
        display_name=payload.display_name,
        age_months=payload.age_months,
        consent_id=payload.consent_id,
        consent_purpose_ref=payload.purpose_ref,
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
        "consent_state": "effective",
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
