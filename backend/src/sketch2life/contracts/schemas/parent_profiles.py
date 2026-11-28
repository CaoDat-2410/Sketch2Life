"""Strict request and response contracts for Parent profile routes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from sketch2life.contracts.schemas.support_needs import (
    require_one_value,
    validated_category,
    validated_note,
)
from sketch2life.domain.parent_profile_context import (
    FORBIDDEN_REF_CONTROLS,
    FORBIDDEN_TEXT_CONTROLS,
    MAX_SHORT_TEXT_CHARS,
    MAX_SOURCE_REF_CHARS,
    SOURCE_KIND_PATTERN,
    parse_approximate_date,
)
from sketch2life.domain.support_needs import (
    MAX_CATEGORY_CHARS,
    MAX_NOTE_CHARS,
    MAX_REVISION,
)


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


class CreateParentContextEntryRequest(ParentRequest):
    """T-12a: one adult-entered entry. ``source_ref`` is stored, never returned or snapshotted."""

    entry_kind: Literal["OBSERVATION", "ACHIEVEMENT", "OUTSIDE_EXPERIENCE"]
    short_text: StrictStr = Field(min_length=1, max_length=MAX_SHORT_TEXT_CHARS)
    source_kind: StrictStr = Field(pattern=SOURCE_KIND_PATTERN.pattern)
    source_ref: StrictStr | None = Field(default=None, max_length=MAX_SOURCE_REF_CHARS)
    approximate_date: StrictStr | None = Field(
        default=None, json_schema_extra={"format": "date"}
    )

    @field_validator("short_text")
    @classmethod
    def short_text_must_contain_visible_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("short_text must contain non-whitespace text")
        if FORBIDDEN_TEXT_CONTROLS.search(value) is not None:
            raise PydanticCustomError("invalid_characters", "control characters are not allowed")
        return value

    @field_validator("source_ref")
    @classmethod
    def source_ref_must_contain_visible_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("source_ref must contain non-whitespace text")
        if value is not None and FORBIDDEN_REF_CONTROLS.search(value) is not None:
            raise PydanticCustomError("invalid_characters", "control characters are not allowed")
        return value

    @field_validator("approximate_date")
    @classmethod
    def approximate_date_must_be_a_calendar_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            parse_approximate_date(value)
        except ValueError:
            raise PydanticCustomError(
                "invalid_date", "approximate_date must be a YYYY-MM-DD calendar date"
            ) from None
        return value


class SupportNeedsPutV1(ParentRequest):
    """T-12c: replace the encrypted support needs of a profile (``expected_revision`` 0 = none yet).

    Both keys are required and nullable; text is kept exactly as sent. Validation errors name the
    field and a code, never the submitted text.
    """

    expected_revision: StrictInt = Field(ge=0, le=MAX_REVISION)
    category: StrictStr | None = Field(max_length=MAX_CATEGORY_CHARS)
    note: StrictStr | None = Field(max_length=MAX_NOTE_CHARS)

    @field_validator("category")
    @classmethod
    def category_rules(cls, value: str | None) -> str | None:
        return validated_category(value)

    @field_validator("note")
    @classmethod
    def note_rules(cls, value: str | None) -> str | None:
        return validated_note(value)

    @model_validator(mode="after")
    def at_least_one_value(self) -> SupportNeedsPutV1:
        require_one_value(self.category, self.note)
        return self


class ParentSupportNeedsV1(BaseModel):
    """The decrypted record; revision 0 means no record (both values null)."""

    contract: Literal["ParentSupportNeedsV1"]
    profile_id: str = Field(json_schema_extra={"format": "uuid"})
    revision: int = Field(ge=0)
    category: str | None
    note: str | None


class ParentSupportNeedsWriteV1(BaseModel):
    """The safe answer of a write: the new revision only, never a value."""

    contract: Literal["ParentSupportNeedsWriteV1"]
    profile_id: str = Field(json_schema_extra={"format": "uuid"})
    revision: int = Field(ge=1)


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


class ParentContextEntryView(BaseModel):
    """The public shape of an entry (no ``source_ref``, no ``created_by``)."""

    context_entry_id: str = Field(json_schema_extra={"format": "uuid"})
    entry_kind: Literal["OBSERVATION", "ACHIEVEMENT", "OUTSIDE_EXPERIENCE"]
    short_text: str
    source_kind: str
    approximate_date: str | None = Field(json_schema_extra={"format": "date"})
    created_at: str = Field(json_schema_extra={"format": "date-time"})


class ParentContextEntryEnvelope(BaseModel):
    context_entry: ParentContextEntryView


class ParentContextEntryListView(BaseModel):
    context_entries: list[ParentContextEntryView]
    next_cursor: str | None
    limit: int


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
        "approximate_date",
        "category",
        "cursor",
        "display_name",
        "entry_kind",
        "expected_revision",
        "interests_summary",
        "limit",
        "note",
        "profile_id",
        "short_text",
        "source_kind",
        "source_ref",
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
        elif error_type == "diagnosis_like":
            code = "DIAGNOSIS_LIKE"
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
