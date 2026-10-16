"""BE2-02 C1 ports: source, admission, authority, context, request/job lineage, observation
provider and the analysis repository/unit of work (0.1-candidate, ASSUMED_CONTRACT).

Every port is correction-specific and narrow. Fakes prove the proposed protocol only; real BE1
snapshot/authority/turn/consent/admission adapters, BE2-03 request lifecycle, durable storage
and a real provider remain later gates. The verified principal comes from the identity port
used by the BE2-01 foundation; nothing here trusts a client-supplied actor or organization.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.domain.vision_analysis import (
    ActorRef,
    ActorRole,
    AdmissionReceipt,
    AnalysisHead,
    AnalysisScope,
    AssistancePin,
    InvalidationIntent,
    InvalidationReason,
    JobLineageView,
    MeaningCorrection,
    ModerationOutcome,
    ObservationEvidence,
    OriginalObservation,
    ProviderContextMode,
    ProviderResultRecord,
    RenderBinding,
    SourceSnapshot,
    VisionObservation,
)


class AnalysisRevisionConflict(ValueError):
    """CAS rejected a head write because the stored analysis revision moved."""


class AnalysisUniqueConflict(Exception):
    """An insert hit an existing key; the whole unit of work rolls back."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


class AnalysisStorageUnavailable(Exception):
    """The unit of work could not commit; nothing it staged became durable."""


# ------------------------------------------------------------------------- authority
class AnalysisAction(StrEnum):
    """Correction-specific actions. BE2-01 ``read_job`` never implies any of these."""

    PROPOSE_INTENT = "propose_intent"
    CONFIRM_MEANING = "confirm_meaning"
    READ_ANALYSIS = "read_analysis"


class AuthorityReason(StrEnum):
    NOT_IN_SCOPE = "NOT_IN_SCOPE"
    GRANT_REVOKED = "GRANT_REVOKED"
    ROLE_NOT_PERMITTED = "ROLE_NOT_PERMITTED"
    TURN_UNBOUND = "TURN_UNBOUND"
    TURN_CLOSED = "TURN_CLOSED"


@dataclass(frozen=True, slots=True)
class AuthorityDecision:
    """``actor`` is the server-resolved author (bound participant/turn for a device)."""

    allowed: bool
    reason: AuthorityReason | None = None
    actor: ActorRef | None = None


class AnalysisAuthorityPort(Protocol):
    def decide(
        self, principal: Principal, action: AnalysisAction, scope: AnalysisScope
    ) -> AuthorityDecision: ...


# --------------------------------------------------------------------------- context
@dataclass(frozen=True, slots=True)
class ContextDecision:
    """Current trusted context for a scope. Ages are authoritative completed months from the
    owning profile port (``None`` = unknown); they are never inferred from a drawing."""

    context_revision: int
    consent_effective: bool
    purpose_granted: bool
    session_active: bool
    audience_age_months: tuple[tuple[str, int | None], ...]
    topic_ref: str | None = None
    age_policy_ref: str | None = None


class AnalysisContextPort(Protocol):
    def current(self, scope: AnalysisScope) -> ContextDecision: ...


# ------------------------------------------------------------ source / admission / lineage
class AnalysisSourcePort(Protocol):
    """Resolves an opaque ``input_snapshot_ref`` to exact checkpoint + render metadata."""

    def resolve(self, snapshot_ref: str, *, organization_id: str) -> SourceSnapshot | None: ...


class AdmissionPort(Protocol):
    """Trusted media-admission receipt for one exact render ref and hash, or ``None``."""

    def receipt_for(
        self, render_ref: str, render_sha256: str, *, organization_id: str
    ) -> AdmissionReceipt | None: ...


class AssistanceRequestPort(Protocol):
    """BE2-03 request identity consumed read-only; BE2-02 never implements its lifecycle."""

    def get(self, assistance_id: str) -> AssistancePin | None: ...


class JobLineagePort(Protocol):
    """BE2-01 job lineage consumed read-only; BE2-02 never writes job state."""

    def get(self, job_id: str) -> JobLineageView | None: ...


# ----------------------------------------------------------------- observation provider
@dataclass(frozen=True, slots=True)
class ObservationContext:
    """Typed context envelope. Only a provider that declares ``typed_context`` consumes it;
    the legacy V2 bridge cannot and refuses it."""

    context_revision: int
    purpose_code: str
    topic_ref: str | None
    age_policy_ref: str | None


@dataclass(frozen=True, slots=True)
class ObservationRequest:
    correlation_id: str
    organization_id: str
    render: RenderBinding
    admission: AdmissionReceipt
    context_mode: ProviderContextMode
    typed_context: ObservationContext | None = None
    processing_image_ref: str | None = None

    def __post_init__(self) -> None:
        typed = self.context_mode is ProviderContextMode.TYPED_CONTEXT
        if typed != (self.typed_context is not None):
            raise ValueError("typed_context is present exactly for typed_context mode")


