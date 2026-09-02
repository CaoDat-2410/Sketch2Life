"""Standalone learning-media orchestration pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .content_validator import Qwen3VLContentValidator
from .fallback import RetryPolicy, StillNarrationFallback
from .frame_sampler import FrameSampler
from .generator_client import GenerationProvider
from .resolver import CacheFirstResolver
from .schemas import GenerationBrief, LearningObjective, PipelineResult, ValidationStatus


class SamplingProvider(Protocol):
    def sample(self, video_path: Path, output_dir: Path):
        """Return a FrameSamplingResult for a generated video."""


class LearningVideoPipeline:
    def __init__(
        self,
        resolver: CacheFirstResolver,
        generator: GenerationProvider,
        sampler: SamplingProvider | FrameSampler,
        validator: Qwen3VLContentValidator,
        fallback: StillNarrationFallback,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._resolver = resolver
        self._generator = generator
        self._sampler = sampler
        self._validator = validator
        self._fallback = fallback
        self._retry_policy = retry_policy or RetryPolicy()

    def run(
        self,
        objective: LearningObjective,
        brief: GenerationBrief,
        frame_output_dir: Path,
    ) -> PipelineResult:
        resolved = self._resolver.resolve(objective)
        if resolved.asset is not None:
            return PipelineResult(
                status="CACHE_HIT",
                objective_id=objective.objective_id,
                objective_version=objective.version,
                asset=resolved.asset,
                retry_count=0,
            )

        retry_count = 0
        while True:
            generated = self._generator.generate(brief)
            sampling = self._sampler.sample(Path(generated.output_path), frame_output_dir)
            validation = self._validator.validate(sampling, brief)

            if validation.status is ValidationStatus.PASS:
                return PipelineResult(
                    status="GENERATED",
                    objective_id=objective.objective_id,
                    objective_version=objective.version,
                    generated_video=generated,
                    validation=validation,
                    retry_count=retry_count,
                )

            if self._retry_policy.can_retry(validation, retry_count):
                retry_count += 1
                continue

            if validation.status is ValidationStatus.BLOCK:
                return PipelineResult(
                    status="BLOCK",
                    objective_id=objective.objective_id,
                    objective_version=objective.version,
                    generated_video=generated,
                    validation=validation,
                    retry_count=retry_count,
                    reason_codes=validation.reason_codes,
                )

            fallback = self._fallback.resolve(objective, validation)
            return PipelineResult(
                status="FALLBACK" if fallback.asset is not None else "BLOCK",
                objective_id=objective.objective_id,
                objective_version=objective.version,
                generated_video=generated,
                validation=validation,
                fallback=fallback,
                asset=fallback.asset,
                retry_count=retry_count,
                reason_codes=[fallback.reason_code],
            )
