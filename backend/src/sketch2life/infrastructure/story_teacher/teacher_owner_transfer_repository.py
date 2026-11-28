"""Story infrastructure adapter for the versioned BE1 Teacher owner-transfer command."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.class_transfer_state import ClassTransferState
from sketch2life.application.ports.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferUnavailable,
)
from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
    StoryTeacherOwnerTransferReceiptV1,
    story_teacher_owner_transfer_key_sha256,
)
from sketch2life.infrastructure.lesson_occurrences.class_transfer_guard import (
    SqlClassTransferState,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_OPERATION = "TRANSFER_TEACHER_OWNER"
_SCOPE_KIND = "COLLECTION"


class SqlStoryTeacherOwnerTransferRepository:
    """Apply owner and epoch changes in one Story transaction with a durable command receipt."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        class_transfer_state_factory: Callable[[Session], ClassTransferState] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._class_transfer_state_factory = class_transfer_state_factory or SqlClassTransferState

    def transfer_owner(
        self, command: StoryTeacherOwnerTransferCommandV1
    ) -> StoryTeacherOwnerTransferReceiptV1:
        key_hash = story_teacher_owner_transfer_key_sha256(
            organization_ref=command.organization_ref,
            class_ref=command.class_ref,
            transfer_id=command.transfer_id,
        )
        try:
            with self._session_factory() as db, db.begin():
                state = self._state(db)
                authorization = state.authorize_story_transfer(command)
                if authorization is None:
                    raise StoryTeacherOwnerTransferUnavailable("BE1 transfer state is unavailable")
                receipt = _find_receipt(db, command, key_hash)
                if receipt is not None:
                    return _replay(command, receipt, key_hash)
                return self._transfer_once(db, command, key_hash)
        except StoryTeacherOwnerTransferUnavailable:
            raise
        except IntegrityError:
            # A concurrent target-owner run or receipt won the database uniqueness race. No part
            # of this transaction committed, so persist/read the stable conflict receipt afresh.
            return self._record_conflict_after_race(command, key_hash)
        except SQLAlchemyError:
            raise StoryTeacherOwnerTransferUnavailable(
                "Story transaction outcome is uncertain"
            ) from None

    def _state(self, db: Session) -> ClassTransferState:
        return self._class_transfer_state_factory(db)

    def _transfer_once(
        self,
        db: Session,
        command: StoryTeacherOwnerTransferCommandV1,
        key_hash: str,
    ) -> StoryTeacherOwnerTransferReceiptV1:
        runs = story_tables.story_runs
        affected = list(
            db.execute(
                select(runs.c.run_id, runs.c.owner_epoch)
                .where(
                    runs.c.organization_ref == command.organization_ref,
                    runs.c.class_ref == command.class_ref,
                    runs.c.active_owner_teacher_id == command.old_owner_teacher_ref,
                )
                .with_for_update()
            ).all()
        )
        conflicting_owner_run = False
        if command.new_owner_teacher_ref is not None:
            conflicting_owner_run = (
                db.scalar(
                    select(runs.c.run_id)
                    .where(
                        runs.c.active_owner_teacher_id == command.new_owner_teacher_ref,
                        runs.c.run_id.not_in([str(row.run_id) for row in affected]),
                    )
                    .with_for_update()
                    .limit(1)
                )
                is not None
            )
        conflict = (
            command.new_owner_teacher_ref is None and bool(affected)
        ) or conflicting_owner_run
        if conflict:
            owner_epoch = max((int(row.owner_epoch) for row in affected), default=0)
            return _store_receipt(
                db,
                command,
                key_hash=key_hash,
                outcome="CONFLICT",
                owner_epoch=owner_epoch,
            )

        now = datetime.now(UTC)
        owner_epoch = 0
        for run_id, previous_epoch in affected:
            result = db.execute(
                update(runs)
                .where(
                    runs.c.run_id == run_id,
                    runs.c.organization_ref == command.organization_ref,
                    runs.c.class_ref == command.class_ref,
                    runs.c.active_owner_teacher_id == command.old_owner_teacher_ref,
                )
                .values(
                    active_owner_teacher_id=command.new_owner_teacher_ref,
                    owner_epoch=runs.c.owner_epoch + 1,
                    revision=runs.c.revision + 1,
                    version=runs.c.version + 1,
                    updated_at=now,
                )
            )
            if result.rowcount != 1:
                raise StoryTeacherOwnerTransferUnavailable("Story owner changed concurrently")
            owner_epoch = max(owner_epoch, int(previous_epoch) + 1)
        return _store_receipt(
            db,
            command,
            key_hash=key_hash,
            outcome="TRANSFERRED",
            owner_epoch=owner_epoch,
        )

    def _record_conflict_after_race(
        self,
        command: StoryTeacherOwnerTransferCommandV1,
        key_hash: str,
    ) -> StoryTeacherOwnerTransferReceiptV1:
        try:
            with self._session_factory() as db, db.begin():
                if self._state(db).authorize_story_transfer(command) is None:
                    raise StoryTeacherOwnerTransferUnavailable("BE1 transfer state is unavailable")
                existing = _find_receipt(db, command, key_hash)
                if existing is not None:
                    return _replay(command, existing, key_hash)
                return _store_receipt(
                    db,
                    command,
                    key_hash=key_hash,
                    outcome="CONFLICT",
                    owner_epoch=0,
                )
        except StoryTeacherOwnerTransferUnavailable:
            raise
        except SQLAlchemyError:
            raise StoryTeacherOwnerTransferUnavailable(
                "Story transaction outcome is uncertain"
            ) from None


