"""Pure10 original failure/choice/intents/receipts. Owner ports authenticate facts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    canonical_digest,
    require_hash,
    require_id,
    require_revision,
    require_time,
)


class Action(StrEnum):
    RETRY = "retry"
    SKIP = "skip"
    END = "end_session"


def short_text(value: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 200:
        raise VideoError("VIDEO_DISPOSITION_INVALID_REASON")


def exact(value: ExactRef) -> None:
    if type(value) is not ExactRef:
        raise VideoError("VIDEO_DISPOSITION_INVALID_REF")
    replace(value)


@dataclass(frozen=True, slots=True)
class FailureTarget:
    organization_id: str
    session_id: str
    video_id: str
    video_version: int
    run_revision: int
    job_id: str
    job_revision: int
    attempt_id: str
    state: JobState
    pin_digest: str
    history_digest: str
    context_revision: int
    audience_revision: int
    failure_ref: ExactRef
    policy: ExactRef
    exhausted_at: datetime

    def __post_init__(self) -> None:
        for item in (
            self.organization_id,
            self.session_id,
            self.video_id,
            self.job_id,
            self.attempt_id,
        ):
            require_id(item)
        for revision in (self.video_version, self.run_revision, self.job_revision):
            require_revision(revision)
        for revision in (self.context_revision, self.audience_revision):
            require_revision(revision, minimum=0)
        for item in (self.pin_digest, self.history_digest):
            require_hash(item)
        exact(self.failure_ref)
        exact(self.policy)
        require_time(self.exhausted_at)
        if self.state is not JobState.FAILED_EXHAUSTED:
            raise VideoError("VIDEO_NOT_EXHAUSTED")

    def digest(self) -> str:
        replace(self)
        return canonical_digest(
            {
                "schema": "BE2-10.Failure/0.1-candidate",
                **{
                    name: getattr(self, name)
                    for name in (
                        "organization_id",
                        "session_id",
                        "video_id",
                        "video_version",
                        "run_revision",
                        "job_id",
                        "job_revision",
                        "attempt_id",
                        "pin_digest",
                        "history_digest",
                        "context_revision",
                        "audience_revision",
                    )
                },
                "failure": self.failure_ref.material(),
                "policy": self.policy.material(),
                "exhausted_at": self.exhausted_at.isoformat(),
            }
        )

    def claim_key(self) -> str:
        # Stable failed lifecycle, NOT moving revisions/actor/action. One winner.
        return canonical_digest(
            {
                "schema": "BE2-10.Claim/0.1-candidate",
                "org": self.organization_id,
                "session": self.session_id,
                "video": self.video_id,
                "job": self.job_id,
            }
        )


@dataclass(frozen=True, slots=True)
class Choice:
    action: Action
    reason: str
    expected_video_version: int
    expected_run_revision: int
    expected_job_revision: int
    expected_session_revision: int
    retry_authorization_note: str | None = None

    def __post_init__(self) -> None:
        if type(self.action) is not Action:
            raise VideoError("VIDEO_DISPOSITION_INVALID_COMMAND")
        short_text(self.reason)
        for value in (
            self.expected_video_version,
            self.expected_run_revision,
            self.expected_job_revision,
        ):
            require_revision(value)
        require_revision(self.expected_session_revision, minimum=0)
        if self.retry_authorization_note is not None:
            short_text(self.retry_authorization_note)
            if self.action is not Action.RETRY:
                raise VideoError("VIDEO_DISPOSITION_INVALID_COMMAND")


@dataclass(frozen=True, slots=True)
class Context:
    principal_id: str
    organization_id: str
    session_id: str
    video_id: str
    client_key: str

    def __post_init__(self) -> None:
        for value in (
            self.principal_id,
            self.organization_id,
            self.session_id,
            self.video_id,
            self.client_key,
        ):
            require_id(value)

    def operation_key(self) -> str:
        replace(self)
        # Excludes video/action/body: same scoped key cannot start another effect.
        return canonical_digest(
            {
                "schema": "BE2-10.Operation/0.1-candidate",
                "org": self.organization_id,
                "session": self.session_id,
                "principal": self.principal_id,
                "key": self.client_key,
            }
        )


def request_digest(context: Context, choice: Choice) -> str:
    replace(context)
    replace(choice)
    return canonical_digest(
        {
            "schema": "BE2-10.Request/0.1-candidate",
            "operation": context.operation_key(),
            "video": context.video_id,
            **{name: getattr(choice, name) for name in choice.__dataclass_fields__},
        }
    )


@dataclass(frozen=True, slots=True)
class RetryAuthorization:
    reference: ExactRef
    target_digest: str
    principal_id: str
    policy: ExactRef
    budget_revision: int
    expires_at: datetime

    def __post_init__(self) -> None:
        exact(self.reference)
        exact(self.policy)
        require_hash(self.target_digest)
        require_id(self.principal_id)
        require_revision(self.budget_revision, minimum=0)
        require_time(self.expires_at)


@dataclass(frozen=True, slots=True)
class NewLifecycle:
    video_id: str
    video_version: int
    run_revision: int
    job_id: str
    job_revision: int
    generation_state: JobState
    review_state: str

    def __post_init__(self) -> None:
        for value in (self.video_id, self.job_id):
            require_id(value)
        for revision in (self.video_version, self.run_revision, self.job_revision):
            require_revision(revision)
        if self.generation_state is not JobState.QUEUED or self.review_state != "pending_media":
            raise VideoError("VIDEO_DISPOSITION_INVALID_NEW_LIFECYCLE")


@dataclass(frozen=True, slots=True)
class EffectReceipt:
    receipt_id: str
    disposition_id: str
    operation_key: str
    request_digest: str
    target_digest: str
    principal_id: str
    action: Action
    session_revision_before: int
    session_revision_after: int
    video_run_revision: int
    recorded_at: datetime
    new_lifecycle: NewLifecycle | None = None
    authorization_ref: ExactRef | None = None
    budget_consumption_ref: ExactRef | None = None
    checkpoint_ref: ExactRef | None = None

    def __post_init__(self) -> None:
        for value in (self.receipt_id, self.disposition_id, self.principal_id):
            require_id(value)
        for value in (self.operation_key, self.request_digest, self.target_digest):
            require_hash(value)
        for revision in (self.session_revision_before, self.session_revision_after):
            require_revision(revision, minimum=0)
        require_revision(self.video_run_revision)
        require_time(self.recorded_at)
        if type(self.action) is not Action:
            raise VideoError("VIDEO_DISPOSITION_INVALID_RECEIPT")
        for reference in (self.authorization_ref, self.budget_consumption_ref, self.checkpoint_ref):
            if reference is not None:
                exact(reference)
        if self.action is Action.RETRY:
            if (
                type(self.new_lifecycle) is not NewLifecycle
                or self.authorization_ref is None
                or (self.budget_consumption_ref is None or self.checkpoint_ref is not None)
            ):
                raise VideoError("VIDEO_DISPOSITION_INVALID_RECEIPT")
            replace(self.new_lifecycle)
            if self.video_run_revision != self.new_lifecycle.run_revision or (
                self.session_revision_after < self.session_revision_before
            ):
                raise VideoError("VIDEO_DISPOSITION_INVALID_RECEIPT")
        elif (
            self.new_lifecycle is not None
            or self.authorization_ref is not None
            or self.budget_consumption_ref is not None
            or self.session_revision_after <= self.session_revision_before
            or ((self.action is Action.END) != (self.checkpoint_ref is not None))
        ):
            raise VideoError("VIDEO_DISPOSITION_INVALID_RECEIPT")


@dataclass(frozen=True, slots=True)
class Intent:
    disposition_id: str
    context: Context
    choice: Choice
    target: FailureTarget
    created_at: datetime
    authorization: RetryAuthorization | None = None
    revision: int = 1
    receipt: EffectReceipt | None = None

    def __post_init__(self) -> None:
        require_id(self.disposition_id)
        for value, cls in (
            (self.context, Context),
            (self.choice, Choice),
            (self.target, FailureTarget),
        ):
            if type(value) is not cls:
                raise VideoError("VIDEO_DISPOSITION_INVALID_INTENT")
            replace(value)
        require_time(self.created_at)
        require_revision(self.revision)
        c, t, cmd = self.context, self.target, self.choice
        if (c.organization_id, c.session_id, c.video_id) != (
            t.organization_id,
            t.session_id,
            t.video_id,
        ):
            raise VideoError("VIDEO_DISPOSITION_SCOPE_MISMATCH")
        if (cmd.expected_video_version, cmd.expected_run_revision, cmd.expected_job_revision) != (
            t.video_version,
            t.run_revision,
            t.job_revision,
        ) or self.created_at < t.exhausted_at:
            raise VideoError("VIDEO_DISPOSITION_STALE_TARGET")
        if cmd.action is Action.RETRY:
            if type(self.authorization) is not RetryAuthorization:
                raise VideoError("VIDEO_RETRY_NOT_AUTHORIZED")
            auth = replace(self.authorization)
            if (auth.target_digest, auth.principal_id, auth.policy) != (
                t.digest(),
                c.principal_id,
                t.policy,
            ) or auth.expires_at <= self.created_at:
                raise VideoError("VIDEO_RETRY_NOT_AUTHORIZED")
        elif self.authorization is not None:
            raise VideoError("VIDEO_DISPOSITION_INVALID_INTENT")
        if (self.receipt is None and self.revision != 1) or (
            self.receipt is not None and self.revision != 2
        ):
            raise VideoError("VIDEO_DISPOSITION_INVALID_INTENT")
        if self.receipt is not None:
            self._bind(self.receipt)

    def digest(self) -> str:
        return request_digest(self.context, self.choice)

    def _bind(self, receipt: EffectReceipt) -> None:
        if type(receipt) is not EffectReceipt:
            raise VideoError("VIDEO_DISPOSITION_INVALID_RECEIPT")
        r = replace(receipt)
        if (
            r.disposition_id,
            r.operation_key,
            r.request_digest,
            r.target_digest,
            r.principal_id,
            r.action,
            r.session_revision_before,
        ) != (
            self.disposition_id,
            self.context.operation_key(),
            self.digest(),
            self.target.digest(),
            self.context.principal_id,
            self.choice.action,
            self.choice.expected_session_revision,
        ) or r.recorded_at < self.created_at:
            raise VideoError("VIDEO_DISPOSITION_RECEIPT_MISMATCH")
        if r.action is Action.RETRY:
            new = r.new_lifecycle
            if (
                new is None
                or self.authorization is None
                or (
                    r.authorization_ref != self.authorization.reference
                    or new.video_id == self.target.video_id
                    or new.job_id == self.target.job_id
                    or new.video_version != self.target.video_version
                )
            ):
                raise VideoError("VIDEO_DISPOSITION_RECEIPT_MISMATCH")
        elif r.video_run_revision != self.target.run_revision:
            raise VideoError("VIDEO_DISPOSITION_RECEIPT_MISMATCH")

    def settle(self, receipt: EffectReceipt) -> Intent:
        replace(self)
        self._bind(receipt)
        if self.receipt is not None:
            if self.receipt == receipt:
                return self
            raise VideoError("VIDEO_DISPOSITION_RECEIPT_CONFLICT")
        return replace(self, revision=2, receipt=replace(receipt))
