"""SQL adapter for current organization-wide School Manager authorization."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.manager_story_run_scope import (
    ManagerStoryRunAuthorization,
    ManagerStoryRunScopeDecision,
)
from sketch2life.application.ports.story_run_force_close import (
    ManagerStoryRunForceCloseFailure,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)


class SqlManagerStoryRunScope:
    def __init__(self, session: Session) -> None:
        self._session = session

    def authorize_manager(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        lock: bool,
    ) -> ManagerStoryRunAuthorization:
        identity_statement = select(AdultIdentityModel).where(
            AdultIdentityModel.subject == principal_subject
        )
        organization_statement = select(OrganizationModel).where(
            OrganizationModel.organization_id == organization_id
        )
        assignment_statement = select(OrganizationAssignmentModel).where(
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.subject == principal_subject,
            OrganizationAssignmentModel.active.is_(True),
            OrganizationAssignmentModel.pending_activation.is_(False),
        )
        if lock:
            identity_statement = identity_statement.with_for_update(read=True)
            organization_statement = organization_statement.with_for_update(read=True)
            assignment_statement = assignment_statement.with_for_update(read=True)
        try:
            identity = self._session.scalar(identity_statement)
            organization = self._session.scalar(organization_statement)
            assignments = tuple(self._session.scalars(assignment_statement).all())
        except SQLAlchemyError:
            self._session.rollback()
            raise ManagerStoryRunForceCloseFailure(
                503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
            ) from None

        if (
            organization is None
            or organization.state != "active"
            or identity is None
            or identity.state != "active"
            or identity.issuer != principal_issuer
            or identity.account_role not in {"school_manager", "teacher"}
            or not assignments
        ):
            return ManagerStoryRunAuthorization(ManagerStoryRunScopeDecision.OUT_OF_SCOPE)

        if identity.account_role == "school_manager":
            manager_assignments = tuple(
                row for row in assignments if row.role == "school_admin"
            )
            if not manager_assignments:
                return ManagerStoryRunAuthorization(ManagerStoryRunScopeDecision.OUT_OF_SCOPE)
            if not any(row.class_id is None for row in manager_assignments):
                return ManagerStoryRunAuthorization(ManagerStoryRunScopeDecision.ROLE_DENIED)
            actor_material = f"{principal_issuer}\0{principal_subject}".encode()
            actor_ref = hashlib.sha256(
                b"be1.manager-story-run-force-close.actor.v1\0" + actor_material
            ).hexdigest()
            return ManagerStoryRunAuthorization(
                ManagerStoryRunScopeDecision.AUTHORIZED,
                audit_actor_ref=actor_ref,
            )

        if any(row.role in {"teacher", "guide", "observer"} for row in assignments):
            return ManagerStoryRunAuthorization(ManagerStoryRunScopeDecision.ROLE_DENIED)
        return ManagerStoryRunAuthorization(ManagerStoryRunScopeDecision.OUT_OF_SCOPE)


__all__ = ["SqlManagerStoryRunScope"]
