"""Contracts of the Teacher lesson occurrence (FEAT-066 goal v3, T-3a; SRS l.775, l.1652).

``LessonVersionRefV1`` is the optional typed lesson pin of SRS l.547 and l.2563: exact
``lesson_id``, ``version_id`` and ``content_sha256``, never ``latest``. It has the same fields,
names and strictness as the Parent flow's ``ParentLessonVersionRefV1`` (a contract test pins the
two together), so an occurrence, its plan revisions and a StoryRun carry one shape.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sketch2life.domain.lesson_occurrences.documents import MAX_TEXT_BYTES
from sketch2life.domain.lesson_occurrences.model import (
    CLASS_ID_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    LessonOccurrenceRuleError,
    has_forbidden_characters,
    parse_scheduled_date,
)
from sketch2life.domain.lesson_occurrences.plan import (
    ACTIVITIES_MAX,
    CUSTOM_DESCRIPTION_MAX_CHARS,
    CUSTOM_TITLE_MAX_CHARS,
    DIRECTION_MAX_CHARS,
    OBJECTIVE_MAX_CHARS,
    OBJECTIVES_MAX,
    SAFETY_NOTES_MAX_CHARS,
)
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    CHECKLIST_ITEM_ID_MAX_LENGTH,
    CHECKLIST_ITEMS_MAX,
    CHECKLIST_VERSION_MAX_LENGTH,
    ITEM_ID_PATTERN,
)

OccurrenceStateV1 = Literal[
    "DRAFT",
    "DOCUMENT_REVIEW",
    "PLAN_REVIEW",
    "APPROVED",
    "SAMPLE_AVAILABLE",
    "SAMPLE_USED",
    "ARCHIVED",
]


class LessonVersionRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    lesson_id: str = Field(min_length=1, max_length=256)
    version_id: str = Field(min_length=1, max_length=256)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CreateLessonOccurrenceRequestV1(BaseModel):
    """Body of ``POST /v1/lesson-occurrences``.

    Organization, owner and Teacher are server-derived, never part of the body.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    class_id: str = Field(min_length=1, max_length=CLASS_ID_MAX_LENGTH)
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    scheduled_date: date | None = None
    lesson_version_ref: LessonVersionRefV1 | None = None

    @field_validator("title")
    @classmethod
    def _title_has_no_control_characters(cls, value: str) -> str:
        if has_forbidden_characters(value):
            raise ValueError("INVALID_FORMAT")
        return value

    @field_validator("class_id")
    @classmethod
    def _class_id_has_no_control_characters(cls, value: str) -> str:
        if has_forbidden_characters(value):
            raise ValueError("INVALID_FORMAT")
        return value

    @field_validator("scheduled_date", mode="before")
    @classmethod
    def _iso_date_only(cls, value: Any) -> Any:
        if value is None:
            return None
        try:
            return parse_scheduled_date(value)
        except LessonOccurrenceRuleError:
            raise ValueError("INVALID_FORMAT") from None


class ApprovedPlanSummaryV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_no: int
    plan_hash: str
    approved_at: datetime


class SampleVideoStateV1(BaseModel):
    """Sample-video slot of the occurrence (SRS l.1708); claim fields stay null until WP-4b."""

    model_config = ConfigDict(extra="forbid")

    slot_state: Literal["AVAILABLE", "CLAIMED"]
    claimed_at: datetime | None = None
    run_ref: str | None = None


class LessonOccurrenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonOccurrenceV1"] = "LessonOccurrenceV1"
    occurrence_id: str
    class_id: str
    title: str
    scheduled_date: date | None = None
    state: OccurrenceStateV1
    revision: int
    responsible_teacher_ref: str
    lesson_version_ref: LessonVersionRefV1 | None = None
    lesson_version_no: int | None = None
    approved_plan: ApprovedPlanSummaryV1 | None = None
    sample_video: SampleVideoStateV1
    created_at: datetime


class LessonOccurrencePageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonOccurrencePageV1"] = "LessonOccurrencePageV1"
    items: list[LessonOccurrenceV1]
    next_cursor: str | None = None


