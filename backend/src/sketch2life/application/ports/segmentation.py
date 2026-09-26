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
    prompt_region: SourceRegionV1 | None = None
    positive_points: tuple[tuple[float, float], ...] = ()
    negative_points: tuple[tuple[float, float], ...] = ()
    requested_part_roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SubjectPartSegmentationResult:
    """A bounded semantic-part result returned by a replaceable segmenter.

    SAM2 is the perception step only.  The application still decides whether a part is
    suitable for a rig and the renderer never treats a missing part as permission to
    invent anatomy.
    """

    part_id: str
    role: str
    source_region: SourceRegionV1
    confidence: float
    mask_artifact_ref: str | None = None
    mask_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class SubjectSegmentationResult:
    source_region: SourceRegionV1
    confidence: float
    adapter_id: str
    adapter_version: str
    mask_artifact_ref: str | None = None
    mask_sha256: str | None = None
    parts: tuple[SubjectPartSegmentationResult, ...] = ()


class SubjectSegmentationPort(Protocol):
    def segment(self, request: SubjectSegmentationRequest) -> SubjectSegmentationResult | None: ...


__all__ = [
    "SubjectSegmentationPort",
    "SubjectSegmentationRequest",
    "SubjectSegmentationResult",
    "SubjectPartSegmentationResult",
]
