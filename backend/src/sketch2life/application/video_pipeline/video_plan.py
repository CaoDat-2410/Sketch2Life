"""VideoPlan: what the renderer needs, derived only from the validated timeline and the confirmed roles.

Pure code. The plan holds per-scene frame counts (target and model), seeds, prompts, subjects, interaction state
ladders and the voiced lines placed on the master clock. Rendering, narration and assembly read it; none of them
decides timing on its own (FEAT-093 plan Rev 2, sections 4 and 15.2).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Final

from sketch2life.application.video_pipeline.age_profile import FPS, MAX_SCENE_FRAMES, ms_to_frames
from sketch2life.application.video_pipeline.caption_plan import LineAudio
from sketch2life.application.video_pipeline.story_timeline import (
    Interaction,
    StoryTimeline,
    TimelineLine,
)

MODEL_FRAME_QUANTUM: Final = 8
MIN_MODEL_FRAMES: Final = 9
PLAN_SCHEMA: Final = "sketch2life.video-plan.v1"


def nearest_model_frames(target_frames: int) -> int:
    """The closest ``1 + 8k`` frame count the LTX model renders (ties go to the shorter clip)."""

    lower = max(MIN_MODEL_FRAMES, ((max(MIN_MODEL_FRAMES, target_frames) - 1) // MODEL_FRAME_QUANTUM) * MODEL_FRAME_QUANTUM + 1)
    upper = lower + MODEL_FRAME_QUANTUM
    return min((lower, upper), key=lambda frames: (abs(frames - target_frames), frames))


@dataclass(frozen=True, slots=True)
class StateLadder:
    """How much of a subject remains (1.0 whole, 0.0 gone) at the start and the end of a scene."""

    target: str
    start: float
    end: float
    verb: str


@dataclass(frozen=True, slots=True)
class ScenePlan:
    index: int
    scene_id: str
    start_frame: int
    target_frames: int
    model_frames: int
    seed: int
    title: str
    visual_prompt: str
    background_prompt: str
    subjects: tuple[str, ...]
    interactions: tuple[Interaction, ...]
    ladders: tuple[StateLadder, ...]
    lines: tuple[TimelineLine, ...]

    @property
    def start_ms(self) -> int:
        return round(self.start_frame * 1000 / FPS)

    @property
    def duration_ms(self) -> int:
        return round(self.target_frames * 1000 / FPS)


@dataclass(frozen=True, slots=True)
class VideoPlan:
    schema_version: str
    story_sha256: str
    age_band: str
    main_entity_id: str
    title: str
    total_frames: int
    scenes: tuple[ScenePlan, ...]

    @property
    def total_ms(self) -> int:
        return round(self.total_frames * 1000 / FPS)

    def line_placements(self) -> list[LineAudio]:
        """Every voiced line at its planned time (no measured clause durations yet)."""

        placements: list[LineAudio] = []
        for scene in self.scenes:
            for line in scene.lines:
                lane = "dialogue" if line.speaker_ref else "narration"
                placements.append(LineAudio(line=line, lane=lane, placed_start_ms=line.start_ms))
        return placements


def _seed(story_sha256: str, index: int) -> int:
    digest = hashlib.sha256(f"{story_sha256}:{index}".encode("ascii")).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def build_video_plan(timeline: StoryTimeline, *, story_sha256: str, main_entity_id: str) -> VideoPlan:
    """Project a validated timeline into render-ready scene plans."""

    scenes: list[ScenePlan] = []
    for scene in timeline.scenes:
        start_frame = ms_to_frames(scene.start_ms)
        target_frames = ms_to_frames(scene.end_ms) - start_frame
        model_frames = min(nearest_model_frames(target_frames), MAX_SCENE_FRAMES)
        ladders = tuple(
            StateLadder(item.target, item.from_state, item.to_state, item.verb)
            for item in scene.interactions
            if item.kind == "consume"
        )
        scenes.append(
            ScenePlan(
                index=scene.index,
                scene_id=f"scene-{scene.index}",
                start_frame=start_frame,
                target_frames=target_frames,
                model_frames=model_frames,
                seed=_seed(story_sha256, scene.index),
                title=scene.title,
                visual_prompt=scene.visual_prompt,
                background_prompt=scene.background_prompt,
                subjects=scene.subjects,
                interactions=scene.interactions,
                ladders=ladders,
                lines=scene.voiced_lines,
            )
        )
    return VideoPlan(
        schema_version=PLAN_SCHEMA,
        story_sha256=story_sha256,
        age_band=timeline.age_band,
        main_entity_id=main_entity_id,
        title=timeline.title,
        total_frames=sum(scene.target_frames for scene in scenes),
        scenes=tuple(scenes),
    )


__all__ = [
    "PLAN_SCHEMA",
    "ScenePlan",
    "StateLadder",
    "VideoPlan",
    "build_video_plan",
    "nearest_model_frames",
]
