"""Port for the FEAT-018 P2-T1 image-decoder boundary (D1 section 4).

Operates on in-memory byte snapshots only; no filesystem path, no `av` import. The only
module permitted to import `av` is the infrastructure adapter that implements this port.
"""

from __future__ import annotations

from typing import Protocol

from sketch2life.domain.understanding.image_admission import (
    DecodedFrameSignals,
    ImageMetadataSignals,
)


class ImageDecodeSourceError(Exception):
    """The decoder determined the snapshot bytes are corrupt, truncated, or otherwise
    unreadable as image data. The application service maps this to
    `INVALID_SOURCE`/`CORRUPT_OR_TRUNCATED`."""


class ImageDecodeProcessingError(Exception):
    """Any decoder-side failure that is not a source-data problem (D1 section 4 exception
    mapping: "any other exception maps to PROCESSING_FAILURE/DECODER_ERROR"). The application
    service maps this to `PROCESSING_FAILURE`/`DECODER_ERROR`."""


class ImageDecodeTimeoutError(Exception):
    """Reserved for a future killable-worker decoder (D1 section 8). The in-process PyAV
    adapter never raises this — a decode inside `libavcodec` does not yield to Python, so no
    in-process mechanism can enforce a timeout. Only a test stub raises it, to prove the
    mapping to `PROCESSING_FAILURE`/`DECODER_TIMEOUT` without claiming runtime protection."""


class ImageDecoderPort(Protocol):
    """Explicitly injected at construction; never a module-level default."""

    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        """Header-only inspection of the given snapshot. Must not decode pixel data.

        Returns `None` if the container cannot be opened or has no video stream — both
        collapse to the same "not an image" signal (D1 section 0, finding F-C). Never raises;
        an unopenable snapshot is a normal, expected outcome here, not a decoder failure.
        """
        ...

    def probe_frame_count(self, snapshot: bytes) -> int:
        """Bounded packet-only probe: counts non-empty compressed packets without decoding
        any of them, stopping as soon as more than one is confirmed. The return value is not
        an exact frame count for multi-frame inputs — only whether it exceeds one matters.

        Raises `ImageDecodeSourceError`, `ImageDecodeProcessingError`, or (from a stub only)
        `ImageDecodeTimeoutError` on failure.
        """
        ...

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        """Decode exactly one frame from the snapshot and return its own dimensions/format,
        never the pixel buffer itself — so there is no decoded-frame reference for a caller
        to retain past this call.

        Raises `ImageDecodeSourceError` if the source is corrupt/truncated or produces no
        frame, `ImageDecodeProcessingError` for any other decoder-side failure, or (from a
        stub only) `ImageDecodeTimeoutError`.
        """
        ...
