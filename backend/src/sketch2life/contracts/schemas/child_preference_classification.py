"""Bounded, adult-reviewed preference classification for one volatile app session."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PreferenceConceptId = Literal[
    "ANIMAL_BUTTERFLY",
    "ANIMAL_GENERIC",
    "ANIMAL_MOVEMENT",
    "PLANT_FLOWER",
    "PLANT_STRUCTURE",
    "SUN_LIGHT",
    "NATURE_OBSERVATION",
    "SCIENCE_OBSERVATION",
    "COUNTING_NUMBER",
    "LANGUAGE_PRINT",
]


class ChildPreferenceClassificationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ChildPreferenceClassificationRequestV1"] = (
        "ChildPreferenceClassificationRequestV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    interest_text: str = Field(default="", max_length=240)
    avoid_text: str = Field(default="", max_length=240)

    @field_validator("interest_text", "avoid_text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_preference_text(self) -> ChildPreferenceClassificationRequestV1:
        if not self.interest_text and not self.avoid_text:
            raise ValueError("at least one preference phrase is required")
        return self


class ChildPreferenceTagV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: PreferenceConceptId
    label_vi: str = Field(min_length=1, max_length=80)
    confidence: float = Field(ge=0.0, le=1.0)


class ChildPreferenceClassificationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ChildPreferenceClassificationV1"] = (
        "ChildPreferenceClassificationV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    interest_tags: tuple[ChildPreferenceTagV1, ...] = Field(default=(), max_length=10)
    avoid_tags: tuple[ChildPreferenceTagV1, ...] = Field(default=(), max_length=10)
    interest_unmapped: bool = False
    avoid_unmapped: bool = False

    @model_validator(mode="after")
    def reject_duplicate_and_conflicting_tags(self) -> ChildPreferenceClassificationV1:
        interest_ids = tuple(tag.concept_id for tag in self.interest_tags)
        avoid_ids = tuple(tag.concept_id for tag in self.avoid_tags)
        if len(interest_ids) != len(set(interest_ids)):
            raise ValueError("interest tags must be unique")
        if len(avoid_ids) != len(set(avoid_ids)):
            raise ValueError("avoid tags must be unique")
        if set(interest_ids) & set(avoid_ids):
            raise ValueError("a concept cannot be both an interest and an avoid tag")
        return self


class ChildPreferenceClassificationFailureV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ChildPreferenceClassificationFailureV1"] = (
        "ChildPreferenceClassificationFailureV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    status: Literal["FAILED"] = "FAILED"
    failure: dict[str, str | bool]


__all__ = [
    "ChildPreferenceClassificationRequestV1",
    "ChildPreferenceClassificationFailureV1",
    "ChildPreferenceClassificationV1",
    "ChildPreferenceTagV1",
    "PreferenceConceptId",
]
