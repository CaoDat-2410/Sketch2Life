"""Teacher Sketch Deck revisions and steps (FEAT-066, approved build 2026-11-26)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261126_dc_0001"
down_revision = "20261126_sh_0001"
branch_labels = None
depends_on = None

SCHEMA = "lesson"


def upgrade() -> None:
    op.create_table(
        "sketch_deck_revisions",
        sa.Column("sketch_deck_revision_id", sa.String(36), primary_key=True),
        sa.Column("occurrence_id", sa.String(36), nullable=False),
        sa.Column("plan_revision_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("plan_content_hash", sa.String(64), nullable=False),
        sa.Column("review_confirmed", sa.Boolean(), nullable=False),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("drawing_steps", postgresql.JSONB(), nullable=False),
        sa.Column("subject_knowledge", postgresql.JSONB(), nullable=False),
        sa.Column("target_age_band", sa.String(128), nullable=False),
        sa.Column("deck_schema_version", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), server_default="GENERATING", nullable=False),
        sa.Column("model_profile_ref", sa.String(128), nullable=False),
        sa.Column("model_profile_version", sa.String(128), nullable=False),
        sa.Column("prompt_template_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("compute_reservation_ref", sa.String(128)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("ready_at", sa.DateTime(timezone=True)),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("revision_no > 0", name="ck_sketch_deck_revision_no"),
        sa.CheckConstraint(
            "plan_content_hash ~ '^[0-9a-f]{64}$'", name="ck_sketch_deck_plan_hash"
        ),
        sa.CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_sketch_deck_content_hash",
        ),
        sa.CheckConstraint("config_hash ~ '^[0-9a-f]{64}$'", name="ck_sketch_deck_config_hash"),
        sa.CheckConstraint("review_confirmed IS TRUE", name="ck_sketch_deck_review_confirmed"),
        sa.CheckConstraint(
            "length(btrim(topic)) BETWEEN 1 AND 120 AND octet_length(topic) <= 480",
            name="ck_sketch_deck_topic",
        ),
        sa.CheckConstraint(
            "CASE WHEN jsonb_typeof(drawing_steps) = 'array' THEN "
            "jsonb_array_length(drawing_steps) BETWEEN 4 AND 8 AND "
            "octet_length(drawing_steps::text) <= 32768 ELSE false END",
            name="ck_sketch_deck_drawing_steps",
        ),
        sa.CheckConstraint(
            "CASE WHEN jsonb_typeof(subject_knowledge) = 'array' THEN "
            "jsonb_array_length(subject_knowledge) BETWEEN 1 AND 8 AND "
            "octet_length(subject_knowledge::text) <= 65536 ELSE false END",
            name="ck_sketch_deck_subject_knowledge",
        ),
        sa.CheckConstraint(
            "length(target_age_band) BETWEEN 1 AND 128", name="ck_sketch_deck_age_band"
        ),
        sa.CheckConstraint(
            "length(deck_schema_version) BETWEEN 1 AND 64",
            name="ck_sketch_deck_schema_version",
        ),
        sa.CheckConstraint(
            "length(model_profile_ref) BETWEEN 1 AND 128 AND "
            "length(model_profile_version) BETWEEN 1 AND 128 AND "
            "length(prompt_template_version) BETWEEN 1 AND 64",
            name="ck_sketch_deck_model_metadata",
        ),
        sa.CheckConstraint(
            "state IN ('GENERATING', 'READY', 'FAILED', 'STALE', 'SUPERSEDED')",
            name="ck_sketch_deck_state",
        ),
        sa.CheckConstraint(
            "(state IN ('GENERATING', 'FAILED') AND content_hash IS NULL AND ready_at IS NULL "
            "AND superseded_at IS NULL) OR "
            "(state IN ('READY', 'STALE') AND content_hash IS NOT NULL AND ready_at IS NOT NULL "
            "AND superseded_at IS NULL) OR "
            "(state = 'SUPERSEDED' AND content_hash IS NOT NULL AND ready_at IS NOT NULL "
            "AND superseded_at IS NOT NULL)",
            name="ck_sketch_deck_state_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["occurrence_id"],
            ["lesson.occurrences.occurrence_id"],
            ondelete="RESTRICT",
            name="fk_sketch_deck_occurrence",
        ),
        sa.ForeignKeyConstraint(
            ["plan_revision_id", "occurrence_id"],
            ["lesson.plan_revisions.plan_revision_id", "lesson.plan_revisions.occurrence_id"],
            ondelete="RESTRICT",
            name="fk_sketch_deck_plan_occurrence",
        ),
        sa.UniqueConstraint("occurrence_id", "revision_no", name="uq_sketch_deck_revision_no"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_sketch_deck_one_ready",
        "sketch_deck_revisions",
        ["occurrence_id"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("state = 'READY'"),
    )
    op.create_table(
        "sketch_deck_steps",
        sa.Column("sketch_deck_step_id", sa.String(36), primary_key=True),
        sa.Column("sketch_deck_revision_id", sa.String(36), nullable=False),
        sa.Column("plan_activity_id", sa.String(36)),
        sa.Column("instruction_group_key", sa.String(80), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("step_kind", sa.String(32), nullable=False),
        sa.Column("subject_key", sa.String(80), nullable=False),
        sa.Column("short_title", sa.String(160), nullable=False),
        sa.Column("child_facing_prompt", sa.String(600), nullable=False),
        sa.Column("teacher_explanation", sa.String(2000), nullable=False),
        sa.Column("bounded_layout_hints", postgresql.JSONB(), nullable=False),
        sa.Column("line_sketch_asset_ref", sa.String(256)),
        sa.Column("line_sketch_asset_version", sa.Integer()),
        sa.Column("source_job_ref", sa.String(128)),
        sa.Column("state", sa.String(16), server_default="GENERATING", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("step_index > 0", name="ck_sketch_deck_step_index"),
        sa.CheckConstraint(
            "length(instruction_group_key) BETWEEN 1 AND 80 AND "
            "length(step_kind) BETWEEN 1 AND 32 AND length(subject_key) BETWEEN 1 AND 80",
            name="ck_sketch_deck_step_keys",
        ),
        sa.CheckConstraint(
            "length(short_title) BETWEEN 1 AND 160 AND "
            "length(child_facing_prompt) BETWEEN 1 AND 600 AND "
            "length(teacher_explanation) BETWEEN 1 AND 2000",
            name="ck_sketch_deck_step_text",
        ),
        sa.CheckConstraint(
            "CASE WHEN jsonb_typeof(bounded_layout_hints) = 'object' THEN "
            "octet_length(bounded_layout_hints::text) <= 16384 ELSE false END",
            name="ck_sketch_deck_layout_hints",
        ),
        sa.CheckConstraint(
            "(line_sketch_asset_ref IS NULL AND line_sketch_asset_version IS NULL) OR "
            "(line_sketch_asset_ref IS NOT NULL AND line_sketch_asset_version > 0)",
            name="ck_sketch_deck_asset_ref_version",
        ),
        sa.CheckConstraint(
            "state IN ('GENERATING', 'READY', 'FAILED', 'STALE', 'SUPERSEDED')",
            name="ck_sketch_deck_step_state",
        ),
        sa.ForeignKeyConstraint(
            ["sketch_deck_revision_id"],
            ["lesson.sketch_deck_revisions.sketch_deck_revision_id"],
            ondelete="RESTRICT",
            name="fk_sketch_deck_step_revision",
        ),
        sa.ForeignKeyConstraint(
            ["plan_activity_id"],
            ["lesson.plan_activities.plan_activity_id"],
            ondelete="RESTRICT",
            name="fk_sketch_deck_step_activity",
        ),
        sa.UniqueConstraint(
            "sketch_deck_revision_id",
            "instruction_group_key",
            "step_index",
            name="uq_sketch_deck_step_order",
        ),
        schema=SCHEMA,
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION lesson.protect_sketch_deck_revision() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE expected_revision integer;
        DECLARE approved_plan_id varchar(36);
        DECLARE plan_state varchar(16);
        DECLARE plan_hash varchar(64);
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'SKETCH_DECK_REVISION_DELETE_FORBIDDEN' USING ERRCODE = '23514';
          ELSIF TG_OP = 'INSERT' THEN
            IF NEW.state <> 'GENERATING' OR NEW.content_hash IS NOT NULL
               OR NEW.ready_at IS NOT NULL OR NEW.superseded_at IS NOT NULL THEN
              RAISE EXCEPTION 'SKETCH_DECK_REVISION_IMMUTABLE' USING ERRCODE = '23514';
            END IF;
            SELECT approved_plan_revision_id INTO approved_plan_id
              FROM lesson.occurrences WHERE occurrence_id = NEW.occurrence_id FOR UPDATE;
            SELECT state, content_hash INTO plan_state, plan_hash
              FROM lesson.plan_revisions
              WHERE plan_revision_id = NEW.plan_revision_id
                AND occurrence_id = NEW.occurrence_id;
            IF approved_plan_id IS DISTINCT FROM NEW.plan_revision_id
               OR plan_state IS DISTINCT FROM 'APPROVED'
               OR plan_hash IS DISTINCT FROM NEW.plan_content_hash THEN
              RAISE EXCEPTION 'SKETCH_DECK_PLAN_PIN_MISMATCH' USING ERRCODE = '23514';
            END IF;
            SELECT COALESCE(MAX(revision_no), 0) + 1 INTO expected_revision
              FROM lesson.sketch_deck_revisions WHERE occurrence_id = NEW.occurrence_id;
            IF NEW.revision_no <> expected_revision THEN
              RAISE EXCEPTION 'SKETCH_DECK_REVISION_NUMBER_GAP' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
          END IF;

          IF ROW(NEW.sketch_deck_revision_id, NEW.occurrence_id, NEW.plan_revision_id,
                 NEW.revision_no, NEW.plan_content_hash, NEW.review_confirmed, NEW.topic,
                 NEW.drawing_steps, NEW.subject_knowledge, NEW.target_age_band,
                 NEW.deck_schema_version, NEW.model_profile_ref, NEW.model_profile_version,
                 NEW.prompt_template_version, NEW.config_hash, NEW.compute_reservation_ref,
                 NEW.created_by, NEW.created_at)
             IS DISTINCT FROM
             ROW(OLD.sketch_deck_revision_id, OLD.occurrence_id, OLD.plan_revision_id,
                 OLD.revision_no, OLD.plan_content_hash, OLD.review_confirmed, OLD.topic,
                 OLD.drawing_steps, OLD.subject_knowledge, OLD.target_age_band,
                 OLD.deck_schema_version, OLD.model_profile_ref, OLD.model_profile_version,
                 OLD.prompt_template_version, OLD.config_hash, OLD.compute_reservation_ref,
                 OLD.created_by, OLD.created_at) THEN
            RAISE EXCEPTION 'SKETCH_DECK_REVISION_IMMUTABLE' USING ERRCODE = '23514';
          END IF;

          IF OLD.state = 'GENERATING' AND NEW.state = 'READY'
             AND NEW.content_hash ~ '^[0-9a-f]{64}$' AND NEW.ready_at IS NOT NULL
             AND NEW.superseded_at IS NULL AND OLD.content_hash IS NULL
             AND OLD.ready_at IS NULL AND OLD.superseded_at IS NULL THEN
            SELECT approved_plan_revision_id INTO approved_plan_id
              FROM lesson.occurrences WHERE occurrence_id = NEW.occurrence_id;
            SELECT state, content_hash INTO plan_state, plan_hash
              FROM lesson.plan_revisions
              WHERE plan_revision_id = NEW.plan_revision_id
                AND occurrence_id = NEW.occurrence_id;
            IF approved_plan_id IS DISTINCT FROM NEW.plan_revision_id
               OR plan_state IS DISTINCT FROM 'APPROVED'
               OR plan_hash IS DISTINCT FROM NEW.plan_content_hash THEN
              RAISE EXCEPTION 'SKETCH_DECK_PLAN_PIN_MISMATCH' USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
              SELECT 1 FROM lesson.plan_activities pa
              WHERE pa.plan_revision_id = NEW.plan_revision_id
                AND NOT EXISTS (
                  SELECT 1 FROM lesson.sketch_deck_steps s
                  WHERE s.sketch_deck_revision_id = NEW.sketch_deck_revision_id
                    AND s.plan_activity_id = pa.plan_activity_id
                )
            ) OR NOT EXISTS (
              SELECT 1 FROM lesson.plan_activities pa
              WHERE pa.plan_revision_id = NEW.plan_revision_id
            ) THEN
              RAISE EXCEPTION 'SKETCH_DECK_ACTIVITY_COVERAGE_REQUIRED' USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
              SELECT 1 FROM lesson.sketch_deck_steps s
              WHERE s.sketch_deck_revision_id = NEW.sketch_deck_revision_id
              GROUP BY s.instruction_group_key
              HAVING COUNT(*) NOT BETWEEN 4 AND 8 OR MIN(s.step_index) <> 1
                 OR MAX(s.step_index) <> COUNT(*) OR COUNT(DISTINCT s.step_index) <> COUNT(*)
                 OR COUNT(DISTINCT COALESCE(s.plan_activity_id, '')) <> 1
            ) OR NOT EXISTS (
              SELECT 1 FROM lesson.sketch_deck_steps s
              WHERE s.sketch_deck_revision_id = NEW.sketch_deck_revision_id
            ) THEN
              RAISE EXCEPTION 'SKETCH_DECK_STEP_GROUP_INVALID' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
          ELSIF OLD.state = 'GENERATING' AND NEW.state = 'FAILED'
             AND NEW.content_hash IS NULL AND NEW.ready_at IS NULL
             AND NEW.superseded_at IS NULL AND OLD.ready_at IS NULL
             AND OLD.superseded_at IS NULL THEN
            RETURN NEW;
          ELSIF OLD.state = 'READY' AND NEW.state = 'STALE'
             AND NEW.content_hash IS NOT DISTINCT FROM OLD.content_hash
             AND NEW.ready_at IS NOT DISTINCT FROM OLD.ready_at
             AND NEW.superseded_at IS NULL AND OLD.superseded_at IS NULL THEN
            RETURN NEW;
          ELSIF OLD.state = 'READY' AND NEW.state = 'SUPERSEDED'
             AND NEW.content_hash IS NOT DISTINCT FROM OLD.content_hash
             AND NEW.ready_at IS NOT DISTINCT FROM OLD.ready_at
             AND NEW.superseded_at IS NOT NULL AND OLD.superseded_at IS NULL THEN
            RETURN NEW;
          END IF;
          RAISE EXCEPTION 'SKETCH_DECK_ILLEGAL_TRANSITION' USING ERRCODE = '23514';
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER protect_sketch_deck_revision BEFORE INSERT OR UPDATE OR DELETE "
        "ON lesson.sketch_deck_revisions FOR EACH ROW "
        "EXECUTE FUNCTION lesson.protect_sketch_deck_revision()"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION lesson.protect_sketch_deck_step() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE revision_state varchar(16);
        DECLARE plan_revision_id_value varchar(36);
        DECLARE activity_plan_id varchar(36);
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'SKETCH_DECK_STEP_DELETE_FORBIDDEN' USING ERRCODE = '23514';
          ELSIF TG_OP = 'INSERT' THEN
            IF NEW.state <> 'GENERATING' THEN
              RAISE EXCEPTION 'SKETCH_DECK_STEP_IMMUTABLE' USING ERRCODE = '23514';
            END IF;
            SELECT state, plan_revision_id INTO revision_state, plan_revision_id_value
              FROM lesson.sketch_deck_revisions
              WHERE sketch_deck_revision_id = NEW.sketch_deck_revision_id;
            IF revision_state IS DISTINCT FROM 'GENERATING' THEN
              RAISE EXCEPTION 'SKETCH_DECK_STEP_REVISION_NOT_GENERATING' USING ERRCODE = '23514';
            END IF;
            IF NEW.plan_activity_id IS NOT NULL THEN
              SELECT plan_revision_id INTO activity_plan_id FROM lesson.plan_activities
                WHERE plan_activity_id = NEW.plan_activity_id;
              IF activity_plan_id IS DISTINCT FROM plan_revision_id_value THEN
                RAISE EXCEPTION 'SKETCH_DECK_ACTIVITY_PIN_MISMATCH' USING ERRCODE = '23514';
              END IF;
            END IF;
            RETURN NEW;
          END IF;
          IF ROW(NEW.sketch_deck_step_id, NEW.sketch_deck_revision_id, NEW.plan_activity_id,
                 NEW.instruction_group_key, NEW.step_index, NEW.step_kind, NEW.subject_key,
                 NEW.short_title, NEW.child_facing_prompt, NEW.teacher_explanation,
                 NEW.bounded_layout_hints, NEW.line_sketch_asset_ref,
                 NEW.line_sketch_asset_version, NEW.source_job_ref, NEW.created_at)
             IS DISTINCT FROM
             ROW(OLD.sketch_deck_step_id, OLD.sketch_deck_revision_id, OLD.plan_activity_id,
                 OLD.instruction_group_key, OLD.step_index, OLD.step_kind, OLD.subject_key,
                 OLD.short_title, OLD.child_facing_prompt, OLD.teacher_explanation,
                 OLD.bounded_layout_hints, OLD.line_sketch_asset_ref,
                 OLD.line_sketch_asset_version, OLD.source_job_ref, OLD.created_at) THEN
            RAISE EXCEPTION 'SKETCH_DECK_STEP_IMMUTABLE' USING ERRCODE = '23514';
          END IF;
          SELECT state INTO revision_state FROM lesson.sketch_deck_revisions
            WHERE sketch_deck_revision_id = NEW.sketch_deck_revision_id;
          IF OLD.state = 'GENERATING' AND NEW.state = 'READY'
             AND revision_state = 'READY' THEN
            RETURN NEW;
          ELSIF OLD.state = 'READY' AND NEW.state = 'STALE'
             AND revision_state = 'STALE' THEN
            RETURN NEW;
          ELSIF OLD.state = 'READY' AND NEW.state = 'SUPERSEDED'
             AND revision_state = 'SUPERSEDED' THEN
            RETURN NEW;
          END IF;
          RAISE EXCEPTION 'SKETCH_DECK_STEP_ILLEGAL_TRANSITION' USING ERRCODE = '23514';
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER protect_sketch_deck_step BEFORE INSERT OR UPDATE OR DELETE "
        "ON lesson.sketch_deck_steps FOR EACH ROW "
        "EXECUTE FUNCTION lesson.protect_sketch_deck_step()"
    )


def downgrade() -> None:
    bind = op.get_bind()
    has_rows = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM lesson.sketch_deck_revisions) "
            "OR EXISTS (SELECT 1 FROM lesson.sketch_deck_steps)"
        )
    ).scalar_one()
    if has_rows:
        raise RuntimeError("Refusing to downgrade Sketch Deck tables while deck data exists")

    op.drop_table("sketch_deck_steps", schema=SCHEMA)
    op.drop_index("uq_sketch_deck_one_ready", table_name="sketch_deck_revisions", schema=SCHEMA)
    op.drop_table("sketch_deck_revisions", schema=SCHEMA)
    op.execute("DROP FUNCTION lesson.protect_sketch_deck_step()")
    op.execute("DROP FUNCTION lesson.protect_sketch_deck_revision()")
