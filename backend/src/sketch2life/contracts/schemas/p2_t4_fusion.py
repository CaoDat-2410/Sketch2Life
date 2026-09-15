"""P2-T4 offline fusion contracts: `P2T4.P2T4FusedResultV1@1.0`.

Frozen G1 contract (freeze commit 18d0c33d35431ca96a76692a68c6b992098699e7). Every model is
strict, frozen, `extra="forbid"`, carries no arbitrary map, and never contains raw transcript
text, media, provider payloads, prompts, credentials, endpoints, or absolute paths. This module
also pins the `P2T4-CANONICAL-JSON-V1` projection used for source-result digests, the
fusion-policy hash, and conflict identifiers.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sketch2life.contracts.schemas.asr import AsrErrorCode, AsrErrorDetail
from sketch2life.contracts.schemas.vision import (
    ObservedTextV1,
    VisionErrorCode,
    VisionFailureDetail,
)

P2T4_CANONICAL_JSON_IDENTITY: Final = "P2T4-CANONICAL-JSON-V1"
P2T4_FUSED_RESULT_IDENTITY: Final = "P2T4.P2T4FusedResultV1@1.0"
P2T4_INPUT_REJECTION_IDENTITY: Final = "P2T4.P2T4FusionInputRejectionV1@1.0"
P2T4_CONFLICT_ID_PREFIX: Final = "P2T4-CONFLICT-"
P2T4_NEGATION_CUES: Final[tuple[tuple[str, ...], ...]] = (
    ("not",),
    ("no",),
    ("never",),
    ("isn", "t"),
    ("doesn", "t"),
    ("didn", "t"),
)

_ObservationId = Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
_Sha256Hex = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
_ConflictId = Annotated[str, Field(pattern=r"^P2T4-CONFLICT-[a-f0-9]{64}$")]
_UnitInterval = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
_AttemptNumber = Annotated[int, Field(ge=0, le=2)]


# --- closed vocabularies -------------------------------------------------------------------


class P2T4FusedResultStatus(StrEnum):
    FUSED = "FUSED"
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"


class P2T4SourceIdentity(StrEnum):
    P2_ASR_RESULT_V1 = "P2.AsrResultV1@1.0"
    P2_VISION_UNDERSTANDING_RESULT_V1 = "P2.VisionUnderstandingResultV1@1.0"


class P2T4InputSlot(StrEnum):
    ASR = "ASR"
    VISION = "VISION"
    BOTH = "BOTH"


class P2T4RejectionPhase(StrEnum):
    IDENTITY_VERSION = "IDENTITY_VERSION"
    STRICT_VALIDATION = "STRICT_VALIDATION"
    ADMISSIBILITY = "ADMISSIBILITY"
    CORRELATION = "CORRELATION"


class P2T4RejectionCode(StrEnum):
    UNKNOWN_INPUT = "UNKNOWN_INPUT"
    WRONG_FAMILY = "WRONG_FAMILY"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    INVALID_DISCRIMINATOR = "INVALID_DISCRIMINATOR"
    INVALID_STRUCTURE = "INVALID_STRUCTURE"
    CORRELATION_MISMATCH = "CORRELATION_MISMATCH"


class P2T4ExpectedIdentity(StrEnum):
    NONE = "NONE"
    P2_ASR_RESULT_V1 = "P2.AsrResultV1@1.0"
    P2_VISION_UNDERSTANDING_RESULT_V1 = "P2.VisionUnderstandingResultV1@1.0"


class P2T4ObservedIdentity(StrEnum):
    UNKNOWN = "UNKNOWN"
    P2_ASR_RESULT_V1 = "P2.AsrResultV1@1.0"
    P2_VISION_UNDERSTANDING_RESULT_V1 = "P2.VisionUnderstandingResultV1@1.0"
    FEAT018_LIVE_ASR_RESULT_V1 = "FEAT018.LiveAsrResultV1@1.0"
    FEAT018_LIVE_VISION_UNDERSTANDING_RESULT_V1 = "FEAT018.LiveVisionUnderstandingResultV1@1.0"
    P2_VISION_UNDERSTANDING_RESULT_V2 = "P2.VisionUnderstandingResultV2@2.0"


class P2T4ObservedStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class P2T4RejectionFieldCode(StrEnum):
    NONE = "NONE"
    CONTRACT_NAME = "CONTRACT_NAME"
    CONTRACT_VERSION = "CONTRACT_VERSION"
    STATUS = "STATUS"
    CORRELATION_ID = "CORRELATION_ID"
    SOURCE_REFERENCE = "SOURCE_REFERENCE"
    FAILURE_BRANCH = "FAILURE_BRANCH"
    UPSTREAM_TYPE = "UPSTREAM_TYPE"
    DUPLICATE_SEGMENT_INDEX = "DUPLICATE_SEGMENT_INDEX"


class P2T4FailedModality(StrEnum):
    ASR = "ASR"
    VISION = "VISION"
    BOTH = "BOTH"


class P2T4ConflictReasonCode(StrEnum):
    ENTITY_ATTRIBUTE_CONTRADICTION = "ENTITY_ATTRIBUTE_CONTRADICTION"
    ACTION_CONTRADICTION = "ACTION_CONTRADICTION"
    RELATION_CONTRADICTION = "RELATION_CONTRADICTION"
    LOW_CONFIDENCE_EVIDENCE = "LOW_CONFIDENCE_EVIDENCE"


class P2T4CandidateKind(StrEnum):
    ENTITY = "ENTITY"
    ACTION = "ACTION"
    RELATION = "RELATION"


class P2T4CertaintyStatus(StrEnum):
    MEASURED = "MEASURED"
    NOT_MEASURED = "NOT_MEASURED"
    NOT_APPLICABLE_CONFLICTING = "NOT_APPLICABLE_CONFLICTING"


_PHASE_CODES: Final[dict[P2T4RejectionPhase, frozenset[P2T4RejectionCode]]] = {
    P2T4RejectionPhase.IDENTITY_VERSION: frozenset(
        {
            P2T4RejectionCode.UNKNOWN_INPUT,
            P2T4RejectionCode.WRONG_FAMILY,
            P2T4RejectionCode.UNSUPPORTED_VERSION,
        }
    ),
    P2T4RejectionPhase.STRICT_VALIDATION: frozenset(
        {P2T4RejectionCode.INVALID_DISCRIMINATOR, P2T4RejectionCode.INVALID_STRUCTURE}
    ),
    P2T4RejectionPhase.ADMISSIBILITY: frozenset({P2T4RejectionCode.INVALID_STRUCTURE}),
    P2T4RejectionPhase.CORRELATION: frozenset({P2T4RejectionCode.CORRELATION_MISMATCH}),
}

CANDIDATE_KIND_RANK: Final[dict[P2T4CandidateKind, int]] = {
    P2T4CandidateKind.ENTITY: 0,
    P2T4CandidateKind.ACTION: 1,
    P2T4CandidateKind.RELATION: 2,
}

CONFLICT_REASON_RANK: Final[dict[P2T4ConflictReasonCode, int]] = {
    P2T4ConflictReasonCode.ENTITY_ATTRIBUTE_CONTRADICTION: 0,
    P2T4ConflictReasonCode.ACTION_CONTRADICTION: 1,
    P2T4ConflictReasonCode.RELATION_CONTRADICTION: 2,
    P2T4ConflictReasonCode.LOW_CONFIDENCE_EVIDENCE: 3,
}


# --- safe typed input rejection ------------------------------------------------------------


class P2T4FusionInputRejectionV1(BaseModel):
    """Terminal, closed-vocabulary rejection. Never a `P2T4FusedResultV1` status."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["P2T4FusionInputRejectionV1"] = "P2T4FusionInputRejectionV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["REJECTED"] = "REJECTED"
    input_slot: P2T4InputSlot
    phase: P2T4RejectionPhase
    code: P2T4RejectionCode
    expected_identity: P2T4ExpectedIdentity
    observed_identity: P2T4ObservedIdentity
    observed_status: P2T4ObservedStatus | None
    field_code: P2T4RejectionFieldCode

    @model_validator(mode="after")
    def _requires_closed_consistency(self) -> P2T4FusionInputRejectionV1:
        if self.code not in _PHASE_CODES[self.phase]:
            raise ValueError("rejection code is not valid for its phase")
        if self.input_slot is P2T4InputSlot.BOTH or self.phase is P2T4RejectionPhase.CORRELATION:
            if (
                self.input_slot is not P2T4InputSlot.BOTH
                or self.phase is not P2T4RejectionPhase.CORRELATION
                or self.expected_identity is not P2T4ExpectedIdentity.NONE
                or self.field_code is not P2T4RejectionFieldCode.CORRELATION_ID
            ):
                raise ValueError("BOTH is only valid for a correlation mismatch")
            return self
        expected = (
            P2T4ExpectedIdentity.P2_ASR_RESULT_V1
            if self.input_slot is P2T4InputSlot.ASR
            else P2T4ExpectedIdentity.P2_VISION_UNDERSTANDING_RESULT_V1
        )
        if self.expected_identity is not expected:
            raise ValueError("expected identity must match the rejected input slot")
        is_admissibility = self.phase is P2T4RejectionPhase.ADMISSIBILITY
        is_duplicate = self.field_code is P2T4RejectionFieldCode.DUPLICATE_SEGMENT_INDEX
        if (is_admissibility or is_duplicate) and (
            not (is_admissibility and is_duplicate)
            or self.input_slot is not P2T4InputSlot.ASR
            or self.observed_identity is not P2T4ObservedIdentity.P2_ASR_RESULT_V1
            or self.observed_status is not P2T4ObservedStatus.SUCCEEDED
        ):
            raise ValueError("admissibility rejection must be the exact duplicate-index form")
        return self


