"""Use cases for Parent profile revisions and authorization lifecycle."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from sketch2life.application.ports.parent_profiles import (
    ParentProfileRecord,
    ParentProfileRepositoryPort,
)
from sketch2life.domain.parent_profiles import (
    ParentProfileRevisionInput,
    ParentProfileRuleViolation,
    normalize_profile_revision,
    profile_revision_sha256,
)

PARENT_STORY_PERSONALIZATION_PURPOSE = "PARENT_STORY_PERSONALIZATION"


class ParentProfileServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentConsentPolicy:
    version: str
    text: str

    @property
    def configured(self) -> bool:
        return bool(
            self.version.strip()
            and len(self.version.strip()) <= 80
            and self.text.strip()
            and len(self.text.strip()) <= 4000
        )

    @property
    def text_sha256(self) -> str:
        return hashlib.sha256(self.text.strip().encode("utf-8")).hexdigest()


class ParentProfileService:
    def __init__(
        self,
        repository: ParentProfileRepositoryPort,
        consent_policy: ParentConsentPolicy,
    ) -> None:
        self._repository = repository
        self._consent_policy = consent_policy

    def consent_policy(self) -> dict[str, str]:
        policy = self._require_policy()
        return {
            "purpose_code": PARENT_STORY_PERSONALIZATION_PURPOSE,
            "policy_version": policy.version,
            "consent_text": policy.text.strip(),
            "consent_text_sha256": policy.text_sha256,
        }

    def list_profiles(self, *, owner_subject: str) -> list[ParentProfileRecord]:
        return self._repository.list_profiles(owner_subject=owner_subject)

    def get_profile(self, *, owner_subject: str, parent_profile_id: str) -> ParentProfileRecord:
        profile = self._repository.get_profile(
            owner_subject=owner_subject, parent_profile_id=parent_profile_id
        )
        if profile is None:
            raise ParentProfileServiceError(404, "PARENT_PROFILE_NOT_FOUND")
        return profile

    def create_profile(
        self,
        *,
        owner_subject: str,
        age_months: int,
        display_name: str,
        interests_summary: str,
        consent_accepted: bool,
        policy_version: str,
    ) -> ParentProfileRecord:
        policy = self._require_policy()
        self._require_acceptance(
            consent_accepted=consent_accepted,
            policy_version=policy_version,
            expected_policy_version=policy.version,
        )
        revision = self._normalize(
            age_months=age_months,
            display_name=display_name,
            interests_summary=interests_summary,
        )
        return self._repository.create_profile(
            owner_subject=owner_subject,
            profile_id=str(uuid.uuid4()),
            revision_id=str(uuid.uuid4()),
            authorization_id=str(uuid.uuid4()),
            revision=revision,
            revision_hash=profile_revision_sha256(revision),
            policy_version=policy.version,
            consent_text_sha256=policy.text_sha256,
        )

    def revise_profile(
        self,
        *,
        owner_subject: str,
        parent_profile_id: str,
        expected_revision: int,
        age_months: int,
        display_name: str,
        interests_summary: str,
    ) -> ParentProfileRecord:
        policy = self._require_policy()
        revision = self._normalize(
            age_months=age_months,
            display_name=display_name,
            interests_summary=interests_summary,
        )
        return self._repository.revise_profile(
            owner_subject=owner_subject,
            parent_profile_id=parent_profile_id,
            expected_revision=expected_revision,
            revision_id=str(uuid.uuid4()),
            revision=revision,
            revision_hash=profile_revision_sha256(revision),
            policy_version=policy.version,
        )

    def grant_authorization(
        self,
        *,
        owner_subject: str,
        parent_profile_id: str,
        consent_accepted: bool,
        policy_version: str,
    ) -> ParentProfileRecord:
        policy = self._require_policy()
        self._require_acceptance(
            consent_accepted=consent_accepted,
            policy_version=policy_version,
            expected_policy_version=policy.version,
        )
        return self._repository.grant_authorization(
            owner_subject=owner_subject,
            parent_profile_id=parent_profile_id,
            authorization_id=str(uuid.uuid4()),
            policy_version=policy.version,
            consent_text_sha256=policy.text_sha256,
        )

    def revoke_authorization(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> ParentProfileRecord:
        return self._repository.revoke_authorization(
            owner_subject=owner_subject,
            parent_profile_id=parent_profile_id,
        )

    def archive_profile(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> ParentProfileRecord:
        return self._repository.archive_profile(
            owner_subject=owner_subject, parent_profile_id=parent_profile_id
        )

    def _require_policy(self) -> ParentConsentPolicy:
        if not self._consent_policy.configured:
            raise ParentProfileServiceError(503, "PARENT_CONSENT_POLICY_UNAVAILABLE")
        return ParentConsentPolicy(
            version=self._consent_policy.version.strip(),
            text=self._consent_policy.text.strip(),
        )

    @staticmethod
    def _require_acceptance(
        *, consent_accepted: bool, policy_version: str, expected_policy_version: str
    ) -> None:
        if not consent_accepted:
            raise ParentProfileServiceError(422, "PARENT_CONSENT_REQUIRED")
        if not policy_version.strip():
            raise ParentProfileServiceError(422, "PARENT_CONSENT_VERSION_REQUIRED")
        if policy_version.strip() != expected_policy_version:
            raise ParentProfileServiceError(409, "PARENT_CONSENT_POLICY_CHANGED")

    @staticmethod
    def _normalize(
        *, age_months: int, display_name: str, interests_summary: str
    ) -> ParentProfileRevisionInput:
        try:
            return normalize_profile_revision(
                age_months=age_months,
                display_name=display_name,
                interests_summary=interests_summary,
            )
        except ParentProfileRuleViolation as exc:
            raise ParentProfileServiceError(422, exc.code) from None


__all__ = [
    "PARENT_STORY_PERSONALIZATION_PURPOSE",
    "ParentConsentPolicy",
    "ParentProfileService",
    "ParentProfileServiceError",
]
