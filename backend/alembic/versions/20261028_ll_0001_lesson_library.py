"""Add the first durable Lesson Library, audience and resumable-upload records."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261028_ll_0001"
down_revision = None
branch_labels = ("lesson_library",)
depends_on = "20261024_0005"


def upgrade() -> None:
    op.execute(sa.schema.CreateSchema("lesson", if_not_exists=True))

    op.create_table(
        "be1_parent_groups",
        sa.Column("parent_group_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("state", sa.String(24), server_default="active", nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["be1_organizations.organization_id"],
            name="fk_be1_parent_group_organization", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("organization_id", "display_name", name="uq_be1_parent_group_name"),
        sa.CheckConstraint("state IN ('active', 'archived')", name="ck_be1_parent_group_state"),
    )
    op.create_table(
        "be1_parent_group_members",
        sa.Column("membership_id", sa.String(36), primary_key=True),
        sa.Column("parent_group_id", sa.String(36), nullable=False),
        sa.Column("parent_principal_ref", sa.String(256), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("invited_by", sa.String(256), nullable=False),
        sa.Column("invited_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_group_id"], ["be1_parent_groups.parent_group_id"],
            name="fk_be1_parent_group_member_group", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("parent_group_id", "parent_principal_ref", name="uq_be1_parent_group_member"),
        sa.CheckConstraint(
            "state IN ('invited', 'active', 'revoked', 'expired')",
            name="ck_be1_parent_group_member_state",
        ),
        sa.CheckConstraint("revision > 0", name="ck_be1_parent_group_member_revision"),
    )
    op.create_index(
        "ix_be1_parent_member_invitations", "be1_parent_group_members",
        ["parent_principal_ref", "state", "invited_at"],
    )

    op.create_table(
        "core_upload_sessions",
        sa.Column("upload_session_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("owner_principal_ref", sa.String(256), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("target_ref", sa.String(256), nullable=False),
        sa.Column("safe_file_name", sa.String(255), nullable=False),
        sa.Column("expected_media_type", sa.String(128), nullable=False),
        sa.Column("expected_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("expected_sha256", sa.String(64), nullable=False),
        sa.Column("chunk_size_bytes", sa.Integer(), nullable=False),
        sa.Column("expected_parts", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("final_asset_ref", sa.String(256)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("aborted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "purpose IN ('PROFILE_IMAGE', 'RUN_ARTWORK', 'RUN_AUDIO', 'LESSON_SOURCE')",
            name="ck_core_upload_purpose",
        ),
        sa.CheckConstraint("expected_size_bytes BETWEEN 1 AND 25000000", name="ck_core_upload_size"),
        sa.CheckConstraint("chunk_size_bytes = 4194304", name="ck_core_upload_chunk_size"),
        sa.CheckConstraint("expected_parts BETWEEN 1 AND 7", name="ck_core_upload_parts_count"),
        sa.CheckConstraint(
            "state IN ('OPEN', 'COMPLETED', 'ABORTED', 'EXPIRED', 'FAILED')",
            name="ck_core_upload_state",
        ),
        sa.CheckConstraint("length(expected_sha256) = 64", name="ck_core_upload_hash"),
    )
    op.create_index(
        "ix_core_upload_owner_state", "core_upload_sessions",
        ["owner_principal_ref", "state", "expires_at"],
    )
    op.create_table(
        "core_upload_parts",
        sa.Column("upload_session_id", sa.String(36), primary_key=True),
        sa.Column("part_number", sa.Integer(), primary_key=True),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_object_ref", sa.String(512), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["upload_session_id"], ["core_upload_sessions.upload_session_id"],
            name="fk_core_upload_part_session", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("part_number > 0", name="ck_core_upload_part_number"),
        sa.CheckConstraint("byte_size BETWEEN 1 AND 4194304", name="ck_core_upload_part_size"),
        sa.CheckConstraint("length(sha256) = 64", name="ck_core_upload_part_hash"),
    )

    op.create_table(
        "library_items",
        sa.Column("lesson_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("owner_kind", sa.String(24), server_default="ORGANIZATION", nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("state", sa.String(24), server_default="ACTIVE", nullable=False),
        sa.Column("visibility", sa.String(24), nullable=False),
        sa.Column("internal_visibility", sa.String(24), nullable=False),
        sa.Column("moderation_state", sa.String(24), server_default="VISIBLE", nullable=False),
        sa.Column("current_version_id", sa.String(36)),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("moderation_reason", sa.String(1000)),
        sa.Column("moderated_by", sa.String(256)),
        sa.Column("moderated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("owner_kind = 'ORGANIZATION'", name="ck_lesson_owner_kind"),
        sa.CheckConstraint("state IN ('ACTIVE', 'ARCHIVED')", name="ck_lesson_item_state"),
        sa.CheckConstraint(
            "visibility IN ('PRIVATE', 'SCHOOL', 'SELECTED_AUDIENCE', 'PUBLIC')",
            name="ck_lesson_visibility",
        ),
        sa.CheckConstraint("internal_visibility IN ('PRIVATE', 'SCHOOL')", name="ck_lesson_internal_visibility"),
        sa.CheckConstraint("moderation_state IN ('VISIBLE', 'HIDDEN')", name="ck_lesson_moderation_state"),
        sa.CheckConstraint("revision > 0", name="ck_lesson_item_revision"),
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_items_org_state", "library_items", ["organization_id", "state", "updated_at"],
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_items_author", "library_items", ["organization_id", "created_by", "updated_at"],
        schema="lesson",
    )
    op.create_table(
        "library_versions",
        sa.Column("version_id", sa.String(36), primary_key=True),
        sa.Column("lesson_id", sa.String(36), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("structured_content_hash", sa.String(64), nullable=False),
        sa.Column("review_state", sa.String(32), server_default="DRAFT", nullable=False),
        sa.Column("source_document_revision_id", sa.String(36)),
        sa.Column("authored_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lesson.library_items.lesson_id"],
            name="fk_lesson_version_item", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("lesson_id", "version_no", name="uq_lesson_version_number"),
        sa.CheckConstraint("version_no > 0", name="ck_lesson_version_number"),
        sa.CheckConstraint("length(structured_content_hash) = 64", name="ck_lesson_version_hash"),
        sa.CheckConstraint(
            "review_state IN ('DRAFT', 'PENDING_REVIEW', 'CHANGES_REQUESTED', 'APPROVED')",
            name="ck_lesson_version_review_state",
        ),
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_versions_item", "library_versions", ["lesson_id", "version_no"], schema="lesson"
    )
    op.create_table(
        "version_activities",
        sa.Column("activity_id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.String(36), nullable=False),
        sa.Column("activity_order", sa.Integer(), nullable=False),
        sa.Column("activity_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"], ["lesson.library_versions.version_id"],
            name="fk_lesson_activity_version", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("version_id", "activity_order", name="uq_lesson_activity_order"),
        sa.CheckConstraint("activity_order > 0", name="ck_lesson_activity_order"),
        schema="lesson",
    )
    op.create_table(
        "access_grants",
        sa.Column("access_grant_id", sa.String(36), primary_key=True),
        sa.Column("lesson_id", sa.String(36), nullable=False),
        sa.Column("version_id", sa.String(36), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("audience_kind", sa.String(24), nullable=False),
        sa.Column("audience_ref", sa.String(256)),
        sa.Column("capability", sa.String(24), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("granted_by", sa.String(256), nullable=False),
        sa.Column("approved_by", sa.String(256)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("decision_reason", sa.String(1000)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lesson.library_items.lesson_id"],
            name="fk_lesson_grant_item", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"], ["lesson.library_versions.version_id"],
            name="fk_lesson_grant_version", ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "audience_kind IN ('PUBLIC', 'ORGANIZATION', 'PRINCIPAL', 'PARENT_GROUP')",
            name="ck_lesson_grant_audience",
        ),
        sa.CheckConstraint("capability IN ('VIEW', 'DOWNLOAD', 'REUSE')", name="ck_lesson_grant_capability"),
        sa.CheckConstraint(
            "state IN ('PENDING_REVIEW', 'INVITED', 'ACTIVE', 'DECLINED', 'EXPIRED', 'REVOKED', 'CHANGES_REQUESTED')",
            name="ck_lesson_grant_state",
        ),
        sa.CheckConstraint(
            "(audience_kind = 'PUBLIC' AND audience_ref IS NULL) OR "
            "(audience_kind <> 'PUBLIC' AND audience_ref IS NOT NULL)",
            name="ck_lesson_grant_audience_ref",
        ),
        sa.CheckConstraint("revision > 0", name="ck_lesson_grant_revision"),
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_grants_org_state", "access_grants", ["organization_id", "state", "created_at"],
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_grants_audience", "access_grants", ["audience_kind", "audience_ref", "state", "expires_at"],
        schema="lesson",
    )
    op.create_table(
        "library_source_documents",
        sa.Column("source_document_id", sa.String(36), primary_key=True),
        sa.Column("lesson_id", sa.String(36), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("uploaded_by", sa.String(256), nullable=False),
        sa.Column("upload_session_id", sa.String(36), nullable=False, unique=True),
        sa.Column("asset_ref", sa.String(256), nullable=False),
        sa.Column("asset_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("safe_file_name", sa.String(255), nullable=False),
        sa.Column("file_extension", sa.String(16), nullable=False),
        sa.Column("declared_media_type", sa.String(128), nullable=False),
        sa.Column("detected_media_type", sa.String(128), nullable=False),
        sa.Column("byte_length", sa.BigInteger(), nullable=False),
        sa.Column("asset_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("page_or_slide_count", sa.Integer()),
        sa.Column("page_coverage", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("parser_name", sa.String(64)),
        sa.Column("parser_version", sa.String(64)),
        sa.Column("scanner_name", sa.String(64), nullable=False),
        sa.Column("scanner_version", sa.String(128), nullable=False),
        sa.Column("scan_verdict", sa.String(16), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_revision_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lesson.library_items.lesson_id"],
            name="fk_lesson_source_item", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("byte_length BETWEEN 1 AND 25000000", name="ck_lesson_source_size"),
        sa.CheckConstraint("length(asset_sha256) = 64", name="ck_lesson_source_hash"),
        sa.CheckConstraint(
            "state IN ('READY_FOR_REVIEW', 'FAILED', 'ARCHIVED')", name="ck_lesson_source_state"
        ),
        sa.CheckConstraint("scan_verdict = 'CLEAN'", name="ck_lesson_source_scan_clean"),
        schema="lesson",
    )
    op.create_index(
        "ix_lesson_source_item", "library_source_documents", ["lesson_id", "created_at"], schema="lesson"
    )
    op.create_table(
        "library_document_revisions",
        sa.Column("revision_id", sa.String(36), primary_key=True),
        sa.Column("source_document_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("extracted_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("page_coverage", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("parser_name", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(64), nullable=False),
        sa.Column("review_state", sa.String(24), server_default="NEEDS_REVIEW", nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["lesson.library_source_documents.source_document_id"],
            name="fk_lesson_document_revision_source", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("source_document_id", "revision_no", name="uq_lesson_document_revision_no"),
        sa.CheckConstraint("revision_no > 0", name="ck_lesson_document_revision_number"),
        sa.CheckConstraint("length(source_sha256) = 64", name="ck_lesson_document_revision_hash"),
        sa.CheckConstraint("review_state IN ('NEEDS_REVIEW', 'CONFIRMED')", name="ck_lesson_document_review_state"),
        schema="lesson",
    )
    op.create_table(
        "command_receipts",
        sa.Column("organization_id", sa.String(128), primary_key=True),
        sa.Column("principal_ref", sa.String(256), primary_key=True),
        sa.Column("operation_scope", sa.String(256), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), primary_key=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(request_fingerprint) = 64", name="ck_lesson_receipt_fingerprint"),
        schema="lesson",
    )


def downgrade() -> None:
    op.drop_table("command_receipts", schema="lesson")
    op.drop_table("library_document_revisions", schema="lesson")
    op.drop_index("ix_lesson_source_item", table_name="library_source_documents", schema="lesson")
    op.drop_table("library_source_documents", schema="lesson")
    op.drop_index("ix_lesson_grants_audience", table_name="access_grants", schema="lesson")
    op.drop_index("ix_lesson_grants_org_state", table_name="access_grants", schema="lesson")
    op.drop_table("access_grants", schema="lesson")
    op.drop_table("version_activities", schema="lesson")
    op.drop_index("ix_lesson_versions_item", table_name="library_versions", schema="lesson")
    op.drop_table("library_versions", schema="lesson")
    op.drop_index("ix_lesson_items_author", table_name="library_items", schema="lesson")
    op.drop_index("ix_lesson_items_org_state", table_name="library_items", schema="lesson")
    op.drop_table("library_items", schema="lesson")
    op.drop_table("core_upload_parts")
    op.drop_index("ix_core_upload_owner_state", table_name="core_upload_sessions")
    op.drop_table("core_upload_sessions")
    op.drop_index("ix_be1_parent_member_invitations", table_name="be1_parent_group_members")
    op.drop_table("be1_parent_group_members")
    op.drop_table("be1_parent_groups")
    op.execute(sa.schema.DropSchema("lesson", if_exists=True))
