"""HTTP contracts for Teacher Sketch Deck generation and retrieval."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.modal_ai import (
    TeacherDrawingStepV1,
    TeacherKnowledgeNoteV1,
)


class StrictSketchDeckModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateSketchDeckRequestV1(StrictSketchDeckModel):
    expected_plan_revision_id: str = Field(
        min_length=1, max_length=36, pattern=r"^[A-Za-z0-9_-]{1,36}$"
    )
    expected_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_confirmed: Literal[True]
    topic: str = Field(min_length=1, max_length=120)
    drawing_steps: list[TeacherDrawingStepV1] = Field(min_length=4, max_length=8)
    subject_knowledge: list[TeacherKnowledgeNoteV1] = Field(min_length=1, max_length=8)
    teacher_confirmed_age_band_ref: (
        Literal[
            "age-36-71-months-v1",
            "age-72-107-months-v1",
            "age-108-120-months-v1",
            "36-71",
        ]
        | None
    ) = None


class SketchDeckStepV1(StrictSketchDeckModel):
    sketch_deck_step_id: str
    plan_activity_id: str | None
    instruction_group_key: str
    step_index: int
    step_kind: str
    subject_key: str
    short_title: str
    child_facing_prompt: str
    teacher_explanation: str
    bounded_layout_hints: dict[str, Any]
    line_sketch_asset_ref: str | None
    line_sketch_asset_version: int | None
    source_job_ref: str | None
    state: Literal["GENERATING", "READY", "FAILED", "STALE", "SUPERSEDED"]
    created_at: datetime


class SketchDeckRevisionV1(StrictSketchDeckModel):
    contract: Literal["SketchDeckRevisionV1"] = "SketchDeckRevisionV1"
    sketch_deck_revision_id: str
    occurrence_id: str
    plan_revision_id: str
    revision_no: int
    plan_content_hash: str
    review_confirmed: Literal[True]
    topic: str
    drawing_steps: list[TeacherDrawingStepV1]
    subject_knowledge: list[str]
    target_age_band: str
    deck_schema_version: str
    state: Literal["GENERATING", "READY", "FAILED", "STALE", "SUPERSEDED"]
    content_hash: str | None
    created_at: datetime
    ready_at: datetime | None
    superseded_at: datetime | None


class SketchDeckCurrentV1(StrictSketchDeckModel):
    contract: Literal["SketchDeckCurrentV1"] = "SketchDeckCurrentV1"
    occurrence_id: str
    current_revision: SketchDeckRevisionV1 | None
    steps: list[SketchDeckStepV1]
    stale: bool
    presentable: bool


__all__ = [
    "CreateSketchDeckRequestV1",
    "SketchDeckCurrentV1",
    "SketchDeckRevisionV1",
    "SketchDeckStepV1",
]
