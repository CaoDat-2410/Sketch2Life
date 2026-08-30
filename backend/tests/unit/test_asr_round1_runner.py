"""Unit tests for the deterministic, no-GPU pieces of the P2-T2 Round-1 runner.

The GPU/model execution path (`run_round1_benchmark`) is exercised separately as a real,
evidence-producing run against the local GPU — it is intentionally not part of this suite so
the standard test run stays GPU/model independent, matching every other test in this repo.
Real P2-T1 gating (`DeterministicMediaValidator`) is exercised directly here without any GPU
or model dependency, matching how `test_media_validation.py` already tests it.
"""

from __future__ import annotations

from hashlib import sha256
from math import sin, tau
from pathlib import Path
from struct import pack
from wave import open as wave_open

import pytest
from pydantic import ValidationError

from sketch2life.benchmark.asr_readiness import (
    AsrRound1RunOutcome,
    AsrRound1RunResultV1,
    AsrSpeechPresenceOutcome,
    speech_presence_outcome_for,
)
from sketch2life.benchmark.asr_round1_runner import (
    FixtureIntegrityError,
    NoWarmupFixtureAvailableError,
    _language_matches,
    _percentile,
    _select_warmup_fixture,
    _verify_fixture_payloads,
    _write_p2t1_companion_image,
)
from sketch2life.contracts.schemas.asr import (
    AsrErrorCode,
    AsrErrorDetail,
    AsrProfileId,
    AsrSpeechDiagnostic,
)
from sketch2life.contracts.schemas.asr_benchmark import (
    AsrFixtureDataProvenance,
    AsrFixtureDurationBand,
    AsrFixtureScenario,
    AsrFixtureSplit,
    AsrRound1FixtureEntryV1,
)
from sketch2life.domain.understanding.media_quality import MediaQualityPolicy, assess_image
from sketch2life.infrastructure.media_validation.file_inspector import inspect_image


def _write_speech_like_wav(path: Path, seconds: float, sample_rate: int = 16000) -> bytes:
    """A sine tone: passes P2-T1's amplitude/activity/zero-crossing audio checks."""

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


def _write_silent_wav(path: Path, seconds: float, sample_rate: int = 16000) -> bytes:
    with wave_open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return path.read_bytes()


def _fixture(
    fixture_id: str,
    audio_bytes: bytes,
    *,
    duration_band: AsrFixtureDurationBand = AsrFixtureDurationBand.FROM_3S_TO_8S,
) -> AsrRound1FixtureEntryV1:
    return AsrRound1FixtureEntryV1(
        fixture_id=fixture_id,
        scenario=AsrFixtureScenario.VI_CLEAR,
        expected_language="vi",
        expected_languages=None,
        source_audio_ref=f"audio/vi_clear/{fixture_id}.wav",
        source_audio_sha256=sha256(audio_bytes).hexdigest(),
        reference_transcript_ref=f"transcripts/{fixture_id}.txt",
        reference_transcript_sha256=sha256(b"reference text").hexdigest(),
        data_provenance=AsrFixtureDataProvenance.SYNTHETIC,
        wer_eligible=True,
        cer_eligible=True,
        language_accuracy_eligible=True,
        fixture_version="v1",
        expected_speech_present=True,
        duration_band=duration_band,
        split=AsrFixtureSplit.HELD_OUT,
        notes="unit test fixture",
    )


def test_verify_fixture_payloads_accepts_matching_hashes_and_duration(tmp_path: Path) -> None:
    (tmp_path / "audio" / "vi_clear").mkdir(parents=True)
    audio_path = tmp_path / "audio" / "vi_clear" / "ok.wav"
    audio_bytes = _write_speech_like_wav(audio_path, seconds=4.0)
    fixture = _fixture("ok", audio_bytes)
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "ok.txt").write_text("reference text", encoding="utf-8")

    resolved = _verify_fixture_payloads(tmp_path, fixture)

    assert resolved == audio_path


