"""Framework-independent rules of the Teacher StoryRun create (FEAT-066 goal v3, T-4b2).

SRS l.1445-1449 (UC-05: one confirmed child, the approved plan, no array of children), l.1663 (the
route and its body), l.495 and l.553 (the Teacher lock; ``created_by_actor_ref`` is provenance
only),
l.549 (a minimal snapshot) and BR-34 (no name, no media, no draw index in any stored value). Nothing
here knows HTTP, SQL or a framework.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, Final

TEACHER_CONTEXT_SCHEMA: Final = "sketch2life.teacher-context.v1"
TEACHER_PIN_SCHEMA: Final = "sketch2life.teacher-run-pin.v1"

# The keys that mark a body as a Teacher body (a Parent body has none of them).
TEACHER_BODY_KEYS: Final = frozenset(
    {
        "profile_ref",
        "occurrence_id",
        "plan",
        "activity_id",
        "selection_id",
        "selection_sha256",
    }
)
# The spellings of a request for more than one child (SRS l.870, l.1449, l.1663: no array).
MULTI_CHILD_KEYS: Final = frozenset({"profile_refs", "child_ids", "children", "profiles"})
DISPATCH_KEYS: Final = TEACHER_BODY_KEYS | MULTI_CHILD_KEYS

# The context keeps the text a Teacher typed only up to these bounds (the plan hash pins the rest);
# the whole snapshot stays below the 32 KiB of ``ck_story_run_input_parent_context``.
CONTEXT_OBJECTIVES_MAX: Final = 12
CONTEXT_OBJECTIVE_CHARS: Final = 400
CONTEXT_DIRECTION_CHARS: Final = 1000
CONTEXT_ACTIVITY_TITLE_CHARS: Final = 200
CONTEXT_MAX_BYTES: Final = 32_768
PIN_MAX_BYTES: Final = 1_048_576

# The run states in which the Teacher lock is released (SRS l.394, l.495, l.1020); SAFETY_BLOCKED is
# an adult-wait state and keeps the lock. DDL-B2 holds the same list in its CHECK and its trigger.
LOCK_FREE_STATES: Final = frozenset(
    {"COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"}
)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_json_object(raw: bytes) -> dict[str, Any] | None:
    """The body as a JSON object, or ``None`` for an empty body, invalid JSON or any other value."""

    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def is_teacher_shaped(body: Mapping[str, Any] | None) -> bool:
    """A JSON object with at least one Teacher key or multi-child spelling goes to the Teacher
    branch; everything else (a Parent body, an empty body, invalid JSON, an array) stays Parent."""

    return body is not None and not DISPATCH_KEYS.isdisjoint(body)


def multi_child_requested(body: Mapping[str, Any]) -> bool:
    """True when the body asks for more than one child: a multi-child key, or an array as
    ``profile_ref`` or as ``profile_ref.id`` (SRS l.870, l.1449, l.1723)."""

    if not MULTI_CHILD_KEYS.isdisjoint(body):
        return True
    profile_ref = body.get("profile_ref")
    if isinstance(profile_ref, list):
        return True
    return isinstance(profile_ref, Mapping) and isinstance(profile_ref.get("id"), list)


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit]


def build_context_snapshot(
    *,
    selection_id: str,
    age_months: int,
    age_revision: int,
    objectives: Sequence[object],
    teacher_direction: str,
    activity_title: str | None,
    activity_snapshot_hash: str | None,
) -> dict[str, Any]:
    """The minimal context of a Teacher run: no name, no media, no seed, no drawn index."""

    snapshot: dict[str, Any] = {
        "schema_version": TEACHER_CONTEXT_SCHEMA,
        "selection_id": selection_id,
        "age_months": age_months,
        "age_revision": age_revision,
        "objectives": [
            _clip(str(item), CONTEXT_OBJECTIVE_CHARS)
            for item in objectives[:CONTEXT_OBJECTIVES_MAX]
        ],
        "teacher_direction": _clip(teacher_direction, CONTEXT_DIRECTION_CHARS),
        "activity_title": (
            _clip(activity_title, CONTEXT_ACTIVITY_TITLE_CHARS) if activity_title else None
        ),
        "activity_snapshot_hash": activity_snapshot_hash,
    }
    if len(canonical_json(snapshot).encode("utf-8")) > CONTEXT_MAX_BYTES:
        raise ValueError("the Teacher context snapshot exceeds its bound")
    return snapshot


def build_pin_snapshot(
    *,
    occurrence_id: str,
    plan_revision_id: str,
    plan_revision_no: int,
    plan_hash: str,
    activity: Mapping[str, Any],
    lesson: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """The pins of the run (SRS l.1448): occurrence, approved plan revision and hash, one activity
    and the lesson lineage of the plan when it has one."""

    snapshot: dict[str, Any] = {
        "schema_version": TEACHER_PIN_SCHEMA,
        "occurrence_id": occurrence_id,
        "plan_revision_id": plan_revision_id,
        "plan_revision_no": plan_revision_no,
        "plan_hash": plan_hash,
        "activity": dict(activity),
        "lesson": dict(lesson) if lesson is not None else None,
    }
    if len(canonical_json(snapshot).encode("utf-8")) > PIN_MAX_BYTES:
        raise ValueError("the Teacher pin snapshot exceeds its bound")
    return snapshot


# The direction a Teacher run hands to the story worker (T-4b3a D7b): smaller than the stored
# context on purpose, a pure function of that snapshot, no name, no media, no seed.
LESSON_DIRECTION_OBJECTIVES_MAX: Final = 6
LESSON_DIRECTION_OBJECTIVE_CHARS: Final = 200
LESSON_DIRECTION_TEXT_CHARS: Final = 600
LESSON_DIRECTION_TITLE_CHARS: Final = 120
LESSON_DIRECTION_KEYS: Final = ("teacher_direction", "objectives", "activity_title")


def teacher_lesson_direction(context: Mapping[str, Any]) -> dict[str, Any] | None:
    """The bounded ``lesson_direction`` of a Teacher story input, or ``None`` when the snapshot
    holds nothing to say. Only the three fields of ``build_context_snapshot`` that carry the
    Teacher's own lesson text are read; the shape is closed (``LESSON_DIRECTION_KEYS``)."""

    direction = str(context.get("teacher_direction") or "").strip()
    raw_objectives = context.get("objectives")
    objectives = [
        _clip(str(item).strip(), LESSON_DIRECTION_OBJECTIVE_CHARS)
        for item in (raw_objectives if isinstance(raw_objectives, list) else [])[
            :LESSON_DIRECTION_OBJECTIVES_MAX
        ]
        if str(item).strip()
    ]
    title = str(context.get("activity_title") or "").strip()
    if not direction and not objectives and not title:
        return None
    return {
        "teacher_direction": _clip(direction, LESSON_DIRECTION_TEXT_CHARS),
        "objectives": objectives,
        "activity_title": _clip(title, LESSON_DIRECTION_TITLE_CHARS) if title else None,
    }


