"""T-6b BE1 assignment transfer saga integration checks on PostgreSQL."""

# ruff: noqa: F811  (the imported fixture is used as a test argument)

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from test_m9b_first_assignment_postgres import (  # type: ignore[import-not-found]
    M9bApi,
    _assign,
    _class,
    _h,
    _identity,
    m9b_api,  # noqa: F401 - pytest fixture
)

from alembic import command
from sketch2life.application.ports.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferUnavailable,
)
from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferReceiptV1,
    story_teacher_owner_transfer_key_sha256,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1TeacherAssignmentTransferModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.story_teacher.teacher_owner_transfer_repository import (
    SqlStoryTeacherOwnerTransferRepository,
)

_BACKEND = Path(__file__).resolve().parents[2]
_BE1_TRANSFER_PARENT = "20261121_nt_0002"


def _reassign(
    api: M9bApi,
    class_id: str,
    candidate_ref: str,
    revision: int,
    key: str,
    *,
    manager: str | None = None,
) -> Any:
    return api.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"candidate_ref": candidate_ref},
        headers=_h(
            manager or api.manager,
            **{"Idempotency-Key": key, "If-Match": f'"{revision}"'},
        ),
    )


def _status(api: M9bApi, accepted: dict[str, str], manager: str | None = None) -> Any:
    return api.client.get(accepted["status_url"], headers=_h(manager or api.manager))


def test_offboard_is_class_scoped_keyed_and_replayable(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "offboard")
    old_subject, teacher_ref = _identity(api, "offboard-old", rows=((api.organization_id, None),))
    first = _assign(api, class_id, teacher_ref, 1, f"t6b-first-{uuid4()}")
    assert first.status_code == 200, first.text

    key = f"t6b-offboard-{uuid4()}"
    headers = _h(api.manager, **{"Idempotency-Key": key, "If-Match": '"2"'})
    response = api.client.delete(
        f"/api/be1/v1/classes/{class_id}/assignments/current", headers=headers
    )
    assert response.status_code == 202, response.text
    accepted = response.json()
    assert accepted["action"] == "OFFBOARD"
    assert accepted["assignment_revision"] == 3
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Location"] == accepted["status_url"]
    assert not {"email", "subject", "uid", "token", "link", "child_name"} & set(accepted)

    replay = api.client.delete(
        f"/api/be1/v1/classes/{class_id}/assignments/current", headers=headers
    )
    assert replay.status_code == 202, replay.text
    assert replay.json() == accepted
    status = _status(api, accepted)
    assert status.status_code == 200, status.text
    assert status.json()["state"] == "OFFBOARDED"
    assert status.headers["Cache-Control"] == "private, no-store"
    assert not {"email", "subject", "uid", "token", "link", "child_name"} & set(status.json())

    foreign = api.client.get(accepted["status_url"], headers=_h(api.other_manager))
    unknown = api.client.get(
        f"/api/be1/v1/classes/{class_id}/assignment-transfers/{uuid4()}",
        headers=_h(api.manager),
    )
    assert (foreign.status_code, foreign.json()["code"]) == (404, "RESOURCE_NOT_FOUND")
    assert (unknown.status_code, unknown.json()["code"]) == (404, "RESOURCE_NOT_FOUND")
    with api.session()() as db:
        active = db.scalar(
            select(OrganizationAssignmentModel.assignment_id).where(
                OrganizationAssignmentModel.subject == old_subject,
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.active.is_(True),
            )
        )
    assert active is None


def test_offboard_without_a_current_teacher_is_a_generic_conflict(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "empty-offboard")
    response = api.client.delete(
        f"/api/be1/v1/classes/{class_id}/assignments/current",
        headers=_h(api.manager, **{"Idempotency-Key": f"t6b-empty-{uuid4()}", "If-Match": '"1"'}),
    )
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "RESOURCE_CONFLICT"
    assert "teacher" not in response.text.lower()


def test_reassign_replay_with_the_same_key_returns_one_transfer(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "reassign-replay")
    _old_subject, old_ref = _identity(api, "replay-old", rows=((api.organization_id, None),))
    _new_subject, new_ref = _identity(api, "replay-new", rows=((api.organization_id, None),))
    first_assignment = _assign(api, class_id, old_ref, 1, f"t6b-initial-{uuid4()}")
    assert first_assignment.status_code == 200, first_assignment.text

    key = f"t6b-reassign-replay-{uuid4()}"
    first = _reassign(api, class_id, new_ref, 2, key)
    assert first.status_code == 202, first.text
    replay = _reassign(api, class_id, new_ref, 2, key)
    assert replay.status_code == 202, replay.text
    assert replay.json() == first.json()

    status = _status(api, first.json())
    assert status.status_code == 200, status.text
    assert status.json()["state"] == "COMPLETED"
    with api.session()() as db:
        count = db.scalar(
            select(func.count()).select_from(Be1TeacherAssignmentTransferModel).where(
                Be1TeacherAssignmentTransferModel.class_id == class_id,
                Be1TeacherAssignmentTransferModel.principal_ref == api.manager,
                Be1TeacherAssignmentTransferModel.idempotency_key == key,
            )
        )
    assert count == 1


