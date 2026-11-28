"""SQLAlchemy adapter for the BE1 Teacher assignment transfer state machine."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import exists, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.teacher_assignment_transfer import (
    TeacherAssignmentTransferCommand,
    TeacherAssignmentTransferError,
    TeacherAssignmentTransferRecord,
    TeacherAssignmentTransferRepository,
    TeacherAssignmentTransferStart,
)
from sketch2life.contracts.schemas.teacher_assignment_transfers import (
    Be1TeacherAssignmentTransferAcceptedV1,
)
from sketch2life.domain.teacher_assignment_transfer import (
    TransferAction,
    TransferState,
    TransferStateError,
    transition,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)

_OPERATION_SCOPE = "POST /classes/{class_id}/assignments"
_PENDING_STATES = (TransferState.TRANSFER_PENDING.value, TransferState.RECONCILE_REQUIRED.value)


class SqlTeacherAssignmentTransferRepository(TeacherAssignmentTransferRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        receipt_hmac_key: bytes | None,
    ) -> None:
        self._session_factory = session_factory
        self._receipt_hmac_key = receipt_hmac_key

    def begin(self, command: TeacherAssignmentTransferCommand) -> TeacherAssignmentTransferStart:
        try:
            with self._session_factory() as db, db.begin():
                classroom = _lock_class(db, command.class_id)
                if classroom is None:
                    raise TeacherAssignmentTransferError(404, "RESOURCE_NOT_FOUND")
                if not _manager_is_authorized(db, command, classroom.organization_id):
                    raise TeacherAssignmentTransferError(404, "RESOURCE_NOT_FOUND")
                scope = _operation_scope(command.class_id)
                receipt = db.get(
                    Be1CommandReceiptModel,
                    (command.principal_subject, scope, command.idempotency_key),
                )
                if (
                    receipt is not None
                    and receipt.request_fingerprint != command.request_fingerprint
                ):
                    raise TeacherAssignmentTransferError(400, "INVALID_IDEMPOTENCY_KEY")

                existing = db.scalar(
                    select(Be1TeacherAssignmentTransferModel).where(
                        Be1TeacherAssignmentTransferModel.principal_ref
                        == command.principal_subject,
                        Be1TeacherAssignmentTransferModel.operation_scope == scope,
                        Be1TeacherAssignmentTransferModel.idempotency_key
                        == command.idempotency_key,
                    )
                )
                if existing is not None:
                    if existing.fingerprint != command.request_fingerprint:
                        raise TeacherAssignmentTransferError(400, "INVALID_IDEMPOTENCY_KEY")
                    return TeacherAssignmentTransferStart(
                        record=_record(db, existing),
                        resume=existing.state in _PENDING_STATES,
                    )
                if receipt is not None:
                    # A prior first-assignment POST owns this key and its original 200 response.
                    raise TeacherAssignmentTransferError(400, "INVALID_IDEMPOTENCY_KEY")

                if classroom.state != "active":
                    raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION")

                pending = db.scalar(
                    select(Be1TeacherAssignmentTransferModel.transfer_id).where(
                        Be1TeacherAssignmentTransferModel.organization_id
                        == classroom.organization_id,
                        Be1TeacherAssignmentTransferModel.class_id == command.class_id,
                        Be1TeacherAssignmentTransferModel.state.in_(_PENDING_STATES),
                    )
                )
                if pending is not None:
                    raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")

                if classroom.assignment_revision != command.expected_revision:
                    raise TeacherAssignmentTransferError(
                        409,
                        "STALE_REVISION",
                        current_version=classroom.assignment_revision,
                    )

                active = list(
                    db.scalars(
                        select(OrganizationAssignmentModel)
                        .where(
                            OrganizationAssignmentModel.organization_id
                            == classroom.organization_id,
                            OrganizationAssignmentModel.class_id == command.class_id,
                            OrganizationAssignmentModel.role == "teacher",
                            OrganizationAssignmentModel.active.is_(True),
                        )
                        .with_for_update()
                    ).all()
                )
                if len(active) != 1:
                    raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")
                old_assignment = active[0]
                old_identity = db.get(AdultIdentityModel, old_assignment.subject)
                if old_identity is None:
                    raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")

                new_assignment: OrganizationAssignmentModel | None = None
                new_identity: AdultIdentityModel | None = None
                if command.action is TransferAction.REASSIGN:
                    if command.candidate_ref is None:
                        raise TeacherAssignmentTransferError(400, "INVALID_REQUEST")
                    candidate_statement = (
                        select(AdultIdentityModel)
                        .where(
                            AdultIdentityModel.account_id == command.candidate_ref,
                            AdultIdentityModel.state == "active",
                            AdultIdentityModel.account_role == "teacher",
                            exists().where(
                                OrganizationAssignmentModel.organization_id
                                == classroom.organization_id,
                                OrganizationAssignmentModel.subject == AdultIdentityModel.subject,
                                OrganizationAssignmentModel.role == "teacher",
                                OrganizationAssignmentModel.active.is_(True),
                            ),
                        )
                        .with_for_update(read=True, of=AdultIdentityModel)
                        .execution_options(populate_existing=True)
                    )
                    new_identity = db.scalar(candidate_statement)
                    if new_identity is None:
                        raise TeacherAssignmentTransferError(404, "RESOURCE_NOT_FOUND")
                    if new_identity.subject == old_assignment.subject:
                        raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")
                    new_assignment = db.scalar(
                        select(OrganizationAssignmentModel)
                        .where(
                            OrganizationAssignmentModel.organization_id
                            == classroom.organization_id,
                            OrganizationAssignmentModel.subject == new_identity.subject,
                            OrganizationAssignmentModel.class_id == command.class_id,
                            OrganizationAssignmentModel.role == "teacher",
                        )
                        .with_for_update()
                    )
                    if new_assignment is not None and new_assignment.active:
                        raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")
                    if new_assignment is None:
                        new_assignment = OrganizationAssignmentModel(
                            assignment_id=str(uuid4()),
                            organization_id=classroom.organization_id,
                            subject=new_identity.subject,
                            class_id=command.class_id,
                            role="teacher",
                            active=False,
                        )
                        db.add(new_assignment)
                        db.flush()
                elif command.candidate_ref is not None:
                    raise TeacherAssignmentTransferError(400, "INVALID_REQUEST")

                now = datetime.now(UTC)
                transfer_id = str(uuid4())
                operation_scope = scope
                fenced_revision = classroom.assignment_revision + 1
                old_assignment.active = False
                if new_assignment is not None:
                    new_assignment.active = False
                classroom.assignment_revision = fenced_revision
                classroom.revision += 1
                transfer = Be1TeacherAssignmentTransferModel(
                    transfer_id=transfer_id,
                    organization_id=classroom.organization_id,
                    class_id=command.class_id,
                    action=command.action.value,
                    state=TransferState.TRANSFER_PENDING.value,
                    principal_ref=command.principal_subject,
                    old_subject=old_assignment.subject,
                    new_subject=new_identity.subject if new_identity is not None else None,
                    old_assignment_id=old_assignment.assignment_id,
                    new_assignment_id=(
                        new_assignment.assignment_id if new_assignment is not None else None
                    ),
                    expected_revision=command.expected_revision,
                    fenced_revision=fenced_revision,
                    operation_scope=operation_scope,
                    idempotency_key=command.idempotency_key,
                    fingerprint=command.request_fingerprint,
                    state_revision=1,
                    attempt_count=0,
                    created_at=now,
                    updated_at=now,
                )
                db.add(transfer)
                db.flush()
                _audit(
                    db,
                    command=command,
                    key=self._receipt_hmac_key,
                    organization_id=classroom.organization_id,
                    transfer_id=transfer_id,
                    state=TransferState.TRANSFER_PENDING,
                )
                record = _record(db, transfer)
            return TeacherAssignmentTransferStart(record=record, resume=True)
        except TeacherAssignmentTransferError:
            raise
        except IntegrityError:
            raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT") from None
        except SQLAlchemyError:
            raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE") from None

    def finalize(
        self,
        command: TeacherAssignmentTransferCommand,
        record: TeacherAssignmentTransferRecord,
        *,
        story_receipt_ref: str,
    ) -> TeacherAssignmentTransferRecord:
        target = (
            TransferState.OFFBOARDED
            if record.action is TransferAction.OFFBOARD
            else TransferState.COMPLETED
        )
        try:
            with self._session_factory() as db, db.begin():
                row, classroom = self._lock_transfer(db, record)
                if row.state in {state.value for state in _TERMINAL_STATES}:
                    return _record(db, row)
                if row.state not in _PENDING_STATES:
                    raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION")
                if classroom.assignment_revision != row.fenced_revision:
                    raise TeacherAssignmentTransferError(409, "STALE_REVISION")
                old_assignment = db.get(
                    OrganizationAssignmentModel, row.old_assignment_id
                )
                if old_assignment is None or old_assignment.active:
                    raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION")
                if row.new_assignment_id is not None:
                    new_assignment = db.get(
                        OrganizationAssignmentModel, row.new_assignment_id
                    )
                    if new_assignment is None or new_assignment.active:
                        raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION")
                    new_assignment.active = True
                classroom.assignment_revision += 1
                classroom.revision += 1
                _transition_row(
                    row,
                    target=target,
                    failure_code=None,
                    story_receipt_ref=story_receipt_ref,
                    now=datetime.now(UTC),
                )
                _audit(
                    db,
                    command=command,
                    key=self._receipt_hmac_key,
                    organization_id=row.organization_id,
                    transfer_id=row.transfer_id,
                    state=target,
                )
                self._add_acceptance_receipt(db, command, row)
                if target in {TransferState.COMPLETED, TransferState.OFFBOARDED}:
                    _emit_transfer_event(db, row, classroom.assignment_revision)
                db.flush()
                result = _record(db, row)
            return result
        except TeacherAssignmentTransferError:
            raise
        except IntegrityError:
            raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT") from None
        except SQLAlchemyError:
            raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE") from None

    def compensate(
        self,
        command: TeacherAssignmentTransferCommand,
        record: TeacherAssignmentTransferRecord,
        *,
        story_receipt_ref: str,
        failure_code: str,
    ) -> TeacherAssignmentTransferRecord:
        try:
            with self._session_factory() as db, db.begin():
                row, classroom = self._lock_transfer(db, record)
                if row.state in {state.value for state in _TERMINAL_STATES}:
                    return _record(db, row)
                old_assignment = db.get(
                    OrganizationAssignmentModel, row.old_assignment_id
                )
                if old_assignment is None:
                    raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION")
                old_assignment.active = True
                classroom.assignment_revision += 1
                classroom.revision += 1
                _transition_row(
                    row,
                    target=TransferState.COMPENSATED_CONFLICT,
                    failure_code=failure_code,
                    story_receipt_ref=story_receipt_ref,
                    now=datetime.now(UTC),
                )
                _audit(
                    db,
                    command=command,
                    key=self._receipt_hmac_key,
                    organization_id=row.organization_id,
                    transfer_id=row.transfer_id,
                    state=TransferState.COMPENSATED_CONFLICT,
                )
                if row.action == TransferAction.REASSIGN.value:
                    self._add_acceptance_receipt(db, command, row)
                db.flush()
                result = _record(db, row)
            return result
        except TeacherAssignmentTransferError:
            raise
        except SQLAlchemyError:
            raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE") from None

    def reconcile(
        self,
        command: TeacherAssignmentTransferCommand,
        record: TeacherAssignmentTransferRecord,
        *,
        failure_code: str,
    ) -> TeacherAssignmentTransferRecord:
        try:
            with self._session_factory() as db, db.begin():
                row, _classroom = self._lock_transfer(db, record)
                if row.state in {state.value for state in _TERMINAL_STATES}:
                    return _record(db, row)
                _transition_row(
                    row,
                    target=TransferState.RECONCILE_REQUIRED,
                    failure_code=failure_code,
                    story_receipt_ref=None,
                    now=datetime.now(UTC),
                )
                _audit(
                    db,
                    command=command,
                    key=self._receipt_hmac_key,
                    organization_id=row.organization_id,
                    transfer_id=row.transfer_id,
                    state=TransferState.RECONCILE_REQUIRED,
                )
                self._add_acceptance_receipt(db, command, row)
                db.flush()
                result = _record(db, row)
            return result
        except TeacherAssignmentTransferError:
            raise
        except SQLAlchemyError:
            raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE") from None

    def status(
        self, *, organization_id: str, class_id: str, transfer_id: str
    ) -> TeacherAssignmentTransferRecord | None:
        try:
            with self._session_factory() as db:
                row = db.scalar(
                    select(Be1TeacherAssignmentTransferModel).where(
                        Be1TeacherAssignmentTransferModel.transfer_id == transfer_id,
                        Be1TeacherAssignmentTransferModel.organization_id == organization_id,
                        Be1TeacherAssignmentTransferModel.class_id == class_id,
                    )
                )
                if row is None:
                    return None
                return _record(db, row)
        except SQLAlchemyError:
            raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE") from None

    def _lock_transfer(
        self, db: Session, record: TeacherAssignmentTransferRecord
    ) -> tuple[Be1TeacherAssignmentTransferModel, ClassroomModel]:
        classroom = _lock_class(db, record.class_id)
        row = db.scalar(
            select(Be1TeacherAssignmentTransferModel)
            .where(
                Be1TeacherAssignmentTransferModel.transfer_id == record.transfer_id,
                Be1TeacherAssignmentTransferModel.organization_id == record.organization_id,
                Be1TeacherAssignmentTransferModel.class_id == record.class_id,
            )
            .with_for_update()
        )
        if classroom is None or row is None:
            raise TeacherAssignmentTransferError(404, "RESOURCE_NOT_FOUND")
        if row.fingerprint != record.request_fingerprint:
            raise TeacherAssignmentTransferError(400, "INVALID_IDEMPOTENCY_KEY")
        return row, classroom

    def _add_acceptance_receipt(
        self,
        db: Session,
        command: TeacherAssignmentTransferCommand,
        row: Be1TeacherAssignmentTransferModel,
    ) -> None:
        response = Be1TeacherAssignmentTransferAcceptedV1(
            transfer_id=row.transfer_id,
            class_id=row.class_id,
            action=row.action,
            state="TRANSFER_PENDING",
            assignment_revision=row.fenced_revision,
            status_url=(
                f"/api/be1/v1/classes/{row.class_id}/assignment-transfers/{row.transfer_id}"
            ),
        ).model_dump(mode="json")
        values = {
            "principal_ref": command.principal_subject,
            "operation_scope": row.operation_scope,
            "idempotency_key": command.idempotency_key,
            "organization_id": row.organization_id,
            "request_fingerprint": command.request_fingerprint,
            "response_json": response,
            "response_status": 202,
        }
        db.execute(
            pg_insert(Be1CommandReceiptModel)
            .values(**values)
            .on_conflict_do_nothing(constraint="pk_be1_command_receipts")
        )
        receipt = db.get(
            Be1CommandReceiptModel,
            (command.principal_subject, row.operation_scope, command.idempotency_key),
        )
        if (
            receipt is None
            or receipt.request_fingerprint != command.request_fingerprint
            or receipt.response_status != 202
            or dict(receipt.response_json) != response
        ):
            raise TeacherAssignmentTransferError(400, "INVALID_IDEMPOTENCY_KEY")


def _lock_class(db: Session, class_id: str) -> ClassroomModel | None:
    return db.scalar(
        select(ClassroomModel)
        .where(ClassroomModel.class_id == class_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _operation_scope(class_id: str) -> str:
    # POST and DELETE share this target scope, so changing method/action with a reused key fails.
    return _OPERATION_SCOPE.format(class_id=class_id)


def _manager_is_authorized(
    db: Session, command: TeacherAssignmentTransferCommand, org: str
) -> bool:
    identity = db.get(AdultIdentityModel, command.principal_subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "school_manager"
        or identity.issuer != command.principal_issuer
    ):
        return False
    return (
        db.scalar(
            select(OrganizationAssignmentModel.assignment_id).where(
                OrganizationAssignmentModel.organization_id == org,
                OrganizationAssignmentModel.subject == command.principal_subject,
                OrganizationAssignmentModel.active.is_(True),
                OrganizationAssignmentModel.role == "school_admin",
                or_(
                    OrganizationAssignmentModel.class_id.is_(None),
                    OrganizationAssignmentModel.class_id == command.class_id,
                ),
            )
        )
        is not None
    )


def _record(
    db: Session, row: Be1TeacherAssignmentTransferModel
) -> TeacherAssignmentTransferRecord:
    classroom = db.scalar(
        select(ClassroomModel).where(
            ClassroomModel.organization_id == row.organization_id,
            ClassroomModel.class_id == row.class_id,
        )
    )
    old_identity = db.get(AdultIdentityModel, row.old_subject)
    new_identity = db.get(AdultIdentityModel, row.new_subject) if row.new_subject else None
    return TeacherAssignmentTransferRecord(
        transfer_id=row.transfer_id,
        organization_id=row.organization_id,
        class_id=row.class_id,
        action=TransferAction(row.action),
        state=TransferState(row.state),
        old_subject=row.old_subject,
        new_subject=row.new_subject,
        old_teacher_ref=old_identity.account_id if old_identity else "",
        new_teacher_ref=new_identity.account_id if new_identity else None,
        expected_revision=row.expected_revision,
        fenced_revision=row.fenced_revision,
        assignment_revision=classroom.assignment_revision if classroom else row.fenced_revision,
        operation_scope=row.operation_scope,
        idempotency_key=row.idempotency_key,
        request_fingerprint=row.fingerprint,
        story_receipt_ref=row.story_receipt_ref,
        last_failure_code=row.last_failure_code,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _transition_row(
    row: Be1TeacherAssignmentTransferModel,
    *,
    target: TransferState,
    failure_code: str | None,
    story_receipt_ref: str | None,
    now: datetime,
) -> None:
    try:
        state_revision, updated_at, attempt_count = transition(
            TransferState(row.state),
            target,
            state_revision=row.state_revision,
            updated_at=now,
            previous_updated_at=row.updated_at,
            attempt_count=row.attempt_count + 1,
            previous_attempt_count=row.attempt_count,
        )
    except TransferStateError as exc:
        raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION") from exc
    row.state = target.value
    row.state_revision = state_revision
    row.updated_at = updated_at
    row.attempt_count = attempt_count
    row.last_failure_code = failure_code
    if story_receipt_ref is not None:
        row.story_receipt_ref = story_receipt_ref
    if target in {
        TransferState.COMPLETED,
        TransferState.OFFBOARDED,
        TransferState.COMPENSATED_CONFLICT,
    }:
        row.finalized_at = now


def _audit(
    db: Session,
    *,
    command: TeacherAssignmentTransferCommand,
    key: bytes | None,
    organization_id: str,
    transfer_id: str,
    state: TransferState,
) -> None:
    material = f"{command.principal_issuer}\0{command.principal_subject}".encode()
    actor_ref = (
        hmac.new(key, b"be1.teacher-assignment-transfer.actor.v1\0" + material, hashlib.sha256)
        .hexdigest()
        if key
        else hashlib.sha256(b"be1.teacher-assignment-transfer.actor.v1\0" + material).hexdigest()
    )
    db.add(
        CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id=organization_id,
            actor_ref=actor_ref,
            action=f"be1.teacher_assignment_transfer.{state.value.lower()}",
            resource_type="teacher_assignment_transfer",
            resource_id=transfer_id,
            decision=state.value,
        )
    )


def _emit_transfer_event(
    db: Session, row: Be1TeacherAssignmentTransferModel, revision: int
) -> None:
    aggregate = db.get(CoreAggregateRevisionModel, row.class_id)
    if aggregate is None:
        aggregate_revision = 1
        db.add(
            CoreAggregateRevisionModel(
                aggregate_id=row.class_id,
                organization_id=row.organization_id,
                revision=aggregate_revision,
            )
        )
    else:
        if aggregate.organization_id != row.organization_id:
            raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")
        aggregate_revision = aggregate.revision + 1
        aggregate.revision = aggregate_revision
    db.add(
        CoreOutboxEventModel(
            event_id=str(uuid4()),
            event_type="be1.teacher_assignment_changed.v1",
            organization_id=row.organization_id,
            aggregate_id=row.class_id,
            aggregate_revision=aggregate_revision,
            payload={
                "transfer_id": row.transfer_id,
                "class_id": row.class_id,
                "action": row.action,
                "assignment_revision": str(revision),
            },
            status="pending",
            attempt_count=0,
        )
    )


_TERMINAL_STATES = {
    TransferState.COMPLETED,
    TransferState.OFFBOARDED,
    TransferState.COMPENSATED_CONFLICT,
}


__all__ = ["SqlTeacherAssignmentTransferRepository"]
