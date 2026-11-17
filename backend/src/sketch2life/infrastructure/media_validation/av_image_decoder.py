"""The only module in this codebase importing `av`. FEAT-018 P2-T1 D2 image decoder.

Implements `ImageDecoderPort` (D1 section 4) using PyAV, operating exclusively on in-memory
byte snapshots — never a filesystem path. Never registered as a module-level default; the
application layer must construct and inject this explicitly.
"""

from __future__ import annotations

import io

import av
import av.error

from sketch2life.application.ports.image_decoder import (
    ImageDecodeProcessingError,
    ImageDecodeSourceError,
)
from sketch2life.domain.understanding.image_admission import (
    DecodedFrameSignals,
    ImageMetadataSignals,
)

# Bounded packet probe (D1 section 0 finding F-D / section 8): stop counting compressed
# packets as soon as more than one non-empty packet is confirmed. Never an exact count.
_MULTIPLE_FRAMES_THRESHOLD = 2


class AvImageDecoder:
    """PyAV-backed `ImageDecoderPort` implementation."""

    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        try:
            with av.open(io.BytesIO(snapshot), mode="r") as container:
                video_streams = container.streams.video
                if not video_streams:
                    return None
                codec_context = video_streams[0].codec_context
                pixel_format = (
                    codec_context.format.name if codec_context.format is not None else None
                )
                return ImageMetadataSignals(
                    container=container.format.name,
                    codec=codec_context.name,
                    pixel_format=pixel_format,
                    width=codec_context.width,
                    height=codec_context.height,
                )
        except av.error.FFmpegError:
            return None

    def probe_frame_count(self, snapshot: bytes) -> int:
        try:
            with av.open(io.BytesIO(snapshot), mode="r") as container:
                seen = 0
                for packet in container.demux(video=0):
                    if packet.size == 0:
                        # The flush sentinel every stream emits at end-of-demux; it is not a
                        # frame and counting it would misclassify every single-frame input.
                        continue
                    seen += 1
                    if seen >= _MULTIPLE_FRAMES_THRESHOLD:
                        break
                return seen
        except av.error.FFmpegError as exc:
            raise ImageDecodeSourceError(str(exc)) from exc
        except Exception as exc:
            raise ImageDecodeProcessingError(str(exc)) from exc

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        try:
            with av.open(io.BytesIO(snapshot), mode="r") as container:
                frame = next(container.decode(video=0), None)
        except av.error.FFmpegError as exc:
            raise ImageDecodeSourceError(str(exc)) from exc
        except Exception as exc:
            raise ImageDecodeProcessingError(str(exc)) from exc

        # The decoded frame's pixel buffer is deliberately never returned across this port
        # boundary — only these three scalar signals are. `frame` (and any pixel data it
        # holds) goes out of scope and is released when this function returns.
        if frame is None:
            raise ImageDecodeSourceError("decoder produced no frame")
        pixel_format = frame.format.name if frame.format is not None else None
        if pixel_format is None:
            raise ImageDecodeSourceError("decoded frame has no resolvable pixel format")
        return DecodedFrameSignals(
            width=frame.width, height=frame.height, pixel_format=pixel_format
        )
