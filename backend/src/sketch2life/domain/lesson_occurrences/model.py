"""Framework-independent rules of the lesson occurrence (FEAT-066 goal v3, T-3a).

SRS l.775 (one approved plan per occurrence), l.798 (occurrence group), l.1652 (create by the
assigned Teacher), l.1699 (revisions and ETags). Nothing here knows HTTP, SQL or a framework.
"""

from __future__ import annotations

import base64
import binascii
import json
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Final

# SRS §6.1.1 (l.396) LessonOccurrence states; T-3a creates DRAFT, T-3d sets APPROVED.
OCCURRENCE_STATES: Final = (
    "DRAFT",
    "DOCUMENT_REVIEW",
    "PLAN_REVIEW",
    "APPROVED",
    "SAMPLE_AVAILABLE",
    "SAMPLE_USED",
    "ARCHIVED",
)
STATE_DRAFT: Final = "DRAFT"
SAMPLE_SLOT_STATES: Final = ("AVAILABLE", "CLAIMED")

TITLE_MAX_LENGTH: Final = 200
CLASS_ID_MAX_LENGTH: Final = 128
CURSOR_MAX_LENGTH: Final = 512

# The Teacher account families that may see an occurrence (be1_organization_assignments.role).
TEACHER_FAMILY_ROLES: Final = frozenset({"teacher", "guide", "observer"})
TEACHER_ROLE: Final = "teacher"

_FORBIDDEN_CATEGORIES: Final = frozenset({"Cc", "Cs"})


class LessonOccurrenceRuleError(ValueError):
    """A value breaks a rule of the occurrence; ``field`` names the request field."""

    def __init__(self, field: str, code: str) -> None:
        self.field = field
        self.code = code
        super().__init__(f"{field}:{code}")


def has_forbidden_characters(text: str) -> bool:
    """True for a control character or a lone surrogate (never stored, never echoed)."""
    return any(unicodedata.category(char) in _FORBIDDEN_CATEGORIES for char in text)


def normalize_title(raw: str) -> str:
    """The stored title: trimmed, 1..200 characters, no control character."""
    title = raw.strip()
    if not title:
        raise LessonOccurrenceRuleError("title", "EMPTY")
    if len(title) > TITLE_MAX_LENGTH:
        raise LessonOccurrenceRuleError("title", "TOO_LONG")
    if has_forbidden_characters(title):
        raise LessonOccurrenceRuleError("title", "INVALID_FORMAT")
    return title


def parse_scheduled_date(raw: object) -> date:
    """An ISO ``YYYY-MM-DD`` calendar date; anything else is ``INVALID_FORMAT``."""
    if not isinstance(raw, str) or len(raw) != 10:
        raise LessonOccurrenceRuleError("scheduled_date", "INVALID_FORMAT")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise LessonOccurrenceRuleError("scheduled_date", "INVALID_FORMAT") from None


class AccessOutcome(StrEnum):
    """Result of a scope decision; the transport maps it to 404, 403 or 409."""

    PROCEED = "PROCEED"
    NOT_FOUND = "NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    ASSIGNMENT_REQUIRED = "ASSIGNMENT_REQUIRED"


@dataclass(frozen=True, slots=True)
class AssignmentFact:
    """One active assignment row of the caller in the class's organization."""

    role: str
    class_id: str | None


def decide_create(rows: Sequence[AssignmentFact], class_id: str) -> AccessOutcome:
    """Teacher assignment decision table for ``POST /v1/lesson-occurrences`` (T-3a-DEC-2).

    ``rows`` are the caller's active teacher-family rows in the class's organization (empty when
    the caller has no valid Teacher identity or no row there: the uniform 404, so a stranger
    never learns that the class exists). Create needs a ``teacher`` row of exactly this class:
    SRS l.775 "Teacher phu trach hien tai" is a per-class assignment, and an organization-wide
    row (``class_id`` NULL) assigns no class.
    """
    if not rows:
        return AccessOutcome.NOT_FOUND
    exact = [row for row in rows if row.class_id == class_id]
    if any(row.role == TEACHER_ROLE for row in exact):
        return AccessOutcome.PROCEED
    if exact:
        return AccessOutcome.FORBIDDEN
    return AccessOutcome.ASSIGNMENT_REQUIRED


def decide_read(rows: Sequence[AssignmentFact], class_id: str) -> AccessOutcome:
    """Read access: any teacher-family row that covers the class (NULL covers every class)."""
    if any(row.class_id is None or row.class_id == class_id for row in rows):
        return AccessOutcome.PROCEED
    return AccessOutcome.NOT_FOUND


def decide_write(
    rows: Sequence[AssignmentFact],
    class_id: str,
    *,
    caller_account_ref: str,
    responsible_teacher_ref: str,
) -> AccessOutcome:
    """Write access to an existing occurrence (T-3b..T-3d): read scope, role, responsibility."""
    covering = [row for row in rows if row.class_id is None or row.class_id == class_id]
    if not covering:
        return AccessOutcome.NOT_FOUND
    if not any(row.role == TEACHER_ROLE for row in covering):
        return AccessOutcome.FORBIDDEN
    if caller_account_ref != responsible_teacher_ref:
        return AccessOutcome.FORBIDDEN
    return AccessOutcome.PROCEED


def encode_cursor(created_at: datetime, occurrence_id: str) -> str:
    payload = json.dumps(
        {"created_at": created_at.isoformat(), "occurrence_id": occurrence_id, "v": 1},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    """Decode an opaque list cursor; any defect is ``INVALID_FORMAT`` on field ``cursor``."""
    try:
        if not 0 < len(cursor) <= CURSOR_MAX_LENGTH:
            raise ValueError
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != {"created_at", "occurrence_id", "v"}:
            raise ValueError
        if type(decoded["v"]) is not int or decoded["v"] != 1:
            raise ValueError
        created_text, occurrence_id = decoded["created_at"], decoded["occurrence_id"]
        if not isinstance(created_text, str) or not isinstance(occurrence_id, str):
            raise ValueError
        if not 0 < len(occurrence_id) <= 36:
            raise ValueError
        created_at = datetime.fromisoformat(created_text)
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError
        return created_at.astimezone(UTC), occurrence_id
    except (binascii.Error, json.JSONDecodeError, UnicodeError, ValueError):
        raise LessonOccurrenceRuleError("cursor", "INVALID_FORMAT") from None


def etag_for_revision(revision: int) -> str:
    """Strong ETag of an occurrence read (C-D7): the quoted revision number."""
    return f'"{revision}"'


def if_none_match_matches(header: str | None, revision: int) -> bool:
    """True when a strong ``If-None-Match`` list names the current revision (or ``*``)."""
    if header is None:
        return False
    current = etag_for_revision(revision)
    return any(token.strip() in {current, "*"} for token in header.split(","))


__all__ = [
    "CLASS_ID_MAX_LENGTH",
    "CURSOR_MAX_LENGTH",
    "OCCURRENCE_STATES",
    "SAMPLE_SLOT_STATES",
    "STATE_DRAFT",
    "TEACHER_FAMILY_ROLES",
    "TEACHER_ROLE",
    "TITLE_MAX_LENGTH",
    "AccessOutcome",
    "AssignmentFact",
    "LessonOccurrenceRuleError",
    "decide_create",
    "decide_read",
    "decide_write",
    "decode_cursor",
    "encode_cursor",
    "etag_for_revision",
    "has_forbidden_characters",
    "if_none_match_matches",
    "normalize_title",
    "parse_scheduled_date",
]
