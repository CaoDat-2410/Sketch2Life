"""The Teacher access of a StoryRun, read from the current BE1 assignment (FEAT-066 T-4a1).

One query over BE1 tables only (no Story table): the Teacher identity, its active class-scoped
``teacher`` assignment, the class of the run's Managed Profile and that class's state. Nothing is
cached, so a revocation or a move of the child takes effect on the next step (SRS l.553, l.864).
The profile and the enrollment state are not conditions: a withdrawn child's run stays reachable
for the class Teacher (FR-C-08 cleanup, T-4a1-DEC-3).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_actor import TeacherRunAccess
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
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
    ) -> TeacherRunAccess | None:
        if not child_id or not organization_id:
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


__all__ = ["SqlTeacherRunAccess"]
