"""Provider-neutral storyboard compilation for the new illustrated-video flow."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

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
        durations = tuple(
            measured[index]
            if measured is not None
            else max(4.0, min(10.0, len(segment.text) / 14.0))
            for index, segment in enumerate(segments)
        )
        groups = self._partition(segments, durations)
        scenes = tuple(
            self._scene(
                segments[start:end],
                index,
                round(sum(durations[start:end]), 3),
                basis,
            )
            for index, (start, end) in enumerate(groups)
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
    def _partition(
        segments: tuple[StoryScriptSegmentV1, ...], durations: tuple[float, ...]
    ) -> tuple[tuple[int, int], ...]:
        """Choose 3–6 timed scenes without splitting approved narration segments."""

        minimum = 3
        maximum = 6
        if len(segments) < minimum:
            raise ValueError("story requires at least three approved narration segments")

        @cache
        def solve(start: int, remaining: int):
            if start == len(segments):
                return (0.0, ()) if remaining == 0 else None
            if remaining <= 0:
                return None
            best = None
            for end in range(start + 1, min(len(segments), start + 8) + 1):
                duration = sum(durations[start:end])
                if duration > 20.0:
                    break
                if duration < 5.0:
                    continue
                continuation = solve(end, remaining - 1)
                if continuation is None:
                    continue
                purposes = {segment.scene_purpose for segment in segments[start:end]}
                if len(purposes) != 1:
                    continue
                score = (duration - 10.0) ** 2
                candidate = (score + continuation[0], ((start, end),) + continuation[1])
                if best is None or candidate < best:
                    best = candidate
            return best

        options = [solve(0, count) for count in range(minimum, maximum + 1)]
        valid = [option for option in options if option is not None]
        if not valid:
            raise ValueError("approved narration cannot fit three to six 5–20 second scenes")
        return min(valid)[1]

    @staticmethod
    def _scene(
        segments: tuple[StoryScriptSegmentV1, ...],
        index: int,
        duration: float,
        basis: str,
    ) -> StoryboardSceneV1:
        narration = " ".join(segment.text for segment in segments)
        if len(narration) > 1_600:
            raise ValueError("scene narration is too long for a visual prompt")
        facts = tuple(
            dict.fromkeys(fact for segment in segments for fact in segment.approved_fact_ids)
        )
        anchors = tuple(
            dict.fromkeys(anchor for segment in segments for anchor in segment.confirmed_anchor_ids)
        )
        if len(facts) > 16 or len(anchors) > 16:
            raise ValueError("scene references exceed the approved fact/anchor limit")
        purpose = segments[0].scene_purpose
        visual_beat = {
            "INTRO": "Introduce the subject from the source drawing.",
            "EXPLAIN": "Show the single action or idea described in this scene.",
            "DEMONSTRATE": "Show the described action at its clearest moment.",
            "RECAP": "Return attention to the same subject for the resolution.",
        }[purpose]
        visual = (
            "Hand-drawn whiteboard illustration on a clean white background: "
            "confident, continuous dark marker contours, clear recognizable shapes, "
            "and selective color accents only where the source drawing has color. "
            "Compose one legible visual beat with space between its elements; keep "
            "the same subject design across scenes while changing the depicted action. "
            "Preserve the source drawing's identity and colors. Do not invent extra "
            "characters, props, labels, scenery, or colors absent from the source. "
            f"Scene beat: {visual_beat} Approved narration: {narration}"
        )
        if len(visual) > 2_000:
            raise ValueError("scene visual prompt exceeds the provider limit")
        motion = {
            "INTRO": "Reveal the setting and subject with a gentle camera push-in.",
            "EXPLAIN": "Animate the subject action progressively in sync with narration.",
            "DEMONSTRATE": "Show the described action with clear, continuous movement.",
            "RECAP": "Return to the subject and resolve the story with a calm movement.",
        }[purpose]
        return StoryboardSceneV1(
            scene_id=f"scene-{index + 1}",
            order=index + 1,
            segment_ids=tuple(segment.segment_id for segment in segments),
            narration_text=narration,
            visual_prompt=visual,
            motion_prompt=motion,
            approved_fact_ids=facts,
            confirmed_anchor_ids=anchors,
            duration_seconds=duration,
            duration_basis=basis,
        )


__all__ = ["StoryboardCompileInput", "StoryVideoPlanner"]
