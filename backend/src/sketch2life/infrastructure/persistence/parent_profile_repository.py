"""SQLAlchemy adapter for Parent profile and data-authorization persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_profiles import (
    ParentProfileRecord,
    ParentProfileRepositoryError,
    ParentProfileRevisionRecord,
)
from sketch2life.application.ports.parent_profiles import ParentProfileRepositoryPort
from sketch2life.application.services.parent_profiles import PARENT_STORY_PERSONALIZATION_PURPOSE
from sketch2life.domain.parent_profiles import ParentProfileRevisionInput
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentDataAuthorizationModel,
    ParentProfileRevisionModel,
)


class SqlParentProfileRepository(ParentProfileRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_profiles(self, *, owner_subject: str) -> list[ParentProfileRecord]:
        profiles = self._session.scalars(
            select(ParentChildProfileModel)
            .where(
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state != "DELETED",
            )
            .order_by(ParentChildProfileModel.updated_at.desc())
        ).all()
        return [self._record(profile) for profile in profiles]

    def get_profile(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> ParentProfileRecord | None:
        profile = self._session.scalar(
            select(ParentChildProfileModel).where(
                ParentChildProfileModel.parent_profile_id == parent_profile_id,
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state != "DELETED",
            )
        )
        return self._record(profile) if profile is not None else None

    def create_profile(
        self,
        *,
        owner_subject: str,
        profile_id: str,
        revision_id: str,
        authorization_id: str,
        revision: ParentProfileRevisionInput,
        revision_hash: str,
        policy_version: str,
        consent_text_sha256: str,
    ) -> ParentProfileRecord:
        now = datetime.now(UTC)
        profile = ParentChildProfileModel(
            parent_profile_id=profile_id,
            owner_subject=owner_subject,
            state="ACTIVE",
            current_revision_ref=None,
            created_at=now,
            updated_at=now,
        )
        self._session.add(profile)
        try:
            self._session.flush()
            revision_row = self._new_revision(
                owner_subject=owner_subject,
                profile_id=profile_id,
                revision_id=revision_id,
                revision_no=1,
                revision=revision,
                revision_hash=revision_hash,
            )
            self._session.add(revision_row)
            self._session.flush()
            profile.current_revision_ref = revision_id
            self._session.add(
                ParentDataAuthorizationModel(
                    authorization_id=authorization_id,
                    parent_profile_id=profile_id,
                    actor_subject=owner_subject,
                    purpose_code=PARENT_STORY_PERSONALIZATION_PURPOSE,
                    policy_version=policy_version,
                    state="GRANTED",
                    source_kind="PARENT_UI",
                    recorded_at=now,
                    evidence_ref=consent_text_sha256,
                    synthetic_demo_flag=False,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentProfileRepositoryError(409, "PARENT_PROFILE_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentProfileRepositoryError(503, "PARENT_PROFILE_STORE_UNAVAILABLE") from None
        return self._record(profile)

    def revise_profile(
        self,
        *,
        owner_subject: str,
        parent_profile_id: str,
        expected_revision: int,
        revision_id: str,
        revision: ParentProfileRevisionInput,
        revision_hash: str,
        policy_version: str,
    ) -> ParentProfileRecord:
        profile = self._get_for_update(owner_subject, parent_profile_id)
        self._require_current_authorization(parent_profile_id, policy_version)
        current = self._current_revision(profile)
        if current.revision_no != expected_revision:
            raise ParentProfileRepositoryError(409, "PARENT_PROFILE_REVISION_CONFLICT")
        new_revision = self._new_revision(
            owner_subject=owner_subject,
            profile_id=parent_profile_id,
            revision_id=revision_id,
            revision_no=current.revision_no + 1,
            revision=revision,
            revision_hash=revision_hash,
        )
        self._session.add(new_revision)
        try:
            self._session.flush()
            profile.current_revision_ref = revision_id
            profile.updated_at = datetime.now(UTC)
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentProfileRepositoryError(409, "PARENT_PROFILE_REVISION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentProfileRepositoryError(503, "PARENT_PROFILE_STORE_UNAVAILABLE") from None
        return self._record(profile)

    def grant_authorization(
        self,
        *,
        owner_subject: str,
        parent_profile_id: str,
        authorization_id: str,
        policy_version: str,
        consent_text_sha256: str,
    ) -> ParentProfileRecord:
        profile = self._get_for_update(owner_subject, parent_profile_id)
        active = self._session.scalars(
            select(ParentDataAuthorizationModel)
            .where(
                ParentDataAuthorizationModel.parent_profile_id == parent_profile_id,
                ParentDataAuthorizationModel.purpose_code
                == PARENT_STORY_PERSONALIZATION_PURPOSE,
                ParentDataAuthorizationModel.state == "GRANTED",
            )
            .with_for_update()
        ).all()
        now = datetime.now(UTC)
        current = next(
            (item for item in active if item.policy_version == policy_version), None
        )
        for authorization in active:
            if authorization is not current:
                authorization.state = "REVOKED"
                authorization.revoked_at = now
        if current is None:
            self._session.add(
                ParentDataAuthorizationModel(
                    authorization_id=authorization_id,
                    parent_profile_id=parent_profile_id,
                    actor_subject=owner_subject,
                    purpose_code=PARENT_STORY_PERSONALIZATION_PURPOSE,
                    policy_version=policy_version,
                    state="GRANTED",
                    source_kind="PARENT_UI",
                    recorded_at=now,
                    evidence_ref=consent_text_sha256,
                    synthetic_demo_flag=False,
                )
            )
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentProfileRepositoryError(409, "PARENT_AUTHORIZATION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentProfileRepositoryError(503, "PARENT_PROFILE_STORE_UNAVAILABLE") from None
        return self._record(profile)

    def revoke_authorization(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> ParentProfileRecord:
        profile = self._get_for_update(owner_subject, parent_profile_id)
        now = datetime.now(UTC)
        active = self._session.scalars(
            select(ParentDataAuthorizationModel)
            .where(
                ParentDataAuthorizationModel.parent_profile_id == parent_profile_id,
                ParentDataAuthorizationModel.purpose_code
                == PARENT_STORY_PERSONALIZATION_PURPOSE,
                ParentDataAuthorizationModel.state == "GRANTED",
            )
            .with_for_update()
        ).all()
        for authorization in active:
            authorization.state = "REVOKED"
            authorization.revoked_at = now
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentProfileRepositoryError(503, "PARENT_PROFILE_STORE_UNAVAILABLE") from None
        return self._record(profile)

    def archive_profile(self, *, owner_subject: str, parent_profile_id: str) -> ParentProfileRecord:
        profile = self._get_for_update(owner_subject, parent_profile_id)
        now = datetime.now(UTC)
        profile.state = "ARCHIVED"
        profile.updated_at = now
        active = self._session.scalars(
            select(ParentDataAuthorizationModel)
            .where(
                ParentDataAuthorizationModel.parent_profile_id == parent_profile_id,
                ParentDataAuthorizationModel.state == "GRANTED",
            )
            .with_for_update()
        ).all()
        for authorization in active:
            authorization.state = "REVOKED"
            authorization.revoked_at = now
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentProfileRepositoryError(503, "PARENT_PROFILE_STORE_UNAVAILABLE") from None
        return self._record(profile)

    def _get_for_update(self, owner_subject: str, parent_profile_id: str) -> ParentChildProfileModel:
        profile = self._session.scalar(
            select(ParentChildProfileModel)
            .where(
                ParentChildProfileModel.parent_profile_id == parent_profile_id,
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state == "ACTIVE",
            )
            .with_for_update()
        )
        if profile is None:
            raise ParentProfileRepositoryError(404, "PARENT_PROFILE_NOT_FOUND")
        return profile

    def _require_current_authorization(self, parent_profile_id: str, policy_version: str) -> None:
        active = self._session.scalar(
            select(ParentDataAuthorizationModel.authorization_id).where(
                ParentDataAuthorizationModel.parent_profile_id == parent_profile_id,
                ParentDataAuthorizationModel.purpose_code
                == PARENT_STORY_PERSONALIZATION_PURPOSE,
                ParentDataAuthorizationModel.policy_version == policy_version,
                ParentDataAuthorizationModel.state == "GRANTED",
            )
        )
        if active is None:
            raise ParentProfileRepositoryError(403, "PARENT_DATA_AUTHORIZATION_REQUIRED")

    def _current_revision(self, profile: ParentChildProfileModel) -> ParentProfileRevisionModel:
        revision = self._session.scalar(
            select(ParentProfileRevisionModel).where(
                ParentProfileRevisionModel.parent_profile_id == profile.parent_profile_id,
                ParentProfileRevisionModel.profile_revision_id == profile.current_revision_ref,
            )
        )
        if revision is None:
            raise ParentProfileRepositoryError(503, "PARENT_PROFILE_REVISION_UNAVAILABLE")
        return revision

    def _record(self, profile: ParentChildProfileModel) -> ParentProfileRecord:
        revision = self._current_revision(profile)
        authorization = self._session.scalar(
            select(ParentDataAuthorizationModel)
            .where(
                ParentDataAuthorizationModel.parent_profile_id == profile.parent_profile_id,
                ParentDataAuthorizationModel.purpose_code
                == PARENT_STORY_PERSONALIZATION_PURPOSE,
            )
            .order_by(
                ParentDataAuthorizationModel.recorded_at.desc(),
                ParentDataAuthorizationModel.authorization_id.desc(),
            )
        )
        return ParentProfileRecord(
            parent_profile_id=profile.parent_profile_id,
            state=profile.state,
            current_revision=ParentProfileRevisionRecord(
                profile_revision_id=revision.profile_revision_id,
                revision_no=revision.revision_no,
                age_months=revision.age_months,
                display_name=revision.display_name,
                interests_summary=revision.interests_summary,
                revision_hash=revision.revision_hash,
                created_at=revision.created_at,
            ),
            authorization_state=authorization.state if authorization else None,
            authorization_policy_version=authorization.policy_version if authorization else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @staticmethod
    def _new_revision(
        *,
        owner_subject: str,
        profile_id: str,
        revision_id: str,
        revision_no: int,
        revision: ParentProfileRevisionInput,
        revision_hash: str,
    ) -> ParentProfileRevisionModel:
        return ParentProfileRevisionModel(
            profile_revision_id=revision_id,
            parent_profile_id=profile_id,
            revision_no=revision_no,
            age_months=revision.age_months,
            age_band_ref=None,
            age_band_version=None,
            display_name=revision.display_name,
            interests_summary=revision.interests_summary,
            authored_by=owner_subject,
            revision_hash=revision_hash,
        )


__all__ = ["SqlParentProfileRepository"]