class ObservationFailureCode(StrEnum):
    # Refused before any provider call.
    CONTEXT_MODE_UNSUPPORTED = "CONTEXT_MODE_UNSUPPORTED"
    DERIVED_INPUT_UNSUPPORTED = "DERIVED_INPUT_UNSUPPORTED"
    MEDIA_TYPE_UNSUPPORTED = "MEDIA_TYPE_UNSUPPORTED"
    ADMISSION_NOT_BOUND = "ADMISSION_NOT_BOUND"
    SOURCE_REJECTED = "SOURCE_REJECTED"
    # Provider reached (or attempted) once; never retried automatically.
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    OUTPUT_MALFORMED = "OUTPUT_MALFORMED"
    UNSAFE_CONTENT = "UNSAFE_CONTENT"


@dataclass(frozen=True, slots=True)
class ObservationSucceeded:
    """`result_document` is the canonical JSON of the whole typed provider result; its
    SHA256 must equal `evidence.result_sha256` (retained and resolvable, C1-R06)."""

    observation: OriginalObservation
    evidence: ObservationEvidence
    moderation: ModerationOutcome
    result_document: str


@dataclass(frozen=True, slots=True)
class ObservationFailed:
    """Typed safe outcome. ``detail`` is a closed token, never provider text."""

    code: ObservationFailureCode
    provider_invoked: bool
    retryable: bool = False
    detail: str | None = None


ObservationOutcome = ObservationSucceeded | ObservationFailed


class VisionObservationPort(Protocol):
    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]: ...

    def observe(self, request: ObservationRequest) -> ObservationOutcome: ...


# ----------------------------------------------------------------------- repository
@dataclass(frozen=True, slots=True)
class CorrectionScopeKey:
    organization_id: str
    principal_id: str
    contract_name: str
    target_id: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CorrectionReceipt:
    """Immutable accepted receipt: enough to return the original response on replay."""

    scope_key: CorrectionScopeKey
    fingerprint: str
    analysis_id: str
    correction_id: str
    previous_revision: int
    analysis_revision_after: int
    current_meaning_ref_after: str | None
    invalidation_event_id: str
    invalidation_reason: InvalidationReason
    author_role: ActorRole


class AnalysisUnitOfWork(Protocol):
    """One transaction. Observations, provider results and corrections are insert/read only."""

    def get_head(self, analysis_id: str) -> AnalysisHead | None: ...

    def find_by_attempt(self, job_id: str, attempt_id: str) -> str | None: ...

    def insert_head(self, head: AnalysisHead) -> None: ...

    def cas_head(self, *, expected_revision: int, head: AnalysisHead) -> None: ...

    def insert_observation(self, observation: VisionObservation) -> None: ...

    def get_observation(self, analysis_id: str) -> VisionObservation | None: ...

    def insert_provider_result(self, record: ProviderResultRecord) -> None: ...

    def get_provider_result(self, result_ref: str) -> ProviderResultRecord | None: ...

    def append_correction(self, correction: MeaningCorrection) -> None: ...

    def get_correction(self, correction_id: str) -> MeaningCorrection | None: ...

    def list_corrections(self, analysis_id: str) -> tuple[MeaningCorrection, ...]: ...

    def get_receipt(self, key: CorrectionScopeKey) -> CorrectionReceipt | None: ...

    def put_receipt(self, receipt: CorrectionReceipt) -> None: ...

    def add_invalidation(self, intent: InvalidationIntent) -> None: ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def record_notice(self, notice_id: str) -> None: ...


class AnalysisRepository(Protocol):
    def transaction(self) -> AbstractContextManager[AnalysisUnitOfWork]: ...


__all__ = [
    "AdmissionPort",
    "AnalysisAction",
    "AnalysisAuthorityPort",
    "AnalysisContextPort",
    "AnalysisRepository",
    "AnalysisRevisionConflict",
    "AnalysisSourcePort",
    "AnalysisStorageUnavailable",
    "AnalysisUniqueConflict",
    "AnalysisUnitOfWork",
    "AssistanceRequestPort",
    "AuthorityDecision",
    "AuthorityReason",
    "ContextDecision",
    "CorrectionReceipt",
    "CorrectionScopeKey",
    "JobLineagePort",
    "ObservationContext",
    "ObservationFailed",
    "ObservationFailureCode",
    "ObservationOutcome",
    "ObservationRequest",
    "ObservationSucceeded",
    "VisionObservationPort",
]
