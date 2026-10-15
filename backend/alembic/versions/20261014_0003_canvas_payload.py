"""Persist bounded, attributed canvas operation payloads for real sync requests."""

from __future__ import annotations

from alembic import op

revision = "20261014_0003"
down_revision = "20261014_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE core_canvas_operations "
        "ADD COLUMN operation_payload jsonb NOT NULL DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE core_canvas_operations DROP COLUMN operation_payload")
