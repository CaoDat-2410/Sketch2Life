"""Shared CONV-1 helpers: idempotency key, page limit, stale revision, validation field errors.

No route adopts these helpers in CONV-1 except as the approved package lists; capability
slices adopt them for their own routes (FEAT-066 D-066-68, D-066-71).
"""

from __future__ import annotations

import base64
import binascii
import json
import types
import typing
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any, NoReturn

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel

PAGE_LIMIT_DEFAULT = 25
PAGE_LIMIT_MAX = 100
# The longest cursor is the consents one: scope with two 128-character ids, a 36-character
# consent id and a timestamp come to about 490 characters; 1024 leaves a wide margin.
CURSOR_MAX_LENGTH = 1024
_CURSOR_VERSION = 1
_CURSOR_KEYS = frozenset({"i", "k", "s", "v"})
_CURSOR_ID_MAX = 128
_CURSOR_SORT_KEY_MAX = 64

_LOCATION_PARTS = frozenset({"body", "query", "header", "path", "cookie"})
_MAX_FIELD_LENGTH = 120
_IDEMPOTENCY_HEADER = "idempotency-key"
_UNKNOWN = "<unknown>"

_TYPE_CODES: Mapping[str, str] = {
    "missing": "REQUIRED",
    "string_too_long": "TOO_LONG",
    "too_long": "TOO_LONG",
    "greater_than": "OUT_OF_RANGE",
    "greater_than_equal": "OUT_OF_RANGE",
    "less_than": "OUT_OF_RANGE",
    "less_than_equal": "OUT_OF_RANGE",
    "string_too_short": "EMPTY",
    "too_short": "EMPTY",
    "int_type": "INVALID_TYPE",
    "int_parsing": "INVALID_TYPE",
    "float_type": "INVALID_TYPE",
    "string_type": "INVALID_TYPE",
    "bool_type": "INVALID_TYPE",
    "model_type": "INVALID_TYPE",
    "list_type": "INVALID_TYPE",
    "dict_type": "INVALID_TYPE",
    "extra_forbidden": "UNKNOWN_FIELD",
}


def limit_query() -> Any:
    """Return the shared `limit` query parameter: default 25, maximum 100 (C-D8)."""
    return Query(default=PAGE_LIMIT_DEFAULT, ge=1, le=PAGE_LIMIT_MAX)


def cursor_query() -> Any:
    """Return the shared opaque `cursor` query parameter (SRS l.1640)."""
    return Query(default=None, min_length=1, max_length=CURSOR_MAX_LENGTH)


def _invalid(field: str, code: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"code": "INVALID_REQUEST", "field_errors": [{"field": field, "code": code}]},
    )


