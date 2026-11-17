"""Strict request and response contracts for Parent profile routes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class ParentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class CreateParentProfileRequest(ParentRequest):
    display_name: str = Field(min_length=1, max_length=120)
    age_months: StrictInt = Field(ge=36, le=120)
    interests_summary: str | None = Field(default=None, max_length=2000)

    @field_validator("display_name")
    @classmethod
    def display_name_must_contain_visible_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("display_name must contain non-whitespace text")
        return value


class PatchParentProfileRequest(ParentRequest):
    expected_revision: StrictInt = Field(ge=1)
    display_name: str = Field(min_length=1, max_length=120)
    age_months: StrictInt = Field(ge=36, le=120)
    interests_summary: str | None = Field(default=None, max_length=2000)

    @field_validator("display_name")
    @classmethod
    def display_name_must_contain_visible_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("display_name must contain non-whitespace text")
        return value


class ParentProfileReference(BaseModel):
    profile_id: str
    revision_no: int
    revision_hash: str


class ParentProfileView(ParentProfileReference):
    display_name: str
    age_months: int
    age_band_ref: str | None
    age_band_version: str | None
    interests_summary: str | None
    state: str
    data_origin: str


class ParentProfileDeletePendingView(BaseModel):
    profile_id: str
    state: Literal["DELETE_PENDING"]
    request_id: str


class ParentProfileListView(BaseModel):
    items: list[ParentProfileView]
    next_cursor: str | None
    request_id: str


class ParentErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: str
    retryable: bool
    request_id: str
    retry_after_seconds: int | None = None
    current_version: int | None = None
    field_errors: list[dict[str, str]] | None = None


def parent_field_errors(issues: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Map validation failures to the public, non-echoing Parent vocabulary."""
    known_fields = {
        "age_months",
        "cursor",
        "display_name",
        "expected_revision",
        "interests_summary",
        "limit",
        "profile_id",
        "Idempotency-Key",
    }
    result: set[tuple[str, str]] = set()
    for issue in issues:
        error_type = issue.get("type")
        if error_type == "extra_forbidden":
            result.add(("<unknown>", "UNKNOWN_FIELD"))
            continue
        location = issue.get("loc")
        parts = location if isinstance(location, (tuple, list)) else ()
        field = next(
            (part for part in reversed(parts) if isinstance(part, str) and part != "body"),
            "body",
        )
        if field not in known_fields and field != "body":
            field = "<unknown>"
        if error_type == "missing":
            code = "REQUIRED"
        elif error_type in {"string_too_long"}:
            code = "TOO_LONG"
        elif error_type in {"greater_than", "greater_than_equal", "less_than", "less_than_equal"}:
            code = "OUT_OF_RANGE"
        elif error_type in {"value_error", "string_too_short"}:
            code = "EMPTY"
        elif error_type in {"int_type", "string_type", "bool_type", "model_type", "list_type"}:
            code = "INVALID_TYPE"
        elif error_type in {"json_invalid", "uuid_parsing", "uuid_type"}:
            code = "INVALID_FORMAT"
        else:
            code = "INVALID_FORMAT"
        result.add((field, code))
    return [{"field": field, "code": code} for field, code in sorted(result)]


def parent_error_payload(
    *,
    code: str,
    message: str,
    request_id: str,
    retryable: bool = False,
    field_errors: list[dict[str, str]] | None = None,
    current_version: int | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "code": code,
        "message": message,
        "correlation_id": request_id,
        "retryable": retryable,
        "request_id": request_id,
    }
    if field_errors:
        body["field_errors"] = [
            {"field": field, "code": error_code}
            for field, error_code in sorted(
                {(item["field"], item["code"]) for item in field_errors}
            )
        ]
    if current_version is not None:
        body["current_version"] = current_version
    return body
