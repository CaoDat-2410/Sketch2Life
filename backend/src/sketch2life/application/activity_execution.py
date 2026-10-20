"""Candidate11 guarded assignment lifecycle and bounded explicit one-event delivery."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from sketch2life.application.ports.activity_execution import (
    Actor,
    Boundary,
    OutcomeAck,
    OutcomeConsumer,
    OutcomeEvent,
    Receipt,
    Store,
)
from sketch2life.domain.activity_execution.model import (
    TERMINAL,
    Action,
    Adaptations,
    Assignment,
    Confirmation,
    State,
    digest,
    exact,
    fail,
    ids,
)
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    require_id,
    require_revision,
)


@dataclass(frozen=True, slots=True)
class Command:
    action: Action
    assignment_id: str | None = None
    expected_revision: int | None = None
    source_ref: ExactRef | None = None
    group_ids: tuple[str, ...] | None = None
    edits: Adaptations | None = None
    confirmation: Confirmation | None = None
    reason: str | None = None
    evidence_refs: tuple[ExactRef, ...] = ()

    def __post_init__(self) -> None:
        from sketch2life.domain.activity_execution.model import text

        if type(self.action) is not Action:
            fail("INVALID_COMMAND")
        if self.assignment_id is not None:
            require_id(self.assignment_id)
            if self.expected_revision is None:
                fail("PRECONDITION_REQUIRED")
            require_revision(self.expected_revision)
        elif self.action is not Action.SELECT or self.expected_revision is not None:
            fail("INVALID_COMMAND")
        if self.action is Action.SELECT:
            if self.source_ref is None or self.group_ids is None or self.confirmation is not None:
                fail("INVALID_COMMAND")
            exact(self.source_ref)
            ids(self.group_ids)
            if self.edits is not None:
                if type(self.edits) is not Adaptations:
                    fail("INVALID_COMMAND")
                replace(self.edits)
            if self.reason is not None or self.evidence_refs:
                fail("INVALID_COMMAND")
        elif self.source_ref is not None or self.group_ids is not None or self.edits is not None:
            fail("INVALID_COMMAND")
        if self.action in {Action.CONFIRM, Action.START}:
            if (
                type(self.confirmation) is not Confirmation
                or self.reason is not None
                or self.evidence_refs
            ):
                fail("INVALID_COMMAND")
            replace(self.confirmation)
        elif self.confirmation is not None:
            fail("INVALID_COMMAND")
        if self.action in {Action.SKIP, Action.INTERRUPT} and self.reason is None:
            fail("REASON_REQUIRED")
        if self.reason is not None:
            text(self.reason, 200)
        if type(self.evidence_refs) is not tuple or len(self.evidence_refs) > 64:
            fail("INVALID_EVIDENCE")
        for ref in self.evidence_refs:
            exact(ref)
        if self.group_ids is not None:
            object.__setattr__(self, "group_ids", tuple(sorted(self.group_ids)))

    def fingerprint(self) -> str:
        replace(self)
        return digest(tuple(getattr(self, name) for name in self.__dataclass_fields__))


def event_id(row: Assignment) -> str:
    return "activity." + digest((row.organization_id, row.assignment_id, row.revision))


def scoped(actor: Actor, row: Assignment) -> None:
    if (row.organization_id, row.audience.session_id) != (actor.organization_id, actor.session_id):
        fail("SCOPE_MISMATCH")


@dataclass(frozen=True, slots=True)
class Result:
    assignment: Assignment
    applied_revision: int
    replayed: bool
    outcome_delivery: str  # not_required/pending/acknowledged, NOT portfolio saved.


class ActivityExecutionService:
    def __init__(
        self,
        boundary: Boundary,
        store: Store,
        *,
        clock: Callable[[], datetime],
        assignment_ids: Callable[[], str],
    ) -> None:
        self.boundary, self.store, self.clock, self.ids = boundary, store, clock, assignment_ids

    def execute(self, actor: Actor, cmd: Command) -> Result:
        actor, cmd = replace(actor), replace(cmd)
        try:
            with self.boundary.guard(actor) as access:
                with self.store.transaction(actor.organization_id, actor.session_id) as tx:
                    old = tx.receipt(actor.principal_id, actor.client_key)
                    before = tx.load(cmd.assignment_id) if cmd.assignment_id is not None else None
                if old is not None:
                    old = replace(old)
                    if old.actor != actor or old.body_digest != cmd.fingerprint():
                        fail("IDEMPOTENCY_CONFLICT")
                    with self.store.transaction(actor.organization_id, actor.session_id) as tx:
                        current = tx.load(old.assignment.assignment_id)
                        if current is None or current.revision < old.assignment.revision:
                            fail("STORAGE_CORRUPT")
                        current = replace(current)
                        scoped(actor, current)
                        access.check(actor, current, "replay")
                        delivery = "not_required"
                        if current.state in TERMINAL:
                            stored_event = tx.event(event_id(current))
                            if stored_event is None:
                                fail("STORAGE_CORRUPT")
                            delivery = "acknowledged" if stored_event[1] is not None else "pending"
                        access.check(actor, current, "replay")
                    return Result(current, old.assignment.revision, True, delivery)
                if cmd.assignment_id is not None and before is None:
                    fail("NOT_FOUND")
                if before is not None:
                    before = replace(before)
                    if (before.organization_id, before.audience.session_id) != (
                        actor.organization_id,
                        actor.session_id,
                    ):
                        fail("SCOPE_MISMATCH")
                    if cmd.expected_revision is None:
                        fail("PRECONDITION_REQUIRED")
                    before.expect(cmd.expected_revision, self.clock())
                now = self.clock()
                if cmd.action is Action.SELECT:
                    if cmd.source_ref is None or cmd.group_ids is None:
                        fail("INVALID_COMMAND")
                    source, audience, policy = access.selection(cmd.source_ref, cmd.group_ids)
                    if (
                        source.source_ref != cmd.source_ref
                        or audience.session_id != actor.session_id
                        or (audience.group_ids != cmd.group_ids)
                    ):
                        fail("SOURCE_MISMATCH")
                    if before is None:
                        after = Assignment(
                            self.ids(),
                            actor.organization_id,
                            actor.principal_id,
                            1,
                            source,
                            cmd.edits or Adaptations(),
                            audience,
                            policy,
                            State.SELECTED,
                            now,
                            now,
                        )
                    else:
                        after = before.reselect(
                            before.revision,
                            source,
                            cmd.edits or Adaptations(),
                            audience,
                            policy,
                            now,
                        )
                    access.check(actor, after, "select")
                else:
                    if before is None:
                        fail("NOT_FOUND")
                    access.check(actor, before, "prepare")
                    proof = None
                    if cmd.action in {Action.CONFIRM, Action.START}:
                        if cmd.confirmation is None:
                            fail("NOT_READY")
                        for child in before.audience.children:
                            access.check_child(before, child)
                        proof = access.preparation(before, cmd.confirmation)
                    after = before.transition(
                        cmd.action,
                        before.revision,
                        now,
                        confirmation=cmd.confirmation,
                        proof=proof,
                        reason=cmd.reason,
                        evidence_refs=cmd.evidence_refs,
                    )
                receipt = Receipt(actor, cmd.fingerprint(), after)
                event = (
                    OutcomeEvent(event_id(after), after, now, actor.principal_id)
                    if after.state in TERMINAL
                    else None
                )
                with self.store.transaction(actor.organization_id, actor.session_id) as tx:
                    if tx.load(after.assignment_id) != before:
                        fail("STALE_REVISION")
                    access.check(actor, after, "commit")
                    tx.write(before, receipt, event)
                    access.check(actor, after, "commit")
            return Result(after, after.revision, False, "pending" if event else "not_required")
        except VideoError:
            raise
        except Exception:
            # Commit/guard exit may follow actual commit; replay original key,
            # never claim rollback or fabricate external outcome saved.
            fail("DEPENDENCY_UNAVAILABLE")

    def invalidate(self, actor: Actor, assignment_id: str, expected: int, cause: str) -> Result:
        """Internal authenticated owner notice, NOT public client authority endpoint."""
        actor = replace(actor)
        require_id(assignment_id)
        require_id(cause)
        require_revision(expected)
        fingerprint = digest(("invalidate", assignment_id, expected, cause))
        try:
            with self.boundary.guard(actor) as access:
                with self.store.transaction(actor.organization_id, actor.session_id) as tx:
                    prior = tx.receipt(actor.principal_id, actor.client_key)
                    current = tx.load(assignment_id)
                    if current is None:
                        fail("NOT_FOUND")
                    current = replace(current)
                    scoped(actor, current)
                    if prior is not None:
                        if prior.actor != actor or prior.body_digest != fingerprint:
                            fail("IDEMPOTENCY_CONFLICT")
                        access.check(actor, current, "notice")
                        delivery = "not_required"
                        if current.state in TERMINAL:
                            stored_event = tx.event(event_id(current))
                            if stored_event is None:
                                fail("STORAGE_CORRUPT")
                            delivery = "acknowledged" if stored_event[1] is not None else "pending"
                        return Result(current, prior.assignment.revision, True, delivery)
                    access.check(actor, current, "notice")
                    after = current.invalidate(expected, cause, self.clock())
                    tx.write(current, Receipt(actor, fingerprint, after), None)
                    access.check(actor, after, "notice")
                return Result(after, after.revision, False, "not_required")
        except VideoError:
            raise
        except Exception:
            fail("DEPENDENCY_UNAVAILABLE")


class ActivityOutcomeDelivery:
    def __init__(self, boundary: Boundary, store: Store, consumer: OutcomeConsumer) -> None:
        self.boundary, self.store, self.consumer = boundary, store, consumer

    def deliver(self, actor: Actor, identity: str) -> str:
        """One explicitly requested event attempt, no scheduler/unlimited loop/lease.
        Concurrent sends allowed ONLY because adopted consumer must durably dedup
        same event ID/body. No distributed exactly-once execution claim.
        """
        actor = replace(actor)
        require_id(identity)
        try:
            with self.boundary.guard(actor) as access:
                with self.store.transaction(actor.organization_id, actor.session_id) as tx:
                    stored = tx.event(identity)
                if stored is None:
                    fail("NOT_FOUND")
                event, ack = stored
                event = replace(event)
                scoped(actor, event.assignment)
                if event.event_id != identity:
                    fail("INVALID_EVENT")
                access.check(actor, event.assignment, "deliver")
                if ack is not None:
                    ack = replace(ack)
                    if (ack.event_id, ack.event_digest) != (identity, event.fingerprint()):
                        fail("INVALID_ACK")
                    return "acknowledged"
                try:
                    ack = self.consumer.send(event)  # Outside DB transaction.
                    if type(ack) is not OutcomeAck:
                        return "pending"
                    ack = replace(ack)
                    if (ack.event_id, ack.event_digest) != (event.event_id, event.fingerprint()):
                        return "pending"
                    with self.store.transaction(actor.organization_id, actor.session_id) as tx:
                        access.check(actor, event.assignment, "deliver")
                        tx.acknowledge(event, ack)
                        access.check(actor, event.assignment, "deliver")
                    return "acknowledged"
                except Exception:
                    return "pending"
        except VideoError:
            raise
        except Exception:
            fail("DEPENDENCY_UNAVAILABLE")
