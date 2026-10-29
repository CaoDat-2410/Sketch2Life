"""BE2-04 SK1 application ports (offline component; owner adapters are ASSUMED_CONTRACT).

The handoff projection ``SketchHandoffV1`` and every type here belong to 04 (N01): adapters
may read BE2-03/BE2-02, but no producer type crosses into this module or the domain.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.ai_jobs import ArtifactDescriptor, Principal
from sketch2life.domain.sketch_proposal import (
    CurrentFacts,
    DecisionToken,
    HandoffBinding,
    LevelOutputRule,
    OutputPart,
    SketchPolicySnapshot,
    SketchProposal,
    StagedGeneration,
)

HANDOFF_CONTRACT_VERSION = "sketch-handoff-v1"


class SketchUniqueConflict(Exception):
    """A unique key (handoff, staged attempt, receipt) already exists."""


class SketchRevisionConflict(Exception):
    """CAS on ``record_version`` lost."""


class StaleDecision(Exception):
    """The decision token or ref-set changed before the 04 commit (plan §7.2a)."""


# ------------------------------------------------------------------ handoff (N01)
@dataclass(frozen=True, slots=True)
class SketchHandoffV1:
    """Versioned 04 consumer projection of one BE2-03 analysis_ready request."""

    binding: HandoffBinding
    contract_version: str = HANDOFF_CONTRACT_VERSION


class HandoffRefusalCode(StrEnum):
    NOT_READY = "HANDOFF_NOT_READY"
    UNREADABLE = "HANDOFF_UNREADABLE"
    MISMATCH = "HANDOFF_MISMATCH"


@dataclass(frozen=True, slots=True)
class HandoffRefusal:
    code: HandoffRefusalCode


@dataclass(frozen=True, slots=True)
class HandoffHint:
    """Non-authoritative hint from the BE2-03 post-commit callback (plan §3.2)."""

    intent_id: str
    assistance_id: str
    request_revision: int
    analysis_id: str
    analysis_revision: int


class SketchHandoffReader(Protocol):
    def resolve(self, organization_id: str,
                assistance_id: str) -> SketchHandoffV1 | HandoffRefusal: ...

    def current(self, binding: HandoffBinding) -> CurrentFacts: ...


# ------------------------------------------------------------------ decision token
class SketchDecisionPort(Protocol):
    def token(self, organization_id: str, refs: tuple[str, ...],
              ref_set_id: str) -> DecisionToken: ...


class SketchPolicyPort(Protocol):
    """Consumer proposal to the BE2-14 owner; SK1 binds a FIXTURE_ONLY adapter."""

    def current(self, organization_id: str, session_id: str) -> SketchPolicySnapshot | None: ...


# ------------------------------------------------------------------ generator
@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Minimised provider projection (TC-06): no child ids, ages, text or candidates."""

    correlation_id: str
    organization_id: str
    proposal_id: str
    proposal_version: int
    attempt_number: int
    render_ref: str
    render_sha256: str
    render_media_type: str
    admission_receipt_id: str
    assistance_level: str
    rule: LevelOutputRule
    confirmed_concepts: tuple[str, ...]
    generator_profile_ref: str
    generation_digest: str


@dataclass(frozen=True, slots=True)
class ProviderCopyRef:
    copy_id: str
    kind: str  # input | output | job | cache
    provider_profile: str


@dataclass(frozen=True, slots=True)
class GenerationSucceeded:
    parts: tuple[OutputPart, ...]
    unsafe: bool
    adapter_id: str
    model_profile_version: str
    configuration_version: str
    evidence_kind: str
    copies: tuple[ProviderCopyRef, ...] = ()


@dataclass(frozen=True, slots=True)
class GenerationFailed:
    code: str  # PROVIDER_TIMEOUT | PROVIDER_UNAVAILABLE | PROVIDER_ERROR
    retryable: bool
    provider_invoked: bool
    copies: tuple[ProviderCopyRef, ...] = ()


