"""BE2-05 Sketch review application service (offline component, FEAT-052, plan candidate R2).

Moderation and per-Sketch Teacher exact review (CMD-35 over DATA-24 V1) in a 05-owned store.
Every decision follows plan §4.6: snapshot -> token -> read -> decide outside the unit, then a
final unit that holds the token epochs through the commit. Child access is decided only by
``eligibility`` (approved, current, not terminal, in audience).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any

from pydantic import ValidationError

from sketch2life.application.ports.ai_jobs import (
    ClockPort,
    IdGeneratorPort,
    Principal,
    PrincipalRole,
    QuarantineIntent,
)
from sketch2life.application.ports.sketch_review import (
    EligibilityChangedIntent,
    ModerationVerdict,
    QuarantineSink,
    ReviewAction,
    ReviewArtifactPort,
    ReviewAuditRecord,
    ReviewAuthorityPort,
    ReviewContextPort,
    ReviewContextSnapshot,
    ReviewPolicy,
    ReviewPolicyPort,
    ReviewReceipt,
    ReviewRevisionConflict,
    ReviewScope,
    ReviewTokenPort,
    ReviewUniqueConflict,
    SketchModerationPort,
    SketchReviewRepository,
    SketchReviewTargetReader,
    SketchReviewUnitOfWork,
    StaleReviewDecision,
)
from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    ExactContentReviewRecordV1,
)
from sketch2life.contracts.schemas.sketch_reviews import (
    ERROR_STATUS,
    BindTarget,
    BoundSketchReview,
    SketchChildPayloadV0,
    SketchReviewBindError,
    SketchReviewQueueItemV0,
    SketchReviewResultV0,
    bind_sketch_review,
    canonical_review_command,
)
from sketch2life.domain.sketch_review import (
    REVIEW_CONTRACT,
    Decision,
    EntryState,
    ModerationOutcome,
    ModerationRecord,
    Projection,
    ReviewAudience,
    ReviewEntry,
    ReviewHead,
    ReviewTarget,
    TerminalVersion,
    VersionTerminalMarker,
    apply_decision,
    compose_projection,
    current_entry,
    entries_by_version,
    mark_stale,
    parse_review_etag,
    policy_version_label,
    review_etag,
    review_key,
    target_moderation_key,
)
from sketch2life.domain.vision_context import strict_canonical_sha256

DECISION_ROUNDS = 2
_KEY_MAX = 120


class SketchReviewError(Exception):
    def __init__(self, code: str, *, current_revisions: Mapping[str, object] | None = None,
                 field_name: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = ERROR_STATUS[code]
        self.current_revisions = dict(current_revisions or {})
        self.field_name = field_name


@dataclass(frozen=True, slots=True)
class ReviewCommand:
    principal: Principal
    proposal_id: str
    idempotency_key: str | None
    if_match: str | None
    body: ExactContentReviewCommandV1 | str | bytes


@dataclass(frozen=True, slots=True)
class ReviewResult:
    status: int
    data: Mapping[str, Any]
    replayed: bool


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    eligible: bool
    participant_id: str | None = None
    review_ref: str | None = None
    target: ReviewTarget | None = None


@dataclass(frozen=True, slots=True)
class SketchReviewDependencies:
    targets: SketchReviewTargetReader
    artifacts: ReviewArtifactPort
    repository: SketchReviewRepository
    tokens: ReviewTokenPort
    moderation: SketchModerationPort
    authority: ReviewAuthorityPort
    context: ReviewContextPort
    policy: ReviewPolicyPort
    quarantine: QuarantineSink
    clock: ClockPort
    ids: IdGeneratorPort


@dataclass(frozen=True, slots=True)
class _Prepared:
    """Everything decided outside the unit for one CMD-35 attempt."""

    target: ReviewTarget
    bound: BoundSketchReview
    policy: ReviewPolicy
    verdict: ModerationVerdict
    descriptors_ok: bool
    expected_decision_revision: int
    generation: tuple[tuple[str, int], ...]


class SketchReviewService:
    def __init__(self, deps: SketchReviewDependencies) -> None:
        self._d = deps

    # ============================================================ CMD-35
    def record_review(self, command: ReviewCommand) -> ReviewResult:
        principal = command.principal
        key = command.idempotency_key
        if not key or len(key) > _KEY_MAX:
            raise SketchReviewError("MALFORMED_REQUEST")
        body = self._parse(command.body)
        fingerprint = strict_canonical_sha256({  # RV-CR05: normalized semantic command
            "contract": REVIEW_CONTRACT, "proposal_id": command.proposal_id,
            "body": canonical_review_command(body)})
        receipt_key = "|".join((principal.organization_id, principal.principal_id,
                                REVIEW_CONTRACT, command.proposal_id, key))
        for _ in range(DECISION_ROUNDS):
            first = self._target(principal, command.proposal_id)
            self._require_teacher(principal, first, ReviewAction.REVIEW)
            replay = self._replay(receipt_key, fingerprint)
            if replay is not None:
                return replay
            self._policy(first)  # preliminary only; the decisive read follows the token
            expected = self._require_if_match(command.if_match, first)
            token = self._d.tokens.token(first, principal)
            prepared = self._prepare(principal, command.proposal_id, body, first, expected,
                                     receipt_key)
            if prepared is None:  # identity moved between snapshot and read: restart
                continue
            try:
                outcome = self._commit_review(principal, token, prepared, body, receipt_key,
                                              fingerprint)
            except StaleReviewDecision:
                continue
            except ReviewUniqueConflict:
                continue
            except ReviewRevisionConflict:
                raise SketchReviewError(
                    "STALE_AGGREGATE",
                    current_revisions=self._current_revisions(first)) from None
            if isinstance(outcome, SketchReviewError):
                raise outcome
            return outcome
        raise SketchReviewError("DEPENDENCY_UNAVAILABLE")

    def _parse(self, body: ExactContentReviewCommandV1 | str | bytes
               ) -> ExactContentReviewCommandV1:
        if isinstance(body, ExactContentReviewCommandV1):
            return body
        try:
            return ExactContentReviewCommandV1.model_validate_json(body, strict=True)
        except ValidationError as exc:
            code = ("FIELD_NOT_ALLOWED" if any(e["type"] == "extra_forbidden"
                                               for e in exc.errors())
                    else "FIELD_VALIDATION_FAILED")
            raise SketchReviewError(code) from None

    def _prepare(self, principal: Principal, proposal_id: str,
                 body: ExactContentReviewCommandV1, first: ReviewTarget, expected: int,
                 receipt_key: str) -> _Prepared | None:
        """Plan §4.6 step 3: every decisive observation is read AFTER the token (RV-CR02); the
        final hold then proves none of their epochs moved before the commit."""

        target = self._d.targets.read(proposal_id)
        if target is None or target.identity() != first.identity():
            return None
        self._require_teacher(principal, target, ReviewAction.REVIEW)
        policy = self._policy(target)
        generation = self._d.tokens.generation(target.organization_id, target.session_id)
        if not target.reviewable:
            raise SketchReviewError("INVALID_STATE")
        try:
            bound = bind_sketch_review(body, self._bind_target(target), proposal_id)
        except SketchReviewBindError as exc:
            raise SketchReviewError(exc.code, field_name=exc.field_name) from None
        context = self._context(target)
        self._require_context(target, context, bound)
        descriptors = tuple(self._d.artifacts.describe(ref) for ref in target.ref_set)
        descriptors_ok = all(
            d is not None and d.quarantine_reason is None and d.sha256 == asset.sha256
            for d, asset in zip(descriptors, target.assets, strict=True))
        if not descriptors_ok:
            raise SketchReviewError("STALE_CONTEXT")
        verdict = self._d.moderation.moderate(target, descriptors, policy)
        if body.decision == "approve":  # early terminal read; the final unit decides (§4.3)
            with self._d.repository.transaction() as tx:
                marker = tx.get_marker(*_vk(target))
                head = tx.get_head(proposal_id)
                receipt = tx.get_receipt(receipt_key)
            if receipt is not None:  # the same key committed meanwhile: restart, then replay
                return None
            if (0 if head is None else head.decision_revision) != expected:
                raise SketchReviewError("STALE_AGGREGATE",
                                        current_revisions=self._current_revisions(target))
            if marker is not None:
                raise SketchReviewError("INVALID_STATE")
        return _Prepared(target, bound, policy, verdict, descriptors_ok, expected, generation)

    def _commit_review(self, principal: Principal, token: object, p: _Prepared,
                       body: ExactContentReviewCommandV1, receipt_key: str,
                       fingerprint: str) -> ReviewResult | SketchReviewError:
        target, bound = p.target, p.bound
        decision = Decision(bound.decision)
        now = self._d.clock.now()
        policy_version = policy_version_label(p.policy.ref(), target.policy_ref)
        audience = ReviewAudience(bound.session_id, bound.group_ids, bound.participant_ids,
                                  bound.audience_context_revision, bound.consent_refs)
        key = review_key(proposal_id=target.proposal_id, version=target.proposal_version,
                         content_sha256=_hash(target), audience=audience,
                         context_revision=target.context_revision,
                         policy_version=policy_version)
        deferred: SketchReviewError | None = None
        with self._d.repository.transaction() as tx:
            tx.hold(token)  # type: ignore[arg-type]
            head = tx.get_head(target.proposal_id) or ReviewHead(target.proposal_id,
                                                                  target.organization_id)
            if tx.get_receipt(receipt_key) is not None:  # same key won meanwhile: replay
                raise ReviewUniqueConflict("receipt")
            if head.decision_revision != p.expected_decision_revision:
                raise ReviewRevisionConflict()  # D-2: the losing same-ETag command gets 412
            # RV-CR01: the assessment for THIS policy + content + refs; never an older policy's.
            moderation = tx.get_moderation(target_moderation_key(target, _label(p.policy)))
            if moderation is None:
                moderation = self._new_moderation(target, p.verdict, p.policy, now)
                tx.put_moderation(moderation)
                if moderation.outcome is ModerationOutcome.BLOCKED:
                    self._add_quarantine(tx, target, moderation.policy_version)
                tx.touch(target.organization_id, target.proposal_id)
            marker = tx.get_marker(*_vk(target))
            entries = tx.entries(target.proposal_id)
            if decision is Decision.APPROVE and (
                moderation.outcome is ModerationOutcome.BLOCKED or marker is not None
            ):  # no bypass of unsafe content; terminal version (OD-07-A)
                deferred = SketchReviewError("INVALID_STATE")
            else:
                existing = next((e for e in entries if e.key == key
                                 and e.state is EntryState.EFFECTIVE
                                 and e.decision is decision
                                 # an entry from an older 05 generation is no duplicate: the
                                 # new decision replaces it (same key -> revoked), RV-CR04
                                 and e.generation == p.generation), None)
                if existing is not None:
                    result = self._result(existing, target, head, semantic_duplicate=True,
                                          status=200)
                else:
                    revision = head.decision_revision + 1
                    entry = ReviewEntry(
                        self._d.ids.new_id("skrev"), revision, decision, bound.reason,
                        principal.principal_id, now, target.proposal_id,
                        target.proposal_version, _hash(target), target.context_revision,
                        audience, policy_version, target.review_revision, key,
                        generation=p.generation)
                    try:
                        outcome = apply_decision(entries, marker, entry, now)
                    except TerminalVersion:
                        raise SketchReviewError("INVALID_STATE") from None
                    tx.put_entries(target.proposal_id, outcome.entries)
                    if outcome.marker is not None:
                        tx.insert_marker(outcome.marker)
                    current_id = None if outcome.current is None else outcome.current.review_id
                    head = replace(head, decision_revision=revision).with_current(
                        _vk(target)[1:], current_id)
                    tx.put_head(expected_decision_revision=p.expected_decision_revision,
                                head=head)
                    for changed in (*outcome.changed, entry):
                        tx.add_intent(self._intent(target, changed.review_id,
                                                   f"{changed.decision}:{changed.state}"))
                    tx.add_audit(ReviewAuditRecord(
                        _event_id("audit", entry.review_id), target.organization_id,
                        target.proposal_id, "sketch.review", str(decision),
                        principal.principal_id, now))
                    tx.touch(target.organization_id, target.proposal_id)
                    result = self._result(entry, target, head, semantic_duplicate=False,
                                          status=201)
                tx.put_receipt(ReviewReceipt(receipt_key, fingerprint, result.status,
                                             result.data, now))
                return result
        assert deferred is not None
        return deferred

    def _result(self, entry: ReviewEntry, target: ReviewTarget, head: ReviewHead, *,
                semantic_duplicate: bool, status: int) -> ReviewResult:
        policy_version = entry.policy_version
        record = ExactContentReviewRecordV1(
            review_id=entry.review_id, review_revision=entry.review_revision,
            reviewer_principal_id=entry.reviewer_principal_id, reviewed_at=entry.reviewed_at,
            policy_version=_opaque(policy_version), state=str(entry.state))  # type: ignore[arg-type]
        data = SketchReviewResultV0(
            record=record, decision=str(entry.decision),  # type: ignore[arg-type]
            target={"id": target.proposal_id, "version": target.proposal_version,  # type: ignore[arg-type]
                    "hash": _hash(target)},
            review_etag=review_etag(target.proposal_id, target.proposal_version,
                                    target.review_revision, head.decision_revision),
            semantic_duplicate=semantic_duplicate, replayed=False,
        ).model_dump(mode="json")
        return ReviewResult(status, data, False)

    def _replay(self, receipt_key: str, fingerprint: str) -> ReviewResult | None:
        with self._d.repository.transaction() as tx:
            receipt = tx.get_receipt(receipt_key)
        if receipt is None:
            return None
        if receipt.fingerprint != fingerprint:
            raise SketchReviewError("IDEMPOTENCY_PAYLOAD_MISMATCH")
        return ReviewResult(receipt.status, {**receipt.data, "replayed": True}, True)

    # ============================================================ moderation
    def moderate(self, teacher: Principal, proposal_id: str) -> ModerationRecord:
        """Moderate the current version once (queue open); same token protocol (§4.4, §4.6)."""

        for _ in range(DECISION_ROUNDS):
            first = self._target(teacher, proposal_id)
            self._require_teacher(teacher, first, ReviewAction.QUEUE_READ)  # preliminary
            if not first.reviewable:
                raise SketchReviewError("INVALID_STATE")
            self._policy(first)  # preliminary
            token = self._d.tokens.token(first, teacher)
            target = self._d.targets.read(proposal_id)
            if target is None or target.identity() != first.identity():
                continue
            self._require_teacher(teacher, target, ReviewAction.QUEUE_READ)  # decisive (CR02)
            policy = self._policy(target)
            descriptors = tuple(self._d.artifacts.describe(ref) for ref in target.ref_set)
            if not all(d is not None and d.quarantine_reason is None for d in descriptors):
                raise SketchReviewError("STALE_CONTEXT")
            verdict = self._d.moderation.moderate(target, descriptors, policy)
            try:
                with self._d.repository.transaction() as tx:
                    tx.hold(token)
                    existing = tx.get_moderation(target_moderation_key(target, _label(policy)))
                    if existing is not None:
                        return existing
                    record = self._new_moderation(target, verdict, policy,
                                                  self._d.clock.now())
                    tx.put_moderation(record)
                    if record.outcome is ModerationOutcome.BLOCKED:
                        self._add_quarantine(tx, target, record.policy_version)
                    tx.touch(target.organization_id, target.proposal_id)
                    return record
            except StaleReviewDecision:
                continue
        raise SketchReviewError("DEPENDENCY_UNAVAILABLE")

    def _new_moderation(self, target: ReviewTarget, verdict: ModerationVerdict,
                        policy: ReviewPolicy, now: Any) -> ModerationRecord:
        return ModerationRecord(
            target.proposal_id, target.proposal_version, _hash(target),
            tuple((a.artifact_ref, a.sha256) for a in target.assets), verdict.outcome,
            verdict.reason_code, _label(policy), now)

    def _add_quarantine(self, tx: SketchReviewUnitOfWork, target: ReviewTarget,
                        policy_label: str) -> None:
        """Intent only: written atomically with the decision; applied after commit (§4.4)."""

        tx.add_quarantine(QuarantineIntent(
            _event_id("quarantine", f"{target.proposal_id}:{target.proposal_version}:"
                                    f"{_hash(target)}:{policy_label}"),
            target.organization_id, target.job_id or "unknown", target.attempt_id or "unknown",
            target.ref_set, "SKETCH_MODERATION_BLOCKED"))

    def deliver_quarantine(self) -> int:
        """After commit, outside any unit: apply pending intents at the sink (idempotent)."""

        with self._d.repository.transaction() as tx:
            pending = tx.pending_quarantine()
        delivered = 0
        for intent in pending:
            try:
                self._d.quarantine.quarantine(intent)
            except Exception:  # noqa: BLE001 - stays pending and is redelivered later
                continue
            with self._d.repository.transaction() as tx:
                tx.mark_quarantine_delivered(intent.event_id)
            delivered += 1
        return delivered

    # ============================================================ Teacher reads
    def queue_item(self, teacher: Principal, proposal_id: str) -> dict[str, Any]:
        target = self._target(teacher, proposal_id)
        self._require_teacher(teacher, target, ReviewAction.QUEUE_READ)
        record = self._d.targets.queue_record(teacher, proposal_id)
        if record is None:
            raise SketchReviewError("RESOURCE_NOT_FOUND")
        state = self._state(target)
        projection, marker, moderation, head = state
        show = (target.reviewable and record.get("content_withheld_reason") is None
                and (moderation is None or moderation.outcome is ModerationOutcome.PASSED))
        return SketchReviewQueueItemV0(
            proposal_id=target.proposal_id, proposal_version=target.proposal_version,
            content_sha256=target.content_sha256,
            source_snapshot_ref=target.source_snapshot_ref, session_id=target.session_id,
            group_id=target.group_id, audience_participant_ids=target.audience,
            context_revision=target.context_revision, assistance_level=target.level,
            display_mode=target.display_mode,  # type: ignore[arg-type]
            text_or_question=target.text if show else None,
            overlay_asset_ref=(target.asset.artifact_ref if show and target.asset is not None
                               else None),
            pipeline_state=projection.pipeline_state,
            moderation_state=projection.moderation_state,  # type: ignore[arg-type]
            moderation_reason=None if moderation is None else moderation.reason_code,
            current_decision=projection.review_decision,  # type: ignore[arg-type]
            decision_applicable=projection.decision_applicable,
            version_terminal=projection.version_terminal,
            approve_allowed=projection.approve_allowed,
            terminal_first_decision=(None if marker is None
                                     else str(marker.first_decision)),  # type: ignore[arg-type]
            approval_ref=projection.approval_ref,
            review_etag=review_etag(target.proposal_id, target.proposal_version,
                                    target.review_revision, head.decision_revision),
        ).model_dump(mode="json")

    def projection(self, teacher: Principal, proposal_id: str) -> dict[str, Any]:
        """Composed DATA-23 record (read-only): producer record + 05 review state (§4.1)."""

        target = self._target(teacher, proposal_id)
        self._require_teacher(teacher, target, ReviewAction.QUEUE_READ)
        record = self._d.targets.queue_record(teacher, proposal_id)
        if record is None:
            raise SketchReviewError("RESOURCE_NOT_FOUND")
        projection, marker, _, head = self._state(target)
        composed = dict(record)
        composed.update({
            "pipeline_state": projection.pipeline_state,
            "moderation_state": projection.moderation_state,
            "approval_ref": projection.approval_ref,
            "review_decision": projection.review_decision,
            "decision_applicable": projection.decision_applicable,
            "version_terminal": projection.version_terminal,
            "terminal_first_decision": None if marker is None else str(marker.first_decision),
            "review_etag": review_etag(target.proposal_id, target.proposal_version,
                                       target.review_revision, head.decision_revision),
        })
        if projection.pipeline_state != "approved" and projection.pipeline_state != (
            "pending_teacher_review"
        ):
            composed["text_or_question"] = None
            composed["overlay_asset_ref"] = None
        return composed

    def _state(self, target: ReviewTarget) -> tuple[Projection, VersionTerminalMarker | None,
                                                    ModerationRecord | None, ReviewHead]:
        with self._d.repository.transaction() as tx:
            head = tx.get_head(target.proposal_id) or ReviewHead(target.proposal_id,
                                                                  target.organization_id)
            entries = tx.entries(target.proposal_id)
            marker = tx.get_marker(*_vk(target)) if target.content_sha256 else None
            moderation = self._current_moderation(tx, target)
        if target.content_sha256 is None:
            return (Projection(target.pipeline_state, target.moderation_state, None, False,
                               False, False, None), None, None, head)
        version_entries = entries_by_version(entries, target.version_key)
        current = current_entry(version_entries, target.version_key)
        applicable = current is not None and self._applicable(current, target)
        projection = compose_projection(target, current=current, current_applicable=applicable,
                                        entries=version_entries, marker=marker,
                                        moderation=moderation)
        return projection, marker, moderation, head

    # ============================================================ Child / access
    def eligibility(self, principal: Principal, proposal_id: str, *,
                    asset_ref: str | None = None, content_sha256: str | None = None,
                    review_ref: str | None = None) -> EligibilityDecision:
        """Plan §4.10: one generic 'not available' outcome for every non-eligible case."""

        denied = EligibilityDecision(False)
        if principal.role is not PrincipalRole.DEVICE:
            return denied
        target = self._d.targets.read(proposal_id)
        if (target is None or target.organization_id != principal.organization_id
                or not target.reviewable or target.content_sha256 is None):
            return denied
        scope = _scope(target)
        if not self._d.authority.allowed(principal, scope, ReviewAction.CHILD_VIEW):
            return denied
        participant = self._d.authority.participant_for(principal, scope)
        if participant is None or participant not in target.audience:
            return denied
        if content_sha256 is not None and content_sha256 != target.content_sha256:
            return denied
        if asset_ref is not None and asset_ref not in target.ref_set:
            return denied
        with self._d.repository.transaction() as tx:
            marker = tx.get_marker(*_vk(target))
            moderation = self._current_moderation(tx, target)
            entries = entries_by_version(tx.entries(target.proposal_id), target.version_key)
        if marker is not None:  # D-1: a terminal version never opens access
            return denied
        if moderation is None or moderation.outcome is not ModerationOutcome.PASSED:
            return denied
        context = self._context_or_none(target)
        if context is None or participant not in context.admitted:
            return denied
        approvals = [e for e in entries if e.decision is Decision.APPROVE
                     and e.state is EntryState.EFFECTIVE
                     and participant in e.audience.participant_ids
                     and self._applicable(e, target)]
        if not approvals:
            return denied
        entry = max(approvals, key=lambda e: e.review_revision)
        if review_ref is not None and review_ref != entry.review_id:
            return denied
        return EligibilityDecision(True, participant, entry.review_id, target)

    def child_payload(self, principal: Principal, proposal_id: str) -> dict[str, Any]:
        decision = self.eligibility(principal, proposal_id)
        if decision.eligible and decision.target is not None:
            target = decision.target
            return SketchChildPayloadV0(
                proposal_id=proposal_id, status="available",
                display_mode=target.display_mode,  # type: ignore[arg-type]
                text_or_question=target.text,
                overlay_asset_ref=None if target.asset is None else target.asset.artifact_ref,
                review_ref=decision.review_ref,
            ).model_dump(mode="json")
        status = "unavailable"
        current = self._d.targets.read(proposal_id)
        if (current is not None and principal.role is PrincipalRole.DEVICE
                and current.organization_id == principal.organization_id
                and current.reviewable and current.content_sha256 is not None):
            with self._d.repository.transaction() as tx:
                marker = tx.get_marker(*_vk(current))
                moderation = self._current_moderation(tx, current)
            if marker is None and (moderation is None
                                   or moderation.outcome is ModerationOutcome.PASSED):
                status = "pending"
        return SketchChildPayloadV0(proposal_id=proposal_id,
                                    status=status).model_dump(mode="json")  # type: ignore[arg-type]

    # ============================================================ stale / notices
    def apply_target_notice(self, notice_id: str, organization_id: str,
                            proposal_id: str) -> tuple[str, ...]:
        """Idempotent by notice id: effective entries no longer applicable become stale."""

        with self._d.repository.transaction() as tx:
            if tx.notice_seen(notice_id):
                return ()
        target = self._d.targets.read(proposal_id)
        stale = self._stale_ids(proposal_id, target)
        with self._d.repository.transaction() as tx:
            if tx.notice_seen(notice_id):
                return ()
            changed = self._mark(tx, organization_id, proposal_id, stale)
            tx.record_notice(notice_id)
        return changed

    def refresh(self, proposal_id: str, organization_id: str) -> tuple[str, ...]:
        target = self._d.targets.read(proposal_id)
        stale = self._stale_ids(proposal_id, target)
        with self._d.repository.transaction() as tx:
            return self._mark(tx, organization_id, proposal_id, stale)

    def _stale_ids(self, proposal_id: str, target: ReviewTarget | None) -> frozenset[str]:
        with self._d.repository.transaction() as tx:
            entries = tx.entries(proposal_id)
        return frozenset(e.review_id for e in entries if e.state is EntryState.EFFECTIVE and (
            target is None or not self._applicable(e, target)))

    def _mark(self, tx: SketchReviewUnitOfWork, organization_id: str, proposal_id: str,
              stale: frozenset[str]) -> tuple[str, ...]:
        if not stale:
            return ()
        entries, changed = mark_stale(tx.entries(proposal_id), stale)
        if not changed:
            return ()
        tx.put_entries(proposal_id, entries)
        head = tx.get_head(proposal_id)
        if head is not None:
            for version_key in {e.version_key for e in changed}:
                current = current_entry(entries, version_key)
                head = head.with_current(version_key, None if current is None
                                         else current.review_id)
            tx.put_head(expected_decision_revision=head.decision_revision, head=head)
        target_version = changed[0].target_version
        for entry in changed:
            tx.add_intent(EligibilityChangedIntent(
                _event_id("stale", entry.review_id), organization_id, proposal_id,
                target_version, entry.review_id, "stale"))
        tx.touch(organization_id, proposal_id)
        return tuple(e.review_id for e in changed)

    # ============================================================ helpers
    def _target(self, principal: Principal, proposal_id: str) -> ReviewTarget:
        target = self._d.targets.read(proposal_id)
        if target is None or target.organization_id != principal.organization_id:
            raise SketchReviewError("RESOURCE_NOT_FOUND")
        return target

    def _require_teacher(self, principal: Principal, target: ReviewTarget,
                         action: ReviewAction) -> None:
        if principal.role is PrincipalRole.DEVICE:
            raise SketchReviewError("RESOURCE_NOT_FOUND")
        if principal.role is not PrincipalRole.TEACHER:
            raise SketchReviewError("FORBIDDEN_SCOPE")
        if not self._d.authority.allowed(principal, _scope(target), action):
            raise SketchReviewError("RESOURCE_NOT_FOUND")

    def _policy(self, target: ReviewTarget) -> ReviewPolicy:
        policy = self._d.policy.current(target.organization_id, target.session_id)
        if policy is None or not policy.enabled:
            raise SketchReviewError("POLICY_UNRESOLVED")
        return policy

    def _head(self, proposal_id: str, organization_id: str) -> ReviewHead:
        with self._d.repository.transaction() as tx:
            return tx.get_head(proposal_id) or ReviewHead(proposal_id, organization_id)

    def _current_revisions(self, target: ReviewTarget) -> dict[str, object]:
        head = self._head(target.proposal_id, target.organization_id)
        return {"proposal_version": target.proposal_version,
                "review_revision": target.review_revision,
                "decision_revision": head.decision_revision,
                "review_etag": review_etag(target.proposal_id, target.proposal_version,
                                           target.review_revision, head.decision_revision)}

    def _require_if_match(self, if_match: str | None, target: ReviewTarget) -> int:
        if if_match is None or not if_match.strip():
            raise SketchReviewError("PRECONDITION_REQUIRED")
        parsed = parse_review_etag(if_match)
        head = self._head(target.proposal_id, target.organization_id)
        if parsed != (target.proposal_id, target.proposal_version, target.review_revision,
                      head.decision_revision):
            raise SketchReviewError("STALE_AGGREGATE",
                                    current_revisions=self._current_revisions(target))
        return head.decision_revision

    def _bind_target(self, target: ReviewTarget) -> BindTarget:
        return BindTarget(target.proposal_id, target.proposal_version, _hash(target),
                          target.context_revision, target.session_id,
                          frozenset({target.group_id} if target.group_id else set()),
                          frozenset(target.audience))

    def _context(self, target: ReviewTarget) -> ReviewContextSnapshot:
        context = self._context_or_none(target)
        if context is None:
            raise SketchReviewError("DEPENDENCY_UNAVAILABLE")
        return context

    def _context_or_none(self, target: ReviewTarget) -> ReviewContextSnapshot | None:
        return self._d.context.current(target.organization_id, target.session_id,
                                       (target.contributor,))

    def _require_context(self, target: ReviewTarget, context: ReviewContextSnapshot,
                         bound: BoundSketchReview) -> None:
        if not context.session_active:
            raise SketchReviewError("INVALID_STATE")
        if target.contributor not in context.consent_effective:
            raise SketchReviewError("CONSENT_REQUIRED")
        if (bound.audience_context_revision != context.audience_context_revision
                or bound.consent_refs != context.consent_refs
                or not set(bound.participant_ids) <= context.admitted):
            raise SketchReviewError("STALE_CONTEXT")

    def _applicable(self, entry: ReviewEntry, target: ReviewTarget) -> bool:
        """Entry still current for this target, context and policy (pull, §4.9)."""

        if (entry.state is not EntryState.EFFECTIVE or not target.reviewable
                or target.content_sha256 is None
                or entry.version_key != target.version_key
                or entry.producer_review_revision != target.review_revision
                or entry.source_context_revision != target.context_revision):
            return False
        context = self._context_or_none(target)
        policy = self._d.policy.current(target.organization_id, target.session_id)
        if context is None or policy is None or not policy.enabled:
            return False
        generation = self._d.tokens.generation(target.organization_id, target.session_id)
        if entry.generation and entry.generation != generation:
            return False  # RV-CR04: an observed 05 invalidation is monotonic; no revival
        return (context.session_active
                and target.contributor in context.consent_effective
                and context.audience_context_revision == entry.audience.audience_context_revision
                and context.consent_refs == entry.audience.consent_refs
                and policy_version_label(policy.ref(), target.policy_ref) == entry.policy_version)

    def _current_moderation(self, tx: SketchReviewUnitOfWork,
                            target: ReviewTarget) -> ModerationRecord | None:
        """Assessment under the CURRENT moderation policy only (RV-CR01)."""

        if target.content_sha256 is None:
            return None
        policy = self._d.policy.current(target.organization_id, target.session_id)
        if policy is None or not policy.enabled:
            return None
        return tx.get_moderation(target_moderation_key(target, _label(policy)))

    def _intent(self, target: ReviewTarget, review_id: str, reason: str
                ) -> EligibilityChangedIntent:
        return EligibilityChangedIntent(_event_id("eligibility", f"{review_id}:{reason}"),
                                        target.organization_id, target.proposal_id,
                                        target.proposal_version, review_id, reason)


def _scope(target: ReviewTarget) -> ReviewScope:
    return ReviewScope(target.organization_id, target.class_id, target.session_id,
                       target.audience)


def _hash(target: ReviewTarget) -> str:
    assert target.content_sha256 is not None
    return target.content_sha256


def _vk(target: ReviewTarget) -> tuple[str, int, str]:
    return (target.proposal_id, target.proposal_version, _hash(target))


def _event_id(kind: str, value: str) -> str:
    return f"be205_{kind}_" + sha256(value.encode()).hexdigest()[:24]


def _label(policy: ReviewPolicy) -> str:
    return f"{policy.policy_id}@{policy.version}"


def _opaque(value: str) -> str:
    """Record V1 ``policy_version`` is an OpaqueId: map the label to an allowed form."""

    return "rp_" + sha256(value.encode()).hexdigest()[:32]


__all__ = [
    "DECISION_ROUNDS",
    "EligibilityDecision",
    "ReviewCommand",
    "ReviewResult",
    "SketchReviewDependencies",
    "SketchReviewError",
    "SketchReviewService",
]
