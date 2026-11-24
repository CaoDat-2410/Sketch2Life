"""Application boundary for Parent sharing, notifications, lesson history and quota reads."""

from __future__ import annotations

from typing import Any, Protocol


class ParentPlatformError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


class ParentPlatformRepositoryPort(Protocol):
    def create_profile_share(
        self, *, owner_subject: str, parent_profile_id: str, teacher_subject: str,
        policy_version: str, idempotency_key: str,
    ) -> dict[str, Any]: ...

    def list_profile_shares(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> list[dict[str, Any]]: ...

    def revoke_profile_share(
        self, *, owner_subject: str, parent_profile_id: str, grant_id: str
    ) -> dict[str, Any]: ...

    def list_teacher_share_invitations(self, *, teacher_subject: str) -> list[dict[str, Any]]: ...

    def accept_profile_share(
        self, *, teacher_subject: str, grant_id: str, managed_profile_ref: str
    ) -> dict[str, Any]: ...

    def decline_profile_share(self, *, teacher_subject: str, grant_id: str) -> dict[str, Any]: ...

    def list_notifications(
        self, *, recipient_subject: str, limit: int, cursor: str | None
    ) -> tuple[list[dict[str, Any]], str | None]: ...

    def mark_notification_read(
        self, *, recipient_subject: str, notification_id: str
    ) -> dict[str, Any]: ...

    def get_parent_quota(self, *, account_id: str) -> dict[str, Any]: ...

    def record_lesson_delivery(
        self, *, organization_id: str, lesson_id: str, version_id: str,
        managed_profile_ref: str, teacher_subject: str, idempotency_key: str,
    ) -> dict[str, Any]: ...

    def list_parent_deliveries(
        self, *, owner_subject: str, parent_profile_id: str, policy_version: str,
        limit: int, cursor: str | None
    ) -> tuple[list[dict[str, Any]], str | None]: ...

    def submit_delivery_feedback(
        self, *, owner_subject: str, parent_profile_id: str, occurrence_id: str,
        policy_version: str, feedback_text: str,
    ) -> dict[str, Any]: ...

    def reply_to_delivery_feedback(
        self, *, organization_id: str, teacher_subject: str, occurrence_id: str,
        reply_text: str,
    ) -> dict[str, Any]: ...


__all__ = ["ParentPlatformError", "ParentPlatformRepositoryPort"]
