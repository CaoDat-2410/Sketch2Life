"""DDL-C part 2: encrypted notification push endpoints (T-8b).

Revision ID: 20261121_nt_0002
Revises: 20261121_pg_0001
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261121_nt_0002"
down_revision = "20261121_pg_0001"
branch_labels = None
depends_on = None

SCHEMA = "notifications"
TABLE = "push_endpoints"
_GUARD_FUNCTION = "notifications.guard_push_endpoint_mutations"
_UPDATE_TRIGGER = "trg_push_endpoint_guard_update"
_DELETE_TRIGGER = "trg_push_endpoint_prevent_delete"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("push_endpoint_id", sa.String(length=36), primary_key=True),
        sa.Column("recipient_account_id", sa.String(length=36), nullable=False),
        sa.Column("platform_kind", sa.String(length=24), nullable=False),
        sa.Column("provider_kind", sa.String(length=24), nullable=False),
        sa.Column("endpoint_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("endpoint_fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "state", sa.String(length=16), server_default=sa.text("'ACTIVE'"), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("app_version", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "platform_kind = 'WEB' AND provider_kind = 'WEB_PUSH'",
            name="ck_push_endpoint_platform_provider",
        ),
        sa.CheckConstraint(
            "octet_length(endpoint_ciphertext) BETWEEN 1 AND 16384",
            name="ck_push_endpoint_ciphertext_size",
        ),
        sa.CheckConstraint(
            "endpoint_fingerprint ~ '^[0-9a-f]{64}$'",
            name="ck_push_endpoint_fingerprint",
        ),
        sa.CheckConstraint("state IN ('ACTIVE', 'REVOKED')", name="ck_push_endpoint_state"),
        sa.CheckConstraint("version >= 1", name="ck_push_endpoint_version"),
        sa.CheckConstraint("last_seen_at >= registered_at", name="ck_push_endpoint_times"),
        sa.CheckConstraint(
            "(state = 'ACTIVE' AND revoked_at IS NULL) OR "
            "(state = 'REVOKED' AND revoked_at IS NOT NULL AND revoked_at >= registered_at)",
            name="ck_push_endpoint_revoked_at",
        ),
        sa.CheckConstraint(
            "app_version IS NULL OR app_version ~ '^[!-~]{1,64}$'",
            name="ck_push_endpoint_app_version",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_push_endpoint_active_provider_fingerprint",
        TABLE,
        ["provider_kind", "endpoint_fingerprint"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.create_index(
        "ix_push_endpoint_recipient_state",
        TABLE,
        ["recipient_account_id", "state"],
        schema=SCHEMA,
    )
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {_GUARD_FUNCTION}() RETURNS trigger AS $$
            DECLARE
                material_changed boolean;
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'push endpoint deletion requires approved retention'
                        USING ERRCODE = '55000';
                END IF;

                IF NEW.push_endpoint_id IS DISTINCT FROM OLD.push_endpoint_id
                   OR NEW.recipient_account_id IS DISTINCT FROM OLD.recipient_account_id
                   OR NEW.platform_kind IS DISTINCT FROM OLD.platform_kind
                   OR NEW.provider_kind IS DISTINCT FROM OLD.provider_kind
                   OR NEW.endpoint_fingerprint IS DISTINCT FROM OLD.endpoint_fingerprint
                   OR NEW.registered_at IS DISTINCT FROM OLD.registered_at THEN
                    RAISE EXCEPTION 'push endpoint owner and registration identity are immutable'
                        USING ERRCODE = '55000';
                END IF;

                IF OLD.state = 'REVOKED' AND NEW.state <> 'REVOKED' THEN
                    RAISE EXCEPTION 'revoked push endpoints cannot be reactivated'
                        USING ERRCODE = '55000';
                END IF;

                IF NEW.state IS DISTINCT FROM OLD.state
                   AND NOT (OLD.state = 'ACTIVE' AND NEW.state = 'REVOKED') THEN
                    RAISE EXCEPTION 'invalid push endpoint state transition'
                        USING ERRCODE = '55000';
                END IF;

                material_changed :=
                    NEW.state IS DISTINCT FROM OLD.state
                    OR NEW.endpoint_ciphertext IS DISTINCT FROM OLD.endpoint_ciphertext
                    OR NEW.last_seen_at IS DISTINCT FROM OLD.last_seen_at
                    OR NEW.app_version IS DISTINCT FROM OLD.app_version
                    OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at;

                IF material_changed AND NEW.version <> OLD.version + 1 THEN
                    RAISE EXCEPTION 'push endpoint material changes require a version increment'
                        USING ERRCODE = '55000';
                ELSIF NOT material_changed AND NEW.version <> OLD.version THEN
                    RAISE EXCEPTION 'push endpoint version cannot change without a material change'
                        USING ERRCODE = '55000';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER {_UPDATE_TRIGGER} BEFORE UPDATE ON {SCHEMA}.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION {_GUARD_FUNCTION}()"
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER {_DELETE_TRIGGER} BEFORE DELETE ON {SCHEMA}.{TABLE} "
            f"FOR EACH ROW EXECUTE FUNCTION {_GUARD_FUNCTION}()"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    has_rows = bind.execute(
        sa.text(f"SELECT EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE} LIMIT 1)")
    ).scalar_one()
    if has_rows:
        raise RuntimeError("push endpoint downgrade refused: rows exist")
    op.execute(sa.text(f"DROP TRIGGER {_DELETE_TRIGGER} ON {SCHEMA}.{TABLE}"))
    op.execute(sa.text(f"DROP TRIGGER {_UPDATE_TRIGGER} ON {SCHEMA}.{TABLE}"))
    op.execute(sa.text(f"DROP FUNCTION {_GUARD_FUNCTION}()"))
    op.drop_index(
        "ix_push_endpoint_recipient_state", table_name=TABLE, schema=SCHEMA
    )
    op.drop_index(
        "uq_push_endpoint_active_provider_fingerprint", table_name=TABLE, schema=SCHEMA
    )
    op.drop_table(TABLE, schema=SCHEMA)
