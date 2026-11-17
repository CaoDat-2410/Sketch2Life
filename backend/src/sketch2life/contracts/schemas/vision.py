"""Versioned, provider-neutral contracts for P2-T3 Phase A vision-understanding fixtures."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

VISION_LABEL_NORMALIZER_VERSION = "vision-label-normalizer-v1"
VISION_POLICY_MATCH_VIEW_VERSION = "vision-policy-match-view-v2"

_ObservationRef = Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
_Confidence = float | None
_LanguageTag = Annotated[str, Field(min_length=2, max_length=32)]

_WINDOWS_DRIVE_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")


def _is_absolute_machine_path(value: str) -> bool:
    """Host-OS-independent check: POSIX absolute, Windows drive-absolute, rooted, or UNC.

    Any leading backslash is rejected: a single leading backslash (`\\temp\\x.png`) is
    rooted on the current Windows drive, and a double leading backslash (`\\\\server\\share`)
    is a UNC path. Both are absolute machine paths regardless of the host OS running this
    check.
    """

    if value.startswith("/") or value.startswith("\\"):
        return True
    return bool(_WINDOWS_DRIVE_ABSOLUTE_PATTERN.match(value))


class VisionImageReferenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ref: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("artifact_ref")
    @classmethod
    def _rejects_absolute_machine_paths(cls, value: str) -> str:
        if _is_absolute_machine_path(value):
            raise ValueError("artifact_ref must not be an absolute machine path")
        return value


class ImageDerivationProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transform_name: str = Field(min_length=1)
    transform_config_version: str = Field(min_length=1)
    source_image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    processing_image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class VisionMediaValidationProvenanceV1(BaseModel):
    """Mirrors P2-T2's shape deliberately; defined independently, never imported from it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    validation_artifact_ref: str = Field(min_length=1)
    validation_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["PASS", "RECAPTURE"]
    validator_policy_version: str = Field(min_length=1)


def vision_label_normalize(value: str) -> str:
    """`vision-label-normalizer-v1`: NFC, trim, whitespace collapse. No casefold/translation."""

    return " ".join(unicodedata.normalize("NFC", value).split())


class TextLanguageDeclarationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["DECLARED", "MIXED", "NOT_DETERMINED"]
    tags: tuple[_LanguageTag, ...] = ()
    is_ground_truth: Literal[False] = False

    @field_validator("tags")
    @classmethod
    def _requires_unique_lowercase_canonical_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        lowered = tuple(tag.lower() for tag in value)
        if len(set(lowered)) != len(lowered):
            raise ValueError("language tags must not contain duplicates")
        return tuple(sorted(lowered))

    @model_validator(mode="after")
    def _requires_tag_count_matches_status(self) -> TextLanguageDeclarationV1:
        if self.status == "DECLARED" and len(self.tags) != 1:
            raise ValueError("DECLARED requires exactly one language tag")
        if self.status == "MIXED" and len(self.tags) < 2:
            raise ValueError("MIXED requires at least two distinct language tags")
        if self.status == "NOT_DETERMINED" and self.tags:
            raise ValueError("NOT_DETERMINED must not carry language tags")
        return self


class ObservedTextV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=1)
    language: TextLanguageDeclarationV1

    @field_validator("value")
    @classmethod
    def _normalizes_value(cls, value: str) -> str:
        normalized = vision_label_normalize(value)
        if not normalized:
            raise ValueError("value must not be empty after normalization")
        return normalized


class VisionProfileId(StrEnum):
    """Phase A defines fake entries only."""

    FAKE_DETERMINISTIC_V1 = "FAKE_DETERMINISTIC_V1"


