"""BE2-04 SK1 Sketch proposal application service (offline component).

Opens a DATA-23 proposal from a BE2-03 ``analysis_ready`` handoff (hint is never
authoritative), schedules one BE2-01 ``sketch_generation`` job per version, records the
worker's generation in an attempt-keyed staging slot and promotes it to
``pending_teacher_review`` only through the C8 gate. Every decision that depends on external
reads runs ``snapshot -> token -> reads -> decide -> commit with require_token`` (plan §7.2a).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256

from sketch2life.application.ports.ai_jobs import (
    ClockPort,
    IdGeneratorPort,
    Principal,
    PrincipalRole,
)
from sketch2life.application.ports.sketch_generation import (
    AdmissionRefusal,
    CleanupIntent,
    DerivativeProvenance,
    DerivedArtifactAdmissionPort,
    GenerationClaim,
    GenerationFailed,
    GenerationRequest,
    HandoffHint,
    HandoffRefusal,
    HandoffRefusalCode,
    JobCreateKind,
    SketchAction,
    SketchArtifactReader,
    SketchAuthorityPort,
    SketchCopyPort,
    SketchDecisionPort,
    SketchEvent,
    SketchGenerator,
    SketchHandoffReader,
    SketchJobCreate,
    SketchJobEvidence,
    SketchJobPort,
    SketchJobReader,
    SketchPolicyPort,
    SketchProposalRepository,
    SketchReceipt,
    SketchScope,
    SketchUnitOfWork,
    StagedArtifact,
    StaleDecision,
)
from sketch2life.domain.ai_jobs.completion import canonical_json, canonical_sha256
from sketch2life.domain.sketch_proposal import (
    ACTIVE_STATES,
    FAILURE_REASONS,
    INVALIDATABLE_STATES,
    RESULT_DOCUMENT_MEDIA_TYPE,
    SKETCH_JOB_TYPE,
    AssetRef,
    HandoffBinding,
    PipelineState,
    ProducerRef,
    PromotedOutput,
    SketchProposal,
    StagedGeneration,
    StagedStatus,
    StatusReason,
    add_cleanup_job,
    content_sha256,
    current_verdict,
    device_status,
    event_id,
    link_job,
    mark_analyzing,
    open_proposal,
    policy_verdict,
    promote,
    ref_set_id,
    refused_open_proposal,
    terminate,
    validate_output,
)
from sketch2life.domain.sketch_proposal import (
    revise_level as revise_version,
)

DECISION_ROUNDS = 2
WORKER_FAILURE_CODES = frozenset({"PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_ERROR",
                                  "OUTPUT_MALFORMED"})
CANCEL_CONTRACT = "SketchGenerationCancelV1"
REVISE_CONTRACT = "SketchLevelRevisionV1"

_ERRORS: Mapping[str, int] = {
    "MALFORMED_REQUEST": 400,
    "FORBIDDEN_SCOPE": 403,
    "RESOURCE_NOT_FOUND": 404,
    "INVALID_STATE": 409,
    "IDEMPOTENCY_PAYLOAD_MISMATCH": 409,
    "PRECONDITION_FAILED": 412,
    "LEVEL_NOT_ALLOWED": 422,
    "PRECONDITION_REQUIRED": 428,
    "DECISION_UNRESOLVED": 503,
}


class SketchError(Exception):
    """Typed, safe application error; never carries content or provider internals."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
        self.http_status = _ERRORS[code]


class OpenOutcome(StrEnum):
    CREATED = "created"
    REPLAYED = "replayed"
    REFUSED = "refused"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class OpenResult:
    outcome: OpenOutcome
    proposal_id: str | None = None
    code: str | None = None


@dataclass(frozen=True, slots=True)
class CommandResult:
    proposal_id: str
    outcome: str
    proposal_version: int
    replayed: bool


@dataclass(frozen=True, slots=True)
class CancelCommand:
    principal: Principal
    proposal_id: str
    idempotency_key: str | None
    if_match: str | None
    reason: str = "CANCELLED_BY_TEACHER"

    def fingerprint(self) -> str:
        return canonical_sha256({"contract": CANCEL_CONTRACT, "proposal_id": self.proposal_id,
                                 "if_match": self.if_match, "reason": self.reason})


@dataclass(frozen=True, slots=True)
class ReviseLevelCommand:
    principal: Principal
    proposal_id: str
    idempotency_key: str | None
    if_match: str | None
    new_level: str

    def fingerprint(self) -> str:
        return canonical_sha256({"contract": REVISE_CONTRACT, "proposal_id": self.proposal_id,
                                 "if_match": self.if_match, "new_level": self.new_level})


class NoticeKind(StrEnum):
    CONSENT_REVOKED = "consent_revoked"
    SESSION_ENDED = "session_ended"
    TURN_REVOKED = "turn_revoked"
    CANVAS_RESTORED = "canvas_restored"


_NOTICE_REASONS: Mapping[NoticeKind, StatusReason] = {
    NoticeKind.CONSENT_REVOKED: StatusReason.CONSENT_REVOKED,
    NoticeKind.SESSION_ENDED: StatusReason.SESSION_ENDED,
    NoticeKind.TURN_REVOKED: StatusReason.TURN_REVOKED,
    NoticeKind.CANVAS_RESTORED: StatusReason.CANVAS_RESTORED,
}


@dataclass(frozen=True, slots=True)
class OwnerNotice:
    notice_id: str
    organization_id: str
    kind: NoticeKind
    participant_id: str | None = None
    session_id: str | None = None
    canvas_id: str | None = None


