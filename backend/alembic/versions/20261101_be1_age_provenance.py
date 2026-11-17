"""Persist profile age provenance and its revision."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261101_be1_age_0001"
down_revision = "20261031_be1_se_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("be1_managed_profiles", sa.Column("age_revision", sa.Integer(), nullable=True))
    op.add_column("be1_managed_profiles", sa.Column("age_source", sa.String(24), nullable=True))
    op.execute(
        sa.text(
            "UPDATE be1_managed_profiles "
            "SET age_revision = 1, age_source = 'LEGACY_UNKNOWN' "
            "WHERE age_revision IS NULL OR age_source IS NULL"
        )
    )
    op.alter_column(
        "be1_managed_profiles",
        "age_revision",
        existing_type=sa.Integer(),
        server_default="1",
        nullable=False,
    )
    op.alter_column(
        "be1_managed_profiles",
        "age_source",
        existing_type=sa.String(24),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_be1_profile_age_revision", "be1_managed_profiles", "age_revision >= 1"
    )
    op.create_check_constraint(
        "ck_be1_profile_age_source",
        "be1_managed_profiles",
        "age_source IN ('LEGACY_UNKNOWN', 'SYNTHETIC_FIXTURE', 'ADULT_DECLARED')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_be1_profile_age_source", "be1_managed_profiles", type_="check")
    op.drop_constraint("ck_be1_profile_age_revision", "be1_managed_profiles", type_="check")
    op.drop_column("be1_managed_profiles", "age_source")
    op.drop_column("be1_managed_profiles", "age_revision")
