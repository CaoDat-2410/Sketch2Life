"""PostgreSQL integration tests for T-6c (Manager emergency force-close; not built yet)."""

# ruff: noqa: F811

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import select

from sketch2life.infrastructure.persistence.be1_models import OrganizationAssignmentModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tests.integration.story_teacher.test_teacher_run_create_postgres import (
    Api,
    api,  # noqa: F401 - pytest fixture
    flow,
    headers,
    post_create,
)

_BACKEND = Path(__file__).resolve().parents[2]
_FORCE_CLOSE_PARENT = "20261122_t6b_0002"


def _conflict_url(d: Api, teacher_account: str, *, org: str | None = None) -> str:
    return (
        f"/api/be1/v1/organizations/{org or d.organization}/teachers/"
        f"{teacher_account}/active-story-run-conflict"
    )


def _force_close_url(d: Api, run_id: str, *, org: str | None = None) -> str:
    return f"/api/be1/v1/organizations/{org or d.organization}/story-runs/{run_id}/force-close"


@pytest.mark.integration
def test_t6c_conflict_read_and_atomic_force_close_releases_lock_writes_receipt_and_audit(
    api: Api,
) -> None:
    """covers: D_T-6C_PROMPT.md §6 test_t6c_atomic_close_releases_lock_receipt_audit"""
    d = api
    _occ, _offer, body = flow(d, who="t2", class_key="a2")
    created = post_create(d, "t2", body)
    assert created.status_code == 201, created.text
    run_id = created.json()["story_run"]["run_id"]
    run_revision = int(created.json()["story_run"]["run_revision"])

    conflict = d.client.get(_conflict_url(d, d.accounts["t2"]), headers=headers(d.subjects["manager"]))
    assert conflict.status_code == 200, conflict.text
    assert conflict.headers["Cache-Control"] == "private, no-store"
    assert set(conflict.json()) == {"contract", "run_id", "run_state", "revision"}
    assert conflict.json()["run_id"] == run_id
    assert conflict.json()["revision"] == run_revision

    reason = "Teacher reassigned urgently; unlock slot for next session."
    closed = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision, "reason": reason},
        headers=headers(d.subjects["manager"], f"t6c-close-{uuid4()}"),
    )
    assert closed.status_code == 200, closed.text
    assert closed.headers["Cache-Control"] == "private, no-store"
    assert set(closed.json()) == {"contract", "run_id", "run_state", "revision"}
    assert closed.json()["run_id"] == run_id
    assert closed.json()["run_state"] == "ABANDONED"
    assert closed.json()["revision"] == run_revision + 1

    with d.sessions()() as db:
        run_row = db.execute(
            select(
                story_tables.story_runs.c.run_state,
                story_tables.story_runs.c.active_owner_teacher_id,
                story_tables.story_runs.c.revision,
            ).where(story_tables.story_runs.c.run_id == run_id)
        ).one()
        receipts = db.execute(
            select(story_tables.story_command_receipts).where(
                story_tables.story_command_receipts.c.operation == "FORCE_CLOSE_RUN",
                story_tables.story_command_receipts.c.resource_ref == run_id,
            )
        ).mappings().all()
        audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.organization_id == d.organization,
                CoreAuditEntryModel.action == "TEACHER_STORY_RUN_FORCE_CLOSED",
                CoreAuditEntryModel.resource_type == "STORY_RUN",
                CoreAuditEntryModel.resource_id == run_id,
            )
        ).all()

    assert run_row.run_state == "ABANDONED"
    assert run_row.active_owner_teacher_id is None
    assert run_row.revision == run_revision + 1
    assert len(receipts) == 1
    assert receipts[0]["state"] == "FINAL"
    assert len(audits) == 1
    assert audits[0].decision.upper() == "ALLOWED"
    assert reason not in repr(audits[0])
    assert reason not in repr(receipts[0])

    after_close = d.client.get(
        _conflict_url(d, d.accounts["t2"]), headers=headers(d.subjects["manager"])
    )
    assert after_close.status_code == 404
    assert after_close.json()["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.integration
def test_t6c_same_key_concurrency_replays_once_and_distinct_keys_close_once(api: Api) -> None:
    """covers: D_T-6C_PROMPT.md §6 test_t6c_same_key_concurrency_replays_once"""
    d = api
    _occ, _offer, body = flow(d, who="t2", class_key="a2")
    created = post_create(d, "t2", body)
    assert created.status_code == 201, created.text
    run_id = created.json()["story_run"]["run_id"]
    run_revision = int(created.json()["story_run"]["run_revision"])

    key = f"t6c-race-{uuid4()}"
    reason = "Emergency close during race check."
    barrier = Barrier(2)

    def send() -> tuple[int, dict[str, object]]:
        barrier.wait()
        resp = d.client.post(
            _force_close_url(d, run_id),
            json={"expected_revision": run_revision, "reason": reason},
            headers=headers(d.subjects["manager"], key),
        )
        return resp.status_code, resp.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: send(), range(2)))

    assert [code for code, _ in results] == [200, 200]
    assert results[0][1] == results[1][1]

    changed_payload = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision, "reason": "Different reason text."},
        headers=headers(d.subjects["manager"], key),
    )
    assert changed_payload.status_code == 400
    assert changed_payload.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    distinct_key = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision + 1, "reason": reason},
        headers=headers(d.subjects["manager"], f"t6c-second-{uuid4()}"),
    )
    assert distinct_key.status_code == 409
    assert distinct_key.json()["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.integration
def test_t6c_stale_revision_and_cross_org_and_revoked_manager_refused(api: Api) -> None:
    """covers: D_T-6C_PROMPT.md §6 stale/cross_org/revoked_manager"""
    d = api
    _occ, _offer, body = flow(d, who="t2", class_key="a2")
    created = post_create(d, "t2", body)
    assert created.status_code == 201, created.text
    run_id = created.json()["story_run"]["run_id"]
    run_revision = int(created.json()["story_run"]["run_revision"])

    stale = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision + 10, "reason": "Stale check."},
        headers=headers(d.subjects["manager"], f"t6c-stale-{uuid4()}"),
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == run_revision

    non_manager = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision, "reason": "Non-manager check."},
        headers=headers(d.subjects["t1"], f"t6c-role-{uuid4()}"),
    )
    assert non_manager.status_code == 403
    assert non_manager.json()["code"] == "ACTION_NOT_ALLOWED"

    foreign = d.client.get(
        _conflict_url(d, d.accounts["t2"], org=d.other_organization),
        headers=headers(d.subjects["manager"]),
    )
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "RESOURCE_NOT_FOUND"

    replay_key = f"t6c-revoked-{uuid4()}"
    ok = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision, "reason": "Valid close before revoke."},
        headers=headers(d.subjects["manager"], replay_key),
    )
    assert ok.status_code == 200

    with d.sessions().begin() as db:
        assignment = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == d.organization,
                OrganizationAssignmentModel.subject == d.subjects["manager"],
                OrganizationAssignmentModel.role == "school_admin",
            )
        )
        assert assignment is not None
        assignment.active = False

    revoked_replay = d.client.post(
        _force_close_url(d, run_id),
        json={"expected_revision": run_revision, "reason": "Valid close before revoke."},
        headers=headers(d.subjects["manager"], replay_key),
    )
    assert revoked_replay.status_code == 404
    assert revoked_replay.json()["code"] == "RESOURCE_NOT_FOUND"
