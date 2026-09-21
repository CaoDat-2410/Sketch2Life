"""Versioned adult Gate-A confirmation contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GateAConfirmationV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["GateAConfirmationV1"] = "GateAConfirmationV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    actor_ref: str = Field(min_length=1, max_length=160)
    meaning_version: int = Field(ge=1)
    confirmed_claim_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    correction: str | None = Field(default=None, max_length=500)


__all__ = ["GateAConfirmationV1"]
