"""Atomic, single-process BE2-06 storage with deterministic fault injection (FIXTURE_ONLY)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock

from sketch2life.application.ports.child_response import (
    ReceiptKey,
    ResponseAudit,
    ResponseReceipt,
    RevisionConflict,
    UniqueConflict,
)
from sketch2life.contracts.schemas.child_responses import TeacherResponseEventV1
from sketch2life.domain.child_response import ResponseEntry, ViewerKey, ViewerState


@dataclass
class ResponseStoreSnapshot:
    states: dict[ViewerKey, ViewerState] = field(default_factory=dict)
    receipts: dict[ReceiptKey, ResponseReceipt] = field(default_factory=dict)
    markers: dict[ViewerKey, str] = field(default_factory=dict)
    history: list[ResponseEntry] = field(default_factory=list)
    audit: list[ResponseAudit] = field(default_factory=list)
    outbox: dict[str, TeacherResponseEventV1] = field(default_factory=dict)

    @property
    def events(self) -> tuple[TeacherResponseEventV1, ...]:
        return tuple(self.outbox.values())


class _UnitOfWork:
    def __init__(self, state: ResponseStoreSnapshot, fault: Callable[[str], None]) -> None:
        self._s = state
        self._fault = fault
        self.dirty = False

    def _written(self, step: str) -> None:
        self.dirty = True
        self._fault(step)

    def get_state(self, key: ViewerKey) -> ViewerState | None:
        return self._s.states.get(key)

    def get_receipt(self, key: ReceiptKey) -> ResponseReceipt | None:
        return self._s.receipts.get(key)

    def save_state(self, *, expected_revision: int, state: ViewerState) -> None:
        current = self._s.states.get(state.key)
        revision = 1 if current is None else current.revision
        if revision != expected_revision or state.revision != revision + 1:
            raise RevisionConflict("viewer response moved")
        if state.key in self._s.markers:
            raise RevisionConflict("terminal viewer state cannot advance")
        self._s.states[state.key] = state
        self._written("save_state")

    def terminal_marker(self, key: ViewerKey) -> str | None:
        return self._s.markers.get(key)

    def mark_terminal(self, key: ViewerKey, response_id: str) -> None:
        if key in self._s.markers:
            raise UniqueConflict("terminal marker already exists")
        self._s.markers[key] = response_id
        self._written("mark_terminal")

    def append_history(self, entry: ResponseEntry) -> None:
        if any(e.response_id == entry.response_id for e in self._s.history):
            raise UniqueConflict("response identity already exists")
        self._s.history.append(entry)
        self._written("append_history")

    def put_receipt(self, receipt: ResponseReceipt) -> None:
        if receipt.key in self._s.receipts:
            raise UniqueConflict("operation receipt already exists")
        self._s.receipts[receipt.key] = receipt
        self._written("put_receipt")

    def add_audit(self, audit: ResponseAudit) -> None:
        if any(a.audit_id == audit.audit_id for a in self._s.audit):
            raise UniqueConflict("audit identity already exists")
        self._s.audit.append(audit)
        self._written("add_audit")

    def add_event(self, event: TeacherResponseEventV1) -> None:
        if event.event_id in self._s.outbox:
            raise UniqueConflict("outbox event already exists")
        self._s.outbox[event.event_id] = event
        self._written("add_event")

    def events(self) -> tuple[TeacherResponseEventV1, ...]:
        return self._s.events


class InMemoryChildResponseStore:
    """Publish staged 06 state only on clean exit. It does not lock 05 or turn authority."""

    marker = "FIXTURE_ONLY"

    def __init__(self) -> None:
        self._state = ResponseStoreSnapshot()
        self._lock = RLock()
        self._faults: list[str] = []
        self.before_transaction: Callable[[], object] | None = None
        self.before_commit: Callable[[], object] | None = None
        self.fail_next_commit = False
        self.commits = 0
        self._generation = 0

    def fail_next(self, step: str) -> None:
        if step not in {"save_state", "mark_terminal", "append_history", "put_receipt",
                        "add_audit", "add_event", "commit"}:
            raise ValueError("unknown transaction fault stage")
        self._faults.append(step)

    def _fault(self, step: str) -> None:
        if self._faults and self._faults[0] == step:
            self._faults.pop(0)
            raise RuntimeError(f"injected child response fault: {step}")

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        # The outside hook permits deterministic two-thread preparation races without
        # making a test wait for a second writer while holding the local repository lock.
        hook = self.before_transaction
        if hook is not None:
            hook()
        with self._lock:
            generation = self._generation
            staged = deepcopy(self._state)
            tx = _UnitOfWork(staged, self._fault)
            yield tx
            if not tx.dirty:
                return
            hook = self.before_commit
            if hook is not None:
                self.before_commit = None
                hook()
            # RLock permits a same-thread nested unit (including test commit hooks).
            # Its accepted commit must survive rather than be overwritten by this copy.
            if self._generation != generation:
                raise RevisionConflict("another local unit published during this transaction")
            if self.fail_next_commit:
                self.fail_next_commit = False
                raise RuntimeError("injected child response commit failure")
            self._fault("commit")
            self._state = staged
            self._generation += 1
            self.commits += 1

    def snapshot(self) -> ResponseStoreSnapshot:
        with self._lock:
            return deepcopy(self._state)
