"""Teacher occurrence presentations, immutable revisions and private SVG review drafts.

FEAT-066 goal v4 Phase E E1 T-SLD1. The down_revision is provisional until Phase D is
squashed; the owner approved this DDL on 2026-11-25. No child/profile/roster reference is stored.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261126_sl_0001"
down_revision = "20261125_nt_0003"
branch_labels = None
depends_on = None

SCHEMA = "lesson"


def upgrade() -> None:
    op.create_table(
        "presentations",
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
            ["occurrence_id"], ["lesson.occurrences.occurrence_id"],
            ondelete="RESTRICT", name="fk_pres_occurrence",
        ),
        sa.UniqueConstraint("occurrence_id", name="uq_pres_occurrence"),
        schema=SCHEMA,
    )
    op.create_table(
        "presentation_revisions",
        sa.Column("presentation_revision_id", sa.String(36), primary_key=True),
        sa.Column("presentation_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("base_revision_no", sa.Integer()),
        sa.Column("plan_revision_id", sa.String(36), nullable=False),
        sa.Column("plan_content_hash", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("slides", postgresql.JSONB(), nullable=False),
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
            "CASE WHEN jsonb_typeof(slides) = 'array' THEN "
            "jsonb_array_length(slides) BETWEEN 1 AND 100 AND "
            "octet_length(slides::text) <= 1048576 ELSE false END",
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
            ["presentation_id"], ["lesson.presentations.presentation_id"],
            ondelete="RESTRICT", name="fk_presrev_presentation",
        ),
        sa.ForeignKeyConstraint(
            ["plan_revision_id"], ["lesson.plan_revisions.plan_revision_id"],
            ondelete="RESTRICT", name="fk_presrev_plan_revision",
        ),
        sa.UniqueConstraint("presentation_id", "revision_no", name="uq_presrev_number"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_presrev_one_ready", "presentation_revisions", ["presentation_id"],
        unique=True, schema=SCHEMA, postgresql_where=sa.text("state = 'READY'"),
    )
    op.create_table(
        "presentation_svg_drafts",
        sa.Column("svg_draft_id", sa.String(36), primary_key=True),
        sa.Column("presentation_id", sa.String(36), nullable=False),
        sa.Column("state", sa.String(16), server_default="PENDING_REVIEW", nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("canonical_sha256", sa.String(64), nullable=False),
        sa.Column("document", postgresql.JSONB(), nullable=False),
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
        sa.CheckConstraint(
            "canonical_sha256 ~ '^[0-9a-f]{64}$'", name="ck_pres_svg_canonical_hash"
        ),
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
            ["presentation_id"], ["lesson.presentations.presentation_id"],
            ondelete="RESTRICT", name="fk_pres_svg_presentation",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_pres_svg_draft_created", "presentation_svg_drafts",
        ["presentation_id", sa.text("created_at DESC")], schema=SCHEMA,
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION lesson.protect_presentation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE occurrence_organization varchar(128);
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'PRESENTATION_DELETE_FORBIDDEN' USING ERRCODE = '23514';
          ELSIF TG_OP = 'INSERT' THEN
            SELECT organization_ref INTO occurrence_organization
              FROM lesson.occurrences WHERE occurrence_id = NEW.occurrence_id;
            IF occurrence_organization IS NULL OR NEW.organization_ref <> occurrence_organization
               OR NEW.revision <> 1 OR NEW.head_revision_no <> 1
               OR NEW.ready_revision_no IS NOT NULL THEN
              RAISE EXCEPTION 'PRESENTATION_IMMUTABLE' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
          END IF;
          IF ROW(NEW.presentation_id, NEW.occurrence_id, NEW.organization_ref,
                 NEW.created_by, NEW.created_at) IS DISTINCT FROM
             ROW(OLD.presentation_id, OLD.occurrence_id, OLD.organization_ref,
                 OLD.created_by, OLD.created_at)
             OR NEW.head_revision_no < OLD.head_revision_no
             OR NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'PRESENTATION_IMMUTABLE' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER protect_presentation BEFORE INSERT OR UPDATE OR DELETE "
        "ON lesson.presentations FOR EACH ROW "
        "EXECUTE FUNCTION lesson.protect_presentation()"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION lesson.protect_presentation_revision() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE expected_revision integer;
        DECLARE occurrence_id_value varchar(36);
        DECLARE plan_state varchar(16);
        DECLARE plan_occurrence_id varchar(36);
        DECLARE plan_hash varchar(64);
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'PRESENTATION_REVISION_DELETE_FORBIDDEN' USING ERRCODE = '23514';
          ELSIF TG_OP = 'INSERT' THEN
            IF NEW.state <> 'DRAFT' OR NEW.readied_by IS NOT NULL
               OR NEW.readied_at IS NOT NULL OR NEW.superseded_at IS NOT NULL THEN
              RAISE EXCEPTION 'PRESENTATION_REVISION_IMMUTABLE' USING ERRCODE = '23514';
            END IF;
            SELECT COALESCE(MAX(revision_no), 0) + 1 INTO expected_revision
              FROM lesson.presentation_revisions WHERE presentation_id = NEW.presentation_id;
            IF NEW.revision_no <> expected_revision THEN
              RAISE EXCEPTION 'PRESENTATION_REVISION_NUMBER_GAP' USING ERRCODE = '23514';
            END IF;
            SELECT occurrence_id INTO occurrence_id_value FROM lesson.presentations
              WHERE presentation_id = NEW.presentation_id;
            SELECT state, occurrence_id, content_hash
              INTO plan_state, plan_occurrence_id, plan_hash
              FROM lesson.plan_revisions
              WHERE plan_revision_id = NEW.plan_revision_id;
            IF plan_state IS DISTINCT FROM 'APPROVED'
               OR plan_occurrence_id IS DISTINCT FROM occurrence_id_value
               OR plan_hash IS DISTINCT FROM NEW.plan_content_hash THEN
              RAISE EXCEPTION 'PRESENTATION_PIN_MISMATCH' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
          END IF;
          IF ROW(NEW.presentation_revision_id, NEW.presentation_id, NEW.revision_no,
                 NEW.base_revision_no, NEW.plan_revision_id, NEW.plan_content_hash,
                 NEW.content_hash, NEW.slides, NEW.created_by, NEW.created_at)
             IS DISTINCT FROM
             ROW(OLD.presentation_revision_id, OLD.presentation_id, OLD.revision_no,
                 OLD.base_revision_no, OLD.plan_revision_id, OLD.plan_content_hash,
                 OLD.content_hash, OLD.slides, OLD.created_by, OLD.created_at) THEN
            RAISE EXCEPTION 'PRESENTATION_REVISION_IMMUTABLE' USING ERRCODE = '23514';
          END IF;
          IF OLD.state = 'DRAFT' AND NEW.state = 'READY'
             AND NEW.readied_by IS NOT NULL AND NEW.readied_at IS NOT NULL
             AND NEW.superseded_at IS NULL AND OLD.readied_by IS NULL
             AND OLD.readied_at IS NULL AND OLD.superseded_at IS NULL THEN
            RETURN NEW;
          ELSIF OLD.state = 'READY' AND NEW.state = 'SUPERSEDED'
             AND NEW.readied_by IS NOT DISTINCT FROM OLD.readied_by
             AND NEW.readied_at IS NOT DISTINCT FROM OLD.readied_at
             AND NEW.superseded_at IS NOT NULL AND OLD.superseded_at IS NULL THEN
            RETURN NEW;
          END IF;
          RAISE EXCEPTION 'PRESENTATION_ILLEGAL_TRANSITION' USING ERRCODE = '23514';
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER protect_presentation_revision BEFORE INSERT OR UPDATE OR DELETE "
        "ON lesson.presentation_revisions FOR EACH ROW "
        "EXECUTE FUNCTION lesson.protect_presentation_revision()"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION lesson.protect_presentation_svg_draft() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'PRESENTATION_SVG_DRAFT_DELETE_FORBIDDEN' USING ERRCODE = '23514';
          ELSIF TG_OP = 'INSERT' THEN
            IF NEW.state <> 'PENDING_REVIEW' OR NEW.revision <> 1
               OR NEW.decided_by IS NOT NULL OR NEW.decided_at IS NOT NULL THEN
              RAISE EXCEPTION 'PRESENTATION_SVG_DRAFT_IMMUTABLE' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
          END IF;
          IF ROW(NEW.svg_draft_id, NEW.presentation_id, NEW.input_hash, NEW.source_sha256,
                 NEW.canonical_sha256, NEW.document, NEW.sanitizer_version, NEW.generator_name,
                 NEW.generator_version, NEW.license_id, NEW.created_by, NEW.created_at)
             IS DISTINCT FROM
             ROW(OLD.svg_draft_id, OLD.presentation_id, OLD.input_hash, OLD.source_sha256,
                 OLD.canonical_sha256, OLD.document, OLD.sanitizer_version, OLD.generator_name,
                 OLD.generator_version, OLD.license_id, OLD.created_by, OLD.created_at) THEN
            RAISE EXCEPTION 'PRESENTATION_SVG_DRAFT_IMMUTABLE' USING ERRCODE = '23514';
          END IF;
          IF OLD.state = 'PENDING_REVIEW' AND NEW.state IN ('ACCEPTED', 'DISCARDED')
             AND NEW.revision = OLD.revision + 1 AND NEW.decided_by IS NOT NULL
             AND NEW.decided_at IS NOT NULL
             AND OLD.decided_by IS NULL AND OLD.decided_at IS NULL THEN
            RETURN NEW;
          END IF;
          RAISE EXCEPTION 'PRESENTATION_SVG_DRAFT_ILLEGAL_TRANSITION' USING ERRCODE = '23514';
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER protect_presentation_svg_draft BEFORE INSERT OR UPDATE OR DELETE "
        "ON lesson.presentation_svg_drafts FOR EACH ROW "
        "EXECUTE FUNCTION lesson.protect_presentation_svg_draft()"
    )

    op.drop_constraint(
        "ck_core_upload_purpose", "core_upload_sessions", type_="check", schema="public"
    )
    op.create_check_constraint(
        "ck_core_upload_purpose",
        "core_upload_sessions",
        "purpose IN ('PROFILE_IMAGE', 'RUN_ARTWORK', 'RUN_AUDIO', 'LESSON_SOURCE', "
        "'OCCURRENCE_DOCUMENT', 'PRESENTATION_IMAGE')",
        schema="public",
    )


def downgrade() -> None:
    bind = op.get_bind()
    has_rows = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM lesson.presentations) "
            "OR EXISTS (SELECT 1 FROM lesson.presentation_revisions) "
            "OR EXISTS (SELECT 1 FROM lesson.presentation_svg_drafts) "
            "OR EXISTS (SELECT 1 FROM public.core_upload_sessions "
            "WHERE purpose = 'PRESENTATION_IMAGE')"
        )
    ).scalar_one()
    if has_rows:
        raise RuntimeError(
            "Refusing to downgrade teacher presentations while presentation data exists"
        )

    op.drop_constraint(
        "ck_core_upload_purpose", "core_upload_sessions", type_="check", schema="public"
    )
    op.create_check_constraint(
        "ck_core_upload_purpose",
        "core_upload_sessions",
        "purpose IN ('PROFILE_IMAGE', 'RUN_ARTWORK', 'RUN_AUDIO', 'LESSON_SOURCE', "
        "'OCCURRENCE_DOCUMENT')",
        schema="public",
    )
    op.drop_index("ix_pres_svg_draft_created", table_name="presentation_svg_drafts", schema=SCHEMA)
    op.drop_index("uq_presrev_one_ready", table_name="presentation_revisions", schema=SCHEMA)
    op.drop_table("presentation_svg_drafts", schema=SCHEMA)
    op.drop_table("presentation_revisions", schema=SCHEMA)
    op.drop_table("presentations", schema=SCHEMA)
    op.execute("DROP FUNCTION lesson.protect_presentation_svg_draft()")
    op.execute("DROP FUNCTION lesson.protect_presentation_revision()")
    op.execute("DROP FUNCTION lesson.protect_presentation()")
