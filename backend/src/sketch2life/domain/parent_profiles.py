"""Provider- and database-independent Parent profile rules."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

MIN_PARENT_CHILD_AGE_MONTHS = 36
MAX_PARENT_CHILD_AGE_MONTHS = 120
MAX_PARENT_DISPLAY_NAME_LENGTH = 120
MAX_PARENT_INTERESTS_LENGTH = 800


class ParentProfileRuleViolation(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentProfileRevisionInput:
    age_months: int
    display_name: str
    interests_summary: str


def normalize_profile_revision(
    *, age_months: int, display_name: str, interests_summary: str
) -> ParentProfileRevisionInput:
    normalized_name = display_name.strip()
    normalized_interests = interests_summary.strip()
    if not MIN_PARENT_CHILD_AGE_MONTHS <= age_months <= MAX_PARENT_CHILD_AGE_MONTHS:
        raise ParentProfileRuleViolation("PARENT_PROFILE_AGE_OUT_OF_RANGE")
    if not normalized_name or len(normalized_name) > MAX_PARENT_DISPLAY_NAME_LENGTH:
        raise ParentProfileRuleViolation("PARENT_PROFILE_DISPLAY_NAME_INVALID")
    if len(normalized_interests) > MAX_PARENT_INTERESTS_LENGTH:
        raise ParentProfileRuleViolation("PARENT_PROFILE_INTERESTS_TOO_LONG")
    return ParentProfileRevisionInput(
        age_months=age_months,
        display_name=normalized_name,
        interests_summary=normalized_interests,
    )


def profile_revision_sha256(value: ParentProfileRevisionInput) -> str:
    canonical = json.dumps(
        {
            "age_months": value.age_months,
            "display_name": value.display_name,
            "interests_summary": value.interests_summary,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


__all__ = [
    "MAX_PARENT_CHILD_AGE_MONTHS",
    "MAX_PARENT_DISPLAY_NAME_LENGTH",
    "MAX_PARENT_INTERESTS_LENGTH",
    "MIN_PARENT_CHILD_AGE_MONTHS",
    "ParentProfileRevisionInput",
    "ParentProfileRuleViolation",
    "normalize_profile_revision",
    "profile_revision_sha256",
]
