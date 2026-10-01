"""Provider-neutral port for one bounded post-Gate-B Pixi show-planning inference."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from sketch2life.contracts.schemas.pixi_show import PixiShowIntentV1
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


@dataclass(frozen=True, slots=True)
class PixiShowAssetCandidate:
    asset_id: str
    label: str
    role: str
    visual_description: str
    topic_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PixiShowPlanningRequest:
    request_id: str
    session_id: str
    source_artifact_ref: str
    source_sha256: str
    package_id: str
    subject_region: SourceRegionV1 | None
    confirmed_subject_id: str
    confirmed_subject_label: str
    subject_tags: tuple[str, ...]
    experience_spec_id: str
    experience_spec_version: int
    renderer_duration_seconds: int
    activity_id: str
    activity_label: str
    objective_ids: tuple[str, ...]
    objective_labels: tuple[str, ...]
    rig_tier: str
    part_roles: tuple[str, ...]
    candidate_assets: tuple[PixiShowAssetCandidate, ...]
    source_crop_content_type: str
    source_crop_bytes: bytes = field(repr=False, compare=False)


class PixiShowPlannerUnavailable(Exception):
    """A sanitized planner failure suitable for a typed user-facing error code."""

    CODES = frozenset(
        {
            "PIXI_SHOW_DISABLED",
            "NO_ELIGIBLE_ASSETS",
            "SUBJECT_CROP_UNAVAILABLE",
            "PLANNER_TIMEOUT",
            "PLANNER_UNAVAILABLE",
            "PLANNER_INVALID_RESULT",
            "SUBJECT_RECONFIRMATION_REQUIRED",
            "BEHAVIOR_CAPABILITY_UNSUPPORTED",
            "NO_COMPATIBLE_ASSET",
        }
    )

    def __init__(self, code: str) -> None:
        if code not in self.CODES:
            code = "PLANNER_UNAVAILABLE"
        super().__init__(code)
        self.code = code


class PixiShowPlannerPort(Protocol):
    def plan(self, request: PixiShowPlanningRequest) -> PixiShowIntentV1: ...


__all__ = [
    "PixiShowAssetCandidate",
    "PixiShowPlannerPort",
    "PixiShowPlannerUnavailable",
    "PixiShowPlanningRequest",
]
