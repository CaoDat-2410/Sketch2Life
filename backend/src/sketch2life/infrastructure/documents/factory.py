"""Composition factories for the document scanner and the optional upload media validator.

Default behaviour is unchanged: the ClamAV adapter and no media validator. The local test pair is
selected only by ``scanner_adapter == "local_test_allowlist"``; settings and both local
constructors refuse that choice outside local/test (T-2z-DEC-3).
"""

from __future__ import annotations

from sketch2life.application.ports.lesson_documents import MalwareScanner
from sketch2life.application.ports.upload_validation import UploadMediaValidator
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.documents.clamav_scanner import ClamAvScanner
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalAdapterRefused,
    LocalTestAllowlistScanner,
    LocalTestSignatureMediaValidator,
    load_allowlist_file,
)


def build_document_scanner(settings: Settings) -> MalwareScanner:
    if settings.scanner_adapter == "local_test_allowlist":
        if settings.local_scanner_allowlist_file is None:
            raise LocalAdapterRefused("the local test scanner needs an allowlist file")
        return LocalTestAllowlistScanner(
            env=settings.env,
            allowed_sha256=load_allowlist_file(settings.local_scanner_allowlist_file),
        )
    return ClamAvScanner(host=settings.clamav_host, port=settings.clamav_port)


def build_upload_media_validator(settings: Settings) -> UploadMediaValidator | None:
    if settings.scanner_adapter == "local_test_allowlist":
        return LocalTestSignatureMediaValidator(env=settings.env)
    return None


__all__ = ["build_document_scanner", "build_upload_media_validator"]
