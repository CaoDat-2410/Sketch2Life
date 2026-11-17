from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from tools.refine_butterfly_candidate import (
    build_candidate,
    mask_for_path,
    prepare,
    progress,
    schedule_for,
)


@pytest.fixture(scope="module")
def candidate():
    source = Image.new("RGB", (24, 24), (230, 125, 90))
    for x in range(12, 24):
        for y in range(24):
            source.putpixel((x, y), (70, 170, 190))
    return build_candidate(source)


def test_outline_is_continuous_and_closed_for_each_wing_and_body(candidate):
    outlines = [p for p in candidate.paths if p.phase == "OUTLINE"]
    assert len(outlines) == 7
    assert all(p.points[0] == p.points[-1] for p in outlines[:5])
    assert all(p.points[0] != p.points[-1] for p in outlines[5:])
    assert all(len(p.points) > 10 for p in outlines)


def test_wings_are_not_mirrored_duplicates(candidate):
    outlines = [p for p in candidate.paths if p.phase == "OUTLINE"]
    left = np.array(outlines[0].points)
    right = np.array(outlines[1].points)
    assert left.shape != right.shape or not np.array_equal(left[:, 1], right[:, 1])


def test_color_has_curved_shape_aware_paths_not_horizontal_scan(candidate):
    color = [p for p in candidate.paths if p.phase == "COLOR"]
    assert len(color) == 5
    for path in color:
        points = np.array(path.points)
        delta = np.diff(points, axis=0)
        assert np.count_nonzero(delta[:, 1]) > len(delta) * .20
        assert (delta[:, 0] > 0).any() and (delta[:, 0] < 0).any()
        assert len(set(path.points)) > 100


def test_all_color_pixels_are_covered_without_final_snap(candidate):
    rows, metrics = schedule_for(candidate, .30)
    frame, _trace, masks = progress(candidate, rows, metrics["estimated_seconds"] + 1e-8)
    active = np.asarray(candidate.fill)[:, :, 3] > 0
    assert np.all(masks["COLOR"][active] > 0)
    assert frame.tobytes() == candidate.asset.tobytes()


def test_zero_progress_is_empty(candidate):
    rows, _metrics = schedule_for(candidate, .30)
    image, trace, masks = progress(candidate, rows, 0)
    assert np.asarray(image)[:, :, 3].sum() == 0
    assert trace["tip"] is None
    assert all(mask.sum() == 0 for mask in masks.values())


def test_no_color_before_color_phase(candidate):
    rows, _metrics = schedule_for(candidate, .30)
    first_color = next(r for r in rows if r["phase"] == "COLOR")
    _image, _trace, masks = progress(candidate, rows, first_color["pen_down_start"] - .001)
    assert not masks["COLOR"].any()
    assert masks["OUTLINE"].any() and masks["DETAIL"].any()


def test_partial_color_does_not_show_whole_component(candidate):
    rows, _metrics = schedule_for(candidate, .30)
    first_color = next(r for r in rows if r["phase"] == "COLOR")
    image, trace, masks = progress(candidate, rows, first_color["pen_down_start"] + .01)
    active = np.asarray(candidate.fill)[:, :, 3] > 0
    count = np.count_nonzero(masks["COLOR"] & active)
    assert 0 < count < active.sum() * .15
    assert trace["state"] == "DOWN"
    assert image.tobytes() != candidate.asset.tobytes()


def test_pen_tip_is_on_actual_brush_path(candidate):
    rows, _metrics = schedule_for(candidate, .30)
    row = rows[0]
    elapsed = row["pen_down_start"] + row["pen_down_seconds"] * .5
    _image, trace, masks = progress(candidate, rows, elapsed)
    x, y = (round(v) for v in trace["tip"])
    assert trace["stroke_id"] == candidate.paths[0].stroke_id
    assert masks["OUTLINE"][y, x] > 0


def test_pen_up_does_not_draw(candidate):
    rows, _metrics = schedule_for(candidate, .30)
    row = rows[1]
    _image, trace, during = progress(candidate, rows,
                                    (row["pen_up_start"] + row["pen_down_start"]) / 2)
    _image, _trace, before = progress(candidate, rows, row["pen_up_start"] + 1e-8)
    assert trace["state"] == "UP"
    assert all(np.array_equal(before[k], during[k]) for k in before)


def test_color_coverage_never_crosses_pigment_mask(candidate):
    rows, metrics = schedule_for(candidate, .30)
    _image, _trace, masks = progress(candidate, rows, metrics["estimated_seconds"])
    allowed = np.asarray(candidate.fill)[:, :, 3] > 0
    assert not (masks["COLOR"] > 0)[~allowed].any()


def test_antialias_edges_are_not_binary(candidate):
    mask = np.asarray(mask_for_path(candidate.paths[0]))
    assert ((mask > 0) & (mask < 255)).any()


def test_pigment_and_ink_dont_change_during_progress(candidate):
    originals = [im.tobytes() for im in (candidate.fill, candidate.outline, candidate.asset)]
    rows, metrics = schedule_for(candidate, .30)
    for fraction in (.25, .5, .75, 1):
        progress(candidate, rows, metrics["estimated_seconds"] * fraction)
    after = [im.tobytes() for im in (candidate.fill, candidate.outline, candidate.asset)]
    assert originals == after


def test_smaller_presentation_timing_not_forced_to_target(candidate):
    _rows, normal = schedule_for(candidate, .30)
    _rows, small = schedule_for(candidate, .22)
    assert small["estimated_seconds"] < normal["estimated_seconds"]
    assert small["pen_up_seconds"] >= 20 * 2 / 24 - 1e-9


@pytest.mark.parametrize("scale", [0, 1.1, float("nan")])
def test_invalid_scale(candidate, scale):
    with pytest.raises(ValueError):
        schedule_for(candidate, scale)


def test_preparation_requires_permission(tmp_path):
    with pytest.raises(ValueError, match="APPROVAL_REQUIRED"):
        prepare(Path("missing"), Path("missing"), tmp_path / "new", confirmed=False)
