"""FEAT-048 C1 pure lifecycle checks; no SQL, authentication or provider proof."""

from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sketch2life.domain.learning_content import model as domain
from sketch2life.domain.learning_content.model import (
    Authority,
    Capability,
    ContentError,
    ContentState,
    ContentVersion,
    ReviewProof,
)

NOW = datetime(2026, 10, 17, tzinfo=UTC)
AUTHOR = Authority("author", "school", frozenset(Capability))
REVIEWER = Authority("reviewer", "school", frozenset(Capability))
PUBLISHER = Authority("publisher", "school", frozenset(Capability))


def draft() -> ContentVersion:
    return domain.create("record", AUTHOR, {"title": "Butterfly", "source_refs": ["source"]}, NOW)


def proof(content: ContentVersion, dimension: str = "safety") -> ReviewProof:
    return ReviewProof(
        "review-" + dimension, dimension, "approve", content.record_id,
        content.version, content.hash, content.context_revision, "audience",
        REVIEWER.principal_id, "policy-v1", content.review_revision + 1)


def approved() -> ContentVersion:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    for dimension in ("safety", "pedagogical"):
        content = domain.record_review(
            content, REVIEWER, proof(content, dimension),
            expected_revision=content.revision,
            expected_review_revision=content.review_revision)
    return content


def published() -> ContentVersion:
    content = approved()
    return domain.publish(
        content, PUBLISHER, expected_revision=content.revision,
        safety_review_id="review-safety", pedagogical_review_id="review-pedagogical",
        policy_version="policy-v1", audience_hash="audience")


def test_canonicalization_is_key_order_invariant_but_not_unicode_normalization() -> None:
    assert domain.canonical_json({"b": 2, "a": 1}) == domain.canonical_json({"a": 1, "b": 2})
    assert domain.content_hash(domain.canonical_json("é")) != domain.content_hash(
        domain.canonical_json("e\u0301"))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1, 2}])
def test_invalid_payload_rejected(value: object) -> None:
    with pytest.raises(ContentError, match="CONTENT_INVALID_PAYLOAD"):
        domain.canonical_json(value)


def test_edit_keeps_published_original_and_clears_review_in_new_version() -> None:
    original = published()
    updated = domain.edit(original, AUTHOR, {"title": "Changed"}, NOW,
                          expected_revision=original.revision, next_version=2)
    assert original.state == ContentState.PUBLISHED
    assert json.loads(original.body_json)["title"] == "Butterfly"
    assert updated.state == ContentState.DRAFT and updated.version == 2
    assert updated.hash != original.hash and updated.reviews == ()
    assert updated.publication_review_ids == ()
    assert updated.created_at == NOW and original.created_at == NOW


def test_immutable_snapshots() -> None:
    with pytest.raises(FrozenInstanceError):
        draft().state = ContentState.PUBLISHED  # type: ignore[misc]


def test_review_and_record_revisions_are_distinct() -> None:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    assert (content.revision, content.review_revision, content.version) == (2, 1, 1)
    with pytest.raises(ContentError, match="CONTENT_STALE_REVIEW"):
        domain.record_review(content, REVIEWER, proof(content),
                             expected_revision=2, expected_review_revision=2)


@pytest.mark.parametrize("actor", [
    AUTHOR, Authority("outsider", "other-school", frozenset(Capability)),
    Authority("child", "school", frozenset()),
])
def test_self_or_cross_school_or_unprivileged_review_denied(actor: Authority) -> None:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    with pytest.raises(ContentError):
        domain.record_review(content, actor,
                             replace(proof(content), reviewer_id=actor.principal_id),
                             expected_revision=2, expected_review_revision=1)


def test_author_with_every_capability_still_cannot_publish() -> None:
    content = approved()
    with pytest.raises(ContentError, match="CONTENT_SEPARATION_REQUIRED"):
        domain.publish(content, AUTHOR, expected_revision=content.revision,
                       safety_review_id="review-safety", pedagogical_review_id="review-pedagogical",
                       policy_version="policy-v1", audience_hash="audience")


@pytest.mark.parametrize(("field", "value"), [
    ("target_id", "other"), ("target_version", 2), ("target_hash", "f" * 64),
    ("context_revision", 99), ("reviewer_id", "other"), ("review_revision", 99),
    ("state", "revoked"), ("dimension", "unknown"), ("decision", "unknown"),
])
def test_invalid_review_proof_rejected(field: str, value: object) -> None:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    with pytest.raises(ContentError):
        domain.record_review(content, REVIEWER, replace(proof(content), **{field: value}),
                             expected_revision=2, expected_review_revision=1)


