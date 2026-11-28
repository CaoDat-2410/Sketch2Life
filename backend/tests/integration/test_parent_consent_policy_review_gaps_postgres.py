# ruff: noqa: E501, F811, SIM117, B023
"""Missing PostgreSQL acceptance tests for E5 T-CONSENT1 named in IMPL_REVIEW_E_E5_R1_20261125.md and E5_PROMPT.md."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from test_parent_consent_policy_postgres import (  # noqa: F401
    ISSUER,
    PATH,
    _add_identity,
    consent_directory,
)

from sketch2life.domain.parent_consent_policy import CURRENT_PARENT_CONSENT_POLICY
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ConsentRecordModel,
)

pytestmark = pytest.mark.integration


def _all_counts(session_factory: Any) -> tuple[int | None, int | None, int | None]:
    with session_factory() as db:
        return (
            db.scalar(select(func.count()).select_from(AdultIdentityModel)),
            db.scalar(select(func.count()).select_from(Be1CommandReceiptModel)),
            db.scalar(select(func.count()).select_from(ConsentRecordModel)),
        )


def test_issuer_mismatch_unknown_subject_and_other_roles_are_403_without_writes(
    consent_directory: tuple[TestClient, Any, dict[str, str]],
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance (E5_PROMPT §2 D3 PG denial matrix & zero writes)"""
    client, session_factory, subjects = consent_directory
    token = uuid4().hex[:8]
    extra_subjects = {
        "manager": f"synthetic-t-consent1-manager-{token}",
        "admin": f"synthetic-t-consent1-admin-{token}",
        "pending_parent": f"synthetic-t-consent1-pending-{token}",
    }
    with session_factory.begin() as db:
        _add_identity(db, extra_subjects["manager"], "school_manager")
        _add_identity(db, extra_subjects["admin"], "platform_admin")
        _add_identity(db, extra_subjects["pending_parent"], "parent", state="pending_verification")

    try:
        before = _all_counts(session_factory)

        cases = [
            {"X-Test-Principal": subjects["parent"], "X-Test-Issuer": "synthetic-other-issuer"},
            {"X-Test-Principal": f"synthetic-unknown-{token}", "X-Test-Issuer": ISSUER},
            {"X-Test-Principal": extra_subjects["manager"], "X-Test-Issuer": ISSUER},
            {"X-Test-Principal": extra_subjects["admin"], "X-Test-Issuer": ISSUER},
            {"X-Test-Principal": extra_subjects["pending_parent"], "X-Test-Issuer": ISSUER},
        ]
        for headers in cases:
            response = client.get(PATH, headers=headers)
            assert response.status_code == 403
            assert response.json()["code"] == "ACTION_NOT_ALLOWED"

        assert _all_counts(session_factory) == before
    finally:
        with session_factory.begin() as db:
            db.execute(
                delete(AdultIdentityModel).where(
                    AdultIdentityModel.subject.in_(tuple(extra_subjects.values()))
                )
            )


def test_active_parent_response_headers_and_full_placeholder_payload_on_postgres(
    consent_directory: tuple[TestClient, Any, dict[str, str]],
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance (E5_PROMPT §3 PG headers, policy fields, zero writes)"""
    client, session_factory, subjects = consent_directory
    before = _all_counts(session_factory)

    response = client.get(
        PATH,
        headers={
            "X-Test-Principal": subjects["parent"],
            "X-Test-Issuer": ISSUER,
            "X-Request-ID": "consent-pg-req-1",
        },
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-cache"
    assert response.headers["Vary"] == "Authorization"
    assert response.headers["X-Request-ID"] == "consent-pg-req-1"
    body = response.json()
    assert body["contract"] == "ParentConsentPolicyV1"
    assert body["request_id"] == "consent-pg-req-1"
    policy = body["policy"]
    assert policy["consent_text"] == CURRENT_PARENT_CONSENT_POLICY.consent_text
    assert policy["consent_text_sha256"] == CURRENT_PARENT_CONSENT_POLICY.consent_text_sha256
    assert policy["policy_state"] == "PLACEHOLDER_NOT_APPROVED"
    assert policy["data_origin_scope"] == "SYNTHETIC_TEST"
    assert policy["effective_from"] is None
    assert policy["links"] == []
    assert policy["acceptance_recording"] == "NOT_AVAILABLE"
    assert _all_counts(session_factory) == before
