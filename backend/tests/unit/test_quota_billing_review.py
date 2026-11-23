"""Local-only regression coverage for quota settlement and payment callbacks."""
import base64
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing import providers
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.persistence.billing_models import (
    BillingOfferModel, BillingPaymentEventModel, VideoQuotaGrantModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db
from sketch2life.interfaces.http.routers import payment_callbacks


class SettlementDB:
    def __init__(self, state="PENDING", prior=None):
        self.invoice = SimpleNamespace(invoice_id="invoice", state=state, provider="VNPAY",
            amount_vnd=100, revision=1, offer_id="offer", owner_kind="PARENT_ACCOUNT",
            owner_ref="parent", units=3)
        self.attempt = SimpleNamespace(invoice_id="invoice", state=state, revision=1)
        self.prior = prior
        self.added = []
        self.calls = 0

    def execute(self, *args, **kwargs):
        pass

    def scalar(self, statement):
        self.calls += 1
        return self.attempt if self.calls % 2 else self.invoice

    def get(self, model, key):
        if model is BillingPaymentEventModel:
            return self.prior
        if model is BillingOfferModel:
            return SimpleNamespace(offer_kind="TOP_UP")

    def add(self, row):
        self.added.append(row)
        if isinstance(row, BillingPaymentEventModel):
            self.prior = row

    def commit(self):
        pass


def settle(db, amount=100):
    return QuotaCommerceService(db, "test", SimpleNamespace()).settle_verified(
        provider="VNPAY", order_ref="order", transaction_ref="transaction",
        amount_vnd=amount, paid=True, payload_digest="digest")


def test_settlement_rejects_amount_mismatch():
    db = SettlementDB()
    with pytest.raises(AdminError) as error:
        settle(db, 101)
    assert error.value.code == "PAYMENT_AMOUNT_MISMATCH"
    assert db.added == []


def test_settlement_duplicate_does_not_issue_another_grant():
    db = SettlementDB()
    assert settle(db) == {"state": "PAID", "duplicate": False}
    assert settle(db) == {"state": "PAID", "duplicate": True}
    assert sum(isinstance(row, VideoQuotaGrantModel) for row in db.added) == 1


def test_paid_after_cancel_issues_grant():
    db = SettlementDB(state="CANCELED")
    assert settle(db) == {"state": "PAID", "duplicate": False}
    assert db.attempt.state == "PAID"
    assert sum(isinstance(row, VideoQuotaGrantModel) for row in db.added) == 1


@pytest.fixture
def callbacks(monkeypatch):
    settings = SimpleNamespace(momo_payment_configured=True, momo_access_key=SecretStr("access"),
        momo_secret_key=SecretStr("secret"), momo_partner_code="partner",
        vnpay_payment_configured=True, vnpay_hash_secret=SecretStr("secret"),
        vnpay_tmn_code="merchant")
    monkeypatch.setattr(payment_callbacks, "get_settings", lambda: settings)
    attempt = SimpleNamespace(provider_request_ref="request")
    invoice = SimpleNamespace(invoice_id="invoice")
    monkeypatch.setattr(payment_callbacks, "_invoice_for_attempt", lambda *args: (attempt, invoice))
    calls = []
    monkeypatch.setattr(payment_callbacks.QuotaCommerceService, "settle_verified",
                        lambda self, **kwargs: calls.append(kwargs))
    app = FastAPI()
    app.include_router(payment_callbacks.router)
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as client:
        yield client, settings, calls


def test_momo_ipn_valid_and_invalid_signature(callbacks):
    client, settings, calls = callbacks
    payload = {"partnerCode": "partner", "orderId": "order", "requestId": "request",
        "amount": 100, "resultCode": 0, "transId": "transaction",
        "extraData": base64.b64encode(json.dumps({"invoice_id": "invoice"}).encode()).decode()}
    payload["signature"] = providers._momo_ipn_signature(payload, "access", "secret")
    assert client.post("/api/payment-callbacks/v1/momo/ipn", json=payload).status_code == 204
    assert len(calls) == 1 and calls[0]["paid"] is True
    payload["signature"] = "bad"
    assert client.post("/api/payment-callbacks/v1/momo/ipn", json=payload).status_code == 401
    assert len(calls) == 1
    payload["signature"] = "\u00e9"
    assert client.post("/api/payment-callbacks/v1/momo/ipn", json=payload).status_code == 401
    assert len(calls) == 1
    payload["signature"] = "bad"
    payload["orderId"] = "\ud800"
    assert client.post(
        "/api/payment-callbacks/v1/momo/ipn",
        content=json.dumps(payload),
        headers={"content-type": "application/json"},
    ).status_code == 401
    assert len(calls) == 1


def test_vnpay_ipn_valid_and_invalid_signature(callbacks):
    client, settings, calls = callbacks
    params = {"vnp_TmnCode": "merchant", "vnp_TxnRef": "order",
        "vnp_TransactionNo": "transaction", "vnp_Amount": "10000",
        "vnp_ResponseCode": "00", "vnp_TransactionStatus": "00"}
    params["vnp_SecureHash"] = providers._vnpay_digest(params, "secret")
    assert client.get("/api/payment-callbacks/v1/vnpay/ipn", params=params).json()["RspCode"] == "00"
    assert len(calls) == 1 and calls[0]["amount_vnd"] == 100
    params["vnp_SecureHash"] = "bad"
    assert client.get("/api/payment-callbacks/v1/vnpay/ipn", params=params).json()["RspCode"] == "97"
    assert len(calls) == 1


@pytest.mark.parametrize("filename", [
    "20261122_quota_commerce.py", "20261123_vnpay_order_info.py", "20261123_vnpay_cancel.py",
])
def test_quota_migrations_explicitly_reject_downgrade(filename):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location("quota_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(RuntimeError):
        module.downgrade()
