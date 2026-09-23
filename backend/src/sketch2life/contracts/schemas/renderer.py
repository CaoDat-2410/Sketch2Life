"""Canonical FEAT-018 manifest and v1 Pixi renderer payload contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.scene_exploration import (
    SceneExplorationPlanV1,
    SceneFocusPlanV1,
    SourceRegionV1,
)


class RendererPointV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)


class RendererTransformV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    position: RendererPointV1 = Field(default_factory=lambda: RendererPointV1(x=0.5, y=0.5))
    scale: float = Field(default=1, ge=0.05, le=4, allow_inf_nan=False)
    rotation_degrees: float = Field(
        default=0, alias="rotationDegrees", ge=-360, le=360, allow_inf_nan=False
    )
    opacity: float = Field(default=1, ge=0, le=1, allow_inf_nan=False)


class RendererChildArtAssetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    source_asset_id: str = Field(alias="sourceAssetId", min_length=1, max_length=200)
    source_asset_version: str = Field(alias="sourceAssetVersion", pattern=r"^[1-9][0-9]*$")
    uri: str = Field(min_length=1, max_length=500)
    asset_kind: Literal["WHOLE_DRAWING", "CROP", "TRANSPARENT_PNG", "MASK"] = Field(
        alias="assetKind"
    )
    crop_version: str | None = Field(default=None, alias="cropVersion", pattern=r"^[1-9][0-9]*$")
    mask_version: str | None = Field(default=None, alias="maskVersion", pattern=r"^[1-9][0-9]*$")
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    source_region: SourceRegionV1 | None = Field(default=None, alias="sourceRegion")

    @model_validator(mode="after")
    def require_extraction_provenance(self) -> RendererChildArtAssetV1:
        if self.asset_kind == "CROP" and self.crop_version is None:
            raise ValueError("crop asset requires cropVersion provenance")
        if self.asset_kind == "CROP" and self.source_region is None:
            raise ValueError("crop asset requires a sourceRegion")
        if self.asset_kind == "MASK" and self.mask_version is None:
            raise ValueError("mask asset requires maskVersion provenance")
        return self


class RendererArtObjectV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    object_id: str = Field(alias="id", pattern=r"^[a-z][a-z0-9_-]*$")
    label: str = Field(min_length=1, max_length=200)
    asset: RendererChildArtAssetV1
    initial_transform: RendererTransformV1 = Field(
        default_factory=RendererTransformV1, alias="initialTransform"
    )
    extraction_status: Literal["READY", "FALLBACK_REQUIRED"] = Field(
        default="READY", alias="extractionStatus"
    )
    interactive: bool = False


class RendererMotionV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    motion_id: str = Field(alias="id", pattern=r"^[a-z][a-z0-9_-]*$")
    scene_id: str = Field(alias="sceneId", pattern=r"^[a-z][a-z0-9_-]*$")
    kind: Literal["MOVE", "MOVE_TO", "SCALE", "ROTATE", "FADE", "FLY", "JUMP", "DRAW_REVEAL"]
    target_id: str = Field(alias="targetId", pattern=r"^[a-z][a-z0-9_-]*$")
    duration_seconds: float = Field(alias="durationSeconds", ge=0.05, le=30, allow_inf_nan=False)
    to: RendererPointV1 | None = None
    scale: float | None = Field(default=None, ge=0.05, le=4, allow_inf_nan=False)
    rotation_degrees: float | None = Field(
        default=None, alias="rotationDegrees", ge=-360, le=360, allow_inf_nan=False
    )
    opacity: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def require_motion_parameter(self) -> RendererMotionV1:
        if self.kind in {"MOVE", "MOVE_TO", "FLY", "JUMP"} and self.to is None:
            raise ValueError("movement requires a normalized destination")
        if self.kind == "SCALE" and self.scale is None:
            raise ValueError("SCALE requires a bounded scale value")
        if self.kind == "ROTATE" and self.rotation_degrees is None:
            raise ValueError("ROTATE requires bounded rotationDegrees")
        if self.kind == "FADE" and self.opacity is None:
            raise ValueError("FADE requires bounded opacity")
        return self


class RendererStageV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    width: int = Field(ge=240, le=4096)
    height: int = Field(ge=240, le=4096)


class ArtAnimationPlanPayloadV1(BaseModel):
    """Exact protocol-v1 payload consumed by ``packages/art-renderer``."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_version: Literal["1"] = Field(alias="contractVersion")
    plan_id: str = Field(alias="planId", min_length=1, max_length=120)
    plan_version: str = Field(alias="planVersion", pattern=r"^[1-9][0-9]*$")
    stage: RendererStageV1
    objects: tuple[RendererArtObjectV1, ...] = Field(min_length=1, max_length=32)
    motions: tuple[RendererMotionV1, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def require_known_unique_targets(self) -> ArtAnimationPlanPayloadV1:
        object_ids = {item.object_id for item in self.objects}
        motion_ids = [item.motion_id for item in self.motions]
        if len(object_ids) != len(self.objects):
            raise ValueError("renderer object IDs must be unique")
        if len(set(motion_ids)) != len(motion_ids):
            raise ValueError("renderer motion IDs must be unique")
        if any(motion.target_id not in object_ids for motion in self.motions):
            raise ValueError("renderer motion references an unknown target")
        return self


class ArtAnimationPlanV1(BaseModel):
    """FEAT-018 identity wrapper around the unchanged renderer protocol-v1 payload."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["ArtAnimationPlanV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    source_artifact_sha256: str = Field(alias="sourceArtifactSha256", pattern=r"^[a-f0-9]{64}$")
    plan: ArtAnimationPlanPayloadV1
    original_art_preserved: Literal[True] = Field(default=True, alias="originalArtPreserved")
    video_executed: Literal[False] = Field(default=False, alias="videoExecuted")

    @model_validator(mode="after")
    def preserve_source_identity(self) -> ArtAnimationPlanV1:
        whole_drawings = [
            item.asset for item in self.plan.objects if item.asset.asset_kind == "WHOLE_DRAWING"
        ]
        if not whole_drawings:
            raise ValueError("animation plan must retain the whole original drawing")
        if any(asset.source_sha256 != self.source_artifact_sha256 for asset in whole_drawings):
            raise ValueError("whole-drawing hash must match the session source hash")
        if any(
            item.asset.source_sha256 != self.source_artifact_sha256 for item in self.plan.objects
        ):
            raise ValueError("every renderer crop must retain the original source hash")
        return self


class PixiManifestAssetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    asset_id: str = Field(alias="assetId", min_length=1, max_length=160)
    asset_version: str = Field(alias="assetVersion", pattern=r"^[1-9][0-9]*$")
    asset_ref: str = Field(alias="assetRef", min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    role: Literal["ORIGINAL_ART", "SUPPLEMENTAL"]
    review_status: Literal["SOURCE_ORIGINAL", "APPROVED"] = Field(alias="reviewStatus")
    rights_status: Literal["NOT_APPLICABLE", "CLEARED"] = Field(alias="rightsStatus")

    @model_validator(mode="after")
    def require_approved_supplemental(self) -> PixiManifestAssetV1:
        if self.role == "ORIGINAL_ART" and (
            self.review_status != "SOURCE_ORIGINAL" or self.rights_status != "NOT_APPLICABLE"
        ):
            raise ValueError("original source art must be marked as preserved, not substituted")
        if self.role == "SUPPLEMENTAL" and (
            self.review_status != "APPROVED" or self.rights_status != "CLEARED"
        ):
            raise ValueError("supplemental Pixi assets require both visual and rights approval")
        return self


class PixiArtAssetManifestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["PixiArtAssetManifestV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    source_artifact_sha256: str = Field(alias="sourceArtifactSha256", pattern=r"^[a-f0-9]{64}$")
    assets: tuple[PixiManifestAssetV1, ...] = Field(min_length=1, max_length=6)
    original_art_preserved: Literal[True] = Field(default=True, alias="originalArtPreserved")
    provider_generation_called: Literal[False] = Field(
        default=False, alias="providerGenerationCalled"
    )

    @model_validator(mode="after")
    def require_original_and_unique_assets(self) -> PixiArtAssetManifestV1:
        originals = [asset for asset in self.assets if asset.role == "ORIGINAL_ART"]
        if len(originals) != 1:
            raise ValueError("manifest must contain exactly one original-art asset")
        if originals[0].sha256 != self.source_artifact_sha256:
            raise ValueError("manifest original-art hash must match the immutable source")
        ids = [asset.asset_id for asset in self.assets]
        if len(set(ids)) != len(ids):
            raise ValueError("manifest asset IDs must be unique")
        return self


class PixiRendererLaunchV1(BaseModel):
    """Validated source-only launch envelope for the FEAT-018 WebView renderer."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["PixiRendererLaunchV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    expected_session_version: int = Field(alias="expectedSessionVersion", ge=0)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    asset_manifest: PixiArtAssetManifestV1 = Field(alias="assetManifest")
    animation_plan: ArtAnimationPlanV1 = Field(alias="animationPlan")
    scene_exploration_plan: SceneExplorationPlanV1 | None = Field(
        default=None, alias="sceneExplorationPlan"
    )
    scene_focus_plan: SceneFocusPlanV1 | None = Field(default=None, alias="sceneFocusPlan")
    source_read_endpoint: Literal["/v1/renderer/source"] = Field(alias="sourceReadEndpoint")
    source_read_capability: str = Field(alias="sourceReadCapability", min_length=40, max_length=200)
    source_read_expires_at: datetime = Field(alias="sourceReadExpiresAt")

    @model_validator(mode="after")
    def preserve_exact_source_and_experience_identity(self) -> PixiRendererLaunchV1:
        if (
            self.source_read_expires_at.tzinfo is None
            or self.source_read_expires_at.utcoffset() is None
        ):
            raise ValueError("renderer source capability expiry must be timezone-aware")
        identity = (
            self.session_id,
            self.experience_spec_ref,
            self.asset_manifest.source_artifact_ref,
            self.asset_manifest.source_artifact_sha256,
        )
        manifest_identity = (
            self.asset_manifest.session_id,
            self.asset_manifest.experience_spec_ref,
            self.asset_manifest.source_artifact_ref,
            self.asset_manifest.source_artifact_sha256,
        )
        plan_identity = (
            self.animation_plan.session_id,
            self.animation_plan.experience_spec_ref,
            self.animation_plan.source_artifact_ref,
            self.animation_plan.source_artifact_sha256,
        )
        if identity != manifest_identity or identity != plan_identity:
            raise ValueError("renderer manifest and plan must retain the launch identity")
        if self.animation_plan.video_executed or not self.animation_plan.original_art_preserved:
            raise ValueError("image-only renderer must preserve source art and exclude video")
        if self.scene_exploration_plan is not None and (
            self.scene_exploration_plan.session_id != self.session_id
            or self.scene_exploration_plan.experience_spec_ref != self.experience_spec_ref
            or self.scene_exploration_plan.source_artifact_ref
            != self.asset_manifest.source_artifact_ref
        ):
            raise ValueError("scene exploration must retain the renderer launch identity")
        if self.scene_focus_plan is not None and (
            self.scene_focus_plan.session_id != self.session_id
            or self.scene_focus_plan.experience_spec_ref != self.experience_spec_ref
            or self.scene_focus_plan.source_artifact_ref != self.asset_manifest.source_artifact_ref
            or self.scene_focus_plan.source_artifact_sha256
            != self.asset_manifest.source_artifact_sha256
        ):
            raise ValueError("scene focus must retain the renderer source identity")
        return self


class RendererBootstrapV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    protocol_version: Literal["1"] = Field(alias="protocolVersion")
    renderer_instance_id: str = Field(alias="rendererInstanceId", min_length=1, max_length=120)


class RendererPlaybackStartedV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["PLAYBACK_STARTED"]
    planId: str = Field(min_length=1, max_length=120)


class RendererPlaybackCompletedV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["PLAYBACK_COMPLETED"]
    planId: str = Field(min_length=1, max_length=120)


class RendererFallbackAppliedV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["FALLBACK_APPLIED"]
    planId: str = Field(min_length=1, max_length=120)
    reason: Literal[
        "EXTRACTION_UNAVAILABLE", "MASK_INVALID", "ASSET_LOAD_FAILED", "MOTION_COMPILE_FAILED"
    ]


class RendererPlaybackFailedV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["PLAYBACK_FAILED"]
    planId: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=160)


