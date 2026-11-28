"""Versioned read contracts for the Teacher workspace."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictTeacherWorkspaceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TeacherProfileV1(StrictTeacherWorkspaceModel):
    contract: Literal["TeacherProfileV1"] = "TeacherProfileV1"
    account_ref: str
    display_name: str | None
    email: str | None


class TeacherActivityV1(StrictTeacherWorkspaceModel):
    lesson_id: str
    version_id: str
    version_no: int
    content_sha256: str
    lesson_title: str
    lesson_topic: str
    lesson_activity_id: str
    activity_order: int
    title: str
    objective: str
    activity_kind: Literal["outdoor", "indoor", "mixed"]
    materials_text: str
    preparation_text: str
    instructions_text: str
    observation_notes: str
    safety_notes: str


class TeacherActivityPageV1(StrictTeacherWorkspaceModel):
    contract: Literal["TeacherActivityPageV1"] = "TeacherActivityPageV1"
    items: list[TeacherActivityV1]
    next_cursor: str | None
