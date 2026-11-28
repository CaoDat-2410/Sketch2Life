"""Application orchestration for the BE1 fence, Story transfer and BE1 finalize saga."""

from __future__ import annotations

import hashlib
import json

from sketch2life.application.ports.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferPort,
    StoryTeacherOwnerTransferUnavailable,
)
from sketch2life.application.ports.teacher_assignment_transfer import (
    TeacherAssignmentTransferCommand,
    TeacherAssignmentTransferError,
    TeacherAssignmentTransferRecord,
    TeacherAssignmentTransferRepository,
)
from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
    StoryTeacherOwnerTransferReceiptV1,
    story_teacher_owner_transfer_key_sha256,
)
from sketch2life.contracts.schemas.teacher_assignment_transfers import (
    Be1TeacherAssignmentTransferAcceptedV1,
)
from sketch2life.domain.teacher_assignment_transfer import TransferAction, TransferState


class TeacherAssignmentTransferService:
    def __init__(
        self,
        *,
        repository: TeacherAssignmentTransferRepository,
        story_transfer: StoryTeacherOwnerTransferPort,
    ) -> None:
        self._repository = repository
        self._story_transfer = story_transfer

    def execute(
        self, command: TeacherAssignmentTransferCommand
    ) -> Be1TeacherAssignmentTransferAcceptedV1:
        start = self._repository.begin(command)
        record = start.record
        if start.resume:
            try:
                story_receipt = self._story_transfer.transfer_owner(self._story_command(record))
            except StoryTeacherOwnerTransferUnavailable:
                record = self._repository.reconcile(
                    command, record, failure_code="STORY_TRANSFER_UNCERTAIN"
                )
            else:
                expected = self._story_command(record)
                if not _receipt_matches(expected, story_receipt):
                    record = self._repository.reconcile(
                        command, record, failure_code="STORY_RECEIPT_MISMATCH"
                    )
                elif story_receipt.outcome == "CONFLICT":
                    record = self._repository.compensate(
                        command,
                        record,
                        story_receipt_ref=story_receipt.transfer_id,
                        failure_code="RESOURCE_CONFLICT",
                    )
                else:
                    try:
                        record = self._repository.finalize(
                            command, record, story_receipt_ref=story_receipt.transfer_id
                        )
                    except TeacherAssignmentTransferError:
                        # Story has committed. The durable BE1 fence is kept for same-key retry.
                        record = self._repository.reconcile(
                            command, record, failure_code="BE1_FINALIZE_UNCERTAIN"
                        )
        if (
            record.state is TransferState.COMPENSATED_CONFLICT
            and record.action is TransferAction.OFFBOARD
        ):
            raise TeacherAssignmentTransferError(409, "RESOURCE_CONFLICT")
        return self._accepted(record)

    @staticmethod
    def _story_command(
        record: TeacherAssignmentTransferRecord,
    ) -> StoryTeacherOwnerTransferCommandV1:
        if not record.old_teacher_ref:
            raise TeacherAssignmentTransferError(409, "INVALID_STATE_TRANSITION")
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "transfer_id": record.transfer_id,
                    "organization_ref": record.organization_id,
                    "class_ref": record.class_id,
                    "action": record.action.value,
                    "old_owner_teacher_ref": record.old_teacher_ref,
                    "new_owner_teacher_ref": record.new_teacher_ref,
                    "assignment_revision": record.fenced_revision,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return StoryTeacherOwnerTransferCommandV1(
            transfer_id=record.transfer_id,
            organization_ref=record.organization_id,
            class_ref=record.class_id,
            action=record.action.value,
            old_owner_teacher_ref=record.old_teacher_ref,
            new_owner_teacher_ref=record.new_teacher_ref,
            assignment_revision=record.fenced_revision,
            idempotency_key=record.idempotency_key,
            request_fingerprint_sha256=fingerprint,
        )

    @staticmethod
    def _accepted(
        record: TeacherAssignmentTransferRecord,
    ) -> Be1TeacherAssignmentTransferAcceptedV1:
        return Be1TeacherAssignmentTransferAcceptedV1(
            transfer_id=record.transfer_id,
            class_id=record.class_id,
            action=record.action.value,
            state="TRANSFER_PENDING",
            assignment_revision=record.fenced_revision,
            status_url=(
                f"/api/be1/v1/classes/{record.class_id}/assignment-transfers/"
                f"{record.transfer_id}"
            ),
        )


def _receipt_matches(
    command: StoryTeacherOwnerTransferCommandV1,
    receipt: StoryTeacherOwnerTransferReceiptV1,
) -> bool:
    expected_key_hash = story_teacher_owner_transfer_key_sha256(
        organization_ref=command.organization_ref,
        class_ref=command.class_ref,
        transfer_id=command.transfer_id,
    )
    return (
        receipt.transfer_id == command.transfer_id
        and receipt.organization_ref == command.organization_ref
        and receipt.class_ref == command.class_ref
        and receipt.action == command.action
        and receipt.old_owner_teacher_ref == command.old_owner_teacher_ref
        and receipt.new_owner_teacher_ref == command.new_owner_teacher_ref
        and receipt.assignment_revision == command.assignment_revision
        and receipt.idempotency_key_sha256 == expected_key_hash
        and receipt.request_fingerprint_sha256 == command.request_fingerprint_sha256
    )


__all__ = ["TeacherAssignmentTransferService"]
