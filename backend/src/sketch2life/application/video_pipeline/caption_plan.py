"""Closed captions that match the video exactly (FEAT-093 plan Rev 2, Amendment A section 15.2).

The story timeline is the single clock. Each spoken line is split into clauses; the text-to-speech worker renders
one audio chunk per clause, so the real duration of every clause is known without any speech recogniser. Cues start
where the assembler places a chunk and end where the chunk ends. When no audio exists (a plan before rendering) the
line window is shared between clauses in proportion to their word count.

Pure code: no model, storage or framework.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from sketch2life.application.video_pipeline.story_timeline import TimelineLine

CLAUSE_GAP_MS: Final = 120  # silence the assembler leaves between two chunks of one line
HOLD_MS: Final = 200  # a cue may stay up this long after its audio, never past the next cue or the window
MIN_CUE_MS: Final = 1_200
MAX_LINES: Final = 2
MAX_LINE_CHARS: Final = 32
_CLAUSE_END = re.compile(r"(?<=[,;:.!?…])\s+|\s+[—–-]\s+")


@dataclass(frozen=True, slots=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str
    lane: str  # "narration" | "dialogue"
    speaker_ref: str | None = None


@dataclass(frozen=True, slots=True)
class LineAudio:
    """One spoken line placed on the master clock, with the measured clause durations when audio exists."""

    line: TimelineLine
    lane: str
    placed_start_ms: int
    clause_durations_ms: tuple[int, ...] | None = None


class CaptionError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def split_clauses(text: str) -> list[str]:
    """Clauses of a display text at punctuation; one-word clauses are merged into the next one."""

    parts = [part.strip() for part in _CLAUSE_END.split(" ".join(text.split())) if part.strip()]
    merged: list[str] = []
    for part in parts:
        if merged and len(merged[-1].split()) < 2:
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    if len(merged) > 1 and len(merged[-1].split()) < 2:
        tail = merged.pop()
        merged[-1] = f"{merged[-1]} {tail}"
    return merged or [" ".join(text.split())]


def wrap_caption(text: str, *, max_chars: int = MAX_LINE_CHARS) -> list[str]:
    """Greedy word wrap; a single word longer than ``max_chars`` stays on its own line."""

    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fits(text: str) -> bool:
    lines = wrap_caption(text)
    return len(lines) <= MAX_LINES and all(len(line) <= MAX_LINE_CHARS for line in lines)


def _split_to_fit(text: str) -> list[str]:
    """Split a clause that does not fit two caption lines into word groups that do."""

    if _fits(text):
        return [text]
    words = text.split()
    groups: list[list[str]] = [[]]
    for word in words:
        candidate = " ".join([*groups[-1], word])
        if groups[-1] and not _fits(candidate):
            groups.append([word])
        else:
            groups[-1].append(word)
    return [" ".join(group) for group in groups]


def _shares(total_ms: int, weights: Sequence[int]) -> list[int]:
    weight_sum = sum(weights) or 1
    shares = [total_ms * weight // weight_sum for weight in weights]
    shares[-1] += total_ms - sum(shares)
    return shares


def build_cues(
    lines: Sequence[LineAudio], *, speaker_labels: Mapping[str, str] | None = None
) -> list[Cue]:
    """Cues for every placed line, in time order."""

    labels = speaker_labels or {}
    cues: list[Cue] = []
    for placed in lines:
        clauses = split_clauses(placed.line.text)
        if placed.clause_durations_ms is not None:
            if len(placed.clause_durations_ms) != len(clauses) or any(d <= 0 for d in placed.clause_durations_ms):
                raise CaptionError("CLAUSE_DURATIONS_MISMATCH")
            starts: list[int] = []
            cursor = placed.placed_start_ms
            for duration in placed.clause_durations_ms:
                starts.append(cursor)
                cursor += duration + CLAUSE_GAP_MS
            spans = [(start, start + duration) for start, duration in zip(starts, placed.clause_durations_ms, strict=True)]
        else:
            window = placed.line.end_ms - placed.line.start_ms
            durations = _shares(window, [len(clause.split()) for clause in clauses])
            spans = []
            cursor = placed.line.start_ms
            for duration in durations:
                spans.append((cursor, cursor + duration))
                cursor += duration
        window_end = placed.line.end_ms if placed.clause_durations_ms is None else max(spans[-1][1], placed.line.end_ms)
        prefix = ""
        if placed.lane == "dialogue" and placed.line.speaker_ref in labels:
            prefix = f"{labels[placed.line.speaker_ref]}: "
        for position, (clause, (start, end)) in enumerate(zip(clauses, spans, strict=True)):
            next_start = spans[position + 1][0] if position + 1 < len(spans) else window_end
            end = min(end + HOLD_MS, max(end, next_start)) if placed.clause_durations_ms is not None else end
            pieces = _split_to_fit(clause)
            lengths = _shares(end - start, [len(item.split()) for item in pieces])
            offset = 0
            for index, piece in enumerate(pieces):
                text = f"{prefix}{piece}" if position == 0 and index == 0 else piece
                cues.append(
                    Cue(start + offset, start + offset + lengths[index], text, placed.lane, placed.line.speaker_ref)
                )
                offset += lengths[index]
    return sorted(cues, key=lambda cue: (cue.start_ms, cue.end_ms))


def extend_short_cues(cues: Sequence[Cue], *, duration_ms: int, min_ms: int = MIN_CUE_MS) -> list[Cue]:
    """Stretch cues shorter than ``min_ms`` into free time before the next cue or the end of the video."""

    result: list[Cue] = []
    for position, cue in enumerate(cues):
        limit = cues[position + 1].start_ms - 40 if position + 1 < len(cues) else duration_ms
        end = cue.end_ms
        if end - cue.start_ms < min_ms:
            end = max(end, min(cue.start_ms + min_ms, limit))
        result.append(Cue(cue.start_ms, end, cue.text, cue.lane, cue.speaker_ref))
    return result


def lint_cues(
    cues: Sequence[Cue], *, duration_ms: int, max_cps: float, min_ms: int = MIN_CUE_MS
) -> list[str]:
    """Violations (codes with the cue index) of the caption rules for children; empty means clean."""

    problems: list[str] = []
    for index, cue in enumerate(cues):
        length = cue.end_ms - cue.start_ms
        if cue.start_ms < 0 or cue.end_ms > duration_ms or length <= 0:
            problems.append(f"CUE_{index}_OUTSIDE_VIDEO")
        if length < min_ms:
            problems.append(f"CUE_{index}_TOO_SHORT")
        if length > 0 and len(cue.text) / (length / 1000) > max_cps:
            problems.append(f"CUE_{index}_TOO_FAST")
        lines = wrap_caption(cue.text)
        if len(lines) > MAX_LINES or any(len(line) > MAX_LINE_CHARS for line in lines):
            problems.append(f"CUE_{index}_TOO_LONG")
    for index, (previous, current) in enumerate(zip(cues, cues[1:], strict=False), start=1):
        if current.start_ms < previous.end_ms:
            problems.append(f"CUE_{index}_OVERLAP")
    return problems


def cue_words_match_script(lines: Sequence[TimelineLine], cues: Sequence[Cue], *, speaker_labels: Mapping[str, str] | None = None) -> bool:
    """True when the cue texts spell exactly the script words, in order (labels excluded)."""

    labels = {f"{value}:" for value in (speaker_labels or {}).values()}
    spoken = [word for line in lines for word in line.text.split()]
    shown = [word for cue in cues for word in cue.text.split() if word not in labels]
    return spoken == shown


def to_webvtt(cues: Sequence[Cue]) -> str:
    def stamp(milliseconds: int) -> str:
        hours, rest = divmod(milliseconds, 3_600_000)
        minutes, rest = divmod(rest, 60_000)
        seconds, millis = divmod(rest, 1_000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

    blocks = ["WEBVTT", ""]
    for index, cue in enumerate(cues, start=1):
        blocks.append(str(index))
        blocks.append(f"{stamp(cue.start_ms)} --> {stamp(cue.end_ms)}")
        blocks.extend(wrap_caption(cue.text))
        blocks.append("")
    return "\n".join(blocks)


__all__ = [
    "CLAUSE_GAP_MS",
    "CaptionError",
    "Cue",
    "LineAudio",
    "build_cues",
    "cue_words_match_script",
    "extend_short_cues",
    "lint_cues",
    "split_clauses",
    "to_webvtt",
    "wrap_caption",
]
