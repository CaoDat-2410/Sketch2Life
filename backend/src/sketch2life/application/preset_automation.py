"""Intent-first manual/conditional control; external effect never inside own SQL tx."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime

from sketch2life.application.ports.preset_automation import (
    Authority,
    Decision,
    LocalReceipt,
    QueuePolicy,
    SessionCommands,
    SessionView,
    Store,
)
from sketch2life.application.preset_governance import receipt_key
from sketch2life.domain.preset_automation.model import (
    Intent,
    IntentState,
    Library,
    Source,
    Stamp,
    State,
    digest,
    fail,
    identifier,
    matches,
    reason,
)


@dataclass(frozen=True)
class ControlRequest:
    client_key: str
    kind: str
    observed: Stamp
    action: str
    value: str
    reason: str
    record_id: str | None = None
    source_version: int | None = None
    source_hash: str | None = None

    def __post_init__(self) -> None:
        identifier(self.client_key)
        reason(self.reason)
        if type(self.observed) is not Stamp or self.kind not in {"pin", "override", "disable"}:
            fail("INVALID_REQUEST")
        if self.kind == "pin":
            if not self.record_id or self.source_version is None or not self.source_hash:
                fail("INVALID_SOURCE")
        elif any(v is not None for v in (self.record_id, self.source_version, self.source_hash)):
            fail("INVALID_SOURCE")


class PresetAutomation:
    def __init__(
        self,
        store: Store,
        authority: Authority,
        commands: SessionCommands,
        queue: QueuePolicy,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.store, self.authority, self.commands, self.queue, self.clock = (
            store,
            authority,
            commands,
            queue,
            clock,
        )

    @staticmethod
    def _view(view: SessionView, org: str, session: str) -> SessionView:
        view = replace(view)
        if (view.organization_id, view.session_id) != (org, session):
            fail("SCOPE_DENIED")
        return view

    def prepare(self, org: str, session: str, actor: str, request: ControlRequest) -> Intent:
        request = replace(request)
        fingerprint = digest(asdict(request))
        key = receipt_key(actor, request.client_key)
        with self.authority.hold(org, actor, session_id=session) as guard:
            guard.check(request.kind)
            # Separate library read; source authority fences verify current source through commit.
            source = None
            source_available = True
            if request.kind == "pin":
                with self.store.transaction(org, "library") as library_rows:
                    library = library_rows.get(request.record_id or "")
                    if type(library) is not Library:
                        fail("NOT_FOUND")
                    version = library.target(request.source_version or 0, request.source_hash or "")
                    source_available = version.state is State.PUBLISHED
                    source = Source(library.record_id, version.number, version.body)
            with self.store.transaction(org, session) as rows:
                old = rows.get(key)
                if old is not None:
                    if (
                        type(old) is not LocalReceipt
                        or old.fingerprint != fingerprint
                        or (old.actor, old.client_key) != (actor, request.client_key)
                    ):
                        fail("IDEMPOTENCY_CONFLICT")
                    result = rows.get(old.object_key)
                    if type(result) is not Intent:
                        fail("STORAGE_CORRUPT")
                    guard.check_current()
                    return result
                if not source_available:
                    fail("SOURCE_UNAVAILABLE")
                view = self._view(guard.session(), org, session)
                if view.observed != request.observed or (request.kind == "pin" and not view.draft):
                    fail("STALE_CONTEXT")
                source = source if source is not None else view.source
                if source is None:
                    fail("PIN_REQUIRED")
                guard.source(source)
                guard.validate_body(source.body)
                intent = Intent(
                    digest([org, session, actor, request.client_key]),
                    org,
                    session,
                    actor,
                    1,
                    request.kind,
                    source,
                    view.observed,
                    view.policy_ref,
                    request.action,
                    request.value,
                    request.reason,
                    self.clock(),
                )
                guard.intent(intent, view)
                guard.check_current()
                rows.put(intent.intent_id, None, intent)
                rows.put(
                    key,
                    None,
                    LocalReceipt(
                        actor, request.client_key, fingerprint, intent.intent_id, 1, source.version
                    ),
                )
                guard.check_current()
                return intent

    def evaluate(self, org: str, session: str, actor: str, event_id: str, rule_id: str) -> Decision:
        identifier(event_id)
        identifier(rule_id)
        key = "decision-" + digest([actor, event_id, rule_id])
        with self.authority.hold(org, actor, session_id=session) as guard:
            guard.check("evaluate")
            with self.store.transaction(org, session) as rows:
                old = rows.get(key)
                if old is not None:
                    if type(old) is not Decision:
                        fail("STORAGE_CORRUPT")
                    guard.check_current()
                    return old
                view = self._view(guard.session(), org, session)
                if view.source is None:
                    fail("PIN_REQUIRED")
                guard.source(view.source)
                guard.validate_body(view.source.body)
                rules = (*view.source.body.stage_rules, *view.source.body.notification_rules)
                rule = next((r for r in rules if r.rule_id == rule_id), None)
                if rule is None:
                    fail("UNKNOWN_RULE")
                guard.rule(rule, view)
                intent = None
                outcome = "disabled"
                now = self.clock()
                if view.automation_enabled:
                    outcome = "not_matched"
                    if matches(rule, stage=view.stage, help_pending=view.help_pending):
                        intent = Intent(
                            digest([org, session, key]),
                            org,
                            session,
                            actor,
                            1,
                            "automation",
                            view.source,
                            view.observed,
                            view.policy_ref,
                            rule.action,
                            rule.rule_id,
                            "matched-" + rule.rule_id,
                            now,
                        )
                        outcome = self.queue.admit(intent)
                        if outcome not in {"queued", "deferred", "unsupported"}:
                            fail("INVALID_QUEUE_OUTCOME")
                        if outcome == "deferred":
                            intent = replace(
                                intent, state=IntentState.DEFERRED, disposition="deferred"
                            )
                        elif outcome == "unsupported":
                            intent = None
                if intent is not None:
                    guard.intent(intent, view)
                decision = Decision(
                    key,
                    org,
                    session,
                    actor,
                    rule_id,
                    view.source,
                    view.observed,
                    view.policy_ref,
                    outcome,
                    intent.intent_id if intent else None,
                    now,
                )
                guard.check_current()
                if intent is not None:
                    rows.put(intent.intent_id, None, intent)
                rows.put(key, None, decision)
                guard.check_current()
                return decision

    def dispatch(self, org: str, session: str, actor: str, intent_id: str) -> Intent:
        """Explicit single attempt/recovery, no loop or implicit scheduler/retry policy."""
        with self.authority.hold(org, actor, session_id=session) as guard:
            guard.check("dispatch")
            with self.store.transaction(org, session) as rows:
                intent = rows.get(intent_id)
                if type(intent) is not Intent:
                    fail("NOT_FOUND")
                if (intent.organization_id, intent.session_id, intent.actor) != (
                    org,
                    session,
                    actor,
                ):
                    fail("SCOPE_DENIED")
                if intent.state not in {
                    IntentState.QUEUED,
                    IntentState.DEFERRED,
                    IntentState.SENDING,
                }:
                    guard.check_current()
                    return intent
                if intent.state is not IntentState.SENDING:
                    view = self._view(guard.session(), org, session)
                    guard.source(intent.source)
                    guard.validate_body(intent.source.body)
                    guard.intent(intent, view)
                    stale = (
                        view.observed != intent.observed
                        or view.policy_ref != intent.policy_ref
                        or (
                            intent.kind == "automation"
                            and (not view.automation_enabled or view.source != intent.source)
                        )
                        or (intent.kind == "pin" and not view.draft)
                    )
                    if not stale and intent.kind == "automation":
                        rule = next(
                            (
                                r
                                for r in (
                                    *intent.source.body.stage_rules,
                                    *intent.source.body.notification_rules,
                                )
                                if r.rule_id == intent.value and r.action == intent.action
                            ),
                            None,
                        )
                        if rule is None:
                            fail("UNKNOWN_RULE")
                        guard.rule(rule, view)
                        stale = not matches(rule, stage=view.stage, help_pending=view.help_pending)
                    sending = intent.transition(
                        IntentState.STALE if stale else IntentState.SENDING,
                        "stale-context" if stale else "sending",
                    )
                    rows.put(intent_id, intent, sending)
                    intent = sending
                guard.check_current()
            if intent.state is not IntentState.SENDING:
                return intent
            # Lookup first: an old committed command must be recovered even after override.
            try:
                effect = self.commands.lookup(intent)
                if effect is None:
                    effect = self.commands.reconcile(intent)
                if effect is None:
                    view = self._view(guard.session(), org, session)
                    if (
                        view.observed != intent.observed
                        or view.policy_ref != intent.policy_ref
                        or (intent.kind == "automation" and not view.automation_enabled)
                    ):
                        return intent  # Unknown in-flight commit: do NOT fake stale/cancelled.
                    guard.check(intent.kind)
                    guard.source(intent.source)
                    guard.validate_body(intent.source.body)
                    guard.intent(intent, view)
                    if intent.kind == "automation":
                        rule = next(
                            (
                                r
                                for r in (
                                    *intent.source.body.stage_rules,
                                    *intent.source.body.notification_rules,
                                )
                                if r.rule_id == intent.value and r.action == intent.action
                            ),
                            None,
                        )
                        if rule is None or view.source != intent.source:
                            return intent
                        guard.rule(rule, view)
                        if not matches(rule, stage=view.stage, help_pending=view.help_pending):
                            return intent
                    guard.check_current()
                    effect = self.commands.execute(intent)
                effect = replace(effect)
                effect.validate_for(intent)
            except (TimeoutError, ConnectionError, ValueError, TypeError):
                return intent  # Original ID remains recoverable; no false rollback/completion.
            with self.store.transaction(org, session) as rows:
                current = rows.get(intent_id)
                if type(current) is not Intent or current.hash != intent.hash:
                    fail("STORAGE_CORRUPT")
                old_effect = rows.get("effect-" + intent_id)
                if old_effect is not None:
                    if old_effect != effect:
                        fail("RECEIPT_CONFLICT")
                    guard.check_current()
                    return current
                if current.state is not IntentState.SENDING:
                    fail("STALE_REVISION")
                finished = current.transition(IntentState(effect.outcome), effect.reason)
                rows.put("effect-" + intent_id, None, effect)
                rows.put(intent_id, current, finished)
                guard.check_current()
                return finished

    def reconcile(self, org: str, session: str, actor: str, intent_id: str) -> Intent:
        """Queued work can become stale; sending work requires real receipt recovery."""
        with self.authority.hold(org, actor, session_id=session) as guard:
            guard.check("reconcile")
            with self.store.transaction(org, session) as rows:
                current = rows.get(intent_id)
                if type(current) is not Intent:
                    fail("NOT_FOUND")
                if current.actor != actor:
                    fail("SCOPE_DENIED")
                if current.state in {IntentState.QUEUED, IntentState.DEFERRED}:
                    view = self._view(guard.session(), org, session)
                    if view.observed != current.observed or view.policy_ref != current.policy_ref:
                        after = current.transition(IntentState.STALE, "stale-context")
                        rows.put(intent_id, current, after)
                        current = after
                guard.check_current()
                if current.state is not IntentState.SENDING:
                    return current
        return self.dispatch(org, session, actor, intent_id)
