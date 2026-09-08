from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from sketch2life.contracts.schemas.vision import (
    EntityCandidateV1,
    ThemeCandidateV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionProfileId,
    VisionProfileV1,
    VisionProhibitedClaimCategory,
    VisionUnderstandingRequestV1,
    vision_profile_catalog,
    vision_profile_catalog_hash,
    vision_profile_config_hash,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionDependencyPinV1,
    VisionModelProvenanceV1,
    VisionNonPolicyErrorDetailV2,
    VisionProfileCatalogV2,
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    VisionWeightHashAbsenceReason,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)

_V1_PROFILE_HASH = "065cf4e6ff19abca12e95804ba6d35924d54e3fd727d2df9d82a6d3f8ed37c15"
_V1_CATALOG_HASH = "4038274c65f387a8e04a813d31d9295f3da31e08b10aa4f9fec49bb550a900dd"
_V2_PROFILE_HASH = "3082f03f32a1cb26e6f5c25fe73813039460129b0f18a15e647b9f5ff08e3267"
_V2_CATALOG_HASH = "72651b96d2c2259344efcb6fb3349807d42b56079a5422530db09c1590f00947"
_SOURCE_REF = VisionImageReferenceV1(
    artifact_ref="fixture:vision:b1:drawing.bin",
    sha256="a" * 64,
)
_EXECUTED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _text(value: str) -> dict[str, object]:
    return {"value": value, "language": {"status": "NOT_DETERMINED", "tags": []}}


def _failure(**overrides: Any) -> VisionUnderstandingFailureV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "phase-b-b1-contract-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "NOT_EXECUTED",
        "error_code": VisionErrorCode.VISION_PROVIDER_FAILURE,
        "error_detail": VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
        "retryable": False,
        "model_provenance": profile.model_provenance,
    }
    values.update(overrides)
    if overrides.get("model_provenance", object()) is None:
        values.pop("model_provenance", None)
    return VisionUnderstandingFailureV2(**values)


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "phase-b-b1-contract-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "PASSED",
        "entities": (),
        "actions": (),
        "relations": (),
        "themes": (),
        "ambiguous_regions": (),
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash_v2(profile),
        "model_provenance": profile.model_provenance,
    }
    values.update(overrides)
    return VisionUnderstandingSuccessV2(**values)


def test_v1_profile_and_catalog_hashes_are_committed_golden_constants() -> None:
    catalog = vision_profile_catalog()
    profile = catalog.resolve(VisionProfileId.FAKE_DETERMINISTIC_V1)

    assert tuple(VisionProfileId) == (VisionProfileId.FAKE_DETERMINISTIC_V1,)
    assert vision_profile_config_hash(profile) == _V1_PROFILE_HASH
    assert vision_profile_catalog_hash(catalog) == _V1_CATALOG_HASH


def test_v2_catalog_has_one_real_profile_and_fixed_compute_identity() -> None:
    catalog = vision_profile_catalog_v2()
    assert len(catalog.profiles) == 1
    profile = catalog.profiles[0]
    assert profile.profile_id is VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1
    assert profile.compute_profile == "GPU_BF16"
    assert profile.timeout_retry_policy == "NEVER_RETRY"
    assert vision_profile_config_hash_v2(profile) == _V2_PROFILE_HASH
    assert vision_profile_catalog_hash_v2(catalog) == _V2_CATALOG_HASH
    assert vision_profile_catalog_v2() is catalog


def test_v1_and_v2_identity_types_and_hash_functions_are_disjoint() -> None:
    v1_profile = VisionProfileV1(
        profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
        timeout_seconds=30.0,
        adapter_version="deterministic-fixture-vision-adapter-v1",
    )
    with pytest.raises(ValidationError):
        VisionProfileCatalogV2(profiles=(v1_profile,))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        vision_profile_config_hash_v2(v1_profile)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        vision_profile_catalog_hash_v2(vision_profile_catalog())  # type: ignore[arg-type]

    assert set(VisionProfileId).isdisjoint(set(VisionProfileIdV2))
    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV2(
            correlation_id="v1-id-cannot-cross",
            source_image_ref=_SOURCE_REF,
            requested_profile_id="FAKE_DETERMINISTIC_V1",
        )


