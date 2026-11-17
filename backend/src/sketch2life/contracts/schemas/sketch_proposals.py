"""BE2-04 DATA-23 SketchProposal strict candidate contracts (SK1, 0.1-candidate).

New contracts only: the shallow DATA-23 ``ShapeSpec`` in ``ai_contract_candidates`` is not
edited and still accepts these records. The Teacher/internal record, the minimal Child view
and event candidates are separate types. The Child view never carries proposal content.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
LongText = Annotated[str, Field(min_length=1, max_length=4000)]
CandidateVersion = Literal["0.1-candidate"]
PipelineStateV1 = Literal["requested", "analyzing", "pending_teacher_review", "approved",
                          "rejected", "blocked_unsafe", "cancelled", "stale", "failed"]
ReasonCode = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ChildResponseV1(_Strict):
    """DATA-23 child_response shape (written by BE2-06 only; 04 always leaves it null)."""

    action: Literal["available", "viewed", "hidden", "declined"]
    participant_id: OpaqueId
    turn_id: OpaqueId
    responded_at: AwareDatetime


class AnalysisRefV1(_Strict):
    analysis_id: OpaqueId
    analysis_revision: int = Field(ge=1)


class JobRefV1(_Strict):
    job_id: OpaqueId
    attempt_id: OpaqueId


class ProducerRefV1(_Strict):
    adapter_id: OpaqueId
    model_profile_version: OpaqueId
    configuration_version: OpaqueId


class PolicyRefV1(_Strict):
    policy_id: OpaqueId
    version: OpaqueId
    status: OpaqueId


class LevelSourceV1(_Strict):
    kind: Literal["request", "revision"]
    receipt_ref: OpaqueId | None

    @model_validator(mode="after")
    def _consistent(self) -> LevelSourceV1:
        if (self.kind == "revision") != (self.receipt_ref is not None):
            raise ValueError("only a revision level source names its receipt")
        return self


class SketchProposalRecordV1(_Strict):
    """Teacher/internal DATA-23 record (H-AI-REVIEW producer side)."""

    contract_name: Literal["SketchProposalRecord"] = "SketchProposalRecord"
    contract_version: CandidateVersion = "0.1-candidate"
    proposal_id: OpaqueId
    proposal_version: int = Field(ge=1)
    review_revision: int = Field(ge=1)
    assistance_id: OpaqueId
    request_revision: int = Field(ge=1)
    source_snapshot_ref: OpaqueId
    context_revision: int = Field(ge=0)
    assistance_level: OpaqueId
    level_source: LevelSourceV1
    display_mode: Literal["side_reference", "overlay"]
    overlay_asset_ref: OpaqueId | None
    text_or_question: LongText | None
    editable_bounds: None
    moderation_state: Literal["not_applicable", "pending", "passed", "blocked"]
    pipeline_state: PipelineStateV1
    created_at: AwareDatetime
    approval_ref: OpaqueId | None
    child_response: ChildResponseV1 | None
    content_sha256: Sha256Hex | None
    content_withheld_reason: ReasonCode | None
    organization_id: OpaqueId
    session_id: OpaqueId
    canvas_id: OpaqueId
    group_id: OpaqueId | None
    audience_participant_ids: tuple[OpaqueId, ...] = Field(min_length=1, max_length=64)
    analysis_ref: AnalysisRefV1
    handoff_kind: Literal["analysis", "cache_hit"]
    cache_source_assistance_id: OpaqueId | None
    generation_job_ref: JobRefV1 | None
    producer_ref: ProducerRefV1 | None
    generation_evidence_kind: Literal["fixture", "provider"] | None
    policy_ref: PolicyRefV1
    status_reason: ReasonCode | None
    etag: str = Field(min_length=1, max_length=300)
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def _consistent(self) -> SketchProposalRecordV1:
        has_content = self.text_or_question is not None or self.overlay_asset_ref is not None
        if has_content and self.pipeline_state != "pending_teacher_review":
            raise ValueError("content is exposed only while pending Teacher review")
        if has_content and self.content_withheld_reason is not None:
            raise ValueError("withheld content carries no content fields")
        if (self.handoff_kind == "cache_hit") != (self.cache_source_assistance_id is not None):
            raise ValueError("only a cache-hit proposal names its cache source")
        return self


class SketchProposalDeviceViewV1(_Strict):
    """Minimal Child projection: status only, never asset/text/proposal id."""

    contract_name: Literal["SketchProposalDeviceView"] = "SketchProposalDeviceView"
    contract_version: CandidateVersion = "0.1-candidate"
    assistance_id: OpaqueId
    status: Literal["pending", "unavailable"]


class SketchProposalEventV1(_Strict):
    """Audit/domain event candidate; delivery transport is NOT_RUN in SK1."""

    contract_name: Literal["SketchProposalEvent"] = "SketchProposalEvent"
    contract_version: CandidateVersion = "0.1-candidate"
    event_id: OpaqueId
    event_type: Literal[
        "sketch.proposal_requested", "sketch.scheduled", "sketch.proposal_ready",
        "sketch.blocked_unsafe", "sketch.failed", "sketch.cancelled", "sketch.stale",
        "sketch.superseded", "sketch.open_refused", "sketch.cleanup_requested",
    ]
    organization_id: OpaqueId
    proposal_id: OpaqueId | None
    proposal_version: int | None = Field(ge=1)
    assistance_id: OpaqueId
    reason: ReasonCode | None
    occurred_at: AwareDatetime


__all__ = [
    "AnalysisRefV1",
    "ChildResponseV1",
    "JobRefV1",
    "LevelSourceV1",
    "PolicyRefV1",
    "ProducerRefV1",
    "SketchProposalDeviceViewV1",
    "SketchProposalEventV1",
    "SketchProposalRecordV1",
]
