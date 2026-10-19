"""Synthetic ASSUMED owner policy/BE1 handler. Not actual integration acceptance."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import UTC, datetime
from threading import RLock

from sketch2life.application.ports.preset_automation import SessionView
from sketch2life.application.preset_automation import ControlRequest, PresetAutomation
from sketch2life.application.preset_governance import PresetGovernance
from sketch2life.contracts.schemas.preset_automation import PresetCommand
from sketch2life.domain.preset_automation.model import (
    Body,
    EffectReceipt,
    Library,
    Review,
    Rule,
    Source,
    Stamp,
    State,
    Version,
    fail,
)
from sketch2life.infrastructure.preset_automation.codec import decode, encode
from sketch2life.infrastructure.preset_automation.sql import revision, validate_change

NOW = datetime(2026, 10, 19, 12, tzinfo=UTC)


def body(**changes):
    values = dict(
        title="Synthetic classroom preset",
        effective_age_policy_ref="assumed-age-v1",
        tool_policy_ref="assumed-tools-v1",
        canvas_mode="shared",
        assistance_policy_ref="assumed-assistance-v1",
        stage_rules=(Rule("stage-help", "stage_is", "drawing", "notify_teacher"),),
        notification_rules=(Rule("pending-help", "help_pending", "yes", "request_support"),),
        video_policy_ref="assumed-video-v1",
        activity_policy_ref="assumed-activity-v1",
        assessment_policy_ref="assumed-assessment-v1",
    )
    return Body(**(values | changes))


def library(published=False):
    b = body()
    reviews = (
        tuple(
            Review(dim, "preset", 1, b.hash, dim, "reviewer", "assumed-review-v1", "approve")
            for dim in ("safety", "pedagogical")
        )
        if published
        else ()
    )
    v = Version(
        1,
        b,
        State.PUBLISHED if published else State.DRAFT,
        "author",
        NOW,
        reviews,
        ("safety", "pedagogical", "assumed-review-v1") if published else None,
    )
    return Library("preset", "school", 1, (v,), "create", "author", NOW)


def command(action="create", key=None, record=None, version=1, **values):
    data = dict(action=action, client_request_id=key or action, **values)
    if action == "create":
        data.setdefault("body", asdict(body()))
    else:
        lib = record or library()
        data.update(
            record_id=lib.record_id,
            target_version=version,
            target_hash=lib.versions[version - 1].body.hash,
        )
    return PresetCommand.model_validate_json(__import__("json").dumps(data))


class Memory:
    def __init__(self):
        self.data, self.history_data = {}, {}
        self.lock = RLock()
        self.in_tx = False
        self.fail_commit = False
        self.fail_effect_write = False

    @contextmanager
    def transaction(self, org, scope):
        with self.lock:
            data, hist = deepcopy(self.data), deepcopy(self.history_data)
            self.in_tx = True
            owner = self

            class Rows:
                def get(self, key):
                    return data.get((org, scope, key))

                def history(self, key, revision):
                    return hist.get((org, scope, key, revision))

                def put(self, key, before, value):
                    if owner.fail_effect_write and isinstance(value, EffectReceipt):
                        raise RuntimeError("assumed ACK write failure")
                    if self.get(key) != before:
                        fail("STALE_REVISION")
                    validate_change(before, value)
                    data[org, scope, key] = decode(encode(value))
                    hist[org, scope, key, revision(value)] = value

            try:
                yield Rows()
                if self.fail_commit:
                    raise RuntimeError("assumed commit failure")
                self.data, self.history_data = data, hist
            finally:
                self.in_tx = False


class Guards:
    def __init__(self):
        self.view = SessionView(
            "school",
            "session",
            Stamp(1, 1, 1, 1),
            Source("preset", 1, body()),
            "assumed-control-v1",
            "drawing",
            True,
            True,
            True,
        )
        self.denied = set()
        self.recalled = False
        self.current = True
        self.calls = []
        self.fail_check_number = None

    @contextmanager
    def hold(self, org, actor, *, session_id=None):
        if org != "school" or actor not in {"author", "teacher", "reviewer", "publisher"}:
            fail("SCOPE_DENIED")
        if session_id is not None and session_id != "session":
            fail("SCOPE_DENIED")
        self.actor = actor
        yield self

    def check(self, action):
        self.calls.append(action)
        expected = {
            "create": "author",
            "edit": "author",
            "submit_review": "author",
            "record_review": "reviewer",
            "request_changes": "reviewer",
            "publish": "publisher",
            "recall": "publisher",
            "archive": "publisher",
        }
        if action in self.denied or self.actor != expected.get(action, "teacher"):
            fail("FORBIDDEN")
        self.check_current()

    def check_current(self):
        self.calls.append("current")
        if not self.current or self.calls.count("current") == self.fail_check_number:
            fail("REVOKED")

    def validate_body(self, b):
        if "body" in self.denied or not b.tool_policy_ref.startswith("assumed-"):
            fail("POLICY_UNAVAILABLE")

    def review(self, lib, proof):
        if "review-proof" in self.denied or proof.policy_ref != "assumed-review-v1":
            fail("REVIEW_UNAVAILABLE")

    def publication(self, lib, version, refs):
        if "publication-proof" in self.denied or refs[2] != "assumed-review-v1":
            fail("REVIEW_UNAVAILABLE")

    def session(self):
        return self.view

    def source(self, source):
        if self.recalled or "source" in self.denied:
            fail("SOURCE_UNAVAILABLE")

    def rule(self, rule, view):
        if "rule" in self.denied or view.policy_ref != "assumed-control-v1":
            fail("POLICY_UNAVAILABLE")

    def intent(self, intent, view):
        if "intent" in self.denied or intent.value == "bypass-review":
            fail("POLICY_UNAVAILABLE")


class Queue:
    result = "queued"

    def admit(self, intent):
        return self.result


class Commands:
    def __init__(self, guards, memory):
        self.guards, self.memory = guards, memory
        self.receipts, self.count = {}, 0
        self.timeout_before = self.timeout_after = False
        self.foreign = False
        self.resolve_stale = False
        self.hook = None

    def lookup(self, intent):
        assert not self.memory.in_tx
        return self.receipts.get(intent.intent_id)

    def reconcile(self, intent):
        assert not self.memory.in_tx
        old = self.receipts.get(intent.intent_id)
        if old is not None:
            return old
        if self.resolve_stale and self.guards.view.observed != intent.observed:
            receipt = EffectReceipt(
                intent.intent_id,
                "school",
                "session",
                intent.hash,
                "stale",
                intent.observed,
                self.guards.view.observed,
                "native-fence-receipt",
                "stale-context",
            )
            self.receipts[intent.intent_id] = receipt
            return receipt
        return None

    def execute(self, intent):
        assert not self.memory.in_tx
        if self.timeout_before:
            raise TimeoutError()
        if self.hook:
            self.hook()
        old = self.receipts.get(intent.intent_id)
        if old is not None:
            old.validate_for(intent)
            return old
        view = self.guards.view
        stale = view.observed != intent.observed
        effective = view.observed
        if not stale:
            self.count += 1
            if intent.kind != "automation":
                effective = replace(
                    view.observed,
                    config=view.observed.config + 1,
                    automation=view.observed.automation + 1,
                )
                self.guards.view = replace(
                    view,
                    observed=effective,
                    source=intent.source if intent.kind == "pin" else view.source,
                    automation_enabled=False
                    if intent.kind == "disable"
                    else view.automation_enabled,
                )
        receipt = EffectReceipt(
            intent.intent_id,
            "school",
            "session",
            intent.hash,
            "stale" if stale else "applied",
            intent.observed,
            effective,
            "assumed-native-receipt",
            "stale-context" if stale else "applied",
        )
        self.receipts[intent.intent_id] = receipt
        if self.timeout_after:
            raise TimeoutError()
        return replace(receipt, session_id="foreign") if self.foreign else receipt


def environment():
    memory, guards, queue = Memory(), Guards(), Queue()
    commands = Commands(guards, memory)
    service = PresetAutomation(memory, guards, commands, queue, clock=lambda: NOW)
    governance = PresetGovernance(memory, guards, clock=lambda: NOW, new_id=lambda: "preset")
    return memory, guards, commands, queue, service, governance


def request(kind="override", key="control", stamp=None):
    return ControlRequest(
        key,
        kind,
        stamp or Stamp(1, 1, 1, 1),
        {"override": "set_tool_policy", "disable": "disable_automation", "pin": "pin"}[kind],
        "assumed-tools-v2",
        "Teacher chose local setting",
        "preset" if kind == "pin" else None,
        1 if kind == "pin" else None,
        body().hash if kind == "pin" else None,
    )
