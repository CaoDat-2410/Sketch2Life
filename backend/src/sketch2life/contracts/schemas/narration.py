"""Versioned narration input contracts for the FEAT-018 supervised demo."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class NarrationNoneV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["NONE"] = "NONE"


class NarrationTextV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["TEXT"] = "TEXT"
    text: str = Field(min_length=1, max_length=2_000)
    language: str = Field(default="vi", min_length=2, max_length=20)
    provenance: Literal["TEXT_TYPED"] = "TEXT_TYPED"


NarrationAudioContentType = Literal[
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
]


class NarrationAudioV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["AUDIO"] = "AUDIO"
    artifact_ref: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: NarrationAudioContentType
    byte_length: int = Field(gt=0, le=20_000_000)
    provenance: Literal["RECORDED_AUDIO"] = "RECORDED_AUDIO"


NarrationInputV1 = Annotated[
    NarrationNoneV1 | NarrationTextV1 | NarrationAudioV1,
    Field(discriminator="kind"),
]


class NarrationReceiptV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["NarrationReceiptV1"] = "NarrationReceiptV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    kind: Literal["AUDIO"] = "AUDIO"
    artifact_ref: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: NarrationAudioContentType
    byte_length: int = Field(gt=0, le=20_000_000)
    guidance: str = Field(min_length=1, max_length=160)


__all__ = [
    "NarrationAudioV1",
    "NarrationAudioContentType",
    "NarrationInputV1",
    "NarrationNoneV1",
    "NarrationReceiptV1",
    "NarrationTextV1",
]
