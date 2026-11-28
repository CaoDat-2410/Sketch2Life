"""Modal refuses a build step that follows a mounted (non-copy) ``add_local_*`` layer."""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "language_audio_app.py"


def test_no_copy_layer_follows_a_mounted_layer_in_reassigned_images() -> None:
    mounted: set[str] = set()
    for node in ast.parse(APP.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        target = node.targets[0]
        func = call.func
        if not isinstance(target, ast.Name) or not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name) or func.value.id != target.id:
            continue
        copies = any(
            keyword.arg == "copy" and isinstance(keyword.value, ast.Constant) and keyword.value.value
            for keyword in call.keywords
        )
        if func.attr.startswith("add_local_") and not copies:
            mounted.add(target.id)
        else:
            assert target.id not in mounted, f"{target.id}: build step on line {node.lineno}"
