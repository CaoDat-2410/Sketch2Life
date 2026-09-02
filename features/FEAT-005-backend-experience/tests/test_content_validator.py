import unittest
from pathlib import Path

from learning_video.content_validator import MockQwen3VLValidator, Qwen3VLContentValidator
from learning_video.schemas import (
    FrameSamplingResult,
    GenerationBrief,
    ValidationStatus,
    VisualInspection,
)


BRIEF = GenerationBrief(
    objective_id="butterfly_proboscis",
    objective_version="v1",
    locale="vi-VN",
    age_band="3-6",
    duration_sec=8,
    prompt="Show a butterfly using its proboscis to drink nectar.",
    show=["butterfly", "proboscis", "nectar"],
)
SAMPLING = FrameSamplingResult(
    status=ValidationStatus.PASS,
    video_path="video.mp4",
    duration_sec=8,
    sampled_frame_paths=[f"frame_{point:03d}.jpg" for point in (0, 25, 50, 75, 100)],
    sample_percentages=[0, 25, 50, 75, 100],
)


class ContentValidatorTest(unittest.TestCase):
    def test_grounded_content_passes(self) -> None:
        result = Qwen3VLContentValidator(MockQwen3VLValidator()).validate(SAMPLING, BRIEF)
        self.assertIs(result.status, ValidationStatus.PASS)
        self.assertEqual(result.reason_codes, [])

    def test_missing_objective_requests_retry(self) -> None:
        model = MockQwen3VLValidator(VisualInspection(objective_present=False))
        result = Qwen3VLContentValidator(model).validate(SAMPLING, BRIEF)
        self.assertIs(result.status, ValidationStatus.RETRY)
        self.assertEqual(result.reason_codes, ["OBJECTIVE_NOT_GROUNDED"])

    def test_prohibited_content_blocks(self) -> None:
        model = MockQwen3VLValidator(
            VisualInspection(objective_present=True, prohibited_content_found=True)
        )
        result = Qwen3VLContentValidator(model).validate(SAMPLING, BRIEF)
        self.assertIs(result.status, ValidationStatus.BLOCK)
        self.assertEqual(result.reason_codes, ["PROHIBITED_CONTENT"])

    def test_visual_corruption_uses_fallback(self) -> None:
        model = MockQwen3VLValidator(
            VisualInspection(objective_present=True, visual_corruption_detected=True)
        )
        result = Qwen3VLContentValidator(model).validate(SAMPLING, BRIEF)
        self.assertIs(result.status, ValidationStatus.FALLBACK)
        self.assertEqual(result.reason_codes, ["VISUAL_CORRUPTION"])

    def test_sampling_failure_does_not_call_content_model(self) -> None:
        class FailingIfCalled:
            def inspect(self, frames: list[Path], brief: GenerationBrief) -> VisualInspection:
                raise AssertionError("content model must not run")

        failed_sampling = SAMPLING.model_copy(
            update={"status": ValidationStatus.BLOCK, "reason_codes": ["VIDEO_NOT_DECODABLE"]}
        )
        result = Qwen3VLContentValidator(FailingIfCalled()).validate(failed_sampling, BRIEF)
        self.assertIs(result.status, ValidationStatus.FALLBACK)
        self.assertEqual(result.reason_codes, ["FRAME_SAMPLING_NOT_PASS"])


if __name__ == "__main__":
    unittest.main()
