"""The actor of a StoryRun step: the owning Parent or the current class Teacher (FEAT-066 T-4a1).

SRS l.1663-1676 name the caller of every step after the create "Actor của run"; FR-T-14 (l.553)
says the Teacher's right to a run follows the CURRENT assignment, never the creator. This module
holds the two small types the guard needs and the port that answers the Teacher question. It
knows no table and no HTTP.

Storage of a Teacher run: ``actor_scope_kind = 'ORGANIZATION'``, ``actor_scope_ref`` = the
organization id, ``profile_ref`` = the Managed Profile child id. A run created by T-4b2 also holds
the Teacher lock and ``occurrence_ref`` (DDL-B2) and is reached through the occurrence pin; a row
without ``occurrence_ref`` is a T-4a1/T-13a test fixture and keeps the interim child-class rule
(T-4a1-DEC-2).
Two things stay apart:

* the **owner scope** of the run row (``ORGANIZATION`` + organization id for a Teacher): who the
  run belongs to, used to find the row; and
* the **command scope** of a receipt or a review decision (``ORGANIZATION`` + the digest of the
  calling principal for a Teacher): who gave the command, used for idempotency and for "the same
  actor confirmed the subject".
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal

PARENT_COMMAND_SCOPE_KIND = "PARENT_ACCOUNT"
TEACHER_COMMAND_SCOPE_KIND = "ORGANIZATION"
CLASS_STATE_ACTIVE = "active"


class RunActorKind(StrEnum):
    PARENT = "PARENT"
    TEACHER = "TEACHER"


@dataclass(frozen=True, slots=True)
class RunActor:
    """An active adult whose role may act on a StoryRun: a Parent or a Teacher."""

    kind: RunActorKind
    account_id: str

    @property
    def is_teacher(self) -> bool:
        return self.kind is RunActorKind.TEACHER

    @property
    def command_scope_kind(self) -> str:
        """The ``actor_scope_kind`` of the receipts and the review decisions of this actor."""

        return TEACHER_COMMAND_SCOPE_KIND if self.is_teacher else PARENT_COMMAND_SCOPE_KIND


@dataclass(frozen=True, slots=True)
class RunAssetOwner:
    """Kind, ref and organization of the Core rows (upload sessions, assets) of one run.

    Parent: ``PARENT_ACCOUNT`` with the typed scope hash and no organization. Teacher:
    ``ORGANIZATION`` with the organization id as ref AND as organization (never NULL, T-4b3a D4).
    """

    kind: str
    ref: str
    organization_id: str | None


@dataclass(frozen=True, slots=True)
class TeacherRunAccess:
    """What the current assignment grants: the class of the child and its state."""

    class_id: str
    class_state: str

    @property
    def writable(self) -> bool:
        """A suspended or archived class is read-only (SRS l.364, l.593, l.1425)."""

        return self.class_state == CLASS_STATE_ACTIVE


class TeacherRunAccessPort(Protocol):
    """Answers "may this Teacher act on this run's child now?" from the CURRENT assignment."""

    def resolve(
        self,
        *,
        principal: VerifiedPrincipal,
        organization_id: str,
        child_id: str | None,
        lock: bool,
        occurrence_ref: str | None = None,
    ) -> TeacherRunAccess | None:
        """The access of an active Teacher with an active class-scoped ``teacher`` assignment to
        the class of the Managed Profile ``(organization_id, child_id)``; ``None`` for everything
        else (org-wide, guide, observer, Manager, a former Teacher, another organization, an
        unknown child, a missing ``child_id``). With ``lock`` the assignment row is held
        ``FOR SHARE`` until the end of the transaction so a revocation cannot slip in between
        the check and the write.

        With ``occurrence_ref`` (a run written by T-4b2) the occurrence pin decides instead of the
        child's class (T-4b2 D10, FR-T-14): the caller must be the CURRENT
        ``responsible_teacher_ref`` of that occurrence in ``organization_id`` and hold an active
        exact-class ``teacher`` assignment to its class. ``created_by_actor_ref`` never grants."""
        ...


__all__ = [
    "CLASS_STATE_ACTIVE",
    "PARENT_COMMAND_SCOPE_KIND",
    "TEACHER_COMMAND_SCOPE_KIND",
    "RunActor",
    "RunActorKind",
    "RunAssetOwner",
    "TeacherRunAccess",
    "TeacherRunAccessPort",
]
