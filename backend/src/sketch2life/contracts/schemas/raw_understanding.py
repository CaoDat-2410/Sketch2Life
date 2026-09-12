"""FEAT-018-owned semantic handoff contract for Gate A proposals.

This contract is deliberately distinct from FEAT-003 V2 and FEAT-017's flat V1.  It
preserves typed observations and provenance while making no eligibility decision.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.vision import (
    ObservedTextV1,
    VisionImageReferenceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionModelProvenanceV1,
    VisionProfileIdV2,
)

_ObservationRef = Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
_Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


class RawEntityObservationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    label: ObservedTextV1
    confidence: _Confidence
    source: Literal["VISION"] = "VISION"


class RawActionObservationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    label: ObservedTextV1
    actor_ref: _ObservationRef | None = None
    object_ref: _ObservationRef | None = None
    confidence: _Confidence
    source: Literal["VISION"] = "VISION"


class RawRelationObservationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    predicate: ObservedTextV1
    subject_ref: _ObservationRef
    object_ref: _ObservationRef
    confidence: _Confidence
    source: Literal["VISION"] = "VISION"

    @model_validator(mode="after")
    def _forbids_self_reference(self) -> RawRelationObservationV1:
        if self.subject_ref == self.object_ref:
            raise ValueError("relation must not self-reference")
        return self


class RawThemeObservationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    label: ObservedTextV1
    evidence_refs: tuple[_ObservationRef, ...] = Field(min_length=1, max_length=64)
    confidence: _Confidence
    source: Literal["VISION"] = "VISION"


class RawAmbiguousObservationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    note: ObservedTextV1
    source: Literal["VISION"] = "VISION"


class RawAsrClaimV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: _ObservationRef
    text: str = Field(min_length=1, max_length=2_000)
    confidence: _Confidence | None = None
    source: Literal["ASR"] = "ASR"


class RawNarrationStatus(StrEnum):
    NOT_SUPPLIED = "NOT_SUPPLIED"
    ASR_SUCCEEDED = "ASR_SUCCEEDED"
    ASR_FAILED = "ASR_FAILED"


class RawAsrFailureCode(StrEnum):
    VALIDATION_REJECTED = "VALIDATION_REJECTED"
    SOURCE_MISMATCH = "SOURCE_MISMATCH"
    TIMEOUT = "TIMEOUT"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    SCHEMA_INVALID = "SCHEMA_INVALID"


class RawAsrFailureV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: RawAsrFailureCode
    retryable: bool
    detail: str = Field(min_length=1, max_length=120)


class RawFusedClaimV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: _ObservationRef
    source_refs: tuple[_ObservationRef, ...] = Field(min_length=2, max_length=64)
    confidence: _Confidence
    source: Literal["FUSED_PROPOSAL"] = "FUSED_PROPOSAL"


class RawConflictCode(StrEnum):
    SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    REFERENCE_INCONSISTENCY = "REFERENCE_INCONSISTENCY"
    UNRESOLVED_AMBIGUITY = "UNRESOLVED_AMBIGUITY"


class RawConflictV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conflict_id: _ObservationRef
    claim_refs: tuple[_ObservationRef, ...] = Field(min_length=2, max_length=64)
    code: RawConflictCode


class RawUncertaintyStatus(StrEnum):
    UPSTREAM_PROVIDED = "UPSTREAM_PROVIDED"
    NOT_PROVIDED = "NOT_PROVIDED"


class RawProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    upstream_contract: Literal["VisionUnderstandingResultV2"]
    upstream_contract_version: Literal["2.0"]
    profile_id: VisionProfileIdV2
    profile_catalog_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    adapter_version: str | None = Field(default=None, min_length=1, max_length=120)
    config_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    model_provenance: VisionModelProvenanceV1 | None = None


class RawFailureCode(StrEnum):
    VALIDATION_REJECTED = "VALIDATION_REJECTED"
    SOURCE_MISMATCH = "SOURCE_MISMATCH"
    STALE_CORRELATION = "STALE_CORRELATION"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"
    PROHIBITED_FIELD = "PROHIBITED_FIELD"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    SCHEMA_INVALID = "SCHEMA_INVALID"


class RawFailureV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: RawFailureCode
    retryable: bool
    upstream_detail: str = Field(min_length=1, max_length=120)


class RawResultEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["RawUnderstandingResultV1"] = "RawUnderstandingResultV1"
    contract_version: Literal["1.0"] = "1.0"
    correlation_id: str = Field(min_length=1, max_length=160)
    session_id: str = Field(min_length=1, max_length=160)
    source_image_ref: VisionImageReferenceV1
    gate_a_required: Literal[True] = True


class RawUnderstandingSuccessV1(RawResultEnvelopeV1):
    status: Literal["SUCCEEDED"] = "SUCCEEDED"
    entities: tuple[RawEntityObservationV1, ...] = Field(max_length=128)
    actions: tuple[RawActionObservationV1, ...] = Field(max_length=128)
    relations: tuple[RawRelationObservationV1, ...] = Field(max_length=128)
    themes: tuple[RawThemeObservationV1, ...] = Field(max_length=128)
    ambiguous_regions: tuple[RawAmbiguousObservationV1, ...] = Field(max_length=128)
    asr_claims: tuple[RawAsrClaimV1, ...] = Field(max_length=128)
    fused_claims: tuple[RawFusedClaimV1, ...] = Field(max_length=128)
    conflicts: tuple[RawConflictV1, ...] = Field(max_length=128)
    uncertainty: _Confidence | None = None
    uncertainty_status: RawUncertaintyStatus = RawUncertaintyStatus.NOT_PROVIDED
    narration_status: RawNarrationStatus = RawNarrationStatus.NOT_SUPPLIED
    asr_failure: RawAsrFailureV1 | None = None
    provenance: RawProvenanceV1

    @model_validator(mode="after")
    def _validates_observation_references(self) -> RawUnderstandingSuccessV1:
        if (
            self.provenance.adapter_version is None
            or self.provenance.config_hash is None
            or self.provenance.model_provenance is None
        ):
            raise ValueError("successful result requires complete model provenance")
        if self.uncertainty_status is RawUncertaintyStatus.UPSTREAM_PROVIDED:
            if self.uncertainty is None:
                raise ValueError("upstream uncertainty status requires a value")
        elif self.uncertainty is not None:
            raise ValueError("uncertainty must be absent when upstream did not provide it")
        if self.narration_status is RawNarrationStatus.NOT_SUPPLIED:
            if self.asr_claims or self.asr_failure is not None:
                raise ValueError("NOT_SUPPLIED narration cannot carry ASR data")
        elif self.narration_status is RawNarrationStatus.ASR_SUCCEEDED:
            if self.asr_failure is not None:
                raise ValueError("ASR_SUCCEEDED cannot carry an ASR failure")
        elif self.asr_failure is None:
            raise ValueError("ASR_FAILED requires a typed ASR failure")
        kinds: dict[str, str] = {}

        def register(ref: str, kind: str) -> None:
            if ref in kinds:
                raise ValueError(f"duplicate observation or claim id: {ref}")
            kinds[ref] = kind

        for entity in self.entities:
            register(entity.observation_id, "ENTITY")
        for action in self.actions:
            register(action.observation_id, "ACTION")
        for relation in self.relations:
            register(relation.observation_id, "RELATION")
        for theme in self.themes:
            register(theme.observation_id, "THEME")
        for region in self.ambiguous_regions:
            register(region.observation_id, "AMBIGUOUS_REGION")
        for asr_claim in self.asr_claims:
            register(asr_claim.claim_id, "ASR")
        for fused_claim in self.fused_claims:
            register(fused_claim.claim_id, "FUSED")
        for conflict in self.conflicts:
            register(conflict.conflict_id, "CONFLICT")

        def require(ref: str, allowed: frozenset[str], field: str) -> None:
            if kinds.get(ref) not in allowed:
                raise ValueError(f"reference integrity violation: {field} -> {ref}")

        for action in self.actions:
            if action.actor_ref is not None:
                require(action.actor_ref, frozenset({"ENTITY"}), "actor_ref")
            if action.object_ref is not None:
                require(action.object_ref, frozenset({"ENTITY"}), "object_ref")
        for relation in self.relations:
            require(relation.subject_ref, frozenset({"ENTITY", "ACTION"}), "subject_ref")
            require(relation.object_ref, frozenset({"ENTITY", "ACTION"}), "object_ref")
        for theme in self.themes:
            for ref in theme.evidence_refs:
                require(ref, frozenset({"ENTITY", "ACTION", "RELATION"}), "evidence_refs")
        for fused_claim in self.fused_claims:
            for ref in fused_claim.source_refs:
                require(
                    ref,
                    frozenset({"ENTITY", "ACTION", "RELATION", "THEME", "ASR"}),
                    "source_refs",
                )
        for conflict in self.conflicts:
            for ref in conflict.claim_refs:
                if ref not in kinds:
                    raise ValueError(f"reference integrity violation: claim_refs -> {ref}")
        return self


class RawUnderstandingFailureV1(RawResultEnvelopeV1):
    status: Literal["FAILED"] = "FAILED"
    provenance: RawProvenanceV1 | None = None
    failure: RawFailureV1


RawUnderstandingResultV1 = Annotated[
    RawUnderstandingSuccessV1 | RawUnderstandingFailureV1,
    Field(discriminator="status"),
]


__all__ = [
    "RawActionObservationV1",
    "RawAmbiguousObservationV1",
    "RawAsrClaimV1",
    "RawAsrFailureCode",
    "RawAsrFailureV1",
    "RawConflictCode",
    "RawConflictV1",
    "RawEntityObservationV1",
    "RawFailureCode",
    "RawFailureV1",
    "RawFusedClaimV1",
    "RawRelationObservationV1",
    "RawResultEnvelopeV1",
    "RawThemeObservationV1",
    "RawUnderstandingFailureV1",
    "RawUnderstandingResultV1",
    "RawUnderstandingSuccessV1",
    "RawNarrationStatus",
    "RawProvenanceV1",
    "RawUncertaintyStatus",
]
