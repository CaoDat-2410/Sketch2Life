"""Add immutable source lineage for Teacher remixes of PUBLIC lesson versions.

T-10b, Phase C. The lesson-library lineage table is a child of the selected lesson head;
it stores provenance only and grants no access to the source version.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261121_ll_0001"
down_revision = "20261120_sel_0001"
branch_labels = None
depends_on = None

SCHEMA = "lesson"
TABLE = "library_version_lineage"
APPEND_ONLY_FUNCTION = "reject_library_version_lineage_mutation"
APPEND_ONLY_TRIGGER = "trg_lesson_version_lineage_append_only"
CYCLE_FUNCTION = "reject_library_version_lineage_cycle"
CYCLE_TRIGGER = "trg_lesson_version_lineage_cycle"
SOURCE_INDEX = "ix_lesson_lineage_source_version"

APPEND_ONLY_FUNCTION_SQL = f"""
CREATE FUNCTION lesson.{APPEND_ONLY_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, lesson
AS $$
BEGIN
  RAISE EXCEPTION 'LESSON_VERSION_LINEAGE_IS_APPEND_ONLY'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

CYCLE_FUNCTION_SQL = f"""
CREATE FUNCTION lesson.{CYCLE_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, lesson
AS $$
DECLARE
  v_cycle boolean;
BEGIN
  -- Serialize edge inserts so two concurrent writers cannot create a cycle by write skew.
  PERFORM pg_catalog.pg_advisory_xact_lock(20261121, 1);

  WITH RECURSIVE ancestry(version_id) AS (
    SELECT NEW.source_version_id
    UNION
    SELECT lineage.source_version_id
      FROM lesson.library_version_lineage AS lineage
      JOIN ancestry ON lineage.derived_version_id = ancestry.version_id
  )
  SELECT EXISTS (
    SELECT 1 FROM ancestry WHERE version_id = NEW.derived_version_id
  ) INTO v_cycle;

  IF v_cycle THEN
    RAISE EXCEPTION 'LESSON_VERSION_LINEAGE_CYCLE_REJECTED'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END;
$$
"""

DOWNGRADE_GUARD_SQL = f"""
DO $ll_downgrade_guard$
BEGIN
  IF EXISTS (SELECT 1 FROM lesson.{TABLE}) THEN
    RAISE EXCEPTION 'DDL-D T-10b downgrade refused: lesson lineage rows exist';
  END IF;
END;
$ll_downgrade_guard$;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("derived_version_id", sa.String(length=36), nullable=False),
        sa.Column("source_version_id", sa.String(length=36), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("derived_version_id", name="pk_lesson_version_lineage"),
        sa.ForeignKeyConstraint(
            ["derived_version_id"],
            ["lesson.library_versions.version_id"],
            name="fk_lesson_lineage_derived_version",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_version_id"],
            ["lesson.library_versions.version_id"],
            name="fk_lesson_lineage_source_version",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "derived_version_id <> source_version_id",
            name="ck_lesson_lineage_not_self",
        ),
        sa.CheckConstraint(
            "source_content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_lesson_lineage_source_content_hash",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        SOURCE_INDEX,
        TABLE,
        ["source_version_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.execute(sa.text(APPEND_ONLY_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {APPEND_ONLY_TRIGGER} "
            f"BEFORE UPDATE OR DELETE ON lesson.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION lesson.{APPEND_ONLY_FUNCTION}()"
        )
    )
    op.execute(sa.text(CYCLE_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {CYCLE_TRIGGER} BEFORE INSERT ON lesson.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION lesson.{CYCLE_FUNCTION}()"
        )
    )


def downgrade() -> None:
    # The lock makes the empty-table check stable through the drop.
    op.execute(sa.text(f"LOCK TABLE lesson.{TABLE} IN ACCESS EXCLUSIVE MODE"))
    op.execute(sa.text(DOWNGRADE_GUARD_SQL))
    op.execute(sa.text(f"DROP TRIGGER {CYCLE_TRIGGER} ON lesson.{TABLE}"))
    op.execute(sa.text(f"DROP TRIGGER {APPEND_ONLY_TRIGGER} ON lesson.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION lesson.{CYCLE_FUNCTION}()"))
    op.execute(sa.text(f"DROP FUNCTION lesson.{APPEND_ONLY_FUNCTION}()"))
    op.drop_index(SOURCE_INDEX, table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
