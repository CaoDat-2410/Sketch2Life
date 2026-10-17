"""Consumer candidate conformance; memory sink is NOT durable BE1 delivery."""

import json
from dataclasses import replace

import pytest
from pydantic import ValidationError

from sketch2life.application.content_consumer_queries import (
    ContentConsumerQueries,
    notice_from_outbox,
)
from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.application.learning_content_eligibility import ContentEligibility
from sketch2life.contracts.schemas.content_consumers import (
    ContentLifecycleNoticeV1,
    ContentNoticeAckV1,
    ContentReferenceQueryV1,
    PublishedContentReferenceV1,
)
from sketch2life.domain.learning_content.model import ContentError, content_hash
from tests.learning_content_fixtures import (
    NOW,
    AssumedBoundary,
    ComponentStore,
    approved,
    command,
)


def payload(kind="content.recall", state="recalled", **changes):
    value = {"record_id": "record", "organization_id": "school", "version": 1,
             "revision": 6, "hash": "a" * 64, "state": state, "kind": kind}
    value.update(changes)
    return json.dumps(value)


class FixtureSink:
    """Conformance illustration only: no persistent dedup or transport authority."""

    def __init__(self):
        self.seen = {}
        self.blocked = set()
        self.pinned_history = []

    def accept(self, notice: ContentLifecycleNoticeV1) -> ContentNoticeAckV1:
        key = (notice.payload.organization_id, notice.event_id)
        digest = content_hash(notice.model_dump_json())
        previous = self.seen.get(key)
        if previous is not None and previous != digest:
            raise ContentError("CONTENT_NOTICE_CONFLICT")
        duplicate = previous is not None
        if not duplicate:
            self.seen[key] = digest
            if notice.payload.kind in {"content.recall", "content.archive"}:
                self.blocked.add((notice.payload.organization_id, notice.payload.record_id,
                                  notice.payload.version))
        # Publication notice never clears terminal invalidation or grants use.
        return ContentNoticeAckV1(
            event_id=notice.event_id, organization_id=notice.payload.organization_id,
            consumer_id="fixture-consumer", outcome="duplicate" if duplicate else "accepted")


@pytest.fixture
def harness():
    boundary = AssumedBoundary()
    store = ComponentStore(boundary)
    service = ContentCommands(store, boundary, clock=lambda: NOW)
    record, refs = approved(service)
    record = service.execute("publisher", "school", command("publish", "publish", record,
                                                             review_ref=refs),
                              expected_revision=record.revision).record
    query = ContentReferenceQueryV1(record_id=record.record_id, age_months=48,
                                     purpose_code="classroom")
    queries = ContentConsumerQueries(ContentEligibility(store, boundary))
    return service, queries, boundary, record, query


def test_current_reference_is_strict_metadata_not_a_usage_grant(harness):
    _, queries, _, record, query = harness
    ref = queries.resolve_reference("consumer", "school", query)
    assert (ref.record_id, ref.version, ref.hash) == (record.record_id, 1, record.hash)
    assert PublishedContentReferenceV1.model_validate_json(ref.model_dump_json()) == ref
    assert not hasattr(ref, "content") and not hasattr(ref, "asset_refs")
    assert ref.publication_review_ref == record.publication_review_ref


@pytest.mark.parametrize("change", ["review", "source", "authority", "policy"])
def test_cached_reference_does_not_bypass_current_eligibility(harness, change):
    _, queries, boundary, _, query = harness
    pinned = queries.resolve_reference("consumer", "school", query)
    if change == "review":
        boundary.revoked_reviews.add(pinned.publication_review_ref.safety_review_id)
    elif change == "source":
        boundary.usage = False
    elif change == "authority":
        boundary.capabilities["consumer"] = frozenset()
    else:
        boundary.policy = replace(boundary.policy, version="changed")
    with pytest.raises(ContentError):
        queries.resolve_reference("consumer", "school", query)
    assert pinned.hash  # Historical metadata is preserved, not permission to use.


def test_recall_preserves_pin_but_blocks_new_default_and_exact_use(harness):
    service, queries, _, record, query = harness
    pinned = queries.resolve_reference("consumer", "school", query)
    service.execute("recaller", "school", command("recall", "recall", record, reason="withdrawn"),
                    expected_revision=record.revision)
    for request in (query, query.model_copy(update={"version": 1, "expected_hash": pinned.hash})):
        with pytest.raises(ContentError):
            queries.resolve_reference("consumer", "school", request)
    assert pinned.version == 1 and pinned.hash == record.hash


def test_delayed_publish_and_duplicates_do_not_restore_retired_exact_version():
    sink = FixtureSink()
    sink.pinned_history.append(("record", 1, "a" * 64))
    recall = notice_from_outbox("recall-event", "school", payload())
    first = sink.accept(recall)
    replay = sink.accept(recall)
    publication = notice_from_outbox("old-publish", "school", payload(
        "content.publish", "published", revision=5))
    sink.accept(publication)
    assert first.outcome == "accepted" and replay.outcome == "duplicate"
    assert sink.blocked == {("school", "record", 1)}
    assert sink.pinned_history == [("record", 1, "a" * 64)]
    assert len(sink.seen) == 2


def test_same_event_id_changed_payload_is_conflict_not_duplicate():
    sink = FixtureSink()
    sink.accept(notice_from_outbox("event", "school", payload()))
    with pytest.raises(ContentError, match="CONTENT_NOTICE_CONFLICT"):
        sink.accept(notice_from_outbox("event", "school", payload(revision=7)))


@pytest.mark.parametrize("kind,state", [
    ("content.create", "draft"), ("content.edit", "draft"),
    ("content.submit_review", "submitted"), ("content.record_review", "submitted"),
    ("content.record_review", "changes_requested"),
    ("content.request_changes", "changes_requested"), ("content.publish", "published"),
    ("content.recall", "recalled"), ("content.archive", "archived"),
])
def test_notice_matches_existing_owned_outbox_shape(kind, state):
    notice = notice_from_outbox("event", "school", payload(kind, state))
    assert notice.payload.kind == kind
    assert ContentLifecycleNoticeV1.model_validate_json(notice.model_dump_json()) == notice


@pytest.mark.parametrize("changes", [dict(state="published"), dict(kind="unknown"),
                                    dict(version=True), dict(version=0), dict(hash="invalid"),
                                    dict(secret="private-content")])
def test_invalid_notice_never_echoes_payload(changes):
    with pytest.raises(ContentError) as error:
        notice_from_outbox("event", "school", payload(**changes))
    assert str(error.value) == "CONTENT_INVALID_NOTICE"


def test_notice_scope_and_exact_version_are_not_substituted():
    with pytest.raises(ContentError, match="CONTENT_NOTICE_SCOPE_MISMATCH"):
        notice_from_outbox("event", "other-school", payload())
    sink = FixtureSink()
    sink.accept(notice_from_outbox("event", "school", payload()))
    assert ("school", "record", 2) not in sink.blocked


def test_query_rejects_fake_scope_and_hash_without_exact_version():
    with pytest.raises(ValidationError):
        ContentReferenceQueryV1(record_id="record", age_months=48,
                                purpose_code="classroom", expected_hash="a" * 64)
    with pytest.raises(ValidationError):
        ContentReferenceQueryV1.model_validate({"record_id": "record", "age_months": 48,
                                                "purpose_code": "classroom",
                                                "organization_id": "injected"})
