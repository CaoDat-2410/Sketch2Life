"""BE2-06 consumer ports; authority and producer results remain external decisions."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.contracts.schemas.child_responses import (
    AuthorizedChildReadV1,
    ChildResponseOutcomeV1,
    ReviewAccessSnapshotV1,
    TeacherResponseEventV1,
    TurnSnapshotV1,
)
from sketch2life.domain.child_response import ResponseAction, ResponseEntry, ViewerKey, ViewerState


class RevisionConflict(Exception):
    """The viewer state changed before the local compare-and-swap."""


class UniqueConflict(Exception):
    """A concurrent operation already committed the immutable receipt/identity."""


class ReviewAccessPort(Protocol):
    def authorize(
        self, principal: Principal, proposal_id: str, *,
        expected_proposal_version: int | None = None, review_ref: str | None = None,
        content_sha256: str | None = None,
    ) -> ReviewAccessSnapshotV1 | None: ...

    def read(
        self, principal: Principal, proposal_id: str, *,
        expected_proposal_version: int | None = None, review_ref: str | None = None,
        content_sha256: str | None = None,
    ) -> AuthorizedChildReadV1 | None: ...


class AuthorityPort(Protocol):
    def new_operation(
        self, principal: Principal, access: ReviewAccessSnapshotV1, turn_id: str | None,
    ) -> TurnSnapshotV1 | None: ...

    def can_disclose(self, principal: Principal, access: ReviewAccessSnapshotV1) -> bool: ...

    def teacher_allowed(self, principal: Principal, access: ReviewAccessSnapshotV1) -> bool: ...


@dataclass(frozen=True, slots=True)
class ReceiptKey:
    organization_id: str
    principal_id: str
    contract_name: str
    target_id: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResponseReceipt:
    key: ReceiptKey
    fingerprint: str
    access: ReviewAccessSnapshotV1
    outcome: ChildResponseOutcomeV1


@dataclass(frozen=True, slots=True)
class ResponseAudit:
    audit_id: str
    operation_key: ReceiptKey
    access: ReviewAccessSnapshotV1
    turn_id: str
    action: ResponseAction
    response_id: str
    applied: bool
    occurred_at: datetime


class ChildResponseUnitOfWork(Protocol):
    def get_state(self, key: ViewerKey) -> ViewerState | None: ...

    def get_receipt(self, key: ReceiptKey) -> ResponseReceipt | None: ...

    def save_state(self, *, expected_revision: int, state: ViewerState) -> None: ...

    def terminal_marker(self, key: ViewerKey) -> str | None: ...

    def mark_terminal(self, key: ViewerKey, response_id: str) -> None: ...

    def append_history(self, entry: ResponseEntry) -> None: ...

    def put_receipt(self, receipt: ResponseReceipt) -> None: ...

    def add_audit(self, audit: ResponseAudit) -> None: ...

    def add_event(self, event: TeacherResponseEventV1) -> None: ...

    def events(self) -> tuple[TeacherResponseEventV1, ...]: ...


class ChildResponseRepository(Protocol):
    def transaction(self) -> AbstractContextManager[ChildResponseUnitOfWork]: ...
