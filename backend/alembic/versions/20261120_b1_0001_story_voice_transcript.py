"""DDL-B1 part 1: Parent run voice idea and the transcript revisions of TD-04.

FEAT-066 goal v3, T-2c (``POST /v1/story-runs/{run_id}/idea``, SRS l.1665, FR-P-03 l.512, BR-23
l.267, l.1413, l.1713). It extends the Story chain on its own branch ``frc08_lifecycle`` (parent
``20261119_frc08_lifecycle_scope``, which it replaces as the head of that chain; the label is
inherited, so none is declared) and creates one table. The package is approved by name (OD-01:
"DDL-B1 video, transcript and run input"); this is part 1. Job rows are not part of it (Q-J).

Upgrade, in order:

1. ``story.run_inputs`` gains ``voice_asset_ref``, ``voice_asset_version`` and
   ``voice_duration_ms`` (all NULL for an existing row; hash, media type and size stay in
   ``core_asset_metadata``, REG l.374).
2. ``ck_story_run_input_typed_idea`` is replaced by ``ck_story_run_input_idea`` (none, text only,
   voice only, or both, with the matching ``idea_source``) and ``ck_story_run_input_voice`` (all
   three voice columns NULL, or a positive version and a duration of 1 to 120,000 ms, l.982).
3. ``story.transcript_revisions`` (REG l.375) with bounded text, a hash bound to the effective
   text, an ``origin`` (``ASR`` or ``ADULT_CORRECTION``), the five states, a composite foreign key
   to ``story.run_inputs`` (ON DELETE CASCADE) and two partial unique indexes: at most one
   ``CONFIRMED`` row and at most one ``PENDING`` or ``NEEDS_CONFIRMATION`` row per
   ``(run_id, source_asset_ref)``. The application marks the old row ``SUPERSEDED`` before it
   inserts a new one (the indexes are checked per statement).
4. ``ck_story_run_state`` accepts ``INPUT_REVIEW`` (11 to 12 values; l.394).
5. ``ck_story_receipt_operation`` retains the two operations from the parallel Parent activity
   branch, then accepts ``SUBMIT_IDEA`` and ``CONFIRM_TRANSCRIPT`` (10 to 12).

The CHECKs are added directly, which suits a disposable verification database; a production
rollout uses ``NOT VALID`` then ``VALIDATE`` (as the FR-C-08 migration does). No GRANT statement is
used by an earlier migration, so none is added.

The downgrade refuses while any transcript row, any voice column value, any voice ``idea_source``,
any ``INPUT_REVIEW`` run or any new-operation receipt exists, then reverses the steps in the
opposite order. Run it with an explicit target, never ``-1`` (the graph has many heads):
``alembic downgrade 20261119_frc08_lifecycle_scope`` and ``alembic upgrade heads``. Never run
against ``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261120_b1_0001"
down_revision = "20261119_frc08_lifecycle_scope"
branch_labels = None
depends_on = None

RUN_STATES_BEFORE = (
    "'INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW',"
    "'SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
    "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED','COMPLETED','DELETED'"
)
RUN_STATES_AFTER = RUN_STATES_BEFORE.replace(
    "'INPUT_PROCESSING',", "'INPUT_PROCESSING','INPUT_REVIEW',"
)
RECEIPT_OPERATIONS_BEFORE = (
    "'CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT',"
    "'CANCEL_RUN','GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION','DELETE_RUN',"
    "'GENERATE_ACTIVITY_SET','SELECT_ACTIVITY'"
)
RECEIPT_OPERATIONS_AFTER = f"{RECEIPT_OPERATIONS_BEFORE},'SUBMIT_IDEA','CONFIRM_TRANSCRIPT'"

TYPED_IDEA_CHECK = (
    "(typed_idea IS NULL AND idea_source IS NULL) OR "
    "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 "
    "AND idea_source = 'TEXT')"
)
IDEA_CHECK = (
    "(typed_idea IS NULL AND voice_asset_ref IS NULL AND idea_source IS NULL) OR "
    "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 "
    "AND voice_asset_ref IS NULL AND idea_source = 'TEXT') OR "
    "(typed_idea IS NULL AND voice_asset_ref IS NOT NULL AND idea_source = 'VOICE') OR "
    "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 "
    "AND voice_asset_ref IS NOT NULL AND idea_source = 'TEXT_AND_VOICE')"
)
VOICE_CHECK = (
    "(voice_asset_ref IS NULL AND voice_asset_version IS NULL AND voice_duration_ms IS NULL) OR "
    "(voice_asset_ref IS NOT NULL AND voice_asset_version IS NOT NULL "
    "AND voice_asset_version > 0 AND voice_duration_ms IS NOT NULL "
    "AND voice_duration_ms BETWEEN 1 AND 120000)"
)

TRANSCRIPT_CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_story_transcript_revision_no", "revision_no > 0"),
    ("ck_story_transcript_origin", "origin IN ('ASR','ADULT_CORRECTION')"),
    (
        "ck_story_transcript_state",
        "state IN ('PENDING','NEEDS_CONFIRMATION','CONFIRMED','SUPERSEDED','FAILED')",
    ),
    (
        "ck_story_transcript_text_bound",
        "(raw_transcript IS NULL OR length(raw_transcript) <= 20000) AND "
        "(adult_corrected_text IS NULL OR length(adult_corrected_text) BETWEEN 1 AND 500)",
    ),
    (
        "ck_story_transcript_hash",
        "(transcript_sha256 IS NULL OR transcript_sha256 ~ '^[0-9a-f]{64}$') AND "
        "(state NOT IN ('NEEDS_CONFIRMATION','CONFIRMED') OR "
        "(transcript_sha256 IS NOT NULL AND "
        "(raw_transcript IS NOT NULL OR adult_corrected_text IS NOT NULL)))",
    ),
    (
        "ck_story_transcript_confirmed",
        "state <> 'CONFIRMED' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
    ),
    ("ck_story_transcript_failed", "state <> 'FAILED' OR error_code IS NOT NULL"),
    (
        "ck_story_transcript_correction",
        "origin <> 'ADULT_CORRECTION' OR adult_corrected_text IS NOT NULL",
    ),
    (
        "ck_story_transcript_timing_bound",
        "segment_timing IS NULL OR octet_length(segment_timing::text) <= 65536",
    ),
)

DOWNGRADE_GUARD = """
DO $b1_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM story.transcript_revisions) THEN
        RAISE EXCEPTION 'DDL-B1 downgrade refused: transcript revisions exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.run_inputs
               WHERE voice_asset_ref IS NOT NULL OR voice_asset_version IS NOT NULL
                  OR voice_duration_ms IS NOT NULL
                  OR idea_source IN ('VOICE','TEXT_AND_VOICE')) THEN
        RAISE EXCEPTION 'DDL-B1 downgrade refused: voice run inputs exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.runs WHERE run_state = 'INPUT_REVIEW') THEN
        RAISE EXCEPTION 'DDL-B1 downgrade refused: INPUT_REVIEW runs exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.command_receipts
               WHERE operation IN ('SUBMIT_IDEA','CONFIRM_TRANSCRIPT')) THEN
        RAISE EXCEPTION 'DDL-B1 downgrade refused: idea or transcript receipts exist';
    END IF;
