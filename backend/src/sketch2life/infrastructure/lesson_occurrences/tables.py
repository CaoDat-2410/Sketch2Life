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

# T-4b1 (migration ``20261120_sel_0001``): one immutable evidence row per Teacher child-selection
# outcome. Metadata only (SRS l.354, BR-34): no name, no age, no seed and no drawn index.
CHILD_SELECTIONS = sa.Table(
    "occurrence_child_selections",
    OCCURRENCE_METADATA,
    sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column("selection_id", sa.String(36), primary_key=True),
    sa.Column("occurrence_id", sa.String(36), nullable=False),
    sa.Column("plan_revision_id", sa.String(36), nullable=False),
    sa.Column("organization_ref", sa.String(128), nullable=False),
    sa.Column("class_ref", sa.String(128), nullable=False),
    sa.Column("teacher_ref", sa.String(36), nullable=False),
    sa.Column("kind", sa.String(8), nullable=False),
    sa.Column("draw_no", sa.SmallInteger()),
    sa.Column("policy_version", sa.String(48), nullable=False),
    sa.Column("eligibility_basis", sa.String(16), nullable=False),
    sa.Column("candidate_count", sa.SmallInteger(), nullable=False),
    sa.Column("candidate_set_hash", sa.String(64), nullable=False),
    sa.Column("selected_child_ref", sa.String(128)),
    sa.Column("class_revision", sa.Integer(), nullable=False),
    sa.Column("occurrence_revision", sa.Integer(), nullable=False),
    sa.Column("state", sa.String(16), nullable=False),
    sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
    sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True)),
    sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    sa.Column("confirmed_by", sa.String(36)),
    sa.Column("confirmation_expires_at", sa.DateTime(timezone=True)),
    sa.Column("consumed_at", sa.DateTime(timezone=True)),
    sa.Column("consumed_run_ref", sa.String(128)),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
)