def test_v2_request_derivation_pairing_and_static_profile_resolution() -> None:
    request = VisionUnderstandingRequestV2(
        correlation_id="valid-v2-request",
        source_image_ref=_SOURCE_REF,
        requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    )
    assert request.contract_name == "VisionUnderstandingRequestV2"
    assert request.contract_version == "2.0"

    processing_ref = VisionImageReferenceV1(
        artifact_ref="fixture:vision:b1:processed.bin", sha256="b" * 64
    )
    valid_derivation = {
        "transform_name": "fixture-transform",
        "transform_config_version": "fixture-transform-v1",
        "source_image_sha256": _SOURCE_REF.sha256,
        "processing_image_sha256": processing_ref.sha256,
    }
    VisionUnderstandingRequestV2(
        correlation_id="valid-v2-derived-request",
        source_image_ref=_SOURCE_REF,
        processing_image_ref=processing_ref,
        derivation_provenance=valid_derivation,
        requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    )
    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV2(
            correlation_id="missing-v2-derivation",
            source_image_ref=_SOURCE_REF,
            processing_image_ref=processing_ref,
            requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        )


def test_model_provenance_requires_one_weight_digest_statement_and_canonical_pins() -> None:
    base: dict[str, Any] = {
        "model_identifier": "org/model",
        "model_revision": "a" * 40,
        "weight_source": "https://example.invalid/model",
        "weight_license": "apache-2.0",
        "dependency_pins": (
            VisionDependencyPinV1(package="transformers", version="4.57.6"),
            VisionDependencyPinV1(package="accelerate", version="1.10.1"),
        ),
    }
    ordered = VisionModelProvenanceV1(
        **base,
        weight_sha256="b" * 64,
    )
    reversed_base = {
        **base,
        "dependency_pins": tuple(reversed(base["dependency_pins"])),
    }
    reversed_pins = VisionModelProvenanceV1(**reversed_base, weight_sha256="b" * 64)
    assert tuple(pin.package for pin in ordered.dependency_pins) == ("accelerate", "transformers")
    assert ordered.model_dump_json() == reversed_pins.model_dump_json()

    with pytest.raises(ValidationError):
        VisionModelProvenanceV1(**base)
    with pytest.raises(ValidationError):
        VisionModelProvenanceV1(
            **base,
            weight_sha256="b" * 64,
            weight_sha256_absence_reason=VisionWeightHashAbsenceReason.SOURCE_DOES_NOT_PUBLISH_A_DIGEST,
        )
    with pytest.raises(ValidationError):
        duplicate_base = {
            **base,
            "dependency_pins": (
                VisionDependencyPinV1(package="accelerate", version="1.10.1"),
                VisionDependencyPinV1(package="accelerate", version="1.10.1"),
            ),
        }
        VisionModelProvenanceV1(
            **duplicate_base,
            weight_sha256="b" * 64,
        )
    with pytest.raises(ValidationError):
        VisionDependencyPinV1(package="transformers", version=">=4.57.0")


@pytest.mark.parametrize("attempt_number", (1, 2))
def test_v2_success_allows_both_inference_attempt_numbers_with_provenance(
    attempt_number: int,
) -> None:
    success = _success(attempt_number=attempt_number)
    assert success.model_provenance is not None
    assert success.policy_execution_state == "PASSED"


@pytest.mark.parametrize(
    "detail",
    (
        VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_NOT_PASSED,
        VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_PROVENANCE_MISSING,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH,
        VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE,
    ),
)
def test_v2_input_failures_are_attempt_zero_and_forbid_model_provenance(
    detail: VisionNonPolicyErrorDetailV2,
) -> None:
    failure = _failure(
        error_code=VisionErrorCode.INPUT_NOT_VALIDATED,
        error_detail=detail,
        attempt_number=0,
        policy_execution_state="NOT_EXECUTED",
        retryable=False,
        model_provenance=None,
    )
    assert failure.model_provenance is None
    assert "model_provenance" not in failure.model_dump(mode="json")


