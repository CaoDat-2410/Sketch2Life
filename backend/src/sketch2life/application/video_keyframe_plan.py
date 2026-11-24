"""Build the video worker's ``keyframe_plan`` from approved subject roles and story staging.

Anything unusable (no boxes, no staging, a bad box) degrades to a ``fallback`` plan that carries a
content-free reason; it never blocks a video.
"""

from __future__ import annotations

from typing import Any

from sketch2life.application.parent_subject_roles import approved_subjects
from sketch2life.application.ports.parent_video_candidates import (
    KeyframeInputs,
    KeyframeSecondary,
)
from sketch2life.application.story_staging import (
    normalize_staging,
    unpack_staging,
)

KEYFRAME_PLAN_SCHEMA = "sketch2life.keyframe-plan.v1"
MAIN_ENTITY = "subject-main"
_BOX_MAX = 20
_BOX_MIN_CELLS = 4


def _box(value: Any) -> tuple[int, int, int, int] | None:
    if (
        isinstance(value, (list, tuple))
        and len(value) == 4
        and all(type(item) is int for item in value)
    ):
        return (value[0], value[1], value[2], value[3])
    return None


def _box_ok(box: tuple[int, int, int, int]) -> bool:
    x0, y0, x1, y1 = box
    return (
        all(0 <= item <= _BOX_MAX for item in box)
        and x1 - x0 >= _BOX_MIN_CELLS
        and y1 - y0 >= _BOX_MIN_CELLS
    )


def keyframe_inputs_from(
    candidate: dict[str, Any] | None, story_content: dict[str, Any] | None
) -> KeyframeInputs | None:
    """None when the drawing has no boxes (a v1 understanding)."""

    if not isinstance(candidate, dict) or not isinstance(candidate.get("main_subject"), dict):
        return None
    main, secondaries = approved_subjects(candidate)
    main_box = _box(main.get("box"))
    if main_box is None:
        return None
    facing = main.get("facing") if main.get("facing") in {"left", "right", "front"} else "front"
    extras: list[KeyframeSecondary] = []
    for item in secondaries:
        box = _box(item.get("box"))
        if box is None:
            return None
        extras.append(KeyframeSecondary(str(item["entity_id"]), str(item.get("label", "")), box))
    staging, issue = (
        unpack_staging(story_content)
        if isinstance(story_content, dict)
        else (None, "STAGING_ABSENT")
    )
    return KeyframeInputs(main_box, str(facing), tuple(extras), staging, issue)


def _fallback(reason: str) -> dict[str, Any]:
    return {
        "schema_version": KEYFRAME_PLAN_SCHEMA,
        "render_mode": "fallback",
        "fallback_reason": reason,
        "source_facing": None,
        "main": None,
        "secondaries": [],
        "staging": None,
    }


def build_keyframe_plan(inputs: KeyframeInputs | None, *, scene_count: int) -> dict[str, Any]:
    if inputs is None:
        return _fallback("KEYFRAME_NO_BOXES")
    if not _box_ok(inputs.main_box) or any(not _box_ok(item.box) for item in inputs.secondaries):
        return _fallback("KEYFRAME_BOX_INVALID")
    if inputs.staging is None:
        return _fallback(f"KEYFRAME_{inputs.staging_issue or 'STAGING_ABSENT'}")
    staging, issue = normalize_staging(
        inputs.staging,
        scene_count=scene_count,
        approved_ids=tuple(item.entity_id for item in inputs.secondaries),
    )
    if staging is None:
        return _fallback("KEYFRAME_STAGING_INVALID")
    return {
        "schema_version": KEYFRAME_PLAN_SCHEMA,
        "render_mode": "keyframe",
        "fallback_reason": None,
        "source_facing": inputs.facing,
        "main": {"entity_id": MAIN_ENTITY, "box": list(inputs.main_box)},
        "secondaries": [
            {"entity_id": item.entity_id, "box": list(item.box)} for item in inputs.secondaries
        ],
        "staging": staging,
    }
