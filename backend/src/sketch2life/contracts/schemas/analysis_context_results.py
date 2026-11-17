"""DATA-22 typed-context sibling contracts (BE2-02 C2, ``0.2-candidate``, not adopted).

The image_only ``0.1-candidate`` contracts in ``analysis_results`` stay byte-for-byte strict
and reject typed records (their literals do not include the new evidence kind, version or
binding field). These siblings reuse the unchanged 0.1 sub-models and add the pinned
``TypedContextBindingV2``: on the provenance as the evidence copy and on the record as the
head binding, which must be equal. CMD-34 command/receipts and the Child projection remain
0.1 and never carry typed context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from sketch2life.contracts.schemas.ai_jobs import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.analysis_results import (
    CorrectionRecordV1,
    EvidenceRefV1,
    ModerationOutcomeV1,
    ObjectCandidateV1,
    OriginalObservationV1,
    ShortTextV1,
    SourceBindingV1,
    UncertaintyV1,
)
from sketch2life.domain.vision_analysis import OBSERVATION_COLLECTION_MAX

TYPED_CANDIDATE_VERSION = "0.2-candidate"
_EVIDENCE_KINDS = frozenset(
    {"vision_observation", "provider_result", "source_checkpoint", "source_render",
     "admission_receipt"}
)


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class TypedContextBindingV2(_Strict):
    """Opaque pinned binding; digests are not proof of anonymity, consent or model use."""

    context_contract: Literal["VisionTypedContextV1"]
    context_contract_version: Literal["0.1-candidate"]
    canonical_rules_version: Literal["vision-context-canonical-v1"]
    context_revision: int = Field(ge=0)
    payload_digest: Sha256Hex
    context_digest: Sha256Hex
    age_band_policy_ref: OpaqueId
    age_band_policy_version: OpaqueId

    @model_validator(mode="after")
    def _distinct(self) -> TypedContextBindingV2:
        if self.payload_digest == self.context_digest:
            raise ValueError("payload and context digests are distinct bindings")
        return self


class TypedProvenanceV2(_Strict):
    evidence_kind: Literal["offline_context_adapter", "synthetic_fake"]
    provider_context_mode: Literal["typed_context"]
    adapter_id: OpaqueId
    result_contract: ShortTextV1
    executed_at: AwareDatetime
    transport_attempts: int = Field(ge=0, le=1)
    profile_id: OpaqueId | None = None
    profile_catalog_hash: Sha256Hex | None = None
    config_hash: Sha256Hex | None = None
    adapter_version: ShortTextV1 | None = None
    model_identifier: ShortTextV1 | None = None
    model_revision: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    content_policy_version: ShortTextV1 | None = None
    policy_match_view_version: ShortTextV1 | None = None
    context_binding: TypedContextBindingV2

    @field_serializer("executed_at")
    def _ser_time(self, value: datetime) -> str | None:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @model_validator(mode="after")
    def _truthful(self) -> TypedProvenanceV2:
        if self.evidence_kind == "offline_context_adapter" and (
            self.transport_attempts != 1 or None in (
                self.profile_id, self.profile_catalog_hash, self.config_hash,
                self.adapter_version, self.model_identifier, self.model_revision,
                self.content_policy_version, self.policy_match_view_version,
            )
        ):
            raise ValueError("context adapter provenance needs one call and full model identity")
        return self


class AnalysisWorkerCandidateV2(_Strict):
    """Typed-context DATA-22 worker candidate (sibling of the 0.1 image_only candidate)."""

    assistance_id: OpaqueId
    expected_request_revision: int = Field(ge=1)
    input_snapshot_ref: OpaqueId
    context_revision: int = Field(ge=0)
    job_id: OpaqueId
    job_attempt_id: OpaqueId
    contract_version: Literal["0.2-candidate"]
    object_candidates: tuple[ObjectCandidateV1, ...] = Field(max_length=OBSERVATION_COLLECTION_MAX)
    uncertainty: UncertaintyV1
    evidence_refs: tuple[EvidenceRefV1, ...] = Field(min_length=5, max_length=5)
    provenance: TypedProvenanceV2
    moderation_outcome: ModerationOutcomeV1

    @model_validator(mode="after")
    def _consistent(self) -> AnalysisWorkerCandidateV2:
        kinds = [ref.kind for ref in self.evidence_refs]
        if set(kinds) != _EVIDENCE_KINDS or len(kinds) != len(_EVIDENCE_KINDS):
            raise ValueError("evidence_refs needs exactly one ref of each evidence kind")
        hashes = {ref.kind: ref.sha256 for ref in self.evidence_refs}
        if hashes["source_checkpoint"] == hashes["source_render"]:
            raise ValueError("checkpoint checksum and render hash must be distinct bindings")
        refs = [candidate.observation_ref for candidate in self.object_candidates]
        if len(refs) != len(set(refs)):
            raise ValueError("object candidate observation refs must be unique")
        unknown = {c.observation_ref for c in self.object_candidates if c.confidence is None}
        if not unknown <= set(self.uncertainty.unknown_confidence_refs):
            raise ValueError("every null-confidence candidate must be listed as unknown")
        if self.provenance.context_binding.context_revision != self.context_revision:
            raise ValueError("the binding pins the analysis context revision")
        return self


class AnalysisRecordV2(_Strict):
    """Teacher/internal typed-context record: the head binding equals the evidence copy."""

    contract_name: Literal["AnalysisResultAndCorrection"]
    contract_version: Literal["0.2-candidate"]
    context_binding: TypedContextBindingV2
    analysis_id: OpaqueId
    analysis_revision: int = Field(ge=1)
    accepted_status: Literal["accepted", "stale"]
    status_reason: ShortTextV1 | None
    candidate: AnalysisWorkerCandidateV2
    original_observation: OriginalObservationV1
    observation_sha256: Sha256Hex
    source_binding: SourceBindingV1
    corrections: tuple[CorrectionRecordV1, ...]
    current_meaning_ref: OpaqueId | None

    @model_validator(mode="after")
    def _consistent(self) -> AnalysisRecordV2:
        if self.context_binding != self.candidate.provenance.context_binding:
            raise ValueError("head binding and evidence binding copy must be equal")
        refs = [c.correction_id for c in self.corrections]
        if self.current_meaning_ref is not None:
            if self.current_meaning_ref not in refs:
                raise ValueError("current meaning must be a recorded correction")
            current = next(c for c in self.corrections
                           if c.correction_id == self.current_meaning_ref)
            if current.kind != "teacher_confirmation":
                raise ValueError("only a teacher confirmation can be the current meaning")
        if (self.accepted_status == "stale") != (self.status_reason is not None):
            raise ValueError("stale needs a status_reason and only then")
        return self


__all__ = [
    "TYPED_CANDIDATE_VERSION",
    "AnalysisRecordV2",
    "AnalysisWorkerCandidateV2",
    "TypedContextBindingV2",
    "TypedProvenanceV2",
]
