"""BE2-04 SK1 in-memory fakes (FIXTURE_ONLY; not production adapters).

* ``InMemorySketchStore`` — staged all-or-nothing unit of work with token check.
* ``CounterDecisionPort`` — decision epochs for unit tests.
* ``FixtureSketchPolicy`` / ``fixture_sketch_policy`` — FIXTURE_ONLY policy.
* ``ScriptedSketchGenerator`` — scripted provider; bytes carry only a PNG signature.
* ``FixtureDerivedArtifactAdmission`` — structural admission over ``FakeArtifacts``.
* ``FakeSketchAuthority`` / ``ScriptedHandoffReader`` — owner fakes for service tests.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from threading import RLock

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.ports.sketch_generation import (
    AdmissionRefusal,
    CleanupIntent,
    DerivativeProvenance,
    GenerationOutcome,
    GenerationRequest,
    GenerationSucceeded,
    HandoffHint,
    HandoffRefusal,
    HandoffRefusalCode,
    ProviderCopyRef,
    SketchAction,
    SketchDecisionPort,
    SketchEvent,
    SketchHandoffV1,
    SketchReceipt,
    SketchRevisionConflict,
    SketchScope,
    SketchUniqueConflict,
    StagedArtifact,
    StaleDecision,
)
from sketch2life.domain.sketch_proposal import (
    FIXTURE_POLICY_STATUS,
    PNG_SIGNATURE,
    RESULT_DOCUMENT_MEDIA_TYPE,
    CurrentFacts,
    DecisionToken,
    DisplayMode,
    HandoffBinding,
    LevelOutputRule,
    OutputPart,
    PartRequirement,
    SketchPolicySnapshot,
    SketchProposal,
    StagedGeneration,
)
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeOwnerFences,
    eligibility_fence_scope,
)

FIXTURE_MARKER = "BE2-04 SK1 synthetic fixture — not a production adapter"
FIXTURE_GENERATOR_PROFILE = "fixture-sketch-profile-v0"


# ------------------------------------------------------------------ policy
def fixture_sketch_policy(**changes: object) -> SketchPolicySnapshot:
    """Fixture rules for the opaque A1 tokens level_fx_1/level_fx_2; not a taxonomy."""

    values: dict[str, object] = {
        "policy_id": "fixture.sketch_generation.v0",
        "version": "1",
        "status": FIXTURE_POLICY_STATUS,
        "enabled": True,
        "purpose_code": "ai_drawing_assistance",
        "rules": {
            "level_fx_1": LevelOutputRule("level_fx_1", DisplayMode.SIDE_REFERENCE,
                                          PartRequirement.REQUIRED, PartRequirement.FORBIDDEN),
            "level_fx_2": LevelOutputRule("level_fx_2", DisplayMode.OVERLAY,
                                          PartRequirement.OPTIONAL, PartRequirement.REQUIRED),
        },
        "asset_media_types": frozenset({"image/png"}),
        "asset_max_bytes": 10_485_760,  # SRS LIMIT_ASSET_BYTES, PROPOSED
        "text_max_chars": 4000,  # SRS LIMIT_TEXT_LONG, PROPOSED
        "generator_profile_ref": FIXTURE_GENERATOR_PROFILE,
        **changes,
    }
    return SketchPolicySnapshot(**values)  # type: ignore[arg-type]


class FixtureSketchPolicy:
    def __init__(self, snapshot: SketchPolicySnapshot | None) -> None:
        self.snapshot = snapshot

    def current(self, organization_id: str, session_id: str) -> SketchPolicySnapshot | None:
        return self.snapshot


# ------------------------------------------------------------------ decision epochs
class CounterDecisionPort:
    """Unit-test decision epochs: one counter per organization plus artifact refs."""

    def __init__(self) -> None:
        self.epochs: dict[str, int] = defaultdict(int)

    def bump(self, key: str) -> None:
        self.epochs[key] += 1

    def token(self, organization_id: str, refs: tuple[str, ...],
              ref_set_id: str) -> DecisionToken:
        keys = (f"org:{organization_id}", *(f"artifact:{ref}" for ref in sorted(refs)))
        return DecisionToken(organization_id, tuple((key, self.epochs[key]) for key in keys),
                             ref_set_id)


# ------------------------------------------------------------------ store
@dataclass
class _State:
    proposals: dict[str, SketchProposal] = field(default_factory=dict)
    by_assistance: dict[tuple[str, str], str] = field(default_factory=dict)
    staged: dict[str, StagedGeneration] = field(default_factory=dict)
    receipts: dict[str, SketchReceipt] = field(default_factory=dict)
    events: list[SketchEvent] = field(default_factory=list)
    cleanup: dict[str, CleanupIntent] = field(default_factory=dict)
    cleanup_delivered: set[str] = field(default_factory=set)
    hints: dict[tuple[str, str], HandoffHint] = field(default_factory=dict)
    revalidations: list[str] = field(default_factory=list)
    notices: set[str] = field(default_factory=set)

    def copy(self) -> _State:
        return _State(dict(self.proposals), dict(self.by_assistance), dict(self.staged),
                      dict(self.receipts), list(self.events), dict(self.cleanup),
                      set(self.cleanup_delivered), dict(self.hints), list(self.revalidations),
                      set(self.notices))


class _UnitOfWork:
    def __init__(self, state: _State, decision: SketchDecisionPort) -> None:
        self._s = state
        self._decision = decision
        self.invalidated: set[str] = set()

    def require_token(self, token: DecisionToken, refs: tuple[str, ...]) -> None:
        current = self._decision.token(token.organization_id, refs, token.ref_set_id)
        if current != token:
            raise StaleDecision()

    def get(self, proposal_id: str) -> SketchProposal | None:
        return self._s.proposals.get(proposal_id)

    def find_by_assistance(self, organization_id: str, assistance_id: str) -> str | None:
        return self._s.by_assistance.get((organization_id, assistance_id))

    def insert(self, proposal: SketchProposal) -> None:
        key = (proposal.organization_id, proposal.binding.assistance_id)
        if key in self._s.by_assistance or proposal.proposal_id in self._s.proposals:
            raise SketchUniqueConflict("handoff")
        self._s.by_assistance[key] = proposal.proposal_id
        self._s.proposals[proposal.proposal_id] = proposal

    def cas(self, *, expected_record_version: int, proposal: SketchProposal) -> None:
        current = self._s.proposals.get(proposal.proposal_id)
        if current is None or current.record_version != expected_record_version:
            raise SketchRevisionConflict(proposal.proposal_id)
        if proposal.record_version != expected_record_version + 1:
            raise SketchRevisionConflict("record_version must advance by one")
        self._s.proposals[proposal.proposal_id] = proposal

    def list_proposals(self, organization_id: str) -> tuple[SketchProposal, ...]:
        return tuple(p for _, p in sorted(self._s.proposals.items())
                     if p.organization_id == organization_id)

    def get_staged(self, job_id: str, attempt_id: str) -> StagedGeneration | None:
        return self._s.staged.get(f"{job_id}:{attempt_id}")

    def put_staged(self, staged: StagedGeneration) -> None:
        if staged.key in self._s.staged:
            raise SketchUniqueConflict("staged")
        self._s.staged[staged.key] = staged

    def update_staged(self, staged: StagedGeneration) -> None:
        if staged.key not in self._s.staged:
            raise SketchRevisionConflict(staged.key)
        self._s.staged[staged.key] = staged

    def staged_for(self, proposal_id: str) -> tuple[StagedGeneration, ...]:
        return tuple(s for s in self._s.staged.values() if s.proposal_id == proposal_id)

    def get_receipt(self, key: str) -> SketchReceipt | None:
        return self._s.receipts.get(key)

    def put_receipt(self, receipt: SketchReceipt) -> None:
        if receipt.key in self._s.receipts:
            raise SketchUniqueConflict("receipt")
        self._s.receipts[receipt.key] = receipt

    def add_event(self, event: SketchEvent) -> None:
        if any(e.event_id == event.event_id for e in self._s.events):
            return
        self._s.events.append(event)

    def add_cleanup(self, intent: CleanupIntent) -> None:
        self._s.cleanup.setdefault(intent.event_id, intent)

    def pending_cleanup(self) -> tuple[CleanupIntent, ...]:
        return tuple(i for key, i in self._s.cleanup.items()
                     if key not in self._s.cleanup_delivered)

    def mark_cleanup(self, event_id: str) -> None:
        self._s.cleanup_delivered.add(event_id)

    def add_hint(self, organization_id: str, hint: HandoffHint) -> None:
        self._s.hints.setdefault((organization_id, hint.intent_id), hint)

    def hints(self, organization_id: str) -> tuple[HandoffHint, ...]:
        return tuple(h for (org, _), h in sorted(self._s.hints.items()) if org == organization_id)

    def drop_hint(self, organization_id: str, intent_id: str) -> None:
        self._s.hints.pop((organization_id, intent_id), None)

    def request_revalidation(self, proposal_id: str) -> None:
        if proposal_id not in self._s.revalidations:
            self._s.revalidations.append(proposal_id)

    def notice_seen(self, notice_id: str) -> bool:
        return notice_id in self._s.notices

    def record_notice(self, notice_id: str) -> None:
        self._s.notices.add(notice_id)

    def publish_invalidation(self, organization_id: str) -> None:
        self.invalidated.add(organization_id)


class InMemorySketchStore:
    """Staged all-or-nothing fake unit of work; invalidations bump the shared owner fence
    after commit (like A1). One re-entrant lock; ``peek`` reads committed state lock-free."""

    marker = FIXTURE_MARKER

    def __init__(self, decision: SketchDecisionPort,
                 fences: FakeOwnerFences | None = None,
                 on_invalidation: Callable[[str], None] | None = None) -> None:
        self._decision = decision
        self._fences = fences
        self._on_invalidation = on_invalidation
        self._state = _State()
        self._lock = RLock()
        self.fail_next_commit = False
        self.before_commit: Callable[[], object] | None = None
        self.commits = 0

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        with self._lock:
            staged = self._state.copy()
            uow = _UnitOfWork(staged, self._decision)
            yield uow
            hook = self.before_commit
            if hook is not None:
                self.before_commit = None
                hook()
            if self.fail_next_commit:
                self.fail_next_commit = False
                raise RuntimeError("injected sketch commit failure")
            self._state = staged
            self.commits += 1
            for organization_id in sorted(uow.invalidated):
                if self._fences is not None:
                    self._fences.bump(eligibility_fence_scope(organization_id))
                if self._on_invalidation is not None:
                    self._on_invalidation(organization_id)

    def peek(self, proposal_id: str) -> SketchProposal | None:
        return self._state.proposals.get(proposal_id)

    def snapshot(self) -> _State:
        with self._lock:
            return self._state.copy()


# ------------------------------------------------------------------ generator
Script = Callable[[GenerationRequest], GenerationOutcome]


def default_outcome(request: GenerationRequest, *, unsafe: bool = False) -> GenerationSucceeded:
    """Exact parts for the request's rule; image bytes carry only a PNG signature."""

    parts: list[OutputPart] = []
    if request.rule.text is not PartRequirement.FORBIDDEN:
        parts.append(OutputPart("text_or_question",
                                text=f"Fixture prompt for {request.assistance_level}?"))
    if request.rule.asset is not PartRequirement.FORBIDDEN:
        body = PNG_SIGNATURE + f"fixture-sketch:{request.generation_digest}".encode()
        parts.append(OutputPart("reference_image", body=body, media_type="image/png",
                                reported_sha256=sha256(body).hexdigest()))
    return GenerationSucceeded(tuple(parts), unsafe, "fake-sketch-generator",
                               request.generator_profile_ref, "fixture-config-v0", "fixture",
                               copies=(ProviderCopyRef(f"copy_out_{request.proposal_id}_"
                                                       f"{request.proposal_version}_"
                                                       f"{request.attempt_number}", "output",
                                                       "fixture-deletes"),))


