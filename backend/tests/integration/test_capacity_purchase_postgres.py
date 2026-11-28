"""Disposable PostgreSQL coverage for capacity settlement and advisory locks."""

import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.billing import capacity_commerce
from sketch2life.infrastructure.billing.capacity_commerce import CapacityCommerceService
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.persistence.billing_models import (
    BillingPaymentAttemptModel,
    CapacityPriceModel,
    SubscriptionModel,
    VideoQuotaGrantModel,
)


def test_paid_capacity_purchase_is_additive_and_excluded_from_quota(monkeypatch):
    url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed capacity tests")
    if "be1_acceptance" not in url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    engine = create_engine(url)
    org, sub, price = (str(uuid4()) for _ in range(3))
    actor = "synthetic-capacity-" + org
    now = datetime.now(UTC)
    settings = SimpleNamespace(
        billing_real_payments_enabled=True,
        momo_payment_configured=True,
        vnpay_payment_configured=False,
    )
    monkeypatch.setattr(
        capacity_commerce,
        "create_momo_checkout",
        lambda *args, **kwargs: {
            "checkout_url": "https://example.test/pay",
            "expires_at": now + timedelta(minutes=15),
        },
    )
    invoice_id = None
    try:
        with Session(engine) as db:
            db.add(
                CapacityPriceModel(
                    price_id=price,
                    cycle_months=1,
                    base_amount_vnd=10000,
                    slot_amount_vnd=10000,
                    created_by=actor,
                )
            )
            db.add(
                SubscriptionModel(
                    subscription_id=sub,
                    organization_ref=org,
                    price_id=price,
                    addon_slots=1,
                    state="ACTIVE",
                    period_start=now - timedelta(days=15),
                    period_end=now + timedelta(days=15),
                    revision=1,
                )
            )
            db.commit()
            service = CapacityCommerceService(db, actor, settings, clock=lambda: now)
            quote = capacity_commerce.capacity_quote(db, org, 2, now, settings)
            fields = dict(
                expected_amount_vnd=quote["amount_vnd"],
                price_id=quote["price_id"],
                period_end=datetime.fromisoformat(quote["period_end"]),
                quoted_at=now,
            )
            checkout = service.checkout_slots(org, 2, "MOMO", "test-key", **fields)
            invoice_id = checkout["invoice_id"]
            assert service.checkout_slots(org, 2, "MOMO", "test-key", **fields) == checkout
            subscription = db.get(SubscriptionModel, sub)
            subscription.state = "CANCEL_AT_PERIOD_END"
            subscription.revision += 1
            db.commit()
            attempt = db.scalar(
                select(BillingPaymentAttemptModel).where(
                    BillingPaymentAttemptModel.invoice_id == invoice_id
                )
            )
            kwargs = dict(
                provider="MOMO",
                order_ref=attempt.provider_order_ref,
                transaction_ref=org,
                amount_vnd=checkout["amount_vnd"],
                paid=True,
                payload_digest="digest",
            )
            assert not service.settle_verified(**kwargs)["duplicate"]
            assert service.settle_verified(**kwargs)["duplicate"]
            db.refresh(subscription)
            assert subscription.addon_slots == 3 and subscription.state == "CANCEL_AT_PERIOD_END"
            assert (
                db.scalar(
                    select(VideoQuotaGrantModel).where(
                        VideoQuotaGrantModel.invoice_id == invoice_id
                    )
                )
                is None
            )
            assert (
                QuotaCommerceService(db, actor, settings).invoices("ORGANIZATION", org)["total"]
                == 0
            )
    finally:
        engine.dispose()
