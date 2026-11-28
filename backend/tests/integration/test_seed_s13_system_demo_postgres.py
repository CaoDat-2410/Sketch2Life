"""PostgreSQL acceptance checks for the S13 Parent and billing seed stage."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import TypedDict

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.lesson_library.feedback_tables import (
    FEEDBACK_MESSAGES,
    FEEDBACK_THREADS,
)
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingPaymentAttemptModel,
    BillingPaymentEventModel,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentConsentPolicyModel,
    ParentProfileContextEntryModel,
)
from sketch2life.infrastructure.platform_admin.sandbox_billing import SandboxBillingService
from sketch2life.infrastructure.platform_admin.sandbox_capacity import SandboxCapacityService
from sketch2life.infrastructure.profile_sharing.tables import PROFILE_SHARE_GRANTS
from tools.seed import data, s13_system_demo, s13_system_demo_data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s1_core import run_s1
from tools.seed.s7a_runs import run_s7a
from tools.seed.s7b_story_states import run_s7b
from tools.seed.s8_lessons import run_s8
from tools.seed.s12_story_v4a import run_s12
from tools.seed.stage_common import check_database_prefix

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)


class SeededRows(TypedDict):
    first_ok: bool
    second_ok: bool
    before_second: dict[str, int]
    totals: dict[str, int]


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
    from sketch2life.infrastructure.config.settings import (
        get_core_database_settings,
        get_settings,
    )

    previous = os.environ.get("SKETCH2LIFE_DATABASE_URL")
    try:
        check_database_prefix()
        engine, _target = guarded_engine()
        try:
            yield engine
        finally:
            engine.dispose()
    finally:
        if previous is None:
            os.environ.pop("SKETCH2LIFE_DATABASE_URL", None)
        else:
            os.environ["SKETCH2LIFE_DATABASE_URL"] = previous
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(scope="module")
def seeded(seed_engine: Engine) -> SeededRows:
    run_s1(seed_engine)
    run_s7a(seed_engine)
    run_s8(seed_engine)
    run_s7b(seed_engine)
    run_s12(seed_engine)
    first = s13_system_demo.run_s13(seed_engine)
    with seed_engine.connect() as connection:
        before_second = s13_system_demo.count_s13_rows(connection, datetime.now(UTC))
    second = s13_system_demo.run_s13(seed_engine)
    with seed_engine.connect() as connection:
        totals = s13_system_demo.count_s13_rows(connection, datetime.now(UTC))
    return {
        "first_ok": first.ok,
        "second_ok": second.ok,
        "before_second": before_second,
        "totals": totals,
    }


def test_s13_twice_adds_no_rows_and_matches_expected(seeded: SeededRows) -> None:
    assert seeded["first_ok"]
    assert seeded["second_ok"]
    assert seeded["before_second"] == s13_system_demo.EXPECTED
    assert seeded["totals"] == s13_system_demo.EXPECTED


def test_parent_profile_policy_share_and_quota_are_readable(
    seed_engine: Engine, seeded: SeededRows
) -> None:
    del seeded
    profile_id = data.parent_profile_id(s13_system_demo_data.PARENT_PROFILE_KEY)
    with Session(seed_engine) as session:
        policy = session.scalar(
            select(ParentConsentPolicyModel).where(
                ParentConsentPolicyModel.policy_version
                == s13_system_demo_data.CONSENT_POLICY_VERSION
            )
        )
        assert policy is not None
        assert policy.state == "DRAFT"
        assert "phụ huynh" in policy.consent_text

        context_entry = session.scalar(
            select(ParentProfileContextEntryModel).where(
                ParentProfileContextEntryModel.parent_profile_id == profile_id
            )
        )
        assert context_entry is not None
        assert context_entry.entry_kind == "OBSERVATION"
        assert "Mít" in context_entry.short_text

        share = session.execute(
            select(PROFILE_SHARE_GRANTS).where(
                PROFILE_SHARE_GRANTS.c.parent_profile_id == profile_id
            )
        ).mappings().one()
        assert share["state"] == "INVITED"
        assert share["data_origin"] == "SYNTHETIC_DEV"
        assert share["granted_fields"] == ["AGE_BAND", "DISPLAY_NAME"]

        feedback_thread = session.execute(
            select(FEEDBACK_THREADS).where(
                FEEDBACK_THREADS.c.lesson_id
                == s13_system_demo_data.PARENT_FEEDBACK_LESSON_ID,
                FEEDBACK_THREADS.c.created_by
                == s13_system_demo_data.PARENT_FEEDBACK_SUBJECT,
            )
        ).mappings().one()
        feedback_message = session.execute(
            select(FEEDBACK_MESSAGES).where(
                FEEDBACK_MESSAGES.c.thread_id == feedback_thread["thread_id"],
                FEEDBACK_MESSAGES.c.actor_ref == s13_system_demo_data.PARENT_FEEDBACK_SUBJECT,
            )
        ).mappings().one()
        assert feedback_message["body"] == s13_system_demo_data.PARENT_FEEDBACK_TEXT

    settings = SimpleNamespace(
        video_quota_included_units_parent=s13_system_demo_data.PARENT_QUOTA_UNITS,
        video_quota_included_units_organization=s13_system_demo_data.ORGANIZATION_QUOTA_UNITS,
        billing_real_payments_enabled=False,
    )
    with Session(seed_engine) as session:
        commerce = QuotaCommerceService(session, data.PLATFORM_ADMIN_SUBJECT, settings)
        parent_quota = commerce.quota_summary("PARENT_ACCOUNT", data.parent_account_id("p1"))
        school_quota = commerce.quota_summary("ORGANIZATION", data.org_id("a"))
        assert parent_quota["available_units"] == s13_system_demo_data.PARENT_QUOTA_UNITS
        assert school_quota["allocation"]["teachers"][0]["teacher_ref"] == data.ORG_A_TEACHERS[0]
        assert school_quota["allocation"]["teachers"][0]["available_units"] == (
            s13_system_demo_data.TEACHER_QUOTA_UNITS
        )


def test_capacity_invoice_is_sandbox_only_and_has_no_provider_attempt(
    seed_engine: Engine, seeded: SeededRows
) -> None:
    del seeded
    settings = SimpleNamespace(env="test", billing_sandbox_enabled=True)
    with Session(seed_engine) as session:
        billing = SandboxBillingService(
            session,
            data.PLATFORM_ADMIN_SUBJECT,
            settings,
            clock=lambda: datetime.now(UTC),
        )
        subscription = SandboxCapacityService(billing).list(25, None)["items"]
        assert len(subscription) == 1
        assert subscription[0]["organization_ref"] == data.org_id("a")
        assert subscription[0]["state"] == "ACTIVE"
        assert subscription[0]["provider"] == "SANDBOX"

        invoice = session.scalar(
            select(BillingInvoiceModel).where(
                BillingInvoiceModel.owner_kind == "ORGANIZATION",
                BillingInvoiceModel.owner_ref == data.org_id("a"),
            )
        )
        assert invoice is not None
        assert invoice.state == "PAID"
        assert invoice.provider == "SANDBOX"
        assert session.scalar(
            select(BillingPaymentAttemptModel.attempt_id).where(
                BillingPaymentAttemptModel.invoice_id == invoice.invoice_id
            )
        ) is None
        event = session.scalar(
            select(BillingPaymentEventModel).where(
                BillingPaymentEventModel.invoice_id == invoice.invoice_id
            )
        )
        assert event is not None
        assert event.provider == "SANDBOX"
