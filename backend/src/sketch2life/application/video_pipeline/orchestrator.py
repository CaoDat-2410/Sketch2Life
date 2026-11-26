"""The Parent video pipeline (FEAT-093 plan Rev 2, section 4): plan, prepare, narrate, render, assemble, check.

C1 renders scenes and nothing else. Scene preparation (one GPU container) and narration (a CPU container) each run in
order on their own thread, while the calling thread renders on C1 as soon as a scene is prepared. Wall time is therefore
about the first preparation plus N renders.

Pure orchestration: every effect goes through a port, so the whole flow is tested with fakes.
"""

from __future__ import annotations

import contextlib
import math
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from typing import Any, TypeVar

from sketch2life.application.video_pipeline.age_profile import FPS, AgeBandProfile, profile_for_age_months
from sketch2life.application.video_pipeline.caption_plan import (
    LineAudio,
    build_cues,
    caption_prefix,
    clause_slot_ms,
    extend_short_cues,
    lint_cues,
    split_clauses,
    to_webvtt,
)
from sketch2life.application.video_pipeline.narration_qc import (
    analyse_wav,
    audio_problems,
    normalize_for_tts,
)
from sketch2life.application.video_pipeline.ports import (
    AssembleJob,
    AssemblerPort,
    NarrationPort,
    PipelineResult,
    PlacedChunk,
    PreparedScene,
    SceneClip,
    ScenePrepJob,
    ScenePreparationPort,
    SceneRenderJob,
    SceneRenderPort,
    VideoPipelineCancelled,
    VideoPipelineError,
    VideoSource,
    VideoValidatorPort,
)
from sketch2life.application.video_pipeline.staging_builder import StagingError, build_staging
from sketch2life.application.video_pipeline.story_timeline import TimelineError, TimelineLine
from sketch2life.application.video_pipeline.timeline_planner import (
    VideoTimelineGeneratorPort,
    plan_timeline,
)
from sketch2life.application.video_pipeline.visual_prompt_guard import (
    drawn_only_prompt,
    is_airborne,
    person_is_drawn,
)
from sketch2life.application.video_pipeline.video_plan import (
    ScenePlan,
    VideoPlan,
    apply_stretches,
    build_video_plan,
)

TAIL_AFTER_VOICE_MS = 300
NARRATION_ATTEMPTS = 2
_TOLERATED_AUDIO_PROBLEMS = frozenset({"AUDIO_SPEECH_RATE_OUT_OF_BAND", "AUDIO_EDGE_SILENCE"})
LINE_GAP_MS = 300
# FEAT-093 Amendment C: one more try for a call that failed with a known outcome. An unknown dispatch outcome is
# never sent again, and input errors would only fail the same way.
STEP_ATTEMPTS = 2
_RETRYABLE_CODE_ENDINGS = ("_FAILED", "_TIMEOUT", "_OUTPUT_INVALID", "_OUTPUT_UNAVAILABLE", "_HASH_MISMATCH")

STAGE_PLANNING = "PLANNING"
STAGE_PREPARING = "PREPARING_SCENES"
STAGE_RENDERING = "RENDERING"
STAGE_NARRATING = "NARRATING"
STAGE_ASSEMBLING = "ASSEMBLING"
STAGE_CHECKING = "CHECKING"

ProgressCallback = Callable[[str, int | None, int], None]
_Result = TypeVar("_Result")


def _retried(call: Callable[[], _Result], *, before_retry: Callable[[], None] | None = None) -> _Result:
    for attempt in range(1, STEP_ATTEMPTS + 1):
        try:
            return call()
        except VideoPipelineError as error:
            if attempt == STEP_ATTEMPTS or not error.code.endswith(_RETRYABLE_CODE_ENDINGS):
                raise
            if before_retry is not None:
                before_retry()
    raise AssertionError("unreachable")


