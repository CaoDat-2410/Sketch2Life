"""FEAT-087 M5: SAM box-prompt wrapper and mask acceptance checks (predictor injected)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import sam_masks as sm

H, W = 200, 300


class _Predictor:
    """Returns a filled rectangle per box (optionally mutated) like SAM2ImagePredictor.predict."""

    def __init__(self, scores=0.95, mutate=None):
        self.boxes = []
        self.image = None
        self.scores = scores
        self.mutate = mutate

    def set_image(self, image):
        self.image = image

    def predict(self, *, box, multimask_output):
        assert multimask_output is False
        self.boxes.append(tuple(int(v) for v in box))
        x0, y0, x1, y1 = self.boxes[-1]
        mask = np.zeros((H, W), dtype=bool)
        mask[y0:y1, x0:x1] = True
        if self.mutate:
            mask = self.mutate(len(self.boxes) - 1, mask)
        return mask[None], np.array([self.scores]), np.zeros((1, 4, 4))


IMAGE = np.zeros((H, W, 3), dtype=np.uint8)


def test_each_box_becomes_a_mask_inside_its_box() -> None:
    predictor = _Predictor()
    masks = sm.masks_for_boxes(
        IMAGE, [(20, 30, 120, 130), (180, 40, 260, 120)], predictor
    )
    assert predictor.image is IMAGE
    assert predictor.boxes == [(20, 30, 120, 130), (180, 40, 260, 120)]
    assert [m.dtype for m in masks] == [np.dtype(bool)] * 2
    assert int(masks[0].sum()) == 100 * 100


def test_a_low_confidence_mask_is_rejected() -> None:
    with pytest.raises(sm.MaskError) as e:
        sm.masks_for_boxes(IMAGE, [(20, 30, 120, 130)], _Predictor(scores=0.3))
    assert e.value.code == "SAM_MASK_LOW_CONFIDENCE"


def test_a_tiny_or_empty_mask_is_rejected() -> None:
    with pytest.raises(sm.MaskError) as e:
        sm.masks_for_boxes(
            IMAGE, [(20, 30, 120, 130)], _Predictor(mutate=lambda i, m: m & False)
        )
    assert e.value.code == "SAM_MASK_TOO_SMALL"

    def sliver(i, m):
        out = np.zeros_like(m)
        out[40:42, 40:60] = True
        return out

    with pytest.raises(sm.MaskError) as e:
        sm.masks_for_boxes(IMAGE, [(20, 30, 120, 130)], _Predictor(mutate=sliver))
    assert e.value.code == "SAM_MASK_TOO_SMALL"


def test_a_mask_that_floods_far_outside_its_box_is_rejected() -> None:
    def flood(i, m):
        out = m.copy()
        out[:, :] = True
        return out

    with pytest.raises(sm.MaskError) as e:
        sm.masks_for_boxes(IMAGE, [(20, 30, 120, 130)], _Predictor(mutate=flood))
    assert e.value.code == "SAM_MASK_ESCAPES_BOX"


def test_overlapping_masks_of_different_objects_are_rejected() -> None:
    with pytest.raises(sm.MaskError) as e:
        sm.masks_for_boxes(
            IMAGE, [(20, 30, 140, 130), (60, 40, 200, 130)], _Predictor()
        )
    assert e.value.code == "SAM_MASKS_OVERLAP"


def test_a_few_stray_pixels_outside_the_box_are_clipped_not_fatal() -> None:
    def speck(i, m):
        out = m.copy()
        out[0:3, 0:3] = True
        return out

    masks = sm.masks_for_boxes(IMAGE, [(20, 30, 120, 130)], _Predictor(mutate=speck))
    assert not masks[0][0:3, 0:3].any() and int(masks[0].sum()) == 100 * 100


def test_boxes_are_clamped_to_the_image() -> None:
    predictor = _Predictor()
    sm.masks_for_boxes(IMAGE, [(-10, -5, 90, 110)], predictor)
    assert predictor.boxes == [(0, 0, 90, 110)]
