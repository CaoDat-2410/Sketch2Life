"""Look at a rendered scene with the Qwen worker (FEAT-094 phase 5, plan 7.3).

Two looks per scene. A local measure compares the border of every frame with the first one: the camera holds still and
the subject stays inside, so a large change there is something coming in (a hand, in the live runs) or a camera move.
The worker gets one picture sheet (the first frame and five moments) and answers with problem codes; this adapter passes
on only the known ones.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from sketch2life.application.video_pipeline.ports import SceneClip, VideoPipelineError
from sketch2life.infrastructure.ai.modal_function_client import APP_NAME, FUNCTION_NAME
from sketch2life.infrastructure.ai.modal_silent_story_video import (
    _ENVIRONMENT,
    _SCRATCH_VOLUME,
    _VOLUME_VERSION,
)

WORKLOAD: Final = "video.scene.validate"
PROBLEMS: Final = ("NEW_CHARACTER", "NEW_OBJECT", "SUBJECT_CHANGED", "STYLE_CHANGED", "TEXT_OR_LOGO")
EDGE_PROBLEM: Final = "EDGE_CHANGED"
GRID_WIDTH: Final = 16  # one grid cell is an 80x80 block of the 1280x720 picture
GRID_HEIGHT: Final = 9
# Measured on the fifteen scenes of three live learning videos: hands reached 98 and 111, other real intrusions 75 and
# 82; clean borders stayed at or under 23 and a slight camera sway at or under 45.
EDGE_LEVEL: Final = 60
EDGE_FRAMES: Final = 6  # a quarter of a second at 24 fps
_BORDER: Final = tuple(
    row * GRID_WIDTH + column
    for row in range(GRID_HEIGHT)
    for column in range(GRID_WIDTH)
    if row in (0, GRID_HEIGHT - 1) or column in (0, GRID_WIDTH - 1)
)
TIMEOUT_SECONDS: Final = 900.0
_FAILED: Final = "VIDEO_SCENE_CHECK_FAILED"


def edge_changed(grids: bytes) -> bool:
    """``grids`` holds one difference grid per frame; true when a border block stays very different long enough."""

    size = GRID_WIDTH * GRID_HEIGHT
    changed = sum(
        any(grids[start + cell] >= EDGE_LEVEL for cell in _BORDER) for start in range(0, len(grids) - size + 1, size)
    )
    return changed >= EDGE_FRAMES


def clip_edge_changed(clip: bytes) -> bool:
    graph = (
        "[0:v]crop=iw:min(ih\\,iw*9/16),scale=640:360,format=rgb24,split[a][b];"
        "[a]select='eq(n\\,0)',loop=loop=-1:size=1:start=0,setpts=N/24/TB[first];"
        "[b]setpts=N/24/TB[every];"
        "[every][first]blend=all_mode=difference:shortest=1,format=gray,"
        f"scale={GRID_WIDTH}:{GRID_HEIGHT}:flags=area[grid]"
    )
    with tempfile.TemporaryDirectory(prefix="sketch2life-edge-") as directory:
        video = Path(directory) / "clip.mp4"
        video.write_bytes(clip)
        done = subprocess.run(  # noqa: S603 - fixed arguments, temporary files
            ["ffmpeg", "-loglevel", "error", "-i", str(video), "-filter_complex", graph,
             "-map", "[grid]", "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"],
            capture_output=True,
            timeout=120,
            check=False,
        )
    if done.returncode != 0 or not done.stdout:
        raise VideoPipelineError(_FAILED)
    return edge_changed(done.stdout)


def picture_sheet(clip: bytes, keyframe_png: bytes, frames: int) -> bytes:
    """A 3x2 PNG: the given first frame, then the clip at each fifth up to the end."""

    last = max(0, frames - 1)
    moments = "+".join(f"eq(n\\,{last * step // 5})" for step in range(1, 6))
    graph = (
        "[0:v]scale=640:360,setsar=1[first];"
        f"[1:v]select='{moments}',scale=640:360,setsar=1[later];"
        "[first][later]concat=n=2:v=1:a=0,tile=3x2[sheet]"
    )
    with tempfile.TemporaryDirectory(prefix="sketch2life-check-") as directory:
        key, video, sheet = (Path(directory) / name for name in ("key.png", "clip.mp4", "sheet.png"))
        key.write_bytes(keyframe_png)
        video.write_bytes(clip)
        done = subprocess.run(  # noqa: S603 - fixed arguments, temporary files
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(key), "-i", str(video), "-filter_complex", graph,
             "-map", "[sheet]", "-frames:v", "1", str(sheet)],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if done.returncode != 0 or not sheet.is_file():
            raise VideoPipelineError(_FAILED)
        return sheet.read_bytes()


def pair_sheet(drawing_png: bytes, keyframe_png: bytes) -> bytes:
    """The child's drawing beside the composed first frame."""

    fit = "scale=640:384:force_original_aspect_ratio=decrease,pad=640:384:(ow-iw)/2:(oh-ih)/2:white,setsar=1"
    graph = f"[0:v]{fit}[drawing];[1:v]{fit}[frame];[drawing][frame]hstack[sheet]"
    with tempfile.TemporaryDirectory(prefix="sketch2life-check-") as directory:
        drawing, key, sheet = (Path(directory) / name for name in ("drawing.png", "key.png", "sheet.png"))
        drawing.write_bytes(drawing_png)
        key.write_bytes(keyframe_png)
        done = subprocess.run(  # noqa: S603 - fixed arguments, temporary files
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(drawing), "-i", str(key), "-filter_complex", graph,
             "-map", "[sheet]", "-frames:v", "1", str(sheet)],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if done.returncode != 0 or not sheet.is_file():
            raise VideoPipelineError(_FAILED)
        return sheet.read_bytes()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ModalSceneCheck:
    def __init__(
        self,
        *,
        volume: Any | None = None,
        function: Any | None = None,
        sheet: Callable[[bytes, bytes, int], bytes] = picture_sheet,
        edges: Callable[[bytes], bool] = clip_edge_changed,
        timeout_seconds: float = TIMEOUT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._volume = volume
        self._function = function
        self._sheet = sheet
        self._edges = edges
        self._timeout = timeout_seconds
        self._sleep = sleep

    def check(self, clip: SceneClip, keyframe_png: bytes) -> tuple[str, ...]:
        try:
            edge = (EDGE_PROBLEM,) if self._edges(clip.video) else ()
        except Exception:  # noqa: BLE001 - the model check still runs
            edge = ()
        try:
            return edge + self._ask(self._sheet(clip.video, keyframe_png, clip.frames))
        except Exception as error:  # noqa: BLE001 - provider detail never leaves this layer
            if edge:
                return edge
            if isinstance(error, VideoPipelineError):
                raise
            raise VideoPipelineError(_FAILED) from None

    def check_keyframe(self, drawing_png: bytes, keyframe_png: bytes) -> tuple[str, ...]:
        """What the painted first frame has that the drawing does not allow (plan 7.1)."""

        try:
            return self._ask(pair_sheet(drawing_png, keyframe_png), kind="keyframe")
        except VideoPipelineError:
            raise
        except Exception:  # noqa: BLE001
            raise VideoPipelineError(_FAILED) from None

    def _ask(self, sheet: bytes, **extra: str) -> tuple[str, ...]:
        request = _canonical(
            {
                "sheet_png_b64": base64.b64encode(sheet).decode("ascii"),
                "sheet_sha256": hashlib.sha256(sheet).hexdigest(),
                **extra,
            }
        )
        manifest = _canonical(
            {
                "schema_version": "sketch2life.modal.ai-request.v1",
                "asset": {
                    "path": "input/request.json",
                    "content_type": "application/json",
                    "size_bytes": len(request),
                    "sha256": hashlib.sha256(request).hexdigest(),
                },
            }
        )
        job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
        prefix = f"sketch2life/{_ENVIRONMENT}/{job_id}/{generation_id}/{attempt_id}/"
        with self._resolve_volume().batch_upload() as batch:
            batch.put_file(io.BytesIO(request), f"/{prefix}input/request.json")
            batch.put_file(io.BytesIO(manifest), f"/{prefix}input/manifest.json")
        call = self._resolve_function().spawn(
            {
                "schema_version": "sketch2life.modal.worker-input.v1",
                "environment": _ENVIRONMENT,
                "workload": WORKLOAD,
                "job_id": job_id,
                "generation_id": generation_id,
                "attempt_id": attempt_id,
                "attempt_prefix": prefix,
                "input_manifest_ref": "input/manifest.json",
                "input_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                "input_bytes": len(request) + len(manifest),
            }
        )
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                result = call.get(timeout=0)
                break
            except TimeoutError:
                if time.monotonic() >= deadline:
                    raise VideoPipelineError(_FAILED) from None
                self._sleep(3.0)
        check = result.get("check") if isinstance(result, dict) else None
        if (
            not isinstance(check, dict)
            or result.get("job_id") != job_id
            or result.get("attempt_id") != attempt_id
            or not isinstance(check.get("problems"), list)
        ):
            raise VideoPipelineError(_FAILED)
        return tuple(item for item in check["problems"] if item in PROBLEMS)

    def _resolve_volume(self) -> Any:
        if self._volume is None:
            import modal

            self._volume = modal.Volume.from_name(_SCRATCH_VOLUME, environment_name=_ENVIRONMENT, version=_VOLUME_VERSION)
        return self._volume

    def _resolve_function(self) -> Any:
        if self._function is None:
            import modal

            self._function = modal.Function.from_name(APP_NAME, FUNCTION_NAME, environment_name=_ENVIRONMENT)
        return self._function


__all__ = [
    "EDGE_PROBLEM",
    "ModalSceneCheck",
    "PROBLEMS",
    "clip_edge_changed",
    "edge_changed",
    "pair_sheet",
    "picture_sheet",
]
