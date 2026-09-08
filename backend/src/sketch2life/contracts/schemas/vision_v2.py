"""Additive V2 contracts for the bounded Qwen vision-understanding study.

The Phase A contracts remain in :mod:`vision` and are deliberately not imported
back into or modified by this module.  V2 reuses only version-neutral image,
text, and candidate value objects; its profile identity, catalog, request, and
result types are disjoint from V1.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    ImageDerivationProvenanceV1,
    ObservedTextV1,
    RelationCandidateV1,
    ThemeCandidateV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
    VisionProhibitedClaimCategory,
)

_ObservationRef = Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]

_WINDOWS_DRIVE_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")


def _is_absolute_machine_path(value: str) -> bool:
    """Reject host-independent POSIX, Windows-rooted, drive, and UNC paths."""

    if value.startswith("/") or value.startswith("\\"):
        return True
    return bool(_WINDOWS_DRIVE_ABSOLUTE_PATTERN.match(value))


class VisionProfileIdV2(StrEnum):
    """Real-model profile identities; disjoint from the Phase A enum."""

    QWEN3_VL_8B_INSTRUCT_BF16_V1 = "QWEN3_VL_8B_INSTRUCT_BF16_V1"


class VisionWeightHashAbsenceReason(StrEnum):
    """Closed reasons why a single SHA-256 weight digest is not carried."""

    SOURCE_DOES_NOT_PUBLISH_A_DIGEST = "SOURCE_DOES_NOT_PUBLISH_A_DIGEST"
    DIGEST_ALGORITHM_INCOMPATIBLE_WITH_SHA256 = (
        "DIGEST_ALGORITHM_INCOMPATIBLE_WITH_SHA256"
    )


class VisionDependencyPinV1(BaseModel):
    """One exact package pin captured as part of model provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    version: str = Field(min_length=1)

    @field_validator("version")
    @classmethod
    def _requires_an_exact_version(cls, value: str) -> str:
        if any(character in value for character in "<>~=!*^") or any(
            character.isspace() for character in value
        ):
            raise ValueError("dependency version must be an exact pin, not a range")
        return value


class VisionModelProvenanceV1(BaseModel):
    """Model/weight/runtime provenance carried only by the V2 result contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_identifier: str = Field(min_length=1)
    model_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    weight_source: str = Field(min_length=1)
    weight_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    weight_sha256_absence_reason: VisionWeightHashAbsenceReason | None = None
    weight_license: str = Field(min_length=1)
    dependency_pins: tuple[VisionDependencyPinV1, ...] = Field(min_length=1)

    @field_validator("model_identifier", "weight_source")
    @classmethod
    def _rejects_absolute_local_paths(cls, value: str) -> str:
        if _is_absolute_machine_path(value):
            raise ValueError("model provenance references must not be absolute machine paths")
        return value

    @field_validator("weight_source")
    @classmethod
    def _requires_a_non_path_weight_reference(cls, value: str) -> str:
        if value.startswith("~"):
            raise ValueError("weight_source must not be a local path")
        return value

    @field_validator("dependency_pins")
    @classmethod
    def _sorts_and_rejects_duplicate_packages(
        cls, value: tuple[VisionDependencyPinV1, ...]
    ) -> tuple[VisionDependencyPinV1, ...]:
        package_names = tuple(pin.package for pin in value)
        if len(package_names) != len(set(package_names)):
            raise ValueError("dependency package names must be unique")
        return tuple(sorted(value, key=lambda pin: pin.package))

    @model_validator(mode="after")
    def _requires_exactly_one_weight_hash_statement(self) -> VisionModelProvenanceV1:
        has_digest = self.weight_sha256 is not None
        has_absence_reason = self.weight_sha256_absence_reason is not None
        if has_digest == has_absence_reason:
            raise ValueError(
                "exactly one of weight_sha256 and weight_sha256_absence_reason is required"
            )
        return self


class VisionDecodingV1(BaseModel):
    """Greedy decoding identity used by the one approved candidate profile."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sampling_enabled: Literal[False] = False
    temperature: None = None
    top_p: None = None
    top_k: None = None
    beam_count: Literal[1] = 1
    max_new_tokens: int = Field(gt=0)
    repetition_penalty: float = Field(gt=0)
    seed: int
    image_preprocessing_version: str = Field(min_length=1)


