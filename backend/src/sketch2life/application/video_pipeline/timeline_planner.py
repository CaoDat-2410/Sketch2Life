"""From a confirmed story to a validated timeline (FEAT-093 plan Rev 2, sections 6, 8, 16; Amendment C).

The model writes the lines and the actions (no timestamps). This module places the lines on the master clock with the
age band's speech rate, so every timestamp is deterministic and frame-exact, then validates the whole timeline with
``parse_timeline``. If a rule fails the planner asks the model again (three attempts in all), naming the broken rule (never the content).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Protocol

from sketch2life.application.video_pipeline.age_profile import (
    AgeBandProfile,
    frames_to_ms,
    ms_to_frames,
)
from sketch2life.application.video_pipeline.story_timeline import (
    TIMELINE_SCHEMA,
    StoryTimeline,
    TimelineError,
    parse_timeline,
)

LEAD_IN_MS: Final = 400
VOICE_GAP_MS: Final = 300
TAIL_MS: Final = 300
MIN_LINE_MS: Final = 1_200
MAX_ATTEMPTS: Final = 3


class VideoTimelineGeneratorPort(Protocol):
    """The model behind the timeline: returns the untimed scenes for the request, or raises."""

    def generate(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class PlannerSubject:
    entity_id: str
    label: str
    role: str  # "main" | "secondary"


def estimate_line_ms(text: str, profile: AgeBandProfile) -> int:
    """How long a line takes to speak at the middle of the age band's speech rate."""

    letters = sum(1 for ch in text if ch.isalnum())
    rate = (profile.speech_cps_min + profile.speech_cps_max) / 2
    return max(MIN_LINE_MS, round(letters / rate * 1000))


def scene_bounds(profile: AgeBandProfile) -> list[tuple[int, int]]:
    """Frame-exact ``(start_ms, end_ms)`` of every scene."""

    frames_per_scene = ms_to_frames(profile.scene_seconds * 1000)
    return [
        (frames_to_ms(index * frames_per_scene), frames_to_ms((index + 1) * frames_per_scene))
        for index in range(profile.scene_count)
    ]


def assign_timing(profile: AgeBandProfile, draft: Mapping[str, Any]) -> dict[str, Any]:
    """The timeline document for an untimed model draft (narration first, then the dialogue lines)."""

    scenes = draft.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != profile.scene_count:
        raise TimelineError("TIMELINE_SCENE_COUNT")
    timed: list[dict[str, Any]] = []
    for position, (scene, (start, end)) in enumerate(zip(scenes, scene_bounds(profile), strict=True), start=1):
        if not isinstance(scene, Mapping):
            raise TimelineError("SCENE_SHAPE_INVALID")
        narration_text = scene.get("narration")
        dialogue = scene.get("dialogue")
        if not isinstance(narration_text, str) or not isinstance(dialogue, list):
            raise TimelineError("SCENE_SHAPE_INVALID")
        cursor = start + LEAD_IN_MS
        narration_end = cursor + estimate_line_ms(narration_text, profile)
        narration = {"text": narration_text, "start_ms": cursor, "end_ms": narration_end}
        cursor = narration_end + VOICE_GAP_MS
        lines: list[dict[str, Any]] = []
        for entry in dialogue:
            if not isinstance(entry, Mapping) or not isinstance(entry.get("text"), str):
                raise TimelineError("LINE_SHAPE_INVALID")
            line_end = cursor + estimate_line_ms(entry["text"], profile)
            lines.append(
                {"speaker_ref": entry.get("speaker_ref"), "text": entry["text"], "start_ms": cursor, "end_ms": line_end}
            )
            cursor = line_end + VOICE_GAP_MS
        if cursor - VOICE_GAP_MS > end - TAIL_MS:
            raise TimelineError(f"SCENE_{position}_VOICE_DOES_NOT_FIT")
        timed.append(
            {
                "index": position,
                "start_ms": start,
                "end_ms": end,
                "title": scene.get("title"),
                "action": scene.get("action"),
                "visual_prompt": scene.get("visual_prompt"),
                "background_prompt": scene.get("background_prompt"),
                "narration": narration,
                "dialogue": lines,
                "subjects": scene.get("subjects"),
                "interactions": scene.get("interactions"),
            }
        )
    return {
        "schema_version": TIMELINE_SCHEMA,
        "title": draft.get("title"),
        "age_band": profile.band,
        "scenes": timed,
    }


def build_timeline_request(
    *,
    profile: AgeBandProfile,
    story: Mapping[str, Any],
    subjects: Sequence[PlannerSubject],
    activity: Mapping[str, Any],
    topic: str,
    previous_error: str | None = None,
) -> dict[str, Any]:
    """The bounded request for the model: numbers from the age table, the story, the roles, the activity."""

    return {
        "schema_version": "sketch2life.video-timeline-request.v1",
        "age_band": {
            "band": profile.band,
            "scene_count": profile.scene_count,
            "scene_seconds": profile.scene_seconds,
            "narration_max_words": profile.narration_max_words,
            "dialogue_max_lines": profile.dialogue_max_lines,
            "dialogue_max_words": profile.dialogue_max_words,
            "secondary_max": profile.secondary_max,
        },
        "topic": topic,
        "story": dict(story),
        "subjects": [
            {"entity_id": item.entity_id, "label": item.label, "role": item.role} for item in subjects
        ],
        "activity": {"title": activity.get("title", ""), "objective": activity.get("objective", "")},
        "previous_error": previous_error,
    }


def plan_timeline(
    *,
    profile: AgeBandProfile,
    story: Mapping[str, Any],
    subjects: Sequence[PlannerSubject],
    activity: Mapping[str, Any],
    topic: str,
    generator: VideoTimelineGeneratorPort,
    max_attempts: int = MAX_ATTEMPTS,
) -> StoryTimeline:
    """Ask the model, place the lines, validate; retry with the broken rule's code, then fail with it."""

    entity_ids: Collection[str] = [item.entity_id for item in subjects]
    main = next((item.entity_id for item in subjects if item.role == "main"), None)
    if main is None:
        raise TimelineError("TIMELINE_MAIN_SUBJECT_UNKNOWN")
    last_error: str | None = None
    for _attempt in range(max_attempts):
        request = build_timeline_request(
            profile=profile, story=story, subjects=subjects, activity=activity, topic=topic, previous_error=last_error
        )
        draft = generator.generate(request)
        try:
            return parse_timeline(
                assign_timing(profile, draft), profile=profile, entity_ids=entity_ids, main_entity_id=main
            )
        except TimelineError as error:
            last_error = error.code
    raise TimelineError(last_error or "TIMELINE_INVALID")


__all__ = [
    "PlannerSubject",
    "VideoTimelineGeneratorPort",
    "assign_timing",
    "build_timeline_request",
    "estimate_line_ms",
    "plan_timeline",
    "scene_bounds",
]
