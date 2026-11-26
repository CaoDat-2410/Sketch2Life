"""C1 adapter: render one scene with LTX-2.5 through the deployed ``generate-video-scene`` function (FEAT-093).

C1 never runs anything else. The prepared keyframe is staged as the scene's source drawing together with a manifest; the
call blocks until the clip exists (the video worker process runs this outside any request) and the clip is read back
from the scratch volume. Nothing provider-specific reaches the caller: failures are ``VideoPipelineError`` codes.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import uuid
from collections.abc import Callable
from typing import Any, Final

from sketch2life.application.video_pipeline.age_profile import FPS
from sketch2life.application.video_pipeline.ports import (
    SceneClip,
    SceneRenderJob,
    VideoPipelineError,
)
from sketch2life.infrastructure.ai.modal_silent_story_video import (
    _ENVIRONMENT,
    _MAX_MANIFEST_BYTES,
    _MAX_OUTPUT_BYTES,
    _SCRATCH_VOLUME,
    _VOLUME_VERSION,
    _read_volume_file,
)

APP_NAME: Final = "sketch2life-srs23-dev-video"
FUNCTION_NAME: Final = "generate-video-scene"
INPUT_SCHEMA: Final = "sketch2life.modal.video-scene-input.v1"
WORKER_INPUT_SCHEMA: Final = "sketch2life.modal.worker-input.v1"
OUTPUT_SCHEMA: Final = "sketch2life.modal.video-scene-output.v1"
WORKLOAD: Final = "video.scene.generate"
WAIT_TIMEOUT_SECONDS: Final = 2_700  # queue behind the warm-up plus a cold start


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ModalSceneRenderer:
    """``SceneRenderPort`` on the LTX container."""

    def __init__(
        self,
        *,
        volume: Any | None = None,
        function: Any | None = None,
        storyboard_sha256: str = "0" * 64,
        scene_count: int = 5,
        timeout_seconds: float = WAIT_TIMEOUT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._volume = volume
        self._function = function
        self._storyboard_sha256 = storyboard_sha256
        self._scene_count = scene_count
        self._timeout = timeout_seconds
        self._sleep = sleep

    def for_plan(self, *, storyboard_sha256: str, scene_count: int) -> ModalSceneRenderer:
        return ModalSceneRenderer(
            volume=self._volume,
            function=self._function,
            storyboard_sha256=storyboard_sha256,
            scene_count=scene_count,
            timeout_seconds=self._timeout,
            sleep=self._sleep,
        )

    def warm_up(self) -> None:
        """Ask Modal to start the render container and load the model; a dispatch failure only costs time."""

        try:
            self._resolve_function().spawn({"warmup": True})
        except Exception:  # noqa: BLE001
            return

    def prime(self, prompts: list[str]) -> None:
        """Let the render container encode all scene prompts at once; it queues ahead of the first scene."""

        payload = {"warmup": True, "prompts": [prompt[:1_200] for prompt in prompts]}
        try:
            self._resolve_function().spawn(payload)
        except Exception:  # noqa: BLE001 - only a speed-up, a scene encodes its own prompt otherwise
            return

    def render(self, job: SceneRenderJob) -> SceneClip:
        scene = job.scene
        keyframe = job.keyframe_png
        if not keyframe or len(keyframe) > 20 * 1024 * 1024:
            raise VideoPipelineError("VIDEO_KEYFRAME_INVALID")
        manifest = {
            "schema_version": INPUT_SCHEMA,
            "scene_id": scene.scene_id,
            "scene_index": scene.index,
            "scene_count": job.scene_count or self._scene_count,
            "purpose": "SYNTHETIC_END_TO_END",
            "storyboard_sha256": job.storyboard_sha256 or self._storyboard_sha256,
            "source_drawing_ref": "input/drawing.png",
            "source_drawing_sha256": hashlib.sha256(keyframe).hexdigest(),
            "visual_prompt": scene.visual_prompt[:1_200],
            "target_duration_seconds": scene.target_frames / FPS,
            "seed": scene.seed,
        }
        manifest_bytes = _canonical(manifest)
        if len(manifest_bytes) > _MAX_MANIFEST_BYTES:
            raise VideoPipelineError("VIDEO_SCENE_MANIFEST_TOO_LARGE")
        job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
        prefix = f"sketch2life/{_ENVIRONMENT}/{job_id}/{generation_id}/{attempt_id}/"
        worker_input = {
            "schema_version": WORKER_INPUT_SCHEMA,
            "environment": _ENVIRONMENT,
            "workload": WORKLOAD,
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "attempt_prefix": prefix,
            "input_manifest_ref": "input/manifest.json",
            "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "input_bytes": len(keyframe) + len(manifest_bytes),
        }
        volume = self._resolve_volume()
        try:
            with volume.batch_upload() as batch:
                batch.put_file(io.BytesIO(keyframe), f"/{prefix}input/drawing.png")
                batch.put_file(io.BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
        except Exception:  # noqa: BLE001 - provider detail never leaves this layer
            raise VideoPipelineError("VIDEO_SCENE_STAGING_FAILED") from None
        try:
            call = self._resolve_function().spawn(worker_input)
        except Exception:  # noqa: BLE001
            raise VideoPipelineError("VIDEO_SCENE_DISPATCH_UNKNOWN") from None

        deadline = time.monotonic() + self._timeout
        result: Any = None
        while True:
            try:
                result = call.get(timeout=0)
                break
            except TimeoutError:
                if time.monotonic() >= deadline:
                    raise VideoPipelineError("VIDEO_SCENE_TIMEOUT") from None
                self._sleep(5.0)
            except Exception:  # noqa: BLE001
                raise VideoPipelineError("VIDEO_SCENE_RENDER_FAILED") from None
        if (
            not isinstance(result, dict)
            or result.get("schema_version") != OUTPUT_SCHEMA
            or result.get("job_id") != job_id
            or result.get("generation_id") != generation_id
            or result.get("attempt_id") != attempt_id
            or result.get("scene_id") != scene.scene_id
        ):
            raise VideoPipelineError("VIDEO_SCENE_OUTPUT_INVALID")
        try:
            clip = _read_volume_file(volume, f"{prefix}output/scene.mp4", maximum_bytes=_MAX_OUTPUT_BYTES)
        except Exception:  # noqa: BLE001
            raise VideoPipelineError("VIDEO_SCENE_OUTPUT_UNAVAILABLE") from None
        if hashlib.sha256(clip).hexdigest() != result.get("output_sha256"):
            raise VideoPipelineError("VIDEO_SCENE_OUTPUT_HASH_MISMATCH")
        return SceneClip(scene_index=scene.index, video=clip, frames=scene.target_frames)

    def _resolve_volume(self) -> Any:
        if self._volume is None:
            import modal

            self._volume = modal.Volume.from_name(
                _SCRATCH_VOLUME, environment_name=_ENVIRONMENT, version=_VOLUME_VERSION
            )
        return self._volume

    def _resolve_function(self) -> Any:
        if self._function is None:
            import modal

            self._function = modal.Function.from_name(APP_NAME, FUNCTION_NAME, environment_name=_ENVIRONMENT)
        return self._function


__all__ = ["ModalSceneRenderer"]
