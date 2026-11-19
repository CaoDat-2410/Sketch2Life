"""CONV-1 unit tests for the shared API-convention helpers (FEAT-066 D-066-68, D-066-71)."""

from __future__ import annotations

from typing import Annotated

import pytest
from fastapi import Body, Header, HTTPException, Query
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from starlette.requests import Request

from sketch2life.interfaces.http import api_conventions as conventions


class _Child(BaseModel):
    display_name: str
    tags: list[str] = []


class _Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=10)
    child: _Child
    nested: _Payload | None = None


def _endpoint(
    item_id: str,
    payload: Annotated[_Payload, Body()],
    limit: int = Query(default=25, ge=1, le=100),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> None:
    return None


ROUTE = APIRoute("/items/{item_id}", _endpoint, methods=["POST"])


def _request(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request({"type": "http", "method": "POST", "path": "/", "headers": headers})


def test_page_limit_defaults() -> None:
    assert conventions.PAGE_LIMIT_DEFAULT == 25
    assert conventions.PAGE_LIMIT_MAX == 100
    limit = conventions.limit_query()
    assert limit.default == 25


def test_parse_idempotency_key_accepts_one_visible_ascii_value() -> None:
    assert conventions.parse_idempotency_key(_request([(b"idempotency-key", b"abc-123")])) == (
        "abc-123"
    )


@pytest.mark.parametrize(
    ("headers", "field_code"),
    [
        ([], "REQUIRED"),
        ([(b"idempotency-key", b"a"), (b"idempotency-key", b"b")], "INVALID_FORMAT"),
        ([(b"idempotency-key", b"has space")], "INVALID_FORMAT"),
        ([(b"idempotency-key", b"x" * 129)], "INVALID_FORMAT"),
    ],
)
def test_parse_idempotency_key_rejections(
    headers: list[tuple[bytes, bytes]], field_code: str
) -> None:
    with pytest.raises(HTTPException) as caught:
        conventions.parse_idempotency_key(_request(headers))
    assert caught.value.status_code == 400
    assert caught.value.detail == {
        "code": "INVALID_REQUEST",
        "field_errors": [{"field": "Idempotency-Key", "code": field_code}],
    }


def test_raise_stale_revision_carries_current_version_or_etag() -> None:
    with pytest.raises(HTTPException) as caught:
        conventions.raise_stale_revision(current_version=4)
    assert caught.value.status_code == 409
    assert caught.value.detail == {"code": "STALE_REVISION", "current_version": 4}
    with pytest.raises(HTTPException) as caught_etag:
        conventions.raise_stale_revision(etag="5")
    assert caught_etag.value.headers == {"ETag": '"5"'}


def test_declared_names_cover_params_aliases_and_nested_models() -> None:
    names = conventions.declared_field_names(ROUTE)
    for expected in ("item_id", "payload", "limit", "Idempotency-Key", "title", "child"):
        assert expected in names
    assert "display_name" in names
    assert "nested" in names


def test_field_errors_never_echo_unknown_keys() -> None:
    issues = [
        {"type": "extra_forbidden", "loc": ("body", "payload", "secret_child_name")},
        {"type": "string_too_long", "loc": ("body", "payload", "title")},
        {"type": "less_than_equal", "loc": ("query", "limit")},
        {"type": "missing", "loc": ("body", "payload", "child", "display_name")},
        {"type": "value_error", "loc": ("body", "payload", "free_form_key")},
        {"type": "int_parsing", "loc": ("body", "payload", "child", "tags", 3)},
    ]
    errors = conventions.field_errors_from_validation(ROUTE, issues)
    assert {"field": "<unknown>", "code": "UNKNOWN_FIELD"} in errors
    assert {"field": "payload.title", "code": "TOO_LONG"} in errors
    assert {"field": "limit", "code": "OUT_OF_RANGE"} in errors
    assert {"field": "payload.child.display_name", "code": "REQUIRED"} in errors
    assert {"field": "<unknown>", "code": "INVALID_FORMAT"} in errors
    assert {"field": "payload.child.tags", "code": "INVALID_TYPE"} in errors
    assert all("secret_child_name" not in error["field"] for error in errors)


@pytest.mark.parametrize(
    ("error_type", "code"), [("missing", "REQUIRED"), ("string_too_long", "INVALID_FORMAT")]
)
def test_idempotency_header_issues(error_type: str, code: str) -> None:
    errors = conventions.field_errors_from_validation(
        ROUTE, [{"type": error_type, "loc": ("header", "Idempotency-Key")}]
    )
    assert errors == [{"field": "Idempotency-Key", "code": code}]


def test_field_errors_without_a_route_are_unknown() -> None:
    errors = conventions.field_errors_from_validation(
        None, [{"type": "missing", "loc": ("body", "anything")}]
    )
    assert errors == [{"field": "<unknown>", "code": "REQUIRED"}]
