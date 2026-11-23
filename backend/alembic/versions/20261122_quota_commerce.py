"""Versioned quota products, provider attempts, and school allocations."""

from alembic import op
from sqlalchemy import Boolean, Column, Integer, String, Text, inspect, text

revision = "20261122_quota_commerce"
down_revision = "20261120_admin_ops_retention"
branch_labels = None
depends_on = None


def _add_column_if_missing(table: str, column: Column) -> None:
    names = {item["name"] for item in inspect(op.get_bind()).get_columns(table, schema="billing")}
    if column.name not in names:
        op.add_column(table, column, schema="billing")


def upgrade():
    from sketch2life.infrastructure.persistence.billing_models import BillingBase

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Quota commerce migration requires PostgreSQL")

    _add_column_if_missing("offer_versions", Column("product_id", String(36)))
    _add_column_if_missing("offer_versions", Column("version", Integer(), nullable=False, server_default="1"))
    _add_column_if_missing(
        "offer_versions",
        Column("display_name", String(120), nullable=False, server_default="Gói hạn mức cũ"),
    )
    _add_column_if_missing(
        "offer_versions",
        Column("offer_kind", String(16), nullable=False, server_default="TOP_UP"),
    )
    _add_column_if_missing("offer_versions", Column("cycle_months", Integer()))
    _add_column_if_missing("invoices", Column("product_id", String(36)))
    _add_column_if_missing(
        "invoices",
        Column("payment_mode", String(16), nullable=False, server_default="MANUAL"),
    )
    _add_column_if_missing("payment_events", Column("provider_transaction_ref", String(128)))
    _add_column_if_missing("payment_events", Column("payload_digest", String(64)))
    _add_column_if_missing("video_quota_usage", Column("allocation_id", String(36)))
    _add_column_if_missing("video_quota_usage", Column("teacher_ref", String(256)))

    # The historical uniqueness rule also blocked multiple paid monthly offers per month.
    op.execute("ALTER TABLE billing.video_quota_grants DROP CONSTRAINT IF EXISTS ck_quota_kind")
    op.execute(
        "ALTER TABLE billing.video_quota_grants ADD CONSTRAINT ck_quota_kind "
        "CHECK (kind IN ('INCLUDED','MONTHLY','TOP_UP'))"
    )
    op.execute(
        "ALTER TABLE billing.video_quota_grants "
        "DROP CONSTRAINT IF EXISTS uq_quota_monthly_scope"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_quota_monthly_scope "
        "ON billing.video_quota_grants (owner_kind, owner_ref, period) "
        "WHERE kind = 'INCLUDED' AND period IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_provider_transaction "
        "ON billing.payment_events (provider, provider_transaction_ref) "
        "WHERE provider_transaction_ref IS NOT NULL"
    )

    for name in (
        "video_quota_products",
        "video_quota_product_events",
        "payment_attempts",
        "video_quota_allocations",
        "video_quota_allocation_events",
    ):
        BillingBase.metadata.tables[f"billing.{name}"].create(bind, checkfirst=True)

    _add_column_if_missing("payment_attempts", Column("provider_request_ref", String(64)))
    _add_column_if_missing("payment_attempts", Column("provider_transaction_date", String(14)))

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_billing_attempt_invoice "
        "ON billing.payment_attempts (invoice_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_quota_allocation_org "
        "ON billing.video_quota_allocations (organization_ref, active)"
    )
    # Product catalog rows are mutable pointers; their event history and allocations are append-only.
    for table, trigger in (
        ("video_quota_product_events", "protect_product_events"),
        ("video_quota_allocation_events", "protect_allocation_events"),
    ):
        op.execute(
            f"CREATE TRIGGER {trigger} BEFORE UPDATE OR DELETE ON billing.{table} "
            "FOR EACH ROW EXECUTE FUNCTION billing.reject_ledger_mutation()"
        )


def downgrade():
    raise RuntimeError("Quota commerce ledger history cannot be removed by an automatic downgrade")
