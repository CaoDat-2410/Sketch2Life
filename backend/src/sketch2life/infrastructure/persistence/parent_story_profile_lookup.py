"""SQL adapter for the read-only S1a-P profile lookup used by StoryRuns."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupUnavailable,
    ParentStoryProfileReference,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)


class SqlParentStoryProfileLookup:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_owned_profile_current_revision(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> ParentStoryProfileReference | None:
        try:
            profile = self._session.scalar(
                select(ParentChildProfileModel).where(
                    ParentChildProfileModel.parent_profile_id == profile_id,
                    ParentChildProfileModel.owner_issuer == principal.issuer,
                    ParentChildProfileModel.owner_subject == principal.subject,
                    ParentChildProfileModel.state == "ACTIVE",
                    ParentChildProfileModel.deleted_at.is_(None),
                )
            )
            if profile is None:
                return None

            revision = self._session.scalar(
                select(ParentProfileRevisionModel).where(
                    ParentProfileRevisionModel.parent_profile_id == profile.parent_profile_id,
                    ParentProfileRevisionModel.revision_no == profile.current_revision_no,
                )
            )
            if revision is None:
                raise ParentStoryProfileLookupUnavailable
        except SQLAlchemyError:
            raise ParentStoryProfileLookupUnavailable from None

        return ParentStoryProfileReference(
            profile_id=profile.parent_profile_id,
            profile_revision_id=revision.profile_revision_id,
            state=profile.state,
            data_origin=profile.data_origin,
            age_months=revision.age_months,
            interests_summary=revision.interests_summary,
        )


__all__ = ["SqlParentStoryProfileLookup"]
