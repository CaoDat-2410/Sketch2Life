"""Story lifecycle adapter: step-4 plan and purge, finalize, fence (DTR Draft 6 §5.1 T2, step 4-5).

The SQL adapter is driven through a recording session with its snapshot read replaced; no
database is used. The plan function, the tombstone rule and the statements are checked.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.core_foundation import CoreAssetPurgeError
from sketch2life.application.ports.story_run_lifecycle import (
    StoryLifecycleError,
    StoryPurgePlan,
    is_projection_body,
    lifecycle_audit_id,
    lifecycle_projection_body,
    lifecycle_request_id,
    sha256_hex,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import (
    S10_RUN_COLUMNS,
    SqlStoryLifecycleStore,
    StoryRunSnapshot,
    story_plan_ids,
    tombstone_fingerprint,
)

RUN = "22222222-2222-4222-8222-222222222222"
REQUEST = lifecycle_request_id(RUN)
PROJECTION = lifecycle_projection_body(
    run_id=RUN, run_state="DELETE_PENDING", revision=3, version=4
)


def _snapshot(**overrides: Any) -> StoryRunSnapshot:
    values: dict[str, Any] = {
        "run_id": RUN,
        "run_state": "DELETE_PENDING",
        "revision": 3,
        "version": 4,
        "s10_present": True,
        "child_ids": ("run_inputs:i1", "story_revisions:s1", "story_scenes:c1"),
        "receipts": (
            ("r-create", "CREATE_RUN", "f" * 64, {"run_id": RUN}),
            ("r-cancel-m2", "CANCEL_RUN", "e" * 64, {"story_run": {"subject_label": "x"}}),
            ("r-cancel-new", "CANCEL_RUN", "d" * 64, PROJECTION),
            ("r-delete", "DELETE_RUN", "c" * 64, PROJECTION),
            ("r-done", "CONFIRM_SUBJECT", tombstone_fingerprint("r-done"), {"decision": "x"}),
        ),
    }
    values.update(overrides)
    return StoryRunSnapshot(**values)


def test_the_story_plan_lists_children_untombstoned_receipts_and_the_run() -> None:
    assert story_plan_ids(_snapshot()) == tuple(
        sorted(
            [
                "run_inputs:i1",
                "story_revisions:s1",
                "story_scenes:c1",
                "receipt:r-create",
                "receipt:r-cancel-m2",
                "run:" + RUN,
            ]
        )
    )


def test_a_purged_run_has_an_empty_plan() -> None:
    clean = _snapshot(
        s10_present=False,
        child_ids=(),
        receipts=(
            ("r-create", "CREATE_RUN", tombstone_fingerprint("r-create"), {"run_id": RUN}),
            ("r-cancel", "CANCEL_RUN", "e" * 64, PROJECTION),
        ),
    )
    assert story_plan_ids(clean) == ()


def test_tombstone_and_projection_predicates() -> None:
    assert tombstone_fingerprint("abc") == sha256_hex("tombstone:abc")
    assert is_projection_body(PROJECTION)
    assert not is_projection_body({**PROJECTION, "story_run": {}})
    assert not is_projection_body({"request_id": "x", "story_run": {}, "purge_state": "PENDING"})


def test_s10_columns_are_the_dtr_list_and_exclude_identity_scope_state_and_versions() -> None:
    assert set(S10_RUN_COLUMNS) == {
        "asset_ref",
        "derived_asset_ref",
        "subject_label",
        "confidence",
        "result_sha256",
        "raw_body_sha256",
        "child_age_months",
        "profile_ref",
        "provider_job_id",
        "provider_attempt_id",
        "understanding_revision",
        "error_code",
        "current_input_revision",
        # FEAT-066 T-1a: the pointer to the current video generation.
        "current_video_generation_id",
    }
    assert not {"run_id", "actor_scope_ref", "run_state", "revision", "version"} & set(
        S10_RUN_COLUMNS
    )


class _Session:
    def __init__(self, scalar: Any = "a" * 64, rowcount: int = 1) -> None:
        self.statements: list[Any] = []
        self._scalar = scalar
        self._rowcount = rowcount

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.statements.append(statement)

        class _Result:
            rowcount = self._rowcount

        return _Result()

    def scalar(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._scalar

    def tables(self) -> list[str]:
        return [str(getattr(getattr(s, "table", None), "name", "")) for s in self.statements]


class _Sessions:
    def __init__(self, session: _Session) -> None:
        self.session = session

    @contextmanager
    def begin(self) -> Iterator[_Session]:
        yield self.session

    @contextmanager
    def __call__(self) -> Iterator[_Session]:
        yield self.session


def _store(
    monkeypatch: pytest.MonkeyPatch, snapshot: StoryRunSnapshot, **session: Any
) -> tuple[SqlStoryLifecycleStore, _Session]:
    fake = _Session(**session)
    store = SqlStoryLifecycleStore(_Sessions(fake))  # type: ignore[arg-type]
    monkeypatch.setattr(store, "_snapshot", lambda _session, _run_id, lock: snapshot)
    return store, fake


def test_purge_story_content_deletes_children_nulls_s10_and_tombstones_in_one_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _snapshot()
    store, session = _store(monkeypatch, snapshot)
    store.purge_story_content(StoryPurgePlan(RUN, story_plan_ids(snapshot)))
    tables = session.tables()
    assert tables[:10] == [
        # FEAT-066 T-1a: video scenes, the run pointer, then the generations go before the reviews.
        "video_generation_scenes",
        "runs",
        "video_generations",
        "story_revision_reviews",
        "review_decisions",
        "story_scenes",
        "story_revisions",
        "understanding_revisions",
        # FEAT-066 T-2c: the transcript text is deleted before its run input (BR-23).
        "transcript_revisions",
        "run_inputs",
    ]
    run_update = session.statements[10]
    assert run_update.table.name == "runs"
    assert {name for name in run_update._values} == set(S10_RUN_COLUMNS)
    receipt_updates = session.statements[11:]
    assert len(receipt_updates) == 2  # the CREATE_RUN fingerprint and the M2 CANCEL_RUN body
    dialect: Any = postgresql.dialect
    params = [dict(update.compile(dialect=dialect()).params) for update in receipt_updates]
    assert params[0]["request_fingerprint_sha256"] == tombstone_fingerprint("r-create")
    assert params[1]["response_body"] == PROJECTION


@pytest.mark.parametrize("state", ("SCRIPT_REVIEW", "COMPLETED"))
def test_purge_refuses_a_run_outside_the_purge_states(
    monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    store, session = _store(monkeypatch, _snapshot(run_state=state))
    with pytest.raises(StoryLifecycleError, match="RUN_NOT_PURGEABLE"):
        store.purge_story_content(StoryPurgePlan(RUN, ()))
    assert session.statements == []


def test_purge_refuses_a_plan_that_no_longer_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    store, session = _store(monkeypatch, _snapshot())
    with pytest.raises(StoryLifecycleError, match="PLAN_CHANGED"):
        store.purge_story_content(StoryPurgePlan(RUN, ("run_inputs:i1",)))
    assert session.statements == []


def test_finalize_writes_deleted_the_aggregate_and_the_completed_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean = _snapshot(s10_present=False, child_ids=(), receipts=())
    store, session = _store(monkeypatch, clean)
    assert store.finalize_deleted(RUN, REQUEST) is True
    assert session.tables() == ["runs", "core_aggregate_revisions", "core_audit_entries"]
    dialect: Any = postgresql.dialect
    run_params = dict(session.statements[0].compile(dialect=dialect()).params)
    assert run_params["run_state"] == "DELETED"
    assert run_params["revision"] == 4 and run_params["version"] == 5
    audit = dict(session.statements[2].compile(dialect=dialect()).params)
    assert audit["audit_id"] == lifecycle_audit_id(REQUEST, "lifecycle.completed")
    assert audit["decision"] == "completed:" + REQUEST and audit["organization_id"] is None
    assert audit["actor_ref"] == "be1-lifecycle-worker"


def test_finalize_is_idempotent_and_refuses_unpurged_or_live_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, session = _store(monkeypatch, _snapshot(run_state="DELETED"))
    assert store.finalize_deleted(RUN, REQUEST) is False
    assert session.statements == []
    store, _ = _store(monkeypatch, _snapshot())  # content still present
    with pytest.raises(StoryLifecycleError, match="STORY_CONTENT_NOT_PURGED"):
        store.finalize_deleted(RUN, REQUEST)
    store, _ = _store(monkeypatch, _snapshot(run_state="SCRIPT_REVIEW"))
    with pytest.raises(StoryLifecycleError, match="RUN_NOT_PURGEABLE"):
        store.finalize_deleted(RUN, REQUEST)
    with pytest.raises(StoryLifecycleError, match="REQUEST_ID_MISMATCH"):
        store.finalize_deleted(RUN, lifecycle_request_id("33333333-3333-4333-8333-333333333333"))


def test_a_lost_finalize_update_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    clean = _snapshot(s10_present=False, child_ids=(), receipts=())
    store, _session = _store(monkeypatch, clean, rowcount=0)
    with pytest.raises(StoryLifecycleError, match="RUN_NOT_PURGEABLE"):
        store.finalize_deleted(RUN, REQUEST)


@pytest.mark.parametrize("bad", ("story_run:" + RUN, RUN[:9] + "ABCD" + RUN[13:], "", "x" * 36))
def test_every_entry_validates_the_run_ref(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    store, session = _store(monkeypatch, _snapshot())
    for call in (
        lambda: store.lifecycle_state(bad),
        lambda: store.plan_story_purge(bad),
        lambda: store.purge_story_content(StoryPurgePlan(bad, ())),
        lambda: store.finalize_deleted(bad, REQUEST),
        lambda: store.insert_reconciliation_event(bad),
    ):
        with pytest.raises(CoreAssetPurgeError, match="RUN_REF_INVALID"):
            call()
    assert session.statements == []


def test_the_reconciliation_insert_is_judged_by_returning_not_by_rowcount() -> None:
    """Owner run 20261119-103216: seen=1 but inserted=0. The insert now uses RETURNING."""
    from datetime import UTC, datetime

    from sketch2life.application.ports.story_run_lifecycle import (
        CANCEL_EVENT_TYPE,
        lifecycle_event_id,
    )
    from sketch2life.infrastructure.persistence.story_lifecycle_store import (
        reconciliation_event_statement,
    )

    statement = reconciliation_event_statement(
        run_id=RUN, scope_ref="a" * 64, revision=2, now=datetime(2026, 11, 19, tzinfo=UTC)
    )
    dialect: Any = postgresql.dialect
    compiled = statement.compile(dialect=dialect())
    sql = str(compiled)
    assert "ON CONFLICT (event_id) DO NOTHING" in sql
    assert sql.rstrip().endswith("RETURNING core_outbox_events.event_id")
    params = dict(compiled.params)
    assert params["event_id"] == lifecycle_event_id(REQUEST, CANCEL_EVENT_TYPE)
    assert params["organization_id"] is None and params["owner_scope_kind"] == "PARENT_ACCOUNT"


class _ReconcileSession:
    """Answers the three reads of ``insert_reconciliation_event`` and records the writes."""

    def __init__(self, *, returned: Any, state: str = "DELETE_PENDING", has_event: bool = False):
        self.returned = returned
        self.state = state
        self.has_event = has_event
        self.statements: list[Any] = []

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.statements.append(statement)
        outer = self

        class _Result:
            rowcount = 0  # deliberately wrong: the code must not rely on it

            def one_or_none(self) -> Any:
                from types import SimpleNamespace

                return SimpleNamespace(
                    run_state=outer.state, revision=2, actor_scope_ref="a" * 64
                )

            def scalar_one_or_none(self) -> Any:
                return outer.returned

        return _Result()

    def scalar(self, *_args: Any, **_kwargs: Any) -> Any:
        return self.has_event


@pytest.mark.parametrize(("returned", "expected"), (("event-id", True), (None, False)))
def test_insert_reconciliation_event_reports_what_returning_returned(
    returned: Any, expected: bool
) -> None:
    session = _ReconcileSession(returned=returned)
    store = SqlStoryLifecycleStore(_Sessions(session))  # type: ignore[arg-type]
    assert store.insert_reconciliation_event(RUN) is expected
    tables = [str(getattr(getattr(s, "table", None), "name", "")) for s in session.statements]
    assert tables[-2:] == ["core_aggregate_revisions", "core_outbox_events"]


@pytest.mark.parametrize(("state", "has_event"), (("DELETED", False), ("DELETE_PENDING", True)))
def test_insert_reconciliation_event_skips_runs_that_need_no_event(
    state: str, has_event: bool
) -> None:
    session = _ReconcileSession(returned="event-id", state=state, has_event=has_event)
    store = SqlStoryLifecycleStore(_Sessions(session))  # type: ignore[arg-type]
    assert store.insert_reconciliation_event(RUN) is False
    assert len(session.statements) == 1  # only the locked run read
