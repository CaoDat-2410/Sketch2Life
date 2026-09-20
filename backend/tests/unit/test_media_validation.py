from __future__ import annotations

import io
import json
from hashlib import sha256
from io import BufferedReader
from math import sin
from pathlib import Path
from struct import pack
from typing import Literal
from wave import open as wave_open
from zlib import compress, crc32

import av
import pytest

import sketch2life.application.services.media_validation as media_validation_service
from sketch2life.application.ports.image_decoder import (
    ImageDecodeProcessingError,
    ImageDecodeSourceError,
)
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    ImageOnlyStructuralMediaValidator,
    ImageOnlyValidationRequest,
    MediaValidationRequest,
    _image_only_failure_code,
)
from sketch2life.contracts.schemas.media_validation import (
    IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH,
    IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE,
    IMAGE_ONLY_VALIDATION_CHECK_ORDER,
    ImageOnlyArtifactReferenceV1,
    ImageOnlyArtifactVerificationV1,
    ImageOnlyDigestStatus,
    ImageOnlySourceStatus,
    ImageOnlyValidationCheckOutcome,
    ImageOnlyValidationContractError,
    ImageOnlyValidationFailureCode,
    ImageOnlyValidationResultV1,
    ImageOnlyValidationStatus,
    MediaFixtureManifestV1,
    canonical_image_only_validation_bytes,
    image_only_validation_artifact_sha256,
    try_create_image_only_artifact_reference,
    verify_image_only_validation_artifact,
)
from sketch2life.domain.understanding.image_admission import (
    AdmissionReason,
    DecodedFrameSignals,
    ImageMetadataSignals,
)
from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageQualitySignals,
    MediaDecision,
    MediaRecaptureReason,
)
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder
from sketch2life.infrastructure.media_validation.file_inspector import (
    _MAX_MEDIA_BYTES,
    FileMediaSignalInspector,
    _pcm_mono_samples,
)

# SECURITY_VALIDATOR_SYNTHETIC_FIXTURES: BEGIN
_B004_SECRET_TOKEN_LIKE_REFERENCES = (
    'fixture:sk_live_123',
    'fixture:sk_test_123',
    'fixture:pk_live_123',
    'fixture:pk_test_123',
    'fixture:ghp_abc123',
    'fixture:github_pat_abc123',
    'fixture:github_pat_...',
    'fixture:glpat-abc123',
    'fixture:glpat-...',
    'fixture:api_key_live',
    'fixture:apikey_live',
    'fixture:access_key_live',
    'fixture:secret_key_live',
    'fixture:secret_value:v1',
    'fixture:password_123',
    'fixture:passwd123',
    'fixture:credential_secret',
    'fixture:token_abc:v1',
    'fixture:bearer_abc',
    'fixture:jwt_token:v1',
    'fixture:oauth_client',
    'fixture:oauth2-token',
    'fixture:private_key_live',
    'fixture:private-key-live',
    'fixture:begin-private-key',
    'fixture:BEGIN-PRIVATE-KEY',
    '-----BEGIN PRIVATE KEY-----',
    'fixture:mysecret:v1',
    'fixture:mytoken',
    'fixture:authbearer',
    'fixture:access-key-live',
    'fixture:credential-secret',
    'fixture:https://user:password@example.test/drawing.png',
    'https://user:password@example.test/drawing.png',
    'fixture:file://user:password@example.test/drawing.png',
    'fixture:SK_LIVE_123',
    'fixture:GitHub_Pat_ABC123',
    'fixture:API_KEY_LIVE',
    'fixture:Bearer_token',
    'fixture:OAuth_client',
    'fixture:Private_Key',
    'fixture:mySecret:v1',
)

_B004_SOURCE_KINDS = (
    'success',
    'missing',
    'unreadable',
    'decoder',
    'policy',
    'ordinary',
)

_B006_JSON_REFERENCES = (
    'fixture:sk_live_123',
    'fixture:ghp_abc123',
    'fixture:api_key_live',
    'fixture:password_123',
    'fixture:secret_value:v1',
    'fixture:token_abc:v1',
    'fixture:jwt_token:v1',
    'fixture:mysecret:v1',
    'fixture:github_pat_...',
    'fixture:glpat-...',
    'fixture:bearer_abc',
    'fixture:oauth_client',
    'fixture:private_key_live',
    'fixture:private-key-live',
    '-----BEGIN PRIVATE KEY-----',
    '/tmp/drawing.png',
    'https://user:password@example.test/drawing.png',
    'fixture:drawing\n:v1',
    'fixture:drawing\x00:v1',
    'fixture:SK_LIVE_123',
    'fixture:mySecret:v1',
    'fixture:' + ('a' * (IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH + 1)),
)

_B006_JSON_SHAPES = (
    'truncated_object',
    'unterminated_string',
    'unterminated_array',
    'invalid_escape',
    'malformed_field',
    'malformed_utf8',
    'duplicate_fields',
)
# SECURITY_VALIDATOR_SYNTHETIC_FIXTURES: END


