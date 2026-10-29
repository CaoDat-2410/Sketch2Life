"""BE2-03 deterministic fakes and the shared fake commit coordinator (fixture use only).

``AssistanceCommitCoordinator`` (plan rev3 §8.2, TC-11) is one re-entrant lock shared by the
coordinated BE2-01 repository decorator, this assistance store and the request-aware
eligibility adapter. Lock order is coordinator → foundation store lock. A foundation write
transaction is indivisible from its fence hold through its commit; an assistance publication
(request state + eligibility epoch) is atomic. A publication requested while the current thread
is inside a foundation transaction is deferred until that transaction exits. This is a fake
composition contract, not database isolation or a real OwnerFence.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock

from sketch2life.application.ports.ai_jobs import FenceResult, OwnerFence, Principal, PrincipalRole
from sketch2life.application.ports.assistance import (
    AssistanceAuthority,
    AssistanceEvent,
    AssistanceRevisionConflict,
    AssistanceUniqueConflict,
    AuthorityReason,
    CanvasFacts,
    CommandReceipt,
    GroupRoster,
    ReceiptKey,
    ResolvedSource,
    SketchIntent,
)
from sketch2life.domain.assistance import (
    FIXTURE_POLICY_STATUS,
    NON_TERMINAL,
    AssistanceRequest,
    CacheHit,
    CheckpointRef,
    Contributor,
    MemberFact,
    PolicySnapshot,
    ReservationState,
    TargetKind,
)
from sketch2life.infrastructure.ai_jobs.fakes import FakeOwnerFences, eligibility_fence_scope

FIXTURE_MARKER = "FIXTURE_ONLY_NOT_DURABLE"


_UNIT_KINDS = ("foundation", "vision", "assistance")


def analysis_fence_scope(organization_id: str) -> str:
    """Fake analysis epoch (A1-CR03-F2); separate from BE2-01's eligibility fence."""

    return f"analysis:{organization_id}"


class CoordinationError(RuntimeError):
    """A unit was opened across the coordinated boundary in a forbidden direction."""


# ------------------------------------------------------------------------ coordinator
class AssistanceCommitCoordinator:
    def __init__(self) -> None:
        self._lock = RLock()
        self._local = threading.local()
        self.deferred_failures: list[BaseException] = []
        self.commit_log: list[str] = []

    def _depth(self, name: str) -> int:
        return int(getattr(self._local, name, 0))

    def _set(self, name: str, value: int) -> None:
        setattr(self._local, name, value)

    def _queue(self) -> list[Callable[[], object]]:
        queue = getattr(self._local, "deferred", None)
        if queue is None:
            queue = []
            self._local.deferred = queue
        assert isinstance(queue, list)
        return queue

    def in_foundation(self) -> bool:
        return self._depth("foundation") > 0

    def in_assistance(self) -> bool:
        return self._depth("assistance") > 0

    def in_atomic_unit(self) -> bool:
        return any(self._depth(kind) > 0 for kind in _UNIT_KINDS)

    @contextmanager
    def foundation(self, label: str = "foundation") -> Iterator[None]:
        """Whole BE2-01 write transaction, hold through commit/rollback."""

        with self._external_unit("foundation", label):
            yield

    @contextmanager
    def vision(self, label: str = "vision") -> Iterator[None]:
        """Whole BE2-02 Vision transaction (A1-CR03-F2), read or write, through commit."""

        with self._external_unit("vision", label):
            yield

    @contextmanager
    def _external_unit(self, kind: str, label: str) -> Iterator[None]:
        if self._depth("assistance") > 0:
            raise CoordinationError(f"{kind} called while an assistance transaction is open")
        self._lock.acquire()
        self._set(kind, self._depth(kind) + 1)
        committed = False
        try:
            yield
            committed = True
        finally:
            depth = self._depth(kind) - 1
            self._set(kind, depth)
            if committed and depth == 0:
                self.commit_log.append(label)
            self._release_and_drain()

    @contextmanager
    def assistance(self) -> Iterator[None]:
        """Assistance unit: request state and epoch are published together."""

        if self._depth("foundation") > 0 or self._depth("vision") > 0:
            raise CoordinationError(
                "assistance publication inside a foundation/vision transaction; request it")
        self._lock.acquire()
        self._set("assistance", self._depth("assistance") + 1)
        try:
            yield
        finally:
            self._set("assistance", self._depth("assistance") - 1)
            self._release_and_drain()

    def _release_and_drain(self) -> None:
        """Release one hold; once this thread is outside every atomic unit, run the
        publications it requested meanwhile, each separately under the coordinator."""

        deferred = [] if self.in_atomic_unit() else self._take_deferred()
        self._lock.release()
        for publication in deferred:
            self._run_deferred(publication)

    def read(self, reader: Callable[[], object]) -> object:
        """Consistent snapshot read (re-entrant; allowed inside any atomic unit)."""

        with self._lock:
            return reader()

    def request_publication(self, publication: Callable[[], object]) -> bool:
        """Run now, or defer until this thread's outermost atomic unit (foundation, vision or
        assistance) exits on commit or rollback. Returns whether it ran immediately."""

        if self.in_atomic_unit():  # A1-CR03-F1: never inside an assistance unit either
            self._queue().append(publication)
            return False
        # A1-CR02: the publication itself runs under the coordinator, so it can never commit
        # inside another thread's atomic unit.
        with self._lock:
            publication()
        return True

    def _take_deferred(self) -> list[Callable[[], object]]:
        queue = self._queue()
        taken = list(queue)
        queue.clear()
        return taken

    def _run_deferred(self, publication: Callable[[], object]) -> None:
        try:
            with self._lock:  # A1-CR02: serialized like an immediate publication
                publication()
        except Exception as exc:  # a failed deferred publication publishes nothing
            self.deferred_failures.append(exc)


