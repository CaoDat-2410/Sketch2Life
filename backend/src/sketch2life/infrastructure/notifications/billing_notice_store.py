"""Read-only Billing scans and transactional billing-notice inbox composition (T-BILLN1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import String, and_, case, cast, exists, func, literal, or_, select, text, tuple_
from sqlalchemy.orm import Session

from sketch2life.application.ports.billing_notice import (
    BillingNoticeCandidate,
    BillingNoticeCandidatePage,
    BillingNoticeOutcome,
    BillingNoticeScanCursor,
)
from sketch2life.application.ports.notifications import (
    NotificationCommandV1,
    NotificationProducerPort,
)
from sketch2life.application.services.billing_notice import (
    BillingNoticeSweep,
    payment_notice_command,
    subscription_notice_command,
)
from sketch2life.domain.billing_notice import (
    GRACE_PERIOD,
    MAX_ORG_RECIPIENTS,
    NOTICE_LOOKBACK,
    RENEWAL_LEAD_1D,
    RENEWAL_LEAD_7D,
    BillingNoticeKind,
    BillingNoticeSource,
    billing_notice_trigger_id,
    normalize_utc,
    payment_notice_due,
    require_aware_utc,
    subscription_notice_due,
    subscription_notice_kind,
)
from sketch2life.infrastructure.notifications.inbox_repository import SqlNotificationProducer
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingPaymentEventModel,
    SubscriptionModel,
)


class SqlBillingNoticeStore:
    """SQL adapter for bounded read-only source scans and one-notice transactions."""

    def __init__(
        self,
        session: Session,
        *,
        producer: NotificationProducerPort | None = None,
    ) -> None:
        self._session = session
        self._producer_override = producer

    def scan_candidates(
        self,
        now: datetime,
        source: BillingNoticeSource,
        limit: int,
        cursor: BillingNoticeScanCursor | None,
    ) -> BillingNoticeCandidatePage:
        instant = require_aware_utc(now, field="now")
        if cursor is not None and cursor.source is not source:
            raise ValueError("billing notice cursor source does not match the scan")
        if source is BillingNoticeSource.SUBSCRIPTIONS:
            statement = self._subscription_scan(instant, limit, cursor)
        elif source is BillingNoticeSource.PAYMENTS:
            statement = self._payment_scan(instant, limit, cursor)
        else:  # pragma: no cover - StrEnum is exhaustively checked by the caller
            raise ValueError("unsupported billing notice source")
        try:
            rows = self._session.execute(statement).mappings().all()
        finally:
            self._session.rollback()  # a listing never holds a transaction or source lock

        has_more = len(rows) > limit
        selected = rows[:limit]
        failed_count = 0
        if source is BillingNoticeSource.SUBSCRIPTIONS:
            candidates_list: list[BillingNoticeCandidate] = []
            for row in selected:
                candidate = self._subscription_candidate(row, instant)
                if candidate is None:
                    failed_count += 1
                else:
                    candidates_list.append(candidate)
            candidates = tuple(candidates_list)
        else:
            candidates = tuple(self._payment_candidate(row) for row in selected)
        last_cursor = None
        if selected:
            last_row = selected[-1]
            last_cursor = BillingNoticeScanCursor(
                source=source,
                timestamp=normalize_utc(last_row["timestamp"], field="scan timestamp"),
                candidate_id=str(last_row["subject_id"]),
            )
        return BillingNoticeCandidatePage(
            candidates=candidates,
            has_more=has_more,
            failed_count=failed_count,
            last_cursor=last_cursor,
        )

    @staticmethod
    def _subscription_scan(
        instant: datetime,
        limit: int,
        cursor: BillingNoticeScanCursor | None,
    ) -> Any:
        period_end = SubscriptionModel.period_end
        renewal_window = and_(
            SubscriptionModel.state == "ACTIVE",
            period_end > instant,
            period_end <= instant + RENEWAL_LEAD_7D,
        )
        grace_window = and_(
            SubscriptionModel.state.in_(("ACTIVE", "GRACE")),
            period_end <= instant - GRACE_PERIOD,
            period_end > instant - GRACE_PERIOD - NOTICE_LOOKBACK,
        )
        state = SubscriptionModel.state
        notice_kind = case(
            (
                and_(
                    state == "ACTIVE",
                    period_end > instant + RENEWAL_LEAD_1D,
                    period_end <= instant + RENEWAL_LEAD_7D,
                ),
                BillingNoticeKind.RENEWAL_7D.value,
            ),
            (
                and_(
                    state == "ACTIVE",
                    period_end > instant,
                    period_end <= instant + RENEWAL_LEAD_1D,
                ),
                BillingNoticeKind.RENEWAL_1D.value,
            ),
            (grace_window, BillingNoticeKind.GRACE_EXPIRED.value),
            else_=None,
        )
        trigger_id = _billing_notice_trigger_expression(
            notice_kind,
            SubscriptionModel.subscription_id,
            period_end=period_end,
        )
        statement = select(
            SubscriptionModel.subscription_id.label("subject_id"),
            SubscriptionModel.organization_ref.label("owner_ref"),
            state.label("state"),
            SubscriptionModel.period_end.label("timestamp"),
        ).where(
            or_(renewal_window, grace_window),
            ~exists().where(INBOX_ITEMS.c.trigger_id == trigger_id),
        )
        if cursor is not None:
            statement = statement.where(
                tuple_(period_end, SubscriptionModel.subscription_id)
                > tuple_(literal(cursor.timestamp), literal(cursor.candidate_id))
            )
        return statement.order_by(period_end, SubscriptionModel.subscription_id).limit(limit + 1)

    @staticmethod
    def _payment_scan(
        instant: datetime,
        limit: int,
        cursor: BillingNoticeScanCursor | None,
    ) -> Any:
        event = BillingPaymentEventModel
        invoice = BillingInvoiceModel
        notice_kind = case(
            (event.outcome == "PAID", BillingNoticeKind.PAYMENT_SUCCEEDED.value),
            (event.outcome == "FAILED", BillingNoticeKind.PAYMENT_FAILED.value),
            else_=None,
        )
        trigger_id = _billing_notice_trigger_expression(notice_kind, event.event_id)
        statement = (
            select(
                event.event_id.label("subject_id"),
                event.invoice_id.label("invoice_id"),
                event.outcome.label("state"),
                event.created_at.label("timestamp"),
                invoice.owner_kind.label("owner_kind"),
                invoice.owner_ref.label("owner_ref"),
            )
            .join(invoice, invoice.invoice_id == event.invoice_id)
            .where(
                event.outcome.in_(("PAID", "FAILED")),
                invoice.state == event.outcome,
                event.created_at >= instant - NOTICE_LOOKBACK,
                ~exists().where(INBOX_ITEMS.c.trigger_id == trigger_id),
            )
        )
        if cursor is not None:
            statement = statement.where(
                tuple_(event.created_at, event.event_id)
                > tuple_(literal(cursor.timestamp), literal(cursor.candidate_id))
            )
        return statement.order_by(event.created_at, event.event_id).limit(limit + 1)

    @staticmethod
    def _subscription_candidate(
        row: Any, now: datetime
    ) -> BillingNoticeCandidate | None:
        period_end = normalize_utc(row["timestamp"], field="period_end")
        state = str(row["state"])
        kind = subscription_notice_kind(state, period_end, now)
        if kind is None:
            return None
        return BillingNoticeCandidate(
            source=BillingNoticeSource.SUBSCRIPTIONS,
            kind=kind,
            subject_id=str(row["subject_id"]),
            timestamp=period_end,
            owner_kind="ORGANIZATION",
            owner_ref=str(row["owner_ref"]),
            state=state,
        )

    @staticmethod
    def _payment_candidate(row: Any) -> BillingNoticeCandidate:
        state = str(row["state"])
        kind = (
            BillingNoticeKind.PAYMENT_SUCCEEDED
            if state == "PAID"
            else BillingNoticeKind.PAYMENT_FAILED
        )
        return BillingNoticeCandidate(
            source=BillingNoticeSource.PAYMENTS,
            kind=kind,
            subject_id=str(row["subject_id"]),
            timestamp=normalize_utc(row["timestamp"], field="created_at"),
            owner_kind=str(row["owner_kind"]),
            owner_ref=str(row["owner_ref"]),
            state=state,
            invoice_id=str(row["invoice_id"]),
        )

    def enqueue_if_due(
        self, candidate: BillingNoticeCandidate, now: datetime
    ) -> BillingNoticeOutcome:
        instant = require_aware_utc(now, field="now")
        trigger_id = _trigger_id(candidate)
        try:
            self._session.execute(
                text(
                    "SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"
                ),
                {"lock_key": f"notice:billing:{trigger_id}"},
            )
            present = self._session.scalar(
                select(exists().where(INBOX_ITEMS.c.trigger_id == trigger_id))
            )
            if present:
                self._session.commit()
                return BillingNoticeOutcome.ALREADY_PRESENT

            if not self._recheck(candidate, instant):
                self._session.rollback()
                return BillingNoticeOutcome.STALE

            recipients = self._recipients(candidate)
            if not recipients:
                self._session.rollback()
                return BillingNoticeOutcome.NO_RECIPIENT

            producer = self._producer_override or SqlNotificationProducer(
                self._session,
                clock=lambda: instant,
            )
            created = False
            for recipient_account_id in recipients:
                command = _command(candidate, recipient_account_id)
                created = producer.enqueue(command).created or created
            self._session.commit()
            return (
                BillingNoticeOutcome.CREATED
                if created
                else BillingNoticeOutcome.ALREADY_PRESENT
            )
        except BaseException:
            self._session.rollback()
            raise

    def _recheck(self, candidate: BillingNoticeCandidate, now: datetime) -> bool:
        if candidate.source is BillingNoticeSource.SUBSCRIPTIONS:
            row = self._session.execute(
                select(SubscriptionModel)
                .where(SubscriptionModel.subscription_id == candidate.subject_id)
                .with_for_update(read=True, skip_locked=True)
            ).scalar_one_or_none()
            if row is None:
                return False
            period_end = normalize_utc(row.period_end, field="period_end")
            return (
                candidate.owner_kind == "ORGANIZATION"
                and row.organization_ref == candidate.owner_ref
                and row.state == candidate.state
                and period_end == candidate.timestamp
                and subscription_notice_due(candidate.kind, row.state, period_end, now)
            )
        if candidate.source is not BillingNoticeSource.PAYMENTS:
            return False
        if candidate.invoice_id is None:
            return False
        event = BillingPaymentEventModel
        invoice = BillingInvoiceModel
        payment_row = (
            self._session.execute(
                select(
                    event.event_id.label("event_id"),
                    event.invoice_id.label("invoice_id"),
                    event.outcome.label("outcome"),
                    event.created_at.label("created_at"),
                    invoice.state.label("invoice_state"),
                    invoice.owner_kind.label("owner_kind"),
                    invoice.owner_ref.label("owner_ref"),
                )
                .join(invoice, invoice.invoice_id == event.invoice_id)
                .where(event.event_id == candidate.subject_id)
                .with_for_update(read=True, skip_locked=True, of=BillingInvoiceModel)
            )
            .mappings()
            .one_or_none()
        )
        if payment_row is None:
            return False
        created_at = normalize_utc(payment_row["created_at"], field="created_at")
        outcome = str(payment_row["outcome"])
        return (
            str(payment_row["event_id"]) == candidate.subject_id
            and str(payment_row["invoice_id"]) == candidate.invoice_id
            and str(payment_row["owner_kind"]) == candidate.owner_kind
            and str(payment_row["owner_ref"]) == candidate.owner_ref
            and outcome == candidate.state
            and created_at == candidate.timestamp
            and payment_notice_due(
                candidate.kind,
                outcome,
                str(payment_row["invoice_state"]),
                created_at,
                now,
            )
        )

    def _recipients(self, candidate: BillingNoticeCandidate) -> tuple[str, ...]:
        if candidate.owner_kind == "ORGANIZATION":
            if candidate.source is BillingNoticeSource.SUBSCRIPTIONS or (
                candidate.source is BillingNoticeSource.PAYMENTS
                and candidate.kind
                in {
                    BillingNoticeKind.PAYMENT_SUCCEEDED,
                    BillingNoticeKind.PAYMENT_FAILED,
                }
            ):
                rows = self._session.scalars(
                    select(AdultIdentityModel.account_id)
                    .join(
                        OrganizationAssignmentModel,
                        OrganizationAssignmentModel.subject == AdultIdentityModel.subject,
                    )
                    .join(
                        OrganizationModel,
                        OrganizationModel.organization_id
                        == OrganizationAssignmentModel.organization_id,
                    )
                    .where(
                        OrganizationModel.organization_id == candidate.owner_ref,
                        OrganizationModel.state == "active",
                        AdultIdentityModel.state == "active",
                        AdultIdentityModel.account_role == "school_manager",
                        OrganizationAssignmentModel.role == "school_admin",
                        OrganizationAssignmentModel.class_id.is_(None),
                        OrganizationAssignmentModel.active.is_(True),
                    )
                    .distinct()
                    .order_by(AdultIdentityModel.account_id)
                    .limit(MAX_ORG_RECIPIENTS)
                ).all()
                return tuple(str(row) for row in rows)
            return ()
        if (
            candidate.owner_kind == "PARENT_ACCOUNT"
            and candidate.source is BillingNoticeSource.PAYMENTS
            and candidate.kind
            in {BillingNoticeKind.PAYMENT_SUCCEEDED, BillingNoticeKind.PAYMENT_FAILED}
        ):
            row = self._session.scalar(
                select(AdultIdentityModel.account_id).where(
                    AdultIdentityModel.account_id == candidate.owner_ref,
                    AdultIdentityModel.state == "active",
                    AdultIdentityModel.account_role == "parent",
                )
            )
            return () if row is None else (str(row),)
        return ()


def _trigger_id(candidate: BillingNoticeCandidate) -> str:
    if candidate.source is BillingNoticeSource.SUBSCRIPTIONS:
        return billing_notice_trigger_id(
            candidate.kind,
            candidate.subject_id,
            period_end=candidate.timestamp,
        )
    return billing_notice_trigger_id(candidate.kind, candidate.subject_id)


def _billing_notice_trigger_expression(
    kind: Any,
    subject_id: Any,
    *,
    period_end: Any | None = None,
) -> Any:
    identity_parts: list[Any] = [kind, subject_id]
    if period_end is not None:
        identity_parts.append(
            func.to_char(
                func.timezone("UTC", period_end),
                'YYYY-MM-DD"T"HH24:MI:SS.US"Z"',
            )
        )
    canonical_json = cast(func.json_build_array(*identity_parts), String)
    compact_json = func.regexp_replace(canonical_json, ", ", ",", "g")
    digest = func.encode(func.sha256(func.convert_to(compact_json, "UTF8")), "hex")
    return literal("billing-notice.") + digest


def _command(
    candidate: BillingNoticeCandidate, recipient_account_id: str
) -> NotificationCommandV1:
    if candidate.source is BillingNoticeSource.SUBSCRIPTIONS:
        return subscription_notice_command(
            recipient_account_id=recipient_account_id,
            organization_ref=candidate.owner_ref,
            kind=candidate.kind,
            subscription_id=candidate.subject_id,
            period_end=candidate.timestamp,
        )
    if candidate.invoice_id is None:
        raise ValueError("payment candidate requires invoice_id")
    return payment_notice_command(
        recipient_account_id=recipient_account_id,
        owner_kind=candidate.owner_kind,
        owner_ref=candidate.owner_ref,
        kind=candidate.kind,
        invoice_id=candidate.invoice_id,
        payment_event_id=candidate.subject_id,
    )


def build_billing_notice_sweep(
    session: Session,
    *,
    producer: NotificationProducerPort | None = None,
) -> BillingNoticeSweep:
    """Build the internal sweep only; no route or production scheduler composes it by default."""

    store = SqlBillingNoticeStore(session, producer=producer)
    return BillingNoticeSweep(store, store)


__all__ = ["SqlBillingNoticeStore", "build_billing_notice_sweep"]