@dataclass(frozen=True, slots=True)
class _LineAudioResult:
    line: TimelineLine
    lane: str
    chunks: tuple[tuple[bytes, int, int, int], ...]  # (wav, trim_head, trim_tail, speech_ms) per clause

    @property
    def clause_durations(self) -> tuple[int, ...]:
        return tuple(chunk[3] for chunk in self.chunks)

    def slots(self, labels: dict[str, str], max_cps: float) -> tuple[int, ...]:
        """Clock time of each clause, long enough for its voice and for reading its captions."""

        prefix = caption_prefix(self.lane, self.line.speaker_ref, labels)
        return tuple(
            clause_slot_ms(f"{prefix}{clause}" if position == 0 else clause, duration, max_cps=max_cps)
            for position, (clause, duration) in enumerate(
                zip(split_clauses(self.line.text), self.clause_durations, strict=True)
            )
        )


def _speaker_labels(source: VideoSource) -> dict[str, str]:
    """``speaker_ref`` codes (short, accent-free) mapped to the subject label they stand for."""

    from sketch2life.application.subject_role_scoring import fold

    labels: dict[str, str] = {}
    for subject in source.subjects:
        for token in fold(subject.label).split():
            if token != "con" and len(token) > 1:
                labels.setdefault(token, subject.label.removeprefix("con ").strip().capitalize())
    return labels


