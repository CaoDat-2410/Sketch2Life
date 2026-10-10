"""Fail-closed phase/clock checks and no out-of-schedule source reveal."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image
from tools.story_world_v2_fixture import make_prototype

from sketch2life.application.services.story_draw_schedule_v2 import (
    build_draw_schedule,
    validate_draw_schedule,
)
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.infrastructure.media.object_stroke_engine_v2 import extract_object_strokes
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import (
    _frame,
    _partial_points,
    _stroke_fraction,
)


@pytest.fixture
def sample():
    result = make_prototype()
    scene = result.scene_plan.scenes[0]
    objects = tuple(extract_object_strokes(result.registry, obj.object_id, strategy="pencil")
                    for obj in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=20, fps=24,
                                   object_first=True, pencil_timing=True)
    return result, scene, objects, schedule


def test_object_first_has_complete_parent_phases_and_single_object_runs(sample) -> None:
    _, _, objects, schedule = sample
    validate_draw_schedule(objects, schedule, require_interleave_reason=True)


def test_deliberate_interleave_needs_reason_but_cannot_skip_parent_phase(sample) -> None:
    _, scene, objects, _ = sample
    schedule = build_draw_schedule(scene, objects, duration_seconds=20)
    with pytest.raises(StoryWorldError, match="interleave needs"):
        validate_draw_schedule(objects, schedule, require_interleave_reason=True)
    validate_draw_schedule(objects, schedule, require_interleave_reason=True,
                           interleave_reason="Draw all object outlines before source coloring")


@pytest.mark.parametrize("fault", ["overlap", "color-first", "missing", "wrong-phase"])
def test_invalid_schedule_is_rejected(sample, fault) -> None:
    _, _, objects, schedule = sample
    strokes = list(schedule.strokes)
    if fault == "overlap":
        strokes[1] = strokes[1].model_copy(update={"start_seconds":0.})
    elif fault == "color-first":
        color = next(s for s in strokes if s.phase == "COLOR")
        strokes.remove(color)
        strokes.insert(0, color.model_copy(update={"start_seconds":0., "end_seconds":.001}))
    elif fault == "missing":
        strokes.pop()
    else:
        strokes[0] = strokes[0].model_copy(update={"phase":"COLOR"})
    with pytest.raises(StoryWorldError, match="DRAW_SCHEDULE_INVALID"):
        validate_draw_schedule(objects, schedule.model_copy(update={"strokes":tuple(strokes)}))


def test_shared_clock_keeps_tip_at_actual_partial_path_endpoint(sample) -> None:
    _, _, objects, schedule = sample
    item = next(s for s in schedule.strokes if s.phase == "COLOR")
    obj = next(o for o in objects if o.object_id == item.object_id)
    path = next(p for p in obj.color_paths if p.stroke_id == item.stroke_id)
    t = (item.start_seconds + item.end_seconds) / 2
    assert _stroke_fraction(item, t) == pytest.approx(.5)
    assert _partial_points(path, _stroke_fraction(item, t)) == _partial_points(path, .5)
    assert _stroke_fraction(item, item.start_seconds - 1) == 0
    assert _stroke_fraction(item, item.end_seconds + 1) == 1


def test_other_objects_cannot_reveal_before_their_schedule_turn(sample) -> None:
    result, scene, objects, schedule = sample
    background = Image.new("RGBA", (result.registry.world.source_width,
                                     result.registry.world.source_height), "white")
    early = np.asarray(_frame(result.registry, scene, objects, schedule, .2, background))
    first = schedule.strokes[0].object_id
    for obj in objects:
        if obj.object_id != first:
            body = result.registry.mask_png_by_id[obj.object_id]
            active = np.asarray(Image.open(io.BytesIO(body)).convert("L")) > 0
            assert np.all(early[active] == 255)
