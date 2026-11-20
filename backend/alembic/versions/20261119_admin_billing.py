"""Independent sandbox billing and product video quota ledger."""

from alembic import op

revision = "20261119_admin_billing"
down_revision = "20261119_admin_publication"
branch_labels = None
depends_on = None


def upgrade():
    from sketch2life.infrastructure.persistence.billing_models import BillingBase

    op.execute("CREATE SCHEMA IF NOT EXISTS billing")
    for name in (
        "offer_versions",
        "invoices",
        "payment_events",
        "video_quota_grants",
        "video_quota_usage",
        "command_receipts",
    ):
        BillingBase.metadata.tables["billing." + name].create(op.get_bind())
    # Grant/usage/payment evidence must not be rewritten by ordinary application commands.
    op.execute(
        "CREATE FUNCTION billing.reject_ledger_mutation() RETURNS trigger "
        "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION "
        "'BILLING_LEDGER_IMMUTABLE'; END; $$"
    )
    for table in ("video_quota_grants", "video_quota_usage", "payment_events", "offer_versions"):
        op.execute(
            f"CREATE TRIGGER protect_ledger BEFORE UPDATE OR DELETE ON billing.{table} "
            "FOR EACH ROW EXECUTE FUNCTION billing.reject_ledger_mutation()"
        )


def downgrade():
    raise RuntimeError("Billing ledger history cannot be removed by an automatic downgrade")
