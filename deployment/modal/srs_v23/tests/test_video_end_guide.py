"""FEAT-094 phase 5: the first frame of a Parent scene may also softly guide its last frame (experiment E2)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))


def _video_app() -> Any:
    spec = importlib.util.spec_from_file_location("sketch2life_video_app_guide", MODAL_DIR / "video_app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


APP = _video_app()


def _manifest(**changes: Any) -> bytes:
    return json.dumps(
        {
            "schema_version": APP.INPUT_SCHEMA,
            "scene_id": "scene-1",
            "scene_index": 1,
            "scene_count": 5,
            "purpose": "SYNTHETIC_END_TO_END",
            "storyboard_sha256": "a" * 64,
            "source_drawing_ref": "input/drawing.png",
            "source_drawing_sha256": "b" * 64,
            "visual_prompt": "A chick pecks the ground.",
            "target_duration_seconds": 10.0,
            "seed": 7,
            **changes,
        }
    ).encode("utf-8")


def test_a_manifest_without_the_guide_renders_as_before(tmp_path: Path) -> None:
    manifest = APP._parse_scene_input(_manifest())

    assert APP._end_guide_arguments(manifest, tmp_path / "k.png") == {}


def test_the_guide_reuses_the_first_frame_at_the_given_strength(tmp_path: Path) -> None:
    manifest = APP._parse_scene_input(_manifest(end_guide_strength=0.7))

    assert APP._end_guide_arguments(manifest, tmp_path / "k.png") == {
        "end_image_path": tmp_path / "k.png",
        "end_strength": 0.7,
    }


@pytest.mark.parametrize("value", [0, 0.05, 1.5, "0.7", True, None])
def test_an_unusable_strength_is_refused(value: Any) -> None:
    with pytest.raises(APP.WorkerContractError, match="VIDEO_INPUT_NOT_ALLOWED"):
        APP._parse_scene_input(_manifest(end_guide_strength=value))


def test_the_scene_renderer_passes_the_guide_to_the_model_call() -> None:
    source = (MODAL_DIR / "video_app.py").read_text(encoding="utf-8")
    render = source[source.index("def generate_video_scene") : source.index("def _build_silent_story_output_payload")]

    assert "**_end_guide_arguments(manifest, image_path)" in render
