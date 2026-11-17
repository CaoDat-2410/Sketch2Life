"""Closed typed routing at the BE2-01 dispatch boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pytest

from sketch2life.application.ports.ai_jobs import (
    DispatchMessage,
    WorkerDispatchEnvelope,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim
from sketch2life.domain.ai_jobs.model import RequestRef
from sketch2life.infrastructure.ai_jobs.harness import build_fixture_harness
from sketch2life.infrastructure.ai_jobs.typed_dispatch import TypedDispatchRouter
from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker

VIDEO_JOB_TYPE = "fixture.knowledge_video"


def _envelope(job_type: str) -> WorkerDispatchEnvelope:
    return WorkerDispatchEnvelope(
        DispatchMessage(
            message_id="message_fx_video",
            job_id="job_fx_video",
            attempt_id="attempt_fx_video",
            attempt_number=1,
            job_type=job_type,
            request_ref=RequestRef("request_fx_video", 1, "a" * 64, 1),
        ),
        "fixture-capability",
    )


@dataclass(frozen=True)
class _Outcome:
    status: str = "pending"
    reason_code: str = "VIDEO_WORK_PENDING"


class _VideoWorker:
    def __init__(self) -> None:
        self.envelopes: list[WorkerDispatchEnvelope] = []
        self.outcome = _Outcome()

    def handle(self, envelope: WorkerDispatchEnvelope) -> _Outcome:
        self.envelopes.append(envelope)
        return self.outcome


class _Provider:
    def __init__(self) -> None:
        self.calls: list[DispatchMessage] = []

    def run(self, message: DispatchMessage) -> CompletionClaim:
        self.calls.append(message)
        raise AssertionError("provider route must not be used in this test")


def test_registered_video_type_forwards_the_original_envelope_without_provider_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = build_fixture_harness()
    video_worker = _VideoWorker()
    provider = _Provider()
    worker = DispatchWorker(
        harness.service,
        provider,
        video_job_type=VIDEO_JOB_TYPE,
        video_worker=video_worker,
    )
    monkeypatch.setattr(
        harness.service,
        "start_attempt",
        lambda *_args: pytest.fail("video admission owns the persisted-job start"),
    )
    envelope = _envelope(VIDEO_JOB_TYPE)

    first = worker.handle(envelope)
    redelivery = worker.handle(envelope)

    assert cast(object, first) is video_worker.outcome
    assert cast(object, redelivery) is video_worker.outcome
    assert video_worker.envelopes == [envelope, envelope]
    assert video_worker.envelopes[0] is envelope
    assert provider.calls == []


def test_unregistered_and_mismatched_types_fail_closed_before_provider_or_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = build_fixture_harness()
    video_worker = _VideoWorker()
    provider = _Provider()
    worker = DispatchWorker(
        harness.service,
        provider,
        video_job_type=VIDEO_JOB_TYPE,
        video_worker=video_worker,
    )
    monkeypatch.setattr(
        harness.service,
        "start_attempt",
        lambda *_args: pytest.fail("unsupported type reached foundation start"),
    )

    unknown = worker.handle(_envelope("fixture.unknown"))
    mismatched = worker.handle(_envelope("fixture.knowledge_video_typo"))

    assert (unknown.status, unknown.reason_code) == ("rejected", "UNSUPPORTED_JOB_TYPE")
    assert (mismatched.status, mismatched.reason_code) == (
        "rejected",
        "UNSUPPORTED_JOB_TYPE",
    )
    assert video_worker.envelopes == []
    assert provider.calls == []


@pytest.mark.parametrize(
    ("video_job_type", "video_target"),
    [(VIDEO_JOB_TYPE, None), (None, _VideoWorker())],
)
def test_video_type_and_target_must_be_registered_together(
    video_job_type: str | None,
    video_target: _VideoWorker | None,
) -> None:
    with pytest.raises(ValueError, match="must be configured together"):
        TypedDispatchRouter(video_job_type=video_job_type, video_target=video_target)


def test_video_route_cannot_shadow_the_existing_provider_type() -> None:
    with pytest.raises(ValueError, match="both provider and video"):
        TypedDispatchRouter(
            video_job_type="sketch_assistance",
            video_target=_VideoWorker(),
        )
