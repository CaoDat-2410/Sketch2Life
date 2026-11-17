"""Add BE1 profile data origin and the FEAT-064 synthetic eligibility proof table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261031_be1_se_0001"
down_revision = "20261024_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing rows are classified only through the new column; their consent references stay.
    op.add_column(
        "be1_managed_profiles",
        sa.Column(
            "data_origin",
            sa.String(24),
            server_default="LEGACY_UNCLASSIFIED",
            nullable=False,
        ),
    )
    op.alter_column("be1_managed_profiles", "data_origin", server_default=None)
    op.alter_column(
        "be1_managed_profiles", "consent_id", existing_type=sa.String(36), nullable=True
    )
    op.alter_column(
        "be1_managed_profiles", "consent_purpose_ref", existing_type=sa.String(128), nullable=True
    )
    op.create_check_constraint(
        "ck_be1_profile_data_origin",
        "be1_managed_profiles",
        "data_origin IN ('REAL', 'SYNTHETIC_DEV', 'LEGACY_UNCLASSIFIED')",
    )
    op.create_check_constraint(
        "ck_be1_profile_origin_consent_refs",
        "be1_managed_profiles",
        "(data_origin = 'REAL' AND consent_id IS NOT NULL AND consent_purpose_ref IS NOT NULL)"
        " OR (data_origin = 'SYNTHETIC_DEV' AND consent_id IS NULL"
        " AND consent_purpose_ref IS NULL)"
        " OR data_origin = 'LEGACY_UNCLASSIFIED'",
    )
    op.create_table(
        "be1_synthetic_eligibility_proofs",
        sa.Column("evidence_id", sa.String(64), primary_key=True),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("data_origin", sa.String(24), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("class_id", sa.String(128), nullable=False),
        sa.Column("child_profile_id", sa.String(128), nullable=False),
        sa.Column("purpose_ref", sa.String(128), nullable=False),
        sa.Column("run_ref", sa.String(128), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("issued_by", sa.String(256), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_revision", sa.Integer(), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["be1_organizations.organization_id"],
            name="fk_be1_synth_proof_organization",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["child_profile_id"],
            ["be1_managed_profiles.child_id"],
            name="fk_be1_synth_proof_profile",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("data_origin = 'SYNTHETIC_DEV'", name="ck_be1_synth_proof_origin"),
        sa.CheckConstraint("expires_at > issued_at", name="ck_be1_synth_proof_interval"),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND revocation_revision = 0)"
            " OR (revoked_at IS NOT NULL AND revocation_revision > 0)",
            name="ck_be1_synth_proof_revocation",
        ),
    )
    op.create_index(
        "ix_be1_synth_proof_scope",
        "be1_synthetic_eligibility_proofs",
        ["organization_id", "class_id", "child_profile_id", "purpose_ref"],
    )


def downgrade() -> None:
    # Fail closed: never discard synthetic evidence, or profiles that cannot satisfy the old schema.
    bind = op.get_bind()
    blockers = bind.execute(
        sa.text(
            "SELECT"
            " (SELECT count(*) FROM be1_synthetic_eligibility_proofs),"
            " (SELECT count(*) FROM be1_managed_profiles WHERE data_origin = 'SYNTHETIC_DEV'),"
            " (SELECT count(*) FROM be1_managed_profiles"
            "  WHERE consent_id IS NULL OR consent_purpose_ref IS NULL)"
        )
    ).one()
    if any(blockers):
        raise RuntimeError(
            "Downgrade refused: synthetic eligibility proofs, SYNTHETIC_DEV profiles or profiles"
            " without consent references exist. Remove or archive them deliberately first."
        )
    op.drop_index("ix_be1_synth_proof_scope", table_name="be1_synthetic_eligibility_proofs")
    op.drop_table("be1_synthetic_eligibility_proofs")
    op.drop_constraint("ck_be1_profile_origin_consent_refs", "be1_managed_profiles", type_="check")
    op.drop_constraint("ck_be1_profile_data_origin", "be1_managed_profiles", type_="check")
    op.alter_column(
        "be1_managed_profiles", "consent_purpose_ref", existing_type=sa.String(128), nullable=False
    )
    op.alter_column(
        "be1_managed_profiles", "consent_id", existing_type=sa.String(36), nullable=False
    )
    op.drop_column("be1_managed_profiles", "data_origin")
