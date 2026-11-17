"""Pure BE2-13 data/state rules. Current capabilities and policy are supplied ports."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import NoReturn


class PresetError(ValueError):
    """Safe code only; never an adapter exception or raw policy/configuration."""


def fail(code: str) -> NoReturn:
    raise PresetError("PRESET_" + code)


def identifier(value: str) -> None:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 128
        or any(not (c.isascii() and (c.isalnum() or c in "_-. :/")) for c in value)
        or value.strip() != value
    ):
        fail("INVALID_ID")


def positive(value: int) -> None:
    if type(value) is not int or value < 1:
        fail("INVALID_REVISION")


def aware(value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        fail("INVALID_TIME")


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def reason(value: str | None) -> None:
    if type(value) is not str or not value.strip() or len(value) > 200:
        fail("REASON_REQUIRED")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    condition: str
    expected: str
    action: str

    def __post_init__(self) -> None:
        identifier(self.rule_id)
        # Candidate vocabulary only; policy must explicitly adopt each rule.
        if self.condition not in {"stage_is", "help_pending"} or self.action not in {
            "notify_teacher",
            "request_support",
        }:
            fail("UNSUPPORTED_RULE")
        identifier(self.expected)
        if self.condition == "help_pending" and self.expected not in {"yes", "no"}:
            fail("UNSUPPORTED_RULE")


@dataclass(frozen=True)
class Body:
    title: str
    effective_age_policy_ref: str
    tool_policy_ref: str
    canvas_mode: str
    assistance_policy_ref: str
    stage_rules: tuple[Rule, ...]
    notification_rules: tuple[Rule, ...]
    video_policy_ref: str
    activity_policy_ref: str
    assessment_policy_ref: str

    def __post_init__(self) -> None:
        if type(self.title) is not str or not self.title.strip() or len(self.title) > 200:
            fail("INVALID_BODY")
        for name in (
            "effective_age_policy_ref",
            "tool_policy_ref",
            "canvas_mode",
            "assistance_policy_ref",
            "video_policy_ref",
            "activity_policy_ref",
            "assessment_policy_ref",
        ):
            identifier(getattr(self, name))
        rules = self.stage_rules + self.notification_rules
        if (
            type(self.stage_rules) is not tuple
            or type(self.notification_rules) is not tuple
            or len(rules) > 32
            or any(type(r) is not Rule for r in rules)
            or len({r.rule_id for r in rules}) != len(rules)
        ):
            fail("INVALID_RULES")

    @property
    def hash(self) -> str:
        return digest(asdict(self))


class State(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHANGES = "changes_requested"
    PUBLISHED = "published"
    RECALLED = "recalled"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Review:
    review_id: str
    record_id: str
    version: int
    body_hash: str
    dimension: str
    reviewer: str
    policy_ref: str
    decision: str
    reason: str | None = None

    def __post_init__(self) -> None:
        for value in (self.review_id, self.record_id, self.reviewer, self.policy_ref):
            identifier(value)
        positive(self.version)
        if (
            len(self.body_hash) != 64
            or any(c not in "0123456789abcdef" for c in self.body_hash)
            or self.dimension not in {"safety", "pedagogical"}
            or self.decision not in {"approve", "reject", "request_changes"}
        ):
            fail("INVALID_REVIEW")
        if self.decision != "approve":
            reason(self.reason)


@dataclass(frozen=True)
class Version:
    number: int
    body: Body
    state: State
    author: str
    created_at: datetime
    reviews: tuple[Review, ...] = ()
    publication: tuple[str, str, str] | None = None
    recalled_at: datetime | None = None
    recall_reason: str | None = None

    def __post_init__(self) -> None:
        positive(self.number)
        identifier(self.author)
        aware(self.created_at)
        if type(self.body) is not Body or type(self.state) is not State:
            fail("INVALID_VERSION")
        if (
            type(self.reviews) is not tuple
            or len(self.reviews) > 2
            or len({r.dimension for r in self.reviews}) != len(self.reviews)
        ):
            fail("INVALID_REVIEW")
        for r in self.reviews:
            if (
                r.version != self.number
                or r.body_hash != self.body.hash
                or r.reviewer == self.author
            ):
                fail("INVALID_REVIEW")
        if self.state in {State.PUBLISHED, State.RECALLED} and self.publication is None:
            fail("INVALID_PUBLICATION")
        if self.publication is not None:
            if type(self.publication) is not tuple or len(self.publication) != 3:
                fail("INVALID_PUBLICATION")
            for value in self.publication:
                identifier(value)
            for dim, rid in zip(("safety", "pedagogical"), self.publication[:2], strict=True):
                if not any(
                    r.dimension == dim
                    and r.review_id == rid
                    and r.decision == "approve"
                    and r.policy_ref == self.publication[2]
                    for r in self.reviews
                ):
                    fail("INVALID_PUBLICATION")
        if self.recalled_at is not None:
            aware(self.recalled_at)
            reason(self.recall_reason)
        if self.state is State.RECALLED and self.recalled_at is None:
            fail("INVALID_PUBLICATION")


@dataclass(frozen=True)
class Library:
    record_id: str
    organization_id: str
    revision: int
    versions: tuple[Version, ...]
    action: str
    actor: str
    changed_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        identifier(self.record_id)
        identifier(self.organization_id)
        positive(self.revision)
        identifier(self.actor)
        aware(self.changed_at)
        if self.action not in {
            "create",
            "edit",
            "submit_review",
            "record_review",
            "publish",
            "request_changes",
            "recall",
            "archive",
        }:
            fail("INVALID_ACTION")
        if self.action in {"request_changes", "recall", "archive"}:
            reason(self.reason)
        if (
            type(self.versions) is not tuple
            or not self.versions
            or tuple(v.number for v in self.versions) != tuple(range(1, len(self.versions) + 1))
        ):
            fail("INVALID_VERSION")
        if any(r.record_id != self.record_id for v in self.versions for r in v.reviews):
            fail("INVALID_REVIEW")

    def target(self, number: int, body_hash: str) -> Version:
        positive(number)
        if number > len(self.versions) or self.versions[number - 1].body.hash != body_hash:
            fail("STALE_TARGET")
        return self.versions[number - 1]

    def change(
        self,
        action: str,
        expected: int,
        version: int,
        body_hash: str,
        actor: str,
        now: datetime,
        *,
        body: Body | None = None,
        review: Review | None = None,
        publication: tuple[str, str, str] | None = None,
        why: str | None = None,
    ) -> Library:
        positive(expected)
        identifier(actor)
        aware(now)
        if expected != self.revision:
            fail("STALE_REVISION")
        old = self.target(version, body_hash)
        if now < old.created_at or now < self.changed_at:
            fail("INVALID_TIME")
        if action == "edit":
            if version != len(self.versions) or body is None:
                fail("INVALID_EDIT")
            new = Version(version + 1, body, State.DRAFT, actor, now)
            return replace(
                self,
                revision=self.revision + 1,
                versions=(*self.versions, new),
                action=action,
                actor=actor,
                changed_at=now,
                reason=why,
            )
        if action == "submit_review" and old.state in {State.DRAFT, State.CHANGES}:
            new = replace(old, state=State.SUBMITTED, reviews=(), publication=None)
        elif action == "record_review" and old.state is State.SUBMITTED and review is not None:
            if (review.record_id, review.version, review.body_hash, review.reviewer) != (
                self.record_id,
                version,
                body_hash,
                actor,
            ):
                fail("INVALID_REVIEW")
            if any(r.review_id == review.review_id for r in old.reviews):
                fail("DUPLICATE_REVIEW")
            new = replace(
                old,
                state=State.SUBMITTED if review.decision == "approve" else State.CHANGES,
                reviews=(*(r for r in old.reviews if r.dimension != review.dimension), review),
            )
        elif action == "publish" and old.state is State.SUBMITTED and publication is not None:
            if actor == old.author:
                fail("SEPARATION_REQUIRED")
            new = replace(old, state=State.PUBLISHED, publication=publication)
        elif action == "request_changes" and old.state is State.SUBMITTED:
            reason(why)
            new = replace(old, state=State.CHANGES, reviews=(), publication=None)
        elif action == "recall" and old.state is State.PUBLISHED:
            reason(why)
            new = replace(old, state=State.RECALLED, recalled_at=now, recall_reason=why)
        elif action == "archive" and old.state is not State.ARCHIVED:
            reason(why)
            new = replace(old, state=State.ARCHIVED)
        else:
            fail("TRANSITION_DENIED")
        return replace(
            self,
            revision=self.revision + 1,
            versions=tuple(new if v.number == version else v for v in self.versions),
            action=action,
            actor=actor,
            changed_at=now,
            reason=why,
        )


@dataclass(frozen=True)
class Stamp:
    session: int
    config: int
    stage: int
    automation: int

    def __post_init__(self) -> None:
        for value in (self.session, self.config, self.stage, self.automation):
            positive(value)


@dataclass(frozen=True)
class Source:
    record_id: str
    version: int
    body: Body

    def __post_init__(self) -> None:
        identifier(self.record_id)
        positive(self.version)
        if type(self.body) is not Body:
            fail("INVALID_SOURCE")


class IntentState(StrEnum):
    QUEUED = "queued"
    DEFERRED = "deferred"
    SENDING = "sending"
    APPLIED = "applied"
    STALE = "stale"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Intent:
    intent_id: str
    organization_id: str
    session_id: str
    actor: str
    revision: int
    kind: str
    source: Source
    observed: Stamp
    policy_ref: str
    action: str
    value: str
    reason: str
    created_at: datetime
    state: IntentState = IntentState.QUEUED
    disposition: str = "queued"

    def __post_init__(self) -> None:
        for value in (
            self.intent_id,
            self.organization_id,
            self.session_id,
            self.actor,
            self.policy_ref,
        ):
            identifier(value)
        positive(self.revision)
        aware(self.created_at)
        reason(self.reason)
        if (
            type(self.source) is not Source
            or type(self.observed) is not Stamp
            or type(self.state) is not IntentState
        ):
            fail("INVALID_INTENT")
        allowed = {
            "pin": {"pin"},
            "override": {"set_tool_policy", "set_assistance_policy"},
            "disable": {"disable_automation"},
            "automation": {"notify_teacher", "request_support"},
        }
        if self.action not in allowed.get(self.kind, set()):
            fail("UNSUPPORTED_ACTION")
        identifier(self.value)
        identifier(self.disposition)

    @property
    def hash(self) -> str:
        data = asdict(self)
        for key in ("revision", "state", "disposition"):
            data.pop(key)
        data["created_at"] = self.created_at.isoformat()
        return digest(data)

    def transition(self, state: IntentState, why: str) -> Intent:
        allowed = {
            IntentState.QUEUED: {
                IntentState.SENDING,
                IntentState.STALE,
                IntentState.CANCELLED,
                IntentState.DEFERRED,
            },
            IntentState.DEFERRED: {IntentState.SENDING, IntentState.STALE, IntentState.CANCELLED},
            IntentState.SENDING: {IntentState.APPLIED, IntentState.STALE, IntentState.REJECTED},
        }
        if state not in allowed.get(self.state, set()):
            fail("TRANSITION_DENIED")
        identifier(why)
        return replace(self, revision=self.revision + 1, state=state, disposition=why)


@dataclass(frozen=True)
class EffectReceipt:
    intent_id: str
    organization_id: str
    session_id: str
    intent_hash: str
    outcome: str
    observed: Stamp
    effective: Stamp
    receipt_ref: str
    reason: str

    def __post_init__(self) -> None:
        for value in (
            self.intent_id,
            self.organization_id,
            self.session_id,
            self.receipt_ref,
            self.reason,
        ):
            identifier(value)
        if (
            self.outcome not in {"applied", "stale", "rejected"}
            or len(self.intent_hash) != 64
            or any(c not in "0123456789abcdef" for c in self.intent_hash)
            or type(self.observed) is not Stamp
            or type(self.effective) is not Stamp
        ):
            fail("INVALID_RECEIPT")

    def validate_for(self, intent: Intent) -> None:
        if (
            self.intent_id,
            self.organization_id,
            self.session_id,
            self.intent_hash,
            self.observed,
        ) != (
            intent.intent_id,
            intent.organization_id,
            intent.session_id,
            intent.hash,
            intent.observed,
        ):
            fail("INVALID_RECEIPT")
        if self.outcome == "applied" and any(
            getattr(self.effective, field) < getattr(self.observed, field)
            for field in ("session", "config", "stage", "automation")
        ):
            fail("INVALID_RECEIPT")
        if (
            self.outcome == "applied"
            and intent.kind in {"pin", "override", "disable"}
            and (
                self.effective.config <= self.observed.config
                or self.effective.automation <= self.observed.automation
                or self.effective.session < self.observed.session
                or self.effective.stage < self.observed.stage
            )
        ):
            fail("INVALID_RECEIPT")


def matches(rule: Rule, *, stage: str, help_pending: bool) -> bool:
    if type(help_pending) is not bool:
        fail("INVALID_OBSERVATION")
    identifier(stage)
    return (
        stage == rule.expected
        if rule.condition == "stage_is"
        else help_pending == (rule.expected == "yes")
    )
