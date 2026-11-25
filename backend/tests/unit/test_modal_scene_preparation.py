"""FEAT-093: the C2 scene-preparation adapter stages the drawing and request, verifies the keyframe."""

from __future__ import annotations

import hashlib
import io
import json
from contextlib import contextmanager

import pytest

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.ports import ScenePrepJob, VideoPipelineError
from sketch2life.application.video_pipeline.story_timeline import parse_timeline
from sketch2life.application.video_pipeline.timeline_planner import assign_timing
from sketch2life.application.video_pipeline.video_plan import build_video_plan
from sketch2life.infrastructure.story_video.modal_scene_preparation import OUTPUT_SCHEMA, ModalScenePreparation

KEYFRAME = b"\x89PNG-keyframe" * 50


def _scene():
    profile = profile_for_age_months(48)
    scenes = [
        {"title": f"Cảnh {i}", "action": "Rùa đi.", "visual_prompt": "A turtle walks, crayon style.",
         "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.", "dialogue": [],
         "subjects": ["main", "sec-1"], "interactions": []}
        for i in range(1, 6)
    ]
    timeline = parse_timeline(
        assign_timing(profile, {"title": "Rùa con", "scenes": scenes}), profile=profile, entity_ids={"main", "sec-1"}
    )
    return build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main").scenes[0]


def _job(**override):
    values = dict(
        scene=_scene(), drawing_sha256="b" * 64, subject_labels={"main": "con rùa", "sec-1": "chiếc lá"},
        subject_boxes={"main": (2, 6, 11, 17), "sec-1": (13, 9, 19, 15)}, main_entity_id="main",
        drawing_png=b"drawing-bytes", staging={"schema_version": "sketch2life.story-staging.v1", "scenes": []},
        secondary_ids=("sec-1",),
    )
    values.update(override)
    return ScenePrepJob(**values)


class _Batch:
    def __init__(self, files):
        self.files = files

    def put_file(self, stream, path):
        self.files[path] = stream.getvalue()


class _Volume:
    def __init__(self):
        self.files = {}

    @contextmanager
    def batch_upload(self):
        yield _Batch(self.files)

    def read_file(self, path):
        yield self.files[path if path in self.files else "/" + path.lstrip("/")]


class _Call:
    def __init__(self, volume, worker_input, *, error=None, tamper=None, background="AI"):
        self.volume, self.input, self.error, self.tamper, self.background = volume, worker_input, error, tamper, background

    def get(self, timeout):
        if self.error:
            raise self.error
        self.volume.files[f"/{self.input['attempt_prefix']}output/keyframe.png"] = KEYFRAME
        result = {
            "schema_version": OUTPUT_SCHEMA, "job_id": self.input["job_id"], "attempt_id": self.input["attempt_id"],
            "scene_id": "scene-1", "background": self.background, "output_sha256": hashlib.sha256(KEYFRAME).hexdigest(),
        }
        result.update(self.tamper or {})
        return result


class _Function:
    def __init__(self, volume, **kwargs):
        self.volume, self.kwargs, self.inputs = volume, kwargs, []

    def spawn(self, worker_input):
        self.inputs.append(worker_input)
        return _Call(self.volume, worker_input, **self.kwargs)


def _adapter(**kwargs):
    volume = _Volume()
    function = _Function(volume, **kwargs)
    return ModalScenePreparation(volume=volume, function=function, sleep=lambda _s: None), volume, function


def test_the_request_is_staged_and_the_keyframe_returned() -> None:
    adapter, volume, function = _adapter()

    prepared = adapter.prepare(_job())

    assert prepared.keyframe_png == KEYFRAME and prepared.background == "AI"
    prefix = function.inputs[0]["attempt_prefix"]
    manifest = json.loads(volume.files[f"/{prefix}input/manifest.json"])
    assert manifest["main"]["box"] == [2, 6, 11, 17] and manifest["secondaries"][0]["entity_id"] == "sec-1"
    assert manifest["plate_prompt"].startswith("A sunny garden")
    assert manifest["source_drawing_sha256"] == hashlib.sha256(b"drawing-bytes").hexdigest()
    assert volume.files[f"/{prefix}input/drawing.png"] == b"drawing-bytes"


def test_a_paper_fallback_is_reported_not_hidden() -> None:
    assert _adapter(background="PAPER")[0].prepare(_job()).background == "PAPER"


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"error": RuntimeError("x")}, "VIDEO_SCENE_PREPARE_FAILED"),
        ({"tamper": {"background": "WEIRD"}}, "VIDEO_SCENE_PREPARE_OUTPUT_INVALID"),
        ({"tamper": {"output_sha256": "0" * 64}}, "VIDEO_SCENE_PREPARE_HASH_MISMATCH"),
    ],
)
def test_failures_become_safe_codes(kwargs, code) -> None:
    with pytest.raises(VideoPipelineError) as error:
        _adapter(**kwargs)[0].prepare(_job())
    assert error.value.code == code


def test_a_job_without_the_drawing_or_staging_is_rejected() -> None:
    for bad in (_job(drawing_png=b""), _job(staging=None)):
        with pytest.raises(VideoPipelineError) as error:
            _adapter()[0].prepare(bad)
        assert error.value.code == "VIDEO_SCENE_PREPARE_INPUT_INVALID"
