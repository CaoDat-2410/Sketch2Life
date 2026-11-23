"""Versioned contracts of a Teacher StoryRun (FEAT-066 goal v3, T-4b2; SRS l.1445-1449, l.1663).

``POST /v1/story-runs`` takes one of two bodies: the Parent body (``ParentStoryRunCreateRequestV1``)
and this Teacher body, which names the confirmed child selection, the occurrence, the approved plan
revision and one activity of that plan. The Teacher view of a run is the Parent view with a string
profile ref (a Managed Profile id is not a UUID), the occurrence, plan and activity pins, and
Teacher-typed snapshots (the Parent models are strict about their schema-version literals).
Neither a name nor media nor a draw index appears in any of them (BR-34).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.parent_story_runs import (
    ParentDrawingCandidateV1,
    ParentLessonPinSnapshotV1,
    ParentRunContextSnapshotV1,
    ParentStoryDisplayV1,
    ParentStoryRunStateV1,
)
from sketch2life.contracts.schemas.story_run_video import (
    ParentStoryQuotaSummaryV1,
    ParentStoryRunVideoV1,
    ParentStoryTimelineEventV1,
)
from sketch2life.domain.story_teacher import (
    CONTEXT_ACTIVITY_TITLE_CHARS,
    CONTEXT_DIRECTION_CHARS,
    CONTEXT_OBJECTIVE_CHARS,
    CONTEXT_OBJECTIVES_MAX,
    TEACHER_CONTEXT_SCHEMA,
    TEACHER_PIN_SCHEMA,
)

HEX64 = r"^[0-9a-f]{64}$"
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class TeacherProfileRefV1(BaseModel):
    """The one child of the run, as the confirmed selection named it (no Teacher branch picks)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    kind: Literal["MANAGED_PROFILE"]
    id: str = Field(min_length=1, max_length=128)


class TeacherPlanRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    revision_no: int = Field(ge=1, le=1_000_000)
    plan_hash: str = Field(pattern=HEX64)


class TeacherStoryRunCreateRequestV1(BaseModel):
    """Body of ``POST /v1/story-runs`` for a Teacher (SRS l.1663: one profile ref, the occurrence,
    the approved plan revision and hash, the confirmed child selection, one approved activity)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    profile_ref: TeacherProfileRefV1
    occurrence_id: str = Field(min_length=1, max_length=36)
    plan: TeacherPlanRefV1
    activity_id: str = Field(min_length=1, max_length=36)
    selection_id: str = Field(pattern=UUID_PATTERN)
    selection_sha256: str = Field(pattern=HEX64)


class TeacherRunContextSnapshotV1(BaseModel):
    """The minimal context of a Teacher run (SRS l.549, l.354): no name, no media, no seed."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.teacher-context.v1"]
    selection_id: str = Field(pattern=UUID_PATTERN)
    age_months: int = Field(ge=36, le=120)
    age_revision: int = Field(ge=1)
    objectives: list[Annotated[str, Field(max_length=CONTEXT_OBJECTIVE_CHARS)]] = Field(
        max_length=CONTEXT_OBJECTIVES_MAX
    )
    teacher_direction: str = Field(max_length=CONTEXT_DIRECTION_CHARS)
    activity_title: str | None = Field(default=None, max_length=CONTEXT_ACTIVITY_TITLE_CHARS)
    activity_snapshot_hash: str | None = Field(default=None, pattern=HEX64)


class TeacherPinActivityV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plan_activity_id: str = Field(min_length=1, max_length=36)
    kind: Literal["LESSON", "CUSTOM", "CATALOG"]
    catalog_activity_ref: str | None = Field(default=None, max_length=256)
    activity_version: int | None = Field(default=None, ge=1)
    snapshot_hash: str | None = Field(default=None, pattern=HEX64)


class TeacherPinLessonV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    lesson_id: str = Field(min_length=1, max_length=36)
    version_id: str = Field(min_length=1, max_length=36)
    version_no: int = Field(ge=1)
    version_hash: str = Field(pattern=HEX64)