PRESENTATIONS = sa.Table(
    "presentations",
    OCCURRENCE_METADATA,
    sa.Column("presentation_id", sa.String(36), primary_key=True),
    sa.Column("occurrence_id", sa.String(36), nullable=False),
    sa.Column("organization_ref", sa.String(128), nullable=False),
    sa.Column("head_revision_no", sa.Integer(), nullable=False),
    sa.Column("ready_revision_no", sa.Integer()),
    sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
    sa.Column("created_by", sa.String(36), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.CheckConstraint("head_revision_no > 0", name="ck_pres_head"),
    sa.CheckConstraint(
        "ready_revision_no IS NULL OR ready_revision_no BETWEEN 1 AND head_revision_no",
        name="ck_pres_ready",
    ),
    sa.CheckConstraint("revision > 0", name="ck_pres_revision"),
    sa.ForeignKeyConstraint(
        ["occurrence_id"],
        ["lesson.occurrences.occurrence_id"],
        ondelete="RESTRICT",
        name="fk_pres_occurrence",
    ),
    sa.UniqueConstraint("occurrence_id", name="uq_pres_occurrence"),
)

PRESENTATION_REVISIONS = sa.Table(
    "presentation_revisions",
    OCCURRENCE_METADATA,
    sa.Column("presentation_revision_id", sa.String(36), primary_key=True),
    sa.Column("presentation_id", sa.String(36), nullable=False),
    sa.Column("revision_no", sa.Integer(), nullable=False),
    sa.Column("base_revision_no", sa.Integer()),
    sa.Column("plan_revision_id", sa.String(36), nullable=False),
    sa.Column("plan_content_hash", sa.String(64), nullable=False),
    sa.Column("content_hash", sa.String(64), nullable=False),
    sa.Column("slides", JSONB, nullable=False),
    sa.Column("state", sa.String(16), server_default="DRAFT", nullable=False),
    sa.Column("created_by", sa.String(36), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("readied_by", sa.String(36)),
    sa.Column("readied_at", sa.DateTime(timezone=True)),
    sa.Column("superseded_at", sa.DateTime(timezone=True)),
    sa.CheckConstraint("revision_no > 0", name="ck_presrev_number"),
    sa.CheckConstraint(
        "(revision_no = 1 AND base_revision_no IS NULL) OR base_revision_no = revision_no - 1",
        name="ck_presrev_base",
    ),
    sa.CheckConstraint("plan_content_hash ~ '^[0-9a-f]{64}$'", name="ck_presrev_plan_hash"),
    sa.CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="ck_presrev_content_hash"),
    sa.CheckConstraint(
        "CASE WHEN jsonb_typeof(slides) = 'array' THEN jsonb_array_length(slides) "
        "BETWEEN 1 AND 100 AND octet_length(slides::text) <= 1048576 ELSE false END",
        name="ck_presrev_slides",
    ),
    sa.CheckConstraint("state IN ('DRAFT', 'READY', 'SUPERSEDED')", name="ck_presrev_state"),
    sa.CheckConstraint(
        "(state = 'DRAFT' AND readied_by IS NULL AND readied_at IS NULL "
        "AND superseded_at IS NULL) OR "
        "(state = 'READY' AND readied_by IS NOT NULL AND readied_at IS NOT NULL "
        "AND superseded_at IS NULL) OR "
        "(state = 'SUPERSEDED' AND readied_by IS NOT NULL AND readied_at IS NOT NULL "
        "AND superseded_at IS NOT NULL)",
        name="ck_presrev_ready_fields",
    ),
    sa.ForeignKeyConstraint(
        ["presentation_id"],
        ["lesson.presentations.presentation_id"],
        ondelete="RESTRICT",
        name="fk_presrev_presentation",
    ),
    sa.ForeignKeyConstraint(
        ["plan_revision_id"],
        ["lesson.plan_revisions.plan_revision_id"],
        ondelete="RESTRICT",
        name="fk_presrev_plan_revision",
    ),
    sa.UniqueConstraint("presentation_id", "revision_no", name="uq_presrev_number"),
)
sa.Index(
    "uq_presrev_one_ready",
    PRESENTATION_REVISIONS.c.presentation_id,
    unique=True,
    postgresql_where=sa.text("state = 'READY'"),
)

PRESENTATION_SVG_DRAFTS = sa.Table(
    "presentation_svg_drafts",
    OCCURRENCE_METADATA,
    sa.Column("svg_draft_id", sa.String(36), primary_key=True),
    sa.Column("presentation_id", sa.String(36), nullable=False),
    sa.Column("state", sa.String(16), server_default="PENDING_REVIEW", nullable=False),
    sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
    sa.Column("input_hash", sa.String(64), nullable=False),
    sa.Column("source_sha256", sa.String(64), nullable=False),
    sa.Column("canonical_sha256", sa.String(64), nullable=False),
    sa.Column("document", JSONB, nullable=False),
    sa.Column("sanitizer_version", sa.String(64), nullable=False),
    sa.Column("generator_name", sa.String(64), nullable=False),
    sa.Column("generator_version", sa.String(128), nullable=False),
    sa.Column("license_id", sa.String(120), nullable=False),
    sa.Column("created_by", sa.String(36), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("decided_by", sa.String(36)),
    sa.Column("decided_at", sa.DateTime(timezone=True)),
    sa.CheckConstraint(
        "state IN ('PENDING_REVIEW', 'ACCEPTED', 'DISCARDED')",
        name="ck_pres_svg_state",
    ),
    sa.CheckConstraint("revision > 0", name="ck_pres_svg_revision"),
    sa.CheckConstraint("input_hash ~ '^[0-9a-f]{64}$'", name="ck_pres_svg_input_hash"),
    sa.CheckConstraint("source_sha256 ~ '^[0-9a-f]{64}$'", name="ck_pres_svg_source_hash"),
    sa.CheckConstraint("canonical_sha256 ~ '^[0-9a-f]{64}$'", name="ck_pres_svg_canonical_hash"),
    sa.CheckConstraint(
        "jsonb_typeof(document) = 'object' AND octet_length(document::text) <= 262144",
        name="ck_pres_svg_document",
    ),
    sa.CheckConstraint(
        "(state = 'PENDING_REVIEW' AND decided_by IS NULL AND decided_at IS NULL) OR "
        "(state IN ('ACCEPTED', 'DISCARDED') AND decided_by IS NOT NULL "
        "AND decided_at IS NOT NULL)",
        name="ck_pres_svg_decided_fields",
    ),
    sa.ForeignKeyConstraint(
        ["presentation_id"],
        ["lesson.presentations.presentation_id"],
        ondelete="RESTRICT",
        name="fk_pres_svg_presentation",
    ),
)
sa.Index(
    "ix_pres_svg_draft_created",
    PRESENTATION_SVG_DRAFTS.c.presentation_id,
    PRESENTATION_SVG_DRAFTS.c.created_at.desc(),
)

PRESENTATION_TABLES = (PRESENTATIONS, PRESENTATION_REVISIONS, PRESENTATION_SVG_DRAFTS)

DDL_A_TABLES = (OCCURRENCES, SOURCE_DOCUMENTS, DOCUMENT_REVISIONS, PLAN_REVISIONS, PLAN_ACTIVITIES)

__all__ = [
    "CHILD_SELECTIONS",
    "DDL_A_TABLES",
    "DOCUMENT_REVISIONS",
    "OCCURRENCES",
    "OCCURRENCE_METADATA",
    "PLAN_ACTIVITIES",
    "PLAN_REVISIONS",
    "PRESENTATION_REVISIONS",
    "PRESENTATION_SVG_DRAFTS",
    "PRESENTATION_TABLES",
    "PRESENTATIONS",
    "SOURCE_DOCUMENTS",
]
