"""DDL-F: typed owner scope, a fifth purpose and validation provenance for upload sessions.

FEAT-066 goal v3, T-2a (generic upload sessions, SRS FR-C-12, l.1654-1658). It extends the
``lesson_library`` branch (parent ``20261119_ar_0002``); it adds no branch label and creates or
drops no table. All statements alter ``core_upload_sessions``; ``core_upload_parts`` is unchanged
(per-part SHA-256, size and an opaque object reference already fit SRS l.1935).

Upgrade, in order:

1. ``organization_id`` becomes nullable (a Parent session has no organization).
2. ``owner_scope_kind`` (default ``ORGANIZATION``) and ``owner_scope_ref`` are added with the
   FR-C-08 typed owner-scope CHECK. Existing lesson rows become ``ORGANIZATION`` rows with a
   NULL ref and satisfy it; no backfill.
3. ``ck_core_upload_purpose`` accepts ``OCCURRENCE_DOCUMENT`` (Teacher occurrence documents). A
   separate purpose keeps these sessions invisible to the lesson routes, which load by
   ``purpose = 'LESSON_SOURCE'``.
4. ``error_code``, ``scan_verdict``, ``scanner_name``, ``scanner_version`` and ``validated_at`` are
   added (the session is the operational copy; ``core_asset_lineage`` stays the provenance record).
5. Two indexes serve the scope lookups of the generic routes and the FR-C-08 run close.

The CHECK is added directly, which suits a disposable verification database; a production rollout
uses ``NOT VALID`` then ``VALIDATE`` (as the FR-C-08 migration does).

The downgrade refuses while any row has a non-organization scope or the new purpose, otherwise it
reverses every step (the five new columns lose their data). Never run against
``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261119_uf_0001"
down_revision = "20261119_ar_0002"
branch_labels = None
depends_on = None

# Same text as ``core_models.OWNER_SCOPE_CHECK`` and the FR-C-08 migration.
OWNER_SCOPE_CHECK = (
    "(owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL "
    "AND length(owner_scope_ref) > 0 "
    "AND organization_id IS NULL) OR "
    "(owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL "
    "AND (owner_scope_ref IS NULL OR "
    "(length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id)))"
)
PURPOSE_BEFORE = "'PROFILE_IMAGE', 'RUN_ARTWORK', 'RUN_AUDIO', 'LESSON_SOURCE'"
PURPOSE_AFTER = f"{PURPOSE_BEFORE}, 'OCCURRENCE_DOCUMENT'"
TABLE = "core_upload_sessions"
NEW_COLUMNS = (
    "error_code",
    "scan_verdict",
    "scanner_name",
    "scanner_version",
    "validated_at",
)

DOWNGRADE_GUARD = """
DO $uf_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM core_upload_sessions
               WHERE owner_scope_kind <> 'ORGANIZATION' OR purpose = 'OCCURRENCE_DOCUMENT')
    THEN
        RAISE EXCEPTION 'DDL-F downgrade refused: generic or occurrence upload sessions exist';
    END IF;
END;
$uf_downgrade_guard$;
"""


def upgrade() -> None:
    op.alter_column(
        TABLE,
        "organization_id",
        existing_type=sa.String(128),
        existing_nullable=False,
        nullable=True,
    )
    op.add_column(
        TABLE,
        sa.Column(
            "owner_scope_kind",
            sa.String(32),
            nullable=False,
            server_default=sa.text("'ORGANIZATION'"),
        ),
    )
    op.add_column(TABLE, sa.Column("owner_scope_ref", sa.String(128), nullable=True))
    op.create_check_constraint("ck_core_upload_owner_scope", TABLE, OWNER_SCOPE_CHECK)
    op.drop_constraint("ck_core_upload_purpose", TABLE, type_="check")
    op.create_check_constraint("ck_core_upload_purpose", TABLE, f"purpose IN ({PURPOSE_AFTER})")
    op.add_column(TABLE, sa.Column("error_code", sa.String(64), nullable=True))
    op.add_column(TABLE, sa.Column("scan_verdict", sa.String(16), nullable=True))
    op.add_column(TABLE, sa.Column("scanner_name", sa.String(64), nullable=True))
    op.add_column(TABLE, sa.Column("scanner_version", sa.String(64), nullable=True))
    op.add_column(TABLE, sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_core_upload_scope_state",
        TABLE,
        ["owner_scope_kind", "owner_scope_ref", "state", "expires_at"],
    )
    op.create_index("ix_core_upload_target_state", TABLE, ["target_ref", "state"])


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.drop_index("ix_core_upload_target_state", table_name=TABLE)
    op.drop_index("ix_core_upload_scope_state", table_name=TABLE)
    for column in reversed(NEW_COLUMNS):
        op.drop_column(TABLE, column)
    op.drop_constraint("ck_core_upload_purpose", TABLE, type_="check")
    op.create_check_constraint("ck_core_upload_purpose", TABLE, f"purpose IN ({PURPOSE_BEFORE})")
    op.drop_constraint("ck_core_upload_owner_scope", TABLE, type_="check")
    op.drop_column(TABLE, "owner_scope_ref")
    op.drop_column(TABLE, "owner_scope_kind")
    op.alter_column(
        TABLE,
        "organization_id",
        existing_type=sa.String(128),
        existing_nullable=True,
        nullable=False,
    )
