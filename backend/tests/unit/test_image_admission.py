"""FEAT-018 P2-T1 D2 tests for the isolated image-admission boundary.

Implements every D1 section 7 boundary and behavioral test. All payloads are generated
deterministically in-test; no image binaries are committed and no personal data is used.
This suite is additive to FEAT-018 and does not modify any FEAT-003 test or fixture.
"""

from __future__ import annotations

import io
import json
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from struct import pack
from typing import Any
from zlib import compress, crc32

import av
import pytest

from sketch2life.application.ports.image_decoder import (
    ImageDecodeProcessingError,
    ImageDecodeSourceError,
    ImageDecodeTimeoutError,
)
from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018AdmissionResult,
    Feat018ImageAdmission,
)
from sketch2life.domain.understanding.image_admission import (
    AdmissionOutcome,
    AdmissionReason,
    DecodedFrameSignals,
    Feat018AdmissionLimits,
    ImageMetadataSignals,
    admission_message,
)
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder

# ---------------------------------------------------------------------------
# Deterministic synthetic fixture generators. No image binaries are committed.
# ---------------------------------------------------------------------------


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return pack(">I", len(data)) + kind + data + pack(">I", crc32(kind + data) & 0xFFFFFFFF)


def _png(
    width: int,
    height: int,
    *,
    bit_depth: int = 8,
    color_type: int = 2,
    raw: bytes | None = None,
    palette: bytes | None = None,
    pad_to_bytes: int | None = None,
) -> bytes:
    """A minimal, valid single-IDAT PNG. `raw` overrides the default solid-fill scanlines."""

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    if raw is None:
        bits_per_pixel = bit_depth * channels
        stride_bits = width * bits_per_pixel
        stride_bytes = (stride_bits + 7) // 8
        row = bytes([0x40]) * stride_bytes if bit_depth != 1 else bytes([0xFF]) * stride_bytes
        raw = b"".join(b"\x00" + row for _ in range(height))
    header = pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    extra = _png_chunk(b"PLTE", palette) if palette is not None else b""
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + extra
        + _png_chunk(b"IDAT", compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    if pad_to_bytes is not None:
        payload = _pad_png_to_exact_bytes(payload, pad_to_bytes)
    return payload


def _pad_png_to_exact_bytes(payload: bytes, target_size: int) -> bytes:
    """Inserts an ancillary `tEXt` chunk sized to make `payload` exactly `target_size` bytes.

    `tEXt` is a standard, always-safe-to-ignore ancillary chunk; a decoder that cannot skip
    it is not a compliant PNG reader. Verified against the real decoder used in this slice.
    """

    overhead = 12 + len(b"Comment\x00")  # 4-byte length + 4-byte type + 4-byte CRC + keyword
    pad_bytes = target_size - len(payload) - overhead
    if pad_bytes < 0:
        raise ValueError(f"target_size {target_size} is smaller than the unpadded payload")
    text_chunk = _png_chunk(b"tEXt", b"Comment\x00" + b"a" * pad_bytes)
    iend_index = payload.index(b"IEND") - 4
    padded = payload[:iend_index] + text_chunk + payload[iend_index:]
    assert len(padded) == target_size, (len(padded), target_size)
    return padded


def _valid_png(width: int = 64, height: int = 64) -> bytes:
    return _png(width, height)


def _jpeg(*, width: int = 64, height: int = 64, frames: int = 1, fill: int = 128) -> bytes:
    """A baseline JPEG (single or multi-frame MJPEG) built with PyAV's own encoder — no
    external decoder dependency, and no NumPy, is needed to author fixtures.

    `VideoFrame.from_bytes` only accepts a small set of pixel formats (verified: `rgba`
    works, `rgb24`/`bgr24`/`gray`/`yuv420p` all raise `NotImplementedError`). A tightly
    packed, unpadded RGBA buffer (`width * height * 4` bytes, no row stride/alignment
    gaps) is supplied; `from_bytes` handles any internal plane stride/padding itself —
    verified against 64x64, 65x33, 63x63 and 100x50 to decode back to the exact requested
    dimensions.
    """

    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format="mjpeg") as container:
        stream = container.add_stream("mjpeg", rate=1)
        stream.width, stream.height, stream.pix_fmt = width, height, "yuvj420p"
        raw_rgba = bytes([fill, fill, fill, 255]) * (width * height)
        for _ in range(frames):
            frame = av.VideoFrame.from_bytes(raw_rgba, width, height, format="rgba")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return buffer.getvalue()


def _rgb16_png(width: int = 32, height: int = 32) -> bytes:
    raw = b"".join(b"\x00" + b"\x00\x40" * (width * 3) for _ in range(height))
    return _png(width, height, bit_depth=16, color_type=2, raw=raw)


def _gray16_png(width: int = 32, height: int = 32) -> bytes:
    raw = b"".join(b"\x00" + b"\x00\x40" * width for _ in range(height))
    return _png(width, height, bit_depth=16, color_type=0, raw=raw)


def _palette_png(width: int = 32, height: int = 32) -> bytes:
    palette = bytes([255, 255, 255, 0, 0, 0])
    raw = b"".join(b"\x00" + bytes([0]) * width for _ in range(height))
    return _png(width, height, bit_depth=8, color_type=3, raw=raw, palette=palette)


def _grayscale8_png(width: int = 32, height: int = 32) -> bytes:
    return _png(width, height, bit_depth=8, color_type=0)


def _rgba8_png(width: int = 32, height: int = 32) -> bytes:
    return _png(width, height, bit_depth=8, color_type=6)


