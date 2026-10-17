"""BE2-14 owned lifecycle persistence ports; not production authority adapters."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.ai_policy.model import PolicyVersion, Review


@dataclass(frozen=True, slots=True)
class PolicyEvent:
    event_id: str
    kind: str
    principal_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class PolicyReceipt:
    organization_id: str
    principal_id: str
    request_id: str
    fingerprint: str
    result_json: str


class PolicyTransaction(Protocol):
    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> PolicyVersion | None: ...

    def save(self, policy: PolicyVersion, *, expected_revision: int | None,
             event: PolicyEvent) -> None: ...

    def review_history(self, organization_id: str, record_id: str, *, version: int,
                       after_revision: int, limit: int) -> tuple[Review, ...]: ...

    def receipt(self, organization_id: str, principal_id: str,
                request_id: str) -> PolicyReceipt | None: ...

    def add_receipt(self, receipt: PolicyReceipt) -> None: ...


class PolicyStore(Protocol):
    def transaction(self) -> AbstractContextManager[PolicyTransaction]: ...
