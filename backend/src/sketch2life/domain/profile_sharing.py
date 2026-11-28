"""Pure rules for the Parent-to-Teacher profile share contract (T-SHARE1)."""

from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Any


class ShareField(str, Enum):  # noqa: UP042
    DISPLAY_NAME = "DISPLAY_NAME"
    AGE_BAND = "AGE_BAND"
    INTERESTS_SUMMARY = "INTERESTS_SUMMARY"


class ShareState(str, Enum):  # noqa: UP042
    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


ALLOWED_FIELDS = frozenset(field.value for field in ShareField)
REFUSED_FIELDS = frozenset({"SUPPORT_NEEDS", "CONTEXT_ENTRIES", "AGE_MONTHS"})
INVITATION_DAYS = 90
GRANT_DAYS = 90
HISTORY_DAYS = 30


class ProfileShareError(Exception):
    """Base for transport-neutral failures raised by the profile-share service."""


class ProfileShareNotFound(ProfileShareError):
    """The caller cannot see the requested profile-share resource."""


class ProfileShareInvalidRequest(ProfileShareError):
    def __init__(
        self,
        code: str,
        *,
        field_errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.field_errors = field_errors or []


class ProfileShareConflict(ProfileShareError):
    def __init__(self, code: str = "RESOURCE_CONFLICT") -> None:
        super().__init__(code)
        self.code = code


class ProfileShareStaleRevision(ProfileShareConflict):
    def __init__(self, current_version: int) -> None:
        super().__init__("STALE_REVISION")
        self.current_version = current_version


class ProfileShareUnavailable(ProfileShareError):
    def __init__(self, code: str = "DATABASE_UNAVAILABLE") -> None:
        super().__init__(code)
        self.code = code


class ShareFieldError(ValueError):
    def __init__(self, field: str, code: str) -> None:
        super().__init__(f"{field}: {code}")
        self.field = field
        self.code = code


def normalize_granted_fields(values: object) -> tuple[str, ...]:
    """Validate the supported scope and return its stable sorted, unique representation."""
    if not isinstance(values, (list, tuple)):
        raise ShareFieldError("granted_fields", "INVALID_TYPE")
    normalized: set[str] = set()
    for value in values:
        raw = value.value if isinstance(value, ShareField) else value
        if not isinstance(raw, str):
            raise ShareFieldError("granted_fields", "INVALID_TYPE")
        if raw in REFUSED_FIELDS:
            raise ShareFieldError("granted_fields", "NOT_SUPPORTED")
        if raw not in ALLOWED_FIELDS:
            raise ShareFieldError("granted_fields", "INVALID_FORMAT")
        normalized.add(raw)
    if not normalized:
        raise ShareFieldError("granted_fields", "OUT_OF_RANGE")
    return tuple(sorted(normalized))


def effective_state(row: object, now: datetime) -> ShareState:
    """Apply invitation and accepted-grant expiry at the exact boundary in UTC-aware time."""
    state_value = _value(row, "state")
    try:
        state = ShareState(state_value)
    except ValueError:
        raise ValueError("unknown profile-share state") from None
    if state is ShareState.INVITED and _value(row, "invitation_expires_at") <= now:
        return ShareState.EXPIRED
    if state is ShareState.ACTIVE and _value(row, "expires_at") <= now:
        return ShareState.EXPIRED
    return state


def generate_invitation_code() -> str:
    """Create a 128-bit bearer code; callers must show it once and store only its digest."""
    return secrets.token_urlsafe(16)


def invitation_code_sha256(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def request_fingerprint(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def invitation_window(created_at: datetime) -> datetime:
    return created_at + timedelta(days=INVITATION_DAYS)


def grant_window(accepted_at: datetime) -> datetime:
    return accepted_at + timedelta(days=GRANT_DAYS)


def delivered_at(
    sample_claimed_at: datetime | None, scheduled_date: date | None
) -> datetime | None:
    if sample_claimed_at is not None:
        return sample_claimed_at
    if scheduled_date is None:
        return None
    return datetime.combine(scheduled_date, datetime.min.time(), tzinfo=UTC)


def history_item_visible(
    *,
    occurrence_state: str,
    delivered_at_value: datetime | None,
    accepted_at: datetime,
    access_ends_at: datetime | None,
    enrollment_created_at: datetime | None,
    now: datetime,
) -> bool:
    """Apply the derived delivery-history window and the enrollment-at-delivery rule."""
    moment = delivered_at_value
    return bool(
        occurrence_state in {"APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"}
        and moment is not None
        and moment <= now
        and moment >= accepted_at
        and moment > now - timedelta(days=HISTORY_DAYS)
        and (access_ends_at is None or moment < access_ends_at)
        and enrollment_created_at is not None
        and enrollment_created_at <= moment
    )


def _value(row: object, name: str) -> Any:
    if isinstance(row, Mapping):
        return row[name]
    return getattr(row, name)


__all__ = [
    "ALLOWED_FIELDS",
    "GRANT_DAYS",
    "HISTORY_DAYS",
    "INVITATION_DAYS",
    "ProfileShareConflict",
    "ProfileShareError",
    "ProfileShareInvalidRequest",
    "ProfileShareNotFound",
    "ProfileShareStaleRevision",
    "ProfileShareUnavailable",
    "REFUSED_FIELDS",
    "ShareField",
    "ShareFieldError",
    "ShareState",
    "delivered_at",
    "effective_state",
    "generate_invitation_code",
    "grant_window",
    "history_item_visible",
    "invitation_code_sha256",
    "invitation_window",
    "normalize_granted_fields",
    "request_fingerprint",
]
