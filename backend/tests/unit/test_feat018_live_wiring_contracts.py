from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas import feat018_live_wiring as wiring
from sketch2life.contracts.schemas.feat018_live_binding import (
    ArtifactIdentityV1,
    DistributionIdentityV1,
    InterpreterIdentityV1,
    ManifestCudaV1,
    ManifestDriverV1,
    ManifestGpuV1,
    ManifestPythonV1,
    SanitizedRuntimeManifestV1,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64


def _host(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "validation_artifact_ref": "fixture:drawing:v1",
        "expected_source_sha256": _SHA_A,
        "observed_source_sha256": _SHA_A,
        "source_matches": True,
        "source_stable": True,
        "admission_outcome": "ADMITTED",
        "admission_reason": None,
        "validation_decision": "PASS",
        "validation_failure_code": None,
        "validator_identity_verified": True,
        "validation_artifact_sha256": _SHA_B,
        "expected_validation_artifact_sha256": None,
        "validation_artifact_matches": None,
        "prompt_hash_verified": True,
        "runtime_config_identity_verified": True,
        "policy_identity_verified": True,
        "accepted": True,
        "failure_codes": (),
    }
    values.update(overrides)
    return values


def _readiness(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "profile_id": "QWEN3_VL_8B_INSTRUCT_BF16_V1",
        "readiness_status": "READY",
        "issue_codes": (),
        "model_revision_state": "VERIFIED",
        "observed_device_class": "NVIDIA_L4",
        "cuda_available": True,
        "bf16_supported": True,
        "dependencies_match": True,
        "accepted": True,
        "failure_codes": (),
    }
    values.update(overrides)
    return values


def _interpreter() -> InterpreterIdentityV1:
    return InterpreterIdentityV1(
        implementation="CPython",
        full_version="3.12.10",
        build_identity="sha256:" + _SHA_C,
        abi_identity="cpython-312",
    )


def _distributions() -> tuple[DistributionIdentityV1, ...]:
    return tuple(
        DistributionIdentityV1(package=name, version=version)
        for name, version in (
            ("accelerate", "1.10.1"),
            ("pydantic", "2.11.7"),
            ("qwen-vl-utils", "0.0.14"),
            ("torch", "2.8.0+cu128"),
            ("transformers", "4.57.6"),
        )
    )


def _modules() -> tuple[ArtifactIdentityV1, ...]:
    return (
        ArtifactIdentityV1(relative_path="backend/src/sketch2life/a.py", sha256=_SHA_A),
        ArtifactIdentityV1(relative_path="backend/src/sketch2life/b/c.py", sha256=_SHA_B),
    )


def _manifest(**overrides: object) -> SanitizedRuntimeManifestV1:
    versions = {item.package: item.version for item in _distributions()}
    values: dict[str, object] = {
        "python": ManifestPythonV1(implementation="CPython", version="3.12.10"),
        "dependencies": tuple(
            DistributionIdentityV1(package=name, version=versions[name])
            for name in ("accelerate", "qwen-vl-utils", "torch", "transformers")
        ),
        "cuda": ManifestCudaV1(available=True, device_count=1, runtime_version="12.8"),
        "driver": ManifestDriverV1(version="570.124.06"),
        "gpu": ManifestGpuV1(device_index=0, sku="NVIDIA_L4", vram_mib=23034, bf16_supported=True),
    }
    values.update(overrides)
    return SanitizedRuntimeManifestV1.model_validate(values)


def _inventory(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "environment": "SESSION",
        "interpreter": _interpreter(),
        "distributions": _distributions(),
        "internal_modules": _modules(),
        "manifest": _manifest(),
        "accepted": True,
        "failure_codes": (),
    }
    values.update(overrides)
    return values


def test_accepted_host_observation_round_trips_through_protected_json() -> None:
    observation = wiring.LiveHostPreflightObservationV1(**_host())
    restored = wiring.LiveHostPreflightObservationV1.model_validate_json(
        observation.model_dump_json()
    )

    assert restored == observation
    assert observation.live_authorized is False
    assert observation.observation_scope == "LIVE_PRODUCER_NOT_AUTHORIZED"
    assert observation.canonical_sha256() == restored.canonical_sha256()


def test_failed_host_observation_accepts_json_failure_arrays() -> None:
    observation = wiring.LiveHostPreflightObservationV1(
        **_host(
            admission_outcome="INVALID_SOURCE",
            admission_reason="CORRUPT_OR_TRUNCATED",
            validation_decision="FAIL",
            validation_failure_code="CORRUPT_OR_TRUNCATED",
            accepted=False,
            failure_codes=("ADMISSION_NOT_ADMITTED", "VALIDATION_NOT_PASS"),
        )
    )
    payload = json.loads(observation.model_dump_json())
    assert payload["failure_codes"] == ["ADMISSION_NOT_ADMITTED", "VALIDATION_NOT_PASS"]

    restored = wiring.LiveHostPreflightObservationV1.model_validate_json(json.dumps(payload))
    assert restored.failure_codes == ("ADMISSION_NOT_ADMITTED", "VALIDATION_NOT_PASS")


@pytest.mark.parametrize(
    "overrides",
    [
        {"failure_codes": ("PROMPT_INVALID",)},
        {"accepted": False},
        {"observed_source_sha256": _SHA_B},
        {"observed_source_sha256": _SHA_B, "source_matches": False},
        {"observed_source_sha256": None, "source_matches": False},
        {"source_stable": False},
        {"admission_reason": "MISSING_SOURCE"},
        {"admission_outcome": "REJECTED"},
        {"admission_outcome": "NOT_RUN", "admission_reason": "MISSING_SOURCE"},
        {"validation_failure_code": "CORRUPT_OR_TRUNCATED"},
        {"validation_decision": "FAIL"},
        {"validation_artifact_sha256": None},
        {"validation_decision": "NOT_RUN"},
        {"validation_artifact_matches": True},
        {"expected_validation_artifact_sha256": _SHA_B, "validation_artifact_matches": False},
        {"expected_validation_artifact_sha256": _SHA_C, "validation_artifact_matches": True},
        {"validator_identity_verified": False},
        {"prompt_hash_verified": False},
        {"runtime_config_identity_verified": False},
        {"policy_identity_verified": False},
        {"live_authorized": True},
        {"live_authorized": 0},
        {"observation_scope": "OFFLINE_SYNTHETIC"},
        {"unexpected": "field"},
        {"failure_codes": ("PROMPT_INVALID", "PROMPT_INVALID"), "accepted": False},
        {"failure_codes": ("NOT_A_CODE",), "accepted": False},
        {"source_matches": 1},
    ],
)
def test_host_observation_rejects_contradictions(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        wiring.LiveHostPreflightObservationV1(**_host(**overrides))


def test_unrun_and_unread_host_observations_are_consistent() -> None:
    observation = wiring.LiveHostPreflightObservationV1(
        **_host(
            observed_source_sha256=None,
            source_matches=False,
            source_stable=None,
            admission_outcome="NOT_RUN",
            validation_decision="NOT_RUN",
            validator_identity_verified=False,
            validation_artifact_sha256=None,
            expected_validation_artifact_sha256=_SHA_B,
            validation_artifact_matches=None,
            accepted=False,
            failure_codes=("FIXTURE_MISSING",),
        )
    )

    assert observation.accepted is False
    with pytest.raises(ValidationError):
        wiring.LiveHostPreflightObservationV1(
            **{**observation.model_dump(), "validator_identity_verified": True}
        )


def test_validation_errors_do_not_echo_private_input() -> None:
    marker = "private-marker-text"
    with pytest.raises(ValidationError) as caught:
        wiring.LiveHostPreflightObservationV1(
            **_host(validation_artifact_ref=f"bad ref {marker}")
        )

    assert marker not in str(caught.value)
    assert marker not in repr(caught.value)


def test_ready_and_not_ready_readiness_observations() -> None:
    ready = wiring.LiveSessionReadinessObservationV1(**_readiness())
    not_ready = wiring.LiveSessionReadinessObservationV1(
        **_readiness(
            readiness_status="NOT_READY",
            issue_codes=("CUDA_NOT_AVAILABLE",),
            cuda_available=False,
            accepted=False,
            failure_codes=("READINESS_NOT_READY",),
        )
    )
    failed = wiring.LiveSessionReadinessObservationV1(
        **_readiness(
            readiness_status="NOT_RUN",
            model_revision_state=None,
            observed_device_class=None,
            cuda_available=None,
            bf16_supported=None,
            dependencies_match=None,
            accepted=False,
            failure_codes=("READINESS_EXCEPTION",),
        )
    )

    for observation in (ready, not_ready, failed):
        assert observation.model_load_performed is False
        assert observation.inference_performed is False
        assert observation.stopped_before == "STAGING"
        assert observation.d4_manifest_revalidation == "NOT_PERFORMED"
        assert type(observation).model_validate_json(observation.model_dump_json()) == observation


@pytest.mark.parametrize(
    "overrides",
    [
        {"issue_codes": ("CUDA_NOT_AVAILABLE",)},
        {
            "readiness_status": "NOT_READY",
            "accepted": False,
            "failure_codes": ("READINESS_NOT_READY",),
        },
        {"model_revision_state": "NOT_VERIFIABLE"},
        {"observed_device_class": "OTHER"},
        {"cuda_available": False},
        {"bf16_supported": False},
        {"dependencies_match": False},
        {"model_revision_state": None},
        {"model_load_performed": True},
        {"model_load_performed": 0},
        {"inference_performed": True},
        {"stopped_before": "DISPATCH"},
        {"d4_manifest_revalidation": "OBSERVED"},
        {"environment": "HOST"},
        {"accepted": False},
        {"failure_codes": ("READINESS_NOT_READY",)},
        {
            "readiness_status": "NOT_READY",
            "issue_codes": ("CUDA_NOT_AVAILABLE", "CUDA_NOT_AVAILABLE"),
            "accepted": False,
            "failure_codes": ("READINESS_NOT_READY",),
        },
        {
            "readiness_status": "NOT_RUN",
            "accepted": False,
            "failure_codes": ("READINESS_EXCEPTION",),
        },
    ],
)
def test_readiness_observation_rejects_contradictions(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        wiring.LiveSessionReadinessObservationV1(**_readiness(**overrides))


def test_accepted_inventory_round_trips_and_has_a_stable_digest() -> None:
    observation = wiring.LiveRuntimeInventoryObservationV1(**_inventory())
    restored = wiring.LiveRuntimeInventoryObservationV1.model_validate_json(
        observation.model_dump_json()
    )

    assert restored == observation
    assert restored.closure_basis == "BOUND_MODULE_LIST"
    assert restored.canonical_sha256() == observation.canonical_sha256()


def test_failed_inventory_carries_no_partial_facts() -> None:
    failed = wiring.LiveRuntimeInventoryObservationV1(
        **_inventory(
            interpreter=None,
            distributions=(),
            internal_modules=(),
            manifest=None,
            accepted=False,
            failure_codes=("MODULE_UNREADABLE",),
        )
    )

    assert failed.accepted is False
    with pytest.raises(ValidationError):
        wiring.LiveRuntimeInventoryObservationV1(
            **_inventory(accepted=False, failure_codes=("MODULE_UNREADABLE",))
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"distributions": tuple(reversed(_distributions()))},
        {"distributions": (*_distributions(), _distributions()[0])},
        {"internal_modules": tuple(reversed(_modules()))},
        {
            "internal_modules": (
                ArtifactIdentityV1(relative_path="backend/tests/unit/test_x.py", sha256=_SHA_A),
            )
        },
        {"internal_modules": ()},
        {"distributions": (), "manifest": None},
        {"interpreter": None},
        {
            "manifest": _manifest(
                python=ManifestPythonV1(implementation="CPython", version="3.12.9")
            )
        },
        {
            "manifest": _manifest(
                dependencies=(
                    DistributionIdentityV1(package="accelerate", version="1.10.1"),
                    DistributionIdentityV1(package="qwen-vl-utils", version="0.0.14"),
                    DistributionIdentityV1(package="torch", version="2.8.1"),
                    DistributionIdentityV1(package="transformers", version="4.57.6"),
                )
            )
        },
        {"closure_basis": "COMPLETE"},
        {"environment": "OTHER"},
        {"failure_codes": ("MODULE_UNREADABLE",)},
    ],
)
def test_inventory_observation_rejects_contradictions(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        wiring.LiveRuntimeInventoryObservationV1(**_inventory(**overrides))


def test_unread_source_stability_rule_is_isolated() -> None:
    # Services ran (REJECTED admission) but the producer's own read failed: only the
    # unread-source stability rule can reject this observation.
    base = _host(
        observed_source_sha256=None,
        source_matches=False,
        source_stable=None,
        admission_outcome="REJECTED",
        admission_reason="NOT_AN_IMAGE",
        validation_decision="NOT_RUN",
        validator_identity_verified=False,
        validation_artifact_sha256=None,
        accepted=False,
        failure_codes=("FIXTURE_UNREADABLE",),
    )
    wiring.LiveHostPreflightObservationV1(**base)
    with pytest.raises(ValidationError):
        wiring.LiveHostPreflightObservationV1(**{**base, "source_stable": True})


def test_stability_requires_a_service_digest_rule_is_isolated() -> None:
    # The source was read and mismatched, so services never ran: only the new
    # services-unrun stability rule can reject a stability claim.
    base = _host(
        observed_source_sha256=_SHA_B,
        source_matches=False,
        source_stable=None,
        admission_outcome="NOT_RUN",
        validation_decision="NOT_RUN",
        validator_identity_verified=False,
        validation_artifact_sha256=None,
        accepted=False,
        failure_codes=("SOURCE_DIGEST_MISMATCH",),
    )
    wiring.LiveHostPreflightObservationV1(**base)
    for stable in (True, False):
        with pytest.raises(ValidationError):
            wiring.LiveHostPreflightObservationV1(**{**base, "source_stable": stable})


def test_received_readiness_fact_rule_is_isolated() -> None:
    # NOT_READY with issues and failure codes: only the "every fact" rule can reject.
    base = _readiness(
        readiness_status="NOT_READY",
        issue_codes=("CUDA_NOT_AVAILABLE",),
        cuda_available=False,
        accepted=False,
        failure_codes=("READINESS_NOT_READY",),
    )
    wiring.LiveSessionReadinessObservationV1(**base)
    for field in (
        "model_revision_state",
        "observed_device_class",
        "cuda_available",
        "bf16_supported",
        "dependencies_match",
    ):
        with pytest.raises(ValidationError):
            wiring.LiveSessionReadinessObservationV1(**{**base, field: None})


def test_extra_fields_are_rejected_by_every_carrier() -> None:
    with pytest.raises(ValidationError):
        wiring.LiveSessionReadinessObservationV1(**_readiness(unexpected="field"))
    with pytest.raises(ValidationError):
        wiring.LiveRuntimeInventoryObservationV1(**_inventory(unexpected="field"))


def test_input_error_has_a_fixed_closed_code_and_message() -> None:
    error = wiring.LiveObservationInputError()

    assert error.code == "INPUT_INVALID"
    assert str(error) == "live observation producer input is invalid"
