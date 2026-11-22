"""Unauthenticated provider callbacks; signed payloads are the only settlement proof."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

import base64
import hashlib
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing.providers import (
    momo_payment_state,
    verify_momo_ipn,
    verify_vnpay_callback,
)
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingPaymentAttemptModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db

router = APIRouter(prefix="/api/payment-callbacks/v1", tags=["Payment callbacks"])
logger = logging.getLogger(__name__)


def _digest(payload: dict) -> str:
    safe = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(safe.encode()).hexdigest()


def _invoice_for_attempt(db: Session, provider: str, order_ref: str):
    attempt = db.scalar(
        select(BillingPaymentAttemptModel).where(
            BillingPaymentAttemptModel.provider == provider,
            BillingPaymentAttemptModel.provider_order_ref == order_ref,
        )
    )
    if attempt is None:
        raise AdminError("PAYMENT_ATTEMPT_NOT_FOUND", 404)
    invoice = db.get(BillingInvoiceModel, attempt.invoice_id)
    if invoice is None:
        raise AdminError("INVOICE_NOT_FOUND", 404)
    return attempt, invoice


@router.post("/momo/ipn", status_code=204)
async def momo_ipn(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        payload = await request.json()
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid JSON") from None
    if not isinstance(payload, dict) or not verify_momo_ipn(settings, payload):
        raise HTTPException(401, "Invalid payment signature")
    if payload.get("partnerCode") != settings.momo_partner_code:
        raise HTTPException(401, "Invalid merchant")
    order_ref = payload.get("orderId")
    transaction_ref = str(payload.get("transId", ""))
    if not isinstance(order_ref, str) or not order_ref:
        raise HTTPException(422, "Missing order reference")
    try:
        extra = json.loads(base64.b64decode(payload.get("extraData", ""), validate=True))
        attempt, invoice = _invoice_for_attempt(db, "MOMO", order_ref)
        amount = int(payload.get("amount"))
        result_code = int(payload.get("resultCode"))
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(422, "Invalid payment fields") from None
    except AdminError as exc:
        raise HTTPException(exc.status, exc.code) from None
    if not isinstance(extra, dict) or extra.get("invoice_id") != invoice.invoice_id:
        raise HTTPException(409, "Invoice does not match payment attempt")
    if attempt.provider_request_ref and payload.get("requestId") != attempt.provider_request_ref:
        raise HTTPException(409, "Payment request does not match attempt")
    outcome = momo_payment_state(result_code)
    if outcome == "PENDING":
        # A signed but non-terminal notification is acknowledged and reconciled
        # later; it must never be recorded as a failed payment by default.
        return Response(status_code=204)
    if not transaction_ref:
        raise HTTPException(422, "Missing transaction reference")
    commerce = QuotaCommerceService(db, "provider:momo", settings)
    try:
        commerce.settle_verified(
            provider="MOMO",
            order_ref=order_ref,
            transaction_ref=transaction_ref,
            amount_vnd=amount,
            paid=outcome == "PAID",
            payload_digest=_digest(payload),
        )
    except AdminError as exc:
        raise HTTPException(exc.status, exc.code) from None
    return Response(status_code=204)


@router.get("/vnpay/ipn")
def vnpay_ipn(request: Request, db: Session = Depends(get_db)):
    try:
        return _process_vnpay_ipn(request, db)
    except Exception as exc:
        # Avoid logging exception details that may contain callback or SQL data.
        logger.error("VNPay IPN processing failed (%s)", type(exc).__name__)
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error("VNPay IPN rollback failed (%s)", type(rollback_error).__name__)
        return JSONResponse({"RspCode": "99", "Message": "Unknown error"})


def _process_vnpay_ipn(request: Request, db: Session) -> JSONResponse:
    settings = get_settings()
    params: dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        if key in params:
            return JSONResponse({"RspCode": "97", "Message": "Invalid signature"})
        params[key] = value
    if not verify_vnpay_callback(settings, params):
        return JSONResponse({"RspCode": "97", "Message": "Invalid signature"})
    if params.get("vnp_TmnCode") != settings.vnpay_tmn_code:
        return JSONResponse({"RspCode": "97", "Message": "Invalid merchant"})
    order_ref = params.get("vnp_TxnRef", "")
    transaction_ref = params.get("vnp_TransactionNo", "")
    if not order_ref or not transaction_ref:
        return JSONResponse({"RspCode": "99", "Message": "Missing transaction reference"})
    try:
        amount = int(params["vnp_Amount"]) // 100
    except (KeyError, ValueError):
        return JSONResponse({"RspCode": "99", "Message": "Invalid amount"})
    try:
        _, invoice = _invoice_for_attempt(db, "VNPAY", order_ref)
    except AdminError:
        return JSONResponse({"RspCode": "01", "Message": "Order not found"})
    if amount * 100 != int(params.get("vnp_Amount", "0")):
        return JSONResponse({"RspCode": "04", "Message": "Invalid amount"})
    response_code = params.get("vnp_ResponseCode")
    transaction_status = params.get("vnp_TransactionStatus")
    if response_code != "00" or transaction_status not in {"00", "02"}:
        # A reversal, unfinished or suspicious result needs QueryDR/operator
        # reconciliation. A callback is not itself sufficient to settle it.
        return JSONResponse({"RspCode": "00", "Message": "Callback accepted"})
    paid = transaction_status == "00"
    commerce = QuotaCommerceService(db, "provider:vnpay", settings)
    try:
        commerce.settle_verified(
            provider="VNPAY",
            order_ref=order_ref,
            transaction_ref=transaction_ref,
            amount_vnd=amount,
            paid=paid,
            payload_digest=_digest(params),
        )
    except AdminError as exc:
        if exc.code == "PAYMENT_ATTEMPT_NOT_FOUND":
            return JSONResponse({"RspCode": "01", "Message": "Order not found"})
        if exc.code == "PAYMENT_AMOUNT_MISMATCH":
            return JSONResponse({"RspCode": "04", "Message": "Invalid amount"})
        if exc.code == "INVALID_STATE_TRANSITION":
            return JSONResponse({"RspCode": "02", "Message": "Order already confirmed"})
        return JSONResponse({"RspCode": "99", "Message": "Unable to confirm payment"})
    return JSONResponse({"RspCode": "00", "Message": "Confirm Success"})
