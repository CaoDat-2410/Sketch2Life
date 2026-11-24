"""Shared validators of the support-needs request bodies of both families (T-12c).

The two request models (Parent and BE1) differ only in their base class; the rules are the
domain's. An error names a field and a stable code and never carries the submitted text.
"""

from __future__ import annotations

from pydantic_core import PydanticCustomError

from sketch2life.domain.support_needs import (
    SupportNeedsRuleViolation,
    check_category,
    check_note,
)

# The type names are the ones both error vocabularies already map: string_too_short to EMPTY,
# string_too_long to TOO_LONG, anything else to INVALID_FORMAT.
_ERROR_TYPES = {
    "EMPTY": ("string_too_short", "value must contain non-whitespace text"),
    "TOO_LONG": ("string_too_long", "value is too long"),
    "INVALID_FORMAT": ("invalid_characters", "control characters are not allowed"),
    "DIAGNOSIS_LIKE": ("diagnosis_like", "value must not name a diagnosis"),
}


def _raise(violation: SupportNeedsRuleViolation) -> PydanticCustomError:
    error_type, message = _ERROR_TYPES.get(violation.code, ("invalid_value", "value is invalid"))
    return PydanticCustomError(error_type, message)


def validated_category(value: str | None) -> str | None:
    if value is not None:
        try:
            check_category(value)
        except SupportNeedsRuleViolation as violation:
            raise _raise(violation) from None
    return value


def validated_note(value: str | None) -> str | None:
    if value is not None:
        try:
            check_note(value)
        except SupportNeedsRuleViolation as violation:
            raise _raise(violation) from None
    return value


def require_one_value(category: str | None, note: str | None) -> None:
    if category is None and note is None:
        raise PydanticCustomError("value_error", "at least one value is required")


__all__ = ["require_one_value", "validated_category", "validated_note"]
