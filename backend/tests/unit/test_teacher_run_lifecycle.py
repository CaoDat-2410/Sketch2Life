"""FEAT-066 T-13a: cancel and delete of a Teacher run (FR-C-08), without a database.

SRS l.500, l.1673-1674, UC-07 l.1465, UC-11 l.1513, l.364, l.593, l.1425. The repository is driven
with a statement-recording session, the Story store and the consumer with the fakes of the Parent
suites, and the AI Jobs notice store with a recording engine. Parent rows are asserted byte for
byte (``organization_id`` stays ``None``); Teacher rows carry the organization.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.ai_jobs import CancellationNotice
from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import (
    RunActor,
    RunActorKind,
    TeacherRunAccess,
)
from sketch2life.application.ports.story_run_lifecycle import (
    CANCEL_ELIGIBLE_STATES,
    CANCEL_EVENT_TYPE,
    DELETE_ELIGIBLE_STATES,
    DELETE_EVENT_TYPE,
    lifecycle_audit_id,
    lifecycle_event_id,
    lifecycle_request_id,
)
from sketch2life.application.services.ai_jobs import notice_matches
from sketch2life.domain.ai_jobs.model import AiJob
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlParentLifecycleNoticeStore
from sketch2life.infrastructure.persistence import story_lifecycle_store as store_module
from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
    NOTICE_REASON_CODES,
    SqlLifecycleAuditWriter,
    SqlLifecycleReceiptStore,
    organization_id_of,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _principal_scope_ref,
)
from tests.unit.test_be1_lifecycle_consumer import (
    EVENT_ID,
    REQUEST_ID,
    _leased_event,
    make_harness,
)
from tests.unit.test_core_run_asset_purge import RUN

PRINCIPAL = VerifiedPrincipal("teacher-1", "issuer-1", frozenset({"teacher"}))
DIGEST = _principal_scope_ref(PRINCIPAL)
ORG = "org-t13a-1"
RUN_ID = "22222222-2222-4222-8222-222222222222"
CHILD = "33333333-3333-4333-8333-333333333333"
REQUEST = lifecycle_request_id(RUN_ID)
TEACHER = RunActor(RunActorKind.TEACHER, "account-1")
PARENT = RunActor(RunActorKind.PARENT, "account-1")
_DIALECT = postgresql.dialect()  # type: ignore[no-untyped-call]


def _params(statement: Any) -> dict[str, Any]:
    return dict(statement.compile(dialect=_DIALECT).params)


class _Result:
    def __init__(self, value: Any = None, rowcount: int = 1) -> None:
        self._value = value
        self.rowcount = rowcount

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> Any:
        return self._value


class _Session:
    def __init__(self, receipt: Any = None) -> None:
        self.receipt = receipt
        self.statements: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> _Result:
        self.statements.append(statement)
        if getattr(getattr(statement, "table", None), "name", "") == "runs":
            return _Result(rowcount=1)
        return _Result(self.receipt)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def writes_to(self, table: str) -> list[Any]:
        return [
            s for s in self.statements if getattr(getattr(s, "table", None), "name", "") == table
        ]


def _repository(
    monkeypatch: pytest.MonkeyPatch,
    *,
    teacher: bool,
    state: str = "SCRIPT_REVIEW",
    class_state: str = "active",
    receipt: Any = None,
) -> tuple[SqlParentStoryRunRepository, _Session, dict[str, Any]]:
    session = _Session(receipt)
    repository = SqlParentStoryRunRepository(
        session,  # type: ignore[arg-type]
        actor=TEACHER if teacher else None,
    )
    stored: dict[str, Any] = {}
    run = {
        "run_id": RUN_ID,
        "run_state": state,
        "revision": 7,
        "version": 9,
        "actor_scope_kind": "ORGANIZATION" if teacher else "PARENT_ACCOUNT",
        "actor_scope_ref": ORG if teacher else DIGEST,
    }
    access = TeacherRunAccess("class-a", class_state) if teacher else None
    monkeypatch.setattr(repository, "_owned_run_access", lambda *_a, **_k: (dict(run), access))
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_k: None)
    monkeypatch.setattr(
        repository, "_store_idempotency_receipt", lambda **kwargs: stored.update(kwargs)
    )
    return repository, session, stored


def _cancel(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": PRINCIPAL,
        "run_id": RUN_ID,
        "expected_revision": 7,
        "idempotency_key": "cancel-1",
    }
    values.update(overrides)
    return repository.cancel_run(**values)


def _delete(repository: SqlParentStoryRunRepository) -> Any:
    return repository.delete_run(principal=PRINCIPAL, run_id=RUN_ID, idempotency_key="delete-1")


# ----------------------------------------------------------------------- the accept rows
@pytest.mark.parametrize("is_cancel", [True, False])
def test_a_teacher_command_writes_organization_rows_and_a_command_scope_receipt(
    monkeypatch: pytest.MonkeyPatch, is_cancel: bool
) -> None:
    state = "SCRIPT_REVIEW" if is_cancel else "COMPLETED"
    repository, session, stored = _repository(monkeypatch, teacher=True, state=state)
    record = _cancel(repository) if is_cancel else _delete(repository)
    assert record.run_state == "DELETE_PENDING" and record.revision == 8 and record.version == 10
    event_type = CANCEL_EVENT_TYPE if is_cancel else DELETE_EVENT_TYPE
    aggregate = _params(session.writes_to("core_aggregate_revisions")[0])
    outbox = _params(session.writes_to("core_outbox_events")[0])
    audit = _params(session.writes_to("core_audit_entries")[0])
    for row in (aggregate, outbox, audit):
        assert row["organization_id"] == ORG
        assert row["owner_scope_kind"] == "ORGANIZATION" and row["owner_scope_ref"] == ORG
    assert outbox["event_id"] == lifecycle_event_id(REQUEST, event_type)
    assert outbox["payload"]["reason_code"] == (
        "TEACHER_CANCEL_REQUESTED" if is_cancel else "TEACHER_DELETE_REQUESTED"
    )
    assert outbox["payload"]["actor_ref"] == DIGEST  # the principal digest, never a name
    action = "lifecycle.cancel_accepted" if is_cancel else "lifecycle.delete_accepted"
    assert audit["audit_id"] == lifecycle_audit_id(REQUEST, action)
    assert audit["actor_ref"] == DIGEST and audit["resource_id"] == RUN_ID
    # the receipt is stored through the command scope of the caller (never the owner row)
    assert stored["scope_kind"] == "STORY_RUN" and stored["scope_ref"] == RUN_ID
    assert stored["response_body"]["run_state"] == "DELETE_PENDING"
    assert session.commits == 1
    # the run update releases the Parent lock column only (the Teacher lock column is T-4b2, H1)
    run_update = _params(session.writes_to("runs")[0])
    assert run_update["active_owner_parent_account_id"] is None


@pytest.mark.parametrize("is_cancel", [True, False])
def test_a_parent_command_keeps_its_rows_byte_for_byte(
    monkeypatch: pytest.MonkeyPatch, is_cancel: bool
) -> None:
    state = "SCRIPT_REVIEW" if is_cancel else "COMPLETED"
    repository, session, _stored = _repository(monkeypatch, teacher=False, state=state)
    _cancel(repository) if is_cancel else _delete(repository)
    for table in ("core_aggregate_revisions", "core_outbox_events", "core_audit_entries"):
        row = _params(session.writes_to(table)[0])
        assert row["organization_id"] is None
        assert row["owner_scope_kind"] == "PARENT_ACCOUNT" and row["owner_scope_ref"] == DIGEST
    outbox = _params(session.writes_to("core_outbox_events")[0])
    assert outbox["payload"]["reason_code"] == (
        "PARENT_CANCEL_REQUESTED" if is_cancel else "PARENT_DELETE_REQUESTED"
    )


def test_the_aggregate_upsert_is_keyed_by_the_owner_scope_of_the_run() -> None:
    session = _Session()
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    repository._upsert_run_aggregate(
        run_id=RUN_ID,
        scope_kind="ORGANIZATION",
        scope_ref=ORG,
        revision=3,
        now=datetime.now(UTC),
    )
    sql = str(session.statements[0].compile(dialect=_DIALECT))
    assert "ON CONFLICT (aggregate_id) DO UPDATE" in sql
    assert _params(session.statements[0])["organization_id"] == ORG
    assert "core_aggregate_revisions.owner_scope_kind = %(owner_scope_kind_1)s" in sql


# -------------------------------------------------------------------- the class state (D7)
@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_teacher_in_a_read_only_class_is_refused_after_the_replay_check(
    monkeypatch: pytest.MonkeyPatch, class_state: str
) -> None:
    for command in (_cancel, _delete):
        repository, session, stored = _repository(
            monkeypatch,
            teacher=True,
            class_state=class_state,
            state="SCRIPT_REVIEW" if command is _cancel else "COMPLETED",
        )
        with pytest.raises(ParentStoryRunError) as caught:
            command(repository)
        assert (caught.value.status_code, caught.value.code) == (409, "INVALID_STATE_TRANSITION")
        assert stored == {} and session.commits == 0 and session.rollbacks == 1
        assert session.writes_to("core_outbox_events") == []
        assert session.writes_to("runs") == []


def test_a_replay_of_an_earlier_success_is_returned_in_a_read_only_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.unit.test_parent_story_run_cancel_repository import _fingerprint

    body = {
        "run_id": RUN_ID,
        "run_state": "DELETE_PENDING",
        "revision": 8,
        "version": 10,
        "lifecycle_request_ref": REQUEST,
        "purge_state": "PENDING",
    }
    receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": RUN_ID,
        "request_fingerprint_sha256": _fingerprint({"run_id": RUN_ID, "expected_revision": 7}),
        "state": "FINAL",
        "response_status": 202,
        "response_body": body,
    }
    repository, session, stored = _repository(
        monkeypatch, teacher=True, class_state="suspended", state="DELETE_PENDING", receipt=receipt
    )
    record = _cancel(repository)
    assert record.run_state == "DELETE_PENDING" and record.revision == 8
    assert stored == {} and session.commits == 1 and session.writes_to("runs") == []
    # the receipt lookup read the command scope of the Teacher, not the Parent kind
    lookup = next(s for s in session.statements if hasattr(s, "whereclause"))
    params = _params(lookup)
    assert "ORGANIZATION" in params.values() and DIGEST in params.values()


def test_the_error_order_is_replay_then_class_then_revision_then_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # a stale revision in an active class is the 409 STALE_REVISION; a non-cancellable state next
    repository, _session, _stored = _repository(monkeypatch, teacher=True)
    with pytest.raises(ParentStoryRunError) as stale:
        _cancel(repository, expected_revision=3)
    assert (stale.value.code, stale.value.current_version) == ("STALE_REVISION", 7)
    repository, _session, _stored = _repository(monkeypatch, teacher=True, state="COMPLETED")
    with pytest.raises(ParentStoryRunError) as state:
        _cancel(repository)
    assert state.value.code == "INVALID_STATE_TRANSITION"
    # a read-only class wins over a stale revision (the class is checked first)
    repository, _session, _stored = _repository(monkeypatch, teacher=True, class_state="suspended")
    with pytest.raises(ParentStoryRunError) as read_only:
        _cancel(repository, expected_revision=3)
    assert read_only.value.code == "INVALID_STATE_TRANSITION"


def test_delete_eligible_states_include_abandoned_and_cancel_excludes_the_closed_ones() -> None:
    assert {"COMPLETED", "FAILED", "ABANDONED"} == DELETE_ELIGIBLE_STATES
    assert not CANCEL_ELIGIBLE_STATES & DELETE_ELIGIBLE_STATES
    assert "DELETE_PENDING" not in CANCEL_ELIGIBLE_STATES


# --------------------------------------------------------------- the Story store (D4a sites)
def test_the_story_store_has_no_parent_only_kind_filter_left() -> None:
    import inspect

    source = inspect.getsource(store_module)
    assert "actor_scope_kind == PARENT_SCOPE_KIND" not in source
    assert "owner_scope_kind=PARENT_SCOPE_KIND" not in source
    assert "_LIFECYCLE_SCOPE_KINDS" in source


@pytest.mark.parametrize(
    ("kind", "organization"), [("PARENT_ACCOUNT", None), ("ORGANIZATION", ORG)]
)
def test_the_reconciliation_event_carries_the_scope_of_the_run(
    kind: str, organization: str | None
) -> None:
    ref = ORG if organization else "a" * 64
    statement = store_module.reconciliation_event_statement(
        run_id=RUN_ID,
        scope_ref=ref,
        revision=4,
        now=datetime(2026, 11, 21, tzinfo=UTC),
        scope_kind=kind,
    )
    params = _params(statement)
    assert params["organization_id"] == organization
    assert params["owner_scope_kind"] == kind and params["owner_scope_ref"] == ref
    default = store_module.reconciliation_event_statement(
        run_id=RUN_ID, scope_ref="a" * 64, revision=4, now=datetime(2026, 11, 21, tzinfo=UTC)
    )
    assert _params(default)["owner_scope_kind"] == "PARENT_ACCOUNT"


class _StoreSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        return SimpleNamespace(rowcount=1)

    def scalar(self, *_a: Any, **_k: Any) -> Any:
        return ORG


class _Sessions:
    def __init__(self, session: _StoreSession) -> None:
        self.session = session

    @contextmanager
    def begin(self) -> Any:
        yield self.session


@pytest.mark.parametrize(
    ("kind", "organization"), [("PARENT_ACCOUNT", None), ("ORGANIZATION", ORG)]
)
def test_finalize_copies_the_scope_of_the_run_into_the_aggregate_and_the_audit(
    monkeypatch: pytest.MonkeyPatch, kind: str, organization: str | None
) -> None:
    session = _StoreSession()
    store = store_module.SqlStoryLifecycleStore(_Sessions(session))  # type: ignore[arg-type]
    snapshot = store_module.StoryRunSnapshot(
        run_id=RUN_ID,
        run_state="DELETE_PENDING",
        revision=3,
        version=4,
        s10_present=False,
        child_ids=(),
        receipts=(),
        scope_kind=kind,
    )
    monkeypatch.setattr(store, "_snapshot", lambda _s, _r, lock: snapshot)
    monkeypatch.setattr(
        store_module.SqlStoryLifecycleStore, "_scope_ref", staticmethod(lambda _s, _r: ORG)
    )
    assert store.finalize_deleted(RUN_ID, REQUEST) is True
    tables = {getattr(getattr(s, "table", None), "name", ""): s for s in session.statements}
    for table in ("core_aggregate_revisions", "core_audit_entries"):
        row = _params(tables[table])
        assert row["organization_id"] == organization
        assert row["owner_scope_kind"] == kind and row["owner_scope_ref"] == ORG


# -------------------------------------------------------------- the consumer (D4a, step "ai")
def test_the_consumer_purges_an_organization_run_and_records_the_teacher_notice() -> None:
    h = make_harness(artwork=False)
    envelope = _leased_event(
        h,
        EVENT_ID,
        owner_scope_kind="ORGANIZATION",
        owner_scope_ref=ORG,
        organization_id=ORG,
    )
    assert h.consumer.handle(envelope) == "completed"
    notice = h.world.notices["lifecycle:" + REQUEST_ID]
    assert notice["scope_kind"] == "ORGANIZATION" and notice["applied_count"] == 0
    assert notice["reason_code"] == "TEACHER_STORY_RUN_DELETED"
    assert h.world.run["state"] == "DELETED"
    receipt = h.world.receipts[REQUEST_ID]
    assert (receipt["kind"], receipt["ref"]) == ("ORGANIZATION", ORG)
    assert receipt["state"] == "completed" and receipt["unresolved_items"] == 0


def test_the_notice_reason_codes_and_the_organization_column_helper() -> None:
    assert NOTICE_REASON_CODES == {
        "PARENT_ACCOUNT": "PARENT_STORY_RUN_DELETED",
        "ORGANIZATION": "TEACHER_STORY_RUN_DELETED",
    }
    assert organization_id_of(LifecycleScope("PARENT_ACCOUNT", "a" * 64)) is None
    assert organization_id_of(LifecycleScope("ORGANIZATION", ORG)) == ORG


def test_the_receipt_and_exception_rows_of_an_organization_scope_carry_the_organization() -> None:
    class _Tx:
        def __init__(self) -> None:
            self.statements: list[Any] = []

        def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
            self.statements.append(statement)
            return SimpleNamespace(
                one_or_none=lambda: SimpleNamespace(
                    request_id=REQUEST_ID,
                    state="requested",
                    result_ref="lcr1",
                    unresolved_items=4,
                    owner_scope_kind="ORGANIZATION",
                    owner_scope_ref=ORG,
                    completed_at=None,
                    target_ref="story_run:" + RUN,
                )
            )

        def scalar(self, *_a: Any, **_k: Any) -> Any:
            return "story_run:" + RUN

    tx = _Tx()
    store = SqlLifecycleReceiptStore(sessions=None)  # type: ignore[arg-type]
    receipt = store.ensure(
        request_id=REQUEST_ID, run_ref=RUN, scope=LifecycleScope("ORGANIZATION", ORG), tx=tx
    )
    insert = _params(tx.statements[0])
    assert insert["organization_id"] == ORG and insert["owner_scope_kind"] == "ORGANIZATION"
    assert insert["owner_scope_ref"] == ORG and receipt.owner_scope_kind == "ORGANIZATION"
    parent_tx = _Tx()
    store.ensure(
        request_id=REQUEST_ID,
        run_ref=RUN,
        scope=LifecycleScope("PARENT_ACCOUNT", "a" * 64),
        tx=parent_tx,
    )
    parent_insert = _params(parent_tx.statements[0])
    assert parent_insert["organization_id"] is None
    assert parent_insert["owner_scope_kind"] == "PARENT_ACCOUNT"
    audit_tx = _Tx()
    SqlLifecycleAuditWriter().write_exception(
        tx=audit_tx,
        request_id=REQUEST_ID,
        run_ref=RUN,
        scope=LifecycleScope("ORGANIZATION", ORG),
        processed_event_id=EVENT_ID,
    )
    audit = _params(audit_tx.statements[0])
    assert audit["organization_id"] == ORG and audit["owner_scope_kind"] == "ORGANIZATION"
    assert audit["owner_scope_ref"] == ORG and audit["action"] == "lifecycle.exception"


# ------------------------------------------------------------ the AI Jobs notice (T13A-01)
class _Connection:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        return SimpleNamespace()


class _Engine:
    def __init__(self) -> None:
        self.connection = _Connection()

    @contextmanager
    def begin(self) -> Any:
        yield self.connection


def _store() -> tuple[SqlParentLifecycleNoticeStore, _Engine]:
    engine = _Engine()
    return (
        SqlParentLifecycleNoticeStore(
            engine,  # type: ignore[arg-type]
            clock=lambda: datetime(2026, 11, 21, tzinfo=UTC),
        ),
        engine,
    )


def test_an_organization_notice_is_complete_with_zero_applied_and_selects_no_job() -> None:
    store, engine = _store()
    store.record_lifecycle_notice(
        notice_id="lifecycle:" + REQUEST,
        scope=LifecycleScope("ORGANIZATION", ORG),
        story_run_ref=RUN_ID,
        reason_code="TEACHER_STORY_RUN_DELETED",
    )
    statement = engine.connection.statements[0]
    sql = str(statement.compile(dialect=_DIALECT))
    assert "ON CONFLICT (notice_id) DO NOTHING" in sql
    row = _params(statement)
    assert row["organization_id"] == ORG
    assert row["owner_scope_kind"] == "ORGANIZATION" and row["owner_scope_ref"] == ORG
    assert row["story_run_ref"] == RUN_ID and row["applied_count"] == 0
    assert row["status"] == "COMPLETE"
    assert row["session_id"] is None and row["job_type"] is None and row["subject_ref"] is None


def test_the_parent_notice_keeps_its_shape_and_the_old_method_stays_parent_only() -> None:
    store, engine = _store()
    scope = LifecycleScope("PARENT_ACCOUNT", "a" * 64)
    store.record_parent_notice(
        notice_id="n-1", scope=scope, story_run_ref=RUN_ID, reason_code="PARENT_STORY_RUN_DELETED"
    )
    store.record_lifecycle_notice(
        notice_id="n-2", scope=scope, story_run_ref=RUN_ID, reason_code="PARENT_STORY_RUN_DELETED"
    )
    first, second = (_params(s) for s in engine.connection.statements)
    for row in (first, second):
        assert row["organization_id"] is None and row["owner_scope_kind"] == "PARENT_ACCOUNT"
        assert row["owner_scope_ref"] == "a" * 64 and row["story_run_ref"] == RUN_ID
    with pytest.raises(ValueError, match="only a Parent"):
        store.record_parent_notice(
            notice_id="n-3",
            scope=LifecycleScope("ORGANIZATION", ORG),
            story_run_ref=RUN_ID,
            reason_code="x",
        )
    with pytest.raises(ValueError, match="unsupported"):
        store.record_lifecycle_notice(
            notice_id="n-4",
            scope=SimpleNamespace(kind="GLOBAL", ref="x"),
            story_run_ref=RUN_ID,
            reason_code="x",
        )
    assert len(engine.connection.statements) == 2


def test_an_organization_notice_with_no_selector_matches_no_job_of_the_organization() -> None:
    notice = CancellationNotice(
        notice_id="lifecycle:" + REQUEST,
        organization_id=ORG,
        reason_code="TEACHER_STORY_RUN_DELETED",
        owner_scope_kind="ORGANIZATION",
        owner_scope_ref=ORG,
        story_run_ref=RUN_ID,
    )
    assert (notice.session_id, notice.job_type, notice.subject_ref) == (None, None, None)
    job = SimpleNamespace(
        organization_id=ORG,
        state="queued",
        job_type="story",
        scope=SimpleNamespace(session_id="s-1", subject_refs=(RUN_ID, "other")),
    )
    # a job of the SAME organization, whose subject is even this run's id, is not touched: the
    # notice names no selector, so the best-effort job cancel is exact at applied_count 0 until
    # T-4b2 adds the job match (hand-off H2)
    assert notice_matches(notice, job) is False  # type: ignore[arg-type]
    assert AiJob is not None


def test_the_sql_job_selection_of_a_selectorless_notice_is_empty_without_a_query() -> None:
    from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobUnitOfWork

    notice = CancellationNotice(
        notice_id="n-1",
        organization_id=ORG,
        reason_code="TEACHER_STORY_RUN_DELETED",
        owner_scope_kind="ORGANIZATION",
        owner_scope_ref=ORG,
        story_run_ref=RUN_ID,
    )
    connection = _Connection()
    unit = SqlAiJobUnitOfWork.__new__(SqlAiJobUnitOfWork)
    cast(Any, unit).connection = connection
    assert unit.jobs_for_notice(notice) == ()
    assert connection.statements == []  # no SELECT: no job can be locked or changed