class VisionProfileV1(BaseModel):
    """Phase A catalog entries are deterministic fakes; no model/weight/runtime provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: VisionProfileId
    adapter_kind: Literal["DETERMINISTIC_FAKE"] = "DETERMINISTIC_FAKE"
    task: Literal["structured_observation"] = "structured_observation"
    compute_profile: Literal["NONE"] = "NONE"
    timeout_seconds: float = Field(gt=0)
    structured_output_mode: Literal["STRICT_JSON_OBJECT"] = "STRICT_JSON_OBJECT"
    adapter_version: str = Field(min_length=1)
    timeout_retry_policy: Literal["NEVER_RETRY"] = "NEVER_RETRY"


class VisionProfileCatalogV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["VisionProfileCatalogV1"] = "VisionProfileCatalogV1"
    contract_version: Literal["1.0"] = "1.0"
    profiles: tuple[VisionProfileV1, ...]

    @model_validator(mode="after")
    def _requires_unique_profile_ids(self) -> VisionProfileCatalogV1:
        profile_ids = tuple(profile.profile_id for profile in self.profiles)
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile IDs must be unique")
        return self

    def resolve(self, profile_id: VisionProfileId) -> VisionProfileV1:
        for profile in self.profiles:
            if profile.profile_id is profile_id:
                return profile
        raise ValueError(f"profile is absent from catalog: {profile_id}")


def vision_profile_catalog() -> VisionProfileCatalogV1:
    """Single static, versioned Phase A catalog: deterministic fake entries only."""

    return VisionProfileCatalogV1(
        profiles=(
            VisionProfileV1(
                profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
                timeout_seconds=30.0,
                adapter_version="deterministic-fixture-vision-adapter-v1",
            ),
        )
    )


def vision_profile_config_hash(profile: VisionProfileV1) -> str:
    payload = dumps(profile.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def vision_profile_catalog_hash(catalog: VisionProfileCatalogV1) -> str:
    payload = dumps(catalog.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


class VisionUnderstandingRequestV1(BaseModel):
    """Structurally valid request. An unknown profile is rejected before the port runs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["VisionUnderstandingRequestV1"] = "VisionUnderstandingRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    correlation_id: str = Field(min_length=1)
    source_image_ref: VisionImageReferenceV1
    processing_image_ref: VisionImageReferenceV1 | None = None
    derivation_provenance: ImageDerivationProvenanceV1 | None = None
    media_validation: VisionMediaValidationProvenanceV1 | None = None
    requested_profile_id: VisionProfileId

    @model_validator(mode="after")
    def _requires_valid_derivation_and_profile(self) -> VisionUnderstandingRequestV1:
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
        vision_profile_catalog().resolve(self.requested_profile_id)
        return self


class EntityCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    label: ObservedTextV1
    confidence: _Confidence = Field(ge=0.0, le=1.0)


class ActionCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    label: ObservedTextV1
    actor_ref: _ObservationRef | None = None
    object_ref: _ObservationRef | None = None
    confidence: _Confidence = Field(ge=0.0, le=1.0)


class RelationCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    predicate: ObservedTextV1
    subject_ref: _ObservationRef
    object_ref: _ObservationRef
    confidence: _Confidence = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _forbids_self_reference(self) -> RelationCandidateV1:
        if self.subject_ref == self.object_ref:
            raise ValueError("REFERENCE_INTEGRITY_VIOLATION: relation must not self-reference")
        return self


class ThemeCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    label: ObservedTextV1
    evidence_refs: tuple[_ObservationRef, ...] = Field(min_length=1)
    confidence: _Confidence = Field(ge=0.0, le=1.0)


