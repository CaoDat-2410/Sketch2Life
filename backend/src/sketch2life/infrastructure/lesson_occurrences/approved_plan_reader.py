"""PostgreSQL adapter of ``ApprovedPlanReadPort`` (V4-A OPEN-A D8): one read-only statement.

It reads the approved-plan pointer of the occurrence and the revision number of that plan. It
takes no lock and writes nothing, so a Story transaction that calls it never changes Lesson state.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.approved_plan_read import ApprovedPlanRef
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES, PLAN_REVISIONS


class SqlApprovedPlanReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def approved_plan(self, occurrence_ref: str) -> ApprovedPlanRef | None:
        row = self._session.execute(
            select(PLAN_REVISIONS.c.plan_revision_id, PLAN_REVISIONS.c.revision_no)
            .join(
                OCCURRENCES,
                OCCURRENCES.c.approved_plan_revision_id == PLAN_REVISIONS.c.plan_revision_id,
            )
            .where(
                OCCURRENCES.c.occurrence_id == occurrence_ref,
                PLAN_REVISIONS.c.state == "APPROVED",
            )
        ).one_or_none()
        if row is None:
            return None
        return ApprovedPlanRef(plan_revision_id=str(row[0]), revision_no=int(row[1]))


__all__ = ["SqlApprovedPlanReader"]