def _b006_malformed_json_payload(
    raw_reference: str,
    shape: str,
) -> str | bytes:
    quoted = json.dumps(raw_reference)
    if shape == 'truncated_object':
        return '{"source_artifact_ref":' + quoted
    if shape == 'unterminated_string':
        return '{"source_artifact_ref":"' + raw_reference
    if shape == 'unterminated_array':
        return '{"source_artifact_ref":[' + quoted
    if shape == 'invalid_escape':
        return '{"source_artifact_ref":"' + raw_reference + r'\q"}'
    if shape == 'malformed_field':
        return '{"source_artifact_ref":' + quoted + ',}'
    if shape == 'malformed_utf8':
        return (
            b'{"source_artifact_ref":'
            + quoted.encode('utf-8')
            + b'\xff'
        )
    if shape == 'duplicate_fields':
        return (
            '{"source_artifact_ref":'
            + quoted
            + ',"source_artifact_ref":'
            + quoted
            + '}'
        )
    raise AssertionError(f'unhandled B-006 JSON shape: {shape}')

def _assert_no_raw_contract_diagnostic(
    error: ImageOnlyValidationContractError,
    raw_reference: str,
) -> None:
    structured = error.errors()
    diagnostics = (
        str(error),
        repr(error),
        repr(structured),
        error.json(),
        repr(error.errors(include_context=True)),
        error.json(include_context=True),
    )
    assert all(raw_reference not in diagnostic for diagnostic in diagnostics)
    assert structured[0]['input'] is None
    assert structured[0]['ctx'] == {}
    assert structured[0]['loc'] == ('source_artifact_ref',)
def test_valid_synthetic_media_passes_and_preserves_source_hashes(
    tmp_path: Path,
) -> None:
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


def test_constant_audio_requests_recapture_for_missing_speech_signal(
    tmp_path: Path,
) -> None:
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


def test_full_scale_negative_pcm_is_clipped_without_contract_crash(
    tmp_path: Path,
) -> None:
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
        samples = tuple(
            _pcm_mono_samples(encoded, channels=1, sample_width=sample_width)
        )

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
    manifest_path = (
        Path(__file__).parents[3] / "data/fixtures/manifests/media-validation-v1.json"
    )

    manifest = MediaFixtureManifestV1.model_validate(
        json.loads(manifest_path.read_text())
    )

    assert manifest.contract_name == "MediaFixtureManifestV1"
    assert all(entry.synthetic_data for entry in manifest.fixtures)
    assert all(entry.image_sha256 and entry.audio_sha256 for entry in manifest.fixtures)


def test_oversized_media_is_rejected_before_decode(tmp_path: Path) -> None:
    image = tmp_path / "oversized.png"
    image.write_bytes(b"x" * (_MAX_MEDIA_BYTES + 1))

    signals = FileMediaSignalInspector().inspect_image(image)

    assert signals.width is None
    assert signals.height is None


def test_source_hashing_reads_the_file_in_bounded_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "multi-chunk.bin"
    image.write_bytes(bytes(range(256)) * 10240)
    audio = tmp_path / "narration.wav"
    _write_wav(audio, seconds=1.0, amplitude=0.3)
    expected_digest = sha256(image.read_bytes()).hexdigest()
    requested_sizes: list[int] = []

    def _reject_whole_file_read(self: Path) -> bytes:
        raise AssertionError("source hashing must not read the whole file into memory")

    real_open = Path.open

    def _recording_open(self: Path, mode: Literal["rb"] = "rb") -> _ReadSpy:
        return _ReadSpy(real_open(self, mode), requested_sizes)

    monkeypatch.setattr(Path, "read_bytes", _reject_whole_file_read)
    monkeypatch.setattr(Path, "open", _recording_open)
    result = DeterministicMediaValidator(_StubInspector()).validate(
        MediaValidationRequest(
            image_path=image,
            audio_path=audio,
            image_artifact_ref="fixture:drawing:v1",
            audio_artifact_ref="fixture:narration:v1",
        )
    )

    assert result.image.sha256 == expected_digest
    assert requested_sizes
    assert all(0 < size <= 1024 * 1024 for size in requested_sizes)
    assert len([size for size in requested_sizes if size]) >= 3


