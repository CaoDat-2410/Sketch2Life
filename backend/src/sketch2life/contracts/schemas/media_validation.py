"""Versioned Pydantic boundary contracts for deterministic media validation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from enum import StrEnum
from hashlib import sha256
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageQualitySignals,
    MediaDecision,
    MediaQualityAssessment,
    MediaRecaptureReason,
)


class SourceMediaReferenceV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_ref: str = Field(min_length=1)
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_status: Literal["AVAILABLE", "MISSING", "UNREADABLE"] = "AVAILABLE"
    working_copy_ref: None = None

    @model_validator(mode="after")
    def validate_provenance(self) -> SourceMediaReferenceV1:
        if self.source_status == "AVAILABLE" and self.sha256 is None:
            raise ValueError("available source must carry a content hash")
        if self.source_status != "AVAILABLE" and self.sha256 is not None:
            raise ValueError("unavailable source must not carry a content hash")
        return self


class ImageQualitySignalsV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    mean_luminance: float | None = Field(default=None, ge=0, le=255)
    luminance_standard_deviation: float | None = Field(default=None, ge=0)
    edge_strength: float | None = Field(default=None, ge=0)
    border_ink_ratio: float | None = Field(default=None, ge=0, le=1)


class AudioQualitySignalsV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    duration_seconds: float | None = Field(default=None, ge=0)
    sample_rate_hz: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    rms: float | None = Field(default=None, ge=0, le=1)
    clipping_ratio: float | None = Field(default=None, ge=0, le=1)
    speech_activity_ratio: float | None = Field(default=None, ge=0, le=1)
    zero_crossing_ratio: float | None = Field(default=None, ge=0, le=1)


class MediaValidationResultV1(BaseModel):
    """Public contract; sources are immutable and normalization is not performed in P2-T1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["MediaValidationResultV1"] = "MediaValidationResultV1"
    contract_version: Literal["1.0"] = "1.0"
    decision: MediaDecision
    recapture_reasons: tuple[MediaRecaptureReason, ...]
    image: SourceMediaReferenceV1
    audio: SourceMediaReferenceV1
    image_signals: ImageQualitySignalsV1
    audio_signals: AudioQualitySignalsV1
    recapture_message: str = Field(min_length=1, max_length=1_000)
    validator_policy_version: str = Field(min_length=1)
    validator_name: Literal["deterministic-media-validator"] = (
        "deterministic-media-validator"
    )


IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH = 128
IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE = 'fixture:rejected-reference:v1'
# This is a positive allowlist, not a generic caller-controlled opaque string.
# It preserves the image references issued by the approved media-validation
# fixtures (the B-series IDs and the versioned drawing identities) plus the
# fixed sanitized failure sentinel. No caller-chosen secret/token namespace is
# accepted, even when its spelling happens to fit a safe ASCII character set.
IMAGE_ONLY_ARTIFACT_REFERENCE_PATTERN = (
    r'^(?:fixture-b[0-9]{2}|'
    r'fixture:(?:drawing|small-dark-drawing|corrupt-drawing):v[0-9]+|'
    r'fixture:rejected-reference:v1)$'
)
_IMAGE_ONLY_ARTIFACT_REFERENCE_RE = re.compile(
    IMAGE_ONLY_ARTIFACT_REFERENCE_PATTERN,
    re.ASCII,
)

_IMAGE_ONLY_REFERENCE_VALIDATION_MESSAGE = (
    'invalid image-only artifact reference'
)


class ImageOnlyValidationContractError(Exception):
    """Sanitized direct-contract rejection with no caller input retained."""

    def __init__(self) -> None:
        super().__init__(_IMAGE_ONLY_REFERENCE_VALIDATION_MESSAGE)

    def errors(
        self,
        *,
        include_context: bool = True,
        include_input: bool = True,
        include_url: bool = True,
    ) -> list[dict[str, Any]]:
        """Expose a ValidationError-shaped diagnostic without caller input."""

        error: dict[str, Any] = {
            'type': 'image_only_reference',
            'loc': ('source_artifact_ref',),
            'msg': _IMAGE_ONLY_REFERENCE_VALIDATION_MESSAGE,
        }
        if include_input:
            error['input'] = None
        if include_context:
            error['ctx'] = {}
        if include_url:
            error['url'] = 'https://errors.pydantic.dev/2.13/v/image_only_reference'
        return [error]

    def json(
        self,
        indent: int | None = None,
        *,
        include_context: bool = True,
        include_input: bool = True,
        include_url: bool = True,
    ) -> str:
        """Return JSON diagnostics using the same safe fields as ``errors``."""

        return json.dumps(
            self.errors(
                include_context=include_context,
                include_input=include_input,
                include_url=include_url,
            ),
            ensure_ascii=True,
            indent=indent,
            separators=None if indent is not None else (',', ':'),
        )

    def error_count(self) -> int:
        return 1


