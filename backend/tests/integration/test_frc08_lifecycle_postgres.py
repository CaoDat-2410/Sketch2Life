"""FR-C-08 owner-run PostgreSQL + MinIO test on a disposable target (Allowlist Draft 13 §7 item 6).

Owner-run only. It refuses to run unless the database and the object store match the explicit
allow-list of ``tools/run_be1_lifecycle_consumer.py`` (fail closed): a loopback database whose
name contains ``frc08`` on a port other than 5432/5433, equal to ``FRC08_ALLOWED_DATABASE`` and
``FRC08_ALLOWED_PORT``; a loopback MinIO endpoint equal to ``FRC08_ALLOWED_ENDPOINT`` with a
bucket containing ``frc08`` equal to ``FRC08_ALLOWED_BUCKET`` and empty at the start; throwaway
credentials. Without ``FRC08_DATABASE_URL`` the module is skipped (NOT_RUN, never PASS).

The database must already be at ``upgrade heads`` (item 5 of the owner's command file). The
test writes synthetic rows only and covers the runtime checks of DTR Draft 6 §10 and port
design Draft 6 §12 that need PostgreSQL or MinIO.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from uuid import UUID, uuid4

import pytest

from tools.run_be1_lifecycle_consumer import TargetRefused, build_consumer, load_targets

if not os.environ.get("FRC08_DATABASE_URL"):
    pytest.skip("NOT_RUN: owner-run only (FRC08_DATABASE_URL is not set)", allow_module_level=True)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import DBAPIError, IntegrityError  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from sketch2life.application.ports.identity import VerifiedPrincipal  # noqa: E402
from sketch2life.application.ports.parent_story_profile_lookup import (  # noqa: E402
    ParentStoryProfileReference,
)
from sketch2life.application.ports.parent_story_runs import (  # noqa: E402
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_lifecycle import (  # noqa: E402
    CANCEL_EVENT_TYPE,
    lifecycle_event_id,
    lifecycle_request_id,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (  # noqa: E402
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import (  # noqa: E402
    SqlStoryLifecycleStore,
)
from sketch2life.infrastructure.storage.s3_compatible import (  # noqa: E402
    Boto3S3CompatibleObjectStorage,
)

COMPLETED = re.compile(
    r"^lcr1;upload=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};ai=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    r"asset=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};story=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    r"sha256=[0-9a-f]{64}(;orph=[0-9]+)?$"
)
PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-frc08-artwork"


@dataclass
class Target:
    engine: Any
    sessions: sessionmaker[Session]
    storage: Boto3S3CompatibleObjectStorage
    consumer: Any


@pytest.fixture(scope="module")
def target() -> Iterator[Target]:
    try:
        targets = load_targets(os.environ, require_storage=True)
    except TargetRefused as refused:
        pytest.fail(f"REFUSED code={refused.code}", pytrace=False)
    consumer, engine = build_consumer(targets, os.environ, worker_id="frc08-test-worker")
    sessions = sessionmaker(engine, expire_on_commit=False, autoflush=False)
    storage = Boto3S3CompatibleObjectStorage(
        bucket=str(targets.s3_bucket),
        endpoint_url=targets.s3_endpoint,
        region_name=os.environ.get("FRC08_S3_REGION", "us-east-1"),
        access_key=os.environ["FRC08_S3_ACCESS_KEY"],
        secret_key=os.environ["FRC08_S3_SECRET_KEY"],
    )
    # The bucket must be empty at the start (refused otherwise). Some S3-compatible servers
    # (the owner-approved S3Mock) may omit KeyCount, so Contents is checked as well.
    listing = storage._client.list_objects_v2(Bucket=targets.s3_bucket, MaxKeys=1)
    if listing.get("Contents") or listing.get("KeyCount", 0):
        pytest.fail("REFUSED code=STORAGE_BUCKET_NOT_EMPTY", pytrace=False)
    with engine.connect() as connection:
        name = connection.execute(text("SELECT current_database()")).scalar_one()
        assert name == targets.database_name
        if connection.execute(text("SELECT count(*) FROM story.runs")).scalar_one():
            pytest.fail("REFUSED code=DATABASE_NOT_FRESH", pytrace=False)
    try:
        yield Target(engine, sessions, storage, consumer)
    finally:
        engine.dispose()


def _principal() -> VerifiedPrincipal:
    return VerifiedPrincipal(f"frc08-parent-{uuid4().hex}", "frc08-issuer", frozenset({"parent"}))


def _profile() -> ParentStoryProfileReference:
    return ParentStoryProfileReference(
        profile_id=uuid4(),
        profile_revision_id=uuid4(),
        state="ACTIVE",
        data_origin="SYNTHETIC_DEV",
        age_months=72,
        interests_summary=None,
    )


def _repository(t: Target) -> SqlParentStoryRunRepository:
    return SqlParentStoryRunRepository(t.sessions())


def _create(t: Target, principal: VerifiedPrincipal, *, artwork: bool = True) -> tuple[str, int]:
    run_id = str(uuid4())
    _repository(t).create_run(
        principal=principal,
        account_id=f"account-{uuid4().hex}",
        profile=_profile(),
        idempotency_key=f"create-{uuid4().hex}",
        run_id=run_id,
        topic="frc08",
        adult_confirmed_idea="synthetic",
    )
    revision = 1
    if artwork:
        original = f"parent/{run_id}/{uuid4().hex}/original"
        derived = f"parent/{run_id}/{uuid4().hex}/normalized.png"
        for key in (original, derived):
            t.storage.put_object(
                key, BytesIO(PNG), content_type="image/png", content_length=len(PNG), metadata={}
            )
        _repository(t).attach_artwork(
            principal=principal,
            run_id=run_id,
            original_asset_ref=original,
            original_sha256="a" * 64,
            original_media_type="image/png",
            original_size_bytes=len(PNG),
            derived_asset_ref=derived,
            derived_sha256="b" * 64,
            derived_size_bytes=len(PNG),
            scanner_name="fixture",
            scanner_version="1",
        )
        revision = 2
    return run_id, revision


def _one(t: Target, sql: str, **params: Any) -> Any:
    with t.engine.connect() as connection:
        return connection.execute(text(sql), params).scalar()


def _drain(t: Target) -> list[str]:
    outcomes = []
    for _ in range(20):
        outcome = t.consumer.run_once()
        if outcome is None:
            break
        outcomes.append(outcome)
    return outcomes


def _downgrade_guard() -> str:
    """The migration's own guard block (DTR §9), loaded from the revision file."""
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "20261119_frc08_lifecycle_scope.py"
    )
    spec = importlib.util.spec_from_file_location("frc08_lifecycle_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return str(migration.DOWNGRADE_GUARD)


_SCOPE_ROWS = "typed owner-scope rows exist"
_RUN_ROWS = "DELETED runs or NULL profile refs exist"
_RECEIPT_ROWS = "DELETE_RUN receipts exist"
_RUN_INSERT = (
    "INSERT INTO story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, "
    "run_state, revision, version) VALUES (:run, 'PARENT_ACCOUNT', :s, :profile, :state, 1, 1)"
)
_GUARD_CASES: dict[str, tuple[str, list[str]]] = {
    "aggregate_parent": (
        _SCOPE_ROWS,
        [
            "INSERT INTO core_aggregate_revisions (aggregate_id, organization_id, "
            "owner_scope_kind, owner_scope_ref, revision) "
            "VALUES (:a, NULL, 'PARENT_ACCOUNT', :s, 1)"
        ],
    ),
    "aggregate_organization_with_scope_ref": (
        _SCOPE_ROWS,
        [
            "INSERT INTO core_aggregate_revisions (aggregate_id, organization_id, "
            "owner_scope_kind, owner_scope_ref, revision) VALUES (:a, 'org-g', 'ORGANIZATION', "
            "'org-g', 1)"
        ],
    ),
    "outbox_parent": (
        _SCOPE_ROWS,
        [
            "INSERT INTO core_aggregate_revisions (aggregate_id, organization_id, revision) "
            "VALUES (:a, 'org-g', 1)",
            "INSERT INTO core_outbox_events (event_id, event_type, organization_id, "
            "owner_scope_kind, owner_scope_ref, aggregate_id, aggregate_revision, payload, status, "
            "attempt_count) VALUES (:e, 'x', NULL, 'PARENT_ACCOUNT', :s, :a, 1, "
            "CAST('{}' AS jsonb), 'pending', 0)",
        ],
    ),
    "lifecycle_request_parent": (
        _SCOPE_ROWS,
        [
            "INSERT INTO be1_data_lifecycle_requests (request_id, organization_id, "
            "owner_scope_kind, owner_scope_ref, request_type, target_ref, state, unresolved_items, "
            "result_ref, requested_by) VALUES (:e, NULL, 'PARENT_ACCOUNT', :s, 'delete', 't', "
            "'requested', 4, 'lcr1', :s)"
        ],
    ),
    "notice_parent": (
        _SCOPE_ROWS,
        [
            "INSERT INTO ai_jobs.cancellation_notice (notice_id, organization_id, reason_code, "
            "status, applied_count, recorded_at, owner_scope_kind, owner_scope_ref, story_run_ref) "
            "VALUES (:e, NULL, 'X', 'COMPLETE', 0, now(), 'PARENT_ACCOUNT', :s, 'r')"
        ],
    ),
    "audit_parent": (
        _SCOPE_ROWS,
        [
            "INSERT INTO core_audit_entries (audit_id, organization_id, owner_scope_kind, "
            "owner_scope_ref, action, resource_type, resource_id, decision) VALUES "
            "(:e, NULL, 'PARENT_ACCOUNT', :s, 'x', 'y', 'z', 'd')"
        ],
    ),
    "run_deleted": (_RUN_ROWS, [_RUN_INSERT.replace(":state", "'DELETED'")]),
    "run_null_profile": (
        _RUN_ROWS,
        [_RUN_INSERT.replace(":profile", "NULL").replace(":state", "'INPUT_PROCESSING'")],
    ),
    "delete_run_receipt": (
        _RECEIPT_ROWS,
        [
            _RUN_INSERT.replace(":state", "'INPUT_PROCESSING'"),
            "INSERT INTO story.command_receipts (receipt_id, actor_scope_kind, actor_scope_ref, "
            "operation, idempotency_scope_kind, idempotency_scope_ref, idempotency_key_sha256, "
            "request_fingerprint_sha256, state, response_status, response_resource_version, "
            "response_body, resource_ref, resource_version, state_version, finalized_at) VALUES "
            "(:e, 'PARENT_ACCOUNT', :s, 'DELETE_RUN', 'STORY_RUN', :run, :h, :h, 'FINAL', 202, 1, "
            "CAST('{}' AS jsonb), :run, 1, 1, now())",
        ],
    ),
}


# Defined first in the module so it runs on the fresh database, before any lifecycle row exists.
@pytest.mark.parametrize("case", sorted(_GUARD_CASES))
def test_each_downgrade_guard_clause_refuses_on_its_own(target: Target, case: str) -> None:
    """DTR §9/§10: every guard case, one at a time, in a transaction that is rolled back."""
    message, inserts = _GUARD_CASES[case]
    guard = text(_downgrade_guard())
    params = {
        "a": f"frc08-guard-{uuid4().hex}",
        "e": str(uuid4()),
        "s": "c" * 64,
        "run": str(uuid4()),
        "profile": str(uuid4()),
        "h": "d" * 64,
    }
    with target.engine.connect() as connection:
        outer = connection.begin()
        try:
            try:
                with connection.begin_nested():
                    connection.execute(guard)  # the database holds no lifecycle row yet
            except DBAPIError:
                pytest.fail("NOT_ISOLATED: lifecycle rows already exist", pytrace=False)
            for statement in inserts:
                connection.execute(text(statement), params)
            with pytest.raises(DBAPIError, match=message), connection.begin_nested():
                connection.execute(guard)
        finally:
            outer.rollback()


def test_schema_delta_checks_and_organization_defaults(target: Target) -> None:
    with target.engine.connect() as connection:
        names = set(
            connection.execute(
                text("SELECT conname FROM pg_constraint WHERE contype = 'c'")
            ).scalars()
        )
        nullable = connection.execute(
            text(
                "SELECT is_nullable FROM information_schema.columns WHERE table_schema = 'story' "
                "AND table_name = 'runs' AND column_name = 'profile_ref'"
            )
        ).scalar_one()
    assert {
        "ck_core_outbox_owner_scope",
        "ck_core_aggregate_owner_scope",
        "ck_be1_data_request_owner_scope",
        "ck_be1_data_request_parent_completed",
        "ck_cancellation_notice_owner_scope",
        "ck_cancellation_notice_parent_story_run_ref",
        "ck_core_audit_owner_scope",
    } <= names
    assert nullable == "YES"
    audit_id = str(uuid4())
    with target.engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO core_audit_entries (audit_id, organization_id, action, "
                "resource_type, resource_id, decision) VALUES (:a, 'org-frc08', 'x', 'y', 'z', 'd')"
            ),
            {"a": audit_id},
        )
    assert _one(
        target,
        "SELECT owner_scope_kind || ':' || coalesce(owner_scope_ref, 'NULL') "
        "FROM core_audit_entries WHERE audit_id = :a",
        a=audit_id,
    ) == "ORGANIZATION:NULL"
    for bad in (
        "INSERT INTO core_audit_entries (audit_id, organization_id, owner_scope_kind, "
        "owner_scope_ref, action, resource_type, resource_id, decision) VALUES "
        "(:a, 'org', 'PARENT_ACCOUNT', 'p', 'x', 'y', 'z', 'd')",
        "INSERT INTO core_audit_entries (audit_id, organization_id, owner_scope_kind, "
        "action, resource_type, resource_id, decision) VALUES "
        "(:a, NULL, 'GLOBAL', 'x', 'y', 'z', 'd')",
        "INSERT INTO be1_data_lifecycle_requests (request_id, organization_id, owner_scope_kind, "
        "owner_scope_ref, request_type, target_ref, state, unresolved_items, result_ref, "
        "requested_by, completed_at) VALUES (:a, NULL, 'PARENT_ACCOUNT', 'p', 'delete', 't', "
        "'completed', 0, 'lcr1;upload=v:0:0@0', 'p', now())",
        "INSERT INTO ai_jobs.cancellation_notice (notice_id, organization_id, reason_code, "
        "status, applied_count, recorded_at, owner_scope_kind, owner_scope_ref) VALUES "
        "(:a, NULL, 'X', 'COMPLETE', 0, now(), 'PARENT_ACCOUNT', 'p')",
    ):
        with pytest.raises(IntegrityError), target.engine.begin() as connection:
            connection.execute(text(bad), {"a": str(uuid4())})


