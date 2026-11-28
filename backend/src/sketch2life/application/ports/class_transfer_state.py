"""BE1 class-transfer state exposed to Story and class-write adapters through a port."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
)


@dataclass(frozen=True, slots=True)
class AuthorizedClassTransfer:
    transfer_id: str
    organization_id: str
    class_id: str
    action: str
    old_teacher_ref: str
    new_teacher_ref: str | None
    assignment_revision: int


class ClassTransferState(Protocol):
    def is_pending(
        self, *, organization_id: str, class_id: str, lock_class: bool = False
    ) -> bool: ...

    def authorize_story_transfer(
        self, command: StoryTeacherOwnerTransferCommandV1
    ) -> AuthorizedClassTransfer | None: ...


__all__ = ["AuthorizedClassTransfer", "ClassTransferState"]
