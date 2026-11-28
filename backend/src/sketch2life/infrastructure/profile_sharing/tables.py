"""Core metadata mirror for migration ``20261126_sh_0001``."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

PROFILE_SHARING_METADATA = sa.MetaData(schema="parent")

PROFILE_SHARE_GRANTS = sa.Table(
    "profile_share_grants",
    PROFILE_SHARING_METADATA,
    sa.Column("share_grant_id", UUID(as_uuid=True), nullable=False),
    sa.Column("parent_profile_id", UUID(as_uuid=True), nullable=False),
    sa.Column("grantor_scope_ref", sa.String(64), nullable=False),
    sa.Column("data_origin", sa.String(16), nullable=False),
    sa.Column("consent_basis", sa.String(32), nullable=False),
    sa.Column("granted_fields", JSONB, nullable=False),
    sa.Column("invitation_code_sha256", sa.String(64), nullable=False),
    sa.Column("state", sa.String(16), server_default="INVITED", nullable=False),
    sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("invitation_expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("organization_ref", sa.String(128)),
    sa.Column("class_ref", sa.String(128)),
    sa.Column("managed_profile_ref", sa.String(128)),
    sa.Column("recipient_subject", sa.String(256)),
    sa.Column("accepted_at", sa.DateTime(timezone=True)),
    sa.Column("expires_at", sa.DateTime(timezone=True)),
    sa.Column("revoked_at", sa.DateTime(timezone=True)),
    sa.Column("expired_at", sa.DateTime(timezone=True)),
    sa.ForeignKeyConstraint(
        ["parent_profile_id"],
        ["parent.child_profiles.parent_profile_id"],
        name="fk_psg_parent_profile",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("share_grant_id", name="pk_parent_profile_share_grants"),
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
    sa.CheckConstraint("state IN ('INVITED','ACTIVE','REVOKED','EXPIRED')", name="ck_psg_state"),
    sa.CheckConstraint("revision > 0", name="ck_psg_revision"),
    sa.CheckConstraint(
        "invitation_expires_at > created_at AND invitation_expires_at <= "
        "created_at + interval '90 days'",
        name="ck_psg_invitation_window",
    ),
    sa.CheckConstraint(
        "(organization_ref IS NULL AND class_ref IS NULL AND managed_profile_ref IS NULL "
        "AND recipient_subject IS NULL AND accepted_at IS NULL AND expires_at IS NULL) OR "
        "(organization_ref IS NOT NULL AND class_ref IS NOT NULL AND "
        "managed_profile_ref IS NOT NULL AND recipient_subject IS NOT NULL "
        "AND accepted_at IS NOT NULL AND expires_at = accepted_at + interval '90 days')",
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
)

sa.Index(
    "uq_psg_one_active_link",
    PROFILE_SHARE_GRANTS.c.organization_ref,
    PROFILE_SHARE_GRANTS.c.managed_profile_ref,
    unique=True,
    postgresql_where=PROFILE_SHARE_GRANTS.c.state == "ACTIVE",
)
sa.Index(
    "ix_psg_profile_created",
    PROFILE_SHARE_GRANTS.c.parent_profile_id,
    PROFILE_SHARE_GRANTS.c.created_at.desc(),
    PROFILE_SHARE_GRANTS.c.share_grant_id.desc(),
)
sa.Index(
    "ix_psg_recipient_link",
    PROFILE_SHARE_GRANTS.c.organization_ref,
    PROFILE_SHARE_GRANTS.c.class_ref,
    PROFILE_SHARE_GRANTS.c.managed_profile_ref,
    PROFILE_SHARE_GRANTS.c.recipient_subject,
    postgresql_where=PROFILE_SHARE_GRANTS.c.state == "ACTIVE",
)

__all__ = ["PROFILE_SHARE_GRANTS", "PROFILE_SHARING_METADATA"]