# ----------------------------------------------------------------------------- source documents
# FEAT-066 T-3b (SRS l.1653, l.1708). Organization, owner, file name, hash and type of an attached
# document are server-derived (l.1637); no storage URL, bucket, key, scanner name or asset ref is
# ever returned, only the opaque ids below (l.1692).
_ASSET_HANDLE = r"^upl_[A-Za-z0-9._:-]{1,64}$"


class AttachOccurrenceDocumentRequestV1(BaseModel):
    """Body of ``POST /v1/lesson-occurrences/{id}/documents``: the completed upload's asset ref."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    asset_ref: str = Field(min_length=1, max_length=128, pattern=_ASSET_HANDLE)


class EditDocumentRevisionRequestV1(BaseModel):
    """Body of ``POST .../documents/{document_id}/revisions`` (T-3c, SRS l.546, l.1437, l.1699).

    The text is stored exactly as sent, so unlike the library schemas this model does not strip
    whitespace. ``max_length`` counts characters and is only a coarse bound (a character is at
    least one UTF-8 byte); the real limit is 2,097,152 UTF-8 bytes and is checked by the service.
    ``expected_head_revision_no`` is the head the Teacher edited from (the stale fence).
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    extracted_text: str = Field(
        min_length=1,
        max_length=MAX_TEXT_BYTES,
        description=(
            "The full edited text, stored exactly as sent. The limit is 2,097,152 UTF-8 bytes, "
            "not characters (count with TextEncoder); blank text and NUL are refused."
        ),
    )
    expected_head_revision_no: int = Field(ge=1, le=1_000_000)


class ExtractionJobRefV1(BaseModel):
    """The extraction job: already terminal, poll ``/v1/jobs/{job_id}`` once to read it."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    target_kind: Literal["LESSON_SOURCE_DOCUMENT"] = "LESSON_SOURCE_DOCUMENT"
    state: Literal["succeeded"] = "succeeded"


class LessonSourceDocumentAcceptedV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonSourceDocumentAcceptedV1"] = "LessonSourceDocumentAcceptedV1"
    source_document_id: str
    document_revision_no: Literal[1] = 1
    job: ExtractionJobRefV1


class LessonSourceDocumentV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonSourceDocumentV1"] = "LessonSourceDocumentV1"
    source_document_id: str
    occurrence_id: str
    file_name: str
    file_extension: Literal[".pdf", ".docx", ".pptx"]
    page_or_slide_count: int | None = None
    document_state: Literal["EXTRACTED", "DELETED"]
    head_revision_no: int
    job_ref: str
    warnings: list[str]
    page_coverage: list[int]
    uploaded_at: datetime


class LessonSourceDocumentPageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonSourceDocumentPageV1"] = "LessonSourceDocumentPageV1"
    items: list[LessonSourceDocumentV1]
    next_cursor: str | None = None


class DocumentParserV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str


class LessonDocumentRevisionSummaryV1(BaseModel):
    """A revision without its text (the text is read one revision at a time)."""

    model_config = ConfigDict(extra="forbid")

    revision_no: int
    origin: Literal["EXTRACTION", "TEACHER_EDIT"]
    review_state: Literal["NEEDS_REVIEW", "CONFIRMED"]
    text_hash: str
    text_length: int
    created_at: datetime


class LessonDocumentRevisionPageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonDocumentRevisionPageV1"] = "LessonDocumentRevisionPageV1"
    items: list[LessonDocumentRevisionSummaryV1]
    next_cursor: str | None = None


class LessonDocumentRevisionV2(BaseModel):
    """One revision with its text. ``text_length`` counts characters of the stored text."""

    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonDocumentRevisionV2"] = "LessonDocumentRevisionV2"
    source_document_id: str
    revision_no: int
    origin: Literal["EXTRACTION", "TEACHER_EDIT"]
    review_state: Literal["NEEDS_REVIEW", "CONFIRMED"]
    base_revision_no: int | None = None
    extracted_text: str
    text_hash: str
    text_length: int
    parser: DocumentParserV1 | None = None
    warnings: list[str]
    page_coverage: list[int]
    created_at: datetime


# ----------------------------------------------------------------------------- plan revisions
# FEAT-066 T-3d (SRS l.547-548, l.775, l.1659-1660, l.1699). The plan copies the occurrence's lesson
# pin, so no pin field exists in the request and no ``latest`` alias in any path. Free text is
# stored exactly as sent: unlike the library schemas these models do not strip whitespace. The
# limits are technical (T-3d-DEC-2), equal to the Lesson Library limits, and are published in the
# schema.


class PlanDocumentRefV1(BaseModel):
    """A text revision of a document of the same occurrence (SRS l.1442, UC-04)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    document_id: str = Field(min_length=1, max_length=36)
    revision_no: int = Field(ge=1, le=1_000_000)

    @field_validator("document_id")
    @classmethod
    def _no_nul(cls, value: str) -> str:
        # PostgreSQL text cannot hold NUL: it would reach the query as a 503 (review F-01).
        if "\x00" in value:
            raise ValueError("INVALID_FORMAT")
        return value


