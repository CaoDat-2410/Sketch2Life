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


def validate_draw_schedule(
    objects: tuple[SourceObjectStrokesV2, ...], schedule: SceneDrawScheduleV2,
    *, require_interleave_reason: bool = False, interleave_reason: str | None = None,
) -> None:
    """Every real path exactly once, serial time, complete parent phases before children."""
    paths = {(obj.object_id, path.stroke_id): path for obj in objects
             for group in (obj.outline_paths, obj.detail_paths, obj.color_paths) for path in group}
    seen: set[tuple[str, str]] = set()
    phase_end: dict[tuple[str, str], float] = {}
    remaining: dict[tuple[str, str], int] = {}
    for (object_id, _), path in paths.items():
        phase_key = (object_id, path.phase)
        remaining[phase_key] = remaining.get(phase_key, 0) + 1
    rank = {"OUTLINE": 0, "DETAIL": 1, "COLOR": 2}
    previous_end = 0.
    object_phases: dict[str, int] = {}
    runs: list[str] = []
    for item in schedule.strokes:
        key = (item.object_id, item.stroke_id)
        scheduled_path = paths.get(key)
        if scheduled_path is None or key in seen or scheduled_path.phase != item.phase:
            raise StoryWorldError("DRAW_SCHEDULE_INVALID", "unknown/duplicate/incorrect-phase path")
        if item.start_seconds < previous_end - 1e-9 or (
            item.end_seconds > schedule.duration_seconds - schedule.hold_seconds + 1e-6
        ):
            raise StoryWorldError("DRAW_SCHEDULE_INVALID", "overlapping or out-of-budget strokes")
        if rank[item.phase] < object_phases.get(item.object_id, 0):
            raise StoryWorldError("DRAW_SCHEDULE_INVALID", "object phase order regressed")
        for parent in ("OUTLINE", "DETAIL"):
            if rank[parent] < rank[item.phase] and remaining.get((item.object_id, parent), 0):
                raise StoryWorldError("DRAW_SCHEDULE_INVALID", "parent phase incomplete")
            if phase_end.get((item.object_id, parent), 0.) > item.start_seconds + 1e-9:
                raise StoryWorldError("DRAW_SCHEDULE_INVALID", "parent phase still active")
        seen.add(key)
        remaining[(item.object_id, item.phase)] -= 1
        object_phases[item.object_id] = rank[item.phase]
        phase_end[(item.object_id, item.phase)] = item.end_seconds
        previous_end = item.end_seconds
        if not runs or runs[-1] != item.object_id:
            runs.append(item.object_id)
    if seen != set(paths):
        raise StoryWorldError("DRAW_SCHEDULE_INVALID", "missing paths")
    if require_interleave_reason and len(runs) != len(set(runs)) and not (
        interleave_reason and interleave_reason.strip()
    ):
        raise StoryWorldError("DRAW_SCHEDULE_INVALID", "interleave needs an explicit purpose")


def build_draw_schedule(
    scene: ScenePlanV2, objects: tuple[SourceObjectStrokesV2, ...],
    *, duration_seconds: float | None = None, fps: int = 12, object_first: bool = False,
    pencil_timing: bool = False,
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
    if object_first:
        strokes = [(object_id, path) for object_id in order
                   for phase in ("outline_paths", "detail_paths", "color_paths")
                   for path in getattr(by_id[object_id], phase)]
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
    weights = [length if pencil_timing else length ** .65 for length in lengths]
    if object_first:
        # Independent phase budgets avoid thousands of short details monopolizing ink time.
        group_totals: dict[tuple[str, str], float] = {}
        for (object_id, path), weight in zip(strokes, weights, strict=True):
            key = (object_id, path.phase)
            group_totals[key] = group_totals.get(key, 0.) + weight
        budgets = {"OUTLINE": .20, "DETAIL": .25, "COLOR": .55}
        weights = [weight / group_totals[(obj, path.phase)] * budgets[path.phase] *
                   by_id[obj].covered_source_pixels ** .4
                   for (obj, path), weight in zip(strokes, weights, strict=True)]
    total = sum(weights)
    pauses = [pause if i else 0. for i in range(len(strokes))]
    if pencil_timing:
        for i in range(1, len(strokes)):
            if (strokes[i][0], strokes[i][1].phase) != (
                strokes[i - 1][0], strokes[i - 1][1].phase,
            ):
                pauses[i] = 2 / fps  # explicit two-frame object/phase pen-up.
        if sum(pauses) >= draw_seconds * .25:
            raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "pencil pauses exceed timing budget")
    cursor = 0.
    pause_total = sum(pauses)
    scheduled = []
    for index, ((object_id, path), weight) in enumerate(zip(strokes, weights, strict=True)):
        start = cursor + pauses[index]
        duration = (draw_seconds - pause_total) * weight / total
        end = start + duration
        scheduled.append(ScheduledStrokeV2(
            object_id=object_id, stroke_id=path.stroke_id, phase=path.phase,
            start_seconds=start, end_seconds=end,
            pen_up_seconds=pauses[index], beat_ref=scene.segment_ids[0],
        ))
        cursor = end
    return SceneDrawScheduleV2(
        scene_id=scene.scene_id, object_order=order, strokes=tuple(scheduled),
        duration_seconds=seconds, hold_seconds=hold,
    )
