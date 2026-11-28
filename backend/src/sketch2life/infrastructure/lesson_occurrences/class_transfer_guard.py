"""BE1 transfer-state adapter shared by Story and class-scoped write boundaries."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, with_expression

from sketch2life.application.ports.class_transfer_state import (
    AuthorizedClassTransfer,
    ClassTransferState,
)
from sketch2life.contracts.schemas.story_teacher_owner_transfer import (
    StoryTeacherOwnerTransferCommandV1,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)


class SqlClassTransferState(ClassTransferState):
    """Read BE1 transfer state using the caller's existing SQLAlchemy transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def is_pending(self, *, organization_id: str, class_id: str, lock_class: bool = False) -> bool:
        if lock_class:
            self._session.scalar(
                select(ClassroomModel.class_id)
                .where(
                    ClassroomModel.organization_id == organization_id,
                    ClassroomModel.class_id == class_id,
                )
                .with_for_update(read=True)
            )
        return (
            self._session.scalar(
                select(Be1TeacherAssignmentTransferModel.transfer_id).where(
                    Be1TeacherAssignmentTransferModel.organization_id == organization_id,
                    Be1TeacherAssignmentTransferModel.class_id == class_id,
                    Be1TeacherAssignmentTransferModel.state.in_(
                        ("TRANSFER_PENDING", "RECONCILE_REQUIRED")
                    ),
                )
            )
            is not None
        )

    def authorize_story_transfer(
        self, command: StoryTeacherOwnerTransferCommandV1
    ) -> AuthorizedClassTransfer | None:
        classroom = self._session.scalar(
            select(ClassroomModel)
            .where(
                ClassroomModel.organization_id == command.organization_ref,
                ClassroomModel.class_id == command.class_ref,
            )
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
        if classroom is None:
            return None
        transfer = self._session.scalar(
            select(Be1TeacherAssignmentTransferModel)
            .where(
                Be1TeacherAssignmentTransferModel.transfer_id == command.transfer_id,
                Be1TeacherAssignmentTransferModel.organization_id == command.organization_ref,
                Be1TeacherAssignmentTransferModel.class_id == command.class_ref,
                Be1TeacherAssignmentTransferModel.state.in_(
                    ("TRANSFER_PENDING", "RECONCILE_REQUIRED")
                ),
            )
            .with_for_update()
        )
        if (
            transfer is None
            or transfer.action != command.action
            or transfer.fenced_revision != command.assignment_revision
            or transfer.old_assignment_id is None
        ):
            return None
        old_assignment = self._session.get(
            OrganizationAssignmentModel, transfer.old_assignment_id
        )
        if (
            old_assignment is None
            or old_assignment.active
            or old_assignment.organization_id != command.organization_ref
            or old_assignment.class_id != command.class_ref
            or old_assignment.role != "teacher"
            or old_assignment.subject != transfer.old_subject
        ):
            return None
        old_identity = self._session.get(AdultIdentityModel, transfer.old_subject)
        if old_identity is None:
            return None

        new_teacher_ref: str | None = None
        if transfer.new_assignment_id is not None:
            new_assignment = self._session.get(
                OrganizationAssignmentModel, transfer.new_assignment_id
            )
            new_identity = (
                self._session.get(AdultIdentityModel, transfer.new_subject)
                if transfer.new_subject is not None
                else None
            )
            if (
                new_assignment is None
                or new_assignment.active
                or new_assignment.organization_id != command.organization_ref
                or new_assignment.class_id != command.class_ref
                or new_assignment.role != "teacher"
                or new_assignment.subject != transfer.new_subject
                or new_identity is None
                or new_identity.state != "active"
                or new_identity.account_role != "teacher"
            ):
                return None
            new_teacher_ref = new_identity.account_id
        if (
            command.old_owner_teacher_ref != old_identity.account_id
            or command.new_owner_teacher_ref != new_teacher_ref
        ):
            return None
        if classroom.assignment_revision != transfer.fenced_revision:
            return None
        return AuthorizedClassTransfer(
            transfer_id=transfer.transfer_id,
            organization_id=transfer.organization_id,
            class_id=transfer.class_id,
            action=transfer.action,
            old_teacher_ref=old_identity.account_id,
            new_teacher_ref=new_teacher_ref,
            assignment_revision=transfer.fenced_revision,
        )


def with_class_transfer_state(statement: Select[Any]) -> Select[Any]:
    """Project pending-transfer state with the class row already being read or locked."""
    pending = (
        select(Be1TeacherAssignmentTransferModel.transfer_id)
        .where(
            Be1TeacherAssignmentTransferModel.organization_id
            == ClassroomModel.organization_id,
            Be1TeacherAssignmentTransferModel.class_id == ClassroomModel.class_id,
            Be1TeacherAssignmentTransferModel.state.in_(
                ("TRANSFER_PENDING", "RECONCILE_REQUIRED")
            ),
        )
        .correlate(ClassroomModel)
        .exists()
    )
    return statement.options(with_expression(ClassroomModel.transfer_pending, pending))


def class_transfer_is_pending(
    db: Session, *, organization_id: str, class_id: str, lock_class: bool = True
) -> bool:
    return SqlClassTransferState(db).is_pending(
        organization_id=organization_id, class_id=class_id, lock_class=lock_class
    )


__all__ = ["SqlClassTransferState", "class_transfer_is_pending", "with_class_transfer_state"]
