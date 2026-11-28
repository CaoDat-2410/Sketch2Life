"""BE1 persistence port for the durable Teacher assignment transfer saga."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.teacher_assignment_transfer import TransferAction, TransferState


class TeacherAssignmentTransferError(RuntimeError):
    def __init__(self, status_code: int, code: str, *, current_version: int | None = None) -> None:
        self.status_code = status_code
        self.code = code
        self.current_version = current_version
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class TeacherAssignmentTransferCommand:
    principal_subject: str
    principal_issuer: str
    class_id: str
    action: TransferAction
    candidate_ref: str | None
    expected_revision: int
    idempotency_key: str
    request_fingerprint: str


@dataclass(frozen=True, slots=True)
class TeacherAssignmentTransferRecord:
    transfer_id: str
    organization_id: str
    class_id: str
    action: TransferAction
    state: TransferState
    old_subject: str
    new_subject: str | None
    old_teacher_ref: str
    new_teacher_ref: str | None
    expected_revision: int
    fenced_revision: int
    assignment_revision: int
    operation_scope: str
    idempotency_key: str
    request_fingerprint: str
    story_receipt_ref: str | None
    last_failure_code: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TeacherAssignmentTransferStart:
    record: TeacherAssignmentTransferRecord
    resume: bool


class TeacherAssignmentTransferRepository(Protocol):
    def begin(
        self, command: TeacherAssignmentTransferCommand
    ) -> TeacherAssignmentTransferStart: ...

    def finalize(
        self,
        command: TeacherAssignmentTransferCommand,
        record: TeacherAssignmentTransferRecord,
        *,
        story_receipt_ref: str,
    ) -> TeacherAssignmentTransferRecord: ...

    def compensate(
        self,
        command: TeacherAssignmentTransferCommand,
        record: TeacherAssignmentTransferRecord,
        *,
        story_receipt_ref: str,
        failure_code: str,
    ) -> TeacherAssignmentTransferRecord: ...

    def reconcile(
        self,
        command: TeacherAssignmentTransferCommand,
        record: TeacherAssignmentTransferRecord,
        *,
        failure_code: str,
    ) -> TeacherAssignmentTransferRecord: ...

    def status(
        self, *, organization_id: str, class_id: str, transfer_id: str
    ) -> TeacherAssignmentTransferRecord | None: ...


__all__ = [
    "TeacherAssignmentTransferCommand",
    "TeacherAssignmentTransferError",
    "TeacherAssignmentTransferRecord",
    "TeacherAssignmentTransferRepository",
    "TeacherAssignmentTransferStart",
]
