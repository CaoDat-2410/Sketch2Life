"""CMD-40 / DATA-27 candidate checks, not consumer or live owner acceptance."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.knowledge_video import VIDEO_LIFECYCLE_CONTRACT
from sketch2life.contracts.schemas.knowledge_video import (
    CreateKnowledgeVideo,
    KnowledgeVideoView,
    VideoAttemptView,
    VideoExactRef,
)

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def test_adopted_video_lifecycle_contract_is_versioned():
    assert VIDEO_LIFECYCLE_CONTRACT == "BE2-VIDEO-LIFECYCLE/1"


def ref():
    return VideoExactRef(ref="fixture.ref", version=1, hash="a" * 64)


def command(**changes):
    return CreateKnowledgeVideo.model_validate({
        "bundle_id": "bundle", "bundle_version": 1, "bundle_hash": "a" * 64,
        "audience_context_revision": 0, "strategy": "generate", **changes,
    })


def view(**changes):
    return KnowledgeVideoView.model_validate({
        "video_id": "video", "video_version": 1, "video_run_revision": 1,
        "video_review_revision": 1, "organization_id": "school", "session_id": "session",
        "job_id": "job", "job_revision": 1, "generation_state": "queued",
        "review_state": "pending_media", "retry_policy_version": ref(),
        "attempt_history": (), "created_at": NOW, **changes,
    })


@pytest.mark.parametrize("strategy", ["reviewed_library", "generate", "compose_library"])
def test_command_strategies_and_json_roundtrip(strategy):
    parsed = command(strategy=strategy)
    assert CreateKnowledgeVideo.model_validate_json(parsed.model_dump_json()) == parsed


@pytest.mark.parametrize("field", [
    "organization_id", "session_id", "principal_id", "role", "consent", "script",
    "endpoint", "api_key", "provider", "callback_url", "approved", "playback_url",
    "policy_epoch", "teacher_review", "duration", "automatic_fallback"
])
def test_no_authority_provider_or_legacy_shortcut_fields(field):
    with pytest.raises(ValidationError):
        command(**{field: "untrusted"})


@pytest.mark.parametrize("field", ["bundle_version", "audience_context_revision"])
@pytest.mark.parametrize("value", [True, "1", 1.0, -1, None])
def test_command_revisions_not_coerced(field, value):
    with pytest.raises(ValidationError):
        command(**{field: value})


@pytest.mark.parametrize("changes", [
    {"bundle_hash": "A" * 64}, {"bundle_id": "https://provider/file"},
    {"bundle_id": ""}, {"strategy": "wan"}, {"bundle_version": 0},
    {"candidate_library_asset_ref": ref()},
    {"requested_profile_ref": {"ref": "p", "version": 1, "hash": "a" * 64, "secret": "x"}},
])
def test_malformed_or_strategy_conflicting_commands(changes):
    with pytest.raises(ValidationError):
        command(**changes)


def test_library_candidate_and_profile_are_only_exact_refs():
    assert command(strategy="reviewed_library", candidate_library_asset_ref=ref())
    assert command(requested_profile_ref=ref())


def test_queued_and_ready_projection_keep_review_and_playback_separate():
    queued = view()
    ready = view(generation_state="succeeded", review_state="ready_for_review", artifact_ref=ref())
    assert queued.artifact_ref is None
    assert ready.playback_state == "not_started"
    assert "playback_url" not in ready.model_dump()
    assert KnowledgeVideoView.model_validate_json(ready.model_dump_json()) == ready


@pytest.mark.parametrize("changes", [
    {"generation_state": "succeeded"}, {"artifact_ref": ref()},
    {"review_state": "ready_for_review"}, {"review_state": "approved"},
    {"playback_state": "playing"}, {"playback_url": "https://bucket/asset"},
    {"generation_state": "stale"}, {"created_at": NOW.replace(tzinfo=None)},
    {"generation_state": "failed_exhausted"}, {"failed_exhausted_at": NOW},
    {"generation_state": "failed_exhausted", "failed_exhausted_at": NOW - timedelta(days=1)},
])
def test_invalid_or_unowned_view_axes(changes):
    with pytest.raises(ValidationError):
        view(**changes)


def test_exhaustion_timestamp_and_attempt_history():
    attempt = VideoAttemptView(attempt_id="attempt", attempt_number=1, state="failed_exhausted")
    assert view(generation_state="failed_exhausted", failed_exhausted_at=NOW,
                attempt_history=(attempt,)).failed_exhausted_at == NOW
    with pytest.raises(ValidationError):
        view(attempt_history=(attempt, attempt))
    with pytest.raises(ValidationError):
        view(attempt_history=(VideoAttemptView(
            attempt_id="attempt2", attempt_number=2, state="queued"
        ),))


@pytest.mark.parametrize("field", [
    "video_version", "video_run_revision", "video_review_revision", "job_revision"
])
def test_view_revision_no_boolean(field):
    with pytest.raises(ValidationError):
        view(**{field: True})
