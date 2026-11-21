"""Audio duration from the stored bytes, without a decoder (goal v3 T-2c; SRS l.982, l.1942).

``POST /v1/story-runs/{id}/idea`` accepts at most two minutes of audio (BR-23, l.982). The length
is read from the container header, never from a client field:

* WAV (``audio/wav``): the standard ``wave`` module; only PCM is readable, and the data chunk
  must fit in the file (a truncated or inflated header is a content mismatch);
* MP4 and M4A (``audio/mp4``): the ``mvhd`` box of ``moov``. The parser reads box headers only
  (never box bodies other than ``mvhd``), handles ``moov`` after ``mdat``, 64-bit box sizes and a
  size of 0 ("to the end of the enclosing box"), accepts ``mvhd`` versions 0 and 1, and refuses
  a timescale of 0, an "unknown duration" marker, a box that leaves its container, and more than
  ``_MAX_BOXES`` boxes in one level.

Every failure is ``AudioDurationError`` (the route answers 422 ``UPLOAD_CONTENT_MISMATCH``). The
module decodes nothing, so hostile bytes cost at most one pass over box headers.
"""

from __future__ import annotations

import io
import struct
import wave
from typing import Final

WAV_MEDIA_TYPE: Final = "audio/wav"
MP4_MEDIA_TYPE: Final = "audio/mp4"
SUPPORTED_AUDIO_MEDIA_TYPES: Final = frozenset({WAV_MEDIA_TYPE, MP4_MEDIA_TYPE})

_MAX_BOXES: Final = 4096
_MAX_DURATION_MS: Final = 2**40  # far above any limit; keeps the arithmetic obviously bounded


class AudioDurationError(ValueError):
    """The bytes are not a readable audio file of the declared type."""

    code = "UPLOAD_CONTENT_MISMATCH"


def audio_duration_ms(data: bytes, *, media_type: str) -> int:
    """Duration in whole milliseconds (rounded up), at least 1, else ``AudioDurationError``."""
    if media_type == WAV_MEDIA_TYPE:
        duration = _wav_duration_ms(data)
    elif media_type == MP4_MEDIA_TYPE:
        duration = _mp4_duration_ms(data)
    else:
        raise AudioDurationError("unsupported audio type")
    if duration < 1 or duration > _MAX_DURATION_MS:
        raise AudioDurationError("duration out of range")
    return duration


def _ceil_div(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


def _wav_duration_ms(data: bytes) -> int:
    try:
        with wave.open(io.BytesIO(data), "rb") as reader:
            frames = reader.getnframes()
            rate = reader.getframerate()
            frame_size = reader.getsampwidth() * reader.getnchannels()
    except (wave.Error, EOFError, struct.error, ValueError, OverflowError):
        raise AudioDurationError("not a PCM WAV file") from None
    if rate <= 0 or frame_size <= 0 or frames <= 0:
        raise AudioDurationError("empty or invalid WAV header")
    if frames * frame_size > len(data):
        raise AudioDurationError("the WAV data chunk is larger than the file")
    return _ceil_div(frames * 1000, rate)


def _boxes(data: bytes, start: int, end: int) -> list[tuple[bytes, int, int]]:
    """Box ``(type, body_start, box_end)`` of one level; headers only, bounded."""
    found: list[tuple[bytes, int, int]] = []
    position = start
    while position < end:
        if len(found) >= _MAX_BOXES:
            raise AudioDurationError("too many boxes")
        if end - position < 8:
            raise AudioDurationError("truncated box header")
        size = struct.unpack_from(">I", data, position)[0]
        box_type = bytes(data[position + 4 : position + 8])
        header = 8
        if size == 1:
            if end - position < 16:
                raise AudioDurationError("truncated 64-bit box header")
            size = struct.unpack_from(">Q", data, position + 8)[0]
            header = 16
        elif size == 0:
            size = end - position
        if size < header or position + size > end:
            raise AudioDurationError("box leaves its container")
        found.append((box_type, position + header, position + size))
        position += size
    return found


def _mp4_duration_ms(data: bytes) -> int:
    top = _boxes(data, 0, len(data))
    if not top or top[0][0] != b"ftyp":
        raise AudioDurationError("no ftyp box")
    moov = next(((body, stop) for kind, body, stop in top if kind == b"moov"), None)
    if moov is None:
        raise AudioDurationError("no moov box")
    mvhd = next(
        ((body, stop) for kind, body, stop in _boxes(data, moov[0], moov[1]) if kind == b"mvhd"),
        None,
    )
    if mvhd is None:
        raise AudioDurationError("no mvhd box")
    body, stop = mvhd
    if stop - body < 4:
        raise AudioDurationError("truncated mvhd")
    version = data[body]
    if version == 0:
        if stop - body < 20:
            raise AudioDurationError("truncated mvhd")
        timescale, duration = struct.unpack_from(">II", data, body + 12)
        unknown = duration == 0xFFFFFFFF
    elif version == 1:
        if stop - body < 32:
            raise AudioDurationError("truncated mvhd")
        timescale = struct.unpack_from(">I", data, body + 20)[0]
        duration = struct.unpack_from(">Q", data, body + 24)[0]
        unknown = duration == 0xFFFFFFFFFFFFFFFF
    else:
        raise AudioDurationError("unsupported mvhd version")
    if timescale == 0 or unknown:
        raise AudioDurationError("no usable duration")
    return _ceil_div(duration * 1000, timescale)


__all__ = [
    "MP4_MEDIA_TYPE",
    "SUPPORTED_AUDIO_MEDIA_TYPES",
    "WAV_MEDIA_TYPE",
    "AudioDurationError",
    "audio_duration_ms",
]
