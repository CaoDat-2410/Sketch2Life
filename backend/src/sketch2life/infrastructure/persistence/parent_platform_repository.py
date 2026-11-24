"""SQL adapter for Parent profile sharing, notifications, quota and lesson feedback."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_platform import ParentPlatformError
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_ITEMS, LIBRARY_VERSIONS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentDataAuthorizationModel,
)
from sketch2life.infrastructure.parent_platform import tables

_HISTORY_DAYS = 30
_SHARE_TERM_DAYS = 90
_HCMC = ZoneInfo("Asia/Ho_Chi_Minh")


class SqlParentPlatformRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_profile_share(
        self, *, owner_subject: str, parent_profile_id: str, teacher_subject: str,
        policy_version: str, idempotency_key: str,
    ) -> dict[str, Any]:
        profile = self._session.scalar(
            select(ParentChildProfileModel).where(
                ParentChildProfileModel.parent_profile_id == parent_profile_id,
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state == "ACTIVE",
            )
        )
        if profile is None:
            raise ParentPlatformError(404, "PARENT_PROFILE_NOT_FOUND")
        if self._session.scalar(
            select(ParentDataAuthorizationModel.authorization_id).where(
                ParentDataAuthorizationModel.parent_profile_id == parent_profile_id,
                ParentDataAuthorizationModel.policy_version == policy_version,
                ParentDataAuthorizationModel.state == "GRANTED",
            ).limit(1)
        ) is None:
            raise ParentPlatformError(403, "PARENT_DATA_AUTHORIZATION_REQUIRED")

        teacher = self._session.scalar(
            select(AdultIdentityModel).where(
                AdultIdentityModel.subject == teacher_subject,
                AdultIdentityModel.account_role == "teacher",
                AdultIdentityModel.state == "active",
            )
        )
        if teacher is None:
            raise ParentPlatformError(404, "TEACHER_ACCOUNT_NOT_FOUND")

        key_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        request_hash = _hash({"parent_profile_id": parent_profile_id, "teacher_subject": teacher_subject})
        prior = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(
                tables.PROFILE_SHARE_GRANTS.c.owner_subject == owner_subject,
                tables.PROFILE_SHARE_GRANTS.c.create_idempotency_key_sha256 == key_hash,
            )
        ).mappings().one_or_none()
        if prior is not None:
            if prior["create_request_sha256"] != request_hash:
                raise ParentPlatformError(409, "INVALID_IDEMPOTENCY_KEY")
            return self._share_response(prior)

        existing = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS.c.grant_id).where(
                tables.PROFILE_SHARE_GRANTS.c.parent_profile_id == parent_profile_id,
                tables.PROFILE_SHARE_GRANTS.c.owner_subject == owner_subject,
                tables.PROFILE_SHARE_GRANTS.c.teacher_subject == teacher_subject,
                tables.PROFILE_SHARE_GRANTS.c.state.in_(("INVITED", "ACTIVE")),
            ).limit(1)
        ).scalar_one_or_none()
        if existing is not None:
            raise ParentPlatformError(409, "PROFILE_SHARE_ALREADY_EXISTS")

        now = datetime.now(UTC)
        grant_id = str(uuid4())
        try:
            self._session.execute(
                insert(tables.PROFILE_SHARE_GRANTS).values(
                    grant_id=grant_id,
                    parent_profile_id=parent_profile_id,
                    owner_subject=owner_subject,
                    teacher_subject=teacher_subject,
                    managed_profile_ref=None,
                    organization_id=None,
                    create_idempotency_key_sha256=key_hash,
                    create_request_sha256=request_hash,
                    state="INVITED",
                    revision=1,
                    created_at=now,
                    expires_at=None,
                    accepted_at=None,
                    revoked_at=None,
                )
            )
            self._insert_notice(
                recipient=teacher_subject,
                kind="PROFILE_SHARE_INVITATION",
                title="Có lời mời chia sẻ hồ sơ",
                resource_kind="PROFILE_SHARE",
                resource_ref=grant_id,
                dedupe_key=f"profile-share-invite:{grant_id}",
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentPlatformError(409, "PROFILE_SHARE_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentPlatformError(503, "PARENT_PLATFORM_STORE_UNAVAILABLE") from None
        row = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
        ).mappings().one()
        return self._share_response(row)

    def list_profile_shares(self, *, owner_subject: str, parent_profile_id: str) -> list[dict[str, Any]]:
        self._owned_profile(owner_subject, parent_profile_id)
        self._expire_shares()
        rows = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(
                tables.PROFILE_SHARE_GRANTS.c.owner_subject == owner_subject,
                tables.PROFILE_SHARE_GRANTS.c.parent_profile_id == parent_profile_id,
            ).order_by(tables.PROFILE_SHARE_GRANTS.c.created_at.desc())
        ).mappings().all()
        return [self._share_response(row) for row in rows]

    def revoke_profile_share(
        self, *, owner_subject: str, parent_profile_id: str, grant_id: str
    ) -> dict[str, Any]:
        row = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(
                tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id,
                tables.PROFILE_SHARE_GRANTS.c.owner_subject == owner_subject,
                tables.PROFILE_SHARE_GRANTS.c.parent_profile_id == parent_profile_id,
            ).with_for_update()
        ).mappings().one_or_none()
        if row is None:
            raise ParentPlatformError(404, "PROFILE_SHARE_NOT_FOUND")
        if row["state"] != "REVOKED":
            now = datetime.now(UTC)
            self._session.execute(
                update(tables.PROFILE_SHARE_GRANTS)
                .where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
                .values(state="REVOKED", revoked_at=now, revision=row["revision"] + 1)
            )
            self._session.commit()
            row = self._session.execute(
                select(tables.PROFILE_SHARE_GRANTS).where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
            ).mappings().one()
        return self._share_response(row)

    def list_teacher_share_invitations(self, *, teacher_subject: str) -> list[dict[str, Any]]:
        self._require_teacher_identity(teacher_subject)
        rows = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(
                tables.PROFILE_SHARE_GRANTS.c.teacher_subject == teacher_subject,
                tables.PROFILE_SHARE_GRANTS.c.state == "INVITED",
            ).order_by(tables.PROFILE_SHARE_GRANTS.c.created_at.asc())
        ).mappings().all()
        return [
            {
                "grant_id": row["grant_id"],
                "parent_profile_ref": row["parent_profile_id"],
                "state": row["state"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def accept_profile_share(
        self, *, teacher_subject: str, grant_id: str, managed_profile_ref: str
    ) -> dict[str, Any]:
        self._require_teacher_identity(teacher_subject)
        row = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(
                tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id,
                tables.PROFILE_SHARE_GRANTS.c.teacher_subject == teacher_subject,
            ).with_for_update()
        ).mappings().one_or_none()
        if row is None:
            raise ParentPlatformError(404, "PROFILE_SHARE_INVITATION_NOT_FOUND")
        if row["state"] == "ACTIVE" and row["managed_profile_ref"] == managed_profile_ref:
            return self._share_response(row)
        if row["state"] != "INVITED":
            raise ParentPlatformError(409, "PROFILE_SHARE_INVITATION_NOT_PENDING")

        managed = self._session.scalar(
            select(ManagedProfileModel).where(
                ManagedProfileModel.child_id == managed_profile_ref,
                ManagedProfileModel.state == "active",
            )
        )
        if managed is None:
            raise ParentPlatformError(404, "MANAGED_PROFILE_NOT_FOUND")
        assignment = self._session.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.subject == teacher_subject,
                OrganizationAssignmentModel.organization_id == managed.organization_id,
                OrganizationAssignmentModel.active.is_(True),
                OrganizationAssignmentModel.role == "teacher",
                or_(OrganizationAssignmentModel.class_id.is_(None),
                    OrganizationAssignmentModel.class_id == managed.class_id),
            ).limit(1)
        )
        enrollment = self._session.scalar(
            select(EnrollmentModel.enrollment_id).where(
                EnrollmentModel.organization_id == managed.organization_id,
                EnrollmentModel.class_id == managed.class_id,
                EnrollmentModel.child_id == managed.child_id,
                EnrollmentModel.state == "active",
            ).limit(1)
        )
        if assignment is None or enrollment is None:
            raise ParentPlatformError(403, "TEACHER_PROFILE_SCOPE_REQUIRED")

        now = datetime.now(UTC)
        try:
            self._session.execute(
                update(tables.PROFILE_SHARE_GRANTS)
                .where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
                .values(
                    state="ACTIVE",
                    organization_id=managed.organization_id,
                    managed_profile_ref=managed_profile_ref,
                    accepted_at=now,
                    expires_at=now + timedelta(days=_SHARE_TERM_DAYS),
                    revision=row["revision"] + 1,
                )
            )
            self._insert_notice(
                recipient=row["owner_subject"],
                kind="PROFILE_SHARE_ACCEPTED",
                title="Lời mời chia sẻ hồ sơ đã được chấp nhận",
                resource_kind="PROFILE_SHARE",
                resource_ref=grant_id,
                dedupe_key=f"profile-share-accepted:{grant_id}",
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentPlatformError(409, "MANAGED_PROFILE_ALREADY_LINKED") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentPlatformError(503, "PARENT_PLATFORM_STORE_UNAVAILABLE") from None
        accepted = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
        ).mappings().one()
        return self._share_response(accepted)

    def decline_profile_share(self, *, teacher_subject: str, grant_id: str) -> dict[str, Any]:
        self._require_teacher_identity(teacher_subject)
        row = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(
                tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id,
                tables.PROFILE_SHARE_GRANTS.c.teacher_subject == teacher_subject,
            ).with_for_update()
        ).mappings().one_or_none()
        if row is None:
            raise ParentPlatformError(404, "PROFILE_SHARE_INVITATION_NOT_FOUND")
        if row["state"] == "DECLINED":
            return self._share_response(row)
        if row["state"] != "INVITED":
            raise ParentPlatformError(409, "PROFILE_SHARE_INVITATION_NOT_PENDING")
        self._session.execute(
            update(tables.PROFILE_SHARE_GRANTS)
            .where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
            .values(state="DECLINED", revision=row["revision"] + 1)
        )
        self._session.commit()
        declined = self._session.execute(
            select(tables.PROFILE_SHARE_GRANTS).where(tables.PROFILE_SHARE_GRANTS.c.grant_id == grant_id)
        ).mappings().one()
        return self._share_response(declined)

    def list_notifications(
        self, *, recipient_subject: str, limit: int, cursor: str | None
    ) -> tuple[list[dict[str, Any]], str | None]:
        stmt = select(tables.INBOX_ITEMS).where(
            tables.INBOX_ITEMS.c.recipient_subject == recipient_subject
        )
        if cursor:
            created_at, notification_id = _decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    tables.INBOX_ITEMS.c.created_at < created_at,
                    and_(tables.INBOX_ITEMS.c.created_at == created_at,
                         tables.INBOX_ITEMS.c.notification_id < notification_id),
                )
            )
        rows = self._session.execute(
            stmt.order_by(tables.INBOX_ITEMS.c.created_at.desc(),
                          tables.INBOX_ITEMS.c.notification_id.desc()).limit(limit + 1)
        ).mappings().all()
        has_more = len(rows) > limit
        page = rows[:limit]
        items = [self._notification_response(row) for row in page]
        next_cursor = _encode_cursor(page[-1]["created_at"], page[-1]["notification_id"]) if has_more and page else None
        return items, next_cursor

    def mark_notification_read(
        self, *, recipient_subject: str, notification_id: str
    ) -> dict[str, Any]:
        row = self._session.execute(
            select(tables.INBOX_ITEMS).where(
                tables.INBOX_ITEMS.c.recipient_subject == recipient_subject,
                tables.INBOX_ITEMS.c.notification_id == notification_id,
            ).with_for_update()
        ).mappings().one_or_none()
        if row is None:
            raise ParentPlatformError(404, "NOTIFICATION_NOT_FOUND")
        if row["read_at"] is None:
            now = datetime.now(UTC)
            self._session.execute(
                update(tables.INBOX_ITEMS)
                .where(tables.INBOX_ITEMS.c.notification_id == notification_id)
                .values(read_at=now)
            )
            self._session.commit()
            row = self._session.execute(
                select(tables.INBOX_ITEMS).where(tables.INBOX_ITEMS.c.notification_id == notification_id)
            ).mappings().one()
        return self._notification_response(row)

    def get_parent_quota(self, *, account_id: str) -> dict[str, Any]:
        now_local = datetime.now(_HCMC)
        period_start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period_start_local.month == 12:
            period_end_local = period_start_local.replace(year=period_start_local.year + 1, month=1)
        else:
            period_end_local = period_start_local.replace(month=period_start_local.month + 1)
        period_start = period_start_local.astimezone(UTC)
        period_end = period_end_local.astimezone(UTC)
        granted = self._session.scalar(
            select(func.coalesce(func.sum(tables.VIDEO_QUOTA_GRANTS.c.quantity), 0)).where(
                tables.VIDEO_QUOTA_GRANTS.c.owner_scope_kind == "PARENT_ACCOUNT",
                tables.VIDEO_QUOTA_GRANTS.c.owner_scope_ref == account_id,
                tables.VIDEO_QUOTA_GRANTS.c.period_start == period_start,
                tables.VIDEO_QUOTA_GRANTS.c.period_end == period_end,
            )
        )
        usage = self._session.scalar(
            select(func.count()).select_from(tables.VIDEO_QUOTA_USAGE).where(
                tables.VIDEO_QUOTA_USAGE.c.owner_scope_kind == "PARENT_ACCOUNT",
                tables.VIDEO_QUOTA_USAGE.c.owner_scope_ref == account_id,
                tables.VIDEO_QUOTA_USAGE.c.used_at >= period_start,
                tables.VIDEO_QUOTA_USAGE.c.used_at < period_end,
            )
        )
        configured = int(granted or 0) > 0
        return {
            "contract": "ParentVideoQuotaSummaryV1",
            "configuration_state": "CONFIGURED" if configured else "NOT_CONFIGURED",
            "period_start": period_start,
            "period_end": period_end,
            "granted": int(granted) if configured else None,
            "used": int(usage or 0) if configured else None,
            "available": max(int(granted or 0) - int(usage or 0), 0) if configured else None,
        }

    def record_lesson_delivery(
        self, *, organization_id: str, lesson_id: str, version_id: str,
        managed_profile_ref: str, teacher_subject: str, idempotency_key: str,
    ) -> dict[str, Any]:
        teacher = self._teacher_assignment(teacher_subject, organization_id)
        managed = self._session.scalar(
            select(ManagedProfileModel).where(
                ManagedProfileModel.child_id == managed_profile_ref,
                ManagedProfileModel.organization_id == organization_id,
                ManagedProfileModel.state == "active",
            )
        )
        if managed is None or (teacher.class_id and teacher.class_id != managed.class_id):
            raise ParentPlatformError(404, "MANAGED_PROFILE_NOT_FOUND")
        if self._session.scalar(
            select(EnrollmentModel.enrollment_id).where(
                EnrollmentModel.organization_id == organization_id,
                EnrollmentModel.class_id == managed.class_id,
                EnrollmentModel.child_id == managed.child_id,
                EnrollmentModel.state == "active",
            ).limit(1)
        ) is None:
            raise ParentPlatformError(409, "MANAGED_PROFILE_NOT_ENROLLED")

        version = self._session.execute(
            select(LIBRARY_VERSIONS, LIBRARY_ITEMS.c.title, LIBRARY_ITEMS.c.organization_id)
            .join(LIBRARY_ITEMS, LIBRARY_ITEMS.c.lesson_id == LIBRARY_VERSIONS.c.lesson_id)
            .where(
                LIBRARY_VERSIONS.c.version_id == version_id,
                LIBRARY_VERSIONS.c.lesson_id == lesson_id,
                LIBRARY_VERSIONS.c.review_state == "APPROVED",
                LIBRARY_ITEMS.c.organization_id == organization_id,
                LIBRARY_ITEMS.c.state == "ACTIVE",
                LIBRARY_ITEMS.c.moderation_state == "VISIBLE",
            )
        ).mappings().one_or_none()
        if version is None:
            raise ParentPlatformError(404, "APPROVED_LESSON_VERSION_NOT_FOUND")
        lesson_content = version["content_json"]
        topic = lesson_content.get("topic", "") if isinstance(lesson_content, dict) else ""
        now = datetime.now(UTC)
        key_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        request_hash = _hash({
            "lesson_id": lesson_id,
            "version_id": version_id,
            "managed_profile_ref": managed_profile_ref,
        })
        prior = self._session.execute(
            select(tables.DELIVERY_OCCURRENCES).where(
                tables.DELIVERY_OCCURRENCES.c.organization_id == organization_id,
                tables.DELIVERY_OCCURRENCES.c.teacher_subject == teacher_subject,
                tables.DELIVERY_OCCURRENCES.c.idempotency_key_sha256 == key_hash,
            )
        ).mappings().one_or_none()
        if prior is not None:
            if prior["request_sha256"] != request_hash:
                raise ParentPlatformError(409, "INVALID_IDEMPOTENCY_KEY")
            return {"contract": "LessonDeliveryOccurrenceV1", **dict(prior)}
        occurrence_id = str(uuid4())
        row = {
            "occurrence_id": occurrence_id,
            "organization_id": organization_id,
            "lesson_id": lesson_id,
            "version_id": version_id,
            "managed_profile_ref": managed_profile_ref,
            "teacher_subject": teacher_subject,
            "lesson_title_snapshot": str(version["title"])[:160],
            "lesson_topic_snapshot": str(topic)[:120],
            "idempotency_key_sha256": key_hash,
            "request_sha256": request_hash,
            "delivered_at": now,
        }
        try:
            self._session.execute(insert(tables.DELIVERY_OCCURRENCES).values(**row))
            self._session.commit()
        except (IntegrityError, SQLAlchemyError):
            self._session.rollback()
            raise ParentPlatformError(503, "LESSON_DELIVERY_STORE_UNAVAILABLE") from None
        return {"contract": "LessonDeliveryOccurrenceV1", **row}

    def list_parent_deliveries(
        self, *, owner_subject: str, parent_profile_id: str, policy_version: str,
        limit: int, cursor: str | None
    ) -> tuple[list[dict[str, Any]], str | None]:
        self._owned_profile(owner_subject, parent_profile_id)
        self._expire_shares()
        active_share = and_(
            tables.PROFILE_SHARE_GRANTS.c.owner_subject == owner_subject,
            tables.PROFILE_SHARE_GRANTS.c.parent_profile_id == parent_profile_id,
            tables.PROFILE_SHARE_GRANTS.c.state == "ACTIVE",
            tables.PROFILE_SHARE_GRANTS.c.expires_at > datetime.now(UTC),
            tables.PROFILE_SHARE_GRANTS.c.managed_profile_ref == tables.DELIVERY_OCCURRENCES.c.managed_profile_ref,
            tables.PROFILE_SHARE_GRANTS.c.organization_id == tables.DELIVERY_OCCURRENCES.c.organization_id,
        )
        stmt = select(tables.DELIVERY_OCCURRENCES).join(
            tables.PROFILE_SHARE_GRANTS, active_share
        ).join(
            ParentDataAuthorizationModel,
            and_(
                ParentDataAuthorizationModel.parent_profile_id == tables.PROFILE_SHARE_GRANTS.c.parent_profile_id,
                ParentDataAuthorizationModel.policy_version == policy_version,
                ParentDataAuthorizationModel.state == "GRANTED",
            ),
        ).where(
            tables.DELIVERY_OCCURRENCES.c.delivered_at >= datetime.now(UTC) - timedelta(days=_HISTORY_DAYS)
        )
        if cursor:
            created_at, occurrence_id = _decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    tables.DELIVERY_OCCURRENCES.c.delivered_at < created_at,
                    and_(tables.DELIVERY_OCCURRENCES.c.delivered_at == created_at,
                         tables.DELIVERY_OCCURRENCES.c.occurrence_id < occurrence_id),
                )
            )
        rows = self._session.execute(
            stmt.order_by(tables.DELIVERY_OCCURRENCES.c.delivered_at.desc(),
                          tables.DELIVERY_OCCURRENCES.c.occurrence_id.desc()).limit(limit + 1)
        ).mappings().all()
        has_more = len(rows) > limit
        page = rows[:limit]
        items = [self._delivery_response(row, parent_profile_id) for row in page]
        next_cursor = _encode_cursor(page[-1]["delivered_at"], page[-1]["occurrence_id"]) if has_more and page else None
        return items, next_cursor

    def submit_delivery_feedback(
        self, *, owner_subject: str, parent_profile_id: str, occurrence_id: str,
        policy_version: str, feedback_text: str,
    ) -> dict[str, Any]:
        self._owned_profile(owner_subject, parent_profile_id)
        occurrence = self._accessible_occurrence(
            owner_subject, parent_profile_id, occurrence_id, policy_version
        )
        prior = self._session.execute(
            select(tables.DELIVERY_FEEDBACK).where(
                tables.DELIVERY_FEEDBACK.c.occurrence_id == occurrence_id,
                tables.DELIVERY_FEEDBACK.c.parent_profile_id == parent_profile_id,
                tables.DELIVERY_FEEDBACK.c.parent_subject == owner_subject,
            ).with_for_update()
        ).mappings().one_or_none()
        now = datetime.now(UTC)
        feedback_id = prior["feedback_id"] if prior else str(uuid4())
        try:
            if prior:
                self._session.execute(
                    update(tables.DELIVERY_FEEDBACK)
                    .where(tables.DELIVERY_FEEDBACK.c.feedback_id == feedback_id)
                    .values(feedback_text=feedback_text, updated_at=now)
                )
            else:
                self._session.execute(
                    insert(tables.DELIVERY_FEEDBACK).values(
                        feedback_id=feedback_id,
                        occurrence_id=occurrence_id,
                        parent_profile_id=parent_profile_id,
                        parent_subject=owner_subject,
                        feedback_text=feedback_text,
                        created_at=now,
                        updated_at=now,
                    )
                )
            self._insert_notice(
                recipient=occurrence["teacher_subject"],
                kind="LESSON_FEEDBACK",
                title="Có phản hồi mới về hoạt động",
                resource_kind="LESSON_DELIVERY",
                resource_ref=occurrence_id,
                dedupe_key=f"lesson-feedback:{feedback_id}:{now.isoformat()}",
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentPlatformError(409, "LESSON_FEEDBACK_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentPlatformError(503, "LESSON_FEEDBACK_STORE_UNAVAILABLE") from None
        row = self._session.execute(
            select(tables.DELIVERY_FEEDBACK).where(tables.DELIVERY_FEEDBACK.c.feedback_id == feedback_id)
        ).mappings().one()
        return self._feedback_response(row)

    def reply_to_delivery_feedback(
        self, *, organization_id: str, teacher_subject: str, occurrence_id: str,
        reply_text: str,
    ) -> dict[str, Any]:
        self._teacher_assignment(teacher_subject, organization_id)
        feedback = self._session.execute(
            select(tables.DELIVERY_FEEDBACK, tables.DELIVERY_OCCURRENCES.c.occurrence_id)
            .join(tables.DELIVERY_OCCURRENCES,
                  tables.DELIVERY_OCCURRENCES.c.occurrence_id == tables.DELIVERY_FEEDBACK.c.occurrence_id)
            .where(
                tables.DELIVERY_FEEDBACK.c.occurrence_id == occurrence_id,
                tables.DELIVERY_OCCURRENCES.c.organization_id == organization_id,
            )
        ).mappings().one_or_none()
        if feedback is None:
            raise ParentPlatformError(404, "LESSON_FEEDBACK_NOT_FOUND")
        reply_id = str(uuid4())
        now = datetime.now(UTC)
        try:
            self._session.execute(
                insert(tables.FEEDBACK_REPLIES).values(
                    reply_id=reply_id,
                    feedback_id=feedback["feedback_id"],
                    organization_id=organization_id,
                    teacher_subject=teacher_subject,
                    reply_text=reply_text,
                    created_at=now,
                )
            )
            self._insert_notice(
                recipient=feedback["parent_subject"],
                kind="LESSON_REPLY",
                title="Giáo viên đã phản hồi góp ý",
                resource_kind="LESSON_DELIVERY",
                resource_ref=occurrence_id,
                dedupe_key=f"lesson-feedback-reply:{reply_id}",
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentPlatformError(503, "LESSON_FEEDBACK_STORE_UNAVAILABLE") from None
        return {
            "contract": "LessonFeedbackReplyV1",
            "reply_id": reply_id,
            "occurrence_id": occurrence_id,
            "reply_text": reply_text,
            "created_at": now,
        }

    def _accessible_occurrence(
        self, owner_subject: str, parent_profile_id: str, occurrence_id: str, policy_version: str
    ):
        self._expire_shares()
        row = self._session.execute(
            select(tables.DELIVERY_OCCURRENCES)
            .join(
                tables.PROFILE_SHARE_GRANTS,
                and_(
                    tables.PROFILE_SHARE_GRANTS.c.managed_profile_ref == tables.DELIVERY_OCCURRENCES.c.managed_profile_ref,
                    tables.PROFILE_SHARE_GRANTS.c.organization_id == tables.DELIVERY_OCCURRENCES.c.organization_id,
                ),
            )
            .join(
                ParentDataAuthorizationModel,
                and_(
                    ParentDataAuthorizationModel.parent_profile_id == tables.PROFILE_SHARE_GRANTS.c.parent_profile_id,
                    ParentDataAuthorizationModel.policy_version == policy_version,
                    ParentDataAuthorizationModel.state == "GRANTED",
                ),
            )
            .where(
                tables.DELIVERY_OCCURRENCES.c.occurrence_id == occurrence_id,
                tables.PROFILE_SHARE_GRANTS.c.owner_subject == owner_subject,
                tables.PROFILE_SHARE_GRANTS.c.parent_profile_id == parent_profile_id,
                tables.PROFILE_SHARE_GRANTS.c.state == "ACTIVE",
                tables.PROFILE_SHARE_GRANTS.c.expires_at > datetime.now(UTC),
                tables.DELIVERY_OCCURRENCES.c.delivered_at >= datetime.now(UTC) - timedelta(days=_HISTORY_DAYS),
            )
        ).mappings().one_or_none()
        if row is None:
            raise ParentPlatformError(404, "LESSON_DELIVERY_NOT_FOUND")
        return row

    def _delivery_response(self, occurrence, parent_profile_id: str) -> dict[str, Any]:
        feedback = self._session.execute(
            select(tables.DELIVERY_FEEDBACK).where(
                tables.DELIVERY_FEEDBACK.c.occurrence_id == occurrence["occurrence_id"],
                tables.DELIVERY_FEEDBACK.c.parent_profile_id == parent_profile_id,
            )
        ).mappings().one_or_none()
        replies = []
        if feedback is not None:
            replies = [
                {
                    "reply_id": reply["reply_id"],
                    "reply_text": reply["reply_text"],
                    "created_at": reply["created_at"],
                }
                for reply in self._session.execute(
                    select(tables.FEEDBACK_REPLIES).where(
                        tables.FEEDBACK_REPLIES.c.feedback_id == feedback["feedback_id"]
                    ).order_by(tables.FEEDBACK_REPLIES.c.created_at.asc())
                ).mappings().all()
            ]
        return {
            "contract": "ParentLessonDeliveryV1",
            "occurrence_id": occurrence["occurrence_id"],
            "lesson_id": occurrence["lesson_id"],
            "version_id": occurrence["version_id"],
            "title": occurrence["lesson_title_snapshot"],
            "topic": occurrence["lesson_topic_snapshot"],
            "delivered_at": occurrence["delivered_at"],
            "feedback": self._feedback_response(feedback) if feedback is not None else None,
            "replies": replies,
        }

    def _owned_profile(self, owner_subject: str, profile_id: str) -> ParentChildProfileModel:
        profile = self._session.scalar(
            select(ParentChildProfileModel).where(
                ParentChildProfileModel.parent_profile_id == profile_id,
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state == "ACTIVE",
            )
        )
        if profile is None:
            raise ParentPlatformError(404, "PARENT_PROFILE_NOT_FOUND")
        return profile

    def _expire_shares(self) -> None:
        now = datetime.now(UTC)
        result = self._session.execute(
            update(tables.PROFILE_SHARE_GRANTS)
            .where(
                tables.PROFILE_SHARE_GRANTS.c.state == "ACTIVE",
                tables.PROFILE_SHARE_GRANTS.c.expires_at <= now,
            )
            .values(state="EXPIRED", revision=tables.PROFILE_SHARE_GRANTS.c.revision + 1)
        )
        if result.rowcount:
            self._session.commit()

    def _require_teacher_identity(self, subject: str) -> None:
        identity = self._session.get(AdultIdentityModel, subject)
        if identity is None or identity.state != "active" or identity.account_role != "teacher":
            raise ParentPlatformError(403, "TEACHER_ROLE_REQUIRED")

    def _teacher_assignment(self, subject: str, organization_id: str):
        self._require_teacher_identity(subject)
        assignment = self._session.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.subject == subject,
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.active.is_(True),
                OrganizationAssignmentModel.role == "teacher",
            ).limit(1)
        )
        if assignment is None:
            raise ParentPlatformError(403, "TEACHER_ORGANIZATION_SCOPE_REQUIRED")
        return assignment

    def _insert_notice(
        self, *, recipient: str, kind: str, title: str, resource_kind: str,
        resource_ref: str, dedupe_key: str,
    ) -> None:
        self._session.execute(
            insert(tables.INBOX_ITEMS).values(
                notification_id=str(uuid4()),
                recipient_subject=recipient,
                notice_kind=kind,
                safe_title=title,
                resource_kind=resource_kind,
                resource_ref=resource_ref,
                dedupe_key=dedupe_key,
                created_at=datetime.now(UTC),
                read_at=None,
            )
        )

    @staticmethod
    def _share_response(row) -> dict[str, Any]:
        state = row["state"]
        if state == "ACTIVE" and row["expires_at"] and row["expires_at"] <= datetime.now(UTC):
            state = "EXPIRED"
        return {
            "contract": "ParentProfileShareGrantV1",
            "grant_id": row["grant_id"],
            "parent_profile_id": row["parent_profile_id"],
            "teacher_subject": row["teacher_subject"],
            "managed_profile_ref": row["managed_profile_ref"] if state == "ACTIVE" else None,
            "state": state,
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "accepted_at": row["accepted_at"],
            "revoked_at": row["revoked_at"],
            "revision": row["revision"],
        }

    @staticmethod
    def _notification_response(row) -> dict[str, Any]:
        return {
            "contract": "NotificationInboxItemV1",
            "notification_id": row["notification_id"],
            "kind": row["notice_kind"],
            "title": row["safe_title"],
            "resource_kind": row["resource_kind"],
            "resource_ref": row["resource_ref"],
            "created_at": row["created_at"],
            "read_at": row["read_at"],
        }

    @staticmethod
    def _feedback_response(row) -> dict[str, Any]:
        return {
            "contract": "LessonDeliveryFeedbackV1",
            "feedback_id": row["feedback_id"],
            "feedback_text": row["feedback_text"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def _hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _encode_cursor(created_at: datetime, resource_id: str) -> str:
    raw = f"{created_at.isoformat()}|{resource_id}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8")
        timestamp, resource_id = raw.split("|", 1)
        created_at = datetime.fromisoformat(timestamp)
        if created_at.tzinfo is None or not resource_id:
            raise ValueError
        return created_at, resource_id
    except (ValueError, UnicodeDecodeError, binascii.Error):
        raise ParentPlatformError(422, "PAGINATION_CURSOR_INVALID") from None


__all__ = ["SqlParentPlatformRepository"]
