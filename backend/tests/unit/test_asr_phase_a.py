from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrFailureV1,
    AsrFixtureManifestEntryV1,
    AsrProfileId,
    AsrRequestV1,
    AsrResultV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
    AudioDerivationProvenanceV1,
    MediaValidationProvenanceV1,
    asr_profile_catalog,
)
from sketch2life.infrastructure.ai.fake_asr import (
    DeterministicFixtureAsrAdapter,
    FakeAsrFixture,
    FakeAsrScenario,
)


def test_manifest_is_synthetic_and_uses_only_phase_a_profiles() -> None:
    manifest_path = _project_root() / "data/fixtures/manifests/asr-phase-a-v1.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = tuple(AsrFixtureManifestEntryV1.model_validate(item) for item in payload["fixtures"])

    assert payload["data_policy"] == "synthetic-only"
    assert all(entry.synthetic_data for entry in entries)
    assert all(entry.source_audio_sha256 == _hash(entry.source_audio_ref) for entry in entries)
    assert all(
        entry.validation_artifact_sha256 == _hash(f"validation:{entry.validation_decision}")
        for entry in entries
    )
    assert {entry.requested_profile_id for entry in entries} <= {
        profile.profile_id
        for profile in asr_profile_catalog().profiles
        if profile.adapter_kind == "DETERMINISTIC_FAKE"
    }


@pytest.mark.parametrize(
    ("artifact_ref", "expected_transcript", "expected_language"),
    (
        ("fixture:asr:vi:v1", "Con buom bay toi bong hoa", "vi"),
        ("fixture:asr:en:v1", "A bird is flying", "en"),
        ("fixture:asr:code-switch:v1", "Con ve mot red car", "vi"),
    ),
)
def test_fake_success_preserves_source_and_returns_schema_valid_contract(
    artifact_ref: str, expected_transcript: str, expected_language: str
) -> None:
    request = _request(artifact_ref)
    result = _adapter().transcribe(request)

    assert isinstance(result, AsrSuccessV1)
    assert result.transcript_raw == expected_transcript
    assert result.detected_language == expected_language
    assert result.speech_diagnostic is AsrSpeechDiagnostic.DETECTED
    assert result.source_audio_ref == request.source_audio_ref
    assert result.attempt_number == 1
    assert result.repair_attempted is False
    assert result.quality_metadata.media_validation_artifact_ref == "fixture:validation:pass:v1"
    parsed = TypeAdapter(AsrResultV1).validate_python(result.model_dump(mode="json"))
    assert isinstance(parsed, AsrSuccessV1)


def test_silence_is_successful_diagnostic_and_never_a_t2_recapture() -> None:
    result = _adapter().transcribe(_request("fixture:asr:silence:v1"))

    assert isinstance(result, AsrSuccessV1)
    assert result.transcript_raw == ""
    assert result.segments == ()
    assert result.speech_diagnostic is AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED
    assert result.attempt_number == 1


def test_indeterminate_speech_is_successful_and_keeps_uncertainty() -> None:
    result = _adapter().transcribe(_request("fixture:asr:indeterminate:v1"))

    assert isinstance(result, AsrSuccessV1)
    assert result.speech_diagnostic is AsrSpeechDiagnostic.INDETERMINATE
    assert result.transcript_raw == ""
    assert result.segments == ()


@pytest.mark.parametrize(
    ("artifact_ref", "profile_id", "error_code", "attempt_number", "retryable", "repair"),
    (
        (
            "fixture:asr:schema-invalid:v1",
            AsrProfileId.FAKE_DETERMINISTIC_V1,
            AsrErrorCode.ASR_SCHEMA_INVALID,
            1,
            False,
            True,
        ),
        (
            "fixture:asr:timeout:v1",
            AsrProfileId.FAKE_DETERMINISTIC_V1,
            AsrErrorCode.ASR_TIMEOUT,
            1,
            False,
            False,
        ),
        (
            "fixture:asr:timeout:v1",
            AsrProfileId.FAKE_IDEMPOTENT_TIMEOUT_V1,
            AsrErrorCode.ASR_TIMEOUT,
            2,
            True,
            False,
        ),
        (
            "fixture:asr:transient-failure:v1",
            AsrProfileId.FAKE_DETERMINISTIC_V1,
            AsrErrorCode.ASR_PROVIDER_FAILURE,
            2,
            True,
            False,
        ),
        (
            "fixture:asr:permanent-failure:v1",
            AsrProfileId.FAKE_DETERMINISTIC_V1,
            AsrErrorCode.ASR_PROVIDER_FAILURE,
            1,
            False,
            False,
        ),
        (
            "fixture:asr:model-unavailable:v1",
            AsrProfileId.FAKE_DETERMINISTIC_V1,
            AsrErrorCode.ASR_MODEL_UNAVAILABLE,
            1,
            False,
            False,
        ),
    ),
)
def test_fake_failures_follow_the_retry_and_repair_matrix(
    artifact_ref: str,
    profile_id: AsrProfileId,
    error_code: AsrErrorCode,
    attempt_number: int,
    retryable: bool,
    repair: bool,
) -> None:
    result = _adapter().transcribe(_request(artifact_ref, profile_id=profile_id))

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is error_code
    assert result.attempt_number == attempt_number
    assert result.retryable is retryable
    assert result.repair_attempted is repair
    assert not hasattr(result, "transcript_raw")
    parsed = TypeAdapter(AsrResultV1).validate_python(result.model_dump(mode="json"))
    assert isinstance(parsed, AsrFailureV1)


