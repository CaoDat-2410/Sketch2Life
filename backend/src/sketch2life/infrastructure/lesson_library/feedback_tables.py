"""School-scoped lesson feedback; text only, never child media or general chat."""

import sqlalchemy as sa

from sketch2life.infrastructure.lesson_library.tables import LESSON_METADATA

FEEDBACK_THREADS = sa.Table(
    "feedback_threads",
    LESSON_METADATA,
    sa.Column("thread_id", sa.String(36), primary_key=True),
    sa.Column("organization_id", sa.String(128), nullable=False),
    sa.Column("lesson_id", sa.String(36), nullable=False),
    sa.Column("version_id", sa.String(36), nullable=False),
    sa.Column("created_by", sa.String(256), nullable=False),
    sa.Column("revision", sa.Integer, nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.CheckConstraint("revision > 0", name="ck_feedback_revision"),
    sa.Index("ix_feedback_school_created", "organization_id", "created_at"),
)
FEEDBACK_MESSAGES = sa.Table(
    "feedback_messages",
    LESSON_METADATA,
    sa.Column("message_id", sa.String(36), primary_key=True),
    sa.Column(
        "thread_id",
        sa.String(36),
        sa.ForeignKey("lesson.feedback_threads.thread_id"),
        nullable=False,
    ),
    sa.Column("actor_ref", sa.String(256), nullable=False),
    sa.Column("body", sa.String(2000), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.CheckConstraint("length(body) BETWEEN 1 AND 2000", name="ck_feedback_body_length"),
)
