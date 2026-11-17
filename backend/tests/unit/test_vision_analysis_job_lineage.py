"""BE2-02 C1 consumes BE2-01 job lineage read-only through its repository port (V07)."""

from __future__ import annotations

from datetime import UTC, datetime

from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.application.services.vision_analysis import ObservationDisposition
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs.model import JobScope, JobState, RequestRef
from sketch2life.domain.vision_analysis import VISION_ANALYSIS_JOB_TYPE
from sketch2life.infrastructure.ai_jobs.fakes import InMemoryAiJobStore
from sketch2life.infrastructure.vision_analysis.harness import (
    ASSISTANCE,
    CHILD_A,
    CONTEXT_REVISION,
    ORG,
    PURPOSE,
    SESSION,
    build_analysis_harness,
    synthetic_snapshot,
)
from sketch2life.infrastructure.vision_analysis.job_lineage import AiJobRepositoryLineage

NOW = datetime(2026, 10, 16, 11, 59, tzinfo=UTC)


def _foundation_job(store: InMemoryAiJobStore, *, running: bool = True) -> jobs.AiJob:
    job = jobs.create_job(
        job_id="job_fx0001",
        attempt_id="att_fx0001",
        job_type=VISION_ANALYSIS_JOB_TYPE,
        scope=JobScope(ORG, SESSION, (CHILD_A,), PURPOSE, ASSISTANCE),
        request_ref=RequestRef(ASSISTANCE, 1, synthetic_snapshot().input_hash(),
                               CONTEXT_REVISION),
        correlation_id="corr_fx_job",
        retry_policy=FIXTURE_RETRY_POLICY,
        now=NOW,
    )
    if running:
        job = jobs.start_attempt(job, "att_fx0001", NOW)
    with store.transaction() as tx:
        tx.insert_job(job)
    return job


def test_v07_running_foundation_attempt_is_consumed_without_rewriting_it() -> None:
    store = InMemoryAiJobStore()
    job = _foundation_job(store)
    h = build_analysis_harness(jobs=AiJobRepositoryLineage(store))
    before = store.snapshot().jobs
    result = h.observe()
    assert result.disposition is ObservationDisposition.ACCEPTED
    after = store.snapshot()
    assert after.jobs == before and after.jobs["job_fx0001"].job_revision == job.job_revision
    assert after.completion_receipts == {} and after.outbox == {}


def test_v07_cancelled_or_queued_foundation_job_is_rejected() -> None:
    store = InMemoryAiJobStore()
    job = _foundation_job(store)
    cancelled = jobs.cancel(job, reason_code="CANCELLED_BY_TEACHER",
                            public_message="cancelled", now=NOW)
    with store.transaction() as tx:
        tx.cas_job(expected_revision=job.job_revision, job=cancelled)
    h = build_analysis_harness(jobs=AiJobRepositoryLineage(store))
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED
    assert result.code == "JOB_CANCELLED" and not result.provider_invoked
    queued_store = InMemoryAiJobStore()
    _foundation_job(queued_store, running=False)
    queued = build_analysis_harness(jobs=AiJobRepositoryLineage(queued_store)).observe()
    assert queued.code == "INVALID_STATE"


def test_v07_lineage_view_maps_the_pinned_attempt_request() -> None:
    store = InMemoryAiJobStore()
    _foundation_job(store)
    view = AiJobRepositoryLineage(store).get("job_fx0001")
    assert view is not None and view.state is JobState.RUNNING
    assert (view.request_id, view.request_revision, view.context_revision) == (
        ASSISTANCE, 1, CONTEXT_REVISION)
    assert view.input_hash == synthetic_snapshot().input_hash()
    assert AiJobRepositoryLineage(store).get("job_fx0404") is None
