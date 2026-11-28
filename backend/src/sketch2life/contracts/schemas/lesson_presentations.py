"""Strict versioned HTTP contracts for Teacher lesson presentations."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.svg_engine import SvgDocumentV1

Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SlideRef = Annotated[str, Field(min_length=1, max_length=36, pattern=r"^[A-Za-z0-9-]+$")]
DraftRef = Annotated[str, Field(min_length=1, max_length=36, pattern=r"^[A-Za-z0-9-]+$")]
CatalogRef = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
UploadRef = Annotated[str, Field(min_length=5, max_length=64, pattern=r"^upl_[A-Za-z0-9._:-]+$")]


class StrictPresentationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreatePresentationRequestV1(StrictPresentationModel):
    seed: Literal["PLAN_ACTIVITIES", "BLANK"] = "PLAN_ACTIVITIES"


class UpdateSlideOperationV1(StrictPresentationModel):
    op: Literal["UPDATE_SLIDE"]
    slide_id: SlideRef
    title: Annotated[str, Field(max_length=200)] | None = None
    body_text: Annotated[str, Field(max_length=2000)] | None = None

    @model_validator(mode="after")
    def needs_a_field(self) -> UpdateSlideOperationV1:
        if self.title is None and self.body_text is None:
            raise ValueError("at least one slide field is required")
        return self


class AddSlideOperationV1(StrictPresentationModel):
    op: Literal["ADD_SLIDE"]
    after_slide_id: SlideRef | None
    title: Annotated[str, Field(max_length=200)]
    body_text: Annotated[str, Field(max_length=2000)]


class DeleteSlideOperationV1(StrictPresentationModel):
    op: Literal["DELETE_SLIDE"]
    slide_id: SlideRef


class MoveSlideOperationV1(StrictPresentationModel):
    op: Literal["MOVE_SLIDE"]
    slide_id: SlideRef
    to_position: int = Field(ge=1, le=100)


class ImageSlideMediaInputV1(StrictPresentationModel):
    kind: Literal["IMAGE"]
    asset_ref: UploadRef
    alt_text: Annotated[str, Field(max_length=300)] = ""


class CatalogSvgSlideMediaInputV1(StrictPresentationModel):
    kind: Literal["SVG_CATALOG"]
    catalog_entry_id: CatalogRef
    alt_text: Annotated[str, Field(max_length=300)] = ""


class AiSvgSlideMediaInputV1(StrictPresentationModel):
    kind: Literal["SVG_AI"]
    svg_draft_id: DraftRef
    alt_text: Annotated[str, Field(max_length=300)] = ""


class VideoSlideMediaInputV1(StrictPresentationModel):
    kind: Literal["VIDEO_EMBED"]
    url: Annotated[str, Field(min_length=1, max_length=2048)]


SlideMediaInputV1 = Annotated[
    ImageSlideMediaInputV1
    | CatalogSvgSlideMediaInputV1
    | AiSvgSlideMediaInputV1
    | VideoSlideMediaInputV1,
    Field(discriminator="kind"),
]


class SetMediaOperationV1(StrictPresentationModel):
    op: Literal["SET_MEDIA"]
    slide_id: SlideRef
    placement: Literal["FULL", "LEFT", "RIGHT"]
    media: SlideMediaInputV1


class ClearMediaOperationV1(StrictPresentationModel):
    op: Literal["CLEAR_MEDIA"]
    slide_id: SlideRef


PresentationOperationV1 = Annotated[
    UpdateSlideOperationV1
    | AddSlideOperationV1
    | DeleteSlideOperationV1
    | MoveSlideOperationV1
    | SetMediaOperationV1
    | ClearMediaOperationV1,
    Field(discriminator="op"),
]


class CreatePresentationRevisionRequestV1(StrictPresentationModel):
    repin_to_current_plan: bool = False
    operations: list[PresentationOperationV1] = Field(min_length=1, max_length=50)


class CreatePresentationSvgDraftRequestV1(StrictPresentationModel):
    plan_activity_id: Annotated[str, Field(min_length=1, max_length=36)]
    subject_text: Annotated[str, Field(min_length=1, max_length=80)]


class DecidePresentationSvgDraftRequestV1(StrictPresentationModel):
    decision: Literal["ACCEPT", "DISCARD"]


class ImageSlideMediaV1(StrictPresentationModel):
    kind: Literal["IMAGE"]
    asset_ref: UploadRef
    alt_text: str
    media_type: Literal["image/jpeg", "image/png", "image/webp"]
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    placement: Literal["FULL", "LEFT", "RIGHT"]


class CatalogSvgSlideMediaV1(StrictPresentationModel):
    kind: Literal["SVG_CATALOG"]
    catalog_entry_id: CatalogRef
    alt_text: str
    canonical_sha256: Sha256Hex
    placement: Literal["FULL", "LEFT", "RIGHT"]


class AiSvgSlideMediaV1(StrictPresentationModel):
    kind: Literal["SVG_AI"]
    svg_draft_id: DraftRef
    alt_text: str
    canonical_sha256: Sha256Hex
    placement: Literal["FULL", "LEFT", "RIGHT"]


class VideoSlideMediaV1(StrictPresentationModel):
    kind: Literal["VIDEO_EMBED"]
    provider: Literal["YOUTUBE", "VIMEO"]
    video_id: str
    embed_url: str
    placement: Literal["FULL", "LEFT", "RIGHT"]


SlideMediaV1 = Annotated[
    ImageSlideMediaV1 | CatalogSvgSlideMediaV1 | AiSvgSlideMediaV1 | VideoSlideMediaV1,
    Field(discriminator="kind"),
]


class PresentationSlideV1(StrictPresentationModel):
    slide_id: SlideRef
    position: int = Field(ge=1, le=100)
    title: Annotated[str, Field(max_length=200)]
    body_text: Annotated[str, Field(max_length=2000)]
    media: SlideMediaV1 | None
    media_state: Literal["CURRENT", "STALE"] | None


class LessonPresentationRevisionV1(StrictPresentationModel):
    contract: Literal["LessonPresentationRevisionV1"] = "LessonPresentationRevisionV1"
    revision_no: int = Field(ge=1)
    base_revision_no: int | None = Field(default=None, ge=1)
    state: Literal["DRAFT", "READY", "SUPERSEDED"]
    aspect_ratio: Literal["16:9"] = "16:9"
    source_state: Literal["CURRENT", "STALE"]
    stale_reasons: list[Literal["PLAN_REVISION_CHANGED", "MEDIA_SOURCE_CHANGED"]]
    plan_revision_no: int = Field(ge=1)
    plan_content_hash: Sha256Hex
    content_hash: Sha256Hex
    slides: list[PresentationSlideV1] = Field(min_length=1, max_length=100)
    created_at: AwareDatetime
    readied_at: AwareDatetime | None


class LessonPresentationV1(StrictPresentationModel):
    contract: Literal["LessonPresentationV1"] = "LessonPresentationV1"
    presentation_id: Annotated[str, Field(min_length=1, max_length=36)]
    occurrence_id: Annotated[str, Field(min_length=1, max_length=36)]
    revision: int = Field(ge=1)
    head_revision_no: int = Field(ge=1)
    ready_revision_no: int | None = Field(default=None, ge=1)
    source_state: Literal["CURRENT", "STALE"]
    stale_reasons: list[Literal["PLAN_REVISION_CHANGED", "MEDIA_SOURCE_CHANGED"]]
    presentable: bool
    head: LessonPresentationRevisionV1


class PresentationSvgGeneratorV1(StrictPresentationModel):
    name: Annotated[str, Field(min_length=1, max_length=64)]
    version: Annotated[str, Field(min_length=1, max_length=128)]


class PresentationSvgDraftV1(StrictPresentationModel):
    contract: Literal["PresentationSvgDraftV1"] = "PresentationSvgDraftV1"
    svg_draft_id: Annotated[str, Field(min_length=1, max_length=36)]
    state: Literal["PENDING_REVIEW", "ACCEPTED", "DISCARDED"]
    revision: int = Field(ge=1)
    document: SvgDocumentV1
    preview_svg: str
    canonical_sha256: Sha256Hex
    generator: PresentationSvgGeneratorV1
    license_id: Annotated[str, Field(min_length=1, max_length=120)]
    created_at: AwareDatetime
    decided_at: AwareDatetime | None


__all__ = [
    "AddSlideOperationV1",
    "AiSvgSlideMediaInputV1",
    "AiSvgSlideMediaV1",
    "CatalogSvgSlideMediaInputV1",
    "CatalogSvgSlideMediaV1",
    "ClearMediaOperationV1",
    "CreatePresentationRequestV1",
    "CreatePresentationRevisionRequestV1",
    "CreatePresentationSvgDraftRequestV1",
    "DecidePresentationSvgDraftRequestV1",
    "DeleteSlideOperationV1",
    "ImageSlideMediaInputV1",
    "ImageSlideMediaV1",
    "LessonPresentationRevisionV1",
    "LessonPresentationV1",
    "MoveSlideOperationV1",
    "PresentationOperationV1",
    "PresentationSlideV1",
    "PresentationSvgDraftV1",
    "SetMediaOperationV1",
    "SlideMediaInputV1",
    "SlideMediaV1",
    "UpdateSlideOperationV1",
    "VideoSlideMediaInputV1",
    "VideoSlideMediaV1",
]