class RendererEntityDiscoveredV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["DISCOVERED_ENTITY"]
    planId: str = Field(min_length=1, max_length=120)
    objectId: str = Field(min_length=1, max_length=120)
    labelVi: str = Field(min_length=1, max_length=60)


class RendererFocusChangedV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["FOCUS_CHANGED"]
    planId: str = Field(min_length=1, max_length=120)
    objectId: str = Field(min_length=1, max_length=120)


RendererEventV1 = Annotated[
    RendererPlaybackStartedV1
    | RendererPlaybackCompletedV1
    | RendererFallbackAppliedV1
    | RendererPlaybackFailedV1
    | RendererEntityDiscoveredV1
    | RendererFocusChangedV1,
    Field(discriminator="type"),
]
RendererEventAdapterV1: TypeAdapter[RendererEventV1] = TypeAdapter(RendererEventV1)


__all__ = [
    "ArtAnimationPlanPayloadV1",
    "ArtAnimationPlanV1",
    "PixiArtAssetManifestV1",
    "PixiManifestAssetV1",
    "PixiRendererLaunchV1",
    "RendererBootstrapV1",
    "RendererChildArtAssetV1",
    "RendererEntityDiscoveredV1",
    "RendererEventAdapterV1",
    "RendererEventV1",
    "RendererFocusChangedV1",
    "SceneExplorationPlanV1",
    "SceneFocusPlanV1",
    "SourceRegionV1",
]
