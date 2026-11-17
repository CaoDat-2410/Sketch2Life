"""Candidate13 ownership/fencing/dedup seams. No default authority or scheduler."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.preset_automation.model import (
    Body,
    EffectReceipt,
    Intent,
    Library,
    Review,
    Rule,
    Source,
    Stamp,
    identifier,
    positive,
)


@dataclass(frozen=True)
class SessionView:
    organization_id: str
    session_id: str
    observed: Stamp
    source: Source | None
    policy_ref: str
    stage: str
    help_pending: bool
    automation_enabled: bool
    draft: bool

    def __post_init__(self) -> None:
        for value in (self.organization_id, self.session_id, self.policy_ref, self.stage):
            identifier(value)
        if any(
            type(v) is not bool for v in (self.help_pending, self.automation_enabled, self.draft)
        ):
            raise ValueError("invalid session view")
        if type(self.observed) is not Stamp or (
            self.source is not None and type(self.source) is not Source
        ):
            raise ValueError("invalid session view")


@dataclass(frozen=True)
class LocalReceipt:
    actor: str
    client_key: str
    fingerprint: str
    object_key: str
    applied_revision: int
    target_version: int

    def __post_init__(self) -> None:
        for value in (self.actor, self.client_key, self.fingerprint, self.object_key):
            identifier(value)
        positive(self.applied_revision)
        positive(self.target_version)
        if len(self.fingerprint) != 64 or any(
            c not in "0123456789abcdef" for c in self.fingerprint
        ):
            raise ValueError("invalid receipt fingerprint")


@dataclass(frozen=True)
class Decision:
    decision_id: str
    organization_id: str
    session_id: str
    actor: str
    rule_id: str
    source: Source
    observed: Stamp
    policy_ref: str
    outcome: str
    intent_id: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        from sketch2life.domain.preset_automation.model import aware, fail

        for value in (
            self.decision_id,
            self.organization_id,
            self.session_id,
            self.actor,
            self.rule_id,
            self.policy_ref,
        ):
            identifier(value)
        aware(self.created_at)
        if (
            type(self.source) is not Source
            or type(self.observed) is not Stamp
            or self.outcome not in {"queued", "deferred", "unsupported", "not_matched", "disabled"}
        ):
            fail("INVALID_DECISION")
        if (self.intent_id is not None) != (self.outcome in {"queued", "deferred"}):
            fail("INVALID_DECISION")
        if self.intent_id is not None:
            identifier(self.intent_id)


Stored = Library | Intent | LocalReceipt | EffectReceipt | Decision


class Rows(Protocol):
    def get(self, key: str) -> Stored | None: ...
    def history(self, key: str, revision: int) -> Stored | None: ...
    def put(self, key: str, before: Stored | None, value: Stored) -> None: ...


class Store(Protocol):
    def transaction(self, organization_id: str, scope: str) -> AbstractContextManager[Rows]: ...


class Fence(Protocol):
    """Actual adopter holds current authority/source/policy fences THROUGH commit.

    check(action) validates independent preset capability and actor/session scope.
    Methods read held verified snapshots without network IO inside own SQL tx;
    actual adopter acquires/refreshes authority before entering that transaction.
    validate_body checks allowlisted refs/mandatory invariants and schema adoption.
    review/publication authenticate CURRENT exact preset proofs, not content rights.
    session is authoritative; source checks exact publication/recall/current rights.
    rule checks adopted condition/action policy, consent/safety/review and audience.
    None return indicates success, exceptions deny; never default permissive.
    """

    def check_current(self) -> None: ...
    def check(self, action: str) -> None: ...
    def validate_body(self, body: Body) -> None: ...
    def review(self, library: Library, proof: Review) -> None: ...
    def publication(self, library: Library, version: int, refs: tuple[str, str, str]) -> None: ...
    def session(self) -> SessionView: ...
    def source(self, source: Source) -> None: ...
    def rule(self, rule: Rule, view: SessionView) -> None: ...
    def intent(self, intent: Intent, view: SessionView) -> None:
        """Check adopted new config values/actions and mandatory gates, not just source body."""
        ...


class Authority(Protocol):
    def hold(
        self, organization_id: str, actor: str, *, session_id: str | None = None
    ) -> AbstractContextManager[Fence]: ...


class QueuePolicy(Protocol):
    """Pure non-I/O admission decision on held policy snapshot, no default weights/capacity."""

    def admit(self, intent: Intent) -> str:
        """Exactly queued/deferred/unsupported; never silently drop."""
        ...


class SessionCommands(Protocol):
    """BE1 owns atomic current compare-and-apply +durable original-ID/body dedup.

    Authenticate scope/actor/source/mandatory gates at the EFFECT transaction, not
    merely at enqueue. Manual override/disable advances config+automation epoch;
    old observed automation is refused even if concurrently already dispatched.
    lookup returns authenticated immutable native receipt or no known receipt;
    absence is NOT proof another concurrent invocation cannot still commit.
    execute must resolve/replay same identity after timeout without new effects.
    Receipt.applied reflects that historical command, not current config after override.
    """

    def lookup(self, intent: Intent) -> EffectReceipt | None: ...
    def reconcile(self, intent: Intent) -> EffectReceipt | None:
        """No NEW effect. Native barrier may durably fence original stale command
        and return exact stale/rejected receipt, or recover prior applied receipt.
        Return None while uncertain. Never infer cancellation from missing lookup.
        """
        ...

    def execute(self, intent: Intent) -> EffectReceipt: ...
