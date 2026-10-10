"""Opt-in coherent detail, localized coloring and object-first timeline checks."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image, ImageDraw
from tools.story_world_v2_fixture import make_prototype as family_prototype
from tools.story_world_v2_ocean_fixture import make_prototype as ocean_prototype

from sketch2life.application.services.story_draw_schedule_v2 import build_draw_schedule
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.object_stroke_engine_v2 import (
    _coherent_details,
    _join_adjacent_paths,
    _localized_color_paths,
    extract_object_strokes,
)
from sketch2life.infrastructure.media.scene_state_composer import (
    SceneStateComposer,
    source_canvas_layers,
)
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _draw_path, _frame


def test_coherence_defers_colored_islands_but_keeps_dark_eye_dot() -> None:
    rgb = np.full((20, 20, 3), 210, dtype=np.uint8)
    rgb[4, 4] = (20, 20, 20)
    rgb[7, 7] = (130, 180, 160)
    selected = np.zeros((20, 20), dtype=bool)
    selected[4, 4] = selected[7, 7] = True
    selected[11, 3:10] = True
    kept = _coherent_details(Image.fromarray(rgb), selected)
    assert kept[4, 4] and not kept[7, 7]
    assert kept[11, 3:10].all()
    assert np.all(~kept | selected)


def test_join_preserves_seam_pixels_and_never_bridges_empty_space() -> None:
    paths = [((30, 5), (31, 5)), ((32, 5), (33, 5)), ((40, 5), (41, 5))]
    joined = _join_adjacent_paths(paths)
    assert len(joined) == 2
    assert {p for path in joined for p in path} == {p for path in paths for p in path}
    assert all(max(abs(x - a), abs(y - b)) <= 1 for path in joined
               for (x, y), (a, b) in zip(path, path[1:], strict=False))


def test_local_color_passes_cover_mask_tips_without_travel_across_holes() -> None:
    active = np.zeros((70, 70), dtype=bool)
    active[3:67, 2:65] = True
    active[17:49, 18:45] = False
    active[69, 69] = True

    def factory(phase, index, points, width):
        return ObjectStrokeV2(stroke_id=f"color-{index}", phase=phase, points=points,
                              brush_width=width, color_rgb=(20, 30, 40))

    paths = _localized_color_paths(active, factory)
    reveal = Image.new("L", (70, 70), 0)
    for path in paths:
        _draw_path(ImageDraw.Draw(reveal), path, 1.)
        for (a, y), (b, py) in zip(path.points, path.points[1:], strict=False):
            assert y == py
            assert active[y, min(a, b):max(a, b) + 1].all()
    assert np.all((np.asarray(reveal) > 0)[active])


@pytest.mark.parametrize("kind", ["family", "ocean-png", "ocean-jpeg"])
@pytest.mark.parametrize("strategy", ["visual", "pencil"])
def test_visual_strategy_preserves_assets_final_pixels_and_object_sequence(kind, strategy) -> None:
    result = family_prototype() if kind == "family" else ocean_prototype(
        image_format="JPEG" if kind == "ocean-jpeg" else "PNG",
    )
    registry = result.registry
    before = dict(registry.asset_png_by_id)
    objects = tuple(extract_object_strokes(registry, obj.object_id, strategy=strategy)
                    for obj in registry.world.source_objects)
    scene = result.scene_plan.scenes[0]
    schedule = build_draw_schedule(scene, objects, duration_seconds=6, object_first=True)
    runs = list(dict.fromkeys(item.object_id for item in schedule.strokes))
    assert tuple(runs) == schedule.object_order
    for obj in objects:
        phases = [s.phase for s in schedule.strokes if s.object_id == obj.object_id]
        assert phases == sorted(phases, key={"OUTLINE": 0, "DETAIL": 1, "COLOR": 2}.get)
        source = Image.open(io.BytesIO(registry.asset_png_by_id[obj.object_id])).convert("RGBA")
        active = np.asarray(source.getchannel("A")) > 0
        assert all(active[y, x] for group in (obj.outline_paths, obj.detail_paths, obj.color_paths)
                   for path in group for x, y in path.points)
    _, background = source_canvas_layers(registry)
    final = _frame(registry, scene, objects, schedule, 6., background)
    assert final.tobytes() == SceneStateComposer().render_scene(registry, scene).tobytes()
    assert registry.asset_png_by_id == before


def test_white_cleared_background_does_not_delay_first_source_ink() -> None:
    result = family_prototype()
    scene = result.scene_plan.scenes[0]
    objects = tuple(extract_object_strokes(result.registry, obj.object_id, strategy="visual")
                    for obj in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=6, object_first=True)
    background = Image.new("RGBA", (result.registry.world.source_width,
                                     result.registry.world.source_height), "white")
    early = _frame(result.registry, scene, objects, schedule, .2, background)
    assert np.any(np.asarray(early) < 255)
