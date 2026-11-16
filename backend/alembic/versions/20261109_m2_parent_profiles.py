"""Create the isolated Parent-owned profile foundation."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261109_m2_parent_profiles"
down_revision = None
branch_labels = ("parent",)
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA parent"))
    op.create_table(
        "child_profiles",
        sa.Column("parent_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_issuer", sa.Text(), nullable=False),
        sa.Column("owner_subject", sa.Text(), nullable=False),
        sa.Column(
            "state", sa.String(length=16), server_default=sa.text("'ACTIVE'"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("current_revision_no", sa.BigInteger(), nullable=False),
        sa.Column(
            "data_origin",
            sa.String(length=32),
            server_default=sa.text("'SYNTHETIC_DEV'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_revision_no > 0",
            name="ck_parent_child_profiles_current_revision_no_positive",
        ),
        sa.CheckConstraint(
            "data_origin = 'SYNTHETIC_DEV'",
            name="ck_parent_child_profiles_data_origin_synthetic_dev",
        ),
        sa.PrimaryKeyConstraint("parent_profile_id", name="pk_parent_child_profiles"),
        schema="parent",
    )
    op.create_table(
        "profile_revisions",
        sa.Column("profile_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_no", sa.BigInteger(), nullable=False),
        sa.Column("age_months", sa.SmallInteger(), nullable=False),
        sa.Column("age_band_ref", sa.Text(), nullable=True),
        sa.Column("age_band_version", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("interests_summary", sa.String(length=2000), nullable=True),
        sa.Column("authored_by_issuer", sa.Text(), nullable=False),
        sa.Column("authored_by_subject", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revision_hash", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "revision_no > 0",
            name="ck_parent_profile_revisions_revision_no_positive",
        ),
        sa.CheckConstraint(
            "age_months BETWEEN 36 AND 120",
            name="ck_parent_profile_revisions_age_months_36_120",
        ),
        sa.CheckConstraint(
            "(age_band_ref IS NULL AND age_band_version IS NULL) OR "
            "(age_band_ref IS NOT NULL AND age_band_version IS NOT NULL)",
            name="ck_parent_profile_revisions_age_band_pair",
        ),
        sa.CheckConstraint(
            "revision_hash ~ '^[0-9a-f]{64}$'",
            name="ck_parent_profile_revisions_revision_hash_sha256",
        ),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_profile_revisions_parent_profile",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("profile_revision_id", name="pk_parent_profile_revisions"),
        sa.UniqueConstraint(
            "parent_profile_id",
            "revision_no",
            name="uq_parent_profile_revisions_parent_revision_no",
        ),
        schema="parent",
    )
    op.create_table(
        "command_receipts",
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("principal_issuer", sa.Text(), nullable=False),
        sa.Column("principal_subject", sa.Text(), nullable=False),
        sa.Column("operation_scope", sa.Text(), nullable=False),
        sa.Column("resource_scope", sa.Text(), nullable=False),
        sa.Column("key_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("request_fingerprint", postgresql.BYTEA(), nullable=False),
        sa.Column("response_status", sa.SmallInteger(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "octet_length(key_hash) = 32",
            name="ck_parent_command_receipts_key_hash_len",
        ),
        sa.CheckConstraint(
            "octet_length(request_fingerprint) = 32",
            name="ck_parent_command_receipts_fingerprint_len",
        ),
        sa.PrimaryKeyConstraint("receipt_id", name="pk_parent_command_receipts"),
        sa.UniqueConstraint(
            "principal_issuer",
            "principal_subject",
            "operation_scope",
            "resource_scope",
            "key_hash",
            name="uq_parent_command_receipts_scope_key",
        ),
        schema="parent",
    )
    op.create_index(
        "ix_parent_command_receipts_owner_created_at",
        "command_receipts",
        ["principal_issuer", "principal_subject", "created_at"],
        schema="parent",
    )
    op.create_foreign_key(
        "fk_parent_child_profiles_current_revision",
        "child_profiles",
        "profile_revisions",
        ["parent_profile_id", "current_revision_no"],
        ["parent_profile_id", "revision_no"],
        source_schema="parent",
        referent_schema="parent",
        deferrable=True,
        initially="DEFERRED",
    )
    op.execute(
        sa.text(
            "CREATE FUNCTION parent.reject_profile_revision_mutation() "
            "RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'Parent profile revisions are immutable' "
            "USING ERRCODE = 'integrity_constraint_violation'; END; $$"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_parent_profile_revisions_immutable "
            "BEFORE UPDATE OR DELETE ON parent.profile_revisions "
            "FOR EACH ROW EXECUTE FUNCTION parent.reject_profile_revision_mutation()"
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_parent_command_receipts_owner_created_at",
        table_name="command_receipts",
        schema="parent",
    )
    op.drop_table("command_receipts", schema="parent")
    op.execute(
        sa.text(
            "DROP TRIGGER trg_parent_profile_revisions_immutable "
            "ON parent.profile_revisions"
        )
    )
    op.execute(sa.text("DROP FUNCTION parent.reject_profile_revision_mutation()"))
    op.drop_constraint(
        "fk_parent_child_profiles_current_revision",
        "child_profiles",
        schema="parent",
        type_="foreignkey",
    )
    op.drop_table("profile_revisions", schema="parent")
    op.drop_table("child_profiles", schema="parent")
    op.execute(sa.text("DROP SCHEMA parent"))
