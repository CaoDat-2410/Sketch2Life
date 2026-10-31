"""Single-use, durable invocation ledger for the synthetic vision pilot."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Connection, Engine, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from sketch2life.infrastructure.vision_analysis import tables

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class InvocationState(StrEnum):
    CLAIMED = "CLAIMED"
    SENT = "SENT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class InvocationRecord:
    run_id: str
    job_id: str
    attempt_id: str
    organization_id: str
    state: InvocationState
    claimed_at: datetime
    sent_at: datetime | None
    finished_at: datetime | None
    result_sha256: str | None


class InvocationLedger:
    """No transition reopens a run or permits a second claim for the same attempt."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @staticmethod
    def _identity(
        run_id: str, job_id: str, attempt_id: str, organization_id: str
    ) -> dict[str, str]:
        values = {
            "run_id": run_id,
            "job_id": job_id,
            "attempt_id": attempt_id,
            "organization_id": organization_id,
        }
        if any(not isinstance(value, str) or not value for value in values.values()):
            raise ValueError("invocation identity fields are required")
        return values

    @staticmethod
    def _require_postgresql(connection: Connection) -> None:
        if connection.dialect.name != "postgresql":
            raise RuntimeError("PostgreSQL is required for the invocation ledger")

    def claim(self, *, run_id: str, job_id: str, attempt_id: str, organization_id: str) -> bool:
        identity = self._identity(run_id, job_id, attempt_id, organization_id)
        with self._engine.begin() as connection:
            self._require_postgresql(connection)
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                {"scope": "feat064-pilot:" + organization_id},
            )
            statement = (
                pg_insert(tables.invocations)
                .values(
                    **identity, state=InvocationState.CLAIMED.value, claimed_at=datetime.now(UTC)
                )
                .on_conflict_do_nothing()
                .returning(tables.invocations.c.run_id)
            )
            return connection.execute(statement).scalar_one_or_none() is not None

    def mark_sent(self, *, run_id: str, job_id: str, attempt_id: str, organization_id: str) -> bool:
        self._identity(run_id, job_id, attempt_id, organization_id)
        with self._engine.begin() as connection:
            self._require_postgresql(connection)
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                {"scope": "feat064-pilot:" + organization_id},
            )
            result = connection.execute(
                update(tables.invocations)
                .where(
                    tables.invocations.c.run_id == run_id,
                    tables.invocations.c.job_id == job_id,
                    tables.invocations.c.attempt_id == attempt_id,
                    tables.invocations.c.organization_id == organization_id,
                    tables.invocations.c.state == InvocationState.CLAIMED.value,
                )
                .values(state=InvocationState.SENT.value, sent_at=datetime.now(UTC))
            )
            return result.rowcount == 1

    def complete(
        self,
        *,
        run_id: str,
        job_id: str,
        attempt_id: str,
        organization_id: str,
        state: str,
        result_sha256: str | None = None,
    ) -> bool:
        self._identity(run_id, job_id, attempt_id, organization_id)
        if state not in {
            InvocationState.SUCCEEDED.value,
            InvocationState.FAILED.value,
            InvocationState.UNKNOWN.value,
        }:
            raise ValueError("completion state must be terminal")
        if result_sha256 is not None and not _SHA256.fullmatch(result_sha256):
            raise ValueError("result_sha256 must be lowercase SHA-256")
        with self._engine.begin() as connection:
            self._require_postgresql(connection)
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                {"scope": "feat064-pilot:" + organization_id},
            )
            result = connection.execute(
                update(tables.invocations)
                .where(
                    tables.invocations.c.run_id == run_id,
                    tables.invocations.c.job_id == job_id,
                    tables.invocations.c.attempt_id == attempt_id,
                    tables.invocations.c.organization_id == organization_id,
                    tables.invocations.c.state == InvocationState.SENT.value,
                )
                .values(state=state, finished_at=datetime.now(UTC), result_sha256=result_sha256)
            )
            return result.rowcount == 1

    def get(self, run_id: str) -> InvocationRecord | None:
        with self._engine.connect() as connection:
            self._require_postgresql(connection)
            row = (
                connection.execute(
                    select(tables.invocations).where(tables.invocations.c.run_id == run_id)
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return None
        return InvocationRecord(
            run_id=row["run_id"],
            job_id=row["job_id"],
            attempt_id=row["attempt_id"],
            organization_id=row["organization_id"],
            state=InvocationState(row["state"]),
            claimed_at=row["claimed_at"],
            sent_at=row["sent_at"],
            finished_at=row["finished_at"],
            result_sha256=row["result_sha256"],
        )


__all__ = ["InvocationLedger", "InvocationRecord", "InvocationState"]
