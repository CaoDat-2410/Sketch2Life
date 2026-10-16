"""Deterministic BE2-02 C1 fakes with fault injection (fixture use only).

The store simulates one authoritative transaction with a process-local lock and a staged copy:
everything written inside a failed or conflicting unit of work is discarded. It is not durable
storage or database isolation and must never be wired into the live app. Owner fakes model the
proposed BE1/BE2-03/BE2-01 protocols only (ASSUMED_CONTRACT); they prove no real integration.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.ports.vision_analysis import (
    AnalysisAction,
    AnalysisRevisionConflict,
    AnalysisStorageUnavailable,
    AnalysisUniqueConflict,
    AuthorityDecision,
    AuthorityReason,
    ContextDecision,
    CorrectionReceipt,
    CorrectionScopeKey,
    ObservationOutcome,
    ObservationRequest,
    ObservationSucceeded,
)
from sketch2life.domain.ai_jobs.completion import canonical_json, canonical_sha256
from sketch2life.domain.vision_analysis import (
    ActorRef,
    ActorRole,
    AdmissionReceipt,
    AnalysisHead,
    AnalysisScope,
    AssistancePin,
    EntityObservation,
    EvidenceKind,
    InvalidationIntent,
    JobLineageView,
    LexicalOutcome,
    MeaningCorrection,
    ModerationOutcome,
    ObservationEvidence,
    ObservedLabel,
    OriginalObservation,
    ProviderContextMode,
    ProviderResultRecord,
    SourceSnapshot,
    VisionObservation,
)

FIXTURE_MARKER = "FIXTURE_ONLY_NOT_DURABLE"


@dataclass
class _AnalysisState:
    heads: dict[str, AnalysisHead] = field(default_factory=dict)
    observations: dict[str, VisionObservation] = field(default_factory=dict)
    provider_results: dict[str, ProviderResultRecord] = field(default_factory=dict)
    attempts: dict[tuple[str, str], str] = field(default_factory=dict)
    corrections: dict[str, MeaningCorrection] = field(default_factory=dict)
    correction_order: dict[str, tuple[str, ...]] = field(default_factory=dict)
    receipts: dict[CorrectionScopeKey, CorrectionReceipt] = field(default_factory=dict)
    invalidations: dict[str, InvalidationIntent] = field(default_factory=dict)
    invalidation_order: tuple[str, ...] = ()
    notices: frozenset[str] = frozenset()

    def copy(self) -> _AnalysisState:
        return _AnalysisState(
            heads=dict(self.heads),
            observations=dict(self.observations),
            provider_results=dict(self.provider_results),
            attempts=dict(self.attempts),
            corrections=dict(self.corrections),
            correction_order=dict(self.correction_order),
            receipts=dict(self.receipts),
            invalidations=dict(self.invalidations),
            invalidation_order=self.invalidation_order,
            notices=self.notices,
        )


class _UnitOfWork:
    def __init__(self, state: _AnalysisState) -> None:
        self.state = state
        # Only a unit of work that staged a write can fail at commit (fault injection).
        self.dirty = False

    def get_head(self, analysis_id: str) -> AnalysisHead | None:
        return self.state.heads.get(analysis_id)

    def find_by_attempt(self, job_id: str, attempt_id: str) -> str | None:
        return self.state.attempts.get((job_id, attempt_id))

    def insert_head(self, head: AnalysisHead) -> None:
        self.dirty = True
        key = (head.lineage.job_id, head.lineage.job_attempt_id)
        if head.analysis_id in self.state.heads or key in self.state.attempts:
            raise AnalysisUniqueConflict("analysis")
        self.state.heads[head.analysis_id] = head
        self.state.attempts[key] = head.analysis_id

    def cas_head(self, *, expected_revision: int, head: AnalysisHead) -> None:
        self.dirty = True
        current = self.state.heads.get(head.analysis_id)
        if current is None or current.analysis_revision != expected_revision:
            raise AnalysisRevisionConflict("analysis revision moved")
        if head.analysis_revision != expected_revision + 1:
            raise AnalysisRevisionConflict("replacement must advance the revision by one")
        if current.observation_sha256 != head.observation_sha256:
            raise AnalysisRevisionConflict("the original observation is immutable")
        self.state.heads[head.analysis_id] = head

    def insert_observation(self, observation: VisionObservation) -> None:
        self.dirty = True
        if observation.analysis_id in self.state.observations:
            raise AnalysisUniqueConflict("observation")
        self.state.observations[observation.analysis_id] = observation

    def get_observation(self, analysis_id: str) -> VisionObservation | None:
        return self.state.observations.get(analysis_id)

    def insert_provider_result(self, record: ProviderResultRecord) -> None:
        self.dirty = True
        if record.result_ref in self.state.provider_results:
            raise AnalysisUniqueConflict("provider_result")
        self.state.provider_results[record.result_ref] = record

    def get_provider_result(self, result_ref: str) -> ProviderResultRecord | None:
        return self.state.provider_results.get(result_ref)

    def append_correction(self, correction: MeaningCorrection) -> None:
        self.dirty = True
        if correction.correction_id in self.state.corrections:
            raise AnalysisUniqueConflict("correction")
        self.state.corrections[correction.correction_id] = correction
        order = self.state.correction_order.get(correction.analysis_id, ())
        self.state.correction_order[correction.analysis_id] = (*order, correction.correction_id)

    def get_correction(self, correction_id: str) -> MeaningCorrection | None:
        return self.state.corrections.get(correction_id)

    def list_corrections(self, analysis_id: str) -> tuple[MeaningCorrection, ...]:
        ids = self.state.correction_order.get(analysis_id, ())
        return tuple(self.state.corrections[correction_id] for correction_id in ids)

    def get_receipt(self, key: CorrectionScopeKey) -> CorrectionReceipt | None:
        return self.state.receipts.get(key)

    def put_receipt(self, receipt: CorrectionReceipt) -> None:
        self.dirty = True
        if receipt.scope_key in self.state.receipts:
            raise AnalysisUniqueConflict("correction_receipt")
        self.state.receipts[receipt.scope_key] = receipt

    def add_invalidation(self, intent: InvalidationIntent) -> None:
        self.dirty = True
        if intent.event_id in self.state.invalidations:
            raise AnalysisUniqueConflict("invalidation")
        self.state.invalidations[intent.event_id] = intent
        self.state.invalidation_order = (*self.state.invalidation_order, intent.event_id)

    def notice_seen(self, notice_id: str) -> bool:
        return notice_id in self.state.notices

    def record_notice(self, notice_id: str) -> None:
        self.dirty = True
        if notice_id in self.state.notices:
            raise AnalysisUniqueConflict("notice")
        self.state.notices = self.state.notices | {notice_id}


class InMemoryAnalysisStore:
    """Staged, all-or-nothing fake unit of work guarded by one re-entrant lock."""

    marker = FIXTURE_MARKER

    def __init__(self) -> None:
        self._state = _AnalysisState()
        self._lock = RLock()
        self.fail_next_commit = False
        self.commits = 0

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        with self._lock:
            staged = self._state.copy()
            unit = _UnitOfWork(staged)
            yield unit
            if self.fail_next_commit and unit.dirty:
                self.fail_next_commit = False
                raise AnalysisStorageUnavailable("injected commit failure")
            self._state = staged
            self.commits += 1

    def snapshot(self) -> _AnalysisState:
        with self._lock:
            return self._state.copy()

    def invalidations(self) -> tuple[InvalidationIntent, ...]:
        state = self.snapshot()
        return tuple(state.invalidations[event_id] for event_id in state.invalidation_order)


# --------------------------------------------------------------------- owner fakes
class FakeAnalysisSource:
    """Opaque snapshot ref -> checkpoint/render metadata, plus render bytes for the bridge."""

    def __init__(self) -> None:
        self.snapshots: dict[str, SourceSnapshot] = {}
        self.render_bytes: dict[str, bytes] = {}

    def add(self, snapshot: SourceSnapshot, image: bytes | None = None) -> None:
        self.snapshots[snapshot.snapshot_ref] = snapshot
        if image is not None:
            self.render_bytes[snapshot.render.render_ref] = image

    def resolve(self, snapshot_ref: str, *, organization_id: str) -> SourceSnapshot | None:
        snapshot = self.snapshots.get(snapshot_ref)
        if snapshot is None or snapshot.organization_id != organization_id:
            return None
        return snapshot

    def read_render(self, render_ref: str) -> bytes:
        return self.render_bytes[render_ref]


class FakeAdmission:
    def __init__(self) -> None:
        self._receipts: dict[tuple[str, str, str], AdmissionReceipt] = {}

    def add(self, receipt: AdmissionReceipt, *, organization_id: str) -> None:
        self._receipts[(organization_id, receipt.render_ref, receipt.render_sha256)] = receipt

    def clear(self) -> None:
        self._receipts.clear()

    def receipt_for(
        self, render_ref: str, render_sha256: str, *, organization_id: str
    ) -> AdmissionReceipt | None:
        return self._receipts.get((organization_id, render_ref, render_sha256))


@dataclass
class DeviceBinding:
    """Server-side device binding to one session/canvas/group participant and turn."""

    organization_id: str
    session_id: str
    canvas_id: str
    group_id: str | None
    participant_id: str
    turn_id: str | None
    turn_open: bool = True


@dataclass(frozen=True, slots=True)
class TeacherGrant:
    organization_id: str
    class_ids: frozenset[str]
    session_ids: frozenset[str] | None = None


class FakeAnalysisAuthority:
    """Teacher grants and device bindings; revocation and turn closing are explicit."""

    def __init__(self) -> None:
        self.teachers: dict[str, TeacherGrant] = {}
        self.devices: dict[str, DeviceBinding] = {}
        self.revoked: set[str] = set()
        self.calls: list[tuple[str, AnalysisAction]] = []

    def grant_teacher(self, principal_id: str, grant: TeacherGrant) -> None:
        self.teachers[principal_id] = grant

    def bind_device(self, principal_id: str, binding: DeviceBinding) -> None:
        self.devices[principal_id] = binding

    def revoke(self, principal_id: str) -> None:
        self.revoked.add(principal_id)

    def close_turn(self, principal_id: str) -> None:
        self.devices[principal_id].turn_open = False

    def decide(
        self, principal: Principal, action: AnalysisAction, scope: AnalysisScope
    ) -> AuthorityDecision:
        self.calls.append((principal.principal_id, action))
        if principal.organization_id != scope.organization_id:
            return AuthorityDecision(False, AuthorityReason.NOT_IN_SCOPE)
        if principal.role is PrincipalRole.TEACHER:
            return self._teacher(principal, action, scope)
        if principal.role is PrincipalRole.DEVICE:
            return self._device(principal, action, scope)
        if action is AnalysisAction.READ_ANALYSIS:
            return AuthorityDecision(False, AuthorityReason.NOT_IN_SCOPE)
        return AuthorityDecision(False, AuthorityReason.ROLE_NOT_PERMITTED)

    def _teacher(
        self, principal: Principal, action: AnalysisAction, scope: AnalysisScope
    ) -> AuthorityDecision:
        grant = self.teachers.get(principal.principal_id)
        if grant is None or grant.organization_id != scope.organization_id:
            return AuthorityDecision(False, AuthorityReason.NOT_IN_SCOPE)
        if scope.class_id not in grant.class_ids or (
            grant.session_ids is not None and scope.session_id not in grant.session_ids
        ):
            return AuthorityDecision(False, AuthorityReason.NOT_IN_SCOPE)
        if principal.principal_id in self.revoked:
            return AuthorityDecision(False, AuthorityReason.GRANT_REVOKED)
        if action is AnalysisAction.PROPOSE_INTENT:
            return AuthorityDecision(False, AuthorityReason.ROLE_NOT_PERMITTED)
        return AuthorityDecision(True, actor=ActorRef(principal.principal_id, ActorRole.TEACHER))

    def _device(
        self, principal: Principal, action: AnalysisAction, scope: AnalysisScope
    ) -> AuthorityDecision:
        binding = self.devices.get(principal.principal_id)
        if (
            binding is None
            or binding.organization_id != scope.organization_id
            or binding.session_id != scope.session_id
            or binding.canvas_id != scope.canvas_id
            or binding.group_id != scope.group_id
            or binding.participant_id != scope.contributor_participant_id
        ):
            # Another child's or another canvas's analysis is concealed, not just forbidden.
            return AuthorityDecision(False, AuthorityReason.NOT_IN_SCOPE)
        if principal.principal_id in self.revoked:
            return AuthorityDecision(False, AuthorityReason.GRANT_REVOKED)
        if action is AnalysisAction.CONFIRM_MEANING:
            return AuthorityDecision(False, AuthorityReason.ROLE_NOT_PERMITTED)
        if action is AnalysisAction.READ_ANALYSIS:
            # Disclosure of the device's own receipts survives a closed turn.
            return AuthorityDecision(True)
        if binding.turn_id is None:
            return AuthorityDecision(False, AuthorityReason.TURN_UNBOUND)
        if not binding.turn_open:
            return AuthorityDecision(False, AuthorityReason.TURN_CLOSED)
        return AuthorityDecision(
            True,
            actor=ActorRef(
                principal.principal_id,
                ActorRole.CHILD_DEVICE,
                participant_id=binding.participant_id,
                turn_id=binding.turn_id,
            ),
        )


@dataclass
class _ContextRow:
    revision: int
    session_active: bool = True
    topic_ref: str | None = None
    age_policy_ref: str | None = "age-policy:36-155-months:proposed"


class FakeAnalysisContext:
    """Context revision per (session, canvas); consent/purpose/age per participant.

    ``on_current`` is a one-shot hook run before the next decision, used to interleave a
    concurrent writer or an in-flight context change deterministically.
    """

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], _ContextRow] = {}
        self.consent: dict[str, bool] = {}
        self.purposes: dict[str, frozenset[str]] = {}
        self.ages: dict[str, int | None] = {}
        self.on_current: Callable[[], object] | None = None

    def set_context(self, session_id: str, canvas_id: str, revision: int,
                    topic_ref: str | None = None) -> None:
        self.rows[(session_id, canvas_id)] = _ContextRow(revision, topic_ref=topic_ref)

    def set_participant(self, participant_id: str, *, age_months: int | None,
                        purposes: frozenset[str], consent: bool = True) -> None:
        self.ages[participant_id] = age_months
        self.purposes[participant_id] = purposes
        self.consent[participant_id] = consent

    def bump(self, session_id: str, canvas_id: str) -> int:
        row = self.rows[(session_id, canvas_id)]
        row.revision += 1
        return row.revision

    def end_session(self, session_id: str) -> None:
        for (session, _), row in self.rows.items():
            if session == session_id:
                row.session_active = False

    def revoke_consent(self, participant_id: str) -> None:
        self.consent[participant_id] = False

    def current(self, scope: AnalysisScope) -> ContextDecision:
        hook, self.on_current = self.on_current, None
        if hook is not None:
            hook()
        row = self.rows[(scope.session_id, scope.canvas_id)]
        audience = scope.audience_participant_ids
        return ContextDecision(
            context_revision=row.revision,
            consent_effective=all(self.consent.get(p, False) for p in audience),
            purpose_granted=all(scope.purpose_code in self.purposes.get(p, frozenset())
                                for p in audience),
            session_active=row.session_active,
            audience_age_months=tuple((p, self.ages.get(p)) for p in audience if p in self.ages),
            topic_ref=row.topic_ref,
            age_policy_ref=row.age_policy_ref,
        )


class FakeAssistanceRequests:
    def __init__(self) -> None:
        self.pins: dict[str, AssistancePin] = {}

    def add(self, pin: AssistancePin) -> None:
        self.pins[pin.assistance_id] = pin

    def get(self, assistance_id: str) -> AssistancePin | None:
        return self.pins.get(assistance_id)


class FakeJobLineage:
    def __init__(self) -> None:
        self.jobs: dict[str, JobLineageView] = {}

    def set(self, view: JobLineageView) -> None:
        self.jobs[view.job_id] = view

    def get(self, job_id: str) -> JobLineageView | None:
        return self.jobs.get(job_id)


# ------------------------------------------------------------------ fake provider
def synthetic_observation(
    entities: tuple[tuple[str, str, float | None], ...] = (("ent-1", "cat", 0.62),),
) -> OriginalObservation:
    return OriginalObservation(
        entities=tuple(
            EntityObservation(observation_id, ObservedLabel(label, "DECLARED", ("en",)), conf)
            for observation_id, label, conf in entities
        ),
        actions=(),
        relations=(),
        themes=(),
        ambiguous_regions=(),
    )


def synthetic_success(
    request: ObservationRequest,
    observation: OriginalObservation | None = None,
    *,
    executed_at: datetime,
) -> ObservationSucceeded:
    """Synthetic-fake evidence: no model, no profile, explicit ``synthetic_fake`` kind."""

    observed = observation or synthetic_observation()
    return ObservationSucceeded(
        observation=observed,
        evidence=ObservationEvidence(
            evidence_kind=EvidenceKind.SYNTHETIC_FAKE,
            provider_context_mode=request.context_mode,
            adapter_id="fake-vision-observation",
            result_contract="SyntheticObservation/0.1-candidate",
            result_sha256=canonical_sha256(observed.canonical()),
            executed_at=executed_at,
            transport_attempts=0,
        ),
        moderation=ModerationOutcome(LexicalOutcome.NOT_EXECUTED, None, None),
        result_document=canonical_json(observed.canonical()),
    )


class FakeVisionObservationProvider:
    """Accepts the new observation envelope, including typed context, for protocol tests."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime],
        supported: frozenset[ProviderContextMode] = frozenset(ProviderContextMode),
        observation: OriginalObservation | None = None,
    ) -> None:
        self._clock = clock
        self._supported = supported
        self.observation = observation
        self.scripted: list[ObservationOutcome] = []
        self.requests: list[ObservationRequest] = []
        self.on_observe: Callable[[], object] | None = None

    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]:
        return self._supported

    def observe(self, request: ObservationRequest) -> ObservationOutcome:
        self.requests.append(request)
        hook, self.on_observe = self.on_observe, None
        if hook is not None:
            hook()
        if self.scripted:
            return self.scripted.pop(0)
        return synthetic_success(request, self.observation, executed_at=self._clock())


__all__ = [
    "FIXTURE_MARKER",
    "DeviceBinding",
    "FakeAdmission",
    "FakeAnalysisAuthority",
    "FakeAnalysisContext",
    "FakeAnalysisSource",
    "FakeAssistanceRequests",
    "FakeJobLineage",
    "FakeVisionObservationProvider",
    "InMemoryAnalysisStore",
    "TeacherGrant",
    "synthetic_observation",
    "synthetic_success",
]
