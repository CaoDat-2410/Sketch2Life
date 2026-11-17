"""Byte/hash/profile rules + explicitly FAKE decoder/providers/authority.

Fixture payload is NOT a real decodable video. No actual runtime/generation proof.
"""

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sketch2life.application.knowledge_video_media import CheckedMediaValidator, VideoMediaPipeline
from sketch2life.application.ports.knowledge_video_media import (
    LibraryMedia,
    RenderAttempt,
    VideoSourceMaterial,
)
from sketch2life.domain.knowledge_video.media import DecodedMedia, MediaBlob, MediaProfile
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
)

NOW = datetime(2026, 10, 18, tzinfo=UTC)
PAYLOAD = b"synthetic-fixture-NOT-a-real-video"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


def ref(name):
    return ExactRef(name, 1, "a" * 64)


class AssumedRenderAuthority:
    """Only records checks/fault injection; not actual foundation capabilities."""

    def __init__(self):
        self.phases = []
        self.fail = None

    def check(self, attempt, phase):
        self.phases.append(phase)
        if phase == self.fail or attempt.capability != "fixture-private-capability":
            raise VideoError("VIDEO_STALE_CONTEXT")


def harness(strategy=Strategy.GENERATE):
    pin = VideoPin(
        "school",
        "session",
        ref("bundle"),
        0,
        0,
        0,
        (ref("source"),),
        strategy,
        ref("profile"),
        ref("encoding"),
        ref("rights"),
        ref("retry"),
        ref("policy"),
        1,
        ref("model") if strategy is Strategy.GENERATE else None,
        ref("library") if strategy is not Strategy.GENERATE else None,
    )
    running = VideoRun("video", 1, 1, 1, "job", pin, NOW).start(1, "attempt")
    attempt = RenderAttempt(running, 2, "fixture-private-capability")
    profile = MediaProfile(
        pin.content_profile,
        pin.encoding,
        tuple(Strategy),
        ("fixture.container",),
        ("fixture.codec",),
        ((16, 16),),
        100,
        1000,
        128,
        2,
        ("fixture.audio",),
        1,
    )
    blob = MediaBlob(PAYLOAD, DIGEST)
    report = DecodedMedia(DIGEST, "fixture.container", "fixture.codec", 16, 16, 500, 12, (), True)
    h = SimpleNamespace(
        attempt=attempt,
        authority=AssumedRenderAuthority(),
        profile=profile,
        blob=blob,
        profiles=Mock(resolve=Mock(return_value=profile)),
        sources=Mock(
            load=Mock(
                return_value=VideoSourceMaterial(pin.bundle, pin.digest(), "fixture-private-script")
            )
        ),
        library=Mock(
            resolve=Mock(
                return_value=LibraryMedia(
                    pin.library_asset or ref("library"),
                    pin.digest(),
                    pin.rights,
                    pin.content_profile,
                    pin.encoding,
                    blob,
                )
            )
        ),
        decoder=Mock(decode=Mock(return_value=report)),
        generator=Mock(generate=Mock(return_value=blob)),
        composer=Mock(compose=Mock(return_value=blob)),
    )
    h.validator = CheckedMediaValidator(h.decoder)
    h.pipeline = VideoMediaPipeline(
        h.authority,
        h.profiles,
        h.sources,
        h.validator,
        library=h.library,
        generator=h.generator,
        composer=h.composer,
    )
    return h


@pytest.mark.parametrize("strategy", list(Strategy))
def test_strategies_prepare_only_never_finalize_or_approve(strategy):
    h = harness(strategy)
    result = h.pipeline.prepare(h.attempt)
    assert result.blob.payload == PAYLOAD and result.strategy is strategy
    assert result.pin_digest == h.attempt.run.pin.digest()
    assert h.attempt.run.generation_state == "running" and h.attempt.run.artifact is None
    assert not hasattr(result, "playback_url") and not hasattr(result, "artifact")
    assert h.authority.phases[-1] == "validation_returned"
    assert h.generator.generate.call_count == (strategy is Strategy.GENERATE)
    assert h.composer.compose.call_count == (strategy is Strategy.COMPOSE_LIBRARY)
    assert h.library.resolve.call_count == (strategy is not Strategy.GENERATE)


def test_library_does_not_need_generator_model_or_raw_script():
    h = harness(Strategy.REVIEWED_LIBRARY)
    pipeline = VideoMediaPipeline(
        h.authority, h.profiles, h.sources, h.validator, library=h.library
    )
    assert pipeline.prepare(h.attempt).blob == h.blob
    assert h.attempt.run.pin.model_profile is None
    h.sources.load.assert_not_called()
    h.generator.generate.assert_not_called()


def test_restart_key_stable_and_attempt_pinned():
    h = harness()
    first = h.pipeline.prepare(h.attempt)
    assert h.pipeline.prepare(h.attempt).operation_key == first.operation_key
    other = replace(h.attempt, run=replace(h.attempt.run, attempt_id="another"))
    assert h.pipeline.prepare(other).operation_key != first.operation_key
    assert h.generator.generate.call_args.args[2] != first.operation_key


