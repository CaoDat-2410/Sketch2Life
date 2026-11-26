from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_video_app",
    MODAL_DIR / "video_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
video_worker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(video_worker)


def test_ltx_prompt_opens_with_the_action_and_describes_only_motion() -> None:
    action = "The yellow chick hops forward once and dips its beak toward the grass."

    prompt = video_worker._ltx_animation_prompt(action)

    assert prompt.startswith(action)
    assert "smooth and continuous" in prompt
    assert "crayon strokes, colours and paper texture exactly as in the first frame" in prompt
    assert prompt.endswith("The camera remains static throughout.")
    assert "\n" not in prompt and len(prompt.split()) <= 200


def test_ltx_prompt_names_nothing_the_model_should_not_draw() -> None:
    # FEAT-094 E1: a prompt full of prohibitions and "add a prop" lines made the model draw an extra object.
    prompt = video_worker._ltx_animation_prompt("The turtle looks at a leaf.")
    lowered = prompt.lower()

    for word in ("do not", "never", " no ", "prop", "watermark", "audio", "duplicate"):
        assert word not in lowered, word


def test_ltx_prompt_ends_an_unfinished_action_sentence() -> None:
    prompt = video_worker._ltx_animation_prompt("  The turtle crawls to the leaf  ")

    assert prompt.startswith("The turtle crawls to the leaf. The movement")


def test_ltx_prompt_rejects_an_empty_scene_direction() -> None:
    with pytest.raises(video_worker.WorkerContractError) as error:
        video_worker._ltx_animation_prompt("  ")

    assert str(error.value) == "VIDEO_SCENE_DIRECTION_REQUIRED"


def test_video_app_no_longer_exposes_full_frame_leaf_guide_path() -> None:
    assert not hasattr(video_worker, "_scene_requires_leaf_guide")
    assert not hasattr(video_worker, "render_leaf_guide_frame")
