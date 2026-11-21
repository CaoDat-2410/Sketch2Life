"""Versioned test capacity prices, subscriptions and immutable event history."""

from alembic import op

revision = "20261119_capacity_sandbox"
down_revision = "20261119_account_activation"
branch_labels = None
depends_on = None


def upgrade():
    from sketch2life.infrastructure.persistence.billing_models import (
        CapacityPriceModel,
        SubscriptionEventModel,
        SubscriptionModel,
    )

    for model in (CapacityPriceModel, SubscriptionModel, SubscriptionEventModel):
        model.__table__.create(op.get_bind())
    for table in ("capacity_price_versions", "subscription_events"):
        op.execute(
            f"CREATE TRIGGER protect_ledger BEFORE UPDATE OR DELETE ON billing.{table} "
            "FOR EACH ROW EXECUTE FUNCTION billing.reject_ledger_mutation()"
        )


def downgrade():
    raise RuntimeError("Subscription history requires a retention-aware migration")
