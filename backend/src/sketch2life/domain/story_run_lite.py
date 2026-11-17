"""Framework-independent StoryRun-lite state and command identity rules."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class OwnerScopeKind(StrEnum):
    PARENT_ACCOUNT = "PARENT_ACCOUNT"
    ORGANIZATION = "ORGANIZATION"


class RunState(StrEnum):
    INPUT_PROCESSING = "INPUT_PROCESSING"
    SUBJECT_REVIEW = "SUBJECT_REVIEW"
    PREPARATION_REVIEW = "PREPARATION_REVIEW"
    SCRIPT_GENERATING = "SCRIPT_GENERATING"
    SCRIPT_GENERATION_UNKNOWN = "SCRIPT_GENERATION_UNKNOWN"
    SCRIPT_REVIEW = "SCRIPT_REVIEW"
    VIDEO_ADMISSION_PENDING = "VIDEO_ADMISSION_PENDING"
    DELETE_PENDING = "DELETE_PENDING"
    FAILED = "FAILED"


class UploadState(StrEnum):
    RECEIVING = "RECEIVING"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    EXPIRED = "EXPIRED"


class ReceiptState(StrEnum):
    PENDING = "PENDING"
    FINAL = "FINAL"


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PART_BYTES = 4 * 1024 * 1024
MAX_PARTS = 5
MAX_IMAGE_PIXELS = 40_000_000
MAX_RESPONSE_SNAPSHOT_BYTES = 256 * 1024
MODEL_INPUT_LIMIT_BYTES = 5_000_000
_KEY_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,200}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class StoryRunLiteError(Exception):
    """Expected domain/application failure with a stable HTTP mapping."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        field_errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.field_errors = field_errors or []


@dataclass(frozen=True, slots=True)
class CommandIdentity:
    actor_scope_kind: OwnerScopeKind
    actor_scope_ref: str
    operation: str
    scope_kind: str
    scope_ref: str
    idempotency_key_sha256: str
    request_fingerprint_sha256: str


def validate_idempotency_key(value: str) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise StoryRunLiteError(
            400, "INVALID_IDEMPOTENCY_KEY", "A valid Idempotency-Key is required."
        )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_fingerprint(
    *, method: str, path: str, request: dict[str, Any], expected_version: int | None = None
) -> str:
    """Hash the validated DTO and normalized version using its fixed, JSON-only field set.

    Request models deliberately contain no floating point values, so sorted compact JSON has
    the same stable representation for the DTO values used by this contract.
    """

    envelope: dict[str, Any] = {
        "api_version": "StoryRunLite-v1",
        "method": method.upper(),
        "path": path,
        "request": request,
    }
    if expected_version is not None:
        envelope["if_match_version"] = expected_version
    try:
        canonical = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise StoryRunLiteError(
            400, "INVALID_REQUEST", "The request cannot be canonicalized."
        ) from None
    return hashlib.sha256(canonical).hexdigest()


def require_sha256(value: str, field: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise StoryRunLiteError(
            422,
            "INVALID_REQUEST",
            f"{field} must be a lowercase SHA-256 digest.",
            field_errors=[
                {
                    "field": field,
                    "code": "INVALID_SHA256",
                    "message": "Expected 64 lowercase hexadecimal characters.",
                }
            ],
        )
    return value


def parse_etag_version(value: str | None) -> int:
    if not value:
        raise StoryRunLiteError(428, "PRECONDITION_REQUIRED", "If-Match is required.")
    candidate = value.strip()
    if candidate.startswith("W/"):
        raise StoryRunLiteError(400, "INVALID_ETAG", "If-Match requires a strong ETag.")
    candidate = candidate.strip('"')
    if candidate.startswith("v"):
        candidate = candidate[1:]
    try:
        version = int(candidate)
    except ValueError:
        raise StoryRunLiteError(
            400, "INVALID_ETAG", "If-Match must contain the resource version."
        ) from None
    if version < 1:
        raise StoryRunLiteError(400, "INVALID_ETAG", "If-Match version must be positive.")
    return version


def etag(version: int) -> str:
    return f'"v{version}"'


def validate_part_number(part_number: int) -> None:
    if not 1 <= part_number <= MAX_PARTS:
        raise StoryRunLiteError(
            422,
            "INVALID_PART_NUMBER",
            "Part number must be between 1 and the advertised max_parts.",
        )


def validate_upload_bounds(size: int) -> None:
    if size < 1:
        raise StoryRunLiteError(422, "INVALID_REQUEST", "expected_size_bytes must be positive.")
    if size > MAX_UPLOAD_BYTES:
        raise StoryRunLiteError(
            413, "IMAGE_TOO_LARGE", "The upload exceeds the server-advertised maximum."
        )


def validate_part_bounds(size: int) -> None:
    if size < 1 or size > MAX_PART_BYTES:
        raise StoryRunLiteError(
            413, "PART_TOO_LARGE", "The part must be between one byte and part_size_bytes."
        )
