"""Story timeline contract ``sketch2life.story-timeline.v1`` (FEAT-093 plan Rev 2, sections 8, 9, 16).

The script is written with narration and dialogue lines and their timestamps, so audio and scene timing
are planned before any rendering. This module only validates and projects; it never calls a model.
The master clock is the frame-exact millisecond timeline: scene windows are contiguous, start at 0, and
every boundary is the millisecond value of a whole frame at 24 fps.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from sketch2life.application.video_pipeline.age_profile import (
    MAX_SCENE_FRAMES,
    MAX_TOTAL_SECONDS,
    MIN_SCENE_FRAMES,
    MIN_TOTAL_SECONDS,
    AgeBandProfile,
    ms_to_frames,
    snap_ms_to_frame,
)

TIMELINE_SCHEMA: Final = "sketch2life.story-timeline.v1"
INTERACTION_KINDS: Final = ("consume", "transfer", "contact", "move", "transform")
SCENE_LENGTH_TOLERANCE_MS: Final = 2_000
MAX_TEXT_CHARS: Final = 240
MAX_PROMPT_CHARS: Final = 900
MAX_BACKGROUND_CHARS: Final = 300

_END_PUNCTUATION: Final = (".", "!", "?", "…")
_DANGLING_TAIL_WORDS: Final = frozenset(
    {
        "từ", "tự", "nếu", "khi", "và", "hoặc", "nhưng", "để", "với", "của", "trong", "ở", "cho",
        "bằng", "do", "theo", "đang", "là", "có", "rồi", "thì", "mà",
    }
)
_BANNED_FRAGMENTS: Final = (
    "giet", "mau me", "sung ", "chet", "ma quy", "kinh di", "tu tu", "danh nhau", "bao luc", "ruou", "thuoc la",
)


class TimelineError(ValueError):
    """A safe, content-free code naming the first broken rule."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class TimelineLine:
    text: str
    start_ms: int
    end_ms: int
    speaker_ref: str | None = None


@dataclass(frozen=True, slots=True)
class Interaction:
    kind: str
    actor: str
    target: str
    verb: str
    from_state: float
    to_state: float


@dataclass(frozen=True, slots=True)
class TimelineScene:
    index: int
    start_ms: int
    end_ms: int
    title: str
    action: str
    visual_prompt: str
    background_prompt: str
    narration: TimelineLine
    dialogue: tuple[TimelineLine, ...]
    subjects: tuple[str, ...]
    interactions: tuple[Interaction, ...]

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @property
    def voiced_lines(self) -> tuple[TimelineLine, ...]:
        return tuple(sorted((self.narration, *self.dialogue), key=lambda line: line.start_ms))


@dataclass(frozen=True, slots=True)
class StoryTimeline:
    title: str
    age_band: str
    scenes: tuple[TimelineScene, ...]

    @property
    def total_ms(self) -> int:
        return self.scenes[-1].end_ms if self.scenes else 0


def word_count(text: str) -> int:
    return len(text.split())


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join("".join(ch if ch.isalnum() else " " for ch in stripped).split())


def _has_non_latin_letter(text: str) -> bool:
    return any(ch.isalpha() and "LATIN" not in unicodedata.name(ch, "") for ch in text)


def check_line_text(text: Any) -> str:
    """The cleaned text of one spoken line, or a TimelineError."""

    if not isinstance(text, str):
        raise TimelineError("LINE_TEXT_INVALID")
    cleaned = " ".join(text.split())
    if not 3 <= len(cleaned) <= MAX_TEXT_CHARS:
        raise TimelineError("LINE_TEXT_LENGTH")
    if any(unicodedata.category(ch).startswith("C") for ch in cleaned):
        raise TimelineError("LINE_TEXT_CONTROL_CHARACTER")
    if _has_non_latin_letter(cleaned):
        raise TimelineError("LINE_TEXT_NON_LATIN_SCRIPT")
    folded = _fold(cleaned)
    if any(fragment in f"{folded} " for fragment in _BANNED_FRAGMENTS):
        raise TimelineError("LINE_TEXT_NOT_ALLOWED")
    body = cleaned.rstrip("".join(_END_PUNCTUATION)).rstrip(" ,;:-")
    words = body.split()
    if not words:
        raise TimelineError("LINE_TEXT_LENGTH")
    if words[-1].casefold() in _DANGLING_TAIL_WORDS:
        raise TimelineError("LINE_TEXT_DANGLING_WORD")
    if len(words[-1]) <= 2 and not any(ch in "aeiouyàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ"
                                       for ch in words[-1].casefold()):
        raise TimelineError("LINE_TEXT_CLIPPED_SYLLABLE")
    return cleaned