GenerationOutcome = GenerationSucceeded | GenerationFailed


class SketchGenerator(Protocol):
    def known_copies(self, request: GenerationRequest) -> tuple[ProviderCopyRef, ...]:
        """Copies created by sending the request (registered before the call, TC-13)."""

    def generate(self, request: GenerationRequest) -> GenerationOutcome: ...


# ------------------------------------------------------------------ admission
@dataclass(frozen=True, slots=True)
class DerivativeProvenance:
    """DATA-20-shaped candidate provenance (ASSUMED_CONTRACT for ArtifactReferenceV1)."""

    origin: str
    source_refs: tuple[tuple[str, str], ...]
    producer_adapter_id: str
    producer_profile_version: str
    classification: str
    purpose_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StagedArtifact:
    artifact_ref: str
    sha256: str
    media_type: str
    byte_size: int


@dataclass(frozen=True, slots=True)
class AdmissionRefusal:
    reason: str


class DerivedArtifactAdmissionPort(Protocol):
    def stage(self, organization_id: str, job_id: str, attempt_id: str, part_key: str,
              body: bytes, media_type: str,
              provenance: DerivativeProvenance) -> StagedArtifact | AdmissionRefusal: ...


class SketchArtifactReader(Protocol):
    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None: ...


# ------------------------------------------------------------------ jobs
@dataclass(frozen=True, slots=True)
class SketchJobCreate:
    principal: Principal
    idempotency_key: str
    target_id: str
    purpose_code: str
    session_id: str
    subject_refs: tuple[str, ...]
    request_id: str
    request_revision: int
    input_hash: str
    context_revision: int
    correlation_id: str


class JobCreateKind(StrEnum):
    CREATED = "created"
    REFUSED = "refused"
    RETRY = "retry"


@dataclass(frozen=True, slots=True)
class JobCreateOutcome:
    kind: JobCreateKind
    job_id: str | None = None
    code: str | None = None


@dataclass(frozen=True, slots=True)
class SketchJobEvidence:
    job_id: str
    organization_id: str
    job_type: str
    state: str
    disposition: str | None
    active_attempt_id: str
    attempt_number: int
    request_id: str
    request_revision: int
    input_hash: str
    context_revision: int
    result_refs: tuple[tuple[str, str], ...]
    failure_code: str | None
    job_revision: int

    @property
    def terminal(self) -> bool:
        return self.state in {"succeeded", "failed_exhausted", "blocked_unsafe", "cancelled"}


class SketchJobPort(Protocol):
    def create(self, request: SketchJobCreate) -> JobCreateOutcome: ...

    def cancel(self, principal: Principal, job_id: str, expected_job_revision: int,
               reason_code: str = "CANCELLED_BY_TEACHER") -> str: ...


class SketchJobReader(Protocol):
    def get(self, job_id: str) -> SketchJobEvidence | None: ...

    def find_semantic(self, request: SketchJobCreate) -> str | None: ...


class SketchCopyPort(Protocol):
    def register(self, organization_id: str, scope_ref: str, copy: ProviderCopyRef) -> None: ...


# ------------------------------------------------------------------ authority
class SketchAction(StrEnum):
    READ = "read"
    CANCEL = "cancel"
    REVISE = "revise"
    DEVICE_VIEW = "device_view"


@dataclass(frozen=True, slots=True)
class SketchScope:
    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    audience: tuple[str, ...]


class SketchAuthorityPort(Protocol):
    def allowed(self, principal: Principal, scope: SketchScope, action: SketchAction) -> bool: ...


# ------------------------------------------------------------------ store
@dataclass(frozen=True, slots=True)
class SketchReceipt:
    key: str
    fingerprint: str
    proposal_id: str
    outcome: str
    result_version: int
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class SketchEvent:
    event_id: str
    event_type: str
    organization_id: str
    proposal_id: str | None
    proposal_version: int | None
    assistance_id: str
    reason: str | None
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class CleanupIntent:
    """Quarantine of non-promoted 04 outputs; delivered through the artifact port (C9)."""

    event_id: str
    organization_id: str
    job_id: str
    attempt_id: str
    artifact_refs: tuple[str, ...]
    reason_code: str


