from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta

import pytest

from sketch2life.domain.profile_sharing import (
    ShareFieldError,
    ShareState,
    delivered_at,
    effective_state,
    generate_invitation_code,
    grant_window,
    history_item_visible,
    invitation_code_sha256,
    invitation_window,
    normalize_granted_fields,
    request_fingerprint,
)


def test_granted_fields_are_sorted_unique_and_least_privilege() -> None:
    assert normalize_granted_fields(
        ["INTERESTS_SUMMARY", "DISPLAY_NAME", "DISPLAY_NAME"]
    ) == ("DISPLAY_NAME", "INTERESTS_SUMMARY")
    for refused in ("SUPPORT_NEEDS", "CONTEXT_ENTRIES", "AGE_MONTHS"):
        with pytest.raises(ShareFieldError) as error:
            normalize_granted_fields([refused])
        assert error.value.field == "granted_fields"
        assert error.value.code == "NOT_SUPPORTED"
    with pytest.raises(ShareFieldError):
        normalize_granted_fields([])


def test_effective_state_expires_at_inclusive_boundaries() -> None:
    now = datetime(2026, 11, 25, 12, tzinfo=UTC)
    invited = {"state": "INVITED", "invitation_expires_at": now}
    active = {"state": "ACTIVE", "expires_at": now}
    assert effective_state(invited, now) is ShareState.EXPIRED
    assert effective_state(active, now) is ShareState.EXPIRED
    assert effective_state(
        {"state": "INVITED", "invitation_expires_at": now + timedelta(microseconds=1)}, now
    ) is ShareState.INVITED
    assert effective_state(
        {"state": "ACTIVE", "expires_at": now + timedelta(microseconds=1)}, now
    ) is ShareState.ACTIVE


def test_code_hash_fingerprints_and_windows_are_stable() -> None:
    code = generate_invitation_code()
    assert 16 <= len(code) <= 64
    assert re.fullmatch(r"[A-Za-z0-9_-]+", code)
    assert len(invitation_code_sha256(code)) == 64
    payload = {"op": "parent_share.create.v1", "granted_fields": ["DISPLAY_NAME"]}
    reordered = dict(reversed(list(payload.items())))
    assert request_fingerprint(payload) == request_fingerprint(reordered)
    assert request_fingerprint(payload) != request_fingerprint({**payload, "granted_fields": []})
    now = datetime(2026, 11, 25, 12, tzinfo=UTC)
    assert invitation_window(now) == now + timedelta(days=90)
    assert grant_window(now) == now + timedelta(days=90)


def test_delivery_time_uses_claim_or_utc_midnight() -> None:
    claim = datetime(2026, 11, 25, 15, 30, tzinfo=UTC)
    assert delivered_at(claim, date(2026, 11, 24)) == claim
    assert delivered_at(None, date(2026, 11, 24)) == datetime(2026, 11, 24, tzinfo=UTC)
    assert delivered_at(None, None) is None


def test_delivery_history_predicate_covers_scope_and_window_edges() -> None:
    now = datetime(2026, 11, 25, 12, tzinfo=UTC)
    accepted = now - timedelta(days=2)
    enrollment = now - timedelta(days=4)
    common = {
        "occurrence_state": "SAMPLE_AVAILABLE",
        "delivered_at_value": accepted,
        "accepted_at": accepted,
        "access_ends_at": now + timedelta(days=1),
        "enrollment_created_at": enrollment,
        "now": now,
    }
    assert history_item_visible(**common)
    before_accept = accepted - timedelta(seconds=1)
    assert not history_item_visible(**{**common, "delivered_at_value": before_accept})
    assert not history_item_visible(**{**common, "delivered_at_value": now - timedelta(days=30)})
    assert not history_item_visible(**{**common, "delivered_at_value": now + timedelta(seconds=1)})
    assert not history_item_visible(**{**common, "access_ends_at": accepted})
    assert not history_item_visible(
        **{**common, "enrollment_created_at": accepted + timedelta(seconds=1)}
    )
    assert not history_item_visible(**{**common, "occurrence_state": "DRAFT"})
