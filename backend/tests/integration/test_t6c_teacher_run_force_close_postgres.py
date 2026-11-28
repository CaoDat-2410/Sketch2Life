"""T-6c Manager force-close atomicity, authorization, replay and race checks on PostgreSQL."""

# ruff: noqa: F811  (the imported fixture is used as a test argument)

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, delete, event, func, insert, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.infrastructure.config.settings import (
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import OrganizationAssignmentModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tests.integration.story_teacher.test_teacher_run_create_postgres import (
    Api,
    flow,
    headers,
    post_create,
)

_BACKEND = Path(__file__).resolve().parents[2]
_FORCE_CLOSE_PATH = "/api/be1/v1/organizations/{organization_id}/story-runs/{run_id}/force-close"
_CONFLICT_PATH = (
    "/api/be1/v1/organizations/{organization_id}/teachers/{teacher_ref}/"
    "active-story-run-conflict"
)
_ROUNDTRIP_HEAD = "20261122_t6c_0001"
_ROUNDTRIP_PARENT = "20261122_t6b_0002"


def _create_run(d: Api, *, who: str = "t1", class_key: str = "a1") -> tuple[str, int]:
    _occurrence, _offer, body = flow(d, who=who, class_key=class_key)
    created = post_create(d, who, body)
    assert created.status_code == 201, created.text
    run = created.json()["story_run"]
    run_id = str(run["run_id"])
    return run_id, int(_run_metadata(d, run_id)["revision"])


def _force_close(
    d: Api,
    *,
    organization_id: str,
    run_id: str,
    key: str,
    expected_revision: int,
    reason: str = "Manager approved Teacher reassignment",
):
    return d.client.post(
        _FORCE_CLOSE_PATH.format(organization_id=organization_id, run_id=run_id),
        headers=headers(d.subjects["manager"], key),
        json={"expected_revision": expected_revision, "reason": reason},
    )


def _run_metadata(d: Api, run_id: str) -> dict[str, Any]:
    runs = story_tables.story_runs
    with d.sessions()() as db:
        return dict(
            db.execute(
                select(
                    runs.c.run_id,
                    runs.c.run_state,
                    runs.c.revision,
                    runs.c.version,
                    runs.c.active_owner_teacher_id,
                    runs.c.occurrence_ref,
                    runs.c.created_by_actor_ref,
                    runs.c.asset_ref,
                    runs.c.derived_asset_ref,
                ).where(runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )


def test_t6c_atomic_close_releases_lock_records_audit_and_replays_once(api: Api) -> None:
    d = api
    run_id, revision = _create_run(d)
    before = _run_metadata(d, run_id)
    conflict = d.client.get(
        _CONFLICT_PATH.format(
            organization_id=d.organization,
            teacher_ref=d.accounts["t1"],
        ),
        headers=headers(d.subjects["manager"]),
    )
    assert conflict.status_code == 200
    assert conflict.headers["Cache-Control"] == "private, no-store"
    assert conflict.json() == {
        "contract": "ManagerActiveStoryRunConflictV1",
        "run_id": run_id,
        "run_state": before["run_state"],
        "revision": revision,
    }

    reason = "Manager approved Teacher reassignment"
    key = f"t6c-close-{uuid4()}"
    first = _force_close(
        d,
        organization_id=d.organization,
        run_id=run_id,
        key=key,
        expected_revision=revision,
        reason=reason,
    )
    replay = _force_close(
        d,
        organization_id=d.organization,
        run_id=run_id,
        key=key,
        expected_revision=revision,
        reason=reason,
    )
    assert first.status_code == replay.status_code == 200
    assert first.headers["Cache-Control"] == replay.headers["Cache-Control"] == "private, no-store"
    assert first.json() == replay.json() == {
        "contract": "ManagerForceClosedStoryRunV1",
        "run_id": run_id,
        "run_state": "ABANDONED",
        "revision": revision + 1,
    }

    changed = _force_close(
        d,
        organization_id=d.organization,
        run_id=run_id,
        key=key,
        expected_revision=revision,
        reason="Different approved reason",
    )
    assert changed.status_code == 400
    assert changed.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    after = _run_metadata(d, run_id)
    assert after["run_state"] == "ABANDONED"
    assert after["revision"] == revision + 1 and after["version"] == before["version"] + 1
    assert after["active_owner_teacher_id"] is None
    for field in ("occurrence_ref", "created_by_actor_ref", "asset_ref", "derived_asset_ref"):
        assert after[field] == before[field]

    receipts = story_tables.story_command_receipts
    with d.sessions()() as db:
        receipt_rows = db.execute(
            select(receipts).where(
                receipts.c.operation == "FORCE_CLOSE_RUN",
                receipts.c.resource_ref == run_id,
            )
        ).mappings().all()
        audit_rows = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.action == "TEACHER_STORY_RUN_FORCE_CLOSED",
                CoreAuditEntryModel.resource_id == run_id,
            )
        ).all()
    assert len(receipt_rows) == len(audit_rows) == 1
    assert receipt_rows[0]["state"] == "FINAL"
    assert receipt_rows[0]["response_body"] == first.json()
    assert reason not in json.dumps(dict(receipt_rows[0]), default=str)
    audit = audit_rows[0]
    assert (
        audit.organization_id,
        audit.owner_scope_kind,
        audit.owner_scope_ref,
        audit.action,
        audit.resource_type,
        audit.resource_id,
        audit.decision,
    ) == (
        d.organization,
        "ORGANIZATION",
        d.organization,
        "TEACHER_STORY_RUN_FORCE_CLOSED",
        "STORY_RUN",
        run_id,
        "ALLOWED",
    )
    assert audit.actor_ref != d.subjects["manager"]
    assert reason not in repr(audit)

    for mutation in (
        update(receipts)
        .where(receipts.c.operation == "FORCE_CLOSE_RUN", receipts.c.resource_ref == run_id)
        .values(state="PENDING"),
        delete(receipts).where(
            receipts.c.operation == "FORCE_CLOSE_RUN", receipts.c.resource_ref == run_id
        ),
    ):
        with pytest.raises(DBAPIError, match="append-only"), d.sessions().begin() as db:
            db.execute(mutation)


def test_t6c_stale_revision_and_out_of_scope_requests_write_nothing(api: Api) -> None:
    d = api
    run_id, revision = _create_run(d)
    teacher_attempt = d.client.post(
        _FORCE_CLOSE_PATH.format(organization_id=d.organization, run_id=run_id),
        headers=headers(d.subjects["t1"], f"t6c-role-{uuid4()}"),
        json={"expected_revision": revision, "reason": "not a Manager"},
    )
    assert teacher_attempt.status_code == 403
    assert teacher_attempt.json()["code"] == "ACTION_NOT_ALLOWED"

    stale = _force_close(
        d,
        organization_id=d.organization,
        run_id=run_id,
        key=f"t6c-stale-{uuid4()}",
        expected_revision=revision + 1,
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == revision

    foreign = _force_close(
        d,
        organization_id=d.other_organization,
        run_id=run_id,
        key=f"t6c-foreign-{uuid4()}",
        expected_revision=revision,
    )
    unknown = _force_close(
        d,
        organization_id=d.organization,
        run_id=str(uuid4()),
        key=f"t6c-unknown-{uuid4()}",
        expected_revision=revision,
    )
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.json()["code"] == unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    assert set(foreign.json()) == set(unknown.json())

    after = _run_metadata(d, run_id)
    assert after["run_state"] != "ABANDONED"
    assert after["revision"] == revision
    with d.sessions()() as db:
        assert db.scalar(
            select(story_tables.story_command_receipts.c.receipt_id).where(
                story_tables.story_command_receipts.c.operation == "FORCE_CLOSE_RUN",
                story_tables.story_command_receipts.c.resource_ref == run_id,
            )
        ) is None
        assert db.scalar(
            select(CoreAuditEntryModel.audit_id).where(
                CoreAuditEntryModel.action == "TEACHER_STORY_RUN_FORCE_CLOSED",
                CoreAuditEntryModel.resource_id == run_id,
            )
        ) is None


def test_t6c_revoked_manager_cannot_replay_a_completed_receipt(api: Api) -> None:
    d = api
    run_id, revision = _create_run(d)
    key = f"t6c-revoked-{uuid4()}"
    first = _force_close(
        d,
        organization_id=d.organization,
        run_id=run_id,
        key=key,
        expected_revision=revision,
    )
    assert first.status_code == 200
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

    replay = _force_close(
        d,
        organization_id=d.organization,
        run_id=run_id,
        key=key,
        expected_revision=revision,
    )
    assert replay.status_code == 404
    assert replay.json()["code"] == "RESOURCE_NOT_FOUND"
    assert replay.headers["Cache-Control"] == "private, no-store"


def test_t6c_database_failure_rolls_back_run_receipt_and_audit(api: Api) -> None:
    d = api
    run_id, revision = _create_run(d)

    def reject_audit(_mapper, _connection, _target) -> None:
        raise IntegrityError("synthetic audit rejection", {}, RuntimeError("rejected"))

    event.listen(CoreAuditEntryModel, "before_insert", reject_audit)
    try:
        failed = _force_close(
            d,
            organization_id=d.organization,
            run_id=run_id,
            key=f"t6c-rollback-{uuid4()}",
            expected_revision=revision,
        )
    finally:
        event.remove(CoreAuditEntryModel, "before_insert", reject_audit)
    assert failed.status_code == 409
    assert failed.json()["code"] == "RESOURCE_CONFLICT"
    after = _run_metadata(d, run_id)
    assert after["run_state"] != "ABANDONED"
    assert after["revision"] == revision and after["active_owner_teacher_id"] is not None
    with d.sessions()() as db:
        assert db.scalar(
            select(story_tables.story_command_receipts.c.receipt_id).where(
                story_tables.story_command_receipts.c.operation == "FORCE_CLOSE_RUN",
                story_tables.story_command_receipts.c.resource_ref == run_id,
            )
        ) is None
        assert db.scalar(
            select(CoreAuditEntryModel.audit_id).where(
                CoreAuditEntryModel.action == "TEACHER_STORY_RUN_FORCE_CLOSED",
                CoreAuditEntryModel.resource_id == run_id,
            )
        ) is None


@pytest.mark.parametrize("same_key", [True, False], ids=["replay", "distinct-keys"])
def test_t6c_concurrent_requests_close_once(api: Api, same_key: bool) -> None:
    d = api
    run_id, revision = _create_run(d)
    barrier = Barrier(2)
    keys = (f"t6c-race-{uuid4()}", f"t6c-race-{uuid4()}")

    def send(index: int):
        barrier.wait(timeout=10)
        return _force_close(
            d,
            organization_id=d.organization,
            run_id=run_id,
            key=keys[0] if same_key else keys[index],
            expected_revision=revision,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(send, (0, 1)))
    statuses = sorted(response.status_code for response in responses)
    assert statuses == ([200, 200] if same_key else [200, 409])
    if not same_key:
        conflict = next(response for response in responses if response.status_code == 409)
        assert conflict.json()["code"] == "INVALID_STATE_TRANSITION"
    with d.sessions()() as db:
        receipt_count = db.scalar(
            select(func.count())
            .select_from(story_tables.story_command_receipts)
            .where(
                story_tables.story_command_receipts.c.operation == "FORCE_CLOSE_RUN",
                story_tables.story_command_receipts.c.resource_ref == run_id,
            )
        )
    assert receipt_count == 1


@pytest.fixture
def t6c_roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T6C_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip("set T6C_ROUNDTRIP_DATABASE_URL to a disposable Story round-trip database")
    database_name = url.rsplit("/", 1)[-1]
    if not all(part in database_name for part in ("be1_acceptance", "t6c", "roundtrip")):
        pytest.fail("T6C_ROUNDTRIP_DATABASE_URL must identify a disposable t6c round-trip database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(_BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_t6c_downgrade_refuses_force_close_receipt_history(t6c_roundtrip) -> None:
    from uuid import uuid4

    from tests.integration.story_teacher.test_teacher_run_roundtrip_postgres import _insert_run

    config, engine = t6c_roundtrip
    run_id = _insert_run(engine, run_state="ABANDONED")
    now = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            insert(story_tables.story_command_receipts).values(
                receipt_id=str(uuid4()),
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref="synthetic-t6c-org",
                operation="FORCE_CLOSE_RUN",
                idempotency_scope_kind="STORY_RUN",
                idempotency_scope_ref="a" * 64,
                idempotency_key_sha256="b" * 64,
                request_fingerprint_sha256="c" * 64,
                state="FINAL",
                response_status=200,
                response_resource_version=2,
                response_body={
                    "contract": "ManagerForceClosedStoryRunV1",
                    "run_id": run_id,
                    "run_state": "ABANDONED",
                    "revision": 2,
                },
                resource_ref=run_id,
                resource_version=2,
                state_version=1,
                created_at=now,
                finalized_at=now,
            )
        )
    with pytest.raises(DBAPIError, match="force-close receipts exist"):
        command.downgrade(config, _ROUNDTRIP_PARENT)
    with engine.connect() as connection:
        versions = set(
            connection.execute(text("select version_num from alembic_version")).scalars()
        )
        receipts = set(
            connection.execute(
                select(story_tables.story_command_receipts.c.operation).where(
                    story_tables.story_command_receipts.c.resource_ref == run_id
                )
            ).scalars()
        )
    # the refused downgrade rolls back whole, including the later receipt-check revision
    assert "20261126_as_0003" in versions and _ROUNDTRIP_PARENT not in versions
    assert receipts == {"FORCE_CLOSE_RUN"}
