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


def test_ltx_prompt_keeps_source_art_and_only_allows_scripted_props() -> None:
    prompt = video_worker._ltx_animation_prompt(
        "The turtle looks at the leaf named in the adult-confirmed scene."
    )

    assert "exact source subject, silhouette" in prompt
    assert "Add only a prop explicitly named in the approved action" in prompt
    assert "Never show the source artwork as a duplicate, thumbnail" in prompt
    assert "one continuous shot" in prompt
    assert "The turtle looks at the leaf named in the adult-confirmed scene." in prompt


def test_ltx_prompt_forbids_every_audio_track() -> None:
    prompt = video_worker._ltx_animation_prompt("The approved character waves once.")

    assert "Do not generate speech, narration, subtitles, music, sound, or any audio." in prompt


def test_ltx_prompt_keeps_subject_clear_and_background_unmarked() -> None:
    prompt = video_worker._ltx_animation_prompt("The turtle looks at a leaf.")

    assert "Keep the camera and paper fixed" in prompt
    assert "no cuts, extra objects, readable text" in prompt


def test_ltx_prompt_rejects_an_empty_scene_direction() -> None:
    with pytest.raises(video_worker.WorkerContractError) as error:
        video_worker._ltx_animation_prompt("  ")

    assert str(error.value) == "VIDEO_SCENE_DIRECTION_REQUIRED"


def test_video_app_no_longer_exposes_full_frame_leaf_guide_path() -> None:
    assert not hasattr(video_worker, "_scene_requires_leaf_guide")
    assert not hasattr(video_worker, "render_leaf_guide_frame")
