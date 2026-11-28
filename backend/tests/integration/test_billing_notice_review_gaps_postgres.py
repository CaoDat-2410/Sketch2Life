# ruff: noqa: E501, F811, SIM117, B023
"""Missing PostgreSQL acceptance tests for E4 T-BILLN1 named in IMPL_REVIEW_E_E4_R1_20261125.md and E4_FIX1_PROMPT.md."""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest
from sqlalchemy import select, update
from test_billing_notice_postgres import (  # noqa: F401
    ACTIVE_ADMIN_ACCOUNT,
    ACTIVE_ADMIN_SUBJECT,
    NOW,
    ORG_ID,
    PARENT_ACCOUNT,
    PARENT_SUBJECT,
    PREFIX,
    Postgres,
    _assert_read_only,
    _identity,
    _inbox_rows,
    _invoice,
    _payment_event,
    _run_once,
    _seed,
    _seed_notice_admin,
    _subscription,
    postgres,
)

from sketch2life.application.ports.billing_notice import BillingNoticeOutcome
from sketch2life.domain.billing_notice import (
    BILLING_GRACE_EXPIRED,
    BILLING_ORG_PAYMENT_SUCCEEDED,
    BILLING_PARENT_PAYMENT_FAILED,
    BILLING_RENEWAL_DUE_1D,
    BillingNoticeKind,
    BillingNoticeSource,
    billing_notice_trigger_id,
)
from sketch2life.infrastructure.notifications.billing_notice_store import SqlBillingNoticeStore
from sketch2life.infrastructure.notifications.notification_worker import run_billing_notice_pages
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.infrastructure.persistence.be1_models import (
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.billing_models import BillingInvoiceModel

pytestmark = pytest.mark.integration


def _existing_inbox_row(
    *,
    inbox_item_id: str,
    recipient: str,
    recipient_role: str,
    org_ref: str | None,
    notification_type: str,
    trigger_id: str,
    safe_parameters: dict[str, str],
) -> dict[str, object]:
    return {
        "inbox_item_id": inbox_item_id,
        "recipient_account_id": recipient,
        "recipient_role": recipient_role,
        "organization_ref": org_ref,
        "notification_type": notification_type,
        "template_version": 1,
        "trigger_id": trigger_id,
        "trigger_dedupe_key": trigger_id,
        "command_sha256": "a" * 64,
        "safe_parameters": safe_parameters,
        "created_at": NOW,
    }


def test_more_than_five_pages_of_existing_payment_triggers_do_not_starve_newest(
    postgres: Postgres,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md P2-2 / E4_FIX1_PROMPT.md (payments >250 notified rows do not starve newest)"""
    _seed_notice_admin(postgres)
    total_events = 260
    pre_notified = 251
    event_ids = [f"{PREFIX}event-bulk-{index:04}" for index in range(total_events)]
    invoice_ids = [f"{PREFIX}invoice-bulk-{index:04}" for index in range(total_events)]

    with postgres.factory.begin() as session:
        session.add_all(
            [
                _invoice(invoice_id, "ORGANIZATION", ORG_ID, "PAID")
                for invoice_id in invoice_ids
            ]
        )
        session.add_all(
            [
                _payment_event(event_id, invoice_id, "PAID")
                for event_id, invoice_id in zip(event_ids, invoice_ids, strict=True)
            ]
        )
        session.execute(
            INBOX_ITEMS.insert().values(
                [
                    _existing_inbox_row(
                        inbox_item_id=f"{PREFIX}inbox-pay-{index:04}",
                        recipient=ACTIVE_ADMIN_ACCOUNT,
                        recipient_role="school_manager",
                        org_ref=ORG_ID,
                        notification_type=BILLING_ORG_PAYMENT_SUCCEEDED,
                        trigger_id=billing_notice_trigger_id(
                            BillingNoticeKind.PAYMENT_SUCCEEDED,
                            event_id,
                        ),
                        safe_parameters={"invoice_ref": invoice_id},
                    )
                    for index, (event_id, invoice_id) in enumerate(
                        zip(event_ids[:pre_notified], invoice_ids[:pre_notified], strict=True)
                    )
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

    assert first_pass["scanned"] == first_pass["created"] == total_events - pre_notified
    assert first_pass["failed"] == 0
    newest_trigger = billing_notice_trigger_id(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        event_ids[-1],
    )
    received_triggers = {
        str(row["trigger_id"]) for row in _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)
    }
    assert newest_trigger in received_triggers
    assert len(received_triggers) == total_events


def test_existing_renewal_1d_and_grace_expired_triggers_excluded_by_scan_antijoin(
    postgres: Postgres,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md P2-2 / E4_FIX1_PROMPT.md (SQL anti-join covers RENEWAL_1D and GRACE_EXPIRED)"""
    _seed_notice_admin(postgres)
    renewal_1d_end = NOW + timedelta(days=1)
    grace_end = NOW - timedelta(days=7)
    r1d_ids = [f"{PREFIX}sub-1d-{index:04}" for index in range(252)]
    grace_ids = [f"{PREFIX}sub-grace-{index:04}" for index in range(252)]

    with postgres.factory.begin() as session:
        session.add_all([_subscription(sid, renewal_1d_end) for sid in r1d_ids])
        session.add_all([_subscription(sid, grace_end) for sid in grace_ids])
        session.execute(
            INBOX_ITEMS.insert().values(
                [
                    _existing_inbox_row(
                        inbox_item_id=f"{PREFIX}inbox-1d-{index:04}",
                        recipient=ACTIVE_ADMIN_ACCOUNT,
                        recipient_role="school_manager",
                        org_ref=ORG_ID,
                        notification_type=BILLING_RENEWAL_DUE_1D,
                        trigger_id=billing_notice_trigger_id(
                            BillingNoticeKind.RENEWAL_1D,
                            sid,
                            period_end=renewal_1d_end,
                        ),
                        safe_parameters={
                            "subscription_ref": sid,
                            "due_local_date": "2026-11-26",
                        },
                    )
                    for index, sid in enumerate(r1d_ids[:251])
                ]
                + [
                    _existing_inbox_row(
                        inbox_item_id=f"{PREFIX}inbox-gr-{index:04}",
                        recipient=ACTIVE_ADMIN_ACCOUNT,
                        recipient_role="school_manager",
                        org_ref=ORG_ID,
                        notification_type=BILLING_GRACE_EXPIRED,
                        trigger_id=billing_notice_trigger_id(
                            BillingNoticeKind.GRACE_EXPIRED,
                            sid,
                            period_end=grace_end,
                        ),
                        safe_parameters={
                            "subscription_ref": sid,
                            "due_local_date": "2026-11-25",
                        },
                    )
                    for index, sid in enumerate(grace_ids[:251])
                ]
            )
        )

    result = _assert_read_only(
        postgres,
        lambda: run_billing_notice_pages(
            postgres.factory,
            now=NOW,
            batch_size=50,
            max_pages=5,
        ),
    )

    assert result["scanned"] == result["created"] == 2
    assert result["failed"] == 0
    triggers = {str(row["trigger_id"]) for row in _inbox_rows(postgres, ACTIVE_ADMIN_ACCOUNT)}
    assert billing_notice_trigger_id(
        BillingNoticeKind.RENEWAL_1D, r1d_ids[-1], period_end=renewal_1d_end
    ) in triggers
    assert billing_notice_trigger_id(
        BillingNoticeKind.GRACE_EXPIRED, grace_ids[-1], period_end=grace_end
    ) in triggers


def test_org_recipient_limit_20_scope_filters_and_later_admin_dedupe(
    postgres: Postgres,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D4/D6 cap 20, org/role filter, later admin)"""
    capped_org = f"{PREFIX}org-capped"
    sub_id = f"{PREFIX}sub-capped"
    admin_accounts = [f"{PREFIX}cap-acc-{i:02}" for i in range(22)]
    admin_subjects = [f"{PREFIX}cap-sub-{i:02}" for i in range(22)]
    class_admin_account = f"{PREFIX}cap-class-acc"
    class_admin_subject = f"{PREFIX}cap-class-sub"
    inactive_assign_account = f"{PREFIX}cap-inact-acc"
    inactive_assign_subject = f"{PREFIX}cap-inact-sub"
    org_teacher_account = f"{PREFIX}cap-teacher-acc"
    org_teacher_subject = f"{PREFIX}cap-teacher-sub"
    later_admin_account = f"{PREFIX}cap-later-acc"
    later_admin_subject = f"{PREFIX}cap-later-sub"

    with postgres.factory.begin() as session:
        session.add(
            OrganizationModel(
                organization_id=capped_org,
                display_name="Capped Org",
                state="active",
                revision=1,
                created_at=NOW,
            )
        )
        for subj, acc in zip(admin_subjects, admin_accounts, strict=True):
            session.add(_identity(subj, acc, "school_manager"))
            session.add(
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}asgn-{subj}",
                    organization_id=capped_org,
                    subject=subj,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                )
            )
        session.add_all(
            [
                _identity(class_admin_subject, class_admin_account, "school_manager"),
                _identity(inactive_assign_subject, inactive_assign_account, "school_manager"),
                _identity(org_teacher_subject, org_teacher_account, "teacher"),
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}asgn-class-admin",
                    organization_id=capped_org,
                    subject=class_admin_subject,
                    class_id=f"{PREFIX}class-1",
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}asgn-inact-assign",
                    organization_id=capped_org,
                    subject=inactive_assign_subject,
                    class_id=None,
                    role="school_admin",
                    active=False,
                    pending_activation=False,
                    created_at=NOW,
                ),
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}asgn-org-teacher",
                    organization_id=capped_org,
                    subject=org_teacher_subject,
                    class_id=None,
                    role="teacher",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
            ]
        )
        sub = _subscription(sub_id, NOW + timedelta(days=7))
        sub.organization_ref = capped_org
        session.add(sub)

    first = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert first.created == 1

    with postgres.factory() as session:
        created_rows = (
            session.execute(
                select(INBOX_ITEMS.c.recipient_account_id, INBOX_ITEMS.c.expires_at).where(
                    INBOX_ITEMS.c.organization_ref == capped_org
                )
            )
            .mappings()
            .all()
        )
    delivered_accounts = {str(row["recipient_account_id"]) for row in created_rows}
    assert delivered_accounts == set(admin_accounts[:20])
    assert all(row["expires_at"] is None for row in created_rows)
    assert class_admin_account not in delivered_accounts
    assert inactive_assign_account not in delivered_accounts
    assert org_teacher_account not in delivered_accounts

    with postgres.factory.begin() as session:
        session.add(_identity(later_admin_subject, later_admin_account, "school_manager"))
        session.add(
            OrganizationAssignmentModel(
                assignment_id=f"{PREFIX}asgn-later",
                organization_id=capped_org,
                subject=later_admin_subject,
                class_id=None,
                role="school_admin",
                active=True,
                pending_activation=False,
                created_at=NOW,
            )
        )
    second = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert second.created == 0
    assert _inbox_rows(postgres, later_admin_account) == []


def test_no_recipient_retries_when_admin_activated_and_inactive_org_skipped(
    postgres: Postgres,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D6 NO_RECIPIENT retry & inactive org)"""
    empty_org = f"{PREFIX}org-no-admin"
    inactive_org = f"{PREFIX}org-inactive"
    inactive_org_admin_subj = f"{PREFIX}subj-inact-org"
    inactive_org_admin_acc = f"{PREFIX}acc-inact-org"
    activated_subj = f"{PREFIX}subj-activated"
    activated_acc = f"{PREFIX}acc-activated"

    with postgres.factory.begin() as session:
        session.add_all(
            [
                OrganizationModel(
                    organization_id=empty_org,
                    display_name="Empty Org",
                    state="active",
                    revision=1,
                    created_at=NOW,
                ),
                OrganizationModel(
                    organization_id=inactive_org,
                    display_name="Inactive Org",
                    state="disabled",
                    revision=1,
                    created_at=NOW,
                ),
                _identity(inactive_org_admin_subj, inactive_org_admin_acc, "school_manager"),
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}asgn-inact-org",
                    organization_id=inactive_org,
                    subject=inactive_org_admin_subj,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
            ]
        )
        s1 = _subscription(f"{PREFIX}sub-empty-org", NOW + timedelta(days=7))
        s1.organization_ref = empty_org
        s2 = _subscription(f"{PREFIX}sub-inact-org", NOW + timedelta(days=7))
        s2.organization_ref = inactive_org
        session.add_all([s1, s2])

    first = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert first.scanned == first.no_recipient == 2
    assert first.created == 0

    with postgres.factory.begin() as session:
        session.add(_identity(activated_subj, activated_acc, "school_manager"))
        session.add(
            OrganizationAssignmentModel(
                assignment_id=f"{PREFIX}asgn-activated",
                organization_id=empty_org,
                subject=activated_subj,
                class_id=None,
                role="school_admin",
                active=True,
                pending_activation=False,
                created_at=NOW,
            )
        )

    second = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )
    assert second.scanned == 2
    assert second.created == 1
    assert second.no_recipient == 1
    assert len(_inbox_rows(postgres, activated_acc)) == 1
    assert _inbox_rows(postgres, inactive_org_admin_acc) == []


