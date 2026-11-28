"""DDL-B1 part 2: video generations, their scenes and the run clock columns.

FEAT-066 goal v3, T-1a (``POST /v1/story-runs/{run_id}/video-generations``, SRS l.395, l.1670,
FR-AI-07 l.573, FR-B-11 l.597; REG l.373, l.380, l.381). It extends the Story chain on its own
branch ``frc08_lifecycle``: the parent is ``20261120_b1_0001`` (DDL-B1 part 1, T-2c), which this
revision replaces as the head of that chain (the label is inherited, so none is declared). It never
forks the chain: both revisions replace the same two CHECKs, so a second child of the lifecycle
revision would lose the other's values. The package is approved by name (OD-01: "DDL-B1 video,
transcript and run input"); this is part 2.

Upgrade, in order:

1. ``story.story_scenes`` and ``story.story_revision_reviews`` each gain a unique constraint that
   is trivially true (their primary key is already unique inside it) so a composite foreign key can
   point at it.
2. ``story.video_generations`` (REG l.380): one row per video request, an intent first. Composite
   keys tie a generation to the exact story revision and the exact adult review of that revision;
   partial unique indexes allow one open generation, one ``READY`` generation, one use of a review
   (an ``ADMISSION_REJECTED`` row does not use it) and one generation number per run.
3. ``story.video_generation_scenes`` (REG l.381): the scenes of the pinned revision, copied when the
   generation is accepted (``source_job_ref`` stays NULL until the first real worker, Q-J).
4. ``story.runs`` gains ``current_video_generation_id`` (the circular foreign key, so it is added
   after both tables exist, ``ON DELETE SET NULL``), ``adult_wait_started_at``,
   ``last_meaningful_activity_at`` and ``finished_at``. The two clocks are backfilled from
   ``updated_at`` for the runs that wait for the adult (the first sweep of T-1d1 may close old
   synthetic runs).
5. ``ck_story_run_state`` gains ``VIDEO_QUEUED``, ``VIDEO_GENERATING``, ``VIDEO_SAFETY_VALIDATING``,
   ``VIDEO_READY``, ``SAFETY_BLOCKED`` and ``ABANDONED`` (12 to 18 values; ``DRAFT`` and
   ``STORY_GENERATING`` are added by whoever first writes them) and
   ``ck_story_receipt_operation`` retains the Parent activity operations and gains
   ``CREATE_VIDEO_GENERATION``, ``MARK_VIDEO_UNSUITABLE`` and ``COMPLETE_RUN`` (12 to 15).

The CHECKs are added directly, which suits a disposable verification database; a production rollout
uses ``NOT VALID`` then ``VALIDATE`` (as the FR-C-08 migration does). No GRANT statement is used by
an earlier migration, so none is added.

The downgrade restores the part 1 sets (12 states, 10 operations), drops the three run columns
(the clocks are recomputable from ``updated_at``) and refuses while any video row, any run in one
of the six new states, any ``current_video_generation_id`` or any new receipt operation exists, then
reverses the steps in the opposite order. Run it with an explicit target, never ``-1`` (the graph
has many heads): ``alembic downgrade 20261120_b1_0001`` and ``alembic upgrade heads``. Never run
against ``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261120_vb_0002"
down_revision = "20261120_b1_0001"
branch_labels = None
depends_on = None

FINAL_RUN_STATES = (
    "'DRAFT','INPUT_PROCESSING','INPUT_REVIEW','SUBJECT_REVIEW','PREPARATION_REVIEW',"
    "'STORY_GENERATING','SCRIPT_REVIEW','VIDEO_ADMISSION_PENDING','VIDEO_QUEUED',"
    "'VIDEO_GENERATING','VIDEO_SAFETY_VALIDATING','VIDEO_READY','SAFETY_BLOCKED',"
    "'COMPLETED','FAILED','ABANDONED','DELETE_PENDING','DELETED','SCRIPT_GENERATING',"
    "'SCRIPT_GENERATION_UNKNOWN'"
)
FINAL_RECEIPT_OPERATIONS = (
    "'CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT','CANCEL_RUN',"
    "'GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION','DELETE_RUN','SUBMIT_IDEA',"
    "'CONFIRM_TRANSCRIPT','CREATE_VIDEO_GENERATION','MARK_VIDEO_UNSUITABLE',"
    "'COMPLETE_RUN','SELECT_ACTIVITY','GENERATE_ACTIVITY_SET','TRANSFER_TEACHER_OWNER',"
    "'FORCE_CLOSE_RUN'"
)

NEW_RUN_STATES = (
    "'VIDEO_QUEUED','VIDEO_GENERATING','VIDEO_SAFETY_VALIDATING','VIDEO_READY',"
    "'SAFETY_BLOCKED','ABANDONED'"
)
RUN_STATES_BEFORE = FINAL_RUN_STATES
RUN_STATES_AFTER = FINAL_RUN_STATES
NEW_RECEIPT_OPERATIONS = "'CREATE_VIDEO_GENERATION','MARK_VIDEO_UNSUITABLE','COMPLETE_RUN'"
RECEIPT_OPERATIONS_BEFORE = FINAL_RECEIPT_OPERATIONS
RECEIPT_OPERATIONS_AFTER = FINAL_RECEIPT_OPERATIONS

OPEN_STATES = (
    "'ADMISSION_PENDING','ACCEPTED','QUEUED','GENERATING','TECHNICAL_VALIDATING',"
    "'SAFETY_VALIDATING'"
)
# Runs that wait for the adult (the clocks of T-1d1 are backfilled for them).
WAIT_RUN_STATES = "'INPUT_REVIEW','SUBJECT_REVIEW','PREPARATION_REVIEW','SCRIPT_REVIEW'"

GENERATION_CHECKS: tuple[tuple[str, str], ...] = (
    (
        "ck_vg_state",
        "state IN ('ADMISSION_PENDING','ADMISSION_REJECTED','ACCEPTED','QUEUED','GENERATING',"
        "'TECHNICAL_VALIDATING','SAFETY_VALIDATING','READY','SAFETY_BLOCKED','FAILED',"
        "'REJECTED_BY_ADULT','SUPERSEDED')",
    ),
    ("ck_vg_kind", "generation_kind IN ('INITIAL','QUALITY_REGEN')"),
    (
        "ck_vg_validation_states",
        "technical_validation_state IN ('PENDING','PASSED','FAILED') "
        "AND consistency_validation_state IN ('PENDING','PASSED','FAILED') "
        "AND safety_validation_state IN ('PENDING','PASSED','FAILED')",
    ),
    (
        "ck_vg_hashes",
        "length(request_idempotency_key_hash) = 64 AND length(request_fingerprint_sha256) = 64 "
        "AND length(target_script_hash) = 64",
    ),
    ("ck_vg_revision", "generation_revision > 0"),
    (
        "ck_vg_output",
        "(output_asset_ref IS NULL AND output_asset_version IS NULL) OR "
        "(output_asset_ref IS NOT NULL AND output_asset_version IS NOT NULL "
        "AND output_asset_version > 0)",
    ),
    (
        "ck_vg_shape",
        "(state = 'ADMISSION_PENDING' AND generation_no IS NULL AND accepted_at IS NULL "
        "AND rejected_at IS NULL AND billing_quota_usage_ref IS NULL AND job_ref IS NULL) OR "
        "(state = 'ADMISSION_REJECTED' AND generation_no IS NULL AND accepted_at IS NULL "
        "AND rejected_at IS NOT NULL AND billing_quota_usage_ref IS NULL AND job_ref IS NULL) OR "
        "(state NOT IN ('ADMISSION_PENDING','ADMISSION_REJECTED') "
        "AND generation_no BETWEEN 1 AND 3 AND accepted_at IS NOT NULL AND rejected_at IS NULL "
        "AND compute_reservation_ref IS NOT NULL AND billing_quota_usage_ref IS NOT NULL "
        "AND job_ref IS NOT NULL)",
    ),
    (
        "ck_vg_ready",
        "state <> 'READY' OR (output_asset_ref IS NOT NULL "
        "AND technical_validation_state = 'PASSED' AND consistency_validation_state = 'PASSED' "
        "AND safety_validation_state = 'PASSED' AND completed_at IS NOT NULL)",
    ),
    ("ck_vg_reason", "generation_kind = 'INITIAL' OR quality_reason_code IS NOT NULL"),
    (
        "ck_vg_rejected_by_adult",
        "state <> 'REJECTED_BY_ADULT' OR rejection_reason_code IS NOT NULL",
    ),
    (
        "ck_vg_failure_code",
        "state NOT IN ('FAILED','ADMISSION_REJECTED') OR safe_failure_code IS NOT NULL",
    ),
)
SCENE_CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_vgs_state", "state IN ('QUEUED','GENERATING','READY','FAILED')"),
    (
        "ck_vgs_clip",
        "(clip_asset_ref IS NULL AND clip_asset_version IS NULL) OR "
        "(clip_asset_ref IS NOT NULL AND clip_asset_version IS NOT NULL "
        "AND clip_asset_version > 0)",
    ),
)
# (index name, columns, partial predicate)
GENERATION_INDEXES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("uq_vg_one_open", ("story_run_id",), f"state IN ({OPEN_STATES})"),
    ("uq_vg_one_ready", ("story_run_id",), "state = 'READY'"),
    ("uq_vg_review_consumed", ("story_review_id",), "state <> 'ADMISSION_REJECTED'"),
    ("uq_vg_number", ("story_run_id", "generation_no"), "generation_no IS NOT NULL"),
)

DOWNGRADE_GUARD = f"""
DO $vb_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM story.video_generations) THEN
        RAISE EXCEPTION 'DDL-B1 part 2 downgrade refused: video generations exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.runs
               WHERE run_state IN ({NEW_RUN_STATES})
                  OR current_video_generation_id IS NOT NULL) THEN
        RAISE EXCEPTION 'DDL-B1 part 2 downgrade refused: video runs exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.command_receipts
               WHERE operation IN ({NEW_RECEIPT_OPERATIONS})) THEN
        RAISE EXCEPTION 'DDL-B1 part 2 downgrade refused: video receipts exist';
    END IF;