def test_cancel_purges_everything_and_ends_deleted_with_a_completed_token(target: Target) -> None:
    principal = _principal()
    run_id, revision = _create(target, principal)
    record = _repository(target).cancel_run(
        principal=principal, run_id=run_id, expected_revision=revision, idempotency_key="c-1"
    )
    assert record.run_state == "DELETE_PENDING"
    replay = _repository(target).cancel_run(
        principal=principal, run_id=run_id, expected_revision=revision, idempotency_key="c-1"
    )
    assert replay == record
    with pytest.raises(ParentStoryRunError) as second:
        _repository(target).cancel_run(
            principal=principal,
            run_id=run_id,
            expected_revision=revision + 1,
            idempotency_key="c-2",
        )
    assert second.value.code == "INVALID_STATE_TRANSITION"
    event_id = lifecycle_event_id(lifecycle_request_id(run_id), CANCEL_EVENT_TYPE)
    events = "SELECT count(*) FROM core_outbox_events WHERE event_id = :e"
    assert _one(target, events, e=event_id) == 1

    assert "completed" in _drain(target)
    request_id = lifecycle_request_id(run_id)
    assert _one(target, "SELECT run_state FROM story.runs WHERE run_id = :r", r=run_id) == "DELETED"
    assert _one(target, "SELECT profile_ref FROM story.runs WHERE run_id = :r", r=run_id) is None
    for table in ("run_inputs", "understanding_revisions", "story_revisions"):
        assert _one(target, f"SELECT count(*) FROM story.{table} WHERE run_id = :r", r=run_id) == 0
    assert _one(
        target,
        "SELECT count(*) FROM core_asset_metadata WHERE source_refs @> CAST(:j AS jsonb)",
        j=f'["{run_id}"]',
    ) == 0
    assert target.storage.list_keys(f"parent/{run_id}/") == ()
    token = _one(
        target,
        "SELECT result_ref FROM be1_data_lifecycle_requests WHERE request_id = :q AND "
        "state = 'completed' AND unresolved_items = 0 AND completed_at IS NOT NULL",
        q=request_id,
    )
    assert COMPLETED.fullmatch(token)
    assert _one(
        target,
        "SELECT applied_count FROM ai_jobs.cancellation_notice WHERE notice_id = :n",
        n="lifecycle:" + request_id,
    ) == 0
    actions = set(
        _rows(target, "SELECT action FROM core_audit_entries WHERE resource_id = :r", r=run_id)
    )
    assert actions == {"lifecycle.cancel_accepted", "lifecycle.completed"}
    view = _repository(target).get_run(principal=principal, run_id=run_id)
    assert isinstance(view, ParentStoryLifecycleRecord)
    assert (view.run_state, view.purge_state) == ("DELETED", "COMPLETED")
    status = "SELECT status FROM core_outbox_events WHERE event_id = :e"
    assert _one(target, status, e=event_id) == "delivered"


