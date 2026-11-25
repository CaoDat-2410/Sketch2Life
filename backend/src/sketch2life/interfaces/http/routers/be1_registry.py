"""Organization, class, managed-profile, enrollment and pending-consent endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, NoReturn
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import Select, and_, exists, func, or_, select, tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountProvisioner,
    IdentityAccountProvisioningUnavailable,
    VerifiedPrincipal,
)
from sketch2life.application.ports.support_needs import (
    SupportNeedsCrypto,
    SupportNeedsUnavailable,
)
from sketch2life.contracts.schemas.be1_capacity import (
    Be1CapacityConfigureRequest,
    Be1OrganizationCapacityV1,
    Be1ScheduledCapacityChangeV1,
)
from sketch2life.contracts.schemas.be1_runtime import (
    Be1PilotProfileListResponse,
    Be1ProfileEditResultV1,
    Be1ProfileRevisionPageV1,
    Be1ProfileRevisionV1,
    Be1SupportNeedsPutV1,
    Be1SupportNeedsV1,
    Be1SupportNeedsWriteV1,
    CreateAssignmentRequest,
    CreateClassRequest,
    CreateProfileRequest,
    EditProfileRequest,
    MoveProfileRequest,
    RecordConsentRequest,
)
from sketch2life.domain.be1_profile_revisions import (
    BAND_VERSION,
    HASH_VERSION,
    MAX_EDIT_AGE_MONTHS,
    age_band,
    revision_hash,
)
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.domain.eligibility import PROOF_VERSION
from sketch2life.domain.platform_admin import AdminError
from sketch2life.domain.support_needs import SupportNeedsPayload
from sketch2life.infrastructure.be1.capacity_adapter import (
    Be1CapacityAdapter,
    CapacityDependencyUnavailable,
    effective_active_class_count,
)
from sketch2life.infrastructure.config.settings import MIN_PROFILE_RECEIPT_KEY_BYTES, Settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    DataLifecycleRequestModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    ProfileRevisionModel,
    SessionMembershipModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.infrastructure.persistence.billing_models import SubscriptionModel
from sketch2life.infrastructure.persistence.support_needs_repository import (
    Be1SupportNeedsStore,
    SupportNeedsStale,
)
from sketch2life.interfaces.http.api_conventions import (
    cursor_query,
    decode_cursor,
    decode_time_cursor,
    encode_cursor,
    limit_query,
    parse_idempotency_key,
    raise_stale_revision,
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
    deny_pending_consent,
    event,
    failure,
    get_class,
    get_session,
    hide_archived_from_teacher,
    project_due_capacity_suspensions,
    require_assignment,
    require_class_teacher_row,
    settle_due_class_suspensions,
)
from sketch2life.interfaces.http.support_needs_runtime import (
    SupportNeedsRuntime,
    get_support_needs_runtime,
)

router = APIRouter(prefix="/api/be1/v1", tags=["BE1 registry"], responses=BE1_ERROR_RESPONSES)


def _scope_denied() -> HTTPException:
    return failure(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")


# T-7a cursor scopes (SRS l.1640): one scope per route and organization, so a cursor cannot be
# replayed across routes or organizations.
_CLASS_CURSOR_SCOPE = "be1.classes:{organization_id}:{state}"
_CONSENT_CURSOR_SCOPE = "be1.consents:{organization_id}:{class_id}"
# T-7e (D-066-100): the Teacher class roster, one scope per route, organization and class.
_ROSTER_CURSOR_SCOPE = "be1.profiles:{organization_id}:{class_id}"
# T-12b: the revision history of one profile, bound to route, organization, class and child.
_REVISION_CURSOR_SCOPE = "be1.profile-revisions:{organization_id}:{class_id}:{child_id}"


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
    """The class row, in any state, locked FOR UPDATE.

    It serialises every command that changes the class row: the Teacher assignment and the
    state commands (T-7b). The caller reads the state after the wait, so a command that lost a
    race to a suspension sees ``suspended`` and answers 409, not a 404 (T-7b-DEC-8).
    """
    return (
        select(ClassroomModel)
        .where(ClassroomModel.class_id == class_id)
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


def _roster_audience(
    assignments: tuple[OrganizationAssignmentModel, ...], class_id: str
) -> str:
    """Return "manager" or "teacher" for the roster reads, else 403 (D-066-75 CM-11).

    The rows come from `require_assignment` without a role filter, so the account-role filter
    already kept only `school_admin` rows for a School Manager and `teacher`, `guide` and
    `observer` rows for a Teacher account. The class is known and the caller is assigned in
    the organization, so a refusal is 403 and not the uniform 404 (SRS l.864-865).
    """
    if any(row.role == "school_admin" for row in assignments):
        return "manager"
    require_class_teacher_row(assignments, class_id)  # T-7a2: one copy of the rule
    return "teacher"


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
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """FEAT-066 M9-B: first Teacher of a class; 200 + assignment revision (SRS §21.2 line 1650)."""
    classroom = db.scalar(select(ClassroomModel).where(ClassroomModel.class_id == class_id))
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
    settle_due_class_suspensions(db, organization_id, actor=principal.subject)
    # C-D5: 1-128 visible ASCII, one header; the parsed value replaces the declared one.
    idempotency_key = parse_idempotency_key(request)
    expected_revision = _strong_revision(if_match)
    locked_class = db.scalar(class_lock_select(class_id))
    if locked_class is None:
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
    if locked_class.state != "active":
        # T-7b-DEC-7 (SRS l.593, l.1425): a suspended or archived class is read-only. The class is
        # known to this Manager, so the refusal is 409 (not the uniform 404), also when a
        # suspension committed while this request waited for the row lock.
        db.rollback()
        raise failure(
            409, "INVALID_STATE_TRANSITION", "The class is read-only in its current state"
        )
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
    # TD-28: an assignment moves the class revision (the row is already locked FOR UPDATE).
    locked_class.revision += 1
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


ClassListState = Literal["active", "suspended", "archived", "all"]
_CLASS_STATES: tuple[str, ...] = ("active", "suspended", "archived")
_TEACHER_CLASS_STATES: tuple[str, ...] = ("active", "suspended")


def _listed_states(requested: str, *, manager: bool) -> tuple[str, ...]:
    """The stored states a list request covers (T-7b-DEC-3, SRS l.1708).

    A School Manager may ask for any state; a Teacher never sees an archived class, so
    ``archived`` alone is an empty page and ``all`` means the two states a Teacher can see.
    """
    visible = _CLASS_STATES if manager else _TEACHER_CLASS_STATES
    if requested == "all":
        return visible
    return (requested,) if requested in visible else ()


@router.get("/organizations/{organization_id}/classes")
def list_classes(
    organization_id: str,
    state: Annotated[ClassListState, Query()] = "active",
    limit: int = limit_query(),
    cursor: str | None = cursor_query(),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assignments = require_assignment(db, principal, organization_id)
    settle_due_class_suspensions(db, organization_id, actor=principal.subject)
    allowed_class_ids = {row.class_id for row in assignments if row.class_id is not None}
    # T-7b-DEC-3 (closes T-7a Q-1): only an organization-wide School Manager row lists every
    # class. An organization-wide Teacher-family row is a membership marker and no longer does;
    # a Teacher lists the classes of a class-scoped row (SRS l.1708).
    manager = any(row.role == "school_admin" for row in assignments)
    org_wide = any(row.role == "school_admin" and row.class_id is None for row in assignments)
    statement = select(ClassroomModel).where(
        ClassroomModel.organization_id == organization_id,
        ClassroomModel.state.in_(_listed_states(state, manager=manager)),
    )
    if not org_wide:
        statement = statement.where(ClassroomModel.class_id.in_(allowed_class_ids))
    # T-7a (SRS l.1640): keyset paging, ordered by (created_at, class_id) ascending. The scope
    # filter above runs before paging; the cursor is decoded only after the scope check. The
    # cursor scope carries the state filter, so a cursor cannot move to another filter.
    scope = _CLASS_CURSOR_SCOPE.format(organization_id=organization_id, state=state)
    if cursor is not None:
        after_time, after_id = decode_time_cursor(cursor, scope=scope)
        statement = statement.where(
            tuple_(ClassroomModel.created_at, ClassroomModel.class_id) > (after_time, after_id)
        )
    rows = list(
        db.scalars(
            statement.order_by(ClassroomModel.created_at, ClassroomModel.class_id).limit(limit + 1)
        ).all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    # FEAT-066 M9-B: additive fields the assignment screen needs (one grouped query).
    counts = _teacher_counts(db, organization_id, [row.class_id for row in rows])
    return {
        "contract": "Be1ClassListV1",
        "items": [
            {
                "class_id": row.class_id,
                "display_name": row.display_name,
                "state": row.state,
                "class_revision": row.revision,
                "assignment_revision": class_assignment_revision(
                    counts.get(row.class_id, (0, 0))[0]
                ),
                "has_active_teacher": counts.get(row.class_id, (0, 0))[1] > 0,
            }
            for row in rows
        ],
        "next_cursor": (
            encode_cursor(
                scope=scope, sort_key=rows[-1].created_at.isoformat(), item_id=rows[-1].class_id
            )
            if has_more and rows
            else None
        ),
    }


def _create_class_fingerprint(display_name: str) -> str:
    return hashlib.sha256(
        json.dumps({"display_name": display_name}, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _class_created_body(
    *, class_id: str, display_name: str, state: str, assignment_revision: int
) -> dict[str, object]:
    # state and assignment_revision are additive fields (SRS l.1635). assignment_revision is the
    # revision the next assignment command must send; it is not the class revision of l.1651.
    return {
        "contract": "Be1ClassV1",
        "class_id": class_id,
        "display_name": display_name,
        "state": state,
        "assignment_revision": assignment_revision,
    }


def _stored_class_replay(
    receipt: Be1CommandReceiptModel, *, fingerprint: str, display_name: str
) -> dict[str, object]:
    if receipt.request_fingerprint != fingerprint:
        raise failure(
            400,
            "INVALID_IDEMPOTENCY_KEY",
            "Idempotency-Key was already used for another request",
        )
    stored = receipt.response_json
    return _class_created_body(
        class_id=str(stored["class_id"]),
        display_name=display_name,
        state=str(stored["state"]),
        assignment_revision=int(str(stored["assignment_revision"])),
    )


_CAPACITY_ADMIN_WIRE_ERRORS: dict[str, tuple[int, str]] = {
    "CLASS_SELECTION_REQUIRED": (422, "CLASS_SELECTION_REQUIRED"),
    "INVALID_CAPACITY_DOWNGRADE": (422, "INVALID_CAPACITY_DOWNGRADE"),
    "SUBSCRIPTION_PERIOD_ENDED": (409, "SUBSCRIPTION_PERIOD_ENDED"),
    "NOT_FOUND": (404, "RESOURCE_NOT_FOUND"),
    "INVALID_IDEMPOTENCY_KEY": (400, "INVALID_IDEMPOTENCY_KEY"),
    "STALE_REVISION": (409, "STALE_REVISION"),
}


def _raise_capacity_admin_error(exc: AdminError) -> NoReturn:
    if exc.code == "BILLING_SANDBOX_DISABLED":
        raise failure(
            503,
            "DEPENDENCY_UNAVAILABLE",
            "Billing capacity is temporarily unavailable",
        ) from None
    wire_error = _CAPACITY_ADMIN_WIRE_ERRORS.get(exc.code)
    if wire_error is not None:
        status_code, code = wire_error
        raise failure(status_code, code, "The capacity command could not be completed") from None
    # Billing may add a code before BE1 has a stable public contract for it. Fail closed with
    # the registered dependency error instead of leaking an unclassified internal code.
    raise failure(
        503,
        "DEPENDENCY_UNAVAILABLE",
        "Billing capacity is temporarily unavailable",
    ) from None


def _capacity_adapter(db: Session, actor: str, settings: Settings) -> Be1CapacityAdapter:
    try:
        return Be1CapacityAdapter(db, actor, settings)
    except AdminError as exc:
        _raise_capacity_admin_error(exc)


def _active_class_refs(db: Session, organization_id: str) -> set[str]:
    return set(
        db.scalars(
            select(ClassroomModel.class_id).where(
                ClassroomModel.organization_id == organization_id,
                ClassroomModel.state == "active",
            )
        )
    )


def _capacity_response(
    db: Session,
    adapter: Be1CapacityAdapter,
    *,
    organization_id: str,
    row: SubscriptionModel | None,
    view: dict[str, Any],
) -> Be1OrganizationCapacityV1:
    active_refs = _active_class_refs(db, organization_id)
    due_refs = {str(class_ref) for class_ref in view.get("suspended_class_refs", [])}
    active_count = effective_active_class_count(active_refs, due_refs)
    scheduled = adapter.scheduled_change(row, view)
    return Be1OrganizationCapacityV1(
        organization_id=organization_id,
        subscription_id=row.subscription_id if row is not None else None,
        capacity=int(view["capacity"]),
        active_class_count=active_count,
        available_slots=max(0, int(view["capacity"]) - active_count),
        subscription_state=str(view["state"]),
        revision=int(view["revision"]),
        period_start=view["period_start"],
        period_end=view["period_end"],
        scheduled_change=(
            Be1ScheduledCapacityChangeV1.model_validate(scheduled) if scheduled else None
        ),
    )


def _raise_capacity_unavailable(db: Session) -> NoReturn:
    db.rollback()
    raise failure(
        503,
        "DEPENDENCY_UNAVAILABLE",
        "Billing capacity is temporarily unavailable",
    ) from None


def _capacity_config_fingerprint(
    organization_id: str, payload: Be1CapacityConfigureRequest, expected_revision: int
) -> str:
    material = {
        "organization_id": organization_id,
        "action": payload.action,
        "payload": payload.model_dump(mode="json", exclude_unset=True),
        "expected_revision": expected_revision,
    }
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _capacity_receipt_replay(
    receipt: Be1CommandReceiptModel,
    *,
    fingerprint: str,
    response: Response,
) -> Be1OrganizationCapacityV1:
    if receipt.request_fingerprint != fingerprint:
        raise failure(
            400,
            "INVALID_IDEMPOTENCY_KEY",
            "Idempotency-Key was already used for another request",
        )
    stored = Be1OrganizationCapacityV1.model_validate(receipt.response_json)
    response.headers["ETag"] = f'"{stored.revision}"'
    response.headers["Cache-Control"] = "private, no-store"
    return stored


@router.get(
    "/organizations/{organization_id}/capacity",
    response_model=Be1OrganizationCapacityV1,
)
def read_organization_capacity(
    organization_id: str,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Be1OrganizationCapacityV1:
    """Read only the authenticated Manager's Billing-derived effective capacity."""
    try:
        _require_m2_assignment(db, principal, organization_id, roles={"school_admin"})
    except HTTPException as exc:
        # Capacity is a sensitive Manager resource; do not reveal that an organization has a
        # capacity record to an assigned non-Manager.
        if exc.status_code in {403, 404}:
            raise _scope_denied() from None
        raise
    try:
        adapter = _capacity_adapter(
            db, principal.subject, request.app.state.be1_runtime.settings
        )
        row, view = adapter.view_for_organization(organization_id, lock=False)
        due_refs = {str(class_ref) for class_ref in view.get("suspended_class_refs", [])}
        projected = project_due_capacity_suspensions(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            class_refs=due_refs,
        )
        result = _capacity_response(
            db,
            adapter,
            organization_id=organization_id,
            row=row,
            view=view,
        )
        if projected:
            # Commit the read-time class state, revision, audit, and outbox together.
            db.commit()
    except CapacityDependencyUnavailable:
        _raise_capacity_unavailable(db)
    except AdminError as exc:
        db.rollback()
        _raise_capacity_admin_error(exc)
    except SQLAlchemyError:
        _raise_capacity_unavailable(db)
    response.headers["ETag"] = f'"{result.revision}"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.patch(
    "/organizations/{organization_id}/capacity",
    response_model=Be1OrganizationCapacityV1,
)
def configure_organization_capacity(
    organization_id: str,
    payload: Be1CapacityConfigureRequest,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str, Header(alias="If-Match")],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Be1OrganizationCapacityV1:
    """Configure only this Manager's subscription through the Billing-owned rules."""
    _require_m2_assignment(db, principal, organization_id, roles={"school_admin"})
    idempotency_key = parse_idempotency_key(request)
    expected_revision = _strong_revision(if_match)
    scope = f"PATCH /organizations/{organization_id}/capacity"
    fingerprint = _capacity_config_fingerprint(organization_id, payload, expected_revision)
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        result = _capacity_receipt_replay(receipt, fingerprint=fingerprint, response=response)
        db.rollback()
        return result

    try:
        adapter = _capacity_adapter(
            db, principal.subject, request.app.state.be1_runtime.settings
        )
        # Constructing the command service checks Billing's local-test sandbox gate. Reads and
        # class creation never construct it.
        billing_capacity = adapter.command_service()
        row, view = adapter.view_for_organization(organization_id, lock=True)
        if row is None:
            raise AdminError("NOT_FOUND", 404)
        subscription_id = row.subscription_id
        # The subscription row serializes same-organization PATCH requests. Recheck the BE1
        # receipt after the lock so a concurrent first request replays before its stale check.
        receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if receipt is not None:
            result = _capacity_receipt_replay(
                receipt, fingerprint=fingerprint, response=response
            )
            db.rollback()
            return result

        if row.revision != expected_revision:
            current_revision = row.revision
            db.rollback()
            raise_stale_revision(current_version=current_revision, etag=str(current_revision))

        due_refs = {str(class_ref) for class_ref in view.get("suspended_class_refs", [])}
        project_due_capacity_suspensions(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            class_refs=due_refs,
        )
        config_payload = {
            "action": payload.action,
            "addon_slots": payload.addon_slots,
            "suspend_class_refs": payload.suspend_class_refs or [],
        }
        configured = billing_capacity.configure(  # type: ignore[no-untyped-call]
            subscription_id,
            config_payload,
            expected_revision,
            idempotency_key,
            _active_class_refs(db, organization_id),
        )
        result = _capacity_response(
            db,
            adapter,
            organization_id=organization_id,
            row=row,
            view=configured,
        )
        audit(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            action=f"subscription.{payload.action}",
            resource_type="organization_subscription",
            resource_id=subscription_id,
        )
        db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=idempotency_key,
                organization_id=organization_id,
                request_fingerprint=fingerprint,
                response_json=result.model_dump(mode="json"),
            )
        )
        db.commit()
    except CapacityDependencyUnavailable:
        _raise_capacity_unavailable(db)
    except AdminError as exc:
        db.rollback()
        _raise_capacity_admin_error(exc)
    except SQLAlchemyError:
        _raise_capacity_unavailable(db)
    response.headers["ETag"] = f'"{result.revision}"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/organizations/{organization_id}/classes", status_code=status.HTTP_201_CREATED)
