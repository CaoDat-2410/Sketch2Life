"""Versioned contracts for Parent StoryRun and adult review commands."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.lesson_library import LessonActivityInputV1
from sketch2life.contracts.schemas.story_run_video import (
    ParentStoryQuotaSummaryV1,
    ParentStoryRunVideoV1,
    ParentStoryTimelineEventV1,
)


class ParentLessonVersionRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    lesson_id: str = Field(min_length=1, max_length=256)
    version_id: str = Field(min_length=1, max_length=256)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ParentStoryRunCreateRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    # FastAPI validates parsed JSON values in Python mode, where UUIDs arrive as strings.
    parent_profile_id: UUID = Field(strict=False)
    topic: str = Field(default="", max_length=120)
    adult_confirmed_idea: str = Field(default="", max_length=500)
    intended_drawing_subject: str | None = Field(default=None, min_length=2, max_length=160)
    lesson_version: ParentLessonVersionRefV1 | None = None


class ParentStoryRunCancelRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1)


class ParentRunContextSnapshotV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.parent-context.v1"]
    profile_revision_ref: str = Field(
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    age_months: int = Field(ge=36, le=120)
    interests_summary: str = Field(max_length=2000)
    topic: str = Field(max_length=120)
    adult_confirmed_idea: str = Field(max_length=500)
    intended_drawing_subject: str | None = Field(default=None, max_length=160)


class ParentLessonPinSnapshotV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    schema_version: Literal["sketch2life.parent-lesson-pin.v1"]
    lesson_id: str = Field(min_length=1, max_length=256)
    version_id: str = Field(min_length=1, max_length=256)
    version_no: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_age_band_ref: str | None = Field(default=None, min_length=1, max_length=256)
    target_age_band_version: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=160)
    topic: str = Field(min_length=1, max_length=120)
    drawing_subject: str = Field(min_length=1, max_length=160)
    subject_learning_notes: str = Field(min_length=1, max_length=5000)
    script_direction: str | None = Field(default=None, max_length=2000)
    script_following_allowed: bool
    activities: list[LessonActivityInputV1] = Field(min_length=1, max_length=24)


class ParentSubjectRoleV1(BaseModel):
    """FEAT-087: the adult's final role for one object found in the drawing."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    entity_id: Literal["main", "sec-1", "sec-2", "sec-3"]
    label: str = Field(min_length=1, max_length=100)
    role: Literal["main", "secondary", "excluded"]


class ParentDrawingEntityV1(BaseModel):
    """FEAT-087: one object the AI found (no box or other model internals)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    entity_id: Literal["main", "sec-1", "sec-2", "sec-3"]
    label: str = Field(min_length=1, max_length=100)
    suggested_role: Literal["main", "secondary"]
    # FEAT-093 M1: False for scenery (sun, grass, ground) the adult has not named.
    suggested_included: bool = True


class ParentDrawingCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_subject: str | None
    visible_features: list[str] = Field(min_length=1, max_length=4)
    confidence: float = Field(ge=0, le=1)
    adult_confirmation_required: Literal[True]
    decision: Literal["REVIEW_REQUIRED", "CONFIRMED_BY_ADULT", "CORRECTED_BY_ADULT"]
    # FEAT-087: empty/None for drawings analysed before roles existed.
    entities: list[ParentDrawingEntityV1] = Field(default_factory=list, max_length=4)
    # FEAT-093 M1: True when two subjects are too close to call; the adult must pick the main one.
    needs_choice: bool = False
    subject_roles: list[ParentSubjectRoleV1] | None = None


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


class ParentStoryLearningV1(BaseModel):
    """FEAT-094: what the child learns from this story and whether a person had checked those facts."""

    model_config = ConfigDict(extra="forbid", strict=True)

    fact_source: Literal["CARD", "LESSON", "AI_DRAFT"]
    verified: bool
    points: list[str] = Field(min_length=1, max_length=5)


class ParentStoryDisplayV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.story-revision.v1"]
    language: Literal["vi"]
    title: str
    story: ParentStorySectionsV1
    duration_ms: int = Field(ge=30_000, le=90_000)
    scenes: list[ParentStorySceneDisplayV1] = Field(min_length=5, max_length=15)
    learning: ParentStoryLearningV1 | None = None


ParentStoryRunStateV1 = Literal[
    # The 18 StoryRun states of SRS line 394 (D-215 item 4) ...
    "DRAFT", "INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW", "PREPARATION_REVIEW",
    "STORY_GENERATING", "SCRIPT_REVIEW", "VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED",
    "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING", "VIDEO_READY", "SAFETY_BLOCKED",
    "COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED",
    # ... plus the two documented extensions of the frozen M2 contract (D-216 item 4).
    "SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN",
]


# --- T-2e-a (DDL-B3, SRS l.514, l.527, l.532, l.1412, l.1667): the Parent's main activity ---------
class ParentActivityRefV1(BaseModel):
    """The exact lesson activity a Parent chose: version, content hash and index (never a URL)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    lesson_id: str = Field(min_length=1, max_length=36)
    version_id: str = Field(min_length=1, max_length=36)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    activity_index: int = Field(ge=0, le=23)


