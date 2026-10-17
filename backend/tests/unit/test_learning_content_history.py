"""F03 read projection components, assumed owner scope/effectiveness only."""

from dataclasses import replace

import pytest

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.application.learning_content_history import ContentReviewHistory
from sketch2life.domain.learning_content.model import ContentError
from tests.learning_content_fixtures import (
    BODY,
    NOW,
    AssumedBoundary,
    ComponentStore,
    approved,
    command,
    review_command,
    submitted,
)


@pytest.fixture
def harness():
    boundary = AssumedBoundary()
    store = ComponentStore(boundary)
    service = ContentCommands(store, boundary, clock=lambda: NOW)
    return service, ContentReviewHistory(store, boundary), boundary, store


def read(history, record, **kwargs):
    return history.read("consumer", "school", record.record_id, version=record.version,
                        page_size=10, **kwargs)


def test_pagination_is_scoped_and_keeps_original_proofs(harness):
    service, history, _, store = harness
    record, _ = approved(service)
    before = dict(store.proofs)
    first = history.read("consumer", "school", record.record_id, version=1, page_size=1)
    assert len(first.entries) == 1 and first.next_after_revision == 2
    second = history.read("consumer", "school", record.record_id, version=1, page_size=1,
                          after_revision=first.next_after_revision,
                          snapshot_revision=first.record_revision)
    assert second.next_after_revision is None
    assert first.entries[0].state == second.entries[0].state == "effective"
    assert {first.entries[0].original_proof.dimension,
            second.entries[0].original_proof.dimension} == {"safety", "pedagogical"}
    assert store.proofs == before and not hasattr(first, "body_json")


def test_resubmit_projects_stale_context_without_mutating_approval(harness):
    service, history, _, store = harness
    record = submitted(service)
    changed = service.execute("reviewer", "school", review_command(
        record, "safety", "negative", decision="request_changes", action="request_changes"),
        expected_revision=record.revision).record
    original = next(iter(store.proofs.values()))
    service.execute("author", "school", command("submit_review", "resubmit", changed),
                    expected_revision=changed.revision)
    entry = read(history, record).entries[0]
    assert entry.state == "stale" and entry.stale_reason == "context_changed"
    assert entry.original_proof == original and original.state == "effective"
    assert entry.original_proof.reason == "needs revision"


def test_replaced_dimension_has_explicit_reason(harness):
    service, history, _, _ = harness
    record = submitted(service)
    for request in ("first", "replacement"):
        record = service.execute("reviewer", "school", review_command(
            record, "safety", request), expected_revision=record.revision).record
    entries = read(history, record).entries
    assert [(e.state, e.stale_reason) for e in entries] == [
        ("stale", "dimension_replaced"), ("effective", None)]


@pytest.mark.parametrize("publish_first", [False, True])
def test_edit_does_not_invalidate_previously_published_history(harness, publish_first):
    service, history, _, _ = harness
    record, refs = approved(service)
    if publish_first:
        record = service.execute(
            "publisher", "school", command("publish", "publish", record, review_ref=refs),
            expected_revision=record.revision).record
    service.execute("author", "school", command("edit", "edit", record, content=BODY),
                    expected_revision=record.revision)
    entries = read(history, record).entries
    assert all(e.state == ("effective" if publish_first else "stale") for e in entries)
    if not publish_first:
        assert all(e.stale_reason == "superseded_unpublished_version" for e in entries)


@pytest.mark.parametrize("action", ["recall", "archive"])
def test_retirement_history_stays_readable_even_when_usage_is_denied(harness, action):
    service, history, boundary, _ = harness
    record, refs = approved(service)
    record = service.execute("publisher", "school", command(
        "publish", "publish", record, review_ref=refs), expected_revision=record.revision).record
    service.execute("recaller", "school", command(action, action, record, reason="withdrawn"),
                    expected_revision=record.revision)
    boundary.usage = False
    entries = read(history, record).entries
    assert all(e.stale_reason == ("content_recalled" if action == "recall"
                                 else "content_archived") for e in entries)
    assert all(e.original_proof.state == "effective" for e in entries)


@pytest.mark.parametrize("change,reason", [("policy", "policy_changed"),
                                          ("review", "owner_ineffective")])
def test_current_owner_decisions_are_not_fabricated_revocation_causes(harness, change, reason):
    service, history, boundary, _ = harness
    record, refs = approved(service)
    if change == "policy":
        boundary.policy = replace(boundary.policy, version="new")
    else:
        boundary.revoked_reviews.update((refs["safety_review_id"], refs["pedagogical_review_id"]))
    assert all(e.state == "stale" and e.stale_reason == reason
               for e in read(history, record).entries)


def test_pagination_detects_changed_snapshot(harness):
    service, history, _, _ = harness
    record, _ = approved(service)
    first = history.read("consumer", "school", record.record_id, version=1, page_size=1)
    service.execute("reviewer", "school", review_command(record, "safety", "replacement"),
                    expected_revision=record.revision)
    with pytest.raises(ContentError, match="CONTENT_STALE_REVISION"):
        read(history, record, after_revision=first.next_after_revision,
             snapshot_revision=first.record_revision)


def test_current_authority_rechecked_without_raw_source_permission(harness):
    service, history, boundary, _ = harness
    record, _ = approved(service)
    read(history, record)
    boundary.capabilities["consumer"] = frozenset()
    with pytest.raises(ContentError, match="CONTENT_FORBIDDEN"):
        read(history, record)
    assert not boundary.held


@pytest.mark.parametrize("options", [dict(version=True), dict(version=0), dict(page_size=0),
                                    dict(page_size=101), dict(after_revision=-1),
                                    dict(after_revision=1), dict(snapshot_revision=True)])
def test_invalid_pagination_fails_before_storage(harness, options):
    _, history, _, _ = harness
    query = dict(version=1, page_size=10)
    query.update(options)
    with pytest.raises(ContentError, match="CONTENT_INVALID_QUERY"):
        history.read("consumer", "school", "record", **query)


@pytest.mark.parametrize("fault", ["hash", "version", "revision_order", "duplicate_revision"])
def test_malformed_history_storage_is_not_disclosed(harness, monkeypatch, fault):
    service, history, _, store = harness
    record, _ = approved(service)
    originals = list(store.proofs.values())
    if fault == "hash":
        rows = (replace(originals[0], target_hash="b" * 64),)
    elif fault == "version":
        rows = (replace(originals[0], target_version=99),)
    elif fault == "revision_order":
        rows = tuple(reversed(originals))
    else:
        rows = (originals[0], originals[0])
    monkeypatch.setattr(store, "review_history", lambda *args, **kwargs: rows)
    with pytest.raises(ContentError, match="CONTENT_(REVIEW_MISMATCH|INVALID_HISTORY)"):
        read(history, record)


def test_missing_scoped_target_is_not_found(harness):
    _, history, _, _ = harness
    with pytest.raises(ContentError, match="CONTENT_NOT_FOUND"):
        history.read("consumer", "school", "missing", version=1, page_size=10)


def test_history_read_has_no_receipt_event_or_content_side_effects(harness):
    service, history, _, store = harness
    record, _ = approved(service)
    before = (dict(store.versions), dict(store.heads), dict(store.receipts),
              tuple(store.events), dict(store.proofs))
    page = read(history, record)
    after = (dict(store.versions), dict(store.heads), dict(store.receipts),
             tuple(store.events), dict(store.proofs))
    assert before == after
    assert all(not hasattr(e, "body_json") for e in page.entries)
