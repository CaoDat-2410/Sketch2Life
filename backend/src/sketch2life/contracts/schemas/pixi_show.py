"""Additive FEAT-030 contracts for a bounded, AI-authored Pixi visual show."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.renderer_v2 import PixiRendererLaunchV2
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1

PixiShowAssetRoleV1 = Literal["SUBJECT", "ENVIRONMENT", "PROP", "EFFECT"]
PixiShowRigTierV1 = Literal["FULL_AUTO_RIG", "CUTOUT_MICRO_MOTION", "BBOX_VISUAL_FOCUS"]
PixiShowSourceContentTypeV1 = Literal["image/png", "image/jpeg"]


class PixiSubjectHintV1(StrEnum):
    BIRD = "BIRD"
    INSECT = "INSECT"
    FISH = "FISH"
    QUADRUPED = "QUADRUPED"
    BIPED = "BIPED"
    PLANT = "PLANT"
    VEHICLE = "VEHICLE"
    OBJECT = "OBJECT"
    UNKNOWN = "UNKNOWN"


class PixiBehaviorClassV1(StrEnum):
    WALKER = "WALKER"
    FLYER = "FLYER"
    SWIMMER = "SWIMMER"
    CRAWLER = "CRAWLER"
    ROLLER = "ROLLER"
    STATIONARY = "STATIONARY"


class PixiShowActionV1(StrEnum):
    NOTICE = "NOTICE"
    APPROACH = "APPROACH"
    INTERACT = "INTERACT"
    WALK_STEP = "WALK_STEP"
    FLAP = "FLAP"
    GLIDE = "GLIDE"
    SWIM = "SWIM"
    SLITHER = "SLITHER"
    ROLL = "ROLL"
    SETTLE = "SETTLE"


class PixiShowBeatV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    beat_id: str = Field(alias="beatId", pattern=r"^[a-z][a-z0-9_-]*$", max_length=64)
    start_seconds: float = Field(alias="startSeconds", ge=0, le=30, allow_inf_nan=False)
    end_seconds: float = Field(alias="endSeconds", gt=0, le=30, allow_inf_nan=False)
    action: PixiShowActionV1
    target_role: Literal["SOURCE_SUBJECT", "SUPPLEMENTAL_ASSET"] = Field(alias="targetRole")
    asset_id: str | None = Field(default=None, alias="assetId", min_length=1, max_length=160)
    x: float = Field(default=0.5, ge=0.05, le=0.95, allow_inf_nan=False)
    y: float = Field(default=0.5, ge=0.05, le=0.95, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_target_and_time(self) -> PixiShowBeatV1:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("show beat must have positive duration")
        if (self.target_role == "SUPPLEMENTAL_ASSET") != (self.asset_id is not None):
            raise ValueError("supplemental beats require exactly one asset ID")
        return self


class PixiShowIntentV1(BaseModel):
    """Untrusted, closed-schema output expected from the one planner inference."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    visual_subject_hint_id: PixiSubjectHintV1 = Field(alias="visualSubjectHintId")
    behavior_class: PixiBehaviorClassV1 = Field(alias="behaviorClass")
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    selected_asset_ids: tuple[str, ...] = Field(alias="selectedAssetIds", max_length=3)
    duration_seconds: int = Field(default=20, alias="durationSeconds", ge=15, le=30)
    beats: tuple[PixiShowBeatV1, ...] = Field(min_length=3, max_length=6)
    ending_still: Literal[True] = Field(alias="endingStill")

    @model_validator(mode="after")
    def validate_beats(self) -> PixiShowIntentV1:
        if len(set(self.selected_asset_ids)) != len(self.selected_asset_ids):
            raise ValueError("selected sprite IDs must be unique")
        if self.beats[-1].action != PixiShowActionV1.SETTLE:
            raise ValueError("the final show beat must settle before the still ending")
        if self.duration_seconds - self.beats[-1].end_seconds < 2:
            raise ValueError("show plan must reserve at least two seconds for the still ending")
        previous_end = -1.0
        for beat in self.beats:
            if beat.start_seconds < previous_end:
                raise ValueError("show beats must be ordered and non-overlapping")
            previous_end = beat.end_seconds
            if beat.asset_id is not None and beat.asset_id not in self.selected_asset_ids:
                raise ValueError("show beat references an asset not selected by the plan")
        if any(beat.end_seconds > self.duration_seconds for beat in self.beats):
            raise ValueError("show beat exceeds total duration")
        return self


class PixiShowPlannerAssetCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    asset_id: str = Field(alias="assetId", min_length=1, max_length=160)
    label: str = Field(min_length=1, max_length=120)
    role: PixiShowAssetRoleV1
    visual_description: str = Field(alias="visualDescription", min_length=1, max_length=280)
    topic_tags: tuple[str, ...] = Field(alias="topicTags", max_length=12)


class PixiShowSourceCropV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    content_type: PixiShowSourceContentTypeV1 = Field(alias="contentType")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_base64: str = Field(alias="contentBase64", min_length=16, max_length=1_400_000)


class PixiShowPlannerRequestV1(BaseModel):
    """Provider boundary; deliberately excludes session IDs, child profiles and source URLs."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    contract_name: Literal["PixiShowPlannerRequestV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    request_id: str = Field(alias="requestId", pattern=r"^[a-f0-9-]{36}$")
    source_crop: PixiShowSourceCropV1 = Field(alias="sourceCrop")
    source_subject_region: SourceRegionV1 = Field(alias="sourceSubjectRegion")
    renderer_duration_seconds: int = Field(alias="rendererDurationSeconds", ge=15, le=30)
    confirmed_subject_label: str = Field(
        alias="confirmedSubjectLabel", min_length=1, max_length=160
    )
    subject_tags: tuple[str, ...] = Field(alias="subjectTags", max_length=20)
    activity_id: str = Field(alias="activityId", min_length=1, max_length=120)
    activity_label: str = Field(alias="activityLabel", min_length=1, max_length=160)
    objective_ids: tuple[str, ...] = Field(alias="objectiveIds", min_length=1, max_length=3)
    objective_labels: tuple[str, ...] = Field(alias="objectiveLabels", min_length=1, max_length=3)
    rig_tier: PixiShowRigTierV1 = Field(alias="rigTier")
    part_roles: tuple[str, ...] = Field(alias="partRoles", max_length=8)
    candidate_assets: tuple[PixiShowPlannerAssetCandidateV1, ...] = Field(
        alias="candidateAssets", min_length=1, max_length=6
    )

    @model_validator(mode="after")
    def validate_request_consistency(self) -> PixiShowPlannerRequestV1:
        if len(self.objective_ids) != len(self.objective_labels):
            raise ValueError("objective IDs and labels must have matching lengths")
        asset_ids = [asset.asset_id for asset in self.candidate_assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("planner candidates must have unique asset IDs")
        return self


class PixiShowPlannerRequestV2(PixiShowPlannerRequestV1):
    """V2 planner request permits an empty approved companion shortlist."""

    # Pydantic enforces each concrete protocol discriminator at runtime.
    contract_name: Literal["PixiShowPlannerRequestV2"] = Field(alias="contractName")  # type: ignore[assignment]  # noqa: E501
    contract_version: Literal["2.0"] = Field(alias="contractVersion")  # type: ignore[assignment]  # noqa: E501
    candidate_assets: tuple[PixiShowPlannerAssetCandidateV1, ...] = Field(
        alias="candidateAssets", min_length=0, max_length=6
    )


class PixiShowPlanV1(BaseModel):
    """Server-validated show contract. It carries intent/IDs, never code or arbitrary URLs."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    contract_name: Literal["PixiShowPlanV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    plan_id: str = Field(alias="planId", min_length=1, max_length=160)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    package_id: str = Field(alias="packageId", min_length=1, max_length=160)
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    source_subject_region: SourceRegionV1 = Field(alias="sourceSubjectRegion")
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    confirmed_subject_id: str = Field(alias="confirmedSubjectId", min_length=1, max_length=160)
    visual_subject_hint_id: PixiSubjectHintV1 = Field(alias="visualSubjectHintId")
    behavior_class: PixiBehaviorClassV1 = Field(alias="behaviorClass")
    duration_seconds: int = Field(alias="durationSeconds", ge=15, le=30)
    selected_asset_ids: tuple[str, ...] = Field(
        alias="selectedAssetIds", min_length=1, max_length=3
    )
    beats: tuple[PixiShowBeatV1, ...] = Field(min_length=3, max_length=6)
    ending_still: Literal[True] = Field(alias="endingStill")
    compiler_version: Literal["1"] = Field(default="1", alias="compilerVersion")

    @model_validator(mode="after")
    def validate_identity_and_timing(self) -> PixiShowPlanV1:
        if len(set(self.selected_asset_ids)) != len(self.selected_asset_ids):
            raise ValueError("selected sprite IDs must be unique")
        if self.beats[-1].action != PixiShowActionV1.SETTLE:
            raise ValueError("the final show beat must settle before the still ending")
        if self.duration_seconds - self.beats[-1].end_seconds < 2:
            raise ValueError("show plan must reserve at least two seconds for the still ending")
        previous_end = -1.0
        for beat in self.beats:
            if beat.start_seconds < previous_end:
                raise ValueError("show beats must be ordered and non-overlapping")
            previous_end = beat.end_seconds
            if beat.asset_id is not None and beat.asset_id not in self.selected_asset_ids:
                raise ValueError("show beat references an asset not selected by the plan")
        referenced_asset_ids = {beat.asset_id for beat in self.beats if beat.asset_id is not None}
        if referenced_asset_ids != set(self.selected_asset_ids):
            raise ValueError("every selected asset must be used by at least one show beat")
        return self


