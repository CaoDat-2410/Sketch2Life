"""Pricing and checkout for organization capacity purchases."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.domain.billing_capacity import prorated_vnd
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing.providers import (
    ProviderError,
    create_momo_checkout,
    create_vnpay_checkout,
    vnpay_order_info,
)
from sketch2life.infrastructure.billing.quota_commerce import (
    QuotaCommerceService,
    capacity_invoice_filter,
)
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingPaymentAttemptModel,
    BillingReceiptModel,
    CapacityPriceModel,
    SubscriptionEventModel,
    SubscriptionModel,
)


def _utc(value: datetime) -> datetime:
    # SQLite fixtures can return naive UTC timestamps; PostgreSQL returns aware timestamps.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def capacity_quote(
    db: Session, organization_id: str, addon_slots: int, now: datetime, settings: Any
) -> dict[str, Any]:
    """Compute a quote without persisting an invoice or making provider requests."""
    if isinstance(addon_slots, bool) or not isinstance(addon_slots, int) or addon_slots < 1:
        raise AdminError("INVALID_CAPACITY_QUOTE", 422)
    subscription = db.scalar(
        select(SubscriptionModel).where(SubscriptionModel.organization_ref == organization_id)
    )
    if subscription is None:
        raise AdminError("SUBSCRIPTION_REQUIRED", 409)
    start, end, instant = map(_utc, (subscription.period_start, subscription.period_end, now))
    if instant >= end:
        raise AdminError("SUBSCRIPTION_PERIOD_ENDED", 409)
    if subscription.state not in {"ACTIVE", "CANCEL_AT_PERIOD_END"}:
        raise AdminError("SUBSCRIPTION_NOT_ACTIVE", 409)
    if subscription.addon_slots + addon_slots > 1000:
        raise AdminError("CAPACITY_LIMIT_EXCEEDED", 422)
    if db.scalar(
        select(SubscriptionEventModel.event_id)
        .where(
            SubscriptionEventModel.subscription_id == subscription.subscription_id,
            SubscriptionEventModel.kind == "CAPACITY_DOWNGRADE_SCHEDULED",
            SubscriptionEventModel.effective_at == subscription.period_end,
        )
        .limit(1)
    ):
        raise AdminError("DOWNGRADE_SCHEDULED", 409)
    price = db.get(CapacityPriceModel, subscription.price_id)
    if price is None:
        raise AdminError("PRICE_UNAVAILABLE", 409)
    amount = prorated_vnd(addon_slots, price.slot_amount_vnd, start, end, instant)
    remaining = end - instant
    duration = end - start

    def micros(delta: timedelta) -> int:
        return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds

    remaining_us, duration_us = micros(remaining), micros(duration)
    ratio = str(Decimal(remaining_us) / Decimal(duration_us))
    enabled = settings.billing_real_payments_enabled
    return {
        "price_id": price.price_id,
        "cycle_months": price.cycle_months,
        "base_amount_vnd": price.base_amount_vnd,
        "slot_amount_vnd": price.slot_amount_vnd,
        "quantity": addon_slots,
        "current_addon_slots": subscription.addon_slots,
        "resulting_capacity": 10 + subscription.addon_slots + addon_slots,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "remaining_time_ratio": ratio,
        "remaining_microseconds": remaining_us,
        "period_microseconds": duration_us,
        "amount_vnd": amount,
        "formula": "quantity × slot price × remaining time / period duration; VND half-up",
        "quoted_at": instant.isoformat(),
        "momo_checkout_enabled": bool(enabled and settings.momo_payment_configured),
        "vnpay_checkout_enabled": bool(enabled and settings.vnpay_payment_configured),
        "synthetic_sandbox_price": True,
    }


class CapacityCommerceService(QuotaCommerceService):
    def checkout_slots(
        self,
        organization_id: str,
        addon_slots: int,
        provider: str,
        key: str,
        *,
        expected_amount_vnd: int,
        price_id: str,
        period_end: datetime,
        quoted_at: datetime,
        client_ip: str = "127.0.0.1",
    ) -> dict[str, Any]:
        payload = {
            "organization_id": organization_id,
            "addon_slots": addon_slots,
            "provider": provider,
            "expected_amount_vnd": expected_amount_vnd,
            "price_id": price_id,
            "period_end": period_end.isoformat(),
            "quoted_at": quoted_at.isoformat(),
        }

        operation = "capacity.checkout"
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

        if not self._payment_enabled(provider):
            raise AdminError("PAYMENT_PROVIDER_NOT_AVAILABLE", 503)

        def execute() -> Any:
            self.lock("subscription:" + organization_id)
            subscription = self.db.scalar(
                select(SubscriptionModel)
                .where(SubscriptionModel.organization_ref == organization_id)
                .execution_options(populate_existing=True)
                .with_for_update()
            )
            if subscription is None:
                raise AdminError("SUBSCRIPTION_REQUIRED", 409)
            now = _utc(self.clock())
            quoted_instant = _utc(quoted_at)
            if quoted_instant > now or now - quoted_instant > timedelta(minutes=5):
                raise AdminError("CAPACITY_QUOTE_CHANGED", 409)
            capacity_quote(self.db, organization_id, addon_slots, now, self.settings)
            if (
                not _utc(subscription.period_start)
                <= quoted_instant
                < _utc(subscription.period_end)
            ):
                raise AdminError("CAPACITY_QUOTE_CHANGED", 409)
            quote = capacity_quote(
                self.db, organization_id, addon_slots, quoted_instant, self.settings
            )
            amount = quote["amount_vnd"]
            if (
                price_id != quote["price_id"]
                or _utc(period_end) != _utc(subscription.period_end)
                or expected_amount_vnd != amount
            ):
                raise AdminError("CAPACITY_QUOTE_CHANGED", 409)
            if provider == "MOMO" and not 1_000 <= amount <= 50_000_000:
                raise AdminError("MOMO_AMOUNT_OUT_OF_RANGE", 422)
            if provider == "VNPAY" and not 1 <= amount <= 999_999_999:
                raise AdminError("VNPAY_AMOUNT_OUT_OF_RANGE", 422)
            open_attempt = self.db.scalar(
                select(BillingPaymentAttemptModel)
                .join(
                    BillingInvoiceModel,
                    BillingPaymentAttemptModel.invoice_id == BillingInvoiceModel.invoice_id,
                )
                .where(
                    BillingInvoiceModel.owner_kind == "ORGANIZATION",
                    BillingInvoiceModel.owner_ref == organization_id,
                    BillingInvoiceModel.state == "PENDING",
                    capacity_invoice_filter(),
                    BillingPaymentAttemptModel.state.in_(("REQUESTING", "OPEN", "UNKNOWN")),
                )
                .limit(1)
            )
            if open_attempt:
                raise AdminError("PAYMENT_ATTEMPT_ALREADY_OPEN", 409)
            invoice_id = str(uuid4())
            invoice = BillingInvoiceModel(
                invoice_id=invoice_id,
                product_id=None,
                offer_id=quote["price_id"],
                owner_kind="ORGANIZATION",
                owner_ref=organization_id,
                units=addon_slots,
                amount_vnd=amount,
                state="PENDING",
                provider=provider,
                payment_mode="MANUAL",
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
            event = SubscriptionEventModel(
                event_id=str(uuid4()),
                subscription_id=subscription.subscription_id,
                invoice_id=invoice_id,
                kind="CAPACITY_QUOTED",
                payload={**quote, "actor": self.actor, "confirmed_at": now.isoformat()},
                actor_ref=self.actor,
                effective_at=now,
            )
            self.db.add_all([invoice, attempt, event])
            self.db.flush()
            # Persist intent before network I/O so a timeout can never create a second charge.
            response = {
                "invoice_id": invoice_id,
                "state": "PENDING",
                "attempt_state": "REQUESTING",
                "provider": provider,
                "amount_vnd": amount,
                "units": addon_slots,
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
                        amount_vnd=amount,
                        order_ref=order_ref,
                        request_id=cast(str, request_ref),
                    )
                else:
                    checkout = create_vnpay_checkout(
                        self.settings,
                        invoice_id=invoice_id,
                        amount_vnd=amount,
                        order_ref=order_ref,
                        order_info=cast(str, order_info),
                        client_ip=client_ip,
                        transaction_date=cast(str, transaction_date),
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
                attempt = self.db.scalar(  # type: ignore[assignment]
                    select(BillingPaymentAttemptModel)
                    .where(BillingPaymentAttemptModel.attempt_id == attempt.attempt_id)
                    .execution_options(populate_existing=True)
                    .with_for_update()
                )
                invoice = self.db.scalar(  # type: ignore[assignment]
                    select(BillingInvoiceModel)
                    .where(BillingInvoiceModel.invoice_id == invoice_id)
                    .execution_options(populate_existing=True)
                    .with_for_update()
                )
                receipt = self.db.get(BillingReceiptModel, pk)  # type: ignore[assignment]
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
            attempt = self.db.scalar(  # type: ignore[assignment]
                select(BillingPaymentAttemptModel)
                .where(BillingPaymentAttemptModel.attempt_id == attempt.attempt_id)
                .execution_options(populate_existing=True)
                .with_for_update()
            )
            invoice = self.db.scalar(  # type: ignore[assignment]
                select(BillingInvoiceModel)
                .where(BillingInvoiceModel.invoice_id == invoice_id)
                .execution_options(populate_existing=True)
                .with_for_update()
            )
            receipt = self.db.get(BillingReceiptModel, pk)  # type: ignore[assignment]
            if attempt is None or invoice is None or receipt is None:
                raise AdminError("PAYMENT_ATTEMPT_NOT_FOUND", 409)
            attempt.checkout_url = checkout["checkout_url"]
            attempt.expires_at = checkout["expires_at"]
            if invoice.state == "PENDING" and attempt.state in {"REQUESTING", "UNKNOWN"}:
                attempt.state = "OPEN"
                attempt.revision += 1
                attempt.updated_at = self.clock()
            response.update(
                {
                    "state": invoice.state,
                    "attempt_state": attempt.state,
                    "checkout_url": attempt.checkout_url if invoice.state == "PENDING" else None,
                    "expires_at": attempt.expires_at.isoformat() if attempt.expires_at else None,
                }
            )
            receipt.response_json = response
            self.db.commit()
            return response

        return cast(dict[str, Any], execute())

    def purchases(
        self, organization_id: str, limit: int = 50, invoice_id: str | None = None
    ) -> dict[str, Any]:
        query = select(BillingInvoiceModel).where(
            BillingInvoiceModel.owner_kind == "ORGANIZATION",
            BillingInvoiceModel.owner_ref == organization_id,
            capacity_invoice_filter(),
        )
        if invoice_id:
            query = query.where(BillingInvoiceModel.invoice_id == invoice_id)
        query = query.order_by(BillingInvoiceModel.created_at.desc()).limit(limit)
        items = []
        for invoice in self.db.scalars(query):
            item = self.invoice_view(invoice, include_owner=False)
            quoted_event = self.db.scalar(
                select(SubscriptionEventModel).where(
                    SubscriptionEventModel.invoice_id == invoice.invoice_id,
                    SubscriptionEventModel.kind == "CAPACITY_QUOTED",
                )
            )
            item["kind"] = quoted_event.payload.get("mode", "ADDON") if quoted_event else "ADDON"
            item["activated"] = bool(
                self.db.scalar(
                    select(SubscriptionEventModel.event_id).where(
                        SubscriptionEventModel.invoice_id == invoice.invoice_id,
                        SubscriptionEventModel.kind == "CAPACITY_PAYMENT_CONFIRMED",
                    )
                )
            )
            items.append(item)
        return {"items": items, "total": len(items)}

    def scoped_purchase(self, organization_id: str, invoice_id: str) -> BillingInvoiceModel:
        invoice = self.db.scalar(
            select(BillingInvoiceModel).where(
                BillingInvoiceModel.invoice_id == invoice_id,
                BillingInvoiceModel.owner_kind == "ORGANIZATION",
                BillingInvoiceModel.owner_ref == organization_id,
                BillingInvoiceModel.provider.in_(("MOMO", "VNPAY")),
                capacity_invoice_filter(),
            )
        )
        if invoice is None:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return invoice


def apply_capacity_payment(
    service: QuotaCommerceService, invoice: BillingInvoiceModel, quote: SubscriptionEventModel
) -> None:
    """Apply a verified payment once, or retain it for manual handling."""
    service.lock("subscription:" + invoice.owner_ref)
    subscription = service.db.scalar(
        select(SubscriptionModel)
        .where(
            SubscriptionModel.subscription_id == quote.subscription_id,
            SubscriptionModel.organization_ref == invoice.owner_ref,
        )
        .with_for_update()
    )
    now = _utc(service.clock())
    quoted_end = _utc(datetime.fromisoformat(quote.payload["period_end"]))
    applicable = (
        subscription is not None
        and _utc(subscription.period_end) == quoted_end
        and now < quoted_end
        and subscription.addon_slots + invoice.units <= 1000
    )
    if applicable and subscription is not None:
        subscription.addon_slots += invoice.units
        subscription.revision += 1
    service.db.add(
        SubscriptionEventModel(
            event_id=str(uuid4()),
            subscription_id=quote.subscription_id,
            invoice_id=invoice.invoice_id,
            kind="CAPACITY_PAYMENT_CONFIRMED" if applicable else "CAPACITY_PAYMENT_UNAPPLIED",
            payload={"invoice_id": invoice.invoice_id, "quantity": invoice.units},
            actor_ref="provider:" + invoice.provider.lower(),
            effective_at=now,
        )
    )
