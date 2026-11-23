"""FEAT-066 T-2c: audio duration from the stored bytes, without a decoder (SRS l.982, l.1942).

WAV goes through the standard ``wave`` module, MP4/M4A through the ``mvhd`` box. The MP4 cases are
the hostile ones the plan names: ``moov`` after ``mdat``, 64-bit sizes, size 0, depth and box
count caps, ``mvhd`` versions 0 and 1, a timescale of 0, unknown or overflowing durations, and a
box that leaves its container.
"""

from __future__ import annotations

import io
import struct
import wave
from pathlib import Path

import pytest

from sketch2life.application.ports.upload_validation import header_matches_media_type
from sketch2life.infrastructure.media_validation import audio_duration as module
from sketch2life.infrastructure.media_validation.audio_duration import (
    AudioDurationError,
    audio_duration_ms,
)

WAV = "audio/wav"
MP4 = "audio/mp4"


def wav_bytes(frames: int, rate: int = 8000, *, width: int = 2, channels: int = 1) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(width)
        writer.setframerate(rate)
        writer.writeframes(b"\x00" * frames * width * channels)
    return buffer.getvalue()


def box(kind: bytes, body: bytes = b"", *, wide: bool = False, zero: bool = False) -> bytes:
    if zero:
        return struct.pack(">I", 0) + kind + body
    if wide:
        return struct.pack(">I", 1) + kind + struct.pack(">Q", 16 + len(body)) + body
    return struct.pack(">I", 8 + len(body)) + kind + body


def mvhd_v0(timescale: int, duration: int) -> bytes:
    body = b"\x00\x00\x00\x00" + struct.pack(">IIII", 0, 0, timescale, duration) + b"\x00" * 80
    return box(b"mvhd", body)


def mvhd_v1(timescale: int, duration: int) -> bytes:
    body = b"\x01\x00\x00\x00" + struct.pack(">QQIQ", 0, 0, timescale, duration) + b"\x00" * 80
    return box(b"mvhd", body)


FTYP = box(b"ftyp", b"M4A \x00\x00\x00\x00M4A mp42isom")


def mp4(*children: bytes) -> bytes:
    return b"".join(children)


# ------------------------------------------------------------------------------------- WAV
def test_a_wav_duration_is_rounded_up_to_whole_milliseconds() -> None:
    assert audio_duration_ms(wav_bytes(8000), media_type=WAV) == 1000
    assert audio_duration_ms(wav_bytes(12000), media_type=WAV) == 1500
    assert audio_duration_ms(wav_bytes(1), media_type=WAV) == 1  # 0.125 ms rounds up
    assert audio_duration_ms(wav_bytes(16000 * 120, rate=16000, channels=2), media_type=WAV) == (
        120_000
    )


def test_a_stereo_wav_counts_frames_not_samples() -> None:
    assert audio_duration_ms(wav_bytes(8000, channels=2), media_type=WAV) == 1000


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"RIFF",
        b"not a wav at all, just some bytes",
        wav_bytes(0),  # no frames
        wav_bytes(800)[:30],  # truncated header
    ],
)
def test_an_unreadable_or_empty_wav_is_a_content_mismatch(data: bytes) -> None:
    with pytest.raises(AudioDurationError) as raised:
        audio_duration_ms(data, media_type=WAV)
    assert raised.value.code == "UPLOAD_CONTENT_MISMATCH"


def test_a_wav_whose_data_chunk_is_larger_than_the_file_is_refused() -> None:
    data = bytearray(wav_bytes(800))
    data[-1600 - 4 : -1600] = struct.pack("<I", 2_000_000)  # data chunk size, far over the file
    with pytest.raises(AudioDurationError):
        audio_duration_ms(bytes(data), media_type=WAV)
    truncated = wav_bytes(8000)[:-4000]
    with pytest.raises(AudioDurationError):
        audio_duration_ms(truncated, media_type=WAV)


def test_a_non_pcm_wav_is_refused() -> None:
    data = bytearray(wav_bytes(800))
    data[20:22] = struct.pack("<H", 3)  # IEEE float: the standard module reads PCM only
    with pytest.raises(AudioDurationError):
        audio_duration_ms(bytes(data), media_type=WAV)


def test_a_wav_with_a_zero_sample_rate_is_refused() -> None:
    data = bytearray(wav_bytes(800))
    data[24:28] = struct.pack("<I", 0)
    with pytest.raises(AudioDurationError):
        audio_duration_ms(bytes(data), media_type=WAV)


# ------------------------------------------------------------------------------------- MP4
def test_the_mp4_duration_is_the_mvhd_duration_over_its_timescale() -> None:
    data = mp4(FTYP, box(b"moov", mvhd_v0(1000, 5000)), box(b"mdat", b"\x00" * 64))
    assert audio_duration_ms(data, media_type=MP4) == 5000
    assert audio_duration_ms(mp4(FTYP, box(b"moov", mvhd_v0(44100, 44100))), media_type=MP4) == 1000
    assert (
        audio_duration_ms(mp4(FTYP, box(b"moov", mvhd_v0(3, 1))), media_type=MP4) == 334
    )  # 333.33 ms rounds up


def test_moov_after_mdat_is_found() -> None:
    data = mp4(FTYP, box(b"mdat", b"\x01" * 4096), box(b"moov", mvhd_v0(1000, 2500)))
    assert audio_duration_ms(data, media_type=MP4) == 2500