class VisionProfileV2(BaseModel):
    """Real-model profile; deterministic fakes remain V1-only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: VisionProfileIdV2
    adapter_kind: Literal["QWEN_VL_LOCAL"] = "QWEN_VL_LOCAL"
    task: Literal["structured_observation"] = "structured_observation"
    compute_profile: Literal["GPU_BF16"] = "GPU_BF16"
    timeout_seconds: float = Field(gt=0)
    structured_output_mode: Literal["STRICT_JSON_OBJECT"] = "STRICT_JSON_OBJECT"
    adapter_version: str = Field(min_length=1)
    timeout_retry_policy: Literal["NEVER_RETRY"] = "NEVER_RETRY"
    model_provenance: VisionModelProvenanceV1
    decoding: VisionDecodingV1


class VisionProfileCatalogV2(BaseModel):
    """One static V2 catalog containing real candidates only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["VisionProfileCatalogV2"] = "VisionProfileCatalogV2"
    contract_version: Literal["2.0"] = "2.0"
    profiles: tuple[VisionProfileV2, ...]

    @model_validator(mode="after")
    def _requires_unique_profile_ids(self) -> VisionProfileCatalogV2:
        profile_ids = tuple(profile.profile_id for profile in self.profiles)
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile IDs must be unique")
        return self

    def resolve(self, profile_id: VisionProfileIdV2) -> VisionProfileV2:
        for profile in self.profiles:
            if profile.profile_id is profile_id:
                return profile
        raise ValueError(f"profile is absent from catalog: {profile_id}")


_QWEN_MODEL_REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"

_QWEN_MODEL_PROVENANCE = VisionModelProvenanceV1(
    model_identifier="Qwen/Qwen3-VL-8B-Instruct",
    model_revision=_QWEN_MODEL_REVISION,
    weight_source="https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct",
    weight_sha256=None,
    weight_sha256_absence_reason=VisionWeightHashAbsenceReason.SOURCE_DOES_NOT_PUBLISH_A_DIGEST,
    weight_license="apache-2.0",
    dependency_pins=(
        VisionDependencyPinV1(package="accelerate", version="1.10.1"),
        VisionDependencyPinV1(package="qwen-vl-utils", version="0.0.14"),
        VisionDependencyPinV1(package="torch", version="2.8.0"),
        VisionDependencyPinV1(package="transformers", version="4.57.6"),
    ),
)

_QWEN_PROFILE_V2 = VisionProfileV2(
    profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    timeout_seconds=120.0,
    adapter_version="qwen3-vl-local-adapter-v2-b1",
    model_provenance=_QWEN_MODEL_PROVENANCE,
    decoding=VisionDecodingV1(
        max_new_tokens=512,
        repetition_penalty=1.0,
        seed=0,
        image_preprocessing_version="qwen3-vl-processor-config-b1",
    ),
)

_VISION_PROFILE_CATALOG_V2 = VisionProfileCatalogV2(profiles=(_QWEN_PROFILE_V2,))


def vision_profile_catalog_v2() -> VisionProfileCatalogV2:
    """Return the single immutable V2 catalog snapshot."""

    return _VISION_PROFILE_CATALOG_V2