class HookedOwnerFences(FakeOwnerFences):
    """Owner fences with a one-shot hook after a successful hold (post-hold/pre-commit seam)."""

    def __init__(self) -> None:
        super().__init__()
        self.after_successful_hold: Callable[[], object] | None = None

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        result = super().hold(fences)
        hook = self.after_successful_hold
        if result.current and hook is not None:
            self.after_successful_hold = None
            hook()
        return result


# ---------------------------------------------------------------------- store
@dataclass
class _State:
    requests: dict[str, AssistanceRequest] = field(default_factory=dict)
    receipts: dict[ReceiptKey, CommandReceipt] = field(default_factory=dict)
    cache: dict[tuple[str, str], CacheHit] = field(default_factory=dict)
    events: list[AssistanceEvent] = field(default_factory=list)
    intents: list[SketchIntent] = field(default_factory=list)
    notices: set[str] = field(default_factory=set)

    def copy(self) -> _State:
        return _State(dict(self.requests), dict(self.receipts), dict(self.cache),
                      list(self.events), list(self.intents), set(self.notices))


class _UnitOfWork:
    def __init__(self, state: _State, fences: FakeOwnerFences) -> None:
        self._s = state
        self._fences = fences
        self.fence_bumps: set[str] = set()

    def decision_epoch(self, organization_id: str) -> tuple[int, int]:
        """Committed decision token, read under the coordinator: the owner/request epoch
        and the analysis epoch bumped by every committed coordinated Vision write."""

        return (self._fences.epochs[eligibility_fence_scope(organization_id)],
                self._fences.epochs[analysis_fence_scope(organization_id)])

    def get(self, assistance_id: str) -> AssistanceRequest | None:
        return self._s.requests.get(assistance_id)

    def insert(self, request: AssistanceRequest) -> None:
        if request.assistance_id in self._s.requests:
            raise AssistanceUniqueConflict("assistance_id")
        org = request.facts.organization_id
        if request.status in NON_TERMINAL and self.find_active_semantic(
            org, request.semantic_identity
        ) is not None:
            raise AssistanceUniqueConflict("semantic_identity")
        self._s.requests[request.assistance_id] = request

    def cas(self, *, expected_record_version: int, request: AssistanceRequest) -> None:
        current = self._s.requests.get(request.assistance_id)
        if current is None or current.record_version != expected_record_version:
            raise AssistanceRevisionConflict(request.assistance_id)
        self._s.requests[request.assistance_id] = request

    def find_active_semantic(self, organization_id: str, identity: str) -> str | None:
        for request in self._s.requests.values():
            if (request.facts.organization_id == organization_id
                    and request.status in NON_TERMINAL
                    and request.semantic_identity == identity):
                return request.assistance_id
        return None

    def active_by_operation_target(
        self, organization_id: str, key: str
    ) -> tuple[AssistanceRequest, ...]:
        return tuple(
            r for r in self._s.requests.values()
            if r.facts.organization_id == organization_id and r.status in NON_TERMINAL
            and r.operation_target == key
        )

    def latest_counted(self, organization_id: str, debounce_key: str) -> datetime | None:
        times = [r.created_at for r in self._s.requests.values()
                 if r.facts.organization_id == organization_id and r.counts_for_debounce
                 and r.debounce_key == debounce_key]
        return max(times) if times else None

    def count_reserved(self, organization_id: str, session_id: str,
                       target_key: str | None) -> int:
        return sum(
            1 for r in self._s.requests.values()
            if r.facts.organization_id == organization_id and r.facts.session_id == session_id
            and r.reservation in {ReservationState.HELD, ReservationState.CONSUMED}
            and (target_key is None or r.facts.target.key() == target_key)
        )

    def get_receipt(self, key: ReceiptKey) -> CommandReceipt | None:
        return self._s.receipts.get(key)

    def put_receipt(self, receipt: CommandReceipt) -> None:
        if receipt.key in self._s.receipts:
            raise AssistanceUniqueConflict("receipt")
        self._s.receipts[receipt.key] = receipt

    def find_cache(self, organization_id: str, identity: str) -> CacheHit | None:
        return self._s.cache.get((organization_id, identity))

    def put_cache(self, organization_id: str, identity: str, hit: CacheHit) -> None:
        self._s.cache[(organization_id, identity)] = hit

    def add_event(self, event: AssistanceEvent) -> None:
        if all(e.event_id != event.event_id for e in self._s.events):
            self._s.events.append(event)

    def add_sketch_intent(self, intent: SketchIntent) -> None:
        self._s.intents.append(intent)

    def notice_seen(self, notice_id: str) -> bool:
        return notice_id in self._s.notices

    def record_notice(self, notice_id: str) -> None:
        self._s.notices.add(notice_id)

    def list_requests(self, organization_id: str) -> tuple[AssistanceRequest, ...]:
        return tuple(r for r in self._s.requests.values()
                     if r.facts.organization_id == organization_id)

    def publish_request_fence(self, organization_id: str) -> None:
        self.fence_bumps.add(organization_id)


