from datetime import datetime, timezone

import pytest

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoJobService,
    WhiteboardVideoPipelineError,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoResultV1


HASH = "a" * 64
NOW = datetime(2026, 9, 24, 8, 0, tzinfo=timezone.utc)


def valid_result(job_hash: str = HASH) -> WhiteboardVideoResultV1:
    return WhiteboardVideoResultV1(
        job_id="job-result-001",
        video_artifact_id="artifact-video-001",
        mp4_ref="artifact-ref/video.mp4",
        mask_refs=("artifact-mask-001",),
        stroke_refs=("artifact-stroke-001",),
        tts_ref="artifact-tts-001",
        source_hash=job_hash,
        experience_spec_id="spec-001",
        learning_thread_ref="thread-001",
        duration_seconds=8,
        codec="H264_AVC_HIGH_L4_1",
        size_bytes=4_000_000,
    )


class SuccessfulPipeline:
    def run(self, job, update_stage):
        for stage, progress in (
            ("LOCALIZING", 15),
            ("SEGMENTING", 35),
            ("EXTRACTING_STROKES", 55),
            ("RENDERING", 70),
            ("ENCODING", 90),
        ):
            update_stage(stage, progress)
        return valid_result(job.source_hash)


class RetryableFailurePipeline:
    def run(self, job, update_stage):
        update_stage("SEGMENTING", 35)
        raise WhiteboardVideoPipelineError("SEGMENTATION_TIMEOUT", retryable=True)


class MismatchedResultPipeline:
    def run(self, job, update_stage):
        update_stage("ENCODING", 90)
        return valid_result("b" * 64)


def make_service(pipeline):
    return WhiteboardVideoJobService(pipeline=pipeline, now=lambda: NOW)


def make_job(service):
    return service.create_job(
        session_id="session-001",
        experience_spec_id="spec-001",
        source_artifact_id="artifact-source-001",
        source_hash=HASH,
        learning_thread_ref="thread-001",
        idempotency_key="idem-001",
    )


def test_successful_pipeline_reaches_ready() -> None:
    service = make_service(SuccessfulPipeline())
    job = make_job(service)

    result = service.run(job.job_id)

    assert result.status == "READY"
    assert service.store.get(job.job_id).status == "READY"
    assert service.store.get(job.job_id).progress == 100


def test_retryable_failure_can_create_new_attempt() -> None:
    service = make_service(RetryableFailurePipeline())
    job = make_job(service)

    with pytest.raises(WhiteboardVideoPipelineError, match="SEGMENTATION_TIMEOUT"):
        service.run(job.job_id)

    failed = service.store.get(job.job_id)
    assert failed.status == "RETRYABLE_FAILURE"
    retried = service.retry(job.job_id, idempotency_key="idem-002")
    assert retried.attempt == 2
    assert retried.job_version == 2
    assert retried.idempotency_key == "idem-002"


def test_source_mismatch_cannot_reach_ready() -> None:
    service = make_service(MismatchedResultPipeline())
    job = make_job(service)

    with pytest.raises(WhiteboardVideoPipelineError, match="SOURCE_HASH_MISMATCH"):
        service.run(job.job_id)

    assert service.store.get(job.job_id).status == "FAILED"


def test_retry_budget_exhaustion_becomes_failed() -> None:
    service = make_service(RetryableFailurePipeline())
    job = make_job(service)

    for attempt in range(1, 4):
        with pytest.raises(WhiteboardVideoPipelineError):
            service.run(job.job_id)
        current = service.store.get(job.job_id)
        if attempt < 3:
            job = service.retry(job.job_id, idempotency_key=f"idem-00{attempt + 1}")

    assert service.store.get(job.job_id).status == "FAILED"
