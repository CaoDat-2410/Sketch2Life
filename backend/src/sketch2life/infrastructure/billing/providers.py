"""Signed one-time checkout adapters for MoMo and VNPay."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import socket
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from urllib.error import URLError
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4
from zoneinfo import ZoneInfo


class ProviderError(Exception):
    def __init__(self, code: str, status: int = 503):
        super().__init__(code)
        self.code = code
        self.status = status


_MOMO_FINAL_FAILURE_CODES = frozenset(
    {1001, 1002, 1003, 1004, 1005, 1006, 1007, 1017, 1026, 4001, 4002, 4100}
)


def momo_payment_state(result_code: int) -> str:
    """Map only documented terminal MoMo payment results into ledger outcomes."""
    if result_code in {0, 9000}:
        # Checkout explicitly uses captureWallet with autoCapture=true.
        return "PAID"
    if result_code in _MOMO_FINAL_FAILURE_CODES:
        return "FAILED"
    return "PENDING"


def _is_https_or_local(url: str, env: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme == "https" and parsed.netloc:
        return True
    return env in {"local", "test"} and parsed.scheme == "http" and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def _require_callback_url(url: str, env: str) -> str:
    if not _is_https_or_local(url, env):
        raise ProviderError("PAYMENT_CALLBACK_URL_INVALID", 503)
    return url


def _append_invoice(url: str, invoice_id: str) -> str:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["invoice"] = invoice_id
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def _post_json(url: str, payload: dict, timeout: int) -> dict:
    request = Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        class RejectRedirects(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        with build_opener(RejectRedirects).open(request, timeout=timeout) as response:
            if not 200 <= response.status < 300:
                raise ProviderError("PAYMENT_PROVIDER_UNAVAILABLE", 503)
            result = json.loads(response.read(256_000).decode("utf-8"))
    except (URLError, TimeoutError, socket.timeout, OSError, ValueError):
        raise ProviderError("PAYMENT_PROVIDER_UNAVAILABLE", 503) from None
    if not isinstance(result, dict):
        raise ProviderError("PAYMENT_PROVIDER_INVALID_RESPONSE", 503)
    return result


def _momo_request_signature(payload: dict, access_key: str, secret_key: str) -> str:
    # MoMo v2 signs the documented checkout fields in this exact order.
    names = (
        "amount",
        "extraData",
        "ipnUrl",
        "orderId",
        "orderInfo",
        "partnerCode",
        "redirectUrl",
        "requestId",
        "requestType",
    )
    message = "accessKey=" + access_key + "&" + "&".join(
        f"{name}={payload.get(name, '')}" for name in names
    )
    return hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()


def _momo_ipn_signature(payload: dict, access_key: str, secret_key: str) -> str:
    names = (
        "amount",
        "extraData",
        "message",
        "orderId",
        "orderInfo",
        "orderType",
        "partnerCode",
        "payType",
        "requestId",
        "responseTime",
        "resultCode",
        "transId",
    )
    message = "accessKey=" + access_key + "&" + "&".join(
        f"{name}={payload.get(name, '')}" for name in names
    )
    return hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()


def _safe_momo_checkout_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "test-payment.momo.vn",
        "payment.momo.vn",
    }:
        raise ProviderError("PAYMENT_PROVIDER_INVALID_RESPONSE", 503)
    return url


def _safe_momo_endpoint(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "test-payment.momo.vn",
        "payment.momo.vn",
    } or parsed.path != "/v2/gateway/api/create":
        raise ProviderError("MOMO_ENDPOINT_INVALID", 503)
    return url


def _momo_create_response_valid(response: dict, payload: dict) -> bool:
    # MoMo's v2 /create response does not include a response signature. The
    # signed IPN/query payloads are verified separately; for this HTTPS response
    # bind the returned order to the exact request before accepting its pay URL.
    try:
        amount_matches = int(response.get("amount", -1)) == int(payload["amount"])
    except (TypeError, ValueError):
        return False
    return (
        response.get("orderId") == payload.get("orderId")
        and response.get("requestId") == payload.get("requestId")
        and amount_matches
        and response.get("partnerCode") == payload.get("partnerCode")
    )


def create_momo_checkout(
    settings, *, invoice_id: str, amount_vnd: int, order_ref: str, request_id: str
) -> dict:
    if not settings.momo_payment_configured:
        raise ProviderError("MOMO_NOT_CONFIGURED", 503)
    if not 1_000 <= amount_vnd <= 50_000_000:
        raise ProviderError("MOMO_AMOUNT_OUT_OF_RANGE", 422)
    access_key = settings.momo_access_key.get_secret_value()
    secret_key = settings.momo_secret_key.get_secret_value()
    payload = {
        "partnerCode": settings.momo_partner_code,
        "requestId": request_id,
        "amount": amount_vnd,
        "orderId": order_ref,
        "orderInfo": f"Quota video {invoice_id}",
        "redirectUrl": _append_invoice(
            _require_callback_url(settings.momo_return_url, settings.env), invoice_id
        ),
        "ipnUrl": _require_callback_url(settings.momo_ipn_url, settings.env),
        "requestType": "captureWallet",
        "autoCapture": True,
        "orderExpireTime": 15,
        "extraData": base64.b64encode(
            json.dumps({"invoice_id": invoice_id}, separators=(",", ":")).encode()
        ).decode(),
        "lang": "vi",
    }
    payload["signature"] = _momo_request_signature(payload, access_key, secret_key)
    response = _post_json(
        _safe_momo_endpoint(settings.momo_endpoint),
        payload,
        settings.billing_provider_timeout_seconds,
    )
    if not _momo_create_response_valid(response, payload):
        raise ProviderError("MOMO_RESPONSE_SIGNATURE_INVALID", 502)
    if response.get("resultCode") != 0 or not isinstance(response.get("payUrl"), str):
        raise ProviderError("MOMO_CHECKOUT_REJECTED", 502)
    return {
        "provider_order_ref": order_ref,
        "checkout_url": _safe_momo_checkout_url(response["payUrl"]),
        "expires_at": datetime.now(UTC) + timedelta(minutes=15),
        "request_id": payload["requestId"],
    }


def verify_momo_ipn(settings, payload: dict) -> bool:
    if not settings.momo_payment_configured:
        return False
    received = payload.get("signature")
    if not isinstance(received, str):
        return False
    expected = _momo_ipn_signature(
        payload,
        settings.momo_access_key.get_secret_value(),
        settings.momo_secret_key.get_secret_value(),
    )
    return hmac.compare_digest(received.lower(), expected.lower())


def _safe_momo_query_endpoint(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "test-payment.momo.vn",
        "payment.momo.vn",
    } or parsed.path != "/v2/gateway/api/create":
        raise ProviderError("MOMO_ENDPOINT_INVALID", 503)
    return urlunsplit((parsed.scheme, parsed.netloc, "/v2/gateway/api/query", "", ""))


def query_momo_transaction(settings, *, order_ref: str, amount_vnd: int) -> dict:
    """Read a MoMo order status; only a confirmed transaction is eligible to settle."""
    if not settings.momo_payment_configured:
        raise ProviderError("MOMO_NOT_CONFIGURED", 503)
    access_key = settings.momo_access_key.get_secret_value()
    secret_key = settings.momo_secret_key.get_secret_value()
    request_id = str(uuid4())
    payload = {
        "partnerCode": settings.momo_partner_code,
        "requestId": request_id,
        "orderId": order_ref,
        "lang": "vi",
    }
    signed = (
        f"accessKey={access_key}&orderId={order_ref}"
        f"&partnerCode={settings.momo_partner_code}&requestId={request_id}"
    )
    payload["signature"] = hmac.new(
        secret_key.encode(), signed.encode(), hashlib.sha256
    ).hexdigest()
    response = _post_json(
        _safe_momo_query_endpoint(settings.momo_endpoint),
        payload,
        max(30, settings.billing_provider_timeout_seconds),
    )
    try:
        raw_amount = response.get("amount")
        response_amount = int(raw_amount) if raw_amount is not None else None
        result_code = int(response.get("resultCode", -1))
        transaction_ref = str(response.get("transId", "")).strip()
    except (TypeError, ValueError):
        raise ProviderError("MOMO_QUERY_INVALID_RESPONSE", 502) from None
    if (
        response.get("partnerCode") != settings.momo_partner_code
        or response.get("orderId") != order_ref
        or (response.get("requestId") not in (None, request_id))
    ):
        raise ProviderError("MOMO_QUERY_RESPONSE_MISMATCH", 502)
    # MoMo's documented final QR-expired response (1005) may omit amount and
    # transId because no payment transaction was created. Bind that response
    # to this merchant/order/request above; for every other outcome, retain the
    # strict amount check before trusting a status.
    if response_amount is None:
        if result_code != 1005:
            raise ProviderError("MOMO_QUERY_RESPONSE_MISMATCH", 502)
    elif response_amount != amount_vnd:
        raise ProviderError("MOMO_QUERY_RESPONSE_MISMATCH", 502)
    state = momo_payment_state(result_code)
    if state == "FAILED" and result_code == 1005 and not transaction_ref:
        return {
            "state": "FAILED",
            "provider": "MOMO",
            "transaction_ref": None,
            "amount_vnd": amount_vnd,
            "result_code": result_code,
            "request_id": request_id,
        }
    if state == "PENDING" or not transaction_ref:
        return {"state": "PENDING", "provider": "MOMO"}
    return {
        "state": state,
        "provider": "MOMO",
        "transaction_ref": transaction_ref,
        "amount_vnd": response_amount,
        "result_code": result_code,
        "request_id": request_id,
    }


def _vnpay_signing_data(params: dict[str, str]) -> str:
    return urlencode(
        [(key, value) for key, value in sorted(params.items()) if value != ""],
        quote_via=quote_plus,
        safe="",
    )


def _vnpay_digest(params: dict[str, str], secret: str) -> str:
    return hmac.new(
        secret.encode(), _vnpay_signing_data(params).encode(), hashlib.sha512
    ).hexdigest()


def vnpay_order_info(order_ref: str) -> str:
    """Build the plain-text order description required by VNPAY PAY 2.1.0."""
    safe_ref = "".join(char for char in order_ref if char.isascii() and char.isalnum())
    if not safe_ref:
        raise ProviderError("VNPAY_ORDER_REFERENCE_INVALID", 422)
    return f"Quota video {safe_ref}"


def _vnpay_query_digest(values: list[str], secret: str) -> str:
    message = "|".join(values)
    return hmac.new(secret.encode(), message.encode(), hashlib.sha512).hexdigest()


def _vnpay_url(settings, params: dict[str, str]) -> str:
    base = settings.vnpay_payment_url
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.hostname not in {
        "sandbox.vnpayment.vn",
        "pay.vnpay.vn",
    }:
        raise ProviderError("VNPAY_ENDPOINT_INVALID", 503)
    # PAY API v2.1.0 explicitly omits vnp_SecureHashType; that field belongs
    # to the older 2.0.0/2.0.1 parameter set.
    signed = {**params}
    signed["vnp_SecureHash"] = _vnpay_digest(
        signed, settings.vnpay_hash_secret.get_secret_value()
    )
    return base + "?" + urlencode(sorted(signed.items()), quote_via=quote_plus, safe="")


def create_vnpay_checkout(
    settings,
    *,
    invoice_id: str,
    amount_vnd: int,
    order_ref: str,
    order_info: str,
    client_ip: str,
    transaction_date: str,
) -> dict:
    if not settings.vnpay_payment_configured:
        raise ProviderError("VNPAY_NOT_CONFIGURED", 503)
    try:
        normalized_ip = str(ip_address(client_ip))
    except ValueError:
        normalized_ip = "127.0.0.1"
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.vnpay_tmn_code,
        "vnp_Amount": str(amount_vnd * 100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_ref,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": _append_invoice(
            _require_callback_url(settings.vnpay_return_url, settings.env), invoice_id
        ),
        "vnp_IpAddr": normalized_ip,
        "vnp_CreateDate": transaction_date,
        "vnp_ExpireDate": (now + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S"),
    }
    return {
        "provider_order_ref": order_ref,
        "checkout_url": _vnpay_url(settings, params),
        "expires_at": now.astimezone(UTC) + timedelta(minutes=15),
        "transaction_date": transaction_date,
    }


def verify_vnpay_callback(settings, payload: dict[str, str]) -> bool:
    if not settings.vnpay_payment_configured:
        return False
    received = payload.get("vnp_SecureHash")
    if not received:
        return False
    signed = {
        key: value
        for key, value in payload.items()
        if key not in {"vnp_SecureHash", "vnp_SecureHashType"}
    }
    expected = _vnpay_digest(signed, settings.vnpay_hash_secret.get_secret_value())
    return hmac.compare_digest(received.lower(), expected.lower())


_VNPAY_QUERY_RESPONSE_FIELDS = (
    "vnp_ResponseId",
    "vnp_Command",
    "vnp_ResponseCode",
    "vnp_Message",
    "vnp_TmnCode",
    "vnp_TxnRef",
    "vnp_Amount",
    "vnp_BankCode",
    "vnp_PayDate",
    "vnp_TransactionNo",
    "vnp_TransactionType",
    "vnp_TransactionStatus",
    "vnp_OrderInfo",
    "vnp_PromotionCode",
    "vnp_PromotionAmount",
)


def _vnpay_query_response_valid(settings, response: dict) -> bool:
    received = response.get("vnp_SecureHash")
    if not isinstance(received, str) or not received:
        return False
    expected = _vnpay_query_digest(
        [str(response.get(name, "")) for name in _VNPAY_QUERY_RESPONSE_FIELDS],
        settings.vnpay_hash_secret.get_secret_value(),
    )
    return hmac.compare_digest(received.lower(), expected.lower())


def query_vnpay_transaction(
    settings,
    *,
    order_ref: str,
    amount_vnd: int,
    transaction_date: str,
    order_info: str,
) -> dict:
    """Use VNPAY QueryDR and verify its response checksum before applying status."""
    if not settings.vnpay_payment_configured:
        raise ProviderError("VNPAY_NOT_CONFIGURED", 503)
    endpoint = settings.vnpay_query_url
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or parsed.hostname not in {
        "sandbox.vnpayment.vn",
        "merchant.vnpay.vn",
    } or parsed.path != "/merchant_webapi/api/transaction":
        raise ProviderError("VNPAY_QUERY_ENDPOINT_INVALID", 503)
    try:
        server_ip = str(ip_address(settings.vnpay_server_ip))
    except ValueError:
        raise ProviderError("VNPAY_SERVER_IP_INVALID", 503) from None
    request_id = uuid4().hex
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y%m%d%H%M%S")
    values = [
        request_id,
        "2.1.0",
        "querydr",
        settings.vnpay_tmn_code,
        order_ref,
        transaction_date,
        now,
        server_ip,
        order_info,
    ]
    payload = {
        "vnp_RequestId": request_id,
        "vnp_Version": "2.1.0",
        "vnp_Command": "querydr",
        "vnp_TmnCode": settings.vnpay_tmn_code,
        "vnp_TxnRef": order_ref,
        "vnp_TransactionDate": transaction_date,
        "vnp_CreateDate": now,
        "vnp_IpAddr": server_ip,
        "vnp_OrderInfo": order_info,
        "vnp_SecureHash": _vnpay_query_digest(
            values, settings.vnpay_hash_secret.get_secret_value()
        ),
    }
    response = _post_json(endpoint, payload, settings.billing_provider_timeout_seconds)
    # The sandbox can return an unsigned {vnp_ResponseCode: "99",
    # vnp_Message: "Unexpected error"} instead of a QueryDR response.
    # Report the gateway failure accurately; never treat it as a signed result.
    if not response.get("vnp_SecureHash") and str(response.get("vnp_ResponseCode", "")) == "99":
        raise ProviderError("VNPAY_QUERY_GATEWAY_ERROR", 502)
    if not _vnpay_query_response_valid(settings, response):
        raise ProviderError("VNPAY_QUERY_RESPONSE_SIGNATURE_INVALID", 502)
    try:
        response_code = str(response.get("vnp_ResponseCode", ""))
        transaction_status = str(response.get("vnp_TransactionStatus", ""))
        transaction_ref = str(response.get("vnp_TransactionNo", ""))
    except (TypeError, ValueError):
        raise ProviderError("VNPAY_QUERY_INVALID_RESPONSE", 502) from None
    if response.get("vnp_TmnCode") != settings.vnpay_tmn_code or response.get("vnp_TxnRef") != order_ref:
        raise ProviderError("VNPAY_QUERY_RESPONSE_MISMATCH", 502)
    # 91 means VNPay has no transaction for this order; 94 means the query
    # itself was duplicated. Only the cancellation flow may use 91, and only
    # after the checkout URL has expired. It is never a payment failure proof.
    if response_code == "91":
        return {"state": "PENDING", "provider": "VNPAY", "no_transaction": True}
    if response_code == "94":
        return {"state": "PENDING", "provider": "VNPAY"}
    if response_code != "00":
        raise ProviderError("VNPAY_QUERY_REJECTED", 502)
    try:
        response_amount = int(response.get("vnp_Amount", -1))
    except (TypeError, ValueError):
        raise ProviderError("VNPAY_QUERY_INVALID_RESPONSE", 502) from None
    if response_amount != amount_vnd * 100:
        raise ProviderError("VNPAY_QUERY_RESPONSE_MISMATCH", 502)
    if not transaction_ref or transaction_status not in {"00", "02"}:
        return {"state": "PENDING", "provider": "VNPAY"}
    return {
        "state": "PAID" if transaction_status == "00" else "FAILED",
        "provider": "VNPAY",
        "transaction_ref": transaction_ref,
        "amount_vnd": amount_vnd,
        "response_code": response_code,
        "transaction_status": transaction_status,
        "request_id": request_id,
    }
