"""Process-local job state for the illustrated story-video pipeline."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from sketch2life.application.services.story_video_pipeline import (
    StoryVideoPipeline,
    StoryVideoProviderError,
    StoryVideoRun,
)
from sketch2life.contracts.schemas.story_video import ApprovedStoryPackageV1, StoryScriptSegmentV1
from sketch2life.contracts.schemas.story_video_media import VideoJobStatusV1


class StoryVideoJobService:
    def __init__(
        self,
        *,
        pipeline: StoryVideoPipeline | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._pipeline = pipeline
        self._now = now
        self._lock = RLock()
        self._jobs: dict[str, VideoJobStatusV1] = {}
        self._inputs: dict[
            str, tuple[ApprovedStoryPackageV1, tuple[StoryScriptSegmentV1, ...]]
        ] = {}
        self._runs: dict[str, StoryVideoRun] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}

    @property
    def can_run(self) -> bool:
        return self._pipeline is not None

    def create_or_replay(
        self,
        *,
        session_id: str,
        idempotency_key: str,
        package: ApprovedStoryPackageV1,
        segments: tuple[StoryScriptSegmentV1, ...],
    ) -> tuple[VideoJobStatusV1, bool]:
        if package.session_id != session_id:
            raise ValueError("package session does not match URL session")
        fingerprint = package.package_hash
        key = (session_id, idempotency_key)
        with self._lock:
            prior = self._idempotency.get(key)
            if prior is not None:
                if prior[1] != fingerprint:
                    raise ValueError("idempotency key payload mismatch")
                return self._jobs[prior[0]], True
            job = VideoJobStatusV1(
                job_id=str(uuid4()),
                session_id=session_id,
                state="QUEUED",
                stage="QUEUED",
                progress_percent=0,
                retry_count=0,
                public_message="Story video job queued.",
            )
            self._jobs[job.job_id] = job
            self._inputs[job.job_id] = (package, segments)
            self._idempotency[key] = (job.job_id, fingerprint)
            return job, False

    def get(self, job_id: str) -> VideoJobStatusV1:
        return self._jobs[job_id]

    def for_session(self, session_id: str) -> tuple[VideoJobStatusV1, ...]:
        return tuple(job for job in self._jobs.values() if job.session_id == session_id)

    def run_safely(self, job_id: str) -> None:
        try:
            self.run(job_id)
        except StoryVideoProviderError as error:
            with self._lock:
                current = self._jobs[job_id]
                state = (
                    "BLOCKED"
                    if error.code == "PROVIDER_NOT_CONFIGURED"
                    else "RETRYABLE_FAILURE"
                    if error.retryable
                    else "FAILED"
                )
                self._jobs[job_id] = current.model_copy(
                    update={
                        "state": state,
                        "stage": "FAILED",
                        "public_message": "Story video generation failed.",
                    }
                )

    def run(self, job_id: str) -> StoryVideoRun:
        if self._pipeline is None:
            with self._lock:
                current = self._jobs[job_id]
                self._jobs[job_id] = current.model_copy(
                    update={
                        "state": "BLOCKED",
                        "stage": "PREFLIGHT",
                        "public_message": "Story video provider is not configured.",
                    }
                )
            raise StoryVideoProviderError("PROVIDER_NOT_CONFIGURED", retryable=False)

        package, segments = self._inputs[job_id]

        def update(stage: str, progress: int) -> None:
            state = "READY" if stage == "READY" else "SCENES_RENDERING"
            with self._lock:
                current = self._jobs[job_id]
                self._jobs[job_id] = current.model_copy(
                    update={
                        "state": state,
                        "stage": stage,
                        "progress_percent": progress,
                        "public_message": "Story video generation in progress.",
                    }
                )

        self._pipeline._update_stage = update
        run = self._pipeline.run(package, segments)
        with self._lock:
            self._runs[job_id] = run
            self._jobs[job_id] = self._jobs[job_id].model_copy(
                update={"state": "READY", "stage": "READY", "progress_percent": 100}
            )
        return run

    def result(self, job_id: str) -> StoryVideoRun | None:
        return self._runs.get(job_id)


__all__ = ["StoryVideoJobService"]
