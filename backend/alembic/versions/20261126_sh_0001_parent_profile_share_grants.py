"""Parent-owned, revocable Teacher profile-share invitations (T-SHARE1)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "20261126_sh_0001"
down_revision = "20261126_sl_0001"
branch_labels = None
depends_on = ("20261121_psn_0001",)

SCHEMA = "parent"
TABLE = "profile_share_grants"


def upgrade() -> None:
    # Preserve the earlier platform-support grants before creating the consented T-SHARE1 table.
    op.execute(
        sa.text(
            """
            DO $legacy_platform_profile_share$
            BEGIN
                IF to_regclass('parent.platform_profile_share_grants') IS NULL
                   AND to_regclass('parent.profile_share_grants') IS NOT NULL
                   AND EXISTS (
                       SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'parent'
                         AND table_name = 'profile_share_grants'
                         AND column_name = 'grant_id'
                   ) THEN
                    ALTER TABLE parent.profile_share_grants
                        RENAME TO platform_profile_share_grants;
                END IF;
            END;
            $legacy_platform_profile_share$;
            """
        )
    )
    op.create_table(
        TABLE,
        sa.Column("share_grant_id", sa.Uuid(), nullable=False),
        sa.Column("parent_profile_id", sa.Uuid(), nullable=False),
        sa.Column("grantor_scope_ref", sa.String(length=64), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("consent_basis", sa.String(length=32), nullable=False),
        sa.Column("granted_fields", JSONB(), nullable=False),
        sa.Column("invitation_code_sha256", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), server_default="INVITED", nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("invitation_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_ref", sa.String(length=128), nullable=True),
        sa.Column("class_ref", sa.String(length=128), nullable=True),
        sa.Column("managed_profile_ref", sa.String(length=128), nullable=True),
        sa.Column("recipient_subject", sa.String(length=256), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("grantor_scope_ref ~ '^[0-9a-f]{64}$'", name="ck_psg_grantor_ref"),
        sa.CheckConstraint("data_origin IN ('SYNTHETIC_DEV','REAL')", name="ck_psg_data_origin"),
        sa.CheckConstraint("consent_basis = 'PARENT_GRANT_ACT_V1'", name="ck_psg_consent_basis"),
        sa.CheckConstraint(
            "CASE WHEN jsonb_typeof(granted_fields) = 'array' THEN "
            "jsonb_array_length(granted_fields) BETWEEN 1 AND 3 AND granted_fields "
            "<@ '[\"DISPLAY_NAME\",\"AGE_BAND\",\"INTERESTS_SUMMARY\"]'::jsonb "
            "ELSE false END",
            name="ck_psg_fields",
        ),
        sa.UniqueConstraint("invitation_code_sha256", name="uq_psg_invitation_code"),
        sa.CheckConstraint("invitation_code_sha256 ~ '^[0-9a-f]{64}$'", name="ck_psg_code_hash"),
        sa.CheckConstraint(
            "state IN ('INVITED','ACTIVE','REVOKED','EXPIRED')", name="ck_psg_state"
        ),
        sa.CheckConstraint("revision > 0", name="ck_psg_revision"),
        sa.CheckConstraint(
            "invitation_expires_at > created_at AND invitation_expires_at <= "
            "created_at + interval '2160 hours'",
            name="ck_psg_invitation_window",
        ),
        sa.CheckConstraint(
            "(organization_ref IS NULL AND class_ref IS NULL AND managed_profile_ref IS NULL "
            "AND recipient_subject IS NULL AND accepted_at IS NULL AND expires_at IS NULL) OR "
            "(organization_ref IS NOT NULL AND class_ref IS NOT NULL AND "
            "managed_profile_ref IS NOT NULL AND recipient_subject IS NOT NULL "
            "AND accepted_at IS NOT NULL AND expires_at = accepted_at + interval '2160 hours')",
            name="ck_psg_link_fields",
        ),
        sa.CheckConstraint(
            "(state = 'INVITED' AND accepted_at IS NULL AND revoked_at IS NULL "
            "AND expired_at IS NULL) OR "
            "(state = 'ACTIVE' AND accepted_at IS NOT NULL AND revoked_at IS NULL "
            "AND expired_at IS NULL) OR "
            "(state = 'REVOKED' AND revoked_at IS NOT NULL AND expired_at IS NULL) OR "
            "(state = 'EXPIRED' AND expired_at IS NOT NULL AND revoked_at IS NULL)",
            name="ck_psg_state_fields",
        ),
        sa.ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_psg_parent_profile",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("share_grant_id", name="pk_parent_profile_share_grants"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_psg_one_active_link",
        TABLE,
        ["organization_ref", "managed_profile_ref"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.create_index(
        "ix_psg_profile_created",
        TABLE,
        ["parent_profile_id", sa.text("created_at DESC"), sa.text("share_grant_id DESC")],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_psg_recipient_link",
        TABLE,
        ["organization_ref", "class_ref", "managed_profile_ref", "recipient_subject"],
        schema=SCHEMA,
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.execute(
        """
        CREATE FUNCTION parent.protect_profile_share_grant()
        RETURNS trigger
        LANGUAGE plpgsql
        SET search_path = pg_catalog, parent
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    MESSAGE = 'PROFILE_SHARE_GRANT_DELETE_FORBIDDEN';
            END IF;
            IF TG_OP = 'INSERT' THEN
                IF NEW.state <> 'INVITED' OR NEW.revision <> 1 THEN
                    RAISE EXCEPTION USING ERRCODE = '23514',
                        MESSAGE = 'PROFILE_SHARE_GRANT_INSERT_STATE';
                END IF;
                RETURN NEW;
            END IF;
            IF NEW.share_grant_id IS DISTINCT FROM OLD.share_grant_id
               OR NEW.parent_profile_id IS DISTINCT FROM OLD.parent_profile_id
               OR NEW.grantor_scope_ref IS DISTINCT FROM OLD.grantor_scope_ref
               OR NEW.data_origin IS DISTINCT FROM OLD.data_origin
               OR NEW.consent_basis IS DISTINCT FROM OLD.consent_basis
               OR NEW.granted_fields IS DISTINCT FROM OLD.granted_fields
               OR NEW.invitation_code_sha256 IS DISTINCT FROM OLD.invitation_code_sha256
               OR NEW.created_at IS DISTINCT FROM OLD.created_at
               OR NEW.invitation_expires_at IS DISTINCT FROM OLD.invitation_expires_at THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    MESSAGE = 'PROFILE_SHARE_GRANT_IMMUTABLE';
            END IF;
            IF OLD.accepted_at IS NOT NULL AND (
               NEW.organization_ref IS DISTINCT FROM OLD.organization_ref
               OR NEW.class_ref IS DISTINCT FROM OLD.class_ref
               OR NEW.managed_profile_ref IS DISTINCT FROM OLD.managed_profile_ref
               OR NEW.recipient_subject IS DISTINCT FROM OLD.recipient_subject
               OR NEW.accepted_at IS DISTINCT FROM OLD.accepted_at
               OR NEW.expires_at IS DISTINCT FROM OLD.expires_at) THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    MESSAGE = 'PROFILE_SHARE_GRANT_LINK_IMMUTABLE';
            END IF;
            IF NOT ((OLD.state = 'INVITED' AND NEW.state IN ('ACTIVE','REVOKED','EXPIRED'))
                OR (OLD.state = 'ACTIVE' AND NEW.state IN ('REVOKED','EXPIRED'))) THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    MESSAGE = 'PROFILE_SHARE_GRANT_ILLEGAL_TRANSITION';
            END IF;
            IF NEW.revision <> OLD.revision + 1 THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    MESSAGE = 'PROFILE_SHARE_GRANT_REVISION';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protect_profile_share_grant
        BEFORE INSERT OR UPDATE OR DELETE ON parent.profile_share_grants
        FOR EACH ROW EXECUTE FUNCTION parent.protect_profile_share_grant()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM parent.profile_share_grants) THEN
                RAISE EXCEPTION 'T-SHARE1 downgrade refused: profile-share grant rows exist';
            END IF;
        END;
        $$
        """
    )
    op.execute(
        "DROP TRIGGER trg_protect_profile_share_grant ON parent.profile_share_grants"
    )
    op.drop_table(TABLE, schema=SCHEMA)
    op.execute("DROP FUNCTION parent.protect_profile_share_grant()")
