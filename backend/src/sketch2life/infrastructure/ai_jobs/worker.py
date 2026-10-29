"""Worker loop for BE2-01 Phase B batch B5 test processes (plan Δ14, accepted Q6).

``DispatchWorker.handle`` takes one transient ``WorkerDispatchEnvelope``: durable start first,
then a progress stage, the (fake) provider and the completion, all with the envelope's
attempt-bound capability. A duplicate or settled delivery never reaches the provider. A
provider exception produces no completion claim; the attempt then times out and the approved
policy retry takes over (no claim journal, no exactly-once provider execution, no invented
fingerprint). Not wired into the live app; production wiring belongs to INTG-02.

``CapabilityRedactionFilter`` keeps capabilities out of log records: it drops RQ's structured
``arguments``/``kwargs`` extras and scrubs capability-shaped text (also malformed forms and objects
rendered as text) from messages, arguments, other extras
and exception text before any handler formats the record.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from typing import Any

from sketch2life.application.ports.ai_jobs import (
    AiProviderPort,
    CompletionReceipt,
    WorkerDispatchEnvelope,
)
from sketch2life.application.services.ai_jobs import AiJobError, AiJobService
from sketch2life.domain.ai_jobs.model import JobProgress, ProgressKind
from sketch2life.infrastructure.ai_jobs.typed_dispatch import (
    TypedDispatchRouter,
    VideoDispatchOutcome,
    VideoDispatchTarget,
)
from sketch2life.infrastructure.ai_jobs.worker_capability import CAPABILITY_PATTERN

STARTED_PROGRESS = JobProgress(ProgressKind.STAGES, None, "provider_running")
REDACTED = "<redacted>"
# Structured extras RQ attaches to failure records (``job.args``/``job.kwargs``).
_ARGUMENT_EXTRAS = ("arguments", "kwargs")
# Attributes every LogRecord has; anything else is a caller-supplied extra (B5-R02).
_STANDARD_ATTRIBUTES = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime"}

_log = logging.getLogger("sketch2life.ai_jobs.worker")


@dataclass(frozen=True, slots=True)
class WorkerOutcome:
    """``completed`` | ``not_started`` | ``rejected`` | ``provider_failed``; codes only."""

    status: str
    reason_code: str | None
    receipt: CompletionReceipt | None = None


class DispatchWorker:
    def __init__(
        self,
        service: AiJobService,
        provider: AiProviderPort,
        *,
        video_job_type: str | None = None,
        video_worker: VideoDispatchTarget | None = None,
        provider_job_types: frozenset[str] = frozenset({"sketch_assistance"}),
    ) -> None:
        self._service = service
        self._provider = provider
        self._router = TypedDispatchRouter(
            provider_job_types=provider_job_types,
            video_job_type=video_job_type,
            video_target=video_worker,
        )

    def handle(self, envelope: WorkerDispatchEnvelope) -> WorkerOutcome | VideoDispatchOutcome:
        message, capability = envelope.message, envelope.capability
        route = self._router.resolve(message.job_type)
        if route.kind == "video":
            if route.video_target is None:
                return WorkerOutcome("rejected", "VIDEO_ROUTE_UNAVAILABLE")
            return route.video_target.handle(envelope)
        if route.kind == "unsupported":
            return WorkerOutcome("rejected", "UNSUPPORTED_JOB_TYPE")
        try:
            started = self._service.start_attempt(capability, message.job_id, message.attempt_id)
        except AiJobError as error:
            return WorkerOutcome("rejected", error.code)
        if not started.started:
            return WorkerOutcome("not_started", started.reason_code)
        try:
            self._service.report_progress(capability, message.job_id, message.attempt_id,
                                          STARTED_PROGRESS)
        except AiJobError as error:
            return WorkerOutcome("rejected", error.code)
        try:
            claim = self._provider.run(message)
        except Exception:
            # No claim exists, so none is invented; the overdue sweep recovers the attempt.
            return WorkerOutcome("provider_failed", "PROVIDER_ERROR")
        try:
            receipt = self._service.accept_completion(capability, claim)
        except AiJobError as error:
            return WorkerOutcome("rejected", error.code)
        return WorkerOutcome("completed", receipt.reason_code, receipt)


_installed: DispatchWorker | None = None


def install_worker(worker: DispatchWorker | None) -> None:
    """Bind the process's worker (test entry modules only); ``None`` unbinds it."""

    global _installed
    _installed = worker


def installed_worker() -> DispatchWorker | None:
    return _installed


def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        return CAPABILITY_PATTERN.sub(REDACTED, value)
    if isinstance(value, tuple):
        return tuple(_scrub(item) for item in value)
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, dict):
        return {_scrub(key): _scrub(item) for key, item in value.items()}
    if value is None or isinstance(value, bool | int | float):
        return value
    # Any other object would be rendered with str() by the formatter (e.g. an exception or
    # envelope); render it now so a capability inside it is scrubbed too (B5-R02).
    return CAPABILITY_PATTERN.sub(REDACTED, str(value))


class CapabilityRedactionFilter(logging.Filter):
    """Redact worker capabilities from a record before it is formatted or handled."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Interpolate first: scrubbing a template can remove its placeholders, and a token
        # may itself span the template and arguments. Do not retain the original arguments.
        record.msg = _scrub(record.getMessage())
        record.args = ()
        for name, value in list(record.__dict__.items()):
            if name in _ARGUMENT_EXTRAS:
                record.__dict__[name] = REDACTED
            elif name not in _STANDARD_ATTRIBUTES:
                record.__dict__[name] = _scrub(value)  # any other extra (B5-R02)
        if record.exc_info:
            record.exc_text = _scrub("".join(traceback.format_exception(*record.exc_info)))
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = _scrub(record.exc_text)
        if record.stack_info:
            record.stack_info = _scrub(record.stack_info)
        return True


def install_log_redaction(*logger_names: str) -> CapabilityRedactionFilter:
    """Attach one redaction filter to each named logger (idempotent per logger)."""

    redaction = CapabilityRedactionFilter()
    for name in logger_names:
        target = logging.getLogger(name)
        if not any(isinstance(f, CapabilityRedactionFilter) for f in target.filters):
            target.addFilter(redaction)
    return redaction


__all__ = [
    "REDACTED",
    "STARTED_PROGRESS",
    "CapabilityRedactionFilter",
    "DispatchWorker",
    "WorkerOutcome",
    "install_log_redaction",
    "install_worker",
    "installed_worker",
]
