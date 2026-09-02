"""Provider-neutral generation interface and deterministic mock provider."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Protocol

from .schemas import GeneratedVideo, GenerationBrief, ProvenanceMetadata


class GenerationProvider(Protocol):
    def generate(self, brief: GenerationBrief) -> GeneratedVideo:
        """Generate a bounded video artifact for the supplied brief."""


class MockGenerator:
    """Returns deterministic artifact metadata without invoking a model or GPU."""

    provider_name = "mock"

    def generate(self, brief: GenerationBrief) -> GeneratedVideo:
        artifact_id = f"MOCK-{brief.objective_id}-{brief.objective_version}"
        output_path = PurePosixPath("outputs", "mock", f"{artifact_id}.mp4").as_posix()
        return GeneratedVideo(
            artifact_id=artifact_id,
            objective_id=brief.objective_id,
            objective_version=brief.objective_version,
            output_path=output_path,
            duration_sec=float(brief.duration_sec),
            provider=self.provider_name,
            provenance=ProvenanceMetadata(
                source="mock_generator",
                model_name="mock",
                model_version="v1",
                config_hash="mock-config-v1",
            ),
        )
