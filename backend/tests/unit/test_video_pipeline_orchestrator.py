"""FEAT-093 block C: the orchestrator with fake ports (one video container, narration, captions)."""

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

    def prepare(self, job):
        self.calls.append((job.scene.index, threading.current_thread().name))
        return PreparedScene(keyframe_png=b"png", background="AI")


class _Render:
    def __init__(self):
        self.calls = []

    def render(self, job):
        self.calls.append((job.scene.index, threading.current_thread().name))
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


def test_every_scene_is_prepared_before_the_first_render_so_one_container_never_switches_back() -> None:
    order: list[tuple[str, int]] = []

    class _OrderedPrep(_Prep):
        def prepare(self, job):
            order.append(("prepare", job.scene.index))
            return super().prepare(job)

    class _OrderedRender(_Render):
        def render(self, job):
            order.append(("render", job.scene.index))
            return super().render(job)

    pipeline, _ = _pipeline(prep=_OrderedPrep(), render=_OrderedRender())

    pipeline.run(_source())

    assert order == [("prepare", i) for i in range(1, 6)] + [("render", i) for i in range(1, 6)]


def test_a_scene_that_cannot_be_prepared_stops_the_run_before_any_render() -> None:
    class _Broken(_Prep):
        def prepare(self, job):
            if job.scene.index == 4:
                raise VideoPipelineError("VIDEO_SCENE_PREPARE_OUTPUT_INVALID_INPUT")
            return super().prepare(job)

    render = _Render()
    pipeline, _ = _pipeline(prep=_Broken(), render=render)

    with pytest.raises(VideoPipelineError):
        pipeline.run(_source())

    assert render.calls == []


def test_progress_reports_every_stage_in_order() -> None:
    stages = []
    pipeline, _ = _pipeline()

    pipeline.run(_source(), progress=lambda stage, scene, count: stages.append((stage, scene, count)))

    names = [stage for stage, _scene, _count in stages]
    assert names[0] == STAGE_PLANNING and names[1] == STAGE_PREPARING
    assert [scene for stage, scene, _ in stages if stage == STAGE_PREPARING] == [1, 2, 3, 4, 5]
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


def test_a_narration_failure_stops_the_run_before_every_scene_is_rendered() -> None:
    class _Broken(_Narration):
        def synthesize(self, spoken):
            raise VideoPipelineError("VIDEO_NARRATION_FAILED")

    class _SlowRender(_Render):
        def render(self, job):
            import time

            time.sleep(0.3)  # lets the narration thread fail while scenes are still being rendered
            return super().render(job)

    render = _SlowRender()
    pipeline, _ = _pipeline(narration=_Broken(), render=render)

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code == "VIDEO_NARRATION_FAILED"
    assert len(render.calls) < 5


class _FlakyRender(_Render):
    def __init__(self, code: str, failures: int):
        super().__init__()
        self.code = code
        self.failures = failures

    def render(self, job):
        if job.scene.index == 2 and self.failures:
            self.failures -= 1
            self.calls.append((job.scene.index, "failed"))
            raise VideoPipelineError(self.code)
        return super().render(job)


@pytest.mark.parametrize("code", ["VIDEO_SCENE_RENDER_FAILED", "VIDEO_SCENE_TIMEOUT", "VIDEO_SCENE_OUTPUT_UNAVAILABLE"])
def test_a_transient_render_failure_is_retried_once(code: str) -> None:
    render = _FlakyRender(code, failures=1)
    pipeline, _ = _pipeline(render=render)

    result = pipeline.run(_source())

    assert result.video == b"MP4-5"
    assert [index for index, _thread in render.calls] == [1, 2, 2, 3, 4, 5]


def test_a_second_render_failure_keeps_its_code() -> None:
    render = _FlakyRender("VIDEO_SCENE_RENDER_FAILED", failures=2)
    pipeline, _ = _pipeline(render=render)

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code == "VIDEO_SCENE_RENDER_FAILED"
    assert [index for index, _thread in render.calls] == [1, 2, 2]


def test_an_unknown_dispatch_is_never_sent_twice() -> None:
    render = _FlakyRender("VIDEO_SCENE_DISPATCH_UNKNOWN", failures=1)
    pipeline, _ = _pipeline(render=render)

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code == "VIDEO_SCENE_DISPATCH_UNKNOWN"
    assert [index for index, _thread in render.calls] == [1, 2]


def test_a_transient_preparation_failure_is_retried_once() -> None:
    class _FlakyPrep(_Prep):
        failed = False

        def prepare(self, job):
            if job.scene.index == 1 and not self.failed:
                self.failed = True
                self.calls.append((job.scene.index, "failed"))
                raise VideoPipelineError("VIDEO_SCENE_PREPARE_FAILED")
            return super().prepare(job)

    prep = _FlakyPrep()
    pipeline, _ = _pipeline(prep=prep)

    pipeline.run(_source())

    assert [index for index, _thread in prep.calls][:2] == [1, 1]


def test_a_transient_narration_call_failure_is_retried_once() -> None:
    class _FlakyNarration(_Narration):
        failed = False

        def synthesize(self, spoken):
            if not self.failed:
                self.failed = True
                self.calls.append(spoken)
                raise VideoPipelineError("VIDEO_NARRATION_FAILED")
            return super().synthesize(spoken)

    narration = _FlakyNarration()
    pipeline, _ = _pipeline(narration=narration)

    pipeline.run(_source())

    assert narration.calls[0] == narration.calls[1]


