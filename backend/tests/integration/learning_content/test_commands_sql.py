"""Real PostgreSQL application/CAS/receipt tests; owner boundary remains ASSUMED."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier

import pytest
from sqlalchemy import func, select

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.application.learning_content_eligibility import ContentEligibility
from sketch2life.domain.learning_content.model import ContentError, ContentState
from sketch2life.infrastructure.learning_content.sql import SqlContentStore
from sketch2life.infrastructure.learning_content.tables import (
    EVENT,
    OUTBOX,
    RECEIPT,
    REVIEW,
    VERSION,
)
from tests.integration.learning_content.test_content_sql import migrate
from tests.learning_content_fixtures import (
    BODY,
    NOW,
    AssumedBoundary,
    approved,
    command,
    review_command,
    submitted,
)


@pytest.fixture
def harness(content_engine, monkeypatch):
    migrate(content_engine, monkeypatch)
    boundary = AssumedBoundary()
    store = SqlContentStore(content_engine)
    return ContentCommands(store, boundary, clock=lambda: NOW), boundary, store


def counts(store):
    with store.engine.connect() as connection:
        return tuple(connection.scalar(select(func.count()).select_from(table))
                     for table in (VERSION, REVIEW, RECEIPT, EVENT, OUTBOX))


def test_application_publish_restart_replay_and_recall_are_durable(harness):
    service, boundary, store = harness
    record, refs = approved(service)
    cmd = command("publish", "publish", record, review_ref=refs)
    published = service.execute("publisher", "school", cmd, expected_revision=record.revision)
    store.engine.dispose()
    restarted = ContentCommands(SqlContentStore(store.engine), boundary, clock=lambda: NOW)
    replay = restarted.execute("publisher", "school", cmd, expected_revision=record.revision)
    assert replay.replayed and replay.record == published.record
    assert counts(store) == (1, 2, 5, 5, 5)
    # Shared response survives repository/connection restart unchanged in receipt.
    with store.transaction() as tx:
        receipt = tx.receipt("school", "reviewer", "safety")
        assert '"reviewed_at":"2026-10-17T00:00:00Z"' in receipt.result_json
    resolver = ContentEligibility(store, boundary)
    assert resolver.resolve("consumer", "school", record.record_id,
                            age_months=48, purpose_code="classroom").hash == record.hash
    recalled = restarted.execute("recaller", "school", command(
        "recall", "recall", published.record, reason="withdrawn source"), expected_revision=5)
    assert recalled.record.state == "recalled"
    with pytest.raises(ContentError, match="CONTENT_RECEIPT_INEFFECTIVE"):
        restarted.execute("publisher", "school", cmd, expected_revision=record.revision)
    with pytest.raises(ContentError, match="CONTENT_NOT_ELIGIBLE"):
        resolver.resolve("consumer", "school", record.record_id,
                         age_months=48, purpose_code="classroom")
    assert counts(store) == (1, 2, 6, 6, 6)


def test_application_receipt_failure_rolls_back_all_sql_writes(harness, monkeypatch):
    service, _, store = harness
    from sketch2life.infrastructure.learning_content.sql import SqlContentTransaction

    def fail(self, receipt):
        raise ContentError("SYNTHETIC_RECEIPT_FAILURE")

    monkeypatch.setattr(SqlContentTransaction, "add_receipt", fail)
    with pytest.raises(ContentError, match="SYNTHETIC_RECEIPT_FAILURE"):
        service.execute("author", "school", command("create", "create", content=BODY))
    assert counts(store) == (0, 0, 0, 0, 0)


def race(service, jobs):
    barrier = Barrier(2)

    def run(job):
        actor, cmd, revision = job
        barrier.wait(timeout=15)
        try:
            return service.execute(actor, "school", cmd, expected_revision=revision)
        except ContentError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(run, jobs))


def test_concurrent_identical_create_recovers_unique_winner(harness):
    service, boundary, store = harness
    # Force both first receipt reads to observe absence. The loser must recover
    # only AFTER SQL rolls back its failed unique insert, not by a memory lock.
    from sketch2life.infrastructure.learning_content.sql import SqlContentTransaction

    barrier = Barrier(2)

    class FirstReadBarrier:
        @contextmanager
        def transaction(self):
            with store.transaction() as tx:
                original = tx.receipt
                used = False

                def receipt(*args):
                    nonlocal used
                    result = original(*args)
                    if not used and result is None:
                        used = True
                        barrier.wait(timeout=15)
                    return result

                assert isinstance(tx, SqlContentTransaction)
                tx.receipt = receipt
                yield tx

    guarded = ContentCommands(FirstReadBarrier(), boundary, clock=lambda: NOW)
    cmd = command("create", "create", content=BODY)
    results = race(guarded, [("author", cmd, None), ("author", cmd, None)])
    assert all(not isinstance(result, str) for result in results)
    assert sorted(result.replayed for result in results) == [False, True]
    assert results[0].record == results[1].record
    assert counts(store) == (1, 0, 1, 1, 1)


@pytest.mark.parametrize("pair", ["edit_publish", "review_publish", "publish_recall"])
def test_conflicting_application_commands_have_one_sql_cas_winner(harness, pair):
    service, _, store = harness
    record, refs = approved(service)
    publish_cmd = command("publish", "publish", record, review_ref=refs)
    if pair == "edit_publish":
        other = ("author", command("edit", "edit", record,
                                    content={**BODY, "title": "New draft"}), record.revision)
    elif pair == "review_publish":
        other = ("reviewer", review_command(record, "safety", "new-review"), record.revision)
    else:
        record = service.execute("publisher", "school", publish_cmd,
                                  expected_revision=record.revision).record
        publish_cmd = command("publish", "second-publish", record, review_ref=refs)
        other = ("recaller", command("recall", "recall", record, reason="withdraw"),
                 record.revision)
    results = race(service, [("publisher", publish_cmd, record.revision), other])
    if pair == "publish_recall":
        # Already-published cannot republish, and recall cannot be resurrected.
        assert sum(not isinstance(item, str) for item in results) == 1
        assert all(item in {"CONTENT_STALE_REVISION", "CONTENT_TRANSITION_DENIED"}
                   for item in results if isinstance(item, str))
    else:
        assert sum(not isinstance(item, str) for item in results) == 1
        assert [item for item in results if isinstance(item, str)] == ["CONTENT_STALE_REVISION"]
    with store.transaction() as tx:
        head = tx.load("school", record.record_id)
        assert head.revision == record.revision + 1
        if pair == "publish_recall":
            assert head.state == ContentState.RECALLED
    assert counts(store)[2:] == (record.revision + 1,) * 3


def test_concurrent_duplicate_submit_replays_without_extra_event(harness):
    service, _, store = harness
    record = service.execute("author", "school", command("create", "create", content=BODY)).record
    cmd = command("submit_review", "submit", record)
    results = race(service, [("author", cmd, 1), ("author", cmd, 1)])
    assert sorted(result.replayed for result in results) == [False, True]
    assert counts(store) == (1, 0, 2, 2, 2)


def test_negative_review_resubmit_preserves_sql_proof_history(harness):
    service, boundary, store = harness
    record = submitted(service)
    boundary.moderation = False
    cmd = review_command(record, "safety", "request-changes", decision="request_changes",
                          action="request_changes")
    changed = service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    fresh = service.execute(
        "author", "school", command("submit_review", "resubmit", changed.record),
        expected_revision=changed.record.revision)
    with store.transaction() as tx:
        loaded = tx.load("school", record.record_id)
        assert loaded.reviews == () and loaded.context_revision == fresh.record.context_revision
    with pytest.raises(ContentError, match="CONTENT_REVIEW_INEFFECTIVE"):
        service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    assert counts(store) == (1, 1, 4, 4, 4)
