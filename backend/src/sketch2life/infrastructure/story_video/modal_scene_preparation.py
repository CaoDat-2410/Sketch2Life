"""C2 adapter: prepare one scene's keyframe (child's subjects over a crayon background plate) (FEAT-093).

Implements ``ScenePreparationPort`` against the ``prepare-video-scene`` function. The drawing and a request manifest are
staged on the scratch volume, the call is awaited, and the keyframe PNG is read back and verified. The worker degrades to
the paper background by itself; this adapter only maps transport failures to ``VideoPipelineError`` codes.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import uuid
from collections.abc import Callable
from typing import Any, Final

from sketch2life.application.video_pipeline.ports import PreparedScene, ScenePrepJob, VideoPipelineError
from sketch2life.infrastructure.ai.modal_silent_story_video import (
    _ENVIRONMENT,
    _MAX_OUTPUT_BYTES,
    _SCRATCH_VOLUME,
    _VOLUME_VERSION,
    _read_volume_file,
)

APP_NAME: Final = "sketch2life-srs23-dev-video"
FUNCTION_NAME: Final = "prepare-video-scene"
INPUT_SCHEMA: Final = "sketch2life.modal.video-scene-prepare-input.v1"
OUTPUT_SCHEMA: Final = "sketch2life.modal.video-scene-prepare-output.v1"
WORKER_INPUT_SCHEMA: Final = "sketch2life.modal.worker-input.v1"
WORKLOAD: Final = "video.scene.prepare"
WAIT_TIMEOUT_SECONDS: Final = 600
BACKGROUNDS: Final = frozenset({"AI", "PAPER"})


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ModalScenePreparation:
    def __init__(
        self,
        *,
        volume: Any | None = None,
        function: Any | None = None,
        timeout_seconds: float = WAIT_TIMEOUT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._volume = volume
        self._function = function
        self._timeout = timeout_seconds
        self._sleep = sleep

    def prepare(self, job: ScenePrepJob) -> PreparedScene:
        if not job.drawing_png or job.staging is None:
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_INPUT_INVALID")
        scene = job.scene
        entities = [
            {"entity_id": entity_id, "label": job.subject_labels.get(entity_id, ""), "box": list(job.subject_boxes[entity_id])}
            for entity_id in (job.main_entity_id, *job.secondary_ids)
        ]
        manifest = {
            "schema_version": INPUT_SCHEMA,
            "scene_id": scene.scene_id,
            "scene_index": scene.index,
            "source_drawing_ref": "input/drawing.png",
            "source_drawing_sha256": hashlib.sha256(job.drawing_png).hexdigest(),
            "main": entities[0],
            "secondaries": entities[1:],
            "staging": job.staging,
            "plate_prompt": scene.background_prompt[:1_200],
            "source_facing": "right",
        }
        manifest_bytes = _canonical(manifest)
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
            "input_bytes": len(job.drawing_png) + len(manifest_bytes),
        }
        volume = self._resolve_volume()
        try:
            with volume.batch_upload() as batch:
                batch.put_file(io.BytesIO(job.drawing_png), f"/{prefix}input/drawing.png")
                batch.put_file(io.BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
        except Exception:  # noqa: BLE001 - provider detail never leaves this layer
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_STAGING_FAILED") from None
        try:
            call = self._resolve_function().spawn(worker_input)
        except Exception:  # noqa: BLE001
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_DISPATCH_UNKNOWN") from None
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                result = call.get(timeout=0)
                break
            except TimeoutError:
                if time.monotonic() >= deadline:
                    raise VideoPipelineError("VIDEO_SCENE_PREPARE_TIMEOUT") from None
                self._sleep(3.0)
            except Exception:  # noqa: BLE001
                raise VideoPipelineError("VIDEO_SCENE_PREPARE_FAILED") from None
        if (
            not isinstance(result, dict)
            or result.get("schema_version") != OUTPUT_SCHEMA
            or result.get("job_id") != job_id
            or result.get("attempt_id") != attempt_id
            or result.get("scene_id") != scene.scene_id
            or result.get("background") not in BACKGROUNDS
        ):
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_OUTPUT_INVALID")
        try:
            keyframe = _read_volume_file(volume, f"{prefix}output/keyframe.png", maximum_bytes=_MAX_OUTPUT_BYTES)
        except Exception:  # noqa: BLE001
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_OUTPUT_UNAVAILABLE") from None
        if hashlib.sha256(keyframe).hexdigest() != result.get("output_sha256"):
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_HASH_MISMATCH")
        return PreparedScene(keyframe_png=keyframe, background=result["background"])

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


__all__ = ["ModalScenePreparation"]
