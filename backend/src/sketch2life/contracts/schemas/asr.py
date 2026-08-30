"""Versioned, provider-neutral contracts for P2-T2 Phase A ASR fixtures."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AsrProfileId(StrEnum):
    FAKE_DETERMINISTIC_V1 = "FAKE_DETERMINISTIC_V1"
    FAKE_IDEMPOTENT_TIMEOUT_V1 = "FAKE_IDEMPOTENT_TIMEOUT_V1"
    WHISPER_TURBO_INT8_AUTO_V1 = "WHISPER_TURBO_INT8_AUTO_V1"
    WHISPER_TURBO_FP16_AUTO_V1 = "WHISPER_TURBO_FP16_AUTO_V1"
    WHISPER_LARGE_V3_INT8_AUTO_V1 = "WHISPER_LARGE_V3_INT8_AUTO_V1"


class AsrSpeechDiagnostic(StrEnum):
    DETECTED = "DETECTED"
    NO_SPEECH_SUSPECTED = "NO_SPEECH_SUSPECTED"
    INDETERMINATE = "INDETERMINATE"


class AsrErrorCode(StrEnum):
    INPUT_NOT_VALIDATED = "INPUT_NOT_VALIDATED"
    ASR_TIMEOUT = "ASR_TIMEOUT"
    ASR_MODEL_UNAVAILABLE = "ASR_MODEL_UNAVAILABLE"
    ASR_PROVIDER_FAILURE = "ASR_PROVIDER_FAILURE"
    ASR_SCHEMA_INVALID = "ASR_SCHEMA_INVALID"


class AsrErrorDetail(StrEnum):
    MEDIA_VALIDATION_NOT_PASSED = "MEDIA_VALIDATION_NOT_PASSED"
    MEDIA_VALIDATION_PROVENANCE_MISSING = "MEDIA_VALIDATION_PROVENANCE_MISSING"
    SOURCE_AUDIO_UNREADABLE = "SOURCE_AUDIO_UNREADABLE"
    SOURCE_AUDIO_HASH_MISMATCH = "SOURCE_AUDIO_HASH_MISMATCH"
    TIMEOUT_BUDGET_EXCEEDED = "TIMEOUT_BUDGET_EXCEEDED"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    TRANSIENT_RUNTIME_FAILURE = "TRANSIENT_RUNTIME_FAILURE"
    PERMANENT_RUNTIME_FAILURE = "PERMANENT_RUNTIME_FAILURE"
    OUTPUT_MAPPING_FAILED = "OUTPUT_MAPPING_FAILED"


class AsrAudioReferenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ref: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AudioDerivationProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transform_name: str = Field(min_length=1)
    transform_config_version: str = Field(min_length=1)
    source_audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    processing_audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class MediaValidationProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    validation_artifact_ref: str = Field(min_length=1)
    validation_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["PASS", "RECAPTURE"]
    validator_policy_version: str = Field(min_length=1)


class LanguageHintV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=2, max_length=32)
    source: str = Field(min_length=1)
    is_ground_truth: Literal[False] = False


class AsrWeightProvenanceV1(BaseModel):
    """Converted-weight source and license for a real ASR profile. Absent for fakes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str = Field(min_length=1)
    license: str = Field(min_length=1)


