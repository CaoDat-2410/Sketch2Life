"""Allow safe closure of expired VNPay quota invoices."""

from alembic import op

revision = "20261123_vnpay_cancel"
down_revision = "20261123_vnpay_order_info"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE billing.invoices DROP CONSTRAINT IF EXISTS ck_billing_invoice_state")
    op.execute(
        "ALTER TABLE billing.invoices ADD CONSTRAINT ck_billing_invoice_state "
        "CHECK (state IN ('PENDING','PAID','FAILED','CANCELED'))"
    )
    op.execute("ALTER TABLE billing.payment_attempts DROP CONSTRAINT IF EXISTS ck_billing_payment_attempt_state")
    op.execute(
        "ALTER TABLE billing.payment_attempts ADD CONSTRAINT ck_billing_payment_attempt_state "
        "CHECK (provider IN ('MOMO','VNPAY') AND "
        "state IN ('REQUESTING','OPEN','UNKNOWN','FAILED','PAID','CANCELED'))"
    )


def downgrade():
    raise RuntimeError("Payment cancellation history cannot be removed by an automatic downgrade")