END;
$b1_downgrade_guard$;
"""


def upgrade() -> None:
    op.add_column(
        "run_inputs", sa.Column("voice_asset_ref", sa.String(256), nullable=True), schema="story"
    )
    op.add_column(
        "run_inputs", sa.Column("voice_asset_version", sa.Integer(), nullable=True), schema="story"
    )
    op.add_column(
        "run_inputs", sa.Column("voice_duration_ms", sa.Integer(), nullable=True), schema="story"
    )
    op.drop_constraint("ck_story_run_input_typed_idea", "run_inputs", schema="story", type_="check")
    op.create_check_constraint("ck_story_run_input_idea", "run_inputs", IDEA_CHECK, schema="story")
    op.create_check_constraint(
        "ck_story_run_input_voice", "run_inputs", VOICE_CHECK, schema="story"
    )

    op.create_table(
        "transcript_revisions",
        sa.Column("transcript_revision_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("run_input_id", sa.String(36), nullable=False),
        sa.Column("source_asset_ref", sa.String(256), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(24), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("raw_transcript", sa.Text(), nullable=True),
        sa.Column("adult_corrected_text", sa.String(500), nullable=True),
        sa.Column("transcript_sha256", sa.String(64), nullable=True),
        sa.Column("language", sa.String(16), nullable=True),
        sa.Column("asr_profile_ref", sa.String(128), nullable=True),
        sa.Column("model_revision", sa.String(128), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
        sa.Column("segment_timing", postgresql.JSONB(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("reviewed_by", sa.String(256), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "run_input_id"],
            ["story.run_inputs.run_id", "story.run_inputs.run_input_id"],
            ondelete="CASCADE",
            name="fk_story_transcript_run_input",
        ),
        sa.UniqueConstraint("run_id", "revision_no", name="uq_story_transcript_revision"),
        schema="story",
    )
    for name, text in TRANSCRIPT_CHECKS:
        op.create_check_constraint(name, "transcript_revisions", text, schema="story")
    op.create_index(
        "uq_story_transcript_confirmed",
        "transcript_revisions",
        ["run_id", "source_asset_ref"],
        unique=True,
        schema="story",
        postgresql_where=sa.text("state = 'CONFIRMED'"),
    )
    op.create_index(
        "uq_story_transcript_open",
        "transcript_revisions",
        ["run_id", "source_asset_ref"],
        unique=True,
        schema="story",
        postgresql_where=sa.text("state IN ('PENDING','NEEDS_CONFIRMATION')"),
    )

    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state", "runs", f"run_state IN ({RUN_STATES_AFTER})", schema="story"
    )
    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({RECEIPT_OPERATIONS_AFTER})",
        schema="story",
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))

    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({RECEIPT_OPERATIONS_BEFORE})",
        schema="story",
    )
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state", "runs", f"run_state IN ({RUN_STATES_BEFORE})", schema="story"
    )

    op.drop_index("uq_story_transcript_open", table_name="transcript_revisions", schema="story")
    op.drop_index(
        "uq_story_transcript_confirmed", table_name="transcript_revisions", schema="story"
    )
    op.drop_table("transcript_revisions", schema="story")

    op.drop_constraint("ck_story_run_input_voice", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_idea", "run_inputs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_input_typed_idea", "run_inputs", TYPED_IDEA_CHECK, schema="story"
    )
    op.drop_column("run_inputs", "voice_duration_ms", schema="story")
    op.drop_column("run_inputs", "voice_asset_version", schema="story")
    op.drop_column("run_inputs", "voice_asset_ref", schema="story")
