"""SQL repository / unit of work for BE2-01 Phase B batch B3 (plan revision 3 §5 Δ2/Δ4/Δ5).

One use-case transaction = one PostgreSQL connection at READ COMMITTED. Writes are plain
INSERTs: a unique violation raises ``UniqueConflict(kind)`` and the whole transaction rolls
back (never ``ON CONFLICT DO NOTHING``). ``cas_job`` updates only when ``job_revision`` still
matches. Owner fences are held through an ``OwnerFencePort`` bound to the same connection, so
the hold lasts until this transaction commits or rolls back (ADR-0018 D4/D7).

Batch boundary: dispatch/notice methods that B4/B5 replace (lease-fenced outbox claim,
atomic notices) raise ``NotImplementedError`` here instead of guessing their semantics.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Connection, Engine, func, insert, null, select, update
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.ai_jobs import (
    OWNER_FENCE_CONTRACT,
    AuditEvent,
    CommandReceipt,
    CommandScopeKey,
    CompletionReceipt,
    DispatchMessage,
    FenceResult,
    JobRevisionConflict,
    OwnerFence,
    OwnerFencePort,
    SemanticRequestKey,
    UniqueConflict,
)
from sketch2life.domain.ai_jobs.model import (
    AiJob,
    Attempt,
    JobFailure,
    JobProgress,
    JobRetryPolicy,
    JobScope,
    JobState,
    ProgressKind,
    RequestRef,
    ResultDisposition,
    ResultRef,
)
from sketch2life.infrastructure.ai_jobs.sql import tables as t

UNIQUE_VIOLATION = "23505"
# Unique/primary-key constraint name -> UniqueConflict.kind.
_CONFLICT_KINDS = {
    "pk_job": "job",
    "pk_attempt": "attempt",
    "uq_attempt_job_id_attempt_number": "attempt",
    "pk_command_receipt": "command_receipt",
    "pk_semantic_request": "semantic_request",
    "pk_completion_receipt": "completion_receipt",
    "uq_completion_receipt_receipt_id": "completion_receipt",
    "pk_cancellation_notice": "cancellation_notice",
    "pk_outbox": "outbox",
    "uq_outbox_event_id": "outbox",
}

OwnerFenceFactory = Callable[[Connection], OwnerFencePort]


def _conflict_kind(error: IntegrityError) -> str | None:
    original = error.orig
    if getattr(original, "sqlstate", None) != UNIQUE_VIOLATION:
        return None
    diag = getattr(original, "diag", None)
    name = getattr(diag, "constraint_name", None)
    return _CONFLICT_KINDS.get(str(name), "unknown")


# --------------------------------------------------------------------------- row mapping
def _request_ref_json(ref: RequestRef) -> dict[str, Any]:
    return {
        "request_id": ref.request_id,
        "request_revision": ref.request_revision,
        "input_hash": ref.input_hash,
        "context_revision": ref.context_revision,
    }


def _request_ref(value: dict[str, Any]) -> RequestRef:
    return RequestRef(
        value["request_id"],
        value["request_revision"],
        value["input_hash"],
        value["context_revision"],
    )


def _policy_json(policy: JobRetryPolicy) -> dict[str, Any]:
    return {
        "policy_id": policy.policy_id,
        "max_attempts": policy.max_attempts,
        "backoff_base_ms": policy.backoff_base_ms,
        "backoff_multiplier": policy.backoff_multiplier,
        "backoff_max_ms": policy.backoff_max_ms,
        "attempt_timeout_ms": policy.attempt_timeout_ms,
        "status": policy.status,
    }


def _job_values(job: AiJob) -> dict[str, Any]:
    """Mutable and immutable job columns, excluding the fence bookkeeping column."""

    # SQL NULL, not JSON null: the CHECK allows only NULL or an object.
    failure: Any = null()
    if job.failure is not None:
        failure = {
            "code": job.failure.code,
            "retryable": job.failure.retryable,
            "public_message": job.failure.public_message,
            "attempts_remaining": job.failure.attempts_remaining,
        }
    return {
        "job_id": job.job_id,
        "organization_id": job.organization_id,
        "job_type": job.job_type,
        "job_revision": job.job_revision,
        "state": str(job.state),
        "session_id": job.scope.session_id,
        "subject_refs": list(job.scope.subject_refs),
        "purpose_code": job.scope.purpose_code,
        "target_id": job.scope.target_id,
        "request_ref": _request_ref_json(job.request_ref),
        "correlation_id": job.correlation_id,
        "policy_snapshot_id": job.retry_policy.policy_id,
        "policy_snapshot": _policy_json(job.retry_policy),
        "progress": {
            "kind": str(job.progress.kind),
            "value": job.progress.value,
            "stage_label": job.progress.stage_label,
        },
        "result_disposition": (
            str(job.result_disposition) if job.result_disposition is not None else None
        ),
        "result_refs": [
            {"artifact_ref": r.artifact_ref, "sha256": r.sha256, "provenance": r.provenance}
            for r in job.result_refs
        ],
        "failure": failure,
        "retry_not_before": job.retry_not_before,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "lineage_note": job.lineage_note,
        "history": list(job.history),
    }


def _attempt_values(job_id: str, attempt: Attempt) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "job_id": job_id,
        "attempt_number": attempt.attempt_number,
        "request_ref": _request_ref_json(attempt.request_ref),
        "created_at": attempt.created_at,
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "outcome": attempt.outcome,
    }


def _job_from_rows(row: Any, attempt_rows: list[Any]) -> AiJob:
    policy = row.policy_snapshot
    failure = row.failure
    progress = row.progress
    return AiJob(
        job_id=row.job_id,
        job_type=row.job_type,
        scope=JobScope(
            organization_id=row.organization_id,
            session_id=row.session_id,
            subject_refs=tuple(row.subject_refs),
            purpose_code=row.purpose_code,
            target_id=row.target_id,
        ),
        job_revision=row.job_revision,
        request_ref=_request_ref(row.request_ref),
        attempts=tuple(
            Attempt(
                attempt_id=a.attempt_id,
                attempt_number=a.attempt_number,
                request_ref=_request_ref(a.request_ref),
                created_at=a.created_at,
                started_at=a.started_at,
                finished_at=a.finished_at,
                outcome=a.outcome,
            )
            for a in attempt_rows
        ),
        state=JobState(row.state),
        correlation_id=row.correlation_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        retry_policy=JobRetryPolicy(
            policy_id=policy["policy_id"],
            max_attempts=policy["max_attempts"],
            backoff_base_ms=policy["backoff_base_ms"],
            backoff_multiplier=policy["backoff_multiplier"],
            backoff_max_ms=policy["backoff_max_ms"],
            attempt_timeout_ms=policy["attempt_timeout_ms"],
            status=policy["status"],
        ),
        progress=JobProgress(
            ProgressKind(progress["kind"]), progress["value"], progress["stage_label"]
        ),
        result_disposition=(
            ResultDisposition(row.result_disposition) if row.result_disposition else None
        ),
        result_refs=tuple(
            ResultRef(r["artifact_ref"], r["sha256"], r["provenance"]) for r in row.result_refs
        ),
        failure=(
            JobFailure(
                failure["code"],
                failure["retryable"],
                failure["public_message"],
                failure["attempts_remaining"],
            )
            if failure is not None
            else None
        ),
        retry_not_before=row.retry_not_before,
        completed_at=row.completed_at,
        lineage_note=row.lineage_note,
        history=tuple(row.history),
    )


# --------------------------------------------------------------------------- unit of work
class SqlAiJobUnitOfWork:
    """``AiJobUnitOfWork`` over one connection inside one open transaction."""

    def __init__(self, connection: Connection, owner_fences: OwnerFencePort) -> None:
        self.connection = connection
        self._owner_fences = owner_fences
        self._held: dict[str, int] = {}
        self.writes = 0

    # jobs -----------------------------------------------------------------------------------
    def get_job(self, job_id: str, *, for_update: bool = False) -> AiJob | None:
        query = select(t.job).where(t.job.c.job_id == job_id)
        if for_update:
            query = query.with_for_update()
        row = self.connection.execute(query).one_or_none()
        if row is None:
            return None
        attempts = self.connection.execute(
            select(t.attempt)
            .where(t.attempt.c.job_id == job_id)
            .order_by(t.attempt.c.attempt_number)
        ).all()
        return _job_from_rows(row, list(attempts))

    def insert_job(self, job: AiJob) -> None:
        values = _job_values(job)
        values["accepted_fences"] = dict(self._held)
        self._insert(insert(t.job).values(**values))
        for attempt in job.attempts:
            self._insert(insert(t.attempt).values(**_attempt_values(job.job_id, attempt)))

    def cas_job(self, *, expected_revision: int, job: AiJob) -> None:
        if job.job_revision <= expected_revision:
            raise JobRevisionConflict("replacement must advance job_revision")
        values = _job_values(job)
        for immutable in (
            "job_id",
            "organization_id",
            "job_type",
            "session_id",
            "subject_refs",
            "purpose_code",
            "target_id",
            "request_ref",
            "correlation_id",
            "created_at",
        ):
            values.pop(immutable)
        if self._held:
            values["accepted_fences"] = dict(self._held)
        changed = self.connection.execute(
            update(t.job)
            .where(t.job.c.job_id == job.job_id, t.job.c.job_revision == expected_revision)
            .values(**values)
        ).rowcount
        if changed != 1:
            raise JobRevisionConflict("job revision moved")
        self.writes += 1
        known = set(
            self.connection.execute(
                select(t.attempt.c.attempt_id).where(t.attempt.c.job_id == job.job_id)
            ).scalars()
        )
        for attempt in job.attempts:
            if attempt.attempt_id in known:
                # Domain fields only; B4 dispatch bookkeeping columns are never overwritten.
                self.connection.execute(
                    update(t.attempt)
                    .where(t.attempt.c.attempt_id == attempt.attempt_id)
                    .values(
                        started_at=attempt.started_at,
                        finished_at=attempt.finished_at,
                        outcome=attempt.outcome,
                    )
                )
            else:
                self._insert(insert(t.attempt).values(**_attempt_values(job.job_id, attempt)))

    def list_jobs(self) -> tuple[AiJob, ...]:
        ids = self.connection.execute(select(t.job.c.job_id).order_by(t.job.c.job_id)).scalars()
        return tuple(job for job_id in list(ids) if (job := self.get_job(job_id)) is not None)

    # receipts -------------------------------------------------------------------------------
    def get_command_receipt(self, key: CommandScopeKey) -> CommandReceipt | None:
        c = t.command_receipt.c
        row = self.connection.execute(
            select(t.command_receipt).where(
                c.organization_id == key.organization_id,
                c.principal_id == key.principal_id,
                c.contract_name == key.contract_name,
                c.target_id == key.target_id,
                c.idempotency_key == key.idempotency_key,
            )
        ).one_or_none()
        if row is None:
            return None
        return CommandReceipt(
            key,
            row.fingerprint,
            row.job_id,
            row.outcome,
            row.job_revision_at_commit,
            row.recorded_at,
        )

    def put_command_receipt(self, receipt: CommandReceipt) -> None:
        key = receipt.scope_key
        self._insert(
            insert(t.command_receipt).values(
                organization_id=key.organization_id,
                principal_id=key.principal_id,
                contract_name=key.contract_name,
                target_id=key.target_id,
                idempotency_key=key.idempotency_key,
                fingerprint=receipt.fingerprint,
                job_id=receipt.job_id,
                outcome=receipt.outcome,
                job_revision_at_commit=receipt.job_revision_at_commit,
                recorded_at=receipt.recorded_at,
            )
        )

    def find_semantic(self, key: SemanticRequestKey) -> str | None:
        found: str | None = self.connection.execute(
            select(t.semantic_request.c.job_id).where(
                t.semantic_request.c.semantic_key_sha256 == key.sha256()
            )
        ).scalar_one_or_none()
        return found

    def put_semantic(self, key: SemanticRequestKey, job_id: str) -> None:
        self._insert(
            insert(t.semantic_request).values(
                semantic_key_sha256=key.sha256(),
                organization_id=key.organization_id,
                job_type=key.job_type,
                request_id=key.request_id,
                request_revision=key.request_revision,
                input_hash=key.input_hash,
                context_revision=key.context_revision,
                target_id=key.target_id,
                purpose_code=key.purpose_code,
                session_id=key.session_id,
                subject_refs=list(key.subject_refs),
                job_id=job_id,
                created_at=func.now(),
            )
        )

    def get_completion_receipt(self, job_id: str, attempt_id: str) -> CompletionReceipt | None:
        c = t.completion_receipt.c
        row = self.connection.execute(
            select(t.completion_receipt).where(c.job_id == job_id, c.attempt_id == attempt_id)
        ).one_or_none()
        if row is None:
            return None
        return CompletionReceipt(
            receipt_id=row.receipt_id,
            job_id=row.job_id,
            attempt_id=row.attempt_id,
            fingerprint=row.fingerprint,
            disposition=ResultDisposition(row.disposition),
            reason_code=row.reason_code,
            job_revision_after=row.job_revision_after,
            recorded_at=row.recorded_at,
            authoritative=True,
        )

    def put_completion_receipt(self, receipt: CompletionReceipt) -> None:
        if not receipt.authoritative:
            raise ValueError("only authoritative completion receipts are stored")
        self._insert(
            insert(t.completion_receipt).values(
                job_id=receipt.job_id,
                attempt_id=receipt.attempt_id,
                receipt_id=receipt.receipt_id,
                fingerprint=receipt.fingerprint,
                disposition=str(receipt.disposition),
                reason_code=receipt.reason_code,
                job_revision_after=receipt.job_revision_after,
                recorded_at=receipt.recorded_at,
            )
        )

    # owner fence ----------------------------------------------------------------------------
    def hold_owner_fences(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        result = self._owner_fences.hold(fences)
        if result.current:
            self._held.update({fence.fence_scope: fence.epoch for fence in fences})
        return result

    # outbox ---------------------------------------------------------------------------------
    def add_outbox(self, message: DispatchMessage) -> None:
        organization_id = self.connection.execute(
            select(t.job.c.organization_id).where(t.job.c.job_id == message.job_id)
        ).scalar_one()
        self._insert(
            insert(t.outbox).values(
                message_id=message.message_id,
                kind="dispatch",
                event_id=None,
                organization_id=organization_id,
                job_id=message.job_id,
                attempt_id=message.attempt_id,
                payload={
                    "attempt_number": message.attempt_number,
                    "job_type": message.job_type,
                    "request_ref": _request_ref_json(message.request_ref),
                },
                available_at=func.now(),
                created_at=func.now(),
            )
        )

    def add_audit_intent(self, event_id: str, event: AuditEvent) -> None:
        self._insert(
            insert(t.outbox).values(
                message_id=f"aud_{event_id}",
                kind="audit",
                event_id=event_id,
                organization_id=event.organization_id,
                job_id=event.job_id,
                attempt_id=None,
                payload={
                    "event_type": event.event_type,
                    "correlation_id": event.correlation_id,
                    "reason_code": event.reason_code,
                    "details": dict(event.details),
                },
                available_at=func.now(),
                created_at=func.now(),
            )
        )

    def pending_outbox(self) -> tuple[DispatchMessage, ...]:
        raise NotImplementedError("lease-fenced outbox claim is Phase B batch B4 (Δ6)")

    def mark_dispatched(self, message_id: str) -> None:
        raise NotImplementedError("fenced dispatch acknowledgement is Phase B batch B4 (Δ6)")

    def notice_seen(self, notice_id: str) -> bool:
        raise NotImplementedError("atomic cancellation notices are Phase B batch B5 (Δ10)")

    def record_notice(self, notice_id: str) -> None:
        raise NotImplementedError("atomic cancellation notices are Phase B batch B5 (Δ10)")

    # helpers --------------------------------------------------------------------------------
    def _insert(self, statement: Any) -> None:
        try:
            self.connection.execute(statement)
            self.writes += 1
        except IntegrityError as error:
            kind = _conflict_kind(error)
            if kind is None:
                raise
            raise UniqueConflict(kind) from None


class SqlAiJobRepository:
    """``AiJobRepository`` over a SQLAlchemy engine.

    ``owner_fences`` binds the owner fence implementation to each transaction's connection;
    there is no production binding until the real P2 adapter exists (B-12). ``on_transaction``
    and ``before_commit`` are synthetic fault/barrier hooks used only by tests.
    """

    def __init__(
        self,
        engine: Engine,
        owner_fences: OwnerFenceFactory,
        *,
        on_transaction: Callable[[int], None] | None = None,
        before_commit: Callable[[SqlAiJobUnitOfWork], None] | None = None,
    ) -> None:
        self._engine = engine
        self._owner_fences = owner_fences
        self._on_transaction = on_transaction
        self._before_commit = before_commit
        self.transactions = 0

    @contextmanager
    def transaction(self) -> Iterator[SqlAiJobUnitOfWork]:
        self.transactions += 1
        if self._on_transaction is not None:
            self._on_transaction(self.transactions)
        with self._engine.connect() as connection:
            connection.execution_options(isolation_level="READ COMMITTED")
            with connection.begin():
                fences = self._owner_fences(connection)
                if fences.contract_version != OWNER_FENCE_CONTRACT:
                    raise RuntimeError("unsupported owner fence contract version")
                uow = SqlAiJobUnitOfWork(connection, fences)
                yield uow
                if self._before_commit is not None:
                    self._before_commit(uow)


__all__ = [
    "UNIQUE_VIOLATION",
    "OwnerFenceFactory",
    "SqlAiJobRepository",
    "SqlAiJobUnitOfWork",
]
