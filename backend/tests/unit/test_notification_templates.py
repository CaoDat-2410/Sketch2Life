from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sketch2life.application.services.billing_notice import (
    payment_notice_command,
    subscription_notice_command,
)
from sketch2life.application.services.notification_templates import (
    TEMPLATE_REGISTRY,
    eligible_template_keys,
    is_push_eligible,
    lookup_template,
)
from sketch2life.application.services.notifications import validate_command
from sketch2life.application.services.story_run_reminder import reminder_command
from sketch2life.domain.billing_notice import (
    BILLING_GRACE_EXPIRED,
    BILLING_ORG_PAYMENT_FAILED,
    BILLING_ORG_PAYMENT_SUCCEEDED,
    BILLING_PARENT_PAYMENT_FAILED,
    BILLING_PARENT_PAYMENT_SUCCEEDED,
    BILLING_RENEWAL_DUE_1D,
    BILLING_RENEWAL_DUE_7D,
    BILLING_TEMPLATE_VERSION,
    BillingNoticeKind,
)
from sketch2life.domain.story_run_reminder import (
    REMINDER_NOTIFICATION_TYPE,
    REMINDER_TEMPLATE_VERSION,
)


def test_run_wait_reminder_is_registered_from_the_domain_constants() -> None:
    key = (REMINDER_NOTIFICATION_TYPE, REMINDER_TEMPLATE_VERSION)
    spec = lookup_template(*key)

    assert spec is not None
    assert spec.notification_type == "RUN_WAIT_REMINDER"
    assert spec.version == 1
    assert spec.kind == "REMINDER"
    assert spec.recipient_role == "parent"
    assert spec.allowed_parameters == ()
    assert spec.push_eligible is True
    billing_keys = [
        (notification_type, BILLING_TEMPLATE_VERSION)
        for notification_type in (
            BILLING_RENEWAL_DUE_7D,
            BILLING_RENEWAL_DUE_1D,
            BILLING_GRACE_EXPIRED,
            BILLING_ORG_PAYMENT_SUCCEEDED,
            BILLING_ORG_PAYMENT_FAILED,
            BILLING_PARENT_PAYMENT_SUCCEEDED,
            BILLING_PARENT_PAYMENT_FAILED,
        )
    ]
    assert list(TEMPLATE_REGISTRY) == [key, *billing_keys]
    assert eligible_template_keys() == frozenset({key, *billing_keys})


def test_reminder_command_parameters_fit_the_registered_allowlist() -> None:
    spec = lookup_template(REMINDER_NOTIFICATION_TYPE, REMINDER_TEMPLATE_VERSION)
    assert spec is not None

    command = reminder_command(
        recipient_account_id="parent-1",
        run_id="run-1",
        run_state="SCRIPT_REVIEW",
        wait_since=datetime(2026, 11, 1, tzinfo=UTC),
    )

    assert set(command.safe_parameters) <= set(spec.allowed_parameters)


def test_every_billing_command_builder_fits_its_registered_template() -> None:
    now = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    org_id = "12345678-1234-1234-1234-123456789abc"
    account_id = "abcdef12-1234-1234-1234-123456789abc"
    commands = [
        subscription_notice_command(
            recipient_account_id=account_id,
            organization_ref=org_id,
            kind=kind,
            subscription_id="subscription-123",
            period_end=now + timedelta(days=7),
        )
        for kind in (
            BillingNoticeKind.RENEWAL_7D,
            BillingNoticeKind.RENEWAL_1D,
            BillingNoticeKind.GRACE_EXPIRED,
        )
    ]
    for owner_kind, owner_ref in (("ORGANIZATION", org_id), ("PARENT_ACCOUNT", account_id)):
        for kind in (BillingNoticeKind.PAYMENT_SUCCEEDED, BillingNoticeKind.PAYMENT_FAILED):
            commands.append(
                payment_notice_command(
                    recipient_account_id=account_id,
                    owner_kind=owner_kind,
                    owner_ref=owner_ref,
                    kind=kind,
                    invoice_id="invoice-123",
                    payment_event_id="event-123",
                )
            )

    for command in commands:
        spec = lookup_template(command.notification_type, command.template_version)
        assert spec is not None
        assert command.recipient_role == spec.recipient_role
        assert set(command.safe_parameters) == set(spec.allowed_parameters)
        validate_command(command, created_at=now)


def test_unknown_notification_type_or_version_is_not_push_eligible() -> None:
    assert lookup_template("UNKNOWN_NOTICE", 1) is None
    assert is_push_eligible("UNKNOWN_NOTICE", 1) is False
    assert is_push_eligible(REMINDER_NOTIFICATION_TYPE, REMINDER_TEMPLATE_VERSION + 1) is False