def _mono1_png(width: int = 32, height: int = 32) -> bytes:
    return _png(width, height, bit_depth=1, color_type=0)


def _garbage_idat_png(width: int = 64, height: int = 64) -> bytes:
    """A structurally valid header with an IDAT payload that fails to decompress/decode:
    metadata inspection succeeds, only the actual decode fails (D1 finding F-C)."""

    good = _png(width, height)
    idat_start = good.index(b"IDAT") - 4
    return good[:idat_start] + _png_chunk(b"IDAT", b"\x99" * 200) + _png_chunk(b"IEND", b"")


def _truncated_png(width: int = 64, height: int = 64) -> bytes:
    full = _png(width, height)
    return full[: len(full) // 2]


def _oversized_bytes() -> bytes:
    limit: int = Feat018AdmissionLimits().max_file_bytes
    return b"x" * (limit + 1)


def _png_pixel_budget_exceeded() -> bytes:
    return _png(2000, 2001)


def _png_longest_edge_exceeded() -> bytes:
    return _png(4200, 900)


def _jpeg_two_frame() -> bytes:
    return _jpeg(frames=2)


def _not_an_image_bytes() -> bytes:
    return b"not an image" * 10


def _empty_bytes() -> bytes:
    return b""


# Explicit fixture-generator registry (item 3): every manifest entry's `generator` field must
# be a key here. Used both to regenerate and verify each fixture's `payload_sha256` and to
# detect an unknown/missing generator reference before it silently passes.
FIXTURE_GENERATORS: dict[str, Callable[[], bytes]] = {
    "_valid_png": _valid_png,
    "_jpeg": _jpeg,
    "_oversized_bytes": _oversized_bytes,
    "_png_pixel_budget_exceeded": _png_pixel_budget_exceeded,
    "_png_longest_edge_exceeded": _png_longest_edge_exceeded,
    "_jpeg_two_frame": _jpeg_two_frame,
    "_rgb16_png": _rgb16_png,
    "_truncated_png": _truncated_png,
    "_garbage_idat_png": _garbage_idat_png,
    "_not_an_image_bytes": _not_an_image_bytes,
    "_empty_bytes": _empty_bytes,
}


# ---------------------------------------------------------------------------
# Stubs and spies for application-service-level tests.
# ---------------------------------------------------------------------------


class _StubDecoder:
    """A fully scripted `ImageDecoderPort`. Not PyAV-backed; used to test the application
    service's orchestration and exception mapping in isolation."""

    def __init__(
        self,
        *,
        metadata: ImageMetadataSignals | None,
        frame_count: int | Exception = 1,
        decoded: DecodedFrameSignals | Exception | None = None,
    ) -> None:
        self._metadata = metadata
        self._frame_count = frame_count
        self._decoded = decoded
        self.read_metadata_calls = 0
        self.probe_frame_count_calls = 0
        self.decode_one_frame_calls = 0

    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        self.read_metadata_calls += 1
        return self._metadata

    def probe_frame_count(self, snapshot: bytes) -> int:
        self.probe_frame_count_calls += 1
        if isinstance(self._frame_count, Exception):
            raise self._frame_count
        return self._frame_count

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        self.decode_one_frame_calls += 1
        if isinstance(self._decoded, Exception):
            raise self._decoded
        assert self._decoded is not None
        return self._decoded


class _SpyDecoder:
    """Wraps a real `ImageDecoderPort` and records call counts, for proving that rejected
    inputs never reach later, more expensive stages of the real decoder."""

    def __init__(self, wrapped: AvImageDecoder) -> None:
        self._wrapped = wrapped
        self.read_metadata_calls = 0
        self.probe_frame_count_calls = 0
        self.decode_one_frame_calls = 0

    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        self.read_metadata_calls += 1
        return self._wrapped.read_metadata(snapshot)

    def probe_frame_count(self, snapshot: bytes) -> int:
        self.probe_frame_count_calls += 1
        frame_count: int = self._wrapped.probe_frame_count(snapshot)
        return frame_count

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        self.decode_one_frame_calls += 1
        return self._wrapped.decode_one_frame(snapshot)


_SUPPORTED_METADATA = ImageMetadataSignals(
    container="png_pipe", codec="png", pixel_format="rgb24", width=64, height=64
)


def _admit_real(
    tmp_path: Path, name: str, payload: bytes | None
) -> tuple[Feat018AdmissionResult, Path]:
    """Writes `payload` (or nothing, for a missing-file case) and runs the real decoder."""

    path = tmp_path / name
    if payload is not None:
        path.write_bytes(payload)
    service = Feat018ImageAdmission(AvImageDecoder())
    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref=f"fixture:{name}:v1"))
    return result, path


# ---------------------------------------------------------------------------
# Boundary tests — exact limit and limit+1 (D1 section 7).
# ---------------------------------------------------------------------------


def test_bytes_at_limit_is_admitted(tmp_path: Path) -> None:
    limits = Feat018AdmissionLimits()
    payload = _png(64, 64, pad_to_bytes=limits.max_file_bytes)
    assert len(payload) == limits.max_file_bytes

    result, _ = _admit_real(tmp_path, "at-byte-limit.png", payload)

    assert result.decision.outcome is AdmissionOutcome.ADMITTED
    assert result.decision.reason is None


