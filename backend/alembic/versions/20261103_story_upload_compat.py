"""Relocate an already-applied legacy Story upload layout without copying rows."""

from alembic import context, op
from sketch2life.infrastructure.story_run_lite.migration_compat import relocate_story_upload_tables

revision = "20261103_story_upload_compat"
down_revision = "20261102_story_run_lite"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError("Story upload compatibility requires online PostgreSQL validation")
    relocate_story_upload_tables(op.get_bind(), required=True)


def downgrade() -> None:
    # Reusing the old public names would collide with Lesson Library and could
    # make a mixed database appear compatible with the historical Story app.
    raise RuntimeError("Story upload compatibility migration is not reversible")