@dataclass(frozen=True, slots=True)
class SketchDependencies:
    repository: SketchProposalRepository
    handoffs: SketchHandoffReader
    decision: SketchDecisionPort
    policy: SketchPolicyPort
    generator: SketchGenerator
    admission: DerivedArtifactAdmissionPort
    artifacts: SketchArtifactReader
    jobs: SketchJobPort
    job_reader: SketchJobReader
    copies: SketchCopyPort
    authority: SketchAuthorityPort
    clock: ClockPort
    ids: IdGeneratorPort
    quarantine: Callable[[CleanupIntent], None]


@dataclass(frozen=True, slots=True)
class _Plan:
    """Outcome of a pure decision: what to commit (``None`` = nothing to change)."""

    apply: Callable[[SketchUnitOfWork, SketchProposal], SketchProposal | None] | None
    restart: bool = False


Decide = Callable[[SketchProposal, tuple[StagedGeneration, ...]], _Plan]
Refs = Callable[[SketchProposal, tuple[StagedGeneration, ...]],
                tuple[tuple[str, ...], str | None]]


class SketchGenerationService:
    def __init__(self, deps: SketchDependencies) -> None:
        self._d = deps

    # ================================================================ open (C1)
    def add_hint(self, organization_id: str, hint: HandoffHint) -> None:
        with self._d.repository.transaction() as tx:
            tx.add_hint(organization_id, hint)

    def process_inbox(self, organization_id: str) -> tuple[OpenResult, ...]:
        with self._d.repository.transaction() as tx:
            hints = tx.hints(organization_id)
        results: list[OpenResult] = []
        for hint in hints:
            result = self.open_from_handoff(organization_id, hint.assistance_id, hint=hint)
            results.append(result)
            if result.outcome is not OpenOutcome.UNRESOLVED:
                with self._d.repository.transaction() as tx:
                    tx.drop_hint(organization_id, hint.intent_id)
        return tuple(results)

    def open_from_handoff(self, organization_id: str, assistance_id: str, *,
                          hint: HandoffHint | None = None) -> OpenResult:
        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                existing = tx.find_by_assistance(organization_id, assistance_id)
                existing_proposal = tx.get(existing) if existing is not None else None
            if existing is not None:
                if (existing_proposal is not None
                        and existing_proposal.current.pipeline_state is PipelineState.REQUESTED
                        and existing_proposal.current.job_id is None):
                    self.schedule(existing)
                return OpenResult(OpenOutcome.REPLAYED, existing)
            token = self._d.decision.token(organization_id, (), f"open:{assistance_id}")
            resolved = self._d.handoffs.resolve(organization_id, assistance_id)
            if isinstance(resolved, HandoffRefusal):
                return self._refuse_open(organization_id, assistance_id, resolved.code)
            binding = resolved.binding
            if binding.organization_id != organization_id:
                return self._refuse_open(organization_id, assistance_id,
                                         HandoffRefusalCode.UNREADABLE)
            if hint is not None and not _hint_matches(hint, binding):
                return self._refuse_open(organization_id, assistance_id,
                                         HandoffRefusalCode.MISMATCH)
            current = self._d.handoffs.current(binding)
            policy = self._d.policy.current(organization_id, binding.session_id)
            refusal = current_verdict(binding, current) or policy_verdict(
                policy, level=binding.requested_level, purpose_code=binding.purpose_code,
                opening=True)
            now = self._d.clock.now()
            proposal_id = self._d.ids.new_id("sketch")
            if policy is None:
                assert refusal is not None
                proposal = refused_open_proposal(proposal_id=proposal_id, binding=binding,
                                                 now=now, refusal=refusal)
            else:
                proposal = open_proposal(proposal_id=proposal_id, binding=binding,
                                         policy=policy, now=now, refusal=refusal)
            try:
                with self._d.repository.transaction() as tx:
                    tx.require_token(token, ())
                    raced = tx.find_by_assistance(organization_id, assistance_id)
                    if raced is not None:
                        return OpenResult(OpenOutcome.REPLAYED, raced)
                    tx.insert(proposal)
                    event_type = ("sketch.proposal_requested" if refusal is None else
                                  "sketch.failed" if proposal.current.pipeline_state
                                  is PipelineState.FAILED else "sketch.stale")
                    tx.add_event(self._event(proposal, event_type, refusal))
            except StaleDecision:
                continue
            if refusal is None:
                self.schedule(proposal_id)
            return OpenResult(OpenOutcome.CREATED, proposal_id,
                              None if refusal is None else str(refusal))
        return OpenResult(OpenOutcome.UNRESOLVED)

    def _refuse_open(self, organization_id: str, assistance_id: str,
                     code: HandoffRefusalCode) -> OpenResult:
        now = self._d.clock.now()
        digest = sha256(f"{organization_id}|{assistance_id}|{code}".encode()).hexdigest()[:24]
        with self._d.repository.transaction() as tx:
            tx.add_event(SketchEvent(f"sketch_evt_refused_{digest}", "sketch.open_refused",
                                     organization_id, None, None, assistance_id, str(code), now))
        return OpenResult(OpenOutcome.REFUSED, None, str(code))

    # ================================================================ schedule (C2/C3)
    def schedule(self, proposal_id: str) -> SketchProposal | None:
        with self._d.repository.transaction() as tx:
            proposal = tx.get(proposal_id)
        if proposal is None:
            return None
        current = proposal.current
        if current.pipeline_state is not PipelineState.REQUESTED or current.job_id is not None:
            return proposal
        request = self._job_request(proposal)
        outcome = self._d.jobs.create(request)
        if outcome.kind is JobCreateKind.RETRY:
            return proposal
        found = outcome.job_id if outcome.kind is JobCreateKind.CREATED else (
            self._d.job_reader.find_semantic(request))
        cleanup: str | None = None
        cleanup_reason = StatusReason.SCHEDULE_REFUSED
        for _ in range(DECISION_ROUNDS):
            now = self._d.clock.now()
            with self._d.repository.transaction() as tx:
                latest = tx.get(proposal_id)
                assert latest is not None
                head = latest.current
                same_version = head.version == current.version
                if outcome.kind is JobCreateKind.CREATED and found is not None:
                    if same_version and head.pipeline_state in ACTIVE_STATES and (
                        head.job_id in {None, found}
                    ):
                        updated = link_job(latest, found, now)
                        if updated is not latest:
                            tx.cas(expected_record_version=latest.record_version,
                                   proposal=updated)
                            tx.add_event(self._event(updated, "sketch.scheduled", None))
                    else:  # link lost to a cancel/stale/revision: keep for cleanup
                        updated = add_cleanup_job(latest, found, now)
                        if updated is not latest:
                            tx.cas(expected_record_version=latest.record_version,
                                   proposal=updated)
                        cleanup = found
                        # The job belongs to the scheduled version; report why it lost.
                        owner = latest.versions[current.version - 1]
                        cleanup_reason = owner.status_reason or StatusReason.SCHEDULE_REFUSED
                elif same_version and found is not None and head.job_id == found:
                    pass  # already linked by the worker (dispatch raced the link)
                elif same_version and head.pipeline_state is PipelineState.REQUESTED:
                    updated = terminate(latest, PipelineState.STALE,
                                        StatusReason.SCHEDULE_REFUSED, now,
                                        cleanup_job_id=found)
                    if found is not None:  # orphan from a lost reply (A1-R14 parity)
                        cleanup = found
                    tx.cas(expected_record_version=latest.record_version, proposal=updated)
                    tx.publish_invalidation(updated.organization_id)
                    tx.add_event(self._event(updated, "sketch.stale",
                                             StatusReason.SCHEDULE_REFUSED,
                                             discriminator=outcome.code or "refused"))
            break
        if cleanup is not None:
            self._cleanup_job(proposal_id, cleanup, None, cleanup_reason.value)
        with self._d.repository.transaction() as tx:
            return tx.get(proposal_id)

    def _job_request(self, proposal: SketchProposal) -> SketchJobCreate:
        binding, current = proposal.binding, proposal.current
        role = (PrincipalRole.TEACHER if binding.requester_kind == "teacher"
                else PrincipalRole.DEVICE)
        return SketchJobCreate(
            principal=Principal(binding.requester_principal_id, proposal.organization_id, role),
            idempotency_key=current.create_key,
            target_id=proposal.proposal_id,
            purpose_code=binding.purpose_code,
            session_id=binding.session_id,
            subject_refs=binding.audience,
            request_id=proposal.proposal_id,
            request_revision=current.version,
            input_hash=current.generation_digest,
            context_revision=binding.context_revision,
            correlation_id=f"corr_{proposal.proposal_id}_{current.version}",
        )

    def _cleanup_job(self, proposal_id: str, job_id: str, canceller: Principal | None,
                     reason_code: str = "CANCELLED_BY_TEACHER") -> None:
        """Best-effort explicit job cancel; SketchEligibility denies the job regardless."""

        job = self._d.job_reader.get(job_id)
        if job is None or job.terminal:
            return
        with self._d.repository.transaction() as tx:
            proposal = tx.get(proposal_id)
        if proposal is None:
            return
        principal = canceller or self._job_request(proposal).principal
        self._d.jobs.cancel(principal, job_id, job.job_revision, reason_code)

    # ================================================================ decision loop
    def _decide(self, proposal_id: str, refs: Refs, decide: Decide) -> SketchProposal | None:
        """Plan §7.2a: snapshot (ref-set) -> token -> reads -> decide -> commit with token."""

        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                proposal = tx.get(proposal_id)
                staged = tx.staged_for(proposal_id) if proposal is not None else ()
            if proposal is None:
                return None
            ref_set, staged_key = refs(proposal, staged)
            set_id = ref_set_id(proposal_id, proposal.record_version, proposal.current.version,
                                staged_key, ref_set)
            token = self._d.decision.token(proposal.organization_id, ref_set, set_id)
            plan = decide(proposal, staged)
            if plan.restart:
                continue
            if plan.apply is None:
                return proposal
            try:
                with self._d.repository.transaction() as tx:
                    tx.require_token(token, ref_set)
                    latest = tx.get(proposal_id)
                    if latest is None or latest.record_version != proposal.record_version:
                        raise StaleDecision()
                    if staged_key is not None:
                        current = {s.key: s for s in tx.staged_for(proposal_id)}.get(staged_key)
                        if current is None or current.status is not StagedStatus.STAGED:
                            raise StaleDecision()
                    updated = plan.apply(tx, latest)
            except StaleDecision:
                continue
            return updated if updated is not None else latest
        raise SketchError("DECISION_UNRESOLVED")

    def _current_reason(self, proposal: SketchProposal, *, level: str) -> StatusReason | None:
        binding = proposal.binding
        reason = current_verdict(binding, self._d.handoffs.current(binding))
        if reason is not None:
            return reason
        return policy_verdict(self._d.policy.current(proposal.organization_id,
                                                     binding.session_id),
                              level=level, purpose_code=binding.purpose_code, opening=False)

    def _invalidate(self, tx: SketchUnitOfWork, proposal: SketchProposal, state: PipelineState,
                    reason: StatusReason, *, event_type: str | None = None) -> SketchProposal:
        updated = terminate(proposal, state, reason, self._d.clock.now())
        tx.cas(expected_record_version=proposal.record_version, proposal=updated)
        tx.publish_invalidation(updated.organization_id)
        tx.add_event(self._event(updated, event_type or _event_for(state), reason))
        self._cleanup_staged(tx, updated, reason)
        return updated

    # ================================================================ worker (C5/C6)
    def record_generation(self, job_id: str, attempt_id: str, *,
                          correlation_id: str) -> GenerationClaim:
        job = self._d.job_reader.get(job_id)
        if job is None:
            raise SketchError("RESOURCE_NOT_FOUND")

        def refuse(code: str = "PROVIDER_ERROR", retryable: bool = False) -> GenerationClaim:
            return GenerationClaim(job_id, attempt_id, job.request_revision, job.input_hash,
                                   job.context_revision, False, failure_code=code,
                                   retryable=retryable)

        with self._d.repository.transaction() as tx:
            staged = tx.get_staged(job_id, attempt_id)
            proposal = tx.get(job.request_id)
        if staged is not None:
            return _claim_from(job, staged)
        if (job.job_type != SKETCH_JOB_TYPE or job.state != "running"
                or job.active_attempt_id != attempt_id or proposal is None
                or proposal.organization_id != job.organization_id):
            return refuse()
        version = proposal.current
        if (version.version != job.request_revision
                or version.generation_digest != job.input_hash
                or version.pipeline_state not in ACTIVE_STATES
                or version.job_id not in {None, job_id}):
            return refuse()
        started = self._start_generation(proposal.proposal_id, job)
        if started is None:
            return refuse()
        binding, version = started.binding, started.current
        request = GenerationRequest(
            correlation_id=correlation_id, organization_id=started.organization_id,
            proposal_id=started.proposal_id, proposal_version=version.version,
            attempt_number=job.attempt_number, render_ref=binding.source.render_ref,
            render_sha256=binding.source.render_sha256,
            render_media_type=binding.source.render_media_type,
            admission_receipt_id=binding.source.admission_receipt_id,
            assistance_level=version.level, rule=version.rule,
            confirmed_concepts=binding.meaning.projected_concepts(),
            generator_profile_ref=version.generator_profile_ref,
            generation_digest=version.generation_digest)
        scope_ref = f"sketch_proposal:{started.proposal_id}"
        copy_ids: list[str] = []
        for copy in self._d.generator.known_copies(request):  # claimed before the call
            self._d.copies.register(started.organization_id, scope_ref, copy)
            copy_ids.append(copy.copy_id)
        outcome = self._d.generator.generate(request)  # never inside a transaction
        for copy in outcome.copies:
            self._d.copies.register(started.organization_id, scope_ref, copy)
            copy_ids.append(copy.copy_id)
        if isinstance(outcome, GenerationFailed):
            code = outcome.code if outcome.code in WORKER_FAILURE_CODES else "PROVIDER_ERROR"
            return refuse(code, outcome.retryable)
        policy = self._d.policy.current(started.organization_id, binding.session_id)
        validated = None if policy is None else validate_output(
            outcome.parts, version.rule, policy, render_sha256=binding.source.render_sha256)
        if validated is None:
            return refuse("OUTPUT_MALFORMED", False)
        if self._post_gate(started.proposal_id, job_id) is None:
            return refuse()
        producer = ProducerRef(outcome.adapter_id, outcome.model_profile_version,
                               outcome.configuration_version, outcome.evidence_kind)
        provenance = DerivativeProvenance(
            origin="ai_derived",
            source_refs=((binding.source.render_ref, binding.source.render_sha256),),
            producer_adapter_id=producer.adapter_id,
            producer_profile_version=producer.model_profile_version,
            classification="child_derived_ai_suggestion", purpose_codes=(binding.purpose_code,))
        asset: AssetRef | None = None
        if validated.asset_body is not None:
            assert validated.asset_media_type is not None
            staged_asset = self._d.admission.stage(
                started.organization_id, job_id, attempt_id, "asset", validated.asset_body,
                validated.asset_media_type, provenance)
            if isinstance(staged_asset, AdmissionRefusal):
                return refuse("OUTPUT_MALFORMED", False)
            asset = _asset(staged_asset)
        document = canonical_json({
            "contract": "SketchGenerationResult", "proposal_id": started.proposal_id,
            "proposal_version": version.version, "job_id": job_id, "attempt_id": attempt_id,
            "text_or_question": validated.text,
            "asset": None if asset is None else asset.canonical(),
            "producer": producer.canonical(), "evidence_kind": producer.evidence_kind,
            "unsafe": outcome.unsafe}).encode("utf-8")
        staged_doc = self._d.admission.stage(started.organization_id, job_id, attempt_id,
                                             "result", document, RESULT_DOCUMENT_MEDIA_TYPE,
                                             provenance)
        if isinstance(staged_doc, AdmissionRefusal):
            return refuse("OUTPUT_MALFORMED", False)
        record = StagedGeneration(job_id, attempt_id, started.proposal_id, version.version,
                                  version.generation_digest, outcome.unsafe, validated.text,
                                  asset, _asset(staged_doc), producer, tuple(copy_ids))
        with self._d.repository.transaction() as tx:
            existing = tx.get_staged(job_id, attempt_id)
            if existing is None:
                tx.put_staged(record)
            else:
                record = existing
        return _claim_from(job, record)

    def _start_generation(self, proposal_id: str, job: SketchJobEvidence) -> SketchProposal | None:
        """C5 with token: a change committed after the pre-gate read is never acted on."""

        result: list[bool] = []

        def decide(proposal: SketchProposal, _: tuple[StagedGeneration, ...]) -> _Plan:
            version = proposal.current
            if version.pipeline_state not in ACTIVE_STATES or version.job_id not in {
                None, job.job_id
            } or version.version != job.request_revision:
                result.append(False)
                return _Plan(None)
            reason = self._current_reason(proposal, level=version.level)

            def apply(tx: SketchUnitOfWork, latest: SketchProposal) -> SketchProposal:
                if reason is not None:
                    result.append(False)
                    return self._invalidate(tx, latest, PipelineState.STALE, reason)
                updated = mark_analyzing(latest, job.job_id, self._d.clock.now())
                if updated is not latest:
                    tx.cas(expected_record_version=latest.record_version, proposal=updated)
                result.append(True)
                return updated

            return _Plan(apply)

        updated = self._decide(proposal_id, _no_refs, decide)
        return updated if result and result[-1] else None

    def _post_gate(self, proposal_id: str, job_id: str) -> SketchProposal | None:
        """After the provider: anything moved means the output may not be kept."""

        result: list[bool] = []

        def decide(proposal: SketchProposal, _: tuple[StagedGeneration, ...]) -> _Plan:
            version = proposal.current
            if version.pipeline_state is not PipelineState.ANALYZING or version.job_id != job_id:
                result.append(False)
                return _Plan(None)
            reason = self._current_reason(proposal, level=version.level)
            if reason is None:
                result.append(True)
                return _Plan(None)

            def apply(tx: SketchUnitOfWork, latest: SketchProposal) -> SketchProposal:
                result.append(False)
                return self._invalidate(tx, latest, PipelineState.STALE, reason)

            return _Plan(apply)

        updated = self._decide(proposal_id, _no_refs, decide)
        return updated if result and result[-1] else None

    # ================================================================ reconcile (C8)
    def reconcile(self, proposal_id: str) -> SketchProposal | None:
        job_cache: dict[str, SketchJobEvidence | None] = {}

        def job_of(proposal: SketchProposal, fresh: bool = False) -> SketchJobEvidence | None:
            job_id = proposal.current.job_id
            if job_id is None:
                return None
            if fresh or job_id not in job_cache:
                job_cache[job_id] = self._d.job_reader.get(job_id)
            return job_cache[job_id]

        def refs(proposal: SketchProposal,
                 staged: tuple[StagedGeneration, ...]) -> tuple[tuple[str, ...], str | None]:
            job = job_of(proposal, fresh=True)
            if proposal.current.pipeline_state is not PipelineState.ANALYZING or job is None:
                return (), None
            chosen = _staged_for_attempt(staged, job.job_id, job.active_attempt_id)
            return (chosen.refs(), chosen.key) if chosen is not None else ((), None)

        def decide(proposal: SketchProposal, staged: tuple[StagedGeneration, ...]) -> _Plan:
            version = proposal.current
            if version.pipeline_state not in ACTIVE_STATES:
                leftovers = _leftover(staged, version.promoted)
                if not leftovers:
                    return _Plan(None)

                def sweep(tx: SketchUnitOfWork, latest: SketchProposal) -> SketchProposal:
                    reason = latest.current.status_reason or StatusReason.SUPERSEDED_BY_REVISION
                    self._cleanup_staged(tx, latest, reason)
                    return latest

                return _Plan(sweep)
            # ``refs`` captured the job snapshot for this decision round. Reuse that exact
            # evidence so the ref-set token and success decision cannot select different
            # attempts if a retry starts between two reads. A retry after this snapshot is
            # observed on the next bounded decision round.
            job = job_of(proposal)
            if job is None or not job.terminal:
                return _Plan(None)
            if job.state == "succeeded":
                return self._decide_success(proposal, staged, job)
            if job.state == "blocked_unsafe":
                return _Plan(lambda tx, latest: self._invalidate(
                    tx, latest, PipelineState.BLOCKED_UNSAFE, StatusReason.UNSAFE_CONTENT))
            if job.state == "failed_exhausted":
                reason = FAILURE_REASONS.get(job.failure_code or "", StatusReason.PROVIDER_ERROR)
                return _Plan(lambda tx, latest: self._invalidate(
                    tx, latest, PipelineState.FAILED, reason))
            # A job the owner cancelled (eligibility) reports the current fact, if any.
            cancelled = self._current_reason(proposal, level=version.level) or (
                StatusReason.JOB_CANCELLED)
            return _Plan(lambda tx, latest: self._invalidate(
                tx, latest, PipelineState.STALE, cancelled))

        return self._decide(proposal_id, refs, decide)

    def _decide_success(self, proposal: SketchProposal, staged: tuple[StagedGeneration, ...],
                        job: SketchJobEvidence) -> _Plan:
        chosen = _staged_for_attempt(staged, job.job_id, job.active_attempt_id)
        if chosen is None:
            return _Plan(None)
        if job.disposition == "stale":
            return _Plan(lambda tx, latest: self._invalidate(
                tx, latest, PipelineState.STALE, StatusReason.CONTEXT_CHANGED))
        if tuple(sorted(job.result_refs)) != chosen.output_pairs():
            return _Plan(lambda tx, latest: self._invalidate(
                tx, latest, PipelineState.FAILED, StatusReason.OUTPUT_MALFORMED))
        if self._quarantined(chosen.refs(), job.job_id, chosen.attempt_id):
            return _Plan(lambda tx, latest: self._invalidate(
                tx, latest, PipelineState.STALE, StatusReason.ARTIFACT_QUARANTINED))
        reason = self._current_reason(proposal, level=proposal.current.level)
        if reason is not None:
            return _Plan(lambda tx, latest: self._invalidate(
                tx, latest, PipelineState.STALE, reason))

        def apply(tx: SketchUnitOfWork, latest: SketchProposal) -> SketchProposal:
            version = latest.current
            digest = content_sha256(latest, version, text=chosen.text, asset=chosen.asset,
                                    producer=chosen.producer)
            output = PromotedOutput(job.job_id, chosen.attempt_id, chosen.text, chosen.asset,
                                    chosen.result_document, chosen.producer, digest)
            updated = promote(latest, output, self._d.clock.now())
            tx.cas(expected_record_version=latest.record_version, proposal=updated)
            tx.update_staged(replace(chosen, status=StagedStatus.PROMOTED))
            tx.add_event(self._event(updated, "sketch.proposal_ready", None))
            self._cleanup_staged(tx, updated, StatusReason.SUPERSEDED_BY_REVISION)
            return updated

        return _Plan(apply)

    def _quarantined(self, refs: tuple[str, ...], job_id: str, attempt_id: str) -> bool:
        for ref in refs:
            descriptor = self._d.artifacts.describe(ref)
            if (descriptor is None or descriptor.quarantine_reason is not None
                    or descriptor.producer_job_id != job_id
                    or descriptor.producer_attempt_id != attempt_id):
                return True
        return False

    def _cleanup_staged(self, tx: SketchUnitOfWork, proposal: SketchProposal,
                        reason: StatusReason) -> None:
        """Supersede every non-promoted staged output and queue its quarantine (C9)."""

        promoted = proposal.current.promoted
        for staged in tx.staged_for(proposal.proposal_id):
            if staged.status is not StagedStatus.STAGED:
                continue
            if promoted is not None and staged.job_id == promoted.job_id and (
                staged.attempt_id == promoted.attempt_id
            ):
                continue
            tx.update_staged(replace(staged, status=StagedStatus.SUPERSEDED))
            tx.add_cleanup(CleanupIntent(
                event_id=event_id(proposal.proposal_id, staged.version, "cleanup", staged.key),
                organization_id=proposal.organization_id, job_id=staged.job_id,
                attempt_id=staged.attempt_id, artifact_refs=staged.refs(),
                reason_code=str(reason)))
            tx.add_event(self._event(proposal, "sketch.cleanup_requested", reason,
                                     discriminator=staged.key))

    def deliver_cleanup(self) -> int:
        """C9: deliver pending quarantine intents; a failing sink keeps them pending."""

        with self._d.repository.transaction() as tx:
            pending = tx.pending_cleanup()
        delivered = 0
        for intent in pending:
            try:
                self._d.quarantine(intent)
            except Exception:
                continue
            with self._d.repository.transaction() as tx:
                tx.mark_cleanup(intent.event_id)
            delivered += 1
        return delivered

    # ================================================================ revalidate
    def revalidate(self, proposal_id: str) -> SketchProposal | None:
        def refs(proposal: SketchProposal,
                 staged: tuple[StagedGeneration, ...]) -> tuple[tuple[str, ...], str | None]:
            promoted = proposal.current.promoted
            if proposal.current.pipeline_state is not PipelineState.PENDING_TEACHER_REVIEW or (
                promoted is None
            ):
                return (), None
            return promoted.refs(), None

        def decide(proposal: SketchProposal, _: tuple[StagedGeneration, ...]) -> _Plan:
            reason = self._content_reason(proposal)
            if proposal.current.pipeline_state is not (
                PipelineState.PENDING_TEACHER_REVIEW
            ) or reason is None:
                return _Plan(None)
            return _Plan(lambda tx, latest: self._invalidate(
                tx, latest, PipelineState.STALE, reason))

        return self._decide(proposal_id, refs, decide)

    def _content_reason(self, proposal: SketchProposal) -> StatusReason | None:
        promoted = proposal.current.promoted
        if promoted is None:
            return None
        if self._quarantined(promoted.refs(), promoted.job_id, promoted.attempt_id):
            return StatusReason.ARTIFACT_QUARANTINED
        return self._current_reason(proposal, level=proposal.current.level)

    # ================================================================ commands
    def cancel(self, command: CancelCommand) -> CommandResult:
        key = self._receipt_key(command.principal, CANCEL_CONTRACT, command.proposal_id,
                                command.idempotency_key)
        if command.if_match is None:
            raise SketchError("PRECONDITION_REQUIRED")
        proposal = self._authorized(command.principal, command.proposal_id, SketchAction.CANCEL)
        replay = self._replay(key, command.fingerprint())
        if replay is not None:
            return replay
        if command.if_match != proposal.etag():
            raise SketchError("PRECONDITION_FAILED")
        if proposal.current.pipeline_state not in ACTIVE_STATES:
            raise SketchError("INVALID_STATE")
        now = self._d.clock.now()
        with self._d.repository.transaction() as tx:
            latest = tx.get(command.proposal_id)
            assert latest is not None
            if latest.record_version != proposal.record_version:
                raise SketchError("PRECONDITION_FAILED")
            updated = self._invalidate(tx, latest, PipelineState.CANCELLED,
                                       StatusReason.CANCELLED_BY_TEACHER)
            tx.put_receipt(SketchReceipt(key, command.fingerprint(), updated.proposal_id,
                                         "cancelled", updated.current.version, now))
        if updated.current.job_id is not None:
            self._cleanup_job(updated.proposal_id, updated.current.job_id, command.principal)
        return CommandResult(updated.proposal_id, "cancelled", updated.current.version, False)

    def revise_level(self, command: ReviseLevelCommand) -> CommandResult:
        key = self._receipt_key(command.principal, REVISE_CONTRACT, command.proposal_id,
                                command.idempotency_key)
        if command.if_match is None:
            raise SketchError("PRECONDITION_REQUIRED")
        proposal = self._authorized(command.principal, command.proposal_id, SketchAction.REVISE)
        replay = self._replay(key, command.fingerprint())
        if replay is not None:
            return replay
        if command.if_match != proposal.etag():
            raise SketchError("PRECONDITION_FAILED")
        if proposal.current.pipeline_state is not PipelineState.PENDING_TEACHER_REVIEW:
            raise SketchError("INVALID_STATE")
        receipt_ref = "rcpt_" + sha256(key.encode()).hexdigest()[:24]
        refused: list[str] = []

        def decide(latest: SketchProposal, _: tuple[StagedGeneration, ...]) -> _Plan:
            if latest.etag() != command.if_match:
                refused.append("PRECONDITION_FAILED")
                return _Plan(None)
            policy = self._d.policy.current(latest.organization_id, latest.binding.session_id)
            if policy_verdict(policy, level=command.new_level,
                              purpose_code=latest.binding.purpose_code,
                              opening=True) is not None or policy is None:
                refused.append("LEVEL_NOT_ALLOWED")
                return _Plan(None)
            rule = policy.rule_for(command.new_level)
            assert rule is not None
            pinned_policy = policy

            def apply(tx: SketchUnitOfWork, current: SketchProposal) -> SketchProposal:
                now = self._d.clock.now()
                revised = revise_version(current, rule=rule, receipt_ref=receipt_ref,
                                         policy=pinned_policy, now=now)
                tx.cas(expected_record_version=current.record_version, proposal=revised)
                tx.publish_invalidation(revised.organization_id)
                tx.add_event(self._event(revised, "sketch.superseded",
                                         StatusReason.SUPERSEDED_BY_REVISION))
                tx.put_receipt(SketchReceipt(key, command.fingerprint(), revised.proposal_id,
                                             "revised", revised.current.version, now))
                return revised

            return _Plan(apply)

        updated = self._decide(command.proposal_id, _no_refs, decide)
        if refused:
            raise SketchError(refused[-1])
        assert updated is not None
        self.schedule(updated.proposal_id)
        return CommandResult(updated.proposal_id, "revised", updated.current.version, False)

    def apply_owner_notice(self, notice: OwnerNotice) -> tuple[str, ...]:
        reason = _NOTICE_REASONS[notice.kind]
        affected: list[str] = []
        cleanup_jobs: list[tuple[str, str]] = []
        with self._d.repository.transaction() as tx:
            if tx.notice_seen(notice.notice_id):
                return ()
            for proposal in tx.list_proposals(notice.organization_id):
                if proposal.current.pipeline_state not in INVALIDATABLE_STATES or not (
                    _notice_matches(notice, proposal.binding)
                ):
                    continue
                updated = self._invalidate(tx, proposal, PipelineState.STALE, reason)
                affected.append(proposal.proposal_id)
                if updated.current.job_id is not None:
                    cleanup_jobs.append((proposal.proposal_id, updated.current.job_id))
            tx.record_notice(notice.notice_id)
        for proposal_id, job_id in cleanup_jobs:
            self._cleanup_job(proposal_id, job_id, None, reason.value)
        return tuple(affected)

    # ================================================================ reads
    def get_record(self, principal: Principal, proposal_id: str) -> dict[str, object]:
        proposal = self._authorized(principal, proposal_id, SketchAction.READ)
        withheld: StatusReason | None = None
        if proposal.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW:
            withheld = self._content_reason(proposal)
            if withheld is not None:
                try:  # read never mutates the proposal; it only asks for a revalidation
                    with self._d.repository.transaction() as tx:
                        tx.request_revalidation(proposal_id)
                except Exception:  # noqa: BLE001 - the read result stays withheld either way
                    pass
        return record_view(proposal, withheld=withheld)

    def device_view(self, principal: Principal, assistance_id: str) -> dict[str, object]:
        with self._d.repository.transaction() as tx:
            proposal_id = tx.find_by_assistance(principal.organization_id, assistance_id)
            proposal = tx.get(proposal_id) if proposal_id is not None else None
        if proposal is None or not self._d.authority.allowed(principal, _scope(proposal),
                                                             SketchAction.DEVICE_VIEW):
            raise SketchError("RESOURCE_NOT_FOUND")
        return {
            "contract_name": "SketchProposalDeviceView",
            "contract_version": "0.1-candidate",
            "assistance_id": assistance_id,
            "status": device_status(proposal.current.pipeline_state),
        }

    # ================================================================ helpers
    def _authorized(self, principal: Principal, proposal_id: str,
                    action: SketchAction) -> SketchProposal:
        if principal.role is not PrincipalRole.TEACHER and action is SketchAction.READ:
            raise SketchError("RESOURCE_NOT_FOUND")
        with self._d.repository.transaction() as tx:
            proposal = tx.get(proposal_id)
        if proposal is None or proposal.organization_id != principal.organization_id:
            raise SketchError("RESOURCE_NOT_FOUND")
        if principal.role is not PrincipalRole.TEACHER:
            raise SketchError("FORBIDDEN_SCOPE")
        if not self._d.authority.allowed(principal, _scope(proposal), action):
            raise SketchError("RESOURCE_NOT_FOUND")
        return proposal

    def _receipt_key(self, principal: Principal, contract: str, proposal_id: str,
                     idempotency_key: str | None) -> str:
        if not idempotency_key or len(idempotency_key) > 120:
            raise SketchError("MALFORMED_REQUEST")
        return "|".join((principal.organization_id, principal.principal_id, contract,
                         proposal_id, idempotency_key))

    def _replay(self, key: str, fingerprint: str) -> CommandResult | None:
        with self._d.repository.transaction() as tx:
            receipt = tx.get_receipt(key)
        if receipt is None:
            return None
        if receipt.fingerprint != fingerprint:
            raise SketchError("IDEMPOTENCY_PAYLOAD_MISMATCH")
        return CommandResult(receipt.proposal_id, receipt.outcome, receipt.result_version, True)

    def _event(self, proposal: SketchProposal, event_type: str, reason: StatusReason | None,
               *, discriminator: str = "") -> SketchEvent:
        version = proposal.current.version
        return SketchEvent(
            event_id(proposal.proposal_id, version, event_type,
                     discriminator or f"{proposal.record_version}"),
            event_type, proposal.organization_id, proposal.proposal_id, version,
            proposal.binding.assistance_id, None if reason is None else str(reason),
            self._d.clock.now())