def _is_safe_image_only_artifact_reference(value: object) -> bool:
    if type(value) is not str:
        return False
    if not value or len(value) > IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH:
        return False
    if value != value.strip() or not value.isascii():
        return False
    return _IMAGE_ONLY_ARTIFACT_REFERENCE_RE.fullmatch(value) is not None


class ImageOnlyArtifactReferenceV1:
    __slots__ = ('value',)

    value: str

    def __init__(self, value: object) -> None:
        if not _is_safe_image_only_artifact_reference(value):
            raise ValueError('invalid image-only artifact reference')
        assert isinstance(value, str)
        self.value = value


def try_create_image_only_artifact_reference(
    value: object,
) -> ImageOnlyArtifactReferenceV1 | None:
    try:
        return ImageOnlyArtifactReferenceV1(value)
    except (TypeError, ValueError):
        return None


class ImageOnlyValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class ImageOnlyValidationFailureCode(StrEnum):
    MISSING_SOURCE = "MISSING_SOURCE"
    UNREADABLE_IMAGE = "UNREADABLE_IMAGE"
    UNSUPPORTED_CONTAINER = "UNSUPPORTED_CONTAINER"
    UNSUPPORTED_CODEC = "UNSUPPORTED_CODEC"
    UNSUPPORTED_PIXEL_FORMAT = "UNSUPPORTED_PIXEL_FORMAT"
    CORRUPT_OR_TRUNCATED = "CORRUPT_OR_TRUNCATED"
    INPUT_TOO_LARGE = "INPUT_TOO_LARGE"
    SOURCE_DIGEST_MISMATCH = "SOURCE_DIGEST_MISMATCH"
    VALIDATOR_EXCEPTION = "VALIDATOR_EXCEPTION"
    MALFORMED_RESULT = "MALFORMED_RESULT"
    SERIALIZATION_HASH_MISMATCH = "SERIALIZATION_HASH_MISMATCH"


class ImageOnlySourceStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    TOO_LARGE = "TOO_LARGE"


