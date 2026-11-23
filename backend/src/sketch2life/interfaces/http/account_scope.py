"""Granted scope of a verified adult account (FEAT-066 T0.2; SRS l.794).

``load_granted_scope`` is the one reader of "which organizations and classes does this
account hold an active assignment in". ``GET /api/auth/v1/me`` returns it for client routing;
later tasks (for example the job reader) reuse it for membership checks. It never replaces
server-side authorisation: every route still re-authorises on its own.

Rules (plan T0.2, review F-4):
- only active assignments in active organizations count;
- a class is listed only when the classroom exists, belongs to the same organization as the
  assignment, and is active (a dangling or cross-organization ``class_id`` is dropped);
- an assignment without ``class_id`` is organization-wide: its role is reported in the
  organization entry only, classes are never enumerated for it;
- only the roles ``teacher`` and ``school_manager`` carry organization scope; Parent and
  Platform Admin accounts get empty lists even if stray assignment rows exist;
- both lists are capped and ordered by stable keys, ``truncated`` tells that a cap was hit;
- ``organization_id`` (optional) restricts the read to one organization (T0.4 job reader).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)

MAX_SCOPE_ORGANIZATIONS = 100
MAX_SCOPE_CLASSES = 500
ORGANIZATION_SCOPED_ACCOUNT_ROLES = frozenset({"teacher", "school_manager"})

ManagedAccounts = Literal["NONE", "PLATFORM"]


@dataclass(frozen=True)
class GrantedOrganization:
    organization_id: str
    display_name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class GrantedClass:
    organization_id: str
    class_id: str
    display_name: str
    role: str
    state: str


@dataclass(frozen=True)
class GrantedScope:
    account_id: str
    managed: ManagedAccounts
    organizations: tuple[GrantedOrganization, ...] = field(default_factory=tuple)
    classes: tuple[GrantedClass, ...] = field(default_factory=tuple)
    truncated: bool = False

    def organization_ids(self) -> frozenset[str]:
        return frozenset(item.organization_id for item in self.organizations)


def load_granted_scope(
    db: Session, identity: AdultIdentityModel, *, organization_id: str | None = None
) -> GrantedScope:
    """Read the scope of ``identity`` with at most three bounded queries.

    ``organization_id`` narrows every query to that one organization (FEAT-066 T0.4: the job
    reader asks "does this account hold an active assignment in the organization of this job"
    without paying for, or being cut by, the caps of the whole account scope). The rules above
    are unchanged; an organization the account has no active assignment in simply yields an
    empty scope.
    """

    managed: ManagedAccounts = "PLATFORM" if identity.account_role == "platform_admin" else "NONE"
    if identity.account_role not in ORGANIZATION_SCOPED_ACCOUNT_ROLES:
        return GrantedScope(account_id=identity.account_id, managed=managed)

    subject = identity.subject
    truncated = False

    organization_filter = (
        [OrganizationModel.organization_id == organization_id]
        if organization_id is not None
        else []
    )
    organization_rows = db.execute(
        select(OrganizationModel.organization_id, OrganizationModel.display_name)
        .where(
            OrganizationModel.state == "active",
            *organization_filter,
            exists().where(
                OrganizationAssignmentModel.organization_id == OrganizationModel.organization_id,
                OrganizationAssignmentModel.subject == subject,
                OrganizationAssignmentModel.active.is_(True),
            ),
        )
        .order_by(OrganizationModel.organization_id)
        .limit(MAX_SCOPE_ORGANIZATIONS + 1)
    ).all()
    if len(organization_rows) > MAX_SCOPE_ORGANIZATIONS:
        truncated = True
        organization_rows = organization_rows[:MAX_SCOPE_ORGANIZATIONS]
    if not organization_rows:
        return GrantedScope(account_id=identity.account_id, managed=managed)
    organization_ids = [row.organization_id for row in organization_rows]

    role_rows = db.execute(
        select(OrganizationAssignmentModel.organization_id, OrganizationAssignmentModel.role)
        .where(
            OrganizationAssignmentModel.subject == subject,
            OrganizationAssignmentModel.active.is_(True),
            OrganizationAssignmentModel.organization_id.in_(organization_ids),
        )
        .distinct()
    ).all()
    roles_by_organization: dict[str, set[str]] = {}
    for role_row in role_rows:
        roles_by_organization.setdefault(role_row.organization_id, set()).add(role_row.role)

    class_rows = db.execute(
        select(
            OrganizationAssignmentModel.organization_id,
            OrganizationAssignmentModel.class_id,
            ClassroomModel.display_name,
            OrganizationAssignmentModel.role,
            ClassroomModel.state,
        )
        .join(
            ClassroomModel,
            (ClassroomModel.class_id == OrganizationAssignmentModel.class_id)
            & (ClassroomModel.organization_id == OrganizationAssignmentModel.organization_id),
        )
        .where(
            OrganizationAssignmentModel.subject == subject,
            OrganizationAssignmentModel.active.is_(True),
            OrganizationAssignmentModel.class_id.is_not(None),
            OrganizationAssignmentModel.organization_id.in_(organization_ids),
            ClassroomModel.state == "active",
        )
        .order_by(
            OrganizationAssignmentModel.organization_id,
            OrganizationAssignmentModel.class_id,
            OrganizationAssignmentModel.role,
        )
        .limit(MAX_SCOPE_CLASSES + 1)
    ).all()
    if len(class_rows) > MAX_SCOPE_CLASSES:
        truncated = True
        class_rows = class_rows[:MAX_SCOPE_CLASSES]

    return GrantedScope(
        account_id=identity.account_id,
        managed=managed,
        organizations=tuple(
            GrantedOrganization(
                organization_id=row.organization_id,
                display_name=row.display_name,
                roles=tuple(sorted(roles_by_organization.get(row.organization_id, ()))),
            )
            for row in organization_rows
        ),
        classes=tuple(
            GrantedClass(
                organization_id=row.organization_id,
                class_id=row.class_id,
                display_name=row.display_name,
                role=row.role,
                state=row.state,
            )
            for row in class_rows
        ),
        truncated=truncated,
    )


__all__ = [
    "MAX_SCOPE_CLASSES",
    "MAX_SCOPE_ORGANIZATIONS",
    "GrantedClass",
    "GrantedOrganization",
    "GrantedScope",
    "load_granted_scope",
]