def test_mvhd_version_1_with_a_64_bit_duration() -> None:
    data = mp4(FTYP, box(b"moov", mvhd_v1(1000, 90_000)))
    assert audio_duration_ms(data, media_type=MP4) == 90_000


def test_a_64_bit_box_size_and_a_size_of_zero_are_handled() -> None:
    wide = mp4(FTYP, box(b"free", b"\x00" * 10, wide=True), box(b"moov", mvhd_v0(1000, 3000)))
    assert audio_duration_ms(wide, media_type=MP4) == 3000
    wide_moov = mp4(FTYP, box(b"moov", mvhd_v0(1000, 4000), wide=True))
    assert audio_duration_ms(wide_moov, media_type=MP4) == 4000
    # A final box of size 0 runs to the end of the file; here it is the moov itself.
    to_end = mp4(FTYP, box(b"moov", mvhd_v0(1000, 6000), zero=True))
    assert audio_duration_ms(to_end, media_type=MP4) == 6000


def test_a_mvhd_inside_a_nested_box_is_not_taken_for_the_movie_header() -> None:
    nested = box(b"udta", mvhd_v0(1000, 9000))
    data = mp4(FTYP, box(b"moov", nested))
    with pytest.raises(AudioDurationError):
        audio_duration_ms(data, media_type=MP4)


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\x00\x00\x00",
        mp4(box(b"moov", mvhd_v0(1000, 1000))),  # no ftyp first
        mp4(FTYP),  # no moov
        mp4(FTYP, box(b"moov", box(b"trak", b""))),  # no mvhd
        mp4(FTYP, box(b"moov", mvhd_v0(0, 1000))),  # timescale 0
        mp4(FTYP, box(b"moov", mvhd_v0(1000, 0))),  # no duration
        mp4(FTYP, box(b"moov", mvhd_v0(1000, 0xFFFFFFFF))),  # unknown duration marker
        mp4(FTYP, box(b"moov", mvhd_v1(1000, 0xFFFFFFFFFFFFFFFF))),
        mp4(FTYP, box(b"moov", b"\x02" + b"\x00" * 3 + b"\x00" * 100)),  # no mvhd box at all
        mp4(FTYP, box(b"moov", box(b"mvhd", b"\x07\x00\x00\x00" + b"\x00" * 100))),  # version 7
        mp4(FTYP, box(b"moov", box(b"mvhd", b"\x00\x00\x00\x00" + b"\x00" * 8))),  # truncated
        mp4(FTYP, box(b"moov", box(b"mvhd", b"\x01\x00\x00\x00" + b"\x00" * 20))),  # truncated v1
    ],
)
def test_malformed_mp4_is_a_content_mismatch(data: bytes) -> None:
    with pytest.raises(AudioDurationError) as raised:
        audio_duration_ms(data, media_type=MP4)
    assert raised.value.code == "UPLOAD_CONTENT_MISMATCH"


def test_a_box_that_leaves_its_container_is_refused() -> None:
    # moov claims more bytes than the file has.
    lying = struct.pack(">I", 10_000) + b"moov" + mvhd_v0(1000, 1000)
    with pytest.raises(AudioDurationError):
        audio_duration_ms(mp4(FTYP, lying), media_type=MP4)
    # a child of moov claims more than moov holds
    child = struct.pack(">I", 500) + b"mvhd" + b"\x00" * 20
    with pytest.raises(AudioDurationError):
        audio_duration_ms(mp4(FTYP, box(b"moov", child)), media_type=MP4)
    # a box smaller than its own header
    with pytest.raises(AudioDurationError):
        audio_duration_ms(mp4(FTYP, struct.pack(">I", 4) + b"free"), media_type=MP4)
    # a 64-bit header that does not fit
    with pytest.raises(AudioDurationError):
        audio_duration_ms(mp4(FTYP, struct.pack(">I", 1) + b"moov"), media_type=MP4)


def test_the_box_count_per_level_is_capped() -> None:
    many = b"".join(box(b"free") for _ in range(module._MAX_BOXES + 1))
    with pytest.raises(AudioDurationError):
        audio_duration_ms(mp4(FTYP, many, box(b"moov", mvhd_v0(1000, 1000))), media_type=MP4)
    within = b"".join(box(b"free") for _ in range(module._MAX_BOXES - 3))
    assert (
        audio_duration_ms(mp4(FTYP, within, box(b"moov", mvhd_v0(1000, 1000))), media_type=MP4)
        == 1000
    )


def test_a_huge_duration_is_a_content_mismatch_not_an_overflow() -> None:
    data = mp4(FTYP, box(b"moov", mvhd_v1(1, 2**62)))
    with pytest.raises(AudioDurationError):
        audio_duration_ms(data, media_type=MP4)


def test_an_unsupported_type_is_refused_and_the_parser_decodes_nothing() -> None:
    with pytest.raises(AudioDurationError):
        audio_duration_ms(b"\x00" * 100, media_type="audio/ogg")
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    for word in ("ffmpeg", "av.open", "subprocess", "modal", "pydub", "soundfile"):
        assert word not in source


def test_the_mp4_signature_in_the_shared_table_matches_the_first_box() -> None:
    assert header_matches_media_type(MP4, FTYP[:16])
    assert not header_matches_media_type(MP4, wav_bytes(100)[:16])
    assert not header_matches_media_type(MP4, b"\x00" * 16)
    assert header_matches_media_type(WAV, wav_bytes(100)[:16])