def test_bytes_over_limit_is_rejected_with_no_digest(tmp_path: Path) -> None:
    limits = Feat018AdmissionLimits()
    payload = _png(64, 64, pad_to_bytes=limits.max_file_bytes) + b"\x00"
    assert len(payload) == limits.max_file_bytes + 1

    result, _ = _admit_real(tmp_path, "over-byte-limit.png", payload)

    assert result.decision.outcome is AdmissionOutcome.REJECTED
    assert result.decision.reason is AdmissionReason.FILE_BYTES_EXCEEDED
    assert result.decision.digest is None
    assert result.source is None


def test_bounded_read_never_consumes_more_than_limit_plus_one_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Proves the exact D1 bound directly at the byte-I/O level: total bytes actually read
    from the source is never more than `max_file_bytes + 1`, even for a source many times
    larger than the limit, and no single `read()` call ever requests more than
    `_READ_CHUNK_BYTES`. A spy wrapping the real file object is required — asserting only
    the final outcome cannot distinguish "rejected after reading one extra byte" from
    "rejected after reading several extra megabytes"."""

    from sketch2life.application.services import image_admission as image_admission_module

    limits = Feat018AdmissionLimits()
    huge_size = limits.max_file_bytes * 4  # much larger than the limit
    path = tmp_path / "huge.bin"
    block = b"\x00" * (1024 * 1024)
    with path.open("wb") as sink:
        written = 0
        while written < huge_size:
            to_write = min(len(block), huge_size - written)
            sink.write(block[:to_write])
            written += to_write
    assert path.stat().st_size == huge_size

    read_request_sizes: list[int] = []
    total_bytes_returned = 0
    real_open = Path.open

    class _ReadSizeSpy:
        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped

        def read(self, size: int = -1) -> bytes:
            nonlocal total_bytes_returned
            read_request_sizes.append(size)
            data: bytes = self._wrapped.read(size)  # type: ignore[attr-defined]
            total_bytes_returned += len(data)
            return data

        def __enter__(self) -> _ReadSizeSpy:
            return self

        def __exit__(self, *exc_info: object) -> None:
            self._wrapped.close()  # type: ignore[attr-defined]

    def _spy_open(self: Path, mode: str = "r") -> _ReadSizeSpy:
        return _ReadSizeSpy(real_open(self, mode))

    monkeypatch.setattr(Path, "open", _spy_open)
    service = Feat018ImageAdmission(AvImageDecoder())

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.REJECTED
    assert result.decision.reason is AdmissionReason.FILE_BYTES_EXCEEDED
    assert result.decision.digest is None
    assert result.source is None
    assert read_request_sizes, "the spy must have observed at least one read() call"
    assert all(
        size <= image_admission_module._READ_CHUNK_BYTES for size in read_request_sizes
    )
    assert total_bytes_returned <= limits.max_file_bytes + 1, (
        f"consumed {total_bytes_returned} bytes from a {huge_size}-byte source; "
        f"must never exceed {limits.max_file_bytes + 1}"
    )


def test_pixels_at_limit_passes_metadata_stage(tmp_path: Path) -> None:
    limits = Feat018AdmissionLimits()
    assert limits.max_pixels == 2000 * 2000

    result, _ = _admit_real(tmp_path, "pixels-at-limit.png", _png(2000, 2000))

    assert result.decision.outcome is AdmissionOutcome.ADMITTED


def test_pixels_over_limit_is_rejected_before_decode(tmp_path: Path) -> None:
    limits = Feat018AdmissionLimits()
    assert limits.max_pixels < 2000 * 2001
    path = tmp_path / "pixels-over-limit.png"
    path.write_bytes(_png(2000, 2001))
    spy = _SpyDecoder(AvImageDecoder())
    service = Feat018ImageAdmission(spy)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.REJECTED
    assert result.decision.reason is AdmissionReason.PIXEL_BUDGET_EXCEEDED
    assert spy.decode_one_frame_calls == 0
    assert spy.probe_frame_count_calls == 0


def test_edge_at_limit_with_both_dimension_rules_satisfied(tmp_path: Path) -> None:
    limits = Feat018AdmissionLimits()
    assert max(4096, 900) == limits.max_longest_edge
    assert limits.max_pixels > 4096 * 900

    result, _ = _admit_real(tmp_path, "edge-at-limit.png", _png(4096, 900))

    assert result.decision.outcome is AdmissionOutcome.ADMITTED


def test_edge_over_limit_with_pixels_inside_budget_is_rejected(tmp_path: Path) -> None:
    """Proves the longest-edge guard is independent of the pixel budget: 4200x900 is
    3,780,000 pixels (inside the 4,000,000 budget) but its longest edge exceeds 4096."""

    limits = Feat018AdmissionLimits()
    assert limits.max_pixels > 4200 * 900
    assert limits.max_longest_edge < 4200

    result, _ = _admit_real(tmp_path, "edge-over-limit.png", _png(4200, 900))

    assert result.decision.outcome is AdmissionOutcome.REJECTED
    assert result.decision.reason is AdmissionReason.LONGEST_EDGE_EXCEEDED


# ---------------------------------------------------------------------------
# Behavioral tests (D1 section 7).
# ---------------------------------------------------------------------------


def test_compressed_small_pixel_large_is_rejected_before_decode(tmp_path: Path) -> None:
    """A ~16 KB PNG declaring 3000x3000 (9,000,000 px) must be rejected before any decode
    attempt, proven by spy — not merely by outcome."""

    path = tmp_path / "small-file-large-pixels.png"
    payload = _png(3000, 3000)
    path.write_bytes(payload)
    assert len(payload) < 50_000
    spy = _SpyDecoder(AvImageDecoder())
    service = Feat018ImageAdmission(spy)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.REJECTED
    assert result.decision.reason is AdmissionReason.PIXEL_BUDGET_EXCEEDED
    assert spy.decode_one_frame_calls == 0


def test_truncated_input_is_invalid_source_despite_metadata_opening(tmp_path: Path) -> None:
    """The measured trap (D1 finding F-C): metadata opens and reports 0x0 with a `None`
    pixel format. The implementation must not infer validity from a successful open, and
    must not crash when the pixel format is `None`."""

    result, _ = _admit_real(tmp_path, "truncated.png", _truncated_png())

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.CORRUPT_OR_TRUNCATED


def test_png_signature_only_is_invalid_source(tmp_path: Path) -> None:
    result, _ = _admit_real(tmp_path, "signature-only.png", b"\x89PNG\r\n\x1a\n")

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.CORRUPT_OR_TRUNCATED


def test_malformed_compressed_stream_is_invalid_source(tmp_path: Path) -> None:
    """Valid header, garbage IDAT (D1 finding F-C): metadata reports a plausible 64x64
    rgb24 and only the decode fails, via the `FFmpegError`-base-class catch (F-F)."""

    result, _ = _admit_real(tmp_path, "garbage-idat.png", _garbage_idat_png())

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.CORRUPT_OR_TRUNCATED


def test_empty_file_is_not_an_image_at_admission_level(tmp_path: Path) -> None:
    result, _ = _admit_real(tmp_path, "empty.png", b"")

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.NOT_AN_IMAGE


def test_empty_bytes_hash_at_the_snapshot_helper_level(tmp_path: Path) -> None:
    """A separate, layer-specific assertion from the outcome test above: the digest for an
    empty (but completely read) file must be the well-known empty-string SHA-256, proving
    the digest is computed from the real snapshot bytes and never fabricated."""

    result, _ = _admit_real(tmp_path, "empty-for-hash.png", b"")

    assert result.decision.digest == sha256(b"").hexdigest()
    assert result.decision.digest == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_arbitrary_bytes_are_not_an_image(tmp_path: Path) -> None:
    result, _ = _admit_real(tmp_path, "not-an-image.bin", b"hello world" * 40)

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.NOT_AN_IMAGE


@pytest.mark.parametrize(
    "name,payload",
    [
        ("rgb16.png", _rgb16_png()),
        ("gray16.png", _gray16_png()),
    ],
    ids=["rgb16", "gray16"],
)
def test_unsupported_pixel_formats_are_rejected(tmp_path: Path, name: str, payload: bytes) -> None:
    result, _ = _admit_real(tmp_path, name, payload)

    assert result.decision.outcome is AdmissionOutcome.UNSUPPORTED
    assert result.decision.reason is AdmissionReason.UNSUPPORTED_PIXEL_FORMAT


def test_two_frame_jpeg_resolves_to_unsupported_container(tmp_path: Path) -> None:
    """Owner decision U3 (locked): container validation precedes packet probing, so a
    multi-frame JPEG (container `mjpeg`, not `jpeg_pipe`) resolves deterministically to
    `UNSUPPORTED_CONTAINER` rather than being reached by the frame-count probe at all."""

    result, _ = _admit_real(tmp_path, "two-frame.jpg", _jpeg(frames=2))

    assert result.decision.outcome is AdmissionOutcome.UNSUPPORTED
    assert result.decision.reason is AdmissionReason.UNSUPPORTED_CONTAINER


@pytest.mark.parametrize(
    "name,payload",
    [
        ("rgb8.png", _valid_png()),
        ("rgba8.png", _rgba8_png()),
        ("gray8.png", _grayscale8_png()),
        ("palette8.png", _palette_png()),
        ("mono1.png", _mono1_png()),
        ("baseline.jpg", _jpeg()),
    ],
    ids=["rgb8", "rgba8", "gray8", "palette8", "mono1", "baseline-jpeg"],
)
def test_supported_profiles_are_admitted(tmp_path: Path, name: str, payload: bytes) -> None:
    result, _ = _admit_real(tmp_path, name, payload)

    assert result.decision.outcome is AdmissionOutcome.ADMITTED, (name, result.decision)
    assert result.source is not None
    assert result.source.sha256 == sha256(payload).hexdigest()


def test_multiframe_probe_examines_at_most_two_packets_and_decodes_none() -> None:
    """Tests the real decoder's bounded packet probe directly, independent of the service's
    container-gate ordering (U3), which would otherwise intercept a two-frame JPEG first."""

    decoder = AvImageDecoder()
    two_frame = _jpeg(frames=3)

    frame_count = decoder.probe_frame_count(two_frame)

    assert frame_count == 2  # capped; never an exact count above the threshold


def test_multiframe_rejection_end_to_end_via_stub(tmp_path: Path) -> None:
    """Proves the service applies `MULTIPLE_FRAMES` policy end-to-end, using a stub that
    reports a supported container/codec/pixel-format but a frame count above the limit —
    real single-frame-capable containers (PNG, single-frame JPEG) cannot construct this
    case naturally, since a genuinely multi-frame JPEG already fails container validation
    first (U3)."""

    path = tmp_path / "stub-multiframe.png"
    path.write_bytes(_valid_png())
    stub = _StubDecoder(metadata=_SUPPORTED_METADATA, frame_count=2)
    service = Feat018ImageAdmission(stub)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.REJECTED
    assert result.decision.reason is AdmissionReason.MULTIPLE_FRAMES
    assert stub.decode_one_frame_calls == 0


def test_decoded_metadata_mismatch_is_invalid_source(tmp_path: Path) -> None:
    """A decoder that produces dimensions/format disagreeing with the admitted metadata must
    not be trusted, proving the cross-check (D1 section 3 step 8) is not redundant."""

    path = tmp_path / "cross-check-mismatch.png"
    path.write_bytes(_valid_png())
    mismatched = DecodedFrameSignals(width=32, height=32, pixel_format="rgb24")
    stub = _StubDecoder(metadata=_SUPPORTED_METADATA, frame_count=1, decoded=mismatched)
    service = Feat018ImageAdmission(stub)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.CORRUPT_OR_TRUNCATED


def test_source_mutation_between_calls_changes_the_digest(tmp_path: Path) -> None:
    """Each `admit()` call binds to exactly the bytes it itself reads; overwriting the file
    between calls must change the reported digest, proving no stale/cached snapshot."""

    path = tmp_path / "mutating.png"
    path.write_bytes(_valid_png(32, 32))
    service = Feat018ImageAdmission(AvImageDecoder())

    first = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))
    path.write_bytes(_valid_png(48, 48))
    second = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert first.decision.digest != second.decision.digest
    assert first.decision.digest == sha256(_valid_png(32, 32)).hexdigest()
    assert second.decision.digest == sha256(_valid_png(48, 48)).hexdigest()


def test_decoder_mutating_source_mid_admit_does_not_affect_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The between-calls test above proves each *separate* `admit()` call binds to fresh
    bytes; it does not prove anything about a mutation happening *during* one call. Here a
    decoder wrapper overwrites the file on disk immediately after receiving the snapshot,
    then answers using the snapshot bytes it was actually given — which is the only thing
    the `ImageDecoderPort` interface ever hands it; it has no path to re-read even if it
    wanted to. Combined with a `Path.open` call-count spy (scoped to exactly the `admit()`
    call — the mutation itself and this test's own before/after verification reads
    deliberately bypass `Path.open` via the raw `open()` builtin, so they cannot pollute
    the count), this proves both structurally (the port signature carries no path) and
    empirically (the reported result still describes the pre-mutation content, and the
    path was opened exactly once) that no stage reopens the source path within a single
    `admit()` call."""

    path = tmp_path / "mutating-during-admission.png"
    original_payload = _valid_png(64, 64)
    mutated_payload = _valid_png(96, 96)
    with open(path, "wb") as f:  # raw builtin, bypasses the Path.open spy installed below
        f.write(original_payload)

    open_calls = 0
    real_open = Path.open

    def _counting_open(self: Path, mode: str = "r") -> object:
        nonlocal open_calls
        open_calls += 1
        return real_open(self, mode)

    class _MutateOnFirstCallDecoder:
        """Wraps the real decoder. On its first call, overwrites the file on disk with
        different, still-valid image content — via the raw `open()` builtin, not
        `Path.write_bytes`, so the mutation itself is not counted as a `Path.open` call —
        then delegates to the real decoder using the snapshot bytes it was actually given."""

        def __init__(self, wrapped: AvImageDecoder, target: Path, replacement: bytes) -> None:
            self._wrapped = wrapped
            self._target = target
            self._replacement = replacement
            self._mutated = False
            self.read_metadata_calls = 0

        def _mutate_once(self) -> None:
            if not self._mutated:
                with open(self._target, "wb") as f:
                    f.write(self._replacement)
                self._mutated = True

        def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
            self.read_metadata_calls += 1
            self._mutate_once()
            return self._wrapped.read_metadata(snapshot)

        def probe_frame_count(self, snapshot: bytes) -> int:
            self._mutate_once()
            frame_count: int = self._wrapped.probe_frame_count(snapshot)
            return frame_count

        def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
            self._mutate_once()
            return self._wrapped.decode_one_frame(snapshot)

    decoder = _MutateOnFirstCallDecoder(AvImageDecoder(), path, mutated_payload)
    service = Feat018ImageAdmission(decoder)

    monkeypatch.setattr(Path, "open", _counting_open)
    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))
    monkeypatch.setattr(Path, "open", real_open)

    # The path was opened exactly once for the whole call — no stage reopened it.
    assert decoder.read_metadata_calls == 1
    assert open_calls == 1

    # The on-disk file genuinely changed, mid-admit (read via the raw builtin, not
    # Path.open, purely so this assertion cannot itself be miscounted above).
    with open(path, "rb") as read_handle:
        on_disk_now = read_handle.read()
    assert on_disk_now == mutated_payload
    assert on_disk_now != original_payload

    # But the result still describes only the original, pre-mutation snapshot.
    assert result.decision.outcome is AdmissionOutcome.ADMITTED
    assert result.decision.digest == sha256(original_payload).hexdigest()
    assert result.decision.metadata is not None
    assert (result.decision.metadata.width, result.decision.metadata.height) == (64, 64)
    assert result.source is not None
    assert result.source.sha256 == sha256(original_payload).hexdigest()