def create_class(
    organization_id: str,
    payload: CreateClassRequest,
    request: Request,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """SRS l.1649: 201 class reference; a durable Idempotency-Key receipt (l.1697, C-D5/C-D6)."""
    _require_m2_assignment(db, principal, organization_id, roles={"school_admin"})
    idempotency_key = parse_idempotency_key(request)
    scope = f"POST /organizations/{organization_id}/classes"
    fingerprint = _create_class_fingerprint(payload.display_name)
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        replay = _stored_class_replay(
            receipt, fingerprint=fingerprint, display_name=payload.display_name
        )
        db.rollback()
        return replay

    # The Billing subscription row is the organization serialization lock shared with
    # subscription configuration and payment settlement. When there is no subscription row,
    # the adapter locks the BE1 organization row before the active-class count. Capacity view,
    # downgrade projection, class write, audit/outbox and receipt stay in this Session.
    try:
        adapter = _capacity_adapter(
            db, principal.subject, request.app.state.be1_runtime.settings
        )
        _subscription, capacity_view = adapter.view_for_organization(organization_id, lock=True)
    except CapacityDependencyUnavailable:
        _raise_capacity_unavailable(db)
    except AdminError as exc:
        db.rollback()
        _raise_capacity_admin_error(exc)
    except SQLAlchemyError:
        _raise_capacity_unavailable(db)

    # A concurrent same-key create may have committed while this request waited for the
    # subscription lock. Check again before the capacity refusal so successful retries replay.
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        replay = _stored_class_replay(
            receipt, fingerprint=fingerprint, display_name=payload.display_name
        )
        db.rollback()
        return replay

    active_refs = _active_class_refs(db, organization_id)
    due_suspensions = {
        str(class_ref) for class_ref in capacity_view.get("suspended_class_refs", [])
    }
    active_count = effective_active_class_count(active_refs, due_suspensions)
    if active_count >= int(capacity_view["capacity"]):
        db.rollback()
        raise failure(
            409,
            "CLASS_CAPACITY_REACHED",
            "The organization has no available class slots",
        )

    project_due_capacity_suspensions(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        class_refs=due_suspensions,
    )
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
    body = _class_created_body(
        class_id=class_id,
        display_name=record.display_name,
        state=record.state,
        assignment_revision=class_assignment_revision(0),
    )
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            request_fingerprint=fingerprint,
            response_json={
                "class_id": class_id,
                "state": record.state,
                "assignment_revision": body["assignment_revision"],
            },
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first: its class and receipt stand,
        # this transaction (class, audit and event rows included) is rolled back.
        db.rollback()
        winner = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if winner is None:
            raise failure(
                409, "RESOURCE_CONFLICT", "The command conflicts with current records"
            ) from None
        replay = _stored_class_replay(
            winner, fingerprint=fingerprint, display_name=payload.display_name
        )
        db.rollback()
        return replay
    return body


# --- T-7b: class archive and manual suspend (SRS l.1709, l.593, l.1425, TD-08) ---------------
# command -> (target state, states it may start from). `archived` is terminal and there is no
# reactivate or unarchive command: SRS l.1896 ties reactivation to capacity (X-13, not built).
_STATE_COMMANDS: dict[str, tuple[str, frozenset[str]]] = {
    "suspend": ("suspended", frozenset({"active"})),
    "archive": ("archived", frozenset({"active", "suspended"})),
}


def class_state_transition_allowed(command: str, from_state: str) -> bool:
    """The whole state machine: suspend from active; archive from active or suspended."""
    return from_state in _STATE_COMMANDS[command][1]


def _class_state_fingerprint(command: str, expected_revision: int) -> str:
    return hashlib.sha256(
        json.dumps(
            {"command": command, "if_match": expected_revision},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _class_state_body(*, class_id: str, state: str, class_revision: int) -> dict[str, object]:
    # No name, age, child reference or count: only the class id, its state and its revision.
    return {
        "contract": "Be1ClassStateV1",
        "class_id": class_id,
        "state": state,
        "class_revision": class_revision,
    }


def _replayed_class_state(
    receipt: Be1CommandReceiptModel, *, fingerprint: str, response: Response
) -> dict[str, object]:
    if receipt.request_fingerprint != fingerprint:
        raise failure(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    stored = dict(receipt.response_json)
    response.headers["ETag"] = f'"{stored["class_revision"]}"'
    return stored


def _change_class_state(
    command: str,
    class_id: str,
    request: Request,
    response: Response,
    if_match: str | None,
    principal: VerifiedPrincipal,
    db: Session,
) -> dict[str, object]:
    """One keyed state command; the order mirrors `assign_class_teacher` (plan R1)."""
    target_state, _sources = _STATE_COMMANDS[command]
    # (1) the class in any state: a missing class is the uniform 404.
    known = db.scalar(select(ClassroomModel).where(ClassroomModel.class_id == class_id))
    if known is None:
        raise _scope_denied()
    organization_id = known.organization_id
    # (2) School Manager only: strangers, other organizations, Parent and Platform Admin get the
    # uniform 404; a Teacher account assigned in the organization is 403 (SRS l.864-865).
    _require_m2_assignment(
        db, principal, organization_id, roles={"school_admin"}, class_id=class_id
    )
    settle_due_class_suspensions(db, organization_id, actor=principal.subject)
    # (3) the key (1-128 visible ASCII) and the strong class revision.
    idempotency_key = parse_idempotency_key(request)
    expected_revision = _strong_revision(if_match)
    # (4) the class row locked FOR UPDATE in any state.
    classroom = db.scalar(class_lock_select(class_id))
    if classroom is None:
        raise _scope_denied()
    # (5) the receipt: same fingerprint is the stored body, another request is 400.
    scope = f"POST /classes/{class_id}/{command}"
    fingerprint = _class_state_fingerprint(command, expected_revision)
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        replay = _replayed_class_state(receipt, fingerprint=fingerprint, response=response)
        db.rollback()
        return replay
    # (6) the expected class revision (SRS l.1699): a stale request never writes.
    if classroom.revision != expected_revision:
        current = classroom.revision
        db.rollback()
        raise_stale_revision(current_version=current, etag=str(current))
    # (7) the transition (the same state again is refused too).
    from_state = classroom.state
    if not class_state_transition_allowed(command, from_state):
        db.rollback()
        raise failure(
            409,
            "INVALID_STATE_TRANSITION",
            "The class cannot move to this state from its current state",
        )
    # (8) one transaction: state, revision, audit, event, receipt.
    classroom.state = target_state
    classroom.revision += 1
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action=f"class.{command}",
        resource_type="class",
        resource_id=class_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=class_id,
        event_type=f"be1.class.{target_state}.v1",
        payload={"class_id": class_id, "from_state": from_state, "to_state": target_state},
        revision=classroom.revision,
    )
    body = _class_state_body(
        class_id=class_id, state=target_state, class_revision=classroom.revision
    )
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
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first (as `create_class`): this
        # transaction is rolled back and the winner's stored body is the answer.
        db.rollback()
        winner = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if winner is None:
            raise failure(
                409, "RESOURCE_CONFLICT", "The command conflicts with current records"
            ) from None
        replay = _replayed_class_state(winner, fingerprint=fingerprint, response=response)
        db.rollback()
        return replay
    response.headers["ETag"] = f'"{classroom.revision}"'
    return body


@router.post("/classes/{class_id}/suspend")
def suspend_class(
    class_id: str,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-7b: School Manager suspends an active class (read-only, SRS l.593, l.1709)."""
    return _change_class_state("suspend", class_id, request, response, if_match, principal, db)


@router.post("/classes/{class_id}/archive")
def archive_class(
    class_id: str,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-7b: School Manager archives an active or suspended class; terminal (SRS l.1709)."""
    return _change_class_state("archive", class_id, request, response, if_match, principal, db)


def _active_profile_count(db: Session, organization_id: str, class_id: str) -> int:
    """Count every active profile of the class (the Manager summary and the Teacher total)."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(ManagedProfileModel)
            .where(
                ManagedProfileModel.organization_id == organization_id,
                ManagedProfileModel.class_id == class_id,
                ManagedProfileModel.state == "active",
            )
        )
        or 0
    )


def _roster_listed(organization_id: str, class_id: str) -> Select[tuple[ManagedProfileModel]]:
    """Active profiles a Teacher may see: synthetic, or `REAL` with an effective consent.

    The consent condition is the predicate of `consent_is_effective` (organization, class,
    child and purpose match, state `effective`, non-null purpose) written as one `EXISTS`, so a
    page is a single statement. `LEGACY_UNCLASSIFIED` profiles are never listed (SRS l.832).
    """
    consented = exists().where(
        ConsentRecordModel.organization_id == ManagedProfileModel.organization_id,
        ConsentRecordModel.class_id == ManagedProfileModel.class_id,
        ConsentRecordModel.child_id == ManagedProfileModel.child_id,
        ConsentRecordModel.purpose_ref == ManagedProfileModel.consent_purpose_ref,
        ConsentRecordModel.state == "effective",
    )
    return select(ManagedProfileModel).where(
        ManagedProfileModel.organization_id == organization_id,
        ManagedProfileModel.class_id == class_id,
        ManagedProfileModel.state == "active",
        or_(
            ManagedProfileModel.data_origin == "SYNTHETIC_DEV",
            and_(
                ManagedProfileModel.data_origin == "REAL",
                ManagedProfileModel.consent_purpose_ref.is_not(None),
                consented,
            ),
        ),
    )


@router.get("/organizations/{organization_id}/classes/{class_id}/profiles")
def list_profiles(
    organization_id: str,
    class_id: str,
    limit: int = limit_query(),
    cursor: str | None = cursor_query(),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assignments = require_assignment(db, principal, organization_id, class_id=class_id)
    # T-7b-DEC-5: a read, so a suspended class is readable; an archived one only by a Manager.
    hide_archived_from_teacher(get_class(db, organization_id, class_id, write=False), assignments)
    # T-7a (SRS l.2586, D-066-75 CM-3, CM-5, CM-11): the School Manager gets a count only, with
    # no consent gate and no audit row; profile fields go to a Teacher assigned to this class.
    # T-7e (D-066-100): `limit` and `cursor` are accepted and ignored for a Manager, who never
    # decodes a cursor.
    audience = _roster_audience(assignments, class_id)
    active_profile_count = _active_profile_count(db, organization_id, class_id)
    if audience == "manager":
        return {
            "contract": "Be1ClassRosterSummaryV1",
            "class_id": class_id,
            "active_profile_count": active_profile_count,
        }
    # T-7e (D-066-100, SRS l.1640): a Teacher always gets 200 with the synthetic or consented
    # profiles, keyset-paged by (created_at, child_id), plus the count of all active profiles.
    # The cursor is decoded only after the scope checks above.
    statement = _roster_listed(organization_id, class_id)
    scope = _ROSTER_CURSOR_SCOPE.format(organization_id=organization_id, class_id=class_id)
    if cursor is not None:
        after_time, after_id = decode_time_cursor(cursor, scope=scope)
        statement = statement.where(
            tuple_(ManagedProfileModel.created_at, ManagedProfileModel.child_id)
            > (after_time, after_id)
        )
    rows = list(
        db.scalars(
            statement.order_by(ManagedProfileModel.created_at, ManagedProfileModel.child_id).limit(
                limit + 1
            )
        ).all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
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
        "next_cursor": (
            encode_cursor(
                scope=scope, sort_key=rows[-1].created_at.isoformat(), item_id=rows[-1].child_id
            )
            if has_more and rows
            else None
        ),
        "active_profile_count": active_profile_count,
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
    assignments = require_assignment(
        db,
        principal,
        organization_id,
        roles={"teacher"},  # T0.11: no School Manager (SRS l.2586)
        class_id=session.class_id,
    )
    # T-7a2-DEC-1: an org-wide `teacher` row covers the class but is not the assignment.
    require_class_teacher_row(assignments, session.class_id)
    settle_due_class_suspensions(db, organization_id, actor=principal.subject)
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


# --- T-7c: Teacher profile create (SRS l.543, l.832, l.1095, l.1651, l.1697-1699; TD-28) -------
# The real-data success write is parked BLOCKED_OPEN (X-19: `be1_consent_records` has no
# effective state and the SRS names no authorization record). Only the refusing gate is built.
_RECEIPT_SCOPE_LIMIT = 256  # be1_command_receipts.operation_scope is varchar(256)


def _profile_receipt_scope(organization_id: str, class_id: str) -> str:
    """`POST /organizations/{org}/classes/{class}/profiles`, hashed only if it cannot fit."""
    scope = f"POST /organizations/{organization_id}/classes/{class_id}/profiles"
    if len(scope) <= _RECEIPT_SCOPE_LIMIT:
        return scope
    digest = hashlib.sha256(f"{organization_id}/{class_id}".encode()).hexdigest()
    return f"POST /organizations/classes/profiles#{digest}"


_PROFILE_FP_DOMAIN = "be1.profile.create.receipt"
_PROFILE_FP_VERSION = 2
_PROFILE_FP_KEY_ID_DOMAIN = b"be1.profile.create.receipt.key-id"


def _profile_receipt_key(runtime: Be1Runtime) -> bytes:
    """The receipt MAC key; absent or short fails closed with 503, never with a write (O-1).

    Called only when a fingerprint is needed (a stored receipt, the synthetic write, the real
    gate), after the scope checks, so a stranger never learns about the configuration.
    """
    configured = runtime.settings.profile_receipt_hmac_key
    key = configured.get_secret_value().encode("utf-8") if configured is not None else b""
    if len(key) < MIN_PROFILE_RECEIPT_KEY_BYTES:
        raise failure(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable")
    return key


def _profile_key_id(key: bytes) -> str:
    """A short non-reversible id of the key, stored in the receipt so a rotation is detectable."""
    return hmac.new(key, _PROFILE_FP_KEY_ID_DOMAIN, hashlib.sha256).hexdigest()[:8]


def _profile_fingerprint(
    *,
    key: bytes,
    principal_ref: str,
    scope: str,
    payload: CreateProfileRequest,
    expected_revision: int,
) -> str:
    """Keyed HMAC-SHA-256 (hex, 64 chars) over the request, which holds the child's name and age.

    The domain and version live inside the MAC input because the receipt column is 64 characters
    wide (no DDL). The value is derived child data (FR-C-10, SRS l.502, BR-34 l.278): without the
    server key it cannot be confirmed by guessing a name, and it is never logged or returned.
    """
    message = json.dumps(
        {
            "domain": _PROFILE_FP_DOMAIN,
            "v": _PROFILE_FP_VERSION,
            "principal": principal_ref,
            "scope": scope,
            "display_name": payload.display_name,
            "age_months": payload.age_months,
            "consent_id": payload.consent_id,
            "if_match": expected_revision,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _profile_created_body(
    *,
    child_id: str,
    class_id: str,
    enrollment_id: str,
    display_name: str,
    age_months: int,
    data_origin: str,
    class_revision: int,
) -> dict[str, object]:
    return {
        "contract": "Be1ManagedProfileV1",
        "child_id": child_id,
        "class_id": class_id,
        "enrollment_id": enrollment_id,
        "display_name": display_name,
        "age_months": age_months,
        "data_origin": data_origin,
        "class_revision": class_revision,
    }


def _replayed_profile(
    receipt: Be1CommandReceiptModel,
    *,
    fingerprint: str,
    key_id: str,
    class_id: str,
    payload: CreateProfileRequest,
    response: Response,
) -> dict[str, object]:
    """The stored references plus the request's own name and age (equal by fingerprint).

    A receipt written before the keyed format (no `fp_v`), under another format version or another
    key id never matches (T-7c-fix-DEC-4: a stated deviation from SRS l.1697, which would return
    the first result); it answers 400 `INVALID_IDEMPOTENCY_KEY`, never a second profile.
    """
    stored = receipt.response_json
    same_format = (
        stored.get("fp_v") == _PROFILE_FP_VERSION
        and stored.get("fp_kid") == key_id
        and hmac.compare_digest(
            receipt.request_fingerprint.encode("ascii", "replace"), fingerprint.encode("ascii")
        )
    )
    if not same_format:
        raise failure(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    class_revision = int(str(stored["class_revision"]))
    response.headers["ETag"] = f'"{class_revision}"'
    return _profile_created_body(
        child_id=str(stored["child_id"]),
        class_id=class_id,
        enrollment_id=str(stored["enrollment_id"]),
        display_name=payload.display_name,
        age_months=payload.age_months,
        data_origin=str(stored["data_origin"]),
        class_revision=class_revision,
    )


def _profile_create_mode(
    *, env: str, synthetic_pilot_enabled: bool, real_enabled: bool, consent_id: str | None
) -> Literal["synthetic", "real_gate"]:
    """The mode matrix of T-7c-DEC-4. The server decides the origin, never the client.

    ``consent_id`` absent: synthetic when the pilot is on in local/test, else 409 (as before),
    and 400 when only real data is on. ``consent_id`` present: 400 ``UNKNOWN_FIELD`` while real
    data is off, otherwise the refusing real gate.
    """
    synthetic_on = env in {"local", "test"} and synthetic_pilot_enabled
    if consent_id is None:
        if synthetic_on:
            return "synthetic"
        if real_enabled:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_REQUEST",
                    "field_errors": [{"field": "consent_id", "code": "REQUIRED"}],
                },
            )
        raise failure(
            409,
            "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE",
            "Synthetic profile creation is unavailable",
        )
    if not real_enabled:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "consent_id", "code": "UNKNOWN_FIELD"}],
            },
        )
    return "real_gate"


def _refuse_real_profile(
    db: Session, *, organization_id: str, class_id: str, consent_id: str, actor: str
) -> NoReturn:
    """The real-data gate (T-7c-DEC-5): it refuses every time and writes no profile.

    The consent must exist in this organization and class (404 ``CONSENT_NOT_FOUND`` as
    ``revoke_consent``). The child, purpose and id of a real profile are NOT taken from that
    client-chosen row: no consent state is valid yet (X-19, SRS l.1095-1096), so the answer is
    the audited 409 ``CONSENT_NOT_EFFECTIVE`` whatever the row says.
    """
    exists_in_class = db.scalar(
        select(ConsentRecordModel.consent_id).where(
            ConsentRecordModel.organization_id == organization_id,
            ConsentRecordModel.class_id == class_id,
            ConsentRecordModel.consent_id == consent_id,
        )
    )
    if exists_in_class is None:
        db.rollback()
        raise failure(404, "CONSENT_NOT_FOUND", "Consent record was not found")
    deny_pending_consent(
        db,
        organization_id=organization_id,
        actor=actor,
        resource_type="consent",
        resource_id=consent_id,
        action="profile.enroll",
    )
    raise AssertionError("deny_pending_consent always raises")  # fail closed


_PROFILE_GATE_OPERATION = "profile_create_real_gate"
_UNKNOWN_CLIENT = "unknown-client"


def _charge_profile_gate(
    runtime: Be1Runtime, request: Request, principal: VerifiedPrincipal
) -> None:
    """NFR-12 (O-2): 429 + Retry-After by account and client address, never by child or content.

    The address is the TCP peer as the server reports it (forwarded headers are not read here);
    a missing client shares one bucket. The caller rolls back before raising so the class lock is
    released; the 429 writes no audit row, no receipt and no log line with ids.
    """
    client = request.client.host if request.client is not None else _UNKNOWN_CLIENT
    wait = runtime.profile_gate_limiter.acquire(
        _PROFILE_GATE_OPERATION, account=principal.subject, ip=client
    )
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED"},
            headers={"Retry-After": str(wait)},
        )


@router.post(
    "/organizations/{organization_id}/classes/{class_id}/profiles",
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    organization_id: str,
    class_id: str,
    payload: CreateProfileRequest,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-7c: keyed Teacher profile create with the expected class revision (SRS l.1651, l.1697).

    Order: class in any state (404), Teacher row of this class (404, or 403 for another role),
    key, `If-Match`, class row FOR UPDATE, receipt replay, stale revision, active class, mode
    matrix, validation, insert. Create does not bump the class revision (TD-28).
    """
    known = db.scalar(
        select(ClassroomModel).where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.class_id == class_id,
        )
    )
    if known is None:
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
    settle_due_class_suspensions(db, organization_id, actor=principal.subject)
    idempotency_key = parse_idempotency_key(request)
    expected_revision = _strong_revision(if_match)
    classroom = db.scalar(class_lock_select(class_id))
    if classroom is None:
        raise _scope_denied()
    scope = _profile_receipt_scope(organization_id, class_id)
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        try:
            replay_key = _profile_receipt_key(runtime)
            replay = _replayed_profile(
                receipt,
                fingerprint=_profile_fingerprint(
                    key=replay_key,
                    principal_ref=principal.subject,
                    scope=scope,
                    payload=payload,
                    expected_revision=expected_revision,
                ),
                key_id=_profile_key_id(replay_key),
                class_id=class_id,
                payload=payload,
                response=response,
            )
        except HTTPException:
            db.rollback()  # releases the class FOR UPDATE on a 503 or a 400 mismatch
            raise
        db.rollback()
        return replay
    if classroom.revision != expected_revision:
        current = classroom.revision
        db.rollback()
        raise_stale_revision(current_version=current, etag=str(current))
    if classroom.state != "active":
        # T-7b-DEC-5 (SRS l.1425): a read-only class refuses a new profile, after the scope check
        # so a stranger never learns the state.
        db.rollback()
        raise failure(
            409, "INVALID_STATE_TRANSITION", "The class is read-only in its current state"
        )
    mode = _profile_create_mode(
        env=runtime.settings.env,
        synthetic_pilot_enabled=runtime.settings.synthetic_pilot_enabled,
        real_enabled=runtime.settings.real_profile_data_enabled,
        consent_id=payload.consent_id,
    )
    try:
        key = _profile_receipt_key(runtime)  # fail closed (503) before a write or a gate charge
    except HTTPException:
        db.rollback()
        raise
    if mode == "real_gate" and payload.consent_id is not None:
        try:
            # Charged first, before the consent lookup, so probing consent ids is limited too.
            _charge_profile_gate(runtime, request, principal)
        except HTTPException:
            db.rollback()  # releases the class FOR UPDATE; nothing was written
            raise
        _refuse_real_profile(
            db,
            organization_id=organization_id,
            class_id=class_id,
            consent_id=payload.consent_id,
            actor=principal.subject,
        )
    fingerprint = _profile_fingerprint(
        key=key,
        principal_ref=principal.subject,
        scope=scope,
        payload=payload,
        expected_revision=expected_revision,
    )
    key_id = _profile_key_id(key)
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
    class_revision = classroom.revision  # read before the commit expires the row
    body = _profile_created_body(
        child_id=child_id,
        class_id=class_id,
        enrollment_id=enrollment.enrollment_id,
        display_name=profile.display_name,
        age_months=profile.age_months,
        data_origin=profile.data_origin,
        class_revision=class_revision,
    )
    # References only: no name, no age (the fingerprint is the one derived value).
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            request_fingerprint=fingerprint,
            response_json={
                "child_id": child_id,
                "enrollment_id": enrollment.enrollment_id,
                "class_revision": class_revision,
                "data_origin": profile.data_origin,
                # Format and key id (no name, no key): a rotation or a v1 row is detectable
                # without DDL (T-7c-fix-DEC-4).
                "fp_v": _PROFILE_FP_VERSION,
                "fp_kid": key_id,
            },
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first: its profile and receipt stand,
        # this transaction (profile, enrollment, audit and event rows included) is rolled back.
        db.rollback()
        winner = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if winner is None:
            raise failure(
                409, "RESOURCE_CONFLICT", "The command conflicts with current records"
            ) from None
        replay = _replayed_profile(
            winner,
            fingerprint=fingerprint,
            key_id=key_id,
            class_id=class_id,
            payload=payload,
            response=response,
        )
        db.rollback()
        return replay
    response.headers["ETag"] = f'"{class_revision}"'
    return body


# --- FEAT-066 goal v3 T-7d: enrollment move between two classes of one Teacher (FR-T-05) --------
# SRS l.544 (one active enrollment, the earlier one is closed and kept), l.830 and l.1093 (the
# enrollment is the source of the current-class projection), l.1425 (capacity never blocks a
# change in an existing class: no capacity, quota or billing code here), l.1651 and l.1699
# (expected class revision, STALE_REVISION), l.1697 (keyed commands). The School Manager gets 403
# and no cross-Teacher move exists (X-19, T-7d-DEC-2).
_MOVE_SESSION_STATES_OPEN = ("join_pending", "admitted")


def _move_receipt_scope(class_id: str, child_id: str) -> str:
    """`POST /classes/{class}/profiles/{child}/move`, hashed only if it cannot fit (varchar 256)."""
    scope = f"POST /classes/{class_id}/profiles/{child_id}/move"
    if len(scope) <= _RECEIPT_SCOPE_LIMIT:
        return scope
    digest = hashlib.sha256(f"{class_id}/{child_id}".encode()).hexdigest()
    return f"POST /classes/profiles/move#{digest}"


def _move_fingerprint(
    *, class_id: str, child_id: str, payload: MoveProfileRequest, expected_revision: int
) -> str:
    """Ids and counters only (no name or age), so a plain SHA-256 holds no child data."""
    return hashlib.sha256(
        json.dumps(
            {
                "v": 1,
                "command": "profile.move",
                "class_id": class_id,
                "child_id": child_id,
                "target_class_id": payload.target_class_id,
                "target_class_revision": payload.target_class_revision,
                "if_match": expected_revision,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _move_body(
    *,
    child_id: str,
    from_class_id: str,
    to_class_id: str,
    enrollment_id: str,
    from_class_revision: int,
    to_class_revision: int,
) -> dict[str, object]:
    # References and counters only: no name, age, consent state or count.
    return {
        "contract": "Be1ProfileMoveV1",
        "child_id": child_id,
        "from_class_id": from_class_id,
        "to_class_id": to_class_id,
        "enrollment_id": enrollment_id,
        "from_class_revision": from_class_revision,
        "to_class_revision": to_class_revision,
    }


def _replayed_move(receipt: Be1CommandReceiptModel, *, fingerprint: str) -> dict[str, object]:
    if receipt.request_fingerprint != fingerprint:
        raise failure(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    # JSONB reorders keys: rebuild the body so a replay is byte-identical to the first answer.
    stored = receipt.response_json
    return _move_body(
        child_id=str(stored["child_id"]),
        from_class_id=str(stored["from_class_id"]),
        to_class_id=str(stored["to_class_id"]),
        enrollment_id=str(stored["enrollment_id"]),
        from_class_revision=int(str(stored["from_class_revision"])),
        to_class_revision=int(str(stored["to_class_revision"])),
    )


def _teacher_of_class(db: Session, organization_id: str, subject: str, class_id: str) -> bool:
    """An active class-scoped `teacher` row (as `create_profile`: org-wide, guide, observer no)."""
    return (
        db.scalar(
            select(OrganizationAssignmentModel.assignment_id)
            .where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.subject == subject,
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            )
            .limit(1)
        )
        is not None
    )


def _holds_unfinished_session_membership(
    db: Session, *, organization_id: str, class_id: str, child_id: str
) -> bool:
    """The child waits in or sits in a session of the class that is not finished (T-7d-DEC-6)."""
    return (
        db.scalar(
            select(SessionMembershipModel.membership_id)
            .join(
                ClassroomSessionModel,
                ClassroomSessionModel.session_id == SessionMembershipModel.session_id,
            )
            .where(
                SessionMembershipModel.organization_id == organization_id,
                SessionMembershipModel.child_id == child_id,
                SessionMembershipModel.state.in_(_MOVE_SESSION_STATES_OPEN),
                ClassroomSessionModel.organization_id == organization_id,
                ClassroomSessionModel.class_id == class_id,
                ClassroomSessionModel.state != "finished",
            )
            .limit(1)
        )
        is not None
    )


@router.post("/classes/{class_id}/profiles/{child_id}/move")
def move_profile(
    class_id: str,
    child_id: str,
    payload: MoveProfileRequest,
    request: Request,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-7d: a Teacher of both classes moves a child; the old enrollment is closed and kept.

    Order: source class in any state (404), Teacher row of the source class (404, or 403 for
    another role), key, `If-Match`, same-class check (400), target class of the same organization
    with a Teacher row of the Teacher (404), both class rows FOR UPDATE in ascending id order,
    receipt replay, stale source then stale target (409), both classes active (409), the profile
    and its active enrollment, the session guard (409), then one transaction.
    """
    source_known = db.scalar(select(ClassroomModel).where(ClassroomModel.class_id == class_id))
    if source_known is None:
        raise _scope_denied()
    organization_id = source_known.organization_id
    assignments = _require_m2_assignment(
        db, principal, organization_id, roles={"teacher"}, class_id=class_id
    )
    if not any(row.class_id == class_id and row.role == "teacher" for row in assignments):
        raise _scope_denied()
    idempotency_key = parse_idempotency_key(request)
    expected_revision = _strong_revision(if_match)
    target_id = payload.target_class_id
    if target_id == class_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "target_class_id", "code": "INVALID_FORMAT"}],
            },
        )
    # The target: the same organization and a Teacher row of this Teacher, else the uniform 404
    # (X-19: a cross-Teacher move is not built, T-7d-DEC-2).
    target_known = db.scalar(
        select(ClassroomModel.class_id).where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.class_id == target_id,
        )
    )
    if target_known is None or not _teacher_of_class(
        db, organization_id, principal.subject, target_id
    ):
        raise _scope_denied()
    settle_due_class_suspensions(db, organization_id, actor=principal.subject)
    # Both class rows FOR UPDATE in ascending id order: A->B and B->A cannot deadlock.
    locked = {cid: db.scalar(class_lock_select(cid)) for cid in sorted((class_id, target_id))}
    source, target = locked[class_id], locked[target_id]
    if source is None or target is None:
        raise _scope_denied()
    scope = _move_receipt_scope(class_id, child_id)
    fingerprint = _move_fingerprint(
        class_id=class_id, child_id=child_id, payload=payload, expected_revision=expected_revision
    )
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        replay = _replayed_move(receipt, fingerprint=fingerprint)
        db.rollback()
        return replay
    if source.revision != expected_revision:
        current = source.revision
        db.rollback()
        raise_stale_revision(current_version=current, etag=str(current))
    if target.revision != payload.target_class_revision:
        current = target.revision
        db.rollback()
        raise_stale_revision(current_version=current, etag=str(current))
    if source.state != "active" or target.state != "active":
        # T-7b: a suspended or archived class is read-only, on either side of the move.
        db.rollback()
        raise failure(
            409, "INVALID_STATE_TRANSITION", "The class is read-only in its current state"
        )
    profile = db.scalar(
        select(ManagedProfileModel)
        .where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.child_id == child_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.state == "active",
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if profile is None:
        db.rollback()
        raise failure(404, "PROFILE_NOT_FOUND", "Profile was not found")
    open_enrollment = db.scalar(
        select(EnrollmentModel)
        .where(
            EnrollmentModel.organization_id == organization_id,
            EnrollmentModel.class_id == class_id,
            EnrollmentModel.child_id == child_id,
            EnrollmentModel.state == "active",
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if open_enrollment is None:
        # No auto-enrollment (SRS l.1093: a profile without one is quarantined).
        db.rollback()
        raise failure(
            409, "INVALID_STATE_TRANSITION", "The profile has no active enrollment in this class"
        )
    if _holds_unfinished_session_membership(
        db, organization_id=organization_id, class_id=class_id, child_id=child_id
    ):
        db.rollback()
        raise failure(
            409, "INVALID_STATE_TRANSITION", "The child is in a session that is not finished"
        )
    # One transaction: close the old enrollment (flush), open the new one, project the class,
    # bump both class revisions (TD-28), audit, event, receipt.
    open_enrollment.state = "withdrawn"
    db.flush()
    new_enrollment = EnrollmentModel(
        enrollment_id=str(uuid4()),
        organization_id=organization_id,
        class_id=target_id,
        child_id=child_id,
        created_by=principal.subject,
    )
    db.add(new_enrollment)
    profile.class_id = target_id
    source.revision += 1
    target.revision += 1
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="profile.move",
        resource_type="child_profile",
        resource_id=child_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=child_id,
        event_type="be1.profile.moved.v1",
        payload={"child_id": child_id, "from_class_id": class_id, "to_class_id": target_id},
    )
    body = _move_body(
        child_id=child_id,
        from_class_id=class_id,
        to_class_id=target_id,
        enrollment_id=new_enrollment.enrollment_id,
        from_class_revision=source.revision,
        to_class_revision=target.revision,
    )
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
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first (its move stands), or the
        # one-active-enrollment index refused the write: this transaction is rolled back.
        db.rollback()
        winner = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if winner is None:
            raise failure(
                409, "RESOURCE_CONFLICT", "The command conflicts with current records"
            ) from None
        replay = _replayed_move(winner, fingerprint=fingerprint)
        db.rollback()
        return replay
    return body


# --- FEAT-066 goal v4 T-12b: Teacher profile revisions and edit ------------------------------
# SRS l.496-499 (FR-C-04 to FR-C-07), l.829 (head and ownership), l.832 (consent covers real data
# only), l.1651 and l.1697 (expected revision, keyed commands), l.864-865 (uniform 404), l.2586
# (a Teacher reads only the fields granted once the class is assigned). One predicate for the
# three routes, identical to the roster of D-066-100: an assigned class Teacher and a profile that
# is `SYNTHETIC_DEV`, or `REAL` with an effective consent. Real-data writes stay blocked (owner
# default C4: the purge of revisions and receipts is not reviewed yet), so a write to a `REAL`
# profile also needs `real_profile_data_enabled`.
_PROFILE_EDIT_FP_DOMAIN = "be1.profile.edit.receipt"
_PROFILE_EDIT_FP_VERSION = 1


def _edit_receipt_scope(organization_id: str, class_id: str, child_id: str) -> str:
    """`PATCH /organizations/{org}/classes/{class}/profiles/{child}`, hashed only if too long."""
    scope = f"PATCH /organizations/{organization_id}/classes/{class_id}/profiles/{child_id}"
    if len(scope) <= _RECEIPT_SCOPE_LIMIT:
        return scope
    digest = hashlib.sha256(f"{organization_id}/{class_id}/{child_id}".encode()).hexdigest()
    return f"PATCH /organizations/classes/profiles#{digest}"


def _edit_fingerprint(
    *,
    key: bytes,
    principal_ref: str,
    scope: str,
    expected_revision: int,
    patch: dict[str, object],
) -> str:
    """Keyed HMAC-SHA-256 (hex, 64 characters) over actor, resource, revision and the patch.

    The patch holds the child's new name, age or interests, so the value is derived child data
    (FR-C-10): without the server key it cannot be confirmed by guessing, and it is never logged
    or returned. Domain and version live inside the MAC input (the column is 64 characters wide).
    """
    message = json.dumps(
        {
            "domain": _PROFILE_EDIT_FP_DOMAIN,
            "v": _PROFILE_EDIT_FP_VERSION,
            "principal": principal_ref,
            "scope": scope,
            "expected_revision": expected_revision,
            "patch": patch,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _revision_view(row: ProfileRevisionModel) -> dict[str, object]:
    """The answer for one revision; no author, no database key beyond the opaque ids."""
    return {
        "contract": "Be1ProfileRevisionV1",
        "child_id": row.child_id,
        "profile_revision_id": row.profile_revision_id,
        "revision_no": row.revision_no,
        "display_name": row.display_name,
        "age_months": row.age_months,
        "age_band": (
            None
            if row.age_band_code is None or row.age_band_version is None
            else {"band_version": row.age_band_version, "band_code": row.age_band_code}
        ),
        "structured_interests": list(row.structured_interests),
        "revision_hash": row.revision_hash,
        "created_at": row.created_at,
    }


def _edit_result(row: ProfileRevisionModel) -> dict[str, object]:
    return {
        "contract": "Be1ProfileEditResultV1",
        "child_id": row.child_id,
        "profile_revision_id": row.profile_revision_id,
        "revision_no": row.revision_no,
        "revision_hash": row.revision_hash,
    }


def _require_profile_teacher(
    db: Session, principal: VerifiedPrincipal, organization_id: str, class_id: str
) -> None:
    """The class exists (404), the caller is an active class-scoped Teacher (403 or 404).

    As `create_profile`: a School Manager is 403, and an org-wide `teacher` row, a guide or an
    observer is the uniform 404.
    """
    known = db.scalar(
        select(ClassroomModel.class_id).where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.class_id == class_id,
        )
    )
    if known is None:
        raise _scope_denied()
    assignments = _require_m2_assignment(
        db, principal, organization_id, roles={"teacher"}, class_id=class_id
    )
    if not any(row.class_id == class_id and row.role == "teacher" for row in assignments):
        raise _scope_denied()


def _profile_released(
    db: Session, profile: ManagedProfileModel, *, for_write: bool, real_data_enabled: bool
) -> bool:
    """Option B of D-066-100: synthetic, or `REAL` with an effective consent (writes: flag too)."""
    if profile.data_origin == "SYNTHETIC_DEV":
        return True
    if profile.data_origin == "REAL":
        if for_write and not real_data_enabled:
            return False
        return consent_is_effective(
            db,
            organization_id=profile.organization_id,
            class_id=profile.class_id,
            child_id=profile.child_id,
            purpose_ref=profile.consent_purpose_ref,
        )
    return False


def _profile_withdrawn(db: Session, profile: ManagedProfileModel) -> bool:
    """True when access was withdrawn: a deletion is pending, or a non-synthetic consent is revoked.

    SRS l.867, AC-27, FR-C-10 and UC-09 (owner decision Q3, 2026-11-23): a Teacher whose access
    to the profile ended learns nothing, so the caller answers the uniform 404 (no audit row).
    A pending deletion is a ``delete`` lifecycle request that is not completed and whose
    ``target_ref`` is the child, the class or the organization (the predicate of the candidate
    selection; ``exception`` counts too, as there). A revoked consent matters only for a profile
    that is not synthetic, and only when the newest record of its own purpose is the revoke.
    """
    pending_deletion = db.scalar(
        select(
            exists().where(
                DataLifecycleRequestModel.request_type == "delete",
                DataLifecycleRequestModel.state != "completed",
                DataLifecycleRequestModel.target_ref.in_(
                    (profile.child_id, profile.class_id, profile.organization_id)
                ),
            )
        )
    )
    if pending_deletion:
        return True
    if profile.data_origin == "SYNTHETIC_DEV":
        return False
    if profile.consent_purpose_ref is None:
        return False
    # Only the newest record of the profile's own consent purpose counts: a revoke of another
    # purpose, or one that a later record superseded, hides nothing.
    latest = db.scalar(
        select(ConsentRecordModel.state)
        .where(
            ConsentRecordModel.organization_id == profile.organization_id,
            ConsentRecordModel.class_id == profile.class_id,
            ConsentRecordModel.child_id == profile.child_id,
            ConsentRecordModel.purpose_ref == profile.consent_purpose_ref,
        )
        .order_by(ConsentRecordModel.recorded_at.desc(), ConsentRecordModel.state.desc())
        .limit(1)
    )
    return latest == "revoked"


def _read_released_profile(
    db: Session,
    principal: VerifiedPrincipal,
    organization_id: str,
    class_id: str,
    child_id: str,
) -> ManagedProfileModel:
    """Scope, class visibility, the active profile of this class, then the release predicate."""
    _require_profile_teacher(db, principal, organization_id, class_id)
    # An archived class is gone for a Teacher (T-7b-DEC-6); a suspended one is readable.
    assignments = require_assignment(db, principal, organization_id, class_id=class_id)
    hide_archived_from_teacher(get_class(db, organization_id, class_id, write=False), assignments)
    profile = db.scalar(
        select(ManagedProfileModel).where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.child_id == child_id,
            ManagedProfileModel.state == "active",
        )
    )
    if profile is None or _profile_withdrawn(db, profile):
        db.rollback()
        raise _scope_denied()
    if not _profile_released(db, profile, for_write=False, real_data_enabled=False):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="child_profile",
            resource_id=child_id,
            action="profile.revisions.read",
        )
    return profile


@router.get(
    "/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/revisions",
    response_model=Be1ProfileRevisionPageV1,
)
def list_profile_revisions(
    organization_id: str,
    class_id: str,
    child_id: str,
    limit: int = limit_query(),
    cursor: str | None = cursor_query(),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-12b: the immutable revisions of one profile, newest first, keyset-paged (SRS l.1640).

    The first item is the head, so a client learns the revision number to send as
    `expected_revision`. The cursor is decoded only after the scope checks.
    """
    _read_released_profile(db, principal, organization_id, class_id, child_id)
    scope = _REVISION_CURSOR_SCOPE.format(
        organization_id=organization_id, class_id=class_id, child_id=child_id
    )
    statement = select(ProfileRevisionModel).where(ProfileRevisionModel.child_id == child_id)
    if cursor is not None:
        sort_key, after_id = decode_cursor(cursor, scope=scope)
        if not (sort_key.isascii() and sort_key.isdigit() and 1 <= int(sort_key) <= 2**31 - 1):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_REQUEST",
                    "field_errors": [{"field": "cursor", "code": "INVALID_FORMAT"}],
                },
            )
        statement = statement.where(
            tuple_(ProfileRevisionModel.revision_no, ProfileRevisionModel.profile_revision_id)
            < (int(sort_key), after_id)
        )
    rows = list(
        db.scalars(
            statement.order_by(
                ProfileRevisionModel.revision_no.desc(),
                ProfileRevisionModel.profile_revision_id.desc(),
            ).limit(limit + 1)
        ).all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "contract": "Be1ProfileRevisionPageV1",
        "items": [_revision_view(row) for row in rows],
        "next_cursor": (
            encode_cursor(
                scope=scope,
                sort_key=str(rows[-1].revision_no),
                item_id=rows[-1].profile_revision_id,
            )
            if has_more and rows
            else None
        ),
    }


@router.get(
    "/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}"
    "/revisions/{profile_revision_id}",
    response_model=Be1ProfileRevisionV1,
)
def get_profile_revision(
    organization_id: str,
    class_id: str,
    child_id: str,
    profile_revision_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-12b: one revision. The current scope and release predicate hold for a past revision too."""
    _read_released_profile(db, principal, organization_id, class_id, child_id)
    row = db.scalar(
        select(ProfileRevisionModel).where(
            ProfileRevisionModel.child_id == child_id,
            ProfileRevisionModel.profile_revision_id == profile_revision_id,
        )
    )
    if row is None:
        raise _scope_denied()
    return _revision_view(row)


def _replayed_edit(
    db: Session,
    receipt: Be1CommandReceiptModel,
    *,
    fingerprint: str,
    key_id: str,
    child_id: str,
    response: Response,
) -> dict[str, object]:
    """The stored first answer, rebuilt from the immutable revision the receipt names.

    A receipt of another format version or key id, or with another fingerprint, never matches:
    400 `INVALID_IDEMPOTENCY_KEY`. The receipt holds ids only; a revision that is gone (a future
    purge) fails closed with the uniform 404.
    """
    stored = receipt.response_json
    same_request = (
        stored.get("fp_v") == _PROFILE_EDIT_FP_VERSION
        and stored.get("fp_kid") == key_id
        and hmac.compare_digest(
            receipt.request_fingerprint.encode("ascii", "replace"), fingerprint.encode("ascii")
        )
    )
    if not same_request:
        raise failure(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    revision = db.scalar(
        select(ProfileRevisionModel).where(
            ProfileRevisionModel.child_id == child_id,
            ProfileRevisionModel.profile_revision_id == str(stored.get("profile_revision_id")),
        )
    )
    if revision is None:
        raise _scope_denied()
    response.headers["ETag"] = f'"{revision.revision_no}"'
    return _edit_result(revision)


@router.patch(
    "/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}",
    response_model=Be1ProfileEditResultV1,
)
def edit_profile(
    organization_id: str,
    class_id: str,
    child_id: str,
    payload: EditProfileRequest,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-12b: a keyed Teacher edit that appends one immutable revision (SRS l.497, l.829, l.1697).

    Order: class (404), class Teacher (403/404), key (400), class active (409), the profile row
    FOR UPDATE (uniform 404, also when access is withdrawn: a pending deletion or a revoked
    consent), the release predicate (409), the over-age quarantine (409), the
    receipt key (503), receipt replay, stale `expected_revision` (409), then one transaction:
    revision, projection and head, audit, receipt. Authorization and state are rechecked before a
    replay, so a revoked assignment never replays.
    """
    _require_profile_teacher(db, principal, organization_id, class_id)
    idempotency_key = parse_idempotency_key(request)
    get_class(db, organization_id, class_id, write=True)  # FOR SHARE; 409 unless active
    profile = db.scalar(
        select(ManagedProfileModel)
        .where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.child_id == child_id,
            ManagedProfileModel.state == "active",
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if profile is None or _profile_withdrawn(db, profile):
        db.rollback()
        raise _scope_denied()
    if not _profile_released(
        db,
        profile,
        for_write=True,
        real_data_enabled=runtime.settings.real_profile_data_enabled,
    ):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="child_profile",
            resource_id=child_id,
            action="profile.edit",
        )
    if profile.age_months > MAX_EDIT_AGE_MONTHS:
        # A legacy age above 120 months is kept as it is and read-only (AC-62, AC-66).
        db.rollback()
        raise failure(409, "INVALID_STATE_TRANSITION", "The profile is read-only")
    try:
        key = _profile_receipt_key(runtime)  # fail closed (503) before a write
    except HTTPException:
        db.rollback()
        raise
    patch: dict[str, object] = {
        name: getattr(payload, name)
        for name in ("display_name", "age_months", "structured_interests")
        if name in payload.model_fields_set
    }
    scope = _edit_receipt_scope(organization_id, class_id, child_id)
    fingerprint = _edit_fingerprint(
        key=key,
        principal_ref=principal.subject,
        scope=scope,
        expected_revision=payload.expected_revision,
        patch=patch,
    )
    key_id = _profile_key_id(key)
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        try:
            replay = _replayed_edit(
                db, receipt, fingerprint=fingerprint, key_id=key_id, child_id=child_id,
                response=response,
            )
        except HTTPException:
            db.rollback()
            raise
        db.rollback()
        return replay
    head_no = profile.profile_revision_no
    if payload.expected_revision != head_no:
        db.rollback()
        raise_stale_revision(current_version=head_no, etag=str(head_no))
    head = db.scalar(
        select(ProfileRevisionModel).where(
            ProfileRevisionModel.child_id == child_id,
            ProfileRevisionModel.profile_revision_id == profile.current_profile_revision_id,
        )
    )
    if head is None:  # the database guarantees a head; fail closed rather than write
        db.rollback()
        raise failure(409, "RESOURCE_CONFLICT", "The command conflicts with current records")
    new_name = payload.display_name if payload.display_name is not None else head.display_name
    new_age = payload.age_months if payload.age_months is not None else head.age_months
    new_interests = (
        payload.structured_interests
        if payload.structured_interests is not None
        else list(head.structured_interests)
    )
    band = age_band(new_age)
    revision_no = head_no + 1
    revision = ProfileRevisionModel(
        profile_revision_id=str(uuid4()),
        child_id=child_id,
        revision_no=revision_no,
        display_name=new_name,
        age_months=new_age,
        age_band_version=None if band is None else BAND_VERSION,
        age_band_code=None if band is None else band[1],
        structured_interests=new_interests,
        authored_by=principal.subject,
        revision_hash_version=HASH_VERSION,
        revision_hash=revision_hash(
            child_id=child_id,
            revision_no=revision_no,
            display_name=new_name,
            age_months=new_age,
            structured_interests=new_interests,
        ),
    )
    db.add(revision)
    # The projection of the head, in the same transaction. `age_revision` moves in the same
    # UPDATE whenever the age changes (the age invariant of FR-C-05).
    profile.display_name = new_name
    if new_age != profile.age_months:
        profile.age_months = new_age
        profile.age_revision = profile.age_revision + 1
    profile.current_profile_revision_id = revision.profile_revision_id
    profile.profile_revision_no = revision_no
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="profile.edit",
        resource_type="child_profile",
        resource_id=child_id,
    )
    body = _edit_result(revision)
    # References only: no name, no age, no interests, no revision hash.
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            request_fingerprint=fingerprint,
            response_json={
                "profile_revision_id": revision.profile_revision_id,
                "fp_v": _PROFILE_EDIT_FP_VERSION,
                "fp_kid": key_id,
            },
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first: its revision stands.
        db.rollback()
        winner = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if winner is None:
            raise failure(
                409, "RESOURCE_CONFLICT", "The command conflicts with current records"
            ) from None
        replay = _replayed_edit(
            db, winner, fingerprint=fingerprint, key_id=key_id, child_id=child_id,
            response=response,
        )
        db.rollback()
        return replay
    response.headers["ETag"] = f'"{revision_no}"'
    return body


# --- FEAT-066 goal v4 T-12c: encrypted support needs of a managed profile ---------------------
# SRS l.264 BR-20, l.499 FR-C-07, l.932, l.1922, l.2338. The Teacher needs the class assignment,
# an effective consent and a narrow permission, for every profile (synthetic ones included, owner
# default C5); the roster rule of option B does not apply here. Both proofs are ports that deny by
# default: `be1_consent_records` has no effective state and the permission store does not exist
# (SRS section 31.10), so the production routes deny every Teacher and, without a key source
# (gate O-SEED-KEY), answer 503. A School Manager is 403 and an org-wide `teacher` row, a guide or
# an observer is the uniform 404. Nothing here logs, audits or echoes a value.
_SUPPORT_FP_VERSION = 1


class DefaultTeacherSupportNeedsGuard:
    """Production default: the existing consent lookup, and a permission that nobody holds."""

    def consent_effective(self, db: Session, profile: ManagedProfileModel) -> bool:
        return consent_is_effective(
            db,
            organization_id=profile.organization_id,
            class_id=profile.class_id,
            child_id=profile.child_id,
            purpose_ref=profile.consent_purpose_ref,
        )

    def permission_granted(
        self, db: Session, principal: VerifiedPrincipal, profile: ManagedProfileModel
    ) -> bool:
        return False


def _support_unavailable() -> HTTPException:
    return failure(503, "SUPPORT_NEEDS_UNAVAILABLE", "Support needs are unavailable")


def _support_receipt_scope(organization_id: str, class_id: str, child_id: str) -> str:
    """`PUT .../support-needs`, hashed with the pattern of `_move_receipt_scope` if too long."""
    scope = (
        f"PUT /organizations/{organization_id}/classes/{class_id}/profiles/{child_id}"
        "/support-needs"
    )
    if len(scope) <= _RECEIPT_SCOPE_LIMIT:
        return scope
    digest = hashlib.sha256(f"{organization_id}/{class_id}/{child_id}".encode()).hexdigest()
    return f"PUT /organizations/classes/profiles/support-needs#{digest}"


def _support_principal_ref(principal: VerifiedPrincipal) -> str:
    return hashlib.sha256(f"{principal.issuer}\n{principal.subject}".encode()).hexdigest()


def _authorized_support_profile(
    db: Session,
    principal: VerifiedPrincipal,
    organization_id: str,
    class_id: str,
    child_id: str,
    runtime: SupportNeedsRuntime,
    *,
    write: bool,
) -> tuple[ManagedProfileModel, SupportNeedsCrypto]:
    """Every proof, in order; a failure leaves nothing open. The profile row is locked on write."""
    guard = runtime.teacher_guard or DefaultTeacherSupportNeedsGuard()
    action = "profile.support_needs.write" if write else "profile.support_needs.read"
    _require_profile_teacher(db, principal, organization_id, class_id)
    assignments = require_assignment(db, principal, organization_id, class_id=class_id)
    if write:
        get_class(db, organization_id, class_id, write=True)  # FOR SHARE; 409 unless active
    else:
        hide_archived_from_teacher(
            get_class(db, organization_id, class_id, write=False), assignments
        )
    statement = select(ManagedProfileModel).where(
        ManagedProfileModel.organization_id == organization_id,
        ManagedProfileModel.class_id == class_id,
        ManagedProfileModel.child_id == child_id,
        ManagedProfileModel.state == "active",
    )
    if write:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    profile = db.scalar(statement)
    if profile is None or _profile_withdrawn(db, profile):
        db.rollback()
        raise _scope_denied()
    # Permission before consent: a Teacher without the narrow permission never learns the consent
    # state and writes no audit row (T-12c review P3-3; owner decision Q3).
    if not guard.permission_granted(db, principal, profile):
        db.rollback()
        raise _scope_denied()
    if not guard.consent_effective(db, profile):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="child_profile",
            resource_id=child_id,
            action=action,
        )
    if runtime.crypto is None:
        db.rollback()
        raise _support_unavailable()
    return profile, runtime.crypto


@router.get(
    "/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/support-needs",
    response_model=Be1SupportNeedsV1,
)
def get_profile_support_needs(
    organization_id: str,
    class_id: str,
    child_id: str,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    support_runtime: SupportNeedsRuntime = Depends(get_support_needs_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-12c: the decrypted record of one profile (revision 0 and null values when none)."""
    _profile, crypto = _authorized_support_profile(
        db, principal, organization_id, class_id, child_id, support_runtime, write=False
    )
    try:
        revision, payload = Be1SupportNeedsStore(db).read(
            crypto=crypto, organization_id=organization_id, child_id=child_id
        )
    except SupportNeedsUnavailable:
        db.rollback()
        raise _support_unavailable() from None
    response.headers["Cache-Control"] = "private, no-store"
    return {
        "contract": "Be1SupportNeedsV1",
        "child_id": child_id,
        "revision": revision,
        "category": None if payload is None else payload.category,
        "note": None if payload is None else payload.note,
    }


def _replayed_support_write(
    receipt: Be1CommandReceiptModel,
    *,
    crypto: SupportNeedsCrypto,
    organization_id: str,
    child_id: str,
    principal: VerifiedPrincipal,
    payload: SupportNeedsPayload,
    expected_revision: int,
) -> dict[str, object]:
    """The stored first answer (ids only), after the fingerprint of the stored key matches."""
    stored = receipt.response_json
    key_id = stored.get("fp_kid")
    revision = stored.get("revision")
    if (
        stored.get("fp_v") != _SUPPORT_FP_VERSION
        or not isinstance(key_id, str)
        or type(revision) is not int
    ):
        raise failure(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    try:
        expected = crypto.fingerprint(
            family="be1",
            tenant=organization_id,
            profile_id=child_id,
            principal=_support_principal_ref(principal),
            expected_revision=expected_revision,
            payload=payload,
            key_id=key_id,
        ).hex()
    except SupportNeedsUnavailable:
        raise _support_unavailable() from None
    if not hmac.compare_digest(
        receipt.request_fingerprint.encode("ascii", "replace"), expected.encode("ascii")
    ):
        raise failure(
            400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request"
        )
    return {"contract": "Be1SupportNeedsWriteV1", "child_id": child_id, "revision": revision}


@router.put(
    "/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/support-needs",
    response_model=Be1SupportNeedsWriteV1,
)
def put_profile_support_needs(
    organization_id: str,
    class_id: str,
    child_id: str,
    payload: Be1SupportNeedsPutV1,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    support_runtime: SupportNeedsRuntime = Depends(get_support_needs_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """T-12c: replace the encrypted record of one profile, keyed and revision-checked.

    Order: class (404), class Teacher (403/404), key (400), class active (409), the profile row
    FOR UPDATE (uniform 404, also when access is withdrawn), permission (404, no audit), consent
    (409, audited), key source (503), receipt replay,
    stale `expected_revision` (409, not receipted), then one transaction: seal and upsert, audit
    (no value), receipt, commit. Every proof is rechecked under the row lock before a replay.
    """
    _require_profile_teacher(db, principal, organization_id, class_id)
    idempotency_key = parse_idempotency_key(request)
    _profile, crypto = _authorized_support_profile(
        db, principal, organization_id, class_id, child_id, support_runtime, write=True
    )
    value = SupportNeedsPayload(category=payload.category, note=payload.note)
    scope = _support_receipt_scope(organization_id, class_id, child_id)
    principal_ref = _support_principal_ref(principal)
    try:
        fingerprint = crypto.fingerprint(
            family="be1",
            tenant=organization_id,
            profile_id=child_id,
            principal=principal_ref,
            expected_revision=payload.expected_revision,
            payload=value,
        ).hex()
    except SupportNeedsUnavailable:
        db.rollback()
        raise _support_unavailable() from None
    receipt = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
    if receipt is not None:
        try:
            replay = _replayed_support_write(
                receipt,
                crypto=crypto,
                organization_id=organization_id,
                child_id=child_id,
                principal=principal,
                payload=value,
                expected_revision=payload.expected_revision,
            )
        finally:
            db.rollback()
        response.headers["Cache-Control"] = "private, no-store"
        return replay
    store = Be1SupportNeedsStore(db)
    try:
        revision = store.write(
            crypto=crypto,
            organization_id=organization_id,
            child_id=child_id,
            expected_revision=payload.expected_revision,
            payload=value,
        )
    except SupportNeedsStale as stale:
        db.rollback()
        raise_stale_revision(current_version=stale.current_version)
    except (SupportNeedsUnavailable, IntegrityError):
        db.rollback()
        raise _support_unavailable() from None
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="profile.support_needs.write",
        resource_type="child_profile",
        resource_id=child_id,
    )
    # References only: the new revision and the MAC key, never a name, a note or a digest of one.
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal.subject,
            operation_scope=scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            request_fingerprint=fingerprint,
            response_json={
                "revision": revision,
                "fp_v": _SUPPORT_FP_VERSION,
                "fp_kid": crypto.fingerprint_key_id,
            },
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first: its answer stands.
        db.rollback()
        winner = db.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key))
        if winner is None:
            raise failure(
                409, "RESOURCE_CONFLICT", "The command conflicts with current records"
            ) from None
        try:
            replay = _replayed_support_write(
                winner,
                crypto=crypto,
                organization_id=organization_id,
                child_id=child_id,
                principal=principal,
                payload=value,
                expected_revision=payload.expected_revision,
            )
        finally:
            db.rollback()
        response.headers["Cache-Control"] = "private, no-store"
        return replay
    response.headers["Cache-Control"] = "private, no-store"
    return {"contract": "Be1SupportNeedsWriteV1", "child_id": child_id, "revision": revision}


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
    get_class(db, organization_id, class_id)  # T-7b-DEC-5: a write; read-only class is 409
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
    limit: int = limit_query(),
    cursor: str | None = cursor_query(),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assignments = require_assignment(db, principal, organization_id, class_id=class_id)
    hide_archived_from_teacher(get_class(db, organization_id, class_id, write=False), assignments)
    # T-7a (D-066-75 CM-4, CM-11): the Manager list carries no child_id and no purpose_ref;
    # a Teacher sees them only for a class this Teacher is assigned to.
    audience = _roster_audience(assignments, class_id)
    scope = _CONSENT_CURSOR_SCOPE.format(organization_id=organization_id, class_id=class_id)
    statement = select(ConsentRecordModel).where(
        ConsentRecordModel.organization_id == organization_id,
        ConsentRecordModel.class_id == class_id,
    )
    if cursor is not None:
        after_time, after_id = decode_time_cursor(cursor, scope=scope)
        statement = statement.where(
            tuple_(ConsentRecordModel.recorded_at, ConsentRecordModel.consent_id)
            < (after_time, after_id)
        )
    rows = list(
        db.scalars(
            statement.order_by(
                ConsentRecordModel.recorded_at.desc(), ConsentRecordModel.consent_id.desc()
            ).limit(limit + 1)
        ).all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = (
        encode_cursor(
            scope=scope, sort_key=rows[-1].recorded_at.isoformat(), item_id=rows[-1].consent_id
        )
        if has_more and rows
        else None
    )
    if audience == "manager":
        return {
            "contract": "Be1ConsentListManagerV1",
            "items": [
                {"consent_id": row.consent_id, "state": row.state, "effective": False}
                for row in rows
            ],
            "next_cursor": next_cursor,
        }
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
        "next_cursor": next_cursor,
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
