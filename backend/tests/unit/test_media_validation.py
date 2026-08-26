from __future__ import annotations

from hashlib import sha256
from math import sin
from pathlib import Path
from struct import pack
from wave import open as wave_open
from zlib import compress

from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.domain.understanding.media_quality import MediaDecision, MediaRecaptureReason
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector


def test_valid_synthetic_media_passes_and_preserves_source_hashes(tmp_path: Path) -> None:
    image = tmp_path / "drawing.png"
    audio = tmp_path / "narration.wav"
    _write_png(
        image,
        160,
        160,
        lambda x, y: (20, 20, 20) if 30 < x < 130 and y % 7 < 3 else (255, 255, 255),
    )
    _write_wav(audio, seconds=1.0, amplitude=0.3)
    before_image = sha256(image.read_bytes()).hexdigest()
    before_audio = sha256(audio.read_bytes()).hexdigest()

    result = _validate(image, audio)

    assert result.decision is MediaDecision.PASS
    assert result.recapture_reasons == ()
    assert result.image.sha256 == before_image
    assert result.audio.sha256 == before_audio
    assert result.image.working_copy_ref is None
    assert result.audio.working_copy_ref is None
    assert sha256(image.read_bytes()).hexdigest() == before_image
    assert sha256(audio.read_bytes()).hexdigest() == before_audio
    assert result.model_dump(mode="json")["contract_version"] == "1.0"


def test_invalid_inputs_return_stable_ordered_recapture_reasons(tmp_path: Path) -> None:
    image = tmp_path / "small-dark.png"
    audio = tmp_path / "silent.wav"
    _write_png(image, 32, 32, lambda _x, _y: (0, 0, 0))
    _write_wav(audio, seconds=0.2, amplitude=0.0)

    first = _validate(image, audio)
    second = _validate(image, audio)

    assert first == second
    assert first.decision is MediaDecision.RECAPTURE
    assert first.recapture_reasons == (
        MediaRecaptureReason.IMAGE_DIMENSIONS_TOO_SMALL,
        MediaRecaptureReason.IMAGE_TOO_DARK,
        MediaRecaptureReason.IMAGE_LOW_CONTRAST,
        MediaRecaptureReason.IMAGE_BLURRY,
        MediaRecaptureReason.IMAGE_FRAMING_RISK,
        MediaRecaptureReason.AUDIO_DURATION_OUT_OF_RANGE,
        MediaRecaptureReason.AUDIO_SILENT,
    )


def test_corrupt_sources_are_reported_as_unreadable(tmp_path: Path) -> None:
    image = tmp_path / "drawing.png"
    audio = tmp_path / "narration.wav"
    image.write_text("not a PNG", encoding="utf-8")
    audio.write_text("not a WAV", encoding="utf-8")

    result = _validate(image, audio)

    assert result.decision is MediaDecision.RECAPTURE
    assert result.recapture_reasons == (
        MediaRecaptureReason.IMAGE_UNREADABLE,
        MediaRecaptureReason.AUDIO_UNREADABLE,
    )


def test_constant_audio_requests_recapture_for_missing_speech_signal(tmp_path: Path) -> None:
    image = tmp_path / "drawing.png"
    audio = tmp_path / "constant.wav"
    _write_valid_image(image)
    _write_constant_wav(audio, seconds=1.0, amplitude=0.2)

    result = _validate(image, audio)

    assert result.decision is MediaDecision.RECAPTURE
    assert result.recapture_reasons == (MediaRecaptureReason.AUDIO_NO_SPEECH_SIGNAL,)


def test_clipped_audio_requests_recapture(tmp_path: Path) -> None:
    image = tmp_path / "drawing.png"
    audio = tmp_path / "clipped.wav"
    _write_valid_image(image)
    _write_wav(audio, seconds=1.0, amplitude=1.0)

    result = _validate(image, audio)

    assert result.decision is MediaDecision.RECAPTURE
    assert result.recapture_reasons == (MediaRecaptureReason.AUDIO_CLIPPING,)


def _validate(image: Path, audio: Path):
    return DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image,
            audio_path=audio,
            image_artifact_ref="fixture:drawing:v1",
            audio_artifact_ref="fixture:narration:v1",
        )
    )


def _write_valid_image(path: Path) -> None:
    _write_png(
        path,
        160,
        160,
        lambda x, y: (20, 20, 20) if 30 < x < 130 and y % 7 < 3 else (255, 255, 255),
    )


def _write_png(path: Path, width: int, height: int, pixel) -> None:
    raw = b"".join(
        b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width)) for y in range(height)
    )
    header = pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return pack(">I", len(data)) + kind + data + pack(">I", 0)


def _write_wav(path: Path, seconds: float, amplitude: float) -> None:
    sample_rate = 16000
    samples = [
        int(amplitude * 32767 * sin(2 * 3.14159265 * 220 * index / sample_rate))
        for index in range(int(sample_rate * seconds))
    ]
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(pack("<h", sample) for sample in samples))


def _write_constant_wav(path: Path, seconds: float, amplitude: float) -> None:
    sample_rate = 16000
    sample = int(amplitude * 32767)
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pack("<h", sample) * int(sample_rate * seconds))
