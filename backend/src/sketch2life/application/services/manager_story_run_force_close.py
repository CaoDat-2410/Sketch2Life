"""Authorize and orchestrate Manager StoryRun conflict reads and force-close commands."""

from __future__ import annotations

from sketch2life.application.ports.manager_story_run_scope import (
    ManagerStoryRunAuthorization,
    ManagerStoryRunScope,
    ManagerStoryRunScopeDecision,
)
from sketch2life.application.ports.story_run_force_close import (
    ManagerStoryRunConflict,
    ManagerStoryRunForceClosed,
    ManagerStoryRunForceCloseFailure,
    StoryRunForceCloseRepository,
)
from sketch2life.domain.teacher_run_force_close import (
    StoryRunForceCloseRuleError,
    build_force_close_receipt_identity,
)


class ManagerStoryRunForceCloseService:
    def __init__(
        self,
        *,
        scope: ManagerStoryRunScope,
        repository: StoryRunForceCloseRepository,
    ) -> None:
        self._scope = scope
        self._repository = repository

    def get_active_conflict(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        teacher_ref: str,
    ) -> ManagerStoryRunConflict:
        self._authorize(
            principal_subject=principal_subject,
            principal_issuer=principal_issuer,
            organization_id=organization_id,
            lock=False,
        )
        conflict = self._repository.find_active_conflict(
            organization_id=organization_id,
            teacher_ref=teacher_ref,
        )
        if conflict is None:
            raise ManagerStoryRunForceCloseFailure(404, "RESOURCE_NOT_FOUND")
        return conflict

    def force_close(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        run_id: str,
        expected_revision: int,
        reason: str,
        idempotency_key: str,
    ) -> ManagerStoryRunForceClosed:
        try:
            identity = build_force_close_receipt_identity(
                principal_ref=principal_subject,
                organization_id=organization_id,
                run_id=run_id,
                expected_revision=expected_revision,
                reason=reason,
                idempotency_key=idempotency_key,
            )
        except StoryRunForceCloseRuleError:
            raise ManagerStoryRunForceCloseFailure(400, "INVALID_REQUEST") from None

        authorization = self._authorize(
            principal_subject=principal_subject,
            principal_issuer=principal_issuer,
            organization_id=organization_id,
            lock=True,
        )
        if authorization.audit_actor_ref is None:
            raise ManagerStoryRunForceCloseFailure(
                503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
            )
        return self._repository.force_close(
            organization_id=organization_id,
            run_id=run_id,
            expected_revision=expected_revision,
            identity=identity,
            audit_actor_ref=authorization.audit_actor_ref,
        )

    def _authorize(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        lock: bool,
    ) -> ManagerStoryRunAuthorization:
        authorization = self._scope.authorize_manager(
            principal_subject=principal_subject,
            principal_issuer=principal_issuer,
            organization_id=organization_id,
            lock=lock,
        )
        if authorization.decision is ManagerStoryRunScopeDecision.OUT_OF_SCOPE:
            raise ManagerStoryRunForceCloseFailure(404, "RESOURCE_NOT_FOUND")
        if authorization.decision is ManagerStoryRunScopeDecision.ROLE_DENIED:
            raise ManagerStoryRunForceCloseFailure(403, "ACTION_NOT_ALLOWED")
        if authorization.decision is not ManagerStoryRunScopeDecision.AUTHORIZED:
            raise ManagerStoryRunForceCloseFailure(404, "RESOURCE_NOT_FOUND")
        return authorization


__all__ = ["ManagerStoryRunForceCloseService"]