@pytest.mark.parametrize("byte_count", [1024 * 1024 - 1, 1024 * 1024, 1024 * 1024 + 1])
def test_complete_source_digest_across_chunk_boundaries(tmp_path: Path, byte_count: int) -> None:
    """Sized just under, exactly at, and just over the 1 MiB read-chunk boundary. The digest
    must equal an independently computed SHA-256 of the whole file — never a prefix."""

    payload = _png(200, 200, pad_to_bytes=byte_count)
    assert len(payload) == byte_count
    expected = sha256(payload).hexdigest()

    result, _ = _admit_real(tmp_path, f"chunk-boundary-{byte_count}.png", payload)

    assert result.decision.outcome is AdmissionOutcome.ADMITTED
    assert result.decision.digest == expected


@pytest.mark.parametrize(
    "name,payload,expected_outcome,expected_reason,expected_decode_calls",
    [
        # Decidable from the byte budget or metadata alone: decode is never attempted.
        ("oversized.png", b"x" * (Feat018AdmissionLimits().max_file_bytes + 1),
         AdmissionOutcome.REJECTED, AdmissionReason.FILE_BYTES_EXCEEDED, 0),
        ("pixel-over.png", _png(2000, 2001),
         AdmissionOutcome.REJECTED, AdmissionReason.PIXEL_BUDGET_EXCEEDED, 0),
        ("edge-over.png", _png(4200, 900),
         AdmissionOutcome.REJECTED, AdmissionReason.LONGEST_EDGE_EXCEEDED, 0),
        ("unsupported-16bit.png", _rgb16_png(),
         AdmissionOutcome.UNSUPPORTED, AdmissionReason.UNSUPPORTED_PIXEL_FORMAT, 0),
        ("two-frame.jpg", _jpeg(frames=2),
         AdmissionOutcome.UNSUPPORTED, AdmissionReason.UNSUPPORTED_CONTAINER, 0),
        ("truncated.png", _truncated_png(),
         AdmissionOutcome.INVALID_SOURCE, AdmissionReason.CORRUPT_OR_TRUNCATED, 0),
        ("not-an-image.bin", b"not an image" * 10,
         AdmissionOutcome.INVALID_SOURCE, AdmissionReason.NOT_AN_IMAGE, 0),
        # Metadata reports a plausible header (D1 finding F-C); decode is the only way to
        # detect this corruption, so exactly one decode call is correct here, not zero.
        ("garbage-idat.png", _garbage_idat_png(),
         AdmissionOutcome.INVALID_SOURCE, AdmissionReason.CORRUPT_OR_TRUNCATED, 1),
    ],
    ids=[
        "oversized",
        "pixel-over",
        "edge-over",
        "unsupported-16bit",
        "two-frame-container",
        "truncated",
        "not-an-image",
        "garbage-idat",
    ],
)
def test_decode_is_attempted_only_when_it_is_the_detection_mechanism(
    tmp_path: Path,
    name: str,
    payload: bytes,
    expected_outcome: AdmissionOutcome,
    expected_reason: AdmissionReason,
    expected_decode_calls: int,
) -> None:
    """This is a decoder-call-discipline test, not a restatement of D1's zero-provider-call
    invariant, and it must not be read as one. The provider invariant — no Qwen/ASR call
    for any non-`ADMITTED` outcome — holds unconditionally and structurally in this slice:
    D2 contains no provider dependency, adapter, or wiring of any kind, so there is nothing
    capable of making such a call regardless of which stage rejects an input. What this
    test actually proves is narrower and separate: that the real decoder's own expensive
    `decode_one_frame` operation is called only when metadata/frame-count inspection alone
    cannot decide the outcome — never merely because the input was rejected. Decoder call
    counts genuinely do vary by which stage detects the rejection (see the `garbage-idat`
    case below, where exactly one decode call is correct and necessary); that variation is
    a fact about this in-scope decoder, and is unrelated to the provider invariant."""

    path = tmp_path / name
    path.write_bytes(payload)
    spy = _SpyDecoder(AvImageDecoder())
    service = Feat018ImageAdmission(spy)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is expected_outcome
    assert result.decision.reason is expected_reason
    assert spy.decode_one_frame_calls == expected_decode_calls