# --- references, policy, and failure references --------------------------------------------


class P2T4SourceResultRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: P2T4SourceIdentity
    status: Literal["SUCCEEDED", "FAILED"]
    result_sha256: _Sha256Hex


class P2T4NarrationClaimRefV1(BaseModel):
    """Canonical coordinate `(segment_index, claim_start, claim_end)`; never carries text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    segment_index: int = Field(ge=0)
    claim_start: int = Field(ge=0)
    claim_end: int = Field(ge=1)

    @model_validator(mode="after")
    def _requires_exclusive_end_after_start(self) -> P2T4NarrationClaimRefV1:
        if self.claim_end <= self.claim_start:
            raise ValueError("claim_end must be greater than claim_start")
        return self

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.segment_index, self.claim_start, self.claim_end)


class P2T4FusionPolicyConfigV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["P2T4FusionPolicyConfigV1"] = "P2T4FusionPolicyConfigV1"
    contract_version: Literal["1.0"] = "1.0"
    config_version: str = Field(min_length=1)
    entity_match_mode: Literal["WHOLE_TOKEN_SEQUENCE"] = "WHOLE_TOKEN_SEQUENCE"
    narration_weight_mode: Literal["SUPPORT_ONLY"] = "SUPPORT_ONLY"
    confidence_floor: _UnitInterval
    uncertainty_formula_id: Literal["AGREEMENT_WEIGHTED_V1"] = "AGREEMENT_WEIGHTED_V1"
    match_view_version: Literal["vision_policy_match_view-v2"] = "vision_policy_match_view-v2"
    negation_cues: tuple[tuple[str, ...], ...] = P2T4_NEGATION_CUES
    negation_window_tokens: Literal[3] = 3
    corroboration_increment: Literal["0.10"] = "0.10"

    @field_validator("negation_cues")
    @classmethod
    def _requires_frozen_cue_sequences(
        cls, value: tuple[tuple[str, ...], ...]
    ) -> tuple[tuple[str, ...], ...]:
        if value != P2T4_NEGATION_CUES:
            raise ValueError("negation_cues must be exactly the frozen cue sequences")
        return value

    def corroboration_increment_decimal(self) -> Decimal:
        """The only approved arithmetic conversion; never routed through a binary float."""

        return Decimal(self.corroboration_increment)


class P2T4AsrFailureReferenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_asr_result_ref: P2T4SourceResultRefV1
    error_code: AsrErrorCode
    error_detail: AsrErrorDetail
    attempt_number: _AttemptNumber
    retryable: bool
    repair_attempted: bool

    @model_validator(mode="after")
    def _requires_failed_asr_source(self) -> P2T4AsrFailureReferenceV1:
        ref = self.source_asr_result_ref
        if ref.identity is not P2T4SourceIdentity.P2_ASR_RESULT_V1 or ref.status != "FAILED":
            raise ValueError("ASR failure reference requires a FAILED P2 ASR source ref")
        return self


class P2T4VisionFailureReferenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_vision_result_ref: P2T4SourceResultRefV1
    error_code: VisionErrorCode
    error_detail: VisionFailureDetail
    attempt_number: _AttemptNumber
    retryable: bool
    repair_attempted: bool
    policy_execution_state: Literal["NOT_EXECUTED", "BLOCKED"]

    @model_validator(mode="after")
    def _requires_failed_vision_source(self) -> P2T4VisionFailureReferenceV1:
        ref = self.source_vision_result_ref
        if (
            ref.identity is not P2T4SourceIdentity.P2_VISION_UNDERSTANDING_RESULT_V1
            or ref.status != "FAILED"
        ):
            raise ValueError("Vision failure reference requires a FAILED P2 Vision source ref")
        return self


class P2T4UpstreamFailureRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["P2T4UpstreamFailureRefV1"] = "P2T4UpstreamFailureRefV1"
    contract_version: Literal["1.0"] = "1.0"
    failed_modality: P2T4FailedModality
    asr_failure_ref: P2T4AsrFailureReferenceV1 | None
    vision_failure_ref: P2T4VisionFailureReferenceV1 | None

    @model_validator(mode="after")
    def _requires_structurally_matching_references(self) -> P2T4UpstreamFailureRefV1:
        needs_asr = self.failed_modality in (P2T4FailedModality.ASR, P2T4FailedModality.BOTH)
        needs_vision = self.failed_modality in (
            P2T4FailedModality.VISION,
            P2T4FailedModality.BOTH,
        )
        if (self.asr_failure_ref is not None) is not needs_asr:
            raise ValueError("asr_failure_ref must be present exactly for ASR or BOTH")
        if (self.vision_failure_ref is not None) is not needs_vision:
            raise ValueError("vision_failure_ref must be present exactly for VISION or BOTH")
        return self


# --- fused observations ------------------------------------------------------------------


class _FusedObservationBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fused_observation_id: _ObservationId
    source_observation_ref: _ObservationId

    @model_validator(mode="after")
    def _requires_identity_equality(self) -> _FusedObservationBase:
        if self.fused_observation_id != self.source_observation_ref:
            raise ValueError("fused_observation_id must equal source_observation_ref")
        return self


class _NarratedObservationBase(_FusedObservationBase):
    narration_support_applied: bool
    narration_support_ref: P2T4NarrationClaimRefV1 | None
    primary_interpretation: bool

    @model_validator(mode="after")
    def _requires_support_flag_matches_reference(self) -> _NarratedObservationBase:
        if self.narration_support_applied is not (self.narration_support_ref is not None):
            raise ValueError("narration_support_applied must be true iff a support ref exists")
        return self


class P2T4FusedEntityV1(_NarratedObservationBase):
    label: ObservedTextV1


class P2T4FusedActionV1(_NarratedObservationBase):
    label: ObservedTextV1
    actor_ref: _ObservationId | None
    object_ref: _ObservationId | None


class P2T4FusedRelationV1(_NarratedObservationBase):
    predicate: ObservedTextV1
    subject_ref: _ObservationId
    object_ref: _ObservationId

    @model_validator(mode="after")
    def _forbids_self_reference(self) -> P2T4FusedRelationV1:
        if self.subject_ref == self.object_ref:
            raise ValueError("relation subject_ref must differ from object_ref")
        return self


class P2T4FusedThemeV1(_FusedObservationBase):
    label: ObservedTextV1
    evidence_refs: tuple[_ObservationId, ...] = Field(min_length=1)


# --- conflicts and uncertainty -----------------------------------------------------------


class P2T4ConflictV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conflict_id: _ConflictId
    reason_code: P2T4ConflictReasonCode
    vision_claim_ref: _ObservationId
    narration_claim_ref: P2T4NarrationClaimRefV1 | None
    recommended_reviewer_attention: Literal[True]

    @model_validator(mode="after")
    def _requires_canonical_identifier_and_reference(self) -> P2T4ConflictV1:
        if self.conflict_id != conflict_id_for(self.reason_code, self.vision_claim_ref):
            raise ValueError("conflict_id does not match the canonical conflict-ID algorithm")
        if (
            self.reason_code is not P2T4ConflictReasonCode.LOW_CONFIDENCE_EVIDENCE
            and self.narration_claim_ref is None
        ):
            raise ValueError("a contradiction requires a canonical refuting claim reference")
        return self

    def sort_key(self) -> tuple[int, str, tuple[int, int, int, int], str]:
        ref = self.narration_claim_ref
        ref_key = (0, 0, 0, 0) if ref is None else (1, *ref.as_tuple())
        return (
            CONFLICT_REASON_RANK[self.reason_code],
            self.vision_claim_ref,
            ref_key,
            self.conflict_id,
        )


class P2T4ObservationUncertaintyV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationId
    candidate_kind: P2T4CandidateKind
    certainty_status: P2T4CertaintyStatus
    certainty: _UnitInterval | None

    @model_validator(mode="after")
    def _requires_certainty_only_when_measured(self) -> P2T4ObservationUncertaintyV1:
        measured = self.certainty_status is P2T4CertaintyStatus.MEASURED
        if measured is not (self.certainty is not None):
            raise ValueError("certainty must be non-null exactly for MEASURED")
        return self

    def sort_key(self) -> tuple[int, str]:
        return (CANDIDATE_KIND_RANK[self.candidate_kind], self.observation_id)


class P2T4UncertaintySummaryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    formula_id: Literal["AGREEMENT_WEIGHTED_V1"] = "AGREEMENT_WEIGHTED_V1"
    per_observation: tuple[P2T4ObservationUncertaintyV1, ...]

    @model_validator(mode="after")
    def _requires_canonical_order(self) -> P2T4UncertaintySummaryV1:
        keys = [row.sort_key() for row in self.per_observation]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise ValueError("per_observation must be uniquely sorted by (kind rank, id)")
        return self


# --- fused result ------------------------------------------------------------------------


_CONTRADICTION_KIND: Final[dict[P2T4ConflictReasonCode, str]] = {
    P2T4ConflictReasonCode.ENTITY_ATTRIBUTE_CONTRADICTION: "ENTITY",
    P2T4ConflictReasonCode.ACTION_CONTRADICTION: "ACTION",
    P2T4ConflictReasonCode.RELATION_CONTRADICTION: "RELATION",
}


class P2T4FusedResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["P2T4FusedResultV1"] = "P2T4FusedResultV1"
    contract_version: Literal["1.0"] = "1.0"
    status: P2T4FusedResultStatus
    correlation_id: str = Field(min_length=1)
    executed_at: datetime
    source_asr_result_ref: P2T4SourceResultRefV1
    source_vision_result_ref: P2T4SourceResultRefV1
    fusion_policy_config_hash: _Sha256Hex
    entities: tuple[P2T4FusedEntityV1, ...]
    actions: tuple[P2T4FusedActionV1, ...]
    relations: tuple[P2T4FusedRelationV1, ...]
    themes: tuple[P2T4FusedThemeV1, ...]
    conflicts: tuple[P2T4ConflictV1, ...]
    uncertainty: P2T4UncertaintySummaryV1
    upstream_failure: P2T4UpstreamFailureRefV1 | None

    @field_validator("executed_at")
    @classmethod
    def _requires_timezone_aware_execution_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("executed_at must be timezone aware")
        return value

    @model_validator(mode="after")
    def _requires_source_slots(self) -> P2T4FusedResultV1:
        if self.source_asr_result_ref.identity is not P2T4SourceIdentity.P2_ASR_RESULT_V1:
            raise ValueError("source_asr_result_ref must carry the P2 ASR identity")
        if (
            self.source_vision_result_ref.identity
            is not P2T4SourceIdentity.P2_VISION_UNDERSTANDING_RESULT_V1
        ):
            raise ValueError("source_vision_result_ref must carry the P2 Vision identity")
        return self

    @model_validator(mode="after")
    def _requires_status_shape(self) -> P2T4FusedResultV1:
        asr_failed = self.source_asr_result_ref.status == "FAILED"
        vision_failed = self.source_vision_result_ref.status == "FAILED"
        if self.status is P2T4FusedResultStatus.FUSED:
            if self.upstream_failure is not None:
                raise ValueError("FUSED requires upstream_failure=null")
            if asr_failed or vision_failed:
                raise ValueError("FUSED requires both source results to be SUCCEEDED")
            return self
        failure = self.upstream_failure
        if failure is None:
            raise ValueError("UPSTREAM_FAILURE requires a non-null upstream_failure")
        if (
            self.entities
            or self.actions
            or self.relations
            or self.themes
            or self.conflicts
            or self.uncertainty.per_observation
        ):
            raise ValueError("UPSTREAM_FAILURE requires empty fused collections")
        expected_modality = {
            (True, False): P2T4FailedModality.ASR,
            (False, True): P2T4FailedModality.VISION,
            (True, True): P2T4FailedModality.BOTH,
        }.get((asr_failed, vision_failed))
        if expected_modality is None or failure.failed_modality is not expected_modality:
            raise ValueError("failed_modality must match the failed source result statuses")
        if (
            failure.asr_failure_ref is not None
            and failure.asr_failure_ref.source_asr_result_ref != self.source_asr_result_ref
        ):
            raise ValueError("asr_failure_ref must reference the top-level ASR source ref")
        if (
            failure.vision_failure_ref is not None
            and failure.vision_failure_ref.source_vision_result_ref != self.source_vision_result_ref
        ):
            raise ValueError("vision_failure_ref must reference the top-level Vision source ref")
        return self

    @model_validator(mode="after")
    def _requires_reference_integrity(self) -> P2T4FusedResultV1:
        kind_by_id: dict[str, str] = {}

        def register(observation_id: str, kind: str) -> None:
            if observation_id in kind_by_id:
                raise ValueError("fused observation IDs must be unique across collections")
            kind_by_id[observation_id] = kind

        for entity in self.entities:
            register(entity.fused_observation_id, "ENTITY")
        for action in self.actions:
            register(action.fused_observation_id, "ACTION")
        for relation in self.relations:
            register(relation.fused_observation_id, "RELATION")
        for theme in self.themes:
            register(theme.fused_observation_id, "THEME")

        def require(ref: str, allowed: frozenset[str]) -> None:
            if kind_by_id.get(ref) not in allowed:
                raise ValueError("fused reference does not resolve to an allowed observation")

        entity_only = frozenset({"ENTITY"})
        entity_or_action = frozenset({"ENTITY", "ACTION"})
        evidence_kinds = frozenset({"ENTITY", "ACTION", "RELATION"})
        for action in self.actions:
            if action.actor_ref is not None:
                require(action.actor_ref, entity_only)
            if action.object_ref is not None:
                require(action.object_ref, entity_only)
        for relation in self.relations:
            require(relation.subject_ref, entity_or_action)
            require(relation.object_ref, entity_or_action)
        for theme in self.themes:
            for ref in theme.evidence_refs:
                require(ref, evidence_kinds)

        narrated_ids = {
            observation_id for observation_id, kind in kind_by_id.items() if kind in evidence_kinds
        }
        rows = {row.observation_id: row for row in self.uncertainty.per_observation}
        if set(rows) != narrated_ids:
            raise ValueError("uncertainty rows must cover exactly every entity/action/relation")
        for observation_id, row in rows.items():
            if row.candidate_kind.value != kind_by_id[observation_id]:
                raise ValueError("uncertainty candidate_kind must match the fused observation")

        conflicting: set[str] = set()
        seen_conflict_ids: set[str] = set()
        for conflict in self.conflicts:
            if conflict.conflict_id in seen_conflict_ids:
                raise ValueError("conflict IDs must be unique")
            seen_conflict_ids.add(conflict.conflict_id)
            kind = kind_by_id.get(conflict.vision_claim_ref)
            if kind is None:
                raise ValueError("conflict vision_claim_ref must resolve to a fused observation")
            required_kind = _CONTRADICTION_KIND.get(conflict.reason_code)
            if required_kind is not None and kind != required_kind:
                raise ValueError("contradiction reason_code must match the candidate kind")
            conflicting.add(conflict.vision_claim_ref)
        keys = [conflict.sort_key() for conflict in self.conflicts]
        if keys != sorted(keys):
            raise ValueError("conflicts must be in canonical order")

        narrated: list[_NarratedObservationBase] = [
            *self.entities,
            *self.actions,
            *self.relations,
        ]
        for observation in narrated:
            observation_id = observation.fused_observation_id
            is_conflicting = observation_id in conflicting
            if is_conflicting and observation.primary_interpretation:
                raise ValueError("a conflicting candidate cannot be primary")
            row = rows[observation_id]
            not_applicable = row.certainty_status is P2T4CertaintyStatus.NOT_APPLICABLE_CONFLICTING
            if is_conflicting is not not_applicable:
                raise ValueError("NOT_APPLICABLE_CONFLICTING must be used exactly for conflicts")
        return self


# --- canonical projection, digests, and conflict identifiers ------------------------------


def _normalize(value: object) -> object:
    if isinstance(value, BaseModel):
        return _normalize(
            value.model_dump(mode="python", by_alias=False, exclude_none=False, exclude_unset=False)
        )
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, Enum):
        return _normalize(value.value)
    if isinstance(value, str | int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical projection forbids non-finite floats")
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("canonical projection requires timezone-aware datetimes")
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("canonical projection requires string object keys")
            normalized[key] = _normalize(item)
        return normalized
    if isinstance(value, Decimal):
        raise ValueError("canonical projection forbids Decimal values")
    raise TypeError("canonical projection forbids bytes and arbitrary objects")


def canonical_projection(model: BaseModel) -> dict[str, object]:
    """`P2T4-CANONICAL-JSON-V1` projection of a validated model (before `json.dumps`)."""

    projected = _normalize(model)
    if not isinstance(projected, dict):
        raise TypeError("canonical projection of a model must be an object")
    return projected


def canonical_json(model: BaseModel) -> str:
    return json.dumps(
        canonical_projection(model),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_bytes(model: BaseModel) -> bytes:
    return canonical_json(model).encode("utf-8")


def canonical_sha256(model: BaseModel) -> str:
    return hashlib.sha256(canonical_bytes(model)).hexdigest()


def fusion_policy_config_hash(policy: P2T4FusionPolicyConfigV1) -> str:
    return canonical_sha256(policy)


def conflict_id_for(reason_code: P2T4ConflictReasonCode, fused_observation_id: str) -> str:
    """`P2T4-CONFLICT-` + SHA-256 of `reason_code || NUL || fused_observation_id` (UTF-8)."""

    if "\x00" in fused_observation_id:
        raise ValueError("observation ID must not contain NUL")
    payload = reason_code.value.encode("utf-8") + b"\x00" + fused_observation_id.encode("utf-8")
    return P2T4_CONFLICT_ID_PREFIX + hashlib.sha256(payload).hexdigest()
