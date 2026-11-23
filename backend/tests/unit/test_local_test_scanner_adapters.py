"""T-2z: local/test allowlist scanner and signature media validator (TD-29)."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScannerUnavailable,
    scanner_identity_sha256,
)
from sketch2life.application.ports.upload_validation import (
    DOCX_MEDIA_TYPE,
    PPTX_MEDIA_TYPE,
    UploadMediaRejected,
    header_matches_media_type,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.documents.clamav_scanner import ClamAvScanner
from sketch2life.infrastructure.documents.factory import (
    build_document_scanner,
    build_upload_media_validator,
)
from sketch2life.infrastructure.documents.local_test_adapters import (
    LOCAL_SCANNER_NAME,
    MAX_ALLOWLIST_ENTRIES,
    NOT_ALLOWLISTED_CODE,
    LocalAdapterRefused,
    LocalTestAllowlistScanner,
    LocalTestSignatureMediaValidator,
    load_allowlist_file,
)
from tests.synthetic_upload_fixtures import (
    synthetic_jpeg_prefix,
    synthetic_pdf,
    synthetic_png,
    synthetic_uploads,
    synthetic_wav,
    synthetic_webp_prefix,
    synthetic_zip_prefix,
)

PNG = synthetic_png()
PNG_SHA = hashlib.sha256(PNG).hexdigest()
OTHER_SHA = hashlib.sha256(b"another synthetic file").hexdigest()


def _many(count: int) -> list[str]:
    return [hashlib.sha256(str(index).encode()).hexdigest() for index in range(count)]


def _scanner(*allowed: str, env: str = "test") -> LocalTestAllowlistScanner:
    return LocalTestAllowlistScanner(env=env, allowed_sha256=allowed or (PNG_SHA,))


class _UnseekableStream(BytesIO):
    def seek(self, *args: object, **kwargs: object) -> int:
        raise OSError("not seekable")


class _FailingReadStream(BytesIO):
    def read(self, size: int | None = -1) -> bytes:
        raise OSError("read failed")


class _TrackingStream(BytesIO):
    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        self.read_sizes: list[int | None] = []

    def read(self, size: int | None = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


def test_allowlisted_hash_is_clean_with_identity() -> None:
    scanner = _scanner()
    result = scanner.scan(BytesIO(PNG))

    assert result.verdict == "CLEAN"
    assert result.scanner_name == LOCAL_SCANNER_NAME == "local-test-allowlist"
    assert result.scanner_version.startswith("1+allowlist-")
    assert len(result.scanner_version) <= 128
    assert len(result.scanner_name) <= 64
    assert result.scanner_version == scanner.scanner_version
    identity = scanner_identity_sha256(result.scanner_name, result.scanner_version)
    assert len(identity) == 64
    assert (
        identity
        == hashlib.sha256(f"{result.scanner_name}\0{result.scanner_version}".encode()).hexdigest()
    )


def test_result_carries_no_third_scanner_hash_field() -> None:
    result = _scanner().scan(BytesIO(PNG))

    assert not hasattr(result, "scanner_sha256")
    assert {slot for slot in type(result).__slots__} == {
        "scanner_name",
        "scanner_version",
        "verdict",
    }


def test_version_depends_on_the_allowlist_content_not_its_order() -> None:
    first = _scanner(PNG_SHA, OTHER_SHA)
    second = LocalTestAllowlistScanner(env="local", allowed_sha256=[OTHER_SHA, PNG_SHA])
    third = _scanner(PNG_SHA)

    assert first.scanner_version == second.scanner_version
    assert first.scanner_version != third.scanner_version


def test_unlisted_hash_fails_closed_without_leaking_anything() -> None:
    scanner = _scanner(OTHER_SHA)

    with pytest.raises(MalwareDetected) as caught:
        scanner.scan(BytesIO(PNG))

    assert str(caught.value) == NOT_ALLOWLISTED_CODE == "LOCAL_TEST_HASH_NOT_ALLOWLISTED"
    assert PNG_SHA not in repr(caught.value)
    assert OTHER_SHA not in repr(caught.value)


def test_stream_position_is_zero_before_and_after_even_when_it_starts_elsewhere() -> None:
    scanner = _scanner()
    stream = BytesIO(PNG)
    stream.seek(7)

    assert scanner.scan(stream).verdict == "CLEAN"
    assert stream.tell() == 0

    stream.seek(5)
    with pytest.raises(MalwareDetected):
        _scanner(OTHER_SHA).scan(stream)
    assert stream.tell() == 0


def test_large_stream_is_read_in_bounded_chunks() -> None:
    payload = b"synthetic-large-" * 20_000  # 320,000 bytes
    stream = _TrackingStream(payload)
    scanner = _scanner(hashlib.sha256(payload).hexdigest())

    assert scanner.scan(stream).verdict == "CLEAN"
    assert stream.read_sizes
    assert all(size == 64 * 1024 for size in stream.read_sizes)
    assert len(stream.read_sizes) > 4


def test_empty_file_is_hashed_like_any_other_file() -> None:
    empty_sha = hashlib.sha256(b"").hexdigest()

    assert _scanner(empty_sha).scan(BytesIO(b"")).verdict == "CLEAN"
    with pytest.raises(MalwareDetected):
        _scanner(PNG_SHA).scan(BytesIO(b""))


@pytest.mark.parametrize("stream_type", [_UnseekableStream, _FailingReadStream])
def test_unreadable_stream_is_scanner_unavailable(stream_type: type[BytesIO]) -> None:
    with pytest.raises(MalwareScannerUnavailable) as caught:
        _scanner().scan(stream_type(PNG))

    assert PNG_SHA not in str(caught.value)


@pytest.mark.parametrize("env", ["staging", "production", "", "prod", "LOCAL"])
def test_both_classes_refuse_outside_local_and_test(env: str) -> None:
    with pytest.raises(LocalAdapterRefused):
        LocalTestAllowlistScanner(env=env, allowed_sha256=[PNG_SHA])
    with pytest.raises(LocalAdapterRefused):
        LocalTestSignatureMediaValidator(env=env)


@pytest.mark.parametrize("env", ["local", "test"])
def test_both_classes_accept_local_and_test(env: str) -> None:
    assert _scanner(env=env).scan(BytesIO(PNG)).verdict == "CLEAN"
    assert LocalTestSignatureMediaValidator(env=env).validate(
        BytesIO(PNG), declared_media_type="image/png"
    )


@pytest.mark.parametrize(
    "allowed",
    [
        [],
        ["not-a-hash"],
        [PNG_SHA.upper()],
        [PNG_SHA[:-1]],
        [PNG_SHA + "0"],
        [[PNG_SHA]],
        _many(MAX_ALLOWLIST_ENTRIES + 1),
    ],
)
def test_empty_or_malformed_allowlist_refuses_construction(allowed: list[object]) -> None:
    with pytest.raises(LocalAdapterRefused) as caught:
        LocalTestAllowlistScanner(env="test", allowed_sha256=allowed)  # type: ignore[arg-type]

    assert PNG_SHA not in str(caught.value)


def test_allowlist_at_the_size_limit_is_accepted() -> None:
    allowed = _many(MAX_ALLOWLIST_ENTRIES)

    assert LocalTestAllowlistScanner(env="test", allowed_sha256=allowed)


def test_allowlist_file_is_read_and_errors_do_not_echo_path_or_content(tmp_path: Path) -> None:
    good = tmp_path / "allow.json"
    good.write_text(json.dumps({"sha256": [PNG_SHA]}), encoding="utf-8")
    assert load_allowlist_file(good) == frozenset({PNG_SHA})

    for name, content in {
        "missing-key.json": json.dumps({"other": [PNG_SHA]}),
        "not-json.json": "{not json",
        "not-object.json": json.dumps([PNG_SHA]),
        "empty.json": json.dumps({"sha256": []}),
        "bad-entry.json": json.dumps({"sha256": ["XYZ"]}),
        "nested.json": json.dumps({"sha256": [{"a": 1}]}),
    }.items():
        broken = tmp_path / name
        broken.write_text(content, encoding="utf-8")
        with pytest.raises(LocalAdapterRefused) as caught:
            load_allowlist_file(broken)
        assert name not in str(caught.value)
        assert str(tmp_path) not in str(caught.value)

    with pytest.raises(LocalAdapterRefused) as caught:
        load_allowlist_file(tmp_path / "absent.json")
    assert "absent" not in str(caught.value)

    oversized = tmp_path / "huge.json"
    oversized.write_text(json.dumps({"sha256": [PNG_SHA] * 2000}), encoding="utf-8")
    with pytest.raises(LocalAdapterRefused):
        load_allowlist_file(oversized)


def test_every_synthetic_fixture_scans_clean_only_when_listed() -> None:
    uploads = synthetic_uploads()
    scanner = LocalTestAllowlistScanner(env="test", allowed_sha256=[u.sha256 for u in uploads])

    for upload in uploads:
        assert scanner.scan(BytesIO(upload.data)).verdict == "CLEAN"
    with pytest.raises(MalwareDetected):
        scanner.scan(BytesIO(synthetic_zip_prefix()))


# --- signature media validator -------------------------------------------------------------


@pytest.mark.parametrize(
    ("declared", "data"),
    [
        ("image/png", synthetic_png()),
        ("image/jpeg", synthetic_jpeg_prefix()),
        ("image/webp", synthetic_webp_prefix()),
        ("application/pdf", synthetic_pdf()),
        ("audio/wav", synthetic_wav()),
        (DOCX_MEDIA_TYPE, synthetic_zip_prefix()),
        (PPTX_MEDIA_TYPE, synthetic_zip_prefix()),
        (" Image/PNG ", synthetic_png()),
    ],
)
def test_validator_accepts_matching_signature(declared: str, data: bytes) -> None:
    stream = BytesIO(data)
    stream.seek(3)

    result = LocalTestSignatureMediaValidator(env="test").validate(
        stream, declared_media_type=declared
    )

    assert result.detected_media_type == declared.strip().lower()
    assert result.validator_name == "local-test-signature"
    assert result.validator_version
    assert stream.tell() == 0


@pytest.mark.parametrize(
    ("declared", "data"),
    [
        ("image/png", synthetic_jpeg_prefix()),
        ("image/jpeg", synthetic_png()),
        ("image/webp", synthetic_wav()),
        ("audio/wav", synthetic_webp_prefix()),
        ("application/pdf", synthetic_png()),
        (DOCX_MEDIA_TYPE, synthetic_pdf()),
        ("image/png", b""),
        ("application/pdf", b"%PDF"),
    ],
)
def test_validator_rejects_a_signature_mismatch(declared: str, data: bytes) -> None:
    with pytest.raises(UploadMediaRejected) as caught:
        LocalTestSignatureMediaValidator(env="test").validate(
            BytesIO(data), declared_media_type=declared
        )

    assert caught.value.code == "UPLOAD_CONTENT_MISMATCH"
    assert str(caught.value) == "UPLOAD_CONTENT_MISMATCH"


@pytest.mark.parametrize(
    "declared", ["", "text/plain", "application/octet-stream", "image/gif", "video/mp4"]
)
def test_validator_rejects_an_unknown_declared_type(declared: str) -> None:
    with pytest.raises(UploadMediaRejected) as caught:
        LocalTestSignatureMediaValidator(env="test").validate(
            BytesIO(synthetic_png()), declared_media_type=declared
        )

    assert caught.value.code == "UNSUPPORTED_MEDIA_TYPE"


def test_validator_reads_at_most_sixteen_header_bytes_and_decodes_nothing() -> None:
    stream = _TrackingStream(synthetic_png() * 50)

    LocalTestSignatureMediaValidator(env="test").validate(stream, declared_media_type="image/png")

    assert stream.read_sizes == [16]


def test_validator_unreadable_stream_is_a_content_mismatch() -> None:
    with pytest.raises(UploadMediaRejected) as caught:
        LocalTestSignatureMediaValidator(env="test").validate(
            _FailingReadStream(PNG), declared_media_type="image/png"
        )

    assert caught.value.code == "UPLOAD_CONTENT_MISMATCH"


def test_shared_signature_helper_matches_the_validator_table() -> None:
    assert header_matches_media_type("image/png", synthetic_png())
    assert not header_matches_media_type("image/png", synthetic_jpeg_prefix())
    assert not header_matches_media_type("image/gif", synthetic_png())


# --- factory: selection rule (P2-1) --------------------------------------------------------


def _settings(**values: Any) -> Settings:
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


def test_default_selection_is_clamav_and_no_validator() -> None:
    settings = _settings(env="test", clamav_host="127.0.0.1", clamav_port=3310)

    scanner = build_document_scanner(settings)

    assert isinstance(scanner, ClamAvScanner)
    assert build_upload_media_validator(settings) is None


def test_allowlist_file_alone_does_not_select_the_local_adapters(tmp_path: Path) -> None:
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps({"sha256": [PNG_SHA]}), encoding="utf-8")
    settings = _settings(env="test", local_scanner_allowlist_file=allow)

    assert isinstance(build_document_scanner(settings), ClamAvScanner)
    assert build_upload_media_validator(settings) is None


def test_local_selection_builds_both_adapters_from_one_flag(tmp_path: Path) -> None:
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps({"sha256": [PNG_SHA]}), encoding="utf-8")
    settings = _settings(
        env="local", scanner_adapter="local_test_allowlist", local_scanner_allowlist_file=allow
    )

    scanner = build_document_scanner(settings)
    validator = build_upload_media_validator(settings)

    assert isinstance(scanner, LocalTestAllowlistScanner)
    assert isinstance(validator, LocalTestSignatureMediaValidator)
    assert scanner.scan(BytesIO(PNG)).scanner_name == "local-test-allowlist"


def test_local_selection_without_an_allowlist_file_refuses() -> None:
    settings = _settings(env="test", scanner_adapter="local_test_allowlist")

    with pytest.raises(LocalAdapterRefused):
        build_document_scanner(settings)


def test_factory_constructors_refuse_a_non_local_environment_even_if_settings_were_bypassed(
    tmp_path: Path,
) -> None:
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps({"sha256": [PNG_SHA]}), encoding="utf-8")
    settings = _settings(
        env="test", scanner_adapter="local_test_allowlist", local_scanner_allowlist_file=allow
    )
    settings = settings.model_copy(update={"env": "production"})  # no re-validation

    with pytest.raises(LocalAdapterRefused):
        build_document_scanner(settings)
    with pytest.raises(LocalAdapterRefused):
        build_upload_media_validator(settings)