def test_missing_source_has_no_decoder_calls_at_all(tmp_path: Path) -> None:
    path = tmp_path / "does-not-exist.png"
    spy = _SpyDecoder(AvImageDecoder())
    service = Feat018ImageAdmission(spy)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.MISSING_SOURCE
    assert spy.read_metadata_calls == 0
    assert spy.probe_frame_count_calls == 0
    assert spy.decode_one_frame_calls == 0


def test_oversized_file_has_no_decoder_calls_at_all(tmp_path: Path) -> None:
    path = tmp_path / "oversized.png"
    path.write_bytes(b"x" * (Feat018AdmissionLimits().max_file_bytes + 1))
    spy = _SpyDecoder(AvImageDecoder())
    service = Feat018ImageAdmission(spy)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.reason is AdmissionReason.FILE_BYTES_EXCEEDED
    assert spy.read_metadata_calls == 0
    assert spy.probe_frame_count_calls == 0
    assert spy.decode_one_frame_calls == 0


def test_decoder_source_error_at_decode_stage_maps_to_corrupt_or_truncated(
    tmp_path: Path,
) -> None:
    path = tmp_path / "stub-source-error.png"
    path.write_bytes(_valid_png())
    stub = _StubDecoder(
        metadata=_SUPPORTED_METADATA,
        frame_count=1,
        decoded=ImageDecodeSourceError("simulated corrupt stream"),
    )
    service = Feat018ImageAdmission(stub)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.INVALID_SOURCE
    assert result.decision.reason is AdmissionReason.CORRUPT_OR_TRUNCATED


