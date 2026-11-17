"""Continuous source-mask coloring, visible pen-up and preview fidelity."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image, ImageDraw
from tools.story_world_v2_fixture import make_prototype

from sketch2life.application.services.story_draw_schedule_v2 import build_draw_schedule
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.object_stroke_engine_v2 import (
    _pencil_color_paths,
    extract_object_strokes,
)
from sketch2life.infrastructure.media.scene_state_composer import source_canvas_layers
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _draw_path, _frame


def test_pencil_turns_and_coverage_stay_inside_holed_mask() -> None:
    active = np.zeros((80, 90), dtype=bool)
    active[2:76, 3:84] = True
    active[17:48, 25:58] = False
    active[79, 89] = True

    def factory(phase, index, points, width):
        return ObjectStrokeV2(stroke_id=f"color-{index}", phase=phase, points=points,
                              brush_width=width, color_rgb=(25, 55, 75))

    paths = _pencil_color_paths(active, factory)
    assert any(len(p.points) > 4 for p in paths)
    reveal = Image.new("L", (90, 80), 0)
    for path in paths:
        _draw_path(ImageDraw.Draw(reveal), path, 1.)
        for (x0, y0), (x1, y1) in zip(path.points, path.points[1:], strict=False):
            steps = max(1, abs(x1 - x0), abs(y1 - y0))
            assert all(active[round(y0 + (y1 - y0) * i / steps),
                              round(x0 + (x1 - x0) * i / steps)]
                       for i in range(steps + 1))
    assert np.all((np.asarray(reveal) > 0)[active])


def test_pen_up_is_visible_display_overlay_and_disappears_at_completion() -> None:
    result = make_prototype()
    scene = result.scene_plan.scenes[0]
    objects = tuple(extract_object_strokes(result.registry, o.object_id, strategy="pencil")
                    for o in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=20, fps=24,
                                   object_first=True, pencil_timing=True)
    gap = next(s for s in schedule.strokes if s.pen_up_seconds >= 2 / 24)
    background = Image.new("RGBA", (result.registry.world.source_width,
                                     result.registry.world.source_height), "white")
    t = gap.start_seconds - gap.pen_up_seconds / 2
    ink = _frame(result.registry, scene, objects, schedule, t, background)
    display = _frame(result.registry, scene, objects, schedule, t, background, show_pen=True)
    assert 0 < np.any(np.asarray(ink) != np.asarray(display), axis=2).sum() < 100
    final_ink = _frame(result.registry, scene, objects, schedule, 20., background)
    final_display = _frame(
        result.registry, scene, objects, schedule, 20., background, show_pen=True,
    )
    assert final_ink.tobytes() == final_display.tobytes()


def test_unscheduled_preview_is_rejected_and_final_target_still_matches() -> None:
    result = make_prototype()
    scene = result.scene_plan.scenes[0]
    objects = tuple(extract_object_strokes(result.registry, o.object_id, strategy="pencil")
                    for o in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=20, fps=24,
                                   object_first=True, pencil_timing=True)
    source = np.asarray(Image.open(io.BytesIO(result.registry.source_image_bytes)).convert("RGB"))
    _, background = source_canvas_layers(result.registry)
    preview_ids = (objects[-1].object_id,)
    with pytest.raises(StoryWorldError, match="UNSCHEDULED_STROKE"):
        _frame(result.registry, scene, objects, schedule, .3, background,
               background_preview_ids=preview_ids)
    early = np.asarray(_frame(result.registry, scene, objects, schedule, .3, background))
    assert np.all(np.all(early == source, axis=2) | np.all(early == 255, axis=2))
    a = _frame(result.registry, scene, objects, schedule, 20., background)
    b = _frame(result.registry, scene, objects, schedule, 20., background,
               show_pen=True)
    assert a.tobytes() == b.tobytes()