@pytest.mark.parametrize("strategy", list(Strategy))
def test_unconfigured_strategy_never_silently_falls_back(strategy):
    h = harness(strategy)
    pipeline = VideoMediaPipeline(h.authority, h.profiles, h.sources, h.validator)
    with pytest.raises(VideoError, match="VIDEO_STRATEGY_UNSUPPORTED"):
        pipeline.prepare(h.attempt)
    h.generator.generate.assert_not_called()
    h.composer.compose.assert_not_called()


def test_generator_timeout_does_not_lookup_library_or_finalize():
    h = harness()
    h.generator.generate.side_effect = TimeoutError("synthetic timeout")
    with pytest.raises(TimeoutError):
        h.pipeline.prepare(h.attempt)
    h.library.resolve.assert_not_called()
    h.composer.compose.assert_not_called()
    h.decoder.decode.assert_not_called()
    assert h.attempt.run.artifact is None


@pytest.mark.parametrize(
    "phase",
    [
        "prepare",
        "source",
        "source_returned",
        "generation",
        "generation_returned",
        "validation",
        "validation_returned",
    ],
)
def test_revocation_at_each_boundary_never_returns_media(phase):
    h = harness()
    h.authority.fail = phase
    with pytest.raises(VideoError, match="VIDEO_STALE_CONTEXT"):
        h.pipeline.prepare(h.attempt)
    assert h.attempt.run.artifact is None
    if phase in {"prepare", "source", "source_returned", "generation"}:
        h.generator.generate.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("content_profile", ref("other")),
        ("encoding", ref("other")),
        ("strategies", (Strategy.REVIEWED_LIBRARY,)),
    ],
)
def test_wrong_registry_profile_denied_before_provider(field, value):
    h = harness()
    h.profiles.resolve.return_value = replace(h.profile, **{field: value})
    with pytest.raises(VideoError, match="VIDEO_PROFILE_UNAVAILABLE"):
        h.pipeline.prepare(h.attempt)
    h.generator.generate.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("asset", ref("other")),
        ("pin_digest", "b" * 64),
        ("rights", ref("other")),
        ("content_profile", ref("other")),
        ("encoding", ref("other")),
    ],
)
def test_library_binding_cannot_swap_scope_rights_or_asset(field, value):
    h = harness(Strategy.COMPOSE_LIBRARY)
    h.library.resolve.return_value = replace(h.library.resolve.return_value, **{field: value})
    with pytest.raises(VideoError, match="VIDEO_LIBRARY_MISMATCH"):
        h.pipeline.prepare(h.attempt)
    h.composer.compose.assert_not_called()


@pytest.mark.parametrize("phase", ["library", "library_returned"])
def test_recalled_library_denied(phase):
    h = harness(Strategy.REVIEWED_LIBRARY)
    h.authority.fail = phase
    with pytest.raises(VideoError, match="VIDEO_STALE_CONTEXT"):
        h.pipeline.prepare(h.attempt)


@pytest.mark.parametrize("field,value", [("bundle", ref("other")), ("pin_digest", "b" * 64)])
def test_wrong_bundle_script_binding_denied(field, value):
    h = harness()
    h.sources.load.return_value = replace(h.sources.load.return_value, **{field: value})
    with pytest.raises(VideoError, match="VIDEO_SOURCE_MISMATCH"):
        h.pipeline.prepare(h.attempt)
    h.generator.generate.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_hash", "b" * 64),
        ("container", "wrong"),
        ("video_codec", "wrong"),
        ("width", 32),
        ("height", 32),
        ("duration_ms", 99),
        ("duration_ms", 1001),
        ("decoded_frames", 1),
        ("audio_codecs", ("wrong",)),
        ("audio_codecs", ("fixture.audio", "fixture.audio")),
    ],
)
def test_decode_profile_mismatch_cannot_become_prepared_video(field, value):
    h = harness()
    h.decoder.decode.return_value = replace(h.decoder.decode.return_value, **{field: value})
    with pytest.raises(VideoError, match="VIDEO_MEDIA_PROFILE_MISMATCH"):
        h.pipeline.prepare(h.attempt)


@pytest.mark.parametrize(
    "field,value",
    [
        ("width", True),
        ("duration_ms", 0),
        ("duration_ms", 500.0),
        ("decoded_frames", False),
        ("complete", False),
        ("complete", 1),
        ("audio_codecs", []),
    ],
)
def test_forged_native_decoder_report_revalidated(field, value):
    h = harness()
    object.__setattr__(h.decoder.decode.return_value, field, value)
    with pytest.raises(VideoError):
        h.pipeline.prepare(h.attempt)


