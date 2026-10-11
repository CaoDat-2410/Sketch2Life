"""Strict synthetic carriers for the FEAT-018 binding foundation.

These contracts describe received fixture observations, not provider proof or
owner approval.  In particular, matching identities and observation labels
cannot authorize a live run or establish remote cleanup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Annotated, Literal, Self, get_args

from pydantic import (
    BaseModel, ConfigDict, Field, GetCoreSchemaHandler, ValidationError, ValidationInfo,
    field_validator, model_validator,
)
from pydantic_core import ErrorType, PydanticCustomError, PydanticSerializationError, core_schema


Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
GitObjectId = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
SafeIdentity = Annotated[
    str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
]
SafeCode = Annotated[
    str, Field(min_length=1, max_length=96, pattern=r"^[A-Z][A-Z0-9_]*$")
]
SafeVersion = Annotated[
    str, Field(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9][A-Za-z0-9.+_-]*$")
]
PositiveSeconds = Annotated[float, Field(gt=0, le=86_400, allow_inf_nan=False)]
NonnegativeNumber = Annotated[float, Field(ge=0, le=86_400, allow_inf_nan=False)]
ObservationState = Literal["OBSERVED", "UNKNOWN", "NOT_REACHED"]
# D4/staging/runtime only: a received value that differs from the fixture expectation.
PhaseObservationState = Literal["OBSERVED", "OBSERVED_MISMATCH", "UNKNOWN", "NOT_REACHED"]
_RECEIVED_STATES = frozenset({"OBSERVED", "OBSERVED_MISMATCH"})
_SAFE_VALIDATION_ERROR_TYPES = frozenset(get_args(ErrorType))
_VALIDATION_ERROR_TITLE = "FEAT018OfflineContract"
_VALIDATION_ERROR_MESSAGE = "offline contract validation failed"
_SERIALIZATION_ERROR_MESSAGE = "offline contract serialization failed"


def _check_received_identity(state: str, matches: bool, label: str) -> None:
    if state == "OBSERVED" and not matches:
        raise ValueError(f"received {label} identities do not match fixture expectations")
    if state == "OBSERVED_MISMATCH" and matches:
        raise ValueError(f"a {label} mismatch claim requires a differing received identity")


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_key(item, key) for item in value)
    return False


def _without_validation_input(error: ValidationError) -> ValidationError:
    # Titles, custom error codes and formatted messages can also contain provenance.
    # Preserve counts and only trusted built-in codes; every rendered string is fixed.
    return ValidationError.from_exception_data(
        _VALIDATION_ERROR_TITLE,
        [{"type": PydanticCustomError(
            detail["type"] if detail["type"] in _SAFE_VALIDATION_ERROR_TYPES else "value_error",
            _VALIDATION_ERROR_MESSAGE,
          ),
          "loc": (), "input": None}
         for detail in error.errors(include_url=False, include_input=False, include_context=False)],
        hide_input=True,
    )


class _PrivateInputContractMeta(type(BaseModel)):
    def __call__(cls, *args: object, **kwargs: object) -> object:
        try:
            return super().__call__(*args, **kwargs)
        except ValidationError as error:
            raise _without_validation_input(error) from None


class _FrozenContract(BaseModel, metaclass=_PrivateInputContractMeta):
    model_config = ConfigDict(
        frozen=True, extra="forbid", strict=True, allow_inf_nan=False,
        hide_input_in_errors=True, revalidate_instances="always",
        title=_VALIDATION_ERROR_TITLE,
    )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[BaseModel], handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        # Core/TypeAdapter rebuild error titles from model config after our wrapper.
        cls.model_config["title"] = _VALIDATION_ERROR_TITLE

        def validate_redacted(
            value: object, validator: core_schema.ValidatorFunctionWrapHandler,
        ) -> object:
            try:
                return validator(value)
            except ValidationError as error:
                raise _without_validation_input(error) from None

        # Wrap the complete schema, including subclass after validators, so
        # TypeAdapter and nested validation share the private-input boundary.
        return core_schema.no_info_wrap_validator_function(
            validate_redacted, handler(source),
        )

    @classmethod
    def model_validate(cls, *args: object, **kwargs: object) -> Self:
        try:
            return super().model_validate(*args, **kwargs)
        except ValidationError as error:
            raise _without_validation_input(error) from None

    @classmethod
    def model_validate_json(cls, *args: object, **kwargs: object) -> Self:
        try:
            return super().model_validate_json(*args, **kwargs)
        except ValidationError as error:
            raise _without_validation_input(error) from None

    @classmethod
    def model_validate_strings(cls, *args: object, **kwargs: object) -> Self:
        try:
            return super().model_validate_strings(*args, **kwargs)
        except ValidationError as error:
            raise _without_validation_input(error) from None

    def __setattr__(self, name: str, value: object) -> None:
        try:
            super().__setattr__(name, value)
        except ValidationError as error:
            raise _without_validation_input(error) from None

    def __delattr__(self, name: str) -> None:
        try:
            super().__delattr__(name)
        except ValidationError as error:
            raise _without_validation_input(error) from None

    def model_dump(self, *args: object, **kwargs: object) -> dict[str, object]:
        try:
            return super().model_dump(*args, **kwargs)
        except PydanticSerializationError:
            raise ValueError(_SERIALIZATION_ERROR_MESSAGE) from None

    def model_dump_json(self, *args: object, **kwargs: object) -> str:
        try:
            return super().model_dump_json(*args, **kwargs)
        except PydanticSerializationError:
            raise ValueError(_SERIALIZATION_ERROR_MESSAGE) from None

    @field_validator(
        "distributions", "internal_modules", "dependencies",
        "host_source_identities", "issue_codes", "session_source_identities",
        mode="before", check_fields=False,
    )
    @classmethod
    def validate_json_tuple_inputs(cls, value: object, info: ValidationInfo) -> object:
        # Wrap handlers materialize JSON arrays as lists before strict tuple checks.
        if info.mode == "json" and isinstance(value, list):
            return tuple(value)
        return value

    @field_validator(
        "live_authorized", "live_cleanup_proven", "gate_a_required",
        mode="before", check_fields=False,
    )
    @classmethod
    def validate_literal_bool_type(cls, value: object) -> object:
        # Pydantic Literal[False]/Literal[True] can otherwise accept integer 0/1.
        if value is not None and type(value) is not bool:
            raise ValueError("literal boolean facts require exact boolean values")
        return value

    @field_validator("per_attempt_timeout_seconds", mode="before", check_fields=False)
    @classmethod
    def validate_attempt_deadline_type(cls, value: object) -> object:
        if type(value) is not float:
            raise ValueError("attempt deadline requires the explicit float 120.0")
        return value

    def revalidated(self) -> Self:
        """Recheck even instances built using Pydantic's unchecked APIs."""
        if set(self.__dict__) != set(type(self).model_fields):
            raise ValueError("offline carrier contains undeclared or missing fields")
        checked = type(self).model_validate(self)
        return type(self).model_validate_json(checked.model_dump_json(warnings="error"))

    def canonical_bytes(self) -> bytes:
        checked = self.revalidated()
        return json.dumps(
            checked.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    def canonical_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


class ArtifactIdentityV1(_FrozenContract):
    relative_path: Annotated[
        str,
        Field(
            min_length=1,
            max_length=256,
            pattern=r"^backend/(?:src/sketch2life|tests/unit)/[A-Za-z0-9_/]+\.py$",
        ),
    ]
    sha256: Sha256
    git_blob_sha1: GitObjectId | None = None


class DistributionIdentityV1(_FrozenContract):
    package: Annotated[
        str, Field(min_length=1, max_length=96, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    ]
    version: SafeVersion


class InterpreterIdentityV1(_FrozenContract):
    implementation: Literal["CPython", "PyPy"]
    full_version: SafeVersion
    build_identity: SafeIdentity
    abi_identity: SafeIdentity


class RuntimeEnvironmentInventoryV1(_FrozenContract):
    contract_version: Literal["P2T2-OFFLINE-ENVIRONMENT-INVENTORY-V1"] = (
        "P2T2-OFFLINE-ENVIRONMENT-INVENTORY-V1"
    )
    proof_scope: Literal["OFFLINE_SYNTHETIC"] = "OFFLINE_SYNTHETIC"
    environment: Literal["HOST", "SESSION"]
    interpreter: InterpreterIdentityV1
    distributions: Annotated[tuple[DistributionIdentityV1, ...], Field(min_length=1, max_length=512)]
    internal_modules: Annotated[tuple[ArtifactIdentityV1, ...], Field(min_length=1, max_length=512)]
    inventory_scope: Literal["DECLARED_COMPLETE_SYNTHETIC"] = (
        "DECLARED_COMPLETE_SYNTHETIC"
    )

    @model_validator(mode="after")
    def validate_inventory(self) -> Self:
        packages = tuple(item.package for item in self.distributions)
        paths = tuple(item.relative_path for item in self.internal_modules)
        if packages != tuple(sorted(set(packages))) or paths != tuple(sorted(set(paths))):
            raise ValueError("inventory entries must be unique and canonically ordered")
        if any(not item.relative_path.startswith("backend/src/sketch2life/") for item in self.internal_modules):
            raise ValueError("runtime closure must contain source modules only")
        return self


class ManifestPythonV1(_FrozenContract):
    implementation: Literal["CPython", "PyPy"]
    version: SafeVersion


class ManifestCudaV1(_FrozenContract):
    available: bool
    device_count: Annotated[int, Field(ge=0, le=64)]
    runtime_version: Annotated[str, Field(pattern=r"^(?:[0-9]+(?:\.[0-9]+){0,3}|NOT_AVAILABLE)$", max_length=32)]


class ManifestDriverV1(_FrozenContract):
    version: Annotated[str, Field(pattern=r"^(?:[0-9]+(?:\.[0-9]+){0,3}|NOT_AVAILABLE)$", max_length=32)]


class ManifestGpuV1(_FrozenContract):
    device_index: Annotated[int, Field(ge=0, le=63)]
    sku: Literal["NVIDIA_L4", "NVIDIA L4", "OTHER", "NOT_AVAILABLE"]
    vram_mib: Annotated[int, Field(ge=0, le=1_048_576)]
    bf16_supported: bool


class SanitizedRuntimeManifestV1(_FrozenContract):
    """The Section 3A allowlist; complete inventories are a different object."""

    manifest_version: Literal["P2T2-LIVE-RUNTIME-MANIFEST-V1"] = (
        "P2T2-LIVE-RUNTIME-MANIFEST-V1"
    )
    python: ManifestPythonV1
    dependencies: Annotated[tuple[DistributionIdentityV1, ...], Field(min_length=4, max_length=4)]
    cuda: ManifestCudaV1
    driver: ManifestDriverV1
    gpu: ManifestGpuV1

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        if tuple(item.package for item in self.dependencies) != (
            "accelerate", "qwen-vl-utils", "torch", "transformers"
        ):
            raise ValueError("manifest dependencies must match the ordered allowlist")
        if self.cuda.device_count and self.gpu.device_index >= self.cuda.device_count:
            raise ValueError("manifest device index exceeds device count")
        if not self.cuda.available and self.cuda.device_count:
            raise ValueError("unavailable CUDA must not report visible devices")
        return self


class BindingInputIdentityV1(_FrozenContract):
    """Fixture-selected expectations; none of these fields is owner approval."""

    reviewed_runtime_code_commit: GitObjectId
    approval_record_commit: GitObjectId
    correlation_id: SafeIdentity
    fixture_id: SafeIdentity
    source_sha256: Sha256
    validation_artifact_ref: SafeIdentity
    validation_artifact_sha256: Sha256
    validator_identity: SafeIdentity
    validator_policy_version: SafeIdentity
    model_identifier: Literal["Qwen/Qwen3-VL-8B-Instruct"]
    model_revision: GitObjectId
    profile_id: Literal["QWEN3_VL_8B_INSTRUCT_BF16_V1"]
    adapter_version: SafeIdentity
    profile_config_hash: Sha256
    profile_catalog_hash: Sha256
    # Canonical typed fixture-config identity, not an environment-file digest.
    runtime_config_identity_sha256: Sha256
    prompt_protocol_id: SafeIdentity
    prompt_source_identity: SafeIdentity
    prompt_sha256: Sha256
    content_policy_version: SafeIdentity
    policy_match_view_version: SafeIdentity
    policy_scope: Literal["SYNTHETIC_LEXICAL_REGRESSION_ONLY"]
    d12_result: Literal["OFFLINE_REGRESSION_ONLY", "UNBOUND"]
    d4_snapshot_sha256: Sha256
    d4_revision: GitObjectId
    staging_method: Literal["SYNTHETIC_OFFLINE_FIXTURE"]
    staged_reference_class: Literal["SESSION_RELATIVE_FIXTURE"]


class BindingBudgetLimitsV1(_FrozenContract):
    budget_scope: Literal["OFFLINE_FIXTURE_ONLY"] = "OFFLINE_FIXTURE_ONLY"
    per_attempt_timeout_seconds: Literal[120.0]
    total_adapter_cap_seconds: PositiveSeconds
    session_provision_timeout_seconds: PositiveSeconds
    session_ttl_seconds: PositiveSeconds
    gpu_minute_cap: Annotated[float, Field(gt=0, le=1440, allow_inf_nan=False)]
    cleanup_timeout_seconds: PositiveSeconds
    session_termination_deadline_seconds: PositiveSeconds
    grant_max_age_seconds: PositiveSeconds

    @model_validator(mode="after")
    def validate_attempt_type(self) -> Self:
        if type(self.per_attempt_timeout_seconds) is not float:
            raise ValueError("attempt budget must be the explicit float 120.0")
        return self


class BindingOutputCeilingsV1(_FrozenContract):
    d9_binding_state: Literal["OFFLINE_FIXTURE_ONLY"] = "OFFLINE_FIXTURE_ONLY"
    raw_output_bytes: Annotated[int, Field(gt=0, le=1_048_576)]
    ipc_result_bytes: Annotated[int, Field(gt=0, le=1_048_576)]
    stdout_bytes: Annotated[int, Field(gt=0, le=1_048_576)]
    stderr_bytes: Annotated[int, Field(gt=0, le=1_048_576)]


class BindingArtifactInventorySummaryV1(_FrozenContract):
    """Safe counts of the captured baseline, never predicted postflight facts."""

    proof_scope: Literal["OFFLINE_SYNTHETIC"] = "OFFLINE_SYNTHETIC"
    phase: Literal["CAPTURED_PREFLIGHT_BASELINE"] = "CAPTURED_PREFLIGHT_BASELINE"
    baseline_entry_count: Annotated[int, Field(gt=0, le=1_048_576)]
    baseline_file_count: Annotated[int, Field(ge=0, le=1_048_576)]
    baseline_directory_count: Annotated[int, Field(gt=0, le=1_048_576)]
    explicit_root_count: Annotated[int, Field(gt=0, le=1_048_576)]
    max_entries: Annotated[int, Field(gt=0, le=1_048_576)]
    expected_evidence_file_count: Literal[2] = 2

    @field_validator("expected_evidence_file_count", mode="before")
    @classmethod
    def validate_expected_count_type(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("expected evidence count requires an exact integer")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if (
            self.baseline_file_count + self.baseline_directory_count != self.baseline_entry_count
            or self.baseline_entry_count > self.max_entries
            or self.explicit_root_count > self.baseline_directory_count
        ):
            raise ValueError("captured baseline summary counts are inconsistent")
        return self


class BindingPreflightFactsV1(_FrozenContract):
    proof_scope: Literal["OFFLINE_SYNTHETIC"] = "OFFLINE_SYNTHETIC"
    inputs: BindingInputIdentityV1
    admission_outcome: Literal["ADMITTED", "REJECTED", "UNKNOWN"]
    admission_reason: SafeCode | None
    media_validation_decision: Literal["PASS", "REJECTED", "UNKNOWN"]
    host_inventory_sha256: Sha256
    host_source_identities: Annotated[tuple[ArtifactIdentityV1, ...], Field(min_length=1, max_length=512)]
    d4_preflight_state: Literal["OBSERVED", "UNKNOWN"]
    artifact_inventory_summary: BindingArtifactInventorySummaryV1
    output_baseline_captured: bool
    evidence_destinations_absent: bool
    incident_destination_ignored: bool
    observer_ref: SafeIdentity = Field(repr=False)

    @model_validator(mode="after")
    def validate_admission(self) -> Self:
        if self.admission_outcome == "ADMITTED" and self.admission_reason is not None:
            raise ValueError("admitted fixture must have no admission reason")
        paths = tuple(item.relative_path for item in self.host_source_identities)
        if paths != tuple(sorted(set(paths))):
            raise ValueError("preflight source identities must be unique and ordered")
        return self


class BindingManifestV1(_FrozenContract):
    contract_version: Literal["P2T2-OFFLINE-BINDING-V1"] = "P2T2-OFFLINE-BINDING-V1"
    proof_scope: Literal["OFFLINE_SYNTHETIC"] = "OFFLINE_SYNTHETIC"
    live_authorized: Literal[False] = False
    live_seam_state: Literal["UNBOUND"] = "UNBOUND"
    inputs: BindingInputIdentityV1
    host_inventory: RuntimeEnvironmentInventoryV1
    session_inventory: RuntimeEnvironmentInventoryV1
    budgets: BindingBudgetLimitsV1
    ceilings: BindingOutputCeilingsV1

    @model_validator(mode="after")
    def validate_environment_roles(self) -> Self:
        if self.host_inventory.environment != "HOST" or self.session_inventory.environment != "SESSION":
            raise ValueError("binding requires separate host and session inventory roles")
        return self

    def verify_preflight(self, facts: BindingPreflightFactsV1) -> None:
        expected = self.revalidated()
        actual = facts.revalidated()
        if (
            actual.inputs != expected.inputs
            or actual.host_inventory_sha256 != expected.host_inventory.canonical_sha256()
            or actual.host_source_identities != expected.host_inventory.internal_modules
            or actual.admission_outcome != "ADMITTED"
            or actual.admission_reason is not None
            or actual.media_validation_decision != "PASS"
            or actual.d4_preflight_state != "OBSERVED"
            or not actual.output_baseline_captured
            or not actual.evidence_destinations_absent
            or not actual.incident_destination_ignored
        ):
            raise ValueError("offline binding preflight facts are missing or mismatched")


# Kept as an explicit expected-value name for callers that do not use a manifest.
BindingExpectedV1 = BindingManifestV1


class _Observation(_FrozenContract):
    state: ObservationState
    producer: Literal["SYNTHETIC_FIXTURE"] = "SYNTHETIC_FIXTURE"
    verification_scope: Literal["OFFLINE_FIXTURE_ONLY"] = "OFFLINE_FIXTURE_ONLY"
    observer_ref: SafeIdentity | None = Field(repr=False)

    def _check_values(self, values: tuple[object, ...]) -> None:
        if self.state in _RECEIVED_STATES:
            if self.observer_ref is None:
                raise ValueError("observed fixture facts require a fixture observer reference")
        elif self.observer_ref is not None or any(value is not None for value in values):
            raise ValueError("unobserved fixture facts must not carry values or provenance")


class BindingReadinessFactsV1(_Observation):
    status: Literal["READY", "NOT_READY"] | None
    issue_codes: Annotated[tuple[SafeCode, ...], Field(max_length=32)] | None
    model_load_performed: bool | None
    inference_performed: bool | None

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        values = (self.status, self.issue_codes, self.model_load_performed, self.inference_performed)
        self._check_values(values)
        if self.state == "OBSERVED":
            if any(value is None for value in values):
                raise ValueError("observed readiness requires all readiness facts")
            if self.status == "READY" and self.issue_codes != ():
                raise ValueError("ready fixture must have no readiness issues")
            if self.model_load_performed or self.inference_performed:
                raise ValueError("readiness must not preload or execute a model")
        return self


class BindingD4FactsV1(_Observation):
    state: PhaseObservationState
    snapshot_sha256: Sha256 | None
    revision: GitObjectId | None
    runtime_config_identity_sha256: Sha256 | None

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        values = (self.snapshot_sha256, self.revision, self.runtime_config_identity_sha256)
        self._check_values(values)
        if self.state in _RECEIVED_STATES and any(value is None for value in values):
            raise ValueError("observed D4 facts require snapshot and configuration identities")
        return self


class BindingStagingFactsV1(_Observation):
    state: PhaseObservationState
    staged_source_sha256: Sha256 | None
    staging_method: Literal["SYNTHETIC_OFFLINE_FIXTURE"] | None
    staged_reference_class: Literal["SESSION_RELATIVE_FIXTURE"] | None
    source_mime: Literal["image/png", "image/jpeg", "image/webp"] | None
    width: Annotated[int, Field(gt=0, le=65_536)] | None
    height: Annotated[int, Field(gt=0, le=65_536)] | None
    image_reference_verified: bool | None

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        values = (self.staged_source_sha256, self.staging_method, self.staged_reference_class, self.source_mime, self.width, self.height, self.image_reference_verified)
        self._check_values(values)
        if self.state in _RECEIVED_STATES and any(value is None for value in values):
            raise ValueError("observed staging requires the complete safe staging facts")
        return self


class BindingRuntimeFactsV1(_Observation):
    state: PhaseObservationState
    manifest: SanitizedRuntimeManifestV1 | None
    runtime_manifest_sha256: Sha256 | None
    session_inventory_sha256: Sha256 | None
    runtime_inputs: BindingInputIdentityV1 | None
    session_source_identities: Annotated[tuple[ArtifactIdentityV1, ...], Field(min_length=1, max_length=512)] | None
    single_device_visible: bool | None
    post_load_model_device_index: Annotated[int, Field(ge=0, le=63)] | None = None
    post_load_input_device_index: Annotated[int, Field(ge=0, le=63)] | None = None

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        values = (self.manifest, self.runtime_manifest_sha256, self.session_inventory_sha256, self.runtime_inputs, self.session_source_identities, self.single_device_visible, self.post_load_model_device_index, self.post_load_input_device_index)
        self._check_values(values)
        if self.state in _RECEIVED_STATES:
            if any(value is None for value in values[:6]):
                raise ValueError("observed runtime requires the complete safe runtime facts")
            assert self.manifest is not None
            if self.runtime_manifest_sha256 != self.manifest.canonical_sha256():
                raise ValueError("runtime manifest content identity mismatch")
            if (self.post_load_model_device_index is None) != (self.post_load_input_device_index is None):
                raise ValueError("post-load placement must carry both device facts")
            if self.single_device_visible and self.manifest.cuda.device_count != 1:
                raise ValueError("single-device visibility must match the manifest device count")
            if self.post_load_model_device_index is not None and (
                self.post_load_model_device_index != self.manifest.gpu.device_index
                or self.post_load_input_device_index != self.manifest.gpu.device_index
            ):
                raise ValueError("post-load placement must match the selected device index")
        return self


class BindingSessionFactsV1(_FrozenContract):
    """Missing session observations do not assert that generation never began."""

    readiness: BindingReadinessFactsV1
    d4: BindingD4FactsV1
    staging: BindingStagingFactsV1
    runtime: BindingRuntimeFactsV1
    stopped_before: Literal["READINESS", "D4", "STAGING", "DISPATCH"] | None

    @model_validator(mode="after")
    def validate_phase_order(self) -> Self:
        sections = (self.readiness, self.d4, self.staging, self.runtime)
        stop_indexes = {"READINESS": 0, "D4": 1, "STAGING": 2, "DISPATCH": 3}
        if self.stopped_before is None:
            if any(section.state == "NOT_REACHED" for section in sections):
                raise ValueError("not-reached session facts require an explicit phase blocker")
        else:
            index = stop_indexes[self.stopped_before]
            if any(section.state == "NOT_REACHED" for section in sections[:index]):
                raise ValueError("phase blocker cannot erase preceding phase observations")
            if any(section.state in _RECEIVED_STATES for section in sections[index + 1:]):
                raise ValueError("later session observations contradict the phase blocker")
        for position, section in enumerate(sections):
            if section.state == "OBSERVED_MISMATCH" and (
                self.stopped_before is None or stop_indexes[self.stopped_before] != position
            ):
                raise ValueError("an observed mismatch must be the explicit phase blocker")
        if self.d4.state in _RECEIVED_STATES and not (
            self.readiness.state == "OBSERVED" and self.readiness.status == "READY"
        ):
            raise ValueError("D4 observation requires successful readiness")
        if self.staging.state in _RECEIVED_STATES and self.d4.state != "OBSERVED":
            raise ValueError("staging observation requires matching D4 revalidation")
        if self.runtime.state in _RECEIVED_STATES and self.staging.state != "OBSERVED":
            raise ValueError("runtime manifest observation requires matching staging")
        return self


class BindingBooleanObservationV1(_Observation):
    value: bool | None

    @model_validator(mode="after")
    def validate_value(self) -> Self:
        self._check_values((self.value,))
        if self.state == "OBSERVED" and self.value is None:
            raise ValueError("observed assertion requires a value")
        return self


class BindingAssertionFactsV1(_FrozenContract):
    nested_spawn: BindingBooleanObservationV1
    outer_worker_non_daemon: BindingBooleanObservationV1
    containment_before_child_spawn: BindingBooleanObservationV1
    all_descendants_contained: BindingBooleanObservationV1
    no_orphan_after_kill: BindingBooleanObservationV1
    both_process_levels_absent: BindingBooleanObservationV1
    containment_absent: BindingBooleanObservationV1
    late_progress_rejected: BindingBooleanObservationV1
    attempt_deadline_120_seconds: BindingBooleanObservationV1
    total_cap_not_reset: BindingBooleanObservationV1
    timeout_not_retried: BindingBooleanObservationV1
    attempt_count_from_accepted_progress: BindingBooleanObservationV1
    cleanup_finally_executed: BindingBooleanObservationV1
    authoritative_monotonic_control: BindingBooleanObservationV1
    asr_whisper_not_executed: BindingBooleanObservationV1
    no_gate_decision_fabricated: BindingBooleanObservationV1
    correlation_and_provenance_match: BindingBooleanObservationV1
    exact_two_file_inventory: BindingBooleanObservationV1


class BindingResultFactsV1(_FrozenContract):
    v2_state: ObservationState
    v2_schema_valid: bool | None
    v2_status: Literal["SUCCEEDED", "FAILED"] | None
    v2_failure_code: Literal[
        "INPUT_NOT_VALIDATED", "VISION_MODEL_UNAVAILABLE", "VISION_TIMEOUT",
        "VISION_PROVIDER_FAILURE", "VISION_SCHEMA_INVALID", "PROHIBITED_CLAIM_DETECTED"
    ] | None
    v2_attempt_number: Annotated[int, Field(ge=0, le=2)] | None
    raw_state: ObservationState
    raw_schema_valid: bool | None
    raw_status: Literal["SUCCEEDED", "FAILED"] | None
    raw_failure_code: Literal[
        "VALIDATION_REJECTED", "SOURCE_MISMATCH", "STALE_CORRELATION",
        "MALFORMED_OUTPUT", "PROHIBITED_FIELD", "MODEL_UNAVAILABLE", "TIMEOUT",
        "PROVIDER_ERROR", "SCHEMA_INVALID"
    ] | None
    gate_a_required: Literal[True] | None
    narration_status: Literal["NOT_SUPPLIED"] | None
    observer_ref: SafeIdentity | None = Field(repr=False)

    @model_validator(mode="after")
    def validate_results(self) -> Self:
        for state, values in (
            (self.v2_state, (self.v2_schema_valid, self.v2_status, self.v2_failure_code, self.v2_attempt_number)),
            (self.raw_state, (self.raw_schema_valid, self.raw_status, self.raw_failure_code, self.gate_a_required, self.narration_status)),
        ):
            if state != "OBSERVED" and any(value is not None for value in values):
                raise ValueError("unobserved results must not carry result values")
            if state == "OBSERVED" and (self.observer_ref is None or values[0] is None or values[1] is None):
                raise ValueError("observed results require schema, status and fixture provenance")
        if self.v2_state != "OBSERVED" and self.raw_state != "OBSERVED" and self.observer_ref is not None:
            raise ValueError("unobserved results must not carry an observer reference")
        if self.v2_state == "OBSERVED" and (
            (self.v2_status == "SUCCEEDED" and self.v2_failure_code is not None)
            or (self.v2_status == "FAILED" and self.v2_failure_code is None)
        ):
            raise ValueError("received V2 status must agree with its typed failure code")
        if self.v2_state == "OBSERVED" and self.v2_attempt_number is None:
            raise ValueError("observed V2 requires its received adapter-local attempt number")
        if self.raw_state == "OBSERVED" and (
            (self.raw_status == "SUCCEEDED" and self.raw_failure_code is not None)
            or (self.raw_status == "FAILED" and self.raw_failure_code is None)
        ):
            raise ValueError("received Raw status must agree with its typed failure code")
        if self.raw_state == "OBSERVED" and self.gate_a_required is not True:
            raise ValueError("every observed Raw fixture requires Gate A")
        if self.raw_state == "OBSERVED" and self.raw_status == "SUCCEEDED" and (
            self.gate_a_required is not True or self.narration_status != "NOT_SUPPLIED"
        ):
            raise ValueError("successful raw fixture requires Gate A and no supplied narration")
        return self


class BindingBudgetConsumptionV1(_FrozenContract):
    state: ObservationState
    cap_outcome: Literal["WITHIN_CAP", "CAP_REACHED", "UNKNOWN"] | None
    gpu_minutes_consumed: NonnegativeNumber | None
    d9_enforcement: Literal["CONFIRMED", "UNCONFIRMED", "NOT_REACHED"]
    observer_ref: SafeIdentity | None = Field(repr=False)

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        if self.state == "OBSERVED":
            if self.cap_outcome is None or self.observer_ref is None:
                raise ValueError("observed consumption requires outcome and fixture provenance")
        elif any(value is not None for value in (self.cap_outcome, self.gpu_minutes_consumed, self.observer_ref)):
            raise ValueError("unobserved consumption must not carry consumed values")
        if self.state != "OBSERVED" and self.d9_enforcement == "CONFIRMED":
            raise ValueError("unobserved consumption cannot confirm D9 enforcement")
        return self


@dataclass(frozen=True, slots=True)
class RequirementCoverage:
    requirement: str
    producer: str
    carrier: str
    serializer: str
    verifier: str


_COVERAGE_ROWS = (
    ("commit_identity", "host/session fixture observers", "inputs/runtime_inputs", "explicit identity fields", "verify_preflight/session identity equality"),
    ("source_and_fixture_identity", "host admission fixture", "preflight.inputs", "fixture_id/source_sha256", "verify_preflight"),
    ("admission", "host admission fixture", "preflight.admission_outcome/admission_reason", "admission fields", "verify_preflight"),
    ("validation_provenance", "host validator fixture", "preflight.inputs/media_validation_decision", "validation fields", "verify_preflight"),
    ("readiness_no_preload", "session readiness fixture", "session.readiness", "readiness fields", "readiness invariants/bidirectional actual session-ready marker in validate_for_terminal"),
    ("d4_runtime_revalidation", "session D4 fixture", "session.d4", "D4 fields/observation state", "snapshot/config equality; OBSERVED_MISMATCH only as the failed pre-adapter phase blocker"),
    ("staging_and_reference", "session staging fixture", "session.staging", "staging fields/observation state", "source digest equality; success requires image_reference_verified=True; pre-adapter cannot claim it"),
    ("runtime_manifest", "session manifest fixture", "session.runtime", "allowlisted manifest/hash/observation state", "canonical hash/inventory comparison; OBSERVED_MISMATCH only as the failed pre-adapter phase blocker"),
    ("environment_closure", "host/session inventory fixtures", "manifest inventories/preflight/session hashes", "inventory hashes only", "canonical inventory identity comparison"),
    ("model_profile_prompt_policy", "host/session identity fixtures", "inputs/runtime_inputs", "explicit safe identity fields", "identity equality"),
    ("hardware_and_placement", "session manifest fixture", "session.runtime", "manifest/single-device/post-load fields", "manifest bounds/actual placement required and consistent"),
    ("d9_output_ceilings", "output enforcement fixture", "manifest.ceilings/consumption", "ceilings/enforcement/scope", "terminal enforcement gate"),
    ("cardinality", "coordinator/accepted-progress fixture", "terminal counts/assertions", "existing terminal serializer", "actual terminal counts/accepted progress assertion"),
    ("run_failure_code", "actual coordinator terminal", "Feat018LiveSmokeResult.failure_code", "existing terminal serializer: enum value or null", "typed enum check; reserved from binding metadata"),
    ("typed_v2_raw_terminal", "adapter/mapper fixture", "result", "typed status/code fields only", "synthetic receipt equality at wrapper; actual V2/Raw output verifier remains UNBOUND"),
    ("nested_spawn_and_non_daemon", "process observation fixture", "assertions", "state/value; observer_ref local only", "terminal applicability"),
    ("containment_and_descendants", "containment observation fixture", "assertions", "state/value; observer_ref local only", "terminal applicability"),
    ("no_orphan_two_level_cleanup", "cleanup observation fixture", "assertions", "state/value; observer_ref local only", "existing cleanup release gate"),
    ("late_progress", "supervisor acceptance fixture", "assertions.late_progress_rejected", "state/value; observer_ref local only", "terminal applicability"),
    ("attempt_total_deadlines_retry", "monotonic control fixture", "budgets/assertions", "budget values/assertion facts", "finite limits/terminal applicability"),
    ("session_caps_and_consumption", "monotonic/provider-meter fixture", "budgets/consumption", "cap outcome/consumed value", "finite limits/consumption bounds"),
    ("correlation_and_provenance", "caller/mapper fixture", "assertions", "state/value; observer_ref local only", "wrapper request identity/terminal checks"),
    ("gate_a_no_fabricated_decisions", "mapper fixture", "result/assertions", "gate_a_required/assertion facts", "raw success invariants"),
    ("no_asr_no_narration", "caller/mapper fixture", "result/assertions", "ASR assertion/narration status", "raw success invariants"),
    ("authorized_transition_and_failure_applicability", "coordinator fixture", "terminal counts/session.stopped_before", "phase states", "validate_for_terminal"),
    ("cleanup_finally_and_failure", "coordinator cleanup fixture", "assertions/existing terminal", "existing cleanup serializer", "existing release gate"),
    ("evidence_pair_incident_postflight", "finalizer/inventory fixture", "preflight.artifact_inventory_summary/assertions/existing finalizer", "safe captured-baseline counts/assertion/status", "actual baseline summary equality and quiescence/postflight/JSON-last existing primitives"),
)
RETAINED_REQUIREMENT_COVERAGE = tuple(RequirementCoverage(*row) for row in _COVERAGE_ROWS)


class BindingTerminalMetadataV1(_FrozenContract):
    contract_version: Literal["P2T2-OFFLINE-TERMINAL-METADATA-V1"] = (
        "P2T2-OFFLINE-TERMINAL-METADATA-V1"
    )
    proof_scope: Literal["OFFLINE_SYNTHETIC"] = "OFFLINE_SYNTHETIC"
    live_authorized: Literal[False] = False
    live_cleanup_proven: Literal[False] = False
    manifest: BindingManifestV1
    preflight: BindingPreflightFactsV1
    session: BindingSessionFactsV1
    assertions: BindingAssertionFactsV1
    result: BindingResultFactsV1
    consumption: BindingBudgetConsumptionV1

    @model_validator(mode="after")
    def validate_received_facts(self) -> Self:
        self.manifest.verify_preflight(self.preflight)
        inputs = self.manifest.inputs
        # OBSERVED requires equality; OBSERVED_MISMATCH requires a real difference. Both keep
        # the received syntax, provenance and phase rules and never become authorization.
        d4 = self.session.d4
        if d4.state in _RECEIVED_STATES:
            _check_received_identity(d4.state, (
                d4.snapshot_sha256 == inputs.d4_snapshot_sha256
                and d4.revision == inputs.d4_revision
                and d4.runtime_config_identity_sha256 == inputs.runtime_config_identity_sha256
            ), "D4")
        staging = self.session.staging
        if staging.state in _RECEIVED_STATES:
            _check_received_identity(staging.state, (
                staging.staged_source_sha256 == inputs.source_sha256
                and staging.staging_method == inputs.staging_method
                and staging.staged_reference_class == inputs.staged_reference_class
            ), "staging")
        runtime = self.session.runtime
        if runtime.state in _RECEIVED_STATES:
            assert runtime.manifest is not None
            inventory = self.manifest.session_inventory
            installed = {item.package: item.version for item in inventory.distributions}
            pins = {"accelerate": "1.10.1", "qwen-vl-utils": "0.0.14", "torch": "2.8.0", "transformers": "4.57.6"}
            hardware = runtime.manifest
            # Phase order guarantees successful readiness before any runtime observation.
            _check_received_identity(runtime.state, (
                runtime.runtime_inputs == inputs
                and runtime.session_inventory_sha256 == inventory.canonical_sha256()
                and runtime.session_source_identities == inventory.internal_modules
                and all(installed.get(item.package) == item.version for item in hardware.dependencies)
                and hardware.python.implementation == inventory.interpreter.implementation
                and hardware.python.version == inventory.interpreter.full_version
                and all(item.version == pins[item.package] for item in hardware.dependencies)
                and hardware.cuda.available
                and hardware.cuda.device_count == 1
                and hardware.gpu.sku in ("NVIDIA_L4", "NVIDIA L4")
                and hardware.gpu.bf16_supported
                and runtime.single_device_visible is True
            ), "session runtime")
        if self.consumption.gpu_minutes_consumed is not None and self.consumption.cap_outcome == "WITHIN_CAP" and self.consumption.gpu_minutes_consumed > self.manifest.budgets.gpu_minute_cap:
            raise ValueError("within-cap consumption exceeds the fixture cap")
        return self

    def validate_for_terminal(
        self,
        *,
        adapter_call_count: int,
        attempt_count: int | None,
        outcome: str,
        failure_code: str | None,
        session_ready: bool | None = None,
    ) -> None:
        checked = self.revalidated()
        if type(adapter_call_count) is not int or adapter_call_count not in (0, 1):
            raise ValueError("terminal adapter count is invalid")
        if attempt_count is not None and (type(attempt_count) is not int or attempt_count not in (1, 2)):
            raise ValueError("terminal attempt count is invalid")
        if outcome not in ("SUCCEEDED", "FAILED"):
            raise ValueError("terminal outcome is invalid")
        if session_ready is not None and type(session_ready) is not bool:
            raise ValueError("terminal session readiness is invalid")
        if adapter_call_count == 0:
            if attempt_count is not None or outcome != "FAILED" or failure_code is None:
                raise ValueError("pre-adapter metadata requires a typed failed terminal")
            if checked.session.stopped_before is None:
                raise ValueError("pre-adapter metadata requires an explicit phase blocker")
            if checked.result.v2_state == "OBSERVED" or checked.result.raw_state == "OBSERVED":
                raise ValueError("pre-adapter terminal must not fabricate adapter results")
        else:
            if checked.session.stopped_before is not None or any(
                item.state != "OBSERVED" for item in (
                    checked.session.readiness, checked.session.d4,
                    checked.session.staging, checked.session.runtime
                )
            ) or checked.session.readiness.status != "READY":
                raise ValueError("dispatch requires received successful session observations")
            if checked.result.v2_state == "NOT_REACHED" or checked.result.raw_state == "NOT_REACHED":
                raise ValueError("dispatch with missing progress leaves result reachability unknown")
        readiness = checked.session.readiness
        post_ready = (checked.session.d4, checked.session.staging, checked.session.runtime)
        if session_ready is True and not (
            readiness.state == "OBSERVED" and readiness.status == "READY"
        ):
            raise ValueError("terminal readiness contradicts received readiness facts")
        # Without the actual SESSION_READY marker (False or not supplied), no READY claim
        # and no post-ready D4/staging/runtime observation can be carried.
        if session_ready is not True:
            if readiness.state == "OBSERVED" and readiness.status == "READY":
                raise ValueError("a READY claim requires the actual session-ready marker")
            if any(item.state in _RECEIVED_STATES for item in post_ready):
                raise ValueError("post-ready observations require the actual session-ready marker")
        if any(item.state == "OBSERVED_MISMATCH" for item in post_ready) and (
            adapter_call_count != 0 or outcome != "FAILED"
        ):
            raise ValueError("observed mismatches are valid only on failed pre-adapter terminals")
        if adapter_call_count == 0 and checked.session.staging.image_reference_verified is True:
            raise ValueError("pre-adapter metadata cannot claim adapter image-reference verification")
        if attempt_count is not None and (
            checked.assertions.attempt_count_from_accepted_progress.state != "OBSERVED"
            or checked.assertions.attempt_count_from_accepted_progress.value is not True
        ):
            raise ValueError("attempt cardinality requires accepted-progress fixture facts")
        if adapter_call_count and any(
            value.state == "NOT_REACHED" for value in checked.assertions.__dict__.values()
        ):
            raise ValueError("missing process progress must remain unknown after dispatch")
        if outcome == "SUCCEEDED":
            if adapter_call_count != 1 or attempt_count is None:
                raise ValueError("successful terminal requires received call and attempt counts")
            if any(value.state != "OBSERVED" or value.value is not True for value in checked.assertions.__dict__.values()):
                raise ValueError("successful fixture terminal requires every retained assertion")
            if (
                checked.session.staging.state != "OBSERVED"
                or checked.session.staging.image_reference_verified is not True
            ):
                raise ValueError("successful terminal requires verified image-reference staging")
            if checked.result.v2_state != "OBSERVED" or checked.result.v2_schema_valid is not True or checked.result.v2_status != "SUCCEEDED":
                raise ValueError("successful terminal requires a received typed V2 success")
            if checked.result.raw_state != "OBSERVED" or checked.result.raw_schema_valid is not True or checked.result.raw_status != "SUCCEEDED":
                raise ValueError("successful terminal requires a received typed Raw success")
            if checked.consumption.state != "OBSERVED" or checked.consumption.cap_outcome != "WITHIN_CAP" or checked.consumption.d9_enforcement != "CONFIRMED":
                raise ValueError("successful terminal requires received cap and output enforcement facts")

    def evidence_fields(self) -> dict[str, object]:
        """Publish received, allowlisted fixture facts, never inventories or paths."""
        checked = self.revalidated()
        inputs = checked.preflight.inputs
        fields: dict[str, object] = {
            "binding_metadata_version": checked.contract_version,
            "binding_proof_scope": checked.proof_scope,
            "binding_live_authorized": False,
            "binding_live_cleanup_proven": False,
            "binding_live_seam_state": "UNBOUND",
            "binding_identity_scope": "FIXTURE_EXPECTATION_ONLY",
            "reviewed_runtime_code_commit": inputs.reviewed_runtime_code_commit,
            "approval_record_commit": inputs.approval_record_commit,
            "correlation_id": inputs.correlation_id,
            "fixture_id": inputs.fixture_id,
            "source_sha256": inputs.source_sha256,
            "admission_outcome": checked.preflight.admission_outcome,
            "admission_reason": checked.preflight.admission_reason,
            "media_validation_decision": checked.preflight.media_validation_decision,
            "validation_artifact_ref": inputs.validation_artifact_ref,
            "validation_artifact_sha256": inputs.validation_artifact_sha256,
            "validator_identity": inputs.validator_identity,
            "validator_policy_version": inputs.validator_policy_version,
            "host_inventory_sha256": checked.preflight.host_inventory_sha256,
            "artifact_inventory_summary": checked.preflight.artifact_inventory_summary.model_dump(mode="json"),
            "session_phase_blocker": checked.session.stopped_before,
            "readiness_observation_state": checked.session.readiness.state,
            "d4_observation_state": checked.session.d4.state,
            "staging_observation_state": checked.session.staging.state,
            "runtime_observation_state": checked.session.runtime.state,
            # observer_ref is local provenance only; it never enters published evidence.
            "binding_assertions": checked.assertions.model_dump(
                mode="json",
                exclude={name: {"observer_ref"} for name in type(checked.assertions).model_fields},
            ),
            "binding_result_facts": checked.result.model_dump(mode="json", exclude={"observer_ref"}),
            "binding_budget_scope": checked.manifest.budgets.budget_scope,
            "binding_budgets": checked.manifest.budgets.model_dump(mode="json"),
            "binding_output_ceilings": checked.manifest.ceilings.model_dump(mode="json"),
            "binding_consumption": checked.consumption.model_dump(mode="json", exclude={"observer_ref"}),
        }
        if checked.session.readiness.state == "OBSERVED":
            fields.update(readiness_status=checked.session.readiness.status, readiness_issue_codes=list(checked.session.readiness.issue_codes or ()), model_load_during_readiness=checked.session.readiness.model_load_performed)
        # A received mismatch publishes the same allowlisted fields; its state names it.
        if checked.session.d4.state in _RECEIVED_STATES:
            fields.update(d4_snapshot_sha256=checked.session.d4.snapshot_sha256, d4_revision=checked.session.d4.revision, runtime_config_identity_sha256=checked.session.d4.runtime_config_identity_sha256)
        if checked.session.staging.state in _RECEIVED_STATES:
            fields.update(staged_source_sha256=checked.session.staging.staged_source_sha256, staging_method=checked.session.staging.staging_method, staged_reference_class=checked.session.staging.staged_reference_class, source_mime=checked.session.staging.source_mime, source_width=checked.session.staging.width, source_height=checked.session.staging.height, image_reference_verified=checked.session.staging.image_reference_verified)
        if checked.session.runtime.state in _RECEIVED_STATES:
            runtime = checked.session.runtime
            assert runtime.manifest is not None and runtime.runtime_inputs is not None
            fields.update(runtime_manifest=runtime.manifest.model_dump(mode="json"), runtime_manifest_sha256=runtime.runtime_manifest_sha256, session_inventory_sha256=runtime.session_inventory_sha256, single_device_visible=runtime.single_device_visible)
            for name in (
                "model_identifier", "model_revision", "profile_id", "adapter_version",
                "profile_config_hash", "profile_catalog_hash", "prompt_protocol_id",
                "prompt_source_identity", "prompt_sha256", "content_policy_version",
                "policy_match_view_version", "policy_scope", "d12_result",
            ):
                fields[name] = getattr(runtime.runtime_inputs, name)
            if runtime.post_load_model_device_index is not None:
                fields.update(post_load_model_device_index=runtime.post_load_model_device_index, post_load_input_device_index=runtime.post_load_input_device_index)
        if _contains_key(fields, "observer_ref"):
            raise ValueError("local observation provenance cannot enter published evidence")
        return fields


# Owner-managed development invocation. These types never authorize live use or
# promote invocation observations to Studio/provider release evidence.
DevAttemptFailureCode = Literal[
    "NOT_AUTHORIZED", "IDENTITY_MISMATCH", "START_REUSED", "CLAIM_REUSED",
    "CANCELLED", "CANCELLED_BEFORE_START", "CONTROL_INVALID", "CONTROL_EOF",
    "FRAME_LIMIT", "TRANSPORT_LOST", "TRUNCATED_FRAME", "TRUST_UNBOUND",
    "DEADLINE_EXCEEDED", "WORK_DEADLINE", "CLEANUP_DEADLINE", "CANCEL_FAILED",
    "CLEANUP_FAILED", "INSPECTION_MISSING", "INSPECTION_INVALID",
    "INSPECTION_INCOMPLETE", "OWNERSHIP_RETAINED", "V2_INVALID", "RAW_INVALID",
    "PROVENANCE_MISMATCH", "D9_FAILED", "ADAPTER_FAILED", "REGISTRATION_INVALID",
    "CONTAINMENT_UNAVAILABLE", "CONTAINMENT_ESCAPE", "BIRTH_REUSED",
    "SUPERVISOR_LOST", "PROTOCOL_FAILED", "PRIVATE_CHANNEL_UNSAFE",
    "SSH_BINDING_INVALID", "SSH_BINDING_UNVERIFIED", "SSH_IO_FAILED", "SSH_EOF",
    "FRAME_INVALID", "FRAME_LIMIT_EXCEEDED", "FRAME_SEQUENCE_INVALID",
    "WORK_DEADLINE_EXCEEDED", "CLEANUP_DEADLINE_EXCEEDED", "CLOCK_INVALID",
    "TRANSPORT_POLL_LIMIT", "PROOF_REQUIRED",
]


class _DevAttemptContract(_FrozenContract):
    @field_validator("failure_codes", mode="before", check_fields=False)
    @classmethod
    def validate_failure_array(cls, value: object, info: ValidationInfo) -> object:
        if info.mode == "json" and isinstance(value, list):
            return tuple(value)
        return value

    @field_validator("studio_release_proven", mode="before", check_fields=False)
    @classmethod
    def validate_release_type(cls, value: object) -> object:
        if type(value) is not bool:
            raise ValueError("release fact requires an exact boolean")
        return value


class DevAttemptIdentityV1(_DevAttemptContract):
    """Private control identity; never included in the public summary."""

    studio_ref: SafeIdentity = Field(repr=False)
    invocation_ref: SafeIdentity = Field(repr=False)
    nonce: Sha256 = Field(repr=False)
    python_sha256: Sha256 = Field(repr=False)
    entry_sha256: Sha256 = Field(repr=False)
    config_sha256: Sha256 = Field(repr=False)
    source_sha256: Sha256 = Field(repr=False)
    request_sha256: Sha256 = Field(repr=False)

    def __repr__(self) -> str:
        return "DevAttemptIdentityV1(<private>)"

    def __str__(self) -> str:
        return "DevAttemptIdentityV1(<private>)"


class DevAttemptBudgetsV1(_DevAttemptContract):
    work_seconds: PositiveSeconds
    cleanup_seconds: PositiveSeconds
    poll_seconds: PositiveSeconds
    per_attempt_seconds: Literal[120.0] = 120.0

    @field_validator("per_attempt_seconds", mode="before")
    @classmethod
    def validate_exact_attempt(cls, value: object) -> object:
        if type(value) is not float:
            raise ValueError("attempt deadline requires the explicit float")
        return value

    @model_validator(mode="after")
    def validate_poll_budget(self) -> Self:
        if self.poll_seconds > min(self.work_seconds, self.cleanup_seconds):
            raise ValueError("poll interval exceeds the bounded window")
        return self


class DevAttemptControlV1(_DevAttemptContract):
    identity: DevAttemptIdentityV1 = Field(repr=False)
    operation: Literal["OPEN", "START", "CANCEL", "STATUS", "INSPECT", "EOF"]
    sequence: Annotated[int, Field(ge=0, le=1024)] = 0


class DevAttemptVerificationV1(_DevAttemptContract):
    v2_status: Literal["NOT_REACHED", "SUCCEEDED", "FAILED", "INVALID"] = "NOT_REACHED"
    raw_status: Literal["NOT_REACHED", "SUCCEEDED", "FAILED", "INVALID"] = "NOT_REACHED"
    v2_schema_verified: bool | None = None
    raw_schema_verified: bool | None = None
    source_matched: bool | None = None
    correlation_matched: bool | None = None
    provenance_matched: bool | None = None
    gate_a_required: bool | None = None
    narration_status: Literal["NOT_REACHED", "NOT_SUPPLIED"] = "NOT_REACHED"
    failure_codes: Annotated[tuple[DevAttemptFailureCode, ...], Field(max_length=16)] = ()

    @model_validator(mode="after")
    def validate_verification(self) -> Self:
        if len(set(self.failure_codes)) != len(self.failure_codes):
            raise ValueError("duplicate verification failures")
        if self.v2_status == "NOT_REACHED" and any(
            value is not None for value in (
                self.v2_schema_verified, self.source_matched,
                self.correlation_matched, self.provenance_matched,
            )
        ):
            raise ValueError("unreached V2 has no verification facts")
        if self.raw_status == "NOT_REACHED" and (
            self.raw_schema_verified is not None or self.gate_a_required is not None
            or self.narration_status != "NOT_REACHED"
        ):
            raise ValueError("unreached Raw has no verification facts")
        if self.v2_status in ("SUCCEEDED", "FAILED") and self.v2_schema_verified is not True:
            raise ValueError("received V2 must be revalidated")
        if self.raw_status in ("SUCCEEDED", "FAILED") and self.raw_schema_verified is not True:
            raise ValueError("received Raw must be revalidated")
        if self.v2_status == "INVALID" and (
            self.v2_schema_verified is not False or "V2_INVALID" not in self.failure_codes
        ):
            raise ValueError("invalid V2 requires its failed schema observation")
        if self.raw_status == "INVALID" and (
            self.raw_schema_verified is not False or "RAW_INVALID" not in self.failure_codes
        ):
            raise ValueError("invalid Raw requires its failed schema observation")
        if self.raw_status == "FAILED" and (
            self.v2_status != "FAILED" or self.gate_a_required is not True
            or "ADAPTER_FAILED" not in self.failure_codes
            or any(value is not True for value in (
                self.source_matched, self.correlation_matched, self.provenance_matched,
            ))
        ):
            raise ValueError("typed Raw failure requires the checked failed V2")
        if self.raw_status == "SUCCEEDED" and (
            self.v2_status != "SUCCEEDED" or self.gate_a_required is not True
            or self.narration_status != "NOT_SUPPLIED"
            or any(value is not True for value in (
                self.source_matched, self.correlation_matched, self.provenance_matched,
            )) or self.failure_codes
        ):
            raise ValueError("successful verification requires every received invariant")
        return self


class DevAttemptSummaryV1(_DevAttemptContract):
    scope: Literal["OWNER_MANAGED_STUDIO_DEVELOPMENT"] = "OWNER_MANAGED_STUDIO_DEVELOPMENT"
    live_authorized: Literal[False] = False
    studio_release_proven: Literal[False] = False
    outcome: Literal["NOT_AUTHORIZED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN", "CANCELLED"]
    cleanup: Literal["NOT_REACHED", "UNKNOWN", "FAILED", "VERIFIED_OFFLINE"] = "NOT_REACHED"
    adapter_call_count: Literal[0, 1] | None = 0
    attempt_count: Literal[1, 2] | None = None
    verification: DevAttemptVerificationV1 | None = None
    ownership_retained: bool = False
    failure_codes: Annotated[tuple[DevAttemptFailureCode, ...], Field(max_length=16)] = ()

    @field_validator("adapter_call_count", "attempt_count", mode="before")
    @classmethod
    def validate_exact_counts(cls, value: object) -> object:
        if value is not None and type(value) is not int:
            raise ValueError("counts require exact integers")
        return value

    @model_validator(mode="after")
    def validate_summary(self) -> Self:
        if len(set(self.failure_codes)) != len(self.failure_codes):
            raise ValueError("duplicate attempt failures")
        if self.adapter_call_count != 1 and self.attempt_count is not None:
            raise ValueError("a generation count requires an accepted adapter start")
        if self.cleanup in ("UNKNOWN", "FAILED") and not self.ownership_retained:
            raise ValueError("unverified cleanup must retain ownership")
        if self.outcome == "NOT_AUTHORIZED" and (
            self.adapter_call_count != 0 or self.attempt_count is not None
            or self.cleanup != "NOT_REACHED" or self.verification is not None
            or self.ownership_retained
        ):
            raise ValueError("denial must precede every effect")
        if self.outcome == "SUCCEEDED" and (
            self.cleanup != "VERIFIED_OFFLINE" or self.ownership_retained
            or self.adapter_call_count != 1 or self.attempt_count not in (1, 2)
            or self.verification is None or self.verification.raw_status != "SUCCEEDED"
            or self.failure_codes
        ):
            raise ValueError("success needs accepted verification and invocation cleanup")
        return self


class DevAttemptFrameV1(_DevAttemptContract):
    kind: Literal["READY", "PROGRESS", "VERIFICATION", "TERMINAL", "STATUS", "CANCEL_ACK", "INSPECTION", "ERROR"]
    binding_sha256: Sha256
    sequence: Annotated[int, Field(ge=0, le=1024)]
    summary: DevAttemptSummaryV1 | None = None
    progress: Literal["CONTAINMENT_READY", "ADAPTER_STARTED", "GENERATION_ATTEMPT_STARTED", "TERMINAL"] | None = None
    attempt_number: Literal[1, 2] | None = None

    @field_validator("attempt_number", mode="before")
    @classmethod
    def validate_exact_attempt_number(cls, value: object) -> object:
        if value is not None and type(value) is not int:
            raise ValueError("attempt number requires an exact integer")
        return value

    @model_validator(mode="after")
    def validate_frame(self) -> Self:
        if self.kind == "READY" and self.summary is not None:
            raise ValueError("ready cannot carry a result")
        if self.kind == "VERIFICATION" and (
            self.summary is None or self.summary.verification is None
        ):
            raise ValueError("verification frame requires received verification")
        if self.kind == "PROGRESS":
            if self.progress is None or self.summary is not None:
                raise ValueError("progress frame requires only accepted progress")
            if (self.progress == "GENERATION_ATTEMPT_STARTED") != (self.attempt_number is not None):
                raise ValueError("attempt metadata belongs only to generation start")
        elif self.progress is not None or self.attempt_number is not None:
            raise ValueError("non-progress frame cannot carry counts")
        if self.kind in ("TERMINAL", "STATUS", "CANCEL_ACK", "INSPECTION", "ERROR") and self.summary is None:
            raise ValueError("result frame requires closed summary")
        return self