class ParentActivityV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_ref: ParentActivityRefV1 | None = None
    title: str
    objective: str
    materials_text: str
    preparation_text: str
    instructions_text: str
    observation_notes: str
    safety_notes: str
    activity_kind: Literal["outdoor", "indoor", "mixed"]
    source: Literal[
        "PINNED_LESSON",
        "PUBLIC",
        "SHARED",
        "PUBLISHED_SHARED_LESSON",
        "AI_GENERATED_DRAFT",
    ]
    lesson_title: str | None = None
    lesson_topic: str | None = None
    # FEAT-092: provenance written by suggestion-set selections (see the repository snapshot).
    source_lesson_id: str | None = None
    source_lesson_version_id: str | None = None
    source_content_sha256: str | None = None
    source_activity_index: int | None = None
    match_reason: str | None = None
    suggestion_set_id: UUID | None = None
    suggestion_set_revision: int | None = None
    suggestion_activity_index: int | None = None


class ParentPostVideoActivityV1(ParentActivityV1):
    is_main: bool


class ParentMainActivityV1(BaseModel):
    """``NOT_SELECTED`` until the adult chose; then the stored snapshot (no catalog read)."""

    model_config = ConfigDict(extra="forbid")

    state: Literal["NOT_SELECTED", "SELECTED"]
    selected: ParentActivityV1 | None = None
    selected_at: datetime | None = None


class ParentActivityListBasisV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age_band: Literal["36-71", "72-107", "108-120"]
    pinned_lesson: bool
    no_candidate: bool


class ParentActivityListV1(BaseModel):
    """At most 12 age-fit activities in a deterministic order; not a paged collection."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    items: list[ParentActivityV1] = Field(max_length=12)
    basis: ParentActivityListBasisV1


class ParentActivitySelectionRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1)
    activity: ParentActivityRefV1 | None = None
    suggestion_set_id: UUID | None = Field(default=None, strict=False)
    expected_understanding_revision: int | None = Field(default=None, ge=1)
    activity_index: int | None = Field(default=None, ge=0, le=23)

    @model_validator(mode="after")
    def selection_variant(self) -> ParentActivitySelectionRequestV1:
        catalog_selection = (
            self.activity is not None
            and self.suggestion_set_id is None
            and self.expected_understanding_revision is None
            and self.activity_index is None
        )
        suggestion_selection = (
            self.activity is None
            and self.suggestion_set_id is not None
            and self.expected_understanding_revision is not None
            and self.activity_index is not None
        )
        if not catalog_selection and not suggestion_selection:
            raise ValueError("provide either a catalog activity reference or a suggestion-set index")
        return self


class ParentStoryRunResponseV1(BaseModel):
    run_id: UUID
    run_revision: int = Field(ge=1)
    run_state: ParentStoryRunStateV1
    parent_profile_id: UUID
    profile_revision_ref: UUID
    context_revision: int
    context_confirmed: bool
    context_snapshot: ParentRunContextSnapshotV1
    context_snapshot_sha256: str
    lesson_pin_snapshot: ParentLessonPinSnapshotV1 | None = None
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
    # FEAT-066 T-1c (StoryRunDetailV1, SRS l.1811): additive fields only (l.1635).
    video: ParentStoryRunVideoV1 | None = None
    quota: ParentStoryQuotaSummaryV1 = Field(default_factory=ParentStoryQuotaSummaryV1)
    timeline: list[ParentStoryTimelineEventV1] = Field(default_factory=list)
    # FEAT-066 T-2e-a (SRS l.514, l.532, l.1414): additive. The name is not ``activity``: the
    # Teacher response already has that field.
    main_activity: ParentMainActivityV1 | None = None
    post_video_activities: list[ParentPostVideoActivityV1] | None = None
    # FEAT-066 V4-A T-1b-fix (SRS l.406, l.1728; additive, l.1635): true when the adult has to
    # confirm the current story (again) before a video can be requested.
    story_confirmation_required: bool = False


class ParentStoryRunEnvelopeV1(BaseModel):
    request_id: UUID
    story_run: ParentStoryRunResponseV1


class ParentStoryRunLifecycleProjectionV1(BaseModel):
    """FR-C-08 content-free projection from DELETE_PENDING on (Contract Draft 11 §3.4).

    No context snapshot, story, candidate, subject label, profile ref, asset ref, count,
    percentage or storage key is ever part of it (SRS lines 1053, 1520, 1809).
    """

    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    run_state: Literal["DELETE_PENDING", "DELETED"]
    revision: int = Field(ge=1)
    version: int = Field(ge=1)
    lifecycle_request_ref: UUID
    purge_state: Literal["PENDING", "COMPLETED"]


class ParentStoryRunLifecycleEnvelopeV1(BaseModel):
    """Cancel 202, delete 202, GET of a purged run and the replays of a purged run."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    lifecycle: ParentStoryRunLifecycleProjectionV1


