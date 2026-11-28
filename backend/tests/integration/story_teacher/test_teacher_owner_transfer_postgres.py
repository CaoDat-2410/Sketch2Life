"""T-6b Story owner-transfer receipt integration checks on PostgreSQL."""

# ruff: noqa: F811  (the imported fixture is used as a test argument)

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from test_teacher_run_create_postgres import (  # type: ignore[import-not-found]
    Api,
    _assign,
    _identity,
    api,  # noqa: F401 - pytest fixture
    flow,
    post_create,
)

from alembic import command
from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
    story_teacher_owner_transfer_key_sha256,
)
from sketch2life.domain.teacher_assignment_transfer import TransferAction
from sketch2life.infrastructure.persistence.be1_models import (
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_teacher.teacher_owner_transfer_repository import (
    SqlStoryTeacherOwnerTransferRepository,
)

_BACKEND = Path(__file__).resolve().parents[3]
_STORY_TRANSFER_PARENT = "20261123_ppg_0001"


def _seed_transfer(
    d: Api, *, action: TransferAction, new_subject: str | None
) -> tuple[str, str, str | None]:
    old_subject = d.subjects["t2"]
    old_account = d.accounts["t2"]
    new_account: str | None = None
    transfer_id = str(uuid4())
    now = datetime.now(UTC)
    with d.sessions().begin() as db:
        classroom = db.scalar(
            select(ClassroomModel).where(ClassroomModel.class_id == d.classes["a2"])
        )
        assert classroom is not None
        old_assignment = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == d.organization,
                OrganizationAssignmentModel.class_id == d.classes["a2"],
                OrganizationAssignmentModel.subject == old_subject,
                OrganizationAssignmentModel.role == "teacher",
            )
        )
        assert old_assignment is not None and old_assignment.active
        old_assignment.active = False
        new_assignment_id: str | None = None
        if new_subject is not None:
            new_account = _identity(db, new_subject, "teacher")
            _assign(db, d.organization, new_subject, "teacher", None)
            new_assignment_id = str(uuid4())
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=new_assignment_id,
                    organization_id=d.organization,
                    subject=new_subject,
                    class_id=d.classes["a2"],
                    role="teacher",
                    active=False,
                )
            )
            db.flush()
        classroom.assignment_revision = 2
        db.add(
            Be1TeacherAssignmentTransferModel(
                transfer_id=transfer_id,
                organization_id=d.organization,
                class_id=d.classes["a2"],
                action=action.value,
                state="TRANSFER_PENDING",
                principal_ref=d.subjects["manager"],
                old_subject=old_subject,
                new_subject=new_subject,
                old_assignment_id=old_assignment.assignment_id,
                new_assignment_id=new_assignment_id,
                expected_revision=1,
                fenced_revision=2,
                operation_scope=f"POST /classes/{d.classes['a2']}/assignments",
                idempotency_key=f"story-transfer-{transfer_id}",
                fingerprint="a" * 64,
                story_receipt_ref=None,
                state_revision=1,
                attempt_count=0,
                last_failure_code=None,
                created_at=now,
                updated_at=now,
                finalized_at=None,
            )
        )
    return transfer_id, old_account, new_account


