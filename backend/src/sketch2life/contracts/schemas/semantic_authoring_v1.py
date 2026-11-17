"""Portable, strict local authoring JSON contract; not server approval."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2


class RegionAuthoringV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    region_id: str
    semantic_label: str
    mask_ref: str
    mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provenance: str


class StrokeAuthoringV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    path: ObjectStrokeV2
    role: Literal["PRIMARY_CONTOUR", "DISTINCTIVE_DETAIL", "COLOR_REGION", "OPTIONAL_TEXTURE"]
    region_id: str
    essential: bool = True
    minimum_down_seconds: float = Field(default=0.0, ge=0.0, le=120.0)

    @model_validator(mode="after")
    def role_phase(self):
        expected = {
            "PRIMARY_CONTOUR": "OUTLINE",
            "DISTINCTIVE_DETAIL": "DETAIL",
            "OPTIONAL_TEXTURE": "DETAIL",
            "COLOR_REGION": "COLOR",
        }
        if self.path.phase != expected[self.role]:
            raise ValueError("NEEDS_AUTHORING_REVIEW: role/phase mismatch")
        if (
            self.role in {"PRIMARY_CONTOUR", "DISTINCTIVE_DETAIL", "COLOR_REGION"}
            and not self.essential
        ):
            raise ValueError("essential identity/coverage cannot be made optional")
        return self


class SemanticAuthoringPackV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    contract: Literal["SemanticDrawingAuthoringPack"] = "SemanticDrawingAuthoringPack"
    version: Literal["1.0"] = "1.0"
    object_id: str
    asset_ref: str
    asset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provenance: Literal["SOURCE_DRAWING", "NEW_LOCAL_AUTHORED"]
    authoring_method: str
    approval: Literal["TECHNICAL_PROOF_ONLY", "OWNER_APPROVAL_PENDING", "OWNER_APPROVED_LOCAL"]
    route: Literal["AUTO", "REVIEW", "FALLBACK"] = "REVIEW"
    presentation_scale: float = Field(default=1.0, ge=0.05, le=1.0)
    target_seconds: float = Field(gt=0.0, le=300.0)
    regions: tuple[RegionAuthoringV1, ...] = Field(min_length=1, max_length=128)
    strokes: tuple[StrokeAuthoringV1, ...] = Field(min_length=1, max_length=4096)
    stroke_order: tuple[str, ...]
    ink_provenance: Literal["TEMPORARY_SOURCE_DERIVED_INK"] = "TEMPORARY_SOURCE_DERIVED_INK"

    @model_validator(mode="after")
    def references(self):
        region_ids = [r.region_id for r in self.regions]
        ids = [s.path.stroke_id for s in self.strokes]
        if len(set(region_ids)) != len(region_ids) or len(set(ids)) != len(ids):
            raise ValueError("duplicate region or path ID")
        if len(self.stroke_order) != len(ids) or set(self.stroke_order) != set(ids):
            raise ValueError("stroke order must reference every path exactly once")
        if any(s.path.phase == "COLOR" and s.region_id not in region_ids for s in self.strokes):
            raise ValueError("unknown color region")
        ranks = {"OUTLINE": 0, "DETAIL": 1, "COLOR": 2}
        by_id = {s.path.stroke_id: s for s in self.strokes}
        order = [ranks[by_id[i].path.phase] for i in self.stroke_order]
        if order != sorted(order):
            raise ValueError("outline/detail/color order must not regress")
        if sum(len(s.path.points) for s in self.strokes) > 200_000:
            raise ValueError("authoring point budget exceeded")
        return self
