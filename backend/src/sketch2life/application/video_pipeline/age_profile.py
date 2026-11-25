"""Age bands of the Parent video (FEAT-093 plan Rev 2, section 16.1; SRS BR-24).

One table drives the story prompt, the timeline parser, the plan builder and the tests. The hard limits are
the SRS and worker limits: 30-90 s total, 5-15 scenes, 24 fps, scene length at most 473 frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

FPS: Final = 24
MIN_TOTAL_SECONDS: Final = 30
MAX_TOTAL_SECONDS: Final = 90
MIN_SCENES: Final = 5
MAX_SCENES: Final = 15
MAX_SCENE_FRAMES: Final = 473
MIN_SCENE_FRAMES: Final = 25


@dataclass(frozen=True, slots=True)
class AgeBandProfile:
    band: str
    min_months: int
    max_months: int
    scene_count: int
    scene_seconds: int
    narration_max_words: int
    dialogue_max_lines: int
    dialogue_max_words: int
    secondary_max: int
    speech_cps_min: float  # narration speed in characters per second (TTS quality gate)
    speech_cps_max: float
    caption_max_cps: float  # reading speed on screen

    @property
    def total_seconds(self) -> int:
        return self.scene_count * self.scene_seconds


AGE_BANDS: Final[tuple[AgeBandProfile, ...]] = (
    AgeBandProfile("36-71", 36, 71, 5, 6, 9, 1, 5, 1, 9.0, 13.0, 14.0),
    AgeBandProfile("72-107", 72, 107, 7, 6, 14, 2, 8, 2, 10.0, 15.0, 18.0),
    AgeBandProfile("108-120", 108, 120, 9, 6, 20, 3, 12, 3, 11.0, 16.0, 18.0),
)


def profile_for_age_months(age_months: int) -> AgeBandProfile:
    if isinstance(age_months, bool) or not isinstance(age_months, int):
        raise ValueError("AGE_MONTHS_INVALID")
    for profile in AGE_BANDS:
        if profile.min_months <= age_months <= profile.max_months:
            return profile
    raise ValueError("AGE_MONTHS_OUT_OF_RANGE")


def profile_for_band(band: str) -> AgeBandProfile:
    for profile in AGE_BANDS:
        if profile.band == band:
            return profile
    raise ValueError("AGE_BAND_UNKNOWN")


def ms_to_frames(milliseconds: int) -> int:
    return round(milliseconds * FPS / 1000)


def frames_to_ms(frames: int) -> int:
    return round(frames * 1000 / FPS)


def snap_ms_to_frame(milliseconds: int) -> int:
    """The millisecond value of the nearest whole frame (the master clock is frame-exact)."""

    return frames_to_ms(ms_to_frames(milliseconds))


def _validate_table() -> None:
    for profile in AGE_BANDS:
        total = profile.total_seconds
        if not MIN_TOTAL_SECONDS <= total <= MAX_TOTAL_SECONDS:
            raise AssertionError(f"{profile.band}: total {total}s outside the SRS window")
        if not MIN_SCENES <= profile.scene_count <= MAX_SCENES:
            raise AssertionError(f"{profile.band}: scene count outside the SRS window")
        if ms_to_frames(profile.scene_seconds * 1000) > MAX_SCENE_FRAMES:
            raise AssertionError(f"{profile.band}: scene longer than the worker allows")


_validate_table()

__all__ = [
    "AGE_BANDS",
    "AgeBandProfile",
    "FPS",
    "MAX_SCENES",
    "MIN_SCENES",
    "frames_to_ms",
    "ms_to_frames",
    "profile_for_age_months",
    "profile_for_band",
    "snap_ms_to_frame",
]
