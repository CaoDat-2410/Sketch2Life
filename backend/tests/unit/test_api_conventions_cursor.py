"""T-7a unit tests of the shared opaque cursor helper (SRS l.1640); no database."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from functools import partial
from typing import Any

import pytest
from fastapi import HTTPException

from sketch2life.interfaces.http.api_conventions import (
    CURSOR_MAX_LENGTH,
    decode_cursor,
    decode_time_cursor,
    encode_cursor,
)

SCOPE = "be1.classes:org-1"
MOMENT = datetime(2026, 11, 19, 10, 30, 15, 123456, tzinfo=UTC)


def _raw(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(text).decode("ascii").rstrip("=")


def _good(**changes: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"i": "class-1", "k": MOMENT.isoformat(), "s": SCOPE, "v": 1}
    payload.update(changes)
    return payload


def _assert_invalid(call: Any) -> None:
    with pytest.raises(HTTPException) as caught:
        call()
    detail: Any = caught.value.detail
    assert caught.value.status_code == 400
    assert detail == {
        "code": "INVALID_REQUEST",
        "field_errors": [{"field": "cursor", "code": "INVALID_FORMAT"}],
    }


def test_round_trip_and_unpadded_url_safe_text() -> None:
    cursor = encode_cursor(scope=SCOPE, sort_key="key-1", item_id="item-1")
    assert "=" not in cursor and "+" not in cursor and "/" not in cursor
    assert decode_cursor(cursor, scope=SCOPE) == ("key-1", "item-1")


def test_time_cursor_round_trip_keeps_microseconds_and_timezone() -> None:
    cursor = encode_cursor(scope=SCOPE, sort_key=MOMENT.isoformat(), item_id="class-1")
    moment, item_id = decode_time_cursor(cursor, scope=SCOPE)
    assert (moment, item_id) == (MOMENT, "class-1")
    assert moment.utcoffset() is not None


def test_encoding_is_compact_and_key_sorted() -> None:
    cursor = encode_cursor(scope="s", sort_key="k", item_id="i")
    decoded = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("ascii")
    assert decoded == '{"i":"i","k":"k","s":"s","v":1}'


def test_wrong_scope_is_invalid() -> None:
    cursor = encode_cursor(scope=SCOPE, sort_key="k", item_id="i")
    _assert_invalid(lambda: decode_cursor(cursor, scope="be1.classes:org-2"))
    _assert_invalid(lambda: decode_cursor(cursor, scope="be1.consents:org-1:class-1"))


@pytest.mark.parametrize(
    "cursor",
    [
        "!!!not base64!!!",
        "abc",
        "é",
        _raw("not an object"),
        _raw([1, 2]),
        _raw({"i": "class-1", "k": "k", "s": SCOPE}),
        _raw({**_good(), "extra": 1}),
        _raw(_good(v=2)),
        _raw(_good(v=True)),
        _raw(_good(v="1")),
        _raw(_good(i="")),
        _raw(_good(i="x" * 129)),
        _raw(_good(i=5)),
        _raw(_good(k="")),
        _raw(_good(k=5)),
        _raw(_good(s=5)),
    ],
)
def test_malformed_cursors_give_the_400_shape(cursor: str) -> None:
    _assert_invalid(lambda: decode_cursor(cursor, scope=SCOPE))


@pytest.mark.parametrize(
    "cursor",
    [
        _raw(_good(i="a\u0000b")),
        _raw(_good(i="a\nb")),
        _raw(_good(i="a\x7fb")),
        _raw(_good(i="café")),
        _raw(_good(k="2026-11-19T10:30:15+00:00\u0000")),
        _raw(_good(k="k\u0001")),
        _raw(_good(k="ké")),
    ],
)
def test_nul_control_and_non_ascii_characters_are_invalid(cursor: str) -> None:
    _assert_invalid(lambda: decode_cursor(cursor, scope=SCOPE))
    _assert_invalid(lambda: decode_time_cursor(cursor, scope=SCOPE))


def test_only_the_canonical_encoding_is_accepted() -> None:
    padded_any = False
    for item_id in ("class-1", "class-12", "class-123"):
        cursor = encode_cursor(scope=SCOPE, sort_key=MOMENT.isoformat(), item_id=item_id)
        assert decode_cursor(cursor, scope=SCOPE)[1] == item_id
        padded = cursor + "=" * (-len(cursor) % 4)
        if padded != cursor:
            padded_any = True
            _assert_invalid(partial(decode_cursor, padded, scope=SCOPE))
    assert padded_any
    # Re-spelled JSON (spaces, unsorted keys) is refused although it carries the same values.
    spaced = json.dumps(_good(), sort_keys=True).encode("utf-8")
    spaced_cursor = base64.urlsafe_b64encode(spaced).decode("ascii").rstrip("=")
    _assert_invalid(lambda: decode_cursor(spaced_cursor, scope=SCOPE))
    reversed_keys = dict(reversed(list(_good().items())))
    unordered = json.dumps(reversed_keys, separators=(",", ":")).encode("utf-8")
    unordered_cursor = base64.urlsafe_b64encode(unordered).decode("ascii").rstrip("=")
    _assert_invalid(lambda: decode_cursor(unordered_cursor, scope=SCOPE))


def test_standard_alphabet_spelling_is_refused() -> None:
    # A payload whose url-safe form contains `-` or `_` must not be accepted with `+` or `/`.
    payload = json.dumps(_good(i="~~~?>>"), sort_keys=True, separators=(",", ":")).encode()
    standard = base64.b64encode(payload).decode("ascii").rstrip("=")
    safe = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    assert standard != safe
    assert decode_cursor(safe, scope=SCOPE)[1] == "~~~?>>"
    _assert_invalid(lambda: decode_cursor(standard, scope=SCOPE))


def test_time_cursor_requires_the_isoformat_spelling() -> None:
    zulu = _raw(_good(k="2026-11-19T10:30:15.123456Z"))
    _assert_invalid(lambda: decode_time_cursor(zulu, scope=SCOPE))
    spaced = _raw(_good(k="2026-11-19 10:30:15.123456+00:00"))
    _assert_invalid(lambda: decode_time_cursor(spaced, scope=SCOPE))
    offset = _raw(_good(k="2026-11-19T17:30:15+07:00"))
    moment, _ = decode_time_cursor(offset, scope=SCOPE)
    assert moment.utcoffset() is not None


def test_non_json_bytes_are_invalid() -> None:
    cursor = base64.urlsafe_b64encode(b"\xff\xfe\x00not json").decode("ascii")
    _assert_invalid(lambda: decode_cursor(cursor, scope=SCOPE))


def test_maximum_length_id_is_accepted() -> None:
    item_id = "x" * 128
    cursor = encode_cursor(scope=SCOPE, sort_key="k", item_id=item_id)
    assert decode_cursor(cursor, scope=SCOPE) == ("k", item_id)


def test_time_cursor_rejects_naive_and_unparsable_timestamps() -> None:
    naive = _raw(_good(k="2026-11-19T10:30:15"))
    _assert_invalid(lambda: decode_time_cursor(naive, scope=SCOPE))
    garbage = _raw(_good(k="yesterday"))
    _assert_invalid(lambda: decode_time_cursor(garbage, scope=SCOPE))


def test_longest_consent_cursor_fits_the_published_maximum() -> None:
    scope = f"be1.consents:{'o' * 128}:{'c' * 128}"
    cursor = encode_cursor(scope=scope, sort_key=MOMENT.isoformat(), item_id="u" * 36)
    assert len(cursor) < CURSOR_MAX_LENGTH
    assert decode_time_cursor(cursor, scope=scope) == (MOMENT, "u" * 36)