def test_wrong_payload_hash_and_size_rejected_before_decoder():
    h = harness()
    for blob, code in (
        (MediaBlob(PAYLOAD, "b" * 64), "VIDEO_MEDIA_HASH_MISMATCH"),
        (MediaBlob(b"x" * 129, "b" * 64), "VIDEO_MEDIA_TOO_LARGE"),
    ):
        with pytest.raises(VideoError, match=code):
            h.validator.validate(blob, h.profile)
    h.decoder.decode.assert_not_called()


def test_corrupt_compose_input_never_sent_to_provider():
    h = harness(Strategy.COMPOSE_LIBRARY)
    h.library.resolve.return_value = replace(
        h.library.resolve.return_value, blob=MediaBlob(PAYLOAD, "b" * 64)
    )
    with pytest.raises(VideoError, match="VIDEO_MEDIA_HASH_MISMATCH"):
        h.pipeline.prepare(h.attempt)
    h.composer.compose.assert_not_called()


def test_custom_validator_cannot_skip_byte_integrity():
    h = harness()
    h.generator.generate.return_value = MediaBlob(PAYLOAD, "b" * 64)
    custom = Mock(validate=Mock(return_value=h.decoder.decode.return_value))
    pipeline = VideoMediaPipeline(h.authority, h.profiles, h.sources, custom, generator=h.generator)
    with pytest.raises(VideoError, match="VIDEO_MEDIA_HASH_MISMATCH"):
        pipeline.prepare(h.attempt)
    custom.validate.assert_not_called()


@pytest.mark.parametrize("duration", [100, 1000])
def test_inclusive_explicit_profile_boundaries(duration):
    h = harness()
    h.decoder.decode.return_value = replace(h.decoder.decode.return_value, duration_ms=duration)
    assert h.pipeline.prepare(h.attempt).decoded.duration_ms == duration


@pytest.mark.parametrize(
    "field,value",
    [
        ("strategies", ()),
        ("strategies", ("generate",)),
        ("containers", ()),
        ("video_codecs", ["mutable"]),
        ("dimensions", ((True, 16),)),
        ("dimensions", ((16, 16), (16, 16))),
        ("dimensions", ([16, 16],)),
        ("min_duration_ms", 0),
        ("max_duration_ms", 99),
        ("max_bytes", True),
        ("min_decoded_frames", 0),
        ("max_audio_streams", -1),
        ("audio_codecs", ()),
    ],
)
def test_profile_requires_explicit_strict_nonconflicting_terms(field, value):
    with pytest.raises(VideoError):
        replace(harness().profile, **{field: value})


def test_private_bytes_script_and_capability_not_in_repr():
    h = harness()
    assert "fixture-private-capability" not in repr(h.attempt)
    assert "fixture-private-script" not in repr(h.sources.load.return_value)
    assert "synthetic-fixture" not in repr(h.blob)
    assert "synthetic-fixture" not in repr(h.pipeline.prepare(h.attempt))


@pytest.mark.parametrize("report", [None, "provider-success", {"complete": True}])
def test_probe_like_or_untyped_decoder_success_rejected(report):
    h = harness()
    h.decoder.decode.return_value = report
    with pytest.raises(VideoError, match="VIDEO_MEDIA_INVALID"):
        h.pipeline.prepare(h.attempt)


def test_decoder_fault_does_not_finalize_or_auto_fallback():
    h = harness()
    h.decoder.decode.side_effect = TimeoutError("synthetic decoder timeout")
    with pytest.raises(TimeoutError):
        h.pipeline.prepare(h.attempt)
    assert h.attempt.run.artifact is None
    h.library.resolve.assert_not_called()


def test_same_attempt_progress_revision_does_not_change_external_dedup_key():
    h = harness()
    original = h.pipeline.prepare(h.attempt)
    advanced = replace(h.attempt, job_revision=3, run=replace(h.attempt.run, run_revision=3))
    assert h.pipeline.prepare(advanced).operation_key == original.operation_key


@pytest.mark.parametrize(
    "field,value", [("policy_epoch", 2), ("audience_revision", 1), ("context_revision", 1)]
)
def test_original_pin_change_changes_operation_key(field, value):
    h = harness()
    original = h.pipeline.prepare(h.attempt)
    changed_pin = replace(h.attempt.run.pin, **{field: value})
    changed = replace(h.attempt, run=replace(h.attempt.run, pin=changed_pin))
    h.sources.load.return_value = replace(
        h.sources.load.return_value, pin_digest=changed_pin.digest()
    )
    assert h.pipeline.prepare(changed).operation_key != original.operation_key


def test_unknown_profile_does_not_call_decoder_or_provider():
    h = harness()
    h.profiles.resolve.return_value = None
    with pytest.raises(VideoError, match="VIDEO_PROFILE_UNAVAILABLE"):
        h.pipeline.prepare(h.attempt)
    h.generator.generate.assert_not_called()
    h.decoder.decode.assert_not_called()
