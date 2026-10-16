"""Read-only BE2-01 job lineage for BE2-02 (consumes the foundation, never rewrites it).

Wraps any ``AiJobRepository`` (the BE2-01 fake or SQL adapter) and maps the pinned job/attempt
request reference and its ownership ``JobScope`` (session, subjects, purpose, target) to a
``JobLineageView``. It opens a unit of work only to read one job and never calls a mutating
unit-of-work method.
"""

from __future__ import annotations

from sketch2life.application.ports.ai_jobs import AiJobRepository
from sketch2life.domain.vision_analysis import JobLineageView


class AiJobRepositoryLineage:
    def __init__(self, repository: AiJobRepository) -> None:
        self._repository = repository

    def get(self, job_id: str) -> JobLineageView | None:
        with self._repository.transaction() as tx:
            job = tx.get_job(job_id)
        if job is None:
            return None
        pinned = job.active_attempt.request_ref
        return JobLineageView(
            job_id=job.job_id,
            organization_id=job.organization_id,
            job_type=job.job_type,
            state=job.state,
            active_attempt_id=job.active_attempt.attempt_id,
            request_id=pinned.request_id,
            request_revision=pinned.request_revision,
            input_hash=pinned.input_hash,
            context_revision=pinned.context_revision,
            session_id=job.scope.session_id,
            subject_refs=job.scope.subject_refs,
            purpose_code=job.scope.purpose_code,
            target_id=job.scope.target_id,
        )


__all__ = ["AiJobRepositoryLineage"]
