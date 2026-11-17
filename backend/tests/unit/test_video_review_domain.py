"""Pure09 review/head evidence; no actual current owner or playback capability."""

from dataclasses import replace
from datetime import timedelta

import pytest

from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.domain.video_review.model import (
    Applicability,
    Decision,
    Invalidation,
    ReviewHead,
    ReviewSubject,
    TeachingAudience,
)
from tests.unit.test_knowledge_video_worker import NOW, harness


def subject():
    h = harness()
    return ReviewSubject.from_ready(
        h.finalized.video_run,
        TeachingAudience("session", 0, ("group",), ("child",), (("child", 1),)),
    )


def approved():
    return ReviewHead(subject(), 1).record(1, "review", "teacher", Decision.APPROVE, None, NOW)


def test_exact_artifact_hash_is_not_pin_digest_or_catalog_hash_and_ready_not_approved():
    target = subject()
    assert target.artifact.hash != target.pin_digest
    assert not ReviewHead(target, 1).permits_intent(target)
    assert not hasattr(approved(), "playback_url") and not hasattr(approved(), "playing")


@pytest.mark.parametrize("decision", list(Decision))
def test_all_decisions_independent_of08_render_revision_and_no_autoplay(decision):
    h = harness()
    initial = ReviewHead(subject(), 7)
    result = initial.record(7, "review", "teacher", decision, "fixture reason", NOW)
    assert result.revision == 8 and result.entry.revision == 8
    assert result.permits_intent(result.subject) == (decision is Decision.APPROVE)
    assert h.finalized.video_run.review_revision == 1
    assert initial.entry is None


@pytest.mark.parametrize("reason", list(Invalidation))
def test_invalidation_keeps_history_and_cannot_reapprove_or_resurrect(reason):
    head = approved()
    stale = head.invalidate(head.revision, reason)
    assert stale.entry == head.entry and stale.revision == 3
    assert stale.applicability is (
        Applicability.REVOKED if reason is Invalidation.USAGE_REVOKED else Applicability.STALE
    )
    assert not stale.permits_intent(stale.subject)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_TARGET_NOT_CURRENT"):
        stale.record(3, "next", "teacher", Decision.APPROVE, None, NOW)
    with pytest.raises(VideoError):
        stale.invalidate(3, reason)


@pytest.mark.parametrize(
    "changes",
    [
        {"video_version": 2},
        {"video_id": "other"},
        {"organization_id": "other"},
        {"artifact": ExactRef("asset", 1, "d" * 64)},
        {"pin_digest": "d" * 64},
        {"source_context_revision": 1},
        {"policy": ExactRef("policy", 2, "d" * 64)},
    ],
)
def test_old_approval_does_not_apply_to_changed_exact_target(changes):
    head = approved()
    assert not head.permits_intent(replace(head.subject, **changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"session_id": "other"},
        {"audience_revision": 1},
        {"group_ids": ("other",)},
        {"participant_ids": ("other",)},
        {"consent_revisions": (("child", 2),)},
    ],
)
def test_audience_context_consent_change_not_authorized_by_historical_approval(changes):
    head = approved()
    target = replace(head.subject, audience=replace(head.subject.audience, **changes))
    assert not head.permits_intent(target)


def test_audience_set_order_canonicalization_and_no_fabricated_consent_requirement():
    a = TeachingAudience("session", 0, ("b", "a"), ("d", "c"), (("d", 2), ("c", 1)))
    b = TeachingAudience("session", 0, ("a", "b"), ("c", "d"), (("c", 1), ("d", 2)))
    assert a.digest() == b.digest()
    assert TeachingAudience("session", 0, (), (), ()).digest()


@pytest.mark.parametrize(
    "changes",
    [
        {"group_ids": ("x", "x")},
        {"participant_ids": ("x", "x")},
        {"consent_revisions": (("x", 1), ("x", 2))},
        {"audience_revision": True},
        {"consent_revisions": (("x", True),)},
        {"session_id": "url/private"},
        {"group_ids": ["x"]},
        {"consent_revisions": (["x", 1],)},
    ],
)
def test_invalid_audience_closed(changes):
    with pytest.raises(VideoError):
        replace(subject().audience, **changes)


@pytest.mark.parametrize("expected", [0, 1, 3, True, "2"])
def test_review_cas_not_job_run_or_session_revision(expected):
    head = approved()
    with pytest.raises(VideoError):
        head.record(expected, "next", "teacher", Decision.REJECT, "reason", NOW)
    assert head.revision == 2 and head.entry.decision is Decision.APPROVE


@pytest.mark.parametrize("reason", [None, "", "  ", "x" * 201, True])
@pytest.mark.parametrize("decision", [Decision.REJECT, Decision.REQUEST_CHANGES])
def test_negative_decision_requires_valid_reason(decision, reason):
    with pytest.raises(VideoError):
        ReviewHead(subject(), 1).record(1, "review", "teacher", decision, reason, NOW)


@pytest.mark.parametrize(
    "field,value",
    [
        ("video_version", True),
        ("source_context_revision", True),
        ("pin_digest", "bad"),
        ("artifact", None),
        ("policy", None),
        ("audience", None),
    ],
)
def test_subject_native_invalidity(field, value):
    with pytest.raises(VideoError):
        replace(subject(), **{field: value})


def test_not_ready_and_wrong_session_not_reviewable():
    h = harness()
    with pytest.raises(VideoError, match="VIDEO_REVIEW_MEDIA_NOT_READY"):
        ReviewSubject.from_ready(h.attempt.run, subject().audience)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_AUDIENCE_MISMATCH"):
        ReviewSubject.from_ready(
            h.finalized.video_run, replace(subject().audience, session_id="other")
        )


def test_backdated_review_or_naive_time_rejected():
    head = approved()
    for timestamp in (NOW - timedelta(seconds=1), NOW.replace(tzinfo=None)):
        with pytest.raises(VideoError):
            head.record(2, "next", "teacher", Decision.APPROVE, None, timestamp)


def test_set_equivalent_audience_also_equal_for_subject_applicability():
    first = TeachingAudience("session", 0, ("b", "a"), (), ())
    second = TeachingAudience("session", 0, ("a", "b"), (), ())
    assert first == second
    target = replace(subject(), audience=first)
    head = ReviewHead(target, 1).record(1, "review", "teacher", Decision.APPROVE, None, NOW)
    assert head.permits_intent(replace(target, audience=second))


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision", "approve"),
        ("revision", True),
        ("reviewer_id", "private/url"),
    ],
)
def test_forged_native_entry_revalidated_before_intent(field, value):
    head = approved()
    object.__setattr__(head.entry, field, value)
    with pytest.raises(VideoError):
        head.permits_intent(head.subject)


def test_effective_head_cannot_claim_newer_revision_than_its_last_record():
    with pytest.raises(VideoError, match="VIDEO_REVIEW_INVALID_RECORD"):
        replace(approved(), revision=3)


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision", True),
        ("applicability", "effective"),
        ("invalidation", Invalidation.CONTENT_CHANGED),
    ],
)
def test_forged_native_head_revalidated_before_use(field, value):
    head = approved()
    object.__setattr__(head, field, value)
    with pytest.raises(VideoError):
        head.permits_intent(head.subject)


def test_rejection_overrides_approval_but_preserves_immutable_previous_head():
    head = approved()
    rejected = head.record(2, "rejection", "teacher", Decision.REJECT, "fix", NOW)
    assert not rejected.permits_intent(rejected.subject)
    assert head.permits_intent(head.subject)
