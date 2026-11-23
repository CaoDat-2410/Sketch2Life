"""Framework-independent rules of the occurrence plan revision (FEAT-066 goal v3, T-3d).

SRS l.547-548 (an occurrence keeps many activities; a Teacher-written activity needs its safety
checklist), l.775 (one approved plan per occurrence), l.1659-1660 (create a draft plan revision;
confirm with the expected plan hash and the checklist), l.1699 (a stale request never overwrites
the head). Nothing here knows HTTP, SQL or a framework.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from sketch2life.domain.lesson_occurrences.documents import etag_matches
from sketch2life.domain.lesson_occurrences.model import (
    LessonOccurrenceRuleError,
    has_forbidden_characters,
)
from sketch2life.domain.lesson_occurrences.safety_checklist import ChecklistEntry

# Technical limits (T-3d-DEC-2, not SRS numbers): they equal the Lesson Library limits so a whole
# library lesson can be copied, and the database CHECKs of DDL-A.
OBJECTIVES_MAX: Final = 12
OBJECTIVE_MAX_CHARS: Final = 1000
DIRECTION_MAX_CHARS: Final = 2000
SAFETY_NOTES_MAX_CHARS: Final = 2000
ACTIVITIES_MAX: Final = 24
CUSTOM_TITLE_MAX_CHARS: Final = 160
CUSTOM_DESCRIPTION_MAX_CHARS: Final = 4000
CURSOR_MAX_LENGTH: Final = 512

PLAN_STATES: Final = ("DRAFT", "APPROVED", "SUPERSEDED")
PLAN_TRANSITIONS: Final = frozenset({("DRAFT", "APPROVED"), ("APPROVED", "SUPERSEDED")})
ACTIVITY_KINDS: Final = ("LESSON", "CUSTOM", "CATALOG")
# Occurrence states from which a confirm moves the occurrence to ``APPROVED`` (SRS §6.1.1, l.396);
# from a later state the pointer changes and the state stays.
PRE_APPROVAL_STATES: Final = frozenset({"DRAFT", "DOCUMENT_REVIEW", "PLAN_REVIEW"})


def can_transition(old: str, new: str) -> bool:
    """The plan state machine: ``DRAFT -> APPROVED -> SUPERSEDED`` and nothing else."""
    return (old, new) in PLAN_TRANSITIONS


def occurrence_state_after_confirm(current: str) -> str:
    return "APPROVED" if current in PRE_APPROVAL_STATES else current


@dataclass(frozen=True, slots=True)
class ActivityInput:
    """One requested activity as the client sent it."""

    kind: str
    lesson_activity_id: str | None = None
    title: str | None = None
    description: str | None = None


def canonical_hash(value: Any) -> str:
    """SHA-256 of the canonical JSON; the algorithm of the Lesson Library content hash."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def text_problem(value: str, *, required: bool) -> str | None:
    """A NUL or a lone surrogate is ``INVALID_FORMAT``; a blank required text is ``EMPTY``.

    The text is stored exactly as sent (no stripping), so these are the only rules the database
    cannot take. The value is never echoed.
    """
    if "\x00" in value:
        return "INVALID_FORMAT"
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return "INVALID_FORMAT"
    if required and not value.strip():
        return "EMPTY"
    return None


def normalize_safety_notes(value: str | None) -> str | None:
    """Omitted, null and blank notes are stored as NULL; other text is stored exactly."""
    if value is None or not value.strip():
        return None
    return value


def plan_request_problems(
    *,
    objectives: Sequence[str],
    teacher_direction: str,
    safety_notes: str | None,
    activities: Sequence[ActivityInput],
    custom_allowed: bool,
) -> list[dict[str, str]]:
    """Field errors of a plan revision request that need no database (T-3d-DEC-2, DEC-3).

    ``custom_allowed`` is false while no safety checklist exists: a ``CUSTOM`` activity is then
    ``NOT_SUPPORTED`` on its ``kind`` (an explicit refusal the client can show, never a plan that
    can never be approved). ``CATALOG`` waits for TD-16.
    """
    errors: list[dict[str, str]] = []
    for index, objective in enumerate(objectives):
        problem = text_problem(objective, required=True)
        if problem:
            errors.append({"field": f"objectives[{index}]", "code": problem})
    problem = text_problem(teacher_direction, required=True)
    if problem:
        errors.append({"field": "teacher_direction", "code": problem})
    if safety_notes is not None:
        problem = text_problem(safety_notes, required=False)
        if problem:
            errors.append({"field": "safety_notes", "code": problem})
    for index, activity in enumerate(activities):
        base = f"activities[{index}]"
        if activity.kind == "CATALOG":
            errors.append({"field": f"{base}.kind", "code": "NOT_SUPPORTED"})
            continue
        if activity.kind == "LESSON":
            if activity.lesson_activity_id is None:
                errors.append({"field": f"{base}.lesson_activity_id", "code": "REQUIRED"})
            for name, given in (("title", activity.title), ("description", activity.description)):
                if given is not None:
                    errors.append({"field": f"{base}.{name}", "code": "UNKNOWN_FIELD"})
            continue
        # CUSTOM
        if not custom_allowed:
            errors.append({"field": f"{base}.kind", "code": "NOT_SUPPORTED"})
        if activity.lesson_activity_id is not None:
            errors.append({"field": f"{base}.lesson_activity_id", "code": "UNKNOWN_FIELD"})
        if activity.title is None:
            errors.append({"field": f"{base}.title", "code": "REQUIRED"})
        else:
            problem = text_problem(activity.title, required=True)
            if problem is None and has_forbidden_characters(activity.title):
                problem = "INVALID_FORMAT"
            if problem:
                errors.append({"field": f"{base}.title", "code": problem})
        if activity.description is None:
            errors.append({"field": f"{base}.description", "code": "REQUIRED"})
        else:
            problem = text_problem(activity.description, required=True)
            if problem:
                errors.append({"field": f"{base}.description", "code": problem})
    return errors