class ScriptedSketchGenerator:
    """Scripted offline provider (no network); counts calls per proposal."""

    def __init__(self, script: Script | None = None) -> None:
        self.script = script
        self.calls: dict[str, int] = defaultdict(int)
        self.requests: list[GenerationRequest] = []
        self.during_call: Callable[[], object] | None = None

    def known_copies(self, request: GenerationRequest) -> tuple[ProviderCopyRef, ...]:
        suffix = f"{request.proposal_id}_{request.proposal_version}_{request.attempt_number}"
        return (ProviderCopyRef(f"copy_in_{suffix}", "input", "fixture-deletes"),
                ProviderCopyRef(f"copy_job_{suffix}", "job", "fixture-pending"))

    def generate(self, request: GenerationRequest) -> GenerationOutcome:
        self.calls[request.proposal_id] += 1
        self.requests.append(request)
        hook = self.during_call
        if hook is not None:
            self.during_call = None
            hook()
        if self.script is not None:
            return self.script(request)
        return default_outcome(request)


# ------------------------------------------------------------------ admission
class FixtureDerivedArtifactAdmission:
    """Structural admission (ASSUMED_CONTRACT for ArtifactReferenceV1): media type allowlist,
    byte bound, PNG signature, sha recomputation, producer lineage. Decoding is NOT_RUN."""

    def __init__(self, artifacts: FakeArtifacts, *, max_bytes: int = 10_485_760) -> None:
        self._artifacts = artifacts
        self._max_bytes = max_bytes
        self._refs: dict[tuple[str, str, str], StagedArtifact] = {}
        self.provenance: dict[str, DerivativeProvenance] = {}
        self.refuse_next: str | None = None

    def stage(self, organization_id: str, job_id: str, attempt_id: str, part_key: str,
              body: bytes, media_type: str,
              provenance: DerivativeProvenance) -> StagedArtifact | AdmissionRefusal:
        key = (job_id, attempt_id, part_key)
        if key in self._refs:
            return self._refs[key]
        if self.refuse_next is not None:
            reason, self.refuse_next = self.refuse_next, None
            return AdmissionRefusal(reason)
        if media_type not in {"image/png", RESULT_DOCUMENT_MEDIA_TYPE}:
            return AdmissionRefusal("MEDIA_TYPE_UNSUPPORTED")
        if not 0 < len(body) <= self._max_bytes:
            return AdmissionRefusal("SIZE_OUT_OF_BOUNDS")
        if media_type == "image/png" and not body.startswith(PNG_SIGNATURE):
            return AdmissionRefusal("SIGNATURE_MISMATCH")
        if provenance.origin != "ai_derived" or not provenance.source_refs:
            return AdmissionRefusal("LINEAGE_MISSING")
        output = self._artifacts.put(organization_id, body, job_id=job_id, attempt_id=attempt_id)
        staged = StagedArtifact(output.artifact_ref, output.sha256, media_type, len(body))
        self._refs[key] = staged
        self.provenance[staged.artifact_ref] = provenance
        return staged