def test_two_managers_can_reuse_a_key_for_distinct_class_transfers(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "manager-key-collision")
    _old_subject, old_ref = _identity(api, "collision-old", rows=((api.organization_id, None),))
    _first_subject, first_ref = _identity(
        api, "collision-first", rows=((api.organization_id, None),)
    )
    _second_subject, second_ref = _identity(
        api, "collision-second", rows=((api.organization_id, None),)
    )
    first_assignment = _assign(api, class_id, old_ref, 1, f"t6b-initial-{uuid4()}")
    assert first_assignment.status_code == 200, first_assignment.text
    with api.session().begin() as db:
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=api.organization_id,
                subject=api.other_manager,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )

    key = f"same-user-key-{uuid4()}"
    first = _reassign(api, class_id, first_ref, 2, key, manager=api.manager)
    assert first.status_code == 202, first.text
    replay = _reassign(api, class_id, first_ref, 2, key, manager=api.manager)
    assert replay.status_code == 202, replay.text
    assert replay.json() == first.json()
    assert _status(api, first.json()).json()["state"] == "COMPLETED"

    second = _reassign(api, class_id, second_ref, 4, key, manager=api.other_manager)
    assert second.status_code == 202, second.text
    assert second.json()["transfer_id"] != first.json()["transfer_id"]
    second_status = _status(api, second.json(), manager=api.other_manager)
    assert second_status.status_code == 200, second_status.text
    assert second_status.json()["state"] == "COMPLETED"

    with api.session()() as db:
        rows = db.scalars(
            select(Be1TeacherAssignmentTransferModel).where(
                Be1TeacherAssignmentTransferModel.class_id == class_id,
                Be1TeacherAssignmentTransferModel.idempotency_key == key,
            )
        ).all()
    assert len(rows) == 2
    assert {row.state for row in rows} == {"COMPLETED"}


def test_story_conflict_compensates_a_reassignment(
    m9b_api: M9bApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = m9b_api
    class_id = _class(api, "compensate")
    old_subject, old_ref = _identity(api, "compensate-old", rows=((api.organization_id, None),))
    new_subject, new_ref = _identity(api, "compensate-new", rows=((api.organization_id, None),))
    first_assignment = _assign(api, class_id, old_ref, 1, f"t6b-initial-{uuid4()}")
    assert first_assignment.status_code == 200, first_assignment.text

    def conflict(_repository, command):
        return StoryTeacherOwnerTransferReceiptV1(
            transfer_id=command.transfer_id,
            organization_ref=command.organization_ref,
            class_ref=command.class_ref,
            action=command.action,
            old_owner_teacher_ref=command.old_owner_teacher_ref,
            new_owner_teacher_ref=command.new_owner_teacher_ref,
            assignment_revision=command.assignment_revision,
            idempotency_key_sha256=story_teacher_owner_transfer_key_sha256(
                organization_ref=command.organization_ref,
                class_ref=command.class_ref,
                transfer_id=command.transfer_id,
            ),
            request_fingerprint_sha256=command.request_fingerprint_sha256,
            outcome="CONFLICT",
            owner_epoch=0,
        )

    monkeypatch.setattr(SqlStoryTeacherOwnerTransferRepository, "transfer_owner", conflict)
    accepted = _reassign(api, class_id, new_ref, 2, f"t6b-compensate-{uuid4()}")
    assert accepted.status_code == 202, accepted.text
    status = _status(api, accepted.json())
    assert status.status_code == 200, status.text
    assert status.json()["state"] == "COMPENSATED_CONFLICT"
    assert status.json()["last_failure_code"] == "RESOURCE_CONFLICT"
    with api.session()() as db:
        rows = db.scalars(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
            )
        ).all()
    active_by_subject = {row.subject: row.active for row in rows}
    assert active_by_subject[old_subject] is True
    assert active_by_subject[new_subject] is False


def test_reconcile_required_replay_resumes_the_same_transfer(
    m9b_api: M9bApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = m9b_api
    class_id = _class(api, "reconcile-resume")
    _old_subject, old_ref = _identity(api, "resume-old", rows=((api.organization_id, None),))
    _new_subject, new_ref = _identity(api, "resume-new", rows=((api.organization_id, None),))
    first_assignment = _assign(api, class_id, old_ref, 1, f"t6b-initial-{uuid4()}")
    assert first_assignment.status_code == 200, first_assignment.text

    original_transfer = SqlStoryTeacherOwnerTransferRepository.transfer_owner
    calls = 0

    def unavailable_once(repository, command):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise StoryTeacherOwnerTransferUnavailable("temporary Story outage")
        return original_transfer(repository, command)

    monkeypatch.setattr(
        SqlStoryTeacherOwnerTransferRepository, "transfer_owner", unavailable_once
    )
    key = f"t6b-resume-{uuid4()}"
    first = _reassign(api, class_id, new_ref, 2, key)
    assert first.status_code == 202, first.text
    pending = _status(api, first.json())
    assert pending.status_code == 200, pending.text
    assert pending.json()["state"] == "RECONCILE_REQUIRED"
    assert pending.json()["last_failure_code"] == "STORY_TRANSFER_UNCERTAIN"

    replay = _reassign(api, class_id, new_ref, 2, key)
    assert replay.status_code == 202, replay.text
    assert replay.json() == first.json()
    completed = _status(api, replay.json())
    assert completed.status_code == 200, completed.text
    assert completed.json()["state"] == "COMPLETED"
    assert calls == 2


def test_be1_downgrade_refuses_while_transfer_rows_exist(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "downgrade-refusal")
    _old_subject, old_ref = _identity(api, "downgrade-old", rows=((api.organization_id, None),))
    _new_subject, new_ref = _identity(api, "downgrade-new", rows=((api.organization_id, None),))
    first_assignment = _assign(api, class_id, old_ref, 1, f"t6b-initial-{uuid4()}")
    assert first_assignment.status_code == 200, first_assignment.text
    accepted = _reassign(api, class_id, new_ref, 2, f"t6b-downgrade-{uuid4()}")
    assert accepted.status_code == 202, accepted.text

    config = Config(str(_BACKEND / "alembic.ini"))
    with pytest.raises(DBAPIError, match="T-6b BE1 downgrade refused"):
        command.downgrade(config, _BE1_TRANSFER_PARENT)
