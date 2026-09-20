"""Standalone P2-T1 use case; it has no HTTP, queue, database, or model dependency."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal, Protocol

from sketch2life.application.ports.image_decoder import (
    ImageDecodeProcessingError,
    ImageDecoderPort,
    ImageDecodeSourceError,
    ImageDecodeTimeoutError,
)
from sketch2life.contracts.schemas.media_validation import (
    IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE,
    IMAGE_ONLY_VALIDATION_CHECK_ORDER,
    ImageOnlyArtifactReferenceV1,
    ImageOnlyDigestStatus,
    ImageOnlySourceStatus,
    ImageOnlyStructuralProfileV1,
    ImageOnlyValidationCheckName,
    ImageOnlyValidationCheckOutcome,
    ImageOnlyValidationCheckV1,
    ImageOnlyValidationFailureCode,
    ImageOnlyValidationResultV1,
    ImageOnlyValidationStatus,
    MediaValidationResultV1,
    SourceMediaReferenceV1,
    media_validation_contract,
    try_create_image_only_artifact_reference,
)
from sketch2life.domain.understanding.image_admission import (
    AdmissionReason,
    ImageMetadataSignals,
)
from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageOnlyStructuralPolicy,
    ImageQualitySignals,
    MediaQualityPolicy,
    assess_media,
    evaluate_image_only_cross_check,
    evaluate_image_only_frame_count,
    evaluate_image_only_metadata,
)

_HASH_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class MediaValidationRequest:
    image_path: Path
    audio_path: Path
    image_artifact_ref: str
    audio_artifact_ref: str


class MediaSignalInspector(Protocol):
    """Port for reading media at the standalone component boundary."""

    def inspect_image(self, path: Path) -> ImageQualitySignals: ...

    def inspect_audio(self, path: Path) -> AudioQualitySignals: ...


class DeterministicMediaValidator:
    def __init__(
        self, inspector: MediaSignalInspector, policy: MediaQualityPolicy | None = None
    ) -> None:
        self._inspector = inspector
        self._policy = policy or MediaQualityPolicy()

    def validate(self, request: MediaValidationRequest) -> MediaValidationResultV1:
        image = _source_reference(request.image_path, request.image_artifact_ref)
        audio = _source_reference(request.audio_path, request.audio_artifact_ref)
        assessment = assess_media(
            self._inspector.inspect_image(request.image_path),
            self._inspector.inspect_audio(request.audio_path),
            self._policy,
        )
        return media_validation_contract(assessment, image, audio)


@dataclass(frozen=True, slots=True)
class ImageOnlyValidationRequest:
    image_path: Path
    image_artifact_ref: str
    expected_source_sha256: str


class ImageOnlyStructuralMediaValidator:
    def __init__(
        self,
        decoder: ImageDecoderPort,
        policy: ImageOnlyStructuralPolicy | None = None,
    ) -> None:
        self._decoder = decoder
        self._policy = policy or ImageOnlyStructuralPolicy()

    def validate(
        self, request: ImageOnlyValidationRequest
    ) -> ImageOnlyValidationResultV1:
        if not isinstance(request, ImageOnlyValidationRequest):
            return _invalid_image_only_request_failure()
        reference: ImageOnlyArtifactReferenceV1 | None = (
            try_create_image_only_artifact_reference(request.image_artifact_ref)
        )
        if reference is None:
            return _invalid_image_only_request_failure()
        request = ImageOnlyValidationRequest(
            image_path=request.image_path,
            image_artifact_ref=reference.value,
            expected_source_sha256=request.expected_source_sha256,
        )
        checks = _new_image_only_checks()
        try:
            snapshot, exceeded = _read_bounded_snapshot(
                request.image_path,
                self._policy.limits.max_file_bytes,
            )
        except FileNotFoundError:
            return _image_only_failure(
                request,
                ImageOnlyValidationFailureCode.MISSING_SOURCE,
                ImageOnlySourceStatus.MISSING,
                checks,
                ImageOnlyValidationCheckName.SOURCE_READ,
            )
        except OSError:
            return _image_only_failure(
                request,
                ImageOnlyValidationFailureCode.UNREADABLE_IMAGE,
                ImageOnlySourceStatus.UNREADABLE,
                checks,
                ImageOnlyValidationCheckName.SOURCE_READ,
            )
        if exceeded:
            return _image_only_failure(
                request,
                ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
                ImageOnlySourceStatus.TOO_LARGE,
                checks,
                ImageOnlyValidationCheckName.SOURCE_READ,
            )

        checks[ImageOnlyValidationCheckName.SOURCE_READ] = (
            ImageOnlyValidationCheckOutcome.PASS
        )
        source_sha256 = sha256(snapshot).hexdigest()
        byte_count = len(snapshot)
        if source_sha256 != request.expected_source_sha256:
            return _image_only_failure(
                request,
                ImageOnlyValidationFailureCode.SOURCE_DIGEST_MISMATCH,
                ImageOnlySourceStatus.AVAILABLE,
                checks,
                ImageOnlyValidationCheckName.SOURCE_DIGEST,
                digest_status=ImageOnlyDigestStatus.MISMATCH,
                source_sha256=source_sha256,
                byte_count=byte_count,
            )
        checks[ImageOnlyValidationCheckName.SOURCE_DIGEST] = (
            ImageOnlyValidationCheckOutcome.PASS
        )
        return self._validate_snapshot(
            request, snapshot, source_sha256, byte_count, checks
        )

    def _validate_snapshot(
        self,
        request: ImageOnlyValidationRequest,
        snapshot: bytes,
        source_sha256: str,
        byte_count: int,
        checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
    ) -> ImageOnlyValidationResultV1:
        try:
            metadata = self._decoder.read_metadata(snapshot)
        except Exception:  # noqa: BLE001 - failure output is intentionally sanitized
            return _available_image_only_failure(
                request,
                ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
                checks,
                ImageOnlyValidationCheckName.D2_METADATA,
                source_sha256,
                byte_count,
            )
        metadata_reason = evaluate_image_only_metadata(metadata, self._policy)
        if metadata_reason is not None:
            failure_check = _metadata_failure_check(metadata_reason)
            _record_metadata_checks_before_failure(checks, failure_check)
            return _available_image_only_failure(
                request,
                _image_only_failure_code(metadata_reason),
                checks,
                failure_check,
                source_sha256,
                byte_count,
            )
        if metadata is None:
            return _available_image_only_failure(
                request,
                ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
                checks,
                ImageOnlyValidationCheckName.D2_METADATA,
                source_sha256,
                byte_count,
            )
        for check_name in (
            ImageOnlyValidationCheckName.D2_METADATA,
            ImageOnlyValidationCheckName.DIMENSIONS,
            ImageOnlyValidationCheckName.PIXEL_BUDGET,
            ImageOnlyValidationCheckName.LONGEST_EDGE,
        ):
            checks[check_name] = ImageOnlyValidationCheckOutcome.PASS
        return self._validate_frames(
            request,
            snapshot,
            metadata,
            source_sha256,
            byte_count,
            checks,
        )

    def _validate_frames(
        self,
        request: ImageOnlyValidationRequest,
        snapshot: bytes,
        metadata: ImageMetadataSignals,
        source_sha256: str,
        byte_count: int,
        checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
    ) -> ImageOnlyValidationResultV1:
        try:
            frame_count = self._decoder.probe_frame_count(snapshot)
        except ImageDecodeSourceError:
            code = ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED
        except (ImageDecodeProcessingError, ImageDecodeTimeoutError):
            code = ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION
        except Exception:  # noqa: BLE001 - failure output is intentionally sanitized
            code = ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION
        else:
            frame_reason = evaluate_image_only_frame_count(frame_count, self._policy)
            if frame_reason is None and frame_count == 1:
                checks[ImageOnlyValidationCheckName.FRAME_COUNT] = (
                    ImageOnlyValidationCheckOutcome.PASS
                )
                return self._decode_frame(
                    request,
                    snapshot,
                    metadata,
                    source_sha256,
                    byte_count,
                    checks,
                )
            code = ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED
        return _available_image_only_failure(
            request,
            code,
            checks,
            ImageOnlyValidationCheckName.FRAME_COUNT,
            source_sha256,
            byte_count,
        )

    def _decode_frame(
        self,
        request: ImageOnlyValidationRequest,
        snapshot: bytes,
        metadata: ImageMetadataSignals,
        source_sha256: str,
        byte_count: int,
        checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
    ) -> ImageOnlyValidationResultV1:
        try:
            decoded = self._decoder.decode_one_frame(snapshot)
        except ImageDecodeSourceError:
            code = ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED
        except (ImageDecodeProcessingError, ImageDecodeTimeoutError):
            code = ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION
        except Exception:  # noqa: BLE001 - failure output is intentionally sanitized
            code = ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION
        else:
            cross_check_reason = evaluate_image_only_cross_check(metadata, decoded)
            if cross_check_reason is None:
                checks[ImageOnlyValidationCheckName.DECODE_INTEGRITY] = (
                    ImageOnlyValidationCheckOutcome.PASS
                )
                checks[ImageOnlyValidationCheckName.STRUCTURAL_POLICY] = (
                    ImageOnlyValidationCheckOutcome.PASS
                )
                return _image_only_success(
                    request,
                    metadata,
                    source_sha256,
                    byte_count,
                    checks,
                )
            code = ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED
        return _available_image_only_failure(
            request,
            code,
            checks,
            ImageOnlyValidationCheckName.DECODE_INTEGRITY,
            source_sha256,
            byte_count,
        )


def _new_image_only_checks() -> dict[
    ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome
]:
    return {
        name: ImageOnlyValidationCheckOutcome.NOT_RUN
        for name in IMAGE_ONLY_VALIDATION_CHECK_ORDER
    }


def _image_only_check_contracts(
    checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
) -> tuple[ImageOnlyValidationCheckV1, ...]:
    return tuple(
        ImageOnlyValidationCheckV1(name=name, outcome=checks[name])
        for name in IMAGE_ONLY_VALIDATION_CHECK_ORDER
    )


def _invalid_image_only_request_failure() -> ImageOnlyValidationResultV1:
    '''Return a stable failure without retaining any rejected input reference.'''

    checks = _new_image_only_checks()
    checks[ImageOnlyValidationCheckName.SOURCE_READ] = (
        ImageOnlyValidationCheckOutcome.FAIL
    )
    return ImageOnlyValidationResultV1(
        status=ImageOnlyValidationStatus.FAIL,
        failure_code=ImageOnlyValidationFailureCode.MALFORMED_RESULT,
        source_artifact_ref=IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE,
        source_status=ImageOnlySourceStatus.MISSING,
        digest_status=ImageOnlyDigestStatus.NOT_COMPUTED,
        source_sha256=None,
        byte_count=None,
        structural_profile=None,
        checks=_image_only_check_contracts(checks),
    )


def _image_only_failure(
    request: ImageOnlyValidationRequest,
    code: ImageOnlyValidationFailureCode,
    source_status: ImageOnlySourceStatus,
    checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
    failed_check: ImageOnlyValidationCheckName,
    *,
    digest_status: ImageOnlyDigestStatus = ImageOnlyDigestStatus.NOT_COMPUTED,
    source_sha256: str | None = None,
    byte_count: int | None = None,
) -> ImageOnlyValidationResultV1:
    checks[failed_check] = ImageOnlyValidationCheckOutcome.FAIL
    return ImageOnlyValidationResultV1(
        status=ImageOnlyValidationStatus.FAIL,
        failure_code=code,
        source_artifact_ref=request.image_artifact_ref,
        source_status=source_status,
        digest_status=digest_status,
        source_sha256=source_sha256,
        byte_count=byte_count,
        structural_profile=None,
        checks=_image_only_check_contracts(checks),
    )


def _available_image_only_failure(
    request: ImageOnlyValidationRequest,
    code: ImageOnlyValidationFailureCode,
    checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
    failed_check: ImageOnlyValidationCheckName,
    source_sha256: str,
    byte_count: int,
) -> ImageOnlyValidationResultV1:
    return _image_only_failure(
        request,
        code,
        ImageOnlySourceStatus.AVAILABLE,
        checks,
        failed_check,
        digest_status=ImageOnlyDigestStatus.MATCH,
        source_sha256=source_sha256,
        byte_count=byte_count,
    )


def _image_only_success(
    request: ImageOnlyValidationRequest,
    metadata: ImageMetadataSignals,
    source_sha256: str,
    byte_count: int,
    checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
) -> ImageOnlyValidationResultV1:
    if metadata.pixel_format is None:
        raise ValueError("validated metadata must have a pixel format")
    return ImageOnlyValidationResultV1(
        status=ImageOnlyValidationStatus.PASS,
        failure_code=None,
        source_artifact_ref=request.image_artifact_ref,
        source_status=ImageOnlySourceStatus.AVAILABLE,
        digest_status=ImageOnlyDigestStatus.MATCH,
        source_sha256=source_sha256,
        byte_count=byte_count,
        structural_profile=ImageOnlyStructuralProfileV1(
            container=metadata.container,
            codec=metadata.codec,
            pixel_format=metadata.pixel_format,
            width=metadata.width,
            height=metadata.height,
            frame_count=1,
        ),
        checks=_image_only_check_contracts(checks),
    )


def _metadata_failure_check(reason: AdmissionReason) -> ImageOnlyValidationCheckName:
    if reason is AdmissionReason.PIXEL_BUDGET_EXCEEDED:
        return ImageOnlyValidationCheckName.PIXEL_BUDGET
    if reason is AdmissionReason.LONGEST_EDGE_EXCEEDED:
        return ImageOnlyValidationCheckName.LONGEST_EDGE
    return ImageOnlyValidationCheckName.D2_METADATA


def _record_metadata_checks_before_failure(
    checks: dict[ImageOnlyValidationCheckName, ImageOnlyValidationCheckOutcome],
    failed_check: ImageOnlyValidationCheckName,
) -> None:
    if failed_check in {
        ImageOnlyValidationCheckName.PIXEL_BUDGET,
        ImageOnlyValidationCheckName.LONGEST_EDGE,
    }:
        checks[ImageOnlyValidationCheckName.D2_METADATA] = (
            ImageOnlyValidationCheckOutcome.PASS
        )
        checks[ImageOnlyValidationCheckName.DIMENSIONS] = (
            ImageOnlyValidationCheckOutcome.PASS
        )
    if failed_check is ImageOnlyValidationCheckName.LONGEST_EDGE:
        checks[ImageOnlyValidationCheckName.PIXEL_BUDGET] = (
            ImageOnlyValidationCheckOutcome.PASS
        )


_IMAGE_ONLY_FAILURE_BY_ADMISSION_REASON: dict[
    AdmissionReason, ImageOnlyValidationFailureCode
] = {
    AdmissionReason.FILE_BYTES_EXCEEDED: ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
    AdmissionReason.PIXEL_BUDGET_EXCEEDED: ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
    AdmissionReason.LONGEST_EDGE_EXCEEDED: ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
    AdmissionReason.MULTIPLE_FRAMES: ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED,
    AdmissionReason.UNSUPPORTED_CONTAINER: ImageOnlyValidationFailureCode.UNSUPPORTED_CONTAINER,
    AdmissionReason.UNSUPPORTED_CODEC: ImageOnlyValidationFailureCode.UNSUPPORTED_CODEC,
    AdmissionReason.UNSUPPORTED_PIXEL_FORMAT: (
        ImageOnlyValidationFailureCode.UNSUPPORTED_PIXEL_FORMAT
    ),
    AdmissionReason.NOT_AN_IMAGE: ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED,
    AdmissionReason.CORRUPT_OR_TRUNCATED: (
        ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED
    ),
    AdmissionReason.MISSING_SOURCE: ImageOnlyValidationFailureCode.MISSING_SOURCE,
    AdmissionReason.DECODER_ERROR: ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
    AdmissionReason.INTERNAL_ERROR: ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
    AdmissionReason.DECODER_TIMEOUT: ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
}


def _image_only_failure_code(reason: AdmissionReason) -> ImageOnlyValidationFailureCode:
    return _IMAGE_ONLY_FAILURE_BY_ADMISSION_REASON[reason]


def _read_bounded_snapshot(path: Path, limit: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    total = 0
    with path.open("rb") as source:
        while total <= limit:
            chunk = source.read(min(_HASH_CHUNK_BYTES, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
    if total > limit:
        return b"", True
    return b"".join(chunks), False


def _source_reference(path: Path, artifact_ref: str) -> SourceMediaReferenceV1:
    try:
        digest = _file_digest(path)
    except OSError:
        status: Literal["MISSING", "UNREADABLE"] = (
            "MISSING" if not path.exists() else "UNREADABLE"
        )
        return SourceMediaReferenceV1(
            artifact_ref=artifact_ref,
            sha256=None,
            source_status=status,
        )
    return SourceMediaReferenceV1(
        artifact_ref=artifact_ref,
        sha256=digest,
        source_status="AVAILABLE",
    )


def _file_digest(path: Path) -> str:
    """Hash the complete source without holding it in memory."""

    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()
