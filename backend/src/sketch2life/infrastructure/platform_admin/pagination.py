"""Opaque, filter-bound keyset cursors for stable Admin list traversal."""

import base64
import hashlib
import json
import re
from datetime import UTC, datetime

from sqlalchemy import String, and_, cast, or_

from sketch2life.domain.platform_admin import AdminError

_CURSOR_VERSION = 1
_MAX_CURSOR_LENGTH = 768
_CURSOR_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def cursor_scope(endpoint: str, *filters: object) -> str:
    fingerprint = hashlib.sha256(
        json.dumps(filters, ensure_ascii=False, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return endpoint + ":" + fingerprint


def _utc(value: datetime | str) -> datetime:
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    if result.tzinfo is None:
        return result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def encode_datetime_cursor(scope: str, created_at: datetime | str, reference: str) -> str:
    payload = json.dumps(
        {
            "v": _CURSOR_VERSION,
            "s": scope,
            "t": _utc(created_at).isoformat(),
            "r": reference,
        },
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_datetime_cursor(scope: str, cursor: str | None) -> tuple[datetime, str] | None:
    if cursor is None:
        return None
    try:
        if not 1 <= len(cursor) <= _MAX_CURSOR_LENGTH or not _CURSOR_PATTERN.fullmatch(cursor):
            raise ValueError
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        payload = json.loads(raw)
        if (
            not isinstance(payload, dict)
            or payload.get("v") != _CURSOR_VERSION
            or payload.get("s") != scope
            or not isinstance(payload.get("r"), str)
            or not payload["r"]
            or len(payload["r"]) > 256
        ):
            raise ValueError
        return _utc(payload["t"]), payload["r"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise AdminError("INVALID_CURSOR", 422) from None


def apply_datetime_cursor(
    query,
    *,
    created_at_column,
    reference_column,
    scope: str,
    cursor: str | None,
    descending: bool = True,
    dialect: str | None = None,
):
    position = decode_datetime_cursor(scope, cursor)
    if position is None:
        return query
    timestamp, reference = position
    # SQLite stores DateTime values as text and may omit the fractional part when it
    # is zero. Compare canonical stored text there so second-precision values remain
    # equal to their cursor timestamp; production PostgreSQL keeps native timestamps.
    if dialect == "sqlite":
        timestamp = timestamp.replace(tzinfo=None)
        created_at_column = cast(created_at_column, String)
        timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S") + (
            f".{timestamp.microsecond:06d}" if timestamp.microsecond else ""
        )
    if descending:
        after = or_(
            created_at_column < timestamp,
            and_(created_at_column == timestamp, reference_column > reference),
        )
    else:
        after = or_(
            created_at_column > timestamp,
            and_(created_at_column == timestamp, reference_column > reference),
        )
    return query.where(after)


def row_is_after_cursor(
    created_at: datetime | str,
    reference: str,
    *,
    position: tuple[datetime, str] | None,
    descending: bool = True,
) -> bool:
    if position is None:
        return True
    timestamp, last_reference = position
    current_timestamp = _utc(created_at)
    if descending:
        return current_timestamp < timestamp or (
            current_timestamp == timestamp and reference > last_reference
        )
    return current_timestamp > timestamp or (
        current_timestamp == timestamp and reference > last_reference
    )


def next_datetime_cursor(
    rows,
    limit: int,
    *,
    scope: str,
    created_at,
    reference,
) -> str | None:
    if len(rows) <= limit:
        return None
    last = rows[limit - 1]
    return encode_datetime_cursor(scope, created_at(last), reference(last))


def encode_reference_cursor(scope: str, reference: str) -> str:
    payload = json.dumps(
        {"v": _CURSOR_VERSION, "s": scope, "r": reference},
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_reference_cursor(scope: str, cursor: str | None) -> str | None:
    if cursor is None:
        return None
    try:
        if not 1 <= len(cursor) <= _MAX_CURSOR_LENGTH or not _CURSOR_PATTERN.fullmatch(cursor):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        if (
            not isinstance(payload, dict)
            or payload.get("v") != _CURSOR_VERSION
            or payload.get("s") != scope
            or not isinstance(payload.get("r"), str)
            or not payload["r"]
            or len(payload["r"]) > 256
        ):
            raise ValueError
        return payload["r"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise AdminError("INVALID_CURSOR", 422) from None


def apply_reference_cursor(query, *, reference_column, scope: str, cursor: str | None):
    reference = decode_reference_cursor(scope, cursor)
    return query if reference is None else query.where(reference_column > reference)


def next_reference_cursor(rows, limit: int, *, scope: str, reference) -> str | None:
    if len(rows) <= limit:
        return None
    return encode_reference_cursor(scope, reference(rows[limit - 1]))