def create_fingerprint(body: Mapping[str, Any]) -> str:
    """The request fingerprint of the create receipt: the canonical Teacher body."""

    return sha256_json({"command": "teacher-create-run", "body": dict(body)})


def has_lock_free_state(run_state: str) -> bool:
    return run_state in LOCK_FREE_STATES


__all__ = [
    "CONTEXT_ACTIVITY_TITLE_CHARS",
    "CONTEXT_DIRECTION_CHARS",
    "CONTEXT_MAX_BYTES",
    "CONTEXT_OBJECTIVES_MAX",
    "CONTEXT_OBJECTIVE_CHARS",
    "DISPATCH_KEYS",
    "LESSON_DIRECTION_KEYS",
    "LESSON_DIRECTION_OBJECTIVES_MAX",
    "LESSON_DIRECTION_OBJECTIVE_CHARS",
    "LESSON_DIRECTION_TEXT_CHARS",
    "LESSON_DIRECTION_TITLE_CHARS",
    "LOCK_FREE_STATES",
    "MULTI_CHILD_KEYS",
    "PIN_MAX_BYTES",
    "TEACHER_BODY_KEYS",
    "TEACHER_CONTEXT_SCHEMA",
    "TEACHER_PIN_SCHEMA",
    "build_context_snapshot",
    "build_pin_snapshot",
    "canonical_json",
    "create_fingerprint",
    "has_lock_free_state",
    "is_teacher_shaped",
    "multi_child_requested",
    "parse_json_object",
    "sha256_json",
    "teacher_lesson_direction",
]