def test_decoder_processing_error_never_reported_as_invalid_source(tmp_path: Path) -> None:
    """Processing-failure separation (D1 section 2 prohibition 5): a decoder-side failure
    that is not a source-data problem must map to `PROCESSING_FAILURE`, never
    `INVALID_SOURCE` — blaming the user for our failure would be a correctness bug."""

    path = tmp_path / "stub-processing-error.png"
    path.write_bytes(_valid_png())
    stub = _StubDecoder(
        metadata=_SUPPORTED_METADATA,
        frame_count=1,
        decoded=ImageDecodeProcessingError("simulated internal decoder failure"),
    )
    service = Feat018ImageAdmission(stub)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.PROCESSING_FAILURE
    assert result.decision.reason is AdmissionReason.DECODER_ERROR
    assert result.decision.outcome is not AdmissionOutcome.INVALID_SOURCE


def test_decoder_timeout_stub_proves_mapping_only(tmp_path: Path) -> None:
    """`DECODER_TIMEOUT` is reserved for a future killable worker (D1 section 8): the
    in-process real decoder never raises `ImageDecodeTimeoutError`. This test proves only
    that the application service maps the exception correctly if raised — it proves nothing
    about actual runtime timeout enforcement, which does not exist in this slice."""

    path = tmp_path / "stub-timeout.png"
    path.write_bytes(_valid_png())
    stub = _StubDecoder(
        metadata=_SUPPORTED_METADATA,
        frame_count=1,
        decoded=ImageDecodeTimeoutError("simulated timeout from a future worker"),
    )
    service = Feat018ImageAdmission(stub)

    result = service.admit(Feat018AdmissionRequest(path=path, artifact_ref="fixture:v1"))

    assert result.decision.outcome is AdmissionOutcome.PROCESSING_FAILURE
    assert result.decision.reason is AdmissionReason.DECODER_TIMEOUT


