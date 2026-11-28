"""SQLAlchemy table mirrors for Teacher Sketch Deck revisions (schema ``lesson``)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

SKETCH_DECK_METADATA = sa.MetaData()

SKETCH_DECK_REVISIONS = sa.Table(
    "sketch_deck_revisions",
    SKETCH_DECK_METADATA,
    sa.Column("sketch_deck_revision_id", sa.String(36), primary_key=True),
    sa.Column("occurrence_id", sa.String(36), nullable=False),
    sa.Column("plan_revision_id", sa.String(36), nullable=False),
    sa.Column("revision_no", sa.Integer(), nullable=False),
    sa.Column("plan_content_hash", sa.String(64), nullable=False),
    sa.Column("review_confirmed", sa.Boolean(), nullable=False),
    sa.Column("topic", sa.String(120), nullable=False),
    sa.Column("drawing_steps", JSONB, nullable=False),
    sa.Column("subject_knowledge", JSONB, nullable=False),
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
        "length(target_age_band) BETWEEN 1 AND 128",
        name="ck_sketch_deck_age_band",
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
    schema="lesson",
)

sa.Index(
    "uq_sketch_deck_one_ready",
    SKETCH_DECK_REVISIONS.c.occurrence_id,
    unique=True,
    postgresql_where=SKETCH_DECK_REVISIONS.c.state == "READY",
)

SKETCH_DECK_STEPS = sa.Table(
    "sketch_deck_steps",
    SKETCH_DECK_METADATA,
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
    sa.Column("bounded_layout_hints", JSONB, nullable=False),
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
    schema="lesson",
)

SKETCH_DECK_TABLES = (SKETCH_DECK_REVISIONS, SKETCH_DECK_STEPS)

__all__ = [
    "SKETCH_DECK_METADATA",
    "SKETCH_DECK_REVISIONS",
    "SKETCH_DECK_STEPS",
    "SKETCH_DECK_TABLES",
]
