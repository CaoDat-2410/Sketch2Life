"""Ports of the Parent video pipeline (FEAT-093). Infrastructure implements them; the orchestrator only calls them.

Two GPU containers (owner decision D6): C1 renders scenes with LTX-2.5 and nothing else (``SceneRenderPort``); C2 runs
everything else that needs a model (``ScenePreparationPort``, ``NarrationPort``, the timeline generator and the
validator's vision checks). The assembler and caption work run on the CPU of the video worker process.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from sketch2life.application.video_pipeline.caption_plan import Cue
from sketch2life.application.video_pipeline.timeline_planner import PlannerSubject
from sketch2life.application.video_pipeline.video_plan import ScenePlan, VideoPlan


class VideoPipelineError(RuntimeError):
    """A failure with a safe, content-free code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class VideoPipelineCancelled(RuntimeError):
    """The adult cancelled the run; the work is discarded."""


@dataclass(frozen=True, slots=True)
class VideoSource:
    """Everything the pipeline reads about a confirmed story (read-only)."""

    run_id: str
    story_sha256: str
    story: Mapping[str, Any]
    topic: str
    age_months: int
    subjects: tuple[PlannerSubject, ...]
    activity: Mapping[str, Any]
    drawing_png: bytes
    drawing_sha256: str
    subject_boxes: Mapping[str, tuple[int, int, int, int]]  # entity id -> 20x20 grid box
    # FEAT-094: {"title", "scenes": [{"title", "narration", "action_en", "setting_en", ...}]} of a learning script.
    learning: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ScenePrepJob:
    scene: ScenePlan
    drawing_sha256: str
    subject_labels: Mapping[str, str]
    subject_boxes: Mapping[str, tuple[int, int, int, int]]
    main_entity_id: str
    drawing_png: bytes = b""
    staging: Mapping[str, Any] | None = None  # ``sketch2life.story-staging.v1`` for the whole plan
    secondary_ids: tuple[str, ...] = ()
    plate_attempt: int = 0  # above 0: paint the background again with another seed


@dataclass(frozen=True, slots=True)
class PreparedScene:
    keyframe_png: bytes
    background: str  # "AI" | "PAPER"


@dataclass(frozen=True, slots=True)
class SceneRenderJob:
    scene: ScenePlan
    keyframe_png: bytes
    storyboard_sha256: str = ""  # the confirmed story's hash; the renderer falls back to its own default
    scene_count: int = 0


@dataclass(frozen=True, slots=True)
class SceneClip:
    scene_index: int
    video: bytes
    frames: int


@dataclass(frozen=True, slots=True)
class PlacedChunk:
    """One synthesised clause on the master clock; the assembler trims the silent edges."""

    start_ms: int
    wav: bytes
    trim_head_ms: int
    trim_tail_ms: int
    duration_ms: int  # speech duration after trimming


@dataclass(frozen=True, slots=True)
class AssembleJob:
    plan: VideoPlan
    clips: Sequence[SceneClip]
    chunks: Sequence[PlacedChunk]
    cues: Sequence[Cue]
    part_labels: Mapping[int, str] = field(default_factory=dict)  # scene index -> name of the part it teaches


@dataclass(frozen=True, slots=True)
class ValidationReport:
    technical_ok: bool = True
    consistency_ok: bool = True
    safety_ok: bool = True
    finding_codes: tuple[str, ...] = ()
    failure_code: str | None = None


class ScenePreparationPort(Protocol):
    def prepare(self, job: ScenePrepJob) -> PreparedScene: ...


class SceneRenderPort(Protocol):
    def render(self, job: SceneRenderJob) -> SceneClip: ...


class SceneCheckPort(Protocol):
    def check(self, clip: SceneClip, keyframe_png: bytes) -> tuple[str, ...]:
        """Problem codes seen in one rendered scene; raises ``VideoPipelineError`` when it cannot look."""

    def check_keyframe(self, drawing_png: bytes, keyframe_png: bytes) -> tuple[str, ...]:
        """Problem codes seen in one composed first frame, before it is rendered."""


class NarrationPort(Protocol):
    def synthesize(self, spoken_text: str) -> bytes:
        """A 16-bit PCM WAV of one clause."""


class AssemblerPort(Protocol):
    def assemble(self, job: AssembleJob) -> bytes:
        """The final MP4 (video, narration track, faststart)."""


class VideoValidatorPort(Protocol):
    def validate(self, video: bytes, plan: VideoPlan) -> ValidationReport: ...


@dataclass(frozen=True, slots=True)
class PipelineResult:
    video: bytes
    captions_vtt: str
    cues: tuple[Cue, ...]
    plan: VideoPlan
    report: ValidationReport
    backgrounds: Mapping[int, str]
    # FEAT-094: scene index -> problem codes seen by the visual check (empty when it is off or found nothing).
    findings: Mapping[int, tuple[str, ...]] = field(default_factory=dict)


__all__ = [
    "AssembleJob",
    "AssemblerPort",
    "NarrationPort",
    "PipelineResult",
    "PlacedChunk",
    "PreparedScene",
    "SceneCheckPort",
    "SceneClip",
    "ScenePrepJob",
    "ScenePreparationPort",
    "SceneRenderJob",
    "SceneRenderPort",
    "ValidationReport",
    "VideoPipelineCancelled",
    "VideoPipelineError",
    "VideoSource",
    "VideoValidatorPort",
]
