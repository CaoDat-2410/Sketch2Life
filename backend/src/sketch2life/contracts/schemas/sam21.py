"""Wire contracts for the optional SAM 2.1 Lightning worker."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


class Sam21PointV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)


class Sam21SegmentationResponseV1(BaseModel):
    """A bounded response; the mask is optional so degradation remains explicit."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    contract_name: Literal["Sam21SegmentationResponseV1"] = Field(alias="contractName")
    contract_version: Literal["1.0"] = Field(alias="contractVersion")
    status: Literal["SUCCEEDED", "FAILED"]
    adapter_id: str = Field(alias="adapterId", min_length=1, max_length=120)
    adapter_version: str = Field(alias="adapterVersion", min_length=1, max_length=80)
    source_sha256: str = Field(alias="sourceSha256", pattern=r"^[a-f0-9]{64}$")
    source_region: SourceRegionV1 | None = Field(default=None, alias="sourceRegion")
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    mask_base64: str | None = Field(default=None, alias="maskBase64", max_length=6_666_668)
    mask_content_type: Literal["image/png"] | None = Field(
        default=None, alias="maskContentType"
    )
    failure_code: str | None = Field(default=None, alias="failureCode", max_length=80)
    retryable: bool = False

    @model_validator(mode="after")
    def validate_status_payload(self) -> Sam21SegmentationResponseV1:
        if self.status == "SUCCEEDED":
            if self.source_region is None or self.confidence is None:
                raise ValueError("successful segmentation requires a source region and confidence")
            if self.mask_base64 is not None and self.mask_content_type != "image/png":
                raise ValueError("mask content type is required when a mask is returned")
        elif self.failure_code is None:
            raise ValueError("failed segmentation requires a failure code")
        return self


__all__ = ["Sam21PointV1", "Sam21SegmentationResponseV1"]