def _no_refs(proposal: SketchProposal,
             staged: tuple[StagedGeneration, ...]) -> tuple[tuple[str, ...], str | None]:
    return (), None


def _event_for(state: PipelineState) -> str:
    return {
        PipelineState.CANCELLED: "sketch.cancelled",
        PipelineState.FAILED: "sketch.failed",
        PipelineState.BLOCKED_UNSAFE: "sketch.blocked_unsafe",
    }.get(state, "sketch.stale")


def _hint_matches(hint: HandoffHint, binding: HandoffBinding) -> bool:
    return (hint.assistance_id == binding.assistance_id
            and hint.request_revision == binding.request_revision
            and hint.analysis_id == binding.analysis_id
            and hint.analysis_revision == binding.analysis_revision)


def _staged_for_attempt(staged: tuple[StagedGeneration, ...], job_id: str,
                        attempt_id: str) -> StagedGeneration | None:
    return next((s for s in staged if s.job_id == job_id and s.attempt_id == attempt_id), None)


def _leftover(staged: tuple[StagedGeneration, ...],
              promoted: PromotedOutput | None) -> tuple[StagedGeneration, ...]:
    return tuple(s for s in staged if s.status is StagedStatus.STAGED and not (
        promoted is not None and s.job_id == promoted.job_id
        and s.attempt_id == promoted.attempt_id))


