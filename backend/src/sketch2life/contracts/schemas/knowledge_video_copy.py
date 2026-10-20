"""Internal original video-copy journal metadata; not source or deletion proof."""

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyRegistryRegistration
from sketch2life.contracts.schemas.knowledge_video import StrictVideoModel


class VideoCopyJournalEntry(StrictVideoModel):
    registration: CopyRegistryRegistration
    video_id: OpaqueId
    video_version: int = Field(ge=1)
    job_id: OpaqueId
    attempt_id: OpaqueId
    pin_digest: Sha256Hex
    media_operation_key: Sha256Hex
    role: Literal["input", "script", "output", "cache", "job"]
    source_reference: CopyReceiptReference

    @model_validator(mode="after")
    def exact_role(self) -> "VideoCopyJournalEntry":
        # Script is an input copy in the existing BE2-14 union, not a new kind.
        if self.registration.kind != ("input" if self.role == "script" else self.role):
            raise ValueError("VIDEO_COPY_KIND_MISMATCH")
        return self
