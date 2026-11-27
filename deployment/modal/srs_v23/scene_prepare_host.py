"""FEAT-094 phase 2: run scene preparation as a child process of the video container (ADR-0026).

Preparation (FLUX and SAM) and rendering (LTX-2.5) need different package versions and cannot hold the GPU together, so
preparation runs in its own interpreter. Ending the child gives all of its GPU memory back.

Protocol: one JSON object per line on the child's stdin; the child answers with one line that starts with
``REPLY_PREFIX``. Every other output line is library noise and is passed to the log.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import queue
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

REPLY_PREFIX = "@@SCENE_PREPARE@@ "
MANIFEST_SCHEMA = "sketch2life.modal.ai-request.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_DRAWING_BYTES = 20 * 1024 * 1024
MAX_PLATE_PROMPT_CHARS = 1_200
DEFAULT_PLATE_SEED = 7
MAX_SECONDARIES = 3
MAX_SCENES = 15
_ASSET_PATH = "input/request.json"
_OTHER_ENVIRONMENT = ("PYTHONPATH", "VIRTUAL_ENV", "PYTHONHOME")


class PrepWorkerError(RuntimeError):
    """Content-free preparation failure; the message is a code."""


def child_environment(base: Mapping[str, str]) -> dict[str, str]:
    """The container environment without the renderer's Python paths."""

    environment = {name: value for name, value in base.items() if name not in _OTHER_ENVIRONMENT}
    environment["PYTHONUNBUFFERED"] = "1"
    return environment


class PrepWorker:
    """One child process, started on the first request and kept until ``stop`` so that models load once."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        echo: Callable[[str], None] = lambda line: print(line, flush=True),
    ) -> None:
        self._command = list(command)
        self._env = dict(env) if env is not None else None
        self._echo = echo
        self._process: subprocess.Popen[str] | None = None
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._next_id = 0

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def request(self, op: str, body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        if not self.running:
            self._start()
        assert self._process is not None and self._process.stdin is not None
        self._next_id += 1
        try:
            self._process.stdin.write(json.dumps({"id": self._next_id, "op": op, "body": body}) + "\n")
            self._process.stdin.flush()
        except (OSError, ValueError):
            self.stop()
            raise PrepWorkerError("SCENE_PREPARE_PROCESS_EXITED") from None
        reply = self._reply(self._next_id, timeout)
        if reply.get("ok") is not True:
            raise PrepWorkerError(str(reply.get("error") or "SCENE_PREPARE_UNEXPECTED_ERROR"))
        result = reply.get("result")
        return result if isinstance(result, dict) else {}

    def stop(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        for step in (process.terminate, process.kill):
            if process.poll() is not None:
                break
            step()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                continue
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass

    def _start(self) -> None:
        self.stop()
        try:
            process = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=self._env,
            )
        except OSError:
            raise PrepWorkerError("SCENE_PREPARE_PROCESS_UNAVAILABLE") from None
        lines: queue.Queue[str | None] = queue.Queue()

        def read() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                lines.put(line.rstrip("\n"))
            lines.put(None)
            process.stdout.close()

        threading.Thread(target=read, name="scene-prepare-output", daemon=True).start()
        self._process, self._lines = process, lines

    def _reply(self, request_id: int, timeout: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            try:
                line = self._lines.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty:
                self.stop()
                raise PrepWorkerError("SCENE_PREPARE_TIMEOUT") from None
            if line is None:
                self.stop()
                raise PrepWorkerError("SCENE_PREPARE_PROCESS_EXITED")
            if not line.startswith(REPLY_PREFIX):
                if line:
                    self._echo(line)
                continue
            try:
                reply = json.loads(line[len(REPLY_PREFIX) :])
            except json.JSONDecodeError:
                continue
            if isinstance(reply, dict) and reply.get("id") == request_id:
                return reply


def read_prepare_request(attempt_root: Path, *, manifest_sha256: str, input_bytes: int) -> tuple[bytes, dict[str, Any]]:
    """Verify the staged manifest and asset; returns the drawing and the fields the child needs."""

    try:
        manifest_bytes = (attempt_root / "input" / "manifest.json").read_bytes()
    except OSError:
        raise ValueError("MODAL_INPUT_MANIFEST_MISSING") from None
    if len(manifest_bytes) > MAX_MANIFEST_BYTES or hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256:
        raise ValueError("MODAL_INPUT_HASH_MISMATCH")
    try:
        manifest = json.loads(manifest_bytes)
        asset = manifest["asset"]
        if manifest["schema_version"] != MANIFEST_SCHEMA or asset["path"] != _ASSET_PATH:
            raise ValueError("schema")
    except (ValueError, KeyError, TypeError):
        raise ValueError("MODAL_INPUT_MANIFEST_INVALID") from None
    try:
        raw = (attempt_root / _ASSET_PATH).read_bytes()
    except OSError:
        raise ValueError("MODAL_INPUT_ASSET_MISSING") from None
    if (
        asset.get("size_bytes") != len(raw)
        or asset.get("sha256") != hashlib.sha256(raw).hexdigest()
        or input_bytes != len(raw) + len(manifest_bytes)
    ):
        raise ValueError("MODAL_INPUT_HASH_MISMATCH")
    try:
        data = json.loads(raw)
        drawing = base64.b64decode(data["drawing_png_b64"], validate=True)
        if hashlib.sha256(drawing).hexdigest() != data["drawing_sha256"] or len(drawing) > MAX_DRAWING_BYTES:
            raise ValueError("drawing")
        secondaries = data["secondaries"]
        scene_index = int(data["scene_index"])
        fields = {
            "scene_index": scene_index,
            "main": data["main"],
            "secondaries": secondaries,
            "staging": data["staging"],
            "plate_prompt": str(data["plate_prompt"])[:MAX_PLATE_PROMPT_CHARS],
            "source_facing": str(data.get("source_facing", "right")),
            "plate_seed": int(data.get("plate_seed", DEFAULT_PLATE_SEED)),
        }
        if (
            not isinstance(fields["main"], dict)
            or not isinstance(secondaries, list)
            or len(secondaries) > MAX_SECONDARIES
            or not 1 <= scene_index <= MAX_SCENES
            or not 0 <= fields["plate_seed"] < 2**31
        ):
            raise ValueError("shape")
    except (KeyError, ValueError, TypeError, binascii.Error):
        raise ValueError("MODAL_INPUT_MANIFEST_INVALID") from None
    return drawing, fields


__all__ = ["REPLY_PREFIX", "PrepWorker", "PrepWorkerError", "child_environment", "read_prepare_request"]
