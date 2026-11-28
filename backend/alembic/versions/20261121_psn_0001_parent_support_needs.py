"""DDL-D (T-12c, 1 of 2): the encrypted Parent profile support needs.

FEAT-066 goal v4, T-12c (``GET`` and ``PUT /v1/parent/profiles/{profile_id}/support-needs``; SRS
l.264 BR-20, l.499 FR-C-07, l.932, l.1922, l.2338). The package is approved by the owner's Phase B
launch. Parent of this revision is ``20261121_pce_0001`` (T-12a), the head of the Parent branch,
which this revision replaces as the Parent head (no label, no ``depends_on``). The BE1 table is a
separate revision (``20261121_psn_0002``) because ``parent.child_profiles`` and
``public.be1_managed_profiles`` live on separate roots. Alembic heads stay 15 down-only (10
dependency-aware); with both T-12c revisions the graph has 55 revisions.

Upgrade, in order:

1. ``parent.profile_support_needs``: a singleton current record per profile. ``ciphertext`` holds
   the category and the note (AES-256-GCM, tag included, so at least 16 bytes), ``nonce`` is the
   96-bit nonce, ``key_id`` the opaque non-secret key label, ``algorithm_version`` fixes the cipher
   and the associated-data encoding. No column holds a value in the clear and no index covers
   encrypted bytes. The foreign key is ``ON DELETE RESTRICT`` like the other Parent foreign keys:
   no terminal purge of ``parent.child_profiles`` exists yet, so the FR-C-10 executor, when it
   exists, must delete this row (under its own approved procedure) before the profile row.
2. ``UNIQUE (key_id, nonce)``: a nonce is never reused under one key label.
3. A ``BEFORE UPDATE`` trigger: the profile key and ``created_at`` never change, the revision
   rises by exactly one and the nonce changes. A ``BEFORE DELETE`` trigger refuses every delete;
   an erasure procedure is a separately approved migration or role, not built here.

No backfill. The downgrade refuses while any row exists (no automatic export, key destruction or
discard), then drops the triggers, the functions and the table; it is rejected for a populated
environment. Run it with an explicit target, never ``-1``, on a disposable database only:
``alembic downgrade 20261121_pce_0001`` (T-12c's BE1 revision first), then
``alembic upgrade heads``. Never run against ``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261121_psn_0001"
down_revision = "20261121_pce_0001"
branch_labels = None
depends_on = None

SCHEMA = "parent"
TABLE = "profile_support_needs"
UPDATE_FUNCTION = "guard_profile_support_needs_update"
UPDATE_TRIGGER = "trg_parent_profile_support_needs_update"
DELETE_FUNCTION = "refuse_profile_support_needs_delete"
DELETE_TRIGGER = "trg_parent_profile_support_needs_delete"

CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_parent_profile_support_needs_revision", "revision >= 1"),
    (
        "ck_parent_profile_support_needs_ciphertext",
        "octet_length(ciphertext) BETWEEN 16 AND 16384",
    ),
    ("ck_parent_profile_support_needs_nonce", "octet_length(nonce) = 12"),
    ("ck_parent_profile_support_needs_key_id", "char_length(key_id) BETWEEN 1 AND 128"),
    ("ck_parent_profile_support_needs_algorithm", "algorithm_version = 1"),
)

UPDATE_FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{UPDATE_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.parent_profile_id IS DISTINCT FROM OLD.parent_profile_id
     OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
    RAISE EXCEPTION 'PARENT_PROFILE_SUPPORT_NEEDS_KEY_IMMUTABLE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.revision IS DISTINCT FROM OLD.revision + 1 THEN
    RAISE EXCEPTION 'PARENT_PROFILE_SUPPORT_NEEDS_REVISION_STEP'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.nonce IS NOT DISTINCT FROM OLD.nonce THEN
    RAISE EXCEPTION 'PARENT_PROFILE_SUPPORT_NEEDS_NONCE_REUSE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END;
$$
"""

DELETE_FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{DELETE_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'PARENT_PROFILE_SUPPORT_NEEDS_DELETE_FORBIDDEN'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

DOWNGRADE_GUARD = f"""
DO $psn_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE}) THEN
        RAISE EXCEPTION 'DDL-D T-12c downgrade refused: parent support needs exist';
    END IF;
END;
$psn_downgrade_guard$;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("parent_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("ciphertext", postgresql.BYTEA(), nullable=False),
        sa.Column("nonce", postgresql.BYTEA(), nullable=False),
        sa.Column("key_id", sa.String(length=128), nullable=False),
        sa.Column("algorithm_version", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("parent_profile_id", name="pk_parent_profile_support_needs"),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_profile_support_needs_profile",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("key_id", "nonce", name="uq_parent_profile_support_needs_key_nonce"),
        schema=SCHEMA,
    )
    for name, expression in CHECKS:
        op.create_check_constraint(name, TABLE, expression, schema=SCHEMA)
    op.execute(sa.text(UPDATE_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {UPDATE_TRIGGER} BEFORE UPDATE ON {SCHEMA}.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{UPDATE_FUNCTION}()"
        )
    )
    op.execute(sa.text(DELETE_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {DELETE_TRIGGER} BEFORE DELETE ON {SCHEMA}.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{DELETE_FUNCTION}()"
        )
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(sa.text(f"DROP TRIGGER {DELETE_TRIGGER} ON {SCHEMA}.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION {SCHEMA}.{DELETE_FUNCTION}()"))
    op.execute(sa.text(f"DROP TRIGGER {UPDATE_TRIGGER} ON {SCHEMA}.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION {SCHEMA}.{UPDATE_FUNCTION}()"))
    op.drop_table(TABLE, schema=SCHEMA)
