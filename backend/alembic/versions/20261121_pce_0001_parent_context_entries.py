"""DDL-D (T-12a): the Parent-owned profile context entries.

FEAT-066 goal v4, T-12a (``GET`` and ``POST /v1/parent/profiles/{profile_id}/context-entries``;
SRS l.263-265 BR-19 to BR-21, l.497-499 FR-C-05 to FR-C-07, l.2349 FR-P-06; REG l.324-327). The
package is approved by the owner's Phase B launch. It extends the Parent branch on its own
chain: the parent is ``20261109_m2_parent_profiles`` (a separate root and a head), which this
revision replaces as the Parent head (no label is declared, none is needed, and ``depends_on`` is
not used). Alembic heads stay 15 down-only (10 dependency-aware); the graph has 52 revisions.

Upgrade, in order:

1. ``parent.profile_context_entries``: bounded adult-entered observations, achievements and
   out-of-app experiences, attached to the stable ``parent_profile_id`` (not to a profile
   revision). Append only. ``source_ref`` and ``created_by`` are stored but never returned and
   never copied into a Story snapshot. The foreign key is ``ON DELETE RESTRICT`` like the other
   Parent foreign keys: no terminal purge of ``parent.child_profiles`` exists yet, so the FR-C-10
   executor, when it exists, owns the entry purge.
   The text and reference checks also refuse the C0 control characters (newline and tab stay
   legal in ``short_text``) and DEL; PostgreSQL text cannot hold NUL at all.
2. A ``BEFORE UPDATE`` trigger: an entry is never changed (a correction is a new entry). There is
   no DELETE guard: the future purge must be able to delete the rows.
3. The page index ``ix_parent_profile_context_entries_page``.

No Story DDL and no receipt DDL: ``story.run_inputs`` already stores the confirmed context
snapshot (JSONB, hash, revision, 32 KiB bound), ``CONFIRM_CONTEXT`` is an existing receipt
operation, and ``parent.command_receipts`` has no operation check.

The downgrade refuses while any entry exists, then drops the trigger, the function, the index and
the table. Run it with an explicit target, never ``-1`` (the graph has many heads), on a
disposable database only: ``alembic downgrade 20261109_m2_parent_profiles``, then
``alembic upgrade heads``. Never run against ``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261121_pce_0001"
down_revision = "20261109_m2_parent_profiles"
branch_labels = None
depends_on = None

SCHEMA = "parent"
TABLE = "profile_context_entries"
FUNCTION = "reject_profile_context_entry_update"
TRIGGER = "trg_parent_profile_context_entries_append_only"
INDEX = "ix_parent_profile_context_entries_page"

CHECKS: tuple[tuple[str, str], ...] = (
    (
        "ck_parent_profile_context_entries_kind",
        "entry_kind IN ('OBSERVATION','ACHIEVEMENT','OUTSIDE_EXPERIENCE')",
    ),
    (
        "ck_parent_profile_context_entries_text",
        "char_length(btrim(short_text)) BETWEEN 1 AND 500 AND octet_length(short_text) <= 2000 "
        "AND short_text !~ '[\\x01-\\x08\\x0b-\\x1f\\x7f]'",
    ),
    (
        "ck_parent_profile_context_entries_source_kind",
        "source_kind ~ '^[A-Z][A-Z0-9_]{0,31}$'",
    ),
    (
        "ck_parent_profile_context_entries_source_ref",
        "source_ref IS NULL OR (char_length(btrim(source_ref)) BETWEEN 1 AND 256 "
        "AND source_ref !~ '[\\x01-\\x1f\\x7f]')",
    ),
    (
        "ck_parent_profile_context_entries_created_by",
        "char_length(created_by) BETWEEN 1 AND 256",
    ),
)

FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'PARENT_PROFILE_CONTEXT_ENTRY_UPDATE_FORBIDDEN'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

DOWNGRADE_GUARD = f"""
DO $pce_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE}) THEN
        RAISE EXCEPTION 'DDL-D T-12a downgrade refused: profile context entries exist';
    END IF;
END;
$pce_downgrade_guard$;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("context_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_kind", sa.String(length=32), nullable=False),
        sa.Column("short_text", sa.String(length=500), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.String(length=256), nullable=True),
        sa.Column("approximate_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("context_entry_id", name="pk_parent_profile_context_entries"),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_profile_context_entries_profile",
            ondelete="RESTRICT",
        ),
        schema=SCHEMA,
    )
    for name, expression in CHECKS:
        op.create_check_constraint(name, TABLE, expression, schema=SCHEMA)
    op.create_index(
        INDEX,
        TABLE,
        ["parent_profile_id", "created_at", "context_entry_id"],
        schema=SCHEMA,
    )
    op.execute(sa.text(FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {TRIGGER} BEFORE UPDATE ON {SCHEMA}.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{FUNCTION}()"
        )
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(sa.text(f"DROP TRIGGER {TRIGGER} ON {SCHEMA}.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION {SCHEMA}.{FUNCTION}()"))
    op.drop_index(INDEX, table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
