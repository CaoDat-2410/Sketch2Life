"""FEAT-094 phase 2: the video container runs scene preparation as a child process with its own packages."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import scene_prepare_host as host  # noqa: E402

FAKE_CHILD = r"""
import json, sys, time, os
for line in sys.stdin:
    message = json.loads(line)
    op = message["op"]
    if op == "echo":
        print("a library log line", flush=True)
        sys.stdout.write("progress without newline")
        reply = {"id": message["id"], "ok": True, "result": {"body": message["body"], "pid": os.getpid()}}
    elif op == "fail":
        reply = {"id": message["id"], "ok": False, "error": "SCENE_PREPARE_BOOM"}
    elif op == "hang":
        time.sleep(30)
        continue
    elif op == "exit":
        sys.exit(3)
    sys.stdout.write("\n" + "@@SCENE_PREPARE@@ " + json.dumps(reply) + "\n")
    sys.stdout.flush()
"""


def _worker(log: list[str] | None = None) -> Any:
    return host.PrepWorker([sys.executable, "-u", "-c", FAKE_CHILD], echo=(log.append if log is not None else lambda _l: None))


def test_a_request_returns_the_reply_and_passes_other_output_to_the_log() -> None:
    log: list[str] = []
    worker = _worker(log)
    try:
        result = worker.request("echo", {"scene": 1}, timeout=20)
        again = worker.request("echo", {"scene": 2}, timeout=20)
    finally:
        worker.stop()

    assert result["body"] == {"scene": 1} and again["body"] == {"scene": 2}
    assert result["pid"] == again["pid"], "one child serves every scene, so the models load once"
    assert "a library log line" in log


def test_a_reported_failure_raises_its_code_and_keeps_the_child() -> None:
    worker = _worker()
    try:
        with pytest.raises(host.PrepWorkerError, match="SCENE_PREPARE_BOOM"):
            worker.request("fail", {}, timeout=20)
        assert worker.running
    finally:
        worker.stop()


@pytest.mark.parametrize(
    "operation, code", [("hang", "SCENE_PREPARE_TIMEOUT"), ("exit", "SCENE_PREPARE_PROCESS_EXITED")]
)
def test_a_stuck_or_dead_child_is_replaced_on_the_next_request(operation: str, code: str) -> None:
    worker = _worker()
    try:
        first = worker.request("echo", {}, timeout=20)["pid"]
        with pytest.raises(host.PrepWorkerError, match=code):
            worker.request(operation, {}, timeout=1.0)
        assert not worker.running
        assert worker.request("echo", {}, timeout=20)["pid"] != first
    finally:
        worker.stop()


def test_stopping_ends_the_child_and_may_be_repeated() -> None:
    worker = _worker()
    worker.request("echo", {}, timeout=20)
    process = worker._process

    worker.stop()
    worker.stop()

    assert process.poll() is not None and not worker.running


def test_a_child_that_cannot_start_reports_a_code() -> None:
    worker = host.PrepWorker(["/does/not/exist/python"])

    with pytest.raises(host.PrepWorkerError, match="SCENE_PREPARE_PROCESS_UNAVAILABLE"):
        worker.request("echo", {}, timeout=5)


def test_the_child_does_not_inherit_the_other_python_environment() -> None:
    env = host.child_environment(
        {"PYTHONPATH": "/opt/LTX-2/.venv/lib", "VIRTUAL_ENV": "/opt/LTX-2/.venv", "PYTHONHOME": "x", "HF_HUB_OFFLINE": "1"}
    )

    assert "PYTHONPATH" not in env and "VIRTUAL_ENV" not in env and "PYTHONHOME" not in env
    assert env["HF_HUB_OFFLINE"] == "1" and env["PYTHONUNBUFFERED"] == "1"


# ------------------------------------------------------------ the staged request
def _stage(root: Path, data: dict[str, Any]) -> tuple[str, int]:
    asset = json.dumps(data).encode("utf-8")
    manifest = json.dumps(
        {
            "schema_version": "sketch2life.modal.ai-request.v1",
            "asset": {
                "path": "input/request.json",
                "content_type": "application/json",
                "size_bytes": len(asset),
                "sha256": hashlib.sha256(asset).hexdigest(),
            },
        }
    ).encode("utf-8")
    (root / "input").mkdir(parents=True, exist_ok=True)
    (root / "input" / "request.json").write_bytes(asset)
    (root / "input" / "manifest.json").write_bytes(manifest)
    return hashlib.sha256(manifest).hexdigest(), len(asset) + len(manifest)


def _data(**changes: Any) -> dict[str, Any]:
    drawing = b"png-bytes"
    return {
        "scene_id": "scene-2",
        "scene_index": 2,
        "drawing_png_b64": base64.b64encode(drawing).decode("ascii"),
        "drawing_sha256": hashlib.sha256(drawing).hexdigest(),
        "main": {"entity_id": "e1", "label": "con gà", "box": [1, 2, 3, 4]},
        "secondaries": [],
        "staging": {"scenes": []},
        "plate_prompt": "p" * 2_000,
        "source_facing": "right",
        **changes,
    }


def test_the_staged_request_is_verified_and_split_into_drawing_and_fields(tmp_path: Path) -> None:
    digest, size = _stage(tmp_path, _data())

    drawing, fields = host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size)

    assert drawing == b"png-bytes"
    assert fields["scene_index"] == 2 and fields["main"]["entity_id"] == "e1"
    assert len(fields["plate_prompt"]) == 1_200
    assert "drawing_png_b64" not in fields


@pytest.mark.parametrize(
    "changes",
    [
        {"drawing_sha256": "0" * 64},
        {"drawing_png_b64": "not base64!"},
        {"secondaries": [{}] * 4},
        {"secondaries": "none"},
        {"scene_index": 0},
        {"scene_index": 16},
        {"main": None},
    ],
)
def test_an_invalid_request_is_refused(tmp_path: Path, changes: dict[str, Any]) -> None:
    digest, size = _stage(tmp_path, _data(**changes))

    with pytest.raises(ValueError, match="MODAL_INPUT_MANIFEST_INVALID"):
        host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size)


def test_a_changed_manifest_or_asset_is_refused(tmp_path: Path) -> None:
    digest, size = _stage(tmp_path, _data())

    with pytest.raises(ValueError, match="MODAL_INPUT_HASH_MISMATCH"):
        host.read_prepare_request(tmp_path, manifest_sha256="0" * 64, input_bytes=size)
    with pytest.raises(ValueError, match="MODAL_INPUT_HASH_MISMATCH"):
        host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size + 1)
    (tmp_path / "input" / "request.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="MODAL_INPUT_HASH_MISMATCH"):
        host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size)


def test_a_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="MODAL_INPUT_MANIFEST_MISSING"):
        host.read_prepare_request(tmp_path, manifest_sha256="0" * 64, input_bytes=1)


def test_a_repainted_background_uses_the_requested_seed(tmp_path: Path) -> None:
    digest, size = _stage(tmp_path, _data())
    assert host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size)[1]["plate_seed"] == 7

    digest, size = _stage(tmp_path, _data(plate_seed=1016))
    assert host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size)[1]["plate_seed"] == 1016

    for bad in (-1, 2**31, "x"):
        digest, size = _stage(tmp_path, _data(plate_seed=bad))
        with pytest.raises(ValueError, match="MODAL_INPUT_MANIFEST_INVALID"):
            host.read_prepare_request(tmp_path, manifest_sha256=digest, input_bytes=size)
