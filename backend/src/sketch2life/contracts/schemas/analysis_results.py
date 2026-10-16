"""DATA-22 AnalysisResultAndCorrection / CMD-34 candidate wire contracts (BE2-02 C1).

Version ``0.1-candidate``: additive, not adopted into the shared registry, and independent of
the shallow foundation ShapeSpec (which stays unchanged). Unknown fields are rejected, so a
client can never supply server identity, author, role, status, revision or meaning. Text
normalisation (NFC + trim) follows the SRS ShortText/LongText rules; nothing else is repaired.
Legacy V1/V2 Vision value objects are reused unchanged for the original observation view.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from sketch2life.contracts.schemas.ai_jobs import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    RelationCandidateV1,
    ThemeCandidateV1,
)
from sketch2life.domain.vision_analysis import (
    INTENDED_OBJECTS_MAX,
    OBSERVATION_COLLECTION_MAX,
    OBSERVATION_REF_MAX,
    AnalysisRuleViolation,
    normalize_long_text,
    normalize_short_text,
)

CANDIDATE_VERSION = "0.1-candidate"
DATA22_OWNER = "BE2-02"
CORRECTION_CONTRACT = "AnalysisCorrection"
_COLLECTION_MAX = OBSERVATION_COLLECTION_MAX


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _short(value: str) -> str:
    try:
        return normalize_short_text(value)
    except AnalysisRuleViolation as exc:
        raise ValueError(str(exc)) from None


def _long(value: str) -> str:
    try:
        return normalize_long_text(value)
    except AnalysisRuleViolation as exc:
        raise ValueError(str(exc)) from None


ShortTextV1 = Annotated[str, AfterValidator(_short)]
LongTextV1 = Annotated[str, AfterValidator(_long)]
ObservationRef = Annotated[
    str, Field(min_length=1, max_length=OBSERVATION_REF_MAX, pattern=r"^[a-z0-9-]+$")
]
# Null when the model is not calibrated; otherwise a strict finite number. Strict mode rejects
# bool and numeric strings; ``allow_inf_nan=False`` rejects NaN/Infinity.
Confidence = Annotated[float | None, Field(ge=0, le=1, allow_inf_nan=False)]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


# ------------------------------------------------------------- DATA-22 worker candidate
class ObjectCandidateV1(_Strict):
    label: ShortTextV1
    confidence: Confidence
    observation_ref: ObservationRef


class UncertaintyV1(_Strict):
    calibration: Literal["uncalibrated"]
    unknown_confidence_refs: tuple[ObservationRef, ...] = Field(max_length=_COLLECTION_MAX)
    ambiguous_region_refs: tuple[ObservationRef, ...] = Field(max_length=_COLLECTION_MAX)
    requires_meaning_confirmation: Literal[True]


EvidenceRefKind = Literal[
    "vision_observation", "provider_result", "source_checkpoint", "source_render",
    "admission_receipt",
]
_EVIDENCE_KINDS = frozenset(
    {"vision_observation", "provider_result", "source_checkpoint", "source_render",
     "admission_receipt"}
)


class EvidenceRefV1(_Strict):
    """Distinct hashes: observation record, provider result, JSON checkpoint checksum, rendered
    image bytes and admission receipt are never interchangeable."""

    kind: EvidenceRefKind
    ref: OpaqueId
    sha256: Sha256Hex


class ProvenanceV1(_Strict):
    evidence_kind: Literal["synthetic_fake", "offline_legacy_bridge"]
    provider_context_mode: Literal["image_only", "typed_context"]
    adapter_id: OpaqueId
    result_contract: ShortTextV1
    executed_at: AwareDatetime
    transport_attempts: int = Field(ge=0, le=1)
    profile_id: OpaqueId | None = None
    profile_catalog_hash: Sha256Hex | None = None
    config_hash: Sha256Hex | None = None
    adapter_version: ShortTextV1 | None = None
    model_identifier: ShortTextV1 | None = None
    model_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")] | None = None
    content_policy_version: ShortTextV1 | None = None
    policy_match_view_version: ShortTextV1 | None = None

    @field_serializer("executed_at")
    def _ser_time(self, value: datetime) -> str | None:
        return _utc(value)

    @model_validator(mode="after")
    def _truthful(self) -> ProvenanceV1:
        if self.evidence_kind == "offline_legacy_bridge":
            if self.provider_context_mode != "image_only":
                raise ValueError("the legacy bridge is image_only")
            if self.transport_attempts != 1 or None in (
                self.profile_id, self.profile_catalog_hash, self.config_hash,
                self.adapter_version, self.model_identifier, self.model_revision,
                self.content_policy_version, self.policy_match_view_version,
            ):
                raise ValueError("legacy bridge provenance needs one call and full model identity")
        return self


class ModerationOutcomeV1(_Strict):
    lexical_regression: Literal["passed", "not_executed"]
    lexical_policy_version: ShortTextV1 | None
    match_view_version: ShortTextV1 | None
    comprehensive_moderation: Literal["not_run"]
    child_visibility: Literal["withheld"]


class AnalysisWorkerCandidateV1(_Strict):
    """DATA-22 worker candidate, exactly the source field set (internal worker port only)."""

    assistance_id: OpaqueId
    expected_request_revision: int = Field(ge=1)
    input_snapshot_ref: OpaqueId
    context_revision: int = Field(ge=0)
    job_id: OpaqueId
    job_attempt_id: OpaqueId
    contract_version: Literal["0.1-candidate"]
    object_candidates: tuple[ObjectCandidateV1, ...] = Field(max_length=_COLLECTION_MAX)
    uncertainty: UncertaintyV1
    evidence_refs: tuple[EvidenceRefV1, ...] = Field(min_length=5, max_length=5)
    provenance: ProvenanceV1
    moderation_outcome: ModerationOutcomeV1

    @model_validator(mode="after")
    def _consistent(self) -> AnalysisWorkerCandidateV1:
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
        return self


# ----------------------------------------------------------------- CMD-34 command body
class AnalysisCorrectionCommandV1(_Strict):
    """CMD-34 body. ``child_explanation`` omitted and ``null`` both mean no explanation."""

    intended_objects: tuple[ShortTextV1, ...] = Field(min_length=1,
                                                      max_length=INTENDED_OBJECTS_MAX)
    child_explanation: LongTextV1 | None = None
    correction_reason: ShortTextV1
    expected_context_revision: int = Field(ge=0)
    basis_correction_ref: OpaqueId | None = None

    @model_validator(mode="after")
    def _unique_objects(self) -> AnalysisCorrectionCommandV1:
        folded = [value.casefold() for value in self.intended_objects]
        if len(set(folded)) != len(folded):
            raise ValueError("intended_objects must be unique")
        return self


# --------------------------------------------------------------- CMD-34 projections
class CorrectionAuthorV1(_Strict):
    principal_ref: OpaqueId
    role: Literal["teacher", "child_device"]
    participant_id: OpaqueId | None
    turn_id: OpaqueId | None

    @model_validator(mode="after")
    def _binding(self) -> CorrectionAuthorV1:
        bound = self.participant_id is not None and self.turn_id is not None
        if (self.role == "child_device") != bound or (
            self.role == "teacher" and (self.participant_id or self.turn_id)
        ):
            raise ValueError("only a child device author carries a participant/turn binding")
        return self


class CorrectionRecordV1(_Strict):
    correction_id: OpaqueId
    correction_version: int = Field(ge=2)
    kind: Literal["child_proposal", "teacher_confirmation"]
    meaning_status: Literal["proposed", "confirmed"]
    meaning_kind: Literal["intended_concept"]
    author: CorrectionAuthorV1
    intended_objects: tuple[ShortTextV1, ...] = Field(min_length=1,
                                                      max_length=INTENDED_OBJECTS_MAX)
    child_explanation: LongTextV1 | None
    correction_reason: ShortTextV1
    expected_context_revision: int = Field(ge=0)
    basis_correction_ref: OpaqueId | None
    recorded_at: AwareDatetime

    @field_serializer("recorded_at")
    def _ser_time(self, value: datetime) -> str | None:
        return _utc(value)

    @model_validator(mode="after")
    def _consistent(self) -> CorrectionRecordV1:
        proposal = self.kind == "child_proposal"
        if proposal != (self.meaning_status == "proposed"):
            raise ValueError("child proposals are proposed; teacher confirmations confirmed")
        if proposal != (self.author.role == "child_device"):
            raise ValueError("proposal author must be the child device, confirmation a teacher")
        if proposal and self.basis_correction_ref is not None:
            raise ValueError("a child proposal has no basis correction")
        if not proposal and self.child_explanation is not None:
            raise ValueError("a teacher confirmation cannot carry a child explanation")
        return self


class OriginalAnalysisRefV1(_Strict):
    analysis_id: OpaqueId
    observation_sha256: Sha256Hex
    accepted_status: Literal["accepted", "stale"]
    input_snapshot_ref: OpaqueId
    context_revision: int = Field(ge=0)
    job_id: OpaqueId
    job_attempt_id: OpaqueId


class InvalidationNoticeV1(_Strict):
    event_id: OpaqueId
    previous_revision: int = Field(ge=1)
    analysis_revision: int = Field(ge=2)
    reason: Literal["child_intent_proposed", "teacher_meaning_confirmed"]


class AnalysisCorrectionReceiptV1(_Strict):
    """Teacher projection: original refs/candidates stay beside the separate correction."""

    analysis_id: OpaqueId
    analysis_revision: int = Field(ge=2)
    original: OriginalAnalysisRefV1
    object_candidates: tuple[ObjectCandidateV1, ...] = Field(max_length=_COLLECTION_MAX)
    correction: CorrectionRecordV1
    current_meaning_ref: OpaqueId | None
    invalidation: InvalidationNoticeV1

    @model_validator(mode="after")
    def _consistent(self) -> AnalysisCorrectionReceiptV1:
        if self.correction.correction_version != self.analysis_revision:
            raise ValueError("correction version is the analysis revision it created")
        if self.invalidation.analysis_revision != self.analysis_revision:
            raise ValueError("invalidation notice must carry the new analysis revision")
        return self


class AnalysisCorrectionChildReceiptV1(_Strict):
    """Device projection: refs and status only — no model labels, confidence, uncertainty,
    evidence, moderation, Teacher text or age."""

    analysis_id: OpaqueId
    analysis_revision: int = Field(ge=2)
    correction_id: OpaqueId
    correction_version: int = Field(ge=2)
    kind: Literal["child_proposal"]
    meaning_status: Literal["proposed"]
    recorded_at: AwareDatetime

    @field_serializer("recorded_at")
    def _ser_time(self, value: datetime) -> str | None:
        return _utc(value)


class CorrectionMetaV1(_Strict):
    resource_revision: int = Field(ge=2)
    projection: Literal["teacher", "child_device"]
    replayed: bool


class AnalysisCorrectionEnvelopeV1(_Strict):
    contract_name: Literal["AnalysisCorrectionReceipt"] = "AnalysisCorrectionReceipt"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    correlation_id: OpaqueId
    data: AnalysisCorrectionReceiptV1
    meta: CorrectionMetaV1


class AnalysisCorrectionChildEnvelopeV1(_Strict):
    contract_name: Literal["AnalysisCorrectionChildReceipt"] = "AnalysisCorrectionChildReceipt"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    correlation_id: OpaqueId
    data: AnalysisCorrectionChildReceiptV1
    meta: CorrectionMetaV1


# ----------------------------------------------------------- H-AI-REVIEW record view
class CheckpointBindingV1(_Strict):
    checkpoint_id: OpaqueId
    canvas_id: OpaqueId
    document_epoch: int = Field(ge=0)
    checkpoint_revision: int = Field(ge=1)
    checksum_sha256: Sha256Hex


class RenderBindingV1(_Strict):
    render_ref: OpaqueId
    render_sha256: Sha256Hex
    media_type: Literal["image/png", "image/jpeg"]
    renderer_version: ShortTextV1


class SourceBindingV1(_Strict):
    input_snapshot_ref: OpaqueId
    checkpoint: CheckpointBindingV1
    render: RenderBindingV1
    admission_receipt_id: OpaqueId


class OriginalObservationV1(_Strict):
    """Reuses the legacy V1 candidate value objects so the original typed shape is unchanged."""

    entities: tuple[EntityCandidateV1, ...]
    actions: tuple[ActionCandidateV1, ...]
    relations: tuple[RelationCandidateV1, ...]
    themes: tuple[ThemeCandidateV1, ...]
    ambiguous_regions: tuple[AmbiguousRegionCandidateV1, ...]


class AnalysisRecordV1(_Strict):
    """Teacher/internal H-AI-REVIEW view: candidate, original observation, bindings and the
    separate correction history. Not a public route in C1."""

    contract_name: Literal["AnalysisResultAndCorrection"] = "AnalysisResultAndCorrection"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    analysis_id: OpaqueId
    analysis_revision: int = Field(ge=1)
    accepted_status: Literal["accepted", "stale"]
    status_reason: ShortTextV1 | None
    candidate: AnalysisWorkerCandidateV1
    original_observation: OriginalObservationV1
    observation_sha256: Sha256Hex
    source_binding: SourceBindingV1
    # Append-only history is projected complete; no count cap (C1-R05). Size is bounded by the
    # accepted command stream itself; paging is a later persistence/API decision.
    corrections: tuple[CorrectionRecordV1, ...]
    current_meaning_ref: OpaqueId | None

    @model_validator(mode="after")
    def _consistent(self) -> AnalysisRecordV1:
        refs = [c.correction_id for c in self.corrections]
        if self.current_meaning_ref is not None:
            if self.current_meaning_ref not in refs:
                raise ValueError("current meaning must be a recorded correction")
            current = next(c for c in self.corrections if c.correction_id
                           == self.current_meaning_ref)
            if current.kind != "teacher_confirmation":
                raise ValueError("only a teacher confirmation can be the current meaning")
        if (self.accepted_status == "stale") != (self.status_reason is not None):
            raise ValueError("stale needs a status_reason and only then")
        return self


__all__ = [
    "CANDIDATE_VERSION",
    "CORRECTION_CONTRACT",
    "DATA22_OWNER",
    "AnalysisCorrectionChildEnvelopeV1",
    "AnalysisCorrectionChildReceiptV1",
    "AnalysisCorrectionCommandV1",
    "AnalysisCorrectionEnvelopeV1",
    "AnalysisCorrectionReceiptV1",
    "AnalysisRecordV1",
    "AnalysisWorkerCandidateV1",
    "CheckpointBindingV1",
    "CorrectionAuthorV1",
    "CorrectionMetaV1",
    "CorrectionRecordV1",
    "EvidenceRefV1",
    "InvalidationNoticeV1",
    "ModerationOutcomeV1",
    "ObjectCandidateV1",
    "OriginalAnalysisRefV1",
    "OriginalObservationV1",
    "ProvenanceV1",
    "RenderBindingV1",
    "SourceBindingV1",
    "UncertaintyV1",
]
