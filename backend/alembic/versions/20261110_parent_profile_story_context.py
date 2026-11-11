"""Add Parent-owned profiles, versioned data authorization, and StoryRun context snapshots."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261110_parent_profile_story_context"
down_revision = (
    "20261015_ai_0001",
    "20261018_ap_0009",
    "20261017_lc_0001",
    "20261018_kv_0001",
    "20261018_vr_0001",
    "20261019_ae_0001",
    "20261019_pa_0001",
    "20261019_vf_0001",
    "20261101_be1_age_0001",
    "20261102_pv_0001",
    "20261104_story_revisions",
    "20261110_ar_0001",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS parent")
    op.create_table(
        "child_profiles",
        sa.Column("parent_profile_id", sa.String(36), primary_key=True),
        sa.Column("owner_subject", sa.String(256), nullable=False),
        sa.Column("state", sa.String(16), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("current_revision_ref", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("state IN ('ACTIVE','ARCHIVED','DELETED')", name="ck_parent_child_profile_state"),
        sa.UniqueConstraint("parent_profile_id", "owner_subject", name="uq_parent_profile_owner_ref"),
        schema="parent",
    )
    op.create_table(
        "profile_revisions",
        sa.Column("profile_revision_id", sa.String(36), primary_key=True),
        sa.Column("parent_profile_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("age_months", sa.Integer(), nullable=False),
        sa.Column("age_band_ref", sa.String(80), nullable=True),
        sa.Column("age_band_version", sa.String(64), nullable=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("interests_summary", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("authored_by", sa.String(256), nullable=False),
        sa.Column("revision_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("age_months BETWEEN 36 AND 120", name="ck_parent_profile_revision_age_months"),
        sa.CheckConstraint("revision_no > 0", name="ck_parent_profile_revision_no"),
        sa.CheckConstraint("length(trim(display_name)) BETWEEN 1 AND 120", name="ck_parent_profile_revision_display_name"),
        sa.CheckConstraint("length(interests_summary) <= 800", name="ck_parent_profile_revision_interests_length"),
        sa.CheckConstraint("length(revision_hash) = 64", name="ck_parent_profile_revision_hash"),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"], ["parent.child_profiles.parent_profile_id"],
            ondelete="RESTRICT", name="fk_parent_profile_revision_profile",
        ),
        sa.UniqueConstraint("parent_profile_id", "revision_no", name="uq_parent_profile_revision_no"),
        sa.UniqueConstraint("parent_profile_id", "profile_revision_id", name="uq_parent_profile_revision_owner"),
        schema="parent",
    )
    op.create_foreign_key(
        "fk_parent_profile_current_revision",
        "child_profiles",
        "profile_revisions",
        ["parent_profile_id", "current_revision_ref"],
        ["parent_profile_id", "profile_revision_id"],
        source_schema="parent",
        referent_schema="parent",
    )
    op.create_table(
        "data_authorizations",
        sa.Column("authorization_id", sa.String(36), primary_key=True),
        sa.Column("parent_profile_id", sa.String(36), nullable=False),
        sa.Column("actor_subject", sa.String(256), nullable=False),
        sa.Column("purpose_code", sa.String(64), server_default=sa.text("'PARENT_STORY_PERSONALIZATION'"), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("source_kind", sa.String(48), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_ref", sa.String(64), nullable=False),
        sa.Column("synthetic_demo_flag", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("purpose_code = 'PARENT_STORY_PERSONALIZATION'", name="ck_parent_authorization_purpose"),
        sa.CheckConstraint("state IN ('GRANTED','REVOKED','EXPIRED')", name="ck_parent_authorization_state"),
        sa.CheckConstraint("length(policy_version) BETWEEN 1 AND 80", name="ck_parent_authorization_policy_version"),
        sa.CheckConstraint("length(evidence_ref) = 64", name="ck_parent_authorization_evidence_hash"),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"], ["parent.child_profiles.parent_profile_id"],
            ondelete="RESTRICT", name="fk_parent_authorization_profile",
        ),
        schema="parent",
    )
    op.create_index(
        "uq_parent_authorization_active_policy",
        "data_authorizations",
        ["parent_profile_id", "purpose_code", "policy_version"],
        unique=True,
        schema="parent",
        postgresql_where=sa.text("state = 'GRANTED'"),
    )
    op.create_index(
        "ix_parent_authorization_profile_state",
        "data_authorizations",
        ["parent_profile_id", "state"],
        schema="parent",
    )
    op.create_index(
        "ix_parent_profile_owner_state_updated",
        "child_profiles",
        ["owner_subject", "state", "updated_at"],
        schema="parent",
    )

    op.add_column("runs", sa.Column("current_input_revision", sa.Integer(), nullable=True), schema="story")
    op.create_check_constraint(
        "ck_story_run_current_input_revision",
        "runs",
        "current_input_revision IS NULL OR current_input_revision > 0",
        schema="story",
    )
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state",
        "runs",
        "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW',"
        "'SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
        "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED','COMPLETED')",
        schema="story",
    )

    for column in (
        "original_asset_ref", "original_asset_version", "original_sha256",
        "original_media_type", "original_size_bytes", "derived_asset_ref",
        "derived_asset_version", "derived_sha256", "derived_media_type", "derived_size_bytes",
    ):
        op.alter_column("run_inputs", column, schema="story", existing_nullable=False, nullable=True)
    op.drop_constraint("ck_story_run_input_versions", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_hashes", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_sizes", "run_inputs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_input_versions",
        "run_inputs",
        "input_revision > 0 AND ((original_asset_ref IS NULL AND original_asset_version IS NULL "
        "AND original_sha256 IS NULL AND original_media_type IS NULL AND original_size_bytes IS NULL "
        "AND derived_asset_ref IS NULL AND derived_asset_version IS NULL AND derived_sha256 IS NULL "
        "AND derived_media_type IS NULL AND derived_size_bytes IS NULL) OR "
        "(original_asset_ref IS NOT NULL AND original_asset_version IS NOT NULL "
        "AND original_asset_version > 0 AND original_sha256 IS NOT NULL "
        "AND original_media_type IS NOT NULL AND original_size_bytes IS NOT NULL "
        "AND original_size_bytes > 0 AND derived_asset_ref IS NOT NULL "
        "AND derived_asset_version IS NOT NULL AND derived_asset_version > 0 "
        "AND derived_sha256 IS NOT NULL AND derived_media_type IS NOT NULL "
        "AND derived_size_bytes IS NOT NULL AND derived_size_bytes > 0))",
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_hashes",
        "run_inputs",
        "(original_sha256 IS NULL AND derived_sha256 IS NULL) OR "
        "(original_sha256 IS NOT NULL AND derived_sha256 IS NOT NULL "
        "AND length(original_sha256) = 64 AND length(derived_sha256) = 64)",
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_sizes",
        "run_inputs",
        "(original_size_bytes IS NULL AND derived_size_bytes IS NULL) OR "
        "(original_size_bytes IS NOT NULL AND derived_size_bytes IS NOT NULL "
        "AND original_size_bytes BETWEEN 1 AND 20971520 "
        "AND derived_size_bytes BETWEEN 1 AND 5000000)",
        schema="story",
    )
    op.add_column("run_inputs", sa.Column("source_profile_revision_ref", sa.String(36), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("typed_idea", sa.String(500), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("idea_source", sa.String(16), nullable=True), schema="story")
    op.create_check_constraint(
        "ck_story_run_input_typed_idea",
        "run_inputs",
        "(typed_idea IS NULL AND idea_source IS NULL) OR "
        "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 AND idea_source = 'TEXT')",
        schema="story",
    )
    op.add_column("run_inputs", sa.Column("data_authorization_id", sa.String(36), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("context_revision", sa.Integer(), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("context_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("context_snapshot_sha256", sa.String(64), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("context_confirmed_by", sa.String(256), nullable=True), schema="story")
    op.add_column("run_inputs", sa.Column("context_confirmed_at", sa.DateTime(timezone=True), nullable=True), schema="story")
    op.create_foreign_key(
        "fk_story_run_input_profile_revision",
        "run_inputs",
        "profile_revisions",
        ["source_profile_revision_ref"],
        ["profile_revision_id"],
        source_schema="story",
        referent_schema="parent",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_story_run_input_data_authorization",
        "run_inputs",
        "data_authorizations",
        ["data_authorization_id"],
        ["authorization_id"],
        source_schema="story",
        referent_schema="parent",
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_story_run_input_parent_context",
        "run_inputs",
        "(context_snapshot IS NULL AND context_snapshot_sha256 IS NULL AND context_revision IS NULL "
        "AND source_profile_revision_ref IS NULL AND data_authorization_id IS NULL "
        "AND context_confirmed_by IS NULL AND context_confirmed_at IS NULL) OR "
        "(context_snapshot IS NOT NULL AND context_snapshot_sha256 IS NOT NULL "
        "AND length(context_snapshot_sha256) = 64 AND context_revision IS NOT NULL "
        "AND context_revision > 0 "
        "AND source_profile_revision_ref IS NOT NULL AND data_authorization_id IS NOT NULL "
        "AND context_confirmed_by IS NOT NULL AND context_confirmed_at IS NOT NULL "
        "AND octet_length(context_snapshot::text) <= 8192)",
        schema="story",
    )


def downgrade() -> None:
    connection = op.get_bind()
    profile_rows = connection.execute(sa.text("SELECT EXISTS (SELECT 1 FROM parent.child_profiles)")).scalar()
    context_rows = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM story.run_inputs WHERE context_snapshot IS NOT NULL)")
    ).scalar()
    if profile_rows or context_rows:
        raise RuntimeError("Parent profile and StoryRun context data must be exported before downgrade")

    op.drop_constraint("ck_story_run_input_parent_context", "run_inputs", schema="story", type_="check")
    op.drop_constraint(
        "fk_story_run_input_data_authorization", "run_inputs", schema="story", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_story_run_input_profile_revision", "run_inputs", schema="story", type_="foreignkey"
    )
    for column in (
        "context_confirmed_at", "context_confirmed_by", "context_snapshot_sha256",
        "context_snapshot", "context_revision", "data_authorization_id", "source_profile_revision_ref",
    ):
        op.drop_column("run_inputs", column, schema="story")
    op.drop_constraint("ck_story_run_input_typed_idea", "run_inputs", schema="story", type_="check")
    op.drop_column("run_inputs", "idea_source", schema="story")
    op.drop_column("run_inputs", "typed_idea", schema="story")
    op.drop_constraint("ck_story_run_input_versions", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_hashes", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_sizes", "run_inputs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_input_versions", "run_inputs",
        "input_revision > 0 AND original_asset_version > 0 AND derived_asset_version > 0", schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_hashes", "run_inputs",
        "length(original_sha256) = 64 AND length(derived_sha256) = 64", schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_sizes", "run_inputs",
        "original_size_bytes BETWEEN 1 AND 20971520 AND derived_size_bytes BETWEEN 1 AND 5000000", schema="story",
    )
    for column in (
        "original_asset_ref", "original_asset_version", "original_sha256", "original_media_type",
        "original_size_bytes", "derived_asset_ref", "derived_asset_version", "derived_sha256",
        "derived_media_type", "derived_size_bytes",
    ):
        op.alter_column("run_inputs", column, schema="story", existing_nullable=True, nullable=False)
    op.drop_constraint("ck_story_run_current_input_revision", "runs", schema="story", type_="check")
    op.drop_column("runs", "current_input_revision", schema="story")
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state", "runs",
        "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW',"
        "'SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
        "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED')", schema="story",
    )

    op.drop_index("ix_parent_profile_owner_state_updated", table_name="child_profiles", schema="parent")
    op.drop_index("ix_parent_authorization_profile_state", table_name="data_authorizations", schema="parent")
    op.drop_index("uq_parent_authorization_active_policy", table_name="data_authorizations", schema="parent")
    op.drop_table("data_authorizations", schema="parent")
    op.drop_constraint("fk_parent_profile_current_revision", "child_profiles", schema="parent", type_="foreignkey")
    op.drop_table("profile_revisions", schema="parent")
    op.drop_table("child_profiles", schema="parent")