END;
$vb_downgrade_guard$;
"""


def upgrade() -> None:
    # 1. trivially true uniques, the targets of the composite foreign keys below
    op.create_unique_constraint(
        "uq_story_scene_revision_scene",
        "story_scenes",
        ["story_revision_id", "scene_id"],
        schema="story",
    )
    op.create_unique_constraint(
        "uq_story_review_run_revision",
        "story_revision_reviews",
        ["run_id", "story_revision_id", "review_id"],
        schema="story",
    )

    # 2. story.video_generations
    op.create_table(
        "video_generations",
        sa.Column("video_generation_id", sa.String(36), primary_key=True),
        sa.Column("story_run_id", sa.String(36), nullable=False),
        sa.Column("story_revision_id", sa.String(36), nullable=False),
        sa.Column("story_review_id", sa.String(36), nullable=False),
        sa.Column("generation_no", sa.Integer(), nullable=True),
        sa.Column("generation_kind", sa.String(16), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("request_idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("request_fingerprint_sha256", sa.String(64), nullable=False),
        sa.Column("target_script_hash", sa.String(64), nullable=False),
        sa.Column("quality_reason_code", sa.String(32), nullable=True),
        sa.Column("rejection_reason_code", sa.String(32), nullable=True),
        sa.Column("compute_reservation_ref", sa.String(128), nullable=True),
        sa.Column("compute_released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("billing_quota_usage_ref", sa.String(128), nullable=True),
        sa.Column("job_ref", sa.String(64), nullable=True),
        sa.Column("output_asset_ref", sa.String(256), nullable=True),
        sa.Column("output_asset_version", sa.Integer(), nullable=True),
        sa.Column("video_profile_ref", sa.String(128), nullable=True),
        sa.Column("model_revision", sa.String(128), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
        sa.Column(
            "technical_validation_state",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column(
            "consistency_validation_state",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column(
            "safety_validation_state",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("safety_policy_version", sa.String(64), nullable=True),
        sa.Column("safety_finding_codes", postgresql.JSONB(), nullable=True),
        sa.Column("admission_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safe_failure_code", sa.String(64), nullable=True),
        sa.Column("generation_revision", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["story_run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_vg_story_run"
        ),
        sa.ForeignKeyConstraint(
            ["story_run_id", "story_revision_id"],
            ["story.story_revisions.run_id", "story.story_revisions.story_revision_id"],
            name="fk_vg_story_revision",
        ),
        sa.ForeignKeyConstraint(
            ["story_run_id", "story_revision_id", "story_review_id"],
            [
                "story.story_revision_reviews.run_id",
                "story.story_revision_reviews.story_revision_id",
                "story.story_revision_reviews.review_id",
            ],
            name="fk_vg_story_review",
        ),
        sa.UniqueConstraint(
            "video_generation_id", "story_revision_id", name="uq_vg_generation_revision"
        ),
        sa.UniqueConstraint("job_ref", name="uq_vg_job_ref"),
        sa.UniqueConstraint("story_run_id", "request_idempotency_key_hash", name="uq_vg_run_key"),
        schema="story",
    )
    for name, text in GENERATION_CHECKS:
        op.create_check_constraint(name, "video_generations", text, schema="story")
    for index_name, columns, predicate in GENERATION_INDEXES:
        op.create_index(
            index_name,
            "video_generations",
            list(columns),
            unique=True,
            schema="story",
            postgresql_where=sa.text(predicate),
        )

    # 3. story.video_generation_scenes
    op.create_table(
        "video_generation_scenes",
        sa.Column("generation_scene_id", sa.String(36), primary_key=True),
        sa.Column("video_generation_id", sa.String(36), nullable=False),
        sa.Column("story_revision_id", sa.String(36), nullable=False),
        sa.Column("story_scene_id", sa.String(36), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("clip_asset_ref", sa.String(256), nullable=True),
        sa.Column("clip_asset_version", sa.Integer(), nullable=True),
        sa.Column("source_job_ref", sa.String(64), nullable=True),
        sa.Column("consistency_result_code", sa.String(64), nullable=True),
        sa.Column("safe_failure_code", sa.String(64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["video_generation_id", "story_revision_id"],
            [
                "story.video_generations.video_generation_id",
                "story.video_generations.story_revision_id",
            ],
            ondelete="CASCADE",
            name="fk_vgs_generation",
        ),
        sa.ForeignKeyConstraint(
            ["story_revision_id", "story_scene_id"],
            ["story.story_scenes.story_revision_id", "story.story_scenes.scene_id"],
            name="fk_vgs_scene",
        ),
        sa.UniqueConstraint(
            "video_generation_id", "story_scene_id", name="uq_vgs_generation_scene"
        ),
        schema="story",
    )
    for name, text in SCENE_CHECKS:
        op.create_check_constraint(name, "video_generation_scenes", text, schema="story")

    # 4. story.runs: the circular pointer is added after both tables exist
    op.add_column(
        "runs",
        sa.Column("current_video_generation_id", sa.String(36), nullable=True),
        schema="story",
    )
    op.create_foreign_key(
        "fk_story_run_current_video_generation",
        "runs",
        "video_generations",
        ["current_video_generation_id"],
        ["video_generation_id"],
        source_schema="story",
        referent_schema="story",
        ondelete="SET NULL",
    )
    op.add_column(
        "runs",
        sa.Column("adult_wait_started_at", sa.DateTime(timezone=True), nullable=True),
        schema="story",
    )
    op.add_column(
        "runs",
        sa.Column("last_meaningful_activity_at", sa.DateTime(timezone=True), nullable=True),
        schema="story",
    )
    op.add_column(
        "runs", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True), schema="story"
    )
    op.execute(
        sa.text(
            "UPDATE story.runs SET adult_wait_started_at = updated_at, "
            "last_meaningful_activity_at = updated_at "
            f"WHERE run_state IN ({WAIT_RUN_STATES})"
        )
    )

    # 5. the two replaced CHECKs
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state", "runs", f"run_state IN ({FINAL_RUN_STATES})", schema="story"
    )
    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({FINAL_RECEIPT_OPERATIONS})",
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

    op.drop_column("runs", "finished_at", schema="story")
    op.drop_column("runs", "last_meaningful_activity_at", schema="story")
    op.drop_column("runs", "adult_wait_started_at", schema="story")
    op.drop_constraint(
        "fk_story_run_current_video_generation", "runs", schema="story", type_="foreignkey"
    )
    op.drop_column("runs", "current_video_generation_id", schema="story")

    op.drop_table("video_generation_scenes", schema="story")
    for index_name, _columns, _predicate in reversed(GENERATION_INDEXES):
        op.drop_index(index_name, table_name="video_generations", schema="story")
    op.drop_table("video_generations", schema="story")

    op.drop_constraint(
        "uq_story_review_run_revision", "story_revision_reviews", schema="story", type_="unique"
    )
    op.drop_constraint(
        "uq_story_scene_revision_scene", "story_scenes", schema="story", type_="unique"
    )
