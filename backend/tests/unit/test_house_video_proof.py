from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from tools.render_house_video_proof import SourceProgress, presentation, render

from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _partial_points
from sketch2life.infrastructure.media.whiteboard_slice_feasibility import (
    PacingAssumptions,
    timed_pen_paths,
)


@pytest.fixture
def data():
    rgb = np.zeros((10, 12, 4), dtype=np.uint8)
    rgb[:, :, :3] = (210, 130, 85)
    rgb[0, :, :3] = (70, 70, 70)
    rgb[:, :, 3] = 255
    source = Image.fromarray(rgb)
    paths = tuple(ObjectStrokeV2(stroke_id=name, phase=phase, points=points, brush_width=width,
                                color_rgb=(70, 70, 70))
                  for name, phase, points, width in (
                      ("outline", "OUTLINE", ((0, 0), (11, 0)), 2),
                      ("detail", "DETAIL", ((0, 0), (5, 0)), 1),
                      ("color-a", "COLOR", ((0, 2), (11, 2)), 10),
                      ("color-b", "COLOR", ((11, 7), (0, 7)), 10),
                  ))
    rows, metrics = timed_pen_paths(paths, PacingAssumptions())
    ink = np.zeros((10, 12), dtype=bool)
    ink[0] = True
    allowed = {"OUTLINE": ink, "DETAIL": ink, "COLOR": np.ones((10, 12), dtype=bool)}
    return source, paths, rows, allowed, metrics


def test_house_permission_required_before_reading_or_writing(tmp_path: Path):
    with pytest.raises(ValueError, match="HOUSE_PROOF_APPROVAL_REQUIRED"):
        render(tmp_path / "missing", tmp_path / "world", tmp_path / "paths",
               tmp_path / "out", confirmed=False)
    assert not (tmp_path / "out").exists()


def test_outline_never_reveals_color_and_preserves_source_rgb(data):
    source, paths, rows, allowed, _ = data
    rgba, trace, visible, _ = SourceProgress(source, paths, rows, allowed).at(.1)
    assert trace["phase"] == "OUTLINE"
    assert not visible[1:].any()
    assert np.array_equal(np.asarray(rgba)[visible, :3], np.asarray(source)[visible, :3])


def test_pen_up_adds_no_new_pixels_relative_to_path_completion(data):
    source, paths, rows, allowed, _ = data
    engine = SourceProgress(source, paths, rows, allowed)
    _, _, first, _ = engine.at(rows[0]["pen_down_end"])
    _, trace, second, _ = engine.at(rows[1]["pen_up_start"] + .04)
    assert trace["state"] == "UP"
    assert np.array_equal(first, second)


def test_final_pixels_match_source_without_snap_and_hold_is_stable(data):
    source, paths, rows, allowed, metrics = data
    engine = SourceProgress(source, paths, rows, allowed)
    end, _, _, _ = engine.at(metrics["estimated_seconds"])
    hold, _, _, _ = engine.at(metrics["estimated_seconds"] + 1.)
    assert end.tobytes() == hold.tobytes() == source.tobytes()


def test_timeline_rewind_is_rejected(data):
    source, paths, rows, allowed, _ = data
    engine = SourceProgress(source, paths, rows, allowed)
    engine.at(.2)
    with pytest.raises(ValueError, match="MONOTONIC_TIMELINE_REQUIRED"):
        engine.at(.1)


def test_tip_is_actual_arc_length_endpoint(data):
    source, paths, rows, allowed, _ = data
    _, trace, _, _ = SourceProgress(source, paths, rows, allowed).at(.1)
    assert trace["tip"] == list(_partial_points(paths[0], trace["fraction"])[-1])


def test_debug_annotations_do_not_modify_native_source_or_clean_frame(data):
    source, paths, rows, allowed, _ = data
    before = source.tobytes()
    rgba, trace, _, _ = SourceProgress(source, paths, rows, allowed).at(.1)
    clean = presentation(rgba, trace, paths, debug=False)
    debug = presentation(rgba, trace, paths, debug=True)
    assert clean.tobytes() != debug.tobytes()
    assert source.tobytes() == before


def test_empty_ink_mask_exposes_path_quality_failure_without_faking_strokes(data):
    source, paths, rows, allowed, _ = data
    allowed["OUTLINE"] = np.zeros((10, 12), dtype=bool)
    rgba, trace, visible, _ = SourceProgress(source, paths, rows, allowed).at(.1)
    assert trace["state"] == "DOWN"
    assert not visible.any()
    assert not np.asarray(rgba)[:, :, 3].any()