class InMemoryAssistanceStore:
    """Staged all-or-nothing assistance unit of work under the shared coordinator."""

    marker = FIXTURE_MARKER

    def __init__(self, coordinator: AssistanceCommitCoordinator,
                 fences: FakeOwnerFences) -> None:
        self._coordinator = coordinator
        self._fences = fences
        self._state = _State()
        self.fail_next_commit = False

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        with self._coordinator.assistance():
            staged = self._state.copy()
            uow = _UnitOfWork(staged, self._fences)
            yield uow
            if self.fail_next_commit:
                self.fail_next_commit = False
                raise RuntimeError("injected assistance commit failure")
            # State and eligibility epoch are published together, under the coordinator.
            self._state = staged
            for organization_id in sorted(uow.fence_bumps):
                self._fences.bump(eligibility_fence_scope(organization_id))
            if uow.fence_bumps:
                self._coordinator.commit_log.append("assistance")

    def peek(self, assistance_id: str) -> AssistanceRequest | None:
        """Committed state read (used inside a coordinator snapshot)."""

        return self._state.requests.get(assistance_id)

    def snapshot(self) -> _State:
        return self._state.copy()


# ------------------------------------------------------------------ owner fakes
@dataclass
class _Member:
    months: int | None
    age_provenance_ref: str
    age_revision: int
    consent_record_ref: str
    consent_revision: int
    consent_effective: bool
    purposes: frozenset[str]


