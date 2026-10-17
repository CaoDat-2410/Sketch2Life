"""Real PostgreSQL application/CAS/receipt tests; owner boundary remains ASSUMED."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier

import pytest
from sqlalchemy import func, select

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.application.learning_content_eligibility import ContentEligibility
from sketch2life.application.learning_content_history import ContentReviewHistory
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


def test_derived_history_preserves_original_sql_proofs_across_resubmit(harness):
    service, boundary, store = harness
    history = ContentReviewHistory(store, boundary)
    record, _ = approved(service)
    with store.engine.connect() as connection:
        original = list(connection.execute(select(REVIEW.c.proof).order_by(
            REVIEW.c.review_revision)).scalars())
    page = history.read("consumer", "school", record.record_id, version=1, page_size=1)
    assert page.entries[0].state == "effective" and page.next_after_revision == 2
    record = service.execute("reviewer", "school", review_command(
        record, "safety", "replacement"), expected_revision=record.revision).record
    with pytest.raises(ContentError, match="CONTENT_STALE_REVISION"):
        history.read("consumer", "school", record.record_id, version=1, page_size=1,
                     after_revision=2, snapshot_revision=page.record_revision)
    replaced = history.read("consumer", "school", record.record_id, version=1, page_size=10)
    assert replaced.entries[0].stale_reason == "dimension_replaced"
    record = service.execute("reviewer", "school", review_command(
        record, "safety", "negative", decision="request_changes", action="request_changes"),
        expected_revision=record.revision).record
    record = service.execute("author", "school", command("submit_review", "resubmit", record),
                              expected_revision=record.revision).record
    store.engine.dispose()
    page = ContentReviewHistory(SqlContentStore(store.engine), boundary).read(
        "consumer", "school", record.record_id, version=1, page_size=100)
    assert len(page.entries) == 4 and all(e.stale_reason == "context_changed" for e in page.entries)
    with store.engine.connect() as connection:
        current = list(connection.execute(select(REVIEW.c.proof).order_by(
            REVIEW.c.review_revision)).scalars())
    assert current[:2] == original
    assert all(proof["state"] == "effective" for proof in current)
    with store.transaction() as tx:
        assert tx.review_history("other-school", record.record_id, version=1,
                                 after_revision=0, limit=10) == ()


@pytest.mark.parametrize("published_first", [False, True])
def test_history_sql_edit_and_recall_do_not_rewrite_old_approval(harness, published_first):
    service, boundary, store = harness
    record, refs = approved(service)
    if published_first:
        record = service.execute("publisher", "school", command(
            "publish", "publish", record, review_ref=refs),
            expected_revision=record.revision).record
    edited = service.execute("author", "school", command("edit", "edit", record, content=BODY),
                              expected_revision=record.revision).record
    history = ContentReviewHistory(store, boundary)
    page = history.read("consumer", "school", record.record_id, version=1, page_size=10)
    assert all(e.state == ("effective" if published_first else "stale") for e in page.entries)
    assert history.read("consumer", "school", record.record_id, version=2,
                         page_size=10).entries == ()
    if published_first:
        service.execute("recaller", "school", command("recall", "recall", record, reason="retire"),
                        expected_revision=edited.revision)
        boundary.usage = False
        page = history.read("consumer", "school", record.record_id, version=1, page_size=10)
        assert all(e.stale_reason == "content_recalled" for e in page.entries)
        assert all(e.original_proof.state == "effective" for e in page.entries)


@pytest.mark.parametrize("retirement", ["recall", "archive"])
def test_retired_head_edit_requires_fresh_review_without_restoring_old_version(harness, retirement):
    service, boundary, store = harness
    record, refs = approved(service)
    original_publish = command("publish", "publish", record, review_ref=refs)
    record = service.execute("publisher", "school", original_publish,
                              expected_revision=record.revision).record
    retired = service.execute("recaller", "school", command(
        retirement, "retire", record, reason="withdraw old version"),
        expected_revision=record.revision).record
    replacement = command("edit", "replacement", retired, content=BODY)
    new = service.execute("author", "school", replacement,
                           expected_revision=retired.revision).record
    assert new.record_id == retired.record_id and new.version == 2
    assert new.state == "draft" and new.review_revision == new.context_revision == 0
    assert new.publication_review_ref is None and new.recalled_at is None
    assert service.execute("author", "school", replacement,
                           expected_revision=retired.revision).replayed
    with pytest.raises(ContentError, match="CONTENT_TRANSITION_DENIED"):
        service.execute("publisher", "school", command("publish", "bad-publish", new,
                                                        review_ref=refs),
                        expected_revision=new.revision)
    new = service.execute("author", "school", command("submit_review", "new-submit", new),
                           expected_revision=new.revision).record
    new_refs = {"review_policy_version": "policy-v1"}
    for dimension in ("safety", "pedagogical"):
        reviewed = service.execute("reviewer", "school", review_command(
            new, dimension, "new-" + dimension), expected_revision=new.revision)
        new = reviewed.record
        new_refs[dimension + "_review_id"] = reviewed.review_record.review_id
    with pytest.raises(ContentError, match="CONTENT_REVIEW_REQUIRED"):
        service.execute("publisher", "school", command("publish", "old-proofs", new,
                                                        review_ref=refs),
                        expected_revision=new.revision)
    new = service.execute("publisher", "school", command("publish", "new-publish", new,
                                                          review_ref=new_refs),
                           expected_revision=new.revision).record
    resolver = ContentEligibility(store, boundary)
    assert resolver.resolve("consumer", "school", new.record_id,
                            age_months=48, purpose_code="classroom").version == 2
    with pytest.raises(ContentError, match="CONTENT_NOT_PUBLISHED"):
        resolver.resolve("consumer", "school", new.record_id, version=1,
                         age_months=48, purpose_code="classroom")
    with pytest.raises(ContentError, match="CONTENT_RECEIPT_INEFFECTIVE"):
        service.execute("publisher", "school", original_publish, expected_revision=4)
    with store.transaction() as tx:
        old = tx.load("school", new.record_id, version=1)
        assert old.state.value == ("recalled" if retirement == "recall" else "archived")
        assert old.hash == retired.hash and old.recall_reason == "withdraw old version"
        assert len(old.reviews) == 2
    assert counts(store) == (2, 4, 11, 11, 11)
