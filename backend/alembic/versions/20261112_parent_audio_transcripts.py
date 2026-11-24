"""Persist Parent voice inputs and adult-confirmed transcript revisions."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261112_parent_audio_transcripts"
down_revision = "20261111_parent_platform_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_audio_inputs",
        sa.Column("audio_input_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("owner_subject", sa.String(256), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("asset_ref", sa.String(256), nullable=False),
        sa.Column("asset_sha256", sa.String(64), nullable=False),
        sa.Column("media_type", sa.String(32), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("scanner_name", sa.String(64), nullable=False),
        sa.Column("scanner_version", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_story_run_audio_run"),
        sa.UniqueConstraint("run_id", "audio_input_id", name="uq_story_run_audio_owner"),
        sa.UniqueConstraint("run_id", "idempotency_key_sha256", name="uq_story_run_audio_idempotency"),
        sa.CheckConstraint("length(idempotency_key_sha256) = 64 AND length(request_sha256) = 64", name="ck_story_run_audio_request_hashes"),
        sa.CheckConstraint("length(asset_sha256) = 64", name="ck_story_run_audio_asset_hash"),
        sa.CheckConstraint("media_type IN ('audio/wav','audio/mp4','audio/webm','audio/ogg')", name="ck_story_run_audio_media_type"),
        sa.CheckConstraint("size_bytes BETWEEN 1 AND 20971520", name="ck_story_run_audio_size"),
        sa.CheckConstraint("duration_ms BETWEEN 1 AND 120000", name="ck_story_run_audio_duration"),
        schema="story",
    )
    op.create_index(
        "ix_story_run_audio_asset",
        "run_audio_inputs",
        ["asset_ref", "created_at"],
        schema="story",
    )

    op.create_table(
        "transcript_revisions",
        sa.Column("transcript_revision_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("audio_input_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("transcript_raw", sa.String(4000), nullable=False),
        sa.Column("transcript_confirmed", sa.String(500)),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("language_probability", sa.Numeric(5, 4), nullable=False),
        sa.Column("model_id", sa.String(160), nullable=False),
        sa.Column("model_revision", sa.String(80), nullable=False),
        sa.Column("provider_call_id", sa.String(96), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("confirmed_by", sa.String(256)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["run_id", "audio_input_id"],
            ["story.run_audio_inputs.run_id", "story.run_audio_inputs.audio_input_id"],
            ondelete="RESTRICT",
            name="fk_story_transcript_audio",
        ),
        sa.UniqueConstraint("run_id", "transcript_revision_id", name="uq_story_transcript_owner"),
        sa.UniqueConstraint("run_id", "revision_no", name="uq_story_transcript_revision"),
        sa.CheckConstraint("revision_no > 0", name="ck_story_transcript_revision_no"),
        sa.CheckConstraint("state IN ('DRAFT','CONFIRMED','SUPERSEDED')", name="ck_story_transcript_state"),
        sa.CheckConstraint("language = 'vi'", name="ck_story_transcript_language"),
        sa.CheckConstraint("language_probability BETWEEN 0 AND 1", name="ck_story_transcript_probability"),
        sa.CheckConstraint("length(trim(transcript_raw)) <= 4000", name="ck_story_transcript_raw_length"),
        sa.CheckConstraint("transcript_confirmed IS NULL OR length(trim(transcript_confirmed)) BETWEEN 1 AND 500", name="ck_story_transcript_confirmed_length"),
        sa.CheckConstraint(
            "(state = 'CONFIRMED' AND transcript_confirmed IS NOT NULL AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL) OR "
            "(state IN ('DRAFT','SUPERSEDED'))",
            name="ck_story_transcript_confirmation_shape",
        ),
        schema="story",
    )

    op.add_column("run_inputs", sa.Column("audio_input_id", sa.String(36)), schema="story")
    op.add_column("run_inputs", sa.Column("transcript_revision_id", sa.String(36)), schema="story")
    op.drop_constraint("ck_story_run_input_typed_idea", "run_inputs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_input_typed_idea",
        "run_inputs",
        "(typed_idea IS NULL AND idea_source IS NULL) OR "
        "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 "
        "AND idea_source IN ('TEXT','TRANSCRIPT'))",
        schema="story",
    )
    op.create_foreign_key(
        "fk_story_run_input_audio",
        "run_inputs",
        "run_audio_inputs",
        ["run_id", "audio_input_id"],
        ["run_id", "audio_input_id"],
        source_schema="story",
        referent_schema="story",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_story_run_input_transcript",
        "run_inputs",
        "transcript_revisions",
        ["run_id", "transcript_revision_id"],
        ["run_id", "transcript_revision_id"],
        source_schema="story",
        referent_schema="story",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    connection = op.get_bind()
    has_audio = connection.execute(sa.text("SELECT EXISTS (SELECT 1 FROM story.run_audio_inputs)")).scalar()
    if has_audio:
        raise RuntimeError("Parent audio and transcript artifacts must be exported before downgrade")

    op.drop_constraint("fk_story_run_input_transcript", "run_inputs", schema="story", type_="foreignkey")
    op.drop_constraint("fk_story_run_input_audio", "run_inputs", schema="story", type_="foreignkey")
    op.drop_constraint("ck_story_run_input_typed_idea", "run_inputs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_input_typed_idea",
        "run_inputs",
        "(typed_idea IS NULL AND idea_source IS NULL) OR "
        "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 AND idea_source = 'TEXT')",
        schema="story",
    )
    op.drop_column("run_inputs", "transcript_revision_id", schema="story")
    op.drop_column("run_inputs", "audio_input_id", schema="story")
    op.drop_table("transcript_revisions", schema="story")
    op.drop_index("ix_story_run_audio_asset", table_name="run_audio_inputs", schema="story")
    op.drop_table("run_audio_inputs", schema="story")
