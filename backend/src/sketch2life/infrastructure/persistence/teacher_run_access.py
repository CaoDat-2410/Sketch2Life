"""The Teacher access of a StoryRun, read from the current BE1 assignment (FEAT-066 T-4a1).

One query over BE1 tables only (no Story table): the Teacher identity, its active class-scoped
``teacher`` assignment, the class of the run's Managed Profile and that class's state. Nothing is
cached, so a revocation or a move of the child takes effect on the next step (SRS l.553, l.864).
The profile and the enrollment state are not conditions: a withdrawn child's run stays reachable
for the class Teacher (FR-C-08 cleanup, T-4a1-DEC-3).

A run written by T-4b2 carries ``occurrence_ref``: its access follows the occurrence pin instead
(T-4b2 D10): the CURRENT ``responsible_teacher_ref`` of the occurrence who also holds an active
exact-class ``teacher`` assignment. ``created_by_actor_ref`` never grants access (SRS l.553).

The occurrence-pin rule is written ONCE, in ``occurrence_pin_select``, over the identity's
``account_id``: the access port adds the caller's subject and issuer; the Teacher job port of the
video generation (T-4b3b D14) adds the caller's account id. A change to the rule is therefore a
change to both.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_actor import TeacherRunAccess
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
)


def occurrence_pin_select(*columns: Any, occurrence_ref: Any, organization_id: Any) -> Select[Any]:
    """The occurrence-pin rule (T-4b2 D10, T-4b3b D14): the select over the occurrence, its class,
    the exact-class ``teacher`` assignment and the identity, restricted to the identity that is the
    occurrence's CURRENT responsible Teacher, active, with the role ``teacher``.

    The caller adds who is asking (the access port: subject and issuer; the job port: the account
    id). ``occurrence_ref`` and ``organization_id`` are values or columns of an enclosing query.
    """

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
            OCCURRENCES.c.responsible_teacher_ref == AdultIdentityModel.account_id,
            OrganizationAssignmentModel.role == "teacher",
            OrganizationAssignmentModel.active.is_(True),
            AdultIdentityModel.state == "active",
            AdultIdentityModel.account_role == "teacher",
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
        """The occurrence-pin rule: a plain read of the occurrence (no row lock, so no cycle with
        the occurrence-first lock order of the create and of T-5a), the identity's account id as
        the responsible Teacher, and the exact-class assignment (``FOR SHARE`` with ``lock``)."""

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
