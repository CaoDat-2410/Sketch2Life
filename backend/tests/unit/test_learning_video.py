"""FEAT-094 phase 4 and 5: a confirmed learning script goes straight to the video, spoken as written."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from sketch2life.application.video_pipeline.age_profile import MAX_SCENE_FRAMES
from sketch2life.application.video_pipeline.learning_timeline import (
    GROUND_CLAUSE,
    PLAIN_SETTING,
    STYLE_PREFIX,
    learning_profile,
    timeline_from_learning,
)
from sketch2life.application.video_pipeline.orchestrator import SENTENCE_PAUSE_MS
from sketch2life.application.video_pipeline.ports import VideoPipelineError

from test_learning_script import NARRATIONS, _learning
from test_video_pipeline_orchestrator import _Generator, _Prep, _Render, _pipeline, _source


def _learning_source(**changes: Any) -> Any:
    block = _learning()
    scenes = [
        {**entry, "title": f"Cảnh vườn {index}", "narration": text}
        for index, (entry, text) in enumerate(zip(block["scenes"], NARRATIONS, strict=True), start=1)
    ]
    return replace(
        _source(), learning={"title": "Gà Vàng trong vườn", "scenes": scenes}, **changes
    )


@pytest.mark.parametrize("months, scenes", [(48, 5), (84, 6), (114, 7)])
def test_every_age_band_fits_its_longest_narration_in_a_ten_second_scene(months: int, scenes: int) -> None:
    profile = learning_profile(months)

    assert (profile.scene_count, profile.scene_seconds, profile.dialogue_max_lines) == (scenes, 10, 0)
    longest_voice = profile.narration_max_words * 5.5 * 0.8 / ((profile.speech_cps_min + profile.speech_cps_max) / 2)
    assert longest_voice < 10 - 0.7
    assert profile.scene_seconds * 24 <= MAX_SCENE_FRAMES


def test_the_timeline_speaks_the_confirmed_text_with_open_ground_in_every_background() -> None:
    source = _learning_source()

    timeline = timeline_from_learning(source)

    assert [scene.narration.text for scene in timeline.scenes] == NARRATIONS
    assert timeline.total_ms == 50_000 and timeline.title == "Gà Vàng trong vườn"
    assert all(scene.dialogue == () and scene.interactions == () for scene in timeline.scenes)
    assert timeline.scenes[0].visual_prompt == "The chick pecks the ground gently."
    assert all(scene.background_prompt.endswith(GROUND_CLAUSE) for scene in timeline.scenes)
    assert all(len(scene.background_prompt) <= 300 for scene in timeline.scenes)
    assert set(timeline.scenes[0].subjects) == {"main", "sec-1"}


def test_every_background_asks_for_an_empty_crayon_scene_that_survives_the_drawn_only_guard() -> None:
    from sketch2life.application.video_pipeline.visual_prompt_guard import drawn_only_prompt

    background = timeline_from_learning(_learning_source()).scenes[0].background_prompt

    # The first live run painted photographs with a hand and dogs: the style has to be asked for.
    assert background.startswith(STYLE_PREFIX) and "crayon" in background.lower()
    assert "A sunny farm yard with green grass" in background
    guarded = drawn_only_prompt(background, person_drawn=False)
    assert guarded.startswith(STYLE_PREFIX) and GROUND_CLAUSE.strip() in guarded


def test_a_long_setting_keeps_the_ground_request() -> None:
    source = _learning_source()
    source.learning["scenes"][0]["setting_en"] = "A very wide garden with many trees " * 8

    background = timeline_from_learning(source).scenes[0].background_prompt

    assert background.endswith(GROUND_CLAUSE) and len(background) <= 300


def test_a_learning_video_needs_no_second_writing_model() -> None:
    class _Never(_Generator):
        def generate(self, request):
            raise AssertionError("the confirmed script must not be rewritten")

    prompts: list[str] = []

    class _Recording(_Render):
        def render(self, job):
            prompts.append(job.scene.visual_prompt)
            return super().render(job)

    pipeline, _ = _pipeline(render=_Recording(), prep=_Prep())
    pipeline._generator = _Never({})

    result = pipeline.run(_learning_source(), progress=None)

    assert len(prompts) == 5 and result.plan.total_ms >= 50_000
    spoken = [line.text for scene in result.plan.scenes for line in scene.lines]
    assert spoken == NARRATIONS
    assert " ".join(cue_text for cue_text in (cue.text for cue in result.cues)).split()[:3] == NARRATIONS[0].split()[:3]


def test_a_script_that_does_not_fit_the_childs_age_is_refused_with_a_code() -> None:
    source = _learning_source(age_months=84)  # six scenes expected, five confirmed

    pipeline, _ = _pipeline()
    with pytest.raises(VideoPipelineError) as error:
        pipeline.run(source)

    assert error.value.code.startswith("VIDEO_PLAN_")


def test_a_pause_separates_the_two_sentences_of_a_learning_scene() -> None:
    source = _learning_source()
    source.learning["scenes"][0]["narration"] = "Gà Vàng là một loài chim, ai cũng biết. Bạn ấy sống ở sân vườn."
    pipeline, _ = _pipeline()

    pipeline.run(source)

    first, comma, second = pipeline._assembler.job.chunks[:3]
    assert second.start_ms - (comma.start_ms + comma.duration_ms) >= SENTENCE_PAUSE_MS
    assert comma.start_ms - (first.start_ms + first.duration_ms) < SENTENCE_PAUSE_MS  # a comma is not a pause


def test_a_scene_that_teaches_a_part_is_labelled_with_its_name() -> None:
    pipeline, _ = _pipeline()

    pipeline.run(_learning_source())

    assert pipeline._assembler.job.part_labels == {2: "Mỏ"}


def test_an_ordinary_story_has_no_part_labels() -> None:
    pipeline, _ = _pipeline()

    pipeline.run(_source())

    assert pipeline._assembler.job.part_labels == {}


def test_a_setting_that_names_an_animal_is_not_sent_to_the_painter() -> None:
    source = _learning_source()
    source.learning["scenes"][1]["setting_en"] = "Close-up of the chicken near scattered grains on the ground."
    source.learning["scenes"][2]["setting_en"] = "A sunny field. Two ducks swim in a pond."

    backgrounds = [scene.background_prompt for scene in timeline_from_learning(source).scenes]

    assert "chicken" not in backgrounds[1] and PLAIN_SETTING in backgrounds[1]
    assert "A sunny field" in backgrounds[2] and "duck" not in backgrounds[2]
