"""PostgreSQL acceptance cases for T-BILLN1; authored here and intentionally not run."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, delete, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.billing_notice import BillingNoticeSweepResult
from sketch2life.application.services.notification_templates import eligible_template_keys
from sketch2life.application.services.push_delivery import PushDeliveryReport, PushDeliveryWorker
from sketch2life.domain.billing_notice import (
    BILLING_GRACE_EXPIRED,
    BILLING_ORG_PAYMENT_FAILED,
    BILLING_ORG_PAYMENT_SUCCEEDED,
    BILLING_PARENT_PAYMENT_SUCCEEDED,
    BILLING_RENEWAL_DUE_1D,
    BILLING_RENEWAL_DUE_7D,
    BillingNoticeKind,
    BillingNoticeSource,
    billing_notice_trigger_id,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.notifications.billing_notice_store import (
    build_billing_notice_sweep,
)
from sketch2life.infrastructure.notifications.notification_worker import run_billing_notice_pages
from sketch2life.infrastructure.notifications.push_delivery_fakes import LocalFakePushSender
from sketch2life.infrastructure.notifications.push_delivery_repository import SqlPushDeliveryStore
from sketch2life.infrastructure.notifications.tables import (
    INBOX_ITEMS,
    PUSH_DELIVERIES,
    PUSH_ENDPOINTS,
)
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

BACKEND = Path(__file__).resolve().parents[2]
FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}
NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
PREFIX = "b1-e4-"
ORG_ID = PREFIX + "org-main"
EMPTY_ORG_ID = PREFIX + "org-empty"
ACTIVE_ADMIN_SUBJECT = PREFIX + "subject-admin-active"
INACTIVE_ADMIN_SUBJECT = PREFIX + "subject-admin-inactive"
TEACHER_SUBJECT = PREFIX + "subject-teacher"
PARENT_SUBJECT = PREFIX + "subject-parent"
ACTIVE_ADMIN_ACCOUNT = PREFIX + "account-admin-active"
INACTIVE_ADMIN_ACCOUNT = PREFIX + "account-admin-inactive"
TEACHER_ACCOUNT = PREFIX + "account-teacher"
PARENT_ACCOUNT = PREFIX + "account-parent"
SUBSCRIPTION_ID = PREFIX + "subscription-main"
INVOICE_ORG_PAID = PREFIX + "invoice-org-paid"
INVOICE_ORG_FAILED = PREFIX + "invoice-org-failed"
INVOICE_ORG_CANCELED = PREFIX + "invoice-org-canceled"
INVOICE_PARENT_PAID = PREFIX + "invoice-parent-paid"
INVOICE_EMPTY_ORG = PREFIX + "invoice-empty-org"
EVENT_ORG_PAID = PREFIX + "event-org-paid"
EVENT_ORG_FAILED = PREFIX + "event-org-failed"
EVENT_ORG_CANCELED = PREFIX + "event-org-canceled"
EVENT_PARENT_PAID = PREFIX + "event-parent-paid"
EVENT_EMPTY_ORG = PREFIX + "event-empty-org"
ACTIVE_ENDPOINT = PREFIX + "endpoint-admin"
PARENT_ENDPOINT = PREFIX + "endpoint-parent"
FORBIDDEN_DATABASES = {"sketch2life", "sketch2life_m2_s1a"}


@dataclass(frozen=True, slots=True)
class Postgres:
    engine: Engine
    factory: sessionmaker[Session]


def _open_postgres(monkeypatch: pytest.MonkeyPatch) -> Postgres:
    url = os.environ.get("BILLN1_NOTICE_DATABASE_URL")
    if not url:
        pytest.skip(
            "set BILLN1_NOTICE_DATABASE_URL to an isolated disposable PostgreSQL database"
        )
    parsed = make_url(url)
    database = parsed.database or ""
    if "billn1_notices" not in database or "be1_acceptance" not in database:
        pytest.fail(
            "BILLN1_NOTICE_DATABASE_URL must name an isolated billn1_notices "
            "be1_acceptance database"
        )
    if parsed.port in FORBIDDEN_PORTS or database in FORBIDDEN_DATABASES:
        pytest.fail("BILLN1_NOTICE_DATABASE_URL points at a forbidden database or port")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    monkeypatch.setenv("S1A_P_ALEMBIC_DATABASE_URL", url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
    return Postgres(engine, sessionmaker(engine, expire_on_commit=False))


def _cleanup_fixture(postgres: Postgres) -> None:
    accounts = (ACTIVE_ADMIN_ACCOUNT, INACTIVE_ADMIN_ACCOUNT, TEACHER_ACCOUNT, PARENT_ACCOUNT)
    with postgres.factory.begin() as session:
        # Push endpoints and deliveries are immutable by trigger; the disposable test database
        # is cleaned with triggers off for this one transaction.
        session.execute(text("set local session_replication_role = replica"))
        session.execute(
            delete(PUSH_DELIVERIES).where(PUSH_DELIVERIES.c.recipient_account_id.in_(accounts))
        )
        session.execute(delete(INBOX_ITEMS).where(INBOX_ITEMS.c.recipient_account_id.in_(accounts)))
        session.execute(
            delete(PUSH_ENDPOINTS).where(PUSH_ENDPOINTS.c.recipient_account_id.in_(accounts))
        )
        session.execute(
            delete(BillingPaymentEventModel).where(
                BillingPaymentEventModel.event_id.like(f"{PREFIX}%")
            )
        )
        session.execute(
            delete(BillingInvoiceModel).where(BillingInvoiceModel.invoice_id.like(f"{PREFIX}%"))
        )
        session.execute(
            delete(SubscriptionModel).where(SubscriptionModel.subscription_id.like(f"{PREFIX}%"))
        )
        session.execute(
            delete(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.assignment_id.like(f"{PREFIX}%")
            )
        )
        session.execute(
            delete(AdultIdentityModel).where(AdultIdentityModel.subject.like(f"{PREFIX}%"))
        )
        session.execute(
            delete(OrganizationModel).where(OrganizationModel.organization_id.like(f"{PREFIX}%"))
        )


@pytest.fixture
def postgres(monkeypatch: pytest.MonkeyPatch) -> Iterator[Postgres]:
    database = _open_postgres(monkeypatch)
    _cleanup_fixture(database)
    try:
        yield database
    finally:
        _cleanup_fixture(database)
        database.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _identity(
    subject: str,
    account_id: str,
    role: str,
    *,
    state: str = "active",
) -> AdultIdentityModel:
    return AdultIdentityModel(
        subject=subject,
        account_id=account_id,
        issuer="synthetic-billn1",
        state=state,
        account_role=role,
        email_verification_required=False,
        role_revision=1,
        created_at=NOW,
    )


def _subscription(
    subscription_id: str, period_end: datetime, organization_ref: str = ORG_ID
) -> SubscriptionModel:
    return SubscriptionModel(
        subscription_id=subscription_id,
        organization_ref=organization_ref,
        price_id=PREFIX + "price",
        addon_slots=0,
        state="ACTIVE",
        period_start=period_end - timedelta(days=30),
        period_end=period_end,
        revision=1,
    )


def _invoice(
    invoice_id: str,
    owner_kind: str,
    owner_ref: str,
    state: str,
) -> BillingInvoiceModel:
    return BillingInvoiceModel(
        invoice_id=invoice_id,
        offer_id=PREFIX + "offer",
        product_id=None,
        owner_kind=owner_kind,
        owner_ref=owner_ref,
        units=1,
        amount_vnd=100,
        state=state,
        provider="SANDBOX",
        payment_mode="MANUAL",
        revision=1,
        created_at=NOW,
    )


def _payment_event(event_id: str, invoice_id: str, outcome: str) -> BillingPaymentEventModel:
    return BillingPaymentEventModel(
        event_id=event_id,
        invoice_id=invoice_id,
        amount_vnd=100,
        outcome=outcome,
        provider="SANDBOX",
        provider_transaction_ref=None,
        payload_digest=None,
        created_at=NOW,
    )


def _endpoint(endpoint_id: str, recipient: str) -> dict[str, object]:
    return {
        "push_endpoint_id": endpoint_id,
        "recipient_account_id": recipient,
        "platform_kind": "WEB",
        "provider_kind": "WEB_PUSH",
        "endpoint_ciphertext": b"synthetic-billn1-endpoint",
        "endpoint_fingerprint": hashlib.sha256(endpoint_id.encode()).hexdigest(),
        "state": "ACTIVE",
        "version": 1,
        "registered_at": NOW,
        "last_seen_at": NOW,
        "revoked_at": None,
        "app_version": "synthetic",
    }


def _add_ordered(session: Session, rows: list[Any]) -> None:
    """Insert organizations first: the ORM models carry no foreign-key ordering metadata."""
    session.add_all([row for row in rows if isinstance(row, OrganizationModel)])
    session.flush()
    session.add_all([row for row in rows if not isinstance(row, OrganizationModel)])


def _seed(postgres: Postgres) -> None:
    with postgres.factory.begin() as session:
        _add_ordered(session,
            [
                OrganizationModel(
                    organization_id=ORG_ID,
                    display_name="Synthetic Organization",
                    state="active",
                    revision=1,
                    created_at=NOW,
                ),
                OrganizationModel(
                    organization_id=EMPTY_ORG_ID,
                    display_name="Synthetic Organization Without Billing Admin",
                    state="active",
                    revision=1,
                    created_at=NOW,
                ),
                _identity(ACTIVE_ADMIN_SUBJECT, ACTIVE_ADMIN_ACCOUNT, "school_manager"),
                _identity(
                    INACTIVE_ADMIN_SUBJECT,
                    INACTIVE_ADMIN_ACCOUNT,
                    "school_manager",
                    state="inactive",
                ),
                _identity(TEACHER_SUBJECT, TEACHER_ACCOUNT, "teacher"),
                _identity(PARENT_SUBJECT, PARENT_ACCOUNT, "parent"),
                OrganizationAssignmentModel(
                    assignment_id=PREFIX + "assignment-admin-active",
                    organization_id=ORG_ID,
                    subject=ACTIVE_ADMIN_SUBJECT,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
                OrganizationAssignmentModel(
                    assignment_id=PREFIX + "assignment-admin-inactive",
                    organization_id=ORG_ID,
                    subject=INACTIVE_ADMIN_SUBJECT,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
                OrganizationAssignmentModel(
                    assignment_id=PREFIX + "assignment-teacher",
                    organization_id=ORG_ID,
                    subject=TEACHER_SUBJECT,
                    class_id=PREFIX + "class",
                    role="teacher",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
                _subscription(SUBSCRIPTION_ID, NOW + timedelta(days=7)),
                _invoice(INVOICE_ORG_PAID, "ORGANIZATION", ORG_ID, "PAID"),
                _invoice(INVOICE_ORG_FAILED, "ORGANIZATION", ORG_ID, "FAILED"),
                _invoice(INVOICE_ORG_CANCELED, "ORGANIZATION", ORG_ID, "CANCELED"),
                _invoice(INVOICE_PARENT_PAID, "PARENT_ACCOUNT", PARENT_ACCOUNT, "PAID"),
                _invoice(INVOICE_EMPTY_ORG, "ORGANIZATION", EMPTY_ORG_ID, "PAID"),
                _payment_event(EVENT_ORG_PAID, INVOICE_ORG_PAID, "PAID"),
                _payment_event(EVENT_ORG_FAILED, INVOICE_ORG_FAILED, "FAILED"),
                _payment_event(EVENT_ORG_CANCELED, INVOICE_ORG_CANCELED, "FAILED"),
                _payment_event(EVENT_PARENT_PAID, INVOICE_PARENT_PAID, "PAID"),
                _payment_event(EVENT_EMPTY_ORG, INVOICE_EMPTY_ORG, "PAID"),
            ]
        )
        session.execute(
            PUSH_ENDPOINTS.insert().values(
                [
                    _endpoint(ACTIVE_ENDPOINT, ACTIVE_ADMIN_ACCOUNT),
                    _endpoint(PARENT_ENDPOINT, PARENT_ACCOUNT),
                ]
            )
        )


def _seed_notice_admin(postgres: Postgres) -> None:
    with postgres.factory.begin() as session:
        _add_ordered(session,
            [
                OrganizationModel(
                    organization_id=ORG_ID,
                    display_name="Synthetic Organization",
                    state="active",
                    revision=1,
                    created_at=NOW,
                ),
                _identity(ACTIVE_ADMIN_SUBJECT, ACTIVE_ADMIN_ACCOUNT, "school_manager"),
                OrganizationAssignmentModel(
                    assignment_id=PREFIX + "assignment-admin-active",
                    organization_id=ORG_ID,
                    subject=ACTIVE_ADMIN_SUBJECT,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
            ]
        )


def _billing_rows_bytes(postgres: Postgres) -> bytes:
    records: list[tuple[str, tuple[tuple[object, ...], ...]]] = []
    for model, key_column in (
        (SubscriptionModel, SubscriptionModel.subscription_id),
        (BillingInvoiceModel, BillingInvoiceModel.invoice_id),
        (BillingPaymentEventModel, BillingPaymentEventModel.event_id),
    ):
        with postgres.factory() as session:
            rows = session.scalars(
                select(model)
                .where(key_column.like(f"{PREFIX}%"))
                .order_by(key_column)
            ).all()
            values = tuple(
                tuple(getattr(row, column.name) for column in model.__table__.columns)
                for row in rows
            )
        records.append((model.__tablename__, values))
    return repr(tuple(records)).encode("utf-8")


def _assert_read_only(postgres: Postgres, operation):
    before = _billing_rows_bytes(postgres)
    result = operation()
    assert _billing_rows_bytes(postgres) == before
    return result


def _run_once(
    postgres: Postgres,
    source: BillingNoticeSource,
    *,
    now: datetime = NOW,
):
    with postgres.factory() as session:
        return build_billing_notice_sweep(session).run_once(
            now=now,
            limit=500,
            source=source,
        )


def _inbox_rows(postgres: Postgres, recipient: str) -> list[dict[str, object]]:
    with postgres.factory() as session:
        rows = (
            session.execute(
                select(
                    INBOX_ITEMS.c.inbox_item_id,
                    INBOX_ITEMS.c.notification_type,
                    INBOX_ITEMS.c.recipient_role,
                    INBOX_ITEMS.c.organization_ref,
                    INBOX_ITEMS.c.trigger_id,
                    INBOX_ITEMS.c.safe_parameters,
                ).where(INBOX_ITEMS.c.recipient_account_id == recipient)
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]


def test_subscription_notice_schedule_identity_and_idempotency(postgres: Postgres) -> None:
    _seed(postgres)

    first = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    second = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert first.created == 1
    assert second.scanned == second.already_present == 0
    assert first.failed == second.failed == 0

    moved_period_end = NOW + timedelta(days=8)
    with postgres.factory.begin() as session:
        session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.subscription_id == SUBSCRIPTION_ID)
            .values(
                period_start=moved_period_end - timedelta(days=30),
                period_end=moved_period_end,
                revision=2,
            )
        )
    moved = _assert_read_only(
        postgres,
        lambda: _run_once(
            postgres,
            BillingNoticeSource.SUBSCRIPTIONS,
            now=NOW + timedelta(days=1),
        ),
    )
    assert moved.created == 1
    moved_rows = [
        row
        for row in _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)
        if row["safe_parameters"].get("subscription_ref") == SUBSCRIPTION_ID
    ]
    assert sum(row["notification_type"] == BILLING_RENEWAL_DUE_7D for row in moved_rows) == 2

    one_day_end = NOW + timedelta(days=1)
    with postgres.factory.begin() as session:
        session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.subscription_id == SUBSCRIPTION_ID)
            .values(
                period_start=one_day_end - timedelta(days=30),
                period_end=one_day_end,
                revision=3,
            )
        )
    one_day_first = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    one_day_second = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert one_day_first.created == 1
    assert one_day_second.scanned == one_day_second.already_present == 0

    grace_period_end = NOW - timedelta(days=7)
    with postgres.factory.begin() as session:
        session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.subscription_id == SUBSCRIPTION_ID)
            .values(
                period_start=grace_period_end - timedelta(days=30),
                period_end=grace_period_end,
                revision=4,
            )
        )
    grace_first = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    grace_second = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert grace_first.created == 1
    assert grace_second.scanned == grace_second.already_present == 0
    admin_items = _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)
    assert {
        BILLING_RENEWAL_DUE_7D,
        BILLING_RENEWAL_DUE_1D,
        BILLING_GRACE_EXPIRED,
    } <= {row["notification_type"] for row in admin_items}
    assert _inbox_rows(postgres, INACTIVE_ADMIN_ACCOUNT) == []
    assert _inbox_rows(postgres, TEACHER_ACCOUNT) == []
    assert all(row["recipient_role"] == "school_manager" for row in admin_items)
    assert all(row["organization_ref"] == ORG_ID for row in admin_items)
    assert all(
        set(row["safe_parameters"]) == {"subscription_ref", "due_local_date"}
        for row in admin_items
    )


def test_payment_notice_recipient_privacy_and_push_best_effort(postgres: Postgres) -> None:
    _seed(postgres)

    first = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.PAYMENTS),
    )
    second = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.PAYMENTS),
    )
    assert first.created == 3
    assert first.no_recipient == 1
    assert second.scanned == 1
    assert second.created == second.already_present == 0
    assert second.no_recipient == 1

    active_admin_items = _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)
    assert _inbox_rows(postgres, INACTIVE_ADMIN_ACCOUNT) == []
    assert _inbox_rows(postgres, TEACHER_ACCOUNT) == []
    parent_items = _inbox_rows(postgres, PARENT_ACCOUNT)
    assert {
        BILLING_ORG_PAYMENT_SUCCEEDED,
        BILLING_ORG_PAYMENT_FAILED,
    } <= {row["notification_type"] for row in active_admin_items}
    assert [row["notification_type"] for row in parent_items] == [
        BILLING_PARENT_PAYMENT_SUCCEEDED
    ]
    assert all(row["recipient_role"] == "school_manager" for row in active_admin_items)
    assert all(row["organization_ref"] == ORG_ID for row in active_admin_items)
    assert all(row["recipient_role"] == "parent" for row in parent_items)
    assert all(row["organization_ref"] is None for row in parent_items)
    assert all(
        set(row["safe_parameters"]) == {"invoice_ref"}
        for row in (*active_admin_items, *parent_items)
        if "PAYMENT_" in str(row["notification_type"])
    )

    canceled_trigger = billing_notice_trigger_id(
        BillingNoticeKind.PAYMENT_FAILED,
        EVENT_ORG_CANCELED,
    )
    no_recipient_trigger = billing_notice_trigger_id(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        EVENT_EMPTY_ORG,
    )
    with postgres.factory() as session:
        canceled_count = session.scalar(
            select(INBOX_ITEMS.c.inbox_item_id).where(INBOX_ITEMS.c.trigger_id == canceled_trigger)
        )
        no_recipient_count = session.scalar(
            select(INBOX_ITEMS.c.inbox_item_id).where(
                INBOX_ITEMS.c.trigger_id == no_recipient_trigger
            )
        )
    assert canceled_count is None
    assert no_recipient_count is None

    sender = LocalFakePushSender(env="test")
    push_now = NOW + timedelta(hours=12)  # inside the 24 hour push enrollment window

    def run_push() -> PushDeliveryReport:
        with postgres.factory() as session:
            return PushDeliveryWorker(SqlPushDeliveryStore(session), sender).run_once(
                now=push_now,
                batch=200,
            )

    push_report = _assert_read_only(postgres, run_push)
    assert push_report.sent >= 1
    assert push_report.failed == 0
    sent_delivery_ids = tuple(record.delivery_id for record in sender.records)
    with postgres.factory() as session:
        sent_billing_deliveries = session.scalars(
            select(PUSH_DELIVERIES.c.delivery_id)
            .join(
                INBOX_ITEMS,
                INBOX_ITEMS.c.inbox_item_id == PUSH_DELIVERIES.c.inbox_item_id,
            )
            .where(
                PUSH_DELIVERIES.c.delivery_id.in_(sent_delivery_ids),
                PUSH_DELIVERIES.c.status == "SENT",
                INBOX_ITEMS.c.notification_type.like("BILLING_%"),
            )
        ).all()
    assert sent_billing_deliveries
    assert eligible_template_keys() >= {
        (BILLING_RENEWAL_DUE_7D, 1),
        (BILLING_RENEWAL_DUE_1D, 1),
        (BILLING_GRACE_EXPIRED, 1),
        (BILLING_ORG_PAYMENT_SUCCEEDED, 1),
        (BILLING_ORG_PAYMENT_FAILED, 1),
        (BILLING_PARENT_PAYMENT_SUCCEEDED, 1),
    }


def test_concurrent_subscription_passes_create_one_notice(postgres: Postgres) -> None:
    _seed(postgres)
    with postgres.factory.begin() as session:
        session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.subscription_id == SUBSCRIPTION_ID)
            .values(
                period_start=NOW - timedelta(days=25),
                period_end=NOW + timedelta(days=5),
                revision=5,
            )
        )
    barrier = Barrier(2)

    def concurrent_pass() -> BillingNoticeSweepResult:
        with postgres.factory() as session:
            barrier.wait(timeout=10)
            return build_billing_notice_sweep(session).run_once(
                now=NOW,
                limit=500,
                source=BillingNoticeSource.SUBSCRIPTIONS,
            )

    def run_concurrent() -> tuple[BillingNoticeSweepResult, BillingNoticeSweepResult]:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(concurrent_pass)
            second = pool.submit(concurrent_pass)
            return first.result(timeout=30), second.result(timeout=30)

    results = _assert_read_only(postgres, run_concurrent)
    assert sorted(result.created for result in results) == [0, 1]
    assert sorted(result.already_present for result in results) == [0, 1]
    rows = [
        row
        for row in _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)
        if row["safe_parameters"].get("subscription_ref") == SUBSCRIPTION_ID
    ]
    assert sum(row["notification_type"] == BILLING_RENEWAL_DUE_7D for row in rows) == 1


def test_locked_subscription_is_skipped_then_delivered(postgres: Postgres) -> None:
    _seed(postgres)
    with postgres.factory.begin() as session:
        session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.subscription_id == SUBSCRIPTION_ID)
            .values(
                period_start=NOW - timedelta(days=26),
                period_end=NOW + timedelta(days=4),
                revision=6,
            )
        )
    with postgres.factory() as holder:
        holder.execute(
            select(SubscriptionModel)
            .where(SubscriptionModel.subscription_id == SUBSCRIPTION_ID)
            .with_for_update()
        ).scalar_one()
        locked = _assert_read_only(
            postgres,
            lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
        )
        assert locked.skipped_stale >= 1
        holder.rollback()
    unlocked = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert unlocked.created == 1


def test_more_than_five_pages_of_existing_triggers_do_not_starve_newest(
    postgres: Postgres,
) -> None:
    _seed_notice_admin(postgres)
    period_end = NOW + timedelta(days=7)
    subscription_ids = [f"{PREFIX}subscription-bulk-{index:04}" for index in range(600)]
    # One subscription per organization: each bulk organization gets the same active admin.
    bulk_orgs = {
        subscription_id: f"{PREFIX}org-bulk-{index:04}"
        for index, subscription_id in enumerate(subscription_ids)
    }
    with postgres.factory.begin() as session:
        session.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic Bulk Organization",
                    state="active",
                    revision=1,
                    created_at=NOW,
                )
                for organization_id in bulk_orgs.values()
            ]
        )
        session.flush()
        session.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}assignment-bulk-{index:04}",
                    organization_id=bulk_orgs[subscription_id],
                    subject=ACTIVE_ADMIN_SUBJECT,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                )
                for index, subscription_id in enumerate(subscription_ids)
            ]
        )
        session.add_all(
            [
                _subscription(subscription_id, period_end, bulk_orgs[subscription_id])
                for subscription_id in subscription_ids
            ]
        )
        session.execute(
            INBOX_ITEMS.insert().values(
                [
                    {
                        "inbox_item_id": f"{PREFIX}inbox-existing-{index:04}",
                        "recipient_account_id": ACTIVE_ADMIN_ACCOUNT,
                        "recipient_role": "school_manager",
                        "organization_ref": bulk_orgs[subscription_id],
                        "notification_type": BILLING_RENEWAL_DUE_7D,
                        "template_version": 1,
                        "trigger_id": billing_notice_trigger_id(
                            BillingNoticeKind.RENEWAL_7D,
                            subscription_id,
                            period_end=period_end,
                        ),
                        "trigger_dedupe_key": billing_notice_trigger_id(
                            BillingNoticeKind.RENEWAL_7D,
                            subscription_id,
                            period_end=period_end,
                        ),
                        "command_sha256": "a" * 64,
                        "safe_parameters": {
                            "subscription_ref": subscription_id,
                            "due_local_date": "2026-12-02",
                        },
                        "created_at": NOW,
                    }
                    for index, subscription_id in enumerate(subscription_ids[:251])
                ]
            )
        )

    first_pass = _assert_read_only(
        postgres,
        lambda: run_billing_notice_pages(
            postgres.factory,
            now=NOW,
            batch_size=50,
            max_pages=5,
        ),
    )
    second_pass = _assert_read_only(
        postgres,
        lambda: run_billing_notice_pages(
            postgres.factory,
            now=NOW,
            batch_size=50,
            max_pages=5,
        ),
    )

    assert first_pass["scanned"] == first_pass["created"] == 250
    assert second_pass["scanned"] == second_pass["created"] == 99
    assert first_pass["failed"] == second_pass["failed"] == 0
    newest_trigger = billing_notice_trigger_id(
        BillingNoticeKind.RENEWAL_7D,
        subscription_ids[-1],
        period_end=period_end,
    )
    received_triggers = {
        str(row["trigger_id"]) for row in _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)
    }
    assert newest_trigger in received_triggers
    assert len(received_triggers) == 600