# ------------------------------------------------------------------ authority
@dataclass(frozen=True, slots=True)
class DeviceGrant:
    organization_id: str
    session_id: str
    participant_id: str


class FakeSketchAuthority:
    def __init__(self) -> None:
        self.teachers: dict[str, tuple[str, frozenset[str]]] = {}
        self.devices: dict[str, DeviceGrant] = {}

    def allowed(self, principal: Principal, scope: SketchScope, action: SketchAction) -> bool:
        if principal.organization_id != scope.organization_id:
            return False
        if principal.role is PrincipalRole.TEACHER:
            grant = self.teachers.get(principal.principal_id)
            return grant is not None and grant[0] == scope.organization_id and (
                scope.class_id in grant[1])
        if principal.role is PrincipalRole.DEVICE and action is SketchAction.DEVICE_VIEW:
            device = self.devices.get(principal.principal_id)
            return device is not None and device.session_id == scope.session_id and (
                device.participant_id in scope.audience)
        return False


# ------------------------------------------------------------------ handoff (unit)
def all_current(binding: HandoffBinding) -> CurrentFacts:
    return CurrentFacts(True, True, True, True, binding.context_revision,
                        binding.source.input_hash, True, binding.meaning)


class ScriptedHandoffReader:
    """Service-test handoff reader; ``current`` facts are edited by tests."""

    def __init__(self) -> None:
        self.handoffs: dict[tuple[str, str], SketchHandoffV1 | HandoffRefusal] = {}
        self.currents: dict[str, CurrentFacts] = {}
        self.current_calls = 0
        self.after_current: Callable[[], object] | None = None

    def add(self, handoff: SketchHandoffV1) -> None:
        binding = handoff.binding
        self.handoffs[(binding.organization_id, binding.assistance_id)] = handoff
        self.currents[binding.assistance_id] = all_current(binding)

    def resolve(self, organization_id: str,
                assistance_id: str) -> SketchHandoffV1 | HandoffRefusal:
        found = self.handoffs.get((organization_id, assistance_id))
        if found is None:
            return HandoffRefusal(HandoffRefusalCode.UNREADABLE)
        return found

    def current(self, binding: HandoffBinding) -> CurrentFacts:
        self.current_calls += 1
        facts = self.currents.get(binding.assistance_id, all_current(binding))
        hook = self.after_current
        if hook is not None:
            self.after_current = None
            hook()
        return facts

    def set_current(self, assistance_id: str, **changes: object) -> None:
        self.currents[assistance_id] = replace(self.currents[assistance_id],
                                               **changes)  # type: ignore[arg-type]


__all__ = [
    "FIXTURE_GENERATOR_PROFILE",
    "FIXTURE_MARKER",
    "CounterDecisionPort",
    "DeviceGrant",
    "FakeSketchAuthority",
    "FixtureDerivedArtifactAdmission",
    "FixtureSketchPolicy",
    "InMemorySketchStore",
    "ScriptedHandoffReader",
    "ScriptedSketchGenerator",
    "all_current",
    "default_outcome",
    "fixture_sketch_policy",
]
