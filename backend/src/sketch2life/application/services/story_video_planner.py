"""Provider-neutral storyboard compilation for the new illustrated-video flow."""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryboardPlanV1,
    StoryboardSceneV1,
    StoryScriptSegmentV1,
)


@dataclass(frozen=True)
class StoryboardCompileInput:
    package: ApprovedStoryPackageV1
    segments: tuple[StoryScriptSegmentV1, ...]
    measured_segment_durations: tuple[float, ...] | None = None


class StoryVideoPlanner:
    """Compile approved narration into scene instructions without calling AI SDKs.

    The planner is deliberately deterministic. Illustration, TTS and Wan
    adapters consume its immutable output later; they cannot change the source
    package or silently invent timing.
    """

    def compile(self, request: StoryboardCompileInput) -> StoryboardPlanV1:
        package = request.package
        segments = request.segments
        self._validate_segments(segments)
        measured = request.measured_segment_durations
        if measured is not None and len(measured) != len(segments):
            raise ValueError("measured duration count must match script segment count")
        if measured is not None and any(duration <= 0 for duration in measured):
            raise ValueError("measured segment durations must be positive")

        basis = "MEASURED_TTS" if measured is not None else "ESTIMATE"
        scenes = tuple(
            self._scene(segment, index, measured[index] if measured is not None else None, basis)
            for index, segment in enumerate(segments)
        )
        total = round(sum(scene.duration_seconds for scene in scenes), 3)
        if basis == "MEASURED_TTS" and not (
            package.target_duration_min_seconds <= total <= package.target_duration_max_seconds
        ):
            raise ValueError("measured narration must be revised to fit the 40-60 second target")

        plan_data = {
            "storyboard_id": f"storyboard-{package.package_id}",
            "package_id": package.package_id,
            "package_hash": package.package_hash,
            "scenes": scenes,
            "duration_seconds": total,
            "duration_basis": basis,
        }
        return StoryboardPlanV1.model_validate(plan_data)

    @staticmethod
    def _validate_segments(segments: tuple[StoryScriptSegmentV1, ...]) -> None:
        if not segments:
            raise ValueError("approved story must contain at least one script segment")
        expected = tuple(f"segment-{index}" for index in range(1, len(segments) + 1))
        if tuple(segment.segment_id for segment in segments) != expected:
            raise ValueError("script segments must be ordered and contiguous")

    @staticmethod
    def _scene(
        segment: StoryScriptSegmentV1,
        index: int,
        measured_duration: float | None,
        basis: str,
    ) -> StoryboardSceneV1:
        duration = (
            measured_duration
            if measured_duration is not None
            else max(4.0, min(10.0, len(segment.text) / 14.0))
        )
        visual = (
            "Clean black-ink whiteboard line drawing on a plain white background; "
            "one consistent subject and simple composition across all scenes. "
            "Preserve the source drawing's identity and depict only approved details. "
            f"Confirmed anchors: {', '.join(segment.confirmed_anchor_ids)}. "
            f"Narration for this scene: {segment.text}"
        )
        motion = {
            "INTRO": "Reveal the setting and subject with a gentle camera push-in.",
            "EXPLAIN": "Animate the subject action progressively in sync with narration.",
            "DEMONSTRATE": "Show the described action with clear, continuous movement.",
            "RECAP": "Return to the subject and resolve the story with a calm movement.",
        }[segment.scene_purpose]
        return StoryboardSceneV1(
            scene_id=f"scene-{index + 1}",
            order=index + 1,
            segment_ids=(segment.segment_id,),
            narration_text=segment.text,
            visual_prompt=visual,
            motion_prompt=motion,
            approved_fact_ids=segment.approved_fact_ids,
            confirmed_anchor_ids=segment.confirmed_anchor_ids,
            duration_seconds=round(duration, 3),
            duration_basis=basis,
        )


__all__ = ["StoryboardCompileInput", "StoryVideoPlanner"]