def vision_profile_config_hash_v2(profile: VisionProfileV2) -> str:
    """Hash the complete V2 profile without widening or reusing the V1 function."""

    if not isinstance(profile, VisionProfileV2):
        raise TypeError("vision_profile_config_hash_v2 requires VisionProfileV2")
    payload = dumps(profile.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def vision_profile_catalog_hash_v2(catalog: VisionProfileCatalogV2) -> str:
    """Hash the complete ordered V2 catalog snapshot."""

    if not isinstance(catalog, VisionProfileCatalogV2):
        raise TypeError("vision_profile_catalog_hash_v2 requires VisionProfileCatalogV2")
    payload = dumps(catalog.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


class VisionUnderstandingRequestV2(BaseModel):
    """V2 request; profile resolution is bound to the canonical V2 catalog."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["VisionUnderstandingRequestV2"] = "VisionUnderstandingRequestV2"
    contract_version: Literal["2.0"] = "2.0"
    correlation_id: str = Field(min_length=1)
    source_image_ref: VisionImageReferenceV1
    processing_image_ref: VisionImageReferenceV1 | None = None
    derivation_provenance: ImageDerivationProvenanceV1 | None = None
    media_validation: VisionMediaValidationProvenanceV1 | None = None
    requested_profile_id: VisionProfileIdV2

    @model_validator(mode="after")
    def _requires_valid_derivation_and_profile(self) -> VisionUnderstandingRequestV2:
        if self.processing_image_ref is None and self.derivation_provenance is not None:
            raise ValueError("derivation provenance requires a processing image reference")
        if self.processing_image_ref is not None:
            if self.derivation_provenance is None:
                raise ValueError("processing image reference requires derivation provenance")
            if self.derivation_provenance.source_image_sha256 != self.source_image_ref.sha256:
                raise ValueError("derivation provenance must link to the source image hash")
            if (
                self.derivation_provenance.processing_image_sha256
                != self.processing_image_ref.sha256
            ):
                raise ValueError("derivation provenance must link to the processing image hash")
        vision_profile_catalog_v2().resolve(self.requested_profile_id)
        return self


class VisionResultEnvelopeV2(BaseModel):
    """V2 shared result envelope; model provenance is branch-applicable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["VisionUnderstandingResultV2"] = "VisionUnderstandingResultV2"
    contract_version: Literal["2.0"] = "2.0"
    correlation_id: str = Field(min_length=1)
    executed_at: datetime
    source_image_ref: VisionImageReferenceV1
    profile_id: VisionProfileIdV2
    profile_catalog_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    attempt_number: int = Field(ge=0, le=2)
    repair_attempted: bool
    content_policy_version: str = Field(min_length=1)
    policy_match_view_version: str = Field(min_length=1)
    policy_execution_state: Literal["NOT_EXECUTED", "PASSED", "BLOCKED"]

    @field_validator("executed_at")
    @classmethod
    def _requires_timezone_aware_execution_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("executed_at must be timezone aware")
        return value


def _validate_observation_references_v2(
    entities: tuple[EntityCandidateV1, ...],
    actions: tuple[ActionCandidateV1, ...],
    relations: tuple[RelationCandidateV1, ...],
    themes: tuple[ThemeCandidateV1, ...],
    ambiguous_regions: tuple[AmbiguousRegionCandidateV1, ...],
) -> None:
    kind_by_id: dict[str, str] = {}

    def register(observation_id: str, kind: str) -> None:
        if observation_id in kind_by_id:
            raise ValueError(f"DUPLICATE_OBSERVATION_ID: {observation_id}")
        kind_by_id[observation_id] = kind

    for entity in entities:
        register(entity.observation_id, "ENTITY")
    for action in actions:
        register(action.observation_id, "ACTION")
    for relation in relations:
        register(relation.observation_id, "RELATION")
    for theme in themes:
        register(theme.observation_id, "THEME")
    for region in ambiguous_regions:
        register(region.observation_id, "AMBIGUOUS_REGION")

    def require_kind(ref: str, allowed: frozenset[str], field: str) -> None:
        kind = kind_by_id.get(ref)
        if kind is None or kind not in allowed:
            raise ValueError(f"REFERENCE_INTEGRITY_VIOLATION: {field} -> {ref}")

    entity_only = frozenset({"ENTITY"})
    entity_or_action = frozenset({"ENTITY", "ACTION"})
    evidence_kinds = frozenset({"ENTITY", "ACTION", "RELATION"})

    for action in actions:
        if action.actor_ref is not None:
            require_kind(action.actor_ref, entity_only, "actor_ref")
        if action.object_ref is not None:
            require_kind(action.object_ref, entity_only, "object_ref")
    for relation in relations:
        require_kind(relation.subject_ref, entity_or_action, "subject_ref")
        require_kind(relation.object_ref, entity_or_action, "object_ref")
    for theme in themes:
        for ref in theme.evidence_refs:
            require_kind(ref, evidence_kinds, "evidence_refs")


class VisionUnderstandingSuccessV2(VisionResultEnvelopeV2):
    """Schema-valid, policy-passed V2 observations with model provenance."""

    status: Literal["SUCCEEDED"] = "SUCCEEDED"
    entities: tuple[EntityCandidateV1, ...]
    actions: tuple[ActionCandidateV1, ...]
    relations: tuple[RelationCandidateV1, ...]
    themes: tuple[ThemeCandidateV1, ...]
    ambiguous_regions: tuple[AmbiguousRegionCandidateV1, ...]
    adapter_version: str = Field(min_length=1)
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    model_provenance: VisionModelProvenanceV1

    @model_validator(mode="after")
    def _requires_passed_policy_state(self) -> VisionUnderstandingSuccessV2:
        if self.policy_execution_state != "PASSED":
            raise ValueError("a SUCCEEDED result requires policy_execution_state=PASSED")
        _validate_observation_references_v2(
            self.entities, self.actions, self.relations, self.themes, self.ambiguous_regions
        )
        return self


class VisionNonPolicyErrorDetailV2(StrEnum):
    """V2 non-policy details; V1's enum remains unchanged."""

    MEDIA_VALIDATION_NOT_PASSED = "MEDIA_VALIDATION_NOT_PASSED"
    MEDIA_VALIDATION_PROVENANCE_MISSING = "MEDIA_VALIDATION_PROVENANCE_MISSING"
    SOURCE_IMAGE_UNREADABLE = "SOURCE_IMAGE_UNREADABLE"
    SOURCE_IMAGE_HASH_MISMATCH = "SOURCE_IMAGE_HASH_MISMATCH"
    PROFILE_NOT_RESOLVABLE = "PROFILE_NOT_RESOLVABLE"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    TIMEOUT_BUDGET_EXCEEDED = "TIMEOUT_BUDGET_EXCEEDED"
    TRANSIENT_RUNTIME_FAILURE = "TRANSIENT_RUNTIME_FAILURE"
    PERMANENT_RUNTIME_FAILURE = "PERMANENT_RUNTIME_FAILURE"
    OUTPUT_MAPPING_FAILED = "OUTPUT_MAPPING_FAILED"
    DUPLICATE_OBSERVATION_ID = "DUPLICATE_OBSERVATION_ID"
    REFERENCE_INTEGRITY_VIOLATION = "REFERENCE_INTEGRITY_VIOLATION"


VisionFailureDetailV2 = VisionNonPolicyErrorDetailV2 | VisionProhibitedClaimCategory
VisionErrorCodeV2 = VisionErrorCode


_V2_INPUT_DETAILS = frozenset(
    {
        VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_NOT_PASSED,
        VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_PROVENANCE_MISSING,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH,
        VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE,
    }
)
_V2_SCHEMA_DETAILS = frozenset(
    {
        VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
        VisionNonPolicyErrorDetailV2.DUPLICATE_OBSERVATION_ID,
        VisionNonPolicyErrorDetailV2.REFERENCE_INTEGRITY_VIOLATION,
    }
)


def _is_model_reached_failure(error_code: VisionErrorCode) -> bool:
    return error_code is not VisionErrorCode.INPUT_NOT_VALIDATED


class VisionUnderstandingFailureV2(VisionResultEnvelopeV2):
    """Typed V2 failure with the complete terminal-outcome matrix enforced."""

    status: Literal["FAILED"] = "FAILED"
    error_code: VisionErrorCode
    error_detail: VisionFailureDetailV2
    retryable: bool
    # ``exclude_if`` keeps the forbidden input-failure field absent from serialized output.
    model_provenance: VisionModelProvenanceV1 | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def _requires_a_consistent_failure_matrix_row(self) -> VisionUnderstandingFailureV2:
        provenance_was_supplied = "model_provenance" in self.model_fields_set

        if self.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED:
            if not isinstance(self.error_detail, VisionProhibitedClaimCategory):
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires a prohibited-claim category")
            if self.policy_execution_state != "BLOCKED":
                raise ValueError(
                    "PROHIBITED_CLAIM_DETECTED requires policy_execution_state=BLOCKED"
                )
            if self.retryable is not False:
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires retryable=false")
            if self.attempt_number not in {1, 2}:
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires attempt_number=1 or 2")
            if _is_model_reached_failure(self.error_code) and self.model_provenance is None:
                raise ValueError("model-reached outcomes require model_provenance")
            return self

        if not isinstance(self.error_detail, VisionNonPolicyErrorDetailV2):
            raise ValueError(f"{self.error_code} requires a non-policy error detail")

        detail = self.error_detail
        if detail in _V2_INPUT_DETAILS:
            expected_code = VisionErrorCode.INPUT_NOT_VALIDATED
            permitted_attempts = {0}
            expected_retryable = False
            permitted_repair = {False}
        elif detail in {
            VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED,
            VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE,
        }:
            expected_code = VisionErrorCode.VISION_MODEL_UNAVAILABLE
            permitted_attempts = {1}
            expected_retryable = False
            permitted_repair = {False}
        elif detail is VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED:
            expected_code = VisionErrorCode.VISION_TIMEOUT
            permitted_attempts = {1, 2}
            expected_retryable = False
            permitted_repair = {False}
        elif detail is VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE:
            expected_code = VisionErrorCode.VISION_PROVIDER_FAILURE
            permitted_attempts = {2}
            expected_retryable = True
            permitted_repair = {False}
        elif detail is VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE:
            expected_code = VisionErrorCode.VISION_PROVIDER_FAILURE
            permitted_attempts = {1, 2}
            expected_retryable = False
            permitted_repair = {False}
        elif detail in _V2_SCHEMA_DETAILS:
            expected_code = VisionErrorCode.VISION_SCHEMA_INVALID
            permitted_attempts = {1, 2}
            expected_retryable = False
            permitted_repair = {False, True}
        else:  # pragma: no cover - exhaustive guard for future enum additions
            raise ValueError(f"unsupported V2 failure detail: {detail}")

        if self.error_code is not expected_code:
            raise ValueError(f"{detail} is not valid for error_code={self.error_code}")
        if self.policy_execution_state != "NOT_EXECUTED":
            raise ValueError(f"{self.error_code} requires policy_execution_state=NOT_EXECUTED")
        if self.retryable is not expected_retryable:
            raise ValueError(f"{detail} requires retryable={expected_retryable}")
        if self.attempt_number not in permitted_attempts:
            permitted = ", ".join(str(value) for value in sorted(permitted_attempts))
            raise ValueError(f"{detail} requires attempt_number in {{{permitted}}}")
        if self.repair_attempted not in permitted_repair:
            raise ValueError(f"{detail} does not permit repair_attempted={self.repair_attempted}")

        if self.error_code is VisionErrorCode.INPUT_NOT_VALIDATED:
            if self.model_provenance is not None or provenance_was_supplied:
                raise ValueError("INPUT_NOT_VALIDATED forbids model_provenance")
        elif self.model_provenance is None:
            raise ValueError("model-reached outcomes require model_provenance")
        return self


VisionUnderstandingResultV2 = Annotated[
    VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2, Field(discriminator="status")
]


def collect_observed_texts_v2(
    success: VisionUnderstandingSuccessV2,
) -> tuple[ObservedTextV1, ...]:
    """Return declared text fields for the policy layer without exposing raw output."""

    texts: list[ObservedTextV1] = []
    texts.extend(entity.label for entity in success.entities)
    texts.extend(action.label for action in success.actions)
    texts.extend(relation.predicate for relation in success.relations)
    texts.extend(theme.label for theme in success.themes)
    texts.extend(region.note for region in success.ambiguous_regions)
    return tuple(texts)


__all__ = [
    "VisionDecodingV1",
    "VisionDependencyPinV1",
    "VisionErrorCodeV2",
    "VisionFailureDetailV2",
    "VisionModelProvenanceV1",
    "VisionNonPolicyErrorDetailV2",
    "VisionProfileCatalogV2",
    "VisionProfileIdV2",
    "VisionProfileV2",
    "VisionUnderstandingFailureV2",
    "VisionUnderstandingRequestV2",
    "VisionUnderstandingResultV2",
    "VisionUnderstandingSuccessV2",
    "VisionResultEnvelopeV2",
    "VisionWeightHashAbsenceReason",
    "collect_observed_texts_v2",
    "vision_profile_catalog_hash_v2",
    "vision_profile_catalog_v2",
    "vision_profile_config_hash_v2",
]
