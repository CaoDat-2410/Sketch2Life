"""BE2-05 coordination over the shared fake composition (plan §4.6, OD-05).

``CoordinatedSketchReviewRepository`` runs every 05 unit as an ``assistance`` unit of the SAME
``AssistanceCommitCoordinator`` used by the BE2-04 chain: it is mutually exclusive with every
foundation, Vision, assistance and 04 unit and with every coordinated owner publication. The
final token check (``hold``), CAS, inserts, receipts, intents and the 05 epoch bump all happen
under that one hold. Lock order: coordinator (outer) -> store lock (inner). Single-process fake
scope only; database fencing is a separate integration gate.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock

from sketch2life.application.ports.ai_jobs import OwnerFence, Principal, QuarantineIntent
from sketch2life.application.ports.sketch_review import (
    EligibilityChangedIntent,
    ReviewAuditRecord,
    ReviewDecisionToken,
    ReviewReceipt,
    ReviewRevisionConflict,
    ReviewUniqueConflict,
    StaleReviewDecision,
)
from sketch2life.domain.sketch_review import (
    ModerationKey,
    ModerationRecord,
    ReviewEntry,
    ReviewHead,
    ReviewTarget,
    VersionTerminalMarker,
)
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeOwnerFences,
    artifact_fence_scope,
    eligibility_fence_scope,
    grant_fence_scope,
)
from sketch2life.infrastructure.assistance.fakes import (
    AssistanceCommitCoordinator,
    analysis_fence_scope,
)
from sketch2life.infrastructure.sketch_generation.adapters import sketch_policy_fence_scope

FIXTURE_MARKER = "BE2-05 synthetic fixture — not a production adapter"


def review_policy_fence_scope(organization_id: str) -> str:
    return f"review-policy:{organization_id}"


def review_context_fence_scope(organization_id: str, session_id: str) -> str:
    return f"review-context:{organization_id}:{session_id}"


def sketch_review_fence_scope(organization_id: str, proposal_id: str) -> str:
    return f"sketch-review:{organization_id}:{proposal_id}"


# ------------------------------------------------------------------ token
class CoordinatedReviewTokens:
    """Token = superset of the SK1 decision scopes + every promoted ref + 05 scopes (§4.6)."""

    def __init__(self, fences: FakeOwnerFences, coordinator: AssistanceCommitCoordinator) -> None:
        self._fences = fences
        self._coordinator = coordinator

    @staticmethod
    def scopes(target: ReviewTarget, principal: Principal) -> tuple[str, ...]:
        org = target.organization_id
        return (eligibility_fence_scope(org), analysis_fence_scope(org),
                sketch_policy_fence_scope(org),
                *(artifact_fence_scope(ref) for ref in target.ref_set),
                grant_fence_scope(org, principal.principal_id),
                review_policy_fence_scope(org),
                review_context_fence_scope(org, target.session_id))

    def token(self, target: ReviewTarget, principal: Principal) -> ReviewDecisionToken:
        scopes = self.scopes(target, principal)

        def read() -> tuple[tuple[str, int], ...]:
            return tuple((scope, self._fences.epochs[scope]) for scope in scopes)

        epochs = self._coordinator.read(read)
        assert isinstance(epochs, tuple)
        return ReviewDecisionToken(target.organization_id, epochs, target.identity())

    def generation(self, organization_id: str, session_id: str) -> tuple[tuple[str, int], ...]:
        scopes = (review_policy_fence_scope(organization_id),
                  review_context_fence_scope(organization_id, session_id))

        def read() -> tuple[tuple[str, int], ...]:
            return tuple((scope, self._fences.epochs[scope]) for scope in scopes)

        value = self._coordinator.read(read)
        assert isinstance(value, tuple)
        return value


class ReviewEligibilityEpochs:
    def __init__(self, fences: FakeOwnerFences, coordinator: AssistanceCommitCoordinator) -> None:
        self._fences = fences
        self._coordinator = coordinator

    def epoch(self, organization_id: str, proposal_id: str) -> int:
        scope = sketch_review_fence_scope(organization_id, proposal_id)
        value = self._coordinator.read(lambda: self._fences.epochs[scope])
        assert isinstance(value, int)
        return value


# ------------------------------------------------------------------ store
@dataclass
class _State:
    heads: dict[str, ReviewHead] = field(default_factory=dict)
    entries: dict[str, tuple[ReviewEntry, ...]] = field(default_factory=dict)
    markers: dict[tuple[str, int, str], VersionTerminalMarker] = field(default_factory=dict)
    moderation: dict[ModerationKey, ModerationRecord] = field(default_factory=dict)
    receipts: dict[str, ReviewReceipt] = field(default_factory=dict)
    intents: list[EligibilityChangedIntent] = field(default_factory=list)
    quarantine: dict[str, QuarantineIntent] = field(default_factory=dict)
    delivered: set[str] = field(default_factory=set)
    audit: list[ReviewAuditRecord] = field(default_factory=list)
    notices: set[str] = field(default_factory=set)

    def copy(self) -> _State:
        return _State(dict(self.heads), dict(self.entries), dict(self.markers),
                      dict(self.moderation), dict(self.receipts), list(self.intents),
                      dict(self.quarantine), set(self.delivered), list(self.audit),
                      set(self.notices))


class _UnitOfWork:
    def __init__(self, state: _State, fences: FakeOwnerFences) -> None:
        self._s = state
        self._fences = fences
        self.touched: set[tuple[str, str]] = set()

    def hold(self, token: ReviewDecisionToken) -> None:
        result = self._fences.hold(tuple(OwnerFence(scope, epoch)
                                         for scope, epoch in token.epochs))
        if not result.current:
            raise StaleReviewDecision()

    def get_head(self, proposal_id: str) -> ReviewHead | None:
        return self._s.heads.get(proposal_id)

    def put_head(self, *, expected_decision_revision: int | None, head: ReviewHead) -> None:
        current = self._s.heads.get(head.proposal_id)
        stored = 0 if current is None else current.decision_revision
        if expected_decision_revision is not None and stored != expected_decision_revision:
            raise ReviewRevisionConflict()
        self._s.heads[head.proposal_id] = head

    def entries(self, proposal_id: str) -> tuple[ReviewEntry, ...]:
        return self._s.entries.get(proposal_id, ())

    def put_entries(self, proposal_id: str, entries: tuple[ReviewEntry, ...]) -> None:
        old = {e.review_id: e for e in self._s.entries.get(proposal_id, ())}
        new_ids = {e.review_id for e in entries}
        if not set(old) <= new_ids:  # append-only: entries are never removed
            raise ReviewUniqueConflict("entry removal")
        for entry in entries:
            previous = old.get(entry.review_id)
            if previous is not None and (previous.decision, previous.key) != (
                entry.decision, entry.key
            ):
                raise ReviewUniqueConflict("entry rewrite")
        self._s.entries[proposal_id] = entries

    def get_marker(self, proposal_id: str, version: int,
                   content_sha256: str) -> VersionTerminalMarker | None:
        return self._s.markers.get((proposal_id, version, content_sha256))

    def insert_marker(self, marker: VersionTerminalMarker) -> None:
        key = (marker.proposal_id, marker.proposal_version, marker.content_sha256)
        if key in self._s.markers:
            raise ReviewUniqueConflict("marker")
        self._s.markers[key] = marker

    def get_moderation(self, key: ModerationKey) -> ModerationRecord | None:
        return self._s.moderation.get(key)

    def put_moderation(self, record: ModerationRecord) -> None:
        if record.key in self._s.moderation:
            raise ReviewUniqueConflict("moderation")
        self._s.moderation[record.key] = record

    def get_receipt(self, key: str) -> ReviewReceipt | None:
        return self._s.receipts.get(key)

    def put_receipt(self, receipt: ReviewReceipt) -> None:
        if receipt.key in self._s.receipts:
            raise ReviewUniqueConflict("receipt")
        self._s.receipts[receipt.key] = receipt

    def add_intent(self, intent: EligibilityChangedIntent) -> None:
        if all(i.event_id != intent.event_id for i in self._s.intents):
            self._s.intents.append(intent)

    def add_quarantine(self, intent: QuarantineIntent) -> None:
        self._s.quarantine.setdefault(intent.event_id, intent)

    def pending_quarantine(self) -> tuple[QuarantineIntent, ...]:
        return tuple(i for k, i in self._s.quarantine.items() if k not in self._s.delivered)

    def mark_quarantine_delivered(self, event_id: str) -> None:
        self._s.delivered.add(event_id)

    def add_audit(self, record: ReviewAuditRecord) -> None:
        if all(a.event_id != record.event_id for a in self._s.audit):
            self._s.audit.append(record)

    def notice_seen(self, notice_id: str) -> bool:
        return notice_id in self._s.notices

    def record_notice(self, notice_id: str) -> None:
        self._s.notices.add(notice_id)

    def touch(self, organization_id: str, proposal_id: str) -> None:
        self.touched.add((organization_id, proposal_id))


class InMemorySketchReviewStore:
    """All-or-nothing fake unit of work (staged copy, commit on clean exit)."""

    marker = FIXTURE_MARKER

    def __init__(self, fences: FakeOwnerFences) -> None:
        self._fences = fences
        self._state = _State()
        self._lock = RLock()
        self.fail_next_commit = False
        self.before_commit: Callable[[], object] | None = None
        self.commits = 0

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        with self._lock:
            staged = self._state.copy()
            uow = _UnitOfWork(staged, self._fences)
            yield uow
            hook = self.before_commit
            if hook is not None:
                self.before_commit = None
                hook()
            if self.fail_next_commit:
                self.fail_next_commit = False
                raise RuntimeError("injected sketch review commit failure")
            self._state = staged
            self.commits += 1
            self.last_touched = set(uow.touched)

    def snapshot(self) -> _State:
        with self._lock:
            return self._state.copy()


class CoordinatedSketchReviewRepository:
    """Each 05 unit is an ``assistance`` unit of the shared coordinator; the 05 eligibility
    epoch is bumped after the inner commit, still under the hold (rollback bumps nothing)."""

    def __init__(self, inner: InMemorySketchReviewStore, coordinator: AssistanceCommitCoordinator,
                 fences: FakeOwnerFences) -> None:
        self.inner = inner
        self._coordinator = coordinator
        self._fences = fences

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        with self._coordinator.assistance():
            with self.inner.transaction() as tx:
                yield tx
            for organization_id, proposal_id in sorted(tx.touched):
                self._fences.bump(sketch_review_fence_scope(organization_id, proposal_id))


__all__ = [
    "FIXTURE_MARKER",
    "CoordinatedReviewTokens",
    "CoordinatedSketchReviewRepository",
    "InMemorySketchReviewStore",
    "ReviewEligibilityEpochs",
    "review_context_fence_scope",
    "review_policy_fence_scope",
    "sketch_review_fence_scope",
]
