"""DDL-D (T-12c, 2 of 2): the encrypted BE1 profile support needs.

FEAT-066 goal v4, T-12c (``GET`` and ``PUT /api/be1/v1/organizations/{organization_id}/classes/
{class_id}/profiles/{child_id}/support-needs``; SRS l.264 BR-20, l.499 FR-C-07, l.932, l.1922,
l.2338). The package is approved by the owner's Phase B launch. Parent of this revision is
``20261121_bpr_0001`` (T-12b), the head of the BE1-on-Story chain, which this revision replaces
as that head (no label, no ``depends_on``); ``public.be1_managed_profiles`` exists in its
ancestry. Like ``bpr_0001`` it sits on the ``frc08_lifecycle`` branch, not on ``be1_core``: an
existing database needs one ``alembic upgrade heads``. The Parent table is the other T-12c
revision (``20261121_psn_0001``). Alembic heads stay 15 down-only (10 dependency-aware); with both
T-12c revisions the graph has 55 revisions.

Upgrade, in order:

1. ``public.be1_profile_support_needs``: a singleton current record per managed profile.
   ``ciphertext`` holds the category and the note (AES-256-GCM, tag included, so at least 16
   bytes), ``nonce`` is the 96-bit nonce, ``key_id`` the opaque non-secret key label,
   ``algorithm_version`` fixes the cipher and the associated-data encoding. No column holds a
   value in the clear. The foreign key to ``be1_managed_profiles`` is ``ON DELETE RESTRICT``: no
   code deletes a profile, and the FR-C-10 executor, when it exists, must delete this row (under
   its own approved procedure) before the profile row.
2. ``UNIQUE (key_id, nonce)``. The Parent and BE1 families encrypt under different derived keys,
   so a nonce may repeat across the two tables without reusing a key and nonce pair.
3. A ``BEFORE UPDATE`` trigger (the profile key and ``created_at`` never change, the revision
   rises by exactly one, the nonce changes) and a ``BEFORE DELETE`` trigger that refuses every
   delete; an erasure procedure is a separately approved migration or role, not built here.

No backfill. The downgrade refuses while any row exists, then drops the triggers, the functions
and the table. A downgrade of ``20261121_bpr_0001`` needs this revision downgraded first. Run it
with an explicit target, never ``-1``, on a disposable database only:
``alembic downgrade 20261121_bpr_0001``, then ``alembic upgrade heads``. Never run against
``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261121_psn_0002"
down_revision = "20261121_bpr_0001"
branch_labels = None
depends_on = None

TABLE = "be1_profile_support_needs"
PROFILES = "be1_managed_profiles"
UPDATE_FUNCTION = "guard_be1_profile_support_needs_update"
UPDATE_TRIGGER = "trg_be1_profile_support_needs_update"
DELETE_FUNCTION = "refuse_be1_profile_support_needs_delete"
DELETE_TRIGGER = "trg_be1_profile_support_needs_delete"

CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_be1_profile_support_needs_revision", "revision >= 1"),
    ("ck_be1_profile_support_needs_ciphertext", "octet_length(ciphertext) BETWEEN 16 AND 16384"),
    ("ck_be1_profile_support_needs_nonce", "octet_length(nonce) = 12"),
    ("ck_be1_profile_support_needs_key_id", "char_length(key_id) BETWEEN 1 AND 128"),
    ("ck_be1_profile_support_needs_algorithm", "algorithm_version = 1"),
)

UPDATE_FUNCTION_SQL = f"""
CREATE FUNCTION public.{UPDATE_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.child_id IS DISTINCT FROM OLD.child_id
     OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
    RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_KEY_IMMUTABLE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.revision IS DISTINCT FROM OLD.revision + 1 THEN
    RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_REVISION_STEP'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.nonce IS NOT DISTINCT FROM OLD.nonce THEN
    RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_NONCE_REUSE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END;
$$
"""

DELETE_FUNCTION_SQL = f"""
CREATE FUNCTION public.{DELETE_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_DELETE_FORBIDDEN'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

DOWNGRADE_GUARD = f"""
DO $psn2_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM public.{TABLE}) THEN
        RAISE EXCEPTION 'DDL-D T-12c downgrade refused: BE1 support needs exist';
    END IF;
END;
$psn2_downgrade_guard$;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("child_id", sa.String(length=128), nullable=False),
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
        sa.PrimaryKeyConstraint("child_id", name="pk_be1_profile_support_needs"),
        sa.ForeignKeyConstraint(
            ["child_id"],
            [f"{PROFILES}.child_id"],
            name="fk_be1_profile_support_needs_profile",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("key_id", "nonce", name="uq_be1_profile_support_needs_key_nonce"),
    )
    for name, expression in CHECKS:
        op.create_check_constraint(name, TABLE, expression)
    op.execute(sa.text(UPDATE_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {UPDATE_TRIGGER} BEFORE UPDATE ON public.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION public.{UPDATE_FUNCTION}()"
        )
    )
    op.execute(sa.text(DELETE_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {DELETE_TRIGGER} BEFORE DELETE ON public.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION public.{DELETE_FUNCTION}()"
        )
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(sa.text(f"DROP TRIGGER {DELETE_TRIGGER} ON public.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION public.{DELETE_FUNCTION}()"))
    op.execute(sa.text(f"DROP TRIGGER {UPDATE_TRIGGER} ON public.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION public.{UPDATE_FUNCTION}()"))
    op.drop_table(TABLE)