class PlanActivityInputV1(BaseModel):
    """``LESSON``: copy an activity of the pinned lesson version (``lesson_activity_id``).

    ``CUSTOM``: a Teacher-written activity (``title`` and ``description``); it needs a safety
    checklist (SRS l.548) and is refused while the checklist definition is not configured.
    ``CATALOG`` is refused until the activity catalog exists (TD-16).
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["LESSON", "CUSTOM", "CATALOG"]
    lesson_activity_id: str | None = Field(default=None, min_length=1, max_length=36)
    title: str | None = Field(default=None, min_length=1, max_length=CUSTOM_TITLE_MAX_CHARS)
    description: str | None = Field(
        default=None, min_length=1, max_length=CUSTOM_DESCRIPTION_MAX_CHARS
    )


class CreatePlanRevisionRequestV1(BaseModel):
    """Body of ``POST /v1/lesson-occurrences/{id}/plan-revisions`` (draft, immutable once written).

    ``expected_head_revision_no`` is the head the Teacher edited from (0 when no plan revision
    exists); a different head is 409 ``STALE_REVISION`` (SRS l.1699).
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_head_revision_no: int = Field(ge=0, le=1_000_000)
    document_revision_ref: PlanDocumentRefV1 | None = None
    objectives: list[Annotated[str, Field(min_length=1, max_length=OBJECTIVE_MAX_CHARS)]] = Field(
        min_length=1, max_length=OBJECTIVES_MAX
    )
    teacher_direction: str = Field(min_length=1, max_length=DIRECTION_MAX_CHARS)
    safety_notes: str | None = Field(default=None, max_length=SAFETY_NOTES_MAX_CHARS)
    activities: list[PlanActivityInputV1] = Field(default_factory=list, max_length=ACTIVITIES_MAX)


class PlanChecklistItemV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    item_id: str = Field(
        min_length=1, max_length=CHECKLIST_ITEM_ID_MAX_LENGTH, pattern=ITEM_ID_PATTERN
    )
    checked: bool


class PlanChecklistEntryV1(BaseModel):
    """The Teacher's answers for one ``CUSTOM`` activity of the plan."""

    model_config = ConfigDict(extra="forbid", strict=True)

    activity_order: int = Field(ge=1, le=ACTIVITIES_MAX)
    checklist_version: str = Field(min_length=1, max_length=CHECKLIST_VERSION_MAX_LENGTH)
    items: list[PlanChecklistItemV1] = Field(max_length=CHECKLIST_ITEMS_MAX)


