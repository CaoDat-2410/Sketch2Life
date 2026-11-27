"""Versioned contracts for Parent activity suggestion and persisted selection."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.modal_ai import ParentSuggestedActivityV2


class ParentActivitySuggestionsRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_understanding_revision: int = Field(ge=1)
    # A reopened app takes the set it already has instead of asking the model for a second one.
    reuse_latest: bool = False


class ParentActivitySuggestionSetV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract: Literal["ParentActivitySuggestionSetV1"]
    request_id: UUID = Field(strict=False)
    story_run_id: UUID = Field(strict=False)
    suggestion_set_id: UUID = Field(strict=False)
    set_revision: int = Field(ge=1)
    understanding_revision: int = Field(ge=1)
    selection_mode: Literal["CATALOG_SELECTION", "AI_GENERATED_FALLBACK"]
    catalog_candidate_count: int = Field(ge=0, le=500)
    activities_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_required: Literal[True]
    modal_call_id: str | None = Field(default=None, max_length=128)
    activities: list[ParentSuggestedActivityV2] = Field(min_length=1, max_length=24)


class ParentActivitySelectionRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    suggestion_set_id: UUID = Field(strict=False)
    expected_understanding_revision: int = Field(ge=1)
    activity_index: int = Field(ge=0, le=23)


class ParentActivitySelectionReceiptV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract: Literal["ParentActivitySelectionReceiptV1"]
    request_id: UUID = Field(strict=False)
    story_run_id: UUID = Field(strict=False)
    suggestion_set_id: UUID = Field(strict=False)
    activity_selection_id: UUID = Field(strict=False)
    selection_revision: int = Field(ge=1)
    understanding_revision: int = Field(ge=1)
    activity_index: int = Field(ge=0, le=23)
    activity_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    persisted_at: datetime


__all__ = [
    "ParentActivitySelectionReceiptV1",
    "ParentActivitySelectionRequestV1",
    "ParentActivitySuggestionsRequestV1",
    "ParentActivitySuggestionSetV1",
]
