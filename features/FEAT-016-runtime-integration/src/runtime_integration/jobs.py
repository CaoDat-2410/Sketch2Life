"""Local job adapter with version and idempotency semantics."""
from __future__ import annotations

from dataclasses import replace

from .contracts import ArtifactRef, JobSnapshot, RuntimeRejected


class LocalJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobSnapshot] = {}

    def create(self, job_id: str, session_id: str, session_version: int) -> JobSnapshot:
        existing = self._jobs.get(job_id)
        if existing is not None:
            return existing
        job = JobSnapshot(job_id, session_id, "QUEUED", session_version)
        self._jobs[job_id] = job
        return job

    def poll(self, job_id: str) -> JobSnapshot:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise RuntimeRejected("JOB_NOT_FOUND") from exc

    def complete(self, job_id: str, *, session_version: int, result_artifact: ArtifactRef | None = None, error_code: str | None = None) -> JobSnapshot:
        job = self.poll(job_id)
        if job.status in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return job
        if session_version != job.session_version:
            raise RuntimeRejected("STALE_JOB_COMPLETION")
        status = "SUCCEEDED" if result_artifact is not None else "FAILED"
        updated = replace(job, status=status, result_artifact=result_artifact, error_code=error_code)
        self._jobs[job_id] = updated
        return updated

    def cancel(self, job_id: str, *, session_version: int) -> JobSnapshot:
        job = self.poll(job_id)
        if job.status in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return job
        if session_version != job.session_version:
            raise RuntimeRejected("STALE_JOB_CANCELLATION")
        updated = replace(job, status="CANCELLED")
        self._jobs[job_id] = updated
        return updated
