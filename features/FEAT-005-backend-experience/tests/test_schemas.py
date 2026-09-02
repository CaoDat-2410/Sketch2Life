import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from learning_video.schemas import (
    AssetType,
    GenerationBrief,
    LearningObjective,
    MicroVideoAsset,
    ReviewedAsset,
    ReviewedStillNarrationAsset,
)


FIXTURES = Path(__file__).parents[1] / "fixtures"


def read_fixture(relative_path: str) -> dict:
    return json.loads((FIXTURES / relative_path).read_text())


def test_learning_objective_contract_accepts_fixture() -> None:
    objective = LearningObjective.model_validate(read_fixture("objectives/butterfly_proboscis.json"))
    assert objective.objective_id == "butterfly_proboscis"
    assert objective.version == "v1"


def test_reviewed_video_asset_is_discriminated_correctly() -> None:
    entry = ReviewedAsset.model_validate(read_fixture("reviewed_assets/butterfly_video.json"))
    assert isinstance(entry.asset, MicroVideoAsset)
    assert entry.asset.asset_type is AssetType.MICRO_VIDEO
    assert entry.asset.review_status == "REVIEWED"


def test_reviewed_still_narration_asset_is_discriminated_correctly() -> None:
    entry = ReviewedAsset.model_validate(read_fixture("fallback_assets/butterfly_still_narration.json"))
    assert isinstance(entry.asset, ReviewedStillNarrationAsset)
    assert entry.asset.asset_type is AssetType.STILL_NARRATION


def test_generation_brief_requires_bounded_duration() -> None:
    brief = GenerationBrief.model_validate(read_fixture("objectives/butterfly_generation_brief.json"))
    assert 5 <= brief.duration_sec <= 10


def test_generation_brief_rejects_duration_outside_policy() -> None:
    data = read_fixture("objectives/butterfly_generation_brief.json")
    data["duration_sec"] = 11
    with pytest.raises(ValidationError):
        GenerationBrief.model_validate(data)


def test_contracts_reject_unknown_fields() -> None:
    data = read_fixture("objectives/butterfly_proboscis.json")
    data["personality"] = "not allowed"
    with pytest.raises(ValidationError):
        LearningObjective.model_validate(data)
