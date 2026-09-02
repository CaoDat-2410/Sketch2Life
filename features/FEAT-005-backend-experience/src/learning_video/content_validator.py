"""Qwen3-VL-facing learning-content validation policy."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .schemas import (
    FrameSamplingResult,
    GenerationBrief,
    ValidationResult,
    ValidationStatus,
    VisualInspection,
)


class VisualContentModel(Protocol):
    def inspect(self, frames: list[Path], brief: GenerationBrief) -> VisualInspection:
        """Inspect sampled frames against the bounded generation brief."""


class MockQwen3VLValidator:
    """Deterministic stand-in for Qwen3-VL used by fixture tests."""

    def __init__(self, inspection: VisualInspection | None = None) -> None:
        self._inspection = inspection or VisualInspection(objective_present=True)

    def inspect(self, frames: list[Path], brief: GenerationBrief) -> VisualInspection:
        del frames, brief
        return self._inspection


class Qwen3VLContentValidator:
    """Maps model observations and sampling evidence to typed outcomes."""

    def __init__(self, model: VisualContentModel) -> None:
        self._model = model

    def validate(
        self,
        sampling: FrameSamplingResult,
        brief: GenerationBrief,
    ) -> ValidationResult:
        if sampling.status is not ValidationStatus.PASS:
            return ValidationResult(
                status=ValidationStatus.FALLBACK,
                objective_id=brief.objective_id,
                objective_version=brief.objective_version,
                duration_sec=sampling.duration_sec,
                sampled_frame_paths=sampling.sampled_frame_paths,
                reason_codes=["FRAME_SAMPLING_NOT_PASS"],
                validator="qwen3-vl",
            )

        frames = [Path(path) for path in sampling.sampled_frame_paths]
        inspection = self._model.inspect(frames, brief)
        status, reason_codes = self._decision(inspection)
        return ValidationResult(
            status=status,
            objective_id=brief.objective_id,
            objective_version=brief.objective_version,
            duration_sec=sampling.duration_sec,
            sampled_frame_paths=sampling.sampled_frame_paths,
            reason_codes=reason_codes,
            validator="qwen3-vl",
        )

    @staticmethod
    def _decision(inspection: VisualInspection) -> tuple[ValidationStatus, list[str]]:
        if inspection.prohibited_content_found:
            return ValidationStatus.BLOCK, ["PROHIBITED_CONTENT"]
        if not inspection.age_appropriate:
            return ValidationStatus.BLOCK, ["AGE_INAPPROPRIATE"]
        if inspection.visual_corruption_detected:
            return ValidationStatus.FALLBACK, ["VISUAL_CORRUPTION"]
        if not inspection.objective_present:
            return ValidationStatus.RETRY, ["OBJECTIVE_NOT_GROUNDED"]
        return ValidationStatus.PASS, []
