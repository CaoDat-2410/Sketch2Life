"""SQL adapter for the read-only S1a-P profile lookup used by StoryRuns."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupUnavailable,
    ParentStoryProfileReference,
)
from sketch2life.domain.parent_profile_context import SelectedContextEntry
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileContextEntryModel,
    ParentProfileRevisionModel,
)


class SqlParentStoryProfileLookup:
    def __init__(self, session: Session) -> None:
        self._session = session

    def is_owned_profile(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> bool:
        """FEAT-081 C3b: the caller owns this profile (any state); no revision is read."""
        try:
            owned = self._session.scalar(
                select(ParentChildProfileModel.parent_profile_id).where(
                    ParentChildProfileModel.parent_profile_id == profile_id,
                    ParentChildProfileModel.owner_issuer == principal.issuer,
                    ParentChildProfileModel.owner_subject == principal.subject,
                )
            )
        except SQLAlchemyError as exc:
            raise ParentStoryProfileLookupUnavailable("profile ownership unavailable") from exc
        return owned is not None

    def resolve_selected_context_entries(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        entry_ids: Sequence[UUID],
    ) -> list[SelectedContextEntry] | None:
        """T-12a: only the kind and the text of the named entries, only for an ACTIVE profile of
        the caller; a foreign, unknown or pending profile and a foreign id all give ``None``."""

        wanted = set(entry_ids)
        try:
            active = self._session.scalar(
                select(ParentChildProfileModel.parent_profile_id)
                .where(
                    ParentChildProfileModel.parent_profile_id == profile_id,
                    ParentChildProfileModel.owner_issuer == principal.issuer,
                    ParentChildProfileModel.owner_subject == principal.subject,
                    ParentChildProfileModel.state == "ACTIVE",
                    ParentChildProfileModel.deleted_at.is_(None),
                )
                .with_for_update(read=True)
            )
            if active is None:
                return None
            if not wanted:
                return []
            rows = list(
                self._session.scalars(
                    select(ParentProfileContextEntryModel)
                    .where(
                        ParentProfileContextEntryModel.parent_profile_id == profile_id,
                        ParentProfileContextEntryModel.context_entry_id.in_(wanted),
                    )
                    .order_by(
                        ParentProfileContextEntryModel.created_at,
                        ParentProfileContextEntryModel.context_entry_id,
                    )
                )
            )
        except SQLAlchemyError:
            raise ParentStoryProfileLookupUnavailable from None
        if len(rows) != len(wanted):
            return None
        return [SelectedContextEntry(kind=row.entry_kind, text=row.short_text) for row in rows]

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
