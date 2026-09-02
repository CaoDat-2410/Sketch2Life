import unittest

from learning_video.fallback import RetryPolicy, StillNarrationFallback
from learning_video.library import AssetLibrary
from learning_video.schemas import (
    LearningObjective,
    ValidationResult,
    ValidationStatus,
)


OBJECTIVE = LearningObjective(
    objective_id="butterfly_proboscis",
    version="v1",
    locale="vi-VN",
    age_band="3-6",
    concept="Bướm dùng vòi để hút mật từ hoa",
)
LIBRARY = AssetLibrary.from_directory(
    __import__("pathlib").Path(__file__).parents[1] / "fixtures/fallback_assets"
)


def failure(status: ValidationStatus = ValidationStatus.FALLBACK) -> ValidationResult:
    return ValidationResult(
        status=status,
        objective_id=OBJECTIVE.objective_id,
        objective_version=OBJECTIVE.version,
        duration_sec=8,
        reason_codes=["VIDEO_NOT_GROUNDED"],
        validator="qwen3-vl",
    )


class FallbackTest(unittest.TestCase):
    def test_fallback_returns_reviewed_still_narration(self) -> None:
        result = StillNarrationFallback(LIBRARY).resolve(OBJECTIVE, failure())

        self.assertIs(result.status, ValidationStatus.FALLBACK)
        self.assertIsNotNone(result.asset)
        self.assertEqual(result.asset.asset_id, "STILL-BUTTERFLY-PROBOSCIS-v1")

    def test_fallback_preserves_objective_identity(self) -> None:
        result = StillNarrationFallback(LIBRARY).resolve(OBJECTIVE, failure())

        self.assertEqual(result.objective_id, OBJECTIVE.objective_id)
        self.assertEqual(result.objective_version, OBJECTIVE.version)

    def test_missing_fallback_blocks(self) -> None:
        empty_library = AssetLibrary([])
        result = StillNarrationFallback(empty_library).resolve(OBJECTIVE, failure())

        self.assertIs(result.status, ValidationStatus.BLOCK)
        self.assertIsNone(result.asset)
        self.assertEqual(result.reason_code, "NO_REVIEWED_FALLBACK")

    def test_retry_is_allowed_once(self) -> None:
        policy = RetryPolicy(max_retries=1)

        self.assertTrue(policy.can_retry(failure(ValidationStatus.RETRY), 0))
        self.assertFalse(policy.can_retry(failure(ValidationStatus.RETRY), 1))

    def test_non_retry_outcome_is_not_retried(self) -> None:
        policy = RetryPolicy(max_retries=1)

        self.assertFalse(policy.can_retry(failure(ValidationStatus.BLOCK), 0))


if __name__ == "__main__":
    unittest.main()
