"""BE2-02 C1 application: source-bound Vision observations, CMD-34 meaning corrections,
owner invalidation notices and the H-AI-REVIEW read projections (0.1-candidate).

Observation guard order: request/job lineage, (job, attempt) replay, source binding, admission,
input hash, current context/eligibility/age, provider context mode, one provider call, then a
lineage/eligibility/context/source re-check before anything is stored. Pre-provider refusals
call nothing; provider failures store nothing; a cancelled/superseded job or revoked consent
after the call discards the result; a moved context/source stores it ``stale``.

C2 typed context (``required_context_mode=typed_context``): the static provider capability,
then one coherent trusted snapshot verified member by member against the pin, source and the
existing context port, then the minimized projection and both digests are pinned before the
single call. The provider must echo the binding; after the call the current typed facts are
re-verified (any refusal discards the result) and a moved revision or context digest stores
the original ``stale`` with its original binding. Replay, current reads, downstream meaning
and new corrections compare the current typed digest too; accepted CMD-34 receipts still
replay as history after the current disclosure check.

CMD-34 guard order follows the SRS accepted-receipt rule: verified principal and permission to
disclose, then the immutable receipt (identical payload replays the original body even with an
old If-Match or a closed turn), and only an unseen mutation checks the bound turn, eligibility,
If-Match, current context and CAS before one atomic write of correction, receipt and
invalidation intent. Projections are plain JSON-ready mappings validated by the wire contracts.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import cast

from sketch2life.application.ports.ai_jobs import (
    ClockPort,
    IdGeneratorPort,
    Principal,
    PrincipalRole,
)
from sketch2life.application.ports.vision_analysis import (
    AdmissionPort,
    AnalysisAction,
    AnalysisAuthorityPort,
    AnalysisContextPort,
    AnalysisRepository,
    AnalysisRevisionConflict,
    AnalysisSourcePort,
    AnalysisStorageUnavailable,
    AnalysisUniqueConflict,
    AssistanceRequestPort,
    AuthorityReason,
    ContextDecision,
    CorrectionReceipt,
    CorrectionScopeKey,
    JobLineagePort,
    ObservationFailed,
    ObservationFailureCode,
    ObservationRequest,
    VisionContextSourcePort,
    VisionObservationPort,
)
from sketch2life.domain.ai_jobs.completion import canonical_sha256
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.domain.vision_analysis import (
    ANALYSIS_CONTRACT_VERSION,
    OWNER_INVALIDATION_REASONS,
    AcceptedStatus,
    ActorRef,
    ActorRole,
    AnalysisHead,
    AnalysisLineage,
    AnalysisRuleViolation,
    AnalysisScope,
    AssistancePin,
    CorrectionKind,
    InvalidationIntent,
    InvalidationReason,
    LineageVerdict,
    MeaningCorrection,
    ObjectCandidate,
    ObservationClaim,
    ObservedLabel,
    ProviderContextMode,
    ProviderResultRecord,
    SourceSnapshot,
    SourceVerdict,
    VisionObservation,
    analysis_etag,
    apply_correction,
    check_input_hash,
    check_lineage,
    derive_uncertainty,
    document_sha256,
    invalidation_event_id,
    is_applicable,
    mark_stale,
    new_head,
    new_observation,
    normalize_intended_objects,
    normalize_long_text,
    normalize_short_text,
    object_candidates,
    observation_bounds_violation,
    parse_analysis_etag,
    provider_result_ref,
    verify_source,
)
from sketch2life.domain.vision_context import (
    C2_CONTEXT_CAPABILITY,
    AgeBandPolicy,
    ContextCode,
    ContextPortFacts,
    ContextRuleViolation,
    ProviderTypedContext,
    pin_context,
    verify_context_snapshot,
)

CORRECTION_CONTRACT = "AnalysisCorrection"
TYPED_RECORD_VERSION = "0.2-candidate"
# Bounded write rounds: the first attempt plus one re-read after a same-key unique conflict.
WRITE_ROUNDS = 2
_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")

_ERRORS: Mapping[str, tuple[int, str]] = {
    "MALFORMED_REQUEST": (400, "Idempotency-Key is required."),
    "RESOURCE_NOT_FOUND": (404, "Resource not found."),
    "GRANT_REVOKED": (403, "Access to this resource was withdrawn."),
    "FORBIDDEN_SCOPE": (403, "Not permitted for this scope."),
    "CONSENT_REQUIRED": (403, "This action is not permitted for this child."),
    "TURN_CLOSED": (409, "This drawing turn is not open."),
    "INVALID_STATE": (409, "The session is not active."),
    "IDEMPOTENCY_PAYLOAD_MISMATCH": (409, "This key was already used with a different request."),
    "IDEMPOTENCY_CONFLICT": (409, "A concurrent request is still settling."),
    "STALE_CONTEXT": (409, "The drawing or its context changed; reload it."),
    "PRECONDITION_REQUIRED": (428, "If-Match is required."),
    "STALE_AGGREGATE": (412, "The analysis has changed; reload it."),
    "FIELD_NOT_ALLOWED": (422, "A field is not allowed for this sender."),
    "FIELD_VALIDATION_FAILED": (422, "A field is invalid."),
    "AGE_NOT_SUPPORTED": (422, "The age context is not supported."),
    "DEPENDENCY_UNAVAILABLE": (503, "Please try again shortly."),
}


class VisionAnalysisError(Exception):
    """Typed, safe application error; never carries provider output or another child's data."""

    def __init__(self, code: str, *, current_revision: int | None = None) -> None:
        super().__init__(code)
        status, message = _ERRORS[code]
        self.code = code
        self.http_status = status
        self.public_message = message
        self.retryable = code in {"DEPENDENCY_UNAVAILABLE", "IDEMPOTENCY_CONFLICT"}
        self.current_revision = current_revision


