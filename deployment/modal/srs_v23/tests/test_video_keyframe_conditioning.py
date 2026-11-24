"""FEAT-087 M5: LTX conditioning with a start replace + an end guide (fake LTX, no GPU)."""

from __future__ import annotations

import contextlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))
SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_video_app_kf", MODAL_DIR / "video_app.py"
)
assert SPEC is not None and SPEC.loader is not None
video_app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(video_app)


class _Cond:
    def __init__(self, kind, path, frame_idx, strength):
        self.kind, self.path, self.frame_idx, self.strength = (
            kind,
            path,
            frame_idx,
            strength,
        )

    @classmethod
    def replace(cls, path, frame_idx, strength):
        return cls("replace", path, frame_idx, strength)

    @classmethod
    def guide(cls, path, frame_idx, strength):
        return cls("guide", path, frame_idx, strength)


@pytest.fixture()
def fake_ltx(monkeypatch, tmp_path):
    seen: dict = {}

    class Pipeline:
        def __call__(self, **kwargs):
            seen.update(kwargs)
            return types.SimpleNamespace(video="v")

    def encode_video(video, fps, audio, path, video_chunks_number=None):
        Path(path).write_bytes(b"mp4")

    torch = types.ModuleType("torch")
    torch.inference_mode = lambda: contextlib.nullcontext()
    media_io = types.ModuleType("ltx_pipelines.utils.media_io")
    media_io.encode_video = encode_video
    types_mod = types.ModuleType("ltx_pipelines.utils.types")
    types_mod.ImageConditioningInput = _Cond
    for name, module in {
        "torch": torch,
        "ltx_pipelines": types.ModuleType("ltx_pipelines"),
        "ltx_pipelines.utils": types.ModuleType("ltx_pipelines.utils"),
        "ltx_pipelines.utils.media_io": media_io,
        "ltx_pipelines.utils.types": types_mod,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    return Pipeline(), seen, tmp_path


def test_a_scene_without_an_end_frame_is_conditioned_exactly_as_before(
    fake_ltx,
) -> None:
    pipeline, seen, tmp = fake_ltx
    video_app._run_ltx(
        pipeline=pipeline,
        image_path=tmp / "k0.png",
        output_path=tmp / "o.mp4",
        visual_prompt="p",
        seed=1,
        target_duration=6.0,
        prompt_is_compiled=True,
    )
    assert [(c.kind, c.frame_idx, c.strength) for c in seen["images"]] == [
        ("replace", 0, 1.0)
    ]


def test_an_end_keyframe_is_a_guide_on_the_last_generated_frame(fake_ltx) -> None:
    pipeline, seen, tmp = fake_ltx
    plan = video_app._run_ltx(
        pipeline=pipeline,
        image_path=tmp / "k0.png",
        output_path=tmp / "o.mp4",
        visual_prompt="p",
        seed=1,
        target_duration=6.0,
        prompt_is_compiled=True,
        end_image_path=tmp / "k1.png",
        end_strength=0.85,
    )
    start, end = seen["images"]
    assert (start.kind, start.frame_idx, start.strength) == ("replace", 0, 1.0)
    assert (end.kind, end.frame_idx, end.strength) == (
        "guide",
        plan["generated_frame_count"] - 1,
        0.85,
    )
    assert (
        end.path == str(tmp / "k1.png")
        and seen["num_frames"] == plan["generated_frame_count"]
    )


def test_an_end_frame_needs_a_strength_and_vice_versa(fake_ltx) -> None:
    pipeline, _, tmp = fake_ltx
    for kwargs in ({"end_image_path": tmp / "k1.png"}, {"end_strength": 0.8}):
        with pytest.raises(ValueError):
            video_app._run_ltx(
                pipeline=pipeline,
                image_path=tmp / "k0.png",
                output_path=tmp / "o.mp4",
                visual_prompt="p",
                seed=1,
                target_duration=6.0,
                prompt_is_compiled=True,
                **kwargs,
            )


# ---- per-scene render inputs and the SAM loader ------------------------------------------------

import numpy as np
from PIL import Image

import keyframe_plan as kp
import keyframe_render as kr
import sam_masks
import story_visual_plan as svp


def _visual_plan():
    scenes = [
        {"scene_id": f"scene-{i}", "action": f"a{i}", "duration_seconds": 6.0}
        for i in range(1, 6)
    ]
    plan = {
        "schema_version": svp.STORY_VISUAL_PLAN_SCHEMA_V3,
        "source_story_sha256": "a" * 64,
        "entities": [
            {
                "entity_id": "subject-main",
                "kind": "subject",
                "source": "source_drawing",
                "label": "turtle",
                "appearance": "Preserve the exact subject.",
            },
        ],
        "scenes": [
            {
                "scene_id": s["scene_id"],
                "approved_action": s["action"],
                "duration_seconds": 6.0,
                "visible_entity_ids": ["subject-main"],
                "introduced_entity_ids": [],
                "removed_entity_ids": [],
                "continuity_in": "At the left.",
                "continuity_out": "At the right.",
                "spatial_direction": "",
                "model_action_instruction": "The turtle walks to the right slowly.",
                "camera_motion": "locked",
            }
            for s in scenes
        ],
    }
    return scenes, plan


def _set(mode, tmp):
    paths = [tmp / f"k{i}.png" for i in range(6 if mode == "keyframe" else 1)]
    return kr.KeyframeSet(
        mode, None if mode == "keyframe" else "KEYFRAME_NO_BOXES", paths, []
    )


def test_legacy_scenes_keep_the_v7_prompt_and_the_previous_frame_chain(
    tmp_path,
) -> None:
    scenes, plan = _visual_plan()
    chosen = video_app._scene_render_inputs(
        None,
        scenes[2],
        plan,
        scene_index=3,
        scene_count=5,
        legacy_start=tmp_path / "prev.png",
    )
    assert chosen["start_path"] == tmp_path / "prev.png"
    assert chosen["end_path"] is None and chosen["end_strength"] is None
    assert chosen["prompt_version"] == "story-i2v-v7"
    assert chosen["chain_from_previous_scene"] is True


def test_keyframe_scenes_start_and_end_on_their_own_keyframes_with_the_v8_prompt(
    tmp_path,
) -> None:
    scenes, plan = _visual_plan()
    chosen = video_app._scene_render_inputs(
        _set("keyframe", tmp_path),
        scenes[2],
        plan,
        scene_index=3,
        scene_count=5,
        legacy_start=None,
    )
    assert (
        chosen["start_path"] == tmp_path / "k2.png"
        and chosen["end_path"] == tmp_path / "k3.png"
    )
    assert chosen["end_strength"] == kp.END_FRAME_STRENGTH
    assert (
        chosen["prompt_version"] == "story-i2v-v8" and "last frame" in chosen["prompt"]
    )
    assert chosen["chain_from_previous_scene"] is False


def test_fallback_scenes_always_start_from_the_original_and_have_no_end_frame(
    tmp_path,
) -> None:
    scenes, plan = _visual_plan()
    for i in (1, 4):
        chosen = video_app._scene_render_inputs(
            _set("fallback", tmp_path),
            scenes[i - 1],
            plan,
            scene_index=i,
            scene_count=5,
            legacy_start=None,
        )
        assert (
            chosen["start_path"] == tmp_path / "k0.png" and chosen["end_path"] is None
        )
        assert chosen["prompt_version"] == "story-i2v-v8"


def test_the_k0_canvas_equals_the_legacy_conditioning_image(tmp_path) -> None:
    px = np.random.default_rng(3).integers(0, 255, (500, 900, 3), dtype=np.uint8)
    src = tmp_path / "drawing.png"
    Image.fromarray(px).save(src)
    import hashlib

    manifest = {
        "source_drawing_ref": "input/drawing.png",
        "source_drawing_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
    }
    attempt = tmp_path / "attempt"
    (attempt / "input").mkdir(parents=True)
    (attempt / "input" / "drawing.png").write_bytes(src.read_bytes())
    out = tmp_path / "legacy.png"
    video_app._prepare_story_drawing(attempt, manifest, out)
    import keyframe_compositor as kc

    canvas, _ = kc.fit_to_canvas(Image.open(src))
    assert np.array_equal(
        np.asarray(Image.open(out).convert("RGB")), np.asarray(canvas)
    )


def test_a_missing_sam_checkpoint_is_a_fallback_code_not_a_crash(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(video_app, "SAM2_CHECKPOINT", tmp_path / "missing.pt")
    with pytest.raises(sam_masks.MaskError) as e:
        video_app._load_sam_predictor()
    assert e.value.code == "SAM_CHECKPOINT_UNAVAILABLE"
