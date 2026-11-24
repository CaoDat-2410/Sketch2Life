"""SQLAlchemy adapter for system-managed Parent consent policy versions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_consent_policies import (
    ParentConsentPolicyRecord,
    ParentConsentPolicyRepositoryError,
    ParentConsentPolicyRepositoryPort,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentConsentPolicyModel,
    ParentDataAuthorizationModel,
)


class SqlParentConsentPolicyRepository(ParentConsentPolicyRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active_policy(self) -> ParentConsentPolicyRecord | None:
        try:
            row = self._session.scalar(
                select(ParentConsentPolicyModel).where(
                    ParentConsentPolicyModel.state == "ACTIVE"
                )
            )
        except SQLAlchemyError:
            raise ParentConsentPolicyRepositoryError(
                503, "PARENT_CONSENT_POLICY_STORE_UNAVAILABLE"
            ) from None
        return self._record(row) if row is not None else None

    def list_policies(self) -> list[ParentConsentPolicyRecord]:
        try:
            rows = self._session.scalars(
                select(ParentConsentPolicyModel).order_by(
                    ParentConsentPolicyModel.created_at.desc(),
                    ParentConsentPolicyModel.policy_version.desc(),
                )
            )
            return [self._record(row) for row in rows]
        except SQLAlchemyError:
            raise ParentConsentPolicyRepositoryError(
                503, "PARENT_CONSENT_POLICY_STORE_UNAVAILABLE"
            ) from None

    def create_draft(
        self,
        *,
        policy_id: str,
        version: str,
        purpose_code: str,
        text: str,
        text_sha256: str,
        actor_subject: str,
    ) -> ParentConsentPolicyRecord:
        try:
            legacy_authorization = self._session.scalar(
                select(ParentDataAuthorizationModel.authorization_id)
                .where(ParentDataAuthorizationModel.policy_version == version)
                .limit(1)
            )
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentConsentPolicyRepositoryError(
                503, "PARENT_CONSENT_POLICY_STORE_UNAVAILABLE"
            ) from None
        if legacy_authorization is not None:
            raise ParentConsentPolicyRepositoryError(
                409, "PARENT_CONSENT_POLICY_VERSION_CONFLICT"
            )

        row = ParentConsentPolicyModel(
            policy_id=policy_id,
            policy_version=version,
            purpose_code=purpose_code,
            consent_text=text,
            consent_text_sha256=text_sha256,
            state="DRAFT",
            created_by=actor_subject,
        )
        self._session.add(row)
        self._session.add(
            self._audit(
                actor_subject=actor_subject,
                action="PARENT_CONSENT_POLICY_DRAFT_CREATED",
                policy_id=policy_id,
            )
        )
        try:
            self._session.commit()
            self._session.refresh(row)
        except IntegrityError:
            self._session.rollback()
            raise ParentConsentPolicyRepositoryError(
                409, "PARENT_CONSENT_POLICY_VERSION_CONFLICT"
            ) from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentConsentPolicyRepositoryError(
                503, "PARENT_CONSENT_POLICY_STORE_UNAVAILABLE"
            ) from None
        return self._record(row)

    def activate(
        self, *, policy_id: str, actor_subject: str
    ) -> ParentConsentPolicyRecord:
        try:
            row = self._session.scalar(
                select(ParentConsentPolicyModel)
                .where(ParentConsentPolicyModel.policy_id == policy_id)
                .with_for_update()
            )
            if row is None:
                raise ParentConsentPolicyRepositoryError(
                    404, "PARENT_CONSENT_POLICY_NOT_FOUND"
                )
            if row.state == "ACTIVE":
                self._session.commit()
                self._session.refresh(row)
                return self._record(row)
            if row.state != "DRAFT":
                raise ParentConsentPolicyRepositoryError(
                    409, "PARENT_CONSENT_POLICY_VERSION_IMMUTABLE"
                )

            active_rows = self._session.scalars(
                select(ParentConsentPolicyModel)
                .where(ParentConsentPolicyModel.state == "ACTIVE")
                .with_for_update()
            ).all()
            for active_row in active_rows:
                active_row.state = "RETIRED"

            row.state = "ACTIVE"
            row.activated_by = actor_subject
            row.activated_at = datetime.now(UTC)
            self._session.add(
                self._audit(
                    actor_subject=actor_subject,
                    action="PARENT_CONSENT_POLICY_ACTIVATED",
                    policy_id=policy_id,
                )
            )
            self._session.commit()
            self._session.refresh(row)
        except ParentConsentPolicyRepositoryError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise ParentConsentPolicyRepositoryError(
                409, "PARENT_CONSENT_POLICY_ACTIVATION_CONFLICT"
            ) from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentConsentPolicyRepositoryError(
                503, "PARENT_CONSENT_POLICY_STORE_UNAVAILABLE"
            ) from None
        return self._record(row)

    @staticmethod
    def _audit(*, actor_subject: str, action: str, policy_id: str) -> CoreAuditEntryModel:
        return CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id="platform",
            actor_ref=actor_subject,
            action=action,
            resource_type="parent_consent_policy",
            resource_id=policy_id,
            decision="allowed",
        )

    @staticmethod
    def _record(row: ParentConsentPolicyModel) -> ParentConsentPolicyRecord:
        return ParentConsentPolicyRecord(
            policy_id=row.policy_id,
            version=row.policy_version,
            purpose_code=row.purpose_code,
            text=row.consent_text,
            text_sha256=row.consent_text_sha256,
            state=row.state,
            created_by=row.created_by,
            created_at=row.created_at,
            activated_by=row.activated_by,
            activated_at=row.activated_at,
        )


__all__ = ["SqlParentConsentPolicyRepository"]
