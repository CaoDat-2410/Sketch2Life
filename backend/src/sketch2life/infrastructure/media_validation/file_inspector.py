"""Standard-library probes for PNG and PCM WAV quality signals.

The functions only read source files. They never normalize, rewrite, or upload media.
"""

from __future__ import annotations

from collections.abc import Iterator
from math import sqrt
from pathlib import Path
from statistics import fmean, pstdev
from struct import unpack
from wave import Error as WaveError
from wave import open as wave_open
from zlib import decompress

from sketch2life.domain.understanding.media_quality import AudioQualitySignals, ImageQualitySignals

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class FileMediaSignalInspector:
    """Local filesystem implementation of the standalone media-inspection port."""

    def inspect_image(self, path: Path) -> ImageQualitySignals:
        return inspect_image(path)

    def inspect_audio(self, path: Path) -> AudioQualitySignals:
        return inspect_audio(path)


def inspect_image(path: Path) -> ImageQualitySignals:
    try:
        width, height, luminance = _png_luminance(path.read_bytes())
    except (OSError, ValueError):
        return ImageQualitySignals(None, None, None, None, None, None)

    contrast = pstdev(luminance)
    edge_strength = _edge_strength(luminance, width, height)
    return ImageQualitySignals(
        width=width,
        height=height,
        mean_luminance=fmean(luminance),
        luminance_standard_deviation=contrast,
        edge_strength=edge_strength,
        border_ink_ratio=_border_ink_ratio(luminance, width, height),
    )


def inspect_audio(path: Path) -> AudioQualitySignals:
    try:
        with wave_open(str(path), "rb") as audio:
            channels = audio.getnchannels()
            sample_width = audio.getsampwidth()
            sample_rate = audio.getframerate()
            frame_count = audio.getnframes()
            frames = audio.readframes(frame_count)
        if channels < 1 or sample_rate < 1:
            raise ValueError("invalid WAV stream metadata")
        samples = tuple(_pcm_mono_samples(frames, channels, sample_width))
        if not samples:
            raise ValueError("WAV contains no samples")
    except (EOFError, OSError, ValueError, WaveError):
        return AudioQualitySignals(None, None, None, None, None, None, None)

    duration = len(samples) / sample_rate
    rms = sqrt(fmean(sample * sample for sample in samples))
    clipping_ratio = sum(abs(sample) >= 0.995 for sample in samples) / len(samples)
    activity = _speech_activity_ratio(samples, sample_rate)
    crossings = sum(
        current * previous < 0 for previous, current in zip(samples, samples[1:], strict=False)
    ) / max(1, len(samples) - 1)
    return AudioQualitySignals(
        duration_seconds=duration,
        sample_rate_hz=sample_rate,
        channels=channels,
        rms=rms,
        clipping_ratio=clipping_ratio,
        speech_activity_ratio=activity,
        zero_crossing_ratio=crossings,
    )


def _png_luminance(payload: bytes) -> tuple[int, int, tuple[float, ...]]:
    if not payload.startswith(_PNG_SIGNATURE):
        raise ValueError("not a PNG")

    offset = len(_PNG_SIGNATURE)
    width: int | None = None
    height: int | None = None
    bit_depth: int | None = None
    color_type: int | None = None
    interlace: int | None = None
    compressed = bytearray()
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise ValueError("truncated PNG chunk")
        length = unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        if data_end + 4 > len(payload):
            raise ValueError("truncated PNG data")
        data = payload[data_start:data_end]
        offset = data_end + 4
        if chunk_type == b"IHDR":
            if length != 13:
                raise ValueError("invalid PNG header")
            width, height, bit_depth, color_type, compression, filter_method, interlace = unpack(
                ">IIBBBBB", data
            )
            if compression != 0 or filter_method != 0:
                raise ValueError("unsupported PNG encoding")
        elif chunk_type == b"IDAT":
            compressed.extend(data)
        elif chunk_type == b"IEND":
            break

    if (
        width is None
        or height is None
        or bit_depth != 8
        or color_type not in {0, 2, 4, 6}
        or interlace != 0
        or not compressed
    ):
        raise ValueError("unsupported PNG format")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    rows = _unfilter_png_rows(decompress(bytes(compressed)), width, height, channels)
    return width, height, tuple(value for row in rows for value in _row_luminance(row, color_type))


