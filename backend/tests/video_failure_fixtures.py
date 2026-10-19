"""Synthetic exhausted projection, MEMORY persistence and ASSUMED owner authority.

Not actual08 failure projection/budget consumption/BE1 checkpoint/runtime proof.
"""

import copy
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from itertools import count
from types import SimpleNamespace
from unittest.mock import Mock

from sketch2life.application.video_failure import VideoFailureService
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.domain.video_failure.model import (
    Action,
    Choice,
    Context,
    EffectReceipt,
    FailureTarget,
    Intent,
    NewLifecycle,
    RetryAuthorization,
)

NOW = datetime(2026, 10, 19, tzinfo=UTC)


def ref(name):
    return ExactRef(name, 1, "a" * 64)


def target(**changes):
    return FailureTarget(
        **dict(
            organization_id="school",
            session_id="session",
            video_id="video",
            video_version=2,
            run_revision=7,
            job_id="old.job",
            job_revision=9,
            attempt_id="attempt",
            state=JobState.FAILED_EXHAUSTED,
            pin_digest="a" * 64,
            history_digest="b" * 64,
            context_revision=2,
            audience_revision=3,
            failure_ref=ref("failure"),
            policy=ref("policy"),
            exhausted_at=NOW - timedelta(seconds=1),
        )
        | changes
    )


def context(**changes):
    return Context(
        **dict(
            principal_id="teacher",
            organization_id="school",
            session_id="session",
            video_id="video",
            client_key="key",
        )
        | changes
    )


def choice(action=Action.SKIP, **changes):
    return Choice(
        **dict(
            action=action,
            reason="fixture reason",
            expected_video_version=2,
            expected_run_revision=7,
            expected_job_revision=9,
            expected_session_revision=4,
        )
        | changes
    )


def authorization(t=None, **changes):
    t = t or target()
    return RetryAuthorization(
        **dict(
            reference=ref("authorization"),
            target_digest=t.digest(),
            principal_id="teacher",
            policy=t.policy,
            budget_revision=3,
            expires_at=NOW + timedelta(minutes=1),
        )
        | changes
    )


def intent(action=Action.SKIP, **changes):
    return Intent(
        **dict(
            disposition_id="disposition",
            context=context(),
            choice=choice(action),
            target=target(),
            created_at=NOW,
            authorization=authorization() if action is Action.RETRY else None,
        )
        | changes
    )


def receipt(i=None, **changes):
    i = i or intent()
    retry = i.choice.action is Action.RETRY
    return EffectReceipt(
        **dict(
            receipt_id="effect",
            disposition_id=i.disposition_id,
            operation_key=i.context.operation_key(),
            request_digest=i.digest(),
            target_digest=i.target.digest(),
            principal_id=i.context.principal_id,
            action=i.choice.action,
            session_revision_before=4,
            session_revision_after=4 if retry else 5,
            video_run_revision=1 if retry else i.target.run_revision,
            recorded_at=NOW,
            new_lifecycle=NewLifecycle(
                "new.video",
                i.target.video_version,
                1,
                "new.job",
                1,
                JobState.QUEUED,
                "pending_media",
            )
            if retry
            else None,
            authorization_ref=i.authorization.reference if retry else None,
            budget_consumption_ref=ref("consumed") if retry else None,
            checkpoint_ref=ref("checkpoint") if i.choice.action is Action.END else None,
        )
        | changes
    )


class MemoryStore:
    def __init__(self):
        self.rows, self.claims, self.history, self.events = {}, {}, [], []
        self.active = False
        self.fail = None

    @contextmanager
    def transaction(self, org, session):
        assert not self.active
        old = copy.deepcopy((self.rows, self.claims, self.history, self.events))
        self.active = True
        self.scope = (org, session)
        try:
            yield self
            if self.fail == "commit":
                raise RuntimeError("synthetic_sensitive")
        except Exception:
            self.rows, self.claims, self.history, self.events = old
            raise
        finally:
            self.active = False

    def get(self, actor, key):
        assert self.active
        return self.rows.get((*self.scope, actor, key))

    def insert(self, i):
        assert self.active
        key = (*self.scope, i.context.principal_id, i.context.client_key)
        claim = (self.scope[0], i.target.claim_key())
        if key in self.rows or claim in self.claims:
            raise VideoError("VIDEO_DISPOSITION_CONFLICT")
        self.rows[key] = i
        self.claims[claim] = i.disposition_id
        self.history.append(i)
        if self.fail == "insert":
            raise RuntimeError("synthetic_sensitive")
        self.events.append((i.disposition_id, i.revision))

    def save(self, i, *, expected_revision):
        assert self.active
        key = (*self.scope, i.context.principal_id, i.context.client_key)
        if self.rows[key].revision != expected_revision:
            raise VideoError("VIDEO_DISPOSITION_STALE_INTENT")
        self.rows[key] = i
        self.history.append(i)
        if self.fail == "save":
            raise RuntimeError("synthetic_sensitive")
        self.events.append((i.disposition_id, i.revision))


class AssumedBoundary:
    def __init__(self, store):
        self.store, self.target = store, target()
        self.held = False
        self.denied = None
        self.calls = []
        self.fail_exit = False
        self.retry_allowed = True
        self.on_check = None

    @contextmanager
    def guard(self, c):
        if c.principal_id not in {"teacher", "teacher2"} or (c.organization_id, c.session_id) != (
            "school",
            "session",
        ):
            raise VideoError("VIDEO_DISPOSITION_FORBIDDEN")
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("synthetic_sensitive")
        finally:
            self.held = False

    def resolve(self, c, cmd):
        assert self.held and not self.store.active
        return self.target

    def authorize_retry(self, c, t):
        assert self.held and not self.store.active
        if not self.retry_allowed:
            raise VideoError("VIDEO_RETRY_NOT_AUTHORIZED")
        return authorization(t, principal_id=c.principal_id)

    def check(self, i, phase):
        assert self.held
        self.calls.append((phase, self.store.active))
        if self.on_check:
            self.on_check(i, phase)
        if self.denied == phase:
            raise VideoError("VIDEO_DISPOSITION_FORBIDDEN")
        if phase in {"prepare", "commit_intent", "dispatch"}:
            if self.target != i.target:
                raise VideoError("VIDEO_DISPOSITION_STALE_TARGET")
            if i.choice.expected_session_revision != 4:
                raise VideoError("VIDEO_DISPOSITION_STALE_SESSION")
            if i.choice.action is Action.RETRY and not self.retry_allowed:
                raise VideoError("VIDEO_RETRY_NOT_AUTHORIZED")


def harness():
    store = MemoryStore()
    boundary, bridge = AssumedBoundary(store), Mock()
    ids = count(1)

    def execute(i):
        assert boundary.held and not store.active
        assert next(iter(store.rows.values())) == i
        return receipt(i)

    bridge.execute.side_effect = execute
    bridge.lookup.return_value = None
    service = VideoFailureService(
        boundary,
        store,
        bridge,
        clock=lambda: NOW,
        disposition_ids=lambda: "disposition." + str(next(ids)),
    )
    return SimpleNamespace(store=store, boundary=boundary, bridge=bridge, service=service)