class PixiShowPlanV2(PixiShowPlanV1):
    """V2 permits a source-only show while retaining exact asset-reference checks."""

    # Pydantic enforces each concrete protocol discriminator at runtime.
    contract_name: Literal["PixiShowPlanV2"] = Field(alias="contractName")  # type: ignore[assignment]  # noqa: E501
    contract_version: Literal["2.0"] = Field(alias="contractVersion")  # type: ignore[assignment]  # noqa: E501
    selected_asset_ids: tuple[str, ...] = Field(alias="selectedAssetIds", max_length=3)


class PixiShowAssetReadV1(BaseModel):
    """Short-lived capability to read exactly one rights-cleared, selected PNG frame."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    asset_id: str = Field(alias="assetId", min_length=1, max_length=160)
    read_endpoint: Literal["/v1/renderer/pixi-asset"] = Field(alias="readEndpoint")
    read_capability: str = Field(alias="readCapability", min_length=40, max_length=200)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_length: int = Field(alias="byteLength", ge=1, le=1_000_000)
    content_type: Literal["image/png"] = Field(default="image/png", alias="contentType")


class PixiRendererShowEnvelopeV1(BaseModel):
    """Additive FEAT-030 envelope; frozen V1/V2 launch and animation contracts stay intact."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    contract_name: Literal["PixiRendererShowEnvelopeV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    renderer_launch_v2: PixiRendererLaunchV2 = Field(alias="rendererLaunchV2")
    show_plan: PixiShowPlanV1 = Field(alias="showPlan")
    asset_reads: tuple[PixiShowAssetReadV1, ...] = Field(
        alias="assetReads", min_length=1, max_length=3
    )

    @model_validator(mode="after")
    def validate_envelope_identity(self) -> PixiRendererShowEnvelopeV1:
        launch = self.renderer_launch_v2
        plan = self.show_plan
        if (
            launch.session_id != plan.session_id
            or launch.source_sha256 != plan.source_sha256
            or launch.animation_plan.package_id != plan.package_id
            or launch.experience_spec_ref != plan.experience_spec_ref
        ):
            raise ValueError("show envelope identities must match the V2 renderer launch")
        read_ids = tuple(item.asset_id for item in self.asset_reads)
        if len(set(read_ids)) != len(read_ids) or set(read_ids) != set(plan.selected_asset_ids):
            raise ValueError("asset reads must exactly match the selected show asset IDs")
        return self


__all__ = [
    "PixiBehaviorClassV1",
    "PixiShowActionV1",
    "PixiShowBeatV1",
    "PixiShowIntentV1",
    "PixiShowPlannerAssetCandidateV1",
    "PixiShowAssetRoleV1",
    "PixiShowRigTierV1",
    "PixiShowSourceContentTypeV1",
    "PixiShowSourceCropV1",
    "PixiShowPlannerRequestV1",
    "PixiShowPlannerRequestV2",
    "PixiShowPlanV1",
    "PixiShowPlanV2",
    "PixiShowAssetReadV1",
    "PixiRendererShowEnvelopeV1",
    "PixiSubjectHintV1",
]
