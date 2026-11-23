"""DDL-A: lesson occurrence, source document, document revision, plan revision, plan activity.

FEAT-066 goal v3, T-3a (SRS l.775, l.1652-1660; DATA_TABLE_REGISTER l.352-356). One migration
creates the five ``lesson.*`` tables that T-3a, T-3b, T-3c and T-3d use; only T-3a ships it. It
extends the ``lesson_library`` branch (parent ``20261119_uf_0001``); it adds no branch label and
alters no existing table. The library tables ``lesson.library_*`` are untouched.

Design rules (plan T-3a Draft 1 section 4 and plan review R1, amendments A1-A3):

* ``organization_ref``, ``class_ref`` and the actor refs are opaque: no cross-owner foreign key.
  ``responsible_teacher_ref``, ``created_by`` and the other actor columns hold
  ``be1_adult_identities.account_id`` (``VARCHAR(36)``), never the identity-provider subject.
* A1: ``occurrences.approved_plan_revision_id`` is a composite foreign key
  ``(approved_plan_revision_id, occurrence_id) -> plan_revisions (plan_revision_id,
  occurrence_id)``, immediate (not deferred), so it cannot name another occurrence's plan. The
  trigger ``lesson.protect_occurrence`` also requires the target plan to be ``APPROVED`` whenever
  the pointer is set or changed.
* A2: ``lesson.protect_plan_revision`` refuses an INSERT that is not a ``DRAFT`` with empty
  approval columns, whose pin differs from the occurrence's pin, whose document revision belongs
  to another occurrence (or to a deleted document), whose number is not head + 1 or whose
  objectives are not strings of 1..1000 characters. The approval backstop of FR-T-09 (a plan with
  a Teacher-written activity without a safety checklist cannot be approved, SRS l.548) sits in
  the same function, together with the one-way ``DRAFT -> APPROVED -> SUPERSEDED`` machine.
* A3: value CHECKs, column lengths and defaults named in the review (activity kind rules,
  array shapes, SHA-256 hex, ``revision_no`` arithmetic, ``server_default now()``).
* Immutability by trigger, in the style of ``learning_content.protect_version``: DELETE is
  forbidden on every table; identity and content columns never change; the only legal updates
  are the ones the four tasks need (occurrence revision/state/plan pointer/sample slot and
  projection columns; ``document_state`` to ``DELETED``; the one-way review stamp of a document
  revision; the plan state machine; the checklist columns of a Teacher-written activity while the
  plan is a draft).
* ``uq_plan_one_approved`` allows one ``APPROVED`` plan per occurrence (SRS l.775).

Occurrence states are the SRS §6.1.1 (l.396) names ``DRAFT, DOCUMENT_REVIEW, PLAN_REVIEW,
APPROVED, SAMPLE_AVAILABLE, SAMPLE_USED, ARCHIVED``. T-3a creates ``DRAFT`` and T-3d sets
``APPROVED``; the others are allowed by the CHECK so later tasks need no change, and the pointer
is NULL exactly in the three pre-approval states. ``ARCHIVED`` (occurrence) and ``DELETED``
(source document) are reserved states: no v3 route sets
them (the SRS lists no such route); tests set them by SQL. ``occurrences.revision`` and
``revision_no`` are service-incremented; a trigger only enforces ``revision_no = head + 1`` for
the two revision tables and that ``occurrences.revision`` never decreases is a service rule.

The downgrade raises while any of the five tables holds a row, otherwise it drops the
foreign key, the five tables in reverse order and the trigger functions. Never run against the
shared or owner databases (``sketch2life_m2_s1a``) or ports 5432/5433; use a disposable database.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261119_oc_0001"
down_revision = "20261119_uf_0001"
branch_labels = None
depends_on = None

SCHEMA = "lesson"
TABLES = (
    "occurrences",
    "source_documents",
    "document_revisions",
    "plan_revisions",
    "plan_activities",
)
HEX64 = "'^[0-9a-f]{64}$'"
PIN_COLUMNS = (
    "source_lesson_id",
    "source_lesson_version_id",
    "source_lesson_version_no",
    "source_lesson_version_hash",
)

OCCURRENCE_FUNCTION = """
CREATE FUNCTION lesson.protect_occurrence() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_target_state text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'OCCURRENCE_DELETE_FORBIDDEN';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.state <> 'DRAFT' OR NEW.approved_plan_revision_id IS NOT NULL THEN
      RAISE EXCEPTION 'OCCURRENCE_INSERT_NOT_DRAFT';
    END IF;
    RETURN NEW;
  END IF;
  IF ROW(OLD.occurrence_id, OLD.organization_ref, OLD.class_ref, OLD.created_by, OLD.created_at,
         OLD.source_lesson_id, OLD.source_lesson_version_id, OLD.source_lesson_version_no,
         OLD.source_lesson_version_hash)
     IS DISTINCT FROM
     ROW(NEW.occurrence_id, NEW.organization_ref, NEW.class_ref, NEW.created_by, NEW.created_at,
         NEW.source_lesson_id, NEW.source_lesson_version_id, NEW.source_lesson_version_no,
         NEW.source_lesson_version_hash) THEN
    RAISE EXCEPTION 'OCCURRENCE_IMMUTABLE_COLUMN';
  END IF;
  IF NEW.approved_plan_revision_id IS NOT NULL
     AND NEW.approved_plan_revision_id IS DISTINCT FROM OLD.approved_plan_revision_id THEN
    SELECT state INTO v_target_state FROM lesson.plan_revisions
      WHERE plan_revision_id = NEW.approved_plan_revision_id
        AND occurrence_id = NEW.occurrence_id;
    IF v_target_state IS DISTINCT FROM 'APPROVED' THEN
      RAISE EXCEPTION 'OCCURRENCE_PLAN_NOT_APPROVED';
    END IF;
  END IF;
  RETURN NEW;
