"""Frozen own preset/automation rows; does not write session/config tables."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "20261019_pa_0001"
down_revision = None
branch_labels = ("preset_automation",)
depends_on = None
SCHEMA = "preset_automation"


def upgrade() -> None:
    op.execute('CREATE SCHEMA "preset_automation"')
    for name in ("head", "history"):
        op.create_table(
            name,
            sa.Column("organization_id", sa.String(128), primary_key=True),
            sa.Column("scope", sa.String(128), primary_key=True),
            sa.Column("object_key", sa.String(128), primary_key=True),
            sa.Column("revision", sa.BigInteger(), primary_key=name == "history", nullable=False),
            sa.Column("payload", JSONB(), nullable=False),
            sa.CheckConstraint("revision >= 1", name=f"ck_pa_{name}_revision"),
            schema=SCHEMA,
        )
    op.execute("""
      CREATE FUNCTION preset_automation.guard_rows() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_TABLE_NAME = 'history' OR TG_OP = 'DELETE' THEN
          RAISE EXCEPTION 'immutable preset history';
        END IF;
        IF COALESCE(OLD.payload->>'kind','') NOT IN ('library','intent') OR
           NEW.payload->>'kind' IS DISTINCT FROM OLD.payload->>'kind' OR
           NEW.organization_id IS DISTINCT FROM OLD.organization_id OR
           NEW.scope IS DISTINCT FROM OLD.scope OR
           NEW.object_key IS DISTINCT FROM OLD.object_key OR
           NEW.revision <> OLD.revision + 1 OR
           NEW.payload->'value'->>'revision' IS DISTINCT FROM NEW.revision::text THEN
          RAISE EXCEPTION 'immutable preset receipt or invalid CAS';
        END IF;
        IF OLD.payload->>'kind' = 'intent' AND
           OLD.payload->'value'->>'state' NOT IN ('queued','deferred','sending') THEN
          RAISE EXCEPTION 'terminal intent';
        END IF;
        RETURN NEW;
      END $$
    """)
    for name in ("head", "history"):
        op.execute(
            f'CREATE TRIGGER guard_rows BEFORE UPDATE OR DELETE ON preset_automation."{name}" '
            "FOR EACH ROW EXECUTE FUNCTION preset_automation.guard_rows()"
        )


def downgrade() -> None:
    for name in ("history", "head"):
        op.drop_table(name, schema=SCHEMA)
    op.execute("DROP FUNCTION preset_automation.guard_rows()")
    op.execute('DROP SCHEMA "preset_automation"')
