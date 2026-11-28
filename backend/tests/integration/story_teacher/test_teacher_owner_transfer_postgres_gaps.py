"""Additional Story owner-transfer PostgreSQL tests for T-6b gaps identified in cold review R1."""

# ruff: noqa: F811

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    story_teacher_owner_transfer_key_sha256,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_teacher.teacher_owner_transfer_repository import (
    SqlStoryTeacherOwnerTransferRepository,
)
from tests.integration.story_teacher.test_teacher_owner_transfer_postgres import (
    _command,
)
from tests.integration.story_teacher.test_teacher_run_create_postgres import (
    Api,
    api,  # noqa: F401 - pytest fixture
    flow,
    post_create,
)


def _seed_existing_teacher_transfer(
    d: Api,
    *,
    class_key: str,
    old_key: str,
    new_key: str,
    fenced_revision: int = 2,
) -> tuple[str, str, str]:
    old_subject = d.subjects[old_key]
    new_subject = d.subjects[new_key]
    transfer_id = str(uuid4())
    now = datetime.now(UTC)
    with d.sessions().begin() as db:
        classroom = db.scalar(
            select(ClassroomModel).where(ClassroomModel.class_id == d.classes[class_key])
        )
        assert classroom is not None
        old_assignment = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == d.organization,
                OrganizationAssignmentModel.class_id == d.classes[class_key],
                OrganizationAssignmentModel.subject == old_subject,
                OrganizationAssignmentModel.role == "teacher",
            )
        )
        assert old_assignment is not None and old_assignment.active
        old_assignment.active = False
        new_assignment = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == d.organization,
                OrganizationAssignmentModel.class_id == d.classes[class_key],
                OrganizationAssignmentModel.subject == new_subject,
                OrganizationAssignmentModel.role == "teacher",
            )
        )
        if new_assignment is None:
            new_assignment = OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=d.organization,
                subject=new_subject,
                class_id=d.classes[class_key],
                role="teacher",
                active=False,
            )
            db.add(new_assignment)
        else:
            new_assignment.active = False
        db.flush()
        classroom.assignment_revision = fenced_revision
        db.add(
            Be1TeacherAssignmentTransferModel(
                transfer_id=transfer_id,
                organization_id=d.organization,
                class_id=d.classes[class_key],
                action="REASSIGN",
                state="TRANSFER_PENDING",
                principal_ref=d.subjects["manager"],
                old_subject=old_subject,
                new_subject=new_subject,
                old_assignment_id=old_assignment.assignment_id,
                new_assignment_id=new_assignment.assignment_id,
                expected_revision=fenced_revision - 1,
                fenced_revision=fenced_revision,
                operation_scope=f"POST /classes/{d.classes[class_key]}/assignments",
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
    return transfer_id, d.accounts[old_key], d.accounts[new_key]


@pytest.mark.integration
def test_story_reassign_conflicts_when_new_owner_already_holds_an_active_run(
    api: Api,
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    d = api
    _occ1, _offer1, body1 = flow(d, who="t1", class_key="a1")
    created_t1 = post_create(d, "t1", body1)
    assert created_t1.status_code == 201, created_t1.text

    _occ2, _offer2, body2 = flow(d, who="t2", class_key="a2")
    created_t2 = post_create(d, "t2", body2)
    assert created_t2.status_code == 201, created_t2.text
    run_a2 = created_t2.json()["story_run"]["run_id"]

    transfer_id, old_account, new_account = _seed_existing_teacher_transfer(
        d, class_key="a2", old_key="t2", new_key="t1"
    )
    command = _command(d, transfer_id, old_account, new_account)
    receipt = SqlStoryTeacherOwnerTransferRepository(d.sessions()).transfer_owner(command)

    assert receipt.outcome == "CONFLICT"
    with d.sessions()() as db:
        row = db.execute(
            select(
                story_tables.story_runs.c.active_owner_teacher_id,
                story_tables.story_runs.c.owner_epoch,
            ).where(story_tables.story_runs.c.run_id == run_a2)
        ).one()
        stored_status = db.scalar(
            select(story_tables.story_command_receipts.c.response_status).where(
                story_tables.story_command_receipts.c.idempotency_key_sha256
                == story_teacher_owner_transfer_key_sha256(
                    organization_ref=command.organization_ref,
                    class_ref=command.class_ref,
                    transfer_id=command.transfer_id,
                )
            )
        )
    assert (row.active_owner_teacher_id, row.owner_epoch) == (d.accounts["t2"], 0)
    assert stored_status == 409
