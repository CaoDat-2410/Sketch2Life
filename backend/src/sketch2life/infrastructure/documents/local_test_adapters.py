"""Local/test-only malware scanner and upload media validator (T-2z, TD-29).

These doubles let a local or test run exercise the upload pipeline without ClamAV. They are never
a malware scan: ``CLEAN`` is returned only for an explicit allowlist of synthetic fixture SHA-256
digests, every other file fails closed (SRS l.940, l.1934). Both classes refuse to be built unless
the environment is ``local`` or ``test``; settings refuse the adapter selection outside those
environments as well (two layers). Nothing about file content, hashes or paths is logged or put in
an exception message.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO

from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScannerUnavailable,
    MalwareScanResult,
)
from sketch2life.application.ports.upload_validation import (
    HEADER_BYTES,
    UNSUPPORTED_MEDIA_TYPE,
    UPLOAD_CONTENT_MISMATCH,
    MediaValidationResult,
    UploadMediaRejected,
    header_matches_media_type,
    is_known_media_type,
    normalize_media_type,
)

LOCAL_ADAPTER_ENVIRONMENTS = frozenset({"local", "test"})
LOCAL_SCANNER_NAME = "local-test-allowlist"
LOCAL_SCANNER_VERSION_PREFIX = "1+allowlist-"
LOCAL_VALIDATOR_NAME = "local-test-signature"
LOCAL_VALIDATOR_VERSION = "1"
NOT_ALLOWLISTED_CODE = "LOCAL_TEST_HASH_NOT_ALLOWLISTED"
MAX_ALLOWLIST_ENTRIES = 256
MAX_ALLOWLIST_FILE_BYTES = 64 * 1024

_SCAN_CHUNK_BYTES = 64 * 1024
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class LocalAdapterRefused(RuntimeError):
    """A local/test adapter was requested outside local/test or with an unusable allowlist."""


def _require_local_environment(env: str) -> None:
    if env not in LOCAL_ADAPTER_ENVIRONMENTS:
        raise LocalAdapterRefused("local test adapters are available only in local/test")


def validated_allowlist(values: Iterable[str]) -> frozenset[str]:
    """The allowlist as a set; empty, oversized or malformed input is refused (no echo)."""
    try:
        entries = frozenset(values)
    except TypeError:
        raise LocalAdapterRefused("the local test allowlist holds a malformed entry") from None
    if not entries:
        raise LocalAdapterRefused("the local test allowlist is empty")
    if len(entries) > MAX_ALLOWLIST_ENTRIES:
        raise LocalAdapterRefused("the local test allowlist is too large")
    if not all(isinstance(item, str) and _SHA256_HEX.fullmatch(item) for item in entries):
        raise LocalAdapterRefused("the local test allowlist holds a malformed entry")
    return entries


def load_allowlist_file(path: Path) -> frozenset[str]:
    """Read ``{"sha256": [...]}``; the path and the content never appear in an error."""
    try:
        if path.stat().st_size > MAX_ALLOWLIST_FILE_BYTES:
            raise LocalAdapterRefused("the local test allowlist file is too large")
        document = json.loads(path.read_text(encoding="utf-8"))
    except LocalAdapterRefused:
        raise
    except (OSError, ValueError):
        raise LocalAdapterRefused("the local test allowlist file could not be read") from None
    entries = document.get("sha256") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        raise LocalAdapterRefused("the local test allowlist file has no sha256 list")
    return validated_allowlist(entries)


class LocalTestAllowlistScanner:
    """``MalwareScanner`` that reports CLEAN only for allowlisted synthetic fixture digests."""

    def __init__(self, *, env: str, allowed_sha256: Iterable[str]) -> None:
        _require_local_environment(env)
        self._allowed = validated_allowlist(allowed_sha256)
        fingerprint = hashlib.sha256("\n".join(sorted(self._allowed)).encode("ascii")).hexdigest()
        self._version = f"{LOCAL_SCANNER_VERSION_PREFIX}{fingerprint[:16]}"

    @property
    def scanner_name(self) -> str:
        return LOCAL_SCANNER_NAME

    @property
    def scanner_version(self) -> str:
        return self._version

    def scan(self, file_obj: BinaryIO) -> MalwareScanResult:
        digest = hashlib.sha256()
        try:
            file_obj.seek(0)
            while chunk := file_obj.read(_SCAN_CHUNK_BYTES):
                digest.update(chunk)
        except (OSError, ValueError, TypeError, AttributeError):
            raise MalwareScannerUnavailable(
                "local test scanner could not read the stream"
            ) from None
        finally:
            with contextlib.suppress(OSError, ValueError, AttributeError):
                file_obj.seek(0)
        if digest.hexdigest() not in self._allowed:
            raise MalwareDetected(NOT_ALLOWLISTED_CODE)
        return MalwareScanResult(
            scanner_name=LOCAL_SCANNER_NAME, scanner_version=self._version, verdict="CLEAN"
        )


class LocalTestSignatureMediaValidator:
    """``UploadMediaValidator`` that checks the first bytes against the declared type."""

    def __init__(self, *, env: str) -> None:
        _require_local_environment(env)

    def validate(self, file_obj: BinaryIO, *, declared_media_type: str) -> MediaValidationResult:
        if not is_known_media_type(declared_media_type):
            raise UploadMediaRejected(UNSUPPORTED_MEDIA_TYPE)
        try:
            file_obj.seek(0)
            header = file_obj.read(HEADER_BYTES)
        except (OSError, ValueError, TypeError, AttributeError):
            raise UploadMediaRejected(UPLOAD_CONTENT_MISMATCH) from None
        finally:
            with contextlib.suppress(OSError, ValueError, AttributeError):
                file_obj.seek(0)
        if not isinstance(header, bytes) or not header_matches_media_type(
            declared_media_type, header
        ):
            raise UploadMediaRejected(UPLOAD_CONTENT_MISMATCH)
        return MediaValidationResult(
            detected_media_type=normalize_media_type(declared_media_type),
            validator_name=LOCAL_VALIDATOR_NAME,
            validator_version=LOCAL_VALIDATOR_VERSION,
        )


__all__ = [
    "LOCAL_ADAPTER_ENVIRONMENTS",
    "LOCAL_SCANNER_NAME",
    "LOCAL_VALIDATOR_NAME",
    "MAX_ALLOWLIST_ENTRIES",
    "NOT_ALLOWLISTED_CODE",
    "LocalAdapterRefused",
    "LocalTestAllowlistScanner",
    "LocalTestSignatureMediaValidator",
    "load_allowlist_file",
    "validated_allowlist",
]
