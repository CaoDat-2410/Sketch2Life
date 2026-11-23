"""DDL-B1c: the story review epoch, so a spent review can be confirmed again.

FEAT-066 goal v4, T-1b-fix (SRS l.406, l.416, l.1669, l.1728, l.2120; BR-11, BR-14, BR-16). The
package is approved by name (owner decision B1, DDL-B1c). It extends the Story chain on its own
branch: the parent is ``20261123_as_0001`` (DDL-B3), the only head of that chain, which this
revision replaces as its head (the label is inherited, so none is declared and ``depends_on`` is
not used). Alembic heads stay 15 down-only (10 dependency-aware); 51 revisions.

A story revision stays immutable (BR-14). A video request consumes the review of the latest
revision; when that request ends without a usable video the review is spent, and the adult may keep
the current story and confirm it again. That is a NEW review row of the same revision with the next
``review_epoch`` (1..3, one per accepted request). Review rows are never updated.

Upgrade, in order, on ``story.story_revision_reviews``:

1. ``review_epoch smallint NOT NULL DEFAULT 1`` (the default is the backfill);
2. ``UNIQUE (story_revision_id, review_epoch)`` named ``uq_story_revision_review_epoch``;
3. ``uq_story_revision_review_once`` is dropped (nothing references it; the one inbound foreign key
   of the video table targets ``uq_story_review_run_revision``, which stays);
4. ``CHECK (review_epoch BETWEEN 1 AND 3)`` named ``ck_story_revision_review_epoch``.

``ck_story_receipt_operation`` is NOT touched: a re-confirmation reuses ``CONFIRM_STORY_REVISION``.

The downgrade refuses while any review row has ``review_epoch`` greater than 1, then restores the
old unique, drops the new unique and the check, and drops the column. Run it with an explicit
target, never ``-1`` (the graph has many heads), on a disposable database only:
``alembic downgrade 20261123_as_0001``, then ``alembic upgrade heads``. Never run against
``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261123_rv_0001"
down_revision = "20261123_as_0001"
branch_labels = None
depends_on = None

SCHEMA = "story"
TABLE = "story_revision_reviews"
COLUMN = "review_epoch"
OLD_UNIQUE = "uq_story_revision_review_once"
NEW_UNIQUE = "uq_story_revision_review_epoch"
CHECK_NAME = "ck_story_revision_review_epoch"
CHECK_EXPRESSION = "review_epoch BETWEEN 1 AND 3"

DOWNGRADE_GUARD = f"""
DO $rv_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE} WHERE {COLUMN} > 1) THEN
        RAISE EXCEPTION 'DDL-B1c downgrade refused: re-confirmation reviews exist';
    END IF;
END;
$rv_downgrade_guard$;
"""


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column(COLUMN, sa.SmallInteger, nullable=False, server_default=sa.text("1")),
        schema=SCHEMA,
    )
    op.create_unique_constraint(NEW_UNIQUE, TABLE, ["story_revision_id", COLUMN], schema=SCHEMA)
    op.drop_constraint(OLD_UNIQUE, TABLE, schema=SCHEMA, type_="unique")
    op.create_check_constraint(CHECK_NAME, TABLE, CHECK_EXPRESSION, schema=SCHEMA)


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.create_unique_constraint(OLD_UNIQUE, TABLE, ["story_revision_id"], schema=SCHEMA)
    op.drop_constraint(CHECK_NAME, TABLE, schema=SCHEMA, type_="check")
    op.drop_constraint(NEW_UNIQUE, TABLE, schema=SCHEMA, type_="unique")
    op.drop_column(TABLE, COLUMN, schema=SCHEMA)
