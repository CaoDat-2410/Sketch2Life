"""Process-local CMD-40 component fixtures, NOT actual foundation/job/SQL proof.

All run/job-intent/dispatch-intent/receipt maps swap under one local lock. Job and
dispatch entries are fixture intents, not real BE2-01 jobs or delivered messages.
There is deliberately no production factory or fallback binding to these fakes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from threading import RLock

from sketch2life.application.ports.knowledge_video import (
    VideoCreationLease,
    VideoRequestContext,
    VideoSubmission,
)
from sketch2life.contracts.schemas.knowledge_video import CreateKnowledgeVideo, KnowledgeVideoView
from sketch2life.domain.knowledge_video.model import VideoError, VideoPin, VideoRun, require_hash

FIXTURE_MARKER = "FIXTURE_ONLY_NO_FOUNDATION_OR_SQL_ADOPTION"


def _submission(run: VideoRun, outcome: str) -> VideoSubmission:
    """Only the initial queued synthetic intent is implemented by this fixture."""
    attempt_id = "fixture.attempt." + run.video_id
    view = KnowledgeVideoView.model_validate({
        "video_id": run.video_id, "video_version": run.video_version,
        "video_run_revision": run.run_revision, "video_review_revision": run.review_revision,
        "organization_id": run.pin.organization_id, "session_id": run.pin.session_id,
        "job_id": run.job_id, "job_revision": 1, "generation_state": "queued",
        "review_state": run.review_state.value,
        "retry_policy_version": run.pin.retry_policy.material(),
        "attempt_history": ({"attempt_id": attempt_id, "attempt_number": 1, "state": "queued"},),
        "created_at": run.created_at,
    })
    if outcome not in {"created", "replayed", "deduplicated"}:
        raise VideoError("VIDEO_SUBMISSION_MISMATCH")
    return VideoSubmission(run, 1, attempt_id,
                           "created" if outcome == "created" else (
                               "replayed" if outcome == "replayed" else "deduplicated"), view)


@dataclass(frozen=True, slots=True)
class _Lease:
    owner: FixtureVideoOwner
    pin: VideoPin
    epoch: int
    context: VideoRequestContext
    generation: int

    def assert_current(self) -> None:
        if not self.owner.active or self.owner.lease_generation != self.generation:
            raise VideoError("VIDEO_LEASE_CLOSED")
        if self.context.principal_id not in self.owner.allowed_principals:
            raise VideoError("VIDEO_FORBIDDEN")
        if self.owner.epoch != self.epoch or self.owner.pin != self.pin:
            raise VideoError("VIDEO_STALE_CONTEXT")


class FixtureVideoOwner:
    marker = FIXTURE_MARKER

    def __init__(self, pin: VideoPin, principal_id: str = "teacher") -> None:
        self.pin = pin
        self.allowed_principals = {principal_id}
        self.epoch = 1
        self.active = False
        self.lease_generation = 0
        self._lock = RLock()

    @contextmanager
    def hold(self, context: VideoRequestContext,
             command: CreateKnowledgeVideo) -> Iterator[VideoCreationLease]:
        del command  # Simulates an already-resolved stored bundle, not a real resolver.
        with self._lock:
            if self.active:
                raise VideoError("VIDEO_NESTED_FIXTURE_LEASE")
            self.active = True
            self.lease_generation += 1
            try:
                lease = _Lease(self, self.pin, self.epoch, context, self.lease_generation)
                lease.assert_current()
                yield lease
            finally:
                self.active = False


class FixtureAtomicVideoSubmission:
    marker = FIXTURE_MARKER

    def __init__(self, now: datetime) -> None:
        self.now = now
        self.runs: dict[str, VideoRun] = {}
        self.semantic: dict[str, str] = {}
        self.receipts: dict[tuple[str, str, str, str], tuple[str, str]] = {}
        self.job_intents: dict[str, str] = {}
        self.dispatch_intents: dict[str, str] = {}
        self.audit_intents: tuple[tuple[str, str], ...] = ()
        self._sequence = 0
        self._lock = RLock()
        self.before_commit: Callable[[], None] | None = None

    def submit(self, *, context: VideoRequestContext, command_hash: str,
               lease: VideoCreationLease) -> VideoSubmission:
        require_hash(command_hash)
        with self._lock:
            lease.assert_current()
            if lease.context != context:
                raise VideoError("VIDEO_RESOLUTION_MISMATCH")
            pin = lease.pin
            key = context.receipt_key
            prior = self.receipts.get(key)
            outcome = "created"
            if prior is not None:
                prior_body, video_id = prior
                if prior_body != command_hash:
                    raise VideoError("VIDEO_IDEMPOTENCY_CONFLICT")
                run = self.runs[video_id]
                if run.pin.digest() != pin.digest():
                    raise VideoError("VIDEO_STALE_CONTEXT")
                return _submission(run, "replayed")
            semantic = pin.digest()
            winner_id = self.semantic.get(semantic)
            if winner_id is None:
                self._sequence += 1
                video_id = f"fixture.video.{self._sequence}"
                job_id = f"fixture.job.{self._sequence}"
                run = VideoRun(video_id, 1, 1, 1, job_id, pin, self.now)
            else:
                run = self.runs[winner_id]
                outcome = "deduplicated"
            # Stage all effects before the explicit failure/revocation hook. No
            # mutable published collection changes until held-lease validation.
            runs = {**self.runs, run.video_id: run}
            semantics = {**self.semantic, semantic: run.video_id}
            receipts = {**self.receipts, key: (command_hash, run.video_id)}
            jobs = {**self.job_intents, run.job_id: run.video_id}
            dispatch = {**self.dispatch_intents, run.job_id: run.video_id}
            audits = (*self.audit_intents, (run.video_id, outcome))
            result = _submission(run, outcome)
            if self.before_commit is not None:
                self.before_commit()
            lease.assert_current()
            self.runs, self.semantic, self.receipts = runs, semantics, receipts
            self.job_intents, self.dispatch_intents, self.audit_intents = jobs, dispatch, audits
            return result

    def revoke_for_test(self, owner: FixtureVideoOwner) -> None:
        """Same-thread fault injection only. Cross-thread writes need actual owner APIs."""
        owner.epoch += 1
        owner.pin = replace(owner.pin, audience_revision=owner.pin.audience_revision + 1)