def test_source_digests_match_independent_hashes_across_chunk_boundaries(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "narration.wav"
    _write_wav(audio, seconds=1.0, amplitude=0.3)
    payloads = {
        "empty.bin": b"",
        "sub-chunk.bin": b"\x01\x02\x03" * 1024,
        "exact-chunk.bin": b"\x04" * (1024 * 1024),
        "multi-chunk.bin": bytes(range(256)) * 10240,
    }

    for name, payload in payloads.items():
        image = tmp_path / name
        image.write_bytes(payload)

        result = _validate(image, audio)

        assert result.image.sha256 == sha256(payload).hexdigest(), name
        assert result.image.source_status == "AVAILABLE", name


def test_unreadable_source_keeps_its_status_without_a_hash(tmp_path: Path) -> None:
    audio = tmp_path / "narration.wav"
    _write_wav(audio, seconds=1.0, amplitude=0.3)

    result = _validate(tmp_path, audio)

    assert result.image.sha256 is None
    assert result.image.source_status == "UNREADABLE"


def test_serialized_result_and_provenance_hash_stay_byte_identical(
    tmp_path: Path,
) -> None:
    """Guards the digest recorded in benchmark validation provenance.

    The expected value is an independent baseline captured from the previous whole-file
    hashing implementation, not a re-run of the current one.
    """

    image = tmp_path / "drawing.png"
    audio = tmp_path / "narration.wav"
    _write_valid_image(image)
    _write_wav(audio, seconds=1.0, amplitude=0.3)

    serialized = _validate(image, audio).model_dump_json()

    assert sha256(serialized.encode("utf-8")).hexdigest() == (
        "cded7b49413310fe54232ca793693db7d31db999b381908fff4c6521f9dbf5e5"
    )


class _NeverCalledImageDecoder:
    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        raise AssertionError("decoder must not be called")

    def probe_frame_count(self, snapshot: bytes) -> int:
        raise AssertionError("decoder must not be called")

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        raise AssertionError("decoder must not be called")


class _ImageOnlyStubDecoder:
    def __init__(
        self,
        *,
        metadata: ImageMetadataSignals | None = None,
        frame_count: int = 1,
        probe_error: Exception | None = None,
        decode_error: Exception | None = None,
    ) -> None:
        self._metadata = metadata or ImageMetadataSignals(
            "png_pipe", "png", "rgb24", 160, 160
        )
        self._frame_count = frame_count
        self._probe_error = probe_error
        self._decode_error = decode_error

    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        return self._metadata

    def probe_frame_count(self, snapshot: bytes) -> int:
        if self._probe_error is not None:
            raise self._probe_error
        return self._frame_count

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        if self._decode_error is not None:
            raise self._decode_error
        pixel_format = self._metadata.pixel_format
        assert pixel_format is not None
        return DecodedFrameSignals(
            self._metadata.width,
            self._metadata.height,
            pixel_format,
        )


@pytest.mark.parametrize("kind", ["jpeg", "png"])
def test_image_only_valid_jpeg_and_png_pass(kind: str, tmp_path: Path) -> None:
    payload = _image_only_payload(kind)
    result = _validate_image_only(
        tmp_path / f"drawing.{kind}", payload, AvImageDecoder()
    )

    assert result.status is ImageOnlyValidationStatus.PASS
    assert result.failure_code is None
    assert result.source_status is ImageOnlySourceStatus.AVAILABLE
    assert result.digest_status is ImageOnlyDigestStatus.MATCH
    assert result.source_sha256 == sha256(payload).hexdigest()
    assert result.byte_count == len(payload)
    assert result.structural_profile is not None
    assert (
        tuple(check.name for check in result.checks)
        == IMAGE_ONLY_VALIDATION_CHECK_ORDER
    )
    assert all(
        check.outcome is ImageOnlyValidationCheckOutcome.PASS for check in result.checks
    )
    assert "audio" not in result.model_dump(mode="json")


@pytest.mark.parametrize("kind", ["jpeg", "png"])
def test_image_only_jpeg_and_png_are_deterministic(kind: str, tmp_path: Path) -> None:
    payload = _image_only_payload(kind)
    first = _validate_image_only(tmp_path / f"first.{kind}", payload, AvImageDecoder())
    second = _validate_image_only(
        tmp_path / f"second.{kind}", payload, AvImageDecoder()
    )

    assert first == second
    assert canonical_image_only_validation_bytes(first) == (
        canonical_image_only_validation_bytes(second)
    )
    assert image_only_validation_artifact_sha256(first) == (
        image_only_validation_artifact_sha256(second)
    )


def test_image_only_source_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    payload = _png_payload(160, 160)
    path = tmp_path / "drawing.png"
    path.write_bytes(payload)
    result = ImageOnlyStructuralMediaValidator(AvImageDecoder()).validate(
        ImageOnlyValidationRequest(path, "fixture-b01", "0" * 64)
    )

    assert result.failure_code is ImageOnlyValidationFailureCode.SOURCE_DIGEST_MISMATCH
    assert result.digest_status is ImageOnlyDigestStatus.MISMATCH
    _assert_no_partial_success(result)


def test_image_only_missing_and_unreadable_sources_are_typed(tmp_path: Path) -> None:
    validator = ImageOnlyStructuralMediaValidator(_NeverCalledImageDecoder())
    missing = validator.validate(
        ImageOnlyValidationRequest(tmp_path / "missing.png", "fixture-b01", "0" * 64)
    )
    unreadable = validator.validate(
        ImageOnlyValidationRequest(tmp_path, "fixture-b01", "0" * 64)
    )

    assert missing.failure_code is ImageOnlyValidationFailureCode.MISSING_SOURCE
    assert missing.source_status is ImageOnlySourceStatus.MISSING
    assert unreadable.failure_code is ImageOnlyValidationFailureCode.UNREADABLE_IMAGE
    assert unreadable.source_status is ImageOnlySourceStatus.UNREADABLE
    _assert_no_partial_success(missing)
    _assert_no_partial_success(unreadable)


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        (
            ImageMetadataSignals("gif", "png", "rgb24", 160, 160),
            ImageOnlyValidationFailureCode.UNSUPPORTED_CONTAINER,
        ),
        (
            ImageMetadataSignals("png_pipe", "gif", "rgb24", 160, 160),
            ImageOnlyValidationFailureCode.UNSUPPORTED_CODEC,
        ),
        (
            ImageMetadataSignals("png_pipe", "png", "rgb48le", 160, 160),
            ImageOnlyValidationFailureCode.UNSUPPORTED_PIXEL_FORMAT,
        ),
    ],
)
def test_image_only_unsupported_profiles_are_typed(
    tmp_path: Path,
    metadata: ImageMetadataSignals,
    expected: ImageOnlyValidationFailureCode,
) -> None:
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(metadata=metadata),
    )
    assert result.failure_code is expected
    _assert_no_partial_success(result)


