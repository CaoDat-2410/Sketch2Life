"""Versioned HTTP DTOs for the generic upload-session routes (SRS l.1654-1658; goal v3 T-2a).

The names carry a ``Generic`` marker because ``UploadSessionV1`` and ``UploadPartReceiptV1``
already describe the Lesson Library session routes. No model carries a bucket, an object key, a
URL or a credential (SRS l.1692, l.2022): the client sees opaque ids, progress and an asset ref.
Actor, role, owner and organization are never accepted from the client (SRS l.1637); every model
forbids unknown fields.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

OpaqueRef = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
UploadPurpose = Literal["RUN_ARTWORK", "RUN_AUDIO", "OCCURRENCE_DOCUMENT", "PRESENTATION_IMAGE"]
UploadState = Literal["OPEN", "COMPLETED", "ABORTED", "EXPIRED", "FAILED"]
# Sanity bound only: the per-purpose cap (413) is enforced by the service, not by validation.
MAX_DECLARED_BYTES = 10_000_000_000


class StrictUploadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateGenericUploadRequestV1(StrictUploadModel):
    purpose: UploadPurpose
    target_ref: OpaqueRef
    media_type: Annotated[str, Field(min_length=1, max_length=128)]
    expected_size_bytes: int = Field(ge=1, le=MAX_DECLARED_BYTES)
    expected_sha256: Sha256Hex
    file_name: Annotated[str, Field(min_length=1, max_length=255)] | None = None


class CompleteGenericUploadRequestV1(StrictUploadModel):
    expected_size_bytes: int = Field(ge=1, le=MAX_DECLARED_BYTES)
    expected_sha256: Sha256Hex


class GenericUploadAcceptedPartV1(StrictUploadModel):
    part_no: int = Field(ge=1)
    byte_length: int = Field(ge=1)
    sha256: Sha256Hex


class GenericUploadSessionV1(StrictUploadModel):
    contract: Literal["GenericUploadSessionV1"] = "GenericUploadSessionV1"
    upload_id: OpaqueRef
    purpose: UploadPurpose
    target_ref: OpaqueRef
    state: UploadState
    part_size_bytes: int = Field(ge=1)
    expected_parts: int = Field(ge=1)
    accepted_parts: list[GenericUploadAcceptedPartV1]
    byte_count: int = Field(ge=0)
    expires_at: AwareDatetime
    revision: int = Field(ge=1)
    asset_ref: str | None = None
    asset_state: Literal["READY"] | None = None
    error_code: str | None = None


class GenericUploadCompletionV1(GenericUploadSessionV1):
    contract: Literal["GenericUploadCompletionV1"] = "GenericUploadCompletionV1"  # type: ignore[assignment]
    scanner_name: str
    scanner_version: str


class GenericUploadPartReceiptV1(StrictUploadModel):
    contract: Literal["GenericUploadPartReceiptV1"] = "GenericUploadPartReceiptV1"
    upload_id: OpaqueRef
    part_no: int = Field(ge=1)
    byte_length: int = Field(ge=1)
    sha256: Sha256Hex
    accepted: bool
    accepted_part_count: int = Field(ge=1)
    byte_count: int = Field(ge=1)
    revision: int = Field(ge=1)


__all__ = [
    "CompleteGenericUploadRequestV1",
    "CreateGenericUploadRequestV1",
    "GenericUploadAcceptedPartV1",
    "GenericUploadCompletionV1",
    "GenericUploadPartReceiptV1",
    "GenericUploadSessionV1",
    "OpaqueRef",
    "Sha256Hex",
    "UploadPurpose",
    "UploadState",
]
