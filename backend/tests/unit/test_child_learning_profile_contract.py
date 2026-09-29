from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.child_learning_profile import (
    ChildLearningProfileContextV1,
    P1ContextOptionsRequestV1,
)


def test_session_profile_is_versioned_bounded_and_has_no_identity_or_free_text_fields() -> None:
    profile = ChildLearningProfileContextV1(
        profile_declared_by="GUIDE",
        profile_recorded_at=datetime.now(UTC),
        interests=("PLANT_STRUCTURE",),
        dislikes=("SUN_LIGHT",),
        adult_confirmed_progress=(
            {
                "activity_id": "ACT-0055",
                "objective_id": "OBJ_SCIENTIFIC_OBSERVATION",
                "confirmed_at": date.today(),
                "confirmed_by": "GUIDE",
            },
        ),
    )
    assert profile.contract_name == "ChildLearningProfileContextV1"
    assert profile.adult_supervision_available == "NEARBY"
    assert "child_name" not in profile.model_dump()
    assert "notes" not in profile.model_dump()

    with pytest.raises(ValidationError):
        ChildLearningProfileContextV1.model_validate(
            {**profile.model_dump(mode="json"), "notes": "raw personal data"}
        )


def test_profile_rejects_duplicate_overlapping_or_future_selections() -> None:
    with pytest.raises(ValidationError, match="cannot also be a dislike"):
        ChildLearningProfileContextV1(
            profile_declared_by="CAREGIVER",
            profile_recorded_at=datetime.now(UTC),
            interests=("SUN_LIGHT",),
            dislikes=("SUN_LIGHT",),
        )


def test_profile_requires_timezone_aware_adult_declaration_recency() -> None:
    with pytest.raises(ValidationError, match="include a timezone"):
        ChildLearningProfileContextV1(
            profile_declared_by="CAREGIVER",
            profile_recorded_at=datetime.now().replace(tzinfo=None),
        )
    with pytest.raises(ValidationError, match="future-dated"):
        ChildLearningProfileContextV1(
            profile_declared_by="CAREGIVER",
            profile_recorded_at=datetime.now(UTC) + timedelta(minutes=2),
        )
    with pytest.raises(ValidationError, match="future-dated"):
        ChildLearningProfileContextV1(
            profile_declared_by="CAREGIVER",
            profile_recorded_at=datetime.now(UTC),
            adult_confirmed_progress=(
                {
                    "activity_id": "ACT-0055",
                    "objective_id": "OBJ_SCIENTIFIC_OBSERVATION",
                    "confirmed_at": date.today() + timedelta(days=1),
                    "confirmed_by": "CAREGIVER",
                },
            )
        )
    with pytest.raises(ValidationError):
        ChildLearningProfileContextV1(
            profile_declared_by="CAREGIVER",
            profile_recorded_at=datetime.now(UTC),
            interests=("free text about a child",),
        )


def test_context_options_request_requires_versioned_safe_profile_identifiers() -> None:
    request = P1ContextOptionsRequestV1(
        age_months=60,
        child_profile={
            "profile_declared_by": "CAREGIVER",
            "profile_recorded_at": datetime.now(UTC).isoformat(),
            "interests": ["ANIMAL_GENERIC"],
            "readiness_ids": [],
            "available_material_option_ids": [],
        },
    )
    assert request.contract_version == "1.0"
    assert request.child_profile is not None
    assert request.child_profile.readiness_ids == ()
    with pytest.raises(ValidationError):
        P1ContextOptionsRequestV1(
            age_months=60,
            child_profile={"available_material_option_ids": ["unreviewed material"]},
        )
