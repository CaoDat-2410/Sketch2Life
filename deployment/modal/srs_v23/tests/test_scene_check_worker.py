"""FEAT-094 phase 5: the Qwen worker answers fixed problem codes about one picture sheet."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import scene_check  # noqa: E402


def _request(sheet: bytes = b"\x89PNG\r\n\x1a\nsheet", **changes: object) -> dict:
    return {
        "sheet_png_b64": base64.b64encode(sheet).decode("ascii"),
        "sheet_sha256": hashlib.sha256(sheet).hexdigest(),
        **changes,
    }


def test_the_sheet_is_verified_before_it_reaches_the_model() -> None:
    sheet, prompt = scene_check.read_sheet(_request())
    assert sheet.startswith(b"\x89PNG") and prompt == scene_check.PROMPT
    for broken in (
        _request(sheet_sha256="0" * 64),
        _request(sheet_png_b64="not base64!"),
        _request(sheet=b"GIF89a"),
        _request(extra="field"),
        {},
    ):
        with pytest.raises(ValueError, match="MODAL_INPUT_NOT_ALLOWED"):
            scene_check.read_sheet(broken)


def test_each_answered_question_becomes_its_problem_code() -> None:
    answer = {key: False for key in scene_check.SCHEMA["properties"]}
    assert scene_check.problems(json.dumps(answer)) == []

    answer.update(new_person_or_animal=True, text_or_logo=True)

    assert scene_check.problems(json.dumps(answer)) == ["NEW_CHARACTER", "TEXT_OR_LOGO"]
    assert scene_check.SCHEMA["additionalProperties"] is False
    assert set(scene_check.SCHEMA["required"]) == set(scene_check.SCHEMA["properties"])


@pytest.mark.parametrize("text", ["not json", "[]", json.dumps({"new_person_or_animal": "yes"}), "{}"])
def test_an_unusable_answer_is_a_retryable_model_error(text: str) -> None:
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        scene_check.problems(text)


def test_the_question_compares_the_later_moments_with_the_first_frame() -> None:
    assert "top left" in scene_check.PROMPT and "first frame" in scene_check.PROMPT and "six" in scene_check.PROMPT


def test_the_question_names_hands_and_smears_and_allows_ordinary_poses() -> None:
    for words in ("hand", "partly visible", "smeared", "pecking", "closing the eyes"):
        assert words in scene_check.PROMPT


def test_the_shared_worker_routes_the_check_and_mounts_the_module() -> None:
    source = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
    routes = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_shared_qwen_routes"
    )

    assert '"video.scene.validate": check_video_scene.local' in ast.get_source_segment(source, routes)
    assert 'add_local_file(str(_scene_check_file), "/root/scene_check.py")' in source


def test_a_first_frame_is_asked_about_its_painted_background() -> None:
    _sheet, prompt = scene_check.read_sheet(_request(kind="keyframe"))

    assert prompt == scene_check.KEYFRAME_PROMPT
    for words in ("two pictures", "background", "hand", "photograph", "second one of the same kind", "realistic"):
        assert words in prompt
    with pytest.raises(ValueError, match="MODAL_INPUT_NOT_ALLOWED"):
        scene_check.read_sheet(_request(kind="anything"))
