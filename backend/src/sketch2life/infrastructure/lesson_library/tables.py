"""PostgreSQL table ownership for Lesson Library and its new Core/BE1 records."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase

CORE_METADATA = CorePersistenceBase.metadata
LESSON_METADATA = sa.MetaData(schema="lesson")


PARENT_GROUPS = sa.Table(
    "be1_parent_groups",
    CORE_METADATA,
    sa.Column("parent_group_id", sa.String(36), primary_key=True),
    sa.Column(
        "organization_id",
        sa.String(128),
        sa.ForeignKey("be1_organizations.organization_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("display_name", sa.String(120), nullable=False),
    sa.Column("state", sa.String(24), nullable=False, server_default="active"),
    sa.Column("created_by", sa.String(256), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.UniqueConstraint("organization_id", "display_name", name="uq_be1_parent_group_name"),
    sa.CheckConstraint("state IN ('active', 'archived')", name="ck_be1_parent_group_state"),
)

PARENT_GROUP_MEMBERS = sa.Table(
    "be1_parent_group_members",
    CORE_METADATA,
    sa.Column("membership_id", sa.String(36), primary_key=True),
    sa.Column(
        "parent_group_id",
        sa.String(36),
        sa.ForeignKey("be1_parent_groups.parent_group_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("parent_principal_ref", sa.String(256), nullable=False),
    sa.Column("state", sa.String(24), nullable=False),
    sa.Column("invited_by", sa.String(256), nullable=False),
    sa.Column("invited_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("accepted_at", sa.DateTime(timezone=True)),
    sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
    sa.UniqueConstraint("parent_group_id", "parent_principal_ref", name="uq_be1_parent_group_member"),
    sa.CheckConstraint(
        "state IN ('invited', 'active', 'revoked', 'expired')",
        name="ck_be1_parent_group_member_state",
    ),
    sa.CheckConstraint("revision > 0", name="ck_be1_parent_group_member_revision"),
    sa.Index("ix_be1_parent_member_invitations", "parent_principal_ref", "state", "invited_at"),
)

UPLOAD_SESSIONS = sa.Table(
    "core_upload_sessions",
    CORE_METADATA,
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
    sa.Index("ix_core_upload_owner_state", "owner_principal_ref", "state", "expires_at"),
)

UPLOAD_PARTS = sa.Table(
    "core_upload_parts",
    CORE_METADATA,
    sa.Column(
        "upload_session_id",
        sa.String(36),
        sa.ForeignKey("core_upload_sessions.upload_session_id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    sa.Column("part_number", sa.Integer(), primary_key=True),
    sa.Column("byte_size", sa.Integer(), nullable=False),
    sa.Column("sha256", sa.String(64), nullable=False),
    sa.Column("storage_object_ref", sa.String(512), nullable=False),
    sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("part_number > 0", name="ck_core_upload_part_number"),
    sa.CheckConstraint("byte_size BETWEEN 1 AND 4194304", name="ck_core_upload_part_size"),
    sa.CheckConstraint("length(sha256) = 64", name="ck_core_upload_part_hash"),
)

LIBRARY_ITEMS = sa.Table(
    "library_items",
    LESSON_METADATA,
    sa.Column("lesson_id", sa.String(36), primary_key=True),
    sa.Column("organization_id", sa.String(128), nullable=False),
    sa.Column("owner_kind", sa.String(24), nullable=False, server_default="ORGANIZATION"),
    sa.Column("created_by", sa.String(256), nullable=False),
    sa.Column("state", sa.String(24), nullable=False, server_default="ACTIVE"),
    sa.Column("visibility", sa.String(24), nullable=False),
    sa.Column("internal_visibility", sa.String(24), nullable=False),
    sa.Column("moderation_state", sa.String(24), nullable=False, server_default="VISIBLE"),
    sa.Column("current_version_id", sa.String(36)),
    sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
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
    sa.Index("ix_lesson_items_org_state", "organization_id", "state", "updated_at"),
    sa.Index("ix_lesson_items_author", "organization_id", "created_by", "updated_at"),
)

LIBRARY_VERSIONS = sa.Table(
    "library_versions",
    LESSON_METADATA,
    sa.Column("version_id", sa.String(36), primary_key=True),
    sa.Column(
        "lesson_id", sa.String(36), sa.ForeignKey("lesson.library_items.lesson_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("version_no", sa.Integer(), nullable=False),
    sa.Column("content_json", JSONB, nullable=False),
    sa.Column("structured_content_hash", sa.String(64), nullable=False),
    sa.Column("review_state", sa.String(32), nullable=False, server_default="DRAFT"),
    sa.Column("source_document_revision_id", sa.String(36)),
    sa.Column("authored_by", sa.String(256), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("approved_at", sa.DateTime(timezone=True)),
    sa.UniqueConstraint("lesson_id", "version_no", name="uq_lesson_version_number"),
    sa.CheckConstraint("version_no > 0", name="ck_lesson_version_number"),
    sa.CheckConstraint("length(structured_content_hash) = 64", name="ck_lesson_version_hash"),
    sa.CheckConstraint(
        "review_state IN ('DRAFT', 'PENDING_REVIEW', 'CHANGES_REQUESTED', 'APPROVED')",
        name="ck_lesson_version_review_state",
    ),
    sa.Index("ix_lesson_versions_item", "lesson_id", "version_no"),
)

VERSION_ACTIVITIES = sa.Table(
    "version_activities",
    LESSON_METADATA,
    sa.Column("activity_id", sa.String(36), primary_key=True),
    sa.Column(
        "version_id", sa.String(36), sa.ForeignKey("lesson.library_versions.version_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("activity_order", sa.Integer(), nullable=False),
    sa.Column("activity_json", JSONB, nullable=False),
    sa.UniqueConstraint("version_id", "activity_order", name="uq_lesson_activity_order"),
    sa.CheckConstraint("activity_order > 0", name="ck_lesson_activity_order"),
)

ACCESS_GRANTS = sa.Table(
    "access_grants",
    LESSON_METADATA,
    sa.Column("access_grant_id", sa.String(36), primary_key=True),
    sa.Column(
        "lesson_id", sa.String(36), sa.ForeignKey("lesson.library_items.lesson_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column(
        "version_id", sa.String(36), sa.ForeignKey("lesson.library_versions.version_id", ondelete="RESTRICT"),
        nullable=False,
    ),
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
    sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
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
    sa.Index("ix_lesson_grants_org_state", "organization_id", "state", "created_at"),
    sa.Index("ix_lesson_grants_audience", "audience_kind", "audience_ref", "state", "expires_at"),
)

SOURCE_DOCUMENTS = sa.Table(
    "library_source_documents",
    LESSON_METADATA,
    sa.Column("source_document_id", sa.String(36), primary_key=True),
    sa.Column(
        "lesson_id", sa.String(36), sa.ForeignKey("lesson.library_items.lesson_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("organization_id", sa.String(128), nullable=False),
    sa.Column("uploaded_by", sa.String(256), nullable=False),
    sa.Column("upload_session_id", sa.String(36), nullable=False, unique=True),
    sa.Column("asset_ref", sa.String(256), nullable=False),
    sa.Column("asset_version", sa.Integer(), nullable=False, server_default="1"),
    sa.Column("safe_file_name", sa.String(255), nullable=False),
    sa.Column("file_extension", sa.String(16), nullable=False),
    sa.Column("declared_media_type", sa.String(128), nullable=False),
    sa.Column("detected_media_type", sa.String(128), nullable=False),
    sa.Column("byte_length", sa.BigInteger(), nullable=False),
    sa.Column("asset_sha256", sa.String(64), nullable=False),
    sa.Column("state", sa.String(32), nullable=False),
    sa.Column("page_or_slide_count", sa.Integer()),
    sa.Column("page_coverage", JSONB, nullable=False, server_default="[]"),
    sa.Column("warnings", JSONB, nullable=False, server_default="[]"),
    sa.Column("parser_name", sa.String(64)),
    sa.Column("parser_version", sa.String(64)),
    sa.Column("scanner_name", sa.String(64), nullable=False),
    sa.Column("scanner_version", sa.String(128), nullable=False),
    sa.Column("scan_verdict", sa.String(16), nullable=False),
    sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("current_revision_id", sa.String(36)),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("byte_length BETWEEN 1 AND 25000000", name="ck_lesson_source_size"),
    sa.CheckConstraint("length(asset_sha256) = 64", name="ck_lesson_source_hash"),
    sa.CheckConstraint(
        "state IN ('READY_FOR_REVIEW', 'FAILED', 'ARCHIVED')", name="ck_lesson_source_state"
    ),
    sa.CheckConstraint("scan_verdict = 'CLEAN'", name="ck_lesson_source_scan_clean"),
    sa.Index("ix_lesson_source_item", "lesson_id", "created_at"),
)

DOCUMENT_REVISIONS = sa.Table(
    "library_document_revisions",
    LESSON_METADATA,
    sa.Column("revision_id", sa.String(36), primary_key=True),
    sa.Column(
        "source_document_id", sa.String(36),
        sa.ForeignKey("lesson.library_source_documents.source_document_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("revision_no", sa.Integer(), nullable=False),
    sa.Column("source_sha256", sa.String(64), nullable=False),
    sa.Column("extracted_fields", JSONB, nullable=False),
    sa.Column("warnings", JSONB, nullable=False, server_default="[]"),
    sa.Column("page_coverage", JSONB, nullable=False, server_default="[]"),
    sa.Column("parser_name", sa.String(64), nullable=False),
    sa.Column("parser_version", sa.String(64), nullable=False),
    sa.Column("review_state", sa.String(24), nullable=False, server_default="NEEDS_REVIEW"),
    sa.Column("created_by", sa.String(256), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.UniqueConstraint("source_document_id", "revision_no", name="uq_lesson_document_revision_no"),
    sa.CheckConstraint("revision_no > 0", name="ck_lesson_document_revision_number"),
    sa.CheckConstraint("length(source_sha256) = 64", name="ck_lesson_document_revision_hash"),
    sa.CheckConstraint("review_state IN ('NEEDS_REVIEW', 'CONFIRMED')", name="ck_lesson_document_review_state"),
)

COMMAND_RECEIPTS = sa.Table(
    "command_receipts",
    LESSON_METADATA,
    sa.Column("organization_id", sa.String(128), primary_key=True),
    sa.Column("principal_ref", sa.String(256), primary_key=True),
    sa.Column("operation_scope", sa.String(256), primary_key=True),
    sa.Column("idempotency_key", sa.String(128), primary_key=True),
    sa.Column("request_fingerprint", sa.String(64), nullable=False),
    sa.Column("response_json", JSONB, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("length(request_fingerprint) = 64", name="ck_lesson_receipt_fingerprint"),
)


__all__ = [
    "ACCESS_GRANTS",
    "COMMAND_RECEIPTS",
    "CORE_METADATA",
    "DOCUMENT_REVISIONS",
    "LESSON_METADATA",
    "LIBRARY_ITEMS",
    "LIBRARY_VERSIONS",
    "PARENT_GROUP_MEMBERS",
    "PARENT_GROUPS",
    "SOURCE_DOCUMENTS",
    "UPLOAD_PARTS",
    "UPLOAD_SESSIONS",
    "VERSION_ACTIVITIES",
]
