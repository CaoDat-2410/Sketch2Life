"""Strict public contracts for the bounded non-video Modal AI workflows."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ParentSketchGuideRequestV1(StrictRequest):
    topic: str = Field(min_length=1, max_length=120)
    difficulty: Literal["beginner", "simple"] = "beginner"
    step_count: int = Field(default=3, ge=3, le=5)


class ParentDrawingAnalysisRequestV1(StrictRequest):
    story_run_id: UUID
    image_base64: str = Field(min_length=16, max_length=6_700_000)
    media_type: Literal["image/jpeg", "image/png"]


class ParentStoryRequestV1(StrictRequest):
    expected_understanding_revision: int = Field(ge=1)
    rewrite_instruction: str | None = Field(default=None, min_length=1, max_length=400)


class ParentActivitySuggestionRequestV1(StrictRequest):
    expected_understanding_revision: int = Field(ge=1)


class ParentActivitySuggestionItemV1(StrictRequest):
    title: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=1000)
    materials_text: str = Field(max_length=2000)
    preparation_text: str = Field(max_length=2000)
    instructions_text: str = Field(min_length=1, max_length=5000)
    observation_notes: str = Field(max_length=3000)
    safety_notes: str = Field(max_length=3000)
    activity_kind: Literal["outdoor", "indoor", "mixed"]


class ParentActivitySuggestionResponseV1(StrictRequest):
    request_id: UUID
    story_run_id: UUID
    understanding_revision: int = Field(ge=1)
    source: Literal["PINNED_LESSON", "QWEN3_5_MODAL"]
    source_lesson_version_id: str | None
    review_required: Literal[True]
    activities: list[ParentActivitySuggestionItemV1] = Field(min_length=1, max_length=24)


class ParentActivityCatalogCandidateV2(StrictRequest):
    candidate_ref: str = Field(pattern=r"^C[0-9]{3}$")
    lesson_topic: str = Field(min_length=1, max_length=120)
    drawing_subject: str = Field(min_length=1, max_length=160)
    age_band_months: Literal["36-71", "72-107", "108-120"]
    activity: ParentActivitySuggestionItemV1


class ParentActivitySuggestionWorkerRequestV3(StrictRequest):
    schema_version: Literal["sketch2life.parent-activity-suggest-input.v3"]
    age_band_months: Literal["36-71", "72-107", "108-120"]
    age_band_ref: str = Field(pattern=r"^age-[0-9]{2,3}-[0-9]{2,3}-months-v1$")
    topic: str = Field(max_length=120)
    adult_confirmed_idea: str = Field(max_length=300)
    confirmed_subject: str = Field(min_length=1, max_length=160)
    visible_features: list[str] = Field(min_length=1, max_length=4)
    profile_interest_tags: list[str] = Field(max_length=12)
    narration_interest_tags: list[str] = Field(max_length=12)
    candidate_activities: list[ParentActivityCatalogCandidateV2] = Field(max_length=12)


class ParentActivityCandidateSelectionV2(StrictRequest):
    candidate_ref: str = Field(pattern=r"^C[0-9]{3}$")
    match_reason: str = Field(min_length=1, max_length=180)


class ParentActivityFallbackDraftV1(StrictRequest):
    title: str = Field(min_length=1, max_length=60)
    objective: str = Field(min_length=1, max_length=80)
    materials_text: str = Field(max_length=60)
    preparation_text: str = Field(min_length=1, max_length=85)
    instructions_text: str = Field(min_length=1, max_length=150)
    observation_notes: str = Field(max_length=70)
    safety_notes: str = Field(min_length=1, max_length=80)
    activity_kind: Literal["outdoor", "indoor", "mixed"]


class ParentActivitySuggestionWorkerResponseV2(StrictRequest):
    schema_version: Literal["sketch2life.parent-activity-suggestions.v2"]
    decision: Literal["CATALOG_MATCH", "NO_MATCH"]
    selected_candidates: list[ParentActivityCandidateSelectionV2] = Field(max_length=5)
    no_match_reason: str = Field(max_length=120)
    age_band_months: Literal["36-71", "72-107", "108-120"]
    fallback_activities: list[ParentActivityFallbackDraftV1] = Field(max_length=3)

    @model_validator(mode="after")
    def decision_shape(self) -> ParentActivitySuggestionWorkerResponseV2:
        if self.decision == "CATALOG_MATCH":
            if not 1 <= len(self.selected_candidates) <= 5 or self.fallback_activities:
                raise ValueError("catalog match requires selections and no fallback drafts")
        elif (
            self.selected_candidates
            or len(self.fallback_activities) != 3
            or not self.no_match_reason
        ):
            raise ValueError(
                "no match requires a reason and exactly three fallback drafts"
            )
        if len({item.candidate_ref for item in self.selected_candidates}) != len(
            self.selected_candidates
        ):
            raise ValueError("catalog selections must be unique")
        return self


class ParentSuggestedActivityV2(ParentActivitySuggestionItemV1):
    source: Literal["PINNED_LESSON", "PUBLISHED_SHARED_LESSON", "AI_GENERATED_DRAFT"]
    source_lesson_id: str | None = None
    source_lesson_title: str | None = None
    source_lesson_version_id: str | None = None
    source_content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_activity_index: int | None = Field(default=None, ge=0, le=23)
    match_reason: str | None = Field(default=None, max_length=180)


class ParentActivitySuggestionResponseV2(StrictRequest):
    contract: Literal["ParentActivitySuggestionResponseV2"] = "ParentActivitySuggestionResponseV2"
    request_id: UUID
    story_run_id: UUID
    understanding_revision: int = Field(ge=1)
    selection_mode: Literal["CATALOG_SELECTION", "AI_GENERATED_FALLBACK"]
    catalog_candidate_count: int = Field(ge=0, le=12)
    review_required: Literal[True]
    modal_call_id: str | None = Field(default=None, max_length=128)
    activities: list[ParentSuggestedActivityV2] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def response_shape(self) -> ParentActivitySuggestionResponseV2:
        if self.selection_mode == "CATALOG_SELECTION":
            if any(item.source == "AI_GENERATED_DRAFT" for item in self.activities):
                raise ValueError("catalog selection cannot contain generated drafts")
        elif len(self.activities) != 3 or any(
            item.source != "AI_GENERATED_DRAFT" for item in self.activities
        ):
            raise ValueError("fallback must contain exactly three generated drafts")
        return self


class TeacherLessonSuggestionRequestV1(StrictRequest):
    topic: str = Field(min_length=1, max_length=120)
    target_age_months: int = Field(ge=36, le=120)
    objectives: list[str] = Field(min_length=1, max_length=4)
    drawing_subject: str = Field(min_length=1, max_length=160)
    activity_count: int = Field(ge=1, le=6)
    activity_kind: Literal["outdoor", "indoor", "mixed"]
    script_following_allowed: bool = False
    script_direction: str | None = Field(default=None, max_length=2000)


class TeacherDrawingStepV1(StrictRequest):
    action: str = Field(min_length=1, max_length=240)
    placement: str = Field(min_length=1, max_length=240)


class TeacherActivityV1(StrictRequest):
    activity_ref: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    title: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=200)
    materials: str = Field(min_length=1, max_length=500)
    preparation: str = Field(min_length=1, max_length=500)
    instructions: str = Field(min_length=1, max_length=1200)
    safety_notes: str = Field(min_length=1, max_length=500)


class TeacherReviewedPlanRequestV1(StrictRequest):
    review_confirmed: Literal[True]
    plan_revision_ref: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    topic: str = Field(min_length=1, max_length=120)
    target_age_months: int = Field(ge=36, le=120)
    objectives: list[str] = Field(min_length=1, max_length=4)
    drawing_steps: list[TeacherDrawingStepV1] = Field(min_length=3, max_length=5)
    subject_knowledge: list[str] = Field(min_length=1, max_length=8)
    activities: list[TeacherActivityV1] = Field(min_length=1, max_length=6)


__all__ = [
    "ParentActivitySuggestionItemV1",
    "ParentActivitySuggestionRequestV1",
    "ParentActivitySuggestionResponseV1",
    "ParentActivityCatalogCandidateV2",
    "ParentActivityCandidateSelectionV2",
    "ParentActivitySuggestionResponseV2",
    "ParentActivitySuggestionWorkerRequestV3",
    "ParentActivitySuggestionWorkerResponseV2",
    "ParentSuggestedActivityV2",
    "ParentDrawingAnalysisRequestV1",
    "ParentSketchGuideRequestV1",
    "ParentStoryRequestV1",
    "TeacherLessonSuggestionRequestV1",
    "TeacherReviewedPlanRequestV1",
]
