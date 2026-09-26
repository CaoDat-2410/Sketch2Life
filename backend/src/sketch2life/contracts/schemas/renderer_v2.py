"""Renderer V2 launch and bounded bone-motion contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.auto_rig import RigArchetype, RigDeliveryTier
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1


class BonePoseV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    rotation_degrees: float = Field(
        default=0, alias="rotationDegrees", ge=-30, le=30, allow_inf_nan=False
    )
    translate_x: float = Field(default=0, alias="translateX", ge=-0.15, le=0.15)
    translate_y: float = Field(default=0, alias="translateY", ge=-0.15, le=0.15)
    scale_x: float = Field(default=1, alias="scaleX", ge=0.8, le=1.2)
    scale_y: float = Field(default=1, alias="scaleY", ge=0.8, le=1.2)


class BoneKeyframeV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    at_seconds: float = Field(alias="atSeconds", ge=0, le=30, allow_inf_nan=False)
    pose: BonePoseV2


class BoneMotionTrackV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    track_id: str = Field(alias="trackId", pattern=r"^[a-z][a-z0-9_-]*$")
    bone_id: str = Field(alias="boneId", pattern=r"^[a-z][a-z0-9_-]*$")
    profile: Literal["flutter", "sway", "breathe", "tilt", "swim", "step", "focus"]
    keyframes: tuple[BoneKeyframeV2, ...] = Field(min_length=2, max_length=16)
    repeat: int = Field(default=0, ge=0, le=4)

    @model_validator(mode="after")
    def ascending_keyframes(self) -> BoneMotionTrackV2:
        times = [frame.at_seconds for frame in self.keyframes]
        if times != sorted(times) or len(times) != len(set(times)):
            raise ValueError("track keyframes must have unique ascending times")
        return self


class VisualAnimationPlanV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["VisualAnimationPlanV2"] = Field(alias="contractName")
    contract_version: Literal["2.0"] = Field(alias="contractVersion")
    plan_id: str = Field(alias="planId", min_length=1, max_length=160)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    package_id: str = Field(alias="packageId", min_length=1, max_length=160)
    archetype: RigArchetype
    tier: RigDeliveryTier
    duration_seconds: float = Field(alias="durationSeconds", ge=1, le=30)
    tracks: tuple[BoneMotionTrackV2, ...] = Field(default=(), max_length=32)
    learning_bridge_vi: str = Field(alias="learningBridgeVi", min_length=1, max_length=300)
    max_motion_level: Literal[0, 1, 2] = Field(default=2, alias="maxMotionLevel")


class PixiRendererLaunchV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["PixiRendererLaunchV2"] = Field(alias="contractName")
    contract_version: Literal["2.0"] = Field(alias="contractVersion")
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    expected_session_version: int = Field(alias="expectedSessionVersion", ge=0)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    source_read_endpoint: Literal["/v1/renderer/source"] = Field(alias="sourceReadEndpoint")
    source_read_capability: str = Field(alias="sourceReadCapability", min_length=40, max_length=200)
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    package_read_endpoint: Literal["/v1/renderer/rig-package"] = Field(alias="packageReadEndpoint")
    package_read_capability: str = Field(
        alias="packageReadCapability", min_length=40, max_length=200
    )
    package_sha256: str = Field(alias="packageSha256", pattern=r"^[a-f0-9]{64}$")
    package_read_expires_at: datetime = Field(alias="packageReadExpiresAt")
    animation_plan: VisualAnimationPlanV2 = Field(alias="animationPlan")
    fallback_launch: dict[str, object] = Field(alias="fallbackLaunch")

    @model_validator(mode="after")
    def validate_identity(self) -> PixiRendererLaunchV2:
        if (
            self.package_read_expires_at.tzinfo is None
            or self.package_read_expires_at.utcoffset() is None
        ):
            raise ValueError("package capability expiry must be timezone-aware")
        if self.animation_plan.session_id != self.session_id:
            raise ValueError("animation plan session must match launch")
        if self.animation_plan.experience_spec_ref != self.experience_spec_ref:
            raise ValueError("animation plan experience must match launch")
        return self


class RendererLoadCommandV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["RendererLoadCommandV2"] = Field(alias="contractName")
    contract_version: Literal["2.0"] = Field(alias="contractVersion")
    protocol_version: Literal["2"] = Field(alias="protocolVersion")
    sequence: Literal[1]
    renderer_instance_id: str = Field(alias="rendererInstanceId", min_length=1, max_length=120)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    expected_session_version: int = Field(alias="expectedSessionVersion", ge=0)
    experience_spec_ref: VersionedRefV1 = Field(alias="experienceSpecRef")
    source_read_endpoint: Literal["/v1/renderer/source"] = Field(alias="sourceReadEndpoint")
    source_read_capability: str = Field(alias="sourceReadCapability", min_length=40, max_length=200)
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    package_read_endpoint: Literal["/v1/renderer/rig-package"] = Field(alias="packageReadEndpoint")
    package_read_capability: str = Field(
        alias="packageReadCapability", min_length=40, max_length=200
    )
    package_sha256: str = Field(alias="packageSha256", pattern=r"^[a-f0-9]{64}$")
    animation_plan: VisualAnimationPlanV2 = Field(alias="animationPlan")


__all__ = [
    "BoneKeyframeV2",
    "BoneMotionTrackV2",
    "BonePoseV2",
    "PixiRendererLaunchV2",
    "RendererLoadCommandV2",
    "VisualAnimationPlanV2",
]
