from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from pydantic import SecretStr

from sketch2life.infrastructure.billing import providers, quota_commerce
from sketch2life.infrastructure.persistence.billing_models import BillingInvoiceModel


def _settings():
    return SimpleNamespace(
        env="test",
        vnpay_payment_configured=True,
        vnpay_tmn_code="TEST0001",
        vnpay_hash_secret=SecretStr("test-vnpay-secret"),
        vnpay_payment_url="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        vnpay_query_url="https://sandbox.vnpayment.vn/merchant_webapi/api/transaction",
        vnpay_server_ip="8.8.8.8",
        vnpay_return_url="http://localhost:5173/school/billing",
        billing_provider_timeout_seconds=35,
    )


def test_vnpay_pay_210_uses_documented_fields_and_signed_plain_order_info():
    settings = _settings()
    order_ref = "S2L0123456789abcdef0123456789abcdef"
    order_info = providers.vnpay_order_info(order_ref)

    result = providers.create_vnpay_checkout(
        settings,
        invoice_id="67c21e78-34ae-46e6-a371-62421f05d950",
        amount_vnd=10_000,
        order_ref=order_ref,
        order_info=order_info,
        client_ip="127.0.0.1",
        transaction_date="20261123103000",
    )

    query = parse_qs(urlsplit(result["checkout_url"]).query)
    assert set(query) == {
        "vnp_Version",
        "vnp_Command",
        "vnp_TmnCode",
        "vnp_Amount",
        "vnp_CurrCode",
        "vnp_TxnRef",
        "vnp_OrderInfo",
        "vnp_OrderType",
        "vnp_Locale",
        "vnp_ReturnUrl",
        "vnp_IpAddr",
        "vnp_CreateDate",
        "vnp_ExpireDate",
        "vnp_SecureHash",
    }
    assert "vnp_SecureHashType" not in query
    assert query["vnp_Version"] == ["2.1.0"]
    assert query["vnp_Amount"] == ["1000000"]
    assert query["vnp_TxnRef"] == [order_ref]
    assert query["vnp_OrderInfo"] == [order_info]
    assert "-" not in query["vnp_OrderInfo"][0]

    signed_params = {key: values[0] for key, values in query.items() if key != "vnp_SecureHash"}
    assert query["vnp_SecureHash"] == [
        providers._vnpay_digest(signed_params, "test-vnpay-secret")
    ]


def test_vnpay_order_info_strips_non_alphanumeric_reference_characters():
    assert providers.vnpay_order_info("S2L-ab!12") == "Quota video S2Lab12"

    try:
        providers.vnpay_order_info("---")
    except providers.ProviderError as exc:
        assert exc.code == "VNPAY_ORDER_REFERENCE_INVALID"
    else:
        raise AssertionError("an empty sanitized order reference must be rejected")


def test_vnpay_querydr_sends_the_documented_signed_request_fields(monkeypatch):
    settings = _settings()
    captured = {}

    def fake_post(url, payload, timeout):
        captured.update({"url": url, "payload": payload, "timeout": timeout})
        response = {
            "vnp_ResponseId": "response-1",
            "vnp_Command": "querydr",
            "vnp_ResponseCode": "91",
            "vnp_Message": "Transaction not found",
            "vnp_TmnCode": settings.vnpay_tmn_code,
            "vnp_TxnRef": "S2L0123456789abcdef0123456789abcdef",
            "vnp_Amount": "1000000",
            "vnp_BankCode": "",
            "vnp_PayDate": "",
            "vnp_TransactionNo": "",
            "vnp_TransactionType": "",
            "vnp_TransactionStatus": "",
            "vnp_OrderInfo": "Quota video S2L0123456789abcdef0123456789abcdef",
            "vnp_PromotionCode": "",
            "vnp_PromotionAmount": "",
        }
        response["vnp_SecureHash"] = providers._vnpay_query_digest(
            [str(response.get(name, "")) for name in providers._VNPAY_QUERY_RESPONSE_FIELDS],
            settings.vnpay_hash_secret.get_secret_value(),
        )
        return response

    monkeypatch.setattr(providers, "_post_json", fake_post)
    result = providers.query_vnpay_transaction(
        settings,
        order_ref="S2L0123456789abcdef0123456789abcdef",
        amount_vnd=10_000,
        transaction_date="20261123103000",
        order_info="Quota video S2L0123456789abcdef0123456789abcdef",
    )

    payload = captured["payload"]
    assert set(payload) == {
        "vnp_RequestId",
        "vnp_Version",
        "vnp_Command",
        "vnp_TmnCode",
        "vnp_TxnRef",
        "vnp_TransactionDate",
        "vnp_CreateDate",
        "vnp_IpAddr",
        "vnp_OrderInfo",
        "vnp_SecureHash",
    }
    signed_values = [
        payload["vnp_RequestId"],
        payload["vnp_Version"],
        payload["vnp_Command"],
        payload["vnp_TmnCode"],
        payload["vnp_TxnRef"],
        payload["vnp_TransactionDate"],
        payload["vnp_CreateDate"],
        payload["vnp_IpAddr"],
        payload["vnp_OrderInfo"],
    ]
    assert payload["vnp_SecureHash"] == providers._vnpay_query_digest(
        signed_values, settings.vnpay_hash_secret.get_secret_value()
    )
    assert captured["url"] == settings.vnpay_query_url
    assert result == {"state": "PENDING", "provider": "VNPAY", "no_transaction": True}


def test_vnpay_querydr_unsigned_gateway_error_is_not_reported_as_bad_signature(monkeypatch):
    settings = _settings()
    monkeypatch.setattr(
        providers, "_post_json", lambda *_: {"vnp_ResponseCode": "99", "vnp_Message": "Unexpected error"}
    )
    try:
        providers.query_vnpay_transaction(
            settings,
            order_ref="S2L0123456789abcdef0123456789abcdef",
            amount_vnd=10_000,
            transaction_date="20261123103000",
            order_info="Quota video S2L0123456789abcdef0123456789abcdef",
        )
    except providers.ProviderError as exc:
        assert exc.code == "VNPAY_QUERY_GATEWAY_ERROR"
    else:
        raise AssertionError("an unsigned gateway error must not be accepted")


def test_vnpay_reconcile_preserves_legacy_order_info_for_existing_attempts(monkeypatch):
    invoice = SimpleNamespace(
        invoice_id="67c21e78-34ae-46e6-a371-62421f05d950",
        state="PENDING",
        provider="VNPAY",
        amount_vnd=10_000,
    )
    attempt = SimpleNamespace(
        state="OPEN",
        provider_order_ref="S2L0123456789abcdef0123456789abcdef",
        provider_transaction_date="20261123103000",
        provider_order_info=None,
    )

    class FakeSession:
        def get(self, model, _key):
            return invoice if model is BillingInvoiceModel else None

        def scalar(self, _statement):
            return attempt

    captured = {}

    def fake_query(*_args, **kwargs):
        captured.update(kwargs)
        return {"state": "PENDING", "provider": "VNPAY"}

    monkeypatch.setattr(quota_commerce, "query_vnpay_transaction", fake_query)
    service = quota_commerce.QuotaCommerceService(
        FakeSession(), "school-admin", SimpleNamespace()
    )

    result = service.reconcile_invoice(invoice.invoice_id)

    assert result == {
        "invoice_id": invoice.invoice_id,
        "state": "PENDING",
        "reconciled": False,
    }
    assert captured["order_info"] == f"Quota video {invoice.invoice_id}"
