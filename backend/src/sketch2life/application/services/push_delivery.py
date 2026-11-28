"""Bounded application worker for push endpoint delivery (FEAT-066 goal v4, T-NTF1)."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sketch2life.application.ports.push_delivery import (
    PushDeliveryRecordResult,
    PushDeliveryStore,
    PushMessage,
    PushSenderPort,
    PushSendOutcome,
    PushSendResult,
)
from sketch2life.application.services.notification_templates import eligible_template_keys
from sketch2life.domain.push_delivery import ENROLL_WINDOW, push_pointer
from sketch2life.domain.story_run_reminder import require_aware_utc

DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 200
DEFAULT_CALL_TIMEOUT_SECONDS = 10.0
Clock = Callable[[], datetime]
_SENDER_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="push-delivery-sender")


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class PushDeliveryReport:
    enrolled: int = 0
    claimed: int = 0
    sent: int = 0
    retry: int = 0
    failed: int = 0
    dead_endpoint: int = 0
    skipped: int = 0

    def as_counts(self) -> dict[str, int]:
        return asdict(self)


class PushDeliveryWorker:
    """Enroll eligible inbox items and perform at most one bounded batch of sends."""

    def __init__(
        self,
        store: PushDeliveryStore,
        sender: PushSenderPort,
        *,
        clock: Clock = utc_now,
        call_timeout_seconds: float = DEFAULT_CALL_TIMEOUT_SECONDS,
    ) -> None:
        if call_timeout_seconds <= 0:
            raise ValueError("call_timeout_seconds must be positive")
        self._store = store
        self._sender = sender
        self._clock = clock
        self._timeout = call_timeout_seconds

    def run_once(
        self, now: datetime | None = None, batch: int = DEFAULT_BATCH_SIZE
    ) -> PushDeliveryReport:
        if type(batch) is not int or not 1 <= batch <= MAX_BATCH_SIZE:
            raise ValueError(f"batch must be between 1 and {MAX_BATCH_SIZE}")
        instant = require_aware_utc(self._clock() if now is None else now, field="now")
        eligible = eligible_template_keys()
        enrolled = self._store.enroll(
            now=instant,
            limit=batch,
            eligible_templates=eligible,
            window=ENROLL_WINDOW,
        )
        claimed = sent = retry = failed = dead_endpoint = skipped = 0
        for _ in range(batch):
            claim_result = self._store.claim_due(now=instant, eligible_templates=eligible)
            if claim_result.failed:
                failed += 1
                continue
            if claim_result.skipped:
                skipped += 1
                continue
            claim = claim_result.claim
            if claim is None:
                break
            claimed += 1
            message = PushMessage(
                delivery_id=claim.delivery_id,
                push_endpoint_id=claim.push_endpoint_id,
                endpoint_ciphertext=claim.endpoint_ciphertext,
                payload=push_pointer(claim.inbox_item_id),
            )
            result = self._call_sender(message)
            recorded = self._store.record_outcome(claim=claim, result=result, now=instant)
            if recorded is PushDeliveryRecordResult.SENT:
                sent += 1
            elif recorded is PushDeliveryRecordResult.RETRY:
                retry += 1
            elif recorded is PushDeliveryRecordResult.FAILED:
                failed += 1
            elif recorded is PushDeliveryRecordResult.DEAD_ENDPOINT:
                dead_endpoint += 1
        return PushDeliveryReport(
            enrolled=enrolled,
            claimed=claimed,
            sent=sent,
            retry=retry,
            failed=failed,
            dead_endpoint=dead_endpoint,
            skipped=skipped,
        )

    def _call_sender(self, message: PushMessage) -> PushSendResult:
        future = _SENDER_EXECUTOR.submit(self._sender.send, message)
        try:
            result = future.result(timeout=self._timeout)
        except FutureTimeoutError:
            future.cancel()
            return PushSendResult(PushSendOutcome.TIMEOUT)
        except Exception:
            return PushSendResult(PushSendOutcome.SENDER_ERROR)
        if not isinstance(result, PushSendResult):
            return PushSendResult(PushSendOutcome.SENDER_ERROR)
        if not isinstance(result.outcome, PushSendOutcome):
            return PushSendResult(PushSendOutcome.SENDER_ERROR)
        return result


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_CALL_TIMEOUT_SECONDS",
    "MAX_BATCH_SIZE",
    "PushDeliveryReport",
    "PushDeliveryWorker",
    "utc_now",
]