@pytest.mark.parametrize("payload", [b"not-an-image", b"\x89PNG\r\n\x1a\n"])
def test_image_only_corrupt_and_truncated_inputs_fail(
    tmp_path: Path,
    payload: bytes,
) -> None:
    result = _validate_image_only(tmp_path / "broken.bin", payload, AvImageDecoder())
    assert result.failure_code is ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED
    _assert_no_partial_success(result)


def test_image_only_oversized_input_stops_before_decode(tmp_path: Path) -> None:
    path = tmp_path / "oversized.bin"
    path.write_bytes(b"x" * 5_000_001)
    result = ImageOnlyStructuralMediaValidator(_NeverCalledImageDecoder()).validate(
        ImageOnlyValidationRequest(path, "fixture-b01", "0" * 64)
    )
    assert result.failure_code is ImageOnlyValidationFailureCode.INPUT_TOO_LARGE
    assert result.source_status is ImageOnlySourceStatus.TOO_LARGE
    assert result.source_sha256 is None
    assert result.byte_count is None


@pytest.mark.parametrize(
    ("decoder", "expected"),
    [
        (
            _ImageOnlyStubDecoder(frame_count=2),
            ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED,
        ),
        (
            _ImageOnlyStubDecoder(
                metadata=ImageMetadataSignals("png_pipe", "png", "rgb24", 2000, 2001)
            ),
            ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
        ),
        (
            _ImageOnlyStubDecoder(
                metadata=ImageMetadataSignals("png_pipe", "png", "rgb24", 4097, 1)
            ),
            ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
        ),
    ],
)
def test_image_only_frame_pixel_and_edge_limits_fail(
    tmp_path: Path,
    decoder: object,
    expected: ImageOnlyValidationFailureCode,
) -> None:
    result = _validate_image_only(tmp_path / "input.bin", b"bounded-source", decoder)
    assert result.failure_code is expected
    _assert_no_partial_success(result)


@pytest.mark.parametrize(
    ("phase", "error", "expected"),
    [
        (
            "probe",
            ImageDecodeSourceError("secret source detail"),
            ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED,
        ),
        (
            "probe",
            ImageDecodeProcessingError("secret processing detail"),
            ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
        ),
        (
            "decode",
            ImageDecodeSourceError("secret source detail"),
            ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED,
        ),
        (
            "decode",
            ImageDecodeProcessingError("secret processing detail"),
            ImageOnlyValidationFailureCode.VALIDATOR_EXCEPTION,
        ),
    ],
)
def test_image_only_decoder_source_and_processing_failures_are_sanitized(
    tmp_path: Path,
    phase: str,
    error: Exception,
    expected: ImageOnlyValidationFailureCode,
) -> None:
    decoder = _ImageOnlyStubDecoder(
        probe_error=error if phase == "probe" else None,
        decode_error=error if phase == "decode" else None,
    )
    result = _validate_image_only(
        tmp_path / "secret-name.bin", b"bounded-source", decoder
    )
    serialized = canonical_image_only_validation_bytes(result)

    assert result.failure_code is expected
    assert b"secret" not in serialized
    assert str(tmp_path).encode() not in serialized
    _assert_no_partial_success(result)


