"""BE2-03 assistance request orchestration (A1 ASSISTANCE_COMPONENT_OFFLINE, plan revision 3).

CMD-32 submit, scheduler, CMD-33 cancel, owner notices, completion/handoff and settlement.
The service never holds an assistance unit of work while it calls BE2-01, BE2-02 or the
Sketch stage; those calls happen between assistance transactions. Policy values and owner
facts come from ports (fixtures in A1); nothing here is an adopted production policy.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256

from sketch2life.application.ports.ai_jobs import (
    ClockPort,
    IdGeneratorPort,
    Principal,
    PrincipalRole,
)
from sketch2life.application.ports.assistance import (
    AnalysisOutcome,
    AnalysisOutcomePort,
    AssistanceAuthorityPort,
    AssistanceEvent,
    AssistanceJobPort,
    AssistanceJobReader,
    AssistanceOwnerPort,
    AssistancePolicyPort,
    AssistanceRepository,
    AssistanceRevisionConflict,
    AssistanceSourcePort,
    AssistanceUniqueConflict,
    AssistanceUnitOfWork,
    AuthorityReason,
    CanvasFacts,
    CommandReceipt,
    JobCreateKind,
    JobCreateRequest,
    JobEvidence,
    ReceiptKey,
    ReceiptOutcome,
    SketchIntent,
    SketchStagePort,
)
from sketch2life.domain.ai_jobs.completion import canonical_sha256
from sketch2life.domain.assistance import (
    CANCEL_CONTRACT,
    CREATE_CONTRACT,
    ActorKind,
    AssistanceRequest,
    AssistanceRuleViolation,
    CacheHit,
    CheckpointRef,
    Contributor,
    HandoffRef,
    PolicySnapshot,
    Requester,
    RequestReason,
    RequestStatus,
    ReservationState,
    ResolvedFacts,
    ScheduleIdentity,
    Settlement,
    SourcePin,
    StatusReason,
    TargetKind,
    TargetScope,
    add_cleanup_job,
    audience_refusal,
    consume,
    create_key,
    debounce_key,
    fail,
    hand_off,
    link_job,
    normalize_child_intent,
    operation_target,
    semantic_identity,
    settle,
    terminate,
)
from sketch2life.domain.vision_analysis import (
    VISION_ANALYSIS_JOB_TYPE,
    AnalysisScope,
    AssistancePin,
    SourceVerdict,
    verify_source,
)

DECISION_ROUNDS = 3
DEFAULT_POLL_AFTER_MS = 2000
_TERMINAL_JOB_STATES = frozenset({"succeeded", "failed_exhausted", "blocked_unsafe", "cancelled"})

_ERRORS: Mapping[str, tuple[int, str]] = {
    "MALFORMED_REQUEST": (400, "The request is malformed."),
    "RESOURCE_NOT_FOUND": (404, "The resource was not found."),
    "FORBIDDEN_SCOPE": (403, "Not permitted for this scope."),
    "GRANT_REVOKED": (403, "Access was revoked."),
    "CONSENT_REQUIRED": (403, "Consent is required for this request."),
    "TURN_CLOSED": (409, "The drawing turn is not open."),
    "INVALID_STATE": (409, "The request cannot change in its current state."),
    "STALE_CONTEXT": (409, "The drawing or context changed; reload it."),
    "POLICY_UNRESOLVED": (409, "Assistance policy is not available."),
    "IDEMPOTENCY_PAYLOAD_MISMATCH": (409, "This key was used for a different request."),
    "IDEMPOTENCY_CONFLICT": (409, "A concurrent request is still settling."),
    "PRECONDITION_REQUIRED": (428, "If-Match is required."),
    "STALE_AGGREGATE": (412, "The request has changed; reload it."),
    "FIELD_VALIDATION_FAILED": (422, "The request has invalid fields."),
    "AGE_NOT_SUPPORTED": (422, "Assistance is not available for this audience."),
    "RATE_LIMITED": (429, "Please keep drawing and try again shortly."),
    "BUDGET_EXCEEDED": (429, "The assistance budget is used up; ask your teacher."),
    "DEPENDENCY_UNAVAILABLE": (503, "A required service is unavailable."),
}
_RETRYABLE = frozenset({"IDEMPOTENCY_CONFLICT", "RATE_LIMITED", "DEPENDENCY_UNAVAILABLE"})
_AUTHORITY_ERRORS = {
    AuthorityReason.NOT_IN_SCOPE: "RESOURCE_NOT_FOUND",
    AuthorityReason.GRANT_REVOKED: "GRANT_REVOKED",
    AuthorityReason.TURN_CLOSED: "TURN_CLOSED",
    AuthorityReason.ROLE_NOT_PERMITTED: "FORBIDDEN_SCOPE",
}
_AUDIENCE_ERRORS = {
    "AUDIENCE_DUPLICATE": "DEPENDENCY_UNAVAILABLE",  # malformed owner data, refused
    "AUDIENCE_MISMATCH": "DEPENDENCY_UNAVAILABLE",
    "AUDIENCE_SIZE": "FIELD_VALIDATION_FAILED",
    "AGE_NOT_SUPPORTED": "AGE_NOT_SUPPORTED",
    "CONSENT_REQUIRED": "CONSENT_REQUIRED",
}
_DEVICE_REASONS = frozenset({RequestReason.CHILD_REQUEST, RequestReason.EXPLICIT_HELP_SIGNAL})
_TEACHER_REASONS = frozenset({RequestReason.TEACHER_REQUEST, RequestReason.EXPLICIT_HELP_SIGNAL})


class AssistanceError(Exception):
    """Typed, safe application error; never names another child or provider detail."""

    def __init__(self, code: str, *, retry_after_s: int | None = None,
                 current_revision: int | None = None) -> None:
        super().__init__(code)
        status, message = _ERRORS[code]
        self.code = code
        self.http_status = status
        self.public_message = message
        self.retryable = code in _RETRYABLE
        self.retry_after_s = retry_after_s
        self.current_revision = current_revision


class _Retry(Exception):
    pass


# ----------------------------------------------------------------------- commands
@dataclass(frozen=True, slots=True)
class SubmitCommand:
    """CMD-32 after transport parsing; actor/role/org come only from ``principal``."""

    principal: Principal
    idempotency_key: str | None
    canvas_id: str
    checkpoint_ref: CheckpointRef
    target: TargetScope
    region_id: str | None
    requested_level: str
    child_intent: str | None
    request_reason: RequestReason
    context_revision: int
    client_request_id: str
    correlation_id: str = "corr_assistance"

    def fingerprint(self) -> str:
        return canonical_sha256({
            "contract_name": CREATE_CONTRACT,
            "canvas_id": self.canvas_id,
            "checkpoint_ref": self.checkpoint_ref.canonical(),
            "target": self.target.canonical(),
            "region_id": self.region_id,
            "requested_level": self.requested_level,
            "child_intent": self.child_intent,
            "request_reason": str(self.request_reason),
            "context_revision": self.context_revision,
            "client_request_id": self.client_request_id,
        })


@dataclass(frozen=True, slots=True)
class CancelCommand:
    principal: Principal
    assistance_id: str
    idempotency_key: str | None
    if_match: str | None
    reason: str | None = None

    def fingerprint(self) -> str:
        return canonical_sha256({
            "contract_name": CANCEL_CONTRACT,
            "assistance_id": self.assistance_id,
            "if_match": self.if_match,
            "reason": self.reason,
        })


@dataclass(frozen=True, slots=True)
class CommandResult:
    request: AssistanceRequest
    outcome: ReceiptOutcome
    replayed: bool


class NoticeKind(StrEnum):
    CONSENT_REVOKED = "consent_revoked"
    SESSION_ENDED = "session_ended"
    TURN_REVOKED = "turn_revoked"
    CANVAS_RESTORED = "canvas_restored"


_NOTICE_REASONS = {
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
class AssistanceDependencies:
    repository: AssistanceRepository
    owner: AssistanceOwnerPort
    authority: AssistanceAuthorityPort
    sources: AssistanceSourcePort
    policy: AssistancePolicyPort
    jobs: AssistanceJobPort
    job_reader: AssistanceJobReader
    analyses: AnalysisOutcomePort
    sketch_stage: SketchStagePort
    clock: ClockPort
    ids: IdGeneratorPort
    auto_schedule: bool = True
    poll_after_ms: int = DEFAULT_POLL_AFTER_MS


@dataclass(frozen=True, slots=True)
class _Resolution:
    canvas: CanvasFacts
    facts: ResolvedFacts
    contributor: Contributor
    policy: PolicySnapshot
    digest: str
    identity: str
    op_target: str
    debounce: str


class AssistanceService:
    def __init__(self, deps: AssistanceDependencies) -> None:
        self._d = deps

    # ================================================================ CMD-32
    def submit(self, command: SubmitCommand) -> CommandResult:
        principal = command.principal
        kind = _actor_kind(principal)
        key = _required_key(command.idempotency_key)
        try:
            intent = normalize_child_intent(command.child_intent)
        except AssistanceRuleViolation:
            raise AssistanceError("FIELD_VALIDATION_FAILED") from None
        # A1-CR05: one canonical (NFC, trimmed) command drives the fingerprint, semantic
        # identity and storage; equivalent client spellings replay/deduplicate together.
        command = replace(command, child_intent=intent)
        allowed = _DEVICE_REASONS if kind is ActorKind.DEVICE else _TEACHER_REASONS
        if command.request_reason not in allowed or (
            kind is ActorKind.TEACHER and command.child_intent is not None
        ):
            raise AssistanceError("FIELD_VALIDATION_FAILED")
        receipt_key = ReceiptKey(principal.organization_id, principal.principal_id,
                                 CREATE_CONTRACT, command.canvas_id, key)
        fingerprint = command.fingerprint()
        replay = self._replay(receipt_key, principal, fingerprint)
        if replay is not None:
            return replay

        for _ in range(DECISION_ROUNDS):
            # A1-CR03: every owner/source/policy/disclosure/cache decision below is read at
            # one decision epoch and may commit only while that epoch is still current.
            epoch = self._decision_epoch(principal.organization_id)
            resolution = self._resolve_for(command, kind)
            if resolution.policy.purpose_code != resolution.facts.purpose_code:  # pragma: no cover
                raise AssistanceError("POLICY_UNRESOLVED")
            cache = self._cache_candidate(principal, resolution)
            try:
                return self._commit_submit(command, kind, receipt_key, fingerprint,
                                           resolution, cache, epoch)
            except _Retry:
                continue
        raise AssistanceError("IDEMPOTENCY_CONFLICT")

    def _decision_epoch(self, organization_id: str) -> tuple[int, ...]:
        with self._d.repository.transaction() as tx:
            return tx.decision_epoch(organization_id)

    def _resolve_for(self, command: SubmitCommand, kind: ActorKind) -> _Resolution:
        principal = command.principal
        canvas = self._d.owner.canvas(principal.organization_id, command.canvas_id)
        if canvas is None or canvas.organization_id != principal.organization_id:
            raise AssistanceError("RESOURCE_NOT_FOUND")
        decision = self._d.authority.decide(principal, canvas)
        if not decision.allowed:
            raise AssistanceError(_AUTHORITY_ERRORS[decision.reason or
                                                    AuthorityReason.NOT_IN_SCOPE])
        if not canvas.session_active:
            raise AssistanceError("INVALID_STATE")
        target = command.target
        if kind is ActorKind.DEVICE:
            bound = decision.contributor
            if bound is None or bound.turn_id is None:
                raise AssistanceError("TURN_CLOSED")
            if target.kind is not TargetKind.INDIVIDUAL or target.ref_id != bound.participant_id:
                raise AssistanceError("FORBIDDEN_SCOPE")
        audience, roster_revision = self._audience(canvas, target)
        contributor = (decision.contributor if kind is ActorKind.DEVICE
                       else self._teacher_contributor(canvas, audience))
        assert contributor is not None
        self._check_region(canvas, command.region_id, kind, contributor)
        source = self._resolve_source(canvas, command.checkpoint_ref)
        if command.context_revision != canvas.context_revision:
            raise AssistanceError("STALE_CONTEXT", current_revision=canvas.context_revision)
        policy = self._d.policy.current(canvas.organization_id, canvas.session_id)
        if policy is None:
            raise AssistanceError("POLICY_UNRESOLVED")
        members = self._d.owner.members(canvas.organization_id, audience, policy.purpose_code)
        refusal = audience_refusal(audience, members)
        if refusal is not None:
            raise AssistanceError(_AUDIENCE_ERRORS[refusal])
        if not policy.assistance_enabled:
            self._refusal_event(canvas.organization_id, "ASSISTANCE_DISABLED", command)
            raise AssistanceError("FORBIDDEN_SCOPE")
        if command.requested_level not in policy.allowed_levels:
            raise AssistanceError("FIELD_VALIDATION_FAILED")
        facts = ResolvedFacts(
            organization_id=canvas.organization_id,
            class_id=canvas.class_id,
            session_id=canvas.session_id,
            canvas_id=canvas.canvas_id,
            group_id=canvas.group_id,
            roster_revision=roster_revision,
            target=target,
            region_id=command.region_id,
            region_policy_revision=canvas.region_policy_revision,
            contributor_participant_id=contributor.participant_id,
            audience=audience,
            members=members,
            purpose_code=policy.purpose_code,
            age_policy_ref=canvas.age_policy_ref,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            context_revision=canvas.context_revision,
            source=source,
        )
        digest = facts.digest()
        identity = semantic_identity(
            facts, digest=digest, checkpoint_ref=command.checkpoint_ref,
            requested_level=command.requested_level, requester=kind,
            reason=command.request_reason, child_intent=command.child_intent,
        )
        return _Resolution(
            canvas=canvas, facts=facts, contributor=contributor, policy=policy, digest=digest,
            identity=identity,
            op_target=operation_target(canvas.canvas_id, target, command.region_id,
                                       command.checkpoint_ref, command.requested_level),
            debounce=debounce_key(canvas.canvas_id, target),
        )

    def _audience(self, canvas: CanvasFacts,
                  target: TargetScope) -> tuple[tuple[str, ...], int | None]:
        if target.kind is TargetKind.INDIVIDUAL:
            if canvas.mode == "personal":
                if target.ref_id != canvas.personal_participant_id:
                    raise AssistanceError("FORBIDDEN_SCOPE")
                return (target.ref_id,), None
            if canvas.group_id is None:
                raise AssistanceError("FORBIDDEN_SCOPE")
            roster = self._d.owner.roster(canvas.session_id, canvas.group_id)
            if roster is None or target.ref_id not in roster.members:
                raise AssistanceError("FORBIDDEN_SCOPE")
            return (target.ref_id,), roster.revision
        if canvas.mode != "collaborative" or canvas.group_id != target.ref_id:
            raise AssistanceError("FORBIDDEN_SCOPE")
        roster = self._d.owner.roster(canvas.session_id, target.ref_id)
        if roster is None:
            raise AssistanceError("RESOURCE_NOT_FOUND")
        return tuple(roster.members), roster.revision

    def _teacher_contributor(self, canvas: CanvasFacts,
                             audience: tuple[str, ...]) -> Contributor:
        """D5: bound-turn participant in the audience, else the personal owner, else refuse."""

        turn = self._d.owner.current_turn(canvas.canvas_id)
        if turn is not None and turn.participant_id in audience:
            return turn
        if canvas.mode == "personal" and canvas.personal_participant_id in audience:
            assert canvas.personal_participant_id is not None
            return Contributor(canvas.personal_participant_id, None, None)
        raise AssistanceError("TURN_CLOSED")

    @staticmethod
    def _check_region(canvas: CanvasFacts, region_id: str | None, kind: ActorKind,
                      contributor: Contributor) -> None:
        if region_id is None:
            return
        if region_id not in canvas.regions:
            raise AssistanceError("FIELD_VALIDATION_FAILED")
        permitted = canvas.regions[region_id]
        if kind is ActorKind.DEVICE and permitted is not None and (
            contributor.participant_id not in permitted
        ):
            raise AssistanceError("FORBIDDEN_SCOPE")

    def _resolve_source(self, canvas: CanvasFacts, ref: CheckpointRef) -> SourcePin:
        resolved = self._d.sources.resolve(canvas.organization_id, canvas.canvas_id, ref)
        if resolved is None:
            raise AssistanceError("STALE_CONTEXT")
        snapshot = resolved.snapshot
        checkpoint = snapshot.checkpoint
        if (
            ref.document_epoch != canvas.document_epoch
            or checkpoint.document_epoch != ref.document_epoch
            or checkpoint.checkpoint_id != ref.checkpoint_id
            or checkpoint.checksum_sha256 != ref.hash
            or resolved.server_sequence != ref.server_sequence
            or verify_source(snapshot, resolved.admission,
                             organization_id=canvas.organization_id,
                             canvas_id=canvas.canvas_id) is not SourceVerdict.PROCEED
        ):
            raise AssistanceError("STALE_CONTEXT")
        return SourcePin(
            snapshot_ref=snapshot.snapshot_ref,
            checkpoint_id=checkpoint.checkpoint_id,
            document_epoch=checkpoint.document_epoch,
            server_sequence=resolved.server_sequence,
            checkpoint_checksum=checkpoint.checksum_sha256,
            render_ref=snapshot.render.render_ref,
            render_sha256=snapshot.render.render_sha256,
            input_hash=snapshot.input_hash(),
        )

    def _commit_submit(
        self,
        command: SubmitCommand,
        kind: ActorKind,
        receipt_key: ReceiptKey,
        fingerprint: str,
        resolution: _Resolution,
        cache: CacheHit | None,
        epoch: tuple[int, ...],
    ) -> CommandResult:
        principal = command.principal
        org = resolution.facts.organization_id
        now = self._d.clock.now()
        superseded: list[str] = []
        refusal: AssistanceError | None = None
        result: CommandResult | None = None
        with self._d.repository.transaction() as tx:
            prior = tx.get_receipt(receipt_key)
            if prior is not None:
                return self._replayed(prior, principal, fingerprint)
            if tx.decision_epoch(org) != epoch:
                raise _Retry()  # A1-CR03: owner facts moved after the decision; re-decide
            winner_id = tx.find_active_semantic(org, resolution.identity)
            if winner_id is not None:
                winner = tx.get(winner_id)
                assert winner is not None
                if not self._d.authority.disclose(principal, winner):
                    raise AssistanceError("RESOURCE_NOT_FOUND")
                tx.put_receipt(CommandReceipt(receipt_key, fingerprint,
                                              ReceiptOutcome.DEDUPLICATED, winner, now))
                tx.add_event(self._event("assistance.deduplicated", winner, None,
                                         discriminator=_key_digest(receipt_key)))
                return CommandResult(winner, ReceiptOutcome.DEDUPLICATED, False)
            for other in tx.active_by_operation_target(org, resolution.op_target):
                # A1-CR04: only an owner-fact binding that is no longer current supersedes;
                # a different intent/requester over the same facts stays active and the new
                # request is subject to debounce/budget like any other.
                if other.assistance_context_digest == resolution.digest:
                    continue
                stale = terminate(other, RequestStatus.STALE,
                                  StatusReason.SUPERSEDED_BY_FACT_CHANGE, now,
                                  counts_for_debounce=False)
                tx.cas(expected_record_version=other.record_version, request=stale)
                tx.publish_request_fence(org)
                tx.add_event(self._event("assistance.superseded", stale,
                                         str(StatusReason.SUPERSEDED_BY_FACT_CHANGE)))
                superseded.append(other.assistance_id)
            if cache is not None and tx.find_cache(org, resolution.identity) == cache:
                request = self._new_request(command, kind, resolution, now, cache=cache)
                tx.insert(request)
                tx.put_receipt(CommandReceipt(receipt_key, fingerprint,
                                              ReceiptOutcome.CACHE_HIT, request, now))
                tx.add_event(self._event("assistance.requested", request, None))
                tx.add_event(self._event("assistance.analysis_ready", request, "CACHE_HIT"))
                result = CommandResult(request, ReceiptOutcome.CACHE_HIT, False)
            else:
                refusal = self._limits(tx, resolution, now)
                if refusal is not None:
                    tx.add_event(self._refusal(org, refusal.code, receipt_key, now))
                else:
                    request = self._new_request(command, kind, resolution, now, cache=None)
                    try:
                        tx.insert(request)
                    except AssistanceUniqueConflict:
                        raise _Retry() from None
                    tx.put_receipt(CommandReceipt(receipt_key, fingerprint,
                                                  ReceiptOutcome.CREATED, request, now))
                    tx.add_event(self._event("assistance.requested", request, None))
                    result = CommandResult(request, ReceiptOutcome.CREATED, False)
        for assistance_id in superseded:
            self.reconcile(assistance_id)
        if refusal is not None:
            raise refusal
        assert result is not None
        if result.outcome is ReceiptOutcome.CREATED and self._d.auto_schedule:
            self.schedule(result.request.assistance_id)
        return result

    def _limits(self, tx: AssistanceUnitOfWork, resolution: _Resolution,
                now: datetime) -> AssistanceError | None:
        """Debounce then budget (§9). Values are injected fixture policy."""

        policy, facts = resolution.policy, resolution.facts
        last = tx.latest_counted(facts.organization_id, resolution.debounce)
        if last is not None:
            elapsed = now - last
            window = timedelta(seconds=policy.debounce_seconds)
            if elapsed < window:
                remaining = int((window - elapsed).total_seconds()) or 1
                return AssistanceError("RATE_LIMITED", retry_after_s=remaining)
        if (
            tx.count_reserved(facts.organization_id, facts.session_id, facts.target.key())
            >= policy.per_target_limit
            or tx.count_reserved(facts.organization_id, facts.session_id, None)
            >= policy.per_session_limit
        ):
            return AssistanceError("BUDGET_EXCEEDED")
        return None

    def _new_request(self, command: SubmitCommand, kind: ActorKind, resolution: _Resolution,
                     now: datetime, *, cache: CacheHit | None) -> AssistanceRequest:
        assistance_id = self._d.ids.new_id("assist")
        reservation_id = None if cache is not None else self._d.ids.new_id("budget")
        return AssistanceRequest(
            assistance_id=assistance_id,
            request_revision=1,
            record_version=1,
            facts=resolution.facts,
            checkpoint_ref=command.checkpoint_ref,
            requested_level=command.requested_level,
            request_reason=command.request_reason,
            child_intent=command.child_intent,
            client_request_id=command.client_request_id,
            requester=Requester(command.principal.principal_id, kind),
            contributor=resolution.contributor,
            assistance_context_digest=resolution.digest,
            semantic_identity=resolution.identity,
            operation_target=resolution.op_target,
            debounce_key=resolution.debounce,
            status=(RequestStatus.ANALYSIS_READY if cache is not None
                    else RequestStatus.SCHEDULING),
            status_reason=None,
            job_id=None,
            schedule=None if cache is not None else ScheduleIdentity(
                create_key(assistance_id, 1), command.principal.principal_id, kind, 1),
            reservation_id=reservation_id,
            reservation=None if cache is not None else ReservationState.HELD,
            settlement=Settlement.SETTLED if cache is not None else Settlement.OPEN,
            cleanup_job_ids=(),
            cancelled_by=None,
            counts_for_debounce=cache is None,
            cache_hit_of=cache,
            handoff=None,
            created_at=now,
            updated_at=now,
        )

    # ---------------------------------------------------------------- cache gate
    def _cache_candidate(self, principal: Principal,
                         resolution: _Resolution) -> CacheHit | None:
        """D7 supported current-read gate; never worker replay on a terminal job."""

        if not resolution.policy.cache_enabled:
            return None
        org = resolution.facts.organization_id
        with self._d.repository.transaction() as tx:
            hit = tx.find_cache(org, resolution.identity)
            original = tx.get(hit.assistance_id) if hit is not None else None
        if hit is None or original is None:
            return None
        # A1-CR01: cache provenance is the original resource; the requesting principal must
        # currently be allowed to disclose it (a new idempotency key changes nothing).
        if not self._d.authority.disclose(principal, original):
            return None
        if (
            original.status is not RequestStatus.ANALYSIS_READY
            or original.semantic_identity != resolution.identity
        ):
            return None
        evidence = self._d.job_reader.evidence(org, original.assistance_id, (hit.job_id,))
        job = _find(evidence, hit.job_id)
        if job is None or job.state != "succeeded":
            return None
        outcome = self._d.analyses.current(org, hit.analysis_id)
        if (
            outcome is None
            or outcome.accepted_status != "accepted"
            or outcome.meaning_state == "not_applicable"
            or not _outcome_matches(outcome, original, hit.job_id, original.schedule)
        ):
            return None
        return hit

    # ================================================================ scheduler
    def schedule(self, assistance_id: str) -> AssistanceRequest | None:
        """One scheduler pass with the frozen identity (§8.2). Never inside a transaction."""

        with self._d.repository.transaction() as tx:
            request = tx.get(assistance_id)
        if (
            request is None
            or request.status is not RequestStatus.SCHEDULING
            or request.schedule is None
        ):
            return self.reconcile(assistance_id) if request is not None else None
        schedule = request.schedule
        facts = request.facts
        outcome = self._d.jobs.create(JobCreateRequest(
            principal=Principal(schedule.principal_id, facts.organization_id,
                                PrincipalRole.TEACHER if schedule.principal_kind
                                is ActorKind.TEACHER else PrincipalRole.DEVICE),
            idempotency_key=schedule.create_key,
            job_type=VISION_ANALYSIS_JOB_TYPE,
            target_id=request.assistance_id,
            purpose_code=facts.purpose_code,
            session_id=facts.session_id,
            subject_refs=facts.audience,
            request_id=request.assistance_id,
            request_revision=schedule.request_revision,
            input_hash=facts.source.input_hash,
            context_revision=facts.context_revision,
            correlation_id=f"corr_{request.assistance_id}",
        ))
        cleanup: str | None = None
        for _ in range(DECISION_ROUNDS):
            now = self._d.clock.now()
            with self._d.repository.transaction() as tx:
                current = tx.get(assistance_id)
                assert current is not None
                if outcome.kind is JobCreateKind.CREATED:
                    assert outcome.job_id is not None
                    if (current.status is RequestStatus.SCHEDULING
                            and current.request_revision == schedule.request_revision):
                        updated = link_job(current, outcome.job_id, now)
                        event = self._event("assistance.scheduled", updated, None)
                    elif current.job_id == outcome.job_id:
                        break
                    else:  # link lost to cancel/stale: keep the job for cleanup
                        updated = add_cleanup_job(current, outcome.job_id, now)
                        cleanup = outcome.job_id
                        event = None
                elif outcome.kind is JobCreateKind.REFUSED and (
                    current.status is RequestStatus.SCHEDULING
                ):
                    updated = terminate(current, RequestStatus.STALE,
                                        StatusReason.SCHEDULE_REFUSED, now)
                    tx.publish_request_fence(facts.organization_id)
                    event = self._event("assistance.stale", updated, outcome.code)
                else:
                    break
                if updated is not current:
                    try:
                        tx.cas(expected_record_version=current.record_version,
                               request=updated)
                    except AssistanceRevisionConflict:
                        continue
                if event is not None:
                    tx.add_event(event)
            break
        if cleanup is not None:
            self._cleanup_cancel(assistance_id, cleanup)
        return self.reconcile(assistance_id)

    def schedule_pending(self, organization_id: str) -> tuple[str, ...]:
        with self._d.repository.transaction() as tx:
            pending = tuple(r.assistance_id for r in tx.list_requests(organization_id)
                            if r.status is RequestStatus.SCHEDULING)
        for assistance_id in pending:
            self.schedule(assistance_id)
        return pending

    def _cleanup_cancel(self, assistance_id: str, job_id: str) -> None:
        """Best-effort explicit job cancel with the canceller's authority; the fenced
        request-aware eligibility denies any further dispatch/start regardless."""

        with self._d.repository.transaction() as tx:
            request = tx.get(assistance_id)
        if request is None or request.cancelled_by is None:
            return
        evidence = self._d.job_reader.evidence(request.facts.organization_id, assistance_id,
                                               (job_id,))
        job = _find(evidence, job_id)
        if job is None or job.terminal:
            return
        canceller = request.cancelled_by
        self._d.jobs.cancel(
            Principal(canceller.principal_id, request.facts.organization_id,
                      PrincipalRole.TEACHER if canceller.kind is ActorKind.TEACHER
                      else PrincipalRole.DEVICE),
            job_id, job.job_revision,
        )

    # ================================================================ CMD-33
    def cancel(self, command: CancelCommand) -> CommandResult:
        principal = command.principal
        kind = _actor_kind(principal)
        key = _required_key(command.idempotency_key)
        receipt_key = ReceiptKey(principal.organization_id, principal.principal_id,
                                 CANCEL_CONTRACT, command.assistance_id, key)
        fingerprint = command.fingerprint()
        replay = self._replay(receipt_key, principal, fingerprint)
        if replay is not None:
            return replay
        reason = (StatusReason.CANCELLED_BY_TEACHER if kind is ActorKind.TEACHER
                  else StatusReason.CANCELLED_BY_CHILD)
        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                request = tx.get(command.assistance_id)
                epoch = tx.decision_epoch(principal.organization_id)
            self._authorize_cancel(principal, kind, request)
            assert request is not None
            if command.if_match is None:
                raise AssistanceError("PRECONDITION_REQUIRED")
            now = self._d.clock.now()
            with self._d.repository.transaction() as tx:
                prior = tx.get_receipt(receipt_key)
                if prior is not None:
                    return self._replayed(prior, principal, fingerprint)
                if tx.decision_epoch(principal.organization_id) != epoch:
                    continue  # A1-CR03: authority facts moved after the decision; re-decide
                current = tx.get(command.assistance_id)
                assert current is not None
                if command.if_match != current.etag():
                    raise AssistanceError("STALE_AGGREGATE",
                                          current_revision=current.request_revision)
                if current.terminal:
                    raise AssistanceError("INVALID_STATE")
                updated = terminate(current, RequestStatus.CANCELLED, reason, now,
                                    cancelled_by=Requester(principal.principal_id, kind))
                try:
                    tx.cas(expected_record_version=current.record_version, request=updated)
                except AssistanceRevisionConflict:
                    continue
                tx.publish_request_fence(updated.facts.organization_id)
                tx.put_receipt(CommandReceipt(receipt_key, fingerprint,
                                              ReceiptOutcome.CANCELLED, updated, now))
                tx.add_event(self._event("assistance.cancelled", updated, str(reason)))
            if updated.job_id is not None:
                self._cleanup_cancel(updated.assistance_id, updated.job_id)
            self.reconcile(updated.assistance_id)
            return CommandResult(updated, ReceiptOutcome.CANCELLED, False)
        raise AssistanceError("IDEMPOTENCY_CONFLICT")

    def _authorize_cancel(self, principal: Principal, kind: ActorKind,
                          request: AssistanceRequest | None) -> None:
        if request is None or request.facts.organization_id != principal.organization_id:
            raise AssistanceError("RESOURCE_NOT_FOUND")
        canvas = self._d.owner.canvas(principal.organization_id, request.facts.canvas_id)
        if canvas is None:
            raise AssistanceError("RESOURCE_NOT_FOUND")
        decision = self._d.authority.decide(principal, canvas)
        if not decision.allowed:
            raise AssistanceError(_AUTHORITY_ERRORS[decision.reason or
                                                    AuthorityReason.NOT_IN_SCOPE])
        if kind is ActorKind.TEACHER and not self._d.authority.disclose(principal, request):
            raise AssistanceError("RESOURCE_NOT_FOUND")
        if kind is ActorKind.DEVICE:
            # D3/CMD-33: a device on the same canvas may cancel only an individual request
            # whose target is its currently bound participant; group/other targets are 403.
            bound = decision.contributor
            target = request.facts.target
            if (
                bound is None
                or target.kind is not TargetKind.INDIVIDUAL
                or target.ref_id != bound.participant_id
            ):
                raise AssistanceError("FORBIDDEN_SCOPE")

    # ================================================================ notices
    def apply_owner_notice(self, notice: OwnerNotice) -> tuple[str, ...]:
        reason = _NOTICE_REASONS[notice.kind]
        affected: list[str] = []
        with self._d.repository.transaction() as tx:
            if tx.notice_seen(notice.notice_id):
                return ()
            now = self._d.clock.now()
            for request in tx.list_requests(notice.organization_id):
                if request.terminal or not _notice_matches(notice, request):
                    continue
                stale = terminate(request, RequestStatus.STALE, reason, now)
                tx.cas(expected_record_version=request.record_version, request=stale)
                tx.add_event(self._event("assistance.stale", stale, str(reason)))
                affected.append(request.assistance_id)
            if affected:
                tx.publish_request_fence(notice.organization_id)
            tx.record_notice(notice.notice_id)
        for assistance_id in affected:
            self.reconcile(assistance_id)
        return tuple(affected)

    # ================================================================ reconcile
    def reconcile(self, assistance_id: str) -> AssistanceRequest | None:
        """Observe BE2-01 job evidence: consume, fail, hand off or settle (§8.2–§9.1)."""

        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                request = tx.get(assistance_id)
                epoch = (None if request is None
                         else tx.decision_epoch(request.facts.organization_id))
            if request is None or request.settlement is Settlement.SETTLED:
                return request
            assert epoch is not None
            if request.status is RequestStatus.SCHEDULING and not request.cleanup_job_ids:
                return request
            known = tuple(j for j in (request.job_id, *request.cleanup_job_ids)
                          if j is not None)
            evidence = self._d.job_reader.evidence(request.facts.organization_id,
                                                   assistance_id, known)
            if evidence is None:
                return request  # unknown evidence: an unconsumed hold stays held
            try:
                return self._apply_evidence(request, evidence, epoch)
            except _Retry:
                continue
        with self._d.repository.transaction() as tx:
            return tx.get(assistance_id)

    def _apply_evidence(self, request: AssistanceRequest, evidence: tuple[JobEvidence, ...],
                        epoch: tuple[int, ...]) -> AssistanceRequest:
        any_started = any(job.any_attempt_started for job in evidence)
        all_terminal = all(job.terminal for job in evidence)
        handoff: tuple[HandoffRef, SketchIntent] | None = None
        transition: tuple[RequestStatus, StatusReason] | None = None
        if request.status is RequestStatus.SCHEDULED:
            linked = _find(evidence, request.job_id)
            if linked is not None and linked.state == "succeeded":
                handoff, transition = self._handoff_gate(request, linked)
            elif linked is not None and linked.state in {"failed_exhausted", "blocked_unsafe"}:
                transition = (RequestStatus.FAILED, StatusReason.JOB_FAILED)
            elif linked is not None and linked.state == "cancelled":
                transition = (RequestStatus.STALE, StatusReason.JOB_CANCELLED)
        now = self._d.clock.now()
        intent: SketchIntent | None = None
        with self._d.repository.transaction() as tx:
            current = tx.get(request.assistance_id)
            assert current is not None
            org = current.facts.organization_id
            # A1-CR03: the gate's owner/source/analysis reads are valid only at the epoch
            # they were taken; any coordinated owner publication since then re-decides.
            if current.record_version != request.record_version or (
                tx.decision_epoch(org) != epoch
            ):
                raise _Retry()
            updated = current
            if handoff is not None:
                ref, intent = handoff
                updated = hand_off(updated, ref, now)
                tx.put_cache(org, updated.semantic_identity, CacheHit(
                    updated.assistance_id, updated.request_revision, ref.job_id,
                    ref.analysis_id, ref.analysis_revision))
                tx.add_sketch_intent(intent)
                tx.publish_request_fence(org)
                tx.add_event(self._event("assistance.analysis_ready", updated, None))
                tx.add_event(self._event("assistance.sketch_intent_simulated", updated,
                                         intent.status))
            elif transition is not None:
                status, reason = transition
                if status is RequestStatus.FAILED:
                    updated = fail(updated, reason, now)
                    tx.add_event(self._event("assistance.failed", updated, str(reason)))
                else:
                    updated = terminate(updated, status, reason, now)
                    tx.add_event(self._event("assistance.stale", updated, str(reason)))
                tx.publish_request_fence(org)
            if any_started:
                updated = consume(updated, now)
            if updated.terminal and all_terminal:
                updated = settle(updated, now, any_started=any_started)
                tx.add_event(self._event("assistance.cleanup_settled", updated,
                                         str(updated.reservation)
                                         if updated.reservation is not None else None))
            if updated is not current:
                tx.cas(expected_record_version=current.record_version, request=updated)
        if intent is not None:
            self._d.sketch_stage.request_sketch(intent)
        return updated

    def _handoff_gate(
        self, request: AssistanceRequest, job: JobEvidence
    ) -> tuple[tuple[HandoffRef, SketchIntent] | None, tuple[RequestStatus, StatusReason] | None]:
        org = request.facts.organization_id
        # Owner facts first: a moved binding (e.g. revoked consent, which may also make the
        # analysis unreadable) is staleness, not an analysis failure.
        if self._current_digest(request) != request.assistance_context_digest:
            return None, (RequestStatus.STALE, StatusReason.CONTEXT_CHANGED)
        outcome = self._d.analyses.for_attempt(org, job.job_id, job.active_attempt_id)
        if outcome is None or outcome.accepted_status == "rejected":
            return None, (RequestStatus.FAILED, StatusReason.ANALYSIS_REJECTED)
        if outcome.accepted_status != "accepted" or outcome.meaning_state == "not_applicable":
            return None, (RequestStatus.STALE, StatusReason.CONTEXT_CHANGED)
        if not _outcome_matches(outcome, request, job.job_id, request.schedule):
            return None, (RequestStatus.STALE, StatusReason.SOURCE_CHANGED)
        ref = HandoffRef(outcome.analysis_id, outcome.analysis_revision, job.job_id,
                         job.active_attempt_id)
        intent = SketchIntent(
            intent_id="sketch_intent_" + sha256(
                f"{request.assistance_id}|{outcome.analysis_id}".encode()).hexdigest()[:20],
            assistance_id=request.assistance_id,
            request_revision=request.request_revision,
            analysis_id=outcome.analysis_id,
            analysis_revision=outcome.analysis_revision,
        )
        return (ref, intent), None

    def _current_digest(self, request: AssistanceRequest) -> str | None:
        """Recompute the owner-fact binding now, without any principal (§8.4)."""

        facts = request.facts
        canvas = self._d.owner.canvas(facts.organization_id, facts.canvas_id)
        policy = self._d.policy.current(facts.organization_id, facts.session_id)
        if canvas is None or policy is None or not canvas.session_active:
            return None
        try:
            audience, roster_revision = self._audience(canvas, facts.target)
            source = self._resolve_source(canvas, request.checkpoint_ref)
        except AssistanceError:
            return None
        members = self._d.owner.members(facts.organization_id, audience, facts.purpose_code)
        if audience_refusal(audience, members) is not None:
            return None
        if facts.region_id is not None and facts.region_id not in canvas.regions:
            return None
        current = replace(
            facts, roster_revision=roster_revision, audience=audience, members=members,
            region_policy_revision=canvas.region_policy_revision,
            context_revision=canvas.context_revision, source=source,
            age_policy_ref=canvas.age_policy_ref, policy_id=policy.policy_id,
            policy_version=policy.version, purpose_code=policy.purpose_code,
        )
        return current.digest()

    # ================================================================ reads
    def pin(self, assistance_id: str) -> AssistancePin | None:
        """``AssistanceRequestPort`` for BE2-02: the current revision (bumped by cancel/stale)."""

        with self._d.repository.transaction() as tx:
            request = tx.get(assistance_id)
        if request is None:
            return None
        facts = request.facts
        return AssistancePin(
            assistance_id=request.assistance_id,
            request_revision=request.request_revision,
            input_snapshot_ref=facts.source.snapshot_ref,
            context_revision=facts.context_revision,
            scope=AnalysisScope(
                organization_id=facts.organization_id,
                class_id=facts.class_id,
                session_id=facts.session_id,
                canvas_id=facts.canvas_id,
                group_id=facts.group_id,
                contributor_participant_id=facts.contributor_participant_id,
                audience_participant_ids=facts.audience,
                purpose_code=facts.purpose_code,
            ),
        )

    def read(self, principal: Principal, assistance_id: str) -> AssistanceRequest:
        with self._d.repository.transaction() as tx:
            request = tx.get(assistance_id)
        if (
            request is None
            or request.facts.organization_id != principal.organization_id
            or not self._d.authority.disclose(principal, request)
        ):
            raise AssistanceError("RESOURCE_NOT_FOUND")
        return request

    @property
    def poll_after_ms(self) -> int:
        return self._d.poll_after_ms

    # ================================================================ helpers
    def _replay(self, key: ReceiptKey, principal: Principal,
                fingerprint: str) -> CommandResult | None:
        with self._d.repository.transaction() as tx:
            receipt = tx.get_receipt(key)
        if receipt is None:
            return None
        return self._replayed(receipt, principal, fingerprint)

    def _replayed(self, receipt: CommandReceipt, principal: Principal,
                  fingerprint: str) -> CommandResult:
        """Accepted-receipt rule: current disclosure first, then exact fingerprint."""

        if not self._d.authority.disclose(principal, receipt.snapshot):
            raise AssistanceError("RESOURCE_NOT_FOUND")
        if receipt.fingerprint != fingerprint:
            raise AssistanceError("IDEMPOTENCY_PAYLOAD_MISMATCH")
        return CommandResult(receipt.snapshot, receipt.outcome, True)

    def _event(self, event_type: str, request: AssistanceRequest, reason: str | None, *,
               discriminator: str | None = None) -> AssistanceEvent:
        material = f"{event_type}|{request.assistance_id}|{request.record_version}|" \
                   f"{discriminator or ''}"
        return AssistanceEvent(
            event_id="aev_" + sha256(material.encode()).hexdigest()[:24],
            event_type=event_type,
            organization_id=request.facts.organization_id,
            assistance_id=request.assistance_id,
            request_revision=request.request_revision,
            reason=reason,
            occurred_at=self._d.clock.now(),
        )

    def _refusal(self, organization_id: str, code: str, key: ReceiptKey,
                 now: datetime) -> AssistanceEvent:
        material = f"refused|{code}|{_key_digest(key)}|{now.isoformat()}"
        return AssistanceEvent(
            event_id="aev_" + sha256(material.encode()).hexdigest()[:24],
            event_type="assistance.refused",
            organization_id=organization_id,
            assistance_id=None,
            request_revision=None,
            reason=code,
            occurred_at=now,
        )

    def _refusal_event(self, organization_id: str, code: str, command: SubmitCommand) -> None:
        key = ReceiptKey(organization_id, command.principal.principal_id, CREATE_CONTRACT,
                         command.canvas_id, command.idempotency_key or "")
        with self._d.repository.transaction() as tx:
            tx.add_event(self._refusal(organization_id, code, key, self._d.clock.now()))


# ---------------------------------------------------------------------- functions
def _actor_kind(principal: Principal) -> ActorKind:
    if principal.role is PrincipalRole.TEACHER:
        return ActorKind.TEACHER
    if principal.role is PrincipalRole.DEVICE:
        return ActorKind.DEVICE
    raise AssistanceError("FORBIDDEN_SCOPE")  # Admin has no CMD-32/33 role in A1


def _required_key(key: str | None) -> str:
    if not key or len(key) > 120:
        raise AssistanceError("MALFORMED_REQUEST")
    return key


def _key_digest(key: ReceiptKey) -> str:
    return sha256("|".join((key.organization_id, key.principal_id, key.contract_name,
                            key.target_id, key.idempotency_key)).encode()).hexdigest()[:16]


def _find(evidence: tuple[JobEvidence, ...] | None, job_id: str | None) -> JobEvidence | None:
    if evidence is None or job_id is None:
        return None
    return next((job for job in evidence if job.job_id == job_id), None)


def _outcome_matches(outcome: AnalysisOutcome, request: AssistanceRequest, job_id: str,
                     schedule: ScheduleIdentity | None) -> bool:
    source = request.facts.source
    pinned_revision = schedule.request_revision if schedule is not None else 1
    return (
        outcome.assistance_id == request.assistance_id
        and outcome.request_revision == pinned_revision
        and outcome.job_id == job_id
        and outcome.snapshot_ref == source.snapshot_ref
        and outcome.checkpoint_id == source.checkpoint_id
        and outcome.checkpoint_checksum == source.checkpoint_checksum
        and outcome.render_sha256 == source.render_sha256
        and outcome.context_revision == request.facts.context_revision
    )


def _notice_matches(notice: OwnerNotice, request: AssistanceRequest) -> bool:
    facts = request.facts
    if notice.kind is NoticeKind.CONSENT_REVOKED:
        return notice.participant_id in facts.audience
    if notice.kind is NoticeKind.SESSION_ENDED:
        return notice.session_id == facts.session_id
    if notice.kind is NoticeKind.TURN_REVOKED:
        return notice.participant_id == facts.contributor_participant_id and (
            notice.canvas_id in {None, facts.canvas_id}
        )
    return notice.canvas_id == facts.canvas_id


# ---------------------------------------------------------------------- projections
def teacher_view(request: AssistanceRequest) -> dict[str, object]:
    facts = request.facts
    target: dict[str, object] = (
        {"kind": "individual", "participant_id": facts.target.ref_id}
        if facts.target.kind is TargetKind.INDIVIDUAL
        else {"kind": "group", "group_id": facts.target.ref_id}
    )
    contributor = request.contributor
    cache = request.cache_hit_of
    return {
        "contract_name": "AssistanceRequestRecord",
        "contract_version": "0.1-candidate",
        "assistance_id": request.assistance_id,
        "request_revision": request.request_revision,
        "organization_id": facts.organization_id,
        "session_id": facts.session_id,
        "group_id": facts.group_id,
        "canvas_id": facts.canvas_id,
        "checkpoint_ref": request.checkpoint_ref.canonical(),
        "validated_target_scope": target,
        "target_region_id": facts.region_id,
        "requested_level": request.requested_level,
        "request_reason": str(request.request_reason),
        "requester_principal": {"principal_id": request.requester.principal_id,
                                "role": str(request.requester.kind)},
        "contributor_snapshot": {"participant_id": contributor.participant_id,
                                 "turn_id": contributor.turn_id,
                                 "turn_revision": contributor.turn_revision},
        "age_policy_ref": facts.age_policy_ref,
        "audience_age_context_refs": [
            {"participant_id": m.participant_id, "age_provenance_ref": m.age_provenance_ref,
             "age_revision": m.age_revision} for m in facts.members],
        "consent_revision_refs": [
            {"participant_id": m.participant_id, "consent_record_ref": m.consent_record_ref,
             "revision": m.consent_revision} for m in facts.members],
        "purpose_code": facts.purpose_code,
        "context_revision": facts.context_revision,
        "input_hash": facts.source.input_hash,
        "assistance_context_digest": request.assistance_context_digest,
        "policy_ref": {"policy_id": facts.policy_id, "version": facts.policy_version,
                       "status": "FIXTURE_ONLY_NOT_ADOPTED"},
        "status": str(request.status),
        "status_reason": None if request.status_reason is None else str(request.status_reason),
        "job_id": request.job_id,
        "budget_reservation": None if request.reservation_id is None else {
            "reservation_id": request.reservation_id, "state": str(request.reservation)},
        "cache_hit_of": None if cache is None else {
            "assistance_id": cache.assistance_id, "request_revision": cache.request_revision,
            "job_id": cache.job_id, "analysis_id": cache.analysis_id,
            "analysis_revision": cache.analysis_revision},
        "created_at": _utc(request.created_at),
        "updated_at": _utc(request.updated_at),
    }


def device_view(request: AssistanceRequest, poll_after_ms: int | None) -> dict[str, object]:
    status = request.device_status()
    return {
        "contract_name": "AssistanceRequestDeviceView",
        "contract_version": "0.1-candidate",
        "assistance_id": request.assistance_id,
        "request_revision": request.request_revision,
        "status": str(status),
        "job_id": request.job_id,
        "poll_after_ms": poll_after_ms if str(status) == "pending" else None,
    }


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


__all__ = [
    "DECISION_ROUNDS",
    "AssistanceDependencies",
    "AssistanceError",
    "AssistanceService",
    "CancelCommand",
    "CommandResult",
    "NoticeKind",
    "OwnerNotice",
    "SubmitCommand",
    "device_view",
    "teacher_view",
]
