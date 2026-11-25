"""FEAT-093 block C: the orchestrator with fake ports (two containers, pipelining, narration, captions)."""

from __future__ import annotations

import copy
import io
import math
import struct
import threading
import wave

import pytest

from sketch2life.application.video_pipeline.orchestrator import (
    STAGE_ASSEMBLING,
    STAGE_CHECKING,
    STAGE_PLANNING,
    STAGE_PREPARING,
    STAGE_RENDERING,
    VideoPipeline,
)
from sketch2life.application.video_pipeline.ports import (
    PreparedScene,
    SceneClip,
    ValidationReport,
    VideoPipelineCancelled,
    VideoPipelineError,
    VideoSource,
)
from sketch2life.application.video_pipeline.timeline_planner import PlannerSubject

SUBJECTS = (PlannerSubject("main", "con rùa", "main"), PlannerSubject("sec-1", "chiếc lá", "secondary"))


def _draft() -> dict:
    texts = [
        "Rùa con bò ra khỏi hang.",
        "Rùa thấy một chiếc lá xanh.",
        "Rùa cắn một miếng lá.",
        "Chiếc lá còn một nửa.",
        "Rùa ăn xong và mỉm cười.",
    ]
    ladders = [None, None, (1.0, 0.5), (0.5, 0.25), (0.25, 0.0)]
    scenes = []
    for index, text in enumerate(texts):
        step = ladders[index]
        scenes.append(
            {
                "title": f"Cảnh {index + 1}",
                "action": "Rùa con đi tìm thức ăn.",
                "visual_prompt": "A small turtle walks on green grass and looks at a leaf, crayon style.",
                "background_prompt": "A sunny garden with soft green hills, crayon texture, no characters.",
                "narration": text,
                "dialogue": [],
                "subjects": ["main", "sec-1"],
                "interactions": (
                    [
                        {
                            "kind": "consume", "actor": "main", "target": "sec-1", "verb": "ăn",
                            "from_state": step[0], "to_state": step[1],
                        }
                    ]
                    if step
                    else []
                ),
            }
        )
    return {"title": "Rùa con và chiếc lá", "scenes": scenes}


def _wav(seconds: float, rate: int = 24_000) -> bytes:
    frames = bytearray()
    lead, tail = int(rate * 0.05), int(rate * 0.05)
    voiced = int(rate * seconds)
    for i in range(lead + voiced + tail):
        voice = lead <= i < lead + voiced
        frames += struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / rate)) if voice else 0)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(bytes(frames))
    return buffer.getvalue()


class _Generator:
    def __init__(self, draft):
        self.draft = draft

    def generate(self, request):
        return copy.deepcopy(self.draft)


class _Prep:
    def __init__(self):
        self.calls = []
        self.events = {i: threading.Event() for i in range(1, 10)}

    def prepare(self, job):
        self.calls.append((job.scene.index, threading.current_thread().name))
        self.events[job.scene.index].set()
        return PreparedScene(keyframe_png=b"png", background="AI")


class _Render:
    def __init__(self, prep=None):
        self.calls = []
        self.prep = prep

    def render(self, job):
        self.calls.append((job.scene.index, threading.current_thread().name))
        if job.scene.index == 1 and self.prep is not None:
            # proves C2 prepares scene 2 while C1 is still rendering scene 1
            assert self.prep.events[2].wait(5), "scene 2 was not prepared while scene 1 rendered"
        return SceneClip(job.scene.index, b"clip", job.scene.model_frames)


class _Narration:
    def __init__(self, seconds_per_letter=0.1, fail_first=False):
        self.calls = []
        self.rate = seconds_per_letter
        self.fail_first = fail_first

    def synthesize(self, spoken):
        self.calls.append(spoken)
        if self.fail_first and len(self.calls) == 1:
            return b"not a wav"
        return _wav(max(0.6, sum(ch.isalnum() for ch in spoken) * self.rate))


class _Assembler:
    def __init__(self):
        self.job = None

    def assemble(self, job):
        self.job = job
        return b"MP4-" + str(len(job.clips)).encode()


class _Validator:
    def __init__(self, report=None):
        self.report = report or ValidationReport()

    def validate(self, video, plan):
        return self.report


def _source(subjects=SUBJECTS) -> VideoSource:
    return VideoSource(
        run_id="r1", story_sha256="a" * 64, story={"title": "Rùa con"}, topic="Động vật", age_months=48,
        subjects=subjects, activity={"title": "Tìm lá", "objective": "Quan sát lá"}, drawing_png=b"png",
        drawing_sha256="b" * 64, subject_boxes={"main": (3, 6, 14, 17), "sec-1": (14, 9, 19, 15)},
    )


