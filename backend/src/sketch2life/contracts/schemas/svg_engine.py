"""Strict HTTP DTOs for SVG source intake, review, and guide playback."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator


SvgId = Annotated[str, StringConstraints(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9._:-]+$")]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
HttpsUrl = Annotated[str, StringConstraints(max_length=2048, pattern=r"^https://")]
ShortVietnameseText = Annotated[str, StringConstraints(min_length=1, max_length=300)]
SvgColor = Annotated[str, StringConstraints(pattern=r"^(?:none|#[0-9a-fA-F]{6})$")]


class StrictSvgModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SvgPathV1(StrictSvgModel):
    path_id: SvgId
    d: Annotated[str, Field(min_length=1, max_length=8192)]
    fill: str
    stroke: str
    stroke_width: float = Field(gt=0, le=64)


class SvgDocumentV1(StrictSvgModel):
    schema_version: Literal["SvgDocumentV1"] = "SvgDocumentV1"
    view_box: Annotated[
        str,
        Field(
            pattern=r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)? "
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)? "
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)? "
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
        ),
    ]
    paths: list[SvgPathV1] = Field(min_length=1, max_length=400)


class TeacherSvgIllustrationDraftRequestV1(StrictSvgModel):
    contract: Literal["TeacherSvgIllustrationDraftRequestV1"] = (
        "TeacherSvgIllustrationDraftRequestV1"
    )
    topic: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    target_age_months: int = Field(ge=36, le=120)
    visual_style: Literal["warm_storybook", "simple_classroom", "clean_outline"]


class SvgIllustrationModelResultV1(StrictSvgModel):
    schema_version: Literal["SvgIllustrationContentV1"]
    title_vi: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    alt_text_vi: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    document: SvgDocumentV1


class SvgModelProvenanceV1(StrictSvgModel):
    id: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    revision: Annotated[str, StringConstraints(min_length=1, max_length=160)]


class SvgReferenceSourceProvenanceV1(StrictSvgModel):
    asset_id: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    dataset_name: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    dataset_revision: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    dataset_doi: Annotated[str | None, StringConstraints(min_length=1, max_length=80)] = None
    dataset_uri: HttpsUrl | None = None
    source_sha256: Sha256Hex
    license_id: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    license_uri: HttpsUrl


class SvgTopicStrokeGuideRequestV1(StrictSvgModel):
    contract: Literal["SvgTopicStrokeGuideRequestV1"] = "SvgTopicStrokeGuideRequestV1"
    topic: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    difficulty: Literal["beginner", "simple"] = "beginner"


class SvgTopicStrokeGuidePartV1(StrictSvgModel):
    part_id: SvgId
    label_vi: ShortVietnameseText
    path_ids: list[SvgId] = Field(min_length=1, max_length=64)
    depends_on: list[SvgId] = Field(default_factory=list, max_length=32)


class SvgTopicStrokeGuideStageV1(StrictSvgModel):
    step_index: int = Field(strict=True, ge=1, le=8)
    instruction_vi: Annotated[str, Field(min_length=1, max_length=120)]
    part_ids: list[SvgId] = Field(min_length=1, max_length=32)
    new_path_ids: list[SvgId] = Field(min_length=1, max_length=64)
    animation_order: list[SvgId] = Field(min_length=1, max_length=64)


class SvgTopicStrokeGuideV1(StrictSvgModel):
    schema_version: Literal["SvgTopicStrokeGuideV1"] = "SvgTopicStrokeGuideV1"
    guide_id: SvgId
    title_vi: ShortVietnameseText
    parts: list[SvgTopicStrokeGuidePartV1] = Field(min_length=1, max_length=32)
    stages: list[SvgTopicStrokeGuideStageV1] = Field(min_length=4, max_length=8)


class SvgTopicStrokeGuideModelResultV1(StrictSvgModel):
    schema_version: Literal["SvgTopicStrokeGuideContentV1"]
    title_vi: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    document: SvgDocumentV1
    parts: list[SvgTopicStrokeGuidePartV1] = Field(min_length=1, max_length=32)
    stages: list[SvgTopicStrokeGuideStageV1] = Field(min_length=4, max_length=8)


class SvgConstructionStrokeV1(StrictSvgModel):
    path_id: Annotated[str, StringConstraints(pattern=r"^guide_stroke_[0-9]{2}$")]
    d: Annotated[str, Field(min_length=1, max_length=768, pattern=r"^[MLCQZ0-9+.,\-eE\s]+$")]
    role: Literal["construction", "outline", "feature"]
    feature_vi: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    source_path_ids: list[SvgId] = Field(min_length=1, max_length=6)


class SvgConstructionGuideStageV1(StrictSvgModel):
    step_index: int = Field(strict=True, ge=1, le=8)
    label_vi: Annotated[str, StringConstraints(min_length=1, max_length=60)]
    instruction_vi: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    stroke_ids: list[
        Annotated[str, StringConstraints(pattern=r"^guide_stroke_[0-9]{2}$")]
    ] = Field(min_length=1, max_length=20)


class SvgTopicStrokeGuideConstructionModelResultV1(StrictSvgModel):
    schema_version: Literal["SvgTopicStrokeGuideConstructionContentV1"]
    title_vi: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    strokes: list[SvgConstructionStrokeV1] = Field(min_length=8, max_length=20)
    stages: list[SvgConstructionGuideStageV1] = Field(min_length=4, max_length=8)


class SvgTopicStrokeGuideDraftResponseV1(StrictSvgModel):
    contract: Literal["SvgTopicStrokeGuideDraftV1"] = "SvgTopicStrokeGuideDraftV1"
    request_id: SvgId
    modal_call_id: SvgId
    topic: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    status: Literal["DRAFT"]
    review_required: Literal[True]
    persisted: Literal[False]
    model: SvgModelProvenanceV1
    reference_source: SvgReferenceSourceProvenanceV1 | None = None
    document: SvgDocumentV1
    document_sha256: Sha256Hex
    guide: SvgTopicStrokeGuideV1
    path_count: int = Field(ge=8, le=64)
    stage_count: int = Field(ge=4, le=8)
    quality_gates_passed: list[str] = Field(min_length=4, max_length=16)


class SvgTopicStrokeGuidePathLineageV1(StrictSvgModel):
    derived_path_id: SvgId
    source_path_ids: list[SvgId] = Field(min_length=1, max_length=16)
    feature_vi: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    operation: Literal[
        "MANUAL_HEN_DRAWING_SEQUENCE_V5",
        "REFERENCE_ALIGNED_CHILD_DRAWING_SEQUENCE_V6",
        "EXACT_SOURCE_PATH_SEQUENCE_V7",
        "OPENMOJI_SOURCE_SHAPE_TO_PATH_V1",
        "OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1",
        "QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1",
    ]


class SvgTopicStrokeGuideDerivationV1(StrictSvgModel):
    engine_id: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    engine_revision: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    source_guide_uri: HttpsUrl | None = None
    source_guide_sha256: Sha256Hex | None = None
    method: Literal[
        "MANUAL_HEN_DRAWING_SEQUENCE_V5",
        "REFERENCE_ALIGNED_CHILD_DRAWING_SEQUENCE_V6",
        "EXACT_SOURCE_PATH_SEQUENCE_V7",
        "OPENMOJI_SOURCE_SHAPE_TO_PATH_V1",
        "OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1",
        "QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1",
    ]
    source_path_count: int = Field(ge=1, le=5000)
    path_lineage: list[SvgTopicStrokeGuidePathLineageV1] = Field(min_length=1, max_length=400)


class SvgReferenceIllustrationPathV1(StrictSvgModel):
    path_id: SvgId
    d: Annotated[str, Field(min_length=1, max_length=8192)]
    fill: SvgColor
    stroke: SvgColor
    stroke_width: float = Field(gt=0, le=64)
    stroke_linecap: Literal["butt", "round", "square"] = "round"
    stroke_linejoin: Literal["miter", "round", "bevel"] = "round"
    stroke_miterlimit: float = Field(default=4, ge=1, le=10)


class SvgReferenceIllustrationDocumentV1(StrictSvgModel):
    schema_version: Literal["SvgReferenceIllustrationV1"] = "SvgReferenceIllustrationV1"
    view_box: Annotated[
        str,
        Field(
            pattern=r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)? "
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)? "
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)? "
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
        ),
    ]
    paths: list[SvgReferenceIllustrationPathV1] = Field(min_length=1, max_length=400)


class SvgTopicStrokeGuideSourceDraftResponseV1(StrictSvgModel):
    contract: Literal["SvgTopicStrokeGuideSourceDraftV1"] = "SvgTopicStrokeGuideSourceDraftV1"
    request_id: SvgId
    topic: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    status: Literal["DRAFT"]
    review_required: Literal[True]
    persisted: Literal[False]
    generation_source: Literal["CURATED_SOURCE_DERIVATION", "QWEN_SOURCE_PATH_DERIVATION"]
    model: SvgModelProvenanceV1 | None = None
    modal_call_id: SvgId | None = None
    derivation: SvgTopicStrokeGuideDerivationV1
    reference_source: SvgReferenceSourceProvenanceV1
    reference_illustration: SvgReferenceIllustrationDocumentV1
    document: SvgDocumentV1
    document_sha256: Sha256Hex
    guide: SvgTopicStrokeGuideV1
    path_count: int = Field(ge=1, le=400)
    stage_count: int = Field(ge=4, le=8)
    quality_gates_passed: list[str] = Field(min_length=4, max_length=16)


class SvgTopicStrokeGuideConstructionPathLineageV1(StrictSvgModel):
    derived_path_id: Annotated[str, StringConstraints(pattern=r"^guide_stroke_[0-9]{2}$")]
    source_path_ids: list[SvgId] = Field(min_length=1, max_length=6)
    feature_vi: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    role: Literal["construction", "outline", "feature"]


class SvgTopicStrokeGuideConstructionDerivationV1(StrictSvgModel):
    engine_id: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    engine_revision: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    method: Literal["QWEN_REFERENCE_CONDITIONED_CONSTRUCTION_V1"]
    source_path_count: int = Field(ge=1, le=5000)
    path_lineage: list[SvgTopicStrokeGuideConstructionPathLineageV1] = Field(
        min_length=8, max_length=20
    )


class SvgTopicStrokeGuideConstructionDraftResponseV1(StrictSvgModel):
    contract: Literal["SvgTopicStrokeGuideConstructionDraftV1"] = (
        "SvgTopicStrokeGuideConstructionDraftV1"
    )
    request_id: SvgId
    topic: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    status: Literal["DRAFT"]
    review_required: Literal[True]
    persisted: Literal[False]
    generation_source: Literal["QWEN_REFERENCE_CONDITIONED_CONSTRUCTION"]
    model: SvgModelProvenanceV1
    modal_call_id: SvgId
    derivation: SvgTopicStrokeGuideConstructionDerivationV1
    reference_source: SvgReferenceSourceProvenanceV1
    reference_illustration: SvgReferenceIllustrationDocumentV1
    document: SvgDocumentV1
    document_sha256: Sha256Hex
    guide: SvgTopicStrokeGuideV1
    path_count: int = Field(ge=8, le=20)
    stage_count: int = Field(ge=4, le=8)
    quality_gates_passed: list[str] = Field(min_length=4, max_length=20)


class TeacherSvgIllustrationDraftResponseV1(StrictSvgModel):
    contract: Literal["TeacherSvgIllustrationDraftV1"] = "TeacherSvgIllustrationDraftV1"
    request_id: SvgId
    modal_call_id: SvgId
    status: Literal["DRAFT"]
    review_required: Literal[True]
    persisted: Literal[False]
    model: SvgModelProvenanceV1
    title_vi: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    alt_text_vi: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    document: SvgDocumentV1
    document_sha256: Sha256Hex
    path_count: int = Field(ge=4, le=20)


class SvgGuidePartV3(StrictSvgModel):
    part_id: SvgId
    label_vi: ShortVietnameseText
    path_ids: list[SvgId] = Field(min_length=1, max_length=400)
    depends_on: list[SvgId] = Field(default_factory=list, max_length=64)


class SvgGuideStageV3(StrictSvgModel):
    step_index: int = Field(ge=1, le=8)
    instruction_vi: Annotated[str, Field(min_length=1, max_length=500)]
    part_ids: list[SvgId] = Field(min_length=1, max_length=64)
    new_path_ids: list[SvgId] = Field(min_length=1, max_length=400)
    animation_order: list[SvgId] = Field(min_length=1, max_length=400)


class SketchStrokeGuideV3(StrictSvgModel):
    schema_version: Literal["SketchStrokeGuideV3"] = "SketchStrokeGuideV3"
    guide_id: SvgId
    title_vi: ShortVietnameseText
    source_asset_ref: SvgId
    source_asset_version: int = Field(ge=1)
    source_sha256: Sha256Hex
    parts: list[SvgGuidePartV3] = Field(min_length=1, max_length=64)
    stages: list[SvgGuideStageV3] = Field(min_length=4, max_length=8)


class SvgCatalogAssetCreateRequestV1(StrictSvgModel):
    contract: Literal["SvgCatalogAssetCreateRequestV1"] = "SvgCatalogAssetCreateRequestV1"
    title_vi: ShortVietnameseText
    topic_key: Annotated[str, StringConstraints(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")]
    alt_text_vi: Annotated[str, Field(min_length=1, max_length=500)]
    source_uri: HttpsUrl
    license_id: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    license_uri: HttpsUrl
    source_svg: Annotated[str, Field(min_length=1, max_length=1_000_000)]


class SvgSourceReviewRequestV1(StrictSvgModel):
    contract: Literal["SvgSourceReviewRequestV1"] = "SvgSourceReviewRequestV1"
    source_sha256: Sha256Hex
    decision: Literal["APPROVE", "REJECT"]
    reason: Annotated[str, Field(max_length=1000)] | None = None

    @model_validator(mode="after")
    def reject_needs_reason(self) -> SvgSourceReviewRequestV1:
        if self.decision == "REJECT" and not (self.reason or "").strip():
            raise ValueError("reason is required for a rejected source")
        return self


class CreateSvgGuideRevisionRequestV1(StrictSvgModel):
    contract: Literal["CreateSvgGuideRevisionRequestV1"] = "CreateSvgGuideRevisionRequestV1"
    guide: SketchStrokeGuideV3


class SvgReviewReceiptV1(StrictSvgModel):
    contract: Literal["SvgReviewReceiptV1"] = "SvgReviewReceiptV1"
    review_id: SvgId
    catalog_entry_id: SvgId
    review_subject_kind: Literal["SOURCE_ASSET", "GUIDE"]
    review_kind: Literal["EDUCATOR", "CURATOR"]
    decision: Literal["APPROVE", "REJECT"]
    source_sha256: Sha256Hex
    guide_sha256: Sha256Hex | None = None
    grouping_allowed: bool = False
    reviewer_ref: SvgId
    created_at: AwareDatetime


class SvgGuideRevisionReceiptV1(StrictSvgModel):
    contract: Literal["SvgGuideRevisionReceiptV1"] = "SvgGuideRevisionReceiptV1"
    guide_revision_id: SvgId
    guide_ref: SvgId
    guide_revision: int = Field(ge=1)
    source_sha256: Sha256Hex
    guide_sha256: Sha256Hex
    guide: SketchStrokeGuideV3
    authored_by: SvgId
    visibility_scope: Literal["PLATFORM", "ORGANIZATION"]
    organization_id: SvgId | None = None
    review_state: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"


class SvgGuideRevisionListItemV1(SvgGuideRevisionReceiptV1):
    pass


class SvgGuideRevisionPageV1(StrictSvgModel):
    contract: Literal["SvgGuideRevisionPageV1"] = "SvgGuideRevisionPageV1"
    items: list[SvgGuideRevisionListItemV1]


class SvgGuideReviewRequestV1(StrictSvgModel):
    contract: Literal["SvgGuideReviewRequestV1"] = "SvgGuideReviewRequestV1"
    source_sha256: Sha256Hex
    guide_sha256: Sha256Hex
    decision: Literal["APPROVE", "REJECT"]
    reason: Annotated[str, Field(max_length=1000)] | None = None

    @model_validator(mode="after")
    def reject_needs_reason(self) -> SvgGuideReviewRequestV1:
        if self.decision == "REJECT" and not (self.reason or "").strip():
            raise ValueError("reason is required for a rejected guide")
        return self


class SvgCurationRequestV1(StrictSvgModel):
    contract: Literal["SvgCurationRequestV1"] = "SvgCurationRequestV1"
    source_sha256: Sha256Hex
    decision: Literal["APPROVE", "REJECT"]
    grouping_allowed: bool = False
    reason: Annotated[str, Field(max_length=1000)] | None = None

    @model_validator(mode="after")
    def curator_constraints(self) -> SvgCurationRequestV1:
        if self.grouping_allowed and self.decision != "APPROVE":
            raise ValueError("grouping can be enabled only by an approved curation decision")
        if self.decision == "REJECT" and not (self.reason or "").strip():
            raise ValueError("reason is required for a rejected catalog item")
        return self


class SvgCatalogAssetResponseV1(StrictSvgModel):
    contract: Literal["SvgCatalogAssetResponseV1"] = "SvgCatalogAssetResponseV1"
    catalog_entry_id: SvgId
    source_asset_ref: SvgId
    source_asset_version: int = Field(ge=1)
    canonical_asset_ref: SvgId
    canonical_asset_version: int = Field(ge=1)
    source_sha256: Sha256Hex
    canonical_sha256: Sha256Hex
    topic_key: str
    title_vi: str
    alt_text_vi: str
    source_uri: HttpsUrl
    license_id: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    license_uri: HttpsUrl
    visibility_scope: Literal["PLATFORM", "ORGANIZATION"]
    organization_id: SvgId | None = None
    created_by: SvgId
    readiness: Literal["STROKE_READY", "REQUIRES_MANUAL_AUTHORING", "STATIC_ONLY"]
    readiness_reasons: list[str]
    structural_facts: dict[str, int | float]
    review_state: Literal[
        "PENDING_EDUCATOR_REVIEW", "PENDING_CURATOR_REVIEW", "APPROVED", "REJECTED", "ARCHIVED"
    ]
    document: SvgDocumentV1 | None = None


class SvgGuideCatalogItemV1(StrictSvgModel):
    contract: Literal["SvgGuideCatalogItemV1"] = "SvgGuideCatalogItemV1"
    catalog_entry_id: SvgId
    guide_revision_id: SvgId
    topic_key: str
    title_vi: str
    alt_text_vi: str
    source_uri: HttpsUrl
    license_id: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    license_uri: HttpsUrl
    source_sha256: Sha256Hex
    guide_sha256: Sha256Hex
    document: SvgDocumentV1
    guide: SketchStrokeGuideV3


class SvgCatalogPageV1(StrictSvgModel):
    contract: Literal["SvgCatalogPageV1"] = "SvgCatalogPageV1"
    items: list[SvgCatalogAssetResponseV1]


class SvgGuideCatalogPageV1(StrictSvgModel):
    contract: Literal["SvgGuideCatalogPageV1"] = "SvgGuideCatalogPageV1"
    items: list[SvgGuideCatalogItemV1]


__all__ = [
    "SketchStrokeGuideV3",
    "SvgIllustrationModelResultV1",
    "SvgTopicStrokeGuideDraftResponseV1",
    "SvgTopicStrokeGuideDerivationV1",
    "SvgTopicStrokeGuideModelResultV1",
    "SvgTopicStrokeGuidePathLineageV1",
    "SvgTopicStrokeGuidePartV1",
    "SvgTopicStrokeGuideRequestV1",
    "SvgTopicStrokeGuideSourceDraftResponseV1",
    "SvgTopicStrokeGuideConstructionDraftResponseV1",
    "SvgTopicStrokeGuideConstructionDerivationV1",
    "SvgTopicStrokeGuideConstructionModelResultV1",
    "SvgTopicStrokeGuideConstructionPathLineageV1",
    "SvgConstructionGuideStageV1",
    "SvgConstructionStrokeV1",
    "SvgTopicStrokeGuideStageV1",
    "SvgTopicStrokeGuideV1",
    "SvgCatalogAssetCreateRequestV1",
    "SvgCatalogAssetResponseV1",
    "SvgCatalogPageV1",
    "SvgCurationRequestV1",
    "CreateSvgGuideRevisionRequestV1",
    "SvgDocumentV1",
    "SvgGuideCatalogItemV1",
    "SvgGuideCatalogPageV1",
    "SvgGuideRevisionReceiptV1",
    "SvgGuideRevisionListItemV1",
    "SvgGuideRevisionPageV1",
    "SvgReviewReceiptV1",
    "SvgGuideReviewRequestV1",
    "SvgGuideStageV3",
    "SvgPathV1",
    "SvgModelProvenanceV1",
    "SvgReferenceSourceProvenanceV1",
    "TeacherSvgIllustrationDraftRequestV1",
    "TeacherSvgIllustrationDraftResponseV1",
    "SvgSourceReviewRequestV1",
]
