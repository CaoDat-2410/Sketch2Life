"""SQLAlchemy Core mappings for the Parent platform-support read and command models."""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)

PARENT_METADATA = MetaData(schema="parent")
LESSON_METADATA = MetaData(schema="lesson")
NOTIFICATION_METADATA = MetaData(schema="notifications")
BILLING_METADATA = MetaData(schema="billing")

PROFILE_SHARE_GRANTS = Table(
    "profile_share_grants",
    PARENT_METADATA,
    Column("grant_id", String(36), primary_key=True),
    Column(
        "parent_profile_id", String(36),
        nullable=False,
    ),
    Column("owner_subject", String(256), nullable=False),
    Column("teacher_subject", String(256), nullable=False),
    Column("managed_profile_ref", String(128)),
    Column("organization_id", String(128)),
    Column("create_idempotency_key_sha256", String(64), nullable=False),
    Column("create_request_sha256", String(64), nullable=False),
    Column("state", String(16), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True)),
    Column("accepted_at", DateTime(timezone=True)),
    Column("revoked_at", DateTime(timezone=True)),
    UniqueConstraint("owner_subject", "create_idempotency_key_sha256", name="uq_parent_profile_share_idempotency"),
    CheckConstraint("state IN ('INVITED','ACTIVE','DECLINED','REVOKED','EXPIRED')", name="ck_parent_profile_share_state"),
    CheckConstraint("revision > 0", name="ck_parent_profile_share_revision"),
)
Index(
    "ix_parent_profile_share_owner_state",
    PROFILE_SHARE_GRANTS.c.owner_subject,
    PROFILE_SHARE_GRANTS.c.parent_profile_id,
    PROFILE_SHARE_GRANTS.c.state,
    PROFILE_SHARE_GRANTS.c.created_at,
)
Index(
    "ix_parent_profile_share_teacher_state",
    PROFILE_SHARE_GRANTS.c.teacher_subject,
    PROFILE_SHARE_GRANTS.c.state,
    PROFILE_SHARE_GRANTS.c.expires_at,
)
Index(
    "uq_parent_profile_share_active_managed_ref",
    PROFILE_SHARE_GRANTS.c.organization_id,
    PROFILE_SHARE_GRANTS.c.managed_profile_ref,
    unique=True,
    postgresql_where=text("state = 'ACTIVE' AND managed_profile_ref IS NOT NULL"),
)
CheckConstraint(
    "(state = 'ACTIVE' AND organization_id IS NOT NULL AND managed_profile_ref IS NOT NULL "
    "AND accepted_at IS NOT NULL) OR (state = 'INVITED' AND organization_id IS NULL "
    "AND managed_profile_ref IS NULL AND accepted_at IS NULL) OR "
    "state IN ('DECLINED','REVOKED','EXPIRED')",
    name="ck_parent_profile_share_acceptance_shape",
)