class FakeAssistanceOwner:
    """Synthetic BE1 facts (ASSUMED_CONTRACT): canvases, rosters, members and turns."""

    def __init__(self) -> None:
        self.canvases: dict[str, CanvasFacts] = {}
        self.rosters: dict[tuple[str, str], GroupRoster] = {}
        self.member_rows: dict[str, _Member] = {}
        self.turns: dict[str, Contributor] = {}
        self.duplicate_roster: bool = False

    def canvas(self, organization_id: str, canvas_id: str) -> CanvasFacts | None:
        facts = self.canvases.get(canvas_id)
        if facts is None or facts.organization_id != organization_id:
            return None
        return facts

    def roster(self, session_id: str, group_id: str) -> GroupRoster | None:
        roster = self.rosters.get((session_id, group_id))
        if roster is not None and self.duplicate_roster:
            return GroupRoster(roster.group_id, (*roster.members, roster.members[0]),
                               roster.revision)
        return roster

    def members(self, organization_id: str, participant_ids: tuple[str, ...],
                purpose_code: str) -> tuple[MemberFact, ...]:
        facts: list[MemberFact] = []
        for participant in participant_ids:
            row = self.member_rows.get(participant)
            if row is None:
                facts.append(MemberFact(participant, None, "age_unknown", 1, "consent_none", 1,
                                        False, False))
                continue
            facts.append(MemberFact(participant, row.months, row.age_provenance_ref,
                                    row.age_revision, row.consent_record_ref,
                                    row.consent_revision, row.consent_effective,
                                    purpose_code in row.purposes))
        return tuple(facts)

    def current_turn(self, canvas_id: str) -> Contributor | None:
        return self.turns.get(canvas_id)

    def set_member(self, participant_id: str, *, months: int | None,
                   purposes: frozenset[str], consent: bool = True,
                   age_revision: int = 1, consent_revision: int = 1) -> None:
        self.member_rows[participant_id] = _Member(
            months, f"age_{participant_id}", age_revision, f"consent_{participant_id}",
            consent_revision, consent, purposes)

    def update_member(self, participant_id: str, **changes: object) -> None:
        row = self.member_rows[participant_id]
        for name, value in changes.items():
            setattr(row, name, value)


@dataclass
class DeviceBinding:
    organization_id: str
    session_id: str
    canvas_id: str
    participant_id: str
    turn_id: str | None
    turn_revision: int | None
    turn_open: bool = True


@dataclass(frozen=True, slots=True)
class TeacherScope:
    organization_id: str
    class_ids: frozenset[str]


