"""Pure rules for versioned, Vietnamese-first reusable lesson content."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LessonLibraryRuleError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_content_hash(content: dict[str, Any]) -> str:
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def verify_remix_source_content(
    content: dict[str, Any], *, stored_hash: str, requested_hash: str,
) -> str:
    """Return the canonical source hash or reject an authorized stale/corrupt source pin."""
    try:
        validate_content(content)
        computed_hash = canonical_content_hash(content)
    except (LessonLibraryRuleError, TypeError, ValueError) as exc:
        raise LessonLibraryRuleError("STALE_SOURCE_VERSION") from exc
    if (
        not _SHA256.fullmatch(stored_hash)
        or not _SHA256.fullmatch(requested_hash)
        or computed_hash != stored_hash
        or stored_hash != requested_hash
    ):
        raise LessonLibraryRuleError("STALE_SOURCE_VERSION")
    return computed_hash


def remix_request_fingerprint(
    *, destination_organization_id: str, lesson_id: str,
    source_version_id: str, source_content_sha256: str,
) -> str:
    """Bind a replay key to the destination and exact authorized source pin."""
    return canonical_content_hash(
        {
            "operation": "POST /lesson-library/remixes",
            "destination_organization_id": destination_organization_id,
            "lesson_id": lesson_id,
            "source_version_id": source_version_id,
            "source_content_sha256": source_content_sha256,
        }
    )


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


def decline_parent_group_invitation(current_state: str, *, invitation_expired: bool) -> str:
    """Return the decline state or a stable lifecycle error without mutating persistence."""
    if current_state == "expired" or (
        current_state == "invited" and invitation_expired
    ):
        raise LessonLibraryRuleError("INVITATION_EXPIRED")
    if current_state != "invited":
        raise LessonLibraryRuleError("INVALID_STATE_TRANSITION")
    return "declined"


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
    "decline_parent_group_invitation",
    "next_version_number",
    "remix_request_fingerprint",
    "validate_content",
    "verify_remix_source_content",
]
