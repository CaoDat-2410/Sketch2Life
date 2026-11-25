from __future__ import annotations

from datetime import UTC, datetime

from sketch2life.application.services.notification_templates import (
    TEMPLATE_REGISTRY,
    eligible_template_keys,
    is_push_eligible,
    lookup_template,
)
from sketch2life.application.services.story_run_reminder import reminder_command
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
    assert list(TEMPLATE_REGISTRY) == [key]
    assert eligible_template_keys() == frozenset({key})


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


def test_unknown_notification_type_or_version_is_not_push_eligible() -> None:
    assert lookup_template("UNKNOWN_NOTICE", 1) is None
    assert is_push_eligible("UNKNOWN_NOTICE", 1) is False
    assert is_push_eligible(REMINDER_NOTIFICATION_TYPE, REMINDER_TEMPLATE_VERSION + 1) is False