@pytest.mark.parametrize(
    ("error_code", "detail"),
    (
        (VisionErrorCode.VISION_MODEL_UNAVAILABLE, VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED),
        (VisionErrorCode.VISION_MODEL_UNAVAILABLE, VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE),
    ),
)
def test_v2_model_unavailable_is_one_attempt_and_carries_provenance(
    error_code: VisionErrorCode, detail: VisionNonPolicyErrorDetailV2
) -> None:
    failure = _failure(error_code=error_code, error_detail=detail, attempt_number=1)
    assert failure.model_provenance is not None


@pytest.mark.parametrize("attempt_number", (1, 2))
def test_v2_timeout_is_not_retryable_but_can_be_observed_on_either_attempt(
    attempt_number: int,
) -> None:
    failure = _failure(
        error_code=VisionErrorCode.VISION_TIMEOUT,
        error_detail=VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED,
        attempt_number=attempt_number,
    )
    assert failure.retryable is False
    assert failure.model_provenance is not None


def test_v2_retry_trace_rows_are_constructible() -> None:
    transient = _failure(
        error_detail=VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE,
        attempt_number=2,
        retryable=True,
    )
    permanent = _failure(
        error_detail=VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
        attempt_number=2,
    )
    timeout = _failure(
        error_code=VisionErrorCode.VISION_TIMEOUT,
        error_detail=VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED,
        attempt_number=2,
    )
    schema_invalid = _failure(
        error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
        error_detail=VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
        attempt_number=2,
        repair_attempted=True,
    )
    policy_blocked = _failure(
        error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
        error_detail=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
        policy_execution_state="BLOCKED",
        attempt_number=2,
    )
    assert transient.retryable is True
    assert permanent.retryable is False
    assert timeout.error_code is VisionErrorCode.VISION_TIMEOUT
    assert schema_invalid.repair_attempted is True
    assert policy_blocked.policy_execution_state == "BLOCKED"


@pytest.mark.parametrize("detail", tuple(VisionNonPolicyErrorDetailV2))
def test_v2_model_reached_failure_details_carry_provenance_when_valid(
    detail: VisionNonPolicyErrorDetailV2,
) -> None:
    if detail in {
        VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_NOT_PASSED,
        VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_PROVENANCE_MISSING,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH,
        VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE,
    }:
        pytest.skip("input details are covered by the attempt-zero row")
    assert _failure(
        error_code=(
            VisionErrorCode.VISION_MODEL_UNAVAILABLE
            if detail
            in {
                VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED,
                VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE,
            }
            else VisionErrorCode.VISION_TIMEOUT
            if detail is VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED
            else VisionErrorCode.VISION_SCHEMA_INVALID
            if detail in {
                VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
                VisionNonPolicyErrorDetailV2.DUPLICATE_OBSERVATION_ID,
                VisionNonPolicyErrorDetailV2.REFERENCE_INTEGRITY_VIOLATION,
            }
            else VisionErrorCode.VISION_PROVIDER_FAILURE
        ),
        error_detail=detail,
        attempt_number=2 if detail is VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE else 1,
        retryable=detail is VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE,
        repair_attempted=False,
    ).model_provenance is not None


@pytest.mark.parametrize(
    "overrides",
    (
        {
            "error_code": VisionErrorCode.INPUT_NOT_VALIDATED,
            "error_detail": VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
            "attempt_number": 1,
        },
        {
            "error_code": VisionErrorCode.VISION_MODEL_UNAVAILABLE,
            "error_detail": VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED,
            "attempt_number": 2,
        },
        {
            "error_code": VisionErrorCode.VISION_TIMEOUT,
            "error_detail": VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED,
            "attempt_number": 1,
            "retryable": True,
        },
        {
            "error_code": VisionErrorCode.VISION_PROVIDER_FAILURE,
            "error_detail": VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE,
            "attempt_number": 1,
            "retryable": True,
        },
        {
            "error_code": VisionErrorCode.VISION_SCHEMA_INVALID,
            "error_detail": VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
            "attempt_number": 0,
        },
        {
            "error_code": VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
            "error_detail": VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
            "policy_execution_state": "NOT_EXECUTED",
        },
    ),
)
def test_invalid_v2_matrix_rows_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _failure(**overrides)


