"""Replaceable spatial grounding and segmentation boundary for FEAT-030."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


@dataclass(frozen=True, slots=True)
class SubjectSegmentationRequest:
    session_id: str
    source_artifact_ref: str
    source_sha256: str
    target_id: str
    target_label: str
    target_confidence: float
    semantic_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectSegmentationResult:
    source_region: SourceRegionV1
    confidence: float
    adapter_id: str
    adapter_version: str
    mask_artifact_ref: str | None = None
    mask_sha256: str | None = None


class SubjectSegmentationPort(Protocol):
    def segment(self, request: SubjectSegmentationRequest) -> SubjectSegmentationResult | None: ...


__all__ = [
    "SubjectSegmentationPort",
    "SubjectSegmentationRequest",
    "SubjectSegmentationResult",
]
