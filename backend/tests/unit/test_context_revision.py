from __future__ import annotations

import pytest
from sketch2life.infrastructure.assistance.context_revision import (
    CONTEXT_REVISION_SCHEMA_VERSION,
    context_revision,
)


def _payload() -> dict[str, str | int | bool | None]:
    return {
        "schema_version": CONTEXT_REVISION_SCHEMA_VERSION,
        "organization_id": "org-1",
        "class_id": "class-1",
        "session_id": "session-1",
        "session_state": "active",
        "session_run_ref": "run-1",
        "environment": "test",
        "pilot_enabled": True,
        "purpose_ref": "purpose-1",
        "child_id": "child-1",
        "data_origin": "SYNTHETIC_DEV",
        "profile_state": "active",
        "age_months": 60,
        "age_revision": 1,
        "age_source": "SYNTHETIC_FIXTURE",
        "consent_record_ref": None,
        "consent_revision": None,
        "consent_state": None,
        "consent_effective": False,
        "purpose_granted": False,
        "membership_state": "admitted",
        "group_id": "group-1",
        "proof_evidence_id": "proof-1",
        "proof_schema_version": "synthetic-dev-eligibility-v1",
        "proof_data_origin": "SYNTHETIC_DEV",
        "proof_organization_id": "org-1",
        "proof_class_id": "class-1",
        "proof_child_id": "child-1",
        "proof_purpose_ref": "purpose-1",
        "proof_run_ref": "run-1",
        "proof_session_id": "session-1",
        "proof_revocation_revision": 0,
        "proof_issued_at": "2026-01-01T00:00:00Z",
        "proof_expires_at": "2027-01-01T00:00:00Z",
        "proof_revoked_at": None,
        "basis_version": "eligibility-decision-v1",
    }


def test_context_revision_is_stable_and_has_a_fixed_vector() -> None:
    vector = {"a": 1, "b": True, "c": "x", "d": None}
    assert context_revision(vector) == 212040317
    assert context_revision(vector) == context_revision(dict(reversed(list(vector.items()))))


def test_context_revision_is_positive_signed_31_bit_integer() -> None:
    value = context_revision(_payload())
    assert 1 <= value <= 2_147_483_647


def test_every_frozen_fact_input_changes_the_revision_for_the_test_vector() -> None:
    original = _payload()
    baseline = context_revision(original)
    for index, key in enumerate(original):
        changed = dict(original)
        value = changed[key]
        changed[key] = (
            f"changed-{index}"
            if isinstance(value, str)
            else not value
            if isinstance(value, bool)
            else index + 100
        )
        assert context_revision(changed) != baseline, key


@pytest.mark.parametrize(
    "invalid",
    (
        {"a": 1.0},
        {"a": [1]},
        {"a": {"nested": 1}},
        {1: "non-string-key"},
    ),
)
def test_context_revision_rejects_float_and_non_scalar_json_values(
    invalid: dict[object, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        context_revision(invalid)  # type: ignore[arg-type]


def test_context_revision_payload_has_no_session_revision() -> None:
    assert CONTEXT_REVISION_SCHEMA_VERSION == "be1-fact-context-v2"
    assert "session_revision" not in _payload()
    assert "evaluated_at" not in _payload()
