from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from pydantic import SecretStr

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing import providers, quota_commerce
from sketch2life.infrastructure.persistence.billing_models import BillingInvoiceModel, BillingPaymentEventModel


def test_momo_checkout_passes_a_fifteen_minute_expiry_to_provider(monkeypatch):
    settings = SimpleNamespace(
        env="test",
        momo_payment_configured=True,
        momo_access_key=SecretStr("test-access"),
        momo_secret_key=SecretStr("test-secret"),
        momo_partner_code="TESTPARTNER",
        momo_endpoint="https://test-payment.momo.vn/v2/gateway/api/create",
        momo_return_url="http://localhost:5173/school/billing",
        momo_ipn_url="https://hooks.example.test/api/payment-callbacks/v1/momo/ipn",
        billing_provider_timeout_seconds=3,
    )
    captured = {}

    def fake_post(_url, payload, _timeout):
        captured.update(payload)
        return {
            "partnerCode": payload["partnerCode"],
            "orderId": payload["orderId"],
            "requestId": payload["requestId"],
            "amount": payload["amount"],
            "resultCode": 0,
            "payUrl": "https://test-payment.momo.vn/checkout/test-order",
        }

    monkeypatch.setattr(providers, "_post_json", fake_post)
    started = datetime.now(UTC)
    result = providers.create_momo_checkout(
        settings,
        invoice_id="invoice-test",
        amount_vnd=100_000,
        order_ref="S2L-test-order",
        request_id="request-test",
    )

    assert captured["orderExpireTime"] == 15
    assert "invoice=invoice-test" in captured["redirectUrl"]
    assert captured["signature"] == providers._momo_request_signature(
        captured, "test-access", "test-secret"
    )
    assert result["expires_at"] >= started.replace(microsecond=0)


def test_momo_query_accepts_final_expired_order_without_amount_or_transaction_id(monkeypatch):
    settings = SimpleNamespace(
        momo_payment_configured=True,
        momo_access_key=SecretStr("test-access"),
        momo_secret_key=SecretStr("test-secret"),
        momo_partner_code="TESTPARTNER",
        momo_endpoint="https://test-payment.momo.vn/v2/gateway/api/create",
        billing_provider_timeout_seconds=30,
    )

    def fake_post(_url, payload, timeout):
        assert timeout >= 30
        return {
            "partnerCode": payload["partnerCode"],
            "orderId": payload["orderId"],
            "requestId": payload["requestId"],
            "resultCode": 1005,
        }

    monkeypatch.setattr(providers, "_post_json", fake_post)
    result = providers.query_momo_transaction(
        settings, order_ref="S2L-expired-order", amount_vnd=10_000
    )

    assert result["state"] == "FAILED"
    assert result["result_code"] == 1005
    assert result["amount_vnd"] == 10_000
    assert result["transaction_ref"] is None


def test_momo_query_does_not_accept_expiry_for_a_different_order(monkeypatch):
    settings = SimpleNamespace(
        momo_payment_configured=True,
        momo_access_key=SecretStr("test-access"),
        momo_secret_key=SecretStr("test-secret"),
        momo_partner_code="TESTPARTNER",
        momo_endpoint="https://test-payment.momo.vn/v2/gateway/api/create",
        billing_provider_timeout_seconds=30,
    )

    def fake_post(_url, payload, _timeout):
        return {
            "partnerCode": payload["partnerCode"],
            "orderId": "S2L-some-other-order",
            "requestId": payload["requestId"],
            "resultCode": 1005,
        }

    monkeypatch.setattr(providers, "_post_json", fake_post)

    try:
        providers.query_momo_transaction(
            settings, order_ref="S2L-expired-order", amount_vnd=10_000
        )
    except providers.ProviderError as exc:
        assert exc.code == "MOMO_QUERY_RESPONSE_MISMATCH"
    else:
        raise AssertionError("a final failure for a different order must be rejected")