def _rows(t: Target, sql: str, **params: Any) -> list[Any]:
    with t.engine.connect() as connection:
        return list(connection.execute(text(sql), params).scalars())


def test_delete_of_a_completed_run_without_artwork_ends_with_an_empty_asset_entry(
    target: Target,
) -> None:
    principal = _principal()
    run_id, _revision = _create(target, principal, artwork=False)
    with target.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE story.runs SET run_state = 'COMPLETED', active_owner_parent_account_id "
                "= NULL, revision = revision + 1, version = version + 1 WHERE run_id = :r"
            ),
            {"r": run_id},
        )
    record = _repository(target).delete_run(principal=principal, run_id=run_id, idempotency_key="d")
    assert record.run_state == "DELETE_PENDING"
    assert "completed" in _drain(target)
    token = _one(
        target,
        "SELECT result_ref FROM be1_data_lifecycle_requests WHERE request_id = :q",
        q=lifecycle_request_id(run_id),
    )
    assert ";asset=v:0:" in token and COMPLETED.fullmatch(token)


def test_a_retained_asset_ends_in_exception_with_nothing_deleted_in_core(target: Target) -> None:
    principal = _principal()
    run_id, revision = _create(target, principal)
    original = _one(target, "SELECT asset_ref FROM story.runs WHERE run_id = :r", r=run_id)
    foreign = f"parent/{run_id}/{uuid4().hex}/foreign"
    with target.engine.begin() as connection:  # a foreign-scope neighbour: SCOPE_MISMATCH
        connection.execute(
            text(
                "INSERT INTO core_asset_metadata (asset_ref, asset_version, organization_id, "
                "owner_scope_kind, owner_scope_ref, content_sha256, media_type, source_refs, "
                "derived_from_ref) VALUES (:a, 1, NULL, 'PARENT_ACCOUNT', :s, :h, 'image/png', "
                "'[]'::jsonb, :d)"
            ),
            {"a": foreign, "s": "f" * 64, "h": "c" * 64, "d": original},
        )
    _repository(target).cancel_run(
        principal=principal, run_id=run_id, expected_revision=revision, idempotency_key="r-1"
    )
    assert "exception" in _drain(target)
    assert _one(target, "SELECT run_state FROM story.runs WHERE run_id = :r", r=run_id) == (
        "DELETE_PENDING"
    )
    assert _one(target, "SELECT count(*) FROM story.run_inputs WHERE run_id = :r", r=run_id) == 0
    assert len(target.storage.list_keys(f"parent/{run_id}/")) == 2  # nothing deleted
    receipt = _one(
        target,
        "SELECT state || '|' || result_ref FROM be1_data_lifecycle_requests WHERE request_id = :q",
        q=lifecycle_request_id(run_id),
    )
    assert receipt.startswith("exception|") and ";asset=" not in receipt
    assert _one(
        target,
        "SELECT count(*) FROM core_audit_entries WHERE resource_id = :r AND "
        "action = 'lifecycle.exception'",
        r=run_id,
    ) == 1
    assert _drain(target) == []  # the delivered event does not return


