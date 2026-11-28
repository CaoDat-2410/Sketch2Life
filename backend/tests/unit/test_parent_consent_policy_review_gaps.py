# ruff: noqa: E501, F811, SIM117, B023
"""Missing unit tests for E5 T-CONSENT1 named in IMPL_REVIEW_E_E5_R1_20261125.md and E5_PROMPT.md."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.parent_consent_policy import (
    ParentConsentPolicyDetailsV1,
    ParentConsentPolicyV1,
    ParentConsentPurposeV1,
)
from sketch2life.domain.parent_consent_policy import CURRENT_PARENT_CONSENT_POLICY
from sketch2life.interfaces.http.error_envelope import is_conv1_path


def _valid_policy_dict() -> dict[str, object]:
    policy = CURRENT_PARENT_CONSENT_POLICY
    return {
        "purpose_code": policy.purpose_code,
        "policy_version": policy.policy_version,
        "consent_text": policy.consent_text,
        "consent_text_sha256": policy.consent_text_sha256,
        "policy_state": policy.policy_state,
        "data_origin_scope": policy.data_origin_scope,
        "effective_from": policy.effective_from,
        "purposes": [
            {"purpose_code": code, "text_key": key} for code, key in policy.purposes
        ],
        "links": list(policy.links),
        "acceptance_recording": policy.acceptance_recording,
    }


@pytest.mark.parametrize(
    ("model_cls", "payload"),
    [
        (
            ParentConsentPurposeV1,
            {"purpose_code": "SYNTHETIC_TEST_ONLY", "text_key": "k", "extra": 1},
        ),
        (
            ParentConsentPolicyDetailsV1,
            {**_valid_policy_dict(), "policy_state": "APPROVED"},
        ),
        (
            ParentConsentPolicyDetailsV1,
            {**_valid_policy_dict(), "data_origin_scope": "REAL"},
        ),
        (
            ParentConsentPolicyDetailsV1,
            {**_valid_policy_dict(), "acceptance_recording": "AVAILABLE"},
        ),
        (
            ParentConsentPolicyDetailsV1,
            {**_valid_policy_dict(), "extra_field": "forbidden"},
        ),
        (
            ParentConsentPolicyV1,
            {
                "contract": "WrongContractV1",
                "request_id": "req-1",
                "policy": _valid_policy_dict(),
            },
        ),
        (
            ParentConsentPolicyV1,
            {
                "contract": "ParentConsentPolicyV1",
                "request_id": "req-1",
                "policy": _valid_policy_dict(),
                "unexpected": True,
            },
        ),
    ],
)
def test_consent_policy_schemas_forbid_extra_fields_and_invalid_literals(
    model_cls: type[ParentConsentPurposeV1 | ParentConsentPolicyDetailsV1 | ParentConsentPolicyV1],
    payload: dict[str, object],
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance (extra='forbid' & Literal placeholder enforcement)"""
    with pytest.raises(ValidationError):
        model_cls.model_validate(payload)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/v1/parent/consent-policy", True),
        ("/v1/parent/consent-policy/", False),
        ("/v1/parent/consent-policy/accept", False),
        ("/v1/parent/consent-policyX", False),
        ("/v1/parent/profiles", False),
        ("/v1/parent/profiles/profile-1", False),
        ("/api/parent/v1/consent-policy", False),
    ],
)
def test_is_conv1_path_keeps_consent_policy_exact_and_excludes_siblings(
    path: str,
    expected: bool,
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance (E5_PROMPT §2 D2 exact-path CONV-1 boundary)"""
    assert is_conv1_path(path) is expected