class AsrProfileV1(BaseModel):
    """Phase A catalog entries are deterministic fakes, never a model runtime.

    Phase B entries (`adapter_kind="FASTER_WHISPER"`) additionally require
    `model_identifier`, `model_revision`, `weight_provenance`, `adapter_version`,
    and `runtime_version`; a `DETERMINISTIC_FAKE` entry must leave all five `None`,
    which keeps every Phase A fake profile's value/behavior byte-for-byte unchanged.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: AsrProfileId
    adapter_kind: Literal["DETERMINISTIC_FAKE", "FASTER_WHISPER"] = "DETERMINISTIC_FAKE"
    task: Literal["transcribe"] = "transcribe"
    language_mode: Literal["AUTO_DETECT", "HONOR_HINT"] = "AUTO_DETECT"
    beam_size: int = Field(ge=1)
    vad_enabled: bool = False
    word_timestamps_enabled: bool = False
    compute_profile: Literal["NONE", "GPU_INT8_FLOAT16", "GPU_FLOAT16"] = "NONE"
    timeout_seconds: float = Field(gt=0)
    idempotent_timeout_retry: bool = False
    model_identifier: str | None = Field(default=None, min_length=1)
    model_revision: str | None = Field(default=None, min_length=1)
    weight_provenance: AsrWeightProvenanceV1 | None = None
    adapter_version: str | None = Field(default=None, min_length=1)
    runtime_version: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _requires_whisper_provenance_when_real(self) -> AsrProfileV1:
        provenance_fields = (
            self.model_identifier,
            self.model_revision,
            self.weight_provenance,
            self.adapter_version,
            self.runtime_version,
        )
        if self.adapter_kind == "FASTER_WHISPER":
            if any(value is None for value in provenance_fields):
                raise ValueError(
                    "FASTER_WHISPER profile requires model_identifier, model_revision, "
                    "weight_provenance, adapter_version, and runtime_version"
                )
            if self.compute_profile == "NONE":
                raise ValueError("FASTER_WHISPER profile requires a real compute_profile")
        elif any(value is not None for value in provenance_fields):
            raise ValueError("DETERMINISTIC_FAKE profile must not set Whisper provenance fields")
        return self


class AsrProfileCatalogV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["AsrProfileCatalogV1"] = "AsrProfileCatalogV1"
    contract_version: Literal["1.0"] = "1.0"
    profiles: tuple[AsrProfileV1, ...]

    @model_validator(mode="after")
    def _requires_unique_profile_ids(self) -> AsrProfileCatalogV1:
        profile_ids = tuple(profile.profile_id for profile in self.profiles)
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile IDs must be unique")
        return self

    def resolve(self, profile_id: AsrProfileId) -> AsrProfileV1:
        for profile in self.profiles:
            if profile.profile_id is profile_id:
                return profile
        raise ValueError(f"profile is absent from catalog: {profile_id}")


_FASTER_WHISPER_ADAPTER_VERSION = "faster-whisper-asr-adapter-v1"
_FASTER_WHISPER_RUNTIME_VERSION = "faster-whisper==1.2.1;ctranslate2==4.8.1"

_WHISPER_TURBO_WEIGHT_PROVENANCE = AsrWeightProvenanceV1(
    source="huggingface:deepdml/faster-whisper-large-v3-turbo-ct2@4df90f75321148c3a29a9e2351b7ddf8f5b115a8",
    license="MIT",
)
_WHISPER_LARGE_V3_WEIGHT_PROVENANCE = AsrWeightProvenanceV1(
    source="huggingface:Systran/faster-whisper-large-v3@edaa852ec7e145841d8ffdb056a99866b5f0a478",
    license="MIT",
)


def asr_profile_catalog() -> AsrProfileCatalogV1:
    """Single static, versioned, phase-agnostic catalog for request validation and adapters.

    Round 1 (AUTO_DETECT only, per the approved Phase B scope) adds three experimental
    `FASTER_WHISPER` candidates. None is frozen or selected as a runtime default here;
    that is a separate R5/ADR decision. Every Phase A fake entry below is byte-for-byte
    unchanged from before this catalog was renamed from `phase_a_profile_catalog()`.
    """

    return AsrProfileCatalogV1(
        profiles=(
            AsrProfileV1(
                profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1,
                beam_size=1,
                timeout_seconds=5.0,
            ),
            AsrProfileV1(
                profile_id=AsrProfileId.FAKE_IDEMPOTENT_TIMEOUT_V1,
                beam_size=1,
                timeout_seconds=5.0,
                idempotent_timeout_retry=True,
            ),
            AsrProfileV1(
                profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
                adapter_kind="FASTER_WHISPER",
                language_mode="AUTO_DETECT",
                beam_size=5,
                vad_enabled=False,
                word_timestamps_enabled=False,
                compute_profile="GPU_INT8_FLOAT16",
                timeout_seconds=120.0,
                idempotent_timeout_retry=False,
                model_identifier="deepdml/faster-whisper-large-v3-turbo-ct2",
                model_revision="4df90f75321148c3a29a9e2351b7ddf8f5b115a8",
                weight_provenance=_WHISPER_TURBO_WEIGHT_PROVENANCE,
                adapter_version=_FASTER_WHISPER_ADAPTER_VERSION,
                runtime_version=_FASTER_WHISPER_RUNTIME_VERSION,
            ),
            AsrProfileV1(
                profile_id=AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1,
                adapter_kind="FASTER_WHISPER",
                language_mode="AUTO_DETECT",
                beam_size=5,
                vad_enabled=False,
                word_timestamps_enabled=False,
                compute_profile="GPU_FLOAT16",
                timeout_seconds=120.0,
                idempotent_timeout_retry=False,
                model_identifier="deepdml/faster-whisper-large-v3-turbo-ct2",
                model_revision="4df90f75321148c3a29a9e2351b7ddf8f5b115a8",
                weight_provenance=_WHISPER_TURBO_WEIGHT_PROVENANCE,
                adapter_version=_FASTER_WHISPER_ADAPTER_VERSION,
                runtime_version=_FASTER_WHISPER_RUNTIME_VERSION,
            ),
            AsrProfileV1(
                profile_id=AsrProfileId.WHISPER_LARGE_V3_INT8_AUTO_V1,
                adapter_kind="FASTER_WHISPER",
                language_mode="AUTO_DETECT",
                beam_size=5,
                vad_enabled=False,
                word_timestamps_enabled=False,
                compute_profile="GPU_INT8_FLOAT16",
                timeout_seconds=180.0,
                idempotent_timeout_retry=False,
                model_identifier="Systran/faster-whisper-large-v3",
                model_revision="edaa852ec7e145841d8ffdb056a99866b5f0a478",
                weight_provenance=_WHISPER_LARGE_V3_WEIGHT_PROVENANCE,
                adapter_version=_FASTER_WHISPER_ADAPTER_VERSION,
                runtime_version=_FASTER_WHISPER_RUNTIME_VERSION,
            ),
        )
    )


def profile_config_hash(profile: AsrProfileV1) -> str:
    payload = dumps(profile.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


class AsrRequestV1(BaseModel):
    """Structurally valid request. An unknown profile is rejected before the port runs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["AsrRequestV1"] = "AsrRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    correlation_id: str = Field(min_length=1)
    source_audio_ref: AsrAudioReferenceV1
    processing_audio_ref: AsrAudioReferenceV1 | None = None
    derivation_provenance: AudioDerivationProvenanceV1 | None = None
    media_validation: MediaValidationProvenanceV1 | None = None
    requested_profile_id: AsrProfileId
    language_hint: LanguageHintV1 | None = None

    @model_validator(mode="after")
    def _requires_valid_working_copy_and_profile(self) -> AsrRequestV1:
        if self.processing_audio_ref is None and self.derivation_provenance is not None:
            raise ValueError("derivation provenance requires a processing audio reference")
        if self.processing_audio_ref is not None:
            if self.derivation_provenance is None:
                raise ValueError("processing audio reference requires derivation provenance")
            if self.derivation_provenance.source_audio_sha256 != self.source_audio_ref.sha256:
                raise ValueError("derivation provenance must link to the source audio hash")
            if (
                self.derivation_provenance.processing_audio_sha256
                != self.processing_audio_ref.sha256
            ):
                raise ValueError("derivation provenance must link to the processing audio hash")
        asr_profile_catalog().resolve(self.requested_profile_id)
        return self


