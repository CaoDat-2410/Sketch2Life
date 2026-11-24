"""Add Parent share, lesson feedback, inbox, and quota read-model tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261111_parent_platform_support"
down_revision = "20261111_parent_run_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS notifications")
    op.execute("CREATE SCHEMA IF NOT EXISTS billing")

    op.create_table(
        "profile_share_grants",
        sa.Column("grant_id", sa.String(36), primary_key=True),
        sa.Column("parent_profile_id", sa.String(36), nullable=False),
        sa.Column("owner_subject", sa.String(256), nullable=False),
        sa.Column("teacher_subject", sa.String(256), nullable=False),
        sa.Column("managed_profile_ref", sa.String(128)),
        sa.Column("organization_id", sa.String(128)),
        sa.Column("create_idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("create_request_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="INVITED"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"], ["parent.child_profiles.parent_profile_id"],
            ondelete="RESTRICT", name="fk_parent_profile_share_profile",
        ),
        sa.CheckConstraint(
            "state IN ('INVITED','ACTIVE','DECLINED','REVOKED','EXPIRED')",
            name="ck_parent_profile_share_state",
        ),
        sa.CheckConstraint("revision > 0", name="ck_parent_profile_share_revision"),
        sa.CheckConstraint(
            "length(create_idempotency_key_sha256) = 64 AND length(create_request_sha256) = 64",
            name="ck_parent_profile_share_command_hashes",
        ),
        sa.CheckConstraint(
            "(state = 'ACTIVE' AND organization_id IS NOT NULL AND managed_profile_ref IS NOT NULL "
            "AND accepted_at IS NOT NULL) OR (state = 'INVITED' AND organization_id IS NULL "
            "AND managed_profile_ref IS NULL AND accepted_at IS NULL) OR "
            "(state IN ('DECLINED','REVOKED','EXPIRED'))",
            name="ck_parent_profile_share_acceptance_shape",
        ),
        sa.UniqueConstraint(
            "owner_subject", "create_idempotency_key_sha256",
            name="uq_parent_profile_share_idempotency",
        ),
        schema="parent",
    )
    op.create_index(
        "ix_parent_profile_share_owner_state",
        "profile_share_grants",
        ["owner_subject", "parent_profile_id", "state", "created_at"],
        schema="parent",
    )
    op.create_index(
        "ix_parent_profile_share_teacher_state",
        "profile_share_grants",
        ["teacher_subject", "state", "expires_at"],
        schema="parent",
    )
    op.create_index(
        "uq_parent_profile_share_active_managed_ref",
        "profile_share_grants",
        ["organization_id", "managed_profile_ref"],
        unique=True,
        schema="parent",
        postgresql_where=sa.text("state = 'ACTIVE' AND managed_profile_ref IS NOT NULL"),
    )

    op.create_table(
        "delivery_occurrences",
        sa.Column("occurrence_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("lesson_id", sa.String(36), nullable=False),
        sa.Column("version_id", sa.String(36), nullable=False),
        sa.Column("managed_profile_ref", sa.String(128), nullable=False),
        sa.Column("teacher_subject", sa.String(256), nullable=False),
        sa.Column("lesson_title_snapshot", sa.String(160), nullable=False),
        sa.Column("lesson_topic_snapshot", sa.String(120), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lesson.library_items.lesson_id"],
            ondelete="RESTRICT", name="fk_lesson_delivery_item",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"], ["lesson.library_versions.version_id"],
            ondelete="RESTRICT", name="fk_lesson_delivery_version",
        ),
        sa.UniqueConstraint(
            "occurrence_id", "organization_id", name="uq_lesson_delivery_occurrence_org"
        ),
        sa.UniqueConstraint(
            "organization_id", "teacher_subject", "idempotency_key_sha256",
            name="uq_lesson_delivery_idempotency",
        ),
        sa.CheckConstraint("length(managed_profile_ref) > 0", name="ck_lesson_delivery_profile_ref"),
        sa.CheckConstraint("length(idempotency_key_sha256) = 64 AND length(request_sha256) = 64", name="ck_lesson_delivery_hashes"),
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_delivery_profile_time",
        "delivery_occurrences",
        ["managed_profile_ref", "delivered_at"],
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_delivery_org_time",
        "delivery_occurrences",
        ["organization_id", "delivered_at"],
        schema="lesson",
    )

    op.create_table(
        "delivery_feedback",
        sa.Column("feedback_id", sa.String(36), primary_key=True),
        sa.Column("occurrence_id", sa.String(36), nullable=False),
        sa.Column("parent_profile_id", sa.String(36), nullable=False),
        sa.Column("parent_subject", sa.String(256), nullable=False),
        sa.Column("feedback_text", sa.String(1200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["occurrence_id"], ["lesson.delivery_occurrences.occurrence_id"],
            ondelete="RESTRICT", name="fk_lesson_feedback_occurrence",
        ),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"], ["parent.child_profiles.parent_profile_id"],
            ondelete="RESTRICT", name="fk_lesson_feedback_parent_profile",
        ),
        sa.UniqueConstraint(
            "occurrence_id", "parent_profile_id", name="uq_lesson_feedback_occurrence_profile"
        ),
        sa.CheckConstraint("length(trim(feedback_text)) BETWEEN 1 AND 1200", name="ck_lesson_feedback_text"),
        schema="lesson",
    )
    op.create_table(
        "feedback_replies",
        sa.Column("reply_id", sa.String(36), primary_key=True),
        sa.Column("feedback_id", sa.String(36), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("teacher_subject", sa.String(256), nullable=False),
        sa.Column("reply_text", sa.String(1200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["feedback_id"], ["lesson.delivery_feedback.feedback_id"],
            ondelete="RESTRICT", name="fk_lesson_feedback_reply_feedback",
        ),
        sa.CheckConstraint("length(trim(reply_text)) BETWEEN 1 AND 1200", name="ck_lesson_feedback_reply_text"),
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_feedback_reply_feedback_time",
        "feedback_replies",
        ["feedback_id", "created_at"],
        schema="lesson",
    )

    op.create_table(
        "inbox_items",
        sa.Column("notification_id", sa.String(36), primary_key=True),
        sa.Column("recipient_subject", sa.String(256), nullable=False),
        sa.Column("notice_kind", sa.String(48), nullable=False),
        sa.Column("safe_title", sa.String(160), nullable=False),
        sa.Column("resource_kind", sa.String(48)),
        sa.Column("resource_ref", sa.String(128)),
        sa.Column("dedupe_key", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("recipient_subject", "dedupe_key", name="uq_notification_inbox_dedupe"),
        sa.CheckConstraint("length(trim(safe_title)) BETWEEN 1 AND 160", name="ck_notification_title"),
        sa.CheckConstraint(
            "notice_kind IN ('PROFILE_SHARE_INVITATION','PROFILE_SHARE_ACCEPTED','LESSON_FEEDBACK','LESSON_REPLY')",
            name="ck_notification_kind",
        ),
        schema="notifications",
    )
    op.create_index(
        "ix_notification_inbox_recipient_time",
        "inbox_items",
        ["recipient_subject", "created_at"],
        schema="notifications",
    )

    op.create_table(
        "video_quota_grants",
        sa.Column("grant_id", sa.String(36), primary_key=True),
        sa.Column("owner_scope_kind", sa.String(24), nullable=False),
        sa.Column("owner_scope_ref", sa.String(128), nullable=False),
        sa.Column("grant_kind", sa.String(24), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("owner_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')", name="ck_billing_quota_owner_kind"),
        sa.CheckConstraint("grant_kind IN ('INCLUDED','TOP_UP','ADJUSTMENT')", name="ck_billing_quota_grant_kind"),
        sa.CheckConstraint("quantity > 0", name="ck_billing_quota_grant_quantity"),
        sa.CheckConstraint("period_end > period_start", name="ck_billing_quota_period"),
        schema="billing",
    )
    op.create_table(
        "video_quota_usage",
        sa.Column("usage_id", sa.String(36), primary_key=True),
        sa.Column("owner_scope_kind", sa.String(24), nullable=False),
        sa.Column("owner_scope_ref", sa.String(128), nullable=False),
        sa.Column("accepted_request_ref", sa.String(128), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("owner_scope_kind", "owner_scope_ref", "accepted_request_ref", name="uq_billing_quota_usage_request"),
        sa.CheckConstraint("owner_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')", name="ck_billing_usage_owner_kind"),
        schema="billing",
    )


def downgrade() -> None:
    op.drop_table("video_quota_usage", schema="billing")
    op.drop_table("video_quota_grants", schema="billing")
    op.drop_index("ix_notification_inbox_recipient_time", table_name="inbox_items", schema="notifications")
    op.drop_table("inbox_items", schema="notifications")
    op.drop_index("ix_lesson_feedback_reply_feedback_time", table_name="feedback_replies", schema="lesson")
    op.drop_table("feedback_replies", schema="lesson")
    op.drop_table("delivery_feedback", schema="lesson")
    op.drop_index("ix_lesson_delivery_org_time", table_name="delivery_occurrences", schema="lesson")
    op.drop_index("ix_lesson_delivery_profile_time", table_name="delivery_occurrences", schema="lesson")
    op.drop_table("delivery_occurrences", schema="lesson")
    op.drop_index("ix_parent_profile_share_teacher_state", table_name="profile_share_grants", schema="parent")
    op.drop_index("ix_parent_profile_share_owner_state", table_name="profile_share_grants", schema="parent")
    op.drop_index("uq_parent_profile_share_active_managed_ref", table_name="profile_share_grants", schema="parent")
    op.drop_table("profile_share_grants", schema="parent")
    op.execute("DROP SCHEMA IF EXISTS billing")
    op.execute("DROP SCHEMA IF EXISTS notifications")
