"""MEMORY/ASSUMED authority and consumer fixtures, NOT school/BE1/12 proof."""

import copy
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from itertools import count
from types import SimpleNamespace
from unittest.mock import Mock

from sketch2life.application.activity_execution import (
    ActivityExecutionService,
    ActivityOutcomeDelivery,
    Command,
)
from sketch2life.application.ports.activity_execution import Actor, OutcomeAck
from sketch2life.domain.activity_execution.model import (
    Action,
    Adaptations,
    Assignment,
    Audience,
    ChildAge,
    Confirmation,
    Definition,
    ExecutionProof,
    State,
    effective,
    fail,
)
from sketch2life.domain.knowledge_video.model import ExactRef

NOW = datetime(2026, 10, 19, tzinfo=UTC)


def ref(name, hash="a" * 64):
    return ExactRef(name, 1, hash)


def definition(**changes):
    return Definition(
        **dict(
            source_ref=ref("activity"),
            definition_ref=ref("definition"),
            objective_refs=(ref("objective"),),
            title="Fixture activity",
            topic_ids=("plants", "colors"),
            age_min_months=36,
            age_max_months=100,
            materials=("paper",),
            instructions="Observe together",
            safety="Teacher supervises",
            duration_note="Teacher sets pace",
            form="group",
            observation_prompts=("Record only observed actions",),
        )
        | changes
    )


def audience(**changes):
    return Audience(
        **dict(
            session_id="session",
            revision=2,
            group_ids=("group",),
            children=(ChildAge("child1", 40), ChildAge("child2", 90)),
        )
        | changes
    )


def assignment(**changes):
    return Assignment(
        **dict(
            assignment_id="assignment",
            organization_id="school",
            selected_by="teacher",
            revision=1,
            source=definition(),
            edits=Adaptations(),
            audience=audience(),
            policy=ref("policy"),
            state=State.SELECTED,
            created_at=NOW,
            updated_at=NOW,
        )
        | changes
    )


def proof(row):
    return ExecutionProof(
        row.binding_digest(),
        row.policy,
        tuple(c.child_id for c in row.audience.children),
        ref("adaptation.review"),
    )


def prepared(state=State.READY):
    row = assignment()
    row = row.transition(
        Action.CONFIRM, row.revision, NOW, confirmation=Confirmation(True, True), proof=proof(row)
    )
    if state in {State.RUNNING, State.COMPLETED, State.INTERRUPTED}:
        row = row.transition(
            Action.START, row.revision, NOW, confirmation=Confirmation(True, True), proof=proof(row)
        )
    if state is State.COMPLETED:
        row = row.transition(Action.FINISH, row.revision, NOW)
    if state is State.INTERRUPTED:
        row = row.transition(Action.INTERRUPT, row.revision, NOW, reason="fixture reason")
    return row


def actor(**changes):
    return Actor(
        **dict(
            principal_id="teacher", organization_id="school", session_id="session", client_key="key"
        )
        | changes
    )


def select(**changes):
    return Command(
        **dict(action=Action.SELECT, source_ref=ref("activity"), group_ids=("group",)) | changes
    )


class MemoryStore:
    def __init__(self):
        self.rows, self.receipts, self.history, self.events, self.acks = {}, {}, [], {}, {}
        self.active = False
        self.fail = None

    @contextmanager
    def transaction(self, org, session):
        assert not self.active
        old = copy.deepcopy((self.rows, self.receipts, self.history, self.events, self.acks))
        self.scope, self.active = (org, session), True
        try:
            yield self
            if self.fail == "commit":
                raise RuntimeError("synthetic_sensitive")
        except Exception:
            self.rows, self.receipts, self.history, self.events, self.acks = old
            raise
        finally:
            self.active = False

    def load(self, identity):
        assert self.active
        return self.rows.get((*self.scope, identity))

    def receipt(self, principal, key):
        assert self.active
        return self.receipts.get((*self.scope, principal, key))

    def write(self, before, receipt, event):
        assert self.active and self.load(receipt.assignment.assignment_id) == before
        key = (*self.scope, receipt.actor.principal_id, receipt.actor.client_key)
        if key in self.receipts:
            fail("WRITE_CONFLICT")
        self.rows[(*self.scope, receipt.assignment.assignment_id)] = receipt.assignment
        self.receipts[key] = receipt
        self.history.append(receipt)
        if self.fail == "write":
            raise RuntimeError("synthetic_sensitive")
        if event:
            self.events[(*self.scope, event.event_id)] = event

    def event(self, identity):
        assert self.active
        event = self.events.get((*self.scope, identity))
        return None if event is None else (event, self.acks.get((*self.scope, identity)))

    def acknowledge(self, event, ack):
        assert self.active
        if (ack.event_id, ack.event_digest) != (event.event_id, event.fingerprint()):
            fail("INVALID_ACK")
        old = self.acks.get((*self.scope, event.event_id))
        if old is not None and old != ack:
            fail("ACK_CONFLICT")
        self.acks[(*self.scope, event.event_id)] = ack
        if self.fail == "ack":
            raise RuntimeError("synthetic_sensitive")


