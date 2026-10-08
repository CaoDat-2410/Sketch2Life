"""Process-local job state for the illustrated story-video pipeline."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from sketch2life.application.ports.session_storage import ArtifactStore
from sketch2life.application.services.ephemeral_sessions import SessionWorkflowError
from sketch2life.application.services.story_video_pipeline import (
    StoryVideoPipeline,
    StoryVideoProviderError,
    StoryVideoRun,
)
from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryScriptSegmentV1,
    stable_model_hash,
    story_script_segments_hash,
)
from sketch2life.contracts.schemas.story_video_media import VideoJobStatusV1
from sketch2life.contracts.schemas.workflow_records import SessionSnapshotV1

_LOGGER = logging.getLogger("sketch2life.story_video_job")


class StoryVideoInputError(ValueError):
    def __init__(self, code: str, status_code: int = 409) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class StoryVideoJobService:
    def __init__(
        self,
        *,
        pipeline: StoryVideoPipeline | None = None,
        session_snapshot: Callable[[str], SessionSnapshotV1] | None = None,
        source_artifacts: ArtifactStore | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if pipeline is not None and (session_snapshot is None or source_artifacts is None):
            raise ValueError(
                "configured story pipeline requires session and source admission gates"
            )
        self._pipeline = pipeline
        self._session_snapshot = session_snapshot
        self._source_artifacts = source_artifacts
        self._now = now
        self._lock = RLock()
        self._jobs: dict[str, VideoJobStatusV1] = {}
        self._inputs: dict[
            str, tuple[ApprovedStoryPackageV1, tuple[StoryScriptSegmentV1, ...]]
        ] = {}
        self._runs: dict[str, StoryVideoRun] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}
        self._package_jobs: dict[tuple[str, str], str] = {}

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
            raise StoryVideoInputError("STORY_SESSION_MISMATCH")
        if package.story_script_sha256 != story_script_segments_hash(segments):
            raise StoryVideoInputError("STORY_SCRIPT_HASH_MISMATCH")
        if package.package_hash != stable_model_hash(package, exclude={"package_hash"}):
            raise StoryVideoInputError("STORY_PACKAGE_HASH_MISMATCH")
        if self._session_snapshot is not None:
            try:
                snapshot = self._session_snapshot(session_id)
            except (KeyError, SessionWorkflowError) as error:
                raise StoryVideoInputError("STORY_SESSION_UNAVAILABLE", 404) from error
            if snapshot.status != "ACTIVE" or snapshot.state not in {
                "EXPERIENCE_READY", "HANDOFF_READY", "FEEDBACK_RECORDED"
            }:
                raise StoryVideoInputError("STORY_SESSION_NOT_APPROVED")
            if snapshot.version != package.session_version:
                raise StoryVideoInputError("STORY_SESSION_VERSION_MISMATCH")
        if self._source_artifacts is not None:
            stored = self._source_artifacts.get(package.source_image_ref)
            if stored is None:
                raise StoryVideoInputError("STORY_SOURCE_NOT_FOUND", 404)
            descriptor, _body = stored
            if (
                descriptor.session_id != session_id
                or descriptor.sha256 != package.source_image_sha256
                or descriptor.content_type not in {"image/png", "image/jpeg", "image/webp"}
            ):
                raise StoryVideoInputError("STORY_SOURCE_MISMATCH")
        fingerprint = package.package_hash
        key = (session_id, idempotency_key)
        with self._lock:
            prior = self._idempotency.get(key)
            if prior is not None:
                if prior[1] != fingerprint:
                    raise ValueError("idempotency key payload mismatch")
                return self._jobs[prior[0]], True
            package_job_id = self._package_jobs.get((session_id, fingerprint))
            if package_job_id is not None:
                package_job = self._jobs[package_job_id]
                if package_job.state in {
                    "QUEUED", "PREFLIGHT", "NARRATION_READY", "ILLUSTRATIONS_READY",
                    "SCENES_RENDERING", "ASSEMBLING", "VALIDATING", "READY",
                }:
                    self._idempotency[key] = (package_job_id, fingerprint)
                    return package_job, True
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
            self._package_jobs[(session_id, fingerprint)] = job.job_id
            return job, False

    def get(self, job_id: str) -> VideoJobStatusV1:
        with self._lock:
            job = self._jobs[job_id]
        if self._session_snapshot is None or job.state == "EXPIRED":
            return job
        try:
            snapshot = self._session_snapshot(job.session_id)
        except (KeyError, SessionWorkflowError):
            snapshot = None
        if snapshot is not None and snapshot.status == "ACTIVE":
            return job
        with self._lock:
            current = self._jobs[job_id]
            expired = current.model_copy(
                update={
                    "state": "EXPIRED",
                    "stage": "EXPIRED",
                    "public_message": "Story video session expired.",
                }
            )
            self._jobs[job_id] = expired
            self._runs.pop(job_id, None)
            return expired

    def for_session(self, session_id: str) -> tuple[VideoJobStatusV1, ...]:
        return tuple(job for job in self._jobs.values() if job.session_id == session_id)

    def run_safely(self, job_id: str) -> None:
        try:
            self.run(job_id)
        except StoryVideoProviderError as error:
            _LOGGER.warning("story_video_job_provider_failed job_id=%s code=%s", job_id, error.code)
            public_code = error.code if re.fullmatch(r"[A-Z][A-Z0-9_]{1,79}", error.code) else None
            with self._lock:
                current = self._jobs[job_id]
                if current.state == "EXPIRED":
                    return
                state = (
                    "EXPIRED"
                    if error.code == "SESSION_EXPIRED"
                    else "BLOCKED"
                    if error.code == "PROVIDER_NOT_CONFIGURED"
                    else "RETRYABLE_FAILURE"
                    if error.retryable
                    else "FAILED"
                )
                self._jobs[job_id] = current.model_copy(
                    update={
                        "state": state,
                        "stage": "EXPIRED" if state == "EXPIRED" else "FAILED",
                        "public_message": (
                            f"Story video generation failed: {public_code}."
                            if public_code else "Story video generation failed."
                        ),
                    }
                )
        except Exception:  # noqa: BLE001 - background jobs must not escape
            # BackgroundTasks otherwise logs the exception and leaves the job
            # looking queued forever. Keep provider details in private logs.
            _LOGGER.exception("story_video_job_failed_unhandled", extra={"job_id": job_id})
            with self._lock:
                current = self._jobs.get(job_id)
                if current is not None:
                    self._jobs[job_id] = current.model_copy(
                        update={
                            "state": "FAILED",
                            "stage": "FAILED",
                            "public_message": "Story video generation failed: INTERNAL_ERROR.",
                        }
                    )

    def run(self, job_id: str) -> StoryVideoRun:
        if self.get(job_id).state == "EXPIRED":
            raise StoryVideoProviderError("SESSION_EXPIRED", retryable=False)
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
            if self.get(job_id).state == "EXPIRED":
                raise StoryVideoProviderError("SESSION_EXPIRED", retryable=False)
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

        run = self._pipeline.run(package, segments, update_stage=update)
        if self.get(job_id).state == "EXPIRED":
            raise StoryVideoProviderError("SESSION_EXPIRED", retryable=False)
        with self._lock:
            self._runs[job_id] = run
            self._jobs[job_id] = self._jobs[job_id].model_copy(
                update={"state": "READY", "stage": "READY", "progress_percent": 100}
            )
        return run

    def result(self, job_id: str) -> StoryVideoRun | None:
        return self._runs.get(job_id)


__all__ = ["StoryVideoInputError", "StoryVideoJobService"]
