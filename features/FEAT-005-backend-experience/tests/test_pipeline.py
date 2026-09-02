import unittest
from pathlib import Path

from learning_video.content_validator import MockQwen3VLValidator, Qwen3VLContentValidator
from learning_video.fallback import RetryPolicy, StillNarrationFallback
from learning_video.generator_client import MockGenerator
from learning_video.library import AssetLibrary
from learning_video.pipeline import LearningVideoPipeline
from learning_video.resolver import CacheFirstResolver
from learning_video.schemas import (
    FrameSamplingResult,
    GenerationBrief,
    LearningObjective,
    ValidationStatus,
    VisualInspection,
)


ROOT = Path(__file__).parents[1]
OBJECTIVE = LearningObjective(
    objective_id="butterfly_proboscis",
    version="v1",
    locale="vi-VN",
    age_band="3-6",
    concept="Bướm dùng vòi để hút mật từ hoa",
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


class FakeSampler:
    def sample(self, video_path: Path, output_dir: Path) -> FrameSamplingResult:
        del video_path, output_dir
        return FrameSamplingResult(
            status=ValidationStatus.PASS,
            video_path="generated.mp4",
            duration_sec=8,
            sampled_frame_paths=[f"frame_{point:03d}.jpg" for point in (0, 25, 50, 75, 100)],
            sample_percentages=[0, 25, 50, 75, 100],
        )


def make_pipeline(library: AssetLibrary, inspection: VisualInspection) -> LearningVideoPipeline:
    return LearningVideoPipeline(
        resolver=CacheFirstResolver(library),
        generator=MockGenerator(),
        sampler=FakeSampler(),
        validator=Qwen3VLContentValidator(MockQwen3VLValidator(inspection)),
        fallback=StillNarrationFallback(
            AssetLibrary.from_directory(ROOT / "fixtures/fallback_assets")
        ),
        retry_policy=RetryPolicy(max_retries=1),
    )


class PipelineTest(unittest.TestCase):
    def test_cache_hit_does_not_generate(self) -> None:
        library = AssetLibrary.from_directory(ROOT / "fixtures/reviewed_assets")
        result = make_pipeline(library, VisualInspection(objective_present=True)).run(
            OBJECTIVE, BRIEF, ROOT / "outputs/test-frames"
        )
        self.assertEqual(result.status, "CACHE_HIT")
        self.assertIsNotNone(result.asset)
        self.assertIsNone(result.generated_video)

    def test_cache_miss_generates_and_passes(self) -> None:
        result = make_pipeline(AssetLibrary([]), VisualInspection(objective_present=True)).run(
            OBJECTIVE, BRIEF, ROOT / "outputs/test-frames"
        )
        self.assertEqual(result.status, "GENERATED")
        self.assertIsNotNone(result.generated_video)
        self.assertEqual(result.validation.status, ValidationStatus.PASS)

    def test_unsafe_content_blocks_without_fallback(self) -> None:
        result = make_pipeline(
            AssetLibrary([]),
            VisualInspection(objective_present=True, prohibited_content_found=True),
        ).run(OBJECTIVE, BRIEF, ROOT / "outputs/test-frames")
        self.assertEqual(result.status, "BLOCK")
        self.assertIsNone(result.asset)
        self.assertEqual(result.reason_codes, ["PROHIBITED_CONTENT"])


if __name__ == "__main__":
    unittest.main()
