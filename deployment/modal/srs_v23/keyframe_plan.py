"""FEAT-087 M5: the ``keyframe_plan`` manifest block and the LTX conditioning it implies.

``render_mode`` is ``keyframe`` (every scene starts at keyframe K(i-1) and is guided toward
K(i)) or ``fallback`` (every scene starts from the original drawing K0 with no end frame). The
mode and the reason for a fallback are recorded in the output manifest.
"""

from __future__ import annotations

import re
from typing import Any

import story_staging_worker as staging_contract

KEYFRAME_PLAN_SCHEMA = "sketch2life.keyframe-plan.v1"
BOX_GRID_MAX = 20
MIN_BOX_GRID_CELLS = 4
MAX_SECONDARIES = 3
END_FRAME_STRENGTH = 0.85
_REASON = re.compile(r"\A[A-Z][A-Z0-9_]{2,63}\Z")
_PLAN_KEYS = {
    "schema_version",
    "render_mode",
    "fallback_reason",
    "source_facing",
    "main",
    "secondaries",
    "staging",
}


class KeyframePlanError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _box_ok(box: Any) -> bool:
    if (
        not isinstance(box, list)
        or len(box) != 4
        or any(
            type(value) is not int or not 0 <= value <= BOX_GRID_MAX for value in box
        )
    ):
        return False
    x0, y0, x1, y1 = box
    return x1 - x0 >= MIN_BOX_GRID_CELLS and y1 - y0 >= MIN_BOX_GRID_CELLS


def _entity_ok(item: Any, allowed_ids: set[str]) -> bool:
    return (
        isinstance(item, dict)
        and set(item) == {"entity_id", "box"}
        and item["entity_id"] in allowed_ids
        and _box_ok(item["box"])
    )


def validate_keyframe_plan(plan: Any, *, scene_count: int) -> dict[str, Any]:
    if not isinstance(plan, dict) or set(plan) != _PLAN_KEYS:
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    if plan["schema_version"] != KEYFRAME_PLAN_SCHEMA or plan["render_mode"] not in {
        "keyframe",
        "fallback",
    }:
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    secondaries = plan["secondaries"]
    if not isinstance(secondaries, list) or len(secondaries) > MAX_SECONDARIES:
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    ids = [
        item.get("entity_id") if isinstance(item, dict) else None
        for item in secondaries
    ]
    if len(set(ids)) != len(ids) or any(
        not _entity_ok(item, {"sec-1", "sec-2", "sec-3"}) for item in secondaries
    ):
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    main = plan["main"]
    if main is not None and not _entity_ok(main, {"subject-main"}):
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    facing = plan["source_facing"]
    if facing is not None and facing not in {"left", "right", "front"}:
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")

    if plan["render_mode"] == "fallback":
        reason = plan["fallback_reason"]
        if not isinstance(reason, str) or _REASON.fullmatch(reason) is None:
            raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
        return plan

    if plan["fallback_reason"] is not None or main is None or facing is None:
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    try:
        staging_contract.validate_staging(
            plan["staging"], scene_count=scene_count, approved_ids=tuple(ids)
        )
    except staging_contract.StagingError:
        raise KeyframePlanError("KEYFRAME_STAGING_INVALID") from None
    return plan


def scene_conditioning(
    render_mode: str, *, scene_index: int, scene_count: int
) -> dict[str, Any]:
    """Which keyframes condition scene ``scene_index`` (1-based), and how strongly."""

    if not 1 <= scene_index <= scene_count:
        raise KeyframePlanError("KEYFRAME_PLAN_INVALID")
    if render_mode == "keyframe":
        return {
            "start_keyframe": scene_index - 1,
            "end_keyframe": scene_index,
            "start_strength": 1.0,
            "end_strength": END_FRAME_STRENGTH,
        }
    if render_mode == "fallback":
        return {
            "start_keyframe": 0,
            "end_keyframe": None,
            "start_strength": 1.0,
            "end_strength": None,
        }
    raise KeyframePlanError("KEYFRAME_PLAN_INVALID")


def grid_box_to_canvas(
    box: list[int], *, source_size: tuple[int, int], transform: Any
) -> tuple[int, int, int, int]:
    """Grid (0..20) box over the source drawing -> pixel box on the LTX canvas."""

    width, height = source_size
    x0, y0, x1, y1 = box
    source_box = (
        round(x0 * width / BOX_GRID_MAX),
        round(y0 * height / BOX_GRID_MAX),
        round(x1 * width / BOX_GRID_MAX),
        round(y1 * height / BOX_GRID_MAX),
    )
    return transform.box_to_canvas(source_box)
