"""Pure notification rules (FEAT-066 goal v3, T-8a; SRS l.784, l.1681, l.1697, FR-B-14).

No database, no clock: the validation of a ``NotificationCommandV1``, its canonical hash and the
idempotency fingerprints of the two mark-read commands.

The "no child content" rule (SRS l.784, l.1681) is an allowlist, not a denylist (plan review R1,
T8A-02): ``safe_parameters`` hold at most eight entries whose keys are ``snake_case`` tokens and
whose values are integers, booleans, or strings of one token (letters, digits and ``_.:-``, no
space, no diacritic). A person's display name or a sentence therefore cannot pass. A key denylist
stays as a second line of defence. A single-token value such as an opaque reference cannot be told
from a one-word name by a rule; the port documents that parameters are codes, counts and opaque
references, never display text.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any, Final

from sketch2life.application.ports.notifications import (
    NotificationCommandV1,
    NotificationParameter,
    NotificationRejected,
)

RECIPIENT_ROLES: Final = ("parent", "teacher", "school_manager", "platform_admin")
MAX_PARAMETERS: Final = 8
MAX_PARAMETERS_BYTES: Final = 1536
MAX_INT: Final = 2**53 - 1
TEMPLATE_VERSION_MIN: Final = 1
TEMPLATE_VERSION_MAX: Final = 9999
UNREAD_COUNT_CAP: Final = 100

READ_ONE_SCOPE: Final = "POST /notifications/read"
READ_ALL_SCOPE: Final = "POST /notifications/read-all"

_PARAMETER_KEY: Final = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_PARAMETER_TEXT: Final = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
_TYPE: Final = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_TRIGGER: Final = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_ACCOUNT: Final = re.compile(r"^[A-Za-z0-9._:-]{1,36}$")
_REFERENCE: Final = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
# Defence in depth only: a key that names child or contact content is refused whatever its value.
_FORBIDDEN_KEY_PARTS: Final = (
    "name",
    "child",
    "story",
    "transcript",
    "media",
    "url",
    "email",
    "token",
    "endpoint",
    "address",
)


def _reject(field: str, code: str) -> NotificationRejected:
    return NotificationRejected(field, code)


def _validate_parameter_value(key: str, value: object) -> NotificationParameter:
    field = f"safe_parameters.{key}"
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_INT:
            raise _reject(field, "OUT_OF_RANGE")
        return value
    if isinstance(value, str):
        if not _PARAMETER_TEXT.fullmatch(value):
            raise _reject(field, "INVALID_FORMAT")
        return value
    raise _reject(field, "INVALID_TYPE")


def pg_text_size(parameters: dict[str, NotificationParameter]) -> int:
    """Byte size of the parameters in the PostgreSQL ``jsonb`` text form (``", "`` and ``": "``)."""
    text = json.dumps(parameters, ensure_ascii=True, separators=(", ", ": "))
    return len(text.encode("utf-8"))


def validate_parameters(parameters: object) -> dict[str, NotificationParameter]:
    """Return a copy of ``parameters`` when it passes the allowlist, else raise."""
    if not isinstance(parameters, dict):
        raise _reject("safe_parameters", "INVALID_TYPE")
    if len(parameters) > MAX_PARAMETERS:
        raise _reject("safe_parameters", "TOO_LONG")
    checked: dict[str, NotificationParameter] = {}
    for key, value in parameters.items():
        if not isinstance(key, str) or not _PARAMETER_KEY.fullmatch(key):
            raise _reject("safe_parameters", "INVALID_FORMAT")
        if any(part in key for part in _FORBIDDEN_KEY_PARTS):
            raise _reject(f"safe_parameters.{key}", "NOT_SUPPORTED")
        checked[key] = _validate_parameter_value(key, value)
    if pg_text_size(checked) > MAX_PARAMETERS_BYTES:
        raise _reject("safe_parameters", "TOO_LONG")
    return checked


def validate_command(command: NotificationCommandV1, *, created_at: datetime) -> None:
    """Raise ``NotificationRejected`` unless every part of the command is allowed."""
    if not _ACCOUNT.fullmatch(command.recipient_account_id):
        raise _reject("recipient_account_id", "INVALID_FORMAT")
    if command.recipient_role not in RECIPIENT_ROLES:
        raise _reject("recipient_role", "INVALID_FORMAT")
    if not _TYPE.fullmatch(command.notification_type):
        raise _reject("notification_type", "INVALID_FORMAT")
    version = command.template_version
    if type(version) is not int or not TEMPLATE_VERSION_MIN <= version <= TEMPLATE_VERSION_MAX:
        raise _reject("template_version", "OUT_OF_RANGE")
    if not _TRIGGER.fullmatch(command.trigger_id):
        raise _reject("trigger_id", "INVALID_FORMAT")
    if not _TRIGGER.fullmatch(command.dedupe_key):
        raise _reject("dedupe_key", "INVALID_FORMAT")
    reference = command.organization_ref
    if reference is not None and not _REFERENCE.fullmatch(reference):
        raise _reject("organization_ref", "INVALID_FORMAT")
    validate_parameters(command.safe_parameters)
    expires_at = command.expires_at
    if expires_at is not None and (
        expires_at.tzinfo is None or expires_at.utcoffset() is None or expires_at <= created_at
    ):
        raise _reject("expires_at", "OUT_OF_RANGE")


def command_sha256(command: NotificationCommandV1) -> str:
    """SHA-256 of the canonical command, ``expires_at`` left out.

    The expiry is usually computed from the producer's clock, so a retry of the same trigger would
    differ by it alone; the hash identifies the logical notification, so the first stored expiry
    stays.
    """
    canonical: dict[str, Any] = {
        "recipient_account_id": command.recipient_account_id,
        "recipient_role": command.recipient_role,
        "notification_type": command.notification_type,
        "template_version": command.template_version,
        "trigger_id": command.trigger_id,
        "dedupe_key": command.dedupe_key,
        "organization_ref": command.organization_ref,
        "safe_parameters": command.safe_parameters,
    }
    text = json.dumps(canonical, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_fingerprint(operation: str, inbox_item_id: str | None) -> str:
    """Idempotency fingerprint of a mark-read command: the operation and the item it targets.

    The receipt scope is a constant, so the item id lives only in the fingerprint: the same key on
    another item (or on read-all) is a different request and is refused (SRS l.1697).
    """
    text = json.dumps(
        {"operation": operation, "inbox_item_id": inbox_item_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_iso(moment: datetime) -> str:
    """The one spelling used in cursors: UTC offset, ``datetime.isoformat``."""
    return moment.astimezone(UTC).isoformat()


__all__ = [
    "MAX_INT",
    "MAX_PARAMETERS",
    "MAX_PARAMETERS_BYTES",
    "READ_ALL_SCOPE",
    "READ_ONE_SCOPE",
    "RECIPIENT_ROLES",
    "UNREAD_COUNT_CAP",
    "command_sha256",
    "pg_text_size",
    "read_fingerprint",
    "utc_iso",
    "validate_command",
    "validate_parameters",
]
