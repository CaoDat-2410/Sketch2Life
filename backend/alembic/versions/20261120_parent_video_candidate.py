"""Persist one synthetic-only Parent LTX candidate per StoryRun."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261120_parent_video_candidate"
down_revision = "20261114_parent_activity_selection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_candidate_jobs",
        sa.Column("video_candidate_id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("owner_issuer", sa.String(64), nullable=False),
        sa.Column("owner_subject", sa.String(128), nullable=False),
        sa.Column("story_revision_id", sa.String(36), nullable=False),
        sa.Column("story_revision_no", sa.Integer(), nullable=False),
        sa.Column("story_sha256", sa.String(64), nullable=False),
        sa.Column("source_asset_ref", sa.String(256), nullable=False),
        sa.Column("source_asset_version", sa.Integer(), nullable=False),
        sa.Column("source_asset_sha256", sa.String(64), nullable=False),
        sa.Column("source_media_type", sa.String(32), nullable=False),
        sa.Column("activity_selection_id", sa.String(36), nullable=False),
        sa.Column("activity_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("request_fingerprint_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("modal_call_id", sa.String(128), nullable=True),
        sa.Column("job_id", sa.String(80), nullable=False),
        sa.Column("generation_id", sa.String(80), nullable=False),
        sa.Column("attempt_id", sa.String(80), nullable=False),
        sa.Column("attempt_prefix", sa.String(256), nullable=False),
        sa.Column("output_asset_ref", sa.String(256), nullable=True),
        sa.Column("output_sha256", sa.String(64), nullable=True),
        sa.Column("output_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("output_manifest_sha256", sa.String(64), nullable=True),
        sa.Column("output_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("safe_failure_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_story_video_candidate_run"),
        sa.ForeignKeyConstraint(["run_id", "story_revision_id"], ["story.story_revisions.run_id", "story.story_revisions.story_revision_id"], ondelete="CASCADE", name="fk_story_video_candidate_revision_owner"),
        sa.ForeignKeyConstraint(["activity_selection_id"], ["story.parent_activity_selections.activity_selection_id"], ondelete="RESTRICT", name="fk_story_video_candidate_activity_selection"),
        sa.PrimaryKeyConstraint("video_candidate_id", name="pk_story_video_candidate_jobs"),
        sa.UniqueConstraint("run_id", name="uq_story_video_candidate_run"),
        sa.UniqueConstraint("run_id", "idempotency_key_sha256", name="uq_story_video_candidate_idempotency"),
        sa.CheckConstraint("state IN ('STAGING','DISPATCHING','QUEUED','GENERATING','CANDIDATE_READY','FAILED','AWAITING_RECONCILIATION')", name="ck_story_video_candidate_state"),
        sa.CheckConstraint("story_revision_no BETWEEN 1 AND 4", name="ck_story_video_candidate_story_revision"),
        sa.CheckConstraint("source_asset_version > 0", name="ck_story_video_candidate_source_version"),
        sa.CheckConstraint("length(story_sha256) = 64 AND length(source_asset_sha256) = 64", name="ck_story_video_candidate_input_hashes"),
        sa.CheckConstraint("length(activity_snapshot_sha256) = 64", name="ck_story_video_candidate_activity_hash"),
        sa.CheckConstraint("length(idempotency_key_sha256) = 64 AND length(request_fingerprint_sha256) = 64", name="ck_story_video_candidate_request_hashes"),
        sa.CheckConstraint("output_sha256 IS NULL OR length(output_sha256) = 64", name="ck_story_video_candidate_output_hash"),
        sa.CheckConstraint("output_manifest_sha256 IS NULL OR length(output_manifest_sha256) = 64", name="ck_story_video_candidate_manifest_hash"),
        sa.CheckConstraint("output_size_bytes IS NULL OR output_size_bytes BETWEEN 1 AND 268435456", name="ck_story_video_candidate_output_size"),
        sa.CheckConstraint("(state = 'CANDIDATE_READY' AND output_asset_ref IS NOT NULL AND output_sha256 IS NOT NULL AND output_manifest_sha256 IS NOT NULL AND output_size_bytes IS NOT NULL AND safe_failure_code IS NULL) OR (state != 'CANDIDATE_READY' AND output_asset_ref IS NULL AND output_sha256 IS NULL AND output_manifest_sha256 IS NULL AND output_size_bytes IS NULL)", name="ck_story_video_candidate_ready_shape"),
        sa.CheckConstraint("(state = 'FAILED' AND safe_failure_code IS NOT NULL) OR (state != 'FAILED' AND safe_failure_code IS NULL)", name="ck_story_video_candidate_failure_shape"),
        schema="story",
    )
    op.create_index(
        "ix_story_video_candidate_state_updated",
        "video_candidate_jobs",
        ["state", "updated_at"],
        schema="story",
    )


def downgrade() -> None:
    raise RuntimeError(
        "No automatic downgrade: synthetic video candidates may be in use. "
        "Preserve/export Story data and use a separately reviewed forward repair."
    )
