"""Read-only SQL job repository for ``GET /v1/jobs/{job_id}`` (FEAT-066 T0.4).

``SqlAiJobRepository`` needs an owner-fence factory because its units of work can write. The
status route only calls ``get_job``; its fence port refuses every hold, so a write path reached
by mistake fails closed instead of mutating state (B-12: there is no production owner-fence
binding yet).
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.engine import Connection

from sketch2life.application.ports.ai_jobs import OWNER_FENCE_CONTRACT, FenceResult, OwnerFence
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository


class ReadOnlyFenceHold:
    """``OwnerFencePort`` that never holds a fence."""

    contract_version = OWNER_FENCE_CONTRACT

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        raise RuntimeError("the job status reader is read-only and never holds owner fences")


def _read_only_fences(_connection: Connection) -> ReadOnlyFenceHold:
    return ReadOnlyFenceHold()


def build_read_only_job_repository(engine: Engine) -> SqlAiJobRepository:
    """SQL job repository whose transactions can read but never hold an owner fence."""

    return SqlAiJobRepository(engine, _read_only_fences)


__all__ = ["ReadOnlyFenceHold", "build_read_only_job_repository"]