def _find_receipt(
    db: Session, command: StoryTeacherOwnerTransferCommandV1, key_hash: str
) -> RowMapping | None:
    return db.execute(
        select(story_tables.story_command_receipts).where(
            story_tables.story_command_receipts.c.actor_scope_kind == "ORGANIZATION",
            story_tables.story_command_receipts.c.actor_scope_ref == command.organization_ref,
            story_tables.story_command_receipts.c.operation == _OPERATION,
            story_tables.story_command_receipts.c.idempotency_scope_kind == _SCOPE_KIND,
            story_tables.story_command_receipts.c.idempotency_scope_ref == command.class_ref,
            story_tables.story_command_receipts.c.idempotency_key_sha256 == key_hash,
        )
    ).mappings().one_or_none()


def _replay(
    command: StoryTeacherOwnerTransferCommandV1,
    receipt: Mapping[str, Any],
    key_hash: str,
) -> StoryTeacherOwnerTransferReceiptV1:
    if (
        receipt["request_fingerprint_sha256"] != command.request_fingerprint_sha256
        or receipt["state"] != "FINAL"
        or receipt["response_status"] not in {200, 409}
    ):
        raise StoryTeacherOwnerTransferUnavailable("Story receipt does not match the command")
    body = receipt["response_body"]
    if not isinstance(body, dict) or body.get("transfer_id") != command.transfer_id:
        raise StoryTeacherOwnerTransferUnavailable("Story receipt body is invalid")
    return _receipt(
        command,
        key_hash=key_hash,
        outcome=str(body.get("outcome")),
        owner_epoch=int(body.get("owner_epoch", 0)),
    )


def _store_receipt(
    db: Session,
    command: StoryTeacherOwnerTransferCommandV1,
    *,
    key_hash: str,
    outcome: str,
    owner_epoch: int,
) -> StoryTeacherOwnerTransferReceiptV1:
    now = datetime.now(UTC)
    conflict = outcome == "CONFLICT"
    db.execute(
        story_tables.story_command_receipts.insert().values(
            receipt_id=str(uuid4()),
            actor_scope_kind="ORGANIZATION",
            actor_scope_ref=command.organization_ref,
            operation=_OPERATION,
            idempotency_scope_kind=_SCOPE_KIND,
            idempotency_scope_ref=command.class_ref,
            idempotency_key_sha256=key_hash,
            request_fingerprint_sha256=command.request_fingerprint_sha256,
            state="FINAL",
            response_status=409 if conflict else 200,
            response_resource_version=owner_epoch,
            response_body={
                "transfer_id": command.transfer_id,
                "outcome": outcome,
                "owner_epoch": owner_epoch,
            },
            resource_ref=None,
            resource_version=None,
            state_version=1,
            created_at=now,
            finalized_at=now,
        )
    )
    return _receipt(command, key_hash=key_hash, outcome=outcome, owner_epoch=owner_epoch)


def _receipt(
    command: StoryTeacherOwnerTransferCommandV1,
    *,
    key_hash: str,
    outcome: str,
    owner_epoch: int,
) -> StoryTeacherOwnerTransferReceiptV1:
    return StoryTeacherOwnerTransferReceiptV1(
        transfer_id=command.transfer_id,
        organization_ref=command.organization_ref,
        class_ref=command.class_ref,
        action=command.action,
        old_owner_teacher_ref=command.old_owner_teacher_ref,
        new_owner_teacher_ref=command.new_owner_teacher_ref,
        assignment_revision=command.assignment_revision,
        idempotency_key_sha256=key_hash,
        request_fingerprint_sha256=command.request_fingerprint_sha256,
        outcome=outcome,
        owner_epoch=owner_epoch,
    )


__all__ = ["SqlStoryTeacherOwnerTransferRepository"]
