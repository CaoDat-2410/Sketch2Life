"""Owned08 pure rules only: no runtime authorization, decoder or SQL evidence."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    FinalArtifact,
    ReviewState,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
    canonical_digest,
)

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def ref(name="fixture.ref", version=1, hash="a" * 64):
    return ExactRef(name, version, hash)


def pin(**changes):
    return replace(VideoPin(
        "school", "session", ref("bundle"), 0, 0, 0, (ref("source"),), Strategy.GENERATE,
        ref("content.profile"), ref("encoding"), ref("rights"), ref("retry"),
        ref("policy"), 1, ref("model.profile")
    ), **changes)


def run():
    return VideoRun("video", 1, 1, 1, "job", pin(), NOW)


def artifact(p=None):
    p = p or pin()
    return FinalArtifact(ref("artifact"), p.digest(), p.encoding, p.content_profile)


@pytest.mark.parametrize("value", ["", "hello world", "https://host/x", "../file", "x" * 121])
def test_opaque_ids(value):
    with pytest.raises(VideoError, match="VIDEO_INVALID_ID"):
        ref(value)


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "1", None])
def test_exact_ref_requires_positive_integer(value):
    with pytest.raises(VideoError, match="VIDEO_INVALID_REVISION"):
        ref(version=value)


@pytest.mark.parametrize("value", ["", "A" * 64, "g" * 64, "a" * 63, "a" * 65, None])
def test_exact_ref_hash(value):
    with pytest.raises(VideoError, match="VIDEO_INVALID_HASH"):
        ref(hash=value)


def test_canonical_golden_vector_and_order():
    assert canonical_digest({"b": 2, "a": 1}) == (
        "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    )
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
    assert canonical_digest({"text": "é"}) != canonical_digest({"text": "e\u0301"})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object(), {"x": {1, 2}}])
def test_invalid_canonical_payload(value):
    with pytest.raises(VideoError, match="VIDEO_INVALID_CANONICAL_INPUT"):
        canonical_digest(value)


@pytest.mark.parametrize("field", ["organization_id", "session_id"])
def test_scope_changes_fingerprint(field):
    assert pin(**{field: "other"}).digest() != pin().digest()


@pytest.mark.parametrize("field", [
    "bundle", "content_profile", "encoding", "rights", "retry_policy", "policy", "model_profile"
])
def test_exact_ref_changes_fingerprint(field):
    p = pin()
    changed = replace(getattr(p, field), version=2)
    assert replace(p, **{field: changed}).digest() != p.digest()


@pytest.mark.parametrize("field", [
    "editorial_revision", "context_revision", "audience_revision", "policy_epoch"
])
def test_revision_changes_fingerprint(field):
    assert pin(**{field: 2}).digest() != pin().digest()


@pytest.mark.parametrize("field", [
    "editorial_revision", "context_revision", "audience_revision", "policy_epoch"
])
@pytest.mark.parametrize("bad", [True, "2", -1, 2.0])
def test_pin_revision_strict(field, bad):
    with pytest.raises(VideoError, match="VIDEO_INVALID_REVISION"):
        pin(**{field: bad})


def test_source_set_canonicalization_and_mutation():
    p = pin(sources=(ref("b"), ref("a")))
    assert p.digest() == pin(sources=(ref("a"), ref("b"))).digest()
    assert p.digest() != pin(sources=(ref("a"), ref("b", version=2))).digest()
    with pytest.raises(FrozenInstanceError):
        p.session_id = "other"


@pytest.mark.parametrize("sources", [(), [], [ref()], ("not-ref",)])
def test_invalid_sources(sources):
    with pytest.raises(VideoError, match="VIDEO_INVALID_SOURCES"):
        pin(sources=sources)


def test_duplicate_source_including_conflicting_hash_rejected():
    for sources in ((ref(), ref()), (ref(), ref(hash="b" * 64))):
        with pytest.raises(VideoError, match="VIDEO_DUPLICATE_SOURCE"):
            pin(sources=sources)


@pytest.mark.parametrize("changes", [
    {"model_profile": None}, {"library_asset": ref("library")},
    {"strategy": Strategy.REVIEWED_LIBRARY},
    {"strategy": Strategy.REVIEWED_LIBRARY, "model_profile": None},
    {"strategy": Strategy.COMPOSE_LIBRARY},
])
def test_incompatible_strategy_refs(changes):
    with pytest.raises(VideoError, match="VIDEO_STRATEGY_REF_MISMATCH"):
        pin(**changes)


def test_library_and_compose_valid_pins_are_distinct():
    library = pin(strategy=Strategy.REVIEWED_LIBRARY, model_profile=None,
                  library_asset=ref("library"))
    compose = replace(library, strategy=Strategy.COMPOSE_LIBRARY)
    assert len({library.digest(), compose.digest(), pin().digest()}) == 3
    assert replace(compose, model_profile=ref("model")).digest() != compose.digest()


@pytest.mark.parametrize("field", [
    "bundle", "content_profile", "encoding", "rights", "retry_policy", "policy",
    "model_profile", "library_asset"
])
def test_refs_cannot_be_mutable_or_untyped(field):
    with pytest.raises(VideoError, match="VIDEO_INVALID_REF"):
        pin(**{field: {"ref": "untrusted"}})


def test_enum_not_coerced_in_domain():
    with pytest.raises(VideoError, match="VIDEO_INVALID_STRATEGY"):
        pin(strategy="generate")


def test_finalization_does_not_approve_or_start_playback():
    queued = run()
    running = queued.start(1, "attempt")
    ready = running.finalize(2, "attempt", artifact())
    assert queued.generation_state is JobState.QUEUED
    assert running.generation_state is JobState.RUNNING
    assert ready.generation_state is JobState.SUCCEEDED
    assert ready.review_state is ReviewState.READY_FOR_REVIEW
    assert ready.video_version == queued.video_version
    assert ready.review_revision == queued.review_revision
    assert ready.run_revision == 3
    assert not hasattr(ready, "playback_url")
    assert not hasattr(ready, "approve")
    assert not hasattr(ready, "retry")


@pytest.mark.parametrize("method", ["start", "finalize", "cancel"])
def test_stale_revision_rejected(method):
    with pytest.raises(VideoError, match="VIDEO_STALE_RUN"):
        if method == "start":
            run().start(2, "attempt")
        elif method == "finalize":
            run().start(1, "attempt").finalize(1, "attempt", artifact())
        else:
            run().cancel(2)


def test_late_completion_after_cancel_rejected():
    cancelled = run().start(1, "attempt").cancel(2)
    with pytest.raises(VideoError, match="VIDEO_ATTEMPT_NOT_CURRENT"):
        cancelled.finalize(3, "attempt", artifact())
    with pytest.raises(VideoError, match="VIDEO_INVALID_TRANSITION"):
        cancelled.start(3, "attempt2")


def test_wrong_attempt_and_duplicate_completion_rejected():
    running = run().start(1, "attempt")
    with pytest.raises(VideoError, match="VIDEO_ATTEMPT_NOT_CURRENT"):
        running.finalize(2, "other", artifact())
    ready = running.finalize(2, "attempt", artifact())
    with pytest.raises(VideoError, match="VIDEO_ATTEMPT_NOT_CURRENT"):
        ready.finalize(3, "attempt", artifact())
    with pytest.raises(VideoError, match="VIDEO_INVALID_TRANSITION"):
        ready.cancel(3)


@pytest.mark.parametrize("changes", [
    {"pin_digest": "b" * 64}, {"encoding": ref("other")},
    {"content_profile": ref("other")},
])
def test_output_bound_to_exact_request_profile(changes):
    with pytest.raises(VideoError, match="VIDEO_ARTIFACT_MISMATCH"):
        run().start(1, "attempt").finalize(2, "attempt", replace(artifact(), **changes))


@pytest.mark.parametrize("changes", [
    {"generation_state": JobState.SUCCEEDED},
    {"artifact": artifact()}, {"review_state": ReviewState.READY_FOR_REVIEW},
    {"generation_state": JobState.RUNNING}, {"created_at": NOW.replace(tzinfo=None)},
    {"generation_state": "queued"}, {"review_state": "pending_media"},
])
def test_inconsistent_run_rehydration_rejected(changes):
    with pytest.raises(VideoError):
        replace(run(), **changes)
