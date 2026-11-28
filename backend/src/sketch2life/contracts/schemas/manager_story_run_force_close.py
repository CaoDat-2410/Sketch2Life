"""Versioned metadata contracts for Manager StoryRun force-close."""

from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ManagerForceCloseStoryRunRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_revision: int = Field(
        ge=1,
        le=9_223_372_036_854_775_807,
        strict=True,
    )
    reason: str = Field(strict=True, min_length=1, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str:
        if not isinstance(value, str) or any(
            unicodedata.category(character) == "Cc" for character in value
        ):
            raise ValueError("reason must be text without control characters")
        normalized = value.strip()
        if not 1 <= len(normalized) <= 500:
            raise ValueError("reason must contain 1 to 500 characters after trimming")
        return normalized


class ManagerActiveStoryRunConflictV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: Literal["ManagerActiveStoryRunConflictV1"] = "ManagerActiveStoryRunConflictV1"
    run_id: str = Field(min_length=36, max_length=36)
    run_state: str = Field(min_length=1, max_length=64)
    revision: int = Field(ge=1)


class ManagerForceClosedStoryRunV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: Literal["ManagerForceClosedStoryRunV1"] = "ManagerForceClosedStoryRunV1"
    run_id: str = Field(min_length=36, max_length=36)
    run_state: Literal["ABANDONED"] = "ABANDONED"
    revision: int = Field(ge=1)


__all__ = [
    "ManagerActiveStoryRunConflictV1",
    "ManagerForceCloseStoryRunRequestV1",
    "ManagerForceClosedStoryRunV1",
]
