"""Versioned video-quota catalog, checkout, settlement, and school allocations."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, or_, select, text

from sketch2life.domain.billing_capacity import quota_month
from sketch2life.domain.platform_admin import AdminError, require_revision
from sketch2life.infrastructure.billing.providers import (
    ProviderError,
    create_momo_checkout,
    create_vnpay_checkout,
    query_momo_transaction,
    query_vnpay_transaction,
    vnpay_order_info,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingPaymentAttemptModel,
    BillingPaymentEventModel,
    BillingProductAuditEventModel,
    BillingQuotaAllocationEventModel,
    BillingQuotaAllocationModel,
    BillingQuotaProductModel,
    BillingReceiptModel,
    BillingOfferModel,
    VideoQuotaGrantModel,
    VideoQuotaUsageModel,
)


class QuotaCommerceService:
    def __init__(self, db, actor: str, settings, clock=lambda: datetime.now(UTC)):
        self.db = db
        self.actor = actor
        self.settings = settings
        self.clock = clock

    def lock(self, key: str) -> None:
        self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
            {"scope": "billing:" + key},
        )

    def _command(self, operation: str, key: str, payload: dict, execute):
        self.lock(json.dumps((self.actor, operation, key)))
        pk = (self.actor, operation, key)
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        receipt = self.db.get(BillingReceiptModel, pk)
        if receipt:
            if receipt.fingerprint != fingerprint:
                raise AdminError("IDEMPOTENCY_CONFLICT", 409)
            return receipt.response_json
        result = execute()
        self.db.add(
            BillingReceiptModel(
                actor_ref=self.actor,
                operation=operation,
                key=key,
                fingerprint=fingerprint,
                response_json=result,
            )
        )
        self.db.commit()
        return result

    @staticmethod
    def _offer_view(offer: BillingOfferModel) -> dict:
        return {
            "offer_id": offer.offer_id,
            "product_id": offer.product_id,
            "version": offer.version,
            "display_name": offer.display_name,
            "offer_kind": offer.offer_kind,
            "cycle_months": offer.cycle_months,
            "owner_kind": offer.owner_kind,
            "units": offer.units,
            "amount_vnd": offer.amount_vnd,
            "created_at": offer.created_at.isoformat() if offer.created_at else None,
        }

    def product_view(self, product: BillingQuotaProductModel) -> dict:
        offer = self.db.get(BillingOfferModel, product.current_offer_id)
        if offer is None:
            raise AdminError("QUOTA_PRODUCT_OFFER_UNAVAILABLE", 409)
        return {
            **self._offer_view(offer),
            "active": product.active,
            "revision": product.revision,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        }

    def products(self, owner_kind: str | None = None, include_inactive: bool = False) -> dict:
        query = select(BillingQuotaProductModel)
        if owner_kind:
            query = query.where(BillingQuotaProductModel.owner_kind == owner_kind)
        if not include_inactive:
            query = query.where(BillingQuotaProductModel.active.is_(True))
        products = list(
            self.db.scalars(
                query.order_by(
                    BillingQuotaProductModel.owner_kind,
                    BillingQuotaProductModel.offer_kind,
                    BillingQuotaProductModel.created_at,
                )
            )
        )
        return {"items": [self.product_view(item) for item in products], "total": len(products)}

    def save_product(self, payload: dict, key: str, expected: int | None = None) -> dict:
        def execute():
            product_id = payload.get("product_id")
            if product_id is None:
                product_id = str(uuid4())
                version = 1
                product = BillingQuotaProductModel(
                    product_id=product_id,
                    owner_kind=payload["owner_kind"],
                    display_name=payload["display_name"],
                    offer_kind=payload["offer_kind"],
                    cycle_months=payload.get("cycle_months"),
                    current_offer_id="",
                    active=True,
                    revision=1,
                    created_by=self.actor,
                )
                self.db.add(product)
            else:
                product = self.db.get(BillingQuotaProductModel, product_id)
                if product is None:
                    raise AdminError("QUOTA_PRODUCT_NOT_FOUND", 404)
                require_revision(product.revision, expected)
                if (
                    product.owner_kind != payload["owner_kind"]
                    or product.offer_kind != payload["offer_kind"]
                ):
                    raise AdminError("QUOTA_PRODUCT_SCOPE_IMMUTABLE", 422)
                version = product.revision + 1
                product.display_name = payload["display_name"]
                product.cycle_months = payload.get("cycle_months")
                product.active = payload.get("active", product.active)
                product.revision = version
                product.updated_at = self.clock()
            offer_id = str(uuid4())
            offer = BillingOfferModel(
                offer_id=offer_id,
                product_id=product_id,
                version=version,
                display_name=payload["display_name"],
                offer_kind=payload["offer_kind"],
                cycle_months=payload.get("cycle_months"),
                owner_kind=payload["owner_kind"],
                units=payload["units"],
                amount_vnd=payload["amount_vnd"],
                created_by=self.actor,
            )
            self.db.add(offer)
            product.current_offer_id = offer_id
            self.db.flush()
            action = "CREATED" if version == 1 else "VERSIONED"
            self.db.add(
                BillingProductAuditEventModel(
                    event_id=str(uuid4()),
                    product_id=product_id,
                    offer_id=offer_id,
                    actor_ref=self.actor,
                    action=action,
                    snapshot={**self._offer_view(offer), "active": product.active, "revision": version},
                )
            )
            self.db.flush()
            return self.product_view(product)

        return self._command("quota-product.save", key, payload, execute)

    def set_product_active(self, product_id: str, active: bool, expected: int, key: str) -> dict:
        payload = {"product_id": product_id, "active": active, "expected_revision": expected}

        def execute():
            product = self.db.get(BillingQuotaProductModel, product_id)
            if product is None:
                raise AdminError("QUOTA_PRODUCT_NOT_FOUND", 404)
            require_revision(product.revision, expected)
            product.active = active
            product.revision += 1
            product.updated_at = self.clock()
            offer = self.db.get(BillingOfferModel, product.current_offer_id)
            if offer is None:
                raise AdminError("QUOTA_PRODUCT_OFFER_UNAVAILABLE", 409)
            self.db.add(
                BillingProductAuditEventModel(
                    event_id=str(uuid4()),
                    product_id=product_id,
                    offer_id=offer.offer_id,
                    actor_ref=self.actor,
                    action="ACTIVATED" if active else "DEACTIVATED",
                    snapshot={**self._offer_view(offer), "active": active, "revision": product.revision},
                )
            )
            return self.product_view(product)

        return self._command("quota-product.state", key, payload, execute)

    def _payment_enabled(self, provider: str) -> bool:
        if not self.settings.billing_real_payments_enabled:
            return False
        return (
            self.settings.momo_payment_configured
            if provider == "MOMO"
            else self.settings.vnpay_payment_configured
        )

    def checkout(self, product_id: str, owner_kind: str, owner_ref: str, provider: str,
                 payment_mode: str, key: str, client_ip: str = "127.0.0.1") -> dict:
        if not self._payment_enabled(provider):
            raise AdminError("PAYMENT_PROVIDER_NOT_AVAILABLE", 503)
        if payment_mode != "MANUAL":
            raise AdminError("AUTO_RENEWAL_NOT_CONFIGURED", 409)
        payload = {
            "product_id": product_id,
            "owner_kind": owner_kind,
            "owner_ref": owner_ref,
            "provider": provider,
            "payment_mode": payment_mode,
        }

        operation = "quota.checkout"
        self.lock(json.dumps((self.actor, operation, key)))
        pk = (self.actor, operation, key)
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        existing = self.db.get(BillingReceiptModel, pk)
        if existing:
            if existing.fingerprint != fingerprint:
                raise AdminError("IDEMPOTENCY_CONFLICT", 409)
            return existing.response_json

        def execute():
            self.lock("quota-scope:" + owner_kind + ":" + owner_ref)
            product = self.db.get(BillingQuotaProductModel, product_id)
            if product is None or not product.active or product.owner_kind != owner_kind:
                raise AdminError("QUOTA_PRODUCT_UNAVAILABLE", 404)
            offer = self.db.get(BillingOfferModel, product.current_offer_id)
            if offer is None:
                raise AdminError("QUOTA_PRODUCT_OFFER_UNAVAILABLE", 409)
            if provider == "MOMO" and not 1_000 <= offer.amount_vnd <= 50_000_000:
                raise AdminError("MOMO_AMOUNT_OUT_OF_RANGE", 422)
            open_attempt = self.db.scalar(
                select(BillingPaymentAttemptModel).join(
                    BillingInvoiceModel,
                    BillingPaymentAttemptModel.invoice_id == BillingInvoiceModel.invoice_id,
                ).where(
                    BillingInvoiceModel.owner_kind == owner_kind,
                    BillingInvoiceModel.owner_ref == owner_ref,
                    BillingInvoiceModel.state == "PENDING",
                    BillingPaymentAttemptModel.state.in_(("REQUESTING", "OPEN", "UNKNOWN")),
                ).limit(1)
            )
            if open_attempt:
                raise AdminError("PAYMENT_ATTEMPT_ALREADY_OPEN", 409)
            invoice_id = str(uuid4())
            invoice = BillingInvoiceModel(
                invoice_id=invoice_id,
                product_id=product.product_id,
                offer_id=offer.offer_id,
                owner_kind=owner_kind,
                owner_ref=owner_ref,
                units=offer.units,
                amount_vnd=offer.amount_vnd,
                state="PENDING",
                provider=provider,
                payment_mode=payment_mode,
                revision=1,
            )
            order_ref = "S2L" + uuid4().hex
            order_info = vnpay_order_info(order_ref) if provider == "VNPAY" else None
            request_ref = str(uuid4()) if provider == "MOMO" else None
            checkout_now = self.clock()
            if checkout_now.tzinfo is None:
                checkout_now = checkout_now.replace(tzinfo=UTC)
            transaction_date = (
                checkout_now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y%m%d%H%M%S")
                if provider == "VNPAY"
                else None
            )
            attempt = BillingPaymentAttemptModel(
                attempt_id=str(uuid4()),
                invoice_id=invoice_id,
                provider=provider,
                provider_order_ref=order_ref,
                provider_request_ref=request_ref,
                provider_transaction_date=transaction_date,
                provider_order_info=order_info,
                state="REQUESTING",
                revision=1,
            )
            self.db.add_all([invoice, attempt])
            self.db.flush()
            # Persist intent before network I/O so a timeout can never create a second charge.
            response = {
                "invoice_id": invoice_id,
                "state": "PENDING",
                "attempt_state": "REQUESTING",
                "provider": provider,
                "amount_vnd": offer.amount_vnd,
                "units": offer.units,
                "checkout_url": None,
            }
            receipt = BillingReceiptModel(
                actor_ref=self.actor,
                operation=operation,
                key=key,
                fingerprint=fingerprint,
                response_json=response,
            )
            self.db.add(receipt)
            self.db.commit()
            try:
                if provider == "MOMO":
                    checkout = create_momo_checkout(
                        self.settings,
                        invoice_id=invoice_id,
                        amount_vnd=offer.amount_vnd,
                        order_ref=order_ref,
                        request_id=request_ref,
                    )
                else:
                    checkout = create_vnpay_checkout(
                        self.settings,
                        invoice_id=invoice_id,
                        amount_vnd=offer.amount_vnd,
                        order_ref=order_ref,
                        order_info=order_info,
                        client_ip=client_ip,
                        transaction_date=transaction_date,
                    )
            except ProviderError as exc:
                uncertain = exc.code in {
                    "PAYMENT_PROVIDER_UNAVAILABLE",
                    "PAYMENT_PROVIDER_INVALID_RESPONSE",
                    "MOMO_RESPONSE_SIGNATURE_INVALID",
                }
                # A provider callback can race the checkout response. Re-read under
                # row locks so a verified settlement is never downgraded to UNKNOWN
                # or FAILED by a late HTTP error.
                attempt = self.db.scalar(
                    select(BillingPaymentAttemptModel)
                    .where(BillingPaymentAttemptModel.attempt_id == attempt.attempt_id)
                    .execution_options(populate_existing=True)
                    .with_for_update()
                )
                invoice = self.db.scalar(
                    select(BillingInvoiceModel)
                    .where(BillingInvoiceModel.invoice_id == invoice_id)
                    .execution_options(populate_existing=True)
                    .with_for_update()
                )
                receipt = self.db.get(BillingReceiptModel, pk)
                if attempt is None or invoice is None or receipt is None:
                    raise AdminError("PAYMENT_ATTEMPT_NOT_FOUND", 409) from None
                if invoice.state == "PENDING" and attempt.state == "REQUESTING":
                    attempt.state = "UNKNOWN" if uncertain else "FAILED"
                    attempt.revision += 1
                    attempt.updated_at = self.clock()
                    if uncertain and provider == "VNPAY":
                        expiry_base = self.clock()
                        if expiry_base.tzinfo is None:
                            expiry_base = expiry_base.replace(tzinfo=UTC)
                        attempt.expires_at = expiry_base + timedelta(minutes=15)
                    if not uncertain:
                        invoice.state = "FAILED"
                        invoice.revision += 1
                response.update(
                    {
                        "state": invoice.state,
                        "attempt_state": attempt.state,
                        "checkout_url": attempt.checkout_url,
                    }
                )
                if attempt.expires_at:
                    response["expires_at"] = attempt.expires_at.isoformat()
                receipt.response_json = response
                self.db.commit()
                if invoice.state == "PAID":
                    return response
                if exc.status >= 500:
                    raise AdminError(exc.code, exc.status) from None
                raise AdminError(exc.code, exc.status) from None
            # A signed provider callback may arrive before its checkout HTTP
            # response. Lock and refresh both records before writing OPEN.
            attempt = self.db.scalar(
                select(BillingPaymentAttemptModel)
                .where(BillingPaymentAttemptModel.attempt_id == attempt.attempt_id)
                .execution_options(populate_existing=True)
                .with_for_update()
            )
            invoice = self.db.scalar(
                select(BillingInvoiceModel)
                .where(BillingInvoiceModel.invoice_id == invoice_id)
                .execution_options(populate_existing=True)
                .with_for_update()
            )
            receipt = self.db.get(BillingReceiptModel, pk)
            if attempt is None or invoice is None or receipt is None:
                raise AdminError("PAYMENT_ATTEMPT_NOT_FOUND", 409)
            attempt.checkout_url = checkout["checkout_url"]
            attempt.expires_at = checkout["expires_at"]
            if invoice.state == "PENDING" and attempt.state in {"REQUESTING", "UNKNOWN"}:
                attempt.state = "OPEN"
                attempt.revision += 1
                attempt.updated_at = self.clock()
            response.update({
                "state": invoice.state,
                "attempt_state": attempt.state,
                "checkout_url": attempt.checkout_url if invoice.state == "PENDING" else None,
                "expires_at": attempt.expires_at.isoformat() if attempt.expires_at else None,
            })
            receipt.response_json = response
            self.db.commit()
            return response

        return execute()

    def invoice(self, invoice_id: str) -> BillingInvoiceModel:
        row = self.db.get(BillingInvoiceModel, invoice_id)
        if row is None:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return row

    def reconcile_invoice(self, invoice_id: str) -> dict:
        invoice = self.db.get(BillingInvoiceModel, invoice_id)
        if invoice is None:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        if invoice.state != "PENDING":
            return {"invoice_id": invoice_id, "state": invoice.state, "reconciled": False}
        attempt = self.db.scalar(
            select(BillingPaymentAttemptModel)
            .where(BillingPaymentAttemptModel.invoice_id == invoice_id)
            .order_by(BillingPaymentAttemptModel.created_at.desc())
            .limit(1)
        )
        if attempt is None or attempt.state not in {"REQUESTING", "OPEN", "UNKNOWN"}:
            raise AdminError("PAYMENT_ATTEMPT_NOT_RECONCILABLE", 409)
        try:
            if invoice.provider == "MOMO":
                result = query_momo_transaction(
                    self.settings,
                    order_ref=attempt.provider_order_ref,
                    amount_vnd=invoice.amount_vnd,
                )
            elif invoice.provider == "VNPAY":
                if not attempt.provider_transaction_date:
                    raise AdminError("PAYMENT_TRANSACTION_DATE_UNAVAILABLE", 409)
                result = query_vnpay_transaction(
                    self.settings,
                    order_ref=attempt.provider_order_ref,
                    amount_vnd=invoice.amount_vnd,
                    transaction_date=attempt.provider_transaction_date,
                    order_info=(
                        attempt.provider_order_info
                        or f"Quota video {invoice.invoice_id}"
                    ),
                )
            else:
                raise AdminError("PAYMENT_PROVIDER_NOT_SUPPORTED", 409)
        except ProviderError as exc:
            raise AdminError(exc.code, exc.status) from None
        if result["state"] == "PENDING" or (
            result["state"] == "PAID" and not result.get("transaction_ref")
        ):
            return {"invoice_id": invoice_id, "state": "PENDING", "reconciled": False}
        digest = hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        try:
            settled = self.settle_verified(
                provider=invoice.provider,
                order_ref=attempt.provider_order_ref,
                transaction_ref=result.get("transaction_ref"),
                amount_vnd=result.get("amount_vnd", invoice.amount_vnd),
                paid=result["state"] == "PAID",
                payload_digest=digest,
            )
        except AdminError as exc:
            # A callback can confirm the same transaction while this query is in
            # flight. Prefer the committed provider outcome over a stale transition.
            if exc.code == "INVALID_STATE_TRANSITION":
                current = self.db.get(BillingInvoiceModel, invoice_id)
                if current and current.state == result["state"]:
                    return {
                        "invoice_id": invoice_id,
                        "state": current.state,
                        "reconciled": True,
                        "duplicate": True,
                    }
            raise
        return {
            "invoice_id": invoice_id,
            "state": settled["state"],
            "reconciled": True,
            "duplicate": settled["duplicate"],
        }

    def cancel_expired_vnpay_invoice(self, invoice_id: str) -> dict:
        """Close an expired VNPay order only after a signed QueryDR says it is absent."""
        self.lock("cancel-expired-vnpay:" + invoice_id)
        invoice = self.db.scalar(
            select(BillingInvoiceModel)
            .where(BillingInvoiceModel.invoice_id == invoice_id)
            .with_for_update()
        )
        if invoice is None:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        if invoice.state != "PENDING":
            return {
                "invoice_id": invoice_id,
                "state": invoice.state,
                "canceled": invoice.state == "CANCELED",
                "reconciled": False,
            }
        if invoice.provider != "VNPAY":
            raise AdminError("PAYMENT_CANCEL_PROVIDER_NOT_SUPPORTED", 409)

        attempt = self.db.scalar(
            select(BillingPaymentAttemptModel)
            .where(BillingPaymentAttemptModel.invoice_id == invoice_id)
            .order_by(BillingPaymentAttemptModel.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        if attempt is None or attempt.state not in {"REQUESTING", "OPEN", "UNKNOWN"}:
            raise AdminError("PAYMENT_ATTEMPT_NOT_RECONCILABLE", 409)
        now = self.clock()
        expires_at = attempt.expires_at
        if expires_at is None:
            raise AdminError("PAYMENT_EXPIRY_UNAVAILABLE", 409)
        if expires_at.tzinfo is None and now.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        if expires_at > now:
            raise AdminError("PAYMENT_CHECKOUT_STILL_ACTIVE", 409)
        if not attempt.provider_transaction_date:
            raise AdminError("PAYMENT_TRANSACTION_DATE_UNAVAILABLE", 409)

        try:
            result = query_vnpay_transaction(
                self.settings,
                order_ref=attempt.provider_order_ref,
                amount_vnd=invoice.amount_vnd,
                transaction_date=attempt.provider_transaction_date,
                order_info=attempt.provider_order_info or f"Quota video {invoice.invoice_id}",
            )
        except ProviderError as exc:
            raise AdminError(exc.code, exc.status) from None

        if result["state"] in {"PAID", "FAILED"}:
            digest = hashlib.sha256(
                json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            settled = self.settle_verified(
                provider="VNPAY",
                order_ref=attempt.provider_order_ref,
                transaction_ref=result.get("transaction_ref"),
                amount_vnd=result.get("amount_vnd", invoice.amount_vnd),
                paid=result["state"] == "PAID",
                payload_digest=digest,
            )
            return {
                "invoice_id": invoice_id,
                "state": settled["state"],
                "canceled": False,
                "reconciled": True,
                "duplicate": settled["duplicate"],
            }

        if not result.get("no_transaction"):
            return {
                "invoice_id": invoice_id,
                "state": "PENDING",
                "canceled": False,
                "reconciled": False,
            }

        digest = hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.db.add(
            BillingPaymentEventModel(
                event_id=f"VNPAY:terminal-cancel:{attempt.provider_order_ref}",
                invoice_id=invoice.invoice_id,
                amount_vnd=invoice.amount_vnd,
                outcome="CANCELED",
                provider="VNPAY",
                provider_transaction_ref=None,
                payload_digest=digest,
            )
        )
        invoice.state = "CANCELED"
        invoice.revision += 1
        attempt.state = "CANCELED"
        attempt.revision += 1
        attempt.updated_at = now
        self.db.commit()
        return {
            "invoice_id": invoice_id,
            "state": "CANCELED",
            "canceled": True,
            "reconciled": True,
            "duplicate": False,
        }

    def invoice_view(self, invoice: BillingInvoiceModel, include_owner: bool = True) -> dict:
        attempts = list(
            self.db.scalars(
                select(BillingPaymentAttemptModel)
                .where(BillingPaymentAttemptModel.invoice_id == invoice.invoice_id)
                .order_by(BillingPaymentAttemptModel.created_at.desc())
            )
        )
        result = {
            "invoice_id": invoice.invoice_id,
            "product_id": invoice.product_id,
            "offer_id": invoice.offer_id,
            "owner_kind": invoice.owner_kind,
            "units": invoice.units,
            "amount_vnd": invoice.amount_vnd,
            "state": invoice.state,
            "provider": invoice.provider,
            "payment_mode": invoice.payment_mode,
            "revision": invoice.revision,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            "attempts": [
                {
                    "provider": item.provider,
                    "state": item.state,
                    "checkout_url": item.checkout_url,
                    "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                }
                for item in attempts
            ],
        }
        if include_owner:
            result["owner_ref"] = invoice.owner_ref
        return result

    def invoices(self, owner_kind: str | None = None, owner_ref: str | None = None,
                  state: str | None = None, limit: int = 100) -> dict:
        query = select(BillingInvoiceModel)
        if owner_kind:
            query = query.where(BillingInvoiceModel.owner_kind == owner_kind)
        if owner_ref:
            query = query.where(BillingInvoiceModel.owner_ref == owner_ref)
        if state:
            query = query.where(BillingInvoiceModel.state == state)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = list(self.db.scalars(query.order_by(BillingInvoiceModel.created_at.desc()).limit(limit)))
        return {"items": [self.invoice_view(row) for row in rows], "total": total}

    def payment_events(self, limit: int = 100) -> dict:
        rows = list(self.db.scalars(
            select(BillingPaymentEventModel)
            .where(BillingPaymentEventModel.provider.in_(("MOMO", "VNPAY")))
            .order_by(BillingPaymentEventModel.created_at.desc())
            .limit(limit)
        ))
        total = self.db.scalar(
            select(func.count()).select_from(BillingPaymentEventModel).where(
                BillingPaymentEventModel.provider.in_(("MOMO", "VNPAY"))
            )
        ) or 0
        return {
            "items": [
                {
                    "event_id": row.event_id,
                    "invoice_id": row.invoice_id,
                    "provider": row.provider,
                    "provider_transaction_ref": row.provider_transaction_ref,
                    "amount_vnd": row.amount_vnd,
                    "outcome": row.outcome,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ],
            "total": total,
        }

    def product_events(self, product_id: str, limit: int = 100) -> dict:
        rows = list(self.db.scalars(
            select(BillingProductAuditEventModel)
            .where(BillingProductAuditEventModel.product_id == product_id)
            .order_by(BillingProductAuditEventModel.created_at.desc())
            .limit(limit)
        ))
        return {
            "items": [
                {
                    "event_id": row.event_id,
                    "product_id": row.product_id,
                    "offer_id": row.offer_id,
                    "actor_ref": row.actor_ref,
                    "action": row.action,
                    "snapshot": row.snapshot,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ],
            "total": len(rows),
        }

    def user_invoice(self, invoice_id: str, owner_kind: str, owner_ref: str) -> dict:
        row = self.db.scalar(
            select(BillingInvoiceModel).where(
                BillingInvoiceModel.invoice_id == invoice_id,
                BillingInvoiceModel.owner_kind == owner_kind,
                BillingInvoiceModel.owner_ref == owner_ref,
            )
        )
        if row is None:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return self.invoice_view(row, include_owner=False)

    def settle_verified(self, *, provider: str, order_ref: str, transaction_ref: str | None,
                        amount_vnd: int, paid: bool, payload_digest: str) -> dict:
        if paid and not transaction_ref:
            raise AdminError("PAYMENT_TRANSACTION_REF_REQUIRED", 409)
        event_id = (
            f"{provider}:{transaction_ref}"
            if transaction_ref
            else f"{provider}:terminal-failure:{order_ref}"
        )
        self.lock("provider-event:" + event_id)
        attempt = self.db.scalar(
            select(BillingPaymentAttemptModel)
            .where(
                BillingPaymentAttemptModel.provider == provider,
                BillingPaymentAttemptModel.provider_order_ref == order_ref,
            )
            .with_for_update()
        )
        if attempt is None:
            raise AdminError("PAYMENT_ATTEMPT_NOT_FOUND", 404)
        invoice = self.db.scalar(
            select(BillingInvoiceModel)
            .where(BillingInvoiceModel.invoice_id == attempt.invoice_id)
            .with_for_update()
        )
        if invoice is None:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        prior = self.db.get(BillingPaymentEventModel, event_id)
        outcome = "PAID" if paid else "FAILED"
        if prior:
            if (
                prior.invoice_id != invoice.invoice_id
                or prior.amount_vnd != amount_vnd
                or prior.outcome != outcome
            ):
                raise AdminError("PAYMENT_EVENT_CONFLICT", 409)
            return {"state": invoice.state, "duplicate": True}
        if invoice.provider != provider or invoice.amount_vnd != amount_vnd:
            raise AdminError("PAYMENT_AMOUNT_MISMATCH", 409)
        was_canceled = invoice.state == "CANCELED"
        if invoice.state != "PENDING" and not (was_canceled and paid):
            raise AdminError("INVALID_STATE_TRANSITION", 409)
        self.db.add(
            BillingPaymentEventModel(
                event_id=event_id,
                invoice_id=invoice.invoice_id,
                amount_vnd=amount_vnd,
                outcome=outcome,
                provider=provider,
                provider_transaction_ref=transaction_ref,
                payload_digest=payload_digest,
            )
        )
        invoice.state = "PAID" if paid else ("CANCELED" if was_canceled else "FAILED")
        invoice.revision += 1
        attempt.state = "PAID" if paid else ("CANCELED" if was_canceled else "FAILED")
        attempt.revision += 1
        attempt.updated_at = self.clock()
        if paid:
            offer = self.db.get(BillingOfferModel, invoice.offer_id)
            if offer is None:
                raise AdminError("QUOTA_PRODUCT_OFFER_UNAVAILABLE", 409)
            if offer.offer_kind == "MONTHLY":
                period, expiry = quota_month(self.clock())
                kind = "MONTHLY"
            else:
                period, expiry, kind = None, None, "TOP_UP"
            self.db.add(
                VideoQuotaGrantModel(
                    grant_id=str(uuid4()),
                    owner_kind=invoice.owner_kind,
                    owner_ref=invoice.owner_ref,
                    kind=kind,
                    units=invoice.units,
                    invoice_id=invoice.invoice_id,
                    period=period,
                    expires_at=expiry,
                )
            )
        self.db.commit()
        return {"state": invoice.state, "duplicate": False}

    @staticmethod
    def _usage_count(db, grant_id: str) -> int:
        return int(
            db.scalar(
                select(func.count()).select_from(VideoQuotaUsageModel).where(
                    VideoQuotaUsageModel.grant_id == grant_id
                )
            )
            or 0
        )

    def available_grants(self, owner_kind: str, owner_ref: str) -> list[VideoQuotaGrantModel]:
        return list(
            self.db.scalars(
                select(VideoQuotaGrantModel)
                .where(
                    VideoQuotaGrantModel.owner_kind == owner_kind,
                    VideoQuotaGrantModel.owner_ref == owner_ref,
                    or_(VideoQuotaGrantModel.expires_at.is_(None), VideoQuotaGrantModel.expires_at > self.clock()),
                )
                .order_by(
                    case(
                        (VideoQuotaGrantModel.kind == "INCLUDED", 0),
                        (VideoQuotaGrantModel.kind == "MONTHLY", 1),
                        else_=2,
                    ),
                    VideoQuotaGrantModel.created_at,
                    VideoQuotaGrantModel.grant_id,
                )
            )
        )

    def _allocation_net(self, allocation_id: str) -> int:
        rows = self.db.execute(
            select(BillingQuotaAllocationEventModel.event_kind, func.sum(BillingQuotaAllocationEventModel.units))
            .where(BillingQuotaAllocationEventModel.allocation_id == allocation_id)
            .group_by(BillingQuotaAllocationEventModel.event_kind)
        ).all()
        values = {kind: int(total or 0) for kind, total in rows}
        return max(0, values.get("ALLOCATED", 0) - values.get("RECLAIMED", 0) - values.get("RETURNED", 0) - values.get("CONSUMED", 0))

    def quota_summary(self, owner_kind: str, owner_ref: str) -> dict:
        grants = self.available_grants(owner_kind, owner_ref)
        grant_views = []
        total_remaining = 0
        for grant in grants:
            used = self._usage_count(self.db, grant.grant_id)
            remaining = max(0, grant.units - used)
            total_remaining += remaining
            grant_views.append({
                "grant_id": grant.grant_id,
                "kind": grant.kind,
                "units": grant.units,
                "used": used,
                "available": remaining,
                "period": grant.period,
                "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
            })
        allocation_summary = None
        if owner_kind == "ORGANIZATION":
            rows = list(self.db.scalars(
                select(BillingQuotaAllocationModel).where(
                    BillingQuotaAllocationModel.organization_ref == owner_ref,
                    BillingQuotaAllocationModel.active.is_(True),
                )
            ))
            reserved = sum(self._allocation_net(row.allocation_id) for row in rows)
            allocation_summary = {
                "allocated_unused_units": reserved,
                "available_school_units": max(0, total_remaining - reserved),
                "teachers": [
                    {
                        "teacher_ref": row.teacher_ref,
                        "allocation_id": row.allocation_id,
                        "available_units": self._allocation_net(row.allocation_id),
                        "revision": row.revision,
                        "active": row.active,
                    }
                    for row in rows
                ],
            }
        return {
            "owner_kind": owner_kind,
            "available_units": max(0, total_remaining - (allocation_summary or {}).get("allocated_unused_units", 0)),
            "granted_units": sum(g.units for g in grants),
            "used_units": sum(self._usage_count(self.db, g.grant_id) for g in grants),
            "grants": grant_views,
            "allocation": allocation_summary,
        }

    def allocate(self, organization_ref: str, teacher_ref: str, units: int,
                 key: str, expected: int | None = None) -> dict:
        payload = {"organization_ref": organization_ref, "teacher_ref": teacher_ref, "units": units,
                   "expected_revision": expected}

        def execute():
            self.lock("quota-scope:ORGANIZATION:" + organization_ref)
            teacher = self.db.scalar(select(AdultIdentityModel).where(
                AdultIdentityModel.subject == teacher_ref,
                AdultIdentityModel.account_role == "teacher",
                AdultIdentityModel.state == "active",
            ))
            assigned = self.db.scalar(select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == organization_ref,
                OrganizationAssignmentModel.subject == teacher_ref,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            ).limit(1))
            if teacher is None or assigned is None:
                raise AdminError("TEACHER_ASSIGNMENT_UNAVAILABLE", 409)
            allocation = self.db.scalar(select(BillingQuotaAllocationModel).where(
                BillingQuotaAllocationModel.organization_ref == organization_ref,
                BillingQuotaAllocationModel.teacher_ref == teacher_ref,
            ).with_for_update())
            if allocation is None:
                allocation = BillingQuotaAllocationModel(
                    allocation_id=str(uuid4()),
                    organization_ref=organization_ref,
                    teacher_ref=teacher_ref,
                    active=True,
                    revision=1,
                )
                self.db.add(allocation)
                self.db.flush()
            elif expected is not None:
                require_revision(allocation.revision, expected)
            summary = self.quota_summary("ORGANIZATION", organization_ref)
            school_available = summary["available_units"]
            if units > school_available:
                raise AdminError("SCHOOL_QUOTA_INSUFFICIENT", 409)
            allocation.active = True
            allocation.revision += 1
            allocation.updated_at = self.clock()
            self.db.add(BillingQuotaAllocationEventModel(
                event_id=str(uuid4()),
                allocation_id=allocation.allocation_id,
                organization_ref=organization_ref,
                teacher_ref=teacher_ref,
                event_kind="ALLOCATED",
                units=units,
                actor_ref=self.actor,
                operation_key=key,
            ))
            return {
                "allocation_id": allocation.allocation_id,
                "teacher_ref": teacher_ref,
                "available_units": self._allocation_net(allocation.allocation_id) + units,
                "revision": allocation.revision,
            }

        return self._command("quota.allocate", key, payload, execute)

    def reclaim(self, organization_ref: str, teacher_ref: str, units: int,
                expected: int, key: str) -> dict:
        payload = {"organization_ref": organization_ref, "teacher_ref": teacher_ref, "units": units}

        def execute():
            self.lock("quota-scope:ORGANIZATION:" + organization_ref)
            allocation = self.db.scalar(select(BillingQuotaAllocationModel).where(
                BillingQuotaAllocationModel.organization_ref == organization_ref,
                BillingQuotaAllocationModel.teacher_ref == teacher_ref,
            ).with_for_update())
            if allocation is None or not allocation.active:
                raise AdminError("QUOTA_ALLOCATION_NOT_FOUND", 404)
            require_revision(allocation.revision, expected)
            available = self._allocation_net(allocation.allocation_id)
            if units > available:
                raise AdminError("QUOTA_ALLOCATION_IN_USE", 409)
            allocation.revision += 1
            allocation.updated_at = self.clock()
            self.db.add(BillingQuotaAllocationEventModel(
                event_id=str(uuid4()),
                allocation_id=allocation.allocation_id,
                organization_ref=organization_ref,
                teacher_ref=teacher_ref,
                event_kind="RECLAIMED",
                units=units,
                actor_ref=self.actor,
                operation_key=key,
            ))
            remaining = available - units
            if remaining == 0:
                allocation.active = False
            return {"allocation_id": allocation.allocation_id, "teacher_ref": teacher_ref,
                    "available_units": remaining, "revision": allocation.revision}

        return self._command("quota.reclaim", key, payload, execute)

    def allocations(self, organization_ref: str, include_inactive: bool = False) -> dict:
        query = select(BillingQuotaAllocationModel).where(
            BillingQuotaAllocationModel.organization_ref == organization_ref
        )
        if not include_inactive:
            query = query.where(BillingQuotaAllocationModel.active.is_(True))
        rows = list(self.db.scalars(query.order_by(BillingQuotaAllocationModel.updated_at.desc())))
        return {
            "items": [
                {
                    "allocation_id": row.allocation_id,
                    "teacher_ref": row.teacher_ref,
                    "available_units": self._allocation_net(row.allocation_id),
                    "active": row.active,
                    "revision": row.revision,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
                for row in rows
            ],
            "total": len(rows),
        }

    def consume_teacher_quota(self, organization_ref: str, teacher_ref: str,
                              admission_ref: str) -> dict:
        """Consume one school-owned unit from a Teacher's active allocation."""
        self.lock("quota-scope:ORGANIZATION:" + organization_ref)
        existing = self.db.scalar(select(VideoQuotaUsageModel).where(
            VideoQuotaUsageModel.owner_kind == "ORGANIZATION",
            VideoQuotaUsageModel.owner_ref == organization_ref,
            VideoQuotaUsageModel.admission_ref == admission_ref,
        ))
        allocation = self.db.scalar(select(BillingQuotaAllocationModel).where(
            BillingQuotaAllocationModel.organization_ref == organization_ref,
            BillingQuotaAllocationModel.teacher_ref == teacher_ref,
            BillingQuotaAllocationModel.active.is_(True),
        ).with_for_update())
        if allocation is None:
            raise AdminError("QUOTA_ALLOCATION_NOT_FOUND", 409)
        if existing is not None:
            if existing.allocation_id != allocation.allocation_id:
                raise AdminError("QUOTA_ADMISSION_CONFLICT", 409)
            return {"consumed": True, "duplicate": True, "allocation_id": allocation.allocation_id}
        available = self._allocation_net(allocation.allocation_id)
        if available < 1:
            raise AdminError("TEACHER_QUOTA_INSUFFICIENT", 409)
        grant = next((item for item in self.available_grants("ORGANIZATION", organization_ref)
                      if self._usage_count(self.db, item.grant_id) < item.units), None)
        if grant is None:
            raise AdminError("SCHOOL_QUOTA_INSUFFICIENT", 409)
        use_key = "teacher-use:" + hashlib.sha256(admission_ref.encode()).hexdigest()
        if self.db.scalar(select(BillingQuotaAllocationEventModel).where(
            BillingQuotaAllocationEventModel.allocation_id == allocation.allocation_id,
            BillingQuotaAllocationEventModel.operation_key == use_key,
        )):
            raise AdminError("QUOTA_ADMISSION_CONFLICT", 409)
        self.db.add(VideoQuotaUsageModel(
            usage_id=str(uuid4()), grant_id=grant.grant_id,
            owner_kind="ORGANIZATION", owner_ref=organization_ref,
            admission_ref=admission_ref, allocation_id=allocation.allocation_id,
            teacher_ref=teacher_ref,
        ))
        self.db.add(BillingQuotaAllocationEventModel(
            event_id=str(uuid4()), allocation_id=allocation.allocation_id,
            organization_ref=organization_ref, teacher_ref=teacher_ref,
            event_kind="CONSUMED", units=1, actor_ref=self.actor,
            operation_key=use_key,
        ))
        allocation.revision += 1
        allocation.updated_at = self.clock()
        self.db.commit()
        return {
            "consumed": True,
            "duplicate": False,
            "allocation_id": allocation.allocation_id,
            "available_units": available - 1,
            "revision": allocation.revision,
        }

    @classmethod
    def return_teacher_allocation(cls, db, *, organization_ref: str, teacher_ref: str,
                                  actor_ref: str, event_key: str) -> int:
        allocation = db.scalar(select(BillingQuotaAllocationModel).where(
            BillingQuotaAllocationModel.organization_ref == organization_ref,
            BillingQuotaAllocationModel.teacher_ref == teacher_ref,
            BillingQuotaAllocationModel.active.is_(True),
        ).with_for_update())
        if allocation is None:
            return 0
        service = object.__new__(cls)
        service.db = db
        available = service._allocation_net(allocation.allocation_id)
        if available:
            db.add(BillingQuotaAllocationEventModel(
                event_id=str(uuid4()),
                allocation_id=allocation.allocation_id,
                organization_ref=organization_ref,
                teacher_ref=teacher_ref,
                event_kind="RETURNED",
                units=available,
                actor_ref=actor_ref,
                operation_key=event_key,
            ))
        allocation.active = False
        allocation.revision += 1
        allocation.updated_at = datetime.now(UTC)
        return available


def scope_for_be1(db, principal) -> tuple[str, str]:
    identity = db.get(AdultIdentityModel, principal.subject)
    if identity is None or identity.state != "active":
        raise AdminError("ACCOUNT_SCOPE_UNAVAILABLE", 403)
    if identity.account_role == "parent":
        return "PARENT_ACCOUNT", identity.account_id
    if identity.account_role != "school_manager":
        raise AdminError("BILLING_PURCHASE_NOT_ALLOWED", 403)
    assignments = list(db.scalars(select(OrganizationAssignmentModel).where(
        OrganizationAssignmentModel.subject == principal.subject,
        OrganizationAssignmentModel.role == "school_admin",
        OrganizationAssignmentModel.class_id.is_(None),
        OrganizationAssignmentModel.active.is_(True),
    )))
    active_orgs = {
        row.organization_id
        for row in assignments
        if db.scalar(select(OrganizationModel.organization_id).where(
            OrganizationModel.organization_id == row.organization_id,
            OrganizationModel.state == "active",
        ))
    }
    if len(active_orgs) != 1:
        raise AdminError("BILLING_SCOPE_SELECTION_REQUIRED", 409)
    return "ORGANIZATION", next(iter(active_orgs))
