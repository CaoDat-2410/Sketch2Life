"""FEAT-087 M5/G6: automatic quality metrics for rendered frames. CPU only."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import keyframe_metrics as km

PAPER = (244, 240, 226)


def _page(h=200, w=300):
    px = np.zeros((h, w, 3), dtype=np.uint8)
    px[:] = PAPER
    return px


def _stroke(px, y0, y1, x0, x1, color=(30, 30, 30)):
    px[y0:y1, x0:x1] = color
    mask = np.zeros(px.shape[:2], dtype=bool)
    mask[y0:y1, x0:x1] = True
    return mask


def test_ink_mask_uses_the_paper_colour_as_reference() -> None:
    px = _page()
    mask = _stroke(px, 50, 90, 60, 120)
    assert np.array_equal(km.ink_mask(px, PAPER), mask)


def test_ink_ratio_is_one_when_unchanged_and_zero_when_gone() -> None:
    original = _page()
    region = _stroke(original, 50, 90, 60, 120)
    same = original.copy()
    assert km.ink_ratio(same, original, region, PAPER) == pytest.approx(1.0)
    gone = _page()
    assert km.ink_ratio(gone, original, region, PAPER) == 0.0
    half = original.copy()
    half[:, 90:] = PAPER
    assert km.ink_ratio(half, original, region, PAPER) == pytest.approx(0.5)


def test_stray_ink_counts_ink_outside_the_allowed_regions_only() -> None:
    frame = _page()
    allowed = _stroke(frame, 50, 90, 60, 120)
    assert km.stray_ink_ratio(frame, [allowed], PAPER) == 0.0
    _stroke(frame, 150, 170, 200, 260)  # a foreign object
    ratio = km.stray_ink_ratio(frame, [allowed], PAPER)
    assert ratio == pytest.approx((20 * 60) / (200 * 300))
    # a margin around the allowed region absorbs anti-aliased edges
    frame2 = _page()
    allowed2 = _stroke(frame2, 50, 90, 60, 120)
    frame2[48:50, 60:120] = (30, 30, 30)
    assert km.stray_ink_ratio(frame2, [allowed2], PAPER, margin=3) == 0.0


def test_edge_iou_is_one_for_identical_content_and_drops_when_redrawn() -> None:
    a = _page()
    region = _stroke(a, 50, 120, 60, 160)
    a[70:100, 80:140] = (200, 40, 40)
    assert km.edge_iou(a, a, region) == pytest.approx(1.0)
    b = a.copy()
    b[70:100, 80:140] = (30, 30, 30)  # the inner shape lost its outline
    assert km.edge_iou(a, b, region) < 0.9
    c = _page()
    _stroke(c, 50, 120, 60, 160)
    c[55:115, 65:155] = (90, 160, 90)  # restyled interior
    assert km.edge_iou(a, c, region) < 0.6


def test_edge_iou_of_an_empty_region_is_zero_not_a_crash() -> None:
    a = _page()
    assert km.edge_iou(a, a, np.zeros(a.shape[:2], dtype=bool)) == 0.0


def test_motion_is_zero_for_a_still_clip_and_positive_for_a_moving_one() -> None:
    still = [_page() for _ in range(4)]
    assert km.motion_score(still) == 0.0
    moving = []
    for i in range(4):
        px = _page()
        _stroke(px, 50, 90, 20 + 40 * i, 80 + 40 * i)
        moving.append(px)
    assert km.motion_score(moving) > 0.01


def test_frame_report_flags_the_acceptance_thresholds() -> None:
    original = _page()
    main = _stroke(original, 50, 120, 60, 160)
    leaf = _stroke(original, 140, 170, 200, 260, (120, 30, 30))
    final = _page()
    _stroke(final, 50, 120, 60, 160)
    report = km.frame_report(
        final,
        expected_original=original,
        main_mask=main,
        secondary_masks={"sec-1": leaf},
        expected_secondary_ink={"sec-1": 0.0},
        paper=PAPER,
    )
    assert report["edge_iou_main"] == pytest.approx(1.0)
    assert report["secondary_ink_ratio"]["sec-1"] == 0.0
    assert report["stray_ink_ratio"] == 0.0
    assert report["passed"] is True
    final2 = final.copy()
    _stroke(final2, 140, 170, 200, 260, (120, 30, 30))  # leaf is still there
    bad = km.frame_report(
        final2,
        expected_original=original,
        main_mask=main,
        secondary_masks={"sec-1": leaf},
        expected_secondary_ink={"sec-1": 0.0},
        paper=PAPER,
    )
    assert bad["passed"] is False and "SECONDARY_INK_MISMATCH" in bad["violations"]
