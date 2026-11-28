"""Static checks that the merged text worker follows the current dev runtime shape."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "language_audio_app.py"


def _text_gpu_functions() -> list[ast.Call]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            kwargs = {item.arg: item.value for item in decorator.keywords}
            image = kwargs.get("image")
            if "gpu" in kwargs and isinstance(image, ast.Name) and image.id in {
                "_text_image",
                "_story_text_image",
            }:
                calls.append(decorator)
    return calls


def test_every_text_gpu_function_uses_a_fixed_bounded_window() -> None:
    calls = _text_gpu_functions()
    assert len(calls) >= 8
    for call in calls:
        window = {item.arg: item.value for item in call.keywords}["scaledown_window"]
        assert isinstance(window, ast.Constant)
        assert isinstance(window.value, int)
        assert 30 <= window.value <= 120


def test_text_workers_use_the_dev_pinned_model_identity() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    assignments = {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    assert assignments["TEXT_MODEL_ID"] == "Qwen/Qwen3.8-27B-FP8"
    assert assignments["TEXT_MODEL_REVISION"] == "c3a462cc3d38cf351f3b26cbd763469eeb74ef81"


def test_teacher_presentation_svg_worker_uses_dev_mounts_and_window() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "name=\"generate-presentation-svg-draft\"" in source
    assert "KERNEL_CACHE_MOUNT" not in source
    assert "kernel_cache_volume" not in source
    assert "_TEXT_SCALEDOWN_SECONDS" not in source


def test_removed_q38_runtime_overrides_are_not_restored() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "_story_q38_image" not in source
    assert "qwen38_allow_unpinned_dev" not in source
    assert "_resolve_text_scaledown_seconds" not in source
