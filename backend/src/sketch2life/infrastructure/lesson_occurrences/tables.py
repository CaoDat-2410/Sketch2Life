"""Core table definitions of DDL-A (migration ``20261119_oc_0001``), schema ``lesson``.

Columns only: the CHECKs, triggers and the composite pointer foreign key live in the migration and
are proven on PostgreSQL. A separate ``MetaData`` keeps the Lesson Library module untouched; a unit
test pins these columns to the migration. ``lesson.library_*`` stays in
``lesson_library/tables.py``.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

OCCURRENCE_METADATA = sa.MetaData(schema="lesson")

OCCURRENCES = sa.Table(
    "occurrences",
    OCCURRENCE_METADATA,
    sa.Column("occurrence_id", sa.String(36), primary_key=True),
    sa.Column("organization_ref", sa.String(128), nullable=False),
    sa.Column("class_ref", sa.String(128), nullable=False),
    sa.Column("responsible_teacher_ref", sa.String(36), nullable=False),
    sa.Column("created_by", sa.String(36), nullable=False),
    sa.Column("title", sa.String(200), nullable=False),
    sa.Column("scheduled_date", sa.Date()),
    sa.Column("state", sa.String(16), server_default="DRAFT", nullable=False),
    sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
    sa.Column("approved_plan_revision_id", sa.String(36)),
    sa.Column("source_lesson_id", sa.String(36)),
    sa.Column("source_lesson_version_id", sa.String(36)),
    sa.Column("source_lesson_version_no", sa.Integer()),
    sa.Column("source_lesson_version_hash", sa.String(64)),
    sa.Column("sample_slot_state", sa.String(16), server_default="AVAILABLE", nullable=False),
    sa.Column("successful_sample_run_ref", sa.String(128)),
    sa.Column("sample_claimed_at", sa.DateTime(timezone=True)),
    sa.Column("class_projection_confirmed_by_ref", sa.String(36)),
    sa.Column("class_projection_confirmed_at", sa.DateTime(timezone=True)),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
)

SOURCE_DOCUMENTS = sa.Table(
    "source_documents",
    OCCURRENCE_METADATA,
    sa.Column("source_document_id", sa.String(36), primary_key=True),
    sa.Column("occurrence_id", sa.String(36), nullable=False),
    sa.Column("asset_ref", sa.String(256), nullable=False),
    sa.Column("asset_version", sa.Integer(), server_default="1", nullable=False),
    sa.Column("upload_session_ref", sa.String(36), nullable=False),
    sa.Column("extraction_job_ref", sa.String(128), nullable=False),
    sa.Column("safe_file_name", sa.String(255), nullable=False),
    sa.Column("file_extension", sa.String(8), nullable=False),
    sa.Column("page_or_slide_count", sa.Integer()),
    sa.Column("document_state", sa.String(16), server_default="EXTRACTED", nullable=False),
    sa.Column("deleted_at", sa.DateTime(timezone=True)),
    sa.Column("uploaded_by", sa.String(36), nullable=False),
    sa.Column(
        "uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
)

DOCUMENT_REVISIONS = sa.Table(
    "document_revisions",
    OCCURRENCE_METADATA,
    sa.Column("document_revision_id", sa.String(36), primary_key=True),
    sa.Column("source_document_id", sa.String(36), nullable=False),
    sa.Column("revision_no", sa.Integer(), nullable=False),
    sa.Column("origin", sa.String(16), nullable=False),
    sa.Column("base_revision_no", sa.Integer()),
    sa.Column("extracted_text", sa.Text(), nullable=False),
    sa.Column("extracted_text_hash", sa.String(64), nullable=False),
    sa.Column("parser_name", sa.String(64)),
    sa.Column("parser_version", sa.String(64)),
    sa.Column("extraction_warnings", JSONB, server_default="[]", nullable=False),
    sa.Column("page_coverage", JSONB, server_default="[]", nullable=False),
    sa.Column("review_state", sa.String(16), server_default="NEEDS_REVIEW", nullable=False),
    sa.Column("reviewed_by", sa.String(36)),
    sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    sa.Column("created_by", sa.String(36), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
)

PLAN_REVISIONS = sa.Table(
    "plan_revisions",
    OCCURRENCE_METADATA,
    sa.Column("plan_revision_id", sa.String(36), primary_key=True),
    sa.Column("occurrence_id", sa.String(36), nullable=False),
    sa.Column("revision_no", sa.Integer(), nullable=False),
    sa.Column("source_document_revision_id", sa.String(36)),
    sa.Column("objectives", JSONB, nullable=False),
    sa.Column("teacher_direction", sa.Text(), nullable=False),
    sa.Column("safety_notes", sa.Text()),
    sa.Column("state", sa.String(16), server_default="DRAFT", nullable=False),
    sa.Column("content_hash", sa.String(64), nullable=False),
    sa.Column("source_lesson_id", sa.String(36)),
    sa.Column("source_lesson_version_id", sa.String(36)),
    sa.Column("source_lesson_version_no", sa.Integer()),
    sa.Column("source_lesson_version_hash", sa.String(64)),
    sa.Column("created_by", sa.String(36), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("approved_by", sa.String(36)),
    sa.Column("approved_at", sa.DateTime(timezone=True)),
    sa.Column("superseded_at", sa.DateTime(timezone=True)),
)

PLAN_ACTIVITIES = sa.Table(
    "plan_activities",
    OCCURRENCE_METADATA,
    sa.Column("plan_activity_id", sa.String(36), primary_key=True),
    sa.Column("plan_revision_id", sa.String(36), nullable=False),
    sa.Column("activity_order", sa.Integer(), nullable=False),
    sa.Column("activity_kind", sa.String(16), nullable=False),
    sa.Column("catalog_activity_ref", sa.String(256)),
    sa.Column("activity_version", sa.Integer()),
    sa.Column("custom_title", sa.String(160)),
    sa.Column("custom_description", sa.Text()),
    sa.Column("activity_snapshot", JSONB),
    sa.Column("activity_snapshot_hash", sa.String(64)),
    sa.Column("safety_checklist_version", sa.String(32)),
    sa.Column("checklist_result", JSONB),
    sa.Column("confirmed_by", sa.String(36)),
    sa.Column("confirmed_at", sa.DateTime(timezone=True)),
)

DDL_A_TABLES = (OCCURRENCES, SOURCE_DOCUMENTS, DOCUMENT_REVISIONS, PLAN_REVISIONS, PLAN_ACTIVITIES)

__all__ = [
    "DDL_A_TABLES",
    "DOCUMENT_REVISIONS",
    "OCCURRENCES",
    "OCCURRENCE_METADATA",
    "PLAN_ACTIVITIES",
    "PLAN_REVISIONS",
    "SOURCE_DOCUMENTS",
]
