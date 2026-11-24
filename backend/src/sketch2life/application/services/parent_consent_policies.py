"""Use cases for drafting and activating immutable Parent consent policies."""

from __future__ import annotations

import hashlib
import re
import uuid

from sketch2life.application.ports.parent_consent_policies import (
    ParentConsentPolicyRecord,
    ParentConsentPolicyRepositoryError,
    ParentConsentPolicyRepositoryPort,
)

PARENT_STORY_PERSONALIZATION_PURPOSE = "PARENT_STORY_PERSONALIZATION"
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_MAX_POLICY_TEXT_LENGTH = 4000


class ParentConsentPolicyServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


class ParentConsentPolicyService:
    def __init__(self, repository: ParentConsentPolicyRepositoryPort) -> None:
        self._repository = repository

    def get_active(self) -> ParentConsentPolicyRecord | None:
        return self._repository.get_active_policy()

    def list_policies(self) -> list[ParentConsentPolicyRecord]:
        return self._repository.list_policies()

    def create_draft(
        self, *, version: str, text: str, actor_subject: str
    ) -> ParentConsentPolicyRecord:
        normalized_version = version.strip()
        normalized_text = text.strip()
        if not _VERSION_PATTERN.fullmatch(normalized_version):
            raise ParentConsentPolicyServiceError(422, "PARENT_CONSENT_POLICY_VERSION_INVALID")
        if not normalized_text or len(normalized_text) > _MAX_POLICY_TEXT_LENGTH:
            raise ParentConsentPolicyServiceError(422, "PARENT_CONSENT_POLICY_TEXT_INVALID")
        return self._repository.create_draft(
            policy_id=str(uuid.uuid4()),
            version=normalized_version,
            purpose_code=PARENT_STORY_PERSONALIZATION_PURPOSE,
            text=normalized_text,
            text_sha256=hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
            actor_subject=actor_subject,
        )

    def activate(self, *, policy_id: str, actor_subject: str) -> ParentConsentPolicyRecord:
        try:
            uuid.UUID(policy_id)
        except ValueError:
            raise ParentConsentPolicyServiceError(404, "PARENT_CONSENT_POLICY_NOT_FOUND") from None
        return self._repository.activate(policy_id=policy_id, actor_subject=actor_subject)


__all__ = ["ParentConsentPolicyService", "ParentConsentPolicyServiceError"]