def test_image_only_reference_value_object_accepts_only_approved_fixture_ids() -> None:
    accepted = (
        'fixture-b01',
        'fixture-b08',
        'fixture:drawing:v1',
        'fixture:small-dark-drawing:v1',
        'fixture:corrupt-drawing:v1',
        IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE,
    )
    for raw_reference in accepted:
        reference = try_create_image_only_artifact_reference(raw_reference)
        assert reference is not None
        assert reference.value == raw_reference

    maximum = 'fixture:' + ('a' * 63) + ':' + ('b' * 56)
    assert len(maximum) == IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH

    rejected = (
        '',
        ' ',
        ' fixture-b01',
        'fixture-b01 ',
        '/tmp/drawing.png',
        r'C:\images\drawing.png',
        r'\\server\share\drawing.png',
        '../fixture-b01',
        r'..\fixture-b01',
        'file://drawing.png',
        'http://example.test/drawing.png',
        'https://example.test/drawing.png',
        'fixture:drawing?v1',
        'fixture:drawing#v1',
        'https://user:password@example.test/drawing.png',
        'fixture:valid:v1',
        maximum,
        'fixture:' + ('a' * (IMAGE_ONLY_ARTIFACT_REFERENCE_MAX_LENGTH + 1)),
        'fixture:drawing:\u2603:v1',
        'fixture:drawing\n:v1',
        'fixture:drawing\x00:v1',
        None,
        123,
    ) + _B004_SECRET_TOKEN_LIKE_REFERENCES

    for raw_reference in rejected:
        assert try_create_image_only_artifact_reference(raw_reference) is None
        if isinstance(raw_reference, str):
            with pytest.raises(ValueError, match='invalid image-only artifact reference') as error:
                ImageOnlyArtifactReferenceV1(raw_reference)
            if raw_reference.strip():
                assert raw_reference not in str(error.value)

        result = ImageOnlyStructuralMediaValidator(_NeverCalledImageDecoder()).validate(
            ImageOnlyValidationRequest(Path('not-read.bin'), raw_reference, '0' * 64)
        )
        serialized = canonical_image_only_validation_bytes(result)
        digest = image_only_validation_artifact_sha256(result)
        assert result.status is ImageOnlyValidationStatus.FAIL
        assert result.failure_code is ImageOnlyValidationFailureCode.MALFORMED_RESULT
        assert result.source_artifact_ref == IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE
        assert result.structural_profile is None
        assert result.digest_status is ImageOnlyDigestStatus.NOT_COMPUTED
        if isinstance(raw_reference, str) and raw_reference.strip():
            assert raw_reference not in result.model_dump_json()
            assert raw_reference.encode('utf-8') not in serialized
            assert raw_reference not in digest
            assert raw_reference not in str(result)


