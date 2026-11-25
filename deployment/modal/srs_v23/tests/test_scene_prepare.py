"""FEAT-093: scene preparation core with fake SAM and fake plate generator (CPU only)."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import scene_prepare as sp

W, H = 1088, 576  # fits the canvas margin box at scale 1.0
PAPER = (244, 240, 226)
MAIN = {"entity_id": "main", "box": [2, 6, 11, 17]}
LEAF = {"entity_id": "sec-1", "box": [13, 9, 19, 15]}


def _drawing_png() -> bytes:
    pixels = np.zeros((H, W, 3), dtype=np.uint8)
    pixels[:] = PAPER
    pixels[190:490, 110:600] = (40, 90, 50)
    pixels[260:430, 710:1030] = (120, 30, 30)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


class _Predictor:
    def set_image(self, image) -> None:
        self.shape = image.shape[:2]

    def predict(self, box, multimask_output):
        x0, y0, x1, y1 = (int(v) for v in box)
        mask = np.zeros(self.shape, dtype=bool)
        mask[y0:y1, x0:x1] = True
        return np.array([mask]), np.array([0.95]), None


def _staging(state="unchanged"):
    return {
        "schema_version": "sketch2life.story-staging.v1",
        "scenes": [
            {
                "scene_index": 1,
                "main_end": {"position": "left-middle", "facing": "right", "scale": "same"},
                "secondary_end": [{"entity_id": "sec-1", "state": state}],
            }
        ],
    }


def _plate(_prompt: str) -> Image.Image:
    rng = np.random.default_rng(3)
    base = np.full((768, 1280, 3), (150, 205, 150), dtype=np.uint8)
    base[::7] = rng.integers(60, 230, size=(768 // 7 + 1, 1280, 3), dtype=np.uint8)[: len(base[::7])]
    return Image.fromarray(base)


def _run(plate=_plate, predictor=_Predictor, state="unchanged"):
    return sp.prepare_scene(
        _drawing_png(), main=MAIN, secondaries=[LEAF], staging=_staging(state), scene_index=1,
        source_facing="right", plate_prompt="A sunny garden, crayon texture.", generate_plate=plate,
        predictor_factory=predictor,
    )


def _pixels(result) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(result["keyframe_png"])).convert("RGB"))


def test_a_good_plate_goes_behind_the_child_subjects() -> None:
    result = _run()

    assert result["background"] == "AI" and result["reason"] is None
    pixels = _pixels(result)
    assert pixels.shape == (768, 1280, 3)
    assert tuple(pixels[150, 150]) != PAPER  # background is the plate, not paper
    assert (pixels == np.array([120, 30, 30])).all(axis=2).sum() > 1000  # leaf pixels untouched


@pytest.mark.parametrize(
    ("plate", "reason"),
    [
        (lambda _p: Image.new("RGB", (1280, 768), (200, 200, 200)), "PLATE_FLAT"),
        (lambda _p: Image.new("RGB", (1280, 768), "white"), "PLATE_FLAT"),
        (lambda _p: (_ for _ in ()).throw(RuntimeError("boom")), "PLATE_GENERATION_FAILED"),
    ],
)
def test_a_bad_plate_falls_back_to_paper_with_the_keyframe(plate, reason) -> None:
    result = _run(plate=plate)

    assert result["background"] == "PAPER" and result["reason"] == reason
    assert tuple(_pixels(result)[150, 150]) == PAPER  # inside the page, away from the subjects


def test_mostly_white_plate_is_blank() -> None:
    noisy = np.full((768, 1280, 3), 255, dtype=np.uint8)
    noisy[:30] = np.random.default_rng(1).integers(0, 255, size=(30, 1280, 3), dtype=np.uint8)

    assert sp.plate_problem(Image.fromarray(noisy)) == "PLATE_BLANK"


def test_mask_failure_keeps_the_original_drawing_on_the_canvas() -> None:
    class _Weak(_Predictor):
        def predict(self, box, multimask_output):
            mask, _score, extra = super().predict(box, multimask_output)
            return mask, np.array([0.01]), extra

    result = _run(predictor=_Weak)

    assert result["background"] == "PAPER" and result["reason"] == "SAM_MASK_LOW_CONFIDENCE"
    assert _pixels(result).shape == (768, 1280, 3)


def test_a_gone_secondary_is_absent_from_the_keyframe() -> None:
    result = _run(state="gone")

    assert (_pixels(result) == np.array([120, 30, 30])).all(axis=2).sum() == 0
