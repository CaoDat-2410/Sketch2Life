from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from sketch2life.application.services.activity_supervision import (
    supervision_requirement_for_age,
)
from sketch2life.contracts.schemas.child_learning_profile import (
    ChildLearningProfileContextV1,
    ChildLearningProfileContextV2,
    P1ContextOptionsRequestV1,
    P1ContextOptionsRequestV2,
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


def test_v2_profile_accepts_material_ids_from_both_active_catalog_namespaces() -> None:
    profile = ChildLearningProfileContextV2(
        profile_declared_by="CAREGIVER",
        profile_recorded_at=datetime.now(UTC),
        available_material_option_ids=("MAT_PLANT_TRAY", "GMAT-0055-PRIMARY"),
    )

    assert profile.available_material_option_ids == (
        "MAT_PLANT_TRAY",
        "GMAT-0055-PRIMARY",
    )


def test_v2_request_requires_caregiver_for_under_three_and_keeps_36_month_boundary() -> None:
    profile = ChildLearningProfileContextV2(
        profile_declared_by="CAREGIVER",
        profile_recorded_at=datetime.now(UTC),
    )
    common = {
        "child_profile": profile,
        "adult_participating": True,
        "candidate_activity_ids": ("ACT-0001",),
        "supervision_confirmed_activity_ids": ("ACT-0001",),
    }

    with pytest.raises(ValidationError, match="participating caregiver"):
        P1ContextOptionsRequestV2(age_months=35, **common)

    under_three = P1ContextOptionsRequestV2(
        age_months=35,
        caregiver_participating=True,
        **common,
    )
    assert under_three.caregiver_participating is True

    age_three = P1ContextOptionsRequestV2(age_months=36, **common)
    assert age_three.caregiver_participating is False


def test_under_three_supervision_is_direct_caregiver_despite_weaker_catalog_minimum() -> None:
    assert supervision_requirement_for_age(35, "NEARBY") == (
        "DIRECT",
        "Người chăm sóc ở bên và giám sát trực tiếp",
    )
    assert supervision_requirement_for_age(36, "NEARBY") == (
        "NEARBY",
        "Người lớn ở gần",
    )
