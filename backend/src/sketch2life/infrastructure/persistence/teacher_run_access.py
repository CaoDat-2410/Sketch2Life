"""The Teacher access of a StoryRun, read from the current BE1 assignment (FEAT-066 T-4a1).

One query over BE1 tables only (no Story table): the Teacher identity, its active class-scoped
``teacher`` assignment, the class of the run's Managed Profile and that class's state. Nothing is
cached, so a revocation or a move of the child takes effect on the next step (SRS l.553, l.864).
The profile and the enrollment state are not conditions: a withdrawn child's run stays reachable
for the class Teacher (FR-C-08 cleanup, T-4a1-DEC-3).

A run written by T-4b2 carries ``occurrence_ref`` and the immutable organization/class binding. Its
access follows the CURRENT BE1 class assignment, not the occurrence's creation-time responsible
Teacher: a completed transfer changes the class assignment and the Story run owner together.
``created_by_actor_ref`` never grants access (SRS l.553).

The occurrence-pin rule is written ONCE, in ``occurrence_pin_select``, over the identity's
``account_id``: the access port adds the caller's subject and issuer; the Teacher job port of the
video generation (T-4b3b D14) adds the caller's account id. A change to the rule is therefore a
change to both.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_actor import TeacherRunAccess
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
)


def occurrence_pin_select(*columns: Any, occurrence_ref: Any, organization_id: Any) -> Select[Any]:
    """The occurrence-pin rule (T-6b): the select over the occurrence, its class, the exact-class
    active ``teacher`` assignment and the identity. The assignment is the current authority;
    ``responsible_teacher_ref`` records who opened the occurrence and does not survive reassignment.

    The caller adds who is asking (the access port: subject and issuer; the job port: the account
    id). ``occurrence_ref`` and ``organization_id`` are values or columns of an enclosing query.
    """

    # A fresh occurrence is pinned to its creating Teacher. After reassignment, the completed
    # receipt and the current active assignment extend that pin to the successor.
    transferred_owner = (
        select(Be1TeacherAssignmentTransferModel.transfer_id)
        .where(
            Be1TeacherAssignmentTransferModel.organization_id
            == OCCURRENCES.c.organization_ref,
            Be1TeacherAssignmentTransferModel.class_id == OCCURRENCES.c.class_ref,
            Be1TeacherAssignmentTransferModel.action == "REASSIGN",
            Be1TeacherAssignmentTransferModel.state == "COMPLETED",
            Be1TeacherAssignmentTransferModel.new_subject
            == OrganizationAssignmentModel.subject,
            Be1TeacherAssignmentTransferModel.story_receipt_ref.is_not(None),
        )
        .correlate(OCCURRENCES, OrganizationAssignmentModel)
        .exists()
    )
    return (
        select(*columns)
        .select_from(OCCURRENCES)
        .join(
            ClassroomModel,
            (ClassroomModel.organization_id == OCCURRENCES.c.organization_ref)
            & (ClassroomModel.class_id == OCCURRENCES.c.class_ref),
        )
        .join(
            OrganizationAssignmentModel,
            (OrganizationAssignmentModel.organization_id == OCCURRENCES.c.organization_ref)
            & (OrganizationAssignmentModel.class_id == OCCURRENCES.c.class_ref),
        )
        .join(
            AdultIdentityModel,
            AdultIdentityModel.subject == OrganizationAssignmentModel.subject,
        )
        .where(
            OCCURRENCES.c.occurrence_id == occurrence_ref,
            OCCURRENCES.c.organization_ref == organization_id,
            OrganizationAssignmentModel.role == "teacher",
            OrganizationAssignmentModel.active.is_(True),
            AdultIdentityModel.state == "active",
            AdultIdentityModel.account_role == "teacher",
            or_(
                OCCURRENCES.c.responsible_teacher_ref == AdultIdentityModel.account_id,
                transferred_owner,
            ),
        )
    )


class SqlTeacherRunAccess:
    def __init__(self, session: Session) -> None:
        self._session = session

    def resolve(
        self,
        *,
        principal: VerifiedPrincipal,
        organization_id: str,
        child_id: str | None,
        lock: bool,
        occurrence_ref: str | None = None,
    ) -> TeacherRunAccess | None:
        if not organization_id:
            return None
        if occurrence_ref:
            return self._resolve_occurrence(
                principal=principal,
                organization_id=organization_id,
                occurrence_ref=occurrence_ref,
                lock=lock,
            )
        if not child_id:
            return None
        statement = (
            select(ClassroomModel.class_id, ClassroomModel.state)
            .select_from(ManagedProfileModel)
            .join(
                ClassroomModel,
                (ClassroomModel.organization_id == ManagedProfileModel.organization_id)
                & (ClassroomModel.class_id == ManagedProfileModel.class_id),
            )
            .join(
                OrganizationAssignmentModel,
                (OrganizationAssignmentModel.organization_id == ManagedProfileModel.organization_id)
                & (OrganizationAssignmentModel.class_id == ManagedProfileModel.class_id),
            )
            .join(
                AdultIdentityModel,
                AdultIdentityModel.subject == OrganizationAssignmentModel.subject,
            )
            .where(
                ManagedProfileModel.organization_id == organization_id,
                ManagedProfileModel.child_id == child_id,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
                OrganizationAssignmentModel.subject == principal.subject,
                AdultIdentityModel.state == "active",
                AdultIdentityModel.account_role == "teacher",
                AdultIdentityModel.issuer == principal.issuer,
            )
        )
        if lock:
            # FOR SHARE on the assignment row and on the class row: a revocation or a class
            # suspension (FOR UPDATE) waits for this transaction, so no destructive write lands
            # after it (SRS l.364, l.593, l.1425; T-7b F-02 pattern; T13A-I-01). A suspension locks
            # the class row only, so the order run, assignment, class cannot invert.
            statement = statement.with_for_update(
                read=True, of=(OrganizationAssignmentModel, ClassroomModel)
            )
        row = self._session.execute(statement).first()
        if row is None:
            return None
        return TeacherRunAccess(class_id=str(row[0]), class_state=str(row[1]))

    def _resolve_occurrence(
        self,
        *,
        principal: VerifiedPrincipal,
        organization_id: str,
        occurrence_ref: str,
        lock: bool,
    ) -> TeacherRunAccess | None:
        """Resolve the current exact-class Teacher assignment for the occurrence's immutable
        organization/class pin. The occurrence read stays unlocked to preserve the create/T-5a lock
        order; the assignment and class are ``FOR SHARE`` when the caller requests a write lock."""

        statement = occurrence_pin_select(
            ClassroomModel.class_id,
            ClassroomModel.state,
            occurrence_ref=occurrence_ref,
            organization_id=organization_id,
        ).where(
            OrganizationAssignmentModel.subject == principal.subject,
            AdultIdentityModel.issuer == principal.issuer,
        )
        if lock:
            statement = statement.with_for_update(
                read=True, of=(OrganizationAssignmentModel, ClassroomModel)
            )
        row = self._session.execute(statement).first()
        if row is None:
            return None
        return TeacherRunAccess(class_id=str(row[0]), class_state=str(row[1]))


__all__ = ["SqlTeacherRunAccess", "occurrence_pin_select"]
