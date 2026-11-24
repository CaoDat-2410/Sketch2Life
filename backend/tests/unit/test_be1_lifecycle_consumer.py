"""BE1 lifecycle consumer: steps 0-6, leases, compare-and-set, retry bound, exception path.

DTR Draft 6 §6.2-§6.3. The consumer runs against an in-memory world: an outbox with leases and
a transactional ``process_local_once``, the BE1 receipt store, the audit writer, the upload and
notice owners, a Story fake and the production Core purge logic over in-memory assets. A
``Crash`` (a ``BaseException``) models a killed worker: it escapes the consumer, the lease
expires and a new claim continues.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.core_foundation import (
    LifecycleReceipt,
    LifecycleScope,
    OutboxEnvelope,
)
from sketch2life.application.ports.story_run_lifecycle import (
    CANCEL_EVENT_TYPE,
    StoryLifecycleError,
    StoryPurgePlan,
    lifecycle_event_id,
    lifecycle_exception_audit_id,
    lifecycle_request_id,
)
from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
    Be1LifecycleConsumer,
    ConsumerConfig,
    LifecycleToken,
    retry_delay_seconds,
)
from tests.unit.test_core_run_asset_purge import (
    DERIVED,
    ORIGINAL,
    RUN,
    SCOPE,
    MemoryAssets,
    MemoryCore,
    MemoryStorage,
    artwork_world,
)

REQUEST_ID = lifecycle_request_id(RUN)
EVENT_ID = lifecycle_event_id(REQUEST_ID, CANCEL_EVENT_TYPE)
COMPLETED_PATTERN = (
    r"^lcr1;upload=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};ai=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    r"asset=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};story=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    r"sha256=[0-9a-f]{64}(;orph=[0-9]+)?$"
)


class Crash(BaseException):
    """A killed worker; never caught by the consumer."""


@dataclass
class World:
    assets: MemoryAssets
    storage: MemoryStorage
    receipts: dict[str, dict[str, Any]] = field(default_factory=dict)
    audits: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    consumer_receipts: set[tuple[str, str]] = field(default_factory=set)
    uploads: dict[str, str] = field(default_factory=dict)  # upload id -> state
    notices: dict[str, dict[str, Any]] = field(default_factory=dict)
    run: dict[str, Any] = field(default_factory=dict)
    story_content: set[str] = field(default_factory=set)
    other_run_refs: set[str] = field(default_factory=set)
    crash_at: str | None = None
    calls: list[str] = field(default_factory=list)
    renew_fails: bool = False
    deferred: list[int] = field(default_factory=list)
    on_hit: dict[str, Callable[[], None]] = field(default_factory=dict)

    def hit(self, point: str) -> None:
        self.calls.append(point)
        callback = self.on_hit.pop(point, None)
        if callback is not None:
            callback()
        if self.crash_at == point:
            self.crash_at = None
            raise Crash(point)


class FakeOutbox:
    def __init__(self, world: World) -> None:
        self.w = world

    def add_event(self, event_id: str = EVENT_ID, *, attempt_count: int = 0) -> None:
        self.w.events[event_id] = {
            "event_type": CANCEL_EVENT_TYPE,
            "aggregate_id": RUN,
            "aggregate_revision": 2,
            "status": "pending",
            "owner": None,
            "attempt_count": attempt_count,
        }

    def expire_leases(self) -> None:
        for event in self.w.events.values():
            if event["status"] == "leased":
                event["status"] = "pending"
                event["owner"] = None

    def claim_ready(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 30,
        event_types: Collection[str] | None = None,
        aggregate_ids: Collection[str] | None = None,
    ) -> Sequence[OutboxEnvelope]:
        assert limit == 1 and lease_seconds == 900
        claimed = []
        for event_id, event in sorted(self.w.events.items()):
            if event["status"] != "pending":
                continue
            if event_types is not None and event["event_type"] not in event_types:
                continue
            if aggregate_ids is not None and event["aggregate_id"] not in aggregate_ids:
                continue
            event.update(status="leased", owner=worker_id)
            event["attempt_count"] += 1
            claimed.append(self._envelope(event_id, event))
            if len(claimed) == limit:
                break
        return tuple(claimed)

    def renew_lease(self, *, event_id: str, worker_id: str, lease_seconds: int) -> bool:
        self.w.hit("renew")
        event = self.w.events[event_id]
        return (
            not self.w.renew_fails and event["status"] == "leased" and event["owner"] == worker_id
        )

    def defer(self, *, event_id: str, worker_id: str, retry_after_seconds: int) -> bool:
        event = self.w.events[event_id]
        if event["status"] != "leased" or event["owner"] != worker_id:
            return False
        event.update(status="pending", owner=None)
        self.w.deferred.append(retry_after_seconds)
        return True

    def process_local_once(
        self,
        *,
        event_id: str,
        worker_id: str,
        consumer_name: str,
        effect: Callable[[Any, OutboxEnvelope], None],
    ) -> bool:
        event = self.w.events[event_id]
        if event["status"] == "delivered":
            return False
        if event["status"] != "leased" or event["owner"] != worker_id:
            return False
        if (consumer_name, event_id) in self.w.consumer_receipts:
            event.update(status="delivered", owner=None)
            return False
        snapshot = copy.deepcopy((self.w.receipts, self.w.audits))
        try:
            effect(self.w, self._envelope(event_id, event))
        except BaseException:
            self.w.receipts, self.w.audits = snapshot  # the transaction rolls back
            raise
        self.w.consumer_receipts.add((consumer_name, event_id))
        event.update(status="delivered", owner=None)
        return True

    @staticmethod
    def _envelope(event_id: str, event: dict[str, Any]) -> OutboxEnvelope:
        return OutboxEnvelope(
            event_id=event_id,
            event_type=event["event_type"],
            organization_id=None,
            aggregate_id=event["aggregate_id"],
            aggregate_revision=event["aggregate_revision"],
            owner_scope_kind=SCOPE.kind,
            owner_scope_ref=SCOPE.ref,
            attempt_count=event["attempt_count"],
        )


class FakeReceipts:
    def __init__(self, world: World) -> None:
        self.w = world
        self.cas_hook: Callable[[], None] | None = None

    def read(self, request_id: str, *, tx: Any = None) -> LifecycleReceipt | None:
        row = self.w.receipts.get(request_id)
        if row is None:
            return None
        return LifecycleReceipt(
            request_id=request_id,
            state=row["state"],
            result_ref=row["result_ref"],
            unresolved_items=row["unresolved_items"],
            owner_scope_kind=row["kind"],
            owner_scope_ref=row["ref"],
            completed_at=row["completed_at"],
            target_ref=row.get("target"),
        )

    def ensure(
        self, *, request_id: str, run_ref: str, scope: LifecycleScope, tx: Any = None
    ) -> LifecycleReceipt:
        self.w.receipts.setdefault(
            request_id,
            {
                "state": "requested",
                "result_ref": "lcr1",
                "unresolved_items": 4,
                "kind": scope.kind,
                "ref": scope.ref,
                "completed_at": None,
                "target": "story_run:" + run_ref,
            },
        )
        receipt = self.read(request_id)
        assert receipt is not None
        return receipt

    def compare_and_set(
        self,
        *,
        request_id: str,
        expected_state: str,
        expected_result_ref: str | None,
        state: str,
        result_ref: str | None,
        unresolved_items: int,
        completed_at: datetime | None = None,
        tx: Any = None,
    ) -> bool:
        if self.cas_hook is not None:
            hook, self.cas_hook = self.cas_hook, None
            hook()
        row = self.w.receipts.get(request_id)
        if row is None or (row["state"], row["result_ref"]) != (
            expected_state,
            expected_result_ref,
        ):
            return False
        row.update(state=state, result_ref=result_ref, unresolved_items=unresolved_items)
        if completed_at is not None:
            row["completed_at"] = completed_at
        return True


class FakeAudit:
    def __init__(self, world: World) -> None:
        self.w = world

    def write_exception(
        self,
        *,
        tx: Any,
        request_id: str,
        run_ref: str,
        scope: LifecycleScope,
        processed_event_id: str,
    ) -> None:
        self.w.audits.setdefault(
            lifecycle_exception_audit_id(processed_event_id),
            {"action": "lifecycle.exception", "decision": "exception:" + request_id},
        )


class FakeUploads:
    def __init__(self, world: World) -> None:
        self.w = world

    def plan_close_run_uploads(self, scope: LifecycleScope, run_ref: str) -> tuple[str, ...]:
        self.w.hit("upload.plan")
        return tuple(sorted(key for key, state in self.w.uploads.items() if state == "PENDING"))

    def close_run_uploads(self, scope: LifecycleScope, run_ref: str) -> int:
        self.w.hit("upload.act")
        closed = 0
        for key, state in self.w.uploads.items():
            if state == "PENDING":
                self.w.uploads[key] = "ABORTED"
                closed += 1
        self.w.hit("upload.after_act")
        return closed


class FakeNotices:
    def __init__(self, world: World) -> None:
        self.w = world

    def notice_exists(self, notice_id: str) -> bool:
        return notice_id in self.w.notices

    def record_lifecycle_notice(
        self, *, notice_id: str, scope: LifecycleScope, story_run_ref: str, reason_code: str
    ) -> None:
        self.w.hit("ai.act")
        self.w.notices.setdefault(
            notice_id,
            {
                "applied_count": 0,
                "status": "COMPLETE",
                "run": story_run_ref,
                "scope_kind": scope.kind,
                "reason_code": reason_code,
            },
        )
        self.w.hit("ai.after_act")

    def record_parent_notice(
        self, *, notice_id: str, scope: LifecycleScope, story_run_ref: str, reason_code: str
    ) -> None:
        # FEAT-066 T-13a: the consumer calls ``record_lifecycle_notice`` for every scope kind.
        raise AssertionError("the consumer must not call record_parent_notice")


class FakeStory:
    def __init__(self, world: World) -> None:
        self.w = world

    def lifecycle_state(self, run_ref: str) -> str | None:
        return str(self.w.run["state"])

    def plan_story_purge(self, run_ref: str) -> StoryPurgePlan:
        self.w.hit("story.plan")
        return StoryPurgePlan(run_ref, tuple(sorted(self.w.story_content)))

    def purge_story_content(self, plan: StoryPurgePlan) -> None:
        self.w.hit("story.act")
        if self.w.run["state"] not in {"DELETE_PENDING", "DELETED"}:
            raise StoryLifecycleError("RUN_NOT_PURGEABLE")
        if tuple(sorted(self.w.story_content)) != plan.ids:
            raise StoryLifecycleError("PLAN_CHANGED")
        self.w.story_content.clear()
        self.w.hit("story.after_act")

    def finalize_deleted(self, run_ref: str, request_id: str) -> bool:
        self.w.hit("finalize")
        if self.w.run["state"] == "DELETED":
            return False
        assert not self.w.story_content
        self.w.run.update(state="DELETED", revision=self.w.run["revision"] + 1)
        self.w.audits.setdefault("completed", {"action": "lifecycle.completed"})
        return True

    def assets_referenced_by_other_runs(
        self, scope: LifecycleScope, run_ref: str, asset_refs: frozenset[str]
    ) -> frozenset[str]:
        self.w.hit("story.refs")
        return frozenset(asset_refs & self.w.other_run_refs)


class CrashingCore(MemoryCore):
    def __init__(self, world: World) -> None:
        super().__init__(world.assets, world.storage)
        self.w = world

    def purge_objects(self, plan: Any) -> Any:
        result = super().purge_objects(plan)
        self.w.hit("asset.after_objects")
        return result

    def sweep_run_prefix(self, scope: LifecycleScope, run_ref: str) -> Any:
        self.w.hit("asset.sweep")
        result = super().sweep_run_prefix(scope, run_ref)
        self.w.hit("asset.after_sweep")
        return result

    def delete_rows(self, plan: Any, referenced_elsewhere_now: frozenset[str]) -> Any:
        result = super().delete_rows(plan, referenced_elsewhere_now)
        self.w.hit("asset.after_rows")
        return result

    def verify_run_purged(self, scope: LifecycleScope, run_ref: str) -> Any:
        self.w.hit("asset.verify")
        return super().verify_run_purged(scope, run_ref)


@dataclass
class Harness:
    world: World
    outbox: FakeOutbox
    receipts: FakeReceipts
    consumer: Be1LifecycleConsumer
    clock: list[float]

    def receipt(self) -> dict[str, Any]:
        return self.world.receipts[REQUEST_ID]

    def token(self) -> LifecycleToken:
        return LifecycleToken.parse(self.receipt()["result_ref"])

    def run_until_idle(self, limit: int = 30) -> list[str]:
        outcomes = []
        for _ in range(limit):
            try:
                outcome = self.consumer.run_once()
            except Crash:
                self.outbox.expire_leases()
                outcomes.append("crash")
                continue
            if outcome is None:
                return outcomes
            outcomes.append(outcome)
            self.outbox.expire_leases()
            for event in self.world.events.values():
                if event["status"] == "pending":
                    event["available"] = True
        raise AssertionError("consumer did not become idle")


def make_harness(
    *,
    artwork: bool = True,
    uploads: dict[str, str] | None = None,
    story: Sequence[str] = ("run:" + RUN, "run_inputs:i1", "receipt:r1"),
    attempt_count: int = 0,
    worker_id: str = "worker-a",
    world: World | None = None,
) -> Harness:
    if world is None:
        assets, storage = artwork_world() if artwork else (MemoryAssets(), MemoryStorage())
        world = World(assets=assets, storage=storage)
        world.run = {"state": "DELETE_PENDING", "revision": 2}
        world.story_content = set(story)
        world.uploads = dict(uploads or {})
    outbox = FakeOutbox(world)
    if not world.events:
        outbox.add_event(attempt_count=attempt_count)
    receipts = FakeReceipts(world)
    clock = [0.0]
    consumer = Be1LifecycleConsumer(
        outbox=outbox,
        receipts=receipts,
        audit=FakeAudit(world),
        uploads=FakeUploads(world),
        notices=FakeNotices(world),
        assets=CrashingCore(world),
        story=FakeStory(world),
        story_refs=FakeStory(world),
        config=ConsumerConfig(worker_id=worker_id),
        monotonic=lambda: clock[0],
        clock=lambda: datetime(2026, 11, 19, tzinfo=UTC),
    )
    return Harness(world, outbox, receipts, consumer, clock)


# ----------------------------------------------------------------------------------- tests
def test_a_run_with_artwork_completes_in_one_attempt() -> None:
    h = make_harness(uploads={"u1": "PENDING"})
    assert h.consumer.run_once() == "completed"
    receipt = h.receipt()
    assert receipt["state"] == "completed" and receipt["unresolved_items"] == 0
    assert receipt["completed_at"] is not None
    assert re.fullmatch(COMPLETED_PATTERN, receipt["result_ref"])
    token = h.token()
    assert [token.entries[step].count for step in ("upload", "ai", "asset", "story")] == [
        1,
        1,
        2,
        3,
    ]
    assert h.world.run["state"] == "DELETED"
    assert h.world.uploads == {"u1": "ABORTED"}
    assert h.world.notices["lifecycle:" + REQUEST_ID]["applied_count"] == 0
    assert h.world.assets.rows == {} and h.world.storage.objects == set()
    assert h.world.events[EVENT_ID]["status"] == "delivered"
    assert h.consumer.run_once() is None  # the event does not return


def test_a_run_without_artwork_completes_with_an_empty_asset_entry() -> None:
    h = make_harness(artwork=False)
    assert h.consumer.run_once() == "completed"
    assert h.token().entries["asset"].render().startswith("asset=v:0:")


def test_the_claim_filters_lifecycle_event_types_and_leases_one_event() -> None:
    h = make_harness()
    h.world.events["other"] = {
        "event_type": "canvas.operation.accepted.v1",
        "aggregate_id": RUN,
        "aggregate_revision": 1,
        "status": "pending",
        "owner": None,
        "attempt_count": 0,
    }
    h.consumer.run_once()
    assert h.world.events["other"]["status"] == "pending"
    assert h.world.events["other"]["attempt_count"] == 0


def test_targeted_run_once_does_not_claim_another_aggregate() -> None:
    h = make_harness()
    other_run = "33333333-3333-4333-8333-333333333333"
    h.world.events["other-run-event"] = {
        "event_type": CANCEL_EVENT_TYPE,
        "aggregate_id": other_run,
        "aggregate_revision": 2,
        "status": "pending",
        "owner": None,
        "attempt_count": 0,
    }

    assert h.consumer.run_once(target_run_ref=RUN) == "completed"
    assert h.world.events[EVENT_ID]["status"] == "delivered"
    assert h.world.events["other-run-event"]["status"] == "pending"
    assert h.world.events["other-run-event"]["attempt_count"] == 0


def test_a_retained_asset_purges_story_content_deletes_nothing_and_ends_in_exception() -> None:
    h = make_harness()
    h.world.other_run_refs = {DERIVED}  # Story says another run references the artwork
    assert h.consumer.run_once() == "exception"
    receipt = h.receipt()
    assert receipt["state"] == "exception"
    token = h.token()
    assert set(token.entries) == {"upload", "ai", "story"}  # no asset entry
    assert all(entry.verified for entry in token.entries.values())
    assert h.world.story_content == set()  # Story content is not shared
    assert h.world.run["state"] == "DELETE_PENDING"
    assert len(h.world.assets.rows) == 2 and h.world.storage.objects == {ORIGINAL, DERIVED}
    assert "asset.sweep" not in h.world.calls  # a retained plan runs no sweep
    assert lifecycle_exception_audit_id(EVENT_ID) in h.world.audits
    assert h.world.events[EVENT_ID]["status"] == "delivered"  # the old event does not return
    assert h.consumer.run_once() is None


def test_a_failed_step_defers_with_a_doubling_delay_and_the_bound_ends_in_exception() -> None:
    h = make_harness()
    h.world.storage.fail_list = True  # every verification fails
    outcomes = h.run_until_idle()
    assert outcomes[:9] == ["deferred"] * 9
    assert outcomes[9] == "exception"
    assert h.world.deferred == [retry_delay_seconds(n) for n in range(1, 10)]
    assert h.world.deferred[:4] == [30, 60, 120, 240]
    assert retry_delay_seconds(20) == 3600
    assert h.receipt()["state"] == "exception"
    assert h.world.events[EVENT_ID]["attempt_count"] == 10
    assert h.world.events[EVENT_ID]["status"] == "delivered"


def test_the_bound_inserts_a_missing_receipt_before_the_exception() -> None:
    h = make_harness(attempt_count=9)  # the next claim is the tenth
    assert REQUEST_ID not in h.world.receipts
    assert h.consumer.run_once() == "exception"
    assert h.receipt()["state"] == "exception"
    assert h.world.calls.count("upload.plan") == 0  # no purge work at the bound


def test_a_lost_lease_stops_work_without_deferring() -> None:
    h = make_harness(uploads={"u1": "PENDING"})
    h.world.renew_fails = True
    assert h.consumer.run_once() == "stopped"
    assert h.world.deferred == []
    # Nothing was done: the open upload is still open and Story content is untouched.
    assert h.world.uploads == {"u1": "PENDING"}
    assert h.world.story_content == {"run:" + RUN, "run_inputs:i1", "receipt:r1"}
    assert REQUEST_ID not in h.world.receipts  # not even step 0


def test_a_second_worker_is_stopped_by_the_compare_and_set() -> None:
    h = make_harness()

    def other_worker_progresses() -> None:
        h.receipt()["result_ref"] = "lcr1;upload=p:0:" + "0" * 16 + "@" + "0" * 8

    h.receipts.cas_hook = other_worker_progresses
    assert h.consumer.run_once() == "stopped"
    assert h.world.deferred == []


def test_a_zero_row_compare_and_set_inside_the_completion_effect_rolls_back() -> None:
    h = make_harness()
    original_cas = h.receipts.compare_and_set

    def cas(**kwargs: Any) -> bool:
        if kwargs["state"] == "completed":
            return False
        return original_cas(**kwargs)

    h.receipts.compare_and_set = cas  # type: ignore[method-assign]
    assert h.consumer.run_once() == "stopped"
    assert h.receipt()["state"] == "running"
    assert h.world.events[EVENT_ID]["status"] == "leased"  # not delivered


def test_step_six_with_a_surviving_late_orphan_fails_the_attempt_and_writes_no_completed() -> None:
    h = make_harness()
    storage = h.world.storage
    original_list = storage.list_keys
    state = {"after_finalize": False}

    def list_keys(prefix: str) -> tuple[str, ...]:
        if h.world.run["state"] == "DELETED":
            state["after_finalize"] = True
            return (*original_list(prefix), f"{prefix}late/object")  # survives every sweep
        return original_list(prefix)

    storage.list_keys = list_keys  # type: ignore[method-assign]
    assert h.consumer.run_once() == "deferred"
    assert state["after_finalize"]
    assert h.world.run["state"] == "DELETED"
    assert h.receipt()["state"] == "awaiting_external_purge"
    assert h.token().sha256 is None


def test_an_orphan_written_after_step_three_is_swept_in_step_five_and_the_run_completes() -> None:
    h = make_harness()
    # A late object without a metadata row appears while Story purges its content (step 4).
    h.world.on_hit["story.after_act"] = lambda: h.world.storage.objects.add(
        f"parent/{RUN}/late/original"
    )
    assert h.consumer.run_once() == "completed"
    assert h.world.storage.objects == set()
    assert h.token().orph == 1  # informational, not hashed (T6)


def test_an_orphan_inside_step_three_fails_that_attempt_and_the_rerun_sweeps_it() -> None:
    h = make_harness()
    h.world.on_hit["asset.after_rows"] = lambda: h.world.storage.objects.add(
        f"parent/{RUN}/late/derived"
    )
    assert h.consumer.run_once() == "deferred"
    assert not h.token().entries["asset"].verified
    h.run_until_idle()
    assert h.receipt()["state"] == "completed"
    assert h.world.storage.objects == set()


def test_a_step_deadline_fails_the_attempt() -> None:
    h = make_harness()
    clock = h.clock

    def slow_plan(scope: LifecycleScope, run_ref: str) -> tuple[str, ...]:
        clock[0] += 301
        return ()

    h.consumer._uploads.plan_close_run_uploads = slow_plan  # type: ignore[attr-defined]
    assert h.consumer.run_once() == "deferred"
    assert h.receipt()["state"] == "awaiting_external_purge"


def test_a_completed_receipt_with_a_stale_event_is_delivered_unchanged() -> None:
    h = make_harness()
    assert h.consumer.run_once() == "completed"
    final = dict(h.receipt())
    h.outbox.add_event("reconciled-duplicate")
    assert h.consumer.run_once() == "delivered"
    assert h.receipt() == final


def test_a_run_outside_the_purge_states_is_never_purged() -> None:
    h = make_harness()
    h.world.run["state"] = "SCRIPT_REVIEW"
    assert h.consumer.run_once() == "deferred"
    assert h.world.calls.count("upload.plan") == 0
    assert h.world.assets.rows and h.world.story_content


def test_config_bounds_and_lease_defaults() -> None:
    config = ConsumerConfig(worker_id="w")
    assert (config.lease_seconds, config.step_deadline_seconds, config.retry_bound) == (
        900,
        300,
        10,
    )
    for bad in ({"lease_seconds": 0}, {"lease_seconds": 3601}, {"retry_bound": 0}):
        with pytest.raises(ValueError):
            ConsumerConfig(worker_id="w", **bad)  # type: ignore[arg-type]


def test_two_runs_doing_the_same_work_end_with_the_same_entries_and_hash() -> None:
    first = make_harness(uploads={"u1": "PENDING"})
    second = make_harness(uploads={"u1": "PENDING"})
    assert first.consumer.run_once() == "completed"
    assert second.consumer.run_once() == "completed"
    assert first.token().segments() == second.token().segments()
    assert first.token().sha256 == second.token().sha256


def test_receipt_and_audit_rows_hold_only_lifecycle_fields() -> None:
    h = make_harness()
    h.consumer.run_once()
    assert set(h.receipt()) == {
        "state",
        "result_ref",
        "unresolved_items",
        "kind",
        "ref",
        "completed_at",
        "target",
    }
    assert h.receipt()["target"] == "story_run:" + RUN
    for audit in h.world.audits.values():
        assert set(audit) <= {"action", "decision"}
    assert ORIGINAL not in str(h.world.audits) and DERIVED not in str(h.world.receipts)


# ------------------------------------------------------------------ review R1 P3-3 and P3-5
def test_a_reopened_request_completes_with_the_asset_entry_inserted_at_its_position() -> None:
    """DTR §6.6 / §10 (consumer side only; the re-open command itself is out of scope): a
    request re-opened after a manual fix is ``requested`` with verified upload, ai and story
    entries and no asset entry; the consumer runs only the missing asset step."""
    from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import flip, plan_entry

    h = make_harness(story=())  # Story content was purged before the exception
    token = LifecycleToken()
    for entry in (
        plan_entry("upload", []),
        plan_entry("ai", ["lifecycle:" + REQUEST_ID]),
        plan_entry("story", ["run:" + RUN, "run_inputs:i1"]),
    ):
        token = flip(token.with_entry(entry), entry.step)
    seeded = dict(token.entries)
    h.world.receipts[REQUEST_ID] = {
        "state": "requested",
        "result_ref": token.render(),
        "unresolved_items": token.unresolved_items,
        "kind": SCOPE.kind,
        "ref": SCOPE.ref,
        "completed_at": None,
        "target": "story_run:" + RUN,
    }
    h.world.events.clear()
    h.outbox.add_event("reopen-event-1")  # the re-open inserts an event with a fresh id
    assert h.consumer.run_once() == "completed"
    receipt = h.receipt()
    assert receipt["state"] == "completed" and receipt["unresolved_items"] == 0
    assert re.fullmatch(COMPLETED_PATTERN, receipt["result_ref"])
    final = h.token()
    assert [segment.split("=")[0] for segment in final.segments()] == [
        "upload",
        "ai",
        "asset",
        "story",
    ]
    for step in ("upload", "ai", "story"):
        assert final.entries[step] == seeded[step]  # verified entries are never rewritten
    assert final.entries["asset"].verified and final.entries["asset"].count == 2
    assert "upload.plan" not in h.world.calls and "story.plan" not in h.world.calls
    assert h.world.run["state"] == "DELETED"


def _leased_event(h: Harness, event_id: str, **envelope: Any) -> OutboxEnvelope:
    values: dict[str, Any] = {
        "event_id": event_id,
        "event_type": CANCEL_EVENT_TYPE,
        "organization_id": None,
        "aggregate_id": RUN,
        "aggregate_revision": 2,
        "owner_scope_kind": SCOPE.kind,
        "owner_scope_ref": SCOPE.ref,
        "attempt_count": 1,
    }
    values.update(envelope)
    h.world.events[event_id] = {
        "event_type": values["event_type"],
        "aggregate_id": values["aggregate_id"],
        "aggregate_revision": 2,
        "status": "leased",
        "owner": "worker-a",
        "attempt_count": values["attempt_count"],
    }
    return OutboxEnvelope(**values)


@pytest.mark.parametrize(
    "envelope",
    (
        # FEAT-066 T-13a: ``ORGANIZATION`` is a lifecycle scope now (a Teacher run); a kind that
        # is neither Parent nor organization, or an organization event without a ref, is refused.
        {"owner_scope_kind": "GLOBAL", "owner_scope_ref": "org-1", "organization_id": "org-1"},
        {"owner_scope_kind": "ORGANIZATION", "owner_scope_ref": None, "organization_id": "org-1"},
        {"aggregate_id": "story_run:" + RUN},
        {"aggregate_id": RUN.upper()[:9] + "ABCD" + RUN[13:]},
        {"event_type": "canvas.operation.accepted.v1"},
        {"owner_scope_ref": None},
    ),
)
def test_an_event_that_is_not_a_parent_lifecycle_event_is_never_purged(
    envelope: dict[str, Any],
) -> None:
    h = make_harness()
    event = _leased_event(h, "invalid-1", **envelope)
    assert h.consumer.handle(event) == "deferred"
    assert h.world.deferred == [3600]
    assert h.world.receipts == {} and h.world.calls.count("upload.plan") == 0
    assert h.world.assets.rows and h.world.story_content  # nothing purged
    at_bound = _leased_event(h, "invalid-2", attempt_count=10, **envelope)
    assert h.consumer.handle(at_bound) == "delivered"  # delivered without any effect
    assert h.world.events["invalid-2"]["status"] == "delivered"
    assert h.world.receipts == {} and h.world.audits == {}


def test_a_receipt_of_another_owner_scope_stops_the_attempt_and_is_left_unchanged() -> None:
    h = make_harness(uploads={"u1": "PENDING"})
    foreign = {
        "state": "requested",
        "result_ref": "lcr1",
        "unresolved_items": 4,
        "kind": "PARENT_ACCOUNT",
        "ref": "b" * 64,
        "completed_at": None,
        "target": "story_run:" + RUN,
    }
    h.world.receipts[REQUEST_ID] = dict(foreign)
    assert h.consumer.run_once() == "deferred"
    assert h.world.receipts[REQUEST_ID] == foreign  # no CAS on a foreign receipt
    assert h.world.uploads == {"u1": "PENDING"}
    assert h.world.deferred == [retry_delay_seconds(1)]


def test_the_sql_receipt_store_refuses_a_receipt_with_another_target() -> None:
    from sketch2life.application.ports.core_foundation import CoreAssetPurgeError
    from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
        SqlLifecycleReceiptStore,
    )

    class _Session:
        def __init__(self) -> None:
            self.statements: list[Any] = []

        def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> Any:
            self.statements.append(statement)
            row = SimpleNamespace(
                request_id=REQUEST_ID,
                state="requested",
                result_ref="lcr1",
                unresolved_items=4,
                owner_scope_kind=SCOPE.kind,
                owner_scope_ref=SCOPE.ref,
                completed_at=None,
                target_ref="story_run:33333333-3333-4333-8333-333333333333",
            )
            return SimpleNamespace(one_or_none=lambda: row)

        def scalar(self, *_args: Any, **_kwargs: Any) -> Any:
            return "story_run:33333333-3333-4333-8333-333333333333"

    session = _Session()
    store = SqlLifecycleReceiptStore(sessions=None)  # type: ignore[arg-type]
    with pytest.raises(CoreAssetPurgeError, match="RECEIPT_TARGET_MISMATCH"):
        store.ensure(request_id=REQUEST_ID, run_ref=RUN, scope=SCOPE, tx=session)
    assert session.statements[0].table.name == "be1_data_lifecycle_requests"  # insert-if-absent
    with pytest.raises(CoreAssetPurgeError, match="SCOPE_INVALID"):
        store.ensure(
            request_id=REQUEST_ID,
            run_ref=RUN,
            scope=SimpleNamespace(kind="GLOBAL", ref="org-1"),  # type: ignore[arg-type]
            tx=session,
        )


# ------------------------------------------------------------------------- review R2 F-1
def _foreign_receipt_row(case: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "state": "running",
        "result_ref": "lcr1",
        "unresolved_items": 4,
        "kind": "PARENT_ACCOUNT",
        "ref": SCOPE.ref,
        "completed_at": None,
        "target": "story_run:" + RUN,
    }
    if case == "scope":
        row["ref"] = "b" * 64
    else:
        row["target"] = "story_run:33333333-3333-4333-8333-333333333333"
    return row


@pytest.mark.parametrize("case", ("scope", "target"))
def test_a_foreign_receipt_is_left_unchanged_at_the_retry_bound(case: str) -> None:
    """At attempt 10 the exception effect neither changes a receipt of another scope or target
    nor writes an audit row; the event is delivered without an effect."""
    h = make_harness(attempt_count=9)  # the next claim is the tenth
    foreign = _foreign_receipt_row(case)
    h.world.receipts[REQUEST_ID] = dict(foreign)
    assert h.consumer.run_once() == "delivered"
    assert h.world.receipts[REQUEST_ID] == foreign
    assert h.world.audits == {}
    assert h.world.events[EVENT_ID]["status"] == "delivered"
    assert h.world.calls.count("upload.plan") == 0


@pytest.mark.parametrize("case", ("scope", "target"))
def test_a_foreign_receipt_is_left_unchanged_below_the_retry_bound(case: str) -> None:
    h = make_harness(uploads={"u1": "PENDING"})
    foreign = _foreign_receipt_row(case)
    h.world.receipts[REQUEST_ID] = dict(foreign)
    assert h.consumer.run_once() == "deferred"
    assert h.world.receipts[REQUEST_ID] == foreign  # no CAS to awaiting_external_purge
    assert h.world.uploads == {"u1": "PENDING"} and h.world.audits == {}
    assert h.world.deferred == [retry_delay_seconds(1)]