@pytest.mark.parametrize('raw_reference', _B004_SECRET_TOKEN_LIKE_REFERENCES)
@pytest.mark.parametrize('source_kind', _B004_SOURCE_KINDS)
def test_image_only_b004_references_are_rejected_before_every_validation_path(
    tmp_path: Path,
    raw_reference: str,
    source_kind: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / 'input.bin'
    if source_kind in {'success', 'decoder', 'policy'}:
        path.write_bytes(_image_only_payload('png'))
    elif source_kind == 'ordinary':
        path.write_bytes(b'not-an-image')
    elif source_kind == 'unreadable':
        path = tmp_path

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError('rejected references must stop before validation work')

    for name in (
        '_read_bounded_snapshot',
        'evaluate_image_only_metadata',
        'evaluate_image_only_frame_count',
        'evaluate_image_only_cross_check',
    ):
        monkeypatch.setattr(media_validation_service, name, _forbidden)

    if source_kind == 'decoder':
        decoder: object = _ImageOnlyStubDecoder(
            probe_error=ImageDecodeSourceError('decoder secret detail')
        )
    elif source_kind == 'policy':
        decoder = _ImageOnlyStubDecoder(
            metadata=ImageMetadataSignals('gif', 'png', 'rgb24', 160, 160)
        )
    else:
        decoder = _NeverCalledImageDecoder()

    validator = ImageOnlyStructuralMediaValidator(decoder)  # type: ignore[arg-type]
    with caplog.at_level('DEBUG'):
        result = validator.validate(
            ImageOnlyValidationRequest(path, raw_reference, '0' * 64)
        )

    serialized = canonical_image_only_validation_bytes(result)
    digest = image_only_validation_artifact_sha256(result)
    assert result.status is ImageOnlyValidationStatus.FAIL
    assert result.failure_code is ImageOnlyValidationFailureCode.MALFORMED_RESULT
    assert result.source_artifact_ref == IMAGE_ONLY_REJECTED_ARTIFACT_REFERENCE
    assert result.source_status is ImageOnlySourceStatus.MISSING
    assert result.digest_status is ImageOnlyDigestStatus.NOT_COMPUTED
    assert result.source_sha256 is None
    assert result.byte_count is None
    assert result.structural_profile is None
    assert b'"status":"PASS"' not in serialized
    assert raw_reference not in result.model_dump_json()
    assert raw_reference.encode('utf-8') not in serialized
    assert raw_reference not in digest
    assert raw_reference not in repr(result)
    assert raw_reference not in str(result)
    assert raw_reference not in caplog.text

    with pytest.raises(ValueError) as constructor_error:
        ImageOnlyArtifactReferenceV1(raw_reference)
    assert raw_reference not in str(constructor_error.value)

    invalid_result = result.model_dump(mode='json')
    invalid_result['source_artifact_ref'] = raw_reference
    validation_calls = (
        lambda: ImageOnlyValidationResultV1(**invalid_result),
        lambda: ImageOnlyValidationResultV1.model_validate(invalid_result),
        lambda: ImageOnlyValidationResultV1.model_validate_json(
            json.dumps(invalid_result)
        ),
    )
    for validate in validation_calls:
        with pytest.raises(ImageOnlyValidationContractError) as contract_error:
            validate()
        assert type(contract_error.value) is ImageOnlyValidationContractError
        _assert_no_raw_contract_diagnostic(contract_error.value, raw_reference)

    invalid_payload = json.dumps(invalid_result).encode('utf-8')
    verification = verify_image_only_validation_artifact(
        invalid_payload,
        sha256(invalid_payload).hexdigest(),
    )
    assert verification.failure_code is ImageOnlyValidationFailureCode.MALFORMED_RESULT
    assert raw_reference not in repr(verification)
    assert raw_reference not in verification.model_dump_json()


@pytest.mark.parametrize('raw_reference', _B006_JSON_REFERENCES)
@pytest.mark.parametrize('shape', _B006_JSON_SHAPES)
def test_image_only_b006_malformed_json_diagnostics_are_sanitized(
    raw_reference: str,
    shape: str,
) -> None:
    payload = _b006_malformed_json_payload(raw_reference, shape)
    validators = (
        ImageOnlyValidationResultV1.model_validate_json,
        ImageOnlyArtifactVerificationV1.model_validate_json,
    )
    for validate in validators:
        with pytest.raises(ImageOnlyValidationContractError) as error:
            validate(payload)
        _assert_no_raw_contract_diagnostic(error.value, raw_reference)

def test_image_only_b006_oversized_json_diagnostic_is_sanitized() -> None:
    raw_reference = 'fixture:sk_live_123'
    payload = json.dumps(
        {
            'source_artifact_ref': raw_reference,
            'padding': 'x' * 1_000_001,
        }
    )
    assert len(payload.encode('utf-8')) > 1_000_000
    with pytest.raises(ImageOnlyValidationContractError) as error:
        ImageOnlyValidationResultV1.model_validate_json(payload)
    _assert_no_raw_contract_diagnostic(error.value, raw_reference)


@pytest.mark.parametrize(
    'artifact_ref',
    (
        'fixture-b01',
        'fixture-b08',
        'fixture:drawing:v1',
        'fixture:small-dark-drawing:v1',
        'fixture:corrupt-drawing:v1',
    ),
)
def test_image_only_b006_valid_json_fixture_references_remain_accepted(
    tmp_path: Path,
    artifact_ref: str,
) -> None:
    result = _validate_image_only(
        tmp_path / 'drawing.bin',
        b'bounded-source',
        _ImageOnlyStubDecoder(),
        artifact_ref=artifact_ref,
    )
    parsed = ImageOnlyValidationResultV1.model_validate_json(
        result.model_dump_json()
    )
    assert parsed == result
    verification = ImageOnlyArtifactVerificationV1.model_validate_json(
        json.dumps(
            {
                'status': 'PASS',
                'failure_code': None,
                'result': result.model_dump(mode='json'),
            }
        )
    )
    assert verification.result == result

@pytest.mark.parametrize(
    'artifact_ref',
    (
        'fixture-b01',
        'fixture-b08',
        'fixture:drawing:v1',
        'fixture:small-dark-drawing:v1',
        'fixture:corrupt-drawing:v1',
    ),
)
def test_image_only_approved_fixture_references_pass_normally(
    tmp_path: Path,
    artifact_ref: str,
) -> None:
    result = _validate_image_only(
        tmp_path / 'drawing.bin',
        b'bounded-source',
        _ImageOnlyStubDecoder(),
        artifact_ref=artifact_ref,
    )
    assert result.status is ImageOnlyValidationStatus.PASS
    assert result.source_artifact_ref == artifact_ref

def test_image_only_contract_rejects_malformed_and_extra_fields(tmp_path: Path) -> None:
    valid = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    missing_profile = valid.model_dump(mode="json")
    missing_profile["structural_profile"] = None
    with pytest.raises(ImageOnlyValidationContractError) as missing_error:
        ImageOnlyValidationResultV1.model_validate(missing_profile)
    _assert_no_raw_contract_diagnostic(missing_error.value, "complete and consistent")

    extra_field = valid.model_dump(mode="json")
    extra_field["unexpected"] = "forbidden"
    with pytest.raises(ImageOnlyValidationContractError) as extra_error:
        ImageOnlyValidationResultV1.model_validate(extra_field)
    _assert_no_raw_contract_diagnostic(extra_error.value, "forbidden")


def test_image_only_result_contract_hides_rejected_reference_input(
    tmp_path: Path,
) -> None:
    valid = _validate_image_only(
        tmp_path / 'input.bin',
        b'bounded-source',
        _ImageOnlyStubDecoder(),
    )
    raw_reference = r'C:\secret\drawing.png'
    invalid_reference = valid.model_dump(mode='json')
    invalid_reference['source_artifact_ref'] = raw_reference
    with pytest.raises(ImageOnlyValidationContractError) as error:
        ImageOnlyValidationResultV1.model_validate(invalid_reference)
    _assert_no_raw_contract_diagnostic(error.value, raw_reference)


def test_image_only_canonical_serialization_and_hash_verification(
    tmp_path: Path,
) -> None:
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    canonical = canonical_image_only_validation_bytes(result)
    digest = image_only_validation_artifact_sha256(result)

    assert canonical == result.model_dump_json(
        by_alias=False,
        exclude_none=False,
        indent=None,
    ).encode("utf-8")
    assert verify_image_only_validation_artifact(canonical, digest).result == result
    hash_failure = verify_image_only_validation_artifact(canonical, "0" * 64)
    assert hash_failure.failure_code is (
        ImageOnlyValidationFailureCode.SERIALIZATION_HASH_MISMATCH
    )

    noncanonical = result.model_dump_json(indent=2).encode('utf-8')
    serialization_failure = verify_image_only_validation_artifact(
        noncanonical,
        sha256(noncanonical).hexdigest(),
    )
    assert serialization_failure.failure_code is (
        ImageOnlyValidationFailureCode.SERIALIZATION_HASH_MISMATCH
    )
    malformed = b"{not-json}"
    malformed_failure = verify_image_only_validation_artifact(
        malformed,
        sha256(malformed).hexdigest(),
    )
    assert (
        malformed_failure.failure_code
        is ImageOnlyValidationFailureCode.MALFORMED_RESULT
    )


def test_image_only_failure_mapping_is_exact_and_exhaustive() -> None:
    expected = {
        AdmissionReason.FILE_BYTES_EXCEEDED: ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
        AdmissionReason.PIXEL_BUDGET_EXCEEDED: ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
        AdmissionReason.LONGEST_EDGE_EXCEEDED: ImageOnlyValidationFailureCode.INPUT_TOO_LARGE,
        AdmissionReason.MULTIPLE_FRAMES: ImageOnlyValidationFailureCode.CORRUPT_OR_TRUNCATED,
        AdmissionReason.UNSUPPORTED_CONTAINER: (
            ImageOnlyValidationFailureCode.UNSUPPORTED_CONTAINER
        ),
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

    assert set(expected) == set(AdmissionReason)
    assert {
        reason: _image_only_failure_code(reason) for reason in AdmissionReason
    } == expected


def test_image_only_request_result_and_serialization_have_no_audio(
    tmp_path: Path,
) -> None:
    request_fields = set(ImageOnlyValidationRequest.__dataclass_fields__)
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    serialized = canonical_image_only_validation_bytes(result)

    assert all("audio" not in field for field in request_fields)
    assert all(
        "audio" not in field for field in ImageOnlyValidationResultV1.model_fields
    )
    assert b"audio" not in serialized.lower()


_B006_MAPPING_REFERENCES = _B006_JSON_REFERENCES[:8]


@pytest.mark.parametrize("raw_reference", _B006_MAPPING_REFERENCES)
@pytest.mark.parametrize("model_kind", ["result", "verification"])
@pytest.mark.parametrize("mutation", ["extra", "wrong_type"])
def test_image_only_b006_mapping_diagnostics_are_sanitized(
    tmp_path: Path,
    raw_reference: str,
    model_kind: str,
    mutation: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    result_mapping = result.model_dump(mode="json")
    if model_kind == "result":
        mapping: dict[str, object] = result_mapping
        if mutation == "extra":
            mapping["unexpected"] = raw_reference
        else:
            mapping["byte_count"] = raw_reference
        validate = ImageOnlyValidationResultV1.model_validate
    else:
        mapping = {
            "status": "PASS",
            "failure_code": None,
            "result": result_mapping,
        }
        if mutation == "extra":
            mapping["unexpected"] = raw_reference
        else:
            mapping["failure_code"] = raw_reference
        validate = ImageOnlyArtifactVerificationV1.model_validate

    with caplog.at_level("DEBUG"), pytest.raises(
        ImageOnlyValidationContractError
    ) as error:
        validate(mapping)
    _assert_no_raw_contract_diagnostic(error.value, raw_reference)
    assert raw_reference not in caplog.text


@pytest.mark.parametrize("model_kind", ["result", "verification"])
def test_image_only_b006_direct_valid_mappings_remain_accepted(
    tmp_path: Path,
    model_kind: str,
) -> None:
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    result_mapping = result.model_dump(mode="json")
    if model_kind == "result":
        parsed = ImageOnlyValidationResultV1.model_validate(result_mapping)
        assert parsed == result
    else:
        verification = ImageOnlyArtifactVerificationV1.model_validate(
            {
                "status": "PASS",
                "failure_code": None,
                "result": result_mapping,
            }
        )
        assert verification.result == result


@pytest.mark.parametrize("model_kind", ["result", "verification"])
def test_image_only_b006_malformed_source_reference_mapping_is_sanitized(
    tmp_path: Path,
    model_kind: str,
) -> None:
    raw_reference = r"C:\secret\drawing.png"
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    result_mapping = result.model_dump(mode="json")
    result_mapping["source_artifact_ref"] = raw_reference
    if model_kind == "result":
        mapping = result_mapping
        validate = ImageOnlyValidationResultV1.model_validate
    else:
        mapping = {
            "status": "PASS",
            "failure_code": None,
            "result": result_mapping,
        }
        validate = ImageOnlyArtifactVerificationV1.model_validate

    with pytest.raises(ImageOnlyValidationContractError) as error:
        validate(mapping)
    _assert_no_raw_contract_diagnostic(error.value, raw_reference)


@pytest.mark.parametrize("model_kind", ["result", "verification"])
@pytest.mark.parametrize("mutation", ["extra", "wrong_type"])
def test_image_only_b006_nonsensitive_mapping_rejection_is_sanitized(
    tmp_path: Path,
    model_kind: str,
    mutation: str,
) -> None:
    raw_value = "forbidden" if mutation == "extra" else "not-a-byte-count"
    result = _validate_image_only(
        tmp_path / "input.bin",
        b"bounded-source",
        _ImageOnlyStubDecoder(),
    )
    result_mapping = result.model_dump(mode="json")
    if model_kind == "result":
        mapping: dict[str, object] = result_mapping
        if mutation == "extra":
            mapping["unexpected"] = raw_value
        else:
            mapping["byte_count"] = raw_value
        validate = ImageOnlyValidationResultV1.model_validate
    else:
        mapping = {
            "status": "PASS",
            "failure_code": None,
            "result": result_mapping,
        }
        if mutation == "extra":
            mapping["unexpected"] = raw_value
        else:
            mapping["failure_code"] = raw_value
        validate = ImageOnlyArtifactVerificationV1.model_validate

    with pytest.raises(ImageOnlyValidationContractError) as error:
        validate(mapping)
    _assert_no_raw_contract_diagnostic(error.value, raw_value)

def _validate_image_only(
    path: Path,
    payload: bytes,
    decoder: object,
    *,
    artifact_ref: str = "fixture-b01",
) -> ImageOnlyValidationResultV1:
    path.write_bytes(payload)
    return ImageOnlyStructuralMediaValidator(decoder).validate(  # type: ignore[arg-type]
        ImageOnlyValidationRequest(
            image_path=path,
            image_artifact_ref=artifact_ref,
            expected_source_sha256=sha256(payload).hexdigest(),
        )
    )

def _validate_image_only_reference(
    path: Path,
    payload: bytes,
    decoder: object,
    artifact_ref: str,
) -> ImageOnlyValidationResultV1:
    path.write_bytes(payload)
    return ImageOnlyStructuralMediaValidator(decoder).validate(  # type: ignore[arg-type]
        ImageOnlyValidationRequest(
            image_path=path,
            image_artifact_ref=artifact_ref,
            expected_source_sha256=sha256(payload).hexdigest(),
        )
    )


def _assert_no_partial_success(result: ImageOnlyValidationResultV1) -> None:
    serialized = canonical_image_only_validation_bytes(result)
    assert result.status is ImageOnlyValidationStatus.FAIL
    assert result.structural_profile is None
    assert b'"status":"PASS"' not in serialized
    assert b'"structural_profile":null' in serialized


def _image_only_payload(kind: str) -> bytes:
    if kind == "jpeg":
        return _jpeg_payload(160, 160)
    return _png_payload(160, 160)


def _jpeg_payload(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format="mjpeg") as container:
        stream = container.add_stream("mjpeg", rate=1)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuvj420p"
        frame = av.VideoFrame(width, height, "rgb24")
        plane = frame.planes[0]
        row = bytes([128, 128, 128]) * width
        plane.update((row + b"\x00" * (plane.line_size - len(row))) * height)
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return buffer.getvalue()


class _ReadSpy:
    """Records every size requested from the wrapped binary file object."""

    def __init__(self, source: BufferedReader, requested_sizes: list[int]) -> None:
        self._source = source
        self._requested_sizes = requested_sizes

    def read(self, size: int = -1) -> bytes:
        self._requested_sizes.append(size)
        return self._source.read(size)

    def __enter__(self) -> _ReadSpy:
        return self

    def __exit__(self, *exception: object) -> None:
        self._source.close()


class _StubInspector:
    """Keeps the read spy scoped to hashing; the real inspector reads files itself."""

    def inspect_image(self, path: Path) -> ImageQualitySignals:
        return ImageQualitySignals(160, 160, 200.0, 60.0, 8.0, 0.1)

    def inspect_audio(self, path: Path) -> AudioQualitySignals:
        return AudioQualitySignals(1.0, 16000, 1, 0.2, 0.0, 0.9, 0.1)


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
        b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width))
        for y in range(height)
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
        payload = payload[: -len(_png_chunk(b"IDAT", compress(raw)))] + _png_chunk(
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