class ConfirmPlanRevisionRequestV1(BaseModel):
    """Body of ``POST .../plan-revisions/{revision_no}/confirm`` (SRS l.1660).

    ``expected_plan_hash`` is the ``content_hash`` the Teacher read; only the head revision can be
    confirmed, and a hash that differs from it is 409 ``STALE_REVISION``.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    checklist: list[PlanChecklistEntryV1] = Field(default_factory=list, max_length=ACTIVITIES_MAX)


class PlanActivityV1(BaseModel):
    """One activity of ONE plan revision.

    ``plan_activity_id`` (V4-A OPEN-B) is the id of that activity row, the value a Teacher run
    create accepts as ``activity_id``. It is meaningful with ``(revision_no, content_hash)`` only:
    a new revision has new ids. Optional so a stored replay body written before the field existed
    still validates (the replay path fills it from the immutable rows).
    """

    model_config = ConfigDict(extra="forbid")

    plan_activity_id: str | None = Field(default=None, min_length=1, max_length=36)
    order: int
    kind: Literal["LESSON", "CUSTOM", "CATALOG"]
    lesson_activity_id: str | None = None
    title: str | None = None
    description: str | None = None
    snapshot_hash: str | None = None
    checklist_required: bool
    checklist_version: str | None = None
    confirmed: bool


class LessonPlanRevisionV1(BaseModel):
    """One plan revision. ``supersedes_revision_no`` is set only in the confirm response."""

    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonPlanRevisionV1"] = "LessonPlanRevisionV1"
    occurrence_id: str
    revision_no: int
    state: Literal["DRAFT", "APPROVED", "SUPERSEDED"]
    content_hash: str
    document_revision_ref: PlanDocumentRefV1 | None = None
    objectives: list[str]
    teacher_direction: str
    safety_notes: str | None = None
    lesson_version_ref: LessonVersionRefV1 | None = None
    lesson_version_no: int | None = None
    activities: list[PlanActivityV1]
    created_at: datetime
    approved_at: datetime | None = None
    supersedes_revision_no: int | None = None


class LessonPlanRevisionSummaryV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_no: int
    state: Literal["DRAFT", "APPROVED", "SUPERSEDED"]
    content_hash: str
    activity_count: int
    created_at: datetime
    approved_at: datetime | None = None


class LessonPlanRevisionPageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["LessonPlanRevisionPageV1"] = "LessonPlanRevisionPageV1"
    items: list[LessonPlanRevisionSummaryV1]
    next_cursor: str | None = None


# ----------------------------------------------------------------------------- child selection
ChildSelectionStateV1 = Literal[
    "OPEN", "CONFIRMED", "CONSUMED", "EXPIRED", "STALE", "VOID", "EMPTY", "STOPPED"
]


class CreateChildSelectionRequestV1(BaseModel):
    """Body of ``POST .../child-selections``: nothing. No field chooses, filters or orders the
    candidate set and none names a child (SRS l.341, l.549)."""

    model_config = ConfigDict(extra="forbid", strict=True)


class ConfirmChildSelectionRequestV1(BaseModel):
    """Body of ``POST .../child-selections/{selection_id}/confirmation`` (SRS l.346, l.352).

    ``expected_selection_sha256`` is the ``selection_sha256`` the Teacher read, so the Teacher
    confirms exactly the offer that was shown; the selection revision travels in ``If-Match``.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ChildSelectionChildV1(BaseModel):
    """The offered child, read live from the profile row and never stored with the selection."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str
    display_name: str
    age_months: int


class ChildSelectionPlanV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_no: int
    plan_hash: str


class ChildSelectionV1(BaseModel):
    """One answer of the selection routes (SRS l.341-352, AC-56).

    ``child`` is present only while the offer is live (``OPEN`` or ``CONFIRMED``), not expired and
    the child is still eligible; every other answer carries no child data and no reason per child
    (l.347). ``selection_id`` and ``revision`` are null when no row is behind the answer.
    """

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ChildSelectionV1"] = "ChildSelectionV1"
    selection_id: str | None = None
    occurrence_id: str
    outcome: Literal["SELECTED", "NO_ELIGIBLE_CHILD"]
    state: ChildSelectionStateV1
    revision: int | None = None
    draw_no: int | None = None
    reselect_available: bool
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    confirmation_expires_at: datetime | None = None
    selection_sha256: str | None = None
    plan: ChildSelectionPlanV1 | None = None
    consumed_run_ref: str | None = None
    child: ChildSelectionChildV1 | None = None


# ----------------------------------------------------------------------------- class projection
_CANONICAL_UUID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class ProjectionConfirmationRequestV1(BaseModel):
    """Body of ``POST .../projection-confirmation`` (SRS l.1661, l.777, FR-T-16 l.555).

    The pair ``(run_id, generation_id)`` must be the current playable sample of the occurrence.
    ``audience`` and ``use`` are the explicit acknowledgement the SRS asks for without naming
    values (T-5a OPEN-3): the single literals ``CLASS`` and ``CLASS_PROJECTION``; any other value
    is ``INVALID_REQUEST``. The occurrence revision travels in ``If-Match``.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: str = Field(pattern=_CANONICAL_UUID)
    generation_id: str = Field(pattern=_CANONICAL_UUID)
    audience: Literal["CLASS"]
    use: Literal["CLASS_PROJECTION"]