def test_reconcile_final_momo_expiry_without_transaction_id_closes_invoice(monkeypatch):
    invoice = SimpleNamespace(
        invoice_id="invoice-expired",
        state="PENDING",
        provider="MOMO",
        amount_vnd=10_000,
    )
    attempt = SimpleNamespace(state="UNKNOWN", provider_order_ref="S2L-expired-order")

    class FakeSession:
        def get(self, model, _key):
            return invoice if model is BillingInvoiceModel else None

        def scalar(self, _statement):
            return attempt if _statement is not None else None

    service = quota_commerce.QuotaCommerceService(
        FakeSession(), "school-admin", SimpleNamespace()
    )
    monkeypatch.setattr(
        quota_commerce,
        "query_momo_transaction",
        lambda *_args, **_kwargs: {
            "state": "FAILED",
            "provider": "MOMO",
            "transaction_ref": None,
            "amount_vnd": 10_000,
            "result_code": 1005,
            "request_id": "request-expiry",
        },
    )
    settled = {}

    def fake_settle(**kwargs):
        settled.update(kwargs)
        return {"state": "FAILED", "duplicate": False}

    monkeypatch.setattr(service, "settle_verified", fake_settle)

    result = service.reconcile_invoice("invoice-expired")

    assert result["state"] == "FAILED"
    assert result["reconciled"] is True
    assert settled["transaction_ref"] is None
    assert settled["amount_vnd"] == 10_000
    assert settled["paid"] is False


def test_expired_vnpay_invoice_is_canceled_only_after_signed_query_reports_no_transaction(monkeypatch):
    now = datetime(2026, 11, 23, 12, tzinfo=UTC)
    invoice = SimpleNamespace(
        invoice_id="invoice-expired-vnpay",
        state="PENDING",
        provider="VNPAY",
        amount_vnd=10_000,
        revision=1,
    )
    attempt = SimpleNamespace(
        state="OPEN",
        provider_order_ref="S2L-expired-order",
        provider_transaction_date="20261123190000",
        provider_order_info="Quota video S2Lexpiredorder",
        expires_at=now - timedelta(seconds=1),
        updated_at=None,
        revision=1,
    )

    class FakeSession:
        def __init__(self):
            self.rows = [invoice, attempt]
            self.added = []
            self.committed = False

        def execute(self, *_args, **_kwargs):
            return None

        def scalar(self, _statement):
            return self.rows.pop(0)

        def add(self, row):
            self.added.append(row)

        def commit(self):
            self.committed = True

    db = FakeSession()
    monkeypatch.setattr(
        quota_commerce,
        "query_vnpay_transaction",
        lambda *_args, **_kwargs: {"state": "PENDING", "provider": "VNPAY", "no_transaction": True},
    )
    service = quota_commerce.QuotaCommerceService(db, "school-admin", SimpleNamespace(), clock=lambda: now)

    result = service.cancel_expired_vnpay_invoice(invoice.invoice_id)

    assert result["state"] == "CANCELED"
    assert result["canceled"] is True
    assert invoice.state == "CANCELED"
    assert attempt.state == "CANCELED"
    assert db.committed is True
    assert len(db.added) == 1
    assert isinstance(db.added[0], BillingPaymentEventModel)
    assert db.added[0].outcome == "CANCELED"


def test_vnpay_invoice_cannot_be_canceled_while_checkout_link_is_active(monkeypatch):
    now = datetime(2026, 11, 23, 12, tzinfo=UTC)
    invoice = SimpleNamespace(invoice_id="invoice-active", state="PENDING", provider="VNPAY")
    attempt = SimpleNamespace(
        state="OPEN",
        expires_at=now + timedelta(minutes=1),
    )

    class FakeSession:
        def __init__(self):
            self.rows = [invoice, attempt]

        def execute(self, *_args, **_kwargs):
            return None

        def scalar(self, _statement):
            return self.rows.pop(0)

    service = quota_commerce.QuotaCommerceService(FakeSession(), "school-admin", SimpleNamespace(), clock=lambda: now)
    monkeypatch.setattr(
        quota_commerce,
        "query_vnpay_transaction",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("active checkout must not be queried for cancellation")),
    )

    try:
        service.cancel_expired_vnpay_invoice(invoice.invoice_id)
    except AdminError as exc:
        assert exc.code == "PAYMENT_CHECKOUT_STILL_ACTIVE"
    else:
        raise AssertionError("an active VNPay checkout must not be canceled")
