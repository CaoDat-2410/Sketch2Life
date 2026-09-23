"""FEAT-018 contracts for source-preserving drawing exploration.

The VLM supplies semantic observations only.  Region localization is an
explicit, independently versioned boundary so the renderer never invents a
subject position from a label or silently replaces the child's drawing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1


class SourceRegionV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)
    width: float = Field(gt=0, le=1, allow_inf_nan=False)
    height: float = Field(gt=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def stay_inside_source(self) -> SourceRegionV1:
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("source region must stay inside the normalized source image")
        return self


class SubjectCandidateV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    candidate_id: str = Field(alias="candidateId", pattern=r"^[a-z0-9-]+$")
    label_vi: str = Field(alias="labelVi", min_length=1, max_length=60)
    source_claim_ids: tuple[str, ...] = Field(alias="sourceClaimIds", min_length=1, max_length=8)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    confidence_band: Literal["HIGH", "MEDIUM", "LOW"] = Field(alias="confidenceBand")
    image_covered: bool = Field(alias="imageCovered")
    narration_covered: bool = Field(alias="narrationCovered")
    relation_refs: tuple[str, ...] = Field(default=(), alias="relationRefs", max_length=8)


class SubjectCandidateSetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["SubjectCandidateSetV1"] = Field(
        default="SubjectCandidateSetV1", alias="contractName"
    )
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    source_artifact_sha256: str = Field(alias="sourceArtifactSha256", pattern=r"^[a-f0-9]{64}$")
    max_items: Literal[3] = Field(default=3, alias="maxItems")
    items: tuple[SubjectCandidateV1, ...] = Field(min_length=1, max_length=3)
    original_art_preserved: Literal[True] = Field(default=True, alias="originalArtPreserved")


class SceneExplorationBeatV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    beat_id: str = Field(alias="beatId", pattern=r"^[a-z][a-z0-9-]*$")
    order: int = Field(ge=1, le=4)
    effect: Literal["REVEAL", "FOCUS", "TRACE_RELATION", "ZOOM_OUT"]
    target_ref: str | None = Field(default=None, alias="targetRef", max_length=120)
    label_vi: str = Field(alias="labelVi", min_length=1, max_length=60)
    caption_vi: str = Field(alias="captionVi", min_length=1, max_length=180)
    start_seconds: float = Field(alias="startSeconds", ge=0, le=30, allow_inf_nan=False)
    end_seconds: float = Field(alias="endSeconds", gt=0, le=30, allow_inf_nan=False)
    tap_enabled: bool = Field(default=False, alias="tapEnabled")

    @model_validator(mode="after")
    def valid_window(self) -> SceneExplorationBeatV1:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("exploration beat end must be after start")
        return self


class SceneExplorationPlanV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["SceneExplorationPlanV1"] = Field(
        default="SceneExplorationPlanV1", alias="contractName"
    )
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    primary_subject_ref: str = Field(alias="primarySubjectRef", min_length=1, max_length=120)
    primary_label_vi: str = Field(alias="primaryLabelVi", min_length=1, max_length=60)
    relation_label_vi: str | None = Field(default=None, alias="relationLabelVi", max_length=80)
    learning_bridge_vi: str = Field(alias="learningBridgeVi", min_length=1, max_length=240)
    beats: tuple[SceneExplorationBeatV1, ...] = Field(min_length=2, max_length=4)
    tap_to_discover: Literal[True] = Field(default=True, alias="tapToDiscover")
    video_executed: Literal[False] = Field(default=False, alias="videoExecuted")


class SceneFocusTargetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    target_ref: str = Field(alias="targetRef", min_length=1, max_length=120)
    label_vi: str = Field(alias="labelVi", min_length=1, max_length=60)
    source_region: SourceRegionV1 | None = Field(default=None, alias="sourceRegion")
    region_confidence: float | None = Field(default=None, alias="regionConfidence", ge=0, le=1)
    depth_layer: Literal[0, 1, 2] = Field(default=1, alias="depthLayer")
    hit_slop: float = Field(default=0.06, alias="hitSlop", ge=0, le=0.25)
    asset_kind: Literal["CROP", "TRANSPARENT_PNG", "MASK"] | None = Field(
        default=None, alias="assetKind"
    )
    extraction_version: str | None = Field(default=None, alias="extractionVersion")

    @model_validator(mode="after")
    def require_region_provenance(self) -> SceneFocusTargetV1:
        if self.source_region is not None and (
            self.region_confidence is None
            or self.asset_kind is None
            or self.extraction_version is None
        ):
            raise ValueError("localized focus targets require confidence and extraction provenance")
        return self


class SceneFocusPlanV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["SceneFocusPlanV1"] = Field(
        default="SceneFocusPlanV1", alias="contractName"
    )
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    source_artifact_sha256: str = Field(alias="sourceArtifactSha256", pattern=r"^[a-f0-9]{64}$")
    extraction_status: Literal["READY", "FALLBACK_REQUIRED"] = Field(alias="extractionStatus")
    targets: tuple[SceneFocusTargetV1, ...] = Field(default=(), max_length=3)
    fallback_reason: Literal["NO_LOCALIZER", "REGION_INVALID", "CUTOUT_FAILED"] | None = Field(
        default=None, alias="fallbackReason"
    )

    @model_validator(mode="after")
    def validate_status(self) -> SceneFocusPlanV1:
        if self.extraction_status == "READY" and not self.targets:
            raise ValueError("ready focus plans require at least one target")
        if self.extraction_status == "FALLBACK_REQUIRED" and self.targets:
            raise ValueError("fallback focus plans must not expose unverified target regions")
        if self.extraction_status == "FALLBACK_REQUIRED" and self.fallback_reason is None:
            raise ValueError("fallback focus plans require a reason")
        return self


__all__ = [
    "SceneExplorationBeatV1",
    "SceneExplorationPlanV1",
    "SceneFocusPlanV1",
    "SceneFocusTargetV1",
    "SourceRegionV1",
    "SubjectCandidateSetV1",
    "SubjectCandidateV1",
]
