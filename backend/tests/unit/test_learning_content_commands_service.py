"""C3b component tests. Assumed owner ports/memory store are NOT runtime evidence."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.application.learning_content_eligibility import ContentEligibility
from sketch2life.contracts.schemas.learning_content import ContentCommandResult
from sketch2life.domain.learning_content.model import Capability, ContentError, ContentState
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
    return service, boundary, store


def publish(service):
    record, refs = approved(service)
    cmd = command("publish", "publish", record, review_ref=refs)
    result = service.execute("publisher", "school", cmd, expected_revision=record.revision)
    return result, cmd, record.revision


def test_complete_lifecycle_and_shared_review_response(harness):
    service, boundary, store = harness
    result, _, _ = publish(service)
    assert result.record.state == "published" and result.record.revision == 5
    assert result.record.publication_review_ref.safety_review_id
    assert ContentCommandResult.model_validate_json(result.model_dump_json()) == result
    resolver = ContentEligibility(store, boundary)
    assert resolver.resolve("consumer", "school", result.record.record_id,
                            age_months=48, purpose_code="classroom").version == 1
    recall = command("recall", "recall", result.record, reason="source withdrawn")
    recalled = service.execute("recaller", "school", recall, expected_revision=5)
    assert recalled.record.recalled_at == NOW and recalled.record.state == "recalled"
    assert recalled.record.hash == result.record.hash
    assert recalled.record.publication_review_ref == result.record.publication_review_ref
    with pytest.raises(ContentError, match="CONTENT_NOT_ELIGIBLE"):
        resolver.resolve("consumer", "school", result.record.record_id,
                         age_months=48, purpose_code="classroom")
    assert len(store.events) == len(store.receipts) == 6
    assert not boundary.held


def test_edit_published_preserves_old_version_and_clears_approvals(harness):
    service, boundary, store = harness
    result, _, _ = publish(service)
    body = {**BODY, "title": "New title"}
    edited = service.execute(
        "author", "school", command("edit", "edit", result.record, content=body),
        expected_revision=5)
    assert edited.record.version == 2 and edited.record.state == "draft"
    assert edited.record.review_revision == 0 and edited.record.publication_review_ref is None
    old = store.load("school", result.record.record_id, version=1)
    assert old.state == ContentState.PUBLISHED and old.hash == result.record.hash
    assert store.load("school", result.record.record_id).reviews == ()
    resolver = ContentEligibility(store, boundary)
    assert resolver.resolve("consumer", "school", result.record.record_id,
                            age_months=48, purpose_code="classroom").version == 1
    service.execute("recaller", "school", command("recall", "recall-old", result.record,
                                                  reason="retire old version"),
                    expected_revision=edited.record.revision)
    assert store.load("school", result.record.record_id).state == ContentState.DRAFT
    assert store.load("school", result.record.record_id, version=1).state == ContentState.RECALLED


@pytest.mark.parametrize("action,decision", [("record_review", "reject"),
                                             ("request_changes", "request_changes")])
def test_negative_review_can_remediate_failed_moderation_and_resubmit(harness, action, decision):
    service, boundary, store = harness
    record = submitted(service)
    boundary.moderation = False
    cmd = review_command(record, "safety", "negative", decision=decision, action=action)
    result = service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    assert result.record.state == "changes_requested"
    assert result.review_record.reviewed_at == NOW and result.review_record.state == "effective"
    assert result.review_record.reviewer_principal_id == "reviewer"
    assert result.review_record.policy_version == "policy-v1"
    fresh = service.execute("author", "school", command("submit_review", "resubmit", result.record),
                            expected_revision=result.record.revision)
    assert fresh.record.context_revision == record.context_revision + 1
    assert store.load("school", record.record_id).reviews == ()
    with pytest.raises(ContentError, match="CONTENT_REVIEW_INEFFECTIVE"):
        service.execute("reviewer", "school", cmd, expected_revision=record.revision)


def test_approve_requires_moderation_but_draft_and_submit_can_be_reviewed(harness):
    service, boundary, store = harness
    boundary.moderation = False
    record = submitted(service)
    with pytest.raises(ContentError, match="CONTENT_SOURCE_DENIED"):
        service.execute("reviewer", "school", review_command(record, "safety", "approve"),
                        expected_revision=record.revision)
    assert len(store.events) == 2


@pytest.mark.parametrize("classification", ["child_derived", "unknown", ""])
def test_unadopted_source_classification_fails_closed(harness, classification):
    service, boundary, store = harness
    boundary.classification = classification
    with pytest.raises(ContentError, match="CONTENT_SOURCE_AUTHORITY_REQUIRED"):
        service.execute("author", "school", command("create", "create", content=BODY))
    assert not store.events and not store.heads and not store.receipts


def test_receipt_failure_rolls_back_all_component_changes(harness):
    service, _, store = harness
    store.fail_receipt = True
    with pytest.raises(ContentError, match="SYNTHETIC_RECEIPT_FAILURE"):
        service.execute("author", "school", command("create", "create", content=BODY))
    assert not store.events and not store.versions and not store.receipts and not store.heads


@pytest.mark.parametrize("expected", [None, 0, -1, True])
def test_mutations_require_record_if_match(harness, expected):
    service, _, _ = harness
    record = submitted(service)
    with pytest.raises(ContentError, match="CONTENT_PRECONDITION_REQUIRED"):
        service.execute("author", "school", command("archive", "archive", record, reason="retired"),
                        expected_revision=expected)


def test_create_rejects_record_precondition(harness):
    service, _, _ = harness
    with pytest.raises(ContentError, match="CONTENT_UNEXPECTED_PRECONDITION"):
        service.execute("author", "school", command("create", "create", content=BODY),
                        expected_revision=1)


@pytest.mark.parametrize("fault,code", [("hash", "CONTENT_HASH_MISMATCH"),
                                       ("revision", "CONTENT_STALE_REVISION")])
def test_exact_content_and_record_cas_are_separate(harness, fault, code):
    service, _, _ = harness
    record = submitted(service)
    if fault == "hash":
        record = record.model_copy(update={"hash": "b" * 64})
    with pytest.raises(ContentError, match=code):
        service.execute(
            "recaller", "school", command("archive", "archive", record, reason="retire"),
            expected_revision=1 if fault == "revision" else record.revision)


@pytest.mark.parametrize("fault", ["content_kind", "context", "audience", "duplicate_purposes",
                                  "age_policy", "content_policy", "review_revision"])
def test_shared_review_binding_is_exact(harness, fault):
    service, _, store = harness
    record = submitted(service)
    cmd = review_command(record, "safety", "review")
    raw = json.loads(cmd.model_dump_json())
    if fault == "content_kind":
        raw["review"]["review_context"]["content_kind"] = "video"
    elif fault == "context":
        raw["review"]["source_context_revision"] += 1
    elif fault == "audience":
        raw["review"]["audience_scope"]["purpose_codes"] = ["observation"]
    elif fault == "duplicate_purposes":
        raw["review"]["audience_scope"]["purpose_codes"] *= 2
    elif fault == "age_policy":
        raw["review"]["review_context"]["age_policy_ref"] = "other"
    elif fault == "content_policy":
        raw["review"]["review_context"]["content_policy_ref"] = "other"
    else:
        raw["review"]["expected_review_revision"] = 0
    from sketch2life.contracts.schemas.learning_content import CONTENT_COMMAND_ADAPTER
    invalid = CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(raw))
    with pytest.raises(ContentError, match="CONTENT_(REVIEW_MISMATCH|STALE_REVIEW)"):
        service.execute("reviewer", "school", invalid, expected_revision=record.revision)
    assert len(store.events) == 2


def test_same_create_replays_without_side_effects_but_changed_payload_conflicts(harness):
    service, _, store = harness
    cmd = command("create", "create", content=BODY)
    first = service.execute("author", "school", cmd)
    second = service.execute("author", "school", cmd)
    assert second.replayed and second.record == first.record
    assert len(store.events) == len(store.receipts) == 1
    changed = command("create", "create", content={**BODY, "title": "Changed"})
    with pytest.raises(ContentError, match="CONTENT_COMMAND_CONFLICT"):
        service.execute("author", "school", changed)


def test_request_key_is_scoped_to_principal(harness):
    service, _, store = harness
    cmd = command("create", "same-key", content=BODY)
    first = service.execute("author", "school", cmd)
    second = service.execute("editor", "school", cmd)
    assert first.record.record_id != second.record.record_id and len(store.events) == 2


def test_duplicate_submit_does_not_reapply_original_stale_cas(harness):
    service, _, store = harness
    draft = service.execute("author", "school", command("create", "create", content=BODY)).record
    cmd = command("submit_review", "submit", draft)
    service.execute("author", "school", cmd, expected_revision=1)
    replay = service.execute("author", "school", cmd, expected_revision=1)
    assert replay.replayed and replay.current_revision == 2 and len(store.events) == 2
    with pytest.raises(ContentError, match="CONTENT_COMMAND_CONFLICT"):
        service.execute("author", "school", cmd, expected_revision=2)


def test_replay_rechecks_current_authority(harness):
    service, boundary, store = harness
    cmd = command("create", "create", content=BODY)
    service.execute("author", "school", cmd)
    boundary.capabilities["author"] = frozenset()
    with pytest.raises(ContentError, match="CONTENT_FORBIDDEN"):
        service.execute("author", "school", cmd)
    assert len(store.events) == 1


def test_superseded_unpublished_version_cannot_publish_or_replay_review(harness):
    service, _, store = harness
    record, refs = approved(service)
    service.execute("author", "school", command("edit", "edit", record, content=BODY),
                    expected_revision=record.revision)
    with pytest.raises(ContentError, match="CONTENT_SUPERSEDED_VERSION"):
        service.execute(
            "publisher", "school", command("publish", "publish", record, review_ref=refs),
            expected_revision=record.revision + 1)
    assert store.load("school", record.record_id).reviews == ()


@pytest.mark.parametrize("fault", ["review_revoked", "reviewer_revoked", "policy", "usage"])
def test_publish_checks_current_owner_decisions(harness, fault):
    service, boundary, _ = harness
    record, refs = approved(service)
    if fault == "review_revoked":
        boundary.revoked_reviews.add(refs["safety_review_id"])
    elif fault == "reviewer_revoked":
        boundary.revoked_reviewers.add("reviewer")
    elif fault == "policy":
        boundary.policy = replace(boundary.policy, version="new-policy")
    else:
        boundary.usage = False
    with pytest.raises(ContentError):
        service.execute(
            "publisher", "school", command("publish", "publish", record, review_ref=refs),
            expected_revision=record.revision)


def test_publish_replay_after_recall_denied_but_recall_replay_survives_policy_change(harness):
    service, boundary, store = harness
    result, cmd, expected = publish(service)
    assert service.execute("publisher", "school", cmd, expected_revision=expected).replayed
    boundary.usage = False
    boundary.policy = replace(boundary.policy, version="disabled", content_kinds=frozenset())
    recall = command("recall", "recall", result.record, reason="unsafe source")
    recalled = service.execute("recaller", "school", recall, expected_revision=5)
    replay = service.execute("recaller", "school", recall, expected_revision=5)
    assert replay.replayed and replay.record == recalled.record
    with pytest.raises(ContentError, match="CONTENT_RECEIPT_INEFFECTIVE"):
        service.execute("publisher", "school", cmd, expected_revision=expected)
    assert len(store.events) == 6


def test_author_cannot_review_or_publish_even_with_all_capabilities(harness):
    service, boundary, _ = harness
    boundary.capabilities["author"] = frozenset(Capability)
    record = submitted(service)
    with pytest.raises(ContentError, match="CONTENT_SEPARATION_REQUIRED"):
        service.execute("author", "school", review_command(record, "safety", "self-review"),
                        expected_revision=record.revision)
    with pytest.raises(ContentError, match="CONTENT_SEPARATION_REQUIRED"):
        service.execute("author", "school", command("publish", "self-publish", record, review_ref={
            "safety_review_id": "missing", "pedagogical_review_id": "missing-too",
            "review_policy_version": "policy-v1"}), expected_revision=record.revision)


def test_review_capability_is_independent_from_author_and_publisher(harness):
    service, _, _ = harness
    record = submitted(service)
    with pytest.raises(ContentError, match="CONTENT_FORBIDDEN"):
        service.execute("publisher", "school", review_command(record, "safety", "wrong-cap"),
                        expected_revision=record.revision)


def test_archive_is_terminal_and_idempotent(harness):
    service, _, _ = harness
    record = submitted(service)
    cmd = command("archive", "archive", record, reason="withdraw draft")
    archived = service.execute("recaller", "school", cmd, expected_revision=record.revision)
    assert archived.record.state == "archived"
    assert service.execute("recaller", "school", cmd,
                           expected_revision=record.revision).replayed
    with pytest.raises(ContentError, match="CONTENT_TRANSITION_DENIED"):
        service.execute("author", "school", command("edit", "edit", archived.record, content=BODY),
                        expected_revision=archived.record.revision)


def test_component_concurrent_identical_create_has_one_effect(harness):
    service, _, store = harness
    cmd = command("create", "create", content=BODY)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.execute("author", "school", cmd), range(2)))
    assert sorted(result.replayed for result in results) == [False, True]
    assert len(store.events) == 1


def test_invalid_receipt_never_echoes_its_payload(harness):
    service, _, store = harness
    cmd = command("create", "create", content=BODY)
    service.execute("author", "school", cmd)
    key, receipt = next(iter(store.receipts.items()))
    store.receipts[key] = replace(receipt, result_json='{"private":"do-not-echo"}')
    with pytest.raises(ContentError) as error:
        service.execute("author", "school", cmd)
    assert str(error.value) == "CONTENT_INVALID_RECEIPT"


def test_wrong_organization_denied_before_mutation(harness):
    service, _, store = harness
    with pytest.raises(ContentError, match="CONTENT_FORBIDDEN"):
        service.execute("author", "other-school", command("create", "create", content=BODY))
    assert not store.events


def test_review_replay_requires_same_current_effective_proof(harness):
    service, boundary, store = harness
    record = submitted(service)
    cmd = review_command(record, "safety", "review")
    first = service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    replay = service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    assert replay.replayed and replay.review_record == first.review_record
    assert len(store.events) == 3
    boundary.revoked_reviews.add(first.review_record.review_id)
    with pytest.raises(ContentError, match="CONTENT_REVIEW_INEFFECTIVE"):
        service.execute("reviewer", "school", cmd, expected_revision=record.revision)


def test_replaced_dimension_review_cannot_replay(harness):
    service, _, _ = harness
    record = submitted(service)
    cmd = review_command(record, "safety", "review")
    first = service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    service.execute("reviewer", "school", review_command(first.record, "safety", "replacement"),
                    expected_revision=first.record.revision)
    with pytest.raises(ContentError, match="CONTENT_REVIEW_INEFFECTIVE"):
        service.execute("reviewer", "school", cmd, expected_revision=record.revision)


@pytest.mark.parametrize("fault", ["usage", "policy", "moderation", "review"])
def test_publication_replay_rechecks_current_eligibility(harness, fault):
    service, boundary, store = harness
    result, cmd, expected = publish(service)
    if fault == "usage":
        boundary.usage = False
    elif fault == "policy":
        boundary.policy = replace(boundary.policy, version="new-policy")
    elif fault == "moderation":
        boundary.moderation = False
    else:
        boundary.revoked_reviews.add(result.record.publication_review_ref.safety_review_id)
    with pytest.raises(ContentError):
        service.execute("publisher", "school", cmd, expected_revision=expected)
    assert len(store.events) == 5


def test_submit_old_context_receipt_cannot_replay_after_resubmit(harness):
    service, _, _ = harness
    draft = service.execute("author", "school", command("create", "create", content=BODY)).record
    cmd = command("submit_review", "submit", draft)
    record = service.execute("author", "school", cmd, expected_revision=1).record
    changed = service.execute("reviewer", "school", review_command(
        record, "safety", "changes", decision="request_changes", action="request_changes"),
        expected_revision=record.revision).record
    service.execute("author", "school", command("submit_review", "resubmit", changed),
                    expected_revision=changed.revision)
    with pytest.raises(ContentError, match="CONTENT_RECEIPT_INEFFECTIVE"):
        service.execute("author", "school", cmd, expected_revision=1)


def test_review_authority_does_not_include_other_dimension(harness):
    service, boundary, _ = harness
    boundary.capabilities["reviewer"] = frozenset({Capability.REVIEW_SAFETY})
    record = submitted(service)
    with pytest.raises(ContentError, match="CONTENT_FORBIDDEN"):
        service.execute(
            "reviewer", "school", review_command(record, "pedagogical", "wrong-dimension"),
            expected_revision=record.revision)