def test_request_changes_then_resubmit_starts_fresh_context_and_reviews() -> None:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    changes = domain.record_review(
        content, REVIEWER, replace(proof(content), decision="request_changes", reason="Correct it"),
        expected_revision=2, expected_review_revision=1)
    resubmitted = domain.submit(changes, AUTHOR, expected_revision=changes.revision)
    assert changes.state == ContentState.CHANGES_REQUESTED
    assert resubmitted.context_revision > changes.context_revision and resubmitted.reviews == ()
    assert resubmitted.hash == content.hash


@pytest.mark.parametrize(("field", "value"), [
    ("target_hash", "0" * 64), ("target_version", 4), ("target_id", "other"),
    ("context_revision", 9), ("policy_version", "old"),
    ("audience_hash", "wrong"), ("state", "revoked"), ("decision", "reject"),
    ("reviewer_id", "author"),
])
def test_publish_rechecks_exact_proof_binding(field: str, value: object) -> None:
    content = approved()
    stale = replace(content, reviews=(replace(content.reviews[0], **{field: value}),
                                      content.reviews[1]))
    with pytest.raises(ContentError, match="CONTENT_REVIEW_MISMATCH"):
        domain.publish(stale, PUBLISHER, expected_revision=stale.revision,
                       safety_review_id="review-safety", pedagogical_review_id="review-pedagogical",
                       policy_version="policy-v1", audience_hash="audience")


def test_both_distinct_reviews_are_required() -> None:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    with pytest.raises(ContentError, match="CONTENT_REVIEW_REQUIRED"):
        domain.publish(content, PUBLISHER, expected_revision=2,
                       safety_review_id="review-safety", pedagogical_review_id="review-pedagogical",
                       policy_version="policy-v1", audience_hash="audience")


def test_reviewer_can_publish_with_separate_capability_but_no_author_bypass() -> None:
    content = approved()
    result = domain.publish(content, REVIEWER, expected_revision=content.revision,
                            safety_review_id="review-safety",
                            pedagogical_review_id="review-pedagogical",
                            policy_version="policy-v1", audience_hash="audience")
    assert result.state == ContentState.PUBLISHED


@pytest.mark.parametrize("archive", [False, True])
def test_retire_preserves_bytes_reviews_and_is_terminal(archive: bool) -> None:
    content = published()
    retired = domain.retire(content, PUBLISHER, NOW, expected_revision=content.revision,
                            reason="Content corrected", archive=archive)
    assert retired.hash == content.hash and retired.reviews == content.reviews
    assert retired.recalled_at == NOW
    assert retired.state == (ContentState.ARCHIVED if archive else ContentState.RECALLED)
    with pytest.raises(ContentError, match="CONTENT_TRANSITION_DENIED"):
        domain.edit(retired, AUTHOR, {}, NOW, expected_revision=retired.revision, next_version=2)


@pytest.mark.parametrize("reason", ["", "  ", "x" * 201])
def test_retire_reason_required(reason: str) -> None:
    content = published()
    with pytest.raises(ContentError, match="CONTENT_REASON_REQUIRED"):
        domain.retire(content, PUBLISHER, NOW, expected_revision=content.revision, reason=reason)


def test_stale_revision_and_naive_time_rejected() -> None:
    with pytest.raises(ContentError, match="CONTENT_STALE_REVISION"):
        domain.submit(draft(), AUTHOR, expected_revision=0)
    with pytest.raises(ContentError, match="CONTENT_INVALID_TIME"):
        domain.create("record", AUTHOR, {}, datetime(2026, 10, 17))


def test_domain_has_no_framework_imports() -> None:
    tree = ast.parse(Path(domain.__file__).read_text())
    imported = {node.module.split(".")[0] for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module}
    assert not imported & {"pydantic", "sqlalchemy", "fastapi", "sketch2life"}


@pytest.mark.parametrize("reason", [None, "", " ", "x" * 201])
def test_negative_review_requires_nonblank_reason(reason: str | None) -> None:
    content = domain.submit(draft(), AUTHOR, expected_revision=1)
    with pytest.raises(ContentError, match="CONTENT_REASON_REQUIRED"):
        domain.record_review(content, REVIEWER,
                             replace(proof(content), decision="reject", reason=reason),
                             expected_revision=2, expected_review_revision=1)


@pytest.mark.parametrize(("principal", "organization"), [("", "school"), ("author", " ")])
def test_authority_cannot_have_blank_identity(principal: str, organization: str) -> None:
    with pytest.raises(ContentError, match="CONTENT_INVALID_AUTHORITY"):
        Authority(principal, organization, frozenset(Capability))
