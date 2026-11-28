"""The Parent video admission saga and the video job progress (FEAT-066 T-1a; SRS l.395, l.596-597).

The saga is a sequence of independent units, never one transaction across the ports (BR-38 l.282,
Billing contract Draft 9 §9):

1. ``begin_intent`` commits the intent row, the receipt and ``VIDEO_ADMISSION_PENDING`` (SRS l.395:
   "một hàng generation bền vững trước tiên là intent").
2. With no transaction open the service calls the compute reservation first (``COST_LIMIT_REACHED``
   stops there), then the quota admission, both keyed by the stored key hash and the generation id.
3. ``finish_admission`` is a compare-and-set on ``ADMISSION_PENDING``: both clear gives
   ``ACCEPTED``, a refusal gives ``ADMISSION_REJECTED`` and the reservation is released outside any
   transaction.

An answer that cannot be read (``UNAVAILABLE``, a timeout, a crash after step 1) leaves the intent
pending; ``reconcile_pending_admissions`` asks again with the same key and no timer ever rejects an
intent, because a unit that was admitted is never refunded (l.596, FR-C-08). The service holds no
quota, balance, price or month logic: it only forwards the two outcomes and maps them to codes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_video import (
    QUOTA_CONTRACT_VERSION,
    AckStatus,
    AdmissionDecision,
    GenerationRecord,
    ProgressEvent,
    ProgressResult,
    QuotaStatus,
    ReservationStatus,
    RunCommandResult,
    StoryVideoAdapters,
    StoryVideoRepository,
    VideoRequestScope,
    port_fingerprint,
)
from sketch2life.domain.story_video.model import (
    ADMISSION_REFUSALS,
    AI_COST_LIMIT_REACHED,
    SUBSCRIPTION_RESTRICTED,
    UNSUITABLE_REASON_CODES,
    VIDEO_QUOTA_EXCEEDED,
    GenerationState,
)

_LOG = logging.getLogger(__name__)
# The ports run on worker threads so that a slow adapter is cut off by a per-call timeout and the
# request thread never blocks past it (the call is then read as UNAVAILABLE).
_PORT_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="story-video-port")
DEFAULT_PORT_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class AdmissionOutcome:
    """The accepted request (any state of the saga), or the purged-run projection of a replay."""

    record: GenerationRecord | None
    projection: ParentStoryLifecycleRecord | None = None


@dataclass(frozen=True, slots=True)
class ReconcileReport:
    resolved: int
    still_pending: int
    mismatched: int
    compute_closed: int
    cancelled_settled: int = 0


def refusal_error(code: str | None) -> ParentStoryRunError:
    """The stable error of a refused admission (first answer and every replay)."""

    if code is None or code not in ADMISSION_REFUSALS:
        return ParentStoryRunError(503, "PROVIDER_UNAVAILABLE")
    return ParentStoryRunError(ADMISSION_REFUSALS[code], code)


class _Saga:
    def __init__(
        self,
        repository: StoryVideoRepository,
        adapters: StoryVideoAdapters | None,
        *,
        call_timeout_seconds: float = DEFAULT_PORT_TIMEOUT_SECONDS,
    ) -> None:
        self._repository = repository
        self._adapters = adapters
        self._timeout = call_timeout_seconds

    def _call(self, function: Callable[..., Any], **arguments: Any) -> Any | None:
        """One port call with a timeout; a failure or a timeout is read as ``UNAVAILABLE``."""

        try:
            return _PORT_EXECUTOR.submit(function, **arguments).result(timeout=self._timeout)
        except Exception as exc:  # port adapters are owned elsewhere: never read as progress
            _LOG.warning("story_video_port_call_failed kind=%s", type(exc).__name__)
            return None

    def _close_compute(self, record: GenerationRecord) -> bool:
        """Release the reservation (nothing started) or settle it (the job had started)."""

        adapters = self._adapters
        if (
            adapters is None
            or record.compute_reservation_ref is None
            or record.compute_released_at is not None
        ):
            return False
        scope = VideoRequestScope(record.scope_kind, record.scope_ref)  # type: ignore[arg-type]
        if record.started and record.state != GenerationState.ADMISSION_REJECTED:
            acknowledgement = self._call(
                adapters.reservation.settle,
                scope=scope,
                reservation_ref=record.compute_reservation_ref,
                outcome=_settle_outcome(record),
                idempotency_key=record.key_hash,
            )
        else:
            acknowledgement = self._call(
                adapters.reservation.release,
                scope=scope,
                reservation_ref=record.compute_reservation_ref,
                idempotency_key=record.key_hash,
            )
        if acknowledgement is not AckStatus.DONE:
            return False  # kept: the reconciler asks again, a reservation is never lost
        self._repository.mark_compute_closed(record.generation_id)
        return True


def _settle_outcome(record: GenerationRecord) -> str:
    if record.state == GenerationState.READY:
        return "COMPLETED"
    if record.state == GenerationState.SAFETY_BLOCKED:
        return "SAFETY_BLOCKED"
    if record.state in {GenerationState.REJECTED_BY_ADULT, GenerationState.SUPERSEDED}:
        return "COMPLETED"  # the job ran to its end; the adult's choice is not a failure (T-1b)
    return "FAILED"


class StoryVideoAdmissionService(_Saga):
    def request(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        story_sha256: str,
        quality_reason_code: str | None,
        idempotency_key: str,
    ) -> AdmissionOutcome:
        intent = self._repository.begin_intent(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            story_sha256=story_sha256,
            quality_reason_code=quality_reason_code,
            idempotency_key=idempotency_key,
            adapters_available=self._adapters is not None,
        )
        if intent.projection is not None or intent.record is None:
            return AdmissionOutcome(None, intent.projection)
        record = intent.record
        if record.state == GenerationState.ADMISSION_PENDING:
            record = self.resolve(record)
        if record.state == GenerationState.ADMISSION_REJECTED:
            raise refusal_error(record.safe_failure_code)
        return AdmissionOutcome(record)

    def resolve(self, record: GenerationRecord) -> GenerationRecord:
        """Steps 2 and 3 for one pending intent; an unreadable answer leaves it pending."""

        adapters = self._adapters
        if adapters is None or record.state != GenerationState.ADMISSION_PENDING:
            return record
        scope = VideoRequestScope(record.scope_kind, record.scope_ref)  # type: ignore[arg-type]
        fingerprint = port_fingerprint(record)
        reservation = self._call(
            adapters.reservation.reserve,
            scope=scope,
            request_ref=record.generation_id,
            idempotency_key=record.key_hash,
            fingerprint=fingerprint,
        )
        if reservation is None or reservation.status is ReservationStatus.UNAVAILABLE:
            return record
        if reservation.status is ReservationStatus.RESERVED and not reservation.reservation_ref:
            _LOG.warning("story_video_port_answer_without_ref port=reservation")
            return record  # an answer that cannot be recorded is an unreadable answer
        if reservation.status is ReservationStatus.COST_LIMIT_REACHED:
            return self._refuse(record, AI_COST_LIMIT_REACHED, None)
        quota = self._call(
            adapters.quota.admit_video_request,
            scope=VideoRequestScope(
                record.scope_kind,
                record.scope_ref,
                record.teacher_account_id,
            ),  # type: ignore[arg-type]
            request_ref=record.generation_id,
            idempotency_key=record.key_hash,
            fingerprint=fingerprint,
            contract_version=QUOTA_CONTRACT_VERSION,
        )
        if quota is None or quota.status is QuotaStatus.UNAVAILABLE:
            return record
        if quota.status is QuotaStatus.IDEMPOTENCY_MISMATCH:
            # Draft 9 §9: the key was used with another payload; the intent stays for an operator.
            raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
        if quota.status is QuotaStatus.QUOTA_EXCEEDED:
            return self._refuse(record, VIDEO_QUOTA_EXCEEDED, reservation.reservation_ref)
        if quota.status in {
            QuotaStatus.QUOTA_ALLOCATION_NOT_FOUND,
            QuotaStatus.TEACHER_QUOTA_INSUFFICIENT,
            QuotaStatus.SCHOOL_QUOTA_INSUFFICIENT,
        }:
            return self._refuse(record, quota.status.value, reservation.reservation_ref)
        if quota.status is QuotaStatus.SUBSCRIPTION_RESTRICTED:
            return self._refuse(record, SUBSCRIPTION_RESTRICTED, reservation.reservation_ref)
        if quota.status is QuotaStatus.ACCEPTED and not quota.usage_ref:
            _LOG.warning("story_video_port_answer_without_ref port=quota")
            return record  # the reservation stays; the same key asks the quota again
        after = self._repository.finish_admission(
            record.generation_id,
            AdmissionDecision(True, reservation.reservation_ref, quota.usage_ref),
        )
        if after is None:
            return record
        if after.state == GenerationState.FAILED:
            # The run was cancelled while the ports were called: the admitted unit stays consumed
            # and nothing started, so the compute reservation is released (D4).
            self._close_compute(after)
        return after

    def _refuse(
        self, record: GenerationRecord, code: str, reservation_ref: str | None
    ) -> GenerationRecord:
        after = self._repository.finish_admission(
            record.generation_id, AdmissionDecision(False, reservation_ref, None, code)
        )
        if after is None:
            return record
        if after.state == GenerationState.ADMISSION_REJECTED:
            self._close_compute(after)
        return after

    def reconcile_pending_admissions(
        self, *, limit: int = 50, run_id: str | None = None
    ) -> ReconcileReport:
        """Ask the ports again, with the same key, for every pending intent (no scheduler yet).

        ``run_id`` narrows the pass to one run (an operator action or a test); a periodic runner
        passes none.
        """

        resolved = pending = mismatched = closed = 0
        for record in self._repository.pending_intents(limit, run_id):
            try:
                after = self.resolve(record)
            except ParentStoryRunError:
                mismatched += 1
                continue
            if after.state == GenerationState.ADMISSION_PENDING:
                pending += 1
            else:
                resolved += 1
        for record in self._repository.pending_compute_closures(limit):
            if self._close_compute(record):
                closed += 1
        return ReconcileReport(resolved, pending, mismatched, closed, self._sweep_cancelled(limit))

    def _sweep_cancelled(self, limit: int) -> int:
        """Fail the in-flight generations of runs already cancelled (a cancel hook that never ran).

        ``fail_for_cancelled_run`` is a compare-and-set under the run and generation locks, so the
        sweep is safe beside a live hook or worker; a row already settled is a recorded no-op.
        """

        settled = 0
        for record in self._repository.orphaned_in_flight(limit):
            result = self._repository.fail_for_cancelled_run(record.generation_id)
            if result.applied and result.record is not None:
                settled += 1
                self._close_compute(result.record)
        return settled


class StoryVideoCommandService:
    """The adult's two decisions on a ready video (T-1b; SRS l.1671-1672).

    Each command is one repository transaction under the run lock: it holds no port, quota or
    price logic. The compute reservation was settled when the video became ``READY``, so neither
    command calls a port.
    """

    def __init__(self, repository: StoryVideoRepository) -> None:
        self._repository = repository

    def mark_unsuitable(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        generation_id: str,
        reason_code: str,
        idempotency_key: str,
    ) -> RunCommandResult:
        if reason_code not in UNSUITABLE_REASON_CODES:
            raise ParentStoryRunError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "reason_code", "code": "INVALID_VALUE"}],
            )
        return self._repository.mark_unsuitable(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            generation_id=generation_id,
            reason_code=reason_code,
            idempotency_key=idempotency_key,
        )

    def complete(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> RunCommandResult:
        return self._repository.complete_run(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
        )


class StoryVideoProgressService(_Saga):
    """Moves one generation and its run together, and meets cancel (D4, D11)."""

    def __init__(
        self,
        repository: StoryVideoRepository,
        adapters: StoryVideoAdapters | None,
        *,
        call_timeout_seconds: float = DEFAULT_PORT_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(repository, adapters, call_timeout_seconds=call_timeout_seconds)
        self._admission = StoryVideoAdmissionService(
            repository, adapters, call_timeout_seconds=call_timeout_seconds
        )

    def apply(self, generation_id: str, event: ProgressEvent) -> ProgressResult:
        result = self._repository.advance(generation_id, event)
        record = result.record
        if (
            result.applied
            and record is not None
            and record.state
            in {GenerationState.READY, GenerationState.SAFETY_BLOCKED, GenerationState.FAILED}
        ):
            self._close_compute(record)
        return result

    def on_run_cancelled(self, run_id: str) -> None:
        """After the cancel commit, outside any transaction: resolve what the saga still owns.

        A pending intent is resolved by asking the ports again with the stored key (an admitted
        unit stays consumed and the generation ends ``FAILED`` with ``RUN_CANCELLED``, otherwise
        ``ADMISSION_REJECTED``); an in-flight generation ends ``FAILED(RUN_CANCELLED)``. An answer
        that cannot be read leaves the row for the reconciler, and the purge waits for it.
        """

        records = self._repository.open_generations(run_id)
        # In-flight rows first: they need no port answer, so a slow intent never delays them.
        pending = GenerationState.ADMISSION_PENDING
        for record in sorted(records, key=lambda item: item.state == pending):
            if record.state == GenerationState.ADMISSION_PENDING:
                try:
                    self._admission.resolve(record)
                except ParentStoryRunError:
                    continue
                continue
            result = self._repository.fail_for_cancelled_run(record.generation_id)
            if result.applied and result.record is not None:
                self._close_compute(result.record)


__all__ = [
    "DEFAULT_PORT_TIMEOUT_SECONDS",
    "AdmissionOutcome",
    "ReconcileReport",
    "StoryVideoAdmissionService",
    "StoryVideoCommandService",
    "StoryVideoProgressService",
    "refusal_error",
]
