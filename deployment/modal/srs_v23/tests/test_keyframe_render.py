"""FEAT-087 M5: prepare_keyframes = SAM masks + compositor + fallback decisions (fake predictor)."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import keyframe_plan as kp
import keyframe_render as kr
import story_staging_worker as ss

PAPER = (244, 240, 226)
SRC_W, SRC_H = 2000, 1000  # fits 1088x544 -> scale 0.544, offset (96, 112)


def _drawing(tmp: Path) -> Path:
    px = np.zeros((SRC_H, SRC_W, 3), dtype=np.uint8)
    px[:] = PAPER
    px[400:700, 300:900] = (40, 90, 50)  # turtle (source px)
    px[480:620, 1500:1800] = (120, 30, 30)  # leaf
    path = tmp / "drawing.png"
    Image.fromarray(px).save(path)
    return path


def _plan(mode="keyframe", **over):
    states = ("unchanged", "unchanged", "unchanged", "partly_gone", "gone")
    plan = {
        "schema_version": kp.KEYFRAME_PLAN_SCHEMA,
        "render_mode": mode,
        "fallback_reason": None if mode == "keyframe" else "KEYFRAME_NO_BOXES",
        "source_facing": "right",
        "main": {
            "entity_id": "subject-main",
            "box": [3, 8, 9, 15],
        },  # source px 300..900 x 400..750
        "secondaries": [{"entity_id": "sec-1", "box": [14, 8, 19, 14]}],
        "staging": {
            "schema_version": ss.STAGING_SCHEMA,
            "scenes": [
                {
                    "scene_index": i,
                    "main_end": {
                        "position": "left-middle",
                        "facing": "right",
                        "scale": "same",
                    },
                    "secondary_end": [{"entity_id": "sec-1", "state": states[i - 1]}],
                }
                for i in range(1, 6)
            ],
        },
    }
    if mode == "fallback":
        plan.update(main=None, secondaries=[], staging=None, source_facing=None)
    plan.update(over)
    return plan


class _SamByColour:
    """Fake SAM: the mask is every pixel of the colour found at the box centre."""

    def set_image(self, image):
        self.image = image

    def predict(self, *, box, multimask_output):
        x0, y0, x1, y1 = (int(v) for v in box)
        colour = self.image[(y0 + y1) // 2, (x0 + x1) // 2]
        mask = (self.image == colour).all(axis=2)
        return mask[None], np.array([0.97]), None


def test_a_good_plan_gives_six_keyframes_in_keyframe_mode(tmp_path) -> None:
    result = kr.prepare_keyframes(
        _drawing(tmp_path),
        _plan(),
        scene_count=5,
        workdir=tmp_path,
        predictor_factory=_SamByColour,
    )
    assert result.render_mode == "keyframe" and result.fallback_reason is None
    assert len(result.paths) == 6 and all(p.is_file() for p in result.paths)
    assert [s["index"] for s in result.summaries] == list(range(6))
    assert all(len(s["sha256"]) == 64 for s in result.summaries)
    assert result.summaries[5]["secondary_states"] == {"sec-1": "gone"}
    assert (
        result.summaries[5]["stray_ink_ratio"]
        <= result.summaries[0]["stray_ink_ratio"] + 1e-9
    )
    # K0 is the same canvas the legacy path conditions on
    k0 = Image.open(result.paths[0])
    assert k0.size == (1280, 768)
    assert (
        hashlib.sha256(result.paths[0].read_bytes()).hexdigest()
        == result.summaries[0]["sha256"]
    )


def test_a_fallback_plan_gives_only_the_original_and_keeps_the_reason(tmp_path) -> None:
    result = kr.prepare_keyframes(
        _drawing(tmp_path),
        _plan("fallback"),
        scene_count=5,
        workdir=tmp_path,
        predictor_factory=lambda: pytest.fail("SAM must not load for a fallback plan"),
    )
    assert (result.render_mode, result.fallback_reason) == (
        "fallback",
        "KEYFRAME_NO_BOXES",
    )
    assert len(result.paths) == 1


def test_a_sam_rejection_falls_back_with_its_code(tmp_path) -> None:
    class LowScore(_SamByColour):
        def predict(self, *, box, multimask_output):
            mask, _, logits = super().predict(
                box=box, multimask_output=multimask_output
            )
            return mask, np.array([0.1]), logits

    result = kr.prepare_keyframes(
        _drawing(tmp_path),
        _plan(),
        scene_count=5,
        workdir=tmp_path,
        predictor_factory=LowScore,
    )
    assert (result.render_mode, result.fallback_reason) == (
        "fallback",
        "SAM_MASK_LOW_CONFIDENCE",
    )
    assert len(result.paths) == 1


def test_a_sam_crash_falls_back_without_leaking_the_exception_text(tmp_path) -> None:
    def broken():
        raise RuntimeError("CUDA out of memory: /secret/path")

    result = kr.prepare_keyframes(
        _drawing(tmp_path),
        _plan(),
        scene_count=5,
        workdir=tmp_path,
        predictor_factory=broken,
    )
    assert (result.render_mode, result.fallback_reason) == (
        "fallback",
        "KEYFRAME_UNEXPECTED_ERROR",
    )
    assert "secret" not in repr(result.summaries)


def test_a_main_subject_that_covers_an_object_falls_back(tmp_path) -> None:
    plan = _plan()
    for scene in plan["staging"]["scenes"]:
        scene["main_end"]["position"] = "right-middle"
    result = kr.prepare_keyframes(
        _drawing(tmp_path),
        plan,
        scene_count=5,
        workdir=tmp_path,
        predictor_factory=_SamByColour,
    )
    assert (result.render_mode, result.fallback_reason) == (
        "fallback",
        "KEYFRAME_SUBJECT_COVERS_OBJECT",
    )


def test_an_invalid_plan_is_a_contract_error_not_a_fallback(tmp_path) -> None:
    bad = _plan()
    bad["staging"]["scenes"].pop()
    with pytest.raises(kp.KeyframePlanError):
        kr.prepare_keyframes(
            _drawing(tmp_path),
            bad,
            scene_count=5,
            workdir=tmp_path,
            predictor_factory=_SamByColour,
        )