class ProjectionAssignmentV1(BaseModel):
    """The assignment version of SRS l.777: the class revision (a Teacher assignment bumps it)."""

    model_config = ConfigDict(extra="forbid")

    class_revision: int


class ProjectionPlanV1(BaseModel):
    """The plan the sample run is pinned to; ``is_current`` is false when a newer plan was
    approved after the run was created (SRS l.2697: the old READY output stays pinned)."""

    model_config = ConfigDict(extra="forbid")

    revision_no: int
    plan_hash: str
    is_current: bool


class ProjectionSampleVideoV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_state: Literal["AVAILABLE", "CLAIMED"]
    claimed_at: datetime | None = None
    run_ref: str | None = None


class ClassProjectionConfirmationV1(BaseModel):
    """The receipt of a class projection confirmation (SRS l.777): references and times only, no
    child name, no media key, no token and no capability for class members."""

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ClassProjectionConfirmationV1"] = "ClassProjectionConfirmationV1"
    occurrence_id: str
    run_id: str
    generation_id: str
    audience: Literal["CLASS"]
    use: Literal["CLASS_PROJECTION"]
    confirmed_at: datetime
    confirmed_by_ref: str
    assignment: ProjectionAssignmentV1
    plan: ProjectionPlanV1
    occurrence_revision: int
    sample_video: ProjectionSampleVideoV1


class ProjectionPlaybackTokenV1(BaseModel):
    """A short-lived token for the Teacher who controls the class projection (SRS l.1662). The
    token is a bearer secret sent only in the ``X-Playback-Token`` header of the stream route; it
    names no storage location (l.1692)."""

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ProjectionPlaybackTokenV1"] = "ProjectionPlaybackTokenV1"
    token: str
    expires_at: datetime
    stream_path: str
    media_type: Literal["video/mp4"]


__all__ = [
    "ApprovedPlanSummaryV1",
    "AttachOccurrenceDocumentRequestV1",
    "ChildSelectionChildV1",
    "ChildSelectionPlanV1",
    "ChildSelectionStateV1",
    "ChildSelectionV1",
    "ClassProjectionConfirmationV1",
    "ConfirmChildSelectionRequestV1",
    "ConfirmPlanRevisionRequestV1",
    "CreateChildSelectionRequestV1",
    "CreateLessonOccurrenceRequestV1",
    "CreatePlanRevisionRequestV1",
    "DocumentParserV1",
    "EditDocumentRevisionRequestV1",
    "ExtractionJobRefV1",
    "LessonDocumentRevisionPageV1",
    "LessonDocumentRevisionSummaryV1",
    "LessonDocumentRevisionV2",
    "LessonOccurrencePageV1",
    "LessonOccurrenceV1",
    "LessonPlanRevisionPageV1",
    "LessonPlanRevisionSummaryV1",
    "LessonPlanRevisionV1",
    "LessonSourceDocumentAcceptedV1",
    "LessonSourceDocumentPageV1",
    "LessonSourceDocumentV1",
    "LessonVersionRefV1",
    "OccurrenceStateV1",
    "PlanActivityInputV1",
    "PlanActivityV1",
    "PlanChecklistEntryV1",
    "PlanChecklistItemV1",
    "PlanDocumentRefV1",
    "ProjectionAssignmentV1",
    "ProjectionConfirmationRequestV1",
    "ProjectionPlanV1",
    "ProjectionPlaybackTokenV1",
    "ProjectionSampleVideoV1",
    "SampleVideoStateV1",
]
