from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from tools.refine_butterfly_candidate import build_candidate, progress, schedule_for
from tools.render_butterfly_video_proof import ORIGIN, VIEW_SIZE, presentation, render


@pytest.fixture(scope="module")
def candidate():
    source = Image.new("RGB", (24, 24), (230, 125, 90))
    for x in range(12, 24):
        for y in range(24):
            source.putpixel((x, y), (70, 170, 190))
    return build_candidate(source)


def test_video_proof_requires_explicit_technical_permission(tmp_path: Path):
    with pytest.raises(ValueError, match="TECHNICAL_PROOF_APPROVAL_REQUIRED"):
        render(tmp_path / "missing", tmp_path / "missing.json", tmp_path / "out", confirmed=False)
    assert not (tmp_path / "out").exists()


def test_small_baseline_is_not_retimed(candidate):
    rows, metrics = schedule_for(candidate, .22)
    assert len(rows) == 21
    assert sum(row["pen_up_from"] is not None for row in rows) == 20
    assert metrics["estimated_seconds"] == pytest.approx(11.399049898587858)
    assert [row["phase"] for row in rows] == ["OUTLINE"] * 7 + ["DETAIL"] * 9 + ["COLOR"] * 5


def test_blank_and_completed_presentation_are_not_same(candidate):
    rows, metrics = schedule_for(candidate, .22)
    start, trace, _ = progress(candidate, rows, 0.)
    end, _, _ = progress(candidate, rows, metrics["estimated_seconds"] + 1.)
    blank = presentation(start, trace, candidate, debug=False)
    target = presentation(end, {"tip": None}, candidate, debug=False)
    assert np.asarray(blank).min() == 255
    assert np.asarray(target).min() < 100
    assert end.tobytes() == candidate.asset.tobytes()


def test_debug_tip_matches_transformed_geometry_and_clean_stays_unmarked(candidate):
    rows, _ = schedule_for(candidate, .22)
    rgba, trace, _ = progress(candidate, rows, .2)
    clean = presentation(rgba, trace, candidate, debug=False)
    debug = presentation(rgba, trace, candidate, debug=True)
    x = ORIGIN[0] + trace["tip"][0] * VIEW_SIZE[0] / rgba.width
    y = ORIGIN[1] + trace["tip"][1] * VIEW_SIZE[1] / rgba.height
    difference = np.any(np.asarray(clean) != np.asarray(debug), axis=2)
    assert difference[round(y) - 5:round(y) + 6, round(x) - 5:round(x) + 6].any()
    assert clean.size == (960, 540)


def test_final_hold_is_identical_without_replacing_frame(candidate):
    rows, stats = schedule_for(candidate, .22)
    first, _, _ = progress(candidate, rows, stats["estimated_seconds"] + .01)
    last, _, _ = progress(candidate, rows, stats["estimated_seconds"] + 1.35)
    assert first.tobytes() == last.tobytes() == candidate.asset.tobytes()
