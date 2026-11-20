"""Teacher scope of lesson occurrences (SRS l.864-865, l.1652; T-3a-DEC-2, T-3a-DEC-3).

Two entry points share one set of facts (the caller's active teacher-family assignment rows in an
organization) and the pure decisions of ``domain.lesson_occurrences``:

* ``authorize_create``: a class id from the request body. Unknown class, or a caller who is not a
  valid Teacher with a row in the class's organization: uniform 404 ``RESOURCE_NOT_FOUND`` (a
  stranger never learns that the class exists). In that organization: no ``teacher`` row for this
  class is 409 ``TEACHER_ASSIGNMENT_REQUIRED``; a ``guide``/``observer`` row for it only is 403
  ``ACTION_NOT_ALLOWED``.
* ``authorize_occurrence``: an existing occurrence id. Anyone not covering the class (stranger,
  other organization, revoked assignment, School Manager, Parent) gets the same uniform 404 as an
  unknown id. A write also needs the ``teacher`` role and ``responsible_teacher_ref`` equal to the
  caller's account (403 otherwise).

The organization and class of an existing occurrence are the stored opaque refs; no class row is
read. Account ids, never identity-provider subjects, are the refs that the occurrence stores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.model import (
    TEACHER_FAMILY_ROLES,
    AccessOutcome,
    AssignmentFact,
    decide_create,
    decide_read,
    decide_write,
)
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)


class LessonOccurrenceError(Exception):
    """A refusal with its HTTP status and public code; the router maps it to the CONV-1 body."""

    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        field_errors: list[dict[str, str]] | None = None,
        current_version: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.field_errors = field_errors
        self.current_version = current_version
        super().__init__(code)


def not_found() -> LessonOccurrenceError:
    return LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")


@dataclass(frozen=True, slots=True)
class CallerFacts:
    account_ref: str
    rows: tuple[AssignmentFact, ...]


@dataclass(frozen=True, slots=True)
class CreateAuthorization:
    classroom: ClassroomModel
    account_ref: str


@dataclass(frozen=True, slots=True)
class OccurrenceAccess:
    occurrence: RowMapping
    account_ref: str


def load_caller_facts(
    db: Session, principal: VerifiedPrincipal, organization_id: str
) -> CallerFacts | None:
    """The caller's active teacher-family rows in ``organization_id``; ``None`` when not a Teacher.

    ``None`` covers: no identity, an inactive identity, an issuer that differs from the verified
    token, any account role other than ``teacher``, and no active row in the organization.
    """
    if not principal.subject or not principal.issuer:
        return None
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "teacher"
        or identity.issuer != principal.issuer
    ):
        return None
    rows = db.scalars(
        select(OrganizationAssignmentModel).where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.subject == principal.subject,
            OrganizationAssignmentModel.active.is_(True),
            OrganizationAssignmentModel.role.in_(sorted(TEACHER_FAMILY_ROLES)),
        )
    ).all()
    if not rows:
        return None
    return CallerFacts(
        account_ref=identity.account_id,
        rows=tuple(AssignmentFact(role=row.role, class_id=row.class_id) for row in rows),
    )


def _raise_for(outcome: AccessOutcome) -> None:
    if outcome is AccessOutcome.PROCEED:
        return
    if outcome is AccessOutcome.FORBIDDEN:
        raise LessonOccurrenceError(403, "ACTION_NOT_ALLOWED")
    if outcome is AccessOutcome.ASSIGNMENT_REQUIRED:
        raise LessonOccurrenceError(409, "TEACHER_ASSIGNMENT_REQUIRED")
    raise not_found()


def authorize_create(
    db: Session, principal: VerifiedPrincipal, class_id: str
) -> CreateAuthorization:
    """Resolve the class and decide create access; the class row comes back read-locked."""
    classroom = db.scalar(select(ClassroomModel).where(ClassroomModel.class_id == class_id))
    if classroom is None:
        raise not_found()
    facts = load_caller_facts(db, principal, classroom.organization_id)
    if facts is None:
        raise not_found()
    _raise_for(decide_create(facts.rows, class_id))
    # FOR SHARE: a concurrent class change waits for this transaction (T-3a-DEC-4).
    locked = db.scalar(
        select(ClassroomModel)
        .where(ClassroomModel.class_id == class_id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if locked is None:
        raise not_found()
    return CreateAuthorization(classroom=locked, account_ref=facts.account_ref)


def authorize_occurrence(
    db: Session,
    principal: VerifiedPrincipal,
    occurrence_id: str,
    *,
    write: bool = False,
    lock: str | None = None,
) -> OccurrenceAccess:
    """Load an occurrence and decide access (T3A-D3).

    ``lock`` is ``None``, ``"share"`` or ``"update"`` (row lock on the occurrence).
    """
    statement: Any = select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id)
    if lock == "share":
        statement = statement.with_for_update(read=True)
    elif lock == "update":
        statement = statement.with_for_update()
    row = db.execute(statement).mappings().one_or_none()
    if row is None:
        raise not_found()
    facts = load_caller_facts(db, principal, row["organization_ref"])
    if facts is None:
        raise not_found()
    if write:
        outcome = decide_write(
            facts.rows,
            row["class_ref"],
            caller_account_ref=facts.account_ref,
            responsible_teacher_ref=row["responsible_teacher_ref"],
        )
    else:
        outcome = decide_read(facts.rows, row["class_ref"])
    _raise_for(outcome)
    return OccurrenceAccess(occurrence=row, account_ref=facts.account_ref)


__all__ = [
    "CallerFacts",
    "CreateAuthorization",
    "LessonOccurrenceError",
    "OccurrenceAccess",
    "authorize_create",
    "authorize_occurrence",
    "load_caller_facts",
    "not_found",
]
