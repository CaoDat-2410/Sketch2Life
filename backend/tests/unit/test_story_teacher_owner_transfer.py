from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
    StoryTeacherOwnerTransferReceiptV1,
)

_TRANSFER_ID = "11111111-1111-4111-8111-111111111111"
_OLD_OWNER = "22222222-2222-4222-8222-222222222222"
_NEW_OWNER = "33333333-3333-4333-8333-333333333333"
_FINGERPRINT = "a" * 64


def _command(**changes: object) -> StoryTeacherOwnerTransferCommandV1:
    values: dict[str, object] = {
        "transfer_id": _TRANSFER_ID,
        "organization_ref": "synthetic-org",
        "class_ref": "synthetic-class",
        "action": "REASSIGN",
        "old_owner_teacher_ref": _OLD_OWNER,
        "new_owner_teacher_ref": _NEW_OWNER,
        "assignment_revision": 2,
        "idempotency_key": "synthetic-transfer-key",
        "request_fingerprint_sha256": _FINGERPRINT,
    }
    values.update(changes)
    return StoryTeacherOwnerTransferCommandV1(**values)


def test_story_transfer_command_is_versioned_and_metadata_only() -> None:
    command = _command()
    assert command.contract == "StoryTeacherOwnerTransferCommandV1"
    assert command.assignment_revision == 2
    assert type(command).model_config["extra"] == "forbid"
    assert "child_name" not in command.model_dump()
    assert "email" not in command.model_dump()


def test_story_transfer_command_requires_action_and_new_owner_to_agree() -> None:
    with pytest.raises(ValidationError):
        _command(action="OFFBOARD")
    with pytest.raises(ValidationError):
        _command(new_owner_teacher_ref=None)
    with pytest.raises(ValidationError):
        _command(new_owner_teacher_ref=_OLD_OWNER)


@pytest.mark.parametrize("key", ["contains space", "line\nbreak", "tab\tkey"])
def test_story_transfer_key_is_visible_ascii(key: str) -> None:
    with pytest.raises(ValidationError):
        _command(idempotency_key=key)


def test_story_transfer_receipt_hashes_the_idempotency_key_and_keeps_creator_out() -> None:
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
    serialized = receipt.model_dump(mode="json")
    assert serialized["owner_epoch"] == 1
    assert "created_by_actor_ref" not in serialized
    assert "child_name" not in serialized and "email" not in serialized
    with pytest.raises(ValidationError):
        StoryTeacherOwnerTransferReceiptV1(
            **{**serialized, "action": "OFFBOARD"}
        )
