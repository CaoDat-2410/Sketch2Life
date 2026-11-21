"""Durable lesson-scoped feedback threads and immutable messages."""

from alembic import op

revision = "20261119_admin_feedback"
down_revision = "20261119_admin_billing"
branch_labels = None
depends_on = None


def upgrade():
    from sketch2life.infrastructure.lesson_library.feedback_tables import (
        FEEDBACK_MESSAGES,
        FEEDBACK_THREADS,
    )

    FEEDBACK_THREADS.create(op.get_bind())
    FEEDBACK_MESSAGES.create(op.get_bind())


def downgrade():
    raise RuntimeError("Feedback deletion requires a retention-aware lifecycle operation")
