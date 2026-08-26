from __future__ import annotations

import json
from hashlib import sha256
from math import sin
from pathlib import Path
from struct import pack
from wave import open as wave_open
from zlib import compress, crc32

from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.contracts.schemas.media_validation import MediaFixtureManifestV1
from sketch2life.domain.understanding.media_quality import MediaDecision, MediaRecaptureReason
from sketch2life.infrastructure.media_validation.file_inspector import (
    _MAX_MEDIA_BYTES,
    FileMediaSignalInspector,
    _pcm_mono_samples,
)


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
    assert result.recapture_message == "Media quality passed"
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
    assert "Retake the drawing at a larger size" in first.recapture_message


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


def test_full_scale_negative_pcm_is_clipped_without_contract_crash(tmp_path: Path) -> None:
    image = tmp_path / "drawing.png"
    audio = tmp_path / "negative-full-scale.wav"
    _write_valid_image(image)
    _write_pcm_wav(audio, sample_width=2, encoded_sample=b"\x00\x80")

    result = _validate(image, audio)

    assert result.decision is MediaDecision.RECAPTURE
    assert result.recapture_reasons == (
        MediaRecaptureReason.AUDIO_NO_SPEECH_SIGNAL,
        MediaRecaptureReason.AUDIO_CLIPPING,
    )
    assert result.audio_signals.rms == 1


def test_negative_full_scale_pcm_is_bounded_for_supported_sample_widths() -> None:
    encoded_samples = {
        1: b"\x00",
        2: b"\x00\x80",
        3: b"\x00\x00\x80",
        4: b"\x00\x00\x00\x80",
    }

    for sample_width, encoded in encoded_samples.items():
        samples = tuple(_pcm_mono_samples(encoded, channels=1, sample_width=sample_width))

        assert len(samples) == 1
        assert -1 <= samples[0] <= 1
        assert samples[0] == -1


def test_malformed_pngs_are_reported_as_unreadable(tmp_path: Path) -> None:
    audio = tmp_path / "narration.wav"
    _write_wav(audio, seconds=1.0, amplitude=0.3)
    for name, image_bytes in {
        "zero-dimensions.png": _png_payload(0, 160),
        "bad-crc.png": _png_payload(160, 160, corrupt_crc=True),
        "missing-iend.png": _png_payload(160, 160, include_iend=False),
    }.items():
        image = tmp_path / name
        image.write_bytes(image_bytes)

        result = _validate(image, audio)

        assert result.recapture_reasons == (MediaRecaptureReason.IMAGE_UNREADABLE,)


def test_missing_source_has_no_fake_path_hash(tmp_path: Path) -> None:
    image = tmp_path / "missing.png"
    audio = tmp_path / "missing.wav"

    result = _validate(image, audio)

    assert result.image.sha256 is None
    assert result.audio.sha256 is None
    assert result.image.source_status == "MISSING"
    assert result.audio.source_status == "MISSING"


def test_checked_in_fixture_manifest_matches_its_versioned_contract() -> None:
    manifest_path = Path(__file__).parents[3] / "data/fixtures/manifests/media-validation-v1.json"

    manifest = MediaFixtureManifestV1.model_validate(json.loads(manifest_path.read_text()))

    assert manifest.contract_name == "MediaFixtureManifestV1"
    assert all(entry.synthetic_data for entry in manifest.fixtures)
    assert all(entry.image_sha256 and entry.audio_sha256 for entry in manifest.fixtures)


def test_oversized_media_is_rejected_before_decode(tmp_path: Path) -> None:
    image = tmp_path / "oversized.png"
    image.write_bytes(b"x" * (_MAX_MEDIA_BYTES + 1))

    signals = FileMediaSignalInspector().inspect_image(image)

    assert signals.width is None
    assert signals.height is None


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
    path.write_bytes(_png_payload(width, height, pixel=pixel))


def _png_payload(
    width: int,
    height: int,
    pixel=lambda _x, _y: (20, 20, 20),
    *,
    corrupt_crc: bool = False,
    include_iend: bool = True,
) -> bytes:
    raw = b"".join(
        b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width)) for y in range(height)
    )
    header = pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", compress(raw))
    )
    if include_iend:
        payload += _png_chunk(b"IEND", b"", corrupt_crc=corrupt_crc)
    elif corrupt_crc:
        payload = payload[:-len(_png_chunk(b"IDAT", compress(raw)))] + _png_chunk(
            b"IDAT", compress(raw), corrupt_crc=True
        )
    return payload


def _png_chunk(kind: bytes, data: bytes, *, corrupt_crc: bool = False) -> bytes:
    checksum = crc32(kind + data) & 0xFFFFFFFF
    if corrupt_crc:
        checksum ^= 1
    return pack(">I", len(data)) + kind + data + pack(">I", checksum)


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


def _write_pcm_wav(path: Path, sample_width: int, encoded_sample: bytes) -> None:
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(sample_width)
        output.setframerate(16000)
        output.writeframes(encoded_sample * 16000)
