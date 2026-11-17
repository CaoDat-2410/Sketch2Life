"""Thread-safe process-local storage for the unauthenticated Android demo workflow."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock

from sketch2life.application.ports.demo_workflow_storage import DemoWorkflowRecord


class DemoWorkflowVersionConflict(ValueError):
    pass


class InMemoryDemoWorkflowStore:
    def __init__(self) -> None:
        self._records: dict[str, DemoWorkflowRecord] = {}
        self._lock = RLock()

    def create(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._records:
                raise ValueError("workflow data already exists")
            self._records[session_id] = DemoWorkflowRecord(
                session_id=session_id,
                version=0,
                values={},
            )

    def get(self, session_id: str) -> DemoWorkflowRecord | None:
        with self._lock:
            record = self._records.get(session_id)
            return deepcopy(record) if record is not None else None

    def replace(
        self, session_id: str, *, expected_version: int, record: DemoWorkflowRecord
    ) -> None:
        if record.session_id != session_id or record.version != expected_version + 1:
            raise ValueError("replacement workflow identity/version is invalid")
        with self._lock:
            current = self._records.get(session_id)
            if current is None or current.version != expected_version:
                raise DemoWorkflowVersionConflict("workflow data is missing or stale")
            self._records[session_id] = deepcopy(record)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._records.pop(session_id, None) is not None


__all__ = ["DemoWorkflowVersionConflict", "InMemoryDemoWorkflowStore"]
