"""The actor guard of the StoryRun step routes: an active Parent or an active Teacher (T-4a1).

``require_story_run_actor`` is a plain call, not a FastAPI dependency, on purpose: the handlers
call it at the place ``_require_parent`` stood, so FastAPI still validates the body and the headers
first and the check order of every route is unchanged. It answers the one uniform 404
``RESOURCE_NOT_FOUND`` for every other caller (no identity, inactive, issuer mismatch, Manager,
Platform Admin, no role): the existence of a run is an actor matter (SRS l.864-865, l.1664-1676),
so there is no 403 in this guard and no existence oracle for run ids.

The guard decides only the role. Whether a Teacher may act on one run is decided per request from
the CURRENT assignment inside the repository (FR-T-14, l.553): this module never caches it.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository

_ROLE_KINDS = {"parent": RunActorKind.PARENT, "teacher": RunActorKind.TEACHER}


def require_story_run_actor(db: Session, principal: VerifiedPrincipal) -> RunActor:
    identity = db.get(AdultIdentityModel, principal.subject)
    kind = _ROLE_KINDS.get(identity.account_role or "") if identity is not None else None
    if (
        identity is None
        or kind is None
        or identity.state != "active"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    return RunActor(kind=kind, account_id=identity.account_id)


def story_run_repository(db: Session, actor: RunActor) -> SqlParentStoryRunRepository:
    """The StoryRun repository of the step routes (T-4b3a D1).

    A Parent builds it exactly as before T-4a1 (no actor, no access port), so the Parent code path
    and its bytes do not change; a Teacher builds it with the actor and the access port that
    re-reads the CURRENT assignment on every step.
    """

    if actor.is_teacher:
        return SqlParentStoryRunRepository(db, actor=actor, teacher_access=SqlTeacherRunAccess(db))
    return SqlParentStoryRunRepository(db)


def story_video_repository(db: Session, actor: RunActor) -> SqlStoryVideoRepository:
    """The video repository of the step routes (T-4b3b D1): the same rule as the story repository.

    A Parent builds it exactly as before (``SqlStoryVideoRepository(db)``: no actor, no access
    port); a Teacher builds it with the actor and the access port that re-reads the CURRENT
    occurrence-pin assignment on every step.
    """

    if actor.is_teacher:
        return SqlStoryVideoRepository(db, actor, SqlTeacherRunAccess(db))
    return SqlStoryVideoRepository(db)


__all__ = ["require_story_run_actor", "story_run_repository", "story_video_repository"]
