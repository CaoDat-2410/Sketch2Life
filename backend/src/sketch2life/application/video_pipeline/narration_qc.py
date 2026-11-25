"""Narration text normalisation and deterministic audio checks (FEAT-093 plan Rev 2, section 8, S5).

No speech recogniser is used (owner decision D1). The checks cover what can go wrong without one: empty or clipped
audio, long silences at the edges, a speech rate outside the age band, and a line that does not fit its scene window.
Standard library only (``wave`` and ``array``) so the checks run in the API worker without extra dependencies.
"""

from __future__ import annotations

import io
import re
import unicodedata
import wave
from array import array
from dataclasses import dataclass
from typing import Final

from sketch2life.application.video_pipeline.age_profile import AgeBandProfile

SILENCE_THRESHOLD: Final = 330  # about 1 % of 16-bit full scale
CLIP_LEVEL: Final = 32_700
MAX_CLIPPED_RATIO: Final = 0.001
MAX_EDGE_SILENCE_MS: Final = 600
MIN_AUDIO_MS: Final = 300
WINDOW_STRETCH_TOLERANCE: Final = 0.15

_DIGITS = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")


def number_to_vietnamese(value: int) -> str:
    """Spoken form of 0..999 (what a child's story needs); larger numbers are read digit by digit."""

    if value < 0:
        raise ValueError("NUMBER_NEGATIVE")
    if value >= 1000:
        return " ".join(_DIGITS[int(ch)] for ch in str(value))
    if value < 10:
        return _DIGITS[value]
    if value < 20:
        return "mười" if value == 10 else "mười " + ("lăm" if value == 15 else _DIGITS[value - 10])
    if value < 100:
        tens, unit = divmod(value, 10)
        head = f"{_DIGITS[tens]} mươi"
        if unit == 0:
            return head
        if unit == 1:
            return f"{head} mốt"
        if unit == 5:
            return f"{head} lăm"
        return f"{head} {_DIGITS[unit]}"
    hundreds, rest = divmod(value, 100)
    head = f"{_DIGITS[hundreds]} trăm"
    if rest == 0:
        return head
    if rest < 10:
        return f"{head} lẻ {_DIGITS[rest]}"
    return f"{head} {number_to_vietnamese(rest)}"


@dataclass(frozen=True, slots=True)
class NormalizedText:
    display: str
    spoken: str

    @property
    def changed(self) -> bool:
        return self.display != self.spoken


def normalize_for_tts(text: str) -> NormalizedText:
    """Spoken text for the synthesiser; the display text (captions) is never changed."""

    display = " ".join(text.split())
    spoken = re.sub(r"\d+", lambda match: number_to_vietnamese(int(match.group())) if len(match.group()) <= 3
                    else " ".join(_DIGITS[int(ch)] for ch in match.group()), display)
    spoken = "".join(
        ch for ch in spoken
        if ch.isalnum() or ch.isspace() or ch in ",.;:!?…-'’\"()" or unicodedata.category(ch).startswith("M")
    )
    spoken = " ".join(spoken.split())
    return NormalizedText(display=display, spoken=spoken)


def speech_rate_cps(spoken_text: str, duration_ms: int) -> float:
    letters = sum(1 for ch in spoken_text if ch.isalnum())
    return letters / (duration_ms / 1000) if duration_ms > 0 else 0.0


@dataclass(frozen=True, slots=True)
class AudioReport:
    duration_ms: int
    sample_rate: int
    channels: int
    peak: int
    clipped_ratio: float
    leading_silence_ms: int
    trailing_silence_ms: int


def analyse_wav(data: bytes) -> AudioReport:
    """Measurements of a 16-bit PCM WAV; anything else is rejected with a safe code."""

    try:
        with wave.open(io.BytesIO(data), "rb") as reader:
            channels = reader.getnchannels()
            width = reader.getsampwidth()
            rate = reader.getframerate()
            frames = reader.getnframes()
            raw = reader.readframes(frames)
    except (wave.Error, EOFError):
        raise ValueError("AUDIO_NOT_WAV") from None
    if width != 2 or channels not in (1, 2) or rate < 8_000 or frames == 0:
        raise ValueError("AUDIO_FORMAT_UNSUPPORTED")
    samples = array("h")
    samples.frombytes(raw)
    if channels == 2:
        samples = array("h", (max(samples[i], samples[i + 1], key=abs) for i in range(0, len(samples) - 1, 2)))
    peak = max((abs(value) for value in samples), default=0)
    clipped = sum(1 for value in samples if abs(value) >= CLIP_LEVEL)

    def silent_run(sequence: array) -> int:
        count = 0
        for value in sequence:
            if abs(value) >= SILENCE_THRESHOLD:
                break
            count += 1
        return count

    lead = silent_run(samples)
    reversed_samples = array("h", reversed(samples))
    trail = silent_run(reversed_samples)
    return AudioReport(
        duration_ms=round(len(samples) * 1000 / rate),
        sample_rate=rate,
        channels=channels,
        peak=peak,
        clipped_ratio=clipped / len(samples) if samples else 0.0,
        leading_silence_ms=round(lead * 1000 / rate),
        trailing_silence_ms=round(trail * 1000 / rate),
    )


def audio_problems(
    report: AudioReport, *, spoken_text: str, profile: AgeBandProfile, expected_sample_rate: int | None = None
) -> list[str]:
    problems: list[str] = []
    if report.duration_ms < MIN_AUDIO_MS or report.peak < SILENCE_THRESHOLD * 4:
        problems.append("AUDIO_EMPTY_OR_TOO_QUIET")
    if expected_sample_rate is not None and report.sample_rate != expected_sample_rate:
        problems.append("AUDIO_SAMPLE_RATE")
    if report.clipped_ratio > MAX_CLIPPED_RATIO:
        problems.append("AUDIO_CLIPPING")
    if report.leading_silence_ms > MAX_EDGE_SILENCE_MS or report.trailing_silence_ms > MAX_EDGE_SILENCE_MS:
        problems.append("AUDIO_EDGE_SILENCE")
    speech_ms = report.duration_ms - report.leading_silence_ms - report.trailing_silence_ms
    rate = speech_rate_cps(spoken_text, speech_ms)
    if rate and not profile.speech_cps_min <= rate <= profile.speech_cps_max:
        problems.append("AUDIO_SPEECH_RATE_OUT_OF_BAND")
    return problems


@dataclass(frozen=True, slots=True)
class WindowFit:
    decision: str  # "OK" | "STRETCH_SCENE" | "SHORTEN_TEXT"
    extra_ms: int


def fit_window(audio_ms: int, window_ms: int, *, tolerance: float = WINDOW_STRETCH_TOLERANCE) -> WindowFit:
    """Does a rendered line fit the time the script gave it?"""

    if audio_ms <= window_ms:
        return WindowFit("OK", 0)
    if audio_ms <= window_ms * (1 + tolerance):
        return WindowFit("STRETCH_SCENE", audio_ms - window_ms)
    return WindowFit("SHORTEN_TEXT", audio_ms - window_ms)


__all__ = [
    "AudioReport",
    "NormalizedText",
    "WindowFit",
    "analyse_wav",
    "audio_problems",
    "fit_window",
    "normalize_for_tts",
    "number_to_vietnamese",
    "speech_rate_cps",
]