# ---------------------------------------------------------------------------
# Domain-level unit coverage (fast, no I/O).
# ---------------------------------------------------------------------------


def test_outcome_message_covers_every_reason() -> None:
    for reason in AdmissionReason:
        assert admission_message(reason)
    assert admission_message(None) == "Image admitted"


def test_metadata_none_is_not_an_image() -> None:
    from sketch2life.domain.understanding.image_admission import evaluate_metadata

    assert evaluate_metadata(None, Feat018AdmissionLimits()) is AdmissionReason.NOT_AN_IMAGE


def test_metadata_check_order_container_before_pixel_format() -> None:
    """Directly exercises the exact D1 section 3 step-5 ordering: an unsupported container
    is reported even when the pixel format is also unresolved."""

    from sketch2life.domain.understanding.image_admission import evaluate_metadata

    signals = ImageMetadataSignals(
        container="mjpeg", codec="mjpeg", pixel_format=None, width=0, height=0
    )

    assert evaluate_metadata(signals, Feat018AdmissionLimits()) is (
        AdmissionReason.UNSUPPORTED_CONTAINER
    )


# ---------------------------------------------------------------------------
# Fixture manifest (D1 section 6).
# ---------------------------------------------------------------------------

_MANIFEST_PATH = (
    Path(__file__).parents[3]
    / "features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/manifest-v1.json"
)


def _load_manifest() -> Any:
    # Returns `Any`, honestly: `feat018_admission_manifest` has no py.typed marker in this
    # environment (the same pre-existing condition affecting every intra-package import in
    # this file), so its real type cannot be statically resolved here regardless.
    from feat018_admission_manifest import Feat018AdmissionFixtureManifestV1

    return Feat018AdmissionFixtureManifestV1.model_validate(
        json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    )


def _minimal_entry(**overrides: object) -> dict[str, object]:
    """A baseline valid entry dict for the negative schema tests below to mutate."""

    base: dict[str, object] = {
        "fixture_id": "sample-entry",
        "generator": "_valid_png",
        "payload_sha256": sha256(b"placeholder").hexdigest(),
        "expected_outcome": "ADMITTED",
        "expected_reason": None,
        "synthetic_data": True,
    }
    base.update(overrides)
    return base


def test_checked_in_admission_manifest_matches_its_versioned_contract() -> None:
    """Mirrors FEAT-003's `test_checked_in_fixture_manifest_matches_its_versioned_contract`
    pattern, against the FEAT-018-local schema — never `MediaFixtureManifestV1`, and never
    added to FEAT-003's `data/fixtures/manifests/media-validation-v1.json`."""

    manifest = _load_manifest()

    assert manifest.contract_name == "Feat018AdmissionFixtureManifestV1"
    assert all(entry.synthetic_data for entry in manifest.fixtures)
    assert all(len(entry.payload_sha256) == 64 for entry in manifest.fixtures)
    outcomes = {entry.expected_outcome for entry in manifest.fixtures}
    assert outcomes == {
        AdmissionOutcome.ADMITTED,
        AdmissionOutcome.REJECTED,
        AdmissionOutcome.UNSUPPORTED,
        AdmissionOutcome.INVALID_SOURCE,
    }, "manifest should cover every reachable admission outcome except PROCESSING_FAILURE"


def _verify_generators_and_digests(manifest: object) -> None:
    """Regenerates every fixture's payload via the explicit `FIXTURE_GENERATORS` registry
    and asserts its actual SHA-256 equals the checked-in `payload_sha256`. Raises
    `AssertionError` with a specific, greppable message for an unknown generator or a
    digest mismatch — never merely checks that the hash string has 64 characters."""

    for entry in manifest.fixtures:  # type: ignore[attr-defined]
        if entry.generator not in FIXTURE_GENERATORS:
            raise AssertionError(
                f"fixture {entry.fixture_id!r} references unknown generator "
                f"{entry.generator!r}; known generators: {sorted(FIXTURE_GENERATORS)}"
            )
        regenerated = FIXTURE_GENERATORS[entry.generator]()
        actual_sha256 = sha256(regenerated).hexdigest()
        if actual_sha256 != entry.payload_sha256:
            raise AssertionError(
                f"fixture {entry.fixture_id!r}: generator {entry.generator!r} now "
                f"produces sha256={actual_sha256}, but the manifest declares "
                f"{entry.payload_sha256}"
            )