def test_verify_fixture_payloads_rejects_a_tampered_audio_file(tmp_path: Path) -> None:
    fixture = _fixture("tampered", b"original-bytes")
    (tmp_path / "audio" / "vi_clear").mkdir(parents=True)
    (tmp_path / "audio" / "vi_clear" / "tampered.wav").write_bytes(b"different-bytes")
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "tampered.txt").write_text("reference text", encoding="utf-8")

    with pytest.raises(FixtureIntegrityError, match="audio hash mismatch"):
        _verify_fixture_payloads(tmp_path, fixture)


def test_verify_fixture_payloads_rejects_a_tampered_transcript_file(tmp_path: Path) -> None:
    (tmp_path / "audio" / "vi_clear").mkdir(parents=True)
    audio_path = tmp_path / "audio" / "vi_clear" / "bad-transcript.wav"
    audio_bytes = _write_speech_like_wav(audio_path, seconds=4.0)
    fixture = _fixture("bad-transcript", audio_bytes)
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "bad-transcript.txt").write_text(
        "not the reference", encoding="utf-8"
    )

    with pytest.raises(FixtureIntegrityError, match="transcript hash mismatch"):
        _verify_fixture_payloads(tmp_path, fixture)


def test_verify_fixture_payloads_rejects_a_missing_audio_file(tmp_path: Path) -> None:
    fixture = _fixture("missing", b"synthetic-audio")

    with pytest.raises(FixtureIntegrityError, match="missing"):
        _verify_fixture_payloads(tmp_path, fixture)


def test_verify_fixture_payloads_rejects_a_duration_band_mismatch(tmp_path: Path) -> None:
    (tmp_path / "audio" / "vi_clear").mkdir(parents=True)
    audio_path = tmp_path / "audio" / "vi_clear" / "short.wav"
    # Actual audio is under 3 seconds, but the fixture declares "3s_to_8s".
    audio_bytes = _write_speech_like_wav(audio_path, seconds=1.0)
    fixture = _fixture(
        "short", audio_bytes, duration_band=AsrFixtureDurationBand.FROM_3S_TO_8S
    )
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "short.txt").write_text("reference text", encoding="utf-8")

    with pytest.raises(FixtureIntegrityError, match="duration_band mismatch"):
        _verify_fixture_payloads(tmp_path, fixture)


def test_companion_image_passes_the_real_p2_t1_image_policy(tmp_path: Path) -> None:
    image_path = tmp_path / "companion.png"
    _write_p2t1_companion_image(image_path)

    signals = inspect_image(image_path)
    reasons = assess_image(signals, MediaQualityPolicy())

    assert reasons == ()


@pytest.mark.parametrize(
    ("detected", "expected", "matches"),
    (
        ("vi", "vi", True),
        ("en", "en-us", True),
        ("en-us", "en", True),
        ("vi", "en", False),
        ("VI", "vi", True),
    ),
)
def test_language_matches_compares_primary_subtags_case_insensitively(
    detected: str, expected: str, matches: bool
) -> None:
    assert _language_matches(detected, expected) is matches


def test_percentile_matches_known_values_for_a_five_point_series() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    assert _percentile(values, 0.5) == pytest.approx(30.0)
    assert _percentile(values, 0.0) == pytest.approx(10.0)
    assert _percentile(values, 1.0) == pytest.approx(50.0)


def test_percentile_handles_a_single_value() -> None:
    assert _percentile([42.0], 0.95) == pytest.approx(42.0)


@pytest.mark.parametrize(
    ("expected_speech_present", "diagnostic", "outcome"),
    (
        (True, AsrSpeechDiagnostic.DETECTED, AsrSpeechPresenceOutcome.MATCH),
        (True, AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED, AsrSpeechPresenceOutcome.MISMATCH),
        (True, AsrSpeechDiagnostic.INDETERMINATE, AsrSpeechPresenceOutcome.NOT_MEASURED),
        (False, AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED, AsrSpeechPresenceOutcome.MATCH),
        (False, AsrSpeechDiagnostic.DETECTED, AsrSpeechPresenceOutcome.MISMATCH),
        (False, AsrSpeechDiagnostic.INDETERMINATE, AsrSpeechPresenceOutcome.NOT_MEASURED),
    ),
)
def test_speech_presence_outcome_matches_the_declared_matrix(
    expected_speech_present: bool,
    diagnostic: AsrSpeechDiagnostic,
    outcome: AsrSpeechPresenceOutcome,
) -> None:
    assert speech_presence_outcome_for(expected_speech_present, diagnostic) is outcome


