"""Pure policy for the FEAT-018 P2-T1 image-admission boundary.

Additive and isolated from FEAT-003: this module owns no FEAT-003 contract, validator,
inspector, policy or fixture. It implements the decision logic specified in
`evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` (D1) sections 2 and 3. All types here are
stdlib-only; no pydantic or other framework import is permitted in `domain/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AdmissionOutcome(StrEnum):
    """D1 section 2. `ADMITTED` grants nothing beyond eligibility for further validation."""

    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID_SOURCE = "INVALID_SOURCE"
    PROCESSING_FAILURE = "PROCESSING_FAILURE"


class AdmissionReason(StrEnum):
    """D1 section 2. Every non-`ADMITTED` outcome carries exactly one of these."""

    FILE_BYTES_EXCEEDED = "FILE_BYTES_EXCEEDED"
    PIXEL_BUDGET_EXCEEDED = "PIXEL_BUDGET_EXCEEDED"
    LONGEST_EDGE_EXCEEDED = "LONGEST_EDGE_EXCEEDED"
    MULTIPLE_FRAMES = "MULTIPLE_FRAMES"
    UNSUPPORTED_CONTAINER = "UNSUPPORTED_CONTAINER"
    UNSUPPORTED_CODEC = "UNSUPPORTED_CODEC"
    UNSUPPORTED_PIXEL_FORMAT = "UNSUPPORTED_PIXEL_FORMAT"
    NOT_AN_IMAGE = "NOT_AN_IMAGE"
    CORRUPT_OR_TRUNCATED = "CORRUPT_OR_TRUNCATED"
    MISSING_SOURCE = "MISSING_SOURCE"
    DECODER_ERROR = "DECODER_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    # Reserved for a future killable worker (D1 section 8). The in-process decoder never
    # produces this reason; only a stub can, to prove the mapping exists.
    DECODER_TIMEOUT = "DECODER_TIMEOUT"


_OUTCOME_BY_REASON: dict[AdmissionReason, AdmissionOutcome] = {
    AdmissionReason.FILE_BYTES_EXCEEDED: AdmissionOutcome.REJECTED,
    AdmissionReason.PIXEL_BUDGET_EXCEEDED: AdmissionOutcome.REJECTED,
    AdmissionReason.LONGEST_EDGE_EXCEEDED: AdmissionOutcome.REJECTED,
    AdmissionReason.MULTIPLE_FRAMES: AdmissionOutcome.REJECTED,
    AdmissionReason.UNSUPPORTED_CONTAINER: AdmissionOutcome.UNSUPPORTED,
    AdmissionReason.UNSUPPORTED_CODEC: AdmissionOutcome.UNSUPPORTED,
    AdmissionReason.UNSUPPORTED_PIXEL_FORMAT: AdmissionOutcome.UNSUPPORTED,
    AdmissionReason.NOT_AN_IMAGE: AdmissionOutcome.INVALID_SOURCE,
    AdmissionReason.CORRUPT_OR_TRUNCATED: AdmissionOutcome.INVALID_SOURCE,
    AdmissionReason.MISSING_SOURCE: AdmissionOutcome.INVALID_SOURCE,
    AdmissionReason.DECODER_ERROR: AdmissionOutcome.PROCESSING_FAILURE,
    AdmissionReason.INTERNAL_ERROR: AdmissionOutcome.PROCESSING_FAILURE,
    AdmissionReason.DECODER_TIMEOUT: AdmissionOutcome.PROCESSING_FAILURE,
}


def outcome_for_reason(reason: AdmissionReason) -> AdmissionOutcome:
    return _OUTCOME_BY_REASON[reason]


@dataclass(frozen=True, slots=True)
class Feat018AdmissionLimits:
    """D1 section 5 trial configuration (owner decision U4, locked).

    `max_longest_edge` is an independent dimension guard, not an aspect-ratio rule: it bounds
    the single largest declared dimension regardless of total pixel count. The pixel-format
    allowlist is deliberately narrow (owner decision U2): only measured profiles are accepted;
    widening it requires a new probe, not a config change alone.
    """

    max_file_bytes: int = 5_000_000
    max_pixels: int = 4_000_000
    max_longest_edge: int = 4096
    max_frames: int = 1
    allowed_containers: frozenset[str] = frozenset({"png_pipe", "jpeg_pipe"})
    allowed_codecs: frozenset[str] = frozenset({"png", "mjpeg"})
    allowed_pixel_formats: frozenset[str] = frozenset(
        {"rgb24", "rgba", "gray", "pal8", "monob", "yuvj420p"}
    )


@dataclass(frozen=True, slots=True)
class ImageMetadataSignals:
    """Header-only signals read from the snapshot before any pixel decode (D1 section 3
    step 5). `pixel_format` is `None` exactly when the codec's format could not be resolved
    (a corrupt/truncated source), independent of whether `width`/`height` are also invalid.
    """

    container: str
    codec: str
    pixel_format: str | None
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class DecodedFrameSignals:
    """The decoded frame's own dimensions/format, for the step-8 cross-check. Deliberately
    excludes pixel data: this component never returns a pixel buffer across the port boundary,
    so there is no decoded-frame reference for a caller to retain past the cross-check."""

    width: int
    height: int
    pixel_format: str


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    """The pure decision result. `digest` is populated whenever the complete source was read
    (every outcome except `FILE_BYTES_EXCEEDED` and `MISSING_SOURCE`) and is never a prefix or
    fabricated value. `metadata` is populated once step 5 has been reached, regardless of
    whether it ultimately passed."""

    outcome: AdmissionOutcome
    reason: AdmissionReason | None
    digest: str | None
    metadata: ImageMetadataSignals | None


def evaluate_metadata(
    signals: ImageMetadataSignals | None, limits: Feat018AdmissionLimits
) -> AdmissionReason | None:
    """D1 section 3 step 5, in the exact specified order. `signals is None` represents an
    unopenable source or a container with no video stream (both collapse to `NOT_AN_IMAGE`,
    matching the port's `read_metadata` contract). Returns the failing reason, or `None` to
    proceed to the frame-count probe.
    """

    if signals is None:
        return AdmissionReason.NOT_AN_IMAGE
    if signals.container not in limits.allowed_containers:
        return AdmissionReason.UNSUPPORTED_CONTAINER
    if signals.pixel_format is None:
        return AdmissionReason.CORRUPT_OR_TRUNCATED
    if signals.width < 1 or signals.height < 1:
        return AdmissionReason.CORRUPT_OR_TRUNCATED
    if signals.codec not in limits.allowed_codecs:
        return AdmissionReason.UNSUPPORTED_CODEC
    if signals.pixel_format not in limits.allowed_pixel_formats:
        return AdmissionReason.UNSUPPORTED_PIXEL_FORMAT
    if signals.width * signals.height > limits.max_pixels:
        return AdmissionReason.PIXEL_BUDGET_EXCEEDED
    if max(signals.width, signals.height) > limits.max_longest_edge:
        return AdmissionReason.LONGEST_EDGE_EXCEEDED
    return None


def evaluate_frame_count(
    frame_count: int, limits: Feat018AdmissionLimits
) -> AdmissionReason | None:
    """D1 section 3 step 6. `frame_count` is a bounded probe result (never an exact count for
    inputs above the limit); only whether it exceeds `max_frames` matters."""

    if frame_count > limits.max_frames:
        return AdmissionReason.MULTIPLE_FRAMES
    return None


def evaluate_cross_check(
    metadata: ImageMetadataSignals, decoded: DecodedFrameSignals
) -> AdmissionReason | None:
    """D1 section 3 step 8. A decoder that produced dimensions or a format different from
    what metadata inspection admitted must not be trusted; this is what makes the pixel/edge
    budgets meaningful rather than merely a header-declared promise."""

    if (decoded.width, decoded.height, decoded.pixel_format) != (
        metadata.width,
        metadata.height,
        metadata.pixel_format,
    ):
        return AdmissionReason.CORRUPT_OR_TRUNCATED
    return None


_GUIDANCE: dict[AdmissionReason, str] = {
    AdmissionReason.FILE_BYTES_EXCEEDED: "Choose or export a smaller file",
    AdmissionReason.PIXEL_BUDGET_EXCEEDED: "Export the image at smaller dimensions",
    AdmissionReason.LONGEST_EDGE_EXCEEDED: "Export the image at smaller dimensions",
    AdmissionReason.MULTIPLE_FRAMES: "Supply a single static image, not an animation",
    AdmissionReason.UNSUPPORTED_CONTAINER: "Use a supported JPEG or PNG image",
    AdmissionReason.UNSUPPORTED_CODEC: "Use a supported JPEG or PNG image",
    AdmissionReason.UNSUPPORTED_PIXEL_FORMAT: "Use a supported JPEG or PNG image",
    AdmissionReason.NOT_AN_IMAGE: "Choose or export a valid image file",
    AdmissionReason.CORRUPT_OR_TRUNCATED: "Choose or export a valid image file",
    AdmissionReason.MISSING_SOURCE: "Choose a file",
    AdmissionReason.DECODER_ERROR: "The system could not process this image; try again",
    AdmissionReason.INTERNAL_ERROR: "The system could not process this image; try again",
    AdmissionReason.DECODER_TIMEOUT: (
        "The system could not process this image in time; try again"
    ),
}


def admission_message(reason: AdmissionReason | None) -> str:
    """D1 section 2 "Guidance" column. `reason is None` means `ADMITTED`."""

    if reason is None:
        return "Image admitted"
    return _GUIDANCE[reason]
