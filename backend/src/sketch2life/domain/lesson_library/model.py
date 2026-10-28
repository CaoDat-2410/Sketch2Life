"""Pure rules for versioned, Vietnamese-first reusable lesson content."""

from __future__ import annotations

import hashlib
import json
from typing import Any


class LessonLibraryRuleError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_content_hash(content: dict[str, Any]) -> str:
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_content(content: dict[str, Any]) -> None:
    """Validate content invariants without framework or persistence dependencies."""
    if content.get("locale") != "vi-VN":
        raise LessonLibraryRuleError("UNSUPPORTED_LOCALE")
    for field in ("title", "topic", "target_age_band_ref", "drawing_subject"):
        value = content.get(field)
        if not isinstance(value, str) or not value.strip():
            raise LessonLibraryRuleError("REQUIRED_CONTENT_FIELD")
    version = content.get("target_age_band_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise LessonLibraryRuleError("INVALID_AGE_BAND_VERSION")
    objectives = content.get("objectives")
    activities = content.get("activities")
    if not isinstance(objectives, list) or not 1 <= len(objectives) <= 12:
        raise LessonLibraryRuleError("INVALID_OBJECTIVES")
    if not isinstance(activities, list) or not 1 <= len(activities) <= 24:
        raise LessonLibraryRuleError("INVALID_ACTIVITIES")
    for objective in objectives:
        if not isinstance(objective, str) or not objective.strip():
            raise LessonLibraryRuleError("INVALID_OBJECTIVES")
    for activity in activities:
        if not isinstance(activity, dict):
            raise LessonLibraryRuleError("INVALID_ACTIVITIES")
        for field in ("title", "objective", "instructions_text", "activity_kind"):
            value = activity.get(field)
            if not isinstance(value, str) or not value.strip():
                raise LessonLibraryRuleError("INVALID_ACTIVITIES")


def next_version_number(current_version_no: int) -> int:
    if current_version_no < 0:
        raise LessonLibraryRuleError("INVALID_VERSION")
    return current_version_no + 1


def can_read_as_parent(*, moderation_state: str, lesson_state: str, grant_states: set[str]) -> bool:
    return (
        moderation_state == "VISIBLE"
        and lesson_state == "ACTIVE"
        and bool(grant_states.intersection({"VIEW", "REUSE"}))
    )


__all__ = [
    "LessonLibraryRuleError",
    "can_read_as_parent",
    "canonical_content_hash",
    "next_version_number",
    "validate_content",
]
