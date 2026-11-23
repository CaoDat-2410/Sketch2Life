"""Upload target resolver of purpose ``OCCURRENCE_DOCUMENT`` (T-3a-DEC-9; SRS l.1654, l.1653).

T-2a left this purpose without a resolver (it answers 404 until one is registered under
``app.state.upload_target_resolver_factories``). The resolver answers for the responsible Teacher
of the occurrence only; every other caller (stranger, other organization, revoked assignment,
guide, observer, a Teacher who is not responsible) gets ``None``, which the upload route turns
into the uniform 404. The object prefix carries the organization, as for every Teacher asset.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.upload_sessions import (
    ORGANIZATION_SCOPE,
    UploadScope,
    UploadTargetNotAccepting,
)
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    OccurrenceAccess,
    authorize_occurrence,
    class_is_read_only,
)


class OccurrenceUploadTargetResolver:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _access(self, principal: VerifiedPrincipal, target_ref: str) -> OccurrenceAccess | None:
        if not 0 < len(target_ref) <= 36:
            return None
        try:
            return authorize_occurrence(self._db, principal, target_ref, write=True)
        except LessonOccurrenceError:
            return None

    def resolve(self, principal: VerifiedPrincipal, target_ref: str) -> UploadScope | None:
        access = self._access(principal, target_ref)
        if access is None:
            return None
        occurrence = access.occurrence
        organization_id = str(occurrence["organization_ref"])
        return UploadScope(
            owner_scope_kind=ORGANIZATION_SCOPE,
            owner_scope_ref=None,
            organization_id=organization_id,
            object_prefix=f"occurrences/{organization_id}/{occurrence['occurrence_id']}/",
        )

    def ensure_accepting(self, principal: VerifiedPrincipal, target_ref: str) -> None:
        access = self._access(principal, target_ref)
        if (
            access is None
            or access.occurrence["state"] == "ARCHIVED"
            # T-7b-DEC-9: no new upload for the occurrence of a suspended or archived class.
            or class_is_read_only(self._db, access.occurrence, lock=False)
        ):
            raise UploadTargetNotAccepting("INVALID_STATE_TRANSITION")


__all__ = ["OccurrenceUploadTargetResolver"]