class AssumedBoundary:
    def __init__(self, store):
        self.store = store
        self.definition, self.audience, self.policy = definition(), audience(), ref("policy")
        self.held = False
        self.denied = None
        self.on_check = None
        self.fail_exit = False
        self.checked_children = []
        self.denied_children = set()
        self.hazard = False

    @contextmanager
    def guard(self, a):
        if a.principal_id not in {"teacher", "teacher2", "owner.notice"} or (
            a.organization_id,
            a.session_id,
        ) != ("school", "session"):
            fail("FORBIDDEN")
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("synthetic_sensitive")
        finally:
            self.held = False

    def selection(self, source, groups):
        assert self.held and not self.store.active
        if source != self.definition.source_ref:
            fail("SOURCE_MISMATCH")
        return self.definition, replace(self.audience, group_ids=groups), self.policy

    def check(self, a, row, phase):
        assert self.held
        if self.on_check:
            self.on_check(a, row, phase)
        if self.denied == phase:
            fail("FORBIDDEN")
        if phase not in {"notice", "deliver", "replay"} and (
            row.source != self.definition
            or row.audience != self.audience
            or row.policy != self.policy
        ):
            fail("SOURCE_INELIGIBLE")
        if phase == "notice" and a.principal_id != "owner.notice":
            fail("FORBIDDEN")

    def check_child(self, row, child):
        assert self.held and not self.store.active
        self.checked_children.append(child.child_id)
        # Fixture policy ONLY; no production numeric policy selected.
        if child.child_id in self.denied_children or not (
            row.source.age_min_months <= child.age_months <= row.source.age_max_months
        ):
            fail("POLICY_DENIED")

    def preparation(self, row, confirmation):
        assert self.held and not self.store.active
        if self.hazard or "hazard" in effective(row.source, row.edits).materials:
            fail("POLICY_DENIED")
        return proof(row)


def harness():
    store = MemoryStore()
    boundary = AssumedBoundary(store)
    consumer = Mock()
    accepted = {}

    def send(event):
        assert boundary.held and not store.active
        fingerprint = event.fingerprint()
        if event.event_id in accepted:
            assert accepted[event.event_id].event_digest == fingerprint
        else:
            accepted[event.event_id] = OutcomeAck(event.event_id, fingerprint, ref("be1.receipt"))
        return accepted[event.event_id]

    consumer.send.side_effect = send
    counter = count(1)
    service = ActivityExecutionService(
        boundary,
        store,
        clock=lambda: NOW,
        assignment_ids=lambda: "assignment." + str(next(counter)),
    )
    return SimpleNamespace(
        store=store,
        boundary=boundary,
        consumer=consumer,
        accepted=accepted,
        service=service,
        delivery=ActivityOutcomeDelivery(boundary, store, consumer),
        key_counter=count(1),
    )


def execute(h, action=Action.SELECT, **changes):
    if action is Action.SELECT and "assignment_id" not in changes:
        cmd = select(**changes)
    else:
        row = next(iter(h.store.rows.values()))
        cmd = Command(
            **dict(
                action=action,
                assignment_id=row.assignment_id,
                expected_revision=row.revision,
                confirmation=Confirmation(True, True)
                if action in {Action.CONFIRM, Action.START}
                else None,
                reason="fixture reason" if action in {Action.SKIP, Action.INTERRUPT} else None,
            )
            | changes
        )
    return h.service.execute(actor(client_key="key." + str(next(h.key_counter))), cmd)
