"""BE2-04 SK1 adapters over existing BE2-01/02/03 ports and fakes (no source edits).

* ``AssistanceHandoffReader`` — handoff A: authorized public reads of BE2-03/BE2-02 through an
  injected scoped Teacher reader, projected to the 04-owned ``SketchHandoffV1`` (N01).
* ``SketchEligibility`` — foundation ``EligibilityPort`` decorator for sketch jobs.
* ``AiJobSketchPort`` / ``AiJobSketchReader`` — job create/cancel and read-only job lineage.
* ``SketchProviderAdapter`` — foundation ``AiProviderPort`` around ``record_generation``.
* ``SketchStageAdapter`` — BE2-03 ``SketchStagePort``: records a hint, never raises.
* ``SketchCopyRegistrar`` — foundation ProviderCopyLifecycle fake support.
* ``CoordinatedSketchRepository`` / ``FenceDecisionPort`` / ``CoordinatedSketchArtifactPort`` —
  chain-only coordination with the A1 commit coordinator (plan §6.3, §7.2a).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field

from sketch2life.application.ports.ai_jobs import (
    ArtifactDescriptor,
    DispatchMessage,
    EligibilityDecision,
    EligibilityPort,
    Principal,
    PrincipalRole,
    QuarantineIntent,
    SemanticRequestKey,
)
from sketch2life.application.ports.assistance import (
    AssistanceOwnerPort,
    AssistanceSourcePort,
    SketchIntent,
)
from sketch2life.application.ports.sketch_generation import (
    CleanupIntent,
    HandoffHint,
    HandoffRefusal,
    HandoffRefusalCode,
    JobCreateKind,
    JobCreateOutcome,
    ProviderCopyRef,
    SketchHandoffV1,
    SketchJobCreate,
    SketchJobEvidence,
    SketchUnitOfWork,
)
from sketch2life.application.services.ai_jobs import (
    AiJobError,
    AiJobService,
    CancelJobCommand,
    CreateJobCommand,
)
from sketch2life.application.services.assistance import AssistanceError, AssistanceService
from sketch2life.application.services.provider_copy_lifecycle import ProviderCopyLifecycleService
from sketch2life.application.services.sketch_generation import SketchGenerationService
from sketch2life.application.services.vision_analysis import (
    VisionAnalysisError,
    VisionAnalysisService,
)
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    Moderation,
    OutcomeKind,
    OutputRef,
)
from sketch2life.domain.ai_jobs.model import JobScope, RequestRef
from sketch2life.domain.ai_jobs.provider_copy import CopyKind, ProviderCopy
from sketch2life.domain.assistance import AssistanceRequest, CheckpointRef, RequestStatus
from sketch2life.domain.sketch_proposal import (
    ACTIVE_STATES,
    SKETCH_JOB_TYPE,
    CurrentFacts,
    DecisionToken,
    HandoffBinding,
    HandoffKind,
    MeaningBasis,
    SketchProposal,
    SourcePin,
)
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeOwnerFences,
    artifact_fence_scope,
    eligibility_fence_scope,
)
from sketch2life.infrastructure.assistance.fakes import (
    AssistanceCommitCoordinator,
    analysis_fence_scope,
)
from sketch2life.infrastructure.sketch_generation.fakes import InMemorySketchStore


def sketch_policy_fence_scope(organization_id: str) -> str:
    return f"sketch-policy:{organization_id}"


# ------------------------------------------------------------------ handoff A (N01)
class AssistanceHandoffReader:
    """Only this adapter touches BE2-03/BE2-02 types; it returns 04 types only."""

    def __init__(self, assistance: Callable[[], AssistanceService], vision: VisionAnalysisService,
                 owner: AssistanceOwnerPort, sources: AssistanceSourcePort,
                 reader: Principal) -> None:
        if reader.role is not PrincipalRole.TEACHER:
            raise ValueError("the injected handoff reader must be a scoped Teacher")
        self._assistance = assistance
        self._vision = vision
        self._owner = owner
        self._sources = sources
        self._reader = reader

    def _read_request(self, assistance_id: str) -> AssistanceRequest | None:
        try:
            return self._assistance().read(self._reader, assistance_id)
        except AssistanceError:
            return None

    def _read_analysis(self, analysis_id: str) -> tuple[Mapping[str, object], object] | None:
        try:
            record = self._vision.analysis_record(self._reader, analysis_id)
            meaning = self._vision.downstream_meaning(self._reader, analysis_id)
        except VisionAnalysisError:
            return None
        return record, meaning

    def resolve(self, organization_id: str,
                assistance_id: str) -> SketchHandoffV1 | HandoffRefusal:
        if self._reader.organization_id != organization_id:
            return HandoffRefusal(HandoffRefusalCode.UNREADABLE)
        request = self._read_request(assistance_id)
        if request is None:
            return HandoffRefusal(HandoffRefusalCode.UNREADABLE)
        if request.status is not RequestStatus.ANALYSIS_READY:
            return HandoffRefusal(HandoffRefusalCode.NOT_READY)
        if request.handoff is not None:
            kind, cache_source = HandoffKind.ANALYSIS, None
            analysis_id = request.handoff.analysis_id
            analysis_revision = request.handoff.analysis_revision
            job_id, attempt_id = request.handoff.job_id, request.handoff.attempt_id
            lineage_assistance = request.assistance_id
            lineage_revision = (request.schedule.request_revision if request.schedule
                                else request.request_revision)
        elif request.cache_hit_of is not None:
            cache = request.cache_hit_of
            kind, cache_source = HandoffKind.CACHE_HIT, cache.assistance_id
            analysis_id, analysis_revision = cache.analysis_id, cache.analysis_revision
            job_id, attempt_id = cache.job_id, ""
            lineage_assistance, lineage_revision = cache.assistance_id, cache.request_revision
        else:
            return HandoffRefusal(HandoffRefusalCode.NOT_READY)
        read = self._read_analysis(analysis_id)
        if read is None:
            return HandoffRefusal(HandoffRefusalCode.UNREADABLE)
        record, meaning = read
        candidate, source = record["candidate"], record["source_binding"]
        assert isinstance(candidate, dict) and isinstance(source, dict)
        checkpoint, render = source["checkpoint"], source["render"]
        assert isinstance(checkpoint, dict) and isinstance(render, dict)
        facts = request.facts
        if kind is HandoffKind.CACHE_HIT:
            attempt_id = str(candidate["job_attempt_id"])
        lineage_ok = (
            candidate["assistance_id"] == lineage_assistance
            and candidate["expected_request_revision"] == lineage_revision
            and candidate["job_id"] == job_id
            and candidate["job_attempt_id"] == attempt_id
            and candidate["context_revision"] == facts.context_revision
            and source["input_snapshot_ref"] == facts.source.snapshot_ref
            and checkpoint["checkpoint_id"] == facts.source.checkpoint_id
            and checkpoint["checksum_sha256"] == facts.source.checkpoint_checksum
            and render["render_ref"] == facts.source.render_ref
            and render["render_sha256"] == facts.source.render_sha256
        )
        if not lineage_ok:
            return HandoffRefusal(HandoffRefusalCode.MISMATCH)
        binding = HandoffBinding(
            assistance_id=request.assistance_id,
            request_revision=request.request_revision,
            handoff_kind=kind,
            cache_source_assistance_id=cache_source,
            analysis_id=analysis_id,
            analysis_revision=analysis_revision,
            vision_job_id=job_id,
            vision_attempt_id=attempt_id,
            organization_id=facts.organization_id,
            class_id=facts.class_id,
            session_id=facts.session_id,
            canvas_id=facts.canvas_id,
            group_id=facts.group_id,
            target_kind=str(facts.target.kind),
            target_ref=facts.target.ref_id,
            audience=facts.audience,
            roster_revision=facts.roster_revision,
            contributor_participant_id=facts.contributor_participant_id,
            purpose_code=facts.purpose_code,
            source=SourcePin(
                snapshot_ref=facts.source.snapshot_ref,
                checkpoint_id=facts.source.checkpoint_id,
                document_epoch=facts.source.document_epoch,
                server_sequence=facts.source.server_sequence,
                checkpoint_checksum=facts.source.checkpoint_checksum,
                render_ref=facts.source.render_ref,
                render_sha256=facts.source.render_sha256,
                render_media_type=str(render["media_type"]),
                admission_receipt_id=str(source["admission_receipt_id"]),
                input_hash=facts.source.input_hash,
            ),
            context_revision=facts.context_revision,
            requested_level=request.requested_level,
            request_policy_id=facts.policy_id,
            request_policy_version=facts.policy_version,
            requester_principal_id=request.requester.principal_id,
            requester_kind=str(request.requester.kind),
            assistance_context_digest=request.assistance_context_digest,
            meaning=_meaning(meaning),
        )
        return SketchHandoffV1(binding)

    def current(self, binding: HandoffBinding) -> CurrentFacts:
        request = self._read_request(binding.assistance_id)
        handoff_unchanged = request is not None and request.status is (
            RequestStatus.ANALYSIS_READY) and _same_handoff(request, binding)
        canvas = self._owner.canvas(binding.organization_id, binding.canvas_id)
        members = self._owner.members(binding.organization_id, binding.audience,
                                      binding.purpose_code)
        consent_ok = len(members) == len(binding.audience) and all(
            m.consent_effective and m.purpose_granted for m in members)
        resolved = self._sources.resolve(binding.organization_id, binding.canvas_id,
                                         CheckpointRef(binding.source.checkpoint_id,
                                                       binding.source.document_epoch,
                                                       binding.source.server_sequence,
                                                       binding.source.checkpoint_checksum))
        read = self._read_analysis(binding.analysis_id)
        accepted = read is not None and read[0].get("accepted_status") == "accepted"
        return CurrentFacts(
            handoff_unchanged=handoff_unchanged,
            session_active=canvas is not None and canvas.session_active,
            consent_ok=consent_ok,
            audience_unchanged=self._audience_unchanged(binding),
            context_revision=None if canvas is None else canvas.context_revision,
            source_input_hash=None if resolved is None else resolved.snapshot.input_hash(),
            analysis_accepted=accepted,
            meaning=None if read is None else _meaning(read[1]),
        )

    def _audience_unchanged(self, binding: HandoffBinding) -> bool:
        """Same roster facts A1 binds into ``assistance_context_digest``."""

        canvas = self._owner.canvas(binding.organization_id, binding.canvas_id)
        if canvas is None:
            return False
        if binding.roster_revision is None:  # personal canvas, individual target
            return canvas.personal_participant_id == binding.target_ref
        if binding.group_id is None:
            return False
        roster = self._owner.roster(binding.session_id, binding.group_id)
        if roster is None or roster.revision != binding.roster_revision:
            return False
        if binding.target_kind == "group":
            return sorted(roster.members) == sorted(binding.audience)
        return binding.target_ref in roster.members


def _meaning(value: object) -> MeaningBasis:
    state = str(getattr(value, "state", "not_applicable"))
    ref = getattr(value, "confirmation_ref", None)
    concepts = tuple(str(c) for c in getattr(value, "confirmed_concepts", ()))
    return MeaningBasis(state, None if ref is None else str(ref), concepts)


def _same_handoff(request: AssistanceRequest, binding: HandoffBinding) -> bool:
    if request.request_revision != binding.request_revision:
        return False
    if binding.handoff_kind is HandoffKind.ANALYSIS:
        return request.handoff is not None and request.handoff.analysis_id == binding.analysis_id
    return request.cache_hit_of is not None and (
        request.cache_hit_of.analysis_id == binding.analysis_id)


# ------------------------------------------------------------------ eligibility
class SketchEligibility:
    """Proposal-aware eligibility for ``sketch_generation`` jobs; other types pass through."""

    def __init__(self, inner: EligibilityPort,
                 store: InMemorySketchStore | CoordinatedSketchRepository,
                 coordinator: AssistanceCommitCoordinator | None = None) -> None:
        self._inner = inner
        self._store = store
        self._coordinator = coordinator

    def check(self, *, scope: object, request_ref: RequestRef,
              job_type: str) -> EligibilityDecision:
        decision = self._inner.check(scope=scope, request_ref=request_ref,  # type: ignore[arg-type]
                                     job_type=job_type)
        if job_type != SKETCH_JOB_TYPE:
            return decision

        def read() -> SketchProposal | None:
            return self._store.peek(request_ref.request_id)

        proposal = (self._coordinator.read(read) if self._coordinator is not None else read())
        assert proposal is None or isinstance(proposal, SketchProposal)
        reason = _ineligible(proposal, request_ref, getattr(scope, "organization_id", ""))
        if reason is None:
            return decision
        return EligibilityDecision(False, reason, decision.current_context_revision,
                                   decision.fence)


class SketchChainEligibility:
    """Dispatch shared-chain retry checks to the eligibility owner for each job type."""

    def __init__(self, assistance: EligibilityPort, sketch: EligibilityPort) -> None:
        self._assistance = assistance
        self._sketch = sketch

    def check(self, *, scope: JobScope, request_ref: RequestRef,
              job_type: str) -> EligibilityDecision:
        port = self._sketch if job_type == SKETCH_JOB_TYPE else self._assistance
        return port.check(scope=scope, request_ref=request_ref, job_type=job_type)


def _ineligible(proposal: SketchProposal | None, request_ref: RequestRef,
                organization_id: str) -> str | None:
    if proposal is None or proposal.organization_id != organization_id:
        return "REQUEST_NOT_FOUND"
    version = proposal.current
    if version.version != request_ref.request_revision or (
        version.generation_digest != request_ref.input_hash
    ):
        return "CONTEXT_CHANGED"
    if version.pipeline_state not in ACTIVE_STATES:
        return str(version.status_reason) if version.status_reason is not None else (
            "INVALID_STATE")
    return None


# ------------------------------------------------------------------ jobs
class AiJobSketchPort:
    def __init__(self, service: AiJobService) -> None:
        self._service = service
        self.lose_next_reply = False
        self.creates = 0

    def create(self, request: SketchJobCreate) -> JobCreateOutcome:
        self.creates += 1
        try:
            result = self._service.create_job(CreateJobCommand(
                principal=request.principal,
                idempotency_key=request.idempotency_key,
                job_type=SKETCH_JOB_TYPE,
                target_id=request.target_id,
                purpose_code=request.purpose_code,
                session_id=request.session_id,
                subject_refs=request.subject_refs,
                request_ref=RequestRef(request.request_id, request.request_revision,
                                       request.input_hash, request.context_revision),
                correlation_id=request.correlation_id,
            ))
        except AiJobError as exc:
            kind = (JobCreateKind.RETRY if exc.retryable and exc.code != "BUDGET_EXCEEDED"
                    else JobCreateKind.REFUSED)
            return JobCreateOutcome(kind, None, exc.code)
        if self.lose_next_reply:
            self.lose_next_reply = False
            raise LostReply(result.job_id)
        return JobCreateOutcome(JobCreateKind.CREATED, result.job_id)

    def cancel(self, principal: Principal, job_id: str, expected_job_revision: int,
               reason_code: str = "CANCELLED_BY_TEACHER") -> str:
        try:
            self._service.cancel_job(CancelJobCommand(
                principal=principal,
                idempotency_key=f"sketch-cleanup:{job_id}:{expected_job_revision}",
                job_id=job_id,
                expected_job_revision=expected_job_revision,
                reason_code=reason_code,
            ))
        except AiJobError as exc:
            return exc.code
        return "cancelled"


class LostReply(RuntimeError):
    """Fault injection: the create committed but the reply never reached the caller."""


class AiJobSketchReader:
    """Read-only job lineage; never calls a mutating unit-of-work method or ``list_jobs``."""

    def __init__(self, repository: object) -> None:
        self._repository = repository

    def get(self, job_id: str) -> SketchJobEvidence | None:
        with self._repository.transaction() as tx:  # type: ignore[attr-defined]
            job = tx.get_job(job_id)
        if job is None:
            return None
        ref = job.active_attempt.request_ref
        return SketchJobEvidence(
            job_id=job.job_id, organization_id=job.organization_id, job_type=job.job_type,
            state=str(job.state),
            disposition=None if job.result_disposition is None else str(job.result_disposition),
            active_attempt_id=job.active_attempt.attempt_id,
            attempt_number=job.active_attempt.attempt_number,
            request_id=ref.request_id, request_revision=ref.request_revision,
            input_hash=ref.input_hash, context_revision=ref.context_revision,
            result_refs=tuple((r.artifact_ref, r.sha256) for r in job.result_refs),
            failure_code=None if job.failure is None else job.failure.code,
            job_revision=job.job_revision)

    def find_semantic(self, request: SketchJobCreate) -> str | None:
        key = SemanticRequestKey(request.principal.organization_id, SKETCH_JOB_TYPE,
                                 request.request_id, request.request_revision,
                                 request.input_hash, request.context_revision,
                                 request.target_id, request.purpose_code, request.session_id,
                                 tuple(sorted(request.subject_refs)))
        with self._repository.transaction() as tx:  # type: ignore[attr-defined]
            found = tx.find_semantic(key)
        return None if found is None else str(found)


# ------------------------------------------------------------------ worker / stage / copies
class SketchProviderAdapter:
    """``AiProviderPort``: the BE2-04 worker step, mapped to a foundation claim."""

    def __init__(self, service: Callable[[], SketchGenerationService]) -> None:
        self._service = service
        self.runs = 0

    def run(self, message: DispatchMessage) -> CompletionClaim:
        self.runs += 1
        claim = self._service().record_generation(
            message.job_id, message.attempt_id,
            correlation_id=f"corr_{message.job_id}_{message.attempt_number}")
        if claim.success:
            return CompletionClaim(claim.job_id, claim.attempt_id, claim.request_revision,
                                   claim.input_hash, claim.context_revision, OutcomeKind.SUCCESS,
                                   outputs=tuple(OutputRef(r, s) for r, s in claim.outputs),
                                   moderation=Moderation.UNSAFE if claim.unsafe
                                   else Moderation.PASSED)
        return CompletionClaim(claim.job_id, claim.attempt_id, claim.request_revision,
                               claim.input_hash, claim.context_revision, OutcomeKind.FAILURE,
                               failure_code=claim.failure_code, retryable=claim.retryable)


class SketchStageAdapter:
    """BE2-03 ``SketchStagePort``: post-commit hint only; never raises into BE2-03."""

    def __init__(self, service: Callable[[], SketchGenerationService],
                 organization_id: str) -> None:
        self._service = service
        self._organization_id = organization_id
        self.failures: list[str] = []

    def request_sketch(self, intent: SketchIntent) -> None:
        try:
            self._service().add_hint(self._organization_id, HandoffHint(
                intent.intent_id, intent.assistance_id, intent.request_revision,
                intent.analysis_id, intent.analysis_revision))
        except Exception as exc:  # noqa: BLE001 - a lost hint is recovered by open-by-id
            self.failures.append(type(exc).__name__)


class SketchCopyRegistrar:
    def __init__(self, lifecycle: ProviderCopyLifecycleService) -> None:
        self._lifecycle = lifecycle

    def register(self, organization_id: str, scope_ref: str, copy: ProviderCopyRef) -> None:
        self._lifecycle.register_copy(ProviderCopy(copy.copy_id, organization_id, scope_ref,
                                                   CopyKind(copy.kind), copy.provider_profile))


# ------------------------------------------------------------------ chain coordination
class CoordinatedSketchRepository:
    """Each 04 unit runs as an A1 ``assistance`` unit: mutually exclusive with foundation and
    Vision units and owner publications; a unit opened inside one of them is refused."""

    def __init__(self, inner: InMemorySketchStore,
                 coordinator: AssistanceCommitCoordinator) -> None:
        self.inner = inner
        self._coordinator = coordinator

    @contextmanager
    def transaction(self) -> Iterator[SketchUnitOfWork]:
        with self._coordinator.assistance(), self.inner.transaction() as tx:
            yield tx

    def peek(self, proposal_id: str) -> SketchProposal | None:
        return self.inner.peek(proposal_id)


class FenceDecisionPort:
    """Committed epochs read under the coordinator: owner/request, analysis, 04 policy and
    the artifact fence of each ref in the pinned ref-set (plan §7.2a)."""

    def __init__(self, fences: FakeOwnerFences, coordinator: AssistanceCommitCoordinator) -> None:
        self._fences = fences
        self._coordinator = coordinator

    def token(self, organization_id: str, refs: tuple[str, ...],
              ref_set_id: str) -> DecisionToken:
        scopes = (eligibility_fence_scope(organization_id), analysis_fence_scope(organization_id),
                  sketch_policy_fence_scope(organization_id),
                  *(artifact_fence_scope(ref) for ref in sorted(refs)))

        def read() -> tuple[tuple[str, int], ...]:
            return tuple((scope, self._fences.epochs[scope]) for scope in scopes)

        epochs = self._coordinator.read(read)
        assert isinstance(epochs, tuple)
        return DecisionToken(organization_id, epochs, ref_set_id)


@dataclass(frozen=True, slots=True)
class ArtifactAuditEntry:
    caller: str
    event_id: str
    ref: str
    epoch_before: int
    epoch_after: int

    @property
    def bumped(self) -> bool:
        return self.epoch_after > self.epoch_before


@dataclass
class CoordinatedSketchArtifactPort:
    """The only path that changes artifact quarantine state in the chain (TC-21/TC-25).

    Quarantine runs as a coordinator publication: synchronous under the lock outside any unit
    (errors propagate so the foundation keeps the intent pending), deferred inside a unit."""

    raw: FakeArtifacts
    coordinator: AssistanceCommitCoordinator
    fences: FakeOwnerFences
    audit: list[ArtifactAuditEntry] = field(default_factory=list)
    fail_next_quarantine: bool = False

    def view(self, caller: str) -> ArtifactPortView:
        return ArtifactPortView(self, caller)

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        result = self.coordinator.read(lambda: self.raw.describe(artifact_ref))
        assert result is None or isinstance(result, ArtifactDescriptor)
        return result

    def quarantine(self, intent: QuarantineIntent, *, caller: str) -> bool:
        if self.fail_next_quarantine:
            self.fail_next_quarantine = False
            raise RuntimeError("injected sketch artifact sink failure")
        return self.coordinator.request_publication(
            lambda: self._apply(caller, intent.event_id, intent.artifact_refs,
                                lambda: self.raw.quarantine(intent)))

    def owner_quarantine(self, refs: tuple[str, ...], reason: str, *, caller: str) -> bool:
        return self.coordinator.request_publication(
            lambda: self._apply(caller, f"owner:{reason}", refs,
                                lambda: self.raw.owner_quarantine(refs, reason)))

    def _apply(self, caller: str, event: str, refs: tuple[str, ...],
               mutate: Callable[[], None]) -> None:
        before = {ref: self.fences.epochs[artifact_fence_scope(ref)] for ref in refs}
        mutate()
        for ref in refs:
            self.audit.append(ArtifactAuditEntry(caller, event, ref, before[ref],
                                                 self.fences.epochs[artifact_fence_scope(ref)]))


@dataclass(frozen=True, slots=True)
class ArtifactPortView:
    """Caller-tagged ``ArtifactPort`` over the single shared coordinated port."""

    port: CoordinatedSketchArtifactPort
    caller: str

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        return self.port.describe(artifact_ref)

    def quarantine(self, intent: QuarantineIntent) -> None:
        self.port.quarantine(intent, caller=self.caller)


def cleanup_sink(view: ArtifactPortView | FakeArtifacts) -> Callable[[CleanupIntent], None]:
    """C9 delivery: a 04 cleanup intent becomes a foundation quarantine intent."""

    def deliver(intent: CleanupIntent) -> None:
        view.quarantine(QuarantineIntent(intent.event_id, intent.organization_id, intent.job_id,
                                         intent.attempt_id, intent.artifact_refs,
                                         intent.reason_code))

    return deliver


__all__ = [
    "AiJobSketchPort",
    "AiJobSketchReader",
    "ArtifactAuditEntry",
    "ArtifactPortView",
    "AssistanceHandoffReader",
    "CoordinatedSketchArtifactPort",
    "CoordinatedSketchRepository",
    "FenceDecisionPort",
    "LostReply",
    "SketchCopyRegistrar",
    "SketchChainEligibility",
    "SketchEligibility",
    "SketchProviderAdapter",
    "SketchStageAdapter",
    "cleanup_sink",
    "sketch_policy_fence_scope",
]
