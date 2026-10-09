"""Provider-neutral storyboard compilation for the new illustrated-video flow."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Literal

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryboardDrawBeatV1,
    StoryboardPlanV1,
    StoryboardSceneV1,
    StoryScriptSegmentV1,
)
from sketch2life.contracts.schemas.story_world_v2 import (
    CameraStateV2,
    ScenePlanV2,
    StoryScenePlanV2,
    WorldModelV2,
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

        basis: Literal["MEASURED_TTS", "ESTIMATE"] = (
            "MEASURED_TTS" if measured is not None else "ESTIMATE"
        )
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
                durations[start:end],
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

    def compile_v2(
        self, request: StoryboardCompileInput, world: WorldModelV2
    ) -> StoryScenePlanV2:
        """Prototype only: plan explicit reviewed events, never infer approval from prose."""
        self._validate_segments(request.segments)
        if world.package_hash != request.package.package_hash:
            raise StoryWorldError("WORLD_PACKAGE_MISMATCH", "world is for another package")
        if any(event.approval_status != "APPROVED" for event in world.events):
            raise StoryWorldError("NEEDS_APPROVAL", "unreviewed event in world")
        segments = request.segments
        measured = request.measured_segment_durations
        if measured is not None and (
            len(measured) != len(segments) or any(t <= 0 for t in measured)
        ):
            raise StoryWorldError("NARRATION_TIMING_INVALID", "timing count or value is invalid")
        durations = measured or tuple(max(4.0, min(10.0, len(s.text) / 14)) for s in segments)
        total = round(sum(durations), 3)
        if not (
            request.package.target_duration_min_seconds
            <= total <= request.package.target_duration_max_seconds
        ):
            raise StoryWorldError(
                "DURATION_OUT_OF_RANGE", f"narration is {total}s, requires 40–60s"
            )
        event_by_segment = {
            segment.segment_id: tuple(e for e in world.events if e.segment_id == segment.segment_id)
            for segment in segments
        }
        if any(not group for group in event_by_segment.values()):
            raise StoryWorldError("NEEDS_APPROVAL", "every segment needs an approved event")
        if {event.segment_id for event in world.events} != set(event_by_segment):
            raise StoryWorldError("NEEDS_APPROVAL", "event references unrelated segment")
        event_keys = tuple(
            tuple(e.event_id for e in event_by_segment[s.segment_id]) for s in segments
        )

        @cache
        def solve(start: int, remaining: int):
            if start == len(segments):
                return (0.0, ()) if remaining == 0 else None
            if remaining <= 0:
                return None
            best = None
            for end in range(start + 1, min(len(segments), start + 8) + 1):
                seconds = sum(durations[start:end])
                if seconds > 20:
                    break
                if seconds < 5:
                    continue
                # Duration alone may not merge distinct approved events or purposes.
                if len(set(event_keys[start:end])) != 1 or len(
                    {s.scene_purpose for s in segments[start:end]}
                ) != 1:
                    continue
                continuation = solve(end, remaining - 1)
                if continuation is None:
                    continue
                candidate = (
                    (seconds - 10) ** 2 + continuation[0],
                    ((start, end),) + continuation[1],
                )
                if best is None or candidate < best:
                    best = candidate
            return best

        options = [solve(0, count) for count in range(3, 7)]
        valid = [option for option in options if option is not None]
        if not valid:
            raise StoryWorldError(
                "SCENE_PARTITION_IMPOSSIBLE",
                "approved event boundaries cannot form 3–6 scenes of 5–20s each",
            )
        states = world.initial_states
        scenes: list[ScenePlanV2] = []
        source_ids = {item.object_id for item in world.source_objects}
        added_ids = {item.object_id for item in world.narration_objects}
        for index, (start, end) in enumerate(min(valid)[1], 1):
            events = event_by_segment[segments[start].segment_id]
            if len(events) != 1:
                raise StoryWorldError("UNSUPPORTED_ACTION", "multiple actions within one segment")
            event = events[0]
            if not set(event.object_ids).issubset(source_ids | added_ids):
                raise StoryWorldError("NEEDS_APPROVAL", "event references unreviewed object")
            target_states = tuple(
                state.model_copy(update={
                    "x": event.target_positions.get(state.object_id, (state.x, state.y))[0],
                    "y": event.target_positions.get(state.object_id, (state.x, state.y))[1],
                    "scale": event.target_scales.get(state.object_id, state.scale),
                    "rotation_degrees": event.target_rotations.get(
                        state.object_id, state.rotation_degrees
                    ),
                    "action_ref": event.event_id,
                }) if state.object_id in event.object_ids else state
                for state in states
            )
            if event.camera_intent == "PAN" and event.target_positions:
                point = next(iter(event.target_positions.values()))
                camera = CameraStateV2(center_x=point[0], center_y=point[1])
            elif event.camera_intent == "ZOOM":
                camera = CameraStateV2(zoom=1.25)
            else:
                camera = CameraStateV2()
            scenes.append(ScenePlanV2(
                scene_id=f"scene-{index}", order=index,
                event_ids=(event.event_id,),
                segment_ids=tuple(segment.segment_id for segment in segments[start:end]),
                source_object_ids=tuple(item.object_id for item in world.source_objects),
                new_object_ids=tuple(obj for obj in event.object_ids if obj in added_ids),
                action=event.action, starting_states=states, target_states=target_states,
                draw_order=event.object_ids, camera=camera,
                transition_intent=event.transition_intent,
                duration_seconds=round(sum(durations[start:end]), 3),
            ))
            states = target_states
        return StoryScenePlanV2(
            package_hash=world.package_hash, scenes=tuple(scenes), duration_seconds=total
        )

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
        basis: Literal["MEASURED_TTS", "ESTIMATE"],
        segment_durations: tuple[float, ...],
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
        if any(segment.visual_cues for segment in segments) and not all(
            segment.visual_cues for segment in segments
        ):
            raise ValueError("every narration segment in a cued scene needs visual cues")
        draw_beats: list[StoryboardDrawBeatV1] = []
        cursor = 0.0
        for segment, segment_duration in zip(segments, segment_durations, strict=True):
            for cue_index, cue in enumerate(segment.visual_cues):
                start = round(cursor + segment_duration * cue_index / len(segment.visual_cues), 3)
                end = round(
                    cursor + segment_duration * (cue_index + 1) / len(segment.visual_cues), 3
                )
                draw_beats.append(StoryboardDrawBeatV1(
                    element_id=cue.element_id,
                    segment_id=segment.segment_id,
                    label=cue.label,
                    focus_box=cue.focus_box,
                    start_seconds=start,
                    end_seconds=end,
                ))
            cursor += segment_duration
        if draw_beats:
            draw_beats[-1] = draw_beats[-1].model_copy(update={"end_seconds": duration})
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
            "the same subject design across scenes while visibly changing the depicted "
            "action or relationship; do not redraw an unchanged source composition. "
            "Preserve the source drawing's identity and palette. An added action or "
            "object is permitted only when explicitly named in this approved scene "
            "narration or its visual cues. Do not add unsupported characters, props, "
            "labels, scenery, or colors. "
            f"Scene beat: {visual_beat} Approved narration: {narration}"
        )
        if draw_beats:
            visual += " Draw these script-specified elements in order: " + ", ".join(
                beat.label for beat in draw_beats
            ) + "."
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
            draw_beats=tuple(draw_beats),
        )


__all__ = ["StoryboardCompileInput", "StoryVideoPlanner"]
