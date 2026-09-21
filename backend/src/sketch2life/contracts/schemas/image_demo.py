"""Transport projection for the FEAT-018 synthetic image-only demo lane."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.vision import VisionImageReferenceV1


class ImageAdmissionReceiptV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["ImageAdmissionReceiptV1"] = "ImageAdmissionReceiptV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    decision: Literal["ADMITTED", "RECAPTURE"]
    outcome: Literal["ADMITTED", "REJECTED", "UNSUPPORTED", "INVALID_SOURCE", "PROCESSING_FAILURE"]
    reason: str | None = Field(default=None, max_length=80)
    source_image_ref: VisionImageReferenceV1 | None = None
    content_type: Literal["image/jpeg", "image/png"] | None = None
    byte_length: int = Field(ge=0, le=5_000_001)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    guidance: str = Field(min_length=1, max_length=120)
    narration_status: Literal["NOT_SUPPLIED"] = "NOT_SUPPLIED"


__all__ = ["ImageAdmissionReceiptV1"]
