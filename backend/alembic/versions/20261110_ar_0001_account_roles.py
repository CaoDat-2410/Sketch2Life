"""Persist server-managed account roles on BE1 adult identities."""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "20261110_ar_0001"
down_revision = "20261028_ll_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "be1_adult_identities",
        sa.Column("account_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "be1_adult_identities",
        sa.Column("account_role", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "be1_adult_identities",
        sa.Column("role_revision", sa.Integer(), server_default="1", nullable=True),
    )

    connection = op.get_bind()
    subjects = connection.execute(
        sa.text("SELECT subject FROM be1_adult_identities WHERE account_id IS NULL")
    ).scalars().all()
    for subject in subjects:
        connection.execute(
            sa.text(
                "UPDATE be1_adult_identities SET account_id = :account_id "
                "WHERE subject = :subject"
            ),
            {"account_id": str(uuid4()), "subject": subject},
        )

    connection.execute(
        sa.text(
            "WITH role_candidates AS ("
            " SELECT subject, "
            "   CASE WHEN role = 'school_admin' THEN 'school_manager' ELSE 'teacher' END AS account_role "
            " FROM be1_organization_assignments "
            " WHERE active IS TRUE AND role IN ('school_admin', 'teacher', 'guide', 'observer')"
            "), unique_roles AS ("
            " SELECT subject, MIN(account_role) AS account_role "
            " FROM role_candidates GROUP BY subject "
            " HAVING COUNT(DISTINCT account_role) = 1"
            ") UPDATE be1_adult_identities AS identity "
            "SET account_role = unique_roles.account_role "
            "FROM unique_roles WHERE identity.subject = unique_roles.subject"
        )
    )

    op.alter_column("be1_adult_identities", "account_id", nullable=False)
    op.alter_column(
        "be1_adult_identities", "role_revision", nullable=False, server_default="1"
    )
    op.create_unique_constraint(
        "uq_be1_adult_identity_account_id", "be1_adult_identities", ["account_id"]
    )
    op.create_check_constraint(
        "ck_be1_adult_identity_account_role",
        "be1_adult_identities",
        "account_role IS NULL OR account_role IN "
        "('parent', 'teacher', 'school_manager', 'platform_admin')",
    )
    op.create_check_constraint(
        "ck_be1_adult_identity_role_revision",
        "be1_adult_identities",
        "role_revision > 0",
    )
    op.create_index(
        "ix_be1_adult_identity_role_state",
        "be1_adult_identities",
        ["account_role", "state"],
    )


def downgrade() -> None:
    op.drop_index("ix_be1_adult_identity_role_state", table_name="be1_adult_identities")
    op.drop_constraint(
        "ck_be1_adult_identity_role_revision", "be1_adult_identities", type_="check"
    )
    op.drop_constraint(
        "ck_be1_adult_identity_account_role", "be1_adult_identities", type_="check"
    )
    op.drop_constraint(
        "uq_be1_adult_identity_account_id", "be1_adult_identities", type_="unique"
    )
    op.drop_column("be1_adult_identities", "role_revision")
    op.drop_column("be1_adult_identities", "account_role")
    op.drop_column("be1_adult_identities", "account_id")
