# ruff: noqa: E501, F811, SIM117, B023
"""Unit tests for E3 (T-SHARE1) review gaps (domain states, layering, error mapping)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

from sketch2life.domain.profile_sharing import (
    ProfileShareConflict,
    ProfileShareInvalidRequest,
    ProfileShareNotFound,
    ProfileShareStaleRevision,
    ProfileShareUnavailable,
    ShareState,
    effective_state,
    history_item_visible,
)
from sketch2life.interfaces.http.profile_sharing_errors import call_profile_share_service


def test_effective_state_preserves_terminal_states_and_rejects_unknown() -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-1 / Checks-Windows (terminal & invalid states)"""
    now = datetime(2026, 11, 25, 12, tzinfo=UTC)
    assert effective_state({"state": "REVOKED"}, now) is ShareState.REVOKED
    assert effective_state({"state": "EXPIRED"}, now) is ShareState.EXPIRED
    with pytest.raises(ValueError, match="unknown profile-share state"):
        effective_state({"state": "UNKNOWN"}, now)


def test_history_predicate_cuts_off_at_grant_expires_at_not_settlement_time() -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-1 (expiry cut at expires_at)"""
    accepted = datetime(2026, 9, 1, 0, tzinfo=UTC)
    expires_at = accepted + timedelta(days=90)
    now = expires_at + timedelta(days=5)
    enrollment = accepted - timedelta(days=1)

    assert not history_item_visible(
        occurrence_state="SAMPLE_AVAILABLE",
        delivered_at_value=expires_at,
        accepted_at=accepted,
        access_ends_at=expires_at,
        enrollment_created_at=enrollment,
        now=now,
    )
    assert history_item_visible(
        occurrence_state="SAMPLE_AVAILABLE",
        delivered_at_value=expires_at - timedelta(seconds=1),
        accepted_at=accepted,
        access_ends_at=expires_at,
        enrollment_created_at=enrollment,
        now=now,
    )


def test_profile_sharing_service_has_no_http_layer_imports() -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-4 (infrastructure service free of HTTP imports)"""
    backend = Path(__file__).resolve().parents[2]
    service_path = backend / "src" / "sketch2life" / "infrastructure" / "profile_sharing" / "service.py"
    source = service_path.read_text(encoding="utf-8")
    assert "fastapi" not in source
    assert "interfaces.http" not in source


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code", "expected_etag"),
    [
        (ProfileShareNotFound(), 404, "RESOURCE_NOT_FOUND", None),
        (
            ProfileShareInvalidRequest(
                "INVALID_REQUEST", field_errors=[{"field": "limit", "code": "OUT_OF_RANGE"}]
            ),
            400,
            "INVALID_REQUEST",
            None,
        ),
        (ProfileShareInvalidRequest("INVALID_IDEMPOTENCY_KEY"), 400, "INVALID_IDEMPOTENCY_KEY", None),
        (ProfileShareStaleRevision(5), 409, "STALE_REVISION", '"5"'),
        (ProfileShareConflict("INVITATION_EXPIRED"), 409, "INVITATION_EXPIRED", None),
        (ProfileShareUnavailable("DATABASE_UNAVAILABLE"), 503, "DATABASE_UNAVAILABLE", None),
    ],
)
def test_profile_sharing_error_mapper_translates_domain_errors(
    error: Exception,
    expected_status: int,
    expected_code: str,
    expected_etag: str | None,
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-4 (router translates domain errors)"""
    def _raise() -> None:
        raise error

    with pytest.raises(HTTPException) as exc:
        call_profile_share_service(_raise)
    assert exc.value.status_code == expected_status
    assert isinstance(exc.value.detail, dict)
    assert exc.value.detail["code"] == expected_code
    if expected_etag is not None:
        assert exc.value.headers == {"ETag": expected_etag}
        assert exc.value.detail["current_version"] == 5
