"""FEAT-093 block D: the C1 scene renderer stages inputs, waits, verifies and reads the clip."""

from __future__ import annotations

import hashlib
import io
import json
from contextlib import contextmanager

import pytest

from sketch2life.application.video_pipeline.ports import SceneRenderJob, VideoPipelineError
from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.story_timeline import parse_timeline
from sketch2life.application.video_pipeline.timeline_planner import assign_timing
from sketch2life.application.video_pipeline.video_plan import build_video_plan
from sketch2life.infrastructure.story_video.modal_scene_renderer import (
    INPUT_SCHEMA,
    OUTPUT_SCHEMA,
    ModalSceneRenderer,
)

CLIP = b"fake-mp4-bytes" * 100


def _scene():
    profile = profile_for_age_months(48)
    scenes = [
        {
            "title": f"Cảnh {i}", "action": "Rùa đi.", "visual_prompt": "A small turtle walks on grass, crayon style.",
            "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.", "dialogue": [],
            "subjects": ["main"], "interactions": [],
        }
        for i in range(1, 6)
    ]
    timeline = parse_timeline(
        assign_timing(profile, {"title": "Rùa con", "scenes": scenes}), profile=profile, entity_ids={"main"}
    )
    return build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main").scenes[0]


class _Batch:
    def __init__(self, files):
        self.files = files

    def put_file(self, stream: io.BytesIO, path: str) -> None:
        self.files[path] = stream.getvalue()


class _Volume:
    def __init__(self, fail_upload=False):
        self.files: dict[str, bytes] = {}
        self.fail_upload = fail_upload

    @contextmanager
    def batch_upload(self):
        if self.fail_upload:
            raise OSError("boom")
        yield _Batch(self.files)

    def read_file(self, path: str):
        yield self.files[path.lstrip("/")] if path.lstrip("/") in self.files else self.files["/" + path.lstrip("/")]


class _Call:
    def __init__(self, volume, worker_input, *, pending=1, error=None, tamper=None):
        self.volume, self.input, self.pending, self.error, self.tamper = volume, worker_input, pending, error, tamper

    def get(self, timeout):
        assert timeout == 0
        if self.pending > 0:
            self.pending -= 1
            raise TimeoutError
        if self.error is not None:
            raise self.error
        prefix = self.input["attempt_prefix"]
        self.volume.files[f"/{prefix}output/scene.mp4"] = CLIP
        result = {
            "schema_version": OUTPUT_SCHEMA, "job_id": self.input["job_id"], "generation_id": self.input["generation_id"],
            "attempt_id": self.input["attempt_id"], "scene_id": "scene-1", "output_sha256": hashlib.sha256(CLIP).hexdigest(),
        }
        if self.tamper:
            result.update(self.tamper)
        return result


class _Function:
    def __init__(self, volume, **call_kwargs):
        self.volume, self.call_kwargs, self.inputs = volume, call_kwargs, []

    def spawn(self, worker_input):
        self.inputs.append(worker_input)
        return _Call(self.volume, worker_input, **self.call_kwargs)


def _renderer(volume=None, **call_kwargs):
    volume = volume or _Volume()
    function = _Function(volume, **call_kwargs)
    return ModalSceneRenderer(volume=volume, function=function, storyboard_sha256="b" * 64, scene_count=5,
                              sleep=lambda _s: None), volume, function


def test_the_clip_is_staged_rendered_verified_and_returned() -> None:
    renderer, volume, function = _renderer()
    scene = _scene()

    clip = renderer.render(SceneRenderJob(scene=scene, keyframe_png=b"keyframe-png"))

    assert clip.video == CLIP and clip.scene_index == 1 and clip.frames == scene.target_frames
    worker_input = function.inputs[0]
    prefix = worker_input["attempt_prefix"]
    manifest = json.loads(volume.files[f"/{prefix}input/manifest.json"])
    assert manifest["schema_version"] == INPUT_SCHEMA and manifest["scene_id"] == "scene-1"
    assert manifest["source_drawing_sha256"] == hashlib.sha256(b"keyframe-png").hexdigest()
    assert manifest["target_duration_seconds"] == scene.target_frames / 24 and manifest["scene_count"] == 5
    assert manifest["end_guide_strength"] == 0.7
    assert volume.files[f"/{prefix}input/drawing.png"] == b"keyframe-png"
    assert worker_input["input_bytes"] == len(b"keyframe-png") + len(volume.files[f"/{prefix}input/manifest.json"])
    assert worker_input["workload"] == "video.scene.generate"


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"error": RuntimeError("worker crashed")}, "VIDEO_SCENE_RENDER_FAILED"),
        ({"tamper": {"job_id": "other"}}, "VIDEO_SCENE_OUTPUT_INVALID"),
        ({"tamper": {"output_sha256": "0" * 64}}, "VIDEO_SCENE_OUTPUT_HASH_MISMATCH"),
    ],
)
def test_failures_become_safe_codes(kwargs, code) -> None:
    renderer, _volume, _function = _renderer(**kwargs)

    with pytest.raises(VideoPipelineError) as error:
        renderer.render(SceneRenderJob(scene=_scene(), keyframe_png=b"k"))

    assert error.value.code == code


def test_staging_failure_and_empty_keyframe_are_reported() -> None:
    renderer, _v, _f = _renderer(_Volume(fail_upload=True))
    with pytest.raises(VideoPipelineError) as error:
        renderer.render(SceneRenderJob(scene=_scene(), keyframe_png=b"k"))
    assert error.value.code == "VIDEO_SCENE_STAGING_FAILED"

    with pytest.raises(VideoPipelineError) as empty:
        _renderer()[0].render(SceneRenderJob(scene=_scene(), keyframe_png=b""))
    assert empty.value.code == "VIDEO_KEYFRAME_INVALID"


def test_a_call_that_never_finishes_times_out() -> None:
    renderer = ModalSceneRenderer(
        volume=_Volume(), function=_Function(_Volume(), pending=10**6), timeout_seconds=0.0, sleep=lambda _s: None
    )

    with pytest.raises(VideoPipelineError) as error:
        renderer.render(SceneRenderJob(scene=_scene(), keyframe_png=b"k"))

    assert error.value.code == "VIDEO_SCENE_TIMEOUT"
