"""Closed job-type routing for the offline foundation worker composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from sketch2life.application.ports.ai_jobs import WorkerDispatchEnvelope

PROVIDER_JOB_TYPES = frozenset({"sketch_assistance"})


class VideoDispatchOutcome(Protocol):
    @property
    def status(self) -> str: ...

    @property
    def reason_code(self) -> str: ...


class VideoDispatchTarget(Protocol):
    def handle(self, envelope: WorkerDispatchEnvelope) -> VideoDispatchOutcome: ...


@dataclass(frozen=True, slots=True)
class DispatchRoute:
    kind: Literal["provider", "video", "unsupported"]
    video_target: VideoDispatchTarget | None = None


class TypedDispatchRouter:
    """Select the existing sketch provider or one explicitly registered video worker.

    A video discriminator is provided by composition so this router does not invent a
    shared job-type contract. All other unregistered types fail closed.
    """

    def __init__(
        self,
        *,
        provider_job_types: frozenset[str] = PROVIDER_JOB_TYPES,
        video_job_type: str | None = None,
        video_target: VideoDispatchTarget | None = None,
    ) -> None:
        if (video_job_type is None) != (video_target is None):
            raise ValueError("video job type and target must be configured together")
        if any(not isinstance(item, str) or not item or item != item.strip()
               for item in provider_job_types):
            raise ValueError("invalid provider job type")
        if video_job_type is not None and (
            not video_job_type or video_job_type != video_job_type.strip()
        ):
            raise ValueError("invalid video job type")
        if video_job_type is not None and video_job_type in provider_job_types:
            raise ValueError("job type cannot select both provider and video routes")
        self._provider_job_types = provider_job_types
        self._video_job_type = video_job_type
        self._video_target = video_target

    def resolve(self, job_type: str) -> DispatchRoute:
        if not isinstance(job_type, str) or not job_type or job_type != job_type.strip():
            return DispatchRoute("unsupported")
        if job_type == self._video_job_type:
            return DispatchRoute("video", self._video_target)
        if job_type in self._provider_job_types:
            return DispatchRoute("provider")
        return DispatchRoute("unsupported")


__all__ = ["PROVIDER_JOB_TYPES", "DispatchRoute", "TypedDispatchRouter"]
