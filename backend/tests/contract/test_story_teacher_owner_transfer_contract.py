from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
    StoryTeacherOwnerTransferReceiptV1,
)

_TRANSFER = "11111111-1111-4111-8111-111111111111"
_OLD = "22222222-2222-4222-8222-222222222222"
_NEW = "33333333-3333-4333-8333-333333333333"
_FINGERPRINT = "a" * 64


def _command(
    action: str = "REASSIGN", new_owner: str | None = _NEW
) -> StoryTeacherOwnerTransferCommandV1:
    return StoryTeacherOwnerTransferCommandV1(
        transfer_id=_TRANSFER,
        organization_ref="synthetic-org",
        class_ref="synthetic-class",
        action=action,
        old_owner_teacher_ref=_OLD,
        new_owner_teacher_ref=new_owner,
        assignment_revision=2,
        idempotency_key="synthetic-owner-transfer-key",
        request_fingerprint_sha256=_FINGERPRINT,
    )


def test_story_owner_transfer_command_and_receipt_are_versioned_metadata() -> None:
    command = _command()
    receipt = StoryTeacherOwnerTransferReceiptV1(
        transfer_id=command.transfer_id,
        organization_ref=command.organization_ref,
        class_ref=command.class_ref,
        action=command.action,
        old_owner_teacher_ref=command.old_owner_teacher_ref,
        new_owner_teacher_ref=command.new_owner_teacher_ref,
        assignment_revision=command.assignment_revision,
        idempotency_key_sha256=hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest(),
        request_fingerprint_sha256=command.request_fingerprint_sha256,
        outcome="TRANSFERRED",
        owner_epoch=1,
    )
    assert command.contract == "StoryTeacherOwnerTransferCommandV1"
    assert receipt.contract == "StoryTeacherOwnerTransferReceiptV1"
    assert receipt.owner_epoch == 1
    for body in (command.model_dump(mode="json"), receipt.model_dump(mode="json")):
        assert not {"email", "token", "link", "child_name", "story_text"} & set(body)


@pytest.mark.parametrize(
    ("action", "new_owner"),
    [("OFFBOARD", _NEW), ("REASSIGN", None), ("REASSIGN", _OLD)],
)
def test_story_owner_transfer_rejects_action_and_owner_mismatch(
    action: str, new_owner: str | None
) -> None:
    with pytest.raises(ValidationError):
        _command(action, new_owner)
