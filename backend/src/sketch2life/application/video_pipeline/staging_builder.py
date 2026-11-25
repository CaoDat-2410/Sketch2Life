"""Deterministic ``sketch2life.story-staging.v1`` from the video plan (FEAT-093 plan Rev 2, section 9).

The compositor needs, per scene, where the main subject stands, which way it faces and what state every secondary
subject is in. This builder derives all three from the timeline's interactions, so the same typed effect (consume,
transfer, contact, move, transform) works for any story, not only for one example. Pure code; no model.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from sketch2life.application.video_pipeline.story_timeline import Interaction
from sketch2life.application.video_pipeline.video_plan import VideoPlan

STAGING_SCHEMA: Final = "sketch2life.story-staging.v1"
COLUMNS: Final = ("left", "center", "right")
ROWS: Final = ("top", "middle", "bottom")
GRID: Final = 20


class StagingError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def cell_of(box: tuple[int, int, int, int]) -> tuple[int, int]:
    """(column, row) of the 3x3 cell holding the centre of a 20x20 grid box."""

    x0, y0, x1, y1 = box
    column = min(2, int(((x0 + x1) / 2) / (GRID / 3)))
    row = min(2, int(((y0 + y1) / 2) / (GRID / 3)))
    return column, row


def _name(cell: tuple[int, int]) -> str:
    return f"{COLUMNS[cell[0]]}-{ROWS[cell[1]]}"


def _facing(from_cell: tuple[int, int], to_cell: tuple[int, int]) -> str:
    if to_cell[0] > from_cell[0]:
        return "right"
    if to_cell[0] < from_cell[0]:
        return "left"
    return "front"


def _beside(target: tuple[int, int], approach_from_column: int, taken: set[tuple[int, int]]) -> tuple[int, int]:
    """A free cell next to the target on the side the main subject comes from."""

    side = -1 if approach_from_column <= target[0] else 1
    candidates = [
        (target[0] + side, target[1]),
        (target[0] - side, target[1]),
        (target[0] + side, 1),
        (1, target[1]),
        (1, 1),
        (0, target[1]),
        (2, target[1]),
    ]
    for column, row in candidates:
        if 0 <= column <= 2 and 0 <= row <= 2 and (column, row) not in taken and (column, row) != target:
            return column, row
    raise StagingError("STAGING_NO_FREE_CELL")


def build_staging(
    plan: VideoPlan,
    *,
    subject_boxes: Mapping[str, tuple[int, int, int, int]],
    secondary_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Staging for every scene; ``subject_boxes`` are the 20x20 grid boxes of the drawing's subjects."""

    main_id = plan.main_entity_id
    if main_id not in subject_boxes or any(item not in subject_boxes for item in secondary_ids):
        raise StagingError("STAGING_SUBJECT_BOX_MISSING")
    main_cell = cell_of(subject_boxes[main_id])
    secondary_cell = {entity: cell_of(subject_boxes[entity]) for entity in secondary_ids}
    state = {entity: "unchanged" for entity in secondary_ids}
    scenes: list[dict[str, Any]] = []
    for scene in plan.scenes:
        focus: Interaction | None = next(
            (item for item in scene.interactions if item.actor == main_id and item.target in secondary_cell), None
        )
        taken = {cell for entity, cell in secondary_cell.items() if state[entity] != "gone"}
        previous = main_cell
        if focus is not None and focus.kind in ("consume", "contact", "transform", "transfer"):
            target_cell = secondary_cell[focus.target]
            main_cell = _beside(target_cell, previous[0], taken - {target_cell})
        elif focus is not None and focus.kind == "move":
            main_cell = (2 - previous[0], previous[1]) if (2 - previous[0], previous[1]) not in taken else previous
        facing_to = secondary_cell[focus.target] if focus is not None else (1, main_cell[1])
        facing = _facing(main_cell, facing_to) if main_cell != facing_to else "front"
        entries: list[dict[str, Any]] = []
        for entity in secondary_ids:
            current = state[entity]
            for item in scene.interactions:
                if item.target != entity:
                    continue
                if item.kind == "consume":
                    current = "gone" if item.to_state <= 0.0 else "partly_gone"
                elif item.kind == "transfer" and current != "gone":
                    current = "moved"
                    secondary_cell[entity] = _beside(main_cell, main_cell[0], {main_cell})
            state[entity] = current
            entry: dict[str, Any] = {"entity_id": entity, "state": current}
            if current == "moved":
                entry["position"] = _name(secondary_cell[entity])
            entries.append(entry)
        scenes.append(
            {
                "scene_index": scene.index,
                "main_end": {"position": _name(main_cell), "facing": facing, "scale": "same"},
                "secondary_end": entries,
            }
        )
    return {"schema_version": STAGING_SCHEMA, "scenes": scenes}


__all__ = ["STAGING_SCHEMA", "StagingError", "build_staging", "cell_of"]
