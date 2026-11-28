"""Pure fixture and service-safety checks for the S13 whole-system seed stage."""

from __future__ import annotations

from tools.seed import data, s12_story_v4a_data, s13_system_demo_data


def test_s13_uses_reserved_accounts_and_vietnamese_product_copy() -> None:
    assert s13_system_demo_data.PARENT_KEY == "p1"
    assert s13_system_demo_data.PARENT_PROFILE_KEY == "k1"
    assert data.PLATFORM_ADMIN_SUBJECT == "seed-admin"
    assert data.ORG_A_TEACHERS[0] == "seed-tch-a1"
    assert s13_system_demo_data.PARENT_FEEDBACK_SUBJECT == "seed-parent-s12-p6"
    assert [product["owner_kind"] for product in s13_system_demo_data.QUOTA_PRODUCTS] == [
        "PARENT_ACCOUNT",
        "ORGANIZATION",
    ]
    assert all(
        "lượt" in str(product["display_name"])
        for product in s13_system_demo_data.QUOTA_PRODUCTS
    )
    assert all(
        any(ord(character) > 127 for character in str(product["display_name"]))
        for product in s13_system_demo_data.QUOTA_PRODUCTS
    )
    assert "phụ huynh" in s13_system_demo_data.CONSENT_POLICY_TEXT
    assert "Mít" in s13_system_demo_data.PARENT_CONTEXT_ENTRY_TEXT
    assert "Bé thích quan sát tán lá xanh" in s13_system_demo_data.PARENT_FEEDBACK_TEXT
    assert s13_system_demo_data.EXPECTED["lesson_feedback_threads_s13"] == 1
    assert s13_system_demo_data.EXPECTED["notification_inbox_items_s13"] == 1


def test_demo_account_profiles_belong_to_seeded_adults() -> None:
    profiles = data.DEMO_ACCOUNT_PROFILES
    seeded = {row["subject"] for row in data.adult_rows()}
    seeded |= {parent.subject for parent in s12_story_v4a_data.PARENT_SPECS}
    # Every seeded adult has a name, so no account screen shows an unnamed row.
    assert set(profiles) == seeded
    emails = [email for email, _name in profiles.values()]
    assert len(set(emails)) == len(profiles) == 27
    assert all(email.endswith(".test") for email in emails)
    assert all(name and "@" not in name for _email, name in profiles.values())


def test_s13_expects_only_sandbox_capacity_payment_and_no_provider_attempts() -> None:
    assert s13_system_demo_data.EXPECTED["billing_invoices"] == 1
    assert s13_system_demo_data.EXPECTED["billing_payment_events_sandbox"] == 1
    assert s13_system_demo_data.EXPECTED["billing_payment_attempts"] == 0
    assert s13_system_demo_data.EXPECTED["billing_video_quota_usage"] == 0
    assert len(s13_system_demo_data.BILLING_COMMAND_KEYS) + 1 == s13_system_demo_data.EXPECTED[
        "billing_command_receipts_s13"
    ]
    assert len(s13_system_demo_data.QUOTA_PRODUCTS) == 2
