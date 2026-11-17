"""Atomic, defensive-copy own07 storage and deterministic fault hooks. FIXTURE_ONLY."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock

from sketch2life.application.ports.knowledge_bundle import (
    KnowledgeAudit,
    KnowledgeConflict,
    KnowledgeReceipt,
    KnowledgeStorageFailure,
    KnowledgeUnitOfWork,
    ReceiptKey,
)
from sketch2life.contracts.schemas.knowledge_bundles import KnowledgeSupersededV1
from sketch2life.domain.knowledge_bundle import (
    BundleHead,
    CorrectionV1,
    KnowledgeBundleVersion,
    verify_version,
)
from sketch2life.infrastructure.knowledge_bundle.coordination import KnowledgeCommitCoordinator


@dataclass
class KnowledgeStoreSnapshot:
    heads: dict[str, BundleHead] = field(default_factory=dict)
    versions: dict[tuple[str, int], KnowledgeBundleVersion] = field(default_factory=dict)
    corrections: dict[str, CorrectionV1] = field(default_factory=dict)
    receipts: dict[ReceiptKey, KnowledgeReceipt] = field(default_factory=dict)
    audit: dict[str, KnowledgeAudit] = field(default_factory=dict)
    outbox: dict[str, KnowledgeSupersededV1] = field(default_factory=dict)


class _UnitOfWork:
    def __init__(self, state: KnowledgeStoreSnapshot, fault: Callable[[str], None]) -> None:
        self._state = state
        self._fault = fault
        self.dirty = False
        self._active = True

    def close(self) -> None:
        self._active = False

    def _check(self) -> None:
        if not self._active:
            raise KnowledgeStorageFailure("unit is closed")

    def _written(self, stage: str) -> None:
        self.dirty = True
        self._fault(stage)

    def get_head(self, bundle_id: str) -> BundleHead | None:
        self._check()
        return deepcopy(self._state.heads.get(bundle_id))

    def get_version(self, bundle_id: str, version: int) -> KnowledgeBundleVersion | None:
        self._check()
        return deepcopy(self._state.versions.get((bundle_id, version)))

    def get_receipt(self, key: ReceiptKey) -> KnowledgeReceipt | None:
        self._check()
        return deepcopy(self._state.receipts.get(key))

    def put_head(self, head: BundleHead, expected_version: int) -> None:
        self._check()
        current = self._state.heads.get(head.bundle_id)
        actual = 0 if current is None else current.current_version
        editorial = 0 if current is None else current.editorial_revision
        if (
            actual != expected_version
            or head.current_version != actual + 1
            or head.editorial_revision != editorial + 1
            or (
                current is not None
                and (head.organization_id, head.session_id)
                != (current.organization_id, current.session_id)
            )
        ):
            raise KnowledgeConflict("head compare-and-swap failed")
        self._state.heads[head.bundle_id] = deepcopy(head)
        self._written("put_head")

    def put_version(self, version: KnowledgeBundleVersion) -> None:
        self._check()
        verify_version(version)
        key = (version.bundle_id, version.bundle_version)
        if key in self._state.versions:
            raise KnowledgeConflict("immutable version exists")
        self._state.versions[key] = deepcopy(version)
        self._written("put_version")

    def put_correction(self, correction: CorrectionV1) -> None:
        self._check()
        if correction.correction_ref in self._state.corrections:
            raise KnowledgeConflict("correction exists")
        self._state.corrections[correction.correction_ref] = deepcopy(correction)
        self._written("put_correction")

    def put_receipt(self, receipt: KnowledgeReceipt) -> None:
        self._check()
        if receipt.key in self._state.receipts:
            raise KnowledgeConflict("accepted receipt exists")
        self._state.receipts[receipt.key] = deepcopy(receipt)
        self._written("put_receipt")

    def add_audit(self, audit: KnowledgeAudit) -> None:
        self._check()
        if audit.operation_id in self._state.audit:
            raise KnowledgeConflict("audit operation exists")
        self._state.audit[audit.operation_id] = deepcopy(audit)
        self._written("add_audit")

    def add_event(self, event: KnowledgeSupersededV1) -> None:
        self._check()
        if event.event_id in self._state.outbox:
            raise KnowledgeConflict("outbox event exists")
        self._state.outbox[event.event_id] = deepcopy(event)
        self._written("add_event")


class InMemoryKnowledgeRepository:
    marker = "FIXTURE_ONLY"

    def __init__(self, coordinator: KnowledgeCommitCoordinator) -> None:
        self._coordinator = coordinator
        self._lock = RLock()
        self._state = KnowledgeStoreSnapshot()
        self._generation = 0
        self._commits = 0
        self._faults: list[str] = []
        self.before_transaction: Callable[[], None] | None = None
        self.before_commit: Callable[[], None] | None = None
        self.after_commit: Callable[[], None] | None = None

    @property
    def coordination_token(self) -> object:
        return self._coordinator

    @property
    def commits(self) -> int:
        with self._coordinator.read(), self._lock:
            return self._commits

    def snapshot(self) -> KnowledgeStoreSnapshot:
        with self._coordinator.read(), self._lock:
            return deepcopy(self._state)

    def fail_next(self, stage: str) -> None:
        if stage not in {
            "put_head",
            "put_version",
            "put_correction",
            "put_receipt",
            "add_audit",
            "add_event",
            "commit",
            "after_commit",
        }:
            raise ValueError("unknown knowledge fault stage")
        with self._coordinator.read(), self._lock:
            self._faults.append(stage)

    def _fault(self, stage: str) -> None:
        if self._faults and self._faults[0] == stage:
            self._faults.pop(0)
            raise KnowledgeStorageFailure(f"injected knowledge fault: {stage}")

    @contextmanager
    def transaction(self) -> Iterator[KnowledgeUnitOfWork]:
        if self.before_transaction is not None:
            self.before_transaction()
        with self._coordinator.unit(), self._lock:
            generation = self._generation
            tx = _UnitOfWork(deepcopy(self._state), self._fault)
            try:
                yield tx
                if not tx.dirty:
                    return
                if self.before_commit is not None:
                    self.before_commit()
                if generation != self._generation:
                    raise KnowledgeConflict("accepted nested unit changed staged generation")
                self._fault("commit")
                published = deepcopy(tx._state)
                tx.close()
                self._state = published
                self._generation += 1
                self._commits += 1
                if self.after_commit is not None:
                    self.after_commit()
                self._fault("after_commit")
            finally:
                tx.close()
