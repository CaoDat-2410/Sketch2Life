"""Adult confirmation is projected onto a copy without rewriting the VLM snapshot."""

from __future__ import annotations

from sketch2life.infrastructure.persistence.parent_story_repository import (
    _project_confirmed_candidate,
)


def test_projects_confirmation_for_the_same_subject_without_mutating_source() -> None:
    original = {
        "candidate_subject": "butterfly",
        "decision": "REVIEW_REQUIRED",
        "visible_features": ["wings"],
    }

    projected = _project_confirmed_candidate(original, "butterfly")

    assert projected == {
        "candidate_subject": "butterfly",
        "decision": "CONFIRMED_BY_ADULT",
        "visible_features": ["wings"],
    }
    assert original["decision"] == "REVIEW_REQUIRED"


def test_projects_adult_correction_without_mutating_source() -> None:
    original = {"candidate_subject": "moth", "decision": "REVIEW_REQUIRED"}

    projected = _project_confirmed_candidate(original, "butterfly")

    assert projected == {
        "candidate_subject": "butterfly",
        "decision": "CORRECTED_BY_ADULT",
    }
    assert original == {"candidate_subject": "moth", "decision": "REVIEW_REQUIRED"}