def activity_hash_entry(
    *,
    order: int,
    kind: str,
    catalog_activity_ref: str | None,
    activity_version: int | None,
    title: str | None,
    description: str | None,
    snapshot_hash: str | None,
) -> dict[str, Any]:
    return {
        "order": order,
        "kind": kind,
        "catalog_activity_ref": catalog_activity_ref,
        "activity_version": activity_version,
        "title": title,
        "description": description,
        "snapshot_hash": snapshot_hash,
    }


def plan_content_hash(
    *,
    occurrence_id: str,
    document: Mapping[str, str] | None,
    objectives: Sequence[str],
    teacher_direction: str,
    safety_notes: str | None,
    lesson_ref: Mapping[str, Any] | None,
    activities: Sequence[Mapping[str, Any]],
) -> str:
    """The hash of the content that gets approved (T-3d-DEC-4, SRS l.1660 "expected plan hash").

    Excluded: the ids and number of the revision, timestamps, state and the checklist results, so
    the hash names what the Teacher reads and approves, not bookkeeping around it.
    """
    return canonical_hash(
        {
            "occurrence_id": occurrence_id,
            "document": dict(document) if document is not None else None,
            "objectives": list(objectives),
            "teacher_direction": teacher_direction,
            "safety_notes": safety_notes,
            "lesson_ref": dict(lesson_ref) if lesson_ref is not None else None,
            "activities": [dict(activity) for activity in activities],
        }
    )


def create_fingerprint(
    *,
    expected_head_revision_no: int,
    document_ref: Mapping[str, Any] | None,
    objectives: Sequence[str],
    teacher_direction: str,
    safety_notes: str | None,
    activities: Sequence[ActivityInput],
) -> str:
    """Request fingerprint of a plan revision create: the fence and the content as requested."""
    return canonical_hash(
        {
            "expected_head_revision_no": expected_head_revision_no,
            "document_revision_ref": dict(document_ref) if document_ref is not None else None,
            "objectives": list(objectives),
            "teacher_direction": teacher_direction,
            "safety_notes": safety_notes,
            "activities": [
                {
                    "kind": activity.kind,
                    "lesson_activity_id": activity.lesson_activity_id,
                    "title": activity.title,
                    "description": activity.description,
                }
                for activity in activities
            ],
        }
    )


def confirm_fingerprint(
    revision_no: int, expected_plan_hash: str, entries: Sequence[ChecklistEntry]
) -> str:
    """Request fingerprint of a confirm: the revision, the hash and the answers, order-free."""
    return canonical_hash(
        {
            "revision_no": revision_no,
            "expected_plan_hash": expected_plan_hash,
            "checklist": sorted(
                (
                    {
                        "activity_order": entry.activity_order,
                        "checklist_version": entry.checklist_version,
                        "items": sorted(
                            ({"item_id": a.item_id, "checked": a.checked} for a in entry.items),
                            key=lambda row: (str(row["item_id"]), bool(row["checked"])),
                        ),
                    }
                    for entry in entries
                ),
                key=lambda row: (int(row["activity_order"]), str(row["checklist_version"])),
            ),
        }
    )


def plan_etag_value(content_hash: str, state: str) -> str:
    """Content is immutable but the state changes at confirm, so the hash alone is no validator."""
    return f"{content_hash}.{state}"


def plan_etag(content_hash: str, state: str) -> str:
    return f'"{plan_etag_value(content_hash, state)}"'


def encode_plan_cursor(revision_no: int) -> str:
    raw = json.dumps({"k": "plan", "n": revision_no, "v": 1}, sort_keys=True, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_plan_cursor(cursor: str) -> int:
    """A list cursor is the last revision number of the previous page; any defect is a 400."""
    try:
        if not 0 < len(cursor) <= CURSOR_MAX_LENGTH:
            raise ValueError
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != {"k", "n", "v"}:
            raise ValueError
        number = decoded["n"]
        if decoded["k"] != "plan" or type(decoded["v"]) is not int or decoded["v"] != 1:
            raise ValueError
        if type(number) is not int or number < 1:
            raise ValueError
        return number
    except (binascii.Error, json.JSONDecodeError, UnicodeError, ValueError):
        raise LessonOccurrenceRuleError("cursor", "INVALID_FORMAT") from None


__all__ = [
    "ACTIVITIES_MAX",
    "ACTIVITY_KINDS",
    "CUSTOM_DESCRIPTION_MAX_CHARS",
    "CUSTOM_TITLE_MAX_CHARS",
    "DIRECTION_MAX_CHARS",
    "OBJECTIVES_MAX",
    "OBJECTIVE_MAX_CHARS",
    "PLAN_STATES",
    "PLAN_TRANSITIONS",
    "PRE_APPROVAL_STATES",
    "SAFETY_NOTES_MAX_CHARS",
    "ActivityInput",
    "activity_hash_entry",
    "can_transition",
    "canonical_hash",
    "confirm_fingerprint",
    "create_fingerprint",
    "decode_plan_cursor",
    "encode_plan_cursor",
    "etag_matches",
    "normalize_safety_notes",
    "occurrence_state_after_confirm",
    "plan_content_hash",
    "plan_etag",
    "plan_etag_value",
    "plan_request_problems",
    "text_problem",
]
