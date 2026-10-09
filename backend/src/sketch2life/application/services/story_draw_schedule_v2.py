"""Deterministic object/phase schedule; no TTS or inferred story events."""

from __future__ import annotations

import math

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.contracts.schemas.story_strokes_v2 import (
    SceneDrawScheduleV2,
    ScheduledStrokeV2,
    SourceObjectStrokesV2,
)
from sketch2life.contracts.schemas.story_world_v2 import ScenePlanV2


def build_draw_schedule(
    scene: ScenePlanV2, objects: tuple[SourceObjectStrokesV2, ...],
    *, duration_seconds: float | None = None, fps: int = 12,
) -> SceneDrawScheduleV2:
    """Order verified source objects; fail if too many pen lifts for the timeline."""
    if scene.action not in {"STATIC", "TRANSLATE", "SCALE", "ROTATE"} or scene.new_object_ids:
        raise StoryWorldError("UNSUPPORTED_ACTION", "drawing pilot supports source objects only")
    seconds = duration_seconds if duration_seconds is not None else scene.duration_seconds
    if not 3 <= seconds <= 20 or fps < 8:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "invalid clip duration or fps")
    by_id = {item.object_id: item for item in objects}
    order = tuple(dict.fromkeys((*scene.draw_order, *scene.source_object_ids)))
    order = tuple(object_id for object_id in order if object_id in scene.source_object_ids)
    if set(order) != set(scene.source_object_ids) or set(by_id) != set(scene.source_object_ids):
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "stroke data must cover scene sources")
    strokes = [
        (object_id, path)
        for phase in ("outline_paths", "detail_paths", "color_paths")
        for object_id in order
        for path in getattr(by_id[object_id], phase)
    ]
    # One frame can advance multiple short strokes, but not an unbounded number.
    if not strokes or len(strokes) > fps * seconds * 18:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "too many strokes for clip duration")
    hold = max(.2, seconds * .06)
    draw_seconds = seconds - hold
    pause = min(.015, draw_seconds * .1 / len(strokes))
    lengths = [
        max(1., sum(math.dist(a, b) for a, b in zip(path.points, path.points[1:], strict=False)))
        for _, path in strokes
    ]
    # Arc length approximates hand travel; detail/color weights keep tiny features visible.
    weights = [length ** .65 for length in lengths]
    total = sum(weights)
    cursor = 0.
    scheduled = []
    for index, ((object_id, path), weight) in enumerate(zip(strokes, weights, strict=True)):
        start = cursor + (pause if index else 0.)
        duration = (draw_seconds - pause * (len(strokes) - 1)) * weight / total
        end = start + duration
        scheduled.append(ScheduledStrokeV2(
            object_id=object_id, stroke_id=path.stroke_id, phase=path.phase,
            start_seconds=start, end_seconds=end,
            pen_up_seconds=pause if index else 0., beat_ref=scene.segment_ids[0],
        ))
        cursor = end
    return SceneDrawScheduleV2(
        scene_id=scene.scene_id, object_order=order, strokes=tuple(scheduled),
        duration_seconds=seconds, hold_seconds=hold,
    )