def encode_cursor(*, scope: str, sort_key: str, item_id: str) -> str:
    """Encode an opaque keyset cursor bound to one route scope (not signed, not secret).

    The scope binding stops a cursor from one route or organization being replayed on another;
    the scope and authorization checks still gate every page.
    """
    payload = json.dumps(
        {"i": item_id, "k": sort_key, "s": scope, "v": _CURSOR_VERSION},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(cursor: str, *, scope: str) -> tuple[str, str]:
    """Return `(sort_key, item_id)` of a cursor made for `scope`, else 400 INVALID_FORMAT."""
    try:
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != _CURSOR_KEYS:
            raise ValueError
        version, cursor_scope = decoded["v"], decoded["s"]
        sort_key, item_id = decoded["k"], decoded["i"]
        if type(version) is not int or version != _CURSOR_VERSION:
            raise ValueError
        if not isinstance(cursor_scope, str) or cursor_scope != scope:
            raise ValueError
        if not isinstance(sort_key, str) or not 1 <= len(sort_key) <= _CURSOR_SORT_KEY_MAX:
            raise ValueError
        if not isinstance(item_id, str) or not 1 <= len(item_id) <= _CURSOR_ID_MAX:
            raise ValueError
        # Printable ASCII only (no NUL or control characters reach the database), and only the
        # one form `encode_cursor` writes: no base64 padding, no `+` or `/`, no re-spelled JSON.
        if not (sort_key.isascii() and sort_key.isprintable()):
            raise ValueError
        if not (item_id.isascii() and item_id.isprintable()):
            raise ValueError
        if encode_cursor(scope=scope, sort_key=sort_key, item_id=item_id) != cursor:
            raise ValueError
        return sort_key, item_id
    except (binascii.Error, ValueError, RecursionError):
        raise _invalid("cursor", "INVALID_FORMAT") from None


def decode_time_cursor(cursor: str, *, scope: str) -> tuple[datetime, str]:
    """Return `(timestamp, item_id)` of a time-keyed cursor.

    The timestamp needs a timezone and must be spelled exactly as `datetime.isoformat` writes it.
    """
    sort_key, item_id = decode_cursor(cursor, scope=scope)
    try:
        moment = datetime.fromisoformat(sort_key)
    except ValueError:
        raise _invalid("cursor", "INVALID_FORMAT") from None
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise _invalid("cursor", "INVALID_FORMAT")
    if moment.isoformat() != sort_key:
        raise _invalid("cursor", "INVALID_FORMAT")
    return moment, item_id


def parse_idempotency_key(request: Request) -> str:
    """Return the single Idempotency-Key value or raise 400 INVALID_REQUEST (C-D5)."""
    values = request.headers.getlist("Idempotency-Key")
    if not values:
        raise _invalid("Idempotency-Key", "REQUIRED")
    if len(values) != 1:
        raise _invalid("Idempotency-Key", "INVALID_FORMAT")
    value = values[0]
    if not 1 <= len(value) <= 128 or any(ord(char) < 33 or ord(char) > 126 for char in value):
        raise _invalid("Idempotency-Key", "INVALID_FORMAT")
    return value


def raise_stale_revision(
    *, current_version: int | None = None, etag: str | None = None
) -> NoReturn:
    """Raise 409 STALE_REVISION with the current version or the current strong ETag (C-D7)."""
    detail: dict[str, Any] = {"code": "STALE_REVISION"}
    if current_version is not None:
        detail["current_version"] = current_version
    headers = {"ETag": f'"{etag}"'} if etag is not None else None
    raise HTTPException(status_code=409, detail=detail, headers=headers)


def _collect_model_names(annotation: object, names: set[str], seen: set[type]) -> None:
    origin = typing.get_origin(annotation)
    if origin is not None or isinstance(annotation, types.UnionType):
        for argument in typing.get_args(annotation):
            _collect_model_names(argument, names, seen)
        return
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if annotation in seen:
            return
        seen.add(annotation)
        for name, field in annotation.model_fields.items():
            names.add(name)
            if field.alias:
                names.add(field.alias)
            _collect_model_names(field.annotation, names, seen)


def declared_field_names(route: object) -> frozenset[str]:
    """Collect the parameter names, aliases and body-model field names a route declares."""
    names: set[str] = set()
    seen: set[type] = set()
    stack = [getattr(route, "dependant", None)]
    while stack:
        dependant = stack.pop()
        if dependant is None:
            continue
        for group in (
            "path_params",
            "query_params",
            "header_params",
            "cookie_params",
            "body_params",
        ):
            for param in getattr(dependant, group, ()) or ():
                for attribute in ("name", "alias"):
                    value = getattr(param, attribute, None)
                    if isinstance(value, str):
                        names.add(value)
                field_info = getattr(param, "field_info", None)
                _collect_model_names(getattr(field_info, "annotation", None), names, seen)
        stack.extend(getattr(dependant, "dependencies", ()) or ())
    return frozenset(names)


def _field_name(location: Sequence[object], declared: frozenset[str]) -> str:
    parts: list[str] = []
    for part in location:
        if isinstance(part, int):
            continue
        text = str(part)
        if text in _LOCATION_PARTS and not parts:
            continue
        if text not in declared:
            return _UNKNOWN
        parts.append(text)
    field = ".".join(parts)
    return field if 0 < len(field) <= _MAX_FIELD_LENGTH else _UNKNOWN


def field_errors_from_validation(
    route: object, issues: Iterable[Mapping[str, Any]]
) -> list[dict[str, str]]:
    """Map validation issues to non-echoing {field, code} items (CONV-1 §3.2 item 2d)."""
    declared = declared_field_names(route)
    result: set[tuple[str, str]] = set()
    for issue in issues:
        error_type = str(issue.get("type", ""))
        raw_location = issue.get("loc", ())
        location: Sequence[object] = (
            raw_location if isinstance(raw_location, (tuple, list)) else ()
        )
        is_idempotency_header = (
            len(location) >= 2
            and location[0] == "header"
            and str(location[1]).lower() == _IDEMPOTENCY_HEADER
        )
        if is_idempotency_header:
            code = "REQUIRED" if error_type == "missing" else "INVALID_FORMAT"
            result.add(("Idempotency-Key", code))
            continue
        if error_type == "extra_forbidden":
            result.add((_UNKNOWN, "UNKNOWN_FIELD"))
            continue
        result.add((_field_name(location, declared), _TYPE_CODES.get(error_type, "INVALID_FORMAT")))
    return [{"field": field, "code": code} for field, code in sorted(result)]


__all__ = [
    "CURSOR_MAX_LENGTH",
    "PAGE_LIMIT_DEFAULT",
    "PAGE_LIMIT_MAX",
    "cursor_query",
    "declared_field_names",
    "decode_cursor",
    "decode_time_cursor",
    "encode_cursor",
    "field_errors_from_validation",
    "limit_query",
    "parse_idempotency_key",
    "raise_stale_revision",
]