def _claim_from(job: SketchJobEvidence, staged: StagedGeneration) -> GenerationClaim:
    return GenerationClaim(staged.job_id, staged.attempt_id, job.request_revision, job.input_hash,
                           job.context_revision, True, outputs=staged.output_pairs(),
                           unsafe=staged.unsafe)


def _asset(staged: StagedArtifact) -> AssetRef:
    return AssetRef(staged.artifact_ref, staged.sha256, staged.media_type, staged.byte_size)


def _scope(proposal: SketchProposal) -> SketchScope:
    binding = proposal.binding
    return SketchScope(binding.organization_id, binding.class_id, binding.session_id,
                       binding.canvas_id, binding.audience)


def _notice_matches(notice: OwnerNotice, binding: HandoffBinding) -> bool:
    if notice.kind is NoticeKind.CONSENT_REVOKED:
        return notice.participant_id in binding.audience
    if notice.kind is NoticeKind.SESSION_ENDED:
        return notice.session_id == binding.session_id
    if notice.kind is NoticeKind.TURN_REVOKED:
        return notice.participant_id == binding.contributor_participant_id and (
            notice.canvas_id in {None, binding.canvas_id})
    return notice.canvas_id == binding.canvas_id


def _utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def record_view(proposal: SketchProposal, *, withheld: StatusReason | None) -> dict[str, object]:
    """Teacher/internal DATA-23 record; content only while pending and current (§4.1)."""

    binding, version = proposal.binding, proposal.current
    promoted = version.promoted
    show = (version.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
            and promoted is not None and withheld is None)
    return {
        "contract_name": "SketchProposalRecord",
        "contract_version": "0.1-candidate",
        "proposal_id": proposal.proposal_id,
        "proposal_version": version.version,
        "review_revision": proposal.review_revision,
        "assistance_id": binding.assistance_id,
        "request_revision": binding.request_revision,
        "source_snapshot_ref": binding.source.snapshot_ref,
        "context_revision": binding.context_revision,
        "assistance_level": version.level,
        "level_source": {"kind": str(version.level_source),
                         "receipt_ref": version.level_source_ref},
        "display_mode": str(version.rule.display_mode),
        "overlay_asset_ref": (promoted.asset.artifact_ref if show and promoted is not None
                              and promoted.asset is not None else None),
        "text_or_question": promoted.text if show and promoted is not None else None,
        "editable_bounds": None,
        "moderation_state": str(version.moderation_state),
        "pipeline_state": str(version.pipeline_state),
        "created_at": _utc(proposal.created_at),
        "approval_ref": None,
        "child_response": None,
        "content_sha256": promoted.content_sha256 if promoted is not None else None,
        "content_withheld_reason": None if withheld is None else str(withheld),
        "organization_id": proposal.organization_id,
        "session_id": binding.session_id,
        "canvas_id": binding.canvas_id,
        "group_id": binding.group_id,
        "audience_participant_ids": list(binding.audience),
        "analysis_ref": {"analysis_id": binding.analysis_id,
                         "analysis_revision": binding.analysis_revision},
        "handoff_kind": str(binding.handoff_kind),
        "cache_source_assistance_id": binding.cache_source_assistance_id,
        "generation_job_ref": (None if promoted is None else
                               {"job_id": promoted.job_id, "attempt_id": promoted.attempt_id}),
        "producer_ref": None if promoted is None else promoted.producer.canonical(),
        "generation_evidence_kind": None if promoted is None else promoted.producer.evidence_kind,
        "policy_ref": {"policy_id": version.policy_id, "version": version.policy_version,
                       "status": version.policy_status},
        "status_reason": None if version.status_reason is None else str(version.status_reason),
        "etag": proposal.etag(),
        "updated_at": _utc(proposal.updated_at),
    }


def event_view(event: SketchEvent) -> dict[str, object]:
    return {
        "contract_name": "SketchProposalEvent",
        "contract_version": "0.1-candidate",
        "event_id": event.event_id,
        "event_type": event.event_type,
        "organization_id": event.organization_id,
        "proposal_id": event.proposal_id,
        "proposal_version": event.proposal_version,
        "assistance_id": event.assistance_id,
        "reason": event.reason,
        "occurred_at": _utc(event.occurred_at),
    }


__all__ = [
    "DECISION_ROUNDS",
    "CancelCommand",
    "CommandResult",
    "NoticeKind",
    "OpenOutcome",
    "OpenResult",
    "OwnerNotice",
    "ReviseLevelCommand",
    "SketchDependencies",
    "SketchError",
    "SketchGenerationService",
    "event_view",
    "record_view",
]