class ObservationDisposition(StrEnum):
    ACCEPTED = "accepted"
    STALE = "stale"
    REFUSED = "refused"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ObservationResult:
    """Only ``accepted`` is authoritative. ``code`` is a closed token for the worker."""

    disposition: ObservationDisposition
    code: str | None
    provider_invoked: bool
    analysis_id: str | None = None
    analysis_revision: int | None = None
    replayed: bool = False

    @property
    def authoritative(self) -> bool:
        return self.disposition is ObservationDisposition.ACCEPTED


@dataclass(frozen=True, slots=True)
class CorrectionCommand:
    """CMD-34 input after transport parsing. Actor/role/org come only from ``principal``."""

    principal: Principal
    analysis_id: str
    idempotency_key: str | None
    if_match: str | None
    intended_objects: tuple[str, ...]
    correction_reason: str
    expected_context_revision: int
    child_explanation: str | None = None
    basis_correction_ref: str | None = None


@dataclass(frozen=True, slots=True)
class _Payload:
    intended_objects: tuple[str, ...]
    child_explanation: str | None
    correction_reason: str
    expected_context_revision: int
    basis_correction_ref: str | None


@dataclass(frozen=True, slots=True)
class CorrectionResult:
    receipt: CorrectionReceipt
    head: AnalysisHead
    correction: MeaningCorrection
    candidates: tuple[ObjectCandidate, ...]
    replayed: bool

    @property
    def role(self) -> ActorRole:
        return self.receipt.author_role

    @property
    def etag(self) -> str:
        return analysis_etag(self.receipt.analysis_id, self.receipt.analysis_revision_after)


@dataclass(frozen=True, slots=True)
class InvalidationNotice:
    """Owner notice (BE1/BE2-03): source/context/intent changed or consent was revoked."""

    notice_id: str
    organization_id: str
    analysis_id: str
    reason: InvalidationReason


class MeaningState(StrEnum):
    CONFIRMED = "confirmed"
    UNCONFIRMED = "unconfirmed"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class DownstreamMeaning:
    """What a consumer may use: confirmed concepts only when confirmed and still applicable.
    Model candidates are always labelled as candidates, never as the child's meaning."""

    analysis_id: str
    analysis_revision: int
    state: MeaningState
    confirmed_concepts: tuple[str, ...]
    confirmation_ref: str | None
    model_candidates: tuple[ObjectCandidate, ...]
    child_proposal_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VisionAnalysisDependencies:
    repository: AnalysisRepository
    authority: AnalysisAuthorityPort
    context: AnalysisContextPort
    sources: AnalysisSourcePort
    admission: AdmissionPort
    requests: AssistanceRequestPort
    jobs: JobLineagePort
    provider: VisionObservationPort
    clock: ClockPort
    ids: IdGeneratorPort
    required_context_mode: ProviderContextMode = ProviderContextMode.IMAGE_ONLY
    # C2 typed context: trusted owner snapshot port and the injected age-band policy. Both are
    # required for typed_context mode; their absence refuses before any call.
    context_sources: VisionContextSourcePort | None = None
    age_band_policy: AgeBandPolicy | None = None


def eligibility_code(context: ContextDecision, scope: AnalysisScope) -> str | None:
    """Purpose/consent/session/age gate. Ages are authoritative 36–155 completed months for
    every audience participant; an unknown or out-of-range age fails closed. Duplicate
    participants (audience or age facts) are refused before any dict/set conversion (C2)."""

    if not context.consent_effective or not context.purpose_granted:
        return "CONSENT_REQUIRED"
    if not context.session_active:
        return "INVALID_STATE"
    reported = [participant for participant, _ in context.audience_age_months]
    audience = list(scope.audience_participant_ids)
    if len(reported) != len(set(reported)) or len(audience) != len(set(audience)):
        return "AGE_NOT_SUPPORTED"
    ages = dict(context.audience_age_months)
    if set(ages) != set(scope.audience_participant_ids):
        return "AGE_NOT_SUPPORTED"
    for months in ages.values():
        if months is None:
            return "AGE_NOT_SUPPORTED"
        try:
            validate_age_months(months)
        except CoreRuleViolation:
            return "AGE_NOT_SUPPORTED"
    return None


