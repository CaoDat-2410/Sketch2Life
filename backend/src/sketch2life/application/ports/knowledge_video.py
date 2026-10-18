"""BE2-08 candidate owner-lease and atomic-submission boundaries.

No default owner or durable adapter. Adopting this surface requires D01–D04
conformance; a process-local lease/store is component evidence only.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Literal, Protocol

from sketch2life.contracts.schemas.knowledge_video import CreateKnowledgeVideo
from sketch2life.domain.knowledge_video.model import (
    VideoError,
    VideoPin,
    VideoRun,
    require_id,
    require_revision,
)


@dataclass(frozen=True, slots=True)
class VideoRequestContext:
    """Verified server context, not a client-provided role or grant DTO."""

    principal_id: str
    organization_id: str
    session_id: str
    idempotency_key: str
    correlation_id: str

    def __post_init__(self) -> None:
        for value in (self.principal_id, self.organization_id, self.session_id,
                      self.idempotency_key, self.correlation_id):
            require_id(value)

    @property
    def receipt_key(self) -> tuple[str, str, str, str]:
        return (self.organization_id, self.session_id, self.principal_id, self.idempotency_key)


class VideoCreationLease(Protocol):
    """Owner authorization + exact bundle/profile/rights/current-policy observation.

    Resolver checks stored bundle bytes/hash, current script/source eligibility,
    current consent/grant/session/audience, published rights/encoding/profile and
    applicable policy/quota gates. NOT an additional pre-render human approval.
    Held owner fences must cover the actual submission commit; observations
    alone or post-commit assertions cannot close a race.
    """

    @property
    def pin(self) -> VideoPin: ...

    @property
    def context(self) -> VideoRequestContext: ...

    def assert_current(self) -> None:
        """Raise safe VideoError on stale/denied; actual adapter retains guards to commit."""
        ...


class VideoCreationResolver(Protocol):
    def hold(self, context: VideoRequestContext, command: CreateKnowledgeVideo,
             ) -> AbstractContextManager[VideoCreationLease]: ...


@dataclass(frozen=True, slots=True)
class VideoSubmission:
    run: VideoRun
    job_revision: int
    attempt_id: str
    outcome: Literal["created", "replayed", "deduplicated"]

    def __post_init__(self) -> None:
        if not isinstance(self.run, VideoRun):
            raise VideoError("VIDEO_SUBMISSION_MISMATCH")
        require_revision(self.job_revision)
        require_id(self.attempt_id)
        if self.outcome not in {"created", "replayed", "deduplicated"}:
            raise VideoError("VIDEO_SUBMISSION_MISMATCH")


class AtomicVideoSubmission(Protocol):
    def submit(self, *, context: VideoRequestContext, command_hash: str,
               lease: VideoCreationLease) -> VideoSubmission:
        """One commit: run + foundation job + dispatch + semantic/receipt/audit records.

        Replay is scoped to org/session/principal/key, body-bound and under current
        owner eligibility. Different body conflicts; old pin is not rewritten.
        Exact semantic duplicates may share one run/job only after authorization.
        Adapter must enlist owned rows in the foundation's authorized create path,
        not bypass its guards with domain.create_job or two separate transactions.
        Actual transaction-bound fences, conflicts/rollback/recovery require SQL
        conformance. No runtime adapter is supplied by the fixture implementation.
        """
        ...
