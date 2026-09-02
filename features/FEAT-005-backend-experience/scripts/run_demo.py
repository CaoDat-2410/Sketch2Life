"""Run deterministic Person 4 pipeline demos without model or GPU dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FEATURE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FEATURE_ROOT / "src"))

from learning_video.content_validator import MockQwen3VLValidator, Qwen3VLContentValidator  # noqa: E402
from learning_video.fallback import RetryPolicy, StillNarrationFallback  # noqa: E402
from learning_video.generator_client import MockGenerator  # noqa: E402
from learning_video.library import AssetLibrary  # noqa: E402
from learning_video.pipeline import LearningVideoPipeline  # noqa: E402
from learning_video.resolver import CacheFirstResolver  # noqa: E402
from learning_video.schemas import (  # noqa: E402
    FrameSamplingResult,
    GenerationBrief,
    LearningObjective,
    ValidationStatus,
    VisualInspection,
)


class DemoSampler:
    def sample(self, video_path: Path, output_dir: Path) -> FrameSamplingResult:
        del output_dir
        return FrameSamplingResult(
            status=ValidationStatus.PASS,
            video_path=video_path.as_posix(),
            duration_sec=8,
            sampled_frame_paths=[
                f"demo-frame-{point:03d}.jpg" for point in (0, 25, 50, 75, 100)
            ],
            sample_percentages=[0, 25, 50, 75, 100],
        )


def load_objective() -> LearningObjective:
    payload = json.loads(
        (FEATURE_ROOT / "fixtures/objectives/butterfly_proboscis.json").read_text(
            encoding="utf-8"
        )
    )
    return LearningObjective.model_validate(payload)


def load_brief() -> GenerationBrief:
    payload = json.loads(
        (FEATURE_ROOT / "fixtures/objectives/butterfly_generation_brief.json").read_text(
            encoding="utf-8"
        )
    )
    return GenerationBrief.model_validate(payload)


def make_pipeline(cache: bool, inspection: VisualInspection) -> LearningVideoPipeline:
    cache_dir = FEATURE_ROOT / "fixtures/reviewed_assets" if cache else None
    library = AssetLibrary.from_directory(cache_dir) if cache_dir else AssetLibrary([])
    fallback = AssetLibrary.from_directory(FEATURE_ROOT / "fixtures/fallback_assets")
    return LearningVideoPipeline(
        resolver=CacheFirstResolver(library),
        generator=MockGenerator(),
        sampler=DemoSampler(),
        validator=Qwen3VLContentValidator(MockQwen3VLValidator(inspection)),
        fallback=StillNarrationFallback(fallback),
        retry_policy=RetryPolicy(max_retries=1),
    )


def run(case: str) -> dict:
    objective = load_objective()
    brief = load_brief()
    inspection = VisualInspection(objective_present=True)
    if case == "fallback":
        inspection = VisualInspection(objective_present=True, visual_corruption_detected=True)
    if case == "block":
        inspection = VisualInspection(objective_present=True, prohibited_content_found=True)

    result = make_pipeline(case == "cache-hit", inspection).run(
        objective, brief, FEATURE_ROOT / "outputs/demo-frames"
    )
    return result.model_dump(mode="json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=("cache-hit", "cache-miss", "fallback", "block"),
        default="cache-hit",
        help="deterministic pipeline scenario to run",
    )
    args = parser.parse_args()
    print(json.dumps(run(args.case), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