def _unfilter_png_rows(
    decompressed: bytes, width: int, height: int, bytes_per_pixel: int
) -> Iterator[bytes]:
    stride = width * bytes_per_pixel
    expected_length = height * (stride + 1)
    if len(decompressed) != expected_length:
        raise ValueError("PNG data length does not match header")
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = decompressed[offset]
        encoded = decompressed[offset + 1 : offset + stride + 1]
        offset += stride + 1
        current = bytearray(stride)
        for index, value in enumerate(encoded):
            left = current[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                current[index] = value
            elif filter_type == 1:
                current[index] = (value + left) & 0xFF
            elif filter_type == 2:
                current[index] = (value + above) & 0xFF
            elif filter_type == 3:
                current[index] = (value + ((left + above) // 2)) & 0xFF
            elif filter_type == 4:
                current[index] = (value + _paeth(left, above, upper_left)) & 0xFF
            else:
                raise ValueError("unsupported PNG filter")
        previous = current
        yield bytes(current)


def _row_luminance(row: bytes, color_type: int) -> tuple[float, ...]:
    if color_type == 0:
        return tuple(float(value) for value in row)
    if color_type == 2:
        return tuple(
            0.2126 * red + 0.7152 * green + 0.0722 * blue
            for red, green, blue in _groups(row, 3)
        )
    if color_type == 4:
        return tuple((gray * alpha + 255 * (255 - alpha)) / 255 for gray, alpha in _groups(row, 2))
    return tuple(
        (0.2126 * red + 0.7152 * green + 0.0722 * blue) * alpha / 255 + 255 * (255 - alpha) / 255
        for red, green, blue, alpha in _groups(row, 4)
    )


def _groups(values: bytes, size: int) -> Iterator[tuple[int, ...]]:
    return (tuple(values[index : index + size]) for index in range(0, len(values), size))


def _paeth(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
    if distances[0] <= distances[1] and distances[0] <= distances[2]:
        return left
    if distances[1] <= distances[2]:
        return above
    return upper_left


def _edge_strength(luminance: tuple[float, ...], width: int, height: int) -> float:
    horizontal = sum(
        abs(luminance[row * width + column] - luminance[row * width + column + 1])
        for row in range(height)
        for column in range(width - 1)
    )
    vertical = sum(
        abs(luminance[row * width + column] - luminance[(row + 1) * width + column])
        for row in range(height - 1)
        for column in range(width)
    )
    comparisons = height * max(0, width - 1) + max(0, height - 1) * width
    return (horizontal + vertical) / max(1, comparisons)


def _border_ink_ratio(luminance: tuple[float, ...], width: int, height: int) -> float:
    indexes = set(range(width)) | set(range((height - 1) * width, height * width))
    indexes.update(row * width for row in range(height))
    indexes.update(row * width + width - 1 for row in range(height))
    return sum(luminance[index] < 220 for index in indexes) / len(indexes)


def _pcm_mono_samples(payload: bytes, channels: int, sample_width: int) -> Iterator[float]:
    if sample_width not in {1, 2, 3, 4}:
        raise ValueError("unsupported PCM sample width")
    frame_width = channels * sample_width
    if len(payload) % frame_width:
        raise ValueError("truncated PCM frame")
    maximum = float((1 << (8 * sample_width - 1)) - 1)
    for offset in range(0, len(payload), frame_width):
        channel_values = []
        for channel in range(channels):
            start = offset + channel * sample_width
            encoded = payload[start : start + sample_width]
            if sample_width == 1:
                value = (encoded[0] - 128) / 127
            else:
                value = int.from_bytes(encoded, byteorder="little", signed=True) / maximum
            channel_values.append(value)
        yield fmean(channel_values)


def _speech_activity_ratio(samples: tuple[float, ...], sample_rate: int) -> float:
    window_size = max(1, sample_rate // 10)
    windows = [
        samples[index : index + window_size]
        for index in range(0, len(samples), window_size)
    ]
    active = sum(sqrt(fmean(sample * sample for sample in window)) >= 0.015 for window in windows)
    return active / len(windows)
