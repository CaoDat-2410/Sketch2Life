"""BE2-03 DATA-21 / CMD-32 / CMD-33 strict candidate contracts (A1, 0.1-candidate).

New contracts only: the shallow DATA-21 ``ShapeSpec`` in ``ai_contract_candidates`` is not
edited and still accepts these command documents. Teacher/internal records and the minimal
Child-device view are separate types; the device view carries no audience, age, consent,
intent, budget, cache, analysis or provider detail.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
LongText = Annotated[str, Field(min_length=1, max_length=4000)]
ShortText = Annotated[str, Field(min_length=1, max_length=128)]
CandidateVersion = Literal["0.1-candidate"]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class CheckpointRefV1(_Strict):
    checkpoint_id: OpaqueId
    document_epoch: int = Field(ge=0)
    server_sequence: int = Field(ge=0)
    hash: Sha256Hex


class IndividualTargetV1(_Strict):
    kind: Literal["individual"]
    participant_id: OpaqueId


class GroupTargetV1(_Strict):
    kind: Literal["group"]
    group_id: OpaqueId


TargetScopeV1 = Annotated[IndividualTargetV1 | GroupTargetV1, Field(discriminator="kind")]


class AssistanceRequestCommandV1(_Strict):
    """CMD-32 body (DATA-21 command). No actor/role/org/status/audience fields exist."""

    canvas_id: OpaqueId
    checkpoint_ref: CheckpointRefV1
    target_scope: TargetScopeV1
    target_region_id: OpaqueId | None = None
    requested_level: OpaqueId
    child_intent: LongText | None = None
    request_reason: Literal["child_request", "teacher_request", "explicit_help_signal"]
    context_revision: int = Field(ge=0)
    client_request_id: OpaqueId


class AssistanceCancelCommandV1(_Strict):
    """CMD-33 body; the revision travels in ``If-Match``, the actor from the principal."""

    reason: ShortText | None = None


class ContributorV1(_Strict):
    participant_id: OpaqueId
    turn_id: OpaqueId | None
    turn_revision: int | None = Field(ge=1)


class RequesterV1(_Strict):
    principal_id: OpaqueId
    role: Literal["teacher", "device"]


class AgeContextRefV1(_Strict):
    participant_id: OpaqueId
    age_provenance_ref: OpaqueId
    age_revision: int = Field(ge=1)


class ConsentRevisionRefV1(_Strict):
    participant_id: OpaqueId
    consent_record_ref: OpaqueId
    revision: int = Field(ge=1)


class PolicyRefV1(_Strict):
    policy_id: OpaqueId
    version: OpaqueId
    status: OpaqueId


class CacheHitV1(_Strict):
    assistance_id: OpaqueId
    request_revision: int = Field(ge=1)
    job_id: OpaqueId
    analysis_id: OpaqueId
    analysis_revision: int = Field(ge=1)


class BudgetReservationV1(_Strict):
    reservation_id: OpaqueId
    state: Literal["held", "consumed", "released"]


class AssistanceRequestRecordV1(_Strict):
    """Teacher/internal DATA-21 response (H-AI-REVIEW request status/context/target)."""

    contract_name: Literal["AssistanceRequestRecord"] = "AssistanceRequestRecord"
    contract_version: CandidateVersion = "0.1-candidate"
    assistance_id: OpaqueId
    request_revision: int = Field(ge=1)
    organization_id: OpaqueId
    session_id: OpaqueId
    group_id: OpaqueId | None
    canvas_id: OpaqueId
    checkpoint_ref: CheckpointRefV1
    validated_target_scope: TargetScopeV1
    target_region_id: OpaqueId | None
    requested_level: OpaqueId
    request_reason: Literal["child_request", "teacher_request", "explicit_help_signal"]
    requester_principal: RequesterV1
    contributor_snapshot: ContributorV1
    age_policy_ref: OpaqueId
    audience_age_context_refs: tuple[AgeContextRefV1, ...] = Field(min_length=1, max_length=64)
    consent_revision_refs: tuple[ConsentRevisionRefV1, ...] = Field(min_length=1, max_length=64)
    purpose_code: OpaqueId
    context_revision: int = Field(ge=0)
    input_hash: Sha256Hex
    assistance_context_digest: Sha256Hex
    policy_ref: PolicyRefV1
    status: Literal["scheduling", "scheduled", "analysis_ready", "failed", "cancelled", "stale"]
    status_reason: OpaqueId | None
    job_id: OpaqueId | None
    budget_reservation: BudgetReservationV1 | None
    cache_hit_of: CacheHitV1 | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AssistanceRequestDeviceViewV1(_Strict):
    contract_name: Literal["AssistanceRequestDeviceView"] = "AssistanceRequestDeviceView"
    contract_version: CandidateVersion = "0.1-candidate"
    assistance_id: OpaqueId
    request_revision: int = Field(ge=1)
    status: Literal["pending", "cancelled", "unavailable"]
    job_id: OpaqueId | None
    poll_after_ms: int | None = Field(ge=0)


class ReceiptMetaV1(_Strict):
    outcome: Literal["created", "deduplicated", "cache_hit", "cancelled"]
    replayed: bool
    resource_revision: int = Field(ge=1)
    projection: Literal["teacher", "device"]


class AssistanceReceiptEnvelopeV1(_Strict):
    contract_name: Literal["AssistanceReceipt"] = "AssistanceReceipt"
    contract_version: CandidateVersion = "0.1-candidate"
    correlation_id: OpaqueId
    data: AssistanceRequestRecordV1 | AssistanceRequestDeviceViewV1
    meta: ReceiptMetaV1


class AssistanceEventV1(_Strict):
    """Audit/domain event candidate; delivery transport is NOT_RUN in A1."""

    contract_name: Literal["AssistanceEvent"] = "AssistanceEvent"
    contract_version: CandidateVersion = "0.1-candidate"
    event_id: OpaqueId
    event_type: Literal[
        "assistance.requested", "assistance.deduplicated", "assistance.refused",
        "assistance.scheduled", "assistance.cancelled", "assistance.stale",
        "assistance.superseded", "assistance.failed", "assistance.analysis_ready",
        "assistance.sketch_intent_simulated", "assistance.cleanup_settled",
    ]
    organization_id: OpaqueId
    assistance_id: OpaqueId | None
    request_revision: int | None = Field(ge=1)
    reason: OpaqueId | None
    occurred_at: AwareDatetime


__all__ = [
    "AgeContextRefV1",
    "AssistanceCancelCommandV1",
    "AssistanceEventV1",
    "AssistanceReceiptEnvelopeV1",
    "AssistanceRequestCommandV1",
    "AssistanceRequestDeviceViewV1",
    "AssistanceRequestRecordV1",
    "BudgetReservationV1",
    "CacheHitV1",
    "CheckpointRefV1",
    "ConsentRevisionRefV1",
    "ContributorV1",
    "GroupTargetV1",
    "IndividualTargetV1",
    "PolicyRefV1",
    "ReceiptMetaV1",
    "RequesterV1",
    "TargetScopeV1",
]
