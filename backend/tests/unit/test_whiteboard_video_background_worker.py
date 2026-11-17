from __future__ import annotations

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoJobService,
)
from test_whiteboard_video_job import SuccessfulPipeline, make_job, make_service


def test_configured_service_runs_job_safely_to_ready() -> None:
    service: WhiteboardVideoJobService = make_service(SuccessfulPipeline())
    job = make_job(service)

    service.run_safely(job.job_id)

    assert service.store.get(job.job_id).status == "READY"
    assert service.result(job.job_id) is not None


def test_unconfigured_service_does_not_claim_it_can_run() -> None:
    from sketch2life.application.services.whiteboard_video_job import (
        UnconfiguredWhiteboardVideoPipeline,
    )

    service = WhiteboardVideoJobService(pipeline=UnconfiguredWhiteboardVideoPipeline())

    assert service.can_run is False
