from __future__ import annotations

import pytest

from sketch2life.application.services.whiteboard_storyboard import (
    WhiteboardStoryboardGenerator,
)


def test_cat_whiskers_storyboard_is_age_bounded_and_scene_grounded() -> None:
    storyboard = WhiteboardStoryboardGenerator().generate(
        subject_claim="con mèo",
        feature_claim="ria mèo",
        audience_band="EARLY_PRIMARY",
    )

    assert storyboard.topic_vi == "Ria mèo dùng để làm gì?"
    assert (storyboard.audience_age_min, storyboard.audience_age_max) == (6, 8)
    assert storyboard.duration_seconds == 14.0
    assert len(storyboard.scenes) == 4
    assert all(
        set(scene.source_claims) <= set(storyboard.source_claims)
        for scene in storyboard.scenes
    )


def test_storyboard_rejects_unreviewed_topic() -> None:
    with pytest.raises(ValueError, match="no reviewed whiteboard knowledge template"):
        WhiteboardStoryboardGenerator().generate(subject_claim="con voi", feature_claim="cái vòi")


def test_storyboard_resolves_p1_age_months_to_primary_band() -> None:
    storyboard = WhiteboardStoryboardGenerator().generate_for_age(
        subject_claim="con mèo",
        feature_claim="ria mèo",
        age_months=120,
    )

    assert (storyboard.audience_age_min, storyboard.audience_age_max) == (9, 12)


def test_storyboard_director_splits_approved_narration_into_scene_plan() -> None:
    storyboard = WhiteboardStoryboardGenerator().generate(
        subject_claim="con mèo",
        feature_claim="ria mèo",
        narration_vi=(
            "Mèo dùng ria để khám phá xung quanh. "
            "Ria giúp mèo cảm nhận vật ở gần. "
            "Vì vậy không nên cắt ria của mèo."
        ),
    )

    assert len(storyboard.scenes) == 3
    assert [scene.motion for scene in storyboard.scenes] == [
        "INTRO",
        "FOCUS",
        "DEMONSTRATE",
    ]
    assert sum(scene.duration_seconds for scene in storyboard.scenes) == storyboard.duration_seconds
    assert all("line-art whiteboard" in scene.visual_prompt_vi for scene in storyboard.scenes)


def test_storyboard_rejects_age_without_reviewed_audience_band() -> None:
    with pytest.raises(ValueError, match="no reviewed whiteboard audience band"):
        WhiteboardStoryboardGenerator().generate_for_age(
            subject_claim="con mèo",
            feature_claim="ria mèo",
            age_months=60,
        )
