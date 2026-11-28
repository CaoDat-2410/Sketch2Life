"""Offline capacity purchase regressions; provider calls are replaced by fakes."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing import capacity_commerce
from sketch2life.infrastructure.billing.capacity_commerce import CapacityCommerceService
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingPaymentAttemptModel,
    BillingPaymentEventModel,
    BillingReceiptModel,
    CapacityPriceModel,
    SubscriptionEventModel,
    SubscriptionModel,
    VideoQuotaGrantModel,
)

NOW = datetime(2026, 1, 16, tzinfo=UTC)
SETTINGS = SimpleNamespace(
    billing_real_payments_enabled=True, momo_payment_configured=True, vnpay_payment_configured=True
)


class MemoryDB:
    def __init__(self):
        self.rows = []
        self.subscription = SubscriptionModel(
            subscription_id="sub",
            organization_ref="org",
            price_id="price",
            addon_slots=2,
            state="ACTIVE",
            period_start=NOW - timedelta(days=15),
            period_end=NOW + timedelta(days=15),
            revision=1,
        )
        self.price = CapacityPriceModel(
            price_id="price",
            cycle_months=1,
            base_amount_vnd=10000,
            slot_amount_vnd=10000,
            created_by="admin",
        )
        self.rows.extend([self.subscription, self.price])

    def execute(self, *args, **kwargs):
        pass

    def get(self, model, key):
        if model is BillingReceiptModel:
            return next(
                (
                    r
                    for r in self.rows
                    if isinstance(r, model) and (r.actor_ref, r.operation, r.key) == key
                ),
                None,
            )
        attr = {
            CapacityPriceModel: "price_id",
            BillingPaymentEventModel: "event_id",
            BillingInvoiceModel: "invoice_id",
        }.get(model)
        return (
            next((r for r in self.rows if isinstance(r, model) and getattr(r, attr) == key), None)
            if attr
            else None
        )

    def scalar(self, statement):
        sql = str(statement)
        if "FROM billing.organization_subscriptions" in sql:
            return self.subscription
        if "FROM billing.subscription_events" in sql:
            if "CAPACITY_DOWNGRADE" in str(
                statement.compile(compile_kwargs={"literal_binds": True})
            ):
                return None
            return next(
                (
                    r
                    for r in self.rows
                    if isinstance(r, SubscriptionEventModel) and r.kind == "CAPACITY_QUOTED"
                ),
                None,
            )
        if "FROM billing.payment_attempts JOIN" in sql:
            return next(
                (
                    r
                    for r in self.rows
                    if isinstance(r, BillingPaymentAttemptModel)
                    and r.state in {"OPEN", "UNKNOWN", "REQUESTING"}
                ),
                None,
            )
        if "FROM billing.payment_attempts" in sql:
            return next((r for r in self.rows if isinstance(r, BillingPaymentAttemptModel)), None)
        if "FROM billing.invoices" in sql:
            return next((r for r in self.rows if isinstance(r, BillingInvoiceModel)), None)
        return None

    def add(self, row):
        self.rows.append(row)

    def add_all(self, rows):
        self.rows.extend(rows)

    def flush(self):
        pass

    def commit(self):
        pass


def service(db, now=NOW):
    return CapacityCommerceService(db, "manager", SETTINGS, clock=lambda: now)


def quote_fields(db, quantity=2, at=NOW):
    quote = capacity_commerce.capacity_quote(db, "org", quantity, at, SETTINGS)
    return dict(
        expected_amount_vnd=quote["amount_vnd"],
        price_id=quote["price_id"],
        period_end=datetime.fromisoformat(quote["period_end"]),
        quoted_at=datetime.fromisoformat(quote["quoted_at"]),
    )


def checkout(db, monkeypatch, key="key"):
    monkeypatch.setattr(
        capacity_commerce,
        "create_momo_checkout",
        lambda *args, **kw: {
            "checkout_url": "https://example.test/pay",
            "expires_at": NOW + timedelta(minutes=15),
        },
    )
    return service(db).checkout_slots("org", 2, "MOMO", key, **quote_fields(db))


def settle(db, *, paid=True, now=NOW):
    attempt = next(r for r in db.rows if isinstance(r, BillingPaymentAttemptModel))
    return service(db, now).settle_verified(
        provider="MOMO",
        order_ref=attempt.provider_order_ref,
        transaction_ref="tx" if paid else None,
        amount_vnd=10000,
        paid=paid,
        payload_digest="digest",
    )


def test_checkout_receipt_replays_and_rejects_different_payload(monkeypatch):
    db = MemoryDB()
    first = checkout(db, monkeypatch)
    assert checkout(db, monkeypatch) == first
    assert sum(isinstance(r, BillingInvoiceModel) for r in db.rows) == 1
    with pytest.raises(AdminError, match="IDEMPOTENCY_CONFLICT"):
        service(db).checkout_slots("org", 3, "MOMO", "key", **quote_fields(db, 3))
    with pytest.raises(AdminError, match="PAYMENT_ATTEMPT_ALREADY_OPEN"):
        checkout(db, monkeypatch, "other")


def test_verified_payment_activates_once_and_never_grants_video(monkeypatch):
    db = MemoryDB()
    checkout(db, monkeypatch)
    db.subscription.revision += 1  # An unrelated revision does not invalidate a paid purchase.
    assert settle(db)["state"] == "PAID"
    assert settle(db)["duplicate"] is True
    assert db.subscription.addon_slots == 4
    assert (
        sum(
            isinstance(r, SubscriptionEventModel) and r.kind == "CAPACITY_PAYMENT_CONFIRMED"
            for r in db.rows
        )
        == 1
    )
    assert not any(isinstance(r, VideoQuotaGrantModel) for r in db.rows)


def test_failed_and_late_payments_do_not_change_capacity(monkeypatch):
    failed = MemoryDB()
    checkout(failed, monkeypatch)
    settle(failed, paid=False)
    assert failed.subscription.addon_slots == 2
    late = MemoryDB()
    checkout(late, monkeypatch)
    settle(late, now=NOW + timedelta(days=15))
    assert late.subscription.addon_slots == 2
    assert any(
        isinstance(r, SubscriptionEventModel) and r.kind == "CAPACITY_PAYMENT_UNAPPLIED"
        for r in late.rows
    )
    assert next(r for r in late.rows if isinstance(r, BillingInvoiceModel)).state == "PAID"


def test_provider_unavailable_fails_before_writes():
    db = MemoryDB()
    svc = CapacityCommerceService(
        db, "manager", SimpleNamespace(billing_real_payments_enabled=False), clock=lambda: NOW
    )
    with pytest.raises(AdminError, match="PAYMENT_PROVIDER_NOT_AVAILABLE"):
        svc.checkout_slots("org", 1, "MOMO", "key", **quote_fields(db, 1))
    assert len(db.rows) == 2


def test_video_quota_queries_exclude_capacity():
    from sketch2life.infrastructure.billing.quota_commerce import capacity_invoice_filter

    sql = str(
        select(BillingInvoiceModel)
        .where(~capacity_invoice_filter())
        .compile(compile_kwargs={"literal_binds": True})
    )
    assert "NOT (EXISTS" in sql and "CAPACITY_QUOTED" in sql


def test_purchase_queries_include_all_capacity_providers_and_classify_kind():
    class QueryDB:
        def __init__(self):
            self.statements = []
            self.invoices = [
                BillingInvoiceModel(
                    invoice_id=invoice_id,
                    product_id=None,
                    offer_id="capacity-price",
                    owner_kind="ORGANIZATION",
                    owner_ref="org",
                    units=12,
                    amount_vnd=100_000,
                    state="PENDING",
                    provider="SANDBOX" if invoice_id.startswith("admin-") else "MOMO",
                    payment_mode="MANUAL",
                    revision=1,
                )
                for invoice_id in ("admin-start", "admin-renew", "admin-addon", "momo-addon")
            ]
            self.quoted_events = {
                "admin-start": SimpleNamespace(payload={"mode": "START"}),
                "admin-renew": SimpleNamespace(payload={"mode": "RENEW"}),
                "admin-addon": SimpleNamespace(payload={"mode": "ADDON"}),
                "momo-addon": SimpleNamespace(payload={}),
            }

        def scalars(self, statement):
            self.statements.append(statement)
            return self.invoices if "FROM billing.invoices" in str(statement) else []

        def scalar(self, statement):
            self.statements.append(statement)
            sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
            if "CAPACITY_PAYMENT_CONFIRMED" in sql or sql.lstrip().startswith(
                "SELECT billing.invoices."
            ):
                return None
            if "CAPACITY_QUOTED" in sql:
                return next(
                    (
                        event
                        for invoice_id, event in self.quoted_events.items()
                        if f"'{invoice_id}'" in sql
                    ),
                    None,
                )
            return None

    db = QueryDB()
    svc = service(db)
    items = svc.purchases("org")["items"]
    assert {item["invoice_id"] for item in items} == {
        "admin-start",
        "admin-renew",
        "admin-addon",
        "momo-addon",
    }
    assert {item["invoice_id"]: item["kind"] for item in items} == {
        "admin-start": "START",
        "admin-renew": "RENEW",
        "admin-addon": "ADDON",
        "momo-addon": "ADDON",
    }
    purchase_query = str(db.statements[0].compile(compile_kwargs={"literal_binds": True}))
    assert "provider IN ('MOMO', 'VNPAY')" not in purchase_query
    assert "owner_ref = 'org'" in purchase_query and "CAPACITY_QUOTED" in purchase_query

    with pytest.raises(AdminError, match="INVOICE_NOT_FOUND"):
        svc.scoped_purchase("org", "admin-start")
    scoped_query = str(db.statements[-1].compile(compile_kwargs={"literal_binds": True}))
    assert "provider IN ('MOMO', 'VNPAY')" in scoped_query
    assert "CAPACITY_QUOTED" in scoped_query


def test_checkout_locks_and_refreshes_subscription_before_quote(monkeypatch):
    db = MemoryDB()
    fields = quote_fields(db)
    original_scalar = db.scalar
    calls = []

    def scalar(statement):
        if "FROM billing.organization_subscriptions" in str(statement):
            calls.append(statement)
        return original_scalar(statement)

    db.scalar = scalar
    monkeypatch.setattr(
        capacity_commerce,
        "create_momo_checkout",
        lambda *a, **kw: {"checkout_url": "https://example.test/pay", "expires_at": NOW},
    )
    service(db).checkout_slots("org", 2, "MOMO", "key", **fields)
    assert len(calls) == 3
    assert calls[0]._for_update_arg is not None
    assert calls[0].get_execution_options().get("populate_existing") is True
    assert calls[1]._for_update_arg is None


def test_capacity_routes_check_assignment_before_access(monkeypatch):
    from fastapi import HTTPException

    from sketch2life.interfaces.http.routers import be1_billing

    calls = []

    def deny(db, principal, organization_id, roles):
        calls.append((organization_id, roles))
        raise AdminError("FORBIDDEN", 403)

    monkeypatch.setattr(be1_billing, "require_assignment", deny)
    with pytest.raises(HTTPException) as error:
        be1_billing.capacity_purchase_quote("other-org", 1, object(), object())
    assert error.value.status_code == 403
    assert calls == [("other-org", {"school_admin"})]


def test_price_and_actor_are_recorded_on_quote_event(monkeypatch):
    db = MemoryDB()
    result = checkout(db, monkeypatch)
    quote = next(r for r in db.rows if isinstance(r, SubscriptionEventModel))
    assert quote.invoice_id == result["invoice_id"] and quote.actor_ref == "manager"
    assert quote.payload["price_id"] == "price"
    assert quote.payload["base_amount_vnd"] == 10000
    assert quote.payload["slot_amount_vnd"] == 10000
    assert quote.payload["quantity"] == 2 and quote.payload["amount_vnd"] == 10000


def test_late_provider_error_does_not_undo_early_callback(monkeypatch):
    from sketch2life.infrastructure.billing.providers import ProviderError

    db = MemoryDB()

    def early_callback(*args, **kwargs):
        settle(db)
        raise ProviderError("PAYMENT_PROVIDER_UNAVAILABLE", 503)

    monkeypatch.setattr(capacity_commerce, "create_momo_checkout", early_callback)
    result = service(db).checkout_slots("org", 2, "MOMO", "key", **quote_fields(db))
    assert result["state"] == "PAID" and db.subscription.addon_slots == 4


@pytest.mark.parametrize("change", ["period", "limit"])
def test_paid_purchase_that_can_no_longer_apply_is_recorded(monkeypatch, change):
    db = MemoryDB()
    checkout(db, monkeypatch)
    if change == "period":
        db.subscription.period_end += timedelta(days=30)
    else:
        db.subscription.addon_slots = 999
    before = db.subscription.addon_slots
    settle(db)
    assert db.subscription.addon_slots == before
    assert any(
        isinstance(r, SubscriptionEventModel) and r.kind == "CAPACITY_PAYMENT_UNAPPLIED"
        for r in db.rows
    )


def test_zero_prorated_amount_rejected_before_creating_invoice(monkeypatch):
    db = MemoryDB()
    db.price.slot_amount_vnd = 1
    monkeypatch.setattr(
        capacity_commerce,
        "create_vnpay_checkout",
        lambda *args, **kwargs: pytest.fail("provider called"),
    )
    with pytest.raises(AdminError, match="VNPAY_AMOUNT_OUT_OF_RANGE"):
        service(db, NOW + timedelta(days=14, hours=23)).checkout_slots(
            "org", 1, "VNPAY", "key", **quote_fields(db, 1, NOW + timedelta(days=14, hours=23))
        )
    assert not any(isinstance(r, BillingInvoiceModel) for r in db.rows)


def test_paid_callback_after_canceled_invoice_applies_once(monkeypatch):
    db = MemoryDB()
    checkout(db, monkeypatch)
    next(r for r in db.rows if isinstance(r, BillingInvoiceModel)).state = "CANCELED"
    next(r for r in db.rows if isinstance(r, BillingPaymentAttemptModel)).state = "CANCELED"
    assert settle(db)["state"] == "PAID"
    assert settle(db)["duplicate"] is True
    assert db.subscription.addon_slots == 4
    confirmed = next(
        r
        for r in db.rows
        if isinstance(r, SubscriptionEventModel) and r.kind == "CAPACITY_PAYMENT_CONFIRMED"
    )
    assert confirmed.actor_ref == "provider:momo"


def test_confirmed_quote_is_charged_and_replayed_after_expiry(monkeypatch):
    db = MemoryDB()
    fields = quote_fields(db)
    calls = []
    monkeypatch.setattr(
        capacity_commerce,
        "create_momo_checkout",
        lambda *a, **kw: (
            calls.append(kw) or {"checkout_url": "https://example.test/pay", "expires_at": NOW}
        ),
    )
    result = service(db, NOW + timedelta(minutes=4)).checkout_slots(
        "org", 2, "MOMO", "key", **fields
    )
    assert result["amount_vnd"] == fields["expected_amount_vnd"] == calls[0]["amount_vnd"]
    event = next(r for r in db.rows if isinstance(r, SubscriptionEventModel))
    assert event.payload["quoted_at"] == NOW.isoformat()
    assert event.payload["confirmed_at"] == (NOW + timedelta(minutes=4)).isoformat()
    assert (
        service(db, NOW + timedelta(minutes=10)).checkout_slots("org", 2, "MOMO", "key", **fields)
        == result
    )
    assert len(calls) == 1


@pytest.mark.parametrize("change", ["amount", "period", "expired", "future", "price"])
def test_changed_quote_refused_without_side_effects(monkeypatch, change):
    db = MemoryDB()
    fields = quote_fields(db)
    now = NOW
    if change == "amount":
        fields["expected_amount_vnd"] += 1
    elif change == "period":
        db.subscription.period_start = NOW + timedelta(seconds=1)
        db.subscription.period_end += timedelta(days=30)
        now += timedelta(minutes=1)
    elif change == "expired":
        now += timedelta(minutes=5, microseconds=1)
    elif change == "future":
        now -= timedelta(microseconds=1)
    else:
        fields["price_id"] = "other"
    monkeypatch.setattr(
        capacity_commerce, "create_momo_checkout", lambda *a, **kw: pytest.fail("provider called")
    )
    with pytest.raises(AdminError, match="CAPACITY_QUOTE_CHANGED"):
        service(db, now).checkout_slots("org", 2, "MOMO", "key", **fields)
    assert not any(
        isinstance(
            r,
            (
                BillingInvoiceModel,
                BillingPaymentAttemptModel,
                SubscriptionEventModel,
                BillingReceiptModel,
            ),
        )
        for r in db.rows
    )


def test_checkout_schema_requires_aware_quote_and_rejects_extra_fields():
    from pydantic import ValidationError

    from sketch2life.contracts.schemas.be1_capacity import Be1CapacityCheckoutRequest

    valid = dict(
        addon_slots=1,
        provider="MOMO",
        expected_amount_vnd=1000,
        price_id="price",
        period_end=NOW,
        quoted_at=NOW,
    )
    Be1CapacityCheckoutRequest(**valid)
    for invalid in (
        {**valid, "client_ip": "127.0.0.1"},
        {**valid, "quoted_at": NOW.replace(tzinfo=None)},
        {**valid, "period_end": NOW.replace(tzinfo=None)},
        {**valid, "expected_amount_vnd": 0},
        {key: value for key, value in valid.items() if key != "quoted_at"},
    ):
        with pytest.raises(ValidationError):
            Be1CapacityCheckoutRequest(**invalid)
