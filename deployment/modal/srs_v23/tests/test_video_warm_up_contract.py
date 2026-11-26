"""FEAT-093 Amendment C: both video GPU functions answer a warm-up before they parse a job."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "file_name, function_name, condition",
    [
        # FEAT-094: the renderer's warm-up may also carry the scene prompts.
        ("video_app.py", "generate_video_scene", "payload.get('warmup') is True"),
        ("language_audio_app.py", "prepare_video_scene", "payload == {'warmup': True}"),
    ],
)
def test_warm_up_is_the_first_branch_and_loads_nothing_from_the_job(
    file_name: str, function_name: str, condition: str
) -> None:
    source = (MODAL_DIR / file_name).read_text(encoding="utf-8")
    function = next(
        node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    branch = next(node for node in function.body if isinstance(node, ast.If))
    assert ast.unparse(branch.test) == condition
    parse_line = next(
        node.lineno
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "parse_worker_input"
    )
    assert branch.lineno < parse_line
