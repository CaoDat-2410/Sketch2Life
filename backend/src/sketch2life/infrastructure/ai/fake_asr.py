"""Deterministic, dependency-free Phase A ASR fixture adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sketch2life.application.ports.asr import AsrPort
from sketch2life.contracts.schemas.asr import (
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrQualityMetadataV1,
    AsrRequestV1,
    AsrResultV1,
    AsrSegmentV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
    asr_profile_catalog,
    profile_config_hash,
)


class FakeAsrScenario(StrEnum):
    VIETNAMESE = "VIETNAMESE"
    NON_VIETNAMESE = "NON_VIETNAMESE"
    CODE_SWITCHING = "CODE_SWITCHING"
    SILENCE = "SILENCE"
    INDETERMINATE = "INDETERMINATE"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    TIMEOUT = "TIMEOUT"
    PROVIDER_TRANSIENT_SUCCESS = "PROVIDER_TRANSIENT_SUCCESS"
    PROVIDER_TRANSIENT_FAILURE = "PROVIDER_TRANSIENT_FAILURE"
    PROVIDER_PERMANENT_FAILURE = "PROVIDER_PERMANENT_FAILURE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class FakeAsrFixture:
    scenario: FakeAsrScenario
    transcript: str = ""
    language: str = "vi"


class DeterministicFixtureAsrAdapter(AsrPort):
    """Maps synthetic fixture references to contracts without loading or invoking a model."""

    _EXECUTED_AT = datetime(2026, 8, 30, tzinfo=UTC)

    def __init__(self, fixtures: dict[str, FakeAsrFixture]) -> None:
        self._fixtures = dict(fixtures)
        self._catalog = asr_profile_catalog()

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1:
        profile = self._catalog.resolve(request.requested_profile_id)
        if request.media_validation is None:
            return self._failure(
                request,
                AsrErrorCode.INPUT_NOT_VALIDATED,
                AsrErrorDetail.MEDIA_VALIDATION_PROVENANCE_MISSING,
                attempt_number=0,
                retryable=False,
            )
        if request.media_validation.decision != "PASS":
            return self._failure(
                request,
                AsrErrorCode.INPUT_NOT_VALIDATED,
                AsrErrorDetail.MEDIA_VALIDATION_NOT_PASSED,
                attempt_number=0,
                retryable=False,
            )

        fixture = self._fixtures.get(request.source_audio_ref.artifact_ref)
        if fixture is None:
            return self._failure(
                request,
                AsrErrorCode.ASR_SCHEMA_INVALID,
                AsrErrorDetail.OUTPUT_MAPPING_FAILED,
                attempt_number=1,
                retryable=False,
                repair_attempted=True,
            )
        if fixture.scenario is FakeAsrScenario.MODEL_UNAVAILABLE:
            return self._failure(
                request,
                AsrErrorCode.ASR_MODEL_UNAVAILABLE,
                AsrErrorDetail.MODEL_LOAD_FAILED,
                attempt_number=1,
                retryable=False,
            )
        if fixture.scenario is FakeAsrScenario.TIMEOUT:
            retryable = profile.idempotent_timeout_retry
            return self._failure(
                request,
                AsrErrorCode.ASR_TIMEOUT,
                AsrErrorDetail.TIMEOUT_BUDGET_EXCEEDED,
                attempt_number=2 if retryable else 1,
                retryable=retryable,
            )
        if fixture.scenario is FakeAsrScenario.PROVIDER_TRANSIENT_FAILURE:
            return self._failure(
                request,
                AsrErrorCode.ASR_PROVIDER_FAILURE,
                AsrErrorDetail.TRANSIENT_RUNTIME_FAILURE,
                attempt_number=2,
                retryable=True,
            )
        if fixture.scenario is FakeAsrScenario.PROVIDER_PERMANENT_FAILURE:
            return self._failure(
                request,
                AsrErrorCode.ASR_PROVIDER_FAILURE,
                AsrErrorDetail.PERMANENT_RUNTIME_FAILURE,
                attempt_number=1,
                retryable=False,
            )
        if fixture.scenario is FakeAsrScenario.SCHEMA_INVALID:
            return self._failure(
                request,
                AsrErrorCode.ASR_SCHEMA_INVALID,
                AsrErrorDetail.OUTPUT_MAPPING_FAILED,
                attempt_number=1,
                retryable=False,
                repair_attempted=True,
            )

        attempts = 2 if fixture.scenario is FakeAsrScenario.PROVIDER_TRANSIENT_SUCCESS else 1
        return self._success(request, fixture, attempts)

    def _success(
        self, request: AsrRequestV1, fixture: FakeAsrFixture, attempt_number: int
    ) -> AsrSuccessV1:
        profile = self._catalog.resolve(request.requested_profile_id)
        no_speech = fixture.scenario is FakeAsrScenario.SILENCE
        indeterminate = fixture.scenario is FakeAsrScenario.INDETERMINATE
        speech_diagnostic = (
            AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED
            if no_speech
            else AsrSpeechDiagnostic.INDETERMINATE
            if indeterminate
            else AsrSpeechDiagnostic.DETECTED
        )
        segments = () if no_speech or indeterminate else (
            AsrSegmentV1(
                index=0,
                start_seconds=0.0,
                end_seconds=1.0,
                text=fixture.transcript,
                average_log_probability=-0.1,
                compression_ratio=1.0,
                no_speech_probability=0.02,
            ),
        )
        validation = request.media_validation
        assert validation is not None
        return AsrSuccessV1(
            correlation_id=request.correlation_id,
            executed_at=self._EXECUTED_AT,
            source_audio_ref=request.source_audio_ref,
            profile_id=profile.profile_id,
            attempt_number=attempt_number,
            repair_attempted=False,
            transcript_raw="" if no_speech or indeterminate else fixture.transcript,
            speech_diagnostic=speech_diagnostic,
            detected_language=fixture.language,
            language_probability=0.99,
            language_hint_echo=request.language_hint,
            language_hint_applied=False,
            segments=segments,
            input_duration_seconds=1.0,
            vad_enabled=False,
            duration_after_vad_seconds=None,
            model_identifier="deterministic-fixture-fake",
            model_revision="phase-a-v1",
            adapter_version="deterministic-fixture-asr-adapter-v1",
            runtime_version="none",
            config_hash=profile_config_hash(profile),
            quality_metadata=AsrQualityMetadataV1(
                media_validation_artifact_ref=validation.validation_artifact_ref,
                media_validation_artifact_sha256=validation.validation_artifact_sha256,
                mean_segment_log_probability=None if not segments else -0.1,
                mean_no_speech_probability=0.98 if no_speech else 0.5 if indeterminate else 0.02,
            ),
        )

    def _failure(
        self,
        request: AsrRequestV1,
        error_code: AsrErrorCode,
        error_detail: AsrErrorDetail,
        *,
        attempt_number: int,
        retryable: bool,
        repair_attempted: bool = False,
    ) -> AsrFailureV1:
        profile = self._catalog.resolve(request.requested_profile_id)
        return AsrFailureV1(
            correlation_id=request.correlation_id,
            executed_at=self._EXECUTED_AT,
            source_audio_ref=request.source_audio_ref,
            profile_id=profile.profile_id,
            attempt_number=attempt_number,
            repair_attempted=repair_attempted,
            error_code=error_code,
            retryable=retryable,
            error_detail=error_detail,
        )
