"""The video timeline of a confirmed learning script (FEAT-094 phase 4): no second writing model.

Every spoken line is the narration the adult confirmed; the pictures come from the script's own English action and
setting. The timeline still passes ``parse_timeline``, so the same text and timing rules hold as for a planned one.
"""

from __future__ import annotations

import re
from typing import Final

from sketch2life.application.video_pipeline.age_profile import AgeBandProfile
from sketch2life.application.video_pipeline.ports import VideoSource
from sketch2life.application.video_pipeline.story_timeline import (
    MAX_BACKGROUND_CHARS,
    StoryTimeline,
    TimelineError,
    parse_timeline,
)
from sketch2life.application.video_pipeline.timeline_planner import assign_timing

# FEAT-094 phase 5: subjects hung in front of tree trunks when the background had nowhere to stand.
GROUND_CLAUSE: Final = " Open flat ground in the lower third."
PLAIN_SETTING: Final = "A calm open place under a soft sky"
# An animal named in a background was painted as a second, large animal behind the child's own (live run 3). The script
# writer is asked not to name one; this is the check that does not depend on the model.
_ANIMAL: Final = re.compile(
    r"\b(animals?|chickens?|hens?|roosters?|chicks?|birds?|dogs?|pupp(y|ies)|cats?|kittens?|fish|butterfl(y|ies)|"
    r"bees?|ants?|rabbits?|bunn(y|ies)|horses?|elephants?|deer|turtles?|ducks?|ducklings?|owls?|parrots?|peacocks?|"
    r"sparrows?|doves?|pigeons?|swans?|caterpillars?|snails?|crabs?|dolphins?|octopus(es)?|seahorses?|whales?)\b",
    re.IGNORECASE,
)
# The script's setting names only a place. Without a style the image model painted photographs, with a hand and dogs
# in them. No word here may name a person: the drawn-only guard drops such sentences.
# "On paper" gave the backgrounds a white page edge, and one clip then grew a hand over the page.
STYLE_PREFIX: Final = "Full-frame crayon illustration to every edge, waxy strokes. Empty scenery with nothing alive:"

# Narration only, one adult voice (BR-24); 10 s scenes (plan 6.2). The caption rates are the age
# bands'. The speech rate is what the voice measured in the live runs (about 16 letters a second);
# it only plans the line windows, and the measured audio places every line (FEAT-098).
LEARNING_PROFILES: Final = (
    AgeBandProfile("36-71", 36, 71, 5, 10, 25, 0, 0, 3, 14.0, 18.0, 14.0),
    AgeBandProfile("72-107", 72, 107, 6, 10, 32, 0, 0, 3, 14.0, 18.0, 18.0),
    AgeBandProfile("108-120", 108, 120, 7, 10, 32, 0, 0, 3, 14.0, 18.0, 18.0),
)


def learning_profile(age_months: int) -> AgeBandProfile:
    for profile in LEARNING_PROFILES:
        if profile.min_months <= age_months <= profile.max_months:
            return profile
    raise ValueError("AGE_MONTHS_OUT_OF_RANGE")


def _background(setting: str) -> str:
    room = MAX_BACKGROUND_CHARS - len(STYLE_PREFIX) - len(GROUND_CLAUSE) - 2  # a space and the full stop
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(setting.split()))
    text = " ".join(item for item in sentences if not _ANIMAL.search(item)) or PLAIN_SETTING
    if len(text) > room:
        text = text[:room].rsplit(" ", 1)[0]
    return f"{STYLE_PREFIX} {text.rstrip(' .,;')}.{GROUND_CLAUSE}"


def timeline_from_learning(source: VideoSource) -> StoryTimeline:
    """The validated timeline of ``source.learning``, or ``TimelineError``."""

    learning = source.learning
    if not learning:
        raise TimelineError("TIMELINE_SCRIPT_MISSING")
    profile = learning_profile(source.age_months)
    subject_ids = [item.entity_id for item in source.subjects]
    main = next((item.entity_id for item in source.subjects if item.role == "main"), None)
    if main is None:
        raise TimelineError("TIMELINE_MAIN_SUBJECT_UNKNOWN")
    draft = {
        "title": learning.get("title"),
        "scenes": [
            {
                "title": scene["title"],
                "action": scene["narration"],
                "visual_prompt": scene["action_en"],
                "background_prompt": _background(scene["setting_en"]),
                "narration": scene["narration"],
                "dialogue": [],
                "subjects": subject_ids,
                "interactions": [],
            }
            for scene in learning["scenes"]
        ],
    }
    return parse_timeline(
        assign_timing(profile, draft), profile=profile, entity_ids=subject_ids, main_entity_id=main
    )


__all__ = [
    "GROUND_CLAUSE",
    "LEARNING_PROFILES",
    "PLAIN_SETTING",
    "STYLE_PREFIX",
    "learning_profile",
    "timeline_from_learning",
]
