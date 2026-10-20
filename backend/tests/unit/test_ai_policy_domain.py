"""Pure policy lifecycle only; no actual owner authority, SQL or activation proof."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

from sketch2life.domain.ai_policy import model as policy

NOW = datetime(2026, 10, 17, tzinfo=UTC)
CAPS = frozenset(policy.Capability)
AUTHOR = policy.Authority("author", "school", CAPS)
REVIEWER = policy.Authority("reviewer", "school", CAPS)


def draft():
    return policy.create("record", AUTHOR, {"synthetic": True}, NOW)


def submitted():
    return policy.submit(draft(), AUTHOR, expected_revision=1)


def proof(record, dimension="safety", **changes):
    return replace(policy.Review(
        dimension + str(record.review_revision), record.record_id, record.version, record.hash,
        record.context_revision, record.review_revision + 1, dimension, "approve",
        REVIEWER.principal_id, "fixture.governance"), **changes)


def review(record, dimension="safety", **changes):
    return policy.record_review(record, REVIEWER, proof(record, dimension, **changes),
                                expected_revision=record.revision,
                                expected_review_revision=record.review_revision)


def approved():
    return review(review(submitted()), "pedagogical")


def publish(record=None, actor=REVIEWER, **changes):
    record = approved() if record is None else record
    args = dict(expected_revision=record.revision,
                safety_review_id=next((r.review_id for r in record.reviews
                                       if r.dimension == "safety"), "missing"),
                pedagogical_review_id=next((r.review_id for r in record.reviews
                                            if r.dimension == "pedagogical"), "missing"),
                current_review_policy="fixture.governance")
    return policy.publish(record, actor, **(args | changes))


def test_lifecycle_immutable_proofs_and_terminal_version_reintroduction():
    original = approved()
    published = publish(original)
    retired = policy.retire(published, REVIEWER, NOW, expected_revision=published.revision,
                            archive=False, reason="synthetic disable")
    new = policy.edit(retired, AUTHOR, {"synthetic": "new"}, NOW,
                      expected_revision=retired.revision, next_version=2)
    assert new.state == policy.State.DRAFT and not new.reviews
    assert not new.publication_review_ids and new.context_revision == 0
    assert retired.reviews == original.reviews
    assert published.state == policy.State.PUBLISHED and retired.state == policy.State.RECALLED
    assert original.state == policy.State.SUBMITTED and new.hash != original.hash
    with pytest.raises(FrozenInstanceError):
        new.version = 3


def test_canonical_hash_key_order_but_no_unicode_normalization():
    first = policy.create("record", AUTHOR, {"a": 1, "b": 2}, NOW)
    second = policy.create("record", AUTHOR, {"b": 2, "a": 1}, NOW)
    assert first.hash == second.hash
    assert policy.create("r", AUTHOR, {"s": "é"}, NOW).hash != policy.create(
        "r", AUTHOR, {"s": "e\u0301"}, NOW).hash


@pytest.mark.parametrize("body", [{"value": float("nan")}, {"value": object()}])
def test_invalid_canonical_body_is_safe(body):
    with pytest.raises(policy.PolicyError, match="^AI_POLICY_INVALID_BODY$"):
        policy.create("r", AUTHOR, body, NOW)


@pytest.mark.parametrize("capability", list(policy.Capability))
def test_capabilities_not_implied_by_admin_role_or_other_scope(capability):
    for actor in (policy.Authority("SuperAdmin", "school", frozenset()),
                  policy.Authority("operator", "other-school", CAPS)):
        with pytest.raises(policy.PolicyError, match="AI_POLICY_FORBIDDEN"):
            policy.authorize(actor, "school", capability)


@pytest.mark.parametrize("capability", [policy.Capability.REVIEW_SAFETY,
                                       policy.Capability.REVIEW_PEDAGOGICAL,
                                       policy.Capability.PUBLISH])
def test_author_cannot_self_approve_or_publish(capability):
    with pytest.raises(policy.PolicyError, match="AI_POLICY_SEPARATION_REQUIRED"):
        policy.authorize(AUTHOR, "school", capability, "author")


@pytest.mark.parametrize("expected", [True, 0, 2, "1"])
def test_stale_revision_is_distinct_from_version(expected):
    with pytest.raises(policy.PolicyError, match="AI_POLICY_STALE_REVISION"):
        policy.check_revision(draft(), expected)


@pytest.mark.parametrize("version", [True, 0, 1, 3])
def test_edit_requires_next_exact_version(version):
    with pytest.raises(policy.PolicyError, match="AI_POLICY_INVALID_VERSION"):
        policy.edit(draft(), AUTHOR, {}, NOW, expected_revision=1, next_version=version)


@pytest.mark.parametrize("changes", [
    {"target_id": "other"}, {"target_version": 2}, {"target_hash": "b" * 64},
    {"context_revision": 2}, {"review_revision": 99}, {"reviewer_id": "spoof"},
    {"policy_version": ""}, {"review_id": ""},
])
def test_review_exact_policy_context(changes):
    with pytest.raises(policy.PolicyError, match="AI_POLICY_REVIEW_MISMATCH"):
        review(submitted(), **changes)


@pytest.mark.parametrize("dimension", ["unknown", "teaching", "Safety"])
def test_unknown_review_dimension(dimension):
    with pytest.raises(policy.PolicyError, match="AI_POLICY_INVALID_REVIEW"):
        review(submitted(), dimension)


def test_named_review_revision_cas():
    record = submitted()
    with pytest.raises(policy.PolicyError, match="AI_POLICY_STALE_REVIEW"):
        policy.record_review(record, REVIEWER, proof(record), expected_revision=record.revision,
                             expected_review_revision=0)


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_negative_review_resubmission_cannot_borrow_old_approval(decision):
    old = review(submitted())
    changed = review(old, "pedagogical", decision=decision, reason="synthetic changes")
    assert changed.state == policy.State.CHANGES_REQUESTED
    with pytest.raises(policy.PolicyError, match="AI_POLICY_TRANSITION_DENIED"):
        publish(changed)
    resubmitted = policy.submit(changed, AUTHOR, expected_revision=changed.revision)
    assert not resubmitted.reviews and resubmitted.context_revision == old.context_revision + 1
    with pytest.raises(policy.PolicyError, match="AI_POLICY_REVIEW_MISMATCH"):
        policy.record_review(resubmitted, REVIEWER, proof(old, "pedagogical"),
                             expected_revision=resubmitted.revision,
                             expected_review_revision=resubmitted.review_revision)
    assert len(old.reviews) == 1 and len(changed.reviews) == 2


@pytest.mark.parametrize("changes", [
    {"current_review_policy": "new-governance"}, {"current_review_policy": ""},
    {"safety_review_id": "missing"}, {"pedagogical_review_id": "missing"},
    {"safety_review_id": "same", "pedagogical_review_id": "same"},
])
def test_publish_exact_proof_set_and_current_policy(changes):
    with pytest.raises(policy.PolicyError, match="AI_POLICY_REVIEW_REQUIRED"):
        publish(**changes)


def test_missing_one_review_cannot_publish():
    with pytest.raises(policy.PolicyError, match="AI_POLICY_REVIEW_REQUIRED"):
        publish(review(submitted()))


@pytest.mark.parametrize("archive", [True, False])
def test_retired_version_is_terminal(archive):
    record = publish()
    retired = policy.retire(record, REVIEWER, NOW, expected_revision=record.revision,
                            archive=archive, reason="synthetic retirement")
    with pytest.raises(policy.PolicyError, match="AI_POLICY_TRANSITION_DENIED"):
        policy.retire(retired, REVIEWER, NOW, expected_revision=retired.revision,
                      archive=archive, reason="again")
    assert retired.hash == record.hash and retired.publication_review_ids


def test_draft_can_archive_but_not_recall_and_reason_required():
    record = draft()
    for archive, reason, error in [(False, "why", "TRANSITION_DENIED"),
                                   (True, " ", "REASON_REQUIRED")]:
        with pytest.raises(policy.PolicyError, match="AI_POLICY_" + error):
            policy.retire(record, REVIEWER, NOW, expected_revision=1,
                          archive=archive, reason=reason)
    assert policy.retire(record, REVIEWER, NOW, expected_revision=1, archive=True,
                          reason="synthetic").state == policy.State.ARCHIVED


def test_naive_time_cannot_create_or_retire():
    with pytest.raises(policy.PolicyError, match="AI_POLICY_INVALID_TIME"):
        policy.create("r", AUTHOR, {}, datetime(2026, 10, 17))
