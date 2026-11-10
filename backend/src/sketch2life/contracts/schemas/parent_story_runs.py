"""Versioned contracts for Parent StoryRun and adult review commands."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParentStoryRunCreateRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    parent_profile_id: UUID
    expected_profile_revision_id: UUID
    consent_policy_version: str = Field(min_length=1, max_length=80)
    topic: str = Field(min_length=1, max_length=120)
    adult_confirmed_idea: str = Field(default="", max_length=500)
    context_confirmed: Literal[True]


class ParentRunContextSnapshotV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.parent-context.v1"]
    profile_revision_ref: str = Field(
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    age_months: int = Field(ge=36, le=120)
    interests_summary: str = Field(max_length=800)
    topic: str = Field(max_length=120)
    adult_confirmed_idea: str = Field(max_length=500)
    consent_policy_version: str = Field(min_length=1, max_length=80)


class ParentDrawingCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_subject: str | None
    visible_features: list[str] = Field(min_length=1, max_length=4)
    confidence: float = Field(ge=0, le=1)
    adult_confirmation_required: Literal[True]
    decision: Literal["REVIEW_REQUIRED", "CONFIRMED_BY_ADULT", "CORRECTED_BY_ADULT"]


class ParentStorySectionsV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    opening: str
    middle: str
    ending: str


class ParentStorySceneDisplayV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    scene_index: int = Field(ge=1, le=15)
    title: str
    action: str
    narration: str
    start_ms: int = Field(ge=0, le=90_000)
    duration_ms: int = Field(ge=1_000, le=20_000)


class ParentStoryDisplayV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.story-revision.v1"]
    language: Literal["vi"]
    title: str
    story: ParentStorySectionsV1
    duration_ms: int = Field(ge=30_000, le=90_000)
    scenes: list[ParentStorySceneDisplayV1] = Field(min_length=5, max_length=15)


class ParentStoryRunResponseV1(BaseModel):
    run_id: UUID
    run_state: Literal[
        "INPUT_PROCESSING", "SUBJECT_REVIEW", "PREPARATION_REVIEW", "SCRIPT_GENERATING",
        "SCRIPT_GENERATION_UNKNOWN", "SCRIPT_REVIEW", "VIDEO_ADMISSION_PENDING",
        "DELETE_PENDING", "FAILED", "COMPLETED",
    ]
    parent_profile_id: UUID
    profile_revision_ref: UUID
    context_revision: int
    context_snapshot: ParentRunContextSnapshotV1
    context_snapshot_sha256: str
    current_input_revision: int | None
    understanding_revision: int | None
    subject_label: str | None
    candidate: ParentDrawingCandidateV1 | None
    story_revision_id: UUID | None
    story_revision_no: int | None
    story_status: Literal[
        "GENERATING", "DRAFT", "CONFIRMED", "SUPERSEDED", "FAILED", "AWAITING_RECONCILIATION"
    ] | None
    story_sha256: str | None
    story: ParentStoryDisplayV1 | None
    job_state: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "AWAITING_RECONCILIATION"] | None
    retryable: bool
    error_code: str | None
    created_at: datetime
    updated_at: datetime


class ParentStoryRunEnvelopeV1(BaseModel):
    request_id: UUID
    story_run: ParentStoryRunResponseV1


class ParentActiveStoryRunEnvelopeV1(BaseModel):
    request_id: UUID
    story_run: ParentStoryRunResponseV1 | None


class ParentSubjectConfirmationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    expected_understanding_revision: int = Field(ge=1)
    confirmed_subject: str = Field(min_length=1, max_length=160)


class ParentSubjectConfirmationResponseV1(BaseModel):
    request_id: UUID
    story_run_id: UUID
    understanding_revision: int
    decision: Literal["CONFIRMED"]


class ParentStoryRevisionRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    expected_understanding_revision: int = Field(ge=1)
    rewrite_instruction: str | None = Field(default=None, min_length=1, max_length=400)


class ParentStoryRevisionConfirmationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1, le=4)
    story_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


__all__ = [
    "ParentDrawingCandidateV1",
    "ParentRunContextSnapshotV1",
    "ParentStoryDisplayV1",
    "ParentStoryRevisionConfirmationRequestV1",
    "ParentStoryRevisionRequestV1",
    "ParentStorySceneDisplayV1",
    "ParentStorySectionsV1",
    "ParentActiveStoryRunEnvelopeV1",
    "ParentStoryRunCreateRequestV1",
    "ParentStoryRunEnvelopeV1",
    "ParentStoryRunResponseV1",
    "ParentSubjectConfirmationRequestV1",
    "ParentSubjectConfirmationResponseV1",
]