END; $$
"""

SOURCE_DOCUMENT_FUNCTION = """
CREATE FUNCTION lesson.protect_source_document() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'SOURCE_DOCUMENT_DELETE_FORBIDDEN';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.document_state <> 'EXTRACTED' THEN
      RAISE EXCEPTION 'SOURCE_DOCUMENT_INSERT_NOT_EXTRACTED';
    END IF;
    RETURN NEW;
  END IF;
  IF ROW(OLD.source_document_id, OLD.occurrence_id, OLD.asset_ref, OLD.asset_version,
         OLD.upload_session_ref, OLD.extraction_job_ref, OLD.safe_file_name,
         OLD.file_extension, OLD.page_or_slide_count, OLD.uploaded_by, OLD.uploaded_at)
     IS DISTINCT FROM
     ROW(NEW.source_document_id, NEW.occurrence_id, NEW.asset_ref, NEW.asset_version,
         NEW.upload_session_ref, NEW.extraction_job_ref, NEW.safe_file_name,
         NEW.file_extension, NEW.page_or_slide_count, NEW.uploaded_by, NEW.uploaded_at) THEN
    RAISE EXCEPTION 'SOURCE_DOCUMENT_IMMUTABLE';
  END IF;
  IF OLD.document_state = 'DELETED'
     AND (NEW.document_state <> 'DELETED' OR NEW.deleted_at IS DISTINCT FROM OLD.deleted_at) THEN
    RAISE EXCEPTION 'SOURCE_DOCUMENT_STATE_ONE_WAY';
  END IF;
  RETURN NEW;
