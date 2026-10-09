from __future__ import annotations

import hashlib
import json

import pytest

from sketch2life.contracts.schemas.story_video import StoryboardDrawBeatV1
from sketch2life.infrastructure.media.whiteboard_draw_schedule import order_strokes_for_beats
from sketch2life.infrastructure.media.whiteboard_sam_masks import predict_stroke_space_masks


def _beats():
    return (
        StoryboardDrawBeatV1(
            element_id="right", segment_id="segment-1", label="Bên phải",
            focus_box=(0.6, 0.1, 0.95, 0.5), start_seconds=0, end_seconds=2.5,
        ),
        StoryboardDrawBeatV1(
            element_id="left", segment_id="segment-1", label="Bên trái",
            focus_box=(0.05, 0.5, 0.4, 0.95), start_seconds=2.5, end_seconds=5,
        ),
    )


def _image_and_strokes(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    image = tmp_path / "scene.png"
    Image.new("RGB", (100, 100), "white").save(image)
    image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    stroke_path = tmp_path / "scene.strokes.json"
    strokes = [
        {"stroke_id": "left", "points": [[10, 70], [30, 70]]},
        {"stroke_id": "right", "points": [[70, 30], [90, 30]]},
    ]
    stroke_path.write_text(json.dumps({
        "artifact_type": "whiteboard_strokes_v1", "source_hash": image_hash,
        "source_width": 100, "source_height": 100,
        "crop_box": [0, 0, 100, 100], "width": 100, "height": 100,
        "strokes": strokes,
    }), encoding="utf-8")
    return image, stroke_path, strokes


class FakePredictor:
    def __init__(self, *, repeat: bool = False) -> None:
        self.repeat = repeat
        self.image_shape = None
        self.calls = 0

    def set_image(self, image) -> None:
        self.image_shape = image.shape

    def predict(self, *, box, multimask_output):
        np = pytest.importorskip("numpy")
        assert multimask_output is True
        self.calls += 1
        mask = np.zeros((100, 100), dtype=np.float32)
        if self.repeat:
            mask[25:36, 65:96] = 1
            mask[65:76, 5:36] = 1
        elif box[0] > 50:
            mask[25:36, 65:96] = 1
        else:
            mask[65:76, 5:36] = 1
        return mask[None], np.array([0.9]), None


def test_sam_masks_are_bound_to_scene_image_and_reorder_ink(tmp_path) -> None:
    image, stroke_path, strokes = _image_and_strokes(tmp_path)
    predictor = FakePredictor()
    masks = predict_stroke_space_masks(image, stroke_path, _beats(), predictor)
    order, windows = order_strokes_for_beats(
        strokes, _beats(), width=100, height=100, beat_masks=masks
    )

    assert predictor.image_shape == (100, 100, 3)
    assert predictor.calls == 2
    assert order == [1, 0]
    assert windows == [(0.0, 2.5, 0, 1), (2.5, 5.0, 1, 2)]
    manifest = json.loads(stroke_path.with_suffix(".sam2-masks.json").read_text())
    assert manifest["illustration_sha256"] == hashlib.sha256(image.read_bytes()).hexdigest()
    for item in manifest["masks"]:
        path = stroke_path.parent / item["mask_ref"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["mask_sha256"]


def test_sam_masks_reject_duplicate_object_selection(tmp_path) -> None:
    image, stroke_path, _strokes = _image_and_strokes(tmp_path)
    with pytest.raises(ValueError, match="DRAW_MASK_OVERLAP"):
        predict_stroke_space_masks(image, stroke_path, _beats(), FakePredictor(repeat=True))


def test_sam_masks_reject_strokes_from_another_illustration(tmp_path) -> None:
    image, stroke_path, _strokes = _image_and_strokes(tmp_path)
    payload = json.loads(stroke_path.read_text(encoding="utf-8"))
    payload["source_hash"] = "a" * 64
    stroke_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="DRAW_MASK_SOURCE_MISMATCH"):
        predict_stroke_space_masks(image, stroke_path, _beats(), FakePredictor())