class VisionAnalysisService:
    def __init__(self, deps: VisionAnalysisDependencies) -> None:
        self._d = deps

    # ------------------------------------------------------------- observation
    def record_observation(
        self, claim: ObservationClaim, *, correlation_id: str
    ) -> ObservationResult:
        pin = self._d.requests.get(claim.assistance_id)
        job = self._d.jobs.get(claim.job_id)
        verdict = check_lineage(claim, pin, job)
        if verdict is not LineageVerdict.PROCEED or pin is None or job is None:
            return ObservationResult(ObservationDisposition.REJECTED, str(verdict), False)
        scope = pin.scope
        with self._d.repository.transaction() as tx:
            existing = tx.find_by_attempt(claim.job_id, claim.job_attempt_id)
            head = tx.get_head(existing) if existing is not None else None
        if head is not None:
            return self._observation_replay(head)

        snapshot = self._d.sources.resolve(
            claim.input_snapshot_ref, organization_id=scope.organization_id
        )
        admission = (
            None
            if snapshot is None
            else self._d.admission.receipt_for(
                snapshot.render.render_ref,
                snapshot.render.render_sha256,
                organization_id=scope.organization_id,
            )
        )
        source = verify_source(
            snapshot, admission, organization_id=scope.organization_id, canvas_id=scope.canvas_id
        )
        if source is not SourceVerdict.PROCEED or snapshot is None or admission is None:
            return ObservationResult(ObservationDisposition.REFUSED, str(source), False)
        if check_input_hash(job, snapshot) is not LineageVerdict.PROCEED:
            return ObservationResult(
                ObservationDisposition.REJECTED, str(LineageVerdict.INPUT_MISMATCH), False
            )
        context = self._d.context.current(scope)
        gate = eligibility_code(context, scope)
        if gate is None and context.context_revision != claim.context_revision:
            gate = "STALE_CONTEXT"
        if gate is not None:
            return ObservationResult(ObservationDisposition.REFUSED, gate, False)
        mode = self._d.required_context_mode
        unsupported = ObservationResult(
            ObservationDisposition.REFUSED,
            str(ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED),
            False,
        )
        if mode not in self._d.provider.supported_context_modes:
            return unsupported
        typed: ProviderTypedContext | None = None
        if mode is ProviderContextMode.TYPED_CONTEXT:
            # Static reviewed capability first: no snapshot, image load or call otherwise.
            if self._d.provider.context_capability != C2_CONTEXT_CAPABILITY:
                return unsupported
            typed, refusal = self._typed_current(
                pin, snapshot, context, expected_revision=pin.context_revision
            )
            if typed is None:
                return ObservationResult(ObservationDisposition.REFUSED, refusal, False)
        outcome = self._d.provider.observe(
            ObservationRequest(
                correlation_id=correlation_id,
                organization_id=scope.organization_id,
                render=snapshot.render,
                admission=admission,
                context_mode=mode,
                typed_context=typed,
            )
        )
        if isinstance(outcome, ObservationFailed):
            return ObservationResult(
                ObservationDisposition.FAILED, str(outcome.code), outcome.provider_invoked
            )
        # Any provider (bridge or fake) must return output the contracts can project and a
        # retained full-result document whose hash is the reported evidence hash (C1-R04/R06).
        if (
            outcome.evidence.provider_context_mode is not mode
            or outcome.evidence.context_binding != (None if typed is None else typed.binding)
            or observation_bounds_violation(outcome.observation) is not None
            or document_sha256(outcome.result_document) != outcome.evidence.result_sha256
        ):
            return ObservationResult(
                ObservationDisposition.FAILED, str(ObservationFailureCode.OUTPUT_MALFORMED), True
            )

        # Re-check everything that may have moved while the provider ran.
        after = check_lineage(
            claim, self._d.requests.get(claim.assistance_id), self._d.jobs.get(claim.job_id)
        )
        if after is not LineageVerdict.PROCEED:
            return ObservationResult(ObservationDisposition.REJECTED, str(after), True)
        context_after = self._d.context.current(scope)
        # The complete current gate (consent, purpose, session, every audience age) — C1-R02.
        gate_after = eligibility_code(context_after, scope)
        if gate_after is not None:
            return ObservationResult(ObservationDisposition.REJECTED, gate_after, True)
        typed_after: ProviderTypedContext | None = None
        if typed is not None:
            # Current per-member typed facts (transfer/field-use/consent/age) — C2. Any refusal
            # now means the output may not be kept: discard, store nothing.
            typed_after, refusal_after = self._typed_current(
                pin, snapshot, context_after, expected_revision=None
            )
            if typed_after is None:
                return ObservationResult(ObservationDisposition.REJECTED, refusal_after, True)
        stale_reason: InvalidationReason | None = None
        if context_after.context_revision != claim.context_revision:
            stale_reason = InvalidationReason.CONTEXT_CHANGED
        elif typed is not None and typed_after is not None and (
            typed_after.binding.context_digest != typed.binding.context_digest
        ):
            # Same revision, different facts: never rebind the output to the new context.
            stale_reason = InvalidationReason.CONTEXT_CHANGED
        else:
            current = self._d.sources.resolve(
                claim.input_snapshot_ref, organization_id=scope.organization_id
            )
            if current is None or current.input_hash() != snapshot.input_hash():
                stale_reason = InvalidationReason.SOURCE_CHANGED

        now = self._d.clock.now()
        analysis_id = self._d.ids.new_id("ana")
        observation = new_observation(
            analysis_id=analysis_id,
            organization_id=scope.organization_id,
            observation=outcome.observation,
            evidence=outcome.evidence,
            moderation=outcome.moderation,
            now=now,
        )
        created = new_head(
            analysis_id=analysis_id,
            scope=scope,
            lineage=AnalysisLineage(
                assistance_id=pin.assistance_id,
                request_revision=pin.request_revision,
                job_id=claim.job_id,
                job_attempt_id=claim.job_attempt_id,
                input_hash=job.input_hash,
            ),
            source=snapshot,
            admission=admission,
            context_revision=claim.context_revision,
            observation_sha256=observation.observation_sha256,
            stale_reason=stale_reason,
            now=now,
            typed_binding=None if typed is None else typed.binding,
        )
        result_record = ProviderResultRecord(
            result_ref=provider_result_ref(analysis_id),
            analysis_id=analysis_id,
            organization_id=scope.organization_id,
            result_contract=outcome.evidence.result_contract,
            canonical_json=outcome.result_document,
            result_sha256=outcome.evidence.result_sha256,
        )
        try:
            with self._d.repository.transaction() as tx:
                raced = tx.find_by_attempt(claim.job_id, claim.job_attempt_id)
                if raced is not None:
                    winner = tx.get_head(raced)
                else:
                    # One unit: the full result, observation and head commit together, so a
                    # failed write never leaves a published but unresolvable result ref.
                    tx.insert_provider_result(result_record)
                    tx.insert_observation(observation)
                    tx.insert_head(created)
                    winner = None
        except AnalysisStorageUnavailable:
            raise VisionAnalysisError("DEPENDENCY_UNAVAILABLE") from None
        if winner is not None:
            return self._observation_replay(winner, provider_invoked=True)
        disposition = (
            ObservationDisposition.STALE if stale_reason else ObservationDisposition.ACCEPTED
        )
        return ObservationResult(
            disposition,
            None if stale_reason is None else str(stale_reason),
            True,
            analysis_id=analysis_id,
            analysis_revision=created.analysis_revision,
        )

    def _observation_replay(
        self, head: AnalysisHead, *, provider_invoked: bool = False
    ) -> ObservationResult:
        """Same analysis identity, no new provider call or mutation, but authority is judged
        against the current gate, context and source, never the stored status alone (C1-R01)."""

        context = self._d.context.current(head.scope)
        gate = eligibility_code(context, head.scope)
        typed_refusal, typed_moved = None, False
        if gate is None and head.typed_binding is not None:
            typed_refusal, typed_moved = self._typed_status(head, context)
        disposition, code = ObservationDisposition.ACCEPTED, None
        if gate is not None:
            disposition, code = ObservationDisposition.REJECTED, gate
        elif typed_refusal is not None:
            disposition, code = ObservationDisposition.REJECTED, typed_refusal
        elif head.accepted_status is AcceptedStatus.STALE:
            disposition, code = ObservationDisposition.STALE, head.status_reason
        elif context.context_revision != head.context_revision or typed_moved:
            disposition = ObservationDisposition.STALE
            code = str(InvalidationReason.CONTEXT_CHANGED)
        elif not self._applicable(head, context):
            disposition = ObservationDisposition.STALE
            code = str(InvalidationReason.SOURCE_CHANGED)
        return ObservationResult(
            disposition,
            code,
            provider_invoked,
            analysis_id=head.analysis_id,
            analysis_revision=head.analysis_revision,
            replayed=True,
        )

    # -------------------------------------------------------------- CMD-34
    def submit_correction(self, command: CorrectionCommand) -> CorrectionResult:
        principal = command.principal
        if not command.idempotency_key or not _KEY.match(command.idempotency_key):
            raise VisionAnalysisError("MALFORMED_REQUEST")
        payload = _normalise(command)
        fingerprint = canonical_sha256(
            {
                "contract_name": CORRECTION_CONTRACT,
                "analysis_id": command.analysis_id,
                "intended_objects": list(payload.intended_objects),
                "child_explanation": payload.child_explanation,
                "correction_reason": payload.correction_reason,
                "expected_context_revision": payload.expected_context_revision,
                "basis_correction_ref": payload.basis_correction_ref,
            }
        )
        key = CorrectionScopeKey(
            principal.organization_id,
            principal.principal_id,
            CORRECTION_CONTRACT,
            command.analysis_id,
            command.idempotency_key,
        )
        for _ in range(WRITE_ROUNDS):
            with self._d.repository.transaction() as tx:
                head = tx.get_head(command.analysis_id)
                observation = tx.get_observation(command.analysis_id)
                receipt = tx.get_receipt(key)
            if (
                head is None
                or observation is None
                or head.organization_id != principal.organization_id
            ):
                raise VisionAnalysisError("RESOURCE_NOT_FOUND")
            context = self._d.context.current(head.scope)
            self._require_disclosure(principal, head.scope, context)
            if receipt is not None:
                return self._replay(receipt, fingerprint, head, observation)

            actor = self._require_action(principal, head.scope)
            _require_field_rules(actor, payload)
            gate = eligibility_code(context, head.scope)
            if gate is not None:
                raise VisionAnalysisError(gate)
            expected = self._require_if_match(command.if_match, head)
            if (
                payload.expected_context_revision != context.context_revision
                or not self._applicable(head, context)
            ):
                raise VisionAnalysisError("STALE_CONTEXT")
            self._require_basis(head, payload.basis_correction_ref)

            now = self._d.clock.now()
            teacher = actor.role is ActorRole.TEACHER
            try:
                correction = MeaningCorrection(
                    correction_id=self._d.ids.new_id("cor"),
                    analysis_id=head.analysis_id,
                    correction_version=head.analysis_revision + 1,
                    kind=(CorrectionKind.TEACHER_CONFIRMATION if teacher
                          else CorrectionKind.CHILD_PROPOSAL),
                    author=actor,
                    intended_objects=payload.intended_objects,
                    child_explanation=payload.child_explanation,
                    correction_reason=payload.correction_reason,
                    expected_context_revision=payload.expected_context_revision,
                    basis_correction_ref=payload.basis_correction_ref,
                    recorded_at=now,
                )
                updated = apply_correction(head, correction, now)
            except AnalysisRuleViolation:
                raise VisionAnalysisError("FIELD_VALIDATION_FAILED") from None
            reason = (InvalidationReason.TEACHER_MEANING_CONFIRMED if teacher
                      else InvalidationReason.CHILD_INTENT_PROPOSED)
            intent = InvalidationIntent(
                event_id=invalidation_event_id(
                    head.analysis_id, updated.analysis_revision, str(reason)
                ),
                organization_id=head.organization_id,
                analysis_id=head.analysis_id,
                previous_revision=head.analysis_revision,
                analysis_revision=updated.analysis_revision,
                reason=reason,
                correction_ref=correction.correction_id,
                occurred_at=now,
            )
            new_receipt = CorrectionReceipt(
                scope_key=key,
                fingerprint=fingerprint,
                analysis_id=head.analysis_id,
                correction_id=correction.correction_id,
                previous_revision=head.analysis_revision,
                analysis_revision_after=updated.analysis_revision,
                current_meaning_ref_after=updated.current_meaning_ref,
                invalidation_event_id=intent.event_id,
                invalidation_reason=reason,
                author_role=actor.role,
            )
            try:
                with self._d.repository.transaction() as tx:
                    if tx.get_receipt(key) is not None:
                        raise AnalysisUniqueConflict("correction_receipt")
                    tx.cas_head(expected_revision=expected, head=updated)
                    tx.append_correction(correction)
                    tx.put_receipt(new_receipt)
                    tx.add_invalidation(intent)
            except AnalysisRevisionConflict:
                raise VisionAnalysisError(
                    "STALE_AGGREGATE", current_revision=self._current_revision(head.analysis_id)
                ) from None
            except AnalysisUniqueConflict:
                continue
            except AnalysisStorageUnavailable:
                raise VisionAnalysisError("DEPENDENCY_UNAVAILABLE") from None
            return CorrectionResult(
                new_receipt, updated, correction, object_candidates(observation.observation),
                replayed=False,
            )
        raise VisionAnalysisError("IDEMPOTENCY_CONFLICT")

    def _replay(
        self,
        receipt: CorrectionReceipt,
        fingerprint: str,
        head: AnalysisHead,
        observation: VisionObservation,
    ) -> CorrectionResult:
        if receipt.fingerprint != fingerprint:
            raise VisionAnalysisError("IDEMPOTENCY_PAYLOAD_MISMATCH")
        with self._d.repository.transaction() as tx:
            correction = tx.get_correction(receipt.correction_id)
        if correction is None:  # pragma: no cover - receipt and correction commit together
            raise VisionAnalysisError("DEPENDENCY_UNAVAILABLE")
        return CorrectionResult(
            receipt, head, correction, object_candidates(observation.observation), replayed=True
        )

    def _require_disclosure(
        self, principal: Principal, scope: AnalysisScope, context: ContextDecision
    ) -> None:
        decision = self._d.authority.decide(principal, AnalysisAction.READ_ANALYSIS, scope)
        if not decision.allowed:
            if decision.reason is AuthorityReason.GRANT_REVOKED:
                raise VisionAnalysisError("GRANT_REVOKED")
            raise VisionAnalysisError("RESOURCE_NOT_FOUND")
        if not context.consent_effective:
            raise VisionAnalysisError("CONSENT_REQUIRED")

    def _require_action(self, principal: Principal, scope: AnalysisScope) -> ActorRef:
        """The action follows the verified principal role; the body cannot choose it."""

        if principal.role is PrincipalRole.TEACHER:
            action, role = AnalysisAction.CONFIRM_MEANING, ActorRole.TEACHER
        elif principal.role is PrincipalRole.DEVICE:
            action, role = AnalysisAction.PROPOSE_INTENT, ActorRole.CHILD_DEVICE
        else:
            raise VisionAnalysisError("FORBIDDEN_SCOPE")
        decision = self._d.authority.decide(principal, action, scope)
        actor = decision.actor
        if decision.allowed and actor is not None:
            if actor.principal_id != principal.principal_id or actor.role is not role:
                raise VisionAnalysisError("FORBIDDEN_SCOPE")
            return actor
        if decision.reason is AuthorityReason.GRANT_REVOKED:
            raise VisionAnalysisError("GRANT_REVOKED")
        if decision.reason is AuthorityReason.TURN_CLOSED:
            raise VisionAnalysisError("TURN_CLOSED")
        raise VisionAnalysisError("FORBIDDEN_SCOPE")

    def _require_if_match(self, header: str | None, head: AnalysisHead) -> int:
        if header is None or not header.strip():
            raise VisionAnalysisError("PRECONDITION_REQUIRED")
        revision = parse_analysis_etag(header, head.analysis_id)
        if revision is None or revision != head.analysis_revision:
            raise VisionAnalysisError("STALE_AGGREGATE", current_revision=head.analysis_revision)
        return revision

    def _require_basis(self, head: AnalysisHead, basis_ref: str | None) -> None:
        if basis_ref is None:
            return
        with self._d.repository.transaction() as tx:
            basis = tx.get_correction(basis_ref)
        if (
            basis is None
            or basis.analysis_id != head.analysis_id
            or basis.kind is not CorrectionKind.CHILD_PROPOSAL
        ):
            raise VisionAnalysisError("FIELD_VALIDATION_FAILED")

    def _applicable(self, head: AnalysisHead, context: ContextDecision) -> bool:
        current = self._d.sources.resolve(
            head.source.snapshot_ref, organization_id=head.organization_id
        )
        if not is_applicable(
            head,
            current_context_revision=context.context_revision,
            current_input_hash=None if current is None else current.input_hash(),
        ):
            return False
        if head.typed_binding is None:
            return True
        # C2: same-revision digest movement or a refused current typed context also ends
        # applicability; the stored binding is never rebound to the new facts.
        refusal, moved = self._typed_status(head, context)
        return refusal is None and not moved

    # ------------------------------------------------------------- typed context
    def _typed_current(
        self,
        pin: AssistancePin,
        source: SourceSnapshot,
        context: ContextDecision,
        *,
        expected_revision: int | None,
    ) -> tuple[ProviderTypedContext | None, str]:
        """The verified, pinned current typed context, or a closed refusal token."""

        port, policy = self._d.context_sources, self._d.age_band_policy
        if port is None or policy is None:
            return None, str(ContextCode.CONTEXT_UNAVAILABLE)
        try:
            snapshot = port.resolve(pin, source)
            if snapshot is None:
                return None, str(ContextCode.CONTEXT_UNAVAILABLE)
            refusal = verify_context_snapshot(
                snapshot,
                pin=pin,
                source=source,
                policy=policy,
                port=ContextPortFacts(
                    context_revision=context.context_revision,
                    consent_effective=context.consent_effective,
                    purpose_granted=context.purpose_granted,
                    session_active=context.session_active,
                    audience_age_months=context.audience_age_months,
                ),
                expected_context_revision=expected_revision,
            )
            if refusal is not None:
                return None, str(refusal)
            return pin_context(snapshot, policy), ""
        except ContextRuleViolation:
            return None, str(ContextCode.CONTEXT_MALFORMED)

    def _typed_status(
        self, head: AnalysisHead, context: ContextDecision
    ) -> tuple[str | None, bool]:
        """(refusal token, digest moved) of the current typed facts against the pin."""

        binding = head.typed_binding
        assert binding is not None
        pin = AssistancePin(
            assistance_id=head.lineage.assistance_id,
            request_revision=head.lineage.request_revision,
            input_snapshot_ref=head.source.snapshot_ref,
            context_revision=head.context_revision,
            scope=head.scope,
        )
        current, refusal = self._typed_current(pin, head.source, context, expected_revision=None)
        if current is None:
            return refusal, True
        return None, current.binding.context_digest != binding.context_digest

    def _current_revision(self, analysis_id: str) -> int | None:
        with self._d.repository.transaction() as tx:
            head = tx.get_head(analysis_id)
        return None if head is None else head.analysis_revision

    # ----------------------------------------------------------- owner notice
    def apply_invalidation(self, notice: InvalidationNotice) -> InvalidationIntent | None:
        """Idempotent by ``notice_id``. Marks an accepted analysis stale and writes a versioned
        invalidation intent in the same transaction; history and corrections are kept."""

        if notice.reason not in OWNER_INVALIDATION_REASONS:
            raise VisionAnalysisError("FIELD_VALIDATION_FAILED")
        now = self._d.clock.now()
        try:
            with self._d.repository.transaction() as tx:
                if tx.notice_seen(notice.notice_id):
                    return None
                head = tx.get_head(notice.analysis_id)
                if head is None or head.organization_id != notice.organization_id:
                    raise VisionAnalysisError("RESOURCE_NOT_FOUND")
                tx.record_notice(notice.notice_id)
                if head.accepted_status is AcceptedStatus.STALE:
                    return None
                updated = mark_stale(head, notice.reason, now)
                tx.cas_head(expected_revision=head.analysis_revision, head=updated)
                intent = InvalidationIntent(
                    event_id=invalidation_event_id(
                        head.analysis_id, updated.analysis_revision, str(notice.reason)
                    ),
                    organization_id=head.organization_id,
                    analysis_id=head.analysis_id,
                    previous_revision=head.analysis_revision,
                    analysis_revision=updated.analysis_revision,
                    reason=notice.reason,
                    correction_ref=None,
                    occurred_at=now,
                )
                tx.add_invalidation(intent)
        except AnalysisStorageUnavailable:
            raise VisionAnalysisError("DEPENDENCY_UNAVAILABLE") from None
        return intent

    # ------------------------------------------------------------ H-AI-REVIEW
    def downstream_meaning(self, principal: Principal, analysis_id: str) -> DownstreamMeaning:
        head, observation, corrections = self._teacher_read(principal, analysis_id)
        context = self._d.context.current(head.scope)
        applicable = self._applicable(head, context) and eligibility_code(
            context, head.scope
        ) is None
        proposals = tuple(c.correction_id for c in corrections
                          if c.kind is CorrectionKind.CHILD_PROPOSAL)
        candidates = object_candidates(observation.observation)
        confirmation = next(
            (c for c in corrections if c.correction_id == head.current_meaning_ref), None
        )
        concepts: tuple[str, ...] = ()
        ref: str | None = None
        if not applicable:
            state = MeaningState.NOT_APPLICABLE
        elif confirmation is None:
            state = MeaningState.UNCONFIRMED
        else:
            state = MeaningState.CONFIRMED
            concepts, ref = confirmation.intended_objects, confirmation.correction_id
        return DownstreamMeaning(
            head.analysis_id, head.analysis_revision, state, concepts, ref, candidates, proposals
        )

    def analysis_record(self, principal: Principal, analysis_id: str) -> Mapping[str, object]:
        head, observation, corrections = self._teacher_read(principal, analysis_id)
        return analysis_record_view(head, observation, corrections)

    def resolve_provider_result(
        self, principal: Principal, result_ref: str
    ) -> ProviderResultRecord:
        """Trusted internal resolver for the ``provider_result`` evidence ref (C1-R06).

        Teacher/H-AI-REVIEW read only, under the same disclosure check as the record; the raw
        result is never part of a Child projection or a public route. The retained content is
        re-verified against the analysis evidence hash before it is returned."""

        with self._d.repository.transaction() as tx:
            record = tx.get_provider_result(result_ref)
        if record is None or record.organization_id != principal.organization_id:
            raise VisionAnalysisError("RESOURCE_NOT_FOUND")
        _, observation, _ = self._teacher_read(principal, record.analysis_id)
        if (
            document_sha256(record.canonical_json) != record.result_sha256
            or record.result_sha256 != observation.evidence.result_sha256
        ):  # pragma: no cover - immutable record; integrity guard for real storage
            raise VisionAnalysisError("DEPENDENCY_UNAVAILABLE")
        return record

    def _teacher_read(
        self, principal: Principal, analysis_id: str
    ) -> tuple[AnalysisHead, VisionObservation, tuple[MeaningCorrection, ...]]:
        with self._d.repository.transaction() as tx:
            head = tx.get_head(analysis_id)
            observation = tx.get_observation(analysis_id)
            corrections = tx.list_corrections(analysis_id)
        if head is None or observation is None or head.organization_id != (
            principal.organization_id
        ):
            raise VisionAnalysisError("RESOURCE_NOT_FOUND")
        self._require_disclosure(principal, head.scope, self._d.context.current(head.scope))
        if principal.role is not PrincipalRole.TEACHER:
            raise VisionAnalysisError("FORBIDDEN_SCOPE")
        return head, observation, corrections


