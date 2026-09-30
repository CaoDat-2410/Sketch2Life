"""Versioned adult Gate-A confirmation contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class GateAConfirmationV2(BaseModel):
    """Gate A that can carry a clearly adult-authored subject without an AI claim ID."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["GateAConfirmationV2"] = "GateAConfirmationV2"
    contract_version: Literal["2.0"] = "2.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    actor_ref: str = Field(min_length=1, max_length=160)
    meaning_version: int = Field(ge=2)
    confirmed_claim_ids: tuple[str, ...] = Field(default=(), max_length=128)
    adult_subject_label: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def require_an_adult_subject_or_ai_claim(self) -> GateAConfirmationV2:
        if self.adult_subject_label is not None and not self.adult_subject_label.strip():
            raise ValueError("adult subject label cannot be blank")
        if not self.confirmed_claim_ids and self.adult_subject_label is None:
            raise ValueError("Gate A needs an AI claim or an adult-entered subject")
        if self.confirmed_claim_ids != tuple(dict.fromkeys(self.confirmed_claim_ids)):
            raise ValueError("a claim can be confirmed only once")
        return self


__all__ = ["GateAConfirmationV1", "GateAConfirmationV2"]
