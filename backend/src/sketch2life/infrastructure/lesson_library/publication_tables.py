"""Exact-version independent review evidence owned by Lesson."""

import sqlalchemy as sa

from sketch2life.infrastructure.lesson_library.tables import LESSON_METADATA

PUBLICATION_REVIEWS = sa.Table(
    "publication_reviews",
    LESSON_METADATA,
    sa.Column("review_id", sa.String(36), primary_key=True),
    sa.Column("lesson_id", sa.String(36), nullable=False),
    sa.Column("version_id", sa.String(36), nullable=False),
    sa.Column("content_hash", sa.String(64), nullable=False),
    sa.Column("reviewer_ref", sa.String(256), nullable=False),
    sa.Column("permission_revision", sa.Integer, nullable=False),
    sa.Column("decision", sa.String(24), nullable=False),
    sa.Column("reason", sa.String(1000)),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.CheckConstraint(
        "decision IN ('APPROVE','REQUEST_CHANGES')", name="ck_publication_review_decision"
    ),
    sa.Index("ix_publication_review_target", "lesson_id", "version_id"),
)
