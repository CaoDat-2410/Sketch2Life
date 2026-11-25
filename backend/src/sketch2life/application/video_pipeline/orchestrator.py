"""The Parent video pipeline (FEAT-093 plan Rev 2, section 4): plan, prepare, narrate, render, assemble, check.

Two GPU containers: C1 renders scenes and nothing else; C2 serves everything else. C2 work is serialised on one
worker thread (it is one container), in the order scene 1, all narration, scene 2 ... scene N, while the calling thread
renders on C1 as soon as a scene is prepared. Wall time is therefore about the first preparation plus N renders.

Pure orchestration: every effect goes through a port, so the whole flow is tested with fakes.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from sketch2life.application.video_pipeline.age_profile import FPS, AgeBandProfile, profile_for_age_months
from sketch2life.application.video_pipeline.caption_plan import (
    CLAUSE_GAP_MS,
    LineAudio,
    build_cues,
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
from sketch2life.application.video_pipeline.video_plan import (
    ScenePlan,
    VideoPlan,
    apply_stretches,
    build_video_plan,
)

TAIL_AFTER_VOICE_MS = 300
NARRATION_ATTEMPTS = 2

STAGE_PLANNING = "PLANNING"
STAGE_PREPARING = "PREPARING_SCENES"
STAGE_RENDERING = "RENDERING"
STAGE_NARRATING = "NARRATING"
STAGE_ASSEMBLING = "ASSEMBLING"
STAGE_CHECKING = "CHECKING"

ProgressCallback = Callable[[str, int | None, int], None]


@dataclass(frozen=True, slots=True)
class _LineAudioResult:
    line: TimelineLine
    lane: str
    chunks: tuple[tuple[bytes, int, int, int], ...]  # (wav, trim_head, trim_tail, speech_ms) per clause

    @property
    def clause_durations(self) -> tuple[int, ...]:
        return tuple(chunk[3] for chunk in self.chunks)

    @property
    def total_ms(self) -> int:
        return sum(self.clause_durations) + CLAUSE_GAP_MS * (len(self.chunks) - 1)


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
        secondary_ids = tuple(item.entity_id for item in source.subjects if item.entity_id != main)
        try:
            staging = build_staging(plan, subject_boxes=source.subject_boxes, secondary_ids=secondary_ids)
        except StagingError as error:
            raise VideoPipelineError(f"VIDEO_{error.code}") from None
        staged = (staging, secondary_ids)

        c2 = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-c2")
        try:
            prep: dict[int, Future[PreparedScene]] = {}
            first = plan.scenes[0]
            prep[first.index] = c2.submit(self._prepare, first, source, labels, main, staged)
            narration_future = c2.submit(self._narrate_all, plan, profile, source)
            for scene in plan.scenes[1:]:
                prep[scene.index] = c2.submit(self._prepare, scene, source, labels, main, staged)

            clips: list[SceneClip] = []
            backgrounds: dict[int, str] = {}
            report(STAGE_PREPARING, 1, count)
            for scene in plan.scenes:
                check_cancel()
                prepared = prep[scene.index].result()
                backgrounds[scene.index] = prepared.background
                report(STAGE_RENDERING, scene.index, count)
                clips.append(self._renderer.render(SceneRenderJob(scene=scene, keyframe_png=prepared.keyframe_png)))
            check_cancel()
            if not narration_future.done():
                report(STAGE_NARRATING, None, count)
            line_audio = narration_future.result()
        finally:
            c2.shutdown(wait=True, cancel_futures=True)

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

    # ----------------------------------------------------------------- C2 work
    def _prepare(
        self,
        scene: ScenePlan,
        source: VideoSource,
        labels: dict[str, str],
        main: str,
        staged: tuple[dict[str, Any], tuple[str, ...]],
    ) -> PreparedScene:
        return self._preparation.prepare(
            ScenePrepJob(
                scene=scene,
                drawing_sha256=source.drawing_sha256,
                subject_labels=labels,
                subject_boxes=source.subject_boxes,
                main_entity_id=main,
                drawing_png=source.drawing_png,
                staging=staged[0],
                secondary_ids=staged[1],
            )
        )

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
            wav = self._narration.synthesize(spoken)
            try:
                measured = analyse_wav(wav)
            except ValueError as error:
                last_problem = str(error)
                continue
            problems = audio_problems(measured, spoken_text=spoken, profile=profile)
            # Single clauses are short, so the speech-rate band is relaxed to the whole range of the three bands.
            problems = [item for item in problems if item != "AUDIO_SPEECH_RATE_OUT_OF_BAND"]
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
        # Pass 1: how much does each scene's narration need beyond the clip?
        extra: dict[int, int] = {}
        for scene in plan.scenes:
            cursor = scene.start_ms
            for line in scene.lines:
                result = by_line[(line.start_ms, line.text)]
                start = max(line.start_ms, cursor)
                cursor = start + result.total_ms + 300
            needed_ms = cursor - 300 + TAIL_AFTER_VOICE_MS - (scene.start_ms + scene.duration_ms)
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
                start = max(line.start_ms, cursor)
                placements.append(
                    LineAudio(
                        line=TimelineLine(line.text, start, start + result.total_ms, line.speaker_ref),
                        lane=result.lane,
                        placed_start_ms=start,
                        clause_durations_ms=result.clause_durations,
                    )
                )
                clause_start = start
                for wav, head, tail, speech in result.chunks:
                    chunks.append(PlacedChunk(clause_start, wav, head, tail, speech))
                    clause_start += speech + CLAUSE_GAP_MS
                cursor = start + result.total_ms + 300
        cues = build_cues(placements, speaker_labels=_speaker_labels(source))
        cues = extend_short_cues(cues, duration_ms=plan.total_ms)
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
