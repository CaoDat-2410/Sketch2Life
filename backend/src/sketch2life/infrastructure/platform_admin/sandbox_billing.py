"""Billing-owned test workflows. No real payment callback or provider dispatch exists here."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import case, func, or_, select, text

from sketch2life.domain.billing_capacity import quota_month
from sketch2life.domain.platform_admin import AdminError, require_revision
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingOfferModel,
    BillingPaymentEventModel,
    BillingReceiptModel,
    VideoQuotaGrantModel,
    VideoQuotaUsageModel,
)
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)


class SandboxBillingService:
    def __init__(self, db, actor, settings, clock=lambda: datetime.now(UTC)):
        if settings.env not in {"local", "test"} or not settings.billing_sandbox_enabled:
            raise AdminError("BILLING_SANDBOX_DISABLED", 403)
        self.db, self.actor, self.clock = db, actor, clock

    def lock(self, scope):
        self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
            {"scope": "billing:" + scope},
        )

    def command(self, operation, key, payload, execute):
        self.lock(json.dumps((self.actor, operation, key)))
        pk = (self.actor, operation, key)
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        receipt = self.db.get(BillingReceiptModel, pk)
        if receipt:
            if receipt.fingerprint != fingerprint:
                raise AdminError("INVALID_IDEMPOTENCY_KEY", 400)
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

    def create_offer(self, payload, key):
        def execute():
            ref = str(uuid4())
            self.db.add(BillingOfferModel(offer_id=ref, created_by=self.actor, **payload))
            return {"offer_id": ref, **payload, "provider": "SANDBOX"}

        return self.command("offer.create", key, payload, execute)

    def offers(self, limit, cursor):
        scope = cursor_scope("sandbox-offers")
        query = select(BillingOfferModel)
        total = self.db.scalar(select(func.count()).select_from(BillingOfferModel)) or 0
        query = apply_datetime_cursor(
            query,
            created_at_column=BillingOfferModel.created_at,
            reference_column=BillingOfferModel.offer_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                query.order_by(BillingOfferModel.created_at.desc(), BillingOfferModel.offer_id)
                .limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.offer_id,
        )
        return {
            "provider": "SANDBOX",
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "offer_id": r.offer_id,
                    "owner_kind": r.owner_kind,
                    "units": r.units,
                    "amount_vnd": r.amount_vnd,
                }
                for r in rows[:limit]
            ],
        }

    def create_invoice(self, payload, key):
        def execute():
            offer = self.db.get(BillingOfferModel, payload["offer_id"])
            if offer is None or offer.owner_kind != payload["owner_kind"]:
                raise AdminError("OFFER_UNAVAILABLE", 422)
            row = BillingInvoiceModel(
                invoice_id=str(uuid4()),
                offer_id=offer.offer_id,
                owner_kind=payload["owner_kind"],
                owner_ref=payload["owner_ref"],
                units=offer.units,
                amount_vnd=offer.amount_vnd,
                state="PENDING",
                provider="SANDBOX",
                revision=1,
            )
            self.db.add(row)
            return self.invoice_view(row)

        return self.command("invoice.create", key, payload, execute)

    def invoice_view(self, row):
        return {
            "invoice_id": row.invoice_id,
            "owner_kind": row.owner_kind,
            "owner_ref": row.owner_ref,
            "offer_id": row.offer_id,
            "units": row.units,
            "amount_vnd": row.amount_vnd,
            "state": row.state,
            "provider": row.provider,
            "revision": row.revision,
        }

    def invoices(self, state, limit, cursor):
        query = select(BillingInvoiceModel)
        if state:
            query = query.where(BillingInvoiceModel.state == state)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("sandbox-invoices", state or "")
        query = apply_datetime_cursor(
            query,
            created_at_column=BillingInvoiceModel.created_at,
            reference_column=BillingInvoiceModel.invoice_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                query.order_by(
                    BillingInvoiceModel.created_at.desc(), BillingInvoiceModel.invoice_id
                ).limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.invoice_id,
        )
        return {
            "provider": "SANDBOX",
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [self.invoice_view(r) for r in rows[:limit]],
        }

    def settle(self, invoice_id, payload, expected, key):
        def execute():
            self.lock("payment-event:" + payload["event_id"])
            row = self.db.scalar(
                select(BillingInvoiceModel)
                .where(BillingInvoiceModel.invoice_id == invoice_id)
                .with_for_update()
            )
            if row is None:
                raise AdminError("NOT_FOUND", 404)
            outcome = "PAID" if payload["paid"] else "FAILED"
            prior = self.db.get(BillingPaymentEventModel, payload["event_id"])
            if prior:
                if (prior.invoice_id, prior.amount_vnd, prior.outcome) != (
                    invoice_id,
                    payload["amount_vnd"],
                    outcome,
                ):
                    raise AdminError("PAYMENT_EVENT_CONFLICT")
                return self.invoice_view(row)
            require_revision(row.revision, expected)
            if row.state != "PENDING" or row.provider != "SANDBOX":
                raise AdminError("INVALID_STATE_TRANSITION")
            if row.amount_vnd != payload["amount_vnd"]:
                raise AdminError("PAYMENT_AMOUNT_MISMATCH")
            self.db.add(
                BillingPaymentEventModel(
                    event_id=payload["event_id"],
                    invoice_id=invoice_id,
                    amount_vnd=payload["amount_vnd"],
                    outcome=outcome,
                    provider="SANDBOX",
                )
            )
            row.state, row.revision = outcome, row.revision + 1
            if payload["paid"] and self.db.get(BillingOfferModel, row.offer_id) is not None:
                self.db.add(
                    VideoQuotaGrantModel(
                        grant_id=str(uuid4()),
                        owner_kind=row.owner_kind,
                        owner_ref=row.owner_ref,
                        kind="TOP_UP",
                        units=row.units,
                        invoice_id=invoice_id,
                        period=None,
                        expires_at=None,
                    )
                )
            elif payload["paid"]:
                from sketch2life.infrastructure.platform_admin.sandbox_capacity import (
                    SandboxCapacityService,
                )

                SandboxCapacityService(self).apply_paid(row)
            return self.invoice_view(row)

        return self.command(
            "invoice.settle:" + invoice_id, key, {**payload, "expected_revision": expected}, execute
        )

    def included(self, payload, key):
        def execute():
            self.lock("scope:" + payload["owner_kind"] + ":" + payload["owner_ref"])
            now = self.clock()
            period, expiry = quota_month(now)
            prior = self.db.scalar(
                select(VideoQuotaGrantModel).where(
                    VideoQuotaGrantModel.owner_kind == payload["owner_kind"],
                    VideoQuotaGrantModel.owner_ref == payload["owner_ref"],
                    VideoQuotaGrantModel.period == period,
                )
            )
            if prior:
                if prior.units != payload["units"]:
                    raise AdminError("MONTHLY_GRANT_CONFLICT")
                return {"grant_id": prior.grant_id, "period": period, "units": prior.units}
            row = VideoQuotaGrantModel(
                grant_id=str(uuid4()),
                owner_kind=payload["owner_kind"],
                owner_ref=payload["owner_ref"],
                kind="INCLUDED",
                units=payload["units"],
                period=period,
                expires_at=expiry,
            )
            self.db.add(row)
            return {"grant_id": row.grant_id, "period": period, "units": row.units}

        return self.command("quota.included", key, payload, execute)

    def available_grants(self, kind, ref):
        return list(
            self.db.scalars(
                select(VideoQuotaGrantModel)
                .where(
                    VideoQuotaGrantModel.owner_kind == kind,
                    VideoQuotaGrantModel.owner_ref == ref,
                    or_(
                        VideoQuotaGrantModel.expires_at.is_(None),
                        VideoQuotaGrantModel.expires_at > self.clock(),
                    ),
                )
                .order_by(
                    case((VideoQuotaGrantModel.kind == "INCLUDED", 0), else_=1),
                    VideoQuotaGrantModel.created_at,
                    VideoQuotaGrantModel.grant_id,
                )
            )
        )

    def usage(self, grant_id):
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(VideoQuotaUsageModel)
                .where(VideoQuotaUsageModel.grant_id == grant_id)
            )
            or 0
        )

    def summary(self, kind, ref):
        grants = self.available_grants(kind, ref)
        return {
            "provider": "SANDBOX",
            "owner_kind": kind,
            "owner_ref": ref,
            "available_units": sum(max(0, g.units - self.usage(g.grant_id)) for g in grants),
            "grants": [
                {
                    "grant_id": g.grant_id,
                    "kind": g.kind,
                    "units": g.units,
                    "used": self.usage(g.grant_id),
                    "expires_at": g.expires_at.isoformat() if g.expires_at else None,
                }
                for g in grants
            ],
        }

    def consume(self, payload, key):
        """Exercise admission accounting in sandbox only; this never dispatches AI jobs."""

        def execute():
            self.lock("scope:" + payload["owner_kind"] + ":" + payload["owner_ref"])
            prior = self.db.scalar(
                select(VideoQuotaUsageModel).where(
                    VideoQuotaUsageModel.owner_kind == payload["owner_kind"],
                    VideoQuotaUsageModel.owner_ref == payload["owner_ref"],
                    VideoQuotaUsageModel.admission_ref == payload["admission_ref"],
                )
            )
            if prior:
                return {"usage_id": prior.usage_id, "grant_id": prior.grant_id, "units": 1}
            for grant in self.available_grants(payload["owner_kind"], payload["owner_ref"]):
                if self.usage(grant.grant_id) < grant.units:
                    row = VideoQuotaUsageModel(
                        usage_id=str(uuid4()),
                        grant_id=grant.grant_id,
                        owner_kind=payload["owner_kind"],
                        owner_ref=payload["owner_ref"],
                        admission_ref=payload["admission_ref"],
                    )
                    self.db.add(row)
                    return {"usage_id": row.usage_id, "grant_id": row.grant_id, "units": 1}
            raise AdminError("VIDEO_QUOTA_EXCEEDED")

        return self.command("quota.consume", key, payload, execute)
