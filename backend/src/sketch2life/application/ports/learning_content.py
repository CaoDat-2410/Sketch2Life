"""BE2-12 storage boundaries. SQL/identity/adapters never leak into application."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.learning_content.model import ContentVersion


@dataclass(frozen=True, slots=True)
class ContentEvent:
    event_id: str
    kind: str
    principal_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ContentReceipt:
    organization_id: str
    principal_id: str
    request_id: str
    fingerprint: str
    result_json: str


class ContentTransaction(Protocol):
    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> ContentVersion | None: ...

    def save(self, content: ContentVersion, *, expected_revision: int | None,
             event: ContentEvent) -> None: ...

    def receipt(self, organization_id: str, principal_id: str,
                request_id: str) -> ContentReceipt | None: ...

    def add_receipt(self, receipt: ContentReceipt) -> None: ...


class ContentStore(Protocol):
    def transaction(self) -> AbstractContextManager[ContentTransaction]: ...
