from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from tools.prepare_whiteboard_slice_step_a import (
    brush_paths,
    checked_bytes,
    make_butterfly,
    prepare,
)

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.whiteboard_slice_feasibility import (
    PacingAssumptions,
    path_coverage,
    separate_phase_masks,
    timed_pen_paths,
)


def path(phase="OUTLINE", points=((1, 1), (11, 1)), name="p1"):
    return ObjectStrokeV2(stroke_id=name, phase=phase, points=points, brush_width=1,
                          color_rgb=(10, 10, 10))


@pytest.mark.parametrize("change", [
    {"fps": 0}, {"fps": 61}, {"ink_pixels_per_second": float("nan")},
    {"color_pixels_per_second": 0}, {"pen_up_pixels_per_second": -1},
    {"minimum_down_frames": 1}, {"minimum_up_frames": 0},
])
def test_bad_pacing_blocks(change):
    with pytest.raises(StoryWorldError):
        timed_pen_paths((path(),), replace(PacingAssumptions(), **change))


def test_minimum_visible_frames_for_short_path():
    rows, metrics = timed_pen_paths((path(points=((1, 1), (1, 1))),), PacingAssumptions())
    assert rows[0]["pen_down_seconds"] == pytest.approx(4 / 24)
    assert metrics["estimated_seconds"] > 0


def test_pen_lifts_have_real_transitions():
    rows, metrics = timed_pen_paths((path(), path(points=((20, 1), (30, 1)), name="p2")),
                                   PacingAssumptions())
    assert rows[1]["pen_up_from"] == [11, 1]
    assert rows[1]["pen_up_to"] == [20, 1]
    assert rows[1]["pen_up_seconds"] >= 2 / 24
    assert metrics["down_travel_pixels"] == 20


def test_previous_phase_endpoint_has_pen_up():
    rows, _metrics = timed_pen_paths((path(),), PacingAssumptions(), previous_endpoint=(0, 0))
    assert rows[0]["pen_up_seconds"] >= 2 / 24


def test_color_speed_is_different_not_fixed_time_compression():
    p = path(points=((0, 0), (600, 0)))
    _rows, ink = timed_pen_paths((p,), PacingAssumptions())
    _rows, color = timed_pen_paths((p.model_copy(update={"phase": "COLOR"}),), PacingAssumptions())
    assert ink["estimated_seconds"] == pytest.approx(600 / 180)
    assert color["estimated_seconds"] == 2


@pytest.mark.parametrize("size", [(0, 10), (3000, 10), (1900, 1200)])
def test_canvas_budgets(size):
    with pytest.raises(StoryWorldError):
        path_coverage(size, ())


def test_path_count_budget():
    with pytest.raises(StoryWorldError):
        path_coverage((12, 12), (path(),) * 4097)


def test_outside_path_blocks():
    with pytest.raises(StoryWorldError):
        path_coverage((10, 10), (path(),))


def test_source_ink_does_not_expose_chromatic_fill():
    image = Image.new("RGBA", (16, 16), (240, 90, 40, 255))
    image.putpixel((5, 1), (40, 40, 40, 255))
    original = image.tobytes()
    groups = {"OUTLINE": (path(),), "DETAIL": (),
              "COLOR": brush_paths(np.ones((16, 16), dtype=bool))}
    masks, counts = separate_phase_masks(image, groups)
    assert masks["OUTLINE"].sum() == 1
    assert not masks["OUTLINE"][1, 6]
    assert counts["color_source_pixels_uncovered"] == 0
    assert counts["outline_boundary_pixels_deferred_to_color"] > 0
    assert image.tobytes() == original


def test_phase_masks_stay_inside_source_alpha():
    image = Image.new("RGBA", (16, 16), (30, 30, 30, 0))
    image.putpixel((5, 1), (30, 30, 30, 255))
    groups = {"OUTLINE": (path(),), "DETAIL": (), "COLOR": (path("COLOR"),)}
    masks, _counts = separate_phase_masks(image, groups)
    assert all(mask.sum() == 1 for phase, mask in masks.items() if phase != "DETAIL")
    assert masks["DETAIL"].sum() == 0


def test_irregular_mask_brush_coverage_is_complete():
    active = np.zeros((16, 16), dtype=bool)
    active[2:14, 2:10] = True
    active[7, 12] = True
    paths = brush_paths(active)
    assert not np.any(active & ~path_coverage((16, 16), paths))
    assert all(active[y, x] for p in paths for x, y in p.points)


def test_missing_coverage_is_reported_not_success():
    image = Image.new("RGBA", (16, 16), (30, 30, 30, 255))
    masks, counts = separate_phase_masks(image, {"OUTLINE": (), "DETAIL": (), "COLOR": ()})
    assert counts["ink_not_reached_by_outline_detail"] == 256
    assert counts["color_source_pixels_uncovered"] == 256
    assert not masks["COLOR"].any()


def test_local_hash_guard(tmp_path):
    image = tmp_path / "candidate.png"
    image.write_bytes(b"local-fixture")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        checked_bytes(str(image), "0" * 64)
    with pytest.raises(ValueError, match="LOCAL_PATH_REQUIRED"):
        checked_bytes("https://example.invalid/image", "0" * 64)


def test_no_permission_no_preparation(tmp_path):
    with pytest.raises(ValueError, match="PERMISSION_REQUIRED"):
        prepare(Path("missing"), Path("missing"), Path("missing"), tmp_path / "new",
                confirm_local_candidate_only=False)


def test_candidate_is_deterministic_new_art_with_all_phases():
    image = Image.new("RGB", (30, 30), (230, 125, 90))
    for x in range(10, 20):
        for y in range(30):
            image.putpixel((x, y), (70, 170, 190))
            image.putpixel((x + 10, y), (70, 190, 90))
    first, groups, recipe = make_butterfly(image)
    second, _groups, _recipe = make_butterfly(image)
    assert first.tobytes() == second.tobytes()
    assert all(groups[phase] for phase in ("OUTLINE", "DETAIL", "COLOR"))
    masks, counts = separate_phase_masks(first, groups)
    assert counts["color_source_pixels_uncovered"] == 0
    assert masks["OUTLINE"].any()
    assert recipe["texture"].endswith("NOT_SOURCE_PIXELS")
