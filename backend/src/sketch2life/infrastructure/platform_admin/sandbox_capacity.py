"""Billing-owned capacity quotes and test subscription reconciliation."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select

from sketch2life.domain.billing_capacity import effective_state, period_end, prorated_vnd
from sketch2life.domain.platform_admin import AdminError, require_revision
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    CapacityPriceModel,
    SubscriptionEventModel,
    SubscriptionModel,
)
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_reference_cursor,
    cursor_scope,
    next_reference_cursor,
)


class SandboxCapacityService:
    def __init__(self, billing):
        self.billing, self.db = billing, billing.db

    def event(self, ref, kind, payload, effective, invoice_id=None, group=None, class_ref=None):
        self.db.add(
            SubscriptionEventModel(
                event_id=str(uuid4()),
                subscription_id=ref,
                kind=kind,
                payload=payload,
                effective_at=effective,
                actor_ref=self.billing.actor,
                invoice_id=invoice_id,
                group_ref=group,
                class_ref=class_ref,
            )
        )

    def price(self, payload, key):
        def execute():
            ref = str(uuid4())
            self.db.add(CapacityPriceModel(price_id=ref, **payload, created_by=self.billing.actor))
            return {"price_id": ref, **payload, "provider": "SANDBOX"}

        return self.billing.command("capacity.price", key, payload, execute)

    def prices(self, limit, cursor):
        query = select(CapacityPriceModel)
        total = self.db.scalar(select(func.count()).select_from(CapacityPriceModel)) or 0
        scope = cursor_scope("capacity-prices")
        query = apply_datetime_cursor(
            query,
            created_at_column=CapacityPriceModel.created_at,
            reference_column=CapacityPriceModel.price_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                query.order_by(CapacityPriceModel.created_at.desc(), CapacityPriceModel.price_id)
                .limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.price_id,
        )
        return {
            "provider": "SANDBOX",
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "price_id": row.price_id,
                    "cycle_months": row.cycle_months,
                    "base_amount_vnd": row.base_amount_vnd,
                    "slot_amount_vnd": row.slot_amount_vnd,
                }
                for row in rows[:limit]
            ],
        }

    def load(self, ref, lock=False):
        query = select(SubscriptionModel).where(SubscriptionModel.subscription_id == ref)
        if lock:
            query = query.with_for_update()
        row = self.db.scalar(query)
        if row is None:
            raise AdminError("NOT_FOUND", 404)
        return row

    def plan(self, row):
        return self.db.scalar(
            select(SubscriptionEventModel)
            .where(
                SubscriptionEventModel.subscription_id == row.subscription_id,
                SubscriptionEventModel.kind == "CAPACITY_DOWNGRADE_SCHEDULED",
                SubscriptionEventModel.effective_at == row.period_end,
            )
            .order_by(
                SubscriptionEventModel.created_at.desc(), SubscriptionEventModel.event_id.desc()
            )
            .limit(1)
        )

    def view(self, row):
        now = self.billing.clock()
        plan = self.plan(row)
        due = plan is not None and now >= plan.effective_at
        slots = plan.payload["addon_slots"] if due else row.addon_slots
        return {
            "subscription_id": row.subscription_id,
            "organization_ref": row.organization_ref,
            "price_id": row.price_id,
            "addon_slots": slots,
            "capacity": 10 + slots,
            "state": effective_state(row.state, row.period_end, now),
            "revision": row.revision,
            "period_start": row.period_start.isoformat(),
            "period_end": row.period_end.isoformat(),
            "scheduled_addon_slots": plan.payload["addon_slots"] if plan and not due else None,
            "suspended_class_refs": list(
                self.db.scalars(
                    select(SubscriptionEventModel.class_ref).where(
                        SubscriptionEventModel.group_ref == plan.group_ref,
                        SubscriptionEventModel.class_ref.is_not(None),
                    )
                )
            )
            if due
            else [],
            "provider": "SANDBOX",
        }

    def list(self, limit, cursor):
        scope = cursor_scope("sandbox-subscriptions")
        query = apply_reference_cursor(
            select(SubscriptionModel),
            reference_column=SubscriptionModel.subscription_id,
            scope=scope,
            cursor=cursor,
        )
        rows = list(self.db.scalars(query.order_by(SubscriptionModel.subscription_id).limit(limit + 1)))
        next_cursor = next_reference_cursor(
            rows, limit, scope=scope, reference=lambda row: row.subscription_id
        )
        return {
            "items": [self.view(r) for r in rows[:limit]],
            "provider": "SANDBOX",
            "limit": limit,
            "next_cursor": next_cursor,
        }

    def quote(self, payload, key, ref=None, expected=None):
        def execute():
            now = self.billing.clock()
            mode = payload["mode"]
            if mode == "START":
                if ref:
                    raise AdminError("INVALID_CAPACITY_QUOTE", 422)
                self.billing.lock("subscription:" + payload["organization_ref"])
                if self.db.scalar(
                    select(SubscriptionModel.subscription_id).where(
                        SubscriptionModel.organization_ref == payload["organization_ref"]
                    )
                ):
                    raise AdminError("SUBSCRIPTION_ALREADY_EXISTS")
                price = self.db.get(CapacityPriceModel, payload["price_id"])
                if price is None:
                    raise AdminError("PRICE_UNAVAILABLE", 422)
                subscription_id = str(uuid4())
                start, end, slots = now, period_end(now, price.cycle_months), payload["addon_slots"]
                amount = price.base_amount_vnd + slots * price.slot_amount_vnd
                org, revision = payload["organization_ref"], 0
            else:
                if not ref:
                    raise AdminError("SUBSCRIPTION_REQUIRED", 422)
                row = self.load(ref, lock=True)
                require_revision(row.revision, expected)
                price = self.db.get(CapacityPriceModel, row.price_id)
                subscription_id, org, revision = ref, row.organization_ref, row.revision
                if mode == "ADDON":
                    slots = payload["addon_slots"]
                    if slots <= row.addon_slots:
                        raise AdminError("CAPACITY_INCREASE_REQUIRED", 422)
                    start, end = row.period_start, row.period_end
                    amount = prorated_vnd(
                        slots - row.addon_slots, price.slot_amount_vnd, start, end, now
                    )
                else:
                    if now < row.period_end:
                        raise AdminError("RENEWAL_NOT_DUE")
                    plan = self.plan(row)
                    slots = plan.payload["addon_slots"] if plan else row.addon_slots
                    start, end = row.period_end, period_end(row.period_end, price.cycle_months)
                    amount = price.base_amount_vnd + slots * price.slot_amount_vnd
            if not 1 <= amount <= 2000000000:
                raise AdminError("QUOTE_AMOUNT_UNAVAILABLE", 422)
            invoice_id = str(uuid4())
            self.db.add(
                BillingInvoiceModel(
                    invoice_id=invoice_id,
                    offer_id=price.price_id,
                    owner_kind="ORGANIZATION",
                    owner_ref=org,
                    units=slots,
                    amount_vnd=amount,
                    provider="SANDBOX",
                    state="PENDING",
                    revision=1,
                )
            )
            snapshot = {
                "mode": mode,
                "organization_ref": org,
                "price_id": price.price_id,
                "addon_slots": slots,
                "period_start": start.isoformat(),
                "period_end": end.isoformat(),
                "subscription_revision": revision,
                "quoted_at": now.isoformat(),
                "amount_vnd": amount,
            }
            self.event(subscription_id, "CAPACITY_QUOTED", snapshot, now, invoice_id)
            return {
                "invoice_id": invoice_id,
                "subscription_id": subscription_id,
                "amount_vnd": amount,
                "revision": 1,
                "state": "PENDING",
                "provider": "SANDBOX",
                "quote": snapshot,
            }

        return self.billing.command(
            "capacity.quote:" + (ref or "new"), key, {**payload, "revision": expected}, execute
        )

    def apply_paid(self, invoice):
        quote = self.db.scalar(
            select(SubscriptionEventModel).where(
                SubscriptionEventModel.invoice_id == invoice.invoice_id,
                SubscriptionEventModel.kind == "CAPACITY_QUOTED",
            )
        )
        if quote is None:
            raise AdminError("CAPACITY_QUOTE_NOT_FOUND")
        payload = quote.payload
        self.billing.lock("subscription:" + payload["organization_ref"])
        if payload["mode"] == "START":
            if self.db.scalar(
                select(SubscriptionModel.subscription_id).where(
                    SubscriptionModel.organization_ref == payload["organization_ref"]
                )
            ):
                raise AdminError("SUBSCRIPTION_ALREADY_EXISTS")
            row = SubscriptionModel(
                subscription_id=quote.subscription_id,
                organization_ref=payload["organization_ref"],
                revision=0,
            )
            self.db.add(row)
        else:
            row = self.load(quote.subscription_id, lock=True)
            require_revision(row.revision, payload["subscription_revision"])
        if self.billing.clock() >= datetime.fromisoformat(payload["period_end"]):
            raise AdminError("CAPACITY_QUOTE_EXPIRED")
        row.price_id, row.addon_slots = payload["price_id"], payload["addon_slots"]
        row.period_start, row.period_end = (
            datetime.fromisoformat(payload["period_start"]),
            datetime.fromisoformat(payload["period_end"]),
        )
        row.state, row.revision = (
            (row.state if payload["mode"] == "ADDON" else "ACTIVE"),
            row.revision + 1,
        )
        self.event(
            row.subscription_id,
            "CAPACITY_PAYMENT_CONFIRMED",
            {"capacity": 10 + row.addon_slots},
            self.billing.clock(),
            invoice.invoice_id,
        )

    def configure(self, ref, payload, expected, key, active_class_refs):
        def execute():
            row = self.load(ref, lock=True)
            require_revision(row.revision, expected)
            now = self.billing.clock()
            if now >= row.period_end:
                raise AdminError("SUBSCRIPTION_PERIOD_ENDED")
            if payload["action"] in {"cancel_renewal", "resume_renewal"}:
                row.state = (
                    "CANCEL_AT_PERIOD_END" if payload["action"] == "cancel_renewal" else "ACTIVE"
                )
                self.event(ref, "SUBSCRIPTION_" + payload["action"].upper(), {}, now)
            else:
                slots = payload["addon_slots"]
                selected = payload["suspend_class_refs"]
                if slots is None or slots >= row.addon_slots or len(selected) != len(set(selected)):
                    raise AdminError("INVALID_CAPACITY_DOWNGRADE", 422)
                if not set(selected).issubset(active_class_refs) or len(selected) != max(
                    0, len(active_class_refs) - (10 + slots)
                ):
                    raise AdminError("CLASS_SELECTION_REQUIRED", 422)
                group = str(uuid4())
                self.event(
                    ref,
                    "CAPACITY_DOWNGRADE_SCHEDULED",
                    {"addon_slots": slots, "capacity": 10 + slots},
                    row.period_end,
                    group=group,
                )
                for class_ref in selected:
                    self.event(
                        ref,
                        "CLASS_SUSPENSION_SCHEDULED",
                        {"capacity": 10 + slots},
                        row.period_end,
                        group=group,
                        class_ref=class_ref,
                    )
            row.revision += 1
            self.db.flush()
            return self.view(row)

        return self.billing.command(
            "subscription.configure:" + ref, key, {**payload, "revision": expected}, execute
        )
