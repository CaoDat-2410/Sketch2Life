"""FEAT-093 block B: deterministic timing and the retrying planner."""

from __future__ import annotations

import copy

import pytest

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.story_timeline import TimelineError, check_line_text
from sketch2life.application.video_pipeline.timeline_planner import (
    PlannerSubject,
    assign_timing,
    build_timeline_request,
    estimate_line_ms,
    plan_timeline,
    scene_bounds,
)

PROFILE = profile_for_age_months(48)
SUBJECTS = [PlannerSubject("main", "con rùa", "main"), PlannerSubject("sec-1", "chiếc lá", "secondary")]


def _draft() -> dict:
    texts = [
        "Rùa con bò ra khỏi hang.",
        "Rùa thấy một chiếc lá xanh.",
        "Rùa cắn một miếng lá.",
        "Chiếc lá còn một nửa.",
        "Rùa ăn xong và mỉm cười.",
    ]
    ladders = [None, None, (1.0, 0.5), (0.5, 0.25), (0.25, 0.0)]
    scenes = []
    for index, text in enumerate(texts):
        step = ladders[index]
        scenes.append(
            {
                "title": f"Cảnh {index + 1}",
                "action": "Rùa con đi tìm thức ăn.",
                "visual_prompt": "A small turtle walks on green grass and looks at a leaf, crayon style.",
                "background_prompt": "A sunny garden with soft green hills, crayon texture, no characters.",
                "narration": text,
                "dialogue": [],
                "subjects": ["main", "sec-1"],
                "interactions": (
                    [{"kind": "consume", "actor": "main", "target": "sec-1", "verb": "ăn",
                      "from_state": step[0], "to_state": step[1]}] if step else []
                ),
            }
        )
    return {"title": "Rùa con và chiếc lá", "scenes": scenes}


class _Generator:
    def __init__(self, *drafts):
        self.drafts = list(drafts)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.drafts.pop(0)


def test_scene_bounds_are_frame_exact_and_contiguous() -> None:
    bounds = scene_bounds(PROFILE)

    assert bounds[0][0] == 0 and bounds[-1][1] == 30_000
    assert all(a[1] == b[0] for a, b in zip(bounds, bounds[1:], strict=False))


def test_line_timing_follows_the_age_band_speech_rate() -> None:
    short = estimate_line_ms("Chào nhé.", PROFILE)
    long = estimate_line_ms("Rùa con bò ra khỏi hang rồi nhìn quanh khu vườn.", PROFILE)

    assert short == 1_200 and long > short


def test_assign_timing_places_narration_first_then_dialogue_inside_the_scene() -> None:
    draft = copy.deepcopy(_draft())
    draft["scenes"][0]["dialogue"] = [{"speaker_ref": "rua", "text": "Chào lá nhé."}]

    timed = assign_timing(PROFILE, draft)

    scene = timed["scenes"][0]
    assert scene["narration"]["start_ms"] == 400
    assert scene["dialogue"][0]["start_ms"] > scene["narration"]["end_ms"]
    assert scene["dialogue"][0]["end_ms"] <= scene["end_ms"]


def test_a_scene_with_too_much_speech_does_not_fit() -> None:
    draft = copy.deepcopy(_draft())
    draft["scenes"][0]["narration"] = " ".join(["Rùa con bò ra khỏi hang xa xôi quá."] * 4)

    with pytest.raises(TimelineError) as error:
        assign_timing(PROFILE, draft)

    assert error.value.code == "SCENE_1_VOICE_DOES_NOT_FIT"


def test_the_planner_returns_a_validated_timeline() -> None:
    generator = _Generator(_draft())

    timeline = plan_timeline(
        profile=PROFILE, story={"title": "x"}, subjects=SUBJECTS, activity={"title": "t", "objective": "o"},
        topic="Động vật", generator=generator,
    )

    assert len(timeline.scenes) == 5 and timeline.total_ms == 30_000
    assert generator.requests[0]["previous_error"] is None


def test_the_planner_retries_once_with_the_broken_rule_code() -> None:
    broken = copy.deepcopy(_draft())
    broken["scenes"][0]["narration"] = "Rùa con đang bò và"
    generator = _Generator(broken, _draft())

    timeline = plan_timeline(
        profile=PROFILE, story={}, subjects=SUBJECTS, activity={}, topic="", generator=generator
    )

    assert len(timeline.scenes) == 5
    assert generator.requests[1]["previous_error"] == "LINE_TEXT_DANGLING_WORD"


def test_the_planner_gives_up_after_three_attempts_with_the_last_code() -> None:
    broken = copy.deepcopy(_draft())
    broken["scenes"][0]["narration"] = "Rùa con đang bò và"
    generator = _Generator(broken, copy.deepcopy(broken), copy.deepcopy(broken))

    with pytest.raises(TimelineError) as error:
        plan_timeline(profile=PROFILE, story={}, subjects=SUBJECTS, activity={}, topic="", generator=generator)

    assert error.value.code == "LINE_TEXT_DANGLING_WORD" and len(generator.requests) == 3


def test_the_request_carries_the_age_numbers_and_roles_only() -> None:
    request = build_timeline_request(
        profile=PROFILE, story={"title": "x"}, subjects=SUBJECTS, activity={"title": "t", "objective": "o", "x": 1},
        topic="Động vật",
    )

    assert request["age_band"]["scene_count"] == 5 and request["age_band"]["narration_max_words"] == 7
    assert request["subjects"][0] == {"entity_id": "main", "label": "con rùa", "role": "main"}
    assert set(request["activity"]) == {"title", "objective"}


@pytest.mark.parametrize("text", ["Đến nơi rồi.", "Xong rồi!"])
def test_a_line_ending_in_the_particle_for_done_is_complete(text: str) -> None:
    assert check_line_text(text) == text