class AsrWordV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    text: str = Field(min_length=1)
    probability: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def _requires_ordered_timestamps(self) -> AsrWordV1:
        if self.end_seconds < self.start_seconds:
            raise ValueError("word end timestamp precedes start timestamp")
        return self


class AsrSegmentV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    text: str = Field(min_length=1)
    average_log_probability: float | None = None
    compression_ratio: float | None = Field(default=None, ge=0)
    no_speech_probability: float | None = Field(default=None, ge=0, le=1)
    words: tuple[AsrWordV1, ...] | None = None

    @model_validator(mode="after")
    def _requires_ordered_timestamps(self) -> AsrSegmentV1:
        if self.end_seconds < self.start_seconds:
            raise ValueError("segment end timestamp precedes start timestamp")
        return self


class AsrQualityMetadataV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["1.0"] = "1.0"
    media_validation_artifact_ref: str = Field(min_length=1)
    media_validation_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mean_segment_log_probability: float | None = None
    mean_no_speech_probability: float | None = Field(default=None, ge=0, le=1)


class AsrResultEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["AsrResultV1"] = "AsrResultV1"
    contract_version: Literal["1.0"] = "1.0"
    correlation_id: str = Field(min_length=1)
    executed_at: datetime
    source_audio_ref: AsrAudioReferenceV1
    profile_id: AsrProfileId
    attempt_number: int = Field(ge=0, le=2)
    repair_attempted: bool

    @field_validator("executed_at")
    @classmethod
    def _requires_timezone_aware_execution_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("executed_at must be timezone aware")
        return value


