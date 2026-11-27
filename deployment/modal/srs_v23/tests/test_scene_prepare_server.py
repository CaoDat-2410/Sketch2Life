"""FEAT-094 phase 2: the child process answers one JSON line per request."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import scene_prepare_server as server  # noqa: E402
from scene_prepare_host import REPLY_PREFIX  # noqa: E402


def _replies(output: str) -> list[dict[str, Any]]:
    return [json.loads(line[len(REPLY_PREFIX) :]) for line in output.splitlines() if line.startswith(REPLY_PREFIX)]


def test_the_server_replies_to_each_line_and_survives_a_failing_request() -> None:
    def fail(_body: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("provider text that must not travel")

    requests = io.StringIO(
        json.dumps({"id": 1, "op": "bad", "body": {}})
        + "\n"
        + json.dumps({"id": 2, "op": "missing", "body": {}})
        + "\n"
        + json.dumps({"id": 3, "op": "good", "body": {"n": 7}})
        + "\n"
    )
    output = io.StringIO()

    server.serve(requests, output, {"bad": fail, "good": lambda body: {"n": body["n"]}})

    replies = _replies(output.getvalue())
    assert [reply["id"] for reply in replies] == [1, 2, 3]
    assert replies[0]["ok"] is False and replies[0]["error"] == "SCENE_PREPARE_UNEXPECTED_ERROR"
    assert "provider text" not in output.getvalue()
    assert replies[1]["ok"] is False
    assert replies[2] == {"id": 3, "ok": True, "result": {"n": 7}}


def test_the_plate_directory_is_the_newest_staged_revision(tmp_path: Path) -> None:
    for revision in ("aaa", "bbb"):
        (tmp_path / "flux_3_image_klein" / revision / "image").mkdir(parents=True)
        (tmp_path / "flux_3_image_klein" / revision / "image" / "modular_model_index.json").write_text("{}")

    assert server.plate_model_dir(tmp_path) == str(tmp_path / "flux_3_image_klein" / "bbb" / "image")
    with pytest.raises(RuntimeError, match="PLATE_MODEL_UNAVAILABLE"):
        server.plate_model_dir(tmp_path / "empty")


def test_a_scene_is_prepared_from_the_job_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "drawing.png").write_bytes(b"drawing")
    seen: dict[str, Any] = {}

    def prepare_scene(drawing: bytes, **arguments: Any) -> dict[str, Any]:
        seen.update(arguments, drawing=drawing)
        return {"keyframe_png": b"keyframe", "background": "PAPER", "reason": "PLATE_FLAT"}

    monkeypatch.setattr(server.scene_prepare, "prepare_scene", prepare_scene)
    request = {
        "scene_index": 2,
        "main": {"entity_id": "e1"},
        "secondaries": [],
        "staging": {},
        "plate_prompt": "a park",
        "source_facing": "right",
    }

    result = server.prepare({"directory": str(tmp_path), "request": request})

    assert result == {"background": "PAPER", "reason": "PLATE_FLAT"}
    assert (tmp_path / "keyframe.png").read_bytes() == b"keyframe"
    assert seen["drawing"] == b"drawing" and seen["scene_index"] == 2 and seen["plate_prompt"] == "a park"
    assert seen["predictor_factory"] is server.load_sam
    painted: list[tuple[str, int]] = []
    monkeypatch.setattr(server, "logged_plate", lambda prompt, seed: painted.append((prompt, seed)))
    seen["generate_plate"]("a park")
    server.prepare({"directory": str(tmp_path), "request": {**request, "plate_seed": 1016}})
    seen["generate_plate"]("a park")
    assert painted == [("a park", 7), ("a park", 1016)]


def test_a_warm_up_reports_the_models_that_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> Any:
        raise RuntimeError("no checkpoint")

    monkeypatch.setattr(server, "load_flux", lambda: object())
    monkeypatch.setattr(server, "load_sam", missing)

    assert server.warm_up({}) == {"loaded": ["plate"]}


def test_the_real_preparation_runs_on_the_paper_fallback_without_models(tmp_path: Path) -> None:
    pixels = np.full((200, 300, 3), 255, dtype=np.uint8)
    pixels[60:140, 80:220] = (200, 40, 40)
    Image.fromarray(pixels).save(tmp_path / "drawing.png")

    result = server.prepare(
        {
            "directory": str(tmp_path),
            "request": {
                "scene_index": 1,
                "main": {"entity_id": "e1", "label": "xe", "box": [250, 300, 750, 700]},
                "secondaries": [],
                "staging": {},
                "plate_prompt": "a park",
                "source_facing": "right",
            },
        }
    )

    assert result["background"] == "PAPER" and result["reason"]
    assert Image.open(tmp_path / "keyframe.png").size == (1280, 768)
