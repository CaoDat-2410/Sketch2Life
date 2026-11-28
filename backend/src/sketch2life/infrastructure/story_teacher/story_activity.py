"""Read the activity pinned by one Teacher StoryRun for story and video inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.contracts.schemas.modal_ai import PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH
from sketch2life.domain.story_teacher import TEACHER_PIN_SCHEMA, teacher_lesson_direction
from sketch2life.infrastructure.lesson_occurrences.tables import (
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
)

_ACTIVITY_KINDS = frozenset({"CATALOG", "LESSON", "CUSTOM"})
_STORY_ACTIVITY_LIMITS = {
    "title": 160,
    "objective": 400,
    "materials_text": 300,
    "preparation_text": PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
    "instructions_text": 700,
    "observation_notes": PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
    "safety_notes": PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
    "activity_kind": 16,
}


def pinned_story_activity(
    session: Session,
    input_row: Mapping[Any, Any],
    *,
    occurrence_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, str] | None:
    """Return the bounded eight-field story activity, or ``None`` when its pin is stale.

    Callers first authorize the run in their request or job scope. Request-side repositories use
    ``SqlTeacherRunAccess``; story-generation jobs additionally bind the run to their organization.
    The worker-side video reader is system-scoped to a generation/run pair. This query then narrows
    the lesson read to the exact immutable plan revision and activity recorded on that run input.
    """

    pin = input_row.get("lesson_pin_snapshot")
    if not isinstance(pin, Mapping) or pin.get("schema_version") != TEACHER_PIN_SCHEMA:
        return None
    plan_revision_id = pin.get("plan_revision_id")
    pinned_occurrence_id = pin.get("occurrence_id")
    pinned_activity = pin.get("activity")
    if (
        not isinstance(plan_revision_id, str)
        or not plan_revision_id
        or not isinstance(pinned_occurrence_id, str)
        or not pinned_occurrence_id
        or (occurrence_id is not None and pinned_occurrence_id != occurrence_id)
    ):
        return None
    if not isinstance(pinned_activity, Mapping):
        return None
    plan_activity_id = pinned_activity.get("plan_activity_id")
    kind = pinned_activity.get("kind")
    if (
        not isinstance(plan_activity_id, str)
        or not plan_activity_id
        or not isinstance(kind, str)
        or kind not in _ACTIVITY_KINDS
    ):
        return None

    statement = (
        select(PLAN_ACTIVITIES)
        .select_from(
            PLAN_ACTIVITIES.join(
                PLAN_REVISIONS,
                PLAN_REVISIONS.c.plan_revision_id == PLAN_ACTIVITIES.c.plan_revision_id,
            ).join(
                OCCURRENCES,
                OCCURRENCES.c.occurrence_id == PLAN_REVISIONS.c.occurrence_id,
            )
        )
        .where(
            PLAN_ACTIVITIES.c.plan_activity_id == plan_activity_id,
            PLAN_ACTIVITIES.c.plan_revision_id == plan_revision_id,
            PLAN_REVISIONS.c.occurrence_id == pinned_occurrence_id,
        )
    )
    if organization_id is not None:
        statement = statement.where(OCCURRENCES.c.organization_ref == organization_id)
    row = (
        session.execute(statement)
        .mappings()
        .one_or_none()
    )
    if (
        row is None
        or row["plan_activity_id"] != plan_activity_id
        or row["plan_revision_id"] != plan_revision_id
        or row["activity_kind"] != kind
    ):
        return None

    snapshot = row["activity_snapshot"]
    if snapshot is None and kind == "CUSTOM":
        snapshot = {}
    if not isinstance(snapshot, Mapping):
        return None
    if kind != "CUSTOM":
        snapshot_hash = pinned_activity.get("snapshot_hash")
        if (
            not isinstance(snapshot_hash, str)
            or not snapshot_hash
            or row["activity_snapshot_hash"] != snapshot_hash
        ):
            return None

    snapshot_title = _text(snapshot.get("title"))
    title = _text(row["custom_title"]) or snapshot_title
    if not title:
        return None
    instructions = (
        _text(snapshot.get("instructions_text"))
        or _text(row["custom_description"])
        or title
    )
    context = input_row.get("context_snapshot")
    objectives = context.get("objectives") if isinstance(context, Mapping) else None
    objective = _text(snapshot.get("objective")) or _joined_text(objectives) or title
    activity_kind = snapshot.get("activity_kind")
    raw: dict[str, str] = {
        "title": title,
        "objective": objective,
        "materials_text": _text(snapshot.get("materials_text")),
        "preparation_text": _text(snapshot.get("preparation_text")),
        "instructions_text": instructions,
        "observation_notes": _text(snapshot.get("observation_notes")),
        "safety_notes": _text(snapshot.get("safety_notes")),
        "activity_kind": (
            activity_kind
            if isinstance(activity_kind, str)
            and activity_kind in {"outdoor", "indoor", "mixed"}
            else "indoor"
        ),
    }
    return {
        name: str(raw.get(name, "")).strip()[:limit]
        for name, limit in _STORY_ACTIVITY_LIMITS.items()
    }


def teacher_lesson_direction_text(context: Mapping[str, Any]) -> str | None:
    """Render the bounded Teacher direction object as one plain worker string."""

    direction = teacher_lesson_direction(context)
    if direction is None:
        return None
    lines: list[str] = []
    teacher_direction = direction["teacher_direction"]
    if teacher_direction:
        lines.append(f"Định hướng: {teacher_direction}")
    objectives = direction["objectives"]
    if objectives:
        lines.append(f"Mục tiêu: {'; '.join(objectives)}")
    activity_title = direction["activity_title"]
    if activity_title:
        lines.append(f"Hoạt động: {activity_title}")
    value = "\n".join(lines).strip()[:2000]
    return value or None


def _text(value: object) -> str:
    return str(value or "").strip()


def _joined_text(value: object) -> str:
    if not isinstance(value, list):
        return ""
    return "; ".join(text for item in value if (text := _text(item)))


__all__ = ["pinned_story_activity", "teacher_lesson_direction_text"]
