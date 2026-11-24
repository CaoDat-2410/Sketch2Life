"""Store versioned Parent consent policies managed by Platform Admin."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261113_parent_consent_policy"
down_revision = "20261112_parent_audio_transcripts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consent_policies",
        sa.Column("policy_id", sa.String(36), primary_key=True),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("purpose_code", sa.String(80), nullable=False),
        sa.Column("consent_text", sa.Text(), nullable=False),
        sa.Column("consent_text_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), server_default=sa.text("'DRAFT'"), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("activated_by", sa.String(256), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_parent_consent_policy_state",
        ),
        sa.CheckConstraint(
            "purpose_code = 'PARENT_STORY_PERSONALIZATION'",
            name="ck_parent_consent_policy_purpose",
        ),
        sa.CheckConstraint(
            "length(trim(consent_text)) BETWEEN 1 AND 4000",
            name="ck_parent_consent_policy_text_length",
        ),
        sa.CheckConstraint(
            "length(consent_text_sha256) = 64",
            name="ck_parent_consent_policy_text_sha256",
        ),
        sa.UniqueConstraint("policy_version", name="uq_parent_consent_policy_version"),
        schema="parent",
    )
    op.create_index(
        "uq_parent_consent_policy_one_active",
        "consent_policies",
        ["state"],
        unique=True,
        schema="parent",
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.create_index(
        "ix_parent_consent_policy_state_created",
        "consent_policies",
        ["state", "created_at"],
        schema="parent",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_parent_consent_policy_state_created",
        table_name="consent_policies",
        schema="parent",
    )
    op.drop_index(
        "uq_parent_consent_policy_one_active",
        table_name="consent_policies",
        schema="parent",
    )
    op.drop_table("consent_policies", schema="parent")
