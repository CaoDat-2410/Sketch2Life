"""BE2-05 Sketch review application ports (offline component, FEAT-052).

The producer is read only through its public service API (plan §4.5): the target reader maps the
producer's returned values into the 05-owned ``ReviewTarget``. Authority, context and policy are
candidate owner ports bound to fixtures in this checkpoint.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.ai_jobs import ArtifactDescriptor, Principal, QuarantineIntent
from sketch2life.domain.sketch_review import (
    ModerationKey,
    ModerationOutcome,
    ModerationRecord,
    ReviewEntry,
    ReviewHead,
    ReviewTarget,
    VersionTerminalMarker,
)


class StaleReviewDecision(Exception):
    """The decision token changed before the 05 commit (plan §4.6 step 4a)."""


class ReviewRevisionConflict(Exception):
    """CAS on the head ``decision_revision`` lost."""


class ReviewUniqueConflict(Exception):
    """A unique key (receipt, marker, entry) already exists."""


# ------------------------------------------------------------------ producer reads
class SketchReviewTargetReader(Protocol):
    def read(self, proposal_id: str) -> ReviewTarget | None:
        """Producer public revalidation, mapped to the 05 projection (system-level read)."""
        ...

    def queue_record(self, teacher: Principal, proposal_id: str) -> Mapping[str, object] | None:
        """Producer Teacher record (real Teacher principal only; never a device)."""
        ...


class ReviewArtifactPort(Protocol):
    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None: ...


class QuarantineSink(Protocol):
    def quarantine(self, intent: QuarantineIntent) -> None:
        """Apply at the sink; called only after the 05 commit, outside the unit (§4.4)."""
        ...


# ------------------------------------------------------------------ moderation / policy
@dataclass(frozen=True, slots=True)
class ReviewPolicy:
    policy_id: str
    version: str
    status: str
    enabled: bool
    text_max_chars: int
    blocked_terms: frozenset[str]
    asset_media_types: frozenset[str]
    asset_max_bytes: int
    consent_purpose: str

    def ref(self) -> dict[str, str]:
        return {"policy_id": self.policy_id, "version": self.version}


class ReviewPolicyPort(Protocol):
    def current(self, organization_id: str, session_id: str) -> ReviewPolicy | None: ...


@dataclass(frozen=True, slots=True)
class ModerationVerdict:
    outcome: ModerationOutcome
    reason_code: str | None


class SketchModerationPort(Protocol):
    def moderate(self, target: ReviewTarget, descriptors: tuple[ArtifactDescriptor | None, ...],
                 policy: ReviewPolicy) -> ModerationVerdict: ...


# ------------------------------------------------------------------ authority / context
class ReviewAction(StrEnum):
    REVIEW = "review"
    QUEUE_READ = "queue_read"
    CHILD_VIEW = "child_view"


@dataclass(frozen=True, slots=True)
class ReviewScope:
    organization_id: str
    class_id: str
    session_id: str
    audience: tuple[str, ...]


class ReviewAuthorityPort(Protocol):
    def allowed(self, principal: Principal, scope: ReviewScope, action: ReviewAction) -> bool: ...

    def participant_for(self, principal: Principal, scope: ReviewScope) -> str | None:
        """Bound participant of a device principal in this session, or None."""
        ...


@dataclass(frozen=True, slots=True)
class ReviewContextSnapshot:
    audience_context_revision: int
    consent_refs: tuple[tuple[str, int], ...]
    consent_effective: frozenset[str]
    admitted: frozenset[str]
    session_active: bool


class ReviewContextPort(Protocol):
    def current(self, organization_id: str, session_id: str,
                subjects: tuple[str, ...]) -> ReviewContextSnapshot | None: ...


# ------------------------------------------------------------------ decision token
@dataclass(frozen=True, slots=True)
class ReviewDecisionToken:
    organization_id: str
    epochs: tuple[tuple[str, int], ...]
    target_identity: str


class ReviewTokenPort(Protocol):
    def token(self, target: ReviewTarget, principal: Principal) -> ReviewDecisionToken: ...

    def generation(self, organization_id: str, session_id: str) -> tuple[tuple[str, int], ...]:
        """Current monotonic 05 invalidation generation (review policy + review context)."""
        ...


# ------------------------------------------------------------------ store
@dataclass(frozen=True, slots=True)
class ReviewReceipt:
    key: str
    fingerprint: str
    status: int
    data: Mapping[str, object]
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class EligibilityChangedIntent:
    """Consumer notice for read-model/cache dispatchers; delivery is out of scope."""

    event_id: str
    organization_id: str
    proposal_id: str
    proposal_version: int
    review_id: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class ReviewAuditRecord:
    event_id: str
    organization_id: str
    proposal_id: str
    action: str
    decision: str | None
    principal_id: str | None
    occurred_at: datetime


class SketchReviewUnitOfWork(Protocol):
    def hold(self, token: ReviewDecisionToken) -> None:
        """Raise ``StaleReviewDecision`` unless every token epoch is still current."""

    def get_head(self, proposal_id: str) -> ReviewHead | None: ...

    def put_head(self, *, expected_decision_revision: int | None, head: ReviewHead) -> None: ...

    def entries(self, proposal_id: str) -> tuple[ReviewEntry, ...]: ...

    def put_entries(self, proposal_id: str, entries: tuple[ReviewEntry, ...]) -> None: ...

    def get_marker(self, proposal_id: str, version: int,
                   content_sha256: str) -> VersionTerminalMarker | None: ...

    def insert_marker(self, marker: VersionTerminalMarker) -> None:
        """Unique insert; there is no update or delete."""

    def get_moderation(self, key: ModerationKey) -> ModerationRecord | None:
        """Assessment for exact content + refs + moderation policy (RV-CR01)."""

    def put_moderation(self, record: ModerationRecord) -> None:
        """Append-only: an assessment under another policy never rewrites an old one."""

    def get_receipt(self, key: str) -> ReviewReceipt | None: ...

    def put_receipt(self, receipt: ReviewReceipt) -> None: ...

    def add_intent(self, intent: EligibilityChangedIntent) -> None: ...

    def add_quarantine(self, intent: QuarantineIntent) -> None: ...

    def pending_quarantine(self) -> tuple[QuarantineIntent, ...]: ...

    def mark_quarantine_delivered(self, event_id: str) -> None: ...

    def add_audit(self, record: ReviewAuditRecord) -> None: ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def record_notice(self, notice_id: str) -> None: ...

    def touch(self, organization_id: str, proposal_id: str) -> None:
        """Publish this proposal's 05 eligibility epoch after a successful commit."""


class SketchReviewRepository(Protocol):
    def transaction(self) -> AbstractContextManager[SketchReviewUnitOfWork]: ...


class EligibilityEpochPort(Protocol):
    def epoch(self, organization_id: str, proposal_id: str) -> int: ...


__all__ = [
    "EligibilityChangedIntent",
    "EligibilityEpochPort",
    "ModerationVerdict",
    "QuarantineSink",
    "ReviewAction",
    "ReviewArtifactPort",
    "ReviewAuditRecord",
    "ReviewAuthorityPort",
    "ReviewContextPort",
    "ReviewContextSnapshot",
    "ReviewDecisionToken",
    "ReviewPolicy",
    "ReviewPolicyPort",
    "ReviewReceipt",
    "ReviewRevisionConflict",
    "ReviewScope",
    "ReviewTokenPort",
    "ReviewUniqueConflict",
    "SketchModerationPort",
    "SketchReviewRepository",
    "SketchReviewTargetReader",
    "SketchReviewUnitOfWork",
    "StaleReviewDecision",
]
