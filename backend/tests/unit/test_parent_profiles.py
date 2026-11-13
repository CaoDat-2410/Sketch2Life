"""Framework-neutral Parent profile snapshot rules."""

from __future__ import annotations

import pytest

from sketch2life.contracts.schemas.parent_profiles import PatchParentProfileRequest
from sketch2life.domain.parent_profiles import (
    ParentProfileError,
    ProfileSnapshot,
    ProfileState,
    request_fingerprint,
    validate_snapshot,
)


def test_patch_omission_and_explicit_null_have_the_same_normalized_hash() -> None:
    omitted_request = PatchParentProfileRequest.model_validate(
        {"expected_revision": 1, "display_name": "Mina", "age_months": 72}
    )
    null_request = PatchParentProfileRequest.model_validate(
        {
            "expected_revision": 1,
            "display_name": "Mina",
            "age_months": 72,
            "interests_summary": None,
        }
    )
    omitted = ProfileSnapshot(
        omitted_request.display_name,
        omitted_request.age_months,
        omitted_request.interests_summary,
    )
    explicit_null = ProfileSnapshot(
        null_request.display_name,
        null_request.age_months,
        null_request.interests_summary,
    )

    assert "interests_summary" not in omitted_request.model_fields_set
    assert "interests_summary" in null_request.model_fields_set
    assert omitted.normalized_payload() == explicit_null.normalized_payload()
    assert omitted.revision_hash() == explicit_null.revision_hash()
    assert len(omitted.revision_hash()) == 64


@pytest.mark.parametrize("age_months", [36, 120])
def test_parent_age_bounds_include_endpoints(age_months: int) -> None:
    validate_snapshot(ProfileSnapshot("Mina", age_months, None))


def test_profile_state_exposes_active_and_delete_pending_values() -> None:
    assert ProfileState.ACTIVE.value == "ACTIVE"
    assert ProfileState.DELETE_PENDING.value == "DELETE_PENDING"


@pytest.mark.parametrize("age_months", [35, 121, True])
def test_parent_age_bounds_reject_outside_and_boolean(age_months: int) -> None:
    with pytest.raises(ParentProfileError) as error:
        validate_snapshot(ProfileSnapshot("Mina", age_months, None))

    assert error.value.code == "INVALID_REQUEST"


def test_snapshot_rejects_blank_name_and_overlong_summary() -> None:
    with pytest.raises(ParentProfileError):
        validate_snapshot(ProfileSnapshot("  ", 72, None))
    with pytest.raises(ParentProfileError):
        validate_snapshot(ProfileSnapshot("Mina", 72, "x" * 2001))


def test_request_fingerprint_binds_operation_resource_and_normalized_payload() -> None:
    payload = ProfileSnapshot("Mina", 72, None).normalized_payload()
    first = request_fingerprint(
        operation="patch_profile", resource_scope="profile-a", payload=payload
    )
    same = request_fingerprint(
        operation="patch_profile", resource_scope="profile-a", payload=payload
    )
    other_resource = request_fingerprint(
        operation="patch_profile", resource_scope="profile-b", payload=payload
    )

    assert first == same
    assert first != other_resource
    assert len(first) == 32