def test_manifest_payloads_regenerate_to_their_declared_sha256() -> None:
    """The load-bearing manifest test, against the real checked-in manifest."""

    _verify_generators_and_digests(_load_manifest())


def test_manifest_every_registered_generator_is_referenced() -> None:
    """The inverse check: every generator in the registry is actually used by at least one
    manifest entry, so the registry cannot silently accumulate dead entries either."""

    manifest = _load_manifest()
    referenced = {entry.generator for entry in manifest.fixtures}
    assert referenced == set(FIXTURE_GENERATORS), (
        f"registry/manifest drift — registered but unreferenced: "
        f"{set(FIXTURE_GENERATORS) - referenced}; "
        f"referenced but unregistered: {referenced - set(FIXTURE_GENERATORS)}"
    )


def test_manifest_verification_detects_unknown_generator() -> None:
    """Proves `_verify_generators_and_digests` genuinely detects an unknown generator,
    using a synthetic manifest constructed for exactly this purpose — the real checked-in
    manifest can never exercise this failure path by definition."""

    from feat018_admission_manifest import Feat018AdmissionFixtureManifestV1

    payload = {
        "contract_name": "Feat018AdmissionFixtureManifestV1",
        "contract_version": "1.0",
        "data_policy": "synthetic-only",
        "generator": "test",
        "fixtures": [_minimal_entry(generator="_this_generator_does_not_exist")],
    }
    manifest = Feat018AdmissionFixtureManifestV1.model_validate(payload)

    with pytest.raises(AssertionError, match="unknown generator"):
        _verify_generators_and_digests(manifest)


def test_manifest_verification_detects_digest_mismatch() -> None:
    """Proves `_verify_generators_and_digests` genuinely detects a drifted digest — a
    stale `payload_sha256` that no longer matches what its named generator produces."""

    from feat018_admission_manifest import Feat018AdmissionFixtureManifestV1

    payload = {
        "contract_name": "Feat018AdmissionFixtureManifestV1",
        "contract_version": "1.0",
        "data_policy": "synthetic-only",
        "generator": "test",
        "fixtures": [
            _minimal_entry(
                generator="_valid_png", payload_sha256=sha256(b"wrong bytes").hexdigest()
            )
        ],
    }
    manifest = Feat018AdmissionFixtureManifestV1.model_validate(payload)

    with pytest.raises(AssertionError, match="now produces"):
        _verify_generators_and_digests(manifest)


def test_manifest_rejects_duplicate_fixture_ids() -> None:
    from feat018_admission_manifest import Feat018AdmissionFixtureManifestV1
    from pydantic import ValidationError

    payload = {
        "contract_name": "Feat018AdmissionFixtureManifestV1",
        "contract_version": "1.0",
        "data_policy": "synthetic-only",
        "generator": "test",
        "fixtures": [
            _minimal_entry(fixture_id="dupe"),
            _minimal_entry(fixture_id="dupe"),
        ],
    }

    with pytest.raises(ValidationError, match="duplicate fixture_id"):
        Feat018AdmissionFixtureManifestV1.model_validate(payload)


def test_manifest_entry_requires_reason_for_non_admitted_outcome() -> None:
    from feat018_admission_manifest import Feat018AdmissionFixtureManifestEntryV1
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="must declare an expected_reason"):
        Feat018AdmissionFixtureManifestEntryV1.model_validate(
            _minimal_entry(expected_outcome="REJECTED", expected_reason=None)
        )


def test_manifest_entry_rejects_reason_on_admitted_outcome() -> None:
    from feat018_admission_manifest import Feat018AdmissionFixtureManifestEntryV1
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="must not declare"):
        Feat018AdmissionFixtureManifestEntryV1.model_validate(
            _minimal_entry(
                expected_outcome="ADMITTED", expected_reason="FILE_BYTES_EXCEEDED"
            )
        )


def test_manifest_entry_rejects_mismatched_outcome_reason_pair() -> None:
    """`UNSUPPORTED_CODEC` belongs to `UNSUPPORTED`, not `REJECTED` — declaring them
    together must fail, not silently accept an internally inconsistent fixture."""

    from feat018_admission_manifest import Feat018AdmissionFixtureManifestEntryV1
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="belongs to outcome"):
        Feat018AdmissionFixtureManifestEntryV1.model_validate(
            _minimal_entry(
                expected_outcome="REJECTED", expected_reason="UNSUPPORTED_CODEC"
            )
        )


def test_manifest_entry_rejects_unknown_outcome_value() -> None:
    from feat018_admission_manifest import Feat018AdmissionFixtureManifestEntryV1
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Feat018AdmissionFixtureManifestEntryV1.model_validate(
            _minimal_entry(expected_outcome="NOT_A_REAL_OUTCOME", expected_reason=None)
        )


def test_manifest_entry_rejects_unknown_reason_value() -> None:
    from feat018_admission_manifest import Feat018AdmissionFixtureManifestEntryV1
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Feat018AdmissionFixtureManifestEntryV1.model_validate(
            _minimal_entry(
                expected_outcome="REJECTED", expected_reason="NOT_A_REAL_REASON"
            )
        )