class SketchUnitOfWork(Protocol):
    def require_token(self, token: DecisionToken, refs: tuple[str, ...]) -> None:
        """Raise ``StaleDecision`` unless the committed epochs still equal the token."""

    def get(self, proposal_id: str) -> SketchProposal | None: ...

    def find_by_assistance(self, organization_id: str, assistance_id: str) -> str | None: ...

    def insert(self, proposal: SketchProposal) -> None: ...

    def cas(self, *, expected_record_version: int, proposal: SketchProposal) -> None: ...

    def list_proposals(self, organization_id: str) -> tuple[SketchProposal, ...]: ...

    def get_staged(self, job_id: str, attempt_id: str) -> StagedGeneration | None: ...

    def put_staged(self, staged: StagedGeneration) -> None: ...

    def update_staged(self, staged: StagedGeneration) -> None: ...

    def staged_for(self, proposal_id: str) -> tuple[StagedGeneration, ...]: ...

    def get_receipt(self, key: str) -> SketchReceipt | None: ...

    def put_receipt(self, receipt: SketchReceipt) -> None: ...

    def add_event(self, event: SketchEvent) -> None: ...

    def add_cleanup(self, intent: CleanupIntent) -> None: ...

    def pending_cleanup(self) -> tuple[CleanupIntent, ...]: ...

    def mark_cleanup(self, event_id: str) -> None: ...

    def add_hint(self, organization_id: str, hint: HandoffHint) -> None: ...

    def hints(self, organization_id: str) -> tuple[HandoffHint, ...]: ...

    def drop_hint(self, organization_id: str, intent_id: str) -> None: ...

    def request_revalidation(self, proposal_id: str) -> None: ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def record_notice(self, notice_id: str) -> None: ...

    def publish_invalidation(self, organization_id: str) -> None:
        """Bump the owner/request fence after commit (fake composition, like A1)."""


class SketchProposalRepository(Protocol):
    def transaction(self) -> AbstractContextManager[SketchUnitOfWork]: ...


# ------------------------------------------------------------------ results
@dataclass(frozen=True, slots=True)
class GenerationClaim:
    """Worker outcome the provider adapter maps to a foundation ``CompletionClaim``."""

    job_id: str
    attempt_id: str
    request_revision: int
    input_hash: str
    context_revision: int
    success: bool
    outputs: tuple[tuple[str, str], ...] = ()
    unsafe: bool = False
    failure_code: str | None = None
    retryable: bool = False


__all__ = [
    "HANDOFF_CONTRACT_VERSION",
    "AdmissionRefusal",
    "CleanupIntent",
    "DerivativeProvenance",
    "DerivedArtifactAdmissionPort",
    "GenerationClaim",
    "GenerationFailed",
    "GenerationOutcome",
    "GenerationRequest",
    "GenerationSucceeded",
    "HandoffHint",
    "HandoffRefusal",
    "HandoffRefusalCode",
    "JobCreateKind",
    "JobCreateOutcome",
    "ProviderCopyRef",
    "SketchAction",
    "SketchArtifactReader",
    "SketchAuthorityPort",
    "SketchCopyPort",
    "SketchDecisionPort",
    "SketchEvent",
    "SketchGenerator",
    "SketchHandoffReader",
    "SketchHandoffV1",
    "SketchJobCreate",
    "SketchJobEvidence",
    "SketchJobPort",
    "SketchJobReader",
    "SketchPolicyPort",
    "SketchProposalRepository",
    "SketchReceipt",
    "SketchRevisionConflict",
    "SketchScope",
    "SketchUniqueConflict",
    "SketchUnitOfWork",
    "StagedArtifact",
    "StaleDecision",
]