class VideoPipeline:
    def __init__(
        self,
        *,
        timeline_generator: VideoTimelineGeneratorPort,
        preparation: ScenePreparationPort,
        renderer: SceneRenderPort,
        narration: NarrationPort,
        assembler: AssemblerPort,
        validator: VideoValidatorPort,
    ) -> None:
        self._generator = timeline_generator
        self._preparation = preparation
        self._renderer = renderer
        self._narration = narration
        self._assembler = assembler
        self._validator = validator

    def run(
        self,
        source: VideoSource,
        *,
        progress: ProgressCallback | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> PipelineResult:
        def report(stage: str, scene: int | None, count: int) -> None:
            if progress is not None:
                progress(stage, scene, count)

        def check_cancel() -> None:
            if cancelled is not None and cancelled():
                raise VideoPipelineCancelled()

        profile = profile_for_age_months(source.age_months)
        main = next((item.entity_id for item in source.subjects if item.role == "main"), None)
        if main is None:
            raise VideoPipelineError("VIDEO_MAIN_SUBJECT_MISSING")

        report(STAGE_PLANNING, None, profile.scene_count)
        check_cancel()
        self._warm_up()
        try:
            timeline = plan_timeline(
                profile=profile,
                story=source.story,
                subjects=source.subjects,
                activity=source.activity,
                topic=source.topic,
                generator=self._generator,
            )
        except TimelineError as error:
            raise VideoPipelineError(f"VIDEO_PLAN_{error.code}") from None
        plan = build_video_plan(timeline, story_sha256=source.story_sha256, main_entity_id=main)
        count = len(plan.scenes)
        labels = {item.entity_id: item.label for item in source.subjects}
        person_drawn = person_is_drawn(labels.values())
        plan = replace(
            plan,
            scenes=tuple(
                replace(
                    scene,
                    visual_prompt=drawn_only_prompt(scene.visual_prompt, person_drawn=person_drawn),
                    background_prompt=drawn_only_prompt(scene.background_prompt, person_drawn=person_drawn),
                )
                for scene in plan.scenes
            ),
        )
        secondary_ids = tuple(item.entity_id for item in source.subjects if item.entity_id != main)
        try:
            staging = build_staging(
                plan,
                subject_boxes=source.subject_boxes,
                secondary_ids=secondary_ids,
                grounded=not is_airborne(labels[main]),
            )
        except StagingError as error:
            raise VideoPipelineError(f"VIDEO_{error.code}") from None
        staged = (staging, secondary_ids)

        c2 = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-c2")
        voice = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-voice")
        try:
            prep: dict[int, Future[PreparedScene]] = {}
            first = plan.scenes[0]
            prep[first.index] = c2.submit(self._prepare, first, source, labels, main, staged)
            narration_future = voice.submit(self._narrate_all, plan, profile, source)
            for scene in plan.scenes[1:]:
                prep[scene.index] = c2.submit(self._prepare, scene, source, labels, main, staged)

            clips: list[SceneClip] = []
            backgrounds: dict[int, str] = {}
            report(STAGE_PREPARING, 1, count)
            for scene in plan.scenes:
                check_cancel()
                if narration_future.done():
                    narration_future.result()  # a narration failure surfaces now, before more scenes are rendered
                prepared = prep[scene.index].result()
                backgrounds[scene.index] = prepared.background
                report(STAGE_RENDERING, scene.index, count)
                job = SceneRenderJob(
                    scene=scene,
                    keyframe_png=prepared.keyframe_png,
                    storyboard_sha256=plan.story_sha256,
                    scene_count=count,
                )
                clips.append(_retried(lambda job=job: self._renderer.render(job), before_retry=check_cancel))
            check_cancel()
            if not narration_future.done():
                report(STAGE_NARRATING, None, count)
            line_audio = narration_future.result()
        finally:
            c2.shutdown(wait=True, cancel_futures=True)
            voice.shutdown(wait=True, cancel_futures=True)

        report(STAGE_ASSEMBLING, None, count)
        check_cancel()
        plan, chunks, cues = self._place(plan, profile, line_audio, source)
        video = self._assembler.assemble(AssembleJob(plan=plan, clips=tuple(clips), chunks=tuple(chunks), cues=tuple(cues)))

        report(STAGE_CHECKING, None, count)
        check_cancel()
        validation = self._validator.validate(video, plan)
        if validation.failure_code is not None or not (
            validation.technical_ok and validation.consistency_ok and validation.safety_ok
        ):
            raise VideoPipelineError(validation.failure_code or "VIDEO_VALIDATION_FAILED")
        return PipelineResult(
            video=video,
            captions_vtt=to_webvtt(cues),
            cues=tuple(cues),
            plan=plan,
            report=validation,
            backgrounds=backgrounds,
        )

    def _warm_up(self) -> None:
        """Start the GPU containers while the timeline is planned, so their cold starts overlap it (best effort)."""

        for port in (self._preparation, self._renderer):
            warm_up = getattr(port, "warm_up", None)
            if callable(warm_up):
                with contextlib.suppress(Exception):
                    warm_up()

    # ----------------------------------------------------------------- C2 work
    def _prepare(
        self,
        scene: ScenePlan,
        source: VideoSource,
        labels: dict[str, str],
        main: str,
        staged: tuple[dict[str, Any], tuple[str, ...]],
    ) -> PreparedScene:
        job = ScenePrepJob(
            scene=scene,
            drawing_sha256=source.drawing_sha256,
            subject_labels=labels,
            subject_boxes=source.subject_boxes,
            main_entity_id=main,
            drawing_png=source.drawing_png,
            staging=staged[0],
            secondary_ids=staged[1],
        )
        return _retried(lambda: self._preparation.prepare(job))

    def _narrate_all(self, plan: VideoPlan, profile: AgeBandProfile, source: VideoSource) -> list[_LineAudioResult]:
        results: list[_LineAudioResult] = []
        for scene in plan.scenes:
            for line in scene.lines:
                lane = "dialogue" if line.speaker_ref else "narration"
                chunks = []
                for clause in split_clauses(line.text):
                    chunks.append(self._synthesize_checked(clause, profile))
                results.append(_LineAudioResult(line=line, lane=lane, chunks=tuple(chunks)))
        return results

    def _synthesize_checked(self, clause: str, profile: AgeBandProfile) -> tuple[bytes, int, int, int]:
        spoken = normalize_for_tts(clause).spoken
        last_problem = "AUDIO_UNKNOWN"
        for _attempt in range(NARRATION_ATTEMPTS):
            wav = _retried(lambda: self._narration.synthesize(spoken))
            try:
                measured = analyse_wav(wav)
            except ValueError as error:
                last_problem = str(error)
                continue
            problems = audio_problems(measured, spoken_text=spoken, profile=profile)
            # Single clauses are short, so the speech-rate band is relaxed to the whole range of the three bands; silence
            # at the edges is cut off by the assembler.
            problems = [item for item in problems if item not in _TOLERATED_AUDIO_PROBLEMS]
            if not problems:
                speech = measured.duration_ms - measured.leading_silence_ms - measured.trailing_silence_ms
                return wav, measured.leading_silence_ms, measured.trailing_silence_ms, speech
            last_problem = problems[0]
        raise VideoPipelineError(f"VIDEO_NARRATION_{last_problem}")

    # ----------------------------------------------------------- placement
    def _place(
        self,
        plan: VideoPlan,
        profile: AgeBandProfile,
        line_audio: Sequence[_LineAudioResult],
        source: VideoSource,
    ) -> tuple[VideoPlan, list[PlacedChunk], list]:
        by_line = {(result.line.start_ms, result.line.text): result for result in line_audio}
        labels = _speaker_labels(source)
        slots = {key: result.slots(labels, profile.caption_max_cps) for key, result in by_line.items()}
        # Pass 1: how much does each scene's narration need beyond the clip?
        extra: dict[int, int] = {}
        for scene in plan.scenes:
            cursor = scene.start_ms
            for line in scene.lines:
                start = max(line.start_ms, cursor)
                cursor = start + sum(slots[(line.start_ms, line.text)]) + LINE_GAP_MS
            needed_ms = cursor - LINE_GAP_MS + TAIL_AFTER_VOICE_MS - (scene.start_ms + scene.duration_ms)
            if needed_ms > 0:
                extra[scene.index] = math.ceil(needed_ms * FPS / 1000)
        try:
            plan = apply_stretches(plan, extra) if extra else plan
        except ValueError as error:
            raise VideoPipelineError(f"VIDEO_NARRATION_{error}") from None

        # Pass 2: absolute placement on the final clock (the stretch moved later scenes and their lines).
        placements: list[LineAudio] = []
        chunks: list[PlacedChunk] = []
        for scene in plan.scenes:
            cursor = scene.start_ms
            for line in scene.lines:
                original_start = line.start_ms - _shift_for(plan, scene)
                result = by_line[(original_start, line.text)]
                line_slots = slots[(original_start, line.text)]
                start = max(line.start_ms, cursor)
                placements.append(
                    LineAudio(
                        line=TimelineLine(line.text, start, start + sum(line_slots), line.speaker_ref),
                        lane=result.lane,
                        placed_start_ms=start,
                        clause_durations_ms=result.clause_durations,
                        clause_slots_ms=line_slots,
                    )
                )
                clause_start = start
                for (wav, head, tail, speech), slot in zip(result.chunks, line_slots, strict=True):
                    chunks.append(PlacedChunk(clause_start, wav, head, tail, speech))
                    clause_start += slot
                cursor = start + sum(line_slots) + LINE_GAP_MS
        cues = build_cues(placements, speaker_labels=labels, max_cps=profile.caption_max_cps)
        cues = extend_short_cues(cues, duration_ms=plan.total_ms, max_cps=profile.caption_max_cps)
        problems = lint_cues(cues, duration_ms=plan.total_ms, max_cps=profile.caption_max_cps)
        if problems:
            raise VideoPipelineError(f"VIDEO_CAPTIONS_{problems[0]}")
        return plan, chunks, cues


def _shift_for(plan: VideoPlan, scene: ScenePlan) -> int:
    """Milliseconds by which earlier stretches moved this scene's lines (start of the scene versus its unstretched start)."""

    unstretched_start_frames = scene.start_frame - sum(
        earlier.hold_frames for earlier in plan.scenes if earlier.index < scene.index
    )
    return round((scene.start_frame - unstretched_start_frames) * 1000 / FPS)


__all__ = [
    "STAGE_ASSEMBLING",
    "STAGE_CHECKING",
    "STAGE_NARRATING",
    "STAGE_PLANNING",
    "STAGE_PREPARING",
    "STAGE_RENDERING",
    "VideoPipeline",
]
