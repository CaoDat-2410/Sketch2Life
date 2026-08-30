"""Unit/contract tests for `FasterWhisperAsrAdapter` — no real model, GPU, or network.

The model factory is injected so these tests exercise the adapter's own mapping/retry/repair
logic against a fake `WhisperModelLike`, proving the contract (typed failures, provenance,
retry/attempt_number semantics, no raw-media/credential logging surface) independent of
whether a real GPU or the real `faster-whisper` package is available in this environment.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrProfileId,
    AsrRequestV1,
    AsrResultV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
    AudioDerivationProvenanceV1,
    MediaValidationProvenanceV1,
    asr_profile_catalog,
)
from sketch2life.infrastructure.ai.faster_whisper_asr import FasterWhisperAsrAdapter
from sketch2life.infrastructure.ai.faster_whisper_runtime_config import (
    FasterWhisperRuntimeConfig,
)


@dataclass
class _FakeSegment:
    start: float
    end: float
    text: str
    avg_logprob: float | None = -0.1
    compression_ratio: float | None = 1.0
    no_speech_prob: float | None = 0.02


@dataclass
class _FakeInfo:
    language: str = "vi"
    language_probability: float = 0.97
    duration: float = 2.0


@dataclass
class _FakeModel:
    segments: list[_FakeSegment] = field(default_factory=list)
    info: _FakeInfo = field(default_factory=_FakeInfo)
    raise_on_transcribe: BaseException | None = None
    calls: list[dict[str, object]] = field(default_factory=list)

    def transcribe(self, audio, **kwargs):  # noqa: ANN001, ANN003 - test double matches provider shape
        self.calls.append({"audio": audio, **kwargs})
        if self.raise_on_transcribe is not None:
            raise self.raise_on_transcribe
        return iter(self.segments), self.info


def _runtime_config(tmp_path: Path) -> FasterWhisperRuntimeConfig:
    return FasterWhisperRuntimeConfig(model_cache_dir=tmp_path / "cache")


def _audio_fixture(
    tmp_path: Path, content: bytes = b"synthetic-audio-bytes"
) -> AsrAudioReferenceV1:
    path = tmp_path / "narration.wav"
    path.write_bytes(content)
    return AsrAudioReferenceV1(artifact_ref=str(path), sha256=sha256(content).hexdigest())


def _validation() -> MediaValidationProvenanceV1:
    return MediaValidationProvenanceV1(
        validation_artifact_ref="fixture:validation:pass:v1",
        validation_artifact_sha256=sha256(b"validation:PASS").hexdigest(),
        decision="PASS",
        validator_policy_version="media-quality-policy-v1",
    )


def _request(
    tmp_path: Path,
    *,
    profile_id: AsrProfileId = AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
    media_validation: MediaValidationProvenanceV1 | None,
) -> AsrRequestV1:
    return AsrRequestV1(
        correlation_id="phase-b-test-correlation",
        source_audio_ref=_audio_fixture(tmp_path),
        media_validation=media_validation,
        requested_profile_id=profile_id,
    )


def test_valid_audio_maps_to_schema_valid_success_with_source_and_provenance(
    tmp_path: Path,
) -> None:
    model = _FakeModel(segments=[_FakeSegment(0.0, 1.2, "Con buom bay")])
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.source_audio_ref == request.source_audio_ref
    assert result.transcript_raw == "Con buom bay"
    assert result.speech_diagnostic is AsrSpeechDiagnostic.DETECTED
    assert result.detected_language == "vi"
    assert result.language_probability == pytest.approx(0.97)
    assert result.attempt_number == 1
    assert result.repair_attempted is False
    assert result.model_identifier == "deepdml/faster-whisper-large-v3-turbo-ct2"
    assert result.quality_metadata.media_validation_artifact_ref == "fixture:validation:pass:v1"
    parsed = TypeAdapter(AsrResultV1).validate_python(result.model_dump(mode="json"))
    assert isinstance(parsed, AsrSuccessV1)


def test_silence_maps_to_success_not_recapture(tmp_path: Path) -> None:
    model = _FakeModel(segments=[])
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.transcript_raw == ""
    assert result.segments == ()
    assert result.speech_diagnostic is AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED


def test_auto_detect_never_forces_a_language(tmp_path: Path) -> None:
    model = _FakeModel(segments=[_FakeSegment(0.0, 1.0, "hello")])
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.language_hint_applied is False
    assert result.language_hint_echo is None
    assert model.calls[0]["language"] is None


@pytest.mark.parametrize(
    ("exc", "expected_detail"),
    (
        (RuntimeError("CUDA out of memory"), AsrErrorDetail.DEVICE_UNAVAILABLE),
        (RuntimeError("cuDNN initialization failed"), AsrErrorDetail.DEVICE_UNAVAILABLE),
        (OSError("model file not found"), AsrErrorDetail.MODEL_LOAD_FAILED),
    ),
)
def test_model_load_failure_maps_to_asr_model_unavailable(
    tmp_path: Path, exc: BaseException, expected_detail: AsrErrorDetail
) -> None:
    def failing_factory(profile, config):  # noqa: ANN001
        raise exc

    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=failing_factory)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.ASR_MODEL_UNAVAILABLE
    assert result.error_detail is expected_detail
    assert result.attempt_number == 1
    assert result.retryable is False
    assert not hasattr(result, "transcript_raw")


def test_non_transient_provider_failure_does_not_retry(tmp_path: Path) -> None:
    model = _FakeModel(raise_on_transcribe=RuntimeError("invalid request"))
    adapter = FasterWhisperAsrAdapter(
        _runtime_config(tmp_path),
        model_factory=lambda p, c: model,
        classify_transient=lambda exc: False,
    )
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.ASR_PROVIDER_FAILURE
    assert result.error_detail is AsrErrorDetail.PERMANENT_RUNTIME_FAILURE
    assert result.attempt_number == 1
    assert result.retryable is False
    assert len(model.calls) == 1


def test_transient_provider_failure_retries_once_then_succeeds(tmp_path: Path) -> None:
    class _FlakyModel(_FakeModel):
        def transcribe(self, audio, **kwargs):  # noqa: ANN001, ANN003
            self.calls.append({"audio": audio, **kwargs})
            if len(self.calls) == 1:
                raise ConnectionError("connection reset")
            return iter(self.segments), self.info

    model = _FlakyModel(segments=[_FakeSegment(0.0, 1.0, "recovered")])
    adapter = FasterWhisperAsrAdapter(
        _runtime_config(tmp_path),
        model_factory=lambda p, c: model,
        classify_transient=lambda exc: isinstance(exc, ConnectionError),
    )
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.attempt_number == 2
    assert len(model.calls) == 2


def test_transient_provider_failure_retries_once_then_still_fails(tmp_path: Path) -> None:
    model = _FakeModel(raise_on_transcribe=ConnectionError("connection reset"))
    adapter = FasterWhisperAsrAdapter(
        _runtime_config(tmp_path),
        model_factory=lambda p, c: model,
        classify_transient=lambda exc: isinstance(exc, ConnectionError),
    )
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.ASR_PROVIDER_FAILURE
    assert result.error_detail is AsrErrorDetail.TRANSIENT_RUNTIME_FAILURE
    assert result.attempt_number == 2
    assert result.retryable is True
    assert len(model.calls) == 2


def test_default_transient_classifier_never_retries(tmp_path: Path) -> None:
    model = _FakeModel(raise_on_transcribe=ConnectionError("connection reset"))
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.retryable is False
    assert result.attempt_number == 1
    assert len(model.calls) == 1


def test_repair_clamps_a_segment_ending_after_the_reported_duration(tmp_path: Path) -> None:
    # info.duration (1.0s) is inconsistent with the segment's own end (1.8s) — a provider
    # output the adapter can still map after one bounded local repair, without re-invoking
    # the model.
    model = _FakeModel(
        segments=[_FakeSegment(0.0, 1.8, "runs-past-reported-duration")],
        info=_FakeInfo(duration=1.0),
    )
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.repair_attempted is True
    assert len(model.calls) == 1  # repair never re-invokes the model
    assert result.segments[0].end_seconds <= result.input_duration_seconds


def test_repair_still_failing_maps_to_asr_schema_invalid(tmp_path: Path) -> None:
    # The timestamp repair only touches segment timing, so a provider response with an
    # empty/invalid language code is not fixable by it: both build attempts fail, and the
    # adapter reports the typed failure rather than crashing or silently succeeding.
    model = _FakeModel(
        segments=[_FakeSegment(0.0, 1.0, "unmappable-language")],
        info=_FakeInfo(language="", language_probability=0.5),
    )
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.ASR_SCHEMA_INVALID
    assert result.repair_attempted is True
    assert len(model.calls) == 1


@pytest.mark.parametrize("decision", (None, "RECAPTURE"))
def test_missing_or_failed_p2_t1_validation_is_input_not_validated(
    tmp_path: Path, decision: str | None
) -> None:
    model = _FakeModel()
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    media_validation = (
        None
        if decision is None
        else MediaValidationProvenanceV1(
            validation_artifact_ref="fixture:validation:v1",
            validation_artifact_sha256=sha256(f"validation:{decision}".encode()).hexdigest(),
            decision=decision,  # type: ignore[arg-type]
            validator_policy_version="media-quality-policy-v1",
        )
    )
    request = _request(tmp_path, media_validation=media_validation)

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.INPUT_NOT_VALIDATED
    assert result.attempt_number == 0
    assert not model.calls


def test_source_hash_mismatch_is_rejected_before_any_model_call(tmp_path: Path) -> None:
    model = _FakeModel()
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    audio_ref = _audio_fixture(tmp_path)
    tampered = AsrAudioReferenceV1(artifact_ref=audio_ref.artifact_ref, sha256="0" * 64)
    request = AsrRequestV1(
        correlation_id="phase-b-tamper-check",
        source_audio_ref=tampered,
        media_validation=_validation(),
        requested_profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
    )

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.INPUT_NOT_VALIDATED
    assert result.error_detail is AsrErrorDetail.SOURCE_AUDIO_HASH_MISMATCH
    assert result.attempt_number == 0
    assert not model.calls


def test_missing_source_audio_is_a_typed_failure_before_any_model_call(tmp_path: Path) -> None:
    model = _FakeModel()
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    missing = AsrAudioReferenceV1(
        artifact_ref=str(tmp_path / "missing.wav"), sha256="0" * 64
    )
    request = AsrRequestV1(
        correlation_id="phase-b-missing-source",
        source_audio_ref=missing,
        media_validation=_validation(),
        requested_profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
    )

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.INPUT_NOT_VALIDATED
    assert result.error_detail is AsrErrorDetail.SOURCE_AUDIO_UNREADABLE
    assert result.attempt_number == 0
    assert not model.calls


def test_verified_processing_audio_is_used_without_replacing_source_provenance(
    tmp_path: Path,
) -> None:
    model = _FakeModel(segments=[_FakeSegment(0.0, 1.0, "working-copy")])
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    source_audio = _audio_fixture(tmp_path, b"original-audio")
    processing_path = tmp_path / "normalized.wav"
    processing_bytes = b"derived-working-copy"
    processing_path.write_bytes(processing_bytes)
    processing_audio = AsrAudioReferenceV1(
        artifact_ref=str(processing_path), sha256=sha256(processing_bytes).hexdigest()
    )
    request = AsrRequestV1(
        correlation_id="phase-b-working-copy",
        source_audio_ref=source_audio,
        processing_audio_ref=processing_audio,
        derivation_provenance=AudioDerivationProvenanceV1(
            transform_name="normalize",
            transform_config_version="audio-normalize-v1",
            source_audio_sha256=source_audio.sha256,
            processing_audio_sha256=processing_audio.sha256,
        ),
        media_validation=_validation(),
        requested_profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
    )

    result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.source_audio_ref == source_audio
    assert model.calls[0]["audio"] == str(processing_path)


def test_cublas_runtime_failure_maps_to_model_unavailable(tmp_path: Path) -> None:
    model = _FakeModel(raise_on_transcribe=OSError("cublas64_12.dll is not found"))
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    result = adapter.transcribe(request)

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.ASR_MODEL_UNAVAILABLE
    assert result.error_detail is AsrErrorDetail.DEVICE_UNAVAILABLE
    assert result.attempt_number == 1
    assert result.retryable is False


def test_timeout_returns_without_waiting_for_the_blocked_model_call(tmp_path: Path) -> None:
    class _SlowModel(_FakeModel):
        def transcribe(self, audio, **kwargs):  # noqa: ANN001, ANN003
            self.calls.append({"audio": audio, **kwargs})
            time.sleep(0.2)
            return iter(self.segments), self.info

    model = _SlowModel()
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    profile = asr_profile_catalog().resolve(
        AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1
    ).model_copy(update={"timeout_seconds": 0.05})
    started = time.monotonic()

    with pytest.raises(TimeoutError):
        adapter._run_with_timeout(model, profile, str(tmp_path / "narration.wav"))  # noqa: SLF001
    elapsed = time.monotonic() - started

    assert elapsed < 0.15


def test_no_raw_audio_transcript_or_credentials_are_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    secret_transcript = "SECRET-CHILD-NARRATION-CONTENT"
    model = _FakeModel(segments=[_FakeSegment(0.0, 1.0, secret_transcript)])
    adapter = FasterWhisperAsrAdapter(_runtime_config(tmp_path), model_factory=lambda p, c: model)
    request = _request(tmp_path, media_validation=_validation())

    with caplog.at_level(logging.DEBUG):
        result = adapter.transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert secret_transcript not in log_text
    assert str(request.source_audio_ref.artifact_ref) not in log_text