class AsrSuccessV1(AsrResultEnvelopeV1):
    status: Literal["SUCCEEDED"] = "SUCCEEDED"
    transcript_raw: str
    speech_diagnostic: AsrSpeechDiagnostic
    detected_language: str = Field(min_length=2, max_length=32)
    language_probability: float | None = Field(default=None, ge=0, le=1)
    language_hint_echo: LanguageHintV1 | None = None
    language_hint_applied: bool = False
    segments: tuple[AsrSegmentV1, ...]
    input_duration_seconds: float = Field(gt=0)
    vad_enabled: bool
    duration_after_vad_seconds: float | None = Field(default=None, ge=0)
    model_identifier: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)
    runtime_version: str = Field(min_length=1)
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    quality_metadata: AsrQualityMetadataV1

    @model_validator(mode="after")
    def _requires_coherent_success_signals(self) -> AsrSuccessV1:
        if self.vad_enabled and self.duration_after_vad_seconds is None:
            raise ValueError("VAD duration is required when VAD is enabled")
        if not self.vad_enabled and self.duration_after_vad_seconds is not None:
            raise ValueError("VAD duration must be null when VAD is disabled")
        if self.speech_diagnostic is AsrSpeechDiagnostic.DETECTED and not self.segments:
            raise ValueError("detected speech requires at least one segment")
        if self.segments and self.segments[-1].end_seconds > self.input_duration_seconds:
            raise ValueError("segment timestamp exceeds input duration")
        return self


class AsrFailureV1(AsrResultEnvelopeV1):
    status: Literal["FAILED"] = "FAILED"
    error_code: AsrErrorCode
    retryable: bool
    error_detail: AsrErrorDetail


AsrResultV1 = Annotated[AsrSuccessV1 | AsrFailureV1, Field(discriminator="status")]


class AsrFixtureManifestEntryV1(BaseModel):
    """Synthetic Phase A fixture declaration; no audio payload is stored here."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    source_audio_ref: str = Field(min_length=1)
    source_audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    validation_artifact_ref: str = Field(min_length=1)
    validation_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    validation_decision: Literal["PASS", "RECAPTURE"]
    requested_profile_id: AsrProfileId
    scenario: str = Field(min_length=1)
    synthetic_data: Literal[True] = True
