"""FEAT-093: progress and captions of a Parent video generation.

One row per generation, written by the video worker (stage, scene index and count, start and update time) and, when the
video is ready, its WebVTT captions and cues. The row is derived data: it cascades with the generation and holds no child
content other than the adult-approved narration text of the captions. Parent: ``20261123_rv_0001`` (the Story chain head).
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "20261125_vp_0001"
down_revision = "20261123_rv_0001"
branch_labels = None
depends_on = None

SCHEMA = "story"
TABLE = "video_generation_progress"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "video_generation_id",
            sa.String(36),
            sa.ForeignKey(f"{SCHEMA}.video_generations.video_generation_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("stage", sa.String(24), nullable=False),
        sa.Column("scene_index", sa.SmallInteger),
        sa.Column("scene_count", sa.SmallInteger, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("captions_vtt", sa.Text),
        sa.Column("cues", JSONB),
        sa.CheckConstraint(
            "stage IN ('PLANNING','PREPARING_SCENES','RENDERING','NARRATING','ASSEMBLING','CHECKING')",
            name="ck_vgp_stage",
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table(TABLE, schema=SCHEMA)
