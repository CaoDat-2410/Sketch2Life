"""Replaceable storage for non-durable, session-scoped demo workflow data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DemoWorkflowRecord:
    session_id: str
    version: int
    values: dict[str, object]


class DemoWorkflowStore(Protocol):
    def create(self, session_id: str) -> None: ...

    def get(self, session_id: str) -> DemoWorkflowRecord | None: ...

    def replace(
        self, session_id: str, *, expected_version: int, record: DemoWorkflowRecord
    ) -> None: ...

    def delete(self, session_id: str) -> bool: ...


__all__ = ["DemoWorkflowRecord", "DemoWorkflowStore"]