# D-218 A-3: the frozen cancel envelope that embedded the full run is replaced by the lifecycle
# envelope. The name is kept as an alias for the cancel route's declared response.
ParentStoryRunCancelEnvelopeV1 = ParentStoryRunLifecycleEnvelopeV1


class ParentStoryErrorFieldV1(BaseModel):
    field: str
    code: str
    message: str


class ParentStoryErrorEnvelopeV1(BaseModel):
    code: str
    message: str
    correlation_id: str
    retryable: bool
    retry_after_seconds: int | None = None
    field_errors: list[ParentStoryErrorFieldV1] | None = None


class ParentStoryCancelErrorEnvelopeV1(ParentStoryErrorEnvelopeV1):
    current_version: int | None = Field(default=None, ge=1)


class ParentStoryRunSummaryV1(BaseModel):
    """FEAT-081 C3b history item: summary only (no story, context, topic, media or provider)."""

    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    parent_profile_id: UUID | None
    run_state: str
    revision: int = Field(ge=1)
    deleting: bool
    can_cancel: bool
    can_delete: bool
    created_at: datetime
    updated_at: datetime


class ParentStoryRunHistoryPageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    items: list[ParentStoryRunSummaryV1]
    next_cursor: str | None


class ParentActiveStoryRunEnvelopeV1(BaseModel):
    request_id: UUID
    story_run: ParentStoryRunResponseV1 | None


class ParentSubjectConfirmationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    expected_understanding_revision: int = Field(ge=1)
    confirmed_subject: str = Field(min_length=1, max_length=160)
    # FEAT-087, optional: omitted by older clients, in which case no secondary object is used.
    subject_roles: list[ParentSubjectRoleV1] | None = Field(default=None, min_length=1, max_length=4)


class ParentContextConfirmationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_context_revision: int = Field(ge=1)
    context_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed: Literal[True]


class ParentSubjectConfirmationResponseV1(BaseModel):
    """202 body of the subject confirmation (SRS l.1666).

    ``CONFIRMED``: the subject was accepted as ``understanding_revision``. ``RERUN_REQUESTED``: the
    adult edited the subject, the visual understanding runs again and the new revision is
    confirmed in a second call (SRS l.394, l.1413); ``understanding_revision`` is then the revision
    the adult edited. ``run_revision`` is the revision the command created. The job reference is
    parked (Q-J), so there is no ``job`` field.
    """

    request_id: UUID
    story_run_id: UUID
    understanding_revision: int
    decision: Literal["CONFIRMED", "RERUN_REQUESTED"]
    run_revision: int = Field(ge=1)


class ParentStoryRevisionRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    expected_understanding_revision: int = Field(ge=1)
    rewrite_instruction: str | None = Field(default=None, min_length=1, max_length=400)


class ParentStoryRevisionConfirmationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1, le=4)
    story_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


__all__ = [
    "ParentActivityListBasisV1",
    "ParentActivityListV1",
    "ParentActivityRefV1",
    "ParentActivitySelectionRequestV1",
    "ParentActivityV1",
    "ParentDrawingCandidateV1",
    "ParentMainActivityV1",
    "ParentPostVideoActivityV1",
    "ParentContextConfirmationRequestV1",
    "ParentLessonVersionRefV1",
    "ParentRunContextSnapshotV1",
    "ParentStoryErrorEnvelopeV1",
    "ParentStoryErrorFieldV1",
    "ParentStoryDisplayV1",
    "ParentStoryRevisionConfirmationRequestV1",
    "ParentStoryRevisionRequestV1",
    "ParentStorySceneDisplayV1",
    "ParentStorySectionsV1",
    "ParentActiveStoryRunEnvelopeV1",
    "ParentStoryRunCreateRequestV1",
    "ParentStoryRunCancelRequestV1",
    "ParentStoryRunCancelEnvelopeV1",
    "ParentStoryCancelErrorEnvelopeV1",
    "ParentStoryRunEnvelopeV1",
    "ParentStoryRunLifecycleEnvelopeV1",
    "ParentStoryRunLifecycleProjectionV1",
    "ParentStoryRunResponseV1",
    "ParentStoryRunStateV1",
    "ParentDrawingEntityV1",
    "ParentSubjectRoleV1",
    "ParentSubjectConfirmationRequestV1",
    "ParentSubjectConfirmationResponseV1",
]
