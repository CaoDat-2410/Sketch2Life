"""Seed class lifecycle, keyed synthetic profiles and one enrollment move for S9."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, cast

from sqlalchemy import Connection, Engine, and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest, MoveProfileRequest
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from tools.seed import data
from tools.seed.s9_classes_data import (
    CLASS_STATES,
    EXPECTED,
    MOVE_FROM_CLASS_NUMBER,
    MOVE_TO_CLASS_NUMBER,
    MOVED_CHILD_ID,
    PROFILE_CREATE_CHILD_IDS,
    ClassStateSpec,
    audit_id,
    class_assignment_event_id,
    class_assignment_id,
    class_assignment_key,
    class_assignment_scope,
    class_state_event_id,
    class_state_key,
    class_state_scope,
    keyed_profile_rows,
    lifecycle_profile_rows,
    move_enrollment_id,
    move_event_id,
    move_key,
    move_scope,
    profile_create_key,
    profile_create_scope,
    profile_event_id,
    stage_enrollment_id,
)
from tools.seed.stage_common import StageError, StageResult, run_stage_main, seed_principal

PROFILE_RECEIPT_VERSION = 2
PROFILE_RECEIPT_DOMAIN = "be1.profile.create.receipt"
PROFILE_RECEIPT_KEY_ID_DOMAIN = b"be1.profile.create.receipt.key-id"


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _state_fingerprint(command: str, expected_revision: int) -> str:
    return _canonical_sha256({"command": command, "if_match": expected_revision})


def _assignment_fingerprint(candidate_ref: str, expected_revision: int) -> str:
    return _canonical_sha256({"candidate_ref": candidate_ref, "if_match": expected_revision})


def _profile_receipt_key() -> bytes:
    configured = get_settings().profile_receipt_hmac_key
    if configured is None:
        raise StageError("S9_PROFILE_RECEIPT_KEY_MISSING")
    key = configured.get_secret_value().encode("utf-8")
    if len(key) < 32:
        raise StageError("S9_PROFILE_RECEIPT_KEY_INVALID")
    return key


def _profile_key_id(key: bytes) -> str:
    return hmac.new(key, PROFILE_RECEIPT_KEY_ID_DOMAIN, hashlib.sha256).hexdigest()[:8]


def _profile_fingerprint(
    *, key: bytes, subject: str, scope: str, payload: CreateProfileRequest, expected_revision: int
) -> str:
    message = json.dumps(
        {
            "domain": PROFILE_RECEIPT_DOMAIN,
            "v": PROFILE_RECEIPT_VERSION,
            "principal": subject,
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


def _move_fingerprint(
    *, class_id: str, child_id: str, payload: MoveProfileRequest, expected_revision: int
) -> str:
    return _canonical_sha256(
        {
            "v": 1,
            "command": "profile.move",
            "class_id": class_id,
            "child_id": child_id,
            "target_class_id": payload.target_class_id,
            "target_class_revision": payload.target_class_revision,
            "if_match": expected_revision,
        }
    )


def _add_audit(
    session: Session,
    *,
    key: str,
    organization_id: str,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str,
) -> None:
    session.execute(
        pg_insert(CoreAuditEntryModel)
        .values(
            audit_id=audit_id(key),
            organization_id=organization_id,
            actor_ref=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision="allowed",
        )
        .on_conflict_do_nothing(index_elements=[CoreAuditEntryModel.audit_id])
    )


def _add_event(
    session: Session,
    *,
    event_id: str,
    organization_id: str,
    aggregate_id: str,
    event_type: str,
    payload: dict[str, str],
    revision: int | None = None,
) -> None:
    aggregate = session.get(CoreAggregateRevisionModel, aggregate_id)
    if aggregate is None:
        next_revision = revision or 1
        session.execute(
            pg_insert(CoreAggregateRevisionModel)
            .values(
                aggregate_id=aggregate_id,
                organization_id=organization_id,
                revision=next_revision,
            )
            .on_conflict_do_nothing(index_elements=[CoreAggregateRevisionModel.aggregate_id])
        )
    else:
        if aggregate.organization_id != organization_id:
            raise StageError("S9_EVENT_SCOPE_CONFLICT")
        next_revision = revision if revision is not None else int(aggregate.revision) + 1
        changed = cast(
            CursorResult[Any],
            session.execute(
                update(CoreAggregateRevisionModel)
                .where(
                    CoreAggregateRevisionModel.aggregate_id == aggregate_id,
                    CoreAggregateRevisionModel.revision == aggregate.revision,
                )
                .values(revision=next_revision)
            ),
        )
        if changed.rowcount != 1:
            raise StageError("S9_EVENT_REVISION_CONFLICT")
    session.execute(
        pg_insert(CoreOutboxEventModel)
        .values(
            event_id=event_id,
            event_type=event_type,
            organization_id=organization_id,
            aggregate_id=aggregate_id,
            aggregate_revision=next_revision,
            payload=payload,
            status="pending",
            attempt_count=0,
        )
        .on_conflict_do_nothing(index_elements=[CoreOutboxEventModel.event_id])
    )


def _class_state_expected_revision(class_spec: ClassStateSpec) -> int:
    return 2 if class_spec.class_number == 6 else 1


def _ensure_class_row(session_factory: sessionmaker[Session], class_spec: ClassStateSpec) -> None:
    class_id = data.class_id("a", class_spec.class_number)
    session = session_factory()
    try:
        with session.begin():
            session.execute(
                pg_insert(ClassroomModel)
                .values(
                    class_id=class_id,
                    organization_id=data.org_id("a"),
                    display_name=data.class_display_name("a", class_spec.class_number),
                    state="active",
                    revision=1,
                    created_by=data.manager_subject("a"),
                )
                .on_conflict_do_nothing(index_elements=[ClassroomModel.class_id])
            )
    except Exception:
        session.rollback()
        raise StageError("S9_CLASS_INSERT_FAILED") from None
    finally:
        session.close()


def _ensure_class_assignment(
    session_factory: sessionmaker[Session], class_spec: ClassStateSpec
) -> None:
    class_id = data.class_id("a", class_spec.class_number)
    manager = seed_principal(data.manager_subject("a"))
    teacher_subject = data.ORG_A_TEACHERS[1]
    teacher = next(row for row in data.adult_rows() if row["subject"] == teacher_subject)
    candidate_ref = str(teacher["account_id"])
    scope = class_assignment_scope(class_id)
    key = class_assignment_key(class_id)
    fingerprint = _assignment_fingerprint(candidate_ref, expected_revision=1)
    body = {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": class_assignment_id(class_id),
        "candidate_ref": candidate_ref,
        "role": "teacher",
        "class_id": class_id,
        "active": True,
        "assignment_revision": 2,
    }
    session = session_factory()
    try:
        with session.begin():
            receipt = session.get(Be1CommandReceiptModel, (manager.subject, scope, key))
            if receipt is not None:
                return
            classroom = session.get(ClassroomModel, class_id)
            if classroom is None or classroom.state != "active" or classroom.revision != 1:
                raise StageError("S9_CLASS_ASSIGNMENT_STATE_CONFLICT")
            current_teachers = int(
                session.scalar(
                    select(func.count())
                    .select_from(OrganizationAssignmentModel)
                    .where(
                        OrganizationAssignmentModel.organization_id == data.org_id("a"),
                        OrganizationAssignmentModel.class_id == class_id,
                        OrganizationAssignmentModel.role == "teacher",
                    )
                )
                or 0
            )
            if current_teachers != 0:
                raise StageError("S9_CLASS_ASSIGNMENT_EXISTS")
            identity = session.get(AdultIdentityModel, teacher_subject)
            if identity is None or identity.state != "active" or identity.account_role != "teacher":
                raise StageError("S9_TEACHER_IDENTITY_MISSING")
            assignment_id = class_assignment_id(class_id)
            session.add(
                OrganizationAssignmentModel(
                    assignment_id=assignment_id,
                    organization_id=data.org_id("a"),
                    subject=teacher_subject,
                    class_id=class_id,
                    role="teacher",
                    active=True,
                    pending_activation=False,
                )
            )
            updated = cast(
                CursorResult[Any],
                session.execute(
                    update(ClassroomModel)
                    .where(ClassroomModel.class_id == class_id, ClassroomModel.revision == 1)
                    .values(revision=2)
                ),
            )
            if updated.rowcount != 1:
                raise StageError("S9_CLASS_ASSIGNMENT_REVISION_CONFLICT")
            _add_audit(
                session,
                key=f"assignment:{class_id}",
                organization_id=data.org_id("a"),
                actor=manager.subject,
                action="identity.assignment.create",
                resource_type="adult_assignment",
                resource_id=assignment_id,
            )
            _add_event(
                session,
                event_id=class_assignment_event_id(class_id),
                organization_id=data.org_id("a"),
                aggregate_id=data.org_id("a"),
                event_type="be1.identity.assignment_created.v1",
                payload={"assignment_id": assignment_id, "role": "teacher"},
            )
            session.add(
                Be1CommandReceiptModel(
                    principal_ref=manager.subject,
                    operation_scope=scope,
                    idempotency_key=key,
                    organization_id=data.org_id("a"),
                    request_fingerprint=fingerprint,
                    response_json=body,
                )
            )
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S9_CLASS_ASSIGNMENT_FAILED") from None
    finally:
        session.close()


def _ensure_lifecycle_profiles(session_factory: sessionmaker[Session]) -> None:
    profiles = lifecycle_profile_rows()
    session = session_factory()
    try:
        with session.begin():
            for profile in profiles:
                session.execute(
                    pg_insert(ManagedProfileModel)
                    .values(**profile)
                    .on_conflict_do_nothing(index_elements=[ManagedProfileModel.child_id])
                )
                session.execute(
                    pg_insert(EnrollmentModel)
                    .values(
                        enrollment_id=stage_enrollment_id(profile["child_id"]),
                        organization_id=profile["organization_id"],
                        class_id=profile["class_id"],
                        child_id=profile["child_id"],
                        state="active",
                        created_by=profile["created_by"],
                    )
                    .on_conflict_do_nothing(index_elements=[EnrollmentModel.enrollment_id])
                )
    except Exception:
        session.rollback()
        raise StageError("S9_LIFECYCLE_PROFILE_INSERT_FAILED") from None
    finally:
        session.close()


def _ensure_class_state(session_factory: sessionmaker[Session], class_spec: ClassStateSpec) -> None:
    class_id = data.class_id("a", class_spec.class_number)
    manager = seed_principal(data.manager_subject("a"))
    expected_revision = _class_state_expected_revision(class_spec)
    scope = class_state_scope(class_id, class_spec.command)
    key = class_state_key(class_spec)
    fingerprint = _state_fingerprint(class_spec.command, expected_revision)
    body = {
        "contract": "Be1ClassStateV1",
        "class_id": class_id,
        "state": class_spec.target_state,
        "class_revision": expected_revision + 1,
    }
    session = session_factory()
    try:
        with session.begin():
            receipt = session.get(Be1CommandReceiptModel, (manager.subject, scope, key))
            if receipt is not None:
                return
            classroom = session.get(ClassroomModel, class_id)
            if (
                classroom is None
                or classroom.state != "active"
                or classroom.revision != expected_revision
            ):
                raise StageError("S9_CLASS_STATE_CONFLICT")
            if class_spec.command == "suspend" and classroom.state != "active":
                raise StageError("S9_CLASS_TRANSITION_INVALID")
            if class_spec.command == "archive" and classroom.state not in {"active", "suspended"}:
                raise StageError("S9_CLASS_TRANSITION_INVALID")
            changed = cast(
                CursorResult[Any],
                session.execute(
                    update(ClassroomModel)
                    .where(
                        ClassroomModel.class_id == class_id,
                        ClassroomModel.state == "active",
                        ClassroomModel.revision == expected_revision,
                    )
                    .values(state=class_spec.target_state, revision=expected_revision + 1)
                ),
            )
            if changed.rowcount != 1:
                raise StageError("S9_CLASS_STATE_CONFLICT")
            _add_audit(
                session,
                key=f"class-{class_spec.command}-{class_spec.class_number}",
                organization_id=data.org_id("a"),
                actor=manager.subject,
                action=f"class.{class_spec.command}",
                resource_type="class",
                resource_id=class_id,
            )
            _add_event(
                session,
                event_id=class_state_event_id(class_spec),
                organization_id=data.org_id("a"),
                aggregate_id=class_id,
                event_type=f"be1.class.{class_spec.target_state}.v1",
                payload={
                    "class_id": class_id,
                    "from_state": "active",
                    "to_state": class_spec.target_state,
                },
                revision=expected_revision + 1,
            )
            session.add(
                Be1CommandReceiptModel(
                    principal_ref=manager.subject,
                    operation_scope=scope,
                    idempotency_key=key,
                    organization_id=data.org_id("a"),
                    request_fingerprint=fingerprint,
                    response_json=body,
                )
            )
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S9_CLASS_STATE_FAILED") from None
    finally:
        session.close()


def _ensure_profile_create(
    session_factory: sessionmaker[Session], profile: dict[str, Any], key: bytes
) -> None:
    child_id = str(profile["child_id"])
    subject = data.ORG_A_TEACHERS[0]
    principal = seed_principal(subject)
    scope = profile_create_scope()
    idempotency_key = profile_create_key(child_id)
    payload = CreateProfileRequest(
        display_name=str(profile["display_name"]),
        age_months=int(profile["age_months"]),
        consent_id=None,
    )
    fingerprint = _profile_fingerprint(
        key=key, subject=subject, scope=scope, payload=payload, expected_revision=1
    )
    key_id = _profile_key_id(key)
    enrollment_id = stage_enrollment_id(child_id)
    receipt_body = {
        "child_id": child_id,
        "enrollment_id": enrollment_id,
        "class_revision": 1,
        "data_origin": "SYNTHETIC_DEV",
        "fp_v": PROFILE_RECEIPT_VERSION,
        "fp_kid": key_id,
    }
    session = session_factory()
    try:
        with session.begin():
            if session.get(Be1CommandReceiptModel, (principal.subject, scope, idempotency_key)):
                return
            classroom = session.get(ClassroomModel, data.class_id("a", 1))
            assignment_exists = session.scalar(
                select(OrganizationAssignmentModel.assignment_id).where(
                    OrganizationAssignmentModel.organization_id == data.org_id("a"),
                    OrganizationAssignmentModel.subject == subject,
                    OrganizationAssignmentModel.class_id == data.class_id("a", 1),
                    OrganizationAssignmentModel.role == "teacher",
                    OrganizationAssignmentModel.active.is_(True),
                )
            )
            if (
                classroom is None
                or classroom.state != "active"
                or classroom.revision != 1
                or assignment_exists is None
            ):
                raise StageError("S9_PROFILE_CREATE_SCOPE_CONFLICT")
            session.execute(
                pg_insert(ManagedProfileModel)
                .values(**profile)
                .on_conflict_do_nothing(index_elements=[ManagedProfileModel.child_id])
            )
            session.execute(
                pg_insert(EnrollmentModel)
                .values(
                    enrollment_id=enrollment_id,
                    organization_id=profile["organization_id"],
                    class_id=profile["class_id"],
                    child_id=child_id,
                    state="active",
                    created_by=subject,
                )
                .on_conflict_do_nothing(index_elements=[EnrollmentModel.enrollment_id])
            )
            _add_audit(
                session,
                key=f"profile-enroll:{child_id}",
                organization_id=data.org_id("a"),
                actor=subject,
                action="profile.enroll",
                resource_type="child_profile",
                resource_id=child_id,
            )
            _add_event(
                session,
                event_id=profile_event_id(child_id, "enrolled"),
                organization_id=data.org_id("a"),
                aggregate_id=child_id,
                event_type="be1.profile.enrolled.v1",
                payload={"class_id": data.class_id("a", 1), "child_id": child_id},
            )
            session.add(
                Be1CommandReceiptModel(
                    principal_ref=principal.subject,
                    operation_scope=scope,
                    idempotency_key=idempotency_key,
                    organization_id=data.org_id("a"),
                    request_fingerprint=fingerprint,
                    response_json=receipt_body,
                )
            )
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S9_PROFILE_CREATE_FAILED") from None
    finally:
        session.close()


def _ensure_move(session_factory: sessionmaker[Session]) -> None:
    source_id = data.class_id("a", MOVE_FROM_CLASS_NUMBER)
    target_id = data.class_id("a", MOVE_TO_CLASS_NUMBER)
    organization_id = data.org_id("a")
    subject = data.ORG_A_TEACHERS[0]
    principal = seed_principal(subject)
    payload = MoveProfileRequest(
        target_class_id=target_id,
        target_class_revision=1,
    )
    fingerprint = _move_fingerprint(
        class_id=source_id,
        child_id=MOVED_CHILD_ID,
        payload=payload,
        expected_revision=1,
    )
    enrollment_id = move_enrollment_id()
    body = {
        "contract": "Be1ProfileMoveV1",
        "child_id": MOVED_CHILD_ID,
        "from_class_id": source_id,
        "to_class_id": target_id,
        "enrollment_id": enrollment_id,
        "from_class_revision": 2,
        "to_class_revision": 2,
    }
    session = session_factory()
    try:
        with session.begin():
            if session.get(Be1CommandReceiptModel, (principal.subject, move_scope(), move_key())):
                return
            source = session.get(ClassroomModel, source_id)
            target = session.get(ClassroomModel, target_id)
            if (
                source is None
                or target is None
                or source.state != "active"
                or target.state != "active"
                or source.revision != 1
                or target.revision != 1
            ):
                raise StageError("S9_MOVE_CLASS_CONFLICT")
            for class_id in (source_id, target_id):
                assigned = session.scalar(
                    select(OrganizationAssignmentModel.assignment_id).where(
                        OrganizationAssignmentModel.organization_id == organization_id,
                        OrganizationAssignmentModel.subject == subject,
                        OrganizationAssignmentModel.class_id == class_id,
                        OrganizationAssignmentModel.role == "teacher",
                        OrganizationAssignmentModel.active.is_(True),
                    )
                )
                if assigned is None:
                    raise StageError("S9_MOVE_TEACHER_SCOPE_MISSING")
            profile = session.get(ManagedProfileModel, MOVED_CHILD_ID)
            old_enrollment = session.get(EnrollmentModel, stage_enrollment_id(MOVED_CHILD_ID))
            aggregate = session.get(CoreAggregateRevisionModel, MOVED_CHILD_ID)
            if (
                profile is None
                or profile.organization_id != organization_id
                or profile.class_id != source_id
                or profile.state != "active"
                or old_enrollment is None
                or old_enrollment.state != "active"
                or aggregate is None
                or int(aggregate.revision) != 1
            ):
                raise StageError("S9_MOVE_PROFILE_CONFLICT")
            old_enrollment.state = "withdrawn"
            profile.class_id = target_id
            source_update = cast(
                CursorResult[Any],
                session.execute(
                    update(ClassroomModel)
                    .where(ClassroomModel.class_id == source_id, ClassroomModel.revision == 1)
                    .values(revision=2)
                ),
            )
            target_update = cast(
                CursorResult[Any],
                session.execute(
                    update(ClassroomModel)
                    .where(ClassroomModel.class_id == target_id, ClassroomModel.revision == 1)
                    .values(revision=2)
                ),
            )
            if source_update.rowcount != 1 or target_update.rowcount != 1:
                raise StageError("S9_MOVE_CLASS_REVISION_CONFLICT")
            session.add(
                EnrollmentModel(
                    enrollment_id=enrollment_id,
                    organization_id=organization_id,
                    class_id=target_id,
                    child_id=MOVED_CHILD_ID,
                    state="active",
                    created_by=subject,
                )
            )
            _add_audit(
                session,
                key=f"profile-move:{MOVED_CHILD_ID}",
                organization_id=organization_id,
                actor=subject,
                action="profile.move",
                resource_type="child_profile",
                resource_id=MOVED_CHILD_ID,
            )
            _add_event(
                session,
                event_id=move_event_id(),
                organization_id=organization_id,
                aggregate_id=MOVED_CHILD_ID,
                event_type="be1.profile.moved.v1",
                payload={
                    "child_id": MOVED_CHILD_ID,
                    "from_class_id": source_id,
                    "to_class_id": target_id,
                },
            )
            session.add(
                Be1CommandReceiptModel(
                    principal_ref=principal.subject,
                    operation_scope=move_scope(),
                    idempotency_key=move_key(),
                    organization_id=organization_id,
                    request_fingerprint=fingerprint,
                    response_json=body,
                )
            )
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S9_PROFILE_MOVE_FAILED") from None
    finally:
        session.close()


def _receipt_predicate() -> ColumnElement[bool]:
    clauses = []
    for class_spec in CLASS_STATES:
        class_id = data.class_id("a", class_spec.class_number)
        clauses.append(
            and_(
                Be1CommandReceiptModel.principal_ref == data.manager_subject("a"),
                Be1CommandReceiptModel.operation_scope
                == class_state_scope(class_id, class_spec.command),
                Be1CommandReceiptModel.idempotency_key == class_state_key(class_spec),
            )
        )
    class6_id = data.class_id("a", 6)
    clauses.append(
        and_(
            Be1CommandReceiptModel.principal_ref == data.manager_subject("a"),
            Be1CommandReceiptModel.operation_scope == class_assignment_scope(class6_id),
            Be1CommandReceiptModel.idempotency_key == class_assignment_key(class6_id),
        )
    )
    clauses.extend(
        and_(
            Be1CommandReceiptModel.principal_ref == data.ORG_A_TEACHERS[0],
            Be1CommandReceiptModel.operation_scope == profile_create_scope(),
            Be1CommandReceiptModel.idempotency_key == profile_create_key(child_id),
        )
        for child_id in PROFILE_CREATE_CHILD_IDS
    )
    clauses.append(
        and_(
            Be1CommandReceiptModel.principal_ref == data.ORG_A_TEACHERS[0],
            Be1CommandReceiptModel.operation_scope == move_scope(),
            Be1CommandReceiptModel.idempotency_key == move_key(),
        )
    )
    return or_(*clauses)


def count_s9_rows(connection: Connection) -> dict[str, int]:
    class_ids = [
        data.class_id("a", 1),
        data.class_id("a", 3),
        *(data.class_id("a", spec.class_number) for spec in CLASS_STATES),
    ]
    profile_ids = [row["child_id"] for row in lifecycle_profile_rows()] + list(
        PROFILE_CREATE_CHILD_IDS
    )
    enrollment_ids = [stage_enrollment_id(child_id) for child_id in profile_ids]
    enrollment_ids.append(move_enrollment_id())
    event_ids = [class_state_event_id(spec) for spec in CLASS_STATES]
    event_ids.extend(
        [
            class_assignment_event_id(data.class_id("a", 6)),
            move_event_id(),
        ]
    )
    event_ids.extend(
        profile_event_id(child_id, "enrolled") for child_id in PROFILE_CREATE_CHILD_IDS
    )
    audit_ids = [audit_id(f"class-{spec.command}-{spec.class_number}") for spec in CLASS_STATES]
    audit_ids.append(audit_id(f"assignment:{data.class_id('a', 6)}"))
    audit_ids.extend(
        audit_id(f"profile-enroll:{child_id}") for child_id in PROFILE_CREATE_CHILD_IDS
    )
    audit_ids.append(audit_id(f"profile-move:{MOVED_CHILD_ID}"))
    aggregate_ids = [data.class_id("a", spec.class_number) for spec in CLASS_STATES] + [
        data.org_id("a"),
        *PROFILE_CREATE_CHILD_IDS,
    ]
    assignment_id = class_assignment_id(data.class_id("a", 6))
    return {
        "be1_classrooms": int(
            connection.execute(
                select(func.count())
                .select_from(ClassroomModel)
                .where(ClassroomModel.class_id.in_(class_ids))
            ).scalar_one()
        ),
        "be1_organization_assignments": int(
            connection.execute(
                select(func.count())
                .select_from(OrganizationAssignmentModel)
                .where(OrganizationAssignmentModel.assignment_id == assignment_id)
            ).scalar_one()
        ),
        "be1_managed_profiles": int(
            connection.execute(
                select(func.count())
                .select_from(ManagedProfileModel)
                .where(ManagedProfileModel.child_id.in_(profile_ids))
            ).scalar_one()
        ),
        "be1_enrollments": int(
            connection.execute(
                select(func.count())
                .select_from(EnrollmentModel)
                .where(EnrollmentModel.enrollment_id.in_(enrollment_ids))
            ).scalar_one()
        ),
        "be1_command_receipts": int(
            connection.execute(
                select(func.count()).select_from(Be1CommandReceiptModel).where(_receipt_predicate())
            ).scalar_one()
        ),
        "core_audit_entries": int(
            connection.execute(
                select(func.count())
                .select_from(CoreAuditEntryModel)
                .where(CoreAuditEntryModel.audit_id.in_(audit_ids))
            ).scalar_one()
        ),
        "core_aggregate_revisions": int(
            connection.execute(
                select(func.count())
                .select_from(CoreAggregateRevisionModel)
                .where(CoreAggregateRevisionModel.aggregate_id.in_(aggregate_ids))
            ).scalar_one()
        ),
        "core_outbox_events": int(
            connection.execute(
                select(func.count())
                .select_from(CoreOutboxEventModel)
                .where(CoreOutboxEventModel.event_id.in_(event_ids))
            ).scalar_one()
        ),
    }


def run_s9(engine: Engine) -> StageResult:
    """Seed direct route-equivalent rows with deterministic ids and success receipts."""
    try:
        with engine.connect() as connection:
            before = count_s9_rows(connection)
        session_factory = create_core_session_factory(engine)
        for class_spec in CLASS_STATES:
            _ensure_class_row(session_factory, class_spec)
            if class_spec.class_number == 6:
                _ensure_class_assignment(session_factory, class_spec)
        _ensure_lifecycle_profiles(session_factory)
        for class_spec in CLASS_STATES:
            _ensure_class_state(session_factory, class_spec)
        receipt_key = _profile_receipt_key()
        for profile in keyed_profile_rows():
            _ensure_profile_create(session_factory, profile, receipt_key)
        _ensure_move(session_factory)
        with engine.connect() as connection:
            after = count_s9_rows(connection)
        return StageResult("s9_classes", before, after, EXPECTED)
    except StageError:
        raise
    except SQLAlchemyError:
        raise StageError("S9_DATABASE_ERROR") from None
    except Exception:
        raise StageError("S9_UNEXPECTED_FAILURE") from None


def main() -> int:
    return run_stage_main(run_s9, stage="s9")


if __name__ == "__main__":
    raise SystemExit(main())
