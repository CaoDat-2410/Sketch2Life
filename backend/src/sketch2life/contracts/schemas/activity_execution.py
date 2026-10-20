"""Owned DATA-29/CMD-45 candidates, not adopted policy or BE1 portfolio schemas."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.knowledge_video import VideoExactRef


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ActivityReference(Strict):
    activity_id: OpaqueId
    version: int = Field(ge=1, le=2**63 - 1)
    hash: Sha256Hex


class AudienceScope(Strict):
    session_id: OpaqueId
    group_ids: tuple[OpaqueId, ...] = Field(max_length=64)


class TeacherAdaptations(Strict):
    instructions: str | None = Field(default=None, min_length=1, max_length=2000)
    materials: tuple[str, ...] | None = Field(default=None, max_length=64)
    duration_note: str | None = Field(default=None, min_length=1, max_length=2000)
    safety_note: str | None = Field(default=None, min_length=1, max_length=2000)


class FeasibilityConfirmation(Strict):
    materials_available: bool
    safety_checked: bool
    note: str | None = Field(default=None, min_length=1, max_length=200)


class ActivityCommand(Strict):
    action: Literal["select", "confirm_ready", "start", "finish", "skip", "interrupt"]
    assignment_id: OpaqueId | None = None
    activity_ref: ActivityReference | None = None
    audience_scope: AudienceScope | None = None
    teacher_adaptations: TeacherAdaptations | None = None
    feasibility_confirmation: FeasibilityConfirmation | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=200)
    evidence_refs: tuple[VideoExactRef, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def closed_action(self) -> "ActivityCommand":
        if self.action == "select":
            if (
                self.activity_ref is None
                or self.audience_scope is None
                or (
                    self.feasibility_confirmation is not None
                    or self.reason is not None
                    or self.evidence_refs
                )
            ):
                raise ValueError("invalid select")
        elif (
            self.assignment_id is None
            or self.activity_ref is not None
            or (self.audience_scope is not None or self.teacher_adaptations is not None)
        ):
            raise ValueError("invalid existing command")
        if self.action in {"confirm_ready", "start"}:
            if (
                self.feasibility_confirmation is None
                or self.reason is not None
                or self.evidence_refs
            ):
                raise ValueError("preparation required")
        elif self.feasibility_confirmation is not None:
            raise ValueError("unexpected confirmation")
        if self.action in {"skip", "interrupt"} and (
            self.reason is None or not self.reason.strip()
        ):
            raise ValueError("reason required")
        return self


class EffectiveSnapshot(Strict):
    definition_ref: VideoExactRef
    title: str
    instructions: str
    materials: tuple[str, ...]
    safety: str
    duration_note: str
    form: str
    observation_prompts: tuple[str, ...]


class ActivityAssignmentView(Strict):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    assignment_id: OpaqueId
    assignment_revision: int = Field(ge=1)
    applied_revision: int = Field(ge=1)
    replayed: bool
    organization_id: OpaqueId
    audience_scope: AudienceScope
    learning_objective_refs: tuple[VideoExactRef, ...]
    source_activity_ref: ActivityReference
    effective_activity_snapshot: EffectiveSnapshot
    state: Literal[
        "proposed",
        "teacher_selected",
        "preparation_required",
        "ready",
        "in_progress",
        "completed",
        "skipped",
        "interrupted",
    ]
    selected_by: OpaqueId
    created_at: AwareDatetime
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    invalidation_reason: OpaqueId | None
    outcome_delivery: Literal["not_required", "pending", "acknowledged"]
