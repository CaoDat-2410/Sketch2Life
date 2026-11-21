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


__all__ = ["require_story_run_actor"]
