"""Additive, bounded transport for visually approved Pixi sprite cycles."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.pixi_show import (
    PixiRendererLaunchV2,
    PixiShowAssetReadV1,
    PixiShowPlanV1,
    PixiShowPlanV2,
)

PixiSpriteCycleStatusV1 = Literal["READY", "BLOCKED", "NOT_APPLICABLE"]
PixiSpriteCycleReasonCodeV1 = Literal[
    "ASSET_UNAVAILABLE",
    "INVALID_CYCLE_REQUEST",
    "UNKNOWN_CYCLE",
    "VISUAL_REVIEW_REQUIRED",
    "RIGHTS_NOT_CLEARED",
    "FRAME_QA_REQUIRED",
    "CATALOG_NOT_REGISTERED",
    "RENDERER_NOT_VERIFIED",
    "RUNTIME_NOT_ELIGIBLE",
    "FRAME_QA_FAILED",
    "NO_SAFE_PLACEMENT",
]

_BEHAVIOR_IDS = (
    "walker.biped",
    "walker.quadruped",
    "walker.avian",
    "runner.biped",
    "runner.quadruped",
    "hopper",
    "flyer",
    "glider",
    "swimmer",
    "crawler",
    "slitherer",
    "climber",
    "waver",
    "reacher",
    "dancer",
    "turner",
    "swaying_plant",
    "growing",
    "blooming",
    "drifting",
    "falling",
    "flowing",
    "flickering",
    "roller",
    "rotator",
    "swinger",
    "bouncer",
    "slider",
    "opener_closer",
)
_CYCLE_CLASSES_BY_HINT = {
    "BIRD": {"flyer", "glider", "walker.avian"},
    "INSECT": {"flyer", "crawler"},
    "FISH": {"swimmer"},
    "QUADRUPED": {
        "walker.quadruped", "runner.quadruped", "hopper", "crawler", "slitherer", "climber"
    },
    "BIPED": {"walker.biped", "runner.biped", "climber", "waver", "reacher", "dancer", "turner"},
    "PLANT": {"swaying_plant", "growing", "blooming"},
    "VEHICLE": {"roller", "glider", "drifting", "slider", "rotator"},
    "OBJECT": {"roller", "drifting", "slider", "rotator", "swinger", "bouncer", "opener_closer"},
    "UNKNOWN": set(),
}


class PixiSpriteCycleReadV1(BaseModel):
    """Selected cycle data plus short-lived reads for its exact frame sequence."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    cycle_id: str = Field(alias="cycleId", pattern=r"^motion\.[a-z0-9.-]+$", max_length=100)
    behavior_class_id: str = Field(alias="behaviorClassId", max_length=40)
    variant_id: str = Field(alias="variantId", pattern=r"^[a-z0-9-]+$", max_length=60)
    playback_kind: Literal["FRAME_SEQUENCE", "TRANSFORM_DRIVEN"] = Field(alias="playbackKind")
    loop_mode: Literal["LOOP", "ONCE"] = Field(alias="loopMode")
    frame_rate: int = Field(alias="frameRate", ge=1, le=12)
    start_seconds: float = Field(alias="startSeconds", ge=0, le=30, allow_inf_nan=False)
    end_seconds: float = Field(alias="endSeconds", gt=0, le=30, allow_inf_nan=False)
    x: float = Field(ge=0.12, le=0.88, allow_inf_nan=False)
    y: float = Field(ge=0.12, le=0.88, allow_inf_nan=False)
    scale: float = Field(ge=0.2, le=0.6, allow_inf_nan=False)
    frame_reads: tuple[PixiShowAssetReadV1, ...] = Field(
        alias="frameReads", min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def validate_cycle_payload(self) -> PixiSpriteCycleReadV1:
        expected_count = 1 if self.playback_kind == "TRANSFORM_DRIVEN" else 4
        if len(self.frame_reads) != expected_count:
            raise ValueError("cycle frame count does not match its playback kind")
        expected_ids = tuple(
            f"{self.cycle_id}.frame-{index:02d}" for index in range(1, expected_count + 1)
        )
        if tuple(frame.asset_id for frame in self.frame_reads) != expected_ids:
            raise ValueError("cycle frame IDs must be complete and ordered")
        if self.behavior_class_id not in _BEHAVIOR_IDS:
            raise ValueError("cycle behavior class is not in the closed registry")
        if self.end_seconds <= self.start_seconds:
            raise ValueError("cycle beat must have positive duration")
        return self


class PixiRendererShowEnvelopeV2(BaseModel):
    """V1 show envelope plus an optional independently gated motion-cycle sidecar."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    contract_name: Literal["PixiRendererShowEnvelopeV2"] = Field(alias="contractName")
    contract_version: Literal["2.0"] = Field(alias="contractVersion")
    renderer_launch_v2: PixiRendererLaunchV2 = Field(alias="rendererLaunchV2")
    show_plan: PixiShowPlanV1 = Field(alias="showPlan")
    asset_reads: tuple[PixiShowAssetReadV1, ...] = Field(
        alias="assetReads", min_length=1, max_length=3
    )
    sprite_cycle_status: PixiSpriteCycleStatusV1 = Field(alias="spriteCycleStatus")
    sprite_cycle_reason_code: PixiSpriteCycleReasonCodeV1 | None = Field(
        default=None, alias="spriteCycleReasonCode"
    )
    sprite_cycle: PixiSpriteCycleReadV1 | None = Field(default=None, alias="spriteCycle")

    @model_validator(mode="after")
    def validate_envelope_identity(self) -> PixiRendererShowEnvelopeV2:
        launch, plan = self.renderer_launch_v2, self.show_plan
        if (
            launch.session_id != plan.session_id
            or launch.source_sha256 != plan.source_sha256
            or launch.animation_plan.package_id != plan.package_id
            or launch.experience_spec_ref != plan.experience_spec_ref
        ):
            raise ValueError("show envelope identities must match the V2 renderer launch")
        read_ids = tuple(item.asset_id for item in self.asset_reads)
        if len(set(read_ids)) != len(read_ids) or set(read_ids) != set(plan.selected_asset_ids):
            raise ValueError("static asset reads must exactly match selected show asset IDs")
        cycle = self.sprite_cycle
        if cycle is not None and cycle.end_seconds > plan.duration_seconds:
            raise ValueError("sprite cycle must finish within the show duration")
        if self.sprite_cycle_status == "READY" and (
            cycle is None or self.sprite_cycle_reason_code is not None
        ):
            raise ValueError("ready cycle status requires exactly one cycle and no reason")
        if self.sprite_cycle_status == "BLOCKED" and (
            cycle is not None or self.sprite_cycle_reason_code is None
        ):
            raise ValueError(
                "blocked cycle status requires a safe reason and no frame capabilities"
            )
        if self.sprite_cycle_status == "NOT_APPLICABLE" and (
            cycle is not None or self.sprite_cycle_reason_code is not None
        ):
            raise ValueError("not-applicable status cannot contain cycle data or a failure reason")
        if cycle is not None:
            compatible_classes = _CYCLE_CLASSES_BY_HINT[
                plan.visual_subject_hint_id.value
            ]
            if cycle.behavior_class_id not in compatible_classes:
                raise ValueError("sprite cycle is incompatible with the confirmed subject family")
            region = plan.source_subject_region
            if (
                region.x - 0.14 <= cycle.x <= region.x + region.width + 0.14
                and region.y - 0.14 <= cycle.y <= region.y + region.height + 0.14
            ):
                raise ValueError("sprite cycle overlaps the padded source-subject bounds")
            if any(
                beat.target_role == "SUPPLEMENTAL_ASSET"
                and (beat.x - cycle.x) ** 2 + (beat.y - cycle.y) ** 2 < 0.22**2
                for beat in plan.beats
            ):
                raise ValueError("sprite cycle overlaps a static supplemental asset")
        return self


class PixiRendererShowEnvelopeV3(PixiRendererShowEnvelopeV2):
    """V3 adds source-only plans while preserving the V2 cycle sidecar contract."""

    # Pydantic enforces each concrete protocol discriminator at runtime.
    contract_name: Literal["PixiRendererShowEnvelopeV3"] = Field(alias="contractName")  # type: ignore[assignment]  # noqa: E501
    contract_version: Literal["3.0"] = Field(alias="contractVersion")  # type: ignore[assignment]  # noqa: E501
    show_plan: PixiShowPlanV2 = Field(alias="showPlan")
    asset_reads: tuple[PixiShowAssetReadV1, ...] = Field(
        alias="assetReads", min_length=0, max_length=3
    )


__all__ = [
    "PixiRendererShowEnvelopeV2",
    "PixiRendererShowEnvelopeV3",
    "PixiSpriteCycleReadV1",
    "PixiSpriteCycleReasonCodeV1",
    "PixiSpriteCycleStatusV1",
]