def _command(
    d: Api, transfer_id: str, old_account: str, new_account: str | None
) -> StoryTeacherOwnerTransferCommandV1:
    key = f"story-transfer-{transfer_id}"
    payload = {
        "transfer_id": transfer_id,
        "organization_ref": d.organization,
        "class_ref": d.classes["a2"],
        "action": "OFFBOARD" if new_account is None else "REASSIGN",
        "old_owner_teacher_ref": old_account,
        "new_owner_teacher_ref": new_account,
        "assignment_revision": 2,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return StoryTeacherOwnerTransferCommandV1(
        **payload,
        idempotency_key=key,
        request_fingerprint_sha256=fingerprint,
    )


def test_story_owner_transfer_increments_epoch_keeps_creator_and_replays_once(api: Api) -> None:
    d = api
    _occurrence, _offer, body = flow(d, who="t2", class_key="a2")
    created = post_create(d, "t2", body)
    assert created.status_code == 201, created.text
    run_id = created.json()["story_run"]["run_id"]
    new_subject = f"synthetic-t6b-new-{d.token}"
    transfer_id, old_account, new_account = _seed_transfer(
        d, action=TransferAction.REASSIGN, new_subject=new_subject
    )
    assert new_account is not None
    command = _command(d, transfer_id, old_account, new_account)
    repository = SqlStoryTeacherOwnerTransferRepository(d.sessions())

    first = repository.transfer_owner(command)
    replay = repository.transfer_owner(command)
    assert first.outcome == replay.outcome == "TRANSFERRED"
    assert first.owner_epoch == replay.owner_epoch == 1
    with d.sessions()() as db:
        row = db.execute(
            select(
                story_tables.story_runs.c.active_owner_teacher_id,
                story_tables.story_runs.c.created_by_actor_ref,
                story_tables.story_runs.c.owner_epoch,
            ).where(story_tables.story_runs.c.run_id == run_id)
        ).one()
        receipt_key_hash = story_teacher_owner_transfer_key_sha256(
            organization_ref=command.organization_ref,
            class_ref=command.class_ref,
            transfer_id=command.transfer_id,
        )
        receipts = db.scalar(
            select(func.count()).select_from(story_tables.story_command_receipts).where(
                story_tables.story_command_receipts.c.actor_scope_ref == command.organization_ref,
                story_tables.story_command_receipts.c.operation == "TRANSFER_TEACHER_OWNER",
                story_tables.story_command_receipts.c.idempotency_scope_ref == command.class_ref,
                story_tables.story_command_receipts.c.idempotency_key_sha256 == receipt_key_hash,
            )
        )
    assert (row.active_owner_teacher_id, row.created_by_actor_ref, row.owner_epoch) == (
        new_account,
        old_account,
        1,
    )
    assert receipts == 1
    assert first.idempotency_key_sha256 == replay.idempotency_key_sha256 == receipt_key_hash
    assert story_teacher_owner_transfer_key_sha256(
        organization_ref=command.organization_ref,
        class_ref=command.class_ref,
        transfer_id=str(uuid4()),
    ) != receipt_key_hash


def test_story_offboard_with_an_active_run_records_conflict_without_orphaning(api: Api) -> None:
    d = api
    _occurrence, _offer, body = flow(d, who="t2", class_key="a2")
    created = post_create(d, "t2", body)
    assert created.status_code == 201, created.text
    run_id = created.json()["story_run"]["run_id"]
    transfer_id, old_account, _new_account = _seed_transfer(
        d, action=TransferAction.OFFBOARD, new_subject=None
    )
    command = _command(d, transfer_id, old_account, None)
    receipt = SqlStoryTeacherOwnerTransferRepository(d.sessions()).transfer_owner(command)
    assert receipt.outcome == "CONFLICT"
    with d.sessions()() as db:
        row = db.execute(
            select(
                story_tables.story_runs.c.active_owner_teacher_id,
                story_tables.story_runs.c.created_by_actor_ref,
                story_tables.story_runs.c.owner_epoch,
            ).where(story_tables.story_runs.c.run_id == run_id)
        ).one()
    assert (row.active_owner_teacher_id, row.created_by_actor_ref, row.owner_epoch) == (
        old_account,
        old_account,
        0,
    )


def test_story_downgrade_refuses_while_owner_transfer_receipts_exist(api: Api) -> None:
    d = api
    transfer_id, old_account, new_account = _seed_transfer(
        d,
        action=TransferAction.REASSIGN,
        new_subject=f"synthetic-t6b-downgrade-{d.token}",
    )
    command_v1 = _command(d, transfer_id, old_account, new_account)
    receipt = SqlStoryTeacherOwnerTransferRepository(d.sessions()).transfer_owner(command_v1)
    assert receipt.outcome == "TRANSFERRED"

    config = Config(str(_BACKEND / "alembic.ini"))
    with pytest.raises(DBAPIError, match="Story downgrade refused"):
        command.downgrade(config, _STORY_TRANSFER_PARENT)