class TeacherRunPinSnapshotV1(BaseModel):
    """The pins of the run: occurrence, approved plan revision and hash, activity, lesson lineage.
    Copied forward into every input revision, so T-5a reads the pin from the current one."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.teacher-run-pin.v1"]
    occurrence_id: str = Field(min_length=1, max_length=36)
    plan_revision_id: str = Field(min_length=1, max_length=36)
    plan_revision_no: int = Field(ge=1)
    plan_hash: str = Field(pattern=HEX64)
    activity: TeacherPinActivityV1
    lesson: TeacherPinLessonV1 | None = None


class TeacherRunPlanV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_no: int = Field(ge=1)
    plan_hash: str


class TeacherRunActivityV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_activity_id: str
    kind: str
    snapshot_hash: str | None = None


class TeacherRunProfileRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["MANAGED_PROFILE"] = "MANAGED_PROFILE"
    id: str


class TeacherStoryRunResponseV1(BaseModel):
    """``StoryRunDetailV1`` for a Teacher (SRS l.1811, l.1635 additive): the Parent fields, a string
    profile ref in place of the Parent profile UUID, and the occurrence, plan and activity pins.
    The snapshot fields accept the Teacher schemas and, for a fixture run written before DDL-B2
    (no occurrence), the Parent ones."""

    run_id: UUID
    run_revision: int = Field(ge=1)
    run_state: ParentStoryRunStateV1
    profile_ref: TeacherRunProfileRefV1
    profile_revision_ref: str
    occurrence_id: str | None = None
    plan: TeacherRunPlanV1 | None = None
    activity: TeacherRunActivityV1 | None = None
    context_revision: int
    context_confirmed: bool
    context_snapshot: TeacherRunContextSnapshotV1 | ParentRunContextSnapshotV1
    context_snapshot_sha256: str
    lesson_pin_snapshot: TeacherRunPinSnapshotV1 | ParentLessonPinSnapshotV1 | None = None
    current_input_revision: int | None
    understanding_revision: int | None
    subject_label: str | None
    candidate: ParentDrawingCandidateV1 | None
    story_revision_id: UUID | None
    story_revision_no: int | None
    story_status: (
        Literal[
            "GENERATING", "DRAFT", "CONFIRMED", "SUPERSEDED", "FAILED", "AWAITING_RECONCILIATION"
        ]
        | None
    )
    story_sha256: str | None
    story: ParentStoryDisplayV1 | None
    job_state: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "AWAITING_RECONCILIATION"] | None
    retryable: bool
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    video: ParentStoryRunVideoV1 | None = None
    quota: ParentStoryQuotaSummaryV1 = Field(default_factory=ParentStoryQuotaSummaryV1)
    timeline: list[ParentStoryTimelineEventV1] = Field(default_factory=list)
    story_confirmation_required: bool = False


class TeacherStoryRunEnvelopeV1(BaseModel):
    request_id: UUID
    story_run: TeacherStoryRunResponseV1


class TeacherActiveStoryRunEnvelopeV1(BaseModel):
    request_id: UUID
    story_run: TeacherStoryRunResponseV1 | None


__all__ = [
    "TEACHER_CONTEXT_SCHEMA",
    "TEACHER_PIN_SCHEMA",
    "TeacherActiveStoryRunEnvelopeV1",
    "TeacherPinActivityV1",
    "TeacherPinLessonV1",
    "TeacherPlanRefV1",
    "TeacherProfileRefV1",
    "TeacherRunActivityV1",
    "TeacherRunContextSnapshotV1",
    "TeacherRunPinSnapshotV1",
    "TeacherRunPlanV1",
    "TeacherRunProfileRefV1",
    "TeacherStoryRunCreateRequestV1",
    "TeacherStoryRunEnvelopeV1",
    "TeacherStoryRunResponseV1",
]