def test_transient_failure_can_retry_once_and_succeed() -> None:
    result = _adapter().transcribe(_request("fixture:asr:transient-success:v1"))

    assert isinstance(result, AsrSuccessV1)
    assert result.attempt_number == 2
    assert result.repair_attempted is False


@pytest.mark.parametrize("decision", (None, "RECAPTURE"))
def test_missing_or_failed_p2_t1_validation_is_a_typed_failure(
    decision: str | None,
) -> None:
    media_validation = None if decision is None else _validation(decision)
    result = _adapter().transcribe(
        _request_with_validation("fixture:asr:vi:v1", media_validation=media_validation)
    )

    assert isinstance(result, AsrFailureV1)
    assert result.error_code is AsrErrorCode.INPUT_NOT_VALIDATED
    assert result.attempt_number == 0
    assert result.repair_attempted is False


def test_invalid_profile_is_rejected_at_request_construction_before_port_invocation() -> None:
    payload = _request("fixture:asr:vi:v1").model_dump(mode="json")
    payload["requested_profile_id"] = "FAKE_UNKNOWN_PROFILE"

    with pytest.raises(ValidationError):
        AsrRequestV1.model_validate(payload)


def test_processing_reference_requires_complete_derivation_provenance() -> None:
    request = _request("fixture:asr:vi:v1")
    payload = request.model_dump(mode="json")
    payload["processing_audio_ref"] = {
        "artifact_ref": "fixture:asr:processed:v1",
        "sha256": _hash("processed"),
    }

    with pytest.raises(ValidationError):
        AsrRequestV1.model_validate(payload)

    payload["derivation_provenance"] = AudioDerivationProvenanceV1(
        transform_name="fixture-normalization",
        transform_config_version="v1",
        source_audio_sha256=request.source_audio_ref.sha256,
        processing_audio_sha256=_hash("processed"),
    ).model_dump(mode="json")
    derived_request = AsrRequestV1.model_validate(payload)
    assert derived_request.processing_audio_ref is not None


def _adapter() -> DeterministicFixtureAsrAdapter:
    return DeterministicFixtureAsrAdapter(
        {
            "fixture:asr:vi:v1": FakeAsrFixture(
                FakeAsrScenario.VIETNAMESE, "Con buom bay toi bong hoa", "vi"
            ),
            "fixture:asr:en:v1": FakeAsrFixture(
                FakeAsrScenario.NON_VIETNAMESE, "A bird is flying", "en"
            ),
            "fixture:asr:code-switch:v1": FakeAsrFixture(
                FakeAsrScenario.CODE_SWITCHING, "Con ve mot red car", "vi"
            ),
            "fixture:asr:silence:v1": FakeAsrFixture(FakeAsrScenario.SILENCE),
            "fixture:asr:indeterminate:v1": FakeAsrFixture(FakeAsrScenario.INDETERMINATE),
            "fixture:asr:schema-invalid:v1": FakeAsrFixture(FakeAsrScenario.SCHEMA_INVALID),
            "fixture:asr:timeout:v1": FakeAsrFixture(FakeAsrScenario.TIMEOUT),
            "fixture:asr:transient-success:v1": FakeAsrFixture(
                FakeAsrScenario.PROVIDER_TRANSIENT_SUCCESS, "Con meo dang ngu", "vi"
            ),
            "fixture:asr:transient-failure:v1": FakeAsrFixture(
                FakeAsrScenario.PROVIDER_TRANSIENT_FAILURE
            ),
            "fixture:asr:permanent-failure:v1": FakeAsrFixture(
                FakeAsrScenario.PROVIDER_PERMANENT_FAILURE
            ),
            "fixture:asr:model-unavailable:v1": FakeAsrFixture(FakeAsrScenario.MODEL_UNAVAILABLE),
        }
    )


def _request(
    artifact_ref: str,
    *,
    profile_id: AsrProfileId = AsrProfileId.FAKE_DETERMINISTIC_V1,
) -> AsrRequestV1:
    return _request_with_validation(
        artifact_ref,
        profile_id=profile_id,
        media_validation=_validation("PASS"),
    )


def _request_with_validation(
    artifact_ref: str,
    *,
    profile_id: AsrProfileId = AsrProfileId.FAKE_DETERMINISTIC_V1,
    media_validation: MediaValidationProvenanceV1 | None,
) -> AsrRequestV1:
    return AsrRequestV1(
        correlation_id="phase-a-test-correlation",
        source_audio_ref=AsrAudioReferenceV1(
            artifact_ref=artifact_ref,
            sha256=_hash(artifact_ref),
        ),
        media_validation=media_validation,
        requested_profile_id=profile_id,
    )


def _validation(decision: str) -> MediaValidationProvenanceV1:
    return MediaValidationProvenanceV1(
        validation_artifact_ref="fixture:validation:pass:v1",
        validation_artifact_sha256=_hash(f"validation:{decision}"),
        decision=decision,  # type: ignore[arg-type]
        validator_policy_version="media-quality-policy-v1",
    )


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]
