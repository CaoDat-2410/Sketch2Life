"""BE2-02 C2 typed Vision context client contracts (0.1-candidate, not adopted).

``VisionTypedContextV1`` is the minimized provider context. ``LightningVisionContextRequestV1``
wraps the unchanged V2 image request/source image with that context and both digests for the
candidate path ``/v1/vision/context``; ``LightningVisionContextResultV1`` must echo the
contract, context revision, digests, correlation and source image around an unchanged V2
result. No server, prompt or deployed endpoint implements these yet; the Lightning V2
``/v2/vision`` contract (extra fields forbidden) is untouched and never carries this context.

Absent/null semantics: every key is required; ``teacher_topic`` is ``null`` only when the
trusted topic owner reports no topic (never an empty string). Child text, Teacher feedback,
confirmed meaning, action summaries, identities, exact ages and consent records are not
fields, so a document containing them is rejected rather than silently dropped.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.ai_jobs import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.analysis_results import ShortTextV1
from sketch2life.contracts.schemas.vision import VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
)
from sketch2life.domain.vision_context import CONTEXT_AUDIENCE_MAX

CONTEXT_REQUEST_CONTRACT = "LightningVisionContextRequestV1"
CONTEXT_RESULT_CONTRACT = "LightningVisionContextResultV1"
CONTEXT_CLIENT_VERSION = "0.1-candidate"
CONTEXT_ENDPOINT_PATH = "/v1/vision/context"

AgeBandLabel = Annotated[str, Field(pattern=r"^[a-z0-9-]{1,40}$")]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class VisionTypedContextV1(_Strict):
    """Minimized provider context: anonymous per-member bands (sorted, duplicates kept),
    bounded Teacher topic, trusted request enums and the source image hash it binds to."""

    contract_name: Literal["VisionTypedContextV1"]
    contract_version: Literal["0.1-candidate"]
    context_revision: int = Field(ge=0)
    teacher_topic: ShortTextV1 | None
    audience_age_bands: tuple[AgeBandLabel, ...] = Field(
        min_length=1, max_length=CONTEXT_AUDIENCE_MAX
    )
    age_band_policy_ref: OpaqueId
    age_band_policy_version: OpaqueId
    request_reason: Literal["describe_drawing", "support_meaning_check"]
    target_kind: Literal["whole_canvas", "contributor_strokes"]
    requested_level: Literal["brief", "standard"]
    source_image_sha256: Sha256Hex

    @model_validator(mode="after")
    def _canonical_order(self) -> VisionTypedContextV1:
        if list(self.audience_age_bands) != sorted(self.audience_age_bands):
            raise ValueError("audience_age_bands must be sorted (canonical order)")
        return self


class ContextSourceImageV1(_Strict):
    artifact_ref: OpaqueId
    sha256: Sha256Hex
    content_type: Literal["image/png", "image/jpeg"]
    content_base64: str = Field(min_length=1, max_length=6_666_668)


class LightningVisionContextRequestV1(_Strict):
    """Client request body; ``request`` is the unchanged V2 request (no narration hint)."""

    contract_name: Literal["LightningVisionContextRequestV1"]
    contract_version: Literal["0.1-candidate"]
    request: VisionUnderstandingRequestV2
    source_image: ContextSourceImageV1
    typed_context: VisionTypedContextV1
    payload_digest: Sha256Hex
    context_digest: Sha256Hex

    @model_validator(mode="after")
    def _bound(self) -> LightningVisionContextRequestV1:
        if self.payload_digest == self.context_digest:
            raise ValueError("payload and context digests are distinct bindings")
        if (
            self.source_image.artifact_ref != self.request.source_image_ref.artifact_ref
            or self.source_image.sha256 != self.request.source_image_ref.sha256
            or self.typed_context.source_image_sha256 != self.request.source_image_ref.sha256
        ):
            raise ValueError("context and image must bind the same source image")
        if self.request.processing_image_ref is not None:
            raise ValueError("derived processing images are not supported")
        return self


class LightningVisionContextResultV1(_Strict):
    """Provider response wrapper; every echo must equal the request, and the nested result is
    the unchanged V2 success/failure contract. An echo binds the request; it does not prove
    the model used the context."""

    contract_name: Literal["LightningVisionContextResultV1"]
    contract_version: Literal["0.1-candidate"]
    correlation_id: OpaqueId
    source_image_ref: VisionImageReferenceV1
    context_contract: Literal["VisionTypedContextV1"]
    context_contract_version: Literal["0.1-candidate"]
    context_revision: int = Field(ge=0)
    payload_digest: Sha256Hex
    context_digest: Sha256Hex
    result: VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2

    @model_validator(mode="after")
    def _nested_identity(self) -> LightningVisionContextResultV1:
        if (
            self.result.correlation_id != self.correlation_id
            or self.result.source_image_ref != self.source_image_ref
        ):
            raise ValueError("nested V2 result must carry the same correlation and image")
        return self


__all__ = [
    "CONTEXT_CLIENT_VERSION",
    "CONTEXT_ENDPOINT_PATH",
    "CONTEXT_REQUEST_CONTRACT",
    "CONTEXT_RESULT_CONTRACT",
    "ContextSourceImageV1",
    "LightningVisionContextRequestV1",
    "LightningVisionContextResultV1",
    "VisionTypedContextV1",
]
