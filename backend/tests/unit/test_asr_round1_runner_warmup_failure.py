"""No-GPU unit tests for the Round-1 runner's warmup-failure handling.

Defect fixed: `run_round1_benchmark` used to discard the warmup `adapter.transcribe(...)`
result outright, so a typed `AsrFailureV1` warmup could still produce a numeric `cold_start_ms`
as if a real model warmup had occurred. These tests exercise `run_round1_benchmark`'s own
control flow end to end against a fake `AsrPort` (never a real GPU/model), injected through
`Round1RunnerConfig.adapter_factory` — a narrow seam that does not change the shared
`AsrPort`/`AsrResultV1` contract.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from math import sin, tau
from pathlib import Path
from struct import pack
from wave import open as wave_open

import pytest

from sketch2life.benchmark.asr_round1_runner import (
    Round1RunnerConfig,
    WarmupTranscriptionFailedError,
    run_round1_benchmark,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrProfileId,
    AsrQualityMetadataV1,
    AsrRequestV1,
    AsrResultV1,
    AsrSegmentV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
)
from sketch2life.contracts.schemas.asr_benchmark import (
    AsrFixtureDataProvenance,
    AsrFixtureDurationBand,
    AsrFixtureScenario,
    AsrFixtureSplit,
    AsrRound1FixtureEntryV1,
    AsrRound1FixtureManifestV1,
)
from sketch2life.infrastructure.ai.faster_whisper_runtime_config import FasterWhisperRuntimeConfig


def _write_speech_like_wav(path: Path, seconds: float = 4.0, sample_rate: int = 16000) -> bytes:
    frame_count = int(seconds * sample_rate)
    samples = bytearray()
    for index in range(frame_count):
        value = int(0.3 * 32767 * sin(tau * 220 * index / sample_rate))
        samples.extend(pack("<h", value))
    with wave_open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(bytes(samples))
    return path.read_bytes()


def _write_silent_wav(path: Path, seconds: float = 4.0, sample_rate: int = 16000) -> bytes:
    with wave_open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return path.read_bytes()


def _entry(
    fixtures_root: Path,
    fixture_id: str,
    scenario: AsrFixtureScenario,
    *,
    expected_language: str | None,
    expected_languages: tuple[str, ...] | None = None,
    eligible: bool = False,
    language_accuracy_eligible: bool = False,
    noise_condition_id: str | None = None,
) -> AsrRound1FixtureEntryV1:
    speech = scenario not in {AsrFixtureScenario.SILENCE, AsrFixtureScenario.NOISE}
    audio_dir = fixtures_root / "audio" / scenario.value
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{fixture_id}.wav"
    audio_bytes = (
        _write_speech_like_wav(audio_path) if speech else _write_silent_wav(audio_path)
    )
    transcript_ref = None
    transcript_hash = None
    if speech:
        transcripts_dir = fixtures_root / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        transcript_text = f"reference text {fixture_id}"
        (transcripts_dir / f"{fixture_id}.txt").write_text(transcript_text, encoding="utf-8")
        transcript_ref = f"transcripts/{fixture_id}.txt"
        transcript_hash = sha256(transcript_text.encode()).hexdigest()
    return AsrRound1FixtureEntryV1(
        fixture_id=fixture_id,
        scenario=scenario,
        expected_language=expected_language,
        expected_languages=expected_languages,
        source_audio_ref=f"audio/{scenario.value}/{fixture_id}.wav",
        source_audio_sha256=sha256(audio_bytes).hexdigest(),
        reference_transcript_ref=transcript_ref,
        reference_transcript_sha256=transcript_hash,
        data_provenance=AsrFixtureDataProvenance.SYNTHETIC,
        wer_eligible=eligible,
        cer_eligible=eligible,
        language_accuracy_eligible=language_accuracy_eligible,
        noise_condition_id=noise_condition_id,
        fixture_version="v1",
        expected_speech_present=speech,
        duration_band=AsrFixtureDurationBand.FROM_3S_TO_8S,
        split=AsrFixtureSplit.HELD_OUT,
        notes="warmup-failure test fixture",
    )


def _minimal_ready_manifest(fixtures_root: Path) -> AsrRound1FixtureManifestV1:
    """The smallest manifest satisfying `AsrRound1FixtureManifestV1`'s strict READY rules,
    backed by real on-disk audio/transcript payloads (never fabricated hashes)."""

    entries = (
        _entry(
            fixtures_root,
            "vi-clear-1",
            AsrFixtureScenario.VI_CLEAR,
            expected_language="vi",
            eligible=True,
            language_accuracy_eligible=True,
        ),
        _entry(
            fixtures_root,
            "en-clear-1",
            AsrFixtureScenario.NON_VI_CLEAR,
            expected_language="en",
            eligible=True,
            language_accuracy_eligible=True,
        ),
        _entry(
            fixtures_root,
            "vi-en-code-switch-1",
            AsrFixtureScenario.VI_EN_CODE_SWITCH,
            expected_language="vi",
            expected_languages=("vi", "en"),
            eligible=True,
        ),
        _entry(fixtures_root, "silence-1", AsrFixtureScenario.SILENCE, expected_language=None),
        _entry(
            fixtures_root,
            "noise-1",
            AsrFixtureScenario.NOISE,
            expected_language=None,
            noise_condition_id="cond-v1",
        ),
        _entry(
            fixtures_root,
            "noisy-vi-1",
            AsrFixtureScenario.NOISY_SPEECH,
            expected_language="vi",
            eligible=True,
            noise_condition_id="cond-v1",
        ),
        _entry(
            fixtures_root,
            "noisy-en-1",
            AsrFixtureScenario.NOISY_SPEECH,
            expected_language="en",
            eligible=True,
            noise_condition_id="cond-v1",
        ),
    )
    return AsrRound1FixtureManifestV1(
        manifest_version="asr-round1-v1",
        normalizer_version="vi-asr-normalizer-v1",
        status="READY",
        fixtures=entries,
        notes="warmup-failure test manifest; real local payloads, never committed",
    )


_PLACEHOLDER_AUDIO_REF = AsrAudioReferenceV1(
    artifact_ref="fixture:warmup-placeholder", sha256="a" * 64
)


@dataclass
class _FakeAdapter:
    """A minimal `AsrPort` test double: distinguishes the warmup call by correlation ID."""

    warmup_result: AsrResultV1
    fixture_calls: list[AsrRequestV1] = field(default_factory=list)

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1:
        if request.correlation_id.startswith("asr-round1-warmup-"):
            return self.warmup_result
        self.fixture_calls.append(request)
        return _fixture_success(request)


def _fixture_success(request: AsrRequestV1) -> AsrSuccessV1:
    return AsrSuccessV1(
        correlation_id=request.correlation_id,
        executed_at=datetime.now(UTC),
        source_audio_ref=request.source_audio_ref,
        profile_id=request.requested_profile_id,
        attempt_number=1,
        repair_attempted=False,
        transcript_raw="reference text",
        speech_diagnostic=AsrSpeechDiagnostic.DETECTED,
        detected_language="vi",
        language_probability=0.99,
        segments=(
            AsrSegmentV1(index=0, start_seconds=0.0, end_seconds=1.0, text="reference text"),
        ),
        input_duration_seconds=4.0,
        vad_enabled=False,
        duration_after_vad_seconds=None,
        model_identifier="fake-model",
        model_revision="fake-revision",
        adapter_version="fake-adapter-v1",
        runtime_version="fake-runtime-v1",
        config_hash="a" * 64,
        quality_metadata=AsrQualityMetadataV1(
            media_validation_artifact_ref="fixture:fake:v1",
            media_validation_artifact_sha256=sha256(b"fake").hexdigest(),
        ),
    )


def _warmup_success_result() -> AsrSuccessV1:
    return AsrSuccessV1(
        correlation_id="asr-round1-warmup-placeholder",
        executed_at=datetime.now(UTC),
        source_audio_ref=_PLACEHOLDER_AUDIO_REF,
        profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
        attempt_number=1,
        repair_attempted=False,
        transcript_raw="",
        speech_diagnostic=AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED,
        detected_language="vi",
        language_probability=0.5,
        segments=(),
        input_duration_seconds=4.0,
        vad_enabled=False,
        duration_after_vad_seconds=None,
        model_identifier="fake-model",
        model_revision="fake-revision",
        adapter_version="fake-adapter-v1",
        runtime_version="fake-runtime-v1",
        config_hash="a" * 64,
        quality_metadata=AsrQualityMetadataV1(
            media_validation_artifact_ref="fixture:fake:v1",
            media_validation_artifact_sha256=sha256(b"fake").hexdigest(),
        ),
    )


def _warmup_failure_result() -> AsrFailureV1:
    return AsrFailureV1(
        correlation_id="asr-round1-warmup-placeholder",
        executed_at=datetime.now(UTC),
        source_audio_ref=_PLACEHOLDER_AUDIO_REF,
        profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
        attempt_number=1,
        repair_attempted=False,
        error_code=AsrErrorCode.ASR_MODEL_UNAVAILABLE,
        retryable=False,
        error_detail=AsrErrorDetail.MODEL_LOAD_FAILED,
    )


def _config(fixtures_root: Path, adapter: _FakeAdapter) -> Round1RunnerConfig:
    return Round1RunnerConfig(
        fixtures_root=fixtures_root,
        runtime_config=FasterWhisperRuntimeConfig(),
        sample_vram=False,
        adapter_factory=lambda _runtime_config: adapter,
    )


def test_successful_warmup_proceeds_to_normal_fixture_execution(tmp_path: Path) -> None:
    manifest = _minimal_ready_manifest(tmp_path)
    adapter = _FakeAdapter(warmup_result=_warmup_success_result())

    report = run_round1_benchmark(manifest, _config(tmp_path, adapter))

    assert len(report.runs) == 14  # 7 fixtures x 2 fixed Round-1 profiles
    for metrics in report.metrics_by_profile.values():
        assert metrics.cold_start_ms.status.value == "MEASURED"
        assert metrics.cold_start_ms.value is not None and metrics.cold_start_ms.value >= 0
        assert metrics.total_runs.value == 7
    # The warmup call(s) never appear among the fixtures actually executed.
    assert len(adapter.fixture_calls) == 14


def test_typed_warmup_failure_stops_before_fixture_execution(tmp_path: Path) -> None:
    manifest = _minimal_ready_manifest(tmp_path)
    adapter = _FakeAdapter(warmup_result=_warmup_failure_result())

    with pytest.raises(WarmupTranscriptionFailedError) as excinfo:
        run_round1_benchmark(manifest, _config(tmp_path, adapter))

    assert excinfo.value.error_code is AsrErrorCode.ASR_MODEL_UNAVAILABLE
    assert excinfo.value.error_detail is AsrErrorDetail.MODEL_LOAD_FAILED
    assert excinfo.value.profile_id is AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1
    # No normal fixture run was ever attempted for the failing profile.
    assert adapter.fixture_calls == []
    # The error message carries only closed enum identifiers, never raw provider text.
    message = str(excinfo.value)
    assert "ASR_MODEL_UNAVAILABLE" in message
    assert "MODEL_LOAD_FAILED" in message


def test_failed_warmup_cannot_produce_a_report_with_measured_cold_start(tmp_path: Path) -> None:
    manifest = _minimal_ready_manifest(tmp_path)
    adapter = _FakeAdapter(warmup_result=_warmup_failure_result())

    report = None
    with suppress(WarmupTranscriptionFailedError):
        report = run_round1_benchmark(manifest, _config(tmp_path, adapter))

    # A report was never constructed at all — not "constructed with a NOT_MEASURED cold
    # start," but genuinely absent, since a failed-warmup profile's state is not known-good
    # for any of the timed runs that would otherwise follow it.
    assert report is None