class ImageOnlyDigestStatus(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_COMPUTED = "NOT_COMPUTED"


class ImageOnlyValidationCheckName(StrEnum):
    SOURCE_READ = "SOURCE_READ"
    SOURCE_DIGEST = "SOURCE_DIGEST"
    D2_METADATA = "D2_METADATA"
    FRAME_COUNT = "FRAME_COUNT"
    DIMENSIONS = "DIMENSIONS"
    PIXEL_BUDGET = "PIXEL_BUDGET"
    LONGEST_EDGE = "LONGEST_EDGE"
    DECODE_INTEGRITY = "DECODE_INTEGRITY"
    STRUCTURAL_POLICY = "STRUCTURAL_POLICY"


class ImageOnlyValidationCheckOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


IMAGE_ONLY_VALIDATION_CHECK_ORDER: tuple[ImageOnlyValidationCheckName, ...] = (
    ImageOnlyValidationCheckName.SOURCE_READ,
    ImageOnlyValidationCheckName.SOURCE_DIGEST,
    ImageOnlyValidationCheckName.D2_METADATA,
    ImageOnlyValidationCheckName.FRAME_COUNT,
    ImageOnlyValidationCheckName.DIMENSIONS,
    ImageOnlyValidationCheckName.PIXEL_BUDGET,
    ImageOnlyValidationCheckName.LONGEST_EDGE,
    ImageOnlyValidationCheckName.DECODE_INTEGRITY,
    ImageOnlyValidationCheckName.STRUCTURAL_POLICY,
)


class ImageOnlyValidationCheckV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: ImageOnlyValidationCheckName
    outcome: ImageOnlyValidationCheckOutcome


class ImageOnlyStructuralProfileV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    container: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    codec: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    pixel_format: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    frame_count: Literal[1] = 1


class ImageOnlyValidationResultV1(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    contract_name: Literal["ImageOnlyValidationResultV1"] = (
        "ImageOnlyValidationResultV1"
    )
    contract_version: Literal["1.0"] = "1.0"

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        extra: Any | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> ImageOnlyValidationResultV1:
        try:
            return super().model_validate(
                obj,
                strict=strict,
                extra=extra,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError:
            raise ImageOnlyValidationContractError() from None

    @classmethod
    def model_validate_strings(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        extra: Any | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> ImageOnlyValidationResultV1:
        if not isinstance(obj, Mapping):
            raise ImageOnlyValidationContractError()
        try:
            return super().model_validate_strings(
                obj,
                strict=strict,
                extra=extra,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError:
            raise ImageOnlyValidationContractError() from None
    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        extra: Any | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> ImageOnlyValidationResultV1:
        """Reject parser failures without exposing raw JSON diagnostics."""

        try:
            return super().model_validate_json(
                json_data,
                strict=strict,
                extra=extra,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError:
            raise ImageOnlyValidationContractError() from None

    status: ImageOnlyValidationStatus
    failure_code: ImageOnlyValidationFailureCode | None = None
    source_artifact_ref: str = Field(
        min_length=1,
        max_length=IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH,
        pattern=IMAGE_ONLY_ARTIFACT_REFERENCE_PATTERN,
    )
    source_status: ImageOnlySourceStatus
    digest_status: ImageOnlyDigestStatus
    source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    byte_count: int | None = Field(default=None, ge=0)
    structural_profile: ImageOnlyStructuralProfileV1 | None = None
    checks: tuple[ImageOnlyValidationCheckV1, ...]
    validator_identity: Literal["feat018-image-only-structural-validator-v1"] = (
        "feat018-image-only-structural-validator-v1"
    )
    policy_identity: Literal["feat018-image-only-structural-policy-v1"] = (
        "feat018-image-only-structural-policy-v1"
    )

    @field_validator('source_artifact_ref', mode='before')
    @classmethod
    def reject_unsafe_artifact_reference(cls, value: object) -> object:
        """Reject before Pydantic can place caller input in a diagnostic."""

        if not _is_safe_image_only_artifact_reference(value):
            raise ImageOnlyValidationContractError()
        return value

    @model_validator(mode="after")
    def validate_invariants(self) -> ImageOnlyValidationResultV1:
        _validate_image_only_check_invariants(self)
        _validate_image_only_source_invariants(self)
        _validate_image_only_terminal_invariants(self)
        return self


def _validate_image_only_check_invariants(result: ImageOnlyValidationResultV1) -> None:
    if not _is_safe_image_only_artifact_reference(result.source_artifact_ref):
        raise ValueError('invalid image-only artifact reference')
    names = tuple(check.name for check in result.checks)
    if names != IMAGE_ONLY_VALIDATION_CHECK_ORDER:
        raise ValueError("validation checks must use the complete canonical order")
    failed_count = sum(
        check.outcome is ImageOnlyValidationCheckOutcome.FAIL for check in result.checks
    )
    if result.status is ImageOnlyValidationStatus.PASS and failed_count:
        raise ValueError("PASS result cannot contain a failed check")
    if result.status is ImageOnlyValidationStatus.FAIL and failed_count != 1:
        raise ValueError("FAIL result requires exactly one failed check")


def _validate_image_only_source_invariants(result: ImageOnlyValidationResultV1) -> None:
    if result.source_status is ImageOnlySourceStatus.AVAILABLE:
        if result.digest_status is ImageOnlyDigestStatus.NOT_COMPUTED:
            raise ValueError("available source requires a computed digest")
        if result.source_sha256 is None or result.byte_count is None:
            raise ValueError("available source requires complete digest and byte count")
    elif (
        result.digest_status is not ImageOnlyDigestStatus.NOT_COMPUTED
        or result.source_sha256 is not None
        or result.byte_count is not None
    ):
        raise ValueError("unavailable source must not carry digest or byte-count facts")


def _validate_image_only_terminal_invariants(
    result: ImageOnlyValidationResultV1,
) -> None:
    if result.status is ImageOnlyValidationStatus.PASS:
        if result.failure_code is not None:
            raise ValueError("PASS result must not contain a failure code")
        complete_success = (
            result.source_status is ImageOnlySourceStatus.AVAILABLE
            and result.digest_status is ImageOnlyDigestStatus.MATCH
            and result.structural_profile is not None
            and all(
                check.outcome is ImageOnlyValidationCheckOutcome.PASS
                for check in result.checks
            )
        )
        if not complete_success:
            raise ValueError(
                "PASS result requires complete and consistent success facts"
            )
    elif result.failure_code is None or result.structural_profile is not None:
        raise ValueError("FAIL result requires a code and no partial success profile")

    if result.digest_status is ImageOnlyDigestStatus.MISMATCH:
        if (
            result.failure_code
            is not ImageOnlyValidationFailureCode.SOURCE_DIGEST_MISMATCH
        ):
            raise ValueError("digest mismatch requires SOURCE_DIGEST_MISMATCH")
    elif result.failure_code is ImageOnlyValidationFailureCode.SOURCE_DIGEST_MISMATCH:
        raise ValueError("SOURCE_DIGEST_MISMATCH requires digest mismatch facts")


class ImageOnlyArtifactVerificationV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        extra: Any | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> ImageOnlyArtifactVerificationV1:
        try:
            return super().model_validate(
                obj,
                strict=strict,
                extra=extra,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError:
            raise ImageOnlyValidationContractError() from None

    @classmethod
    def model_validate_strings(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        extra: Any | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> ImageOnlyArtifactVerificationV1:
        if not isinstance(obj, Mapping):
            raise ImageOnlyValidationContractError()
        try:
            return super().model_validate_strings(
                obj,
                strict=strict,
                extra=extra,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError:
            raise ImageOnlyValidationContractError() from None
    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        extra: Any | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> ImageOnlyArtifactVerificationV1:
        """Reject parser failures without exposing raw JSON diagnostics."""

        try:
            return super().model_validate_json(
                json_data,
                strict=strict,
                extra=extra,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError:
            raise ImageOnlyValidationContractError() from None

    status: ImageOnlyValidationStatus
    failure_code: ImageOnlyValidationFailureCode | None = None
    result: ImageOnlyValidationResultV1 | None = None

    @model_validator(mode="after")
    def validate_terminal_shape(self) -> ImageOnlyArtifactVerificationV1:
        if self.status is ImageOnlyValidationStatus.PASS:
            if self.failure_code is not None or self.result is None:
                raise ValueError("PASS verification requires one complete result")
        elif (
            self.failure_code
            not in {
                ImageOnlyValidationFailureCode.MALFORMED_RESULT,
                ImageOnlyValidationFailureCode.SERIALIZATION_HASH_MISMATCH,
            }
            or self.result is not None
        ):
            raise ValueError("FAIL verification requires one closed verification code")
        return self


def canonical_image_only_validation_bytes(result: ImageOnlyValidationResultV1) -> bytes:
    return result.model_dump_json(
        by_alias=False,
        exclude_none=False,
        indent=None,
    ).encode("utf-8")


def image_only_validation_artifact_sha256(result: ImageOnlyValidationResultV1) -> str:
    return sha256(canonical_image_only_validation_bytes(result)).hexdigest()


def verify_image_only_validation_artifact(
    payload: bytes,
    expected_sha256: str,
) -> ImageOnlyArtifactVerificationV1:
    expected_hash_is_valid = len(expected_sha256) == 64 and all(
        character in "0123456789abcdef" for character in expected_sha256
    )
    if not expected_hash_is_valid or sha256(payload).hexdigest() != expected_sha256:
        return ImageOnlyArtifactVerificationV1(
            status=ImageOnlyValidationStatus.FAIL,
            failure_code=ImageOnlyValidationFailureCode.SERIALIZATION_HASH_MISMATCH,
        )
    try:
        result = ImageOnlyValidationResultV1.model_validate_json(payload)
    except (ImageOnlyValidationContractError, ValidationError):
        return ImageOnlyArtifactVerificationV1(
            status=ImageOnlyValidationStatus.FAIL,
            failure_code=ImageOnlyValidationFailureCode.MALFORMED_RESULT,
        )
    if canonical_image_only_validation_bytes(result) != payload:
        return ImageOnlyArtifactVerificationV1(
            status=ImageOnlyValidationStatus.FAIL,
            failure_code=ImageOnlyValidationFailureCode.SERIALIZATION_HASH_MISMATCH,
        )
    return ImageOnlyArtifactVerificationV1(
        status=ImageOnlyValidationStatus.PASS,
        result=result,
    )


class MediaFixtureManifestEntryV1(BaseModel):
    """Fixture declaration. It intentionally contains no real child data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    image_ref: str = Field(min_length=1)
    audio_ref: str = Field(min_length=1)
    expected_decision: MediaDecision
    expected_reasons: tuple[MediaRecaptureReason, ...]
    image_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    audio_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    declared_image_width: int | None = Field(default=None, ge=1)
    declared_image_height: int | None = Field(default=None, ge=1)
    declared_audio_duration_seconds: float | None = Field(default=None, ge=0)
    declared_audio_sample_rate_hz: int | None = Field(default=None, ge=1)
    synthetic_data: Literal[True] = True


class MediaFixtureManifestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["MediaFixtureManifestV1"] = "MediaFixtureManifestV1"
    contract_version: Literal["1.0"] = "1.0"
    data_policy: Literal["synthetic-only"] = "synthetic-only"
    generator: str = Field(min_length=1)
    fixtures: tuple[MediaFixtureManifestEntryV1, ...] = Field(min_length=1)


def image_signals_contract(signals: ImageQualitySignals) -> ImageQualitySignalsV1:
    return ImageQualitySignalsV1(
        width=signals.width,
        height=signals.height,
        mean_luminance=signals.mean_luminance,
        luminance_standard_deviation=signals.luminance_standard_deviation,
        edge_strength=signals.edge_strength,
        border_ink_ratio=signals.border_ink_ratio,
    )


def audio_signals_contract(signals: AudioQualitySignals) -> AudioQualitySignalsV1:
    return AudioQualitySignalsV1(
        duration_seconds=signals.duration_seconds,
        sample_rate_hz=signals.sample_rate_hz,
        channels=signals.channels,
        rms=signals.rms,
        clipping_ratio=signals.clipping_ratio,
        speech_activity_ratio=signals.speech_activity_ratio,
        zero_crossing_ratio=signals.zero_crossing_ratio,
    )


def media_validation_contract(
    assessment: MediaQualityAssessment,
    image: SourceMediaReferenceV1,
    audio: SourceMediaReferenceV1,
) -> MediaValidationResultV1:
    return MediaValidationResultV1(
        decision=assessment.decision,
        recapture_reasons=assessment.reasons,
        image=image,
        audio=audio,
        image_signals=image_signals_contract(assessment.image_signals),
        audio_signals=audio_signals_contract(assessment.audio_signals),
        recapture_message=_recapture_message(assessment.reasons),
        validator_policy_version=assessment.policy_version,
    )


def _recapture_message(reasons: tuple[MediaRecaptureReason, ...]) -> str:
    if not reasons:
        return "Media quality passed"
    messages = {
        MediaRecaptureReason.IMAGE_UNREADABLE: "Retake the drawing image",
        MediaRecaptureReason.IMAGE_DIMENSIONS_TOO_SMALL: "Retake the drawing at a larger size",
        MediaRecaptureReason.IMAGE_TOO_DARK: "Retake the drawing with more light",
        MediaRecaptureReason.IMAGE_LOW_CONTRAST: "Retake the drawing with clearer contrast",
        MediaRecaptureReason.IMAGE_BLURRY: "Retake the drawing without camera movement",
        MediaRecaptureReason.IMAGE_FRAMING_RISK: "Retake the drawing with all edges visible",
        MediaRecaptureReason.AUDIO_UNREADABLE: "Record the narration again",
        MediaRecaptureReason.AUDIO_DURATION_OUT_OF_RANGE: (
            "Record a narration between 0.5 and 180 seconds"
        ),
        MediaRecaptureReason.AUDIO_SILENT: "Record narration with audible speech",
        MediaRecaptureReason.AUDIO_NO_SPEECH_SIGNAL: "Record narration with a clear speech signal",
        MediaRecaptureReason.AUDIO_CLIPPING: "Record narration below the microphone clipping level",
    }
    return "; ".join(messages[reason] for reason in reasons)
