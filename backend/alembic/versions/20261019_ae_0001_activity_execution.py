"""Frozen own11 assignment/history/receipt/event/ACK schema, independent branch."""

from alembic import op

revision = "20261019_ae_0001"
down_revision = None
branch_labels = ("activity_execution",)
depends_on = None

# Literal migration-owned schema descriptors, NEVER import mutable runtime metadata.
TABLES = (
    ("assignment", ("organization_id", "session_id", "assignment_id"), False),
    ("history", ("organization_id", "session_id", "assignment_id"), True),
    ("receipt", ("organization_id", "session_id", "principal_id", "client_key"), False),
    ("event", ("organization_id", "session_id", "event_id"), False),
    ("ack", ("organization_id", "session_id", "event_id"), False),
)
IMMUTABLE = r"""
CREATE FUNCTION activity_execution.immutable_row() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'immutable activity record'; END; $$
"""
GUARD = r"""
CREATE FUNCTION activity_execution.guard_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'activity delete forbidden'; END IF;
 IF (NEW.organization_id,NEW.session_id,NEW.assignment_id) IS DISTINCT FROM
    (OLD.organization_id,OLD.session_id,OLD.assignment_id)
    OR NEW.revision <> OLD.revision + 1
    OR OLD.payload #>> '{value,state}' IN ('completed','skipped','interrupted')
    OR NEW.payload #> '{value,created_at}' IS DISTINCT FROM OLD.payload #> '{value,created_at}'
    OR NEW.payload #> '{value,selected_by}' IS DISTINCT FROM OLD.payload #> '{value,selected_by}'
 THEN RAISE EXCEPTION 'activity stale or immutable assignment'; END IF;
 RETURN NEW;
END; $$
"""


def upgrade() -> None:
    op.execute("CREATE SCHEMA activity_execution")
    for name, keys, revision_key in TABLES:
        columns = ", ".join(f"{key} VARCHAR(120) NOT NULL" for key in keys)
        primary = ",".join((*keys, "revision") if revision_key else keys)
        op.execute(
            f"CREATE TABLE activity_execution.{name} ({columns}, "
            "revision BIGINT NOT NULL, payload JSONB NOT NULL, "
            f"PRIMARY KEY ({primary}), CONSTRAINT {name}_revision CHECK(revision > 0), "
            f"CONSTRAINT {name}_object CHECK(jsonb_typeof(payload) = 'object'))"
        )
    op.execute(IMMUTABLE)
    op.execute(GUARD)
    for table in ("history", "receipt", "event", "ack"):
        op.execute(
            f"CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON activity_execution.{table} "
            "FOR EACH ROW EXECUTE FUNCTION activity_execution.immutable_row()"
        )
    op.execute(
        "CREATE TRIGGER guard_assignment BEFORE UPDATE OR DELETE ON activity_execution.assignment "
        "FOR EACH ROW EXECUTE FUNCTION activity_execution.guard_assignment()"
    )


def downgrade() -> None:
    # Exact own objects, disposable approved test database only, no CASCADE.
    for name, _, _ in reversed(TABLES):
        op.execute(f"DROP TABLE activity_execution.{name}")
    op.execute("DROP FUNCTION activity_execution.guard_assignment()")
    op.execute("DROP FUNCTION activity_execution.immutable_row()")
    op.execute("DROP SCHEMA activity_execution")