def test_parent_payment_failed_and_locked_or_drifted_invoice_is_stale_then_delivered(
    postgres: Postgres,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D5/D6 parent payment failed & locked/drifted invoice)"""
    parent_failed_inv = f"{PREFIX}inv-parent-failed"
    parent_failed_evt = f"{PREFIX}evt-parent-failed"
    inactive_parent_subj = f"{PREFIX}subj-parent-inact"
    inactive_parent_acc = f"{PREFIX}acc-parent-inact"
    inactive_parent_inv = f"{PREFIX}inv-parent-inact"
    inactive_parent_evt = f"{PREFIX}evt-parent-inact"

    with postgres.factory.begin() as session:
        session.add_all(
            [
                _identity(PARENT_SUBJECT, PARENT_ACCOUNT, "parent"),
                _identity(inactive_parent_subj, inactive_parent_acc, "parent", state="inactive"),
                _invoice(parent_failed_inv, "PARENT_ACCOUNT", PARENT_ACCOUNT, "FAILED"),
                _invoice(inactive_parent_inv, "PARENT_ACCOUNT", inactive_parent_acc, "FAILED"),
                _payment_event(parent_failed_evt, parent_failed_inv, "FAILED"),
                _payment_event(inactive_parent_evt, inactive_parent_inv, "FAILED"),
            ]
        )

    with postgres.factory() as holder:
        holder.execute(
            select(BillingInvoiceModel)
            .where(BillingInvoiceModel.invoice_id == parent_failed_inv)
            .with_for_update()
        ).scalar_one()
        locked = _assert_read_only(
            postgres,
            lambda: _run_once(postgres, BillingNoticeSource.PAYMENTS),
        )
        assert locked.skipped_stale >= 1
        assert locked.no_recipient == 1
        holder.rollback()

    unlocked = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.PAYMENTS),
    )
    assert unlocked.created == 1
    parent_rows = _inbox_rows(postgres, PARENT_ACCOUNT)
    assert [row["notification_type"] for row in parent_rows] == [BILLING_PARENT_PAYMENT_FAILED]
    assert parent_rows[0]["recipient_role"] == "parent"
    assert parent_rows[0]["organization_ref"] is None
    assert _inbox_rows(postgres, inactive_parent_acc) == []

    # Drifted invoice state between scan and enqueue_if_due returns STALE.
    drift_inv = f"{PREFIX}inv-drift"
    drift_evt = f"{PREFIX}evt-drift"
    with postgres.factory.begin() as session:
        session.add_all(
            [
                _invoice(drift_inv, "PARENT_ACCOUNT", PARENT_ACCOUNT, "PAID"),
                _payment_event(drift_evt, drift_inv, "PAID"),
            ]
        )
    with postgres.factory() as scanner_session:
        store = SqlBillingNoticeStore(scanner_session)
        page = store.scan_candidates(NOW, BillingNoticeSource.PAYMENTS, 50, None)
        drift_candidate = next(c for c in page.candidates if c.subject_id == drift_evt)
    with postgres.factory.begin() as session:
        session.execute(
            update(BillingInvoiceModel)
            .where(BillingInvoiceModel.invoice_id == drift_inv)
            .values(state="CANCELED", revision=2)
        )
    with postgres.factory() as enqueue_session:
        outcome = SqlBillingNoticeStore(enqueue_session).enqueue_if_due(drift_candidate, NOW)
    assert outcome is BillingNoticeOutcome.STALE


def test_invalid_org_ref_is_counted_failed_without_logging_identifier(
    postgres: Postgres,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D8 & §6 R3 invalid org ref failed, silent)"""
    bad_org_id = f"{PREFIX}bad org ref with spaces"
    admin_subj = f"{PREFIX}subj-bad-org"
    admin_acc = f"{PREFIX}acc-bad-org"
    with postgres.factory.begin() as session:
        session.add_all(
            [
                OrganizationModel(
                    organization_id=bad_org_id,
                    display_name="Bad Org",
                    state="active",
                    revision=1,
                    created_at=NOW,
                ),
                _identity(admin_subj, admin_acc, "school_manager"),
                OrganizationAssignmentModel(
                    assignment_id=f"{PREFIX}asgn-bad-org",
                    organization_id=bad_org_id,
                    subject=admin_subj,
                    class_id=None,
                    role="school_admin",
                    active=True,
                    pending_activation=False,
                    created_at=NOW,
                ),
            ]
        )
        sub = _subscription(f"{PREFIX}sub-bad-org", NOW + timedelta(days=7))
        sub.organization_ref = bad_org_id
        session.add(sub)

    caplog.set_level(logging.DEBUG)
    result = _assert_read_only(
        postgres,
        lambda: _run_once(postgres, BillingNoticeSource.SUBSCRIPTIONS),
    )

    assert result.scanned == result.failed == 1
    assert result.created == 0
    assert bad_org_id not in caplog.text