class AmbiguousRegionCandidateV1(BaseModel):
    """No geometry in Phase A; not a valid evidence-reference target; no confidence field."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: _ObservationRef
    note: ObservedTextV1


def _validate_observation_references(
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

    entity_or_action = frozenset({"ENTITY", "ACTION"})
    entity_only = frozenset({"ENTITY"})
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


class VisionResultEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["VisionUnderstandingResultV1"] = "VisionUnderstandingResultV1"
    contract_version: Literal["1.0"] = "1.0"
    correlation_id: str = Field(min_length=1)
    executed_at: datetime
    source_image_ref: VisionImageReferenceV1
    profile_id: VisionProfileId
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


class VisionUnderstandingSuccessV1(VisionResultEnvelopeV1):
    status: Literal["SUCCEEDED"] = "SUCCEEDED"
    entities: tuple[EntityCandidateV1, ...]
    actions: tuple[ActionCandidateV1, ...]
    relations: tuple[RelationCandidateV1, ...]
    themes: tuple[ThemeCandidateV1, ...]
    ambiguous_regions: tuple[AmbiguousRegionCandidateV1, ...]
    adapter_version: str = Field(min_length=1)
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _requires_passed_policy_state(self) -> VisionUnderstandingSuccessV1:
        if self.policy_execution_state != "PASSED":
            raise ValueError("a SUCCEEDED result requires policy_execution_state=PASSED")
        return self

    @model_validator(mode="after")
    def _requires_consistent_observation_references(self) -> VisionUnderstandingSuccessV1:
        _validate_observation_references(
            self.entities, self.actions, self.relations, self.themes, self.ambiguous_regions
        )
        return self


class VisionProhibitedClaimCategory(StrEnum):
    """Exactly the six approved prohibited-claim categories."""

    PSYCHOLOGICAL_INFERENCE_CLAIM = "PSYCHOLOGICAL_INFERENCE_CLAIM"
    PERSONALITY_CLAIM = "PERSONALITY_CLAIM"
    DIAGNOSTIC_CLAIM = "DIAGNOSTIC_CLAIM"
    MENTAL_STATE_CLAIM = "MENTAL_STATE_CLAIM"
    TRAUMA_CLAIM = "TRAUMA_CLAIM"
    DEVELOPMENTAL_CLAIM = "DEVELOPMENTAL_CLAIM"


class VisionNonPolicyErrorDetail(StrEnum):
    """Every closed input/runtime/schema detail token; disjoint from the prohibited-claim set."""

    MEDIA_VALIDATION_NOT_PASSED = "MEDIA_VALIDATION_NOT_PASSED"
    MEDIA_VALIDATION_PROVENANCE_MISSING = "MEDIA_VALIDATION_PROVENANCE_MISSING"
    SOURCE_IMAGE_UNREADABLE = "SOURCE_IMAGE_UNREADABLE"
    SOURCE_IMAGE_HASH_MISMATCH = "SOURCE_IMAGE_HASH_MISMATCH"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    TIMEOUT_BUDGET_EXCEEDED = "TIMEOUT_BUDGET_EXCEEDED"
    TRANSIENT_RUNTIME_FAILURE = "TRANSIENT_RUNTIME_FAILURE"
    PERMANENT_RUNTIME_FAILURE = "PERMANENT_RUNTIME_FAILURE"
    OUTPUT_MAPPING_FAILED = "OUTPUT_MAPPING_FAILED"
    DUPLICATE_OBSERVATION_ID = "DUPLICATE_OBSERVATION_ID"
    REFERENCE_INTEGRITY_VIOLATION = "REFERENCE_INTEGRITY_VIOLATION"


VisionFailureDetail = VisionNonPolicyErrorDetail | VisionProhibitedClaimCategory


class VisionErrorCode(StrEnum):
    INPUT_NOT_VALIDATED = "INPUT_NOT_VALIDATED"
    VISION_MODEL_UNAVAILABLE = "VISION_MODEL_UNAVAILABLE"
    VISION_TIMEOUT = "VISION_TIMEOUT"
    VISION_PROVIDER_FAILURE = "VISION_PROVIDER_FAILURE"
    VISION_SCHEMA_INVALID = "VISION_SCHEMA_INVALID"
    PROHIBITED_CLAIM_DETECTED = "PROHIBITED_CLAIM_DETECTED"


class _NonPolicyDetailRule:
    __slots__ = ("error_code", "retryable", "attempt_number", "allowed_repair")

    def __init__(
        self,
        error_code: VisionErrorCode,
        retryable: bool,
        attempt_number: int,
        allowed_repair: frozenset[bool],
    ) -> None:
        self.error_code = error_code
        self.retryable = retryable
        self.attempt_number = attempt_number
        self.allowed_repair = allowed_repair


_ALWAYS_NO_REPAIR = frozenset({False})
_EITHER_REPAIR = frozenset({True, False})

_NON_POLICY_DETAIL_RULES: dict[VisionNonPolicyErrorDetail, _NonPolicyDetailRule] = {
    VisionNonPolicyErrorDetail.MEDIA_VALIDATION_NOT_PASSED: _NonPolicyDetailRule(
        VisionErrorCode.INPUT_NOT_VALIDATED, False, 0, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.MEDIA_VALIDATION_PROVENANCE_MISSING: _NonPolicyDetailRule(
        VisionErrorCode.INPUT_NOT_VALIDATED, False, 0, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.SOURCE_IMAGE_UNREADABLE: _NonPolicyDetailRule(
        VisionErrorCode.INPUT_NOT_VALIDATED, False, 0, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.SOURCE_IMAGE_HASH_MISMATCH: _NonPolicyDetailRule(
        VisionErrorCode.INPUT_NOT_VALIDATED, False, 0, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.MODEL_LOAD_FAILED: _NonPolicyDetailRule(
        VisionErrorCode.VISION_MODEL_UNAVAILABLE, False, 1, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.DEVICE_UNAVAILABLE: _NonPolicyDetailRule(
        VisionErrorCode.VISION_MODEL_UNAVAILABLE, False, 1, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.TIMEOUT_BUDGET_EXCEEDED: _NonPolicyDetailRule(
        VisionErrorCode.VISION_TIMEOUT, False, 1, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.TRANSIENT_RUNTIME_FAILURE: _NonPolicyDetailRule(
        VisionErrorCode.VISION_PROVIDER_FAILURE, True, 2, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.PERMANENT_RUNTIME_FAILURE: _NonPolicyDetailRule(
        VisionErrorCode.VISION_PROVIDER_FAILURE, False, 1, _ALWAYS_NO_REPAIR
    ),
    VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED: _NonPolicyDetailRule(
        VisionErrorCode.VISION_SCHEMA_INVALID, False, 1, _EITHER_REPAIR
    ),
    VisionNonPolicyErrorDetail.DUPLICATE_OBSERVATION_ID: _NonPolicyDetailRule(
        VisionErrorCode.VISION_SCHEMA_INVALID, False, 1, _EITHER_REPAIR
    ),
    VisionNonPolicyErrorDetail.REFERENCE_INTEGRITY_VIOLATION: _NonPolicyDetailRule(
        VisionErrorCode.VISION_SCHEMA_INVALID, False, 1, _EITHER_REPAIR
    ),
}


class VisionUnderstandingFailureV1(VisionResultEnvelopeV1):
    status: Literal["FAILED"] = "FAILED"
    error_code: VisionErrorCode
    error_detail: VisionFailureDetail
    retryable: bool

    @model_validator(mode="after")
    def _requires_a_consistent_failure_matrix_row(self) -> VisionUnderstandingFailureV1:
        if self.error_code == VisionErrorCode.PROHIBITED_CLAIM_DETECTED:
            if not isinstance(self.error_detail, VisionProhibitedClaimCategory):
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires a prohibited-claim category")
            if self.policy_execution_state != "BLOCKED":
                raise ValueError(
                    "PROHIBITED_CLAIM_DETECTED requires policy_execution_state=BLOCKED"
                )
            if self.retryable is not False:
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires retryable=false")
            if self.attempt_number != 1:
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires attempt_number=1")
            if self.repair_attempted is not False:
                raise ValueError("PROHIBITED_CLAIM_DETECTED requires repair_attempted=false")
            return self

        if not isinstance(self.error_detail, VisionNonPolicyErrorDetail):
            raise ValueError(f"{self.error_code} requires a non-policy error detail")
        rule = _NON_POLICY_DETAIL_RULES[self.error_detail]
        if self.error_code != rule.error_code:
            raise ValueError(f"{self.error_detail} is not valid for error_code={self.error_code}")
        if self.policy_execution_state != "NOT_EXECUTED":
            raise ValueError(f"{self.error_code} requires policy_execution_state=NOT_EXECUTED")
        if self.retryable is not rule.retryable:
            raise ValueError(f"{self.error_detail} requires retryable={rule.retryable}")
        if self.attempt_number != rule.attempt_number:
            raise ValueError(f"{self.error_detail} requires attempt_number={rule.attempt_number}")
        if self.repair_attempted not in rule.allowed_repair:
            raise ValueError(
                f"{self.error_detail} does not permit repair_attempted={self.repair_attempted}"
            )
        return self


VisionUnderstandingResultV1 = Annotated[
    VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1, Field(discriminator="status")
]


_BOUNDARY_UNICODE_CATEGORIES = frozenset(
    {"Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Zs", "Zl", "Zp"}
)


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def vision_policy_match_view(value: str) -> str:
    """`vision-policy-match-view-v2`: NFC, casefold, P*/Z* -> space; S* symbols kept as content."""

    text = _collapse_whitespace(unicodedata.normalize("NFC", value))
    text = unicodedata.normalize("NFC", text.casefold())
    mapped = "".join(
        " " if unicodedata.category(character) in _BOUNDARY_UNICODE_CATEGORIES else character
        for character in text
    )
    return _collapse_whitespace(mapped)


def vision_policy_match_view_tokens(value: str) -> tuple[str, ...]:
    view = vision_policy_match_view(value)
    return tuple(view.split(" ")) if view else ()


class ProhibitedLexiconEntryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    term_normalized: str = Field(min_length=1)
    category: VisionProhibitedClaimCategory
    match_mode: Literal["WHOLE_TOKEN_SEQUENCE", "WHOLE_FIELD"]

    @model_validator(mode="after")
    def _requires_term_already_in_canonical_match_view_form(self) -> ProhibitedLexiconEntryV1:
        if vision_policy_match_view(self.term_normalized) != self.term_normalized:
            raise ValueError(
                "term_normalized must already be in vision-policy-match-view-v2 canonical form"
            )
        if not vision_policy_match_view_tokens(self.term_normalized):
            raise ValueError("term_normalized must tokenize to at least one token")
        return self


class ProhibitedLexiconV1(BaseModel):
    """Synthetic-only, deterministic, versioned. Never contains real child data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lexicon_version: str = Field(min_length=1)
    match_view_version: str = Field(min_length=1)
    entries: tuple[ProhibitedLexiconEntryV1, ...]


class VisionFixtureManifestEntryV1(BaseModel):
    """Synthetic Phase A fixture declaration; no image payload is stored here."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    scenario: str = Field(min_length=1)
    expected_status: Literal["SUCCEEDED", "FAILED"]
    expected_error_code: VisionErrorCode | None = None
    synthetic_data: Literal[True] = True
