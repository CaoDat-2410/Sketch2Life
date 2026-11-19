"""Organization, class, managed-profile, enrollment and pending-consent endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import secrets
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import Select, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountProvisioner,
    IdentityAccountProvisioningUnavailable,
    VerifiedPrincipal,
)
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
    Be1CommandReceiptModel,
    ClassroomModel,
    ConsentRecordModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.interfaces.http.api_conventions import limit_query, raise_stale_revision
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
    return failure(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")


# --- FEAT-066 C6 M9-B: first Teacher assignment (plan Draft 3) ------------------------------
_ETAG = re.compile(r'^"([1-9][0-9]*)"$')


def class_assignment_revision(teacher_row_count: int) -> int:
    """Derived class assignment revision: 1 + teacher rows of the class (rows are never deleted)."""
    return 1 + teacher_row_count


def _active_teacher_row(organization_id: str) -> Any:
    """Correlated EXISTS: the identity holds an active teacher row in the organization."""
    return exists().where(
        OrganizationAssignmentModel.organization_id == organization_id,
        OrganizationAssignmentModel.subject == AdultIdentityModel.subject,
        OrganizationAssignmentModel.role == "teacher",
        OrganizationAssignmentModel.active.is_(True),
    )


def eligible_teachers_select(organization_id: str) -> Select[Any]:
    """Candidates (M9B-3): active Teacher identities with an active teacher row in the org."""
    return select(AdultIdentityModel).where(
        AdultIdentityModel.state == "active",
        AdultIdentityModel.account_role == "teacher",
        _active_teacher_row(organization_id),
    )


def candidate_lock_select(organization_id: str, candidate_ref: str) -> Select[Any]:
    """One statement: the eligible candidate locked FOR SHARE (blocks a concurrent role change)."""
    return (
        eligible_teachers_select(organization_id)
        .where(AdultIdentityModel.account_id == candidate_ref)
        .with_for_update(read=True, of=AdultIdentityModel)
        .execution_options(populate_existing=True)
    )


def class_lock_select(class_id: str) -> Select[Any]:
    """The active class row locked FOR UPDATE; serialises assignment commands for the class."""
    return (
        select(ClassroomModel)
        .where(ClassroomModel.class_id == class_id, ClassroomModel.state == "active")
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _teacher_counts(
    db: Session, organization_id: str, class_ids: list[str]
) -> dict[str, tuple[int, int]]:
    """(all teacher rows, active teacher rows) per class, one grouped query."""
    if not class_ids:
        return {}
    rows = db.execute(
        select(
            OrganizationAssignmentModel.class_id,
            func.count(),
            func.count().filter(OrganizationAssignmentModel.active.is_(True)),
        )
        .where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.role == "teacher",
            OrganizationAssignmentModel.class_id.in_(class_ids),
        )
        .group_by(OrganizationAssignmentModel.class_id)
    ).all()
    return {str(class_id): (int(total), int(active)) for class_id, total, active in rows}


def _strong_revision(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "If-Match", "code": "REQUIRED"}],
            },
        )
    match = _ETAG.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "If-Match", "code": "INVALID_FORMAT"}],
            },
        )
    return int(match.group(1))


def _encode_candidate_cursor(account_id: str) -> str:
    payload = json.dumps({"account_id": account_id, "v": 1}, sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_candidate_cursor(cursor: str) -> str:
    try:
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != {"account_id", "v"}:
            raise ValueError
        if decoded["v"] != 1 or not isinstance(decoded["account_id"], str):
            raise ValueError
        if not 1 <= len(decoded["account_id"]) <= 36:
            raise ValueError
        return decoded["account_id"]
    except (binascii.Error, json.JSONDecodeError, UnicodeEncodeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "cursor", "code": "INVALID_FORMAT"}],
            },
        ) from None


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
        # CONV-1: every out-of-scope case answers with the one uniform 404 body; an in-scope
        # role refusal (403 ACTION_NOT_ALLOWED) passes through unchanged.
        if exc.status_code == 404:
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


@router.get("/organizations/{organization_id}/teacher-candidates")
def list_teacher_candidates(
    organization_id: str,
    request: Request,
    limit: int = limit_query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=512),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """FEAT-066 M9-B: same-organization Teacher candidates, minimum fields (O-3a, O-3b)."""
    _require_m2_assignment(db, principal, organization_id, roles={"school_admin"})
    statement = eligible_teachers_select(organization_id).order_by(AdultIdentityModel.account_id)
    if cursor is not None:
        after = _decode_candidate_cursor(cursor)
        statement = statement.where(AdultIdentityModel.account_id > after)
    rows = list(db.scalars(statement.limit(limit + 1)))
    has_more = len(rows) > limit
    rows = rows[:limit]
    provisioner: IdentityAccountProvisioner = request.app.state.identity_account_provisioner
    try:
        profiles = provisioner.get_account_profiles([row.subject for row in rows]) if rows else {}
    except IdentityAccountProvisioningUnavailable:
        raise failure(
            503, "IDENTITY_PROVIDER_UNAVAILABLE", "Identity service is temporarily unavailable"
        ) from None
    return {
        "contract": "Be1TeacherCandidatePageV1",
        "items": [
            {
                "candidate_ref": row.account_id,
                "display_name": (
                    profile.display_name
                    if (profile := profiles.get(row.subject)) is not None
                    else None
                ),
            }
            for row in rows
        ],
        "next_cursor": _encode_candidate_cursor(rows[-1].account_id) if has_more and rows else None,
    }


@router.post("/classes/{class_id}/assignments")
def assign_class_teacher(
    class_id: str,
    payload: CreateAssignmentRequest,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """FEAT-066 M9-B: first Teacher of a class; 200 + assignment revision (SRS §21.2 line 1650)."""
    classroom = db.scalar(
        select(ClassroomModel).where(
            ClassroomModel.class_id == class_id, ClassroomModel.state == "active"
        )
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
    expected_revision = _strong_revision(if_match)
    if db.scalar(class_lock_select(class_id)) is None:
        raise _scope_denied()
    scope = f"POST /classes/{class_id}/assignments"
    fingerprint = hashlib.sha256(
        json.dumps(
            {"candidate_ref": payload.candidate_ref, "if_match": expected_revision},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        if receipt.request_fingerprint != fingerprint:
            raise failure(
                400,
                "INVALID_IDEMPOTENCY_KEY",
                "Idempotency-Key was already used for another request",
            )
        stored = dict(receipt.response_json)
        db.rollback()
        response.headers["ETag"] = f'"{stored["assignment_revision"]}"'
        return stored
    total_rows, active_rows = _teacher_counts(db, organization_id, [class_id]).get(
        class_id, (0, 0)
    )
    current_revision = class_assignment_revision(total_rows)
    if current_revision != expected_revision:
        db.rollback()
        raise_stale_revision(current_version=current_revision, etag=str(current_revision))
    if active_rows:
        raise failure(
            409,
            "CLASS_TEACHER_EXISTS",
            "Class already has an active Teacher",
        )
    candidate = db.scalar(candidate_lock_select(organization_id, payload.candidate_ref))
    if candidate is None:
        # M9B-7: unknown, inactive, non-Teacher or other-organization candidate.
        raise _scope_denied()
    assignment_id = str(uuid4())
    new_revision = current_revision + 1
    try:
        db.add(
            OrganizationAssignmentModel(
                assignment_id=assignment_id,
                organization_id=organization_id,
                subject=candidate.subject,
                class_id=class_id,
                role="teacher",
                active=True,
            )
        )
        db.flush()
    except IntegrityError:
        # An earlier inactive row for this Teacher and class (reassignment is UC-12).
        db.rollback()
        raise failure(
            409, "RESOURCE_CONFLICT", "The command conflicts with current records"
        ) from None
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
    body: dict[str, object] = {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": assignment_id,
        "candidate_ref": payload.candidate_ref,
        "role": "teacher",
        "class_id": class_id,
        "active": True,
        "assignment_revision": new_revision,
    }
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            request_fingerprint=fingerprint,
            response_json=body,
        )
    )
    commit(db)
    response.headers["ETag"] = f'"{new_revision}"'
    return body


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
    # FEAT-066 M9-B: additive fields the assignment screen needs (one grouped query).
    counts = _teacher_counts(db, organization_id, [row.class_id for row in rows])
    return {
        "contract": "Be1ClassListV1",
        "items": [
            {
                "class_id": row.class_id,
                "display_name": row.display_name,
                "state": row.state,
                "assignment_revision": class_assignment_revision(
                    counts.get(row.class_id, (0, 0))[0]
                ),
                "has_active_teacher": counts.get(row.class_id, (0, 0))[1] > 0,
            }
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