END; $$
"""

DOCUMENT_REVISION_FUNCTION = """
CREATE FUNCTION lesson.protect_document_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  head integer;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'DOCUMENT_REVISION_DELETE_FORBIDDEN';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.review_state <> 'NEEDS_REVIEW' THEN
      RAISE EXCEPTION 'DOCUMENT_REVISION_INSERT_NOT_PENDING';
    END IF;
    SELECT coalesce(max(revision_no), 0) INTO head FROM lesson.document_revisions
      WHERE source_document_id = NEW.source_document_id;
    IF NEW.revision_no <> head + 1 THEN
      RAISE EXCEPTION 'DOCUMENT_REVISION_NUMBER_GAP';
    END IF;
    RETURN NEW;
  END IF;
  IF ROW(OLD.document_revision_id, OLD.source_document_id, OLD.revision_no, OLD.origin,
         OLD.base_revision_no, OLD.extracted_text, OLD.extracted_text_hash, OLD.parser_name,
         OLD.parser_version, OLD.extraction_warnings, OLD.page_coverage, OLD.created_by,
         OLD.created_at)
     IS DISTINCT FROM
     ROW(NEW.document_revision_id, NEW.source_document_id, NEW.revision_no, NEW.origin,
         NEW.base_revision_no, NEW.extracted_text, NEW.extracted_text_hash, NEW.parser_name,
         NEW.parser_version, NEW.extraction_warnings, NEW.page_coverage, NEW.created_by,
         NEW.created_at) THEN
    RAISE EXCEPTION 'DOCUMENT_REVISION_IMMUTABLE';
  END IF;
  IF OLD.review_state = 'NEEDS_REVIEW' AND NEW.review_state = 'CONFIRMED' THEN
    RETURN NEW;
  END IF;
  IF NEW.review_state = OLD.review_state
     AND NEW.reviewed_by IS NOT DISTINCT FROM OLD.reviewed_by
     AND NEW.reviewed_at IS NOT DISTINCT FROM OLD.reviewed_at THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'DOCUMENT_REVISION_REVIEW_ONE_WAY';
