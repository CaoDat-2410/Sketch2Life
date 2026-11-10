"""Strict public contracts for the bounded non-video Modal AI workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ParentSketchGuideRequestV1(StrictRequest):
    topic: str = Field(min_length=1, max_length=120)
    difficulty: Literal["beginner", "simple"] = "beginner"
    step_count: int = Field(default=3, ge=3, le=5)


class ParentDrawingAnalysisRequestV1(StrictRequest):
    image_base64: str = Field(min_length=16, max_length=6_700_000)


class ParentStoryRequestV1(StrictRequest):
    confirmed_subject: str = Field(min_length=1, max_length=160)
    visible_features: list[str] = Field(min_length=1, max_length=4)
    child_age_months: int = Field(ge=36, le=120)
    drawing_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    understanding_revision: int = Field(ge=1)
    context_revision: int = Field(ge=1)
    adult_confirmed_idea: str = Field(default="", max_length=500)


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
    "ParentDrawingAnalysisRequestV1",
    "ParentSketchGuideRequestV1",
    "ParentStoryRequestV1",
    "TeacherLessonSuggestionRequestV1",
    "TeacherReviewedPlanRequestV1",
]