class FakeAssistanceAuthority:
    def __init__(self) -> None:
        self.teachers: dict[str, TeacherScope] = {}
        self.devices: dict[str, DeviceBinding] = {}
        self.revoked: set[str] = set()
        self.disclosure_revoked: set[str] = set()

    def decide(self, principal: Principal, canvas: CanvasFacts) -> AssistanceAuthority:
        if principal.organization_id != canvas.organization_id:
            return AssistanceAuthority(False, AuthorityReason.NOT_IN_SCOPE)
        if principal.role is PrincipalRole.TEACHER:
            scope = self.teachers.get(principal.principal_id)
            if scope is None or canvas.class_id not in scope.class_ids:
                return AssistanceAuthority(False, AuthorityReason.NOT_IN_SCOPE)
            if principal.principal_id in self.revoked:
                return AssistanceAuthority(False, AuthorityReason.GRANT_REVOKED)
            return AssistanceAuthority(True)
        if principal.role is PrincipalRole.DEVICE:
            binding = self.devices.get(principal.principal_id)
            if binding is None or binding.canvas_id != canvas.canvas_id or (
                binding.session_id != canvas.session_id
            ):
                return AssistanceAuthority(False, AuthorityReason.NOT_IN_SCOPE)
            if principal.principal_id in self.revoked:
                return AssistanceAuthority(False, AuthorityReason.GRANT_REVOKED)
            if binding.turn_id is None or not binding.turn_open:
                return AssistanceAuthority(False, AuthorityReason.TURN_CLOSED)
            return AssistanceAuthority(True, contributor=Contributor(
                binding.participant_id, binding.turn_id, binding.turn_revision))
        return AssistanceAuthority(False, AuthorityReason.ROLE_NOT_PERMITTED)

    def disclose(self, principal: Principal, request: AssistanceRequest) -> bool:
        facts = request.facts
        if principal.organization_id != facts.organization_id or (
            principal.principal_id in self.disclosure_revoked
        ):
            return False
        if principal.role is PrincipalRole.TEACHER:
            scope = self.teachers.get(principal.principal_id)
            return scope is not None and facts.class_id in scope.class_ids
        if principal.role is PrincipalRole.DEVICE:
            binding = self.devices.get(principal.principal_id)
            # A device sees only individual requests for its bound participant (own receipts
            # survive a closed turn), never group requests or another child's request.
            return (binding is not None and binding.canvas_id == facts.canvas_id
                    and facts.target.kind is TargetKind.INDIVIDUAL
                    and facts.target.ref_id == binding.participant_id)
        return False


class FakeAssistanceSource:
    def __init__(self) -> None:
        self.sources: dict[tuple[str, str, str], ResolvedSource] = {}

    def add(self, organization_id: str, canvas_id: str, source: ResolvedSource) -> None:
        checkpoint_id = source.snapshot.checkpoint.checkpoint_id
        self.sources[(organization_id, canvas_id, checkpoint_id)] = source

    def resolve(self, organization_id: str, canvas_id: str,
                ref: CheckpointRef) -> ResolvedSource | None:
        return self.sources.get((organization_id, canvas_id, ref.checkpoint_id))


class FixtureAssistancePolicy:
    """D10: FIXTURE_ONLY adapter for the consumer policy proposal to BE2-14."""

    def __init__(self, snapshot: PolicySnapshot | None) -> None:
        self.snapshot = snapshot
        self.per_session: dict[str, PolicySnapshot | None] = {}

    def current(self, organization_id: str, session_id: str) -> PolicySnapshot | None:
        return self.per_session.get(session_id, self.snapshot)


def fixture_policy(**changes: object) -> PolicySnapshot:
    values: Mapping[str, object] = {
        "policy_id": "fixture-assistance-policy",
        "version": "1",
        "status": FIXTURE_POLICY_STATUS,
        "assistance_enabled": True,
        "allowed_levels": frozenset({"level_fx_1", "level_fx_2"}),
        "debounce_seconds": 5,
        "per_target_limit": 3,
        "per_session_limit": 20,
        "cache_enabled": True,
        "purpose_code": "ai_drawing_assistance",
        **changes,
    }
    return PolicySnapshot(**values)  # type: ignore[arg-type]


class RecordingSketchStage:
    """D8: records simulated intents; there is no producer and no generation."""

    def __init__(self) -> None:
        self.intents: list[SketchIntent] = []

    def request_sketch(self, intent: SketchIntent) -> None:
        self.intents.append(intent)


__all__ = [
    "FIXTURE_MARKER",
    "AssistanceCommitCoordinator",
    "CoordinationError",
    "DeviceBinding",
    "FakeAssistanceAuthority",
    "FakeAssistanceOwner",
    "FakeAssistanceSource",
    "FixtureAssistancePolicy",
    "HookedOwnerFences",
    "InMemoryAssistanceStore",
    "RecordingSketchStage",
    "TeacherScope",
    "analysis_fence_scope",
    "fixture_policy",
]