END; $$
"""

PLAN_REVISION_FUNCTION = """
CREATE FUNCTION lesson.protect_plan_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  occ lesson.occurrences%ROWTYPE;
  head integer;
  v_document_occurrence text;
  v_document_state text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'PLAN_REVISION_DELETE_FORBIDDEN';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.state <> 'DRAFT' OR NEW.approved_by IS NOT NULL OR NEW.approved_at IS NOT NULL
       OR NEW.superseded_at IS NOT NULL THEN
      RAISE EXCEPTION 'PLAN_INSERT_NOT_DRAFT';
    END IF;
    SELECT * INTO occ FROM lesson.occurrences WHERE occurrence_id = NEW.occurrence_id;
    IF NOT FOUND THEN
      RETURN NEW;
    END IF;
    IF ROW(NEW.source_lesson_id, NEW.source_lesson_version_id, NEW.source_lesson_version_no,
           NEW.source_lesson_version_hash)
       IS DISTINCT FROM
       ROW(occ.source_lesson_id, occ.source_lesson_version_id, occ.source_lesson_version_no,
           occ.source_lesson_version_hash) THEN
      RAISE EXCEPTION 'PLAN_PIN_MISMATCH';
    END IF;
    IF NEW.source_document_revision_id IS NOT NULL THEN
      SELECT d.occurrence_id, d.document_state INTO v_document_occurrence, v_document_state
        FROM lesson.document_revisions r
        JOIN lesson.source_documents d ON d.source_document_id = r.source_document_id
        WHERE r.document_revision_id = NEW.source_document_revision_id;
      IF v_document_occurrence IS DISTINCT FROM NEW.occurrence_id
         OR v_document_state IS DISTINCT FROM 'EXTRACTED' THEN
        RAISE EXCEPTION 'PLAN_DOCUMENT_MISMATCH';
      END IF;
    END IF;
    SELECT coalesce(max(revision_no), 0) INTO head FROM lesson.plan_revisions
      WHERE occurrence_id = NEW.occurrence_id;
    IF NEW.revision_no <> head + 1 THEN
      RAISE EXCEPTION 'PLAN_REVISION_NUMBER_GAP';
    END IF;
    IF jsonb_typeof(NEW.objectives) IS DISTINCT FROM 'array'
       OR jsonb_array_length(NEW.objectives) NOT BETWEEN 1 AND 12 THEN
      RAISE EXCEPTION 'PLAN_OBJECTIVE_INVALID';
    END IF;
    IF EXISTS (
      SELECT 1 FROM jsonb_array_elements(NEW.objectives) AS element
      WHERE jsonb_typeof(element) <> 'string'
         OR char_length(element #>> '{}') NOT BETWEEN 1 AND 1000
    ) THEN
      RAISE EXCEPTION 'PLAN_OBJECTIVE_INVALID';
    END IF;
    RETURN NEW;
  END IF;
  IF ROW(OLD.plan_revision_id, OLD.occurrence_id, OLD.revision_no,
         OLD.source_document_revision_id, OLD.objectives, OLD.teacher_direction,
         OLD.safety_notes, OLD.content_hash, OLD.source_lesson_id,
         OLD.source_lesson_version_id, OLD.source_lesson_version_no,
         OLD.source_lesson_version_hash, OLD.created_by, OLD.created_at)
     IS DISTINCT FROM
     ROW(NEW.plan_revision_id, NEW.occurrence_id, NEW.revision_no,
         NEW.source_document_revision_id, NEW.objectives, NEW.teacher_direction,
         NEW.safety_notes, NEW.content_hash, NEW.source_lesson_id,
         NEW.source_lesson_version_id, NEW.source_lesson_version_no,
         NEW.source_lesson_version_hash, NEW.created_by, NEW.created_at) THEN
    RAISE EXCEPTION 'PLAN_IMMUTABLE_CONTENT';
  END IF;
  IF OLD.state = NEW.state THEN
    IF NEW.approved_by IS DISTINCT FROM OLD.approved_by
       OR NEW.approved_at IS DISTINCT FROM OLD.approved_at
       OR NEW.superseded_at IS DISTINCT FROM OLD.superseded_at THEN
      RAISE EXCEPTION 'PLAN_ILLEGAL_TRANSITION';
    END IF;
    RETURN NEW;
  END IF;
  IF OLD.state = 'DRAFT' AND NEW.state = 'APPROVED' THEN
    IF EXISTS (
      SELECT 1 FROM lesson.plan_activities
      WHERE plan_revision_id = OLD.plan_revision_id
        AND activity_kind = 'CUSTOM' AND confirmed_at IS NULL
    ) THEN
      RAISE EXCEPTION 'LESSON_PLAN_CHECKLIST_REQUIRED';
    END IF;
    RETURN NEW;
  END IF;
  IF OLD.state = 'APPROVED' AND NEW.state = 'SUPERSEDED' THEN
    IF NEW.approved_by IS DISTINCT FROM OLD.approved_by
       OR NEW.approved_at IS DISTINCT FROM OLD.approved_at THEN
      RAISE EXCEPTION 'PLAN_IMMUTABLE_CONTENT';
    END IF;
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'PLAN_ILLEGAL_TRANSITION';
END; $$
"""

PLAN_ACTIVITY_FUNCTION = """
CREATE FUNCTION lesson.protect_plan_activity() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_plan_state text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'PLAN_ACTIVITY_DELETE_FORBIDDEN';
  END IF;
  SELECT state INTO v_plan_state FROM lesson.plan_revisions
    WHERE plan_revision_id = NEW.plan_revision_id FOR SHARE;
  IF TG_OP = 'INSERT' THEN
    IF v_plan_state IS DISTINCT FROM 'DRAFT' THEN
      RAISE EXCEPTION 'PLAN_ACTIVITY_PLAN_NOT_DRAFT';
    END IF;
    IF NEW.safety_checklist_version IS NOT NULL OR NEW.checklist_result IS NOT NULL
       OR NEW.confirmed_by IS NOT NULL OR NEW.confirmed_at IS NOT NULL THEN
      RAISE EXCEPTION 'PLAN_ACTIVITY_INSERT_CONFIRMED';
    END IF;
    RETURN NEW;
  END IF;
  IF ROW(OLD.plan_activity_id, OLD.plan_revision_id, OLD.activity_order, OLD.activity_kind,
         OLD.catalog_activity_ref, OLD.activity_version, OLD.custom_title,
         OLD.custom_description, OLD.activity_snapshot, OLD.activity_snapshot_hash)
     IS DISTINCT FROM
     ROW(NEW.plan_activity_id, NEW.plan_revision_id, NEW.activity_order, NEW.activity_kind,
         NEW.catalog_activity_ref, NEW.activity_version, NEW.custom_title,
         NEW.custom_description, NEW.activity_snapshot, NEW.activity_snapshot_hash) THEN
    RAISE EXCEPTION 'PLAN_ACTIVITY_IMMUTABLE';
  END IF;
  IF ROW(OLD.safety_checklist_version, OLD.checklist_result, OLD.confirmed_by, OLD.confirmed_at)
     IS DISTINCT FROM
     ROW(NEW.safety_checklist_version, NEW.checklist_result, NEW.confirmed_by, NEW.confirmed_at)
  THEN
    IF OLD.confirmed_at IS NOT NULL OR v_plan_state IS DISTINCT FROM 'DRAFT' THEN
      RAISE EXCEPTION 'PLAN_ACTIVITY_CHECKLIST_LOCKED';
    END IF;
  END IF;
  RETURN NEW;
END; $$
"""

TRIGGERS = (
    ("occurrences", "protect_occurrence", "INSERT OR UPDATE OR DELETE"),
    ("source_documents", "protect_source_document", "INSERT OR UPDATE OR DELETE"),
    ("document_revisions", "protect_document_revision", "INSERT OR UPDATE OR DELETE"),
    ("plan_revisions", "protect_plan_revision", "INSERT OR UPDATE OR DELETE"),
    ("plan_activities", "protect_plan_activity", "INSERT OR UPDATE OR DELETE"),
)
FUNCTIONS = tuple(function for _table, function, _events in TRIGGERS)

# Value CHECKs. Every CASE keeps a jsonb function from raising on a value of another type.
OCCURRENCE_CHECKS = (
    ("ck_occ_title", "char_length(title) <= 200 AND char_length(btrim(title)) >= 1"),
    (
        "ck_occ_state",
        "state IN ('DRAFT', 'DOCUMENT_REVIEW', 'PLAN_REVIEW', 'APPROVED', "
        "'SAMPLE_AVAILABLE', 'SAMPLE_USED', 'ARCHIVED')",
    ),
    ("ck_occ_revision", "revision > 0"),
    (
        "ck_occ_plan_state",
        "(state IN ('DRAFT', 'DOCUMENT_REVIEW', 'PLAN_REVIEW') AND "
        "approved_plan_revision_id IS NULL) OR "
        "(state IN ('APPROVED', 'SAMPLE_AVAILABLE', 'SAMPLE_USED') AND "
        "approved_plan_revision_id IS NOT NULL) OR "
        "state = 'ARCHIVED'",
    ),
    (
        "ck_occ_pin",
        "(source_lesson_id IS NULL AND source_lesson_version_id IS NULL AND "
        "source_lesson_version_no IS NULL AND source_lesson_version_hash IS NULL) OR "
        "(source_lesson_id IS NOT NULL AND source_lesson_version_id IS NOT NULL AND "
        "source_lesson_version_no IS NOT NULL AND source_lesson_version_hash IS NOT NULL AND "
        f"source_lesson_version_no > 0 AND source_lesson_version_hash ~ {HEX64})",
    ),
    ("ck_occ_sample_state", "sample_slot_state IN ('AVAILABLE', 'CLAIMED')"),
    (
        "ck_occ_sample",
        "(sample_slot_state = 'AVAILABLE' AND sample_claimed_at IS NULL AND "
        "successful_sample_run_ref IS NULL) OR "
        "(sample_slot_state = 'CLAIMED' AND sample_claimed_at IS NOT NULL)",
    ),
    (
        "ck_occ_projection",
        "(class_projection_confirmed_by_ref IS NULL) = (class_projection_confirmed_at IS NULL)",
    ),
)
SOURCE_DOCUMENT_CHECKS = (
    ("ck_srcdoc_asset_version", "asset_version > 0"),
    ("ck_srcdoc_file_name", "char_length(btrim(safe_file_name)) > 0"),
    ("ck_srcdoc_extension", "file_extension IN ('.pdf', '.docx', '.pptx')"),
    (
        "ck_srcdoc_pages",
        "page_or_slide_count IS NULL OR page_or_slide_count BETWEEN 1 AND 100",
    ),
    ("ck_srcdoc_state", "document_state IN ('EXTRACTED', 'DELETED')"),
    ("ck_srcdoc_deleted", "(document_state = 'DELETED') = (deleted_at IS NOT NULL)"),
)
DOCUMENT_REVISION_CHECKS = (
    ("ck_docrev_number", "revision_no > 0"),
    ("ck_docrev_origin", "origin IN ('EXTRACTION', 'TEACHER_EDIT')"),
    (
        "ck_docrev_lineage",
        "(origin = 'EXTRACTION' AND revision_no = 1 AND base_revision_no IS NULL AND "
        "parser_name IS NOT NULL AND parser_version IS NOT NULL) OR "
        "(origin = 'TEACHER_EDIT' AND revision_no > 1 AND base_revision_no IS NOT NULL AND "
        "base_revision_no >= 1 AND base_revision_no < revision_no AND "
        "parser_name IS NULL AND parser_version IS NULL)",
    ),
    ("ck_docrev_text_size", "octet_length(extracted_text) BETWEEN 1 AND 2097152"),
    (
        "ck_docrev_text_hash",
        "extracted_text_hash = encode(sha256(convert_to(extracted_text, 'UTF8')), 'hex')",
    ),
    (
        "ck_docrev_warnings",
        "CASE WHEN jsonb_typeof(extraction_warnings) = 'array' THEN true ELSE false END",
    ),
    (
        "ck_docrev_coverage",
        "CASE WHEN jsonb_typeof(page_coverage) = 'array' THEN true ELSE false END",
    ),
    ("ck_docrev_review_state", "review_state IN ('NEEDS_REVIEW', 'CONFIRMED')"),
    (
        "ck_docrev_review",
        "(review_state = 'NEEDS_REVIEW' AND reviewed_by IS NULL AND reviewed_at IS NULL) OR "
        "(review_state = 'CONFIRMED' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
    ),
)
PLAN_REVISION_CHECKS = (
    ("ck_plan_number", "revision_no > 0"),
    (
        "ck_plan_objectives",
        "CASE WHEN jsonb_typeof(objectives) = 'array' "
        "THEN jsonb_array_length(objectives) BETWEEN 1 AND 12 ELSE false END",
    ),
    (
        "ck_plan_direction",
        "char_length(teacher_direction) <= 2000 AND char_length(btrim(teacher_direction)) >= 1",
    ),
    ("ck_plan_safety_notes", "safety_notes IS NULL OR char_length(safety_notes) <= 2000"),
    ("ck_plan_state", "state IN ('DRAFT', 'APPROVED', 'SUPERSEDED')"),
    ("ck_plan_hash", f"content_hash ~ {HEX64}"),
    (
        "ck_plan_pin",
        "(source_lesson_id IS NULL AND source_lesson_version_id IS NULL AND "
        "source_lesson_version_no IS NULL AND source_lesson_version_hash IS NULL) OR "
        "(source_lesson_id IS NOT NULL AND source_lesson_version_id IS NOT NULL AND "
        "source_lesson_version_no IS NOT NULL AND source_lesson_version_hash IS NOT NULL AND "
        f"source_lesson_version_no > 0 AND source_lesson_version_hash ~ {HEX64})",
    ),
    (
        "ck_plan_approval",
        "(state = 'DRAFT' AND approved_by IS NULL AND approved_at IS NULL AND "
        "superseded_at IS NULL) OR "
        "(state = 'APPROVED' AND approved_by IS NOT NULL AND approved_at IS NOT NULL AND "
        "superseded_at IS NULL) OR "
        "(state = 'SUPERSEDED' AND approved_by IS NOT NULL AND approved_at IS NOT NULL AND "
        "superseded_at IS NOT NULL)",
    ),
)
PLAN_ACTIVITY_CHECKS = (
    ("ck_planact_order", "activity_order BETWEEN 1 AND 24"),
    ("ck_planact_kind", "activity_kind IN ('CATALOG', 'LESSON', 'CUSTOM')"),
    ("ck_planact_version", "activity_version IS NULL OR activity_version > 0"),
    (
        "ck_planact_shape",
        "(activity_kind = 'CUSTOM' AND catalog_activity_ref IS NULL AND "
        "custom_title IS NOT NULL AND char_length(btrim(custom_title)) >= 1 AND "
        "custom_description IS NOT NULL AND char_length(custom_description) <= 4000 AND "
        "char_length(btrim(custom_description)) >= 1) OR "
        "(activity_kind IN ('CATALOG', 'LESSON') AND catalog_activity_ref IS NOT NULL AND "
        "custom_title IS NULL AND custom_description IS NULL AND "
        "activity_snapshot IS NOT NULL AND jsonb_typeof(activity_snapshot) = 'object' AND "
        "activity_snapshot_hash IS NOT NULL)",
    ),
    (
        "ck_planact_snapshot_hash",
        f"activity_snapshot_hash IS NULL OR activity_snapshot_hash ~ {HEX64}",
    ),
    (
        "ck_planact_checklist",
        "(safety_checklist_version IS NULL AND checklist_result IS NULL AND "
        "confirmed_by IS NULL AND confirmed_at IS NULL) OR "
        "(activity_kind = 'CUSTOM' AND safety_checklist_version IS NOT NULL AND "
        "checklist_result IS NOT NULL AND jsonb_typeof(checklist_result) = 'object' AND "
        "confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL)",
    ),
)


def _checks(rows: tuple[tuple[str, str], ...]) -> list[sa.CheckConstraint]:
    return [sa.CheckConstraint(text, name=name) for name, text in rows]


def _created_at() -> sa.Column[Any]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def _fk(column: str, target: str, name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint([column], [target], name=name, ondelete="RESTRICT")


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())

    op.create_table(
        "occurrences",
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
        _created_at(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        *_checks(OCCURRENCE_CHECKS),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_occ_class_created",
        "occurrences",
        ["class_ref", sa.text("created_at DESC"), sa.text("occurrence_id DESC")],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_occ_teacher",
        "occurrences",
        ["responsible_teacher_ref", sa.text("created_at DESC")],
        schema=SCHEMA,
    )

    op.create_table(
        "source_documents",
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
        _fk("occurrence_id", "lesson.occurrences.occurrence_id", "fk_srcdoc_occurrence"),
        sa.UniqueConstraint("asset_ref", "asset_version", name="uq_srcdoc_asset"),
        sa.UniqueConstraint("upload_session_ref", name="uq_srcdoc_upload_session"),
        *_checks(SOURCE_DOCUMENT_CHECKS),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_srcdoc_occurrence_uploaded",
        "source_documents",
        ["occurrence_id", sa.text("uploaded_at DESC"), sa.text("source_document_id DESC")],
        schema=SCHEMA,
    )

    op.create_table(
        "document_revisions",
        sa.Column("document_revision_id", sa.String(36), primary_key=True),
        sa.Column("source_document_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("base_revision_no", sa.Integer()),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extracted_text_hash", sa.String(64), nullable=False),
        sa.Column("parser_name", sa.String(64)),
        sa.Column("parser_version", sa.String(64)),
        sa.Column("extraction_warnings", jsonb, server_default="[]", nullable=False),
        sa.Column("page_coverage", jsonb, server_default="[]", nullable=False),
        sa.Column("review_state", sa.String(16), server_default="NEEDS_REVIEW", nullable=False),
        sa.Column("reviewed_by", sa.String(36)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(36), nullable=False),
        _created_at(),
        _fk(
            "source_document_id",
            "lesson.source_documents.source_document_id",
            "fk_docrev_source_document",
        ),
        sa.UniqueConstraint("source_document_id", "revision_no", name="uq_docrev_number"),
        *_checks(DOCUMENT_REVISION_CHECKS),
        schema=SCHEMA,
    )

    op.create_table(
        "plan_revisions",
        sa.Column("plan_revision_id", sa.String(36), primary_key=True),
        sa.Column("occurrence_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("source_document_revision_id", sa.String(36)),
        sa.Column("objectives", jsonb, nullable=False),
        sa.Column("teacher_direction", sa.Text(), nullable=False),
        sa.Column("safety_notes", sa.Text()),
        sa.Column("state", sa.String(16), server_default="DRAFT", nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("source_lesson_id", sa.String(36)),
        sa.Column("source_lesson_version_id", sa.String(36)),
        sa.Column("source_lesson_version_no", sa.Integer()),
        sa.Column("source_lesson_version_hash", sa.String(64)),
        sa.Column("created_by", sa.String(36), nullable=False),
        _created_at(),
        sa.Column("approved_by", sa.String(36)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        _fk("occurrence_id", "lesson.occurrences.occurrence_id", "fk_plan_occurrence"),
        _fk(
            "source_document_revision_id",
            "lesson.document_revisions.document_revision_id",
            "fk_plan_document_revision",
        ),
        sa.UniqueConstraint("occurrence_id", "revision_no", name="uq_plan_number"),
        # A1: the target of the composite pointer foreign key on lesson.occurrences.
        sa.UniqueConstraint("plan_revision_id", "occurrence_id", name="uq_plan_id_occurrence"),
        *_checks(PLAN_REVISION_CHECKS),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_plan_one_approved",
        "plan_revisions",
        ["occurrence_id"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("state = 'APPROVED'"),
    )

    op.create_table(
        "plan_activities",
        sa.Column("plan_activity_id", sa.String(36), primary_key=True),
        sa.Column("plan_revision_id", sa.String(36), nullable=False),
        sa.Column("activity_order", sa.Integer(), nullable=False),
        sa.Column("activity_kind", sa.String(16), nullable=False),
        sa.Column("catalog_activity_ref", sa.String(256)),
        sa.Column("activity_version", sa.Integer()),
        sa.Column("custom_title", sa.String(200)),
        sa.Column("custom_description", sa.Text()),
        sa.Column("activity_snapshot", jsonb),
        sa.Column("activity_snapshot_hash", sa.String(64)),
        sa.Column("safety_checklist_version", sa.String(32)),
        sa.Column("checklist_result", jsonb),
        sa.Column("confirmed_by", sa.String(36)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        _fk(
            "plan_revision_id",
            "lesson.plan_revisions.plan_revision_id",
            "fk_planact_plan_revision",
        ),
        sa.UniqueConstraint("plan_revision_id", "activity_order", name="uq_planact_order"),
        *_checks(PLAN_ACTIVITY_CHECKS),
        schema=SCHEMA,
    )

    # A1: composite, immediate (not deferred) pointer. MATCH SIMPLE: no check while it is NULL.
    op.create_foreign_key(
        "fk_occ_approved_plan",
        "occurrences",
        "plan_revisions",
        ["approved_plan_revision_id", "occurrence_id"],
        ["plan_revision_id", "occurrence_id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="RESTRICT",
    )

    for statement in (
        OCCURRENCE_FUNCTION,
        SOURCE_DOCUMENT_FUNCTION,
        DOCUMENT_REVISION_FUNCTION,
        PLAN_REVISION_FUNCTION,
        PLAN_ACTIVITY_FUNCTION,
    ):
        op.execute(statement)
    for table, function, events in TRIGGERS:
        op.execute(
            f"CREATE TRIGGER {function} BEFORE {events} ON {SCHEMA}.{table} "
            f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{function}()"
        )


def _refuse_while_rows_exist() -> None:
    bind = op.get_bind()
    for table in TABLES:
        found = bind.execute(sa.text(f"SELECT 1 FROM {SCHEMA}.{table} LIMIT 1")).first()
        if found is not None:
            raise RuntimeError(f"DDL-A downgrade refused: {SCHEMA}.{table} holds rows")


def downgrade() -> None:
    _refuse_while_rows_exist()
    op.drop_constraint("fk_occ_approved_plan", "occurrences", schema=SCHEMA, type_="foreignkey")
    for table in reversed(TABLES):
        # The triggers go with their tables; the functions are dropped afterwards.
        op.drop_table(table, schema=SCHEMA)
    for function in FUNCTIONS:
        op.execute(f"DROP FUNCTION {SCHEMA}.{function}()")
