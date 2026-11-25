"""Versioned HTTP DTOs for the Parent StoryRun input routes (SRS l.1664; goal v3 T-2b).

``POST /v1/story-runs/{run_id}/assets`` attaches a completed generic upload (T-2a) to a run as the
drawing. The client sends only the opaque ``asset_ref`` handle (``upl_{upload id}``); owner, key,
bucket and URL are never accepted from, or returned to, the client (SRS l.1637, l.1692). T-2c and
T-2d add their own request and response models to this module.

T-2c adds ``POST /v1/story-runs/{run_id}/idea`` (SRS l.1665: text, an audio reference or a
transcript correction), ``GET .../transcript`` and ``POST .../transcript-confirmation`` (TD-04,
l.1713). The client sends only opaque handles and revisions; the transcript text is returned only
to its owner by the read route and never appears in an error body.

T-2d adds ``POST /v1/story-runs/{run_id}/story-rewrites`` (SRS l.1668, FR-P-07): the request names
the story revision the adult read (and optionally its hash) and may carry a short hint, which is
untrusted data and never an instruction.
"""

from __future__ import annotations

import unicodedata
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AnalysisState = Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "AWAITING_RECONCILIATION"]


class AttachRunAssetRequestV1(BaseModel):
    """Attach one completed upload to the run; ``expected_run_revision`` is optional (l.1664)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    asset_ref: str = Field(pattern=r"^upl_[0-9a-f-]{36}$")
    expected_run_revision: int | None = Field(default=None, ge=1)


class ResumeDrawingAnalysisRequestV1(BaseModel):
    """Resume an already attached, still-queued drawing without uploading or changing it."""

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_input_revision: int = Field(ge=1)


class ParentDrawingAnalysisResumeAcceptedV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_run_id: UUID
    input_revision: int = Field(ge=1)
    run_revision: int = Field(ge=1)
    dispatch_state: Literal["ACCEPTED"]


class ParentRunAssetAcceptedV1(BaseModel):
    """202 body: the asset ref and its validation state (l.1664); no job reference (T2B-D8)."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_run_id: UUID
    asset_ref: str
    asset_kind: Literal["DRAWING"]
    asset_state: Literal["READY"]
    input_revision: int = Field(ge=1)
    run_revision: int = Field(ge=1)
    run_state: str
    analysis_state: AnalysisState


TRANSCRIPT_TEXT_MAX = 500  # the typed idea and the confirmed transcript share this bound (BR-23)
IdeaSource = Literal["TEXT", "VOICE", "TEXT_AND_VOICE"]
TranscriptState = Literal["NONE", "PENDING", "NEEDS_CONFIRMATION", "CONFIRMED", "FAILED"]


def _clean_text(value: str | None) -> str | None:
    """Trim the text; an empty or over-long text is a field error (400 ``INVALID_REQUEST``)."""
    if value is None:
        return None
    cleaned = value.strip()
    if not 1 <= len(cleaned) <= TRANSCRIPT_TEXT_MAX:
        raise ValueError("text must hold 1 to 500 characters")
    return cleaned


class TranscriptCorrectionV1(BaseModel):
    """The adult's corrected transcript text, based on one exact transcript revision."""

    model_config = ConfigDict(extra="forbid", strict=True)

    base_revision: int = Field(ge=1)
    text: str = Field(max_length=TRANSCRIPT_TEXT_MAX)

    @field_validator("text")
    @classmethod
    def _text(cls, value: str) -> str:
        return _clean_text(value) or ""


class AddRunIdeaRequestV1(BaseModel):
    """``expected_run_revision`` plus text and/or ``audio_ref``, or one transcript correction."""

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_run_revision: int = Field(ge=1)
    text: str | None = Field(default=None, max_length=TRANSCRIPT_TEXT_MAX)
    audio_ref: str | None = Field(default=None, pattern=r"^upl_[0-9a-f-]{36}$")
    transcript_correction: TranscriptCorrectionV1 | None = None

    @field_validator("text")
    @classmethod
    def _text(cls, value: str | None) -> str | None:
        return _clean_text(value)

    @model_validator(mode="after")
    def _one_group(self) -> Self:
        submission = self.text is not None or self.audio_ref is not None
        if submission == (self.transcript_correction is not None):
            raise ValueError("send text and/or audio_ref, or a transcript_correction, not both")
        return self


class IdeaTranscriptRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_revision: int = Field(ge=1)
    state: TranscriptState


class ParentRunIdeaAcceptedV1(BaseModel):
    """202 body of ``/idea``; the ASR job reference is parked (Q-J), so no ``job`` field."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_run_id: UUID
    input_revision: int = Field(ge=1)
    run_revision: int = Field(ge=1)
    run_state: str
    idea_source: IdeaSource | None
    transcript: IdeaTranscriptRefV1 | None


class ParentRunTranscriptV1(BaseModel):
    """The adult's read of the current transcript (SRS l.780, l.1164, l.1707, BR-34)."""

    model_config = ConfigDict(extra="forbid")

    story_run_id: UUID
    transcript_revision: int | None = Field(ge=1)
    state: TranscriptState
    origin: Literal["ASR", "ADULT_CORRECTION"] | None
    text: str | None
    transcript_sha256: str | None
    language: str | None
    error_code: str | None
    run_revision: int = Field(ge=1)


class ConfirmTranscriptRequestV1(BaseModel):
    """Confirm one exact revision and hash (TD-04, l.1713)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_transcript_revision: int = Field(ge=1)
    transcript_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed: Literal[True]


class ParentTranscriptConfirmationV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_run_id: UUID
    transcript_revision: int = Field(ge=1)
    state: Literal["CONFIRMED"]
    run_revision: int = Field(ge=1)
    run_state: str


REWRITE_HINT_MAX = 400  # the legacy rewrite instruction bound (FR-P-07)
STORY_REWRITE_REVISION_MAX = 4  # the first story plus three rewrites (FR-P-07, l.1413)


class RewriteStoryRequestV1(BaseModel):
    """Ask for one more story revision; ``expected_story_revision`` is the one the adult read.

    The range admits 4: after the third rewrite the client holds revision 4 and its next request
    is refused with 409 ``STORY_REWRITE_LIMIT_REACHED``, not with a validation error (l.866).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    expected_story_revision: int = Field(ge=1, le=STORY_REWRITE_REVISION_MAX)
    expected_story_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    hint: str | None = Field(default=None, min_length=1, max_length=REWRITE_HINT_MAX)

    @field_validator("hint")
    @classmethod
    def _hint(cls, value: str | None) -> str | None:
        if value is not None and any(unicodedata.category(char) == "Cc" for char in value):
            raise ValueError("the hint must not contain control characters")
        return value


class ParentStoryRewriteAcceptedV1(BaseModel):
    """202 body of ``story-rewrites``; the job reference is parked (Q-J), so no ``job`` field."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_run_id: UUID
    story_revision_no: int = Field(ge=1, le=STORY_REWRITE_REVISION_MAX)
    run_revision: int = Field(ge=1)
    run_state: Literal["SCRIPT_GENERATING"]


__all__ = [
    "AddRunIdeaRequestV1",
    "AnalysisState",
    "AttachRunAssetRequestV1",
    "ConfirmTranscriptRequestV1",
    "IdeaSource",
    "IdeaTranscriptRefV1",
    "ParentRunAssetAcceptedV1",
    "ParentRunIdeaAcceptedV1",
    "ParentRunTranscriptV1",
    "ParentDrawingAnalysisResumeAcceptedV1",
    "ParentStoryRewriteAcceptedV1",
    "ParentTranscriptConfirmationV1",
    "RewriteStoryRequestV1",
    "ResumeDrawingAnalysisRequestV1",
    "TranscriptCorrectionV1",
    "TranscriptState",
]