def _int(value: Any, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TimelineError(code)
    return value


def _line(raw: Any, *, window: tuple[int, int], max_words: int, dialogue: bool) -> TimelineLine:
    if not isinstance(raw, Mapping):
        raise TimelineError("LINE_SHAPE_INVALID")
    expected = {"text", "start_ms", "end_ms"} | ({"speaker_ref"} if dialogue else set())
    if set(raw) != expected:
        raise TimelineError("LINE_SHAPE_INVALID")
    text = check_line_text(raw["text"])
    if word_count(text) > max_words:
        raise TimelineError("LINE_TOO_MANY_WORDS")
    start = _int(raw["start_ms"], "LINE_TIME_INVALID")
    end = _int(raw["end_ms"], "LINE_TIME_INVALID")
    if not window[0] <= start < end <= window[1]:
        raise TimelineError("LINE_OUTSIDE_SCENE")
    speaker = None
    if dialogue:
        speaker = raw["speaker_ref"]
        if not isinstance(speaker, str) or not re.fullmatch(r"[a-z0-9-]{1,16}", speaker):
            raise TimelineError("LINE_SPEAKER_INVALID")
    return TimelineLine(text=text, start_ms=start, end_ms=end, speaker_ref=speaker)


def _interaction(raw: Any, *, subjects: Collection[str]) -> Interaction:
    if not isinstance(raw, Mapping) or set(raw) != {"kind", "actor", "target", "verb", "from_state", "to_state"}:
        raise TimelineError("INTERACTION_SHAPE_INVALID")
    kind, actor, target, verb = raw["kind"], raw["actor"], raw["target"], raw["verb"]
    if kind not in INTERACTION_KINDS:
        raise TimelineError("INTERACTION_KIND_INVALID")
    if actor not in subjects or target not in subjects or actor == target:
        raise TimelineError("INTERACTION_SUBJECT_INVALID")
    if not isinstance(verb, str) or not 1 <= len(verb.strip()) <= 40:
        raise TimelineError("INTERACTION_VERB_INVALID")
    states: list[float] = []
    for key in ("from_state", "to_state"):
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise TimelineError("INTERACTION_STATE_INVALID")
        states.append(float(value))
    if kind == "consume" and not states[1] < states[0]:
        raise TimelineError("INTERACTION_CONSUME_MUST_REDUCE")
    return Interaction(kind, actor, target, verb.strip(), states[0], states[1])


def _check_lanes(scene_index: int, lines: Sequence[TimelineLine]) -> None:
    # One neutral adult voice (SRS BR-24): narration and dialogue never overlap.
    ordered = sorted(lines, key=lambda line: line.start_ms)
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.start_ms < previous.end_ms:
            raise TimelineError(f"SCENE_{scene_index}_VOICE_OVERLAP")


def _check_continuity(scenes: Sequence[TimelineScene]) -> None:
    remaining: dict[str, float] = {}
    for scene in scenes:
        for interaction in scene.interactions:
            if interaction.kind != "consume":
                continue
            known = remaining.get(interaction.target)
            if known is not None and abs(interaction.from_state - known) > 1e-6:
                raise TimelineError("INTERACTION_LADDER_DISCONTINUITY")
            remaining[interaction.target] = interaction.to_state
    gone = {target for target, state in remaining.items() if state <= 0.0}
    for target in gone:
        last_gone_scene = max(
            scene.index
            for scene in scenes
            for interaction in scene.interactions
            if interaction.kind == "consume" and interaction.target == target and interaction.to_state <= 0.0
        )
        if any(target in scene.subjects for scene in scenes if scene.index > last_gone_scene):
            raise TimelineError("TARGET_REAPPEARS_AFTER_GONE")


def parse_timeline(
    raw: Any,
    *,
    profile: AgeBandProfile,
    entity_ids: Collection[str],
    main_entity_id: str = "main",
) -> StoryTimeline:
    """Validate a model-written timeline against the age band and the confirmed roles."""

    if not isinstance(raw, Mapping) or set(raw) != {"schema_version", "title", "age_band", "scenes"}:
        raise TimelineError("TIMELINE_SHAPE_INVALID")
    if raw["schema_version"] != TIMELINE_SCHEMA or raw["age_band"] != profile.band:
        raise TimelineError("TIMELINE_SCHEMA_INVALID")
    title = raw["title"]
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 100:
        raise TimelineError("TIMELINE_TITLE_INVALID")
    check_line_text(title.strip() + ".")
    raw_scenes = raw["scenes"]
    if not isinstance(raw_scenes, list) or len(raw_scenes) != profile.scene_count:
        raise TimelineError("TIMELINE_SCENE_COUNT")
    ids = set(entity_ids)
    if main_entity_id not in ids:
        raise TimelineError("TIMELINE_MAIN_SUBJECT_UNKNOWN")

    scenes: list[TimelineScene] = []
    previous_end = 0
    secondaries_used: set[str] = set()
    for position, item in enumerate(raw_scenes, start=1):
        keys = {
            "index", "start_ms", "end_ms", "title", "action", "visual_prompt", "background_prompt",
            "narration", "dialogue", "subjects", "interactions",
        }
        if not isinstance(item, Mapping) or set(item) != keys:
            raise TimelineError("SCENE_SHAPE_INVALID")
        if item["index"] != position:
            raise TimelineError("SCENE_INDEX_INVALID")
        start = _int(item["start_ms"], "SCENE_TIME_INVALID")
        end = _int(item["end_ms"], "SCENE_TIME_INVALID")
        if start != previous_end:
            raise TimelineError("SCENE_NOT_CONTIGUOUS")
        if snap_ms_to_frame(start) != start or snap_ms_to_frame(end) != end:
            raise TimelineError("SCENE_NOT_FRAME_ALIGNED")
        frames = ms_to_frames(end - start)
        if not MIN_SCENE_FRAMES <= frames <= MAX_SCENE_FRAMES:
            raise TimelineError("SCENE_LENGTH_INVALID")
        if abs((end - start) - profile.scene_seconds * 1000) > SCENE_LENGTH_TOLERANCE_MS:
            raise TimelineError("SCENE_LENGTH_OFF_AGE_BAND")
        scene_title, action = item["title"], item["action"]
        visual, background = item["visual_prompt"], item["background_prompt"]
        if not isinstance(scene_title, str) or not 1 <= len(scene_title.strip()) <= 100:
            raise TimelineError("SCENE_TITLE_INVALID")
        if not isinstance(action, str) or not 1 <= len(action.strip()) <= 500:
            raise TimelineError("SCENE_ACTION_INVALID")
        if not isinstance(visual, str) or not 8 <= len(visual.strip()) <= MAX_PROMPT_CHARS:
            raise TimelineError("SCENE_VISUAL_PROMPT_INVALID")
        if not isinstance(background, str) or not 8 <= len(background.strip()) <= MAX_BACKGROUND_CHARS:
            raise TimelineError("SCENE_BACKGROUND_PROMPT_INVALID")
        if _has_non_latin_letter(visual) or _has_non_latin_letter(background):
            raise TimelineError("SCENE_PROMPT_NON_LATIN_SCRIPT")

        narration = _line(item["narration"], window=(start, end), max_words=profile.narration_max_words, dialogue=False)
        raw_dialogue = item["dialogue"]
        if not isinstance(raw_dialogue, list) or len(raw_dialogue) > profile.dialogue_max_lines:
            raise TimelineError("SCENE_DIALOGUE_COUNT")
        dialogue = tuple(
            _line(entry, window=(start, end), max_words=profile.dialogue_max_words, dialogue=True)
            for entry in raw_dialogue
        )
        _check_lanes(position, (narration, *dialogue))

        subjects = item["subjects"]
        if (
            not isinstance(subjects, list)
            or not subjects
            or len(set(subjects)) != len(subjects)
            or any(not isinstance(value, str) or value not in ids for value in subjects)
        ):
            raise TimelineError("SCENE_SUBJECTS_INVALID")
        if main_entity_id not in subjects:
            raise TimelineError("SCENE_MAIN_SUBJECT_MISSING")
        secondaries_used.update(value for value in subjects if value != main_entity_id)
        raw_interactions = item["interactions"]
        if not isinstance(raw_interactions, list) or len(raw_interactions) > 4:
            raise TimelineError("SCENE_INTERACTIONS_INVALID")
        interactions = tuple(_interaction(entry, subjects=subjects) for entry in raw_interactions)

        scenes.append(
            TimelineScene(
                index=position,
                start_ms=start,
                end_ms=end,
                title=scene_title.strip(),
                action=action.strip(),
                visual_prompt=visual.strip(),
                background_prompt=background.strip(),
                narration=narration,
                dialogue=dialogue,
                subjects=tuple(subjects),
                interactions=interactions,
            )
        )
        previous_end = end

    if len(secondaries_used) > profile.secondary_max:
        raise TimelineError("TIMELINE_TOO_MANY_SECONDARY_SUBJECTS")
    total_ms = previous_end
    if not MIN_TOTAL_SECONDS * 1000 <= total_ms <= MAX_TOTAL_SECONDS * 1000:
        raise TimelineError("TIMELINE_TOTAL_OUTSIDE_SRS_WINDOW")
    _check_continuity(scenes)
    return StoryTimeline(title=title.strip(), age_band=profile.band, scenes=tuple(scenes))


__all__ = [
    "INTERACTION_KINDS",
    "Interaction",
    "StoryTimeline",
    "TIMELINE_SCHEMA",
    "TimelineError",
    "TimelineLine",
    "TimelineScene",
    "check_line_text",
    "parse_timeline",
    "word_count",
]
