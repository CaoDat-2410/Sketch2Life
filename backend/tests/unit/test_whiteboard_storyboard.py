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


def test_storyboard_rejects_age_without_reviewed_audience_band() -> None:
    with pytest.raises(ValueError, match="no reviewed whiteboard audience band"):
        WhiteboardStoryboardGenerator().generate_for_age(
            subject_claim="con mèo",
            feature_claim="ria mèo",
            age_months=60,
        )
