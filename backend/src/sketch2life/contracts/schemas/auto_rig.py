"""Versioned original-derived auto-rig contracts for FEAT-030."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


class RigArchetype(StrEnum):
    BUTTERFLY = "butterfly"
    BIRD = "bird"
    FLOWER = "flower"
    TREE_BRANCH = "tree_branch"
    FISH = "fish"
    BIPED = "biped"
    RIGID = "rigid"
    GENERIC_ORGANIC = "generic_organic"
    UNKNOWN = "unknown"


class RigDeliveryTier(StrEnum):
    FULL_AUTO_RIG = "FULL_AUTO_RIG"
    CUTOUT_MICRO_MOTION = "CUTOUT_MICRO_MOTION"
    BBOX_VISUAL_FOCUS = "BBOX_VISUAL_FOCUS"
    WHOLE_DRAWING_V1 = "WHOLE_DRAWING_V1"


class RigJobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class RigJobStage(StrEnum):
    TARGETING = "TARGETING"
    GROUNDING = "GROUNDING"
    SEGMENTING = "SEGMENTING"
    CLEANING = "CLEANING"
    ARCHETYPE = "ARCHETYPE"
    RIGGING = "RIGGING"
    VALIDATING = "VALIDATING"
    PACKAGING = "PACKAGING"


class RigTargetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    canonical_entity_id: str = Field(alias="canonicalEntityId", min_length=1, max_length=160)
    normalized_label: str = Field(alias="normalizedLabel", min_length=1, max_length=160)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    semantic_tags: tuple[str, ...] = Field(default=(), alias="semanticTags", max_length=32)


class RigPreparationRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["RigPreparationRequestV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    request_id: str = Field(alias="requestId", min_length=1, max_length=160)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    target: RigTargetV1
    experience_spec_ref: VersionedRefV1 | None = Field(default=None, alias="experienceSpecRef")
    max_motion_level: Literal[0, 1, 2] = Field(default=2, alias="maxMotionLevel")
    pipeline_version: str = Field(alias="pipelineVersion", pattern=r"^[1-9][0-9]*$")
    idempotency_key: str = Field(alias="idempotencyKey", min_length=8, max_length=200)


class RigVertexV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)
    u: float = Field(ge=0, le=1, allow_inf_nan=False)
    v: float = Field(ge=0, le=1, allow_inf_nan=False)


class RigTriangleV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    a: int = Field(ge=0, le=1023)
    b: int = Field(ge=0, le=1023)
    c: int = Field(ge=0, le=1023)

    @model_validator(mode="after")
    def unique_indices(self) -> RigTriangleV1:
        if len({self.a, self.b, self.c}) != 3:
            raise ValueError("triangle indices must be distinct")
        return self


class RigBoneV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    bone_id: str = Field(alias="boneId", pattern=r"^[a-z][a-z0-9_-]*$")
    parent_id: str | None = Field(default=None, alias="parentId", pattern=r"^[a-z][a-z0-9_-]*$")
    pivot_x: float = Field(alias="pivotX", ge=0, le=1, allow_inf_nan=False)
    pivot_y: float = Field(alias="pivotY", ge=0, le=1, allow_inf_nan=False)
    max_rotation_degrees: float = Field(
        alias="maxRotationDegrees", ge=0, le=30, allow_inf_nan=False
    )


class RigInfluenceV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    bone_id: str = Field(alias="boneId", pattern=r"^[a-z][a-z0-9_-]*$")
    weight: float = Field(gt=0, le=1, allow_inf_nan=False)


class RigVertexWeightsV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    vertex_index: int = Field(alias="vertexIndex", ge=0, le=1023)
    influences: tuple[RigInfluenceV1, ...] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def normalized(self) -> RigVertexWeightsV1:
        if abs(sum(item.weight for item in self.influences) - 1) > 1e-5:
            raise ValueError("vertex influence weights must sum to one")
        ids = [item.bone_id for item in self.influences]
        if len(ids) != len(set(ids)):
            raise ValueError("vertex influences must reference unique bones")
        return self


class RigDefinitionV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["RigDefinitionV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    archetype: RigArchetype
    source_region: SourceRegionV1 = Field(alias="sourceRegion")
    vertices: tuple[RigVertexV1, ...] = Field(min_length=4, max_length=1024)
    triangles: tuple[RigTriangleV1, ...] = Field(min_length=2, max_length=2048)
    bones: tuple[RigBoneV1, ...] = Field(min_length=1, max_length=32)
    weights: tuple[RigVertexWeightsV1, ...] = Field(min_length=4, max_length=1024)

    @model_validator(mode="after")
    def validate_graph(self) -> RigDefinitionV1:
        bone_ids = {bone.bone_id for bone in self.bones}
        if len(bone_ids) != len(self.bones):
            raise ValueError("bone IDs must be unique")
        if any(
            bone.parent_id is not None and bone.parent_id not in bone_ids for bone in self.bones
        ):
            raise ValueError("bone parent must exist")
        if any(
            max(triangle.a, triangle.b, triangle.c) >= len(self.vertices)
            for triangle in self.triangles
        ):
            raise ValueError("triangle references an unknown vertex")
        if len(self.weights) != len(self.vertices):
            raise ValueError("every vertex requires weights")
        if {item.vertex_index for item in self.weights} != set(range(len(self.vertices))):
            raise ValueError("vertex weights must cover each vertex exactly once")
        if any(
            influence.bone_id not in bone_ids
            for item in self.weights
            for influence in item.influences
        ):
            raise ValueError("weight references an unknown bone")
        return self


class RigValidationResultV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["RigValidationResultV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    valid: bool
    selected_tier: RigDeliveryTier = Field(alias="selectedTier")
    reason_codes: tuple[str, ...] = Field(default=(), alias="reasonCodes", max_length=16)
    validator_version: str = Field(alias="validatorVersion", pattern=r"^[1-9][0-9]*$")


class DerivedArtifactRefV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    artifact_ref: str = Field(alias="artifactRef", min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: str = Field(alias="contentType", min_length=1, max_length=100)
    byte_length: int = Field(alias="byteLength", ge=1, le=10_000_000)
    role: Literal[
        "ORIGINAL_DERIVED_MASK",
        "ORIGINAL_DERIVED_TEXTURE",
        "ORIGINAL_DERIVED_BACKGROUND_PATCH",
        "ORIGINAL_DERIVED_RIG_PACKAGE",
    ]
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    operation: str = Field(min_length=1, max_length=120)
    operation_version: str = Field(alias="operationVersion", min_length=1, max_length=40)


class RiggedArtworkPackageV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["RiggedArtworkPackageV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    package_id: str = Field(alias="packageId", min_length=1, max_length=160)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    source_artifact_ref: str = Field(alias="sourceArtifactRef", min_length=1, max_length=300)
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    target: RigTargetV1
    archetype: RigArchetype
    tier: RigDeliveryTier
    rig: RigDefinitionV1 | None = None
    derived_artifacts: tuple[DerivedArtifactRefV1, ...] = Field(
        default=(), alias="derivedArtifacts", max_length=4
    )
    validation: RigValidationResultV1
    pipeline_version: str = Field(alias="pipelineVersion", pattern=r"^[1-9][0-9]*$")
    created_at: datetime = Field(alias="createdAt")
    original_art_preserved: Literal[True] = Field(default=True, alias="originalArtPreserved")

    @model_validator(mode="after")
    def validate_tier_payload(self) -> RiggedArtworkPackageV1:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("package creation time must be timezone-aware")
        if self.tier == RigDeliveryTier.FULL_AUTO_RIG and self.rig is None:
            raise ValueError("full auto-rig tier requires a rig definition")
        if self.validation.selected_tier != self.tier:
            raise ValueError("validation tier must match package tier")
        if any(item.source_sha256 != self.source_sha256 for item in self.derived_artifacts):
            raise ValueError("every derived artifact must retain the source hash")
        return self


class AutoRigJobV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["AutoRigJobV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    job_id: str = Field(alias="jobId", min_length=1, max_length=160)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    request_id: str = Field(alias="requestId", min_length=1, max_length=160)
    status: RigJobStatus
    stage: RigJobStage
    progress: int = Field(ge=0, le=100)
    display_message_key: str = Field(alias="displayMessageKey", min_length=1, max_length=80)
    attempt: int = Field(default=1, ge=1, le=2)
    package_ref: str | None = Field(default=None, alias="packageRef", max_length=300)
    selected_tier: RigDeliveryTier | None = Field(default=None, alias="selectedTier")
    failure_code: str | None = Field(default=None, alias="failureCode", max_length=80)
    retryable: bool = False
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


__all__ = [
    "AutoRigJobV1",
    "DerivedArtifactRefV1",
    "RigArchetype",
    "RigBoneV1",
    "RigDefinitionV1",
    "RigDeliveryTier",
    "RigInfluenceV1",
    "RigJobStage",
    "RigJobStatus",
    "RigPreparationRequestV1",
    "RigTargetV1",
    "RigTriangleV1",
    "RigValidationResultV1",
    "RigVertexV1",
    "RigVertexWeightsV1",
    "RiggedArtworkPackageV1",
]