def _normalise(command: CorrectionCommand) -> _Payload:
    try:
        explanation = command.child_explanation
        return _Payload(
            intended_objects=normalize_intended_objects(command.intended_objects),
            child_explanation=None if explanation is None else normalize_long_text(explanation),
            correction_reason=normalize_short_text(command.correction_reason),
            expected_context_revision=_revision(command.expected_context_revision),
            basis_correction_ref=command.basis_correction_ref,
        )
    except AnalysisRuleViolation:
        raise VisionAnalysisError("FIELD_VALIDATION_FAILED") from None


def _revision(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AnalysisRuleViolation("expected_context_revision must be an integer >= 0")
    return value


def _require_field_rules(actor: ActorRef, payload: _Payload) -> None:
    if actor.role is ActorRole.CHILD_DEVICE and payload.basis_correction_ref is not None:
        raise VisionAnalysisError("FIELD_NOT_ALLOWED")
    if actor.role is ActorRole.TEACHER and payload.child_explanation is not None:
        raise VisionAnalysisError("FIELD_NOT_ALLOWED")


# ---------------------------------------------------------------------- projections
def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _candidates(candidates: tuple[ObjectCandidate, ...]) -> list[dict[str, object]]:
    return [
        {"label": c.label, "confidence": c.confidence, "observation_ref": c.observation_ref}
        for c in candidates
    ]


def correction_record_view(correction: MeaningCorrection) -> dict[str, object]:
    author = correction.author
    return {
        "correction_id": correction.correction_id,
        "correction_version": correction.correction_version,
        "kind": str(correction.kind),
        "meaning_status": str(correction.meaning_status),
        "meaning_kind": "intended_concept",
        "author": {
            "principal_ref": author.principal_id,
            "role": str(author.role),
            "participant_id": author.participant_id,
            "turn_id": author.turn_id,
        },
        "intended_objects": list(correction.intended_objects),
        "child_explanation": correction.child_explanation,
        "correction_reason": correction.correction_reason,
        "expected_context_revision": correction.expected_context_revision,
        "basis_correction_ref": correction.basis_correction_ref,
        "recorded_at": _iso(correction.recorded_at),
    }


def teacher_correction_view(result: CorrectionResult) -> dict[str, object]:
    head, receipt = result.head, result.receipt
    return {
        "analysis_id": receipt.analysis_id,
        "analysis_revision": receipt.analysis_revision_after,
        "original": {
            "analysis_id": head.analysis_id,
            "observation_sha256": head.observation_sha256,
            # Corrections are only accepted on an accepted analysis; a replay returns the
            # original body, so this is the status at commit time.
            "accepted_status": str(AcceptedStatus.ACCEPTED),
            "input_snapshot_ref": head.source.snapshot_ref,
            "context_revision": head.context_revision,
            "job_id": head.lineage.job_id,
            "job_attempt_id": head.lineage.job_attempt_id,
        },
        "object_candidates": _candidates(result.candidates),
        "correction": correction_record_view(result.correction),
        "current_meaning_ref": receipt.current_meaning_ref_after,
        "invalidation": {
            "event_id": receipt.invalidation_event_id,
            "previous_revision": receipt.previous_revision,
            "analysis_revision": receipt.analysis_revision_after,
            "reason": str(receipt.invalidation_reason),
        },
    }


def child_correction_view(result: CorrectionResult) -> dict[str, object]:
    """Refs/status only: no model labels, confidence, uncertainty, evidence or Teacher text."""

    correction = result.correction
    return {
        "analysis_id": result.receipt.analysis_id,
        "analysis_revision": result.receipt.analysis_revision_after,
        "correction_id": correction.correction_id,
        "correction_version": correction.correction_version,
        "kind": str(correction.kind),
        "meaning_status": str(correction.meaning_status),
        "recorded_at": _iso(correction.recorded_at),
    }


def worker_candidate_view(head: AnalysisHead, observation: VisionObservation) -> dict[str, object]:
    """DATA-22 worker candidate projection of a stored analysis (exact source field set).

    image_only records keep the exact 0.1-candidate shape; a typed-context record is the
    sibling 0.2-candidate shape whose provenance carries the pinned binding copy (C2)."""

    view = _worker_candidate_v1(head, observation)
    binding = observation.evidence.context_binding
    if binding is not None:
        provenance = {**cast("dict[str, object]", view["provenance"])}
        provenance["context_binding"] = binding.canonical()
        view["contract_version"] = TYPED_RECORD_VERSION
        view["provenance"] = provenance
    return view


def _worker_candidate_v1(head: AnalysisHead, observation: VisionObservation) -> dict[str, object]:
    evidence, moderation = observation.evidence, observation.moderation
    uncertainty = derive_uncertainty(observation.observation)
    checkpoint, render = head.source.checkpoint, head.source.render
    return {
        "assistance_id": head.lineage.assistance_id,
        "expected_request_revision": head.lineage.request_revision,
        "input_snapshot_ref": head.source.snapshot_ref,
        "context_revision": head.context_revision,
        "job_id": head.lineage.job_id,
        "job_attempt_id": head.lineage.job_attempt_id,
        "contract_version": ANALYSIS_CONTRACT_VERSION,
        "object_candidates": _candidates(object_candidates(observation.observation)),
        "uncertainty": {
            "calibration": uncertainty.calibration,
            "unknown_confidence_refs": list(uncertainty.unknown_confidence_refs),
            "ambiguous_region_refs": list(uncertainty.ambiguous_region_refs),
            "requires_meaning_confirmation": uncertainty.requires_meaning_confirmation,
        },
        "evidence_refs": [
            {"kind": "vision_observation", "ref": head.analysis_id,
             "sha256": observation.observation_sha256},
            {"kind": "provider_result", "ref": f"result:{head.analysis_id}",
             "sha256": evidence.result_sha256},
            {"kind": "source_checkpoint", "ref": checkpoint.checkpoint_id,
             "sha256": checkpoint.checksum_sha256},
            {"kind": "source_render", "ref": render.render_ref, "sha256": render.render_sha256},
            {"kind": "admission_receipt", "ref": head.admission.receipt_id,
             "sha256": head.admission.receipt_sha256},
        ],
        "provenance": {
            "evidence_kind": str(evidence.evidence_kind),
            "provider_context_mode": str(evidence.provider_context_mode),
            "adapter_id": evidence.adapter_id,
            "result_contract": evidence.result_contract,
            "executed_at": _iso(evidence.executed_at),
            "transport_attempts": evidence.transport_attempts,
            "profile_id": evidence.profile_id,
            "profile_catalog_hash": evidence.profile_catalog_hash,
            "config_hash": evidence.config_hash,
            "adapter_version": evidence.adapter_version,
            "model_identifier": evidence.model_identifier,
            "model_revision": evidence.model_revision,
            "content_policy_version": evidence.content_policy_version,
            "policy_match_view_version": evidence.policy_match_view_version,
        },
        "moderation_outcome": {
            "lexical_regression": str(moderation.lexical),
            "lexical_policy_version": moderation.lexical_policy_version,
            "match_view_version": moderation.match_view_version,
            "comprehensive_moderation": moderation.comprehensive_moderation,
            "child_visibility": moderation.child_visibility,
        },
    }


def _label(value: ObservedLabel) -> dict[str, object]:
    return {"value": value.value,
            "language": {"status": value.language_status, "tags": list(value.language_tags)}}


def analysis_record_view(
    head: AnalysisHead,
    observation: VisionObservation,
    corrections: tuple[MeaningCorrection, ...],
) -> dict[str, object]:
    original = observation.observation
    checkpoint, render = head.source.checkpoint, head.source.render
    typed: dict[str, object] = {}
    if head.typed_binding is not None:
        # Sibling 0.2-candidate record: the head binding is reachable from the read path.
        typed = {
            "contract_name": "AnalysisResultAndCorrection",
            "contract_version": TYPED_RECORD_VERSION,
            "context_binding": head.typed_binding.canonical(),
        }
    return {
        **typed,
        "analysis_id": head.analysis_id,
        "analysis_revision": head.analysis_revision,
        "accepted_status": str(head.accepted_status),
        "status_reason": head.status_reason,
        "candidate": worker_candidate_view(head, observation),
        "original_observation": {
            "entities": [{"observation_id": e.observation_id, "label": _label(e.label),
                          "confidence": e.confidence} for e in original.entities],
            "actions": [{"observation_id": a.observation_id, "label": _label(a.label),
                         "actor_ref": a.actor_ref, "object_ref": a.object_ref,
                         "confidence": a.confidence} for a in original.actions],
            "relations": [{"observation_id": r.observation_id, "predicate": _label(r.predicate),
                           "subject_ref": r.subject_ref, "object_ref": r.object_ref,
                           "confidence": r.confidence} for r in original.relations],
            "themes": [{"observation_id": t.observation_id, "label": _label(t.label),
                        "evidence_refs": list(t.evidence_refs), "confidence": t.confidence}
                       for t in original.themes],
            "ambiguous_regions": [{"observation_id": g.observation_id, "note": _label(g.note)}
                                  for g in original.ambiguous_regions],
        },
        "observation_sha256": observation.observation_sha256,
        "source_binding": {
            "input_snapshot_ref": head.source.snapshot_ref,
            "checkpoint": {
                "checkpoint_id": checkpoint.checkpoint_id,
                "canvas_id": checkpoint.canvas_id,
                "document_epoch": checkpoint.document_epoch,
                "checkpoint_revision": checkpoint.checkpoint_revision,
                "checksum_sha256": checkpoint.checksum_sha256,
            },
            "render": {
                "render_ref": render.render_ref,
                "render_sha256": render.render_sha256,
                "media_type": render.media_type,
                "renderer_version": render.renderer_version,
            },
            "admission_receipt_id": head.admission.receipt_id,
        },
        "corrections": [correction_record_view(c) for c in corrections],
        "current_meaning_ref": head.current_meaning_ref,
    }


__all__ = [
    "CORRECTION_CONTRACT",
    "TYPED_RECORD_VERSION",
    "CorrectionCommand",
    "CorrectionResult",
    "DownstreamMeaning",
    "InvalidationNotice",
    "MeaningState",
    "ObservationDisposition",
    "ObservationResult",
    "VisionAnalysisDependencies",
    "VisionAnalysisError",
    "VisionAnalysisService",
    "analysis_record_view",
    "child_correction_view",
    "correction_record_view",
    "eligibility_code",
    "teacher_correction_view",
    "worker_candidate_view",
]
