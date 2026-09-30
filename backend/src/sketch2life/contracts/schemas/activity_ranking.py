"""Bounded model-ranking contract over a server-built, eligible activity set."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivityRankingCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    title_vi: str = Field(min_length=1, max_length=160)
    summary_vi: str = Field(min_length=1, max_length=500)
    match_reason_vi: str = Field(min_length=1, max_length=300)
    concept_ids: tuple[str, ...] = Field(max_length=16)
    objective_ids: tuple[str, ...] = Field(max_length=8)


class ActivityRankingRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ActivityRankingRequestV1"] = "ActivityRankingRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    topic_label_vi: str = Field(min_length=1, max_length=240)
    age_months: int = Field(ge=0, le=155)
    confirmed_interest_ids: tuple[str, ...] = Field(default=(), max_length=10)
    confirmed_avoid_ids: tuple[str, ...] = Field(default=(), max_length=10)
    candidates: tuple[ActivityRankingCandidateV1, ...] = Field(max_length=100)

    @model_validator(mode="after")
    def validate_candidates(self) -> ActivityRankingRequestV1:
        ids = tuple(item.activity_id for item in self.candidates)
        if len(ids) != len(set(ids)):
            raise ValueError("ranking candidates must be unique")
        if set(self.confirmed_interest_ids) & set(self.confirmed_avoid_ids):
            raise ValueError("a concept cannot be both an interest and an avoid tag")
        return self


class ActivityRankingResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ActivityRankingResultV1"] = "ActivityRankingResultV1"
    contract_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    ranked_activity_ids: tuple[str, ...] = Field(max_length=3)

    @model_validator(mode="after")
    def validate_ranked_ids(self) -> ActivityRankingResultV1:
        if len(self.ranked_activity_ids) != len(set(self.ranked_activity_ids)):
            raise ValueError("ranked activity IDs must be unique")
        if any(not item.startswith("ACT-") for item in self.ranked_activity_ids):
            raise ValueError("ranked IDs must refer to catalog activities")
        return self


__all__ = [
    "ActivityRankingCandidateV1",
    "ActivityRankingRequestV1",
    "ActivityRankingResultV1",
]