def test_run_result_succeeded_requires_speech_diagnostic_and_no_error_fields() -> None:
    with pytest.raises(ValidationError, match="requires a speech diagnostic"):
        AsrRound1RunResultV1(
            run_id="asr-round1-" + "a" * 64,
            fixture_id="fixture-1",
            scenario=AsrFixtureScenario.VI_CLEAR,
            split=AsrFixtureSplit.HELD_OUT,
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            profile_config_hash="b" * 64,
            outcome=AsrRound1RunOutcome.SUCCEEDED,
            attempt_number=1,
            repair_attempted=False,
            is_cold_start=False,
            inference_latency_ms=12.0,
        )


def test_run_result_succeeded_requires_speech_presence_outcome() -> None:
    with pytest.raises(ValidationError, match="requires a speech-presence outcome"):
        AsrRound1RunResultV1(
            run_id="asr-round1-" + "a" * 64,
            fixture_id="fixture-1",
            scenario=AsrFixtureScenario.VI_CLEAR,
            split=AsrFixtureSplit.HELD_OUT,
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            profile_config_hash="b" * 64,
            outcome=AsrRound1RunOutcome.SUCCEEDED,
            attempt_number=1,
            repair_attempted=False,
            is_cold_start=False,
            inference_latency_ms=12.0,
            speech_diagnostic=AsrSpeechDiagnostic.DETECTED,
        )


def test_run_result_succeeded_accepts_a_complete_speech_presence_outcome() -> None:
    result = AsrRound1RunResultV1(
        run_id="asr-round1-" + "a" * 64,
        fixture_id="fixture-1",
        scenario=AsrFixtureScenario.VI_CLEAR,
        split=AsrFixtureSplit.HELD_OUT,
        profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
        profile_config_hash="b" * 64,
        outcome=AsrRound1RunOutcome.SUCCEEDED,
        attempt_number=1,
        repair_attempted=False,
        is_cold_start=False,
        inference_latency_ms=12.0,
        speech_diagnostic=AsrSpeechDiagnostic.DETECTED,
        speech_presence_outcome=AsrSpeechPresenceOutcome.MATCH,
    )

    assert result.speech_presence_outcome is AsrSpeechPresenceOutcome.MATCH


def test_run_result_failed_requires_error_code_and_detail() -> None:
    with pytest.raises(ValidationError, match="requires an error code"):
        AsrRound1RunResultV1(
            run_id="asr-round1-" + "a" * 64,
            fixture_id="fixture-1",
            scenario=AsrFixtureScenario.VI_CLEAR,
            split=AsrFixtureSplit.HELD_OUT,
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            profile_config_hash="b" * 64,
            outcome=AsrRound1RunOutcome.FAILED,
            attempt_number=1,
            repair_attempted=False,
            is_cold_start=False,
        )


def test_run_result_failed_rejects_a_speech_presence_outcome() -> None:
    with pytest.raises(ValidationError, match="success-only measurements"):
        AsrRound1RunResultV1(
            run_id="asr-round1-" + "a" * 64,
            fixture_id="fixture-1",
            scenario=AsrFixtureScenario.SILENCE,
            split=AsrFixtureSplit.HELD_OUT,
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            profile_config_hash="b" * 64,
            outcome=AsrRound1RunOutcome.FAILED,
            attempt_number=0,
            repair_attempted=False,
            is_cold_start=False,
            error_code=AsrErrorCode.INPUT_NOT_VALIDATED,
            error_detail=AsrErrorDetail.MEDIA_VALIDATION_NOT_PASSED,
            speech_presence_outcome=AsrSpeechPresenceOutcome.NOT_MEASURED,
        )