DELIVERY_OCCURRENCES = Table(
    "delivery_occurrences",
    LESSON_METADATA,
    Column("occurrence_id", String(36), primary_key=True),
    Column("organization_id", String(128), nullable=False),
    Column("lesson_id", String(36), nullable=False),
    Column("version_id", String(36), nullable=False),
    Column("managed_profile_ref", String(128), nullable=False),
    Column("teacher_subject", String(256), nullable=False),
    Column("lesson_title_snapshot", String(160), nullable=False),
    Column("lesson_topic_snapshot", String(120), nullable=False),
    Column("idempotency_key_sha256", String(64), nullable=False),
    Column("request_sha256", String(64), nullable=False),
    Column("delivered_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("length(managed_profile_ref) > 0", name="ck_lesson_delivery_profile_ref"),
    UniqueConstraint(
        "organization_id", "teacher_subject", "idempotency_key_sha256",
        name="uq_lesson_delivery_idempotency",
    ),
    UniqueConstraint("occurrence_id", "organization_id", name="uq_lesson_delivery_occurrence_org"),
    CheckConstraint(
        "length(idempotency_key_sha256) = 64 AND length(request_sha256) = 64",
        name="ck_lesson_delivery_hashes",
    ),
)
Index(
    "ix_lesson_delivery_profile_time",
    DELIVERY_OCCURRENCES.c.managed_profile_ref,
    DELIVERY_OCCURRENCES.c.delivered_at,
)
Index(
    "ix_lesson_delivery_org_time",
    DELIVERY_OCCURRENCES.c.organization_id,
    DELIVERY_OCCURRENCES.c.delivered_at,
)

DELIVERY_FEEDBACK = Table(
    "delivery_feedback",
    LESSON_METADATA,
    Column("feedback_id", String(36), primary_key=True),
    Column("occurrence_id", String(36), nullable=False),
    Column("parent_profile_id", String(36), nullable=False),
    Column("parent_subject", String(256), nullable=False),
    Column("feedback_text", String(1200), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("length(trim(feedback_text)) BETWEEN 1 AND 1200", name="ck_lesson_feedback_text"),
    UniqueConstraint("occurrence_id", "parent_profile_id", name="uq_lesson_feedback_occurrence_profile"),
)

FEEDBACK_REPLIES = Table(
    "feedback_replies",
    LESSON_METADATA,
    Column("reply_id", String(36), primary_key=True),
    Column("feedback_id", String(36), nullable=False),
    Column("organization_id", String(128), nullable=False),
    Column("teacher_subject", String(256), nullable=False),
    Column("reply_text", String(1200), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("length(trim(reply_text)) BETWEEN 1 AND 1200", name="ck_lesson_feedback_reply_text"),
)
Index("ix_lesson_feedback_reply_feedback_time", FEEDBACK_REPLIES.c.feedback_id, FEEDBACK_REPLIES.c.created_at)

INBOX_ITEMS = Table(
    "inbox_items",
    NOTIFICATION_METADATA,
    Column("notification_id", String(36), primary_key=True),
    Column("recipient_subject", String(256), nullable=False),
    Column("notice_kind", String(48), nullable=False),
    Column("safe_title", String(160), nullable=False),
    Column("resource_kind", String(48)),
    Column("resource_ref", String(128)),
    Column("dedupe_key", String(160), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("read_at", DateTime(timezone=True)),
    UniqueConstraint("recipient_subject", "dedupe_key", name="uq_notification_inbox_dedupe"),
)
Index("ix_notification_inbox_recipient_time", INBOX_ITEMS.c.recipient_subject, INBOX_ITEMS.c.created_at)

VIDEO_QUOTA_GRANTS = Table(
    "video_quota_grants",
    BILLING_METADATA,
    Column("grant_id", String(36), primary_key=True),
    Column("owner_scope_kind", String(24), nullable=False),
    Column("owner_scope_ref", String(128), nullable=False),
    Column("grant_kind", String(24), nullable=False),
    Column("period_start", DateTime(timezone=True), nullable=False),
    Column("period_end", DateTime(timezone=True), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

VIDEO_QUOTA_USAGE = Table(
    "video_quota_usage",
    BILLING_METADATA,
    Column("usage_id", String(36), primary_key=True),
    Column("owner_scope_kind", String(24), nullable=False),
    Column("owner_scope_ref", String(128), nullable=False),
    Column("accepted_request_ref", String(128), nullable=False),
    Column("used_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("owner_scope_kind", "owner_scope_ref", "accepted_request_ref", name="uq_billing_quota_usage_request"),
)

__all__ = [
    "DELIVERY_FEEDBACK",
    "DELIVERY_OCCURRENCES",
    "FEEDBACK_REPLIES",
    "INBOX_ITEMS",
    "PROFILE_SHARE_GRANTS",
    "VIDEO_QUOTA_GRANTS",
    "VIDEO_QUOTA_USAGE",
]
