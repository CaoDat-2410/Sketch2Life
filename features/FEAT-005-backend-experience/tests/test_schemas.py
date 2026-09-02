import json
from pathlib import Path

import unittest
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


class SchemaTest(unittest.TestCase):
  def test_learning_objective_contract_accepts_fixture(self) -> None:
    objective = LearningObjective.model_validate(read_fixture("objectives/butterfly_proboscis.json"))
    self.assertEqual(objective.objective_id, "butterfly_proboscis")
    self.assertEqual(objective.version, "v1")


  def test_reviewed_video_asset_is_discriminated_correctly(self) -> None:
    entry = ReviewedAsset.model_validate(read_fixture("reviewed_assets/butterfly_video.json"))
    self.assertIsInstance(entry.asset, MicroVideoAsset)
    self.assertIs(entry.asset.asset_type, AssetType.MICRO_VIDEO)
    self.assertEqual(entry.asset.review_status, "REVIEWED")


  def test_reviewed_still_narration_asset_is_discriminated_correctly(self) -> None:
    entry = ReviewedAsset.model_validate(read_fixture("fallback_assets/butterfly_still_narration.json"))
    self.assertIsInstance(entry.asset, ReviewedStillNarrationAsset)
    self.assertIs(entry.asset.asset_type, AssetType.STILL_NARRATION)


  def test_generation_brief_requires_bounded_duration(self) -> None:
    brief = GenerationBrief.model_validate(read_fixture("objectives/butterfly_generation_brief.json"))
    self.assertTrue(5 <= brief.duration_sec <= 10)


  def test_generation_brief_rejects_duration_outside_policy(self) -> None:
    data = read_fixture("objectives/butterfly_generation_brief.json")
    data["duration_sec"] = 11
    with self.assertRaises(ValidationError):
        GenerationBrief.model_validate(data)


  def test_contracts_reject_unknown_fields(self) -> None:
    data = read_fixture("objectives/butterfly_proboscis.json")
    data["personality"] = "not allowed"
    with self.assertRaises(ValidationError):
        LearningObjective.model_validate(data)


if __name__ == "__main__":
    unittest.main()
