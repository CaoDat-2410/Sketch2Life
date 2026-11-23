"""Inline job recorder over the caller's connection (FEAT-066 goal v3, T-3b, TD-15).

The job aggregate is built by the pure ``domain.ai_jobs`` functions (``create_job``,
``start_attempt``, ``succeed``) and written through ``SqlAiJobUnitOfWork.insert_job`` on the
connection of the caller's open transaction, so the job row and the lesson rows commit or roll
back together. It never commits, and it writes nothing else: no outbox row, no queue message, no
semantic request, no command receipt, no owner-fence hold (the fence port refuses every hold). A
finished job is not a candidate of any sweep: the reconciler selects queued attempts that were
dispatched, running attempts past their timeout and ``failed_retryable`` jobs, none of which a
job born ``succeeded`` can be.
"""

from __future__ import annotations

from sqlalchemy.engine import Connection

from sketch2life.application.ports.inline_jobs import InlineSucceededJob
from sketch2life.domain.ai_jobs.model import (
    JobRetryPolicy,
    JobScope,
    RequestRef,
    ResultDisposition,
    ResultRef,
    create_job,
    start_attempt,
    succeed,
)
from sketch2life.infrastructure.ai_jobs.read_only import ReadOnlyFenceHold
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobUnitOfWork

# A real production policy, not a BE2 fixture value: one attempt and no retry, so a job built
# here can never leave ``succeeded``. The distinct status keeps it apart from the ``PROPOSED``
# fixture policies (plan review R1 F-03 item 4).
INLINE_POLICY_STATUS = "INLINE_NO_RETRY"


def inline_retry_policy(policy_id: str, attempt_timeout_ms: int) -> JobRetryPolicy:
    return JobRetryPolicy(
        policy_id=policy_id,
        max_attempts=1,
        backoff_base_ms=0,
        backoff_multiplier=1,
        backoff_max_ms=0,
        attempt_timeout_ms=attempt_timeout_ms,
        status=INLINE_POLICY_STATUS,
    )


class SqlInlineJobRecorder:
    """``InlineJobRecorder`` writing on one SQLAlchemy connection (never commits)."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def record_succeeded(self, job: InlineSucceededJob) -> None:
        request_ref = RequestRef(
            request_id=job.request_id,
            request_revision=job.request_revision,
            input_hash=job.input_hash,
            context_revision=0,
        )
        created = create_job(
            job_id=job.job_id,
            attempt_id=job.attempt_id,
            job_type=job.job_type,
            scope=JobScope(
                organization_id=job.organization_id,
                session_id=None,
                subject_refs=(),
                purpose_code=job.purpose_code,
                target_id=job.target_id,
            ),
            request_ref=request_ref,
            correlation_id=job.correlation_id,
            retry_policy=inline_retry_policy(job.policy_id, job.attempt_timeout_ms),
            now=job.at,
        )
        running = start_attempt(created, job.attempt_id, job.at)
        finished = succeed(
            running,
            job.attempt_id,
            result_refs=(
                ResultRef(job.result_artifact_ref, job.result_sha256, job.result_provenance),
            ),
            disposition=ResultDisposition.ACCEPTED,
            now=job.at,
        )
        SqlAiJobUnitOfWork(self._connection, ReadOnlyFenceHold()).insert_job(finished)


__all__ = ["INLINE_POLICY_STATUS", "SqlInlineJobRecorder", "inline_retry_policy"]