def test_reconciliation_inserts_one_event_per_pre_existing_run_and_nothing_on_a_rerun(
    target: Target,
) -> None:
    from tools.frc08_reconcile_delete_pending import reconcile

    principal = _principal()
    run_id, _revision = _create(target, principal, artwork=False)
    with target.engine.begin() as connection:  # an M2-era cancel: no lifecycle event
        connection.execute(
            text(
                "UPDATE story.runs SET run_state = 'DELETE_PENDING', "
                "active_owner_parent_account_id = NULL WHERE run_id = :r"
            ),
            {"r": run_id},
        )
    store = SqlStoryLifecycleStore(target.sessions)
    seen, inserted = reconcile(store)
    event_id = lifecycle_event_id(lifecycle_request_id(run_id), CANCEL_EVENT_TYPE)
    stored = _one(
        target,
        "SELECT event_type || '|' || status || '|' || owner_scope_kind FROM core_outbox_events "
        "WHERE event_id = :e AND aggregate_id = :r",
        e=event_id,
        r=run_id,
    )
    assert stored == CANCEL_EVENT_TYPE + "|pending|PARENT_ACCOUNT"  # the row itself, first
    assert (seen, inserted) == (1, 1)
    assert reconcile(store) == (0, 0)
    assert "completed" in _drain(target)


def test_a_stale_compare_and_set_is_refused_by_the_receipt_store(target: Target) -> None:
    from sketch2life.application.ports.core_foundation import LifecycleScope
    from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
        SqlLifecycleReceiptStore,
    )

    store = SqlLifecycleReceiptStore(target.sessions)
    run_id = str(UUID(int=uuid4().int))
    request_id = lifecycle_request_id(run_id)
    receipt = store.ensure(
        request_id=request_id, run_ref=run_id, scope=LifecycleScope("PARENT_ACCOUNT", "a" * 64)
    )
    assert receipt.state == "requested" and receipt.result_ref == "lcr1"
    assert store.compare_and_set(
        request_id=request_id,
        expected_state="requested",
        expected_result_ref="lcr1",
        state="running",
        result_ref="lcr1",
        unresolved_items=4,
    )
    assert not store.compare_and_set(  # a second worker with the old state loses
        request_id=request_id,
        expected_state="requested",
        expected_result_ref="lcr1",
        state="running",
        result_ref="lcr1",
        unresolved_items=4,
    )