def test_run_result_zero_attempt_forbids_inference_latency() -> None:
    with pytest.raises(ValidationError, match="cannot report inference latency"):
        AsrRound1RunResultV1(
            run_id="asr-round1-" + "a" * 64,
            fixture_id="fixture-1",
            scenario=AsrFixtureScenario.VI_CLEAR,
            split=AsrFixtureSplit.HELD_OUT,
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            profile_config_hash="b" * 64,
            outcome=AsrRound1RunOutcome.FAILED,
            attempt_number=0,
            repair_attempted=False,
            is_cold_start=False,
            inference_latency_ms=5.0,
            error_code=AsrErrorCode.INPUT_NOT_VALIDATED,
            error_detail=AsrErrorDetail.MEDIA_VALIDATION_NOT_PASSED,
        )


def _write_manifest_fixture_payload(
    fixtures_root: Path,
    fixture_id: str,
    scenario: AsrFixtureScenario,
    *,
    speech_like: bool,
    seconds: float = 4.0,
) -> AsrRound1FixtureEntryV1:
    scenario_dir = fixtures_root / "audio" / scenario.value
    scenario_dir.mkdir(parents=True, exist_ok=True)
    audio_path = scenario_dir / f"{fixture_id}.wav"
    audio_bytes = (
        _write_speech_like_wav(audio_path, seconds=seconds)
        if speech_like
        else _write_silent_wav(audio_path, seconds=seconds)
    )
    speech = scenario is not AsrFixtureScenario.SILENCE
    transcript_ref = None
    transcript_hash = None
    if speech:
        transcripts_dir = fixtures_root / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        (transcripts_dir / f"{fixture_id}.txt").write_text("reference text", encoding="utf-8")
        transcript_ref = f"transcripts/{fixture_id}.txt"
        transcript_hash = sha256(b"reference text").hexdigest()
    return AsrRound1FixtureEntryV1(
        fixture_id=fixture_id,
        scenario=scenario,
        expected_language="vi" if speech else None,
        expected_languages=None,
        source_audio_ref=f"audio/{scenario.value}/{fixture_id}.wav",
        source_audio_sha256=sha256(audio_bytes).hexdigest(),
        reference_transcript_ref=transcript_ref,
        reference_transcript_sha256=transcript_hash,
        data_provenance=AsrFixtureDataProvenance.SYNTHETIC,
        wer_eligible=speech,
        cer_eligible=speech,
        language_accuracy_eligible=speech,
        fixture_version="v1",
        expected_speech_present=speech,
        duration_band=AsrFixtureDurationBand.FROM_3S_TO_8S,
        split=AsrFixtureSplit.HELD_OUT,
        notes="unit test fixture",
    )


def test_select_warmup_fixture_picks_the_first_real_pass_by_id(tmp_path: Path) -> None:
    companion_image_path = tmp_path / "companion.png"
    _write_p2t1_companion_image(companion_image_path)
    silent = _write_manifest_fixture_payload(
        tmp_path, "a-silence", AsrFixtureScenario.SILENCE, speech_like=False
    )
    speech = _write_manifest_fixture_payload(
        tmp_path, "b-speech", AsrFixtureScenario.VI_CLEAR, speech_like=True
    )

    picked = _select_warmup_fixture(tmp_path, (silent, speech), companion_image_path)

    assert picked.fixture_id == "b-speech"
    assert picked.media_validation.decision == "PASS"


def test_select_warmup_fixture_raises_when_no_fixture_passes_p2_t1(tmp_path: Path) -> None:
    companion_image_path = tmp_path / "companion.png"
    _write_p2t1_companion_image(companion_image_path)
    silent_one = _write_manifest_fixture_payload(
        tmp_path, "silence-one", AsrFixtureScenario.SILENCE, speech_like=False
    )
    silent_two = _write_manifest_fixture_payload(
        tmp_path, "silence-two", AsrFixtureScenario.SILENCE, speech_like=False
    )

    with pytest.raises(NoWarmupFixtureAvailableError, match="no manifest fixture"):
        _select_warmup_fixture(tmp_path, (silent_one, silent_two), companion_image_path)
