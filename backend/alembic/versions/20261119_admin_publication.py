"""Allow platform-owned reusable lessons and preserve independent review evidence."""

import sqlalchemy as sa

from alembic import op

revision = "20261119_admin_publication"
down_revision = "20261119_admin_foundation"
branch_labels = None
depends_on = "20261017_lc_0001"


def upgrade():
    op.add_column(
        "review",
        sa.Column("permission_revision", sa.Integer, nullable=True),
        schema="learning_content",
    )
    op.drop_constraint("ck_lesson_owner_kind", "library_items", schema="lesson", type_="check")
    op.alter_column("library_items", "organization_id", schema="lesson", nullable=True)
    op.create_check_constraint(
        "ck_lesson_owner_kind",
        "library_items",
        "owner_kind IN ('ORGANIZATION','PLATFORM')",
        schema="lesson",
    )
    op.create_check_constraint(
        "ck_lesson_owner_scope",
        "library_items",
        "(owner_kind = 'PLATFORM' AND organization_id IS NULL) OR "
        "(owner_kind = 'ORGANIZATION' AND organization_id IS NOT NULL)",
        schema="lesson",
    )
    from sketch2life.infrastructure.lesson_library.publication_tables import PUBLICATION_REVIEWS

    PUBLICATION_REVIEWS.create(op.get_bind())


def downgrade():
    raise RuntimeError("Published versions and review evidence require a retention-aware migration")
