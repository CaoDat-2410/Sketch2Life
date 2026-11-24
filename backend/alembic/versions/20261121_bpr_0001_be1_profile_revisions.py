"""DDL-D (T-12b): immutable Teacher profile revisions and the head of each managed profile.

FEAT-066 goal v4, T-12b (``GET .../profiles/{child_id}/revisions``, ``GET .../revisions/{id}`` and
``PATCH .../profiles/{child_id}``; SRS l.496-499 FR-C-04 to FR-C-07, l.829 head and ownership,
l.2336; REG l.272, l.335, l.425). The package is approved by the owner's Phase B launch. Parent of
this revision is ``20261123_rv_0001``, the head of the Story branch: its full ancestry (through
``depends_on``) holds ``20261101_be1_age_0001`` and ``20261014_0002``, where the BE1 profile table
is created and altered, so ``public.be1_managed_profiles`` exists when this runs. The revision
sits on the ``frc08_lifecycle`` branch, not on ``be1_core``: an existing database needs one
``alembic upgrade heads``. Alembic heads stay 15 down-only (10 dependency-aware); the graph has
53 revisions (T-12c adds two more later).

Upgrade, in order:

1. ``public.be1_profile_revisions``: one immutable snapshot of the fields a Teacher may edit
   (display name, age with its versioned age band, bounded structured interests). The foreign key
   to the profile is ``ON DELETE RESTRICT``: no code deletes a profile, and the purge of
   revisions and receipts (FR-C-10) is a later reviewed task (OPEN-4).
2. Two nullable head columns on ``public.be1_managed_profiles``.
3. A deterministic baseline: revision 1 per profile (``uuid5`` of the child id), author
   ``LEGACY_UNCLASSIFIED``, no interests, the profile's own creation time. It is a baseline as of
   this migration, not a reconstructed history.
4. A reconciliation (counts, heads, name, age, recomputed hash). Any mismatch aborts the
   migration; the columns are never left nullable on a database that does not reconcile.
5. ``NOT NULL`` on both head columns, ``profile_revision_no >= 1``.
6. The composite head foreign key ``(child_id, current_profile_revision_id)`` to
   ``(child_id, profile_revision_id)``, ``DEFERRABLE INITIALLY DEFERRED`` so a profile and its new
   revision are written in one transaction.
7. A ``BEFORE UPDATE OR DELETE`` trigger that makes the revisions append only, and two deferred
   constraint triggers (``be1_profile_head_consistent``): at commit the head must point at an
   existing revision of the same child with the head number, and no revision of that child may
   have a higher number.

The hash and the baseline id are computed here by copies of the functions in
``sketch2life.domain.be1_profile_revisions`` (a migration does not import application code); a
unit test pins the copies equal.

The downgrade refuses unless every revision is an untouched migration baseline (revision 1,
author ``LEGACY_UNCLASSIFIED``, no interests, equal to its profile's projection): only then does
it drop nothing that ``upgrade`` cannot rebuild. A profile created through the API after the
migration has a real author, so its revision blocks the downgrade. It then drops the triggers,
the head foreign key, the head columns, the table and the functions. Run it with an explicit
target, never ``-1`` (the graph has many heads), on a disposable database only:
``alembic downgrade 20261123_rv_0001``, then ``alembic upgrade heads``.
Never run against ``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261121_bpr_0001"
down_revision = "20261123_rv_0001"
branch_labels = None
depends_on = None

TABLE = "be1_profile_revisions"
PROFILES = "be1_managed_profiles"
HEAD_ID = "current_profile_revision_id"
HEAD_NO = "profile_revision_no"
HEAD_FK = "fk_be1_profile_head_revision"
HEAD_CHECK = "ck_be1_profile_revision_no"
APPEND_ONLY_FUNCTION = "reject_be1_profile_revision_change"
APPEND_ONLY_TRIGGER = "trg_be1_profile_revisions_append_only"
HEAD_FUNCTION = "be1_profile_head_consistent"
HEAD_TRIGGER_PROFILE = "trg_be1_profile_head_consistent"
HEAD_TRIGGER_REVISION = "trg_be1_profile_revisions_head_consistent"
LEGACY_AUTHOR = "LEGACY_UNCLASSIFIED"

# --- copies of the domain functions (pinned equal by tests/unit/test_be1_profile_revisions.py) ---
_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "urn:sketch2life:be1:profile-revision-baseline:v1")


def _baseline_id(child_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, child_id))


def _band(age_months: int) -> tuple[int, str] | None:
    if age_months <= 71:
        return 1, "AGE_36_71"
    if age_months <= 107:
        return 1, "AGE_72_107"
    if age_months <= 120:
        return 1, "AGE_108_120"
    return None


def _hash(
    child_id: str,
    revision_no: int,
    display_name: str,
    age_months: int,
    interests: Sequence[str],
) -> str:
    band = _band(age_months)
    payload = json.dumps(
        {
            "domain": "be1.profile.revision",
            "v": 1,
            "child_id": child_id,
            "revision_no": revision_no,
            "display_name": display_name,
            "age_months": age_months,
            "age_band": None if band is None else {"version": band[0], "code": band[1]},
            "structured_interests": list(interests),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


APPEND_ONLY_FUNCTION_SQL = f"""
CREATE FUNCTION public.{APPEND_ONLY_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'BE1_PROFILE_REVISION_IS_APPEND_ONLY'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

HEAD_FUNCTION_SQL = f"""
CREATE FUNCTION public.{HEAD_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  head_id varchar(36);
  head_no integer;
BEGIN
  SELECT p.{HEAD_ID}, p.{HEAD_NO} INTO head_id, head_no
    FROM public.{PROFILES} p WHERE p.child_id = NEW.child_id;
  IF NOT FOUND THEN
    RETURN NULL;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.{TABLE} r
     WHERE r.child_id = NEW.child_id
       AND r.profile_revision_id = head_id
       AND r.revision_no = head_no
  ) THEN
    RAISE EXCEPTION 'BE1_PROFILE_HEAD_MISMATCH'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.{TABLE} r
     WHERE r.child_id = NEW.child_id AND r.revision_no > head_no
  ) THEN
    RAISE EXCEPTION 'BE1_PROFILE_HEAD_NOT_LATEST'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NULL;
END;
$$
"""

DOWNGRADE_GUARD = f"""
DO $bpr_downgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.{TABLE} r
         WHERE r.revision_no <> 1 OR r.structured_interests <> '[]'::jsonb
            OR r.authored_by <> '{LEGACY_AUTHOR}'
    ) OR EXISTS (
        SELECT 1 FROM public.{PROFILES} p
          JOIN public.{TABLE} r ON r.child_id = p.child_id AND r.revision_no = 1
         WHERE p.display_name <> r.display_name OR p.age_months <> r.age_months
            OR p.{HEAD_ID} <> r.profile_revision_id OR p.{HEAD_NO} <> 1
    ) THEN
        RAISE EXCEPTION 'DDL-D T-12b downgrade refused: revisions beyond the baseline exist';
    END IF;
END;
$bpr_downgrade_guard$;
"""


def _create_revision_table() -> None:
    op.create_table(
        TABLE,
        sa.Column("profile_revision_id", sa.String(length=36), nullable=False),
        sa.Column("child_id", sa.String(length=128), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("age_months", sa.Integer(), nullable=False),
        sa.Column("age_band_version", sa.Integer(), nullable=True),
        sa.Column("age_band_code", sa.String(length=32), nullable=True),
        sa.Column(
            "structured_interests",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("authored_by", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revision_hash_version", sa.Integer(), nullable=False),
        sa.Column("revision_hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("profile_revision_id", name="pk_be1_profile_revisions"),
        sa.ForeignKeyConstraint(
            ["child_id"],
            [f"{PROFILES}.child_id"],
            name="fk_be1_profile_revision_profile",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("child_id", "revision_no", name="uq_be1_profile_revision_no"),
        sa.UniqueConstraint("child_id", "profile_revision_id", name="uq_be1_profile_revision_pair"),
        sa.CheckConstraint("revision_no >= 1", name="ck_be1_profile_revision_no_positive"),
        sa.CheckConstraint(
            "char_length(btrim(display_name)) >= 1", name="ck_be1_profile_revision_name"
        ),
        sa.CheckConstraint("age_months BETWEEN 36 AND 155", name="ck_be1_profile_revision_age"),
        sa.CheckConstraint(
            "(age_months BETWEEN 36 AND 71 AND age_band_version = 1"
            " AND age_band_code = 'AGE_36_71')"
            " OR (age_months BETWEEN 72 AND 107 AND age_band_version = 1"
            " AND age_band_code = 'AGE_72_107')"
            " OR (age_months BETWEEN 108 AND 120 AND age_band_version = 1"
            " AND age_band_code = 'AGE_108_120')"
            " OR (age_months > 120 AND age_band_version IS NULL AND age_band_code IS NULL)",
            name="ck_be1_profile_revision_band",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(structured_interests) = 'array'"
            " AND octet_length(structured_interests::text) <= 8192",
            name="ck_be1_profile_revision_interests",
        ),
        sa.CheckConstraint(
            "revision_hash_version = 1 AND revision_hash ~ '^[0-9a-f]{64}$'",
            name="ck_be1_profile_revision_hash",
        ),
    )


def _baseline_row(row: sa.Row[tuple[str, str, int, object]]) -> dict[str, object]:
    band = _band(row.age_months)
    return {
        "profile_revision_id": _baseline_id(row.child_id),
        "child_id": row.child_id,
        "display_name": row.display_name,
        "age_months": row.age_months,
        "age_band_version": None if band is None else band[0],
        "age_band_code": None if band is None else band[1],
        "authored_by": LEGACY_AUTHOR,
        "created_at": row.created_at,
        "revision_hash": _hash(row.child_id, 1, row.display_name, row.age_months, []),
    }


def _backfill_baseline() -> None:
    bind = op.get_bind()
    profiles = bind.execute(
        sa.text(
            f"SELECT child_id, display_name, age_months, created_at FROM public.{PROFILES} "
            "ORDER BY child_id"
        )
    ).all()
    if profiles:
        bind.execute(
            sa.text(
                f"INSERT INTO public.{TABLE} (profile_revision_id, child_id, revision_no, "
                "display_name, age_months, age_band_version, age_band_code, structured_interests, "
                "authored_by, created_at, revision_hash_version, revision_hash) VALUES "
                "(:profile_revision_id, :child_id, 1, :display_name, :age_months, "
                ":age_band_version, :age_band_code, CAST('[]' AS jsonb), :authored_by, "
                ":created_at, 1, :revision_hash)"
            ),
            [_baseline_row(row) for row in profiles],
        )
    bind.execute(
        sa.text(
            f"UPDATE public.{PROFILES} p SET {HEAD_ID} = r.profile_revision_id, {HEAD_NO} = 1 "
            f"FROM public.{TABLE} r WHERE r.child_id = p.child_id AND r.revision_no = 1"
        )
    )


def _reconcile_baseline() -> None:
    """Abort on any mismatch; the message carries counts only (never a name)."""
    bind = op.get_bind()
    profile_count = bind.execute(sa.text(f"SELECT count(*) FROM public.{PROFILES}")).scalar_one()
    revision_count = bind.execute(sa.text(f"SELECT count(*) FROM public.{TABLE}")).scalar_one()
    unheaded = bind.execute(
        sa.text(f"SELECT count(*) FROM public.{PROFILES} WHERE {HEAD_ID} IS NULL")
    ).scalar_one()
    drift = bind.execute(
        sa.text(
            f"SELECT count(*) FROM public.{PROFILES} p JOIN public.{TABLE} r "
            f"ON r.child_id = p.child_id AND r.profile_revision_id = p.{HEAD_ID} "
            f"AND r.revision_no = p.{HEAD_NO} "
            "WHERE p.display_name <> r.display_name OR p.age_months <> r.age_months"
        )
    ).scalar_one()
    bad_hash = 0
    for row in bind.execute(
        sa.text(
            "SELECT child_id, revision_no, display_name, age_months, structured_interests, "
            f"revision_hash FROM public.{TABLE}"
        )
    ):
        expected = _hash(
            row.child_id,
            row.revision_no,
            row.display_name,
            row.age_months,
            row.structured_interests,
        )
        if expected != row.revision_hash:
            bad_hash += 1
    if profile_count != revision_count or unheaded or drift or bad_hash:
        raise RuntimeError(
            "DDL-D T-12b baseline does not reconcile: "
            f"profiles={profile_count} revisions={revision_count} unheaded={unheaded} "
            f"drift={drift} bad_hash={bad_hash}"
        )


def upgrade() -> None:
    _create_revision_table()
    op.add_column(PROFILES, sa.Column(HEAD_ID, sa.String(length=36), nullable=True))
    op.add_column(PROFILES, sa.Column(HEAD_NO, sa.Integer(), nullable=True))
    _backfill_baseline()
    _reconcile_baseline()
    op.alter_column(PROFILES, HEAD_ID, existing_type=sa.String(length=36), nullable=False)
    op.alter_column(PROFILES, HEAD_NO, existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(HEAD_CHECK, PROFILES, f"{HEAD_NO} >= 1")
    op.create_foreign_key(
        HEAD_FK,
        PROFILES,
        TABLE,
        ["child_id", HEAD_ID],
        ["child_id", "profile_revision_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.execute(sa.text(APPEND_ONLY_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE TRIGGER {APPEND_ONLY_TRIGGER} BEFORE UPDATE OR DELETE ON public.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION public.{APPEND_ONLY_FUNCTION}()"
        )
    )
    op.execute(sa.text(HEAD_FUNCTION_SQL))
    op.execute(
        sa.text(
            f"CREATE CONSTRAINT TRIGGER {HEAD_TRIGGER_PROFILE} "
            f"AFTER INSERT OR UPDATE OF {HEAD_ID}, {HEAD_NO} ON public.{PROFILES} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            f"EXECUTE FUNCTION public.{HEAD_FUNCTION}()"
        )
    )
    op.execute(
        sa.text(
            f"CREATE CONSTRAINT TRIGGER {HEAD_TRIGGER_REVISION} "
            f"AFTER INSERT ON public.{TABLE} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            f"EXECUTE FUNCTION public.{HEAD_FUNCTION}()"
        )
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(sa.text(f"DROP TRIGGER {HEAD_TRIGGER_REVISION} ON public.{TABLE}"))
    op.execute(sa.text(f"DROP TRIGGER {HEAD_TRIGGER_PROFILE} ON public.{PROFILES}"))
    op.execute(sa.text(f"DROP FUNCTION public.{HEAD_FUNCTION}()"))
    op.execute(sa.text(f"DROP TRIGGER {APPEND_ONLY_TRIGGER} ON public.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION public.{APPEND_ONLY_FUNCTION}()"))
    op.drop_constraint(HEAD_FK, PROFILES, type_="foreignkey")
    op.drop_constraint(HEAD_CHECK, PROFILES, type_="check")
    op.drop_column(PROFILES, HEAD_NO)
    op.drop_column(PROFILES, HEAD_ID)
    op.drop_table(TABLE)