def test_a_planning_worker_failure_keeps_its_own_code() -> None:
    from sketch2life.infrastructure.story_video.modal_timeline import VideoPlanningUnavailable

    class _Unavailable(_Generator):
        def generate(self, request):
            raise VideoPlanningUnavailable("TIMELINE_DRAFT_SCENE_COUNT")

    pipeline = VideoPipeline(
        timeline_generator=_Unavailable({}), preparation=_Prep(), renderer=_Render(), narration=_Narration(),
        assembler=_Assembler(), validator=_Validator(),
    )

    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(_source())

    assert error.value.code == "TIMELINE_DRAFT_SCENE_COUNT"


def test_the_timeline_gets_a_third_attempt() -> None:
    broken = _draft()
    broken["scenes"][0]["narration"] = "Rùa con đang bò và"

    class _FixedOnThird(_Generator):
        requests: list = []

        def generate(self, request):
            self.requests.append(request["previous_error"])
            return _draft() if len(self.requests) == 3 else copy.deepcopy(broken)

    generator = _FixedOnThird(broken)
    pipeline = VideoPipeline(
        timeline_generator=generator, preparation=_Prep(), renderer=_Render(), narration=_Narration(),
        assembler=_Assembler(), validator=_Validator(),
    )

    pipeline.run(_source())

    assert generator.requests == [None, "LINE_TEXT_DANGLING_WORD", "LINE_TEXT_DANGLING_WORD"]


def test_only_preparation_is_warmed_before_planning_because_it_runs_first() -> None:
    events: list[str] = []

    class _WarmPrep(_Prep):
        def warm_up(self):
            events.append("warm-prep")
            raise RuntimeError("provider down")  # a failed warm-up never fails the run

    class _WarmRender(_Render):
        def warm_up(self):
            events.append("warm-render")  # loading the renderer now would be undone by preparation

    class _Recording(_Generator):
        def generate(self, request):
            events.append("plan")
            return super().generate(request)

    pipeline = VideoPipeline(
        timeline_generator=_Recording(_draft()), preparation=_WarmPrep(), renderer=_WarmRender(),
        narration=_Narration(), assembler=_Assembler(), validator=_Validator(),
    )

    assert pipeline.run(_source()).video == b"MP4-5"
    assert events == ["warm-prep", "plan"]


def _captions_ok(result) -> None:
    from sketch2life.application.video_pipeline.caption_plan import lint_cues

    assert lint_cues(result.cues, duration_ms=result.plan.total_ms, max_cps=14.0) == []


def test_a_very_fast_voice_still_gives_captions_a_child_can_read() -> None:
    draft = _draft()
    for scene in draft["scenes"]:
        scene["narration"] = "Ồ, lá kìa, ăn thôi."
        scene["dialogue"] = [{"speaker_ref": "rua", "text": "Đến nơi rồi."}]
    pipeline, _ = _pipeline(draft=draft, narration=_Narration(seconds_per_letter=0.04))

    _captions_ok(pipeline.run(_source()))


def test_long_silence_at_the_edges_of_a_clip_is_trimmed_not_failed() -> None:
    class _Padded(_Narration):
        def synthesize(self, spoken):
            seconds = max(0.6, sum(ch.isalnum() for ch in spoken) * 0.1)
            rate = 24_000
            frames = bytearray()
            for i in range(int(rate * (seconds + 1.6))):
                voiced = int(rate * 0.8) <= i < int(rate * (seconds + 0.8))
                frames += struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / rate)) if voiced else 0)
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as writer:
                writer.setnchannels(1)
                writer.setsampwidth(2)
                writer.setframerate(rate)
                writer.writeframes(bytes(frames))
            return buffer.getvalue()

    pipeline, _ = _pipeline(narration=_Padded())

    _captions_ok(pipeline.run(_source()))


def test_narration_does_not_wait_behind_scene_preparation() -> None:
    voiced = threading.Event()

    class _BlockedPrep(_Prep):
        def prepare(self, job):
            if job.scene.index == 1:
                assert voiced.wait(5), "narration waited for scene preparation"
            return super().prepare(job)

    class _Signalling(_Narration):
        def synthesize(self, spoken):
            voiced.set()
            return super().synthesize(spoken)

    pipeline, _ = _pipeline(prep=_BlockedPrep(), narration=_Signalling())

    assert pipeline.run(_source()).video == b"MP4-5"


def test_the_renderer_never_receives_a_person_that_was_not_drawn() -> None:
    draft = _draft()
    draft["scenes"][4]["visual_prompt"] = "A child touches the turtle on the grass, crayon style."
    prompts: list[str] = []
    staged: list[dict] = []

    class _Recording(_Render):
        def render(self, job):
            prompts.append(job.scene.visual_prompt)
            return super().render(job)

    class _Staged(_Prep):
        def prepare(self, job):
            staged.append(job.staging)
            return super().prepare(job)

    pipeline, _ = _pipeline(draft=draft, prep=_Staged(), render=_Recording())

    pipeline.run(_source())

    assert len(prompts) == 5 and not any("child" in prompt.lower() for prompt in prompts)
    assert staged[0]["scenes"][0]["main_end"]["grounded"] is True


def test_the_renderer_gets_every_scene_prompt_after_preparation_and_before_the_first_render() -> None:
    events: list[tuple[str, object]] = []

    class _Logged(_Prep):
        def prepare(self, job):
            events.append(("prepare", job.scene.index))
            return super().prepare(job)

    class _Priming(_Render):
        def prime(self, prompts):
            events.append(("prime", tuple(prompts)))
            raise RuntimeError("provider down")  # priming is only a speed-up

        def render(self, job):
            events.append(("render", job.scene.visual_prompt))
            return super().render(job)

    pipeline, _prep = _pipeline(prep=_Logged(), render=_Priming())

    result = pipeline.run(_source())

    assert [name for name, _ in events] == ["prepare"] * 5 + ["prime"] + ["render"] * 5
    assert events[5] == ("prime", tuple(scene.visual_prompt for scene in result.plan.scenes))
