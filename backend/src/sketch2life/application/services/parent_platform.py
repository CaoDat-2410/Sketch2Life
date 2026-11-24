"""Parent platform use cases with bounded input and explicit role-scoped operations."""

from __future__ import annotations

import re

from sketch2life.application.ports.parent_platform import (
    ParentPlatformError,
    ParentPlatformRepositoryPort,
)

_OPAQUE_REF = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}\Z")


class ParentPlatformService:
    def __init__(self, repository: ParentPlatformRepositoryPort) -> None:
        self._repository = repository

    def create_profile_share(self, *, owner_subject: str, parent_profile_id: str,
                             teacher_subject: str, policy_version: str, idempotency_key: str):
        teacher = teacher_subject.strip()
        if not _OPAQUE_REF.fullmatch(teacher):
            raise ParentPlatformError(422, "TEACHER_REFERENCE_INVALID")
        if not idempotency_key.strip() or len(idempotency_key) > 128:
            raise ParentPlatformError(422, "IDEMPOTENCY_KEY_INVALID")
        return self._repository.create_profile_share(
            owner_subject=owner_subject,
            parent_profile_id=parent_profile_id,
            teacher_subject=teacher,
            policy_version=policy_version,
            idempotency_key=idempotency_key.strip(),
        )

    def list_profile_shares(self, *, owner_subject: str, parent_profile_id: str):
        return self._repository.list_profile_shares(
            owner_subject=owner_subject, parent_profile_id=parent_profile_id
        )

    def revoke_profile_share(self, *, owner_subject: str, parent_profile_id: str, grant_id: str):
        return self._repository.revoke_profile_share(
            owner_subject=owner_subject, parent_profile_id=parent_profile_id, grant_id=grant_id
        )

    def list_teacher_share_invitations(self, *, teacher_subject: str):
        return self._repository.list_teacher_share_invitations(teacher_subject=teacher_subject)

    def accept_profile_share(self, *, teacher_subject: str, grant_id: str, managed_profile_ref: str):
        ref = managed_profile_ref.strip()
        if not _OPAQUE_REF.fullmatch(ref):
            raise ParentPlatformError(422, "MANAGED_PROFILE_REFERENCE_INVALID")
        return self._repository.accept_profile_share(
            teacher_subject=teacher_subject, grant_id=grant_id, managed_profile_ref=ref
        )

    def decline_profile_share(self, *, teacher_subject: str, grant_id: str):
        return self._repository.decline_profile_share(teacher_subject=teacher_subject, grant_id=grant_id)

    def list_notifications(self, *, recipient_subject: str, limit: int, cursor: str | None):
        if limit < 1 or limit > 50:
            raise ParentPlatformError(422, "NOTIFICATION_LIMIT_INVALID")
        return self._repository.list_notifications(
            recipient_subject=recipient_subject, limit=limit, cursor=cursor
        )

    def mark_notification_read(self, *, recipient_subject: str, notification_id: str):
        return self._repository.mark_notification_read(
            recipient_subject=recipient_subject, notification_id=notification_id
        )

    def get_parent_quota(self, *, account_id: str):
        return self._repository.get_parent_quota(account_id=account_id)

    def record_lesson_delivery(self, *, organization_id: str, lesson_id: str, version_id: str,
                               managed_profile_ref: str, teacher_subject: str, idempotency_key: str):
        ref = managed_profile_ref.strip()
        if not _OPAQUE_REF.fullmatch(ref):
            raise ParentPlatformError(422, "MANAGED_PROFILE_REFERENCE_INVALID")
        return self._repository.record_lesson_delivery(
            organization_id=organization_id, lesson_id=lesson_id, version_id=version_id,
            managed_profile_ref=ref, teacher_subject=teacher_subject, idempotency_key=idempotency_key,
        )

    def list_parent_deliveries(self, *, owner_subject: str, parent_profile_id: str,
                               policy_version: str, limit: int, cursor: str | None):
        if limit < 1 or limit > 50:
            raise ParentPlatformError(422, "LESSON_HISTORY_LIMIT_INVALID")
        return self._repository.list_parent_deliveries(
            owner_subject=owner_subject, parent_profile_id=parent_profile_id,
            policy_version=policy_version, limit=limit, cursor=cursor,
        )

    def submit_delivery_feedback(self, *, owner_subject: str, parent_profile_id: str,
                                 occurrence_id: str, policy_version: str, feedback_text: str):
        content = feedback_text.strip()
        if not content or len(content) > 1200:
            raise ParentPlatformError(422, "LESSON_FEEDBACK_INVALID")
        return self._repository.submit_delivery_feedback(
            owner_subject=owner_subject, parent_profile_id=parent_profile_id,
            occurrence_id=occurrence_id, policy_version=policy_version, feedback_text=content,
        )

    def reply_to_delivery_feedback(self, *, organization_id: str, teacher_subject: str,
                                  occurrence_id: str, reply_text: str):
        content = reply_text.strip()
        if not content or len(content) > 1200:
            raise ParentPlatformError(422, "LESSON_FEEDBACK_REPLY_INVALID")
        return self._repository.reply_to_delivery_feedback(
            organization_id=organization_id, teacher_subject=teacher_subject,
            occurrence_id=occurrence_id, reply_text=content,
        )


__all__ = ["ParentPlatformService"]
