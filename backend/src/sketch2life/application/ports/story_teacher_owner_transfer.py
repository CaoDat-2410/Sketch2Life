"""Story-side owner transfer port; BE1 passes only a versioned metadata contract."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
    StoryTeacherOwnerTransferReceiptV1,
)


class StoryTeacherOwnerTransferUnavailable(RuntimeError):
    """The Story transaction outcome is uncertain and must be reconciled with the same key."""


class StoryTeacherOwnerTransferPort(Protocol):
    def transfer_owner(
        self, command: StoryTeacherOwnerTransferCommandV1
    ) -> StoryTeacherOwnerTransferReceiptV1: ...


__all__ = ["StoryTeacherOwnerTransferPort", "StoryTeacherOwnerTransferUnavailable"]