def test_v2_provenance_is_required_on_all_policy_and_runtime_reached_rows() -> None:
    for category in VisionProhibitedClaimCategory:
        blocked = _failure(
            error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
            error_detail=category,
            policy_execution_state="BLOCKED",
        )
        assert blocked.model_provenance is not None
    for error_code, detail in (
        (VisionErrorCode.VISION_MODEL_UNAVAILABLE, VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED),
        (VisionErrorCode.VISION_TIMEOUT, VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED),
        (
            VisionErrorCode.VISION_PROVIDER_FAILURE,
            VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
        ),
        (VisionErrorCode.VISION_SCHEMA_INVALID, VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED),
    ):
        assert _failure(error_code=error_code, error_detail=detail).model_provenance is not None


def test_v2_strict_schema_rejects_extra_fields_and_missing_collections() -> None:
    payload = _success().model_dump(mode="json")
    payload["unexpected"] = "not allowed"
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV2.model_validate(payload)

    missing = _success().model_dump(mode="json")
    del missing["themes"]
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV2.model_validate(missing)

    nested = _success(
        entities=(
            EntityCandidateV1(
                observation_id="entity-a",
                label=_text("a fox"),
                confidence=None,
            ),
        )
    ).model_dump(mode="json")
    nested["entities"][0]["unexpected"] = "not allowed"
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV2.model_validate(nested)


def test_v2_duplicate_and_reference_integrity_errors_are_structural() -> None:
    entity = EntityCandidateV1(
        observation_id="shared-id",
        label=_text("a fox"),
        confidence=None,
    )
    theme = ThemeCandidateV1(
        observation_id="shared-id",
        label=_text("nature"),
        evidence_refs=("shared-id",),
        confidence=None,
    )
    with pytest.raises(ValidationError, match="DUPLICATE_OBSERVATION_ID"):
        _success(entities=(entity,), themes=(theme,))

    with pytest.raises(ValidationError, match="REFERENCE_INTEGRITY_VIOLATION"):
        _success(
            entities=(entity,),
            themes=(
                ThemeCandidateV1(
                    observation_id="theme-a",
                    label=_text("nature"),
                    evidence_refs=("missing-id",),
                    confidence=None,
                ),
            ),
        )


def test_v2_result_union_round_trips_success_and_failure_without_raw_fields() -> None:
    success = _success()
    failure = _failure(
        error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
        error_detail=VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
        repair_attempted=True,
    )
    parsed_success = TypeAdapter(VisionUnderstandingResultV2).validate_python(
        success.model_dump(mode="json")
    )
    parsed_failure = TypeAdapter(VisionUnderstandingResultV2).validate_python(
        failure.model_dump(mode="json")
    )
    assert isinstance(parsed_success, VisionUnderstandingSuccessV2)
    assert isinstance(parsed_failure, VisionUnderstandingFailureV2)
    assert "raw_output" not in success.model_dump(mode="json")
    assert "raw_output" not in failure.model_dump(mode="json")


def test_v2_dependency_pins_and_profile_hash_change_when_configuration_changes() -> None:
    profile = vision_profile_catalog_v2().profiles[0]
    changed = profile.model_copy(update={"adapter_version": "qwen3-vl-local-adapter-v2-test"})
    assert vision_profile_config_hash_v2(changed) != vision_profile_config_hash_v2(profile)
    changed_catalog = VisionProfileCatalogV2(profiles=(changed,))
    assert vision_profile_catalog_hash_v2(changed_catalog) != vision_profile_catalog_hash_v2(
        vision_profile_catalog_v2()
    )


def test_v1_request_still_accepts_only_the_original_fake_profile() -> None:
    request = VisionUnderstandingRequestV1(
        correlation_id="v1-regression",
        source_image_ref=_SOURCE_REF,
        requested_profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
    )
    assert request.requested_profile_id is VisionProfileId.FAKE_DETERMINISTIC_V1