def _pipeline(draft=None, *, prep=None, render=None, narration=None, assembler=None, validator=None):
    prep = prep or _Prep()
    pipeline = VideoPipeline(
        timeline_generator=_Generator(draft or _draft()),
        preparation=prep,
        renderer=render or _Render(),
        narration=narration or _Narration(),
        assembler=assembler or _Assembler(),
        validator=validator or _Validator(),
    )
    return pipeline, prep


def test_the_happy_path_returns_video_cues_and_a_frame_exact_plan() -> None:
    assembler = _Assembler()
    pipeline, _prep = _pipeline(assembler=assembler)

    result = pipeline.run(_source())

    assert result.video == b"MP4-5"
    assert result.plan.total_frames == 720 and result.plan.total_ms == 30_000
    assert result.captions_vtt.startswith("WEBVTT") and len(result.cues) >= 5
    assert [clip.scene_index for clip in assembler.job.clips] == [1, 2, 3, 4, 5]
    assert all(chunk.duration_ms > 0 for chunk in assembler.job.chunks)
    assert set(result.backgrounds.values()) == {"AI"}


def test_c1_only_renders_and_c2_prepares_scene_two_while_scene_one_renders() -> None:
    prep = _Prep()
    render = _Render(prep)
    pipeline, _ = _pipeline(prep=prep, render=render)

    pipeline.run(_source())

    assert [index for index, _thread in render.calls] == [1, 2, 3, 4, 5]
    assert all(thread == render.calls[0][1] for _index, thread in render.calls)  # one render thread (C1)
    assert all(thread.startswith("video-c2") for _index, thread in prep.calls)  # preparation on the C2 thread
    assert prep.calls[0][0] == 1


def test_progress_reports_every_stage_in_order() -> None:
    stages = []
    pipeline, _ = _pipeline()

    pipeline.run(_source(), progress=lambda stage, scene, count: stages.append((stage, scene, count)))

    names = [stage for stage, _scene, _count in stages]
    assert names[0] == STAGE_PLANNING and names[1] == STAGE_PREPARING
    assert names.count(STAGE_RENDERING) == 5 and names[-2:] == [STAGE_ASSEMBLING, STAGE_CHECKING]
    assert [scene for stage, scene, _ in stages if stage == STAGE_RENDERING] == [1, 2, 3, 4, 5]
    assert all(count == 5 for _stage, _scene, count in stages)


def test_a_clause_with_a_bad_wav_is_synthesised_again() -> None:
    narration = _Narration(fail_first=True)
    pipeline, _ = _pipeline(narration=narration)

    pipeline.run(_source())

    assert narration.calls.count(narration.calls[0]) >= 2


def test_narration_that_keeps_failing_names_the_audio_rule() -> None:
    class _Silent(_Narration):
        def synthesize(self, spoken):
            return _wav(0.05)

    pipeline, _ = _pipeline(narration=_Silent())

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code.startswith("VIDEO_NARRATION_AUDIO_")


def test_a_long_voice_holds_the_last_frame_and_shifts_later_scenes() -> None:
    pipeline, _ = _pipeline(narration=_Narration(seconds_per_letter=0.4))

    result = pipeline.run(_source())

    assert any(scene.hold_frames > 0 for scene in result.plan.scenes)
    assert result.plan.total_frames > 720
    starts = [scene.start_frame for scene in result.plan.scenes]
    assert starts == sorted(starts)


def test_the_planner_failure_is_reported_with_its_code() -> None:
    broken = _draft()
    broken["scenes"][0]["narration"] = "Rùa con đang bò và"
    pipeline, _ = _pipeline(draft=broken)

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code == "VIDEO_PLAN_LINE_TEXT_DANGLING_WORD"


def test_a_failed_validation_stops_the_pipeline() -> None:
    pipeline, _ = _pipeline(
        validator=_Validator(ValidationReport(safety_ok=False, failure_code="VIDEO_SAFETY_BLOCKED"))
    )

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code == "VIDEO_SAFETY_BLOCKED"


def test_cancelling_stops_before_rendering_more_scenes() -> None:
    render = _Render()
    pipeline, _ = _pipeline(render=render)
    seen = {"count": 0}

    def cancelled() -> bool:
        seen["count"] += 1
        return seen["count"] > 3

    with pytest.raises(VideoPipelineCancelled):
        pipeline.run(_source(), cancelled=cancelled)

    assert len(render.calls) < 5


def test_a_run_without_a_main_subject_fails_early() -> None:
    pipeline, _ = _pipeline()

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source((PlannerSubject("sec-1", "chiếc lá", "secondary"),)))

    assert error.value.code == "VIDEO_MAIN_SUBJECT_MISSING"
