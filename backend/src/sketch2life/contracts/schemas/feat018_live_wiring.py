"""Additive observation carriers for FEAT-018 A-LIVE-W1 live fact producers.

Each model records what one explicitly invoked producer observed. None of them is an
offline synthetic fixture, a live authorization, Stage-4 evidence or remote cleanup
proof. Live binding, staging, budgets and live enabling remain separate later work.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, ValidationInfo, field_validator, model_validator

from sketch2life.contracts.schemas.feat018_live_binding import (
    ArtifactIdentityV1,
    DistributionIdentityV1,
    InterpreterIdentityV1,
    SafeCode,
    SafeIdentity,
    SanitizedRuntimeManifestV1,
    Sha256,
    _FrozenContract,
)

LIVE_OBSERVATION_SCOPE: Literal["LIVE_PRODUCER_NOT_AUTHORIZED"] = (
    "LIVE_PRODUCER_NOT_AUTHORIZED"
)
INTERNAL_MODULE_PREFIX = "backend/src/sketch2life/"
MAX_FAILURE_CODES = 16
MAX_INVENTORY_ENTRIES = 512
MAX_READINESS_ISSUES = 32

LiveObservationScope = Literal["LIVE_PRODUCER_NOT_AUTHORIZED"]
AdmissionOutcomeValue = Literal[
    "ADMITTED", "REJECTED", "UNSUPPORTED", "INVALID_SOURCE", "PROCESSING_FAILURE", "NOT_RUN"
]
ValidationDecisionValue = Literal["PASS", "FAIL", "NOT_RUN"]
ReadinessStatusValue = Literal["READY", "NOT_READY", "NOT_RUN"]
RevisionStateValue = Literal["VERIFIED", "NOT_VERIFIABLE", "MISMATCH"]
DeviceClassValue = Literal["NVIDIA_L4", "OTHER", "NOT_AVAILABLE"]
InventoryEnvironment = Literal["HOST", "SESSION"]

HostPreflightFailureCode = Literal[
    "FIXTURE_MISSING",
    "FIXTURE_UNREADABLE",
    "FIXTURE_TOO_LARGE",
    "SOURCE_DIGEST_MISMATCH",
    "SOURCE_UNSTABLE",
    "ADMISSION_NOT_ADMITTED",
    "ADMISSION_EXCEPTION",
    "VALIDATION_NOT_PASS",
    "VALIDATION_EXCEPTION",
    "VALIDATION_IDENTITY_MISMATCH",
    "VALIDATION_ARTIFACT_MISMATCH",
    "PROMPT_INVALID",
    "PROMPT_HASH_MISMATCH",
    "RUNTIME_CONFIG_IDENTITY_MISMATCH",
    "POLICY_IDENTITY_MISMATCH",
]
SessionReadinessFailureCode = Literal[
    "READINESS_NOT_READY",
    "READINESS_EXCEPTION",
    "READINESS_PROFILE_MISMATCH",
]
RuntimeInventoryFailureCode = Literal[
    "INTERPRETER_UNKNOWN",
    "DISTRIBUTION_INVALID",
    "DISTRIBUTION_DUPLICATE",
    "DISTRIBUTION_LIMIT",
    "MODULE_UNREADABLE",
    "MODULE_TOO_LARGE",
    "MODULE_UNSAFE",
    "MANIFEST_INVALID",
]


class LiveObservationInputError(ValueError):
    """Structural producer input was rejected before any read; the message is fixed."""

    code: Literal["INPUT_INVALID"]

    def __init__(self) -> None:
        super().__init__("live observation producer input is invalid")
        self.code = "INPUT_INVALID"


# mypy cannot see that the shared base's metaclass derives from type(BaseModel) at runtime.
class _LiveObservation(_FrozenContract):  # type: ignore[metaclass]
    observation_scope: LiveObservationScope = LIVE_OBSERVATION_SCOPE
    live_authorized: Literal[False] = False

    @field_validator("failure_codes", mode="before", check_fields=False)
    @classmethod
    def validate_failure_code_array(cls, value: object, info: ValidationInfo) -> object:
        # The shared wrap validator materializes JSON arrays as lists before strict tuples.
        if info.mode == "json" and isinstance(value, list):
            return tuple(value)
        return value

    @field_validator(
        "model_load_performed", "inference_performed", mode="before", check_fields=False
    )
    @classmethod
    def validate_negative_fact_type(cls, value: object) -> object:
        # Literal[False] can otherwise accept the integer 0.
        if type(value) is not bool:
            raise ValueError("negative execution facts require exact boolean values")
        return value

    @staticmethod
    def _check_unique(values: tuple[str, ...], label: str) -> None:
        if len(set(values)) != len(values):
            raise ValueError(f"duplicate {label}")


class LiveHostPreflightObservationV1(_LiveObservation):
    """Host preflight facts observed for one fixture; not a preflight approval."""

    contract_version: Literal["FEAT018-LIVE-HOST-PREFLIGHT-OBSERVATION-V1"] = (
        "FEAT018-LIVE-HOST-PREFLIGHT-OBSERVATION-V1"
    )
    validation_artifact_ref: SafeIdentity
    expected_source_sha256: Sha256
    observed_source_sha256: Sha256 | None
    source_matches: bool
    source_stable: bool | None
    admission_outcome: AdmissionOutcomeValue
    admission_reason: SafeCode | None
    validation_decision: ValidationDecisionValue
    validation_failure_code: SafeCode | None
    validator_identity_verified: bool
    validation_artifact_sha256: Sha256 | None
    expected_validation_artifact_sha256: Sha256 | None
    validation_artifact_matches: bool | None
    prompt_hash_verified: bool
    runtime_config_identity_verified: bool
    policy_identity_verified: bool
    accepted: bool
    failure_codes: Annotated[
        tuple[HostPreflightFailureCode, ...], Field(max_length=MAX_FAILURE_CODES)
    ]

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        self._check_unique(self.failure_codes, "host preflight failure codes")
        observed = self.observed_source_sha256
        expected_source = self.expected_source_sha256
        if self.source_matches != (observed is not None and observed == expected_source):
            raise ValueError("source match flag contradicts the observed digest")
        if observed is None and self.source_stable is not None:
            raise ValueError("an unread source cannot carry a stability fact")
        services_unrun = (
            self.admission_outcome == "NOT_RUN" and self.validation_decision == "NOT_RUN"
        )
        if services_unrun and self.source_stable is not None:
            raise ValueError("stability requires a compared service digest")
        if (self.admission_outcome in ("ADMITTED", "NOT_RUN")) != (self.admission_reason is None):
            raise ValueError("an admission reason must accompany exactly a rejected outcome")
        if self.validation_decision == "NOT_RUN":
            if (
                self.validation_failure_code is not None
                or self.validation_artifact_sha256 is not None
                or self.validator_identity_verified
            ):
                raise ValueError("unrun validation cannot carry validation facts")
        else:
            if (self.validation_decision == "FAIL") != (self.validation_failure_code is not None):
                raise ValueError("a validation failure code must accompany exactly FAIL")
            if self.validation_artifact_sha256 is None:
                raise ValueError("a received validation result has an artifact digest")
        expected = self.expected_validation_artifact_sha256
        if expected is None or self.validation_artifact_sha256 is None:
            if self.validation_artifact_matches is not None:
                raise ValueError("an artifact comparison requires both digests")
        elif self.validation_artifact_matches != (self.validation_artifact_sha256 == expected):
            raise ValueError("artifact match flag contradicts the digests")
        if self.accepted == bool(self.failure_codes):
            raise ValueError("acceptance must be exactly the absence of failure codes")
        if self.accepted and not (
            self.source_matches
            and self.source_stable is True
            and self.admission_outcome == "ADMITTED"
            and self.validation_decision == "PASS"
            and self.validator_identity_verified
            and self.validation_artifact_matches is not False
            and self.prompt_hash_verified
            and self.runtime_config_identity_verified
            and self.policy_identity_verified
        ):
            raise ValueError("an accepted host preflight requires every observed check")
        return self


class LiveSessionReadinessObservationV1(_LiveObservation):
    """No-model-load readiness facts.

    The D4 sanitized-manifest digest is not revalidated and no fixture is staged; the
    producer always stops before STAGING.
    """

    contract_version: Literal["FEAT018-LIVE-SESSION-READINESS-OBSERVATION-V1"] = (
        "FEAT018-LIVE-SESSION-READINESS-OBSERVATION-V1"
    )
    environment: Literal["SESSION"] = "SESSION"
    profile_id: SafeIdentity
    readiness_status: ReadinessStatusValue
    issue_codes: Annotated[tuple[SafeCode, ...], Field(max_length=MAX_READINESS_ISSUES)]
    model_revision_state: RevisionStateValue | None
    observed_device_class: DeviceClassValue | None
    cuda_available: bool | None
    bf16_supported: bool | None
    dependencies_match: bool | None
    model_load_performed: Literal[False] = False
    inference_performed: Literal[False] = False
    d4_manifest_revalidation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    stopped_before: Literal["STAGING"] = "STAGING"
    accepted: bool
    failure_codes: Annotated[
        tuple[SessionReadinessFailureCode, ...], Field(max_length=MAX_FAILURE_CODES)
    ]

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        self._check_unique(self.failure_codes, "readiness failure codes")
        self._check_unique(self.issue_codes, "readiness issue codes")
        facts = (
            self.model_revision_state,
            self.observed_device_class,
            self.cuda_available,
            self.bf16_supported,
            self.dependencies_match,
        )
        if self.readiness_status == "NOT_RUN":
            if self.issue_codes or any(value is not None for value in facts):
                raise ValueError("unrun readiness cannot carry readiness facts")
        else:
            if any(value is None for value in facts):
                raise ValueError("a received readiness result requires every readiness fact")
            if (self.readiness_status == "READY") == bool(self.issue_codes):
                raise ValueError("readiness issues must accompany exactly NOT_READY")
            if self.readiness_status == "READY" and not (
                self.model_revision_state == "VERIFIED"
                and self.observed_device_class == "NVIDIA_L4"
                and self.cuda_available
                and self.bf16_supported
                and self.dependencies_match
            ):
                raise ValueError("READY requires a verified revision, device and dependency pins")
        if self.accepted == bool(self.failure_codes):
            raise ValueError("acceptance must be exactly the absence of failure codes")
        if self.accepted and self.readiness_status != "READY":
            raise ValueError("accepted readiness requires READY")
        return self


class LiveRuntimeInventoryObservationV1(_LiveObservation):
    """Measured interpreter, distributions and an explicitly bound module list.

    The closure basis is always the supplied list, so the observation never claims a
    complete runtime closure on its own. A failed observation carries no partial facts.
    """

    contract_version: Literal["FEAT018-LIVE-RUNTIME-INVENTORY-OBSERVATION-V1"] = (
        "FEAT018-LIVE-RUNTIME-INVENTORY-OBSERVATION-V1"
    )
    environment: InventoryEnvironment
    closure_basis: Literal["BOUND_MODULE_LIST"] = "BOUND_MODULE_LIST"
    interpreter: InterpreterIdentityV1 | None
    distributions: Annotated[
        tuple[DistributionIdentityV1, ...], Field(max_length=MAX_INVENTORY_ENTRIES)
    ]
    internal_modules: Annotated[
        tuple[ArtifactIdentityV1, ...], Field(max_length=MAX_INVENTORY_ENTRIES)
    ]
    manifest: SanitizedRuntimeManifestV1 | None
    accepted: bool
    failure_codes: Annotated[
        tuple[RuntimeInventoryFailureCode, ...], Field(max_length=MAX_FAILURE_CODES)
    ]

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        self._check_unique(self.failure_codes, "inventory failure codes")
        packages = tuple(item.package for item in self.distributions)
        paths = tuple(item.relative_path for item in self.internal_modules)
        if packages != tuple(sorted(set(packages))) or paths != tuple(sorted(set(paths))):
            raise ValueError("inventory entries must be unique and canonically ordered")
        if any(not path.startswith(INTERNAL_MODULE_PREFIX) for path in paths):
            raise ValueError("the bound closure must contain source modules only")
        if self.accepted == bool(self.failure_codes):
            raise ValueError("acceptance must be exactly the absence of failure codes")
        if self.accepted:
            if self.interpreter is None or not self.distributions or not self.internal_modules:
                raise ValueError("an accepted inventory requires every measured section")
        elif (
            self.interpreter is not None
            or self.distributions
            or self.internal_modules
            or self.manifest is not None
        ):
            raise ValueError("a failed inventory must not carry partial facts")
        if self.manifest is not None and self.interpreter is not None:
            if (
                self.manifest.python.implementation != self.interpreter.implementation
                or self.manifest.python.version != self.interpreter.full_version
            ):
                raise ValueError("the manifest interpreter differs from the inventory")
            versions = {item.package: item.version for item in self.distributions}
            if any(
                versions.get(item.package) != item.version
                for item in self.manifest.dependencies
            ):
                raise ValueError("the manifest dependencies differ from the inventory")
        return self


__all__ = [
    "INTERNAL_MODULE_PREFIX",
    "LIVE_OBSERVATION_SCOPE",
    "MAX_FAILURE_CODES",
    "MAX_INVENTORY_ENTRIES",
    "MAX_READINESS_ISSUES",
    "AdmissionOutcomeValue",
    "DeviceClassValue",
    "HostPreflightFailureCode",
    "InventoryEnvironment",
    "LiveHostPreflightObservationV1",
    "LiveObservationInputError",
    "LiveRuntimeInventoryObservationV1",
    "LiveSessionReadinessObservationV1",
    "ReadinessStatusValue",
    "RevisionStateValue",
    "RuntimeInventoryFailureCode",
    "SessionReadinessFailureCode",
    "ValidationDecisionValue",
]
