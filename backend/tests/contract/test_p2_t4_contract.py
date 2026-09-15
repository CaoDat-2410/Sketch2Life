"""Independent, hand-authored schema-parity oracle for `P2T4.P2T4FusedResultV1@1.0`.

The oracle below lists every contract field with its requiredness/nullability, every closed
enum and literal, the cross-field invariants, the rejection precedence, the canonical sort
keys, and the privacy rules, transcribed by hand from the frozen G1 contract. It is checked
behaviorally: samples are validated, serialized key sets are compared against the oracle, and
mutations must be rejected. It never loads a schema snapshot, calls `json_schema()`, reads
`model_fields`, or derives expectations from `p2_t4_fusion.py`.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from sketch2life.contracts.schemas.p2_t4_fusion import (
    P2T4AsrFailureReferenceV1,
    P2T4CandidateKind,
    P2T4CertaintyStatus,
    P2T4ConflictReasonCode,
    P2T4ConflictV1,
    P2T4ExpectedIdentity,
    P2T4FailedModality,
    P2T4FusedActionV1,
    P2T4FusedEntityV1,
    P2T4FusedRelationV1,
    P2T4FusedResultStatus,
    P2T4FusedResultV1,
    P2T4FusedThemeV1,
    P2T4FusionInputRejectionV1,
    P2T4FusionPolicyConfigV1,
    P2T4InputSlot,
    P2T4NarrationClaimRefV1,
    P2T4ObservationUncertaintyV1,
    P2T4ObservedIdentity,
    P2T4ObservedStatus,
    P2T4RejectionCode,
    P2T4RejectionFieldCode,
    P2T4RejectionPhase,
    P2T4SourceIdentity,
    P2T4SourceResultRefV1,
    P2T4UncertaintySummaryV1,
    P2T4UpstreamFailureRefV1,
    P2T4VisionFailureReferenceV1,
    canonical_json,
)

# --- hand-authored oracle ------------------------------------------------------------------

# Field spec: (required, nullable). A "fixed" literal field always serializes with its one
# allowed value; it is listed under LITERALS and is rejected for any other value.
ORACLE_FIELDS: dict[str, dict[str, tuple[bool, bool]]] = {
    "P2T4FusionInputRejectionV1": {
        "contract_name": (True, False),
        "contract_version": (True, False),
        "status": (True, False),
        "input_slot": (True, False),
        "phase": (True, False),
        "code": (True, False),
        "expected_identity": (True, False),
        "observed_identity": (True, False),
        "observed_status": (True, True),
        "field_code": (True, False),
    },
    "P2T4SourceResultRefV1": {
        "identity": (True, False),
        "status": (True, False),
        "result_sha256": (True, False),
    },
    "P2T4NarrationClaimRefV1": {
        "segment_index": (True, False),
        "claim_start": (True, False),
        "claim_end": (True, False),
    },
    "P2T4FusionPolicyConfigV1": {
        "contract_name": (True, False),
        "contract_version": (True, False),
        "config_version": (True, False),
        "entity_match_mode": (True, False),
        "narration_weight_mode": (True, False),
        "confidence_floor": (True, False),
        "uncertainty_formula_id": (True, False),
        "match_view_version": (True, False),
        "negation_cues": (True, False),
        "negation_window_tokens": (True, False),
        "corroboration_increment": (True, False),
    },
    "P2T4UpstreamFailureRefV1": {
        "contract_name": (True, False),
        "contract_version": (True, False),
        "failed_modality": (True, False),
        "asr_failure_ref": (True, True),
        "vision_failure_ref": (True, True),
    },
    "P2T4AsrFailureReferenceV1": {
        "source_asr_result_ref": (True, False),
        "error_code": (True, False),
        "error_detail": (True, False),
        "attempt_number": (True, False),
        "retryable": (True, False),
        "repair_attempted": (True, False),
    },
    "P2T4VisionFailureReferenceV1": {
        "source_vision_result_ref": (True, False),
        "error_code": (True, False),
        "error_detail": (True, False),
        "attempt_number": (True, False),
        "retryable": (True, False),
        "repair_attempted": (True, False),
        "policy_execution_state": (True, False),
    },
    "P2T4FusedEntityV1": {
        "fused_observation_id": (True, False),
        "source_observation_ref": (True, False),
        "label": (True, False),
        "narration_support_applied": (True, False),
        "narration_support_ref": (True, True),
        "primary_interpretation": (True, False),
    },
    "P2T4FusedActionV1": {
        "fused_observation_id": (True, False),
        "source_observation_ref": (True, False),
        "label": (True, False),
        "actor_ref": (True, True),
        "object_ref": (True, True),
        "narration_support_applied": (True, False),
        "narration_support_ref": (True, True),
        "primary_interpretation": (True, False),
    },
    "P2T4FusedRelationV1": {
        "fused_observation_id": (True, False),
        "source_observation_ref": (True, False),
        "predicate": (True, False),
        "subject_ref": (True, False),
        "object_ref": (True, False),
        "narration_support_applied": (True, False),
        "narration_support_ref": (True, True),
        "primary_interpretation": (True, False),
    },
    "P2T4FusedThemeV1": {
        "fused_observation_id": (True, False),
        "source_observation_ref": (True, False),
        "label": (True, False),
        "evidence_refs": (True, False),
    },
    "P2T4ConflictV1": {
        "conflict_id": (True, False),
        "reason_code": (True, False),
        "vision_claim_ref": (True, False),
        "narration_claim_ref": (True, True),
        "recommended_reviewer_attention": (True, False),
    },
    "P2T4ObservationUncertaintyV1": {
        "observation_id": (True, False),
        "candidate_kind": (True, False),
        "certainty_status": (True, False),
        "certainty": (True, True),
    },
    "P2T4UncertaintySummaryV1": {
        "formula_id": (True, False),
        "per_observation": (True, False),
    },
    "P2T4FusedResultV1": {
        "contract_name": (True, False),
        "contract_version": (True, False),
        "status": (True, False),
        "correlation_id": (True, False),
        "executed_at": (True, False),
        "source_asr_result_ref": (True, False),
        "source_vision_result_ref": (True, False),
        "fusion_policy_config_hash": (True, False),
        "entities": (True, False),
        "actions": (True, False),
        "relations": (True, False),
        "themes": (True, False),
        "conflicts": (True, False),
        "uncertainty": (True, False),
        "upstream_failure": (True, True),
    },
}

ORACLE_LITERALS: dict[str, dict[str, object]] = {
    "P2T4FusionInputRejectionV1": {
        "contract_name": "P2T4FusionInputRejectionV1",
        "contract_version": "1.0",
        "status": "REJECTED",
    },
    "P2T4FusionPolicyConfigV1": {
        "contract_name": "P2T4FusionPolicyConfigV1",
        "contract_version": "1.0",
        "entity_match_mode": "WHOLE_TOKEN_SEQUENCE",
        "narration_weight_mode": "SUPPORT_ONLY",
        "uncertainty_formula_id": "AGREEMENT_WEIGHTED_V1",
        "match_view_version": "vision_policy_match_view-v2",
        "negation_cues": (
            ("not",),
            ("no",),
            ("never",),
            ("isn", "t"),
            ("doesn", "t"),
            ("didn", "t"),
        ),
        "negation_window_tokens": 3,
        "corroboration_increment": "0.10",
    },
    "P2T4UpstreamFailureRefV1": {
        "contract_name": "P2T4UpstreamFailureRefV1",
        "contract_version": "1.0",
    },
    "P2T4ConflictV1": {"recommended_reviewer_attention": True},
    "P2T4UncertaintySummaryV1": {"formula_id": "AGREEMENT_WEIGHTED_V1"},
    "P2T4FusedResultV1": {"contract_name": "P2T4FusedResultV1", "contract_version": "1.0"},
}

ORACLE_ENUMS: dict[str, list[str]] = {
    "fused_result_status": ["FUSED", "UPSTREAM_FAILURE"],
    "source_identity": ["P2.AsrResultV1@1.0", "P2.VisionUnderstandingResultV1@1.0"],
    "input_slot": ["ASR", "VISION", "BOTH"],
    "rejection_phase": ["IDENTITY_VERSION", "STRICT_VALIDATION", "ADMISSIBILITY", "CORRELATION"],
    "rejection_code": [
        "UNKNOWN_INPUT",
        "WRONG_FAMILY",
        "UNSUPPORTED_VERSION",
        "INVALID_DISCRIMINATOR",
        "INVALID_STRUCTURE",
        "CORRELATION_MISMATCH",
    ],
    "expected_identity": ["NONE", "P2.AsrResultV1@1.0", "P2.VisionUnderstandingResultV1@1.0"],
    "observed_identity": [
        "UNKNOWN",
        "P2.AsrResultV1@1.0",
        "P2.VisionUnderstandingResultV1@1.0",
        "FEAT018.LiveAsrResultV1@1.0",
        "FEAT018.LiveVisionUnderstandingResultV1@1.0",
        "P2.VisionUnderstandingResultV2@2.0",
    ],
    "observed_status": ["SUCCEEDED", "FAILED", "UNKNOWN"],
    "field_code": [
        "NONE",
        "CONTRACT_NAME",
        "CONTRACT_VERSION",
        "STATUS",
        "CORRELATION_ID",
        "SOURCE_REFERENCE",
        "FAILURE_BRANCH",
        "UPSTREAM_TYPE",
        "DUPLICATE_SEGMENT_INDEX",
    ],
    "failed_modality": ["ASR", "VISION", "BOTH"],
    "conflict_reason": [
        "ENTITY_ATTRIBUTE_CONTRADICTION",
        "ACTION_CONTRADICTION",
        "RELATION_CONTRADICTION",
        "LOW_CONFIDENCE_EVIDENCE",
    ],
    "candidate_kind": ["ENTITY", "ACTION", "RELATION"],
    "certainty_status": ["MEASURED", "NOT_MEASURED", "NOT_APPLICABLE_CONFLICTING"],
    "source_status": ["SUCCEEDED", "FAILED"],
    "failed_policy_state": ["NOT_EXECUTED", "BLOCKED"],
}

ORACLE_PHASE_CODES: dict[str, list[str]] = {
    "IDENTITY_VERSION": ["UNKNOWN_INPUT", "WRONG_FAMILY", "UNSUPPORTED_VERSION"],
    "STRICT_VALIDATION": ["INVALID_DISCRIMINATOR", "INVALID_STRUCTURE"],
    "ADMISSIBILITY": ["INVALID_STRUCTURE"],
    "CORRELATION": ["CORRELATION_MISMATCH"],
}

ORACLE_REJECTION_PRECEDENCE = (
    "IDENTITY_VERSION",
    "STRICT_VALIDATION",
    "ADMISSIBILITY",
    "CORRELATION",
)
ORACLE_CANDIDATE_KIND_RANK = {"ENTITY": 0, "ACTION": 1, "RELATION": 2}
ORACLE_CONFLICT_REASON_RANK = {
    "ENTITY_ATTRIBUTE_CONTRADICTION": 0,
    "ACTION_CONTRADICTION": 1,
    "RELATION_CONTRADICTION": 2,
    "LOW_CONFIDENCE_EVIDENCE": 3,
}

MODELS: dict[str, type[BaseModel]] = {
    "P2T4FusionInputRejectionV1": P2T4FusionInputRejectionV1,
    "P2T4SourceResultRefV1": P2T4SourceResultRefV1,
    "P2T4NarrationClaimRefV1": P2T4NarrationClaimRefV1,
    "P2T4FusionPolicyConfigV1": P2T4FusionPolicyConfigV1,
    "P2T4UpstreamFailureRefV1": P2T4UpstreamFailureRefV1,
    "P2T4AsrFailureReferenceV1": P2T4AsrFailureReferenceV1,
    "P2T4VisionFailureReferenceV1": P2T4VisionFailureReferenceV1,
    "P2T4FusedEntityV1": P2T4FusedEntityV1,
    "P2T4FusedActionV1": P2T4FusedActionV1,
    "P2T4FusedRelationV1": P2T4FusedRelationV1,
    "P2T4FusedThemeV1": P2T4FusedThemeV1,
    "P2T4ConflictV1": P2T4ConflictV1,
    "P2T4ObservationUncertaintyV1": P2T4ObservationUncertaintyV1,
    "P2T4UncertaintySummaryV1": P2T4UncertaintySummaryV1,
    "P2T4FusedResultV1": P2T4FusedResultV1,
}

ENUM_TYPES: dict[str, type[Any]] = {
    "fused_result_status": P2T4FusedResultStatus,
    "source_identity": P2T4SourceIdentity,
    "input_slot": P2T4InputSlot,
    "rejection_phase": P2T4RejectionPhase,
    "rejection_code": P2T4RejectionCode,
    "expected_identity": P2T4ExpectedIdentity,
    "observed_identity": P2T4ObservedIdentity,
    "observed_status": P2T4ObservedStatus,
    "field_code": P2T4RejectionFieldCode,
    "failed_modality": P2T4FailedModality,
    "conflict_reason": P2T4ConflictReasonCode,
    "candidate_kind": P2T4CandidateKind,
    "certainty_status": P2T4CertaintyStatus,
}


# --- hand-authored valid samples -----------------------------------------------------------

_HEX = "0" * 64
_TEXT = {
    "value": "house",
    "language": {"status": "NOT_DETERMINED", "tags": [], "is_ground_truth": False},
}
_REF = {"segment_index": 0, "claim_start": 1, "claim_end": 2}
_ASR_REF_OK = {"identity": "P2.AsrResultV1@1.0", "status": "SUCCEEDED", "result_sha256": _HEX}
_VISION_REF_OK = {
    "identity": "P2.VisionUnderstandingResultV1@1.0",
    "status": "SUCCEEDED",
    "result_sha256": _HEX,
}
_ASR_REF_FAILED = {**_ASR_REF_OK, "status": "FAILED"}
_VISION_REF_FAILED = {**_VISION_REF_OK, "status": "FAILED"}


def _conflict_id(reason: str, observation_id: str) -> str:
    payload = reason.encode("utf-8") + b"\x00" + observation_id.encode("utf-8")
    return "P2T4-CONFLICT-" + hashlib.sha256(payload).hexdigest()


def _entity(observation_id: str, support: dict[str, int] | None, primary: bool) -> dict[str, Any]:
    return {
        "fused_observation_id": observation_id,
        "source_observation_ref": observation_id,
        "label": _TEXT,
        "narration_support_applied": support is not None,
        "narration_support_ref": support,
        "primary_interpretation": primary,
    }


def _row(observation_id: str, kind: str, status: str, certainty: float | None) -> dict[str, Any]:
    return {
        "observation_id": observation_id,
        "candidate_kind": kind,
        "certainty_status": status,
        "certainty": certainty,
    }


SAMPLE_ASR_FAILURE = {
    "source_asr_result_ref": _ASR_REF_FAILED,
    "error_code": "ASR_TIMEOUT",
    "error_detail": "TIMEOUT_BUDGET_EXCEEDED",
    "attempt_number": 1,
    "retryable": True,
    "repair_attempted": False,
}
SAMPLE_VISION_FAILURE = {
    "source_vision_result_ref": _VISION_REF_FAILED,
    "error_code": "PROHIBITED_CLAIM_DETECTED",
    "error_detail": "MENTAL_STATE_CLAIM",
    "attempt_number": 1,
    "retryable": False,
    "repair_attempted": False,
    "policy_execution_state": "BLOCKED",
}
SAMPLE_CONFLICT = {
    "conflict_id": _conflict_id("ENTITY_ATTRIBUTE_CONTRADICTION", "e-2"),
    "reason_code": "ENTITY_ATTRIBUTE_CONTRADICTION",
    "vision_claim_ref": "e-2",
    "narration_claim_ref": {"segment_index": 0, "claim_start": 3, "claim_end": 4},
    "recommended_reviewer_attention": True,
}
SAMPLE_FUSED_RESULT: dict[str, Any] = {
    "contract_name": "P2T4FusedResultV1",
    "contract_version": "1.0",
    "status": "FUSED",
    "correlation_id": "corr-1",
    "executed_at": datetime(2026, 9, 15, 12, 0, tzinfo=UTC),
    "source_asr_result_ref": _ASR_REF_OK,
    "source_vision_result_ref": _VISION_REF_OK,
    "fusion_policy_config_hash": _HEX,
    "entities": [_entity("e-1", _REF, True), _entity("e-2", None, False)],
    "actions": [
        {
            "fused_observation_id": "a-1",
            "source_observation_ref": "a-1",
            "label": _TEXT,
            "actor_ref": "e-1",
            "object_ref": None,
            "narration_support_applied": False,
            "narration_support_ref": None,
            "primary_interpretation": True,
        }
    ],
    "relations": [
        {
            "fused_observation_id": "r-1",
            "source_observation_ref": "r-1",
            "predicate": _TEXT,
            "subject_ref": "e-1",
            "object_ref": "a-1",
            "narration_support_applied": False,
            "narration_support_ref": None,
            "primary_interpretation": True,
        }
    ],
    "themes": [
        {
            "fused_observation_id": "t-1",
            "source_observation_ref": "t-1",
            "label": _TEXT,
            "evidence_refs": ["e-1", "r-1", "e-1"],
        }
    ],
    "conflicts": [SAMPLE_CONFLICT],
    "uncertainty": {
        "formula_id": "AGREEMENT_WEIGHTED_V1",
        "per_observation": [
            _row("e-1", "ENTITY", "MEASURED", 0.9),
            _row("e-2", "ENTITY", "NOT_APPLICABLE_CONFLICTING", None),
            _row("a-1", "ACTION", "NOT_MEASURED", None),
            _row("r-1", "RELATION", "MEASURED", 0.4),
        ],
    },
    "upstream_failure": None,
}
SAMPLE_UPSTREAM_FAILURE_RESULT: dict[str, Any] = {
    **SAMPLE_FUSED_RESULT,
    "status": "UPSTREAM_FAILURE",
    "source_asr_result_ref": _ASR_REF_FAILED,
    "entities": [],
    "actions": [],
    "relations": [],
    "themes": [],
    "conflicts": [],
    "uncertainty": {"formula_id": "AGREEMENT_WEIGHTED_V1", "per_observation": []},
    "upstream_failure": {
        "contract_name": "P2T4UpstreamFailureRefV1",
        "contract_version": "1.0",
        "failed_modality": "ASR",
        "asr_failure_ref": SAMPLE_ASR_FAILURE,
        "vision_failure_ref": None,
    },
}

SAMPLES: dict[str, dict[str, Any]] = {
    "P2T4FusionInputRejectionV1": {
        "contract_name": "P2T4FusionInputRejectionV1",
        "contract_version": "1.0",
        "status": "REJECTED",
        "input_slot": "ASR",
        "phase": "ADMISSIBILITY",
        "code": "INVALID_STRUCTURE",
        "expected_identity": "P2.AsrResultV1@1.0",
        "observed_identity": "P2.AsrResultV1@1.0",
        "observed_status": "SUCCEEDED",
        "field_code": "DUPLICATE_SEGMENT_INDEX",
    },
    "P2T4SourceResultRefV1": _ASR_REF_OK,
    "P2T4NarrationClaimRefV1": _REF,
    "P2T4FusionPolicyConfigV1": {
        "contract_name": "P2T4FusionPolicyConfigV1",
        "contract_version": "1.0",
        "config_version": "policy-v1",
        "entity_match_mode": "WHOLE_TOKEN_SEQUENCE",
        "narration_weight_mode": "SUPPORT_ONLY",
        "confidence_floor": 0.5,
        "uncertainty_formula_id": "AGREEMENT_WEIGHTED_V1",
        "match_view_version": "vision_policy_match_view-v2",
        "negation_cues": [["not"], ["no"], ["never"], ["isn", "t"], ["doesn", "t"], ["didn", "t"]],
        "negation_window_tokens": 3,
        "corroboration_increment": "0.10",
    },
    "P2T4UpstreamFailureRefV1": SAMPLE_UPSTREAM_FAILURE_RESULT["upstream_failure"],
    "P2T4AsrFailureReferenceV1": SAMPLE_ASR_FAILURE,
    "P2T4VisionFailureReferenceV1": SAMPLE_VISION_FAILURE,
    "P2T4FusedEntityV1": _entity("e-1", _REF, True),
    "P2T4FusedActionV1": SAMPLE_FUSED_RESULT["actions"][0],
    "P2T4FusedRelationV1": SAMPLE_FUSED_RESULT["relations"][0],
    "P2T4FusedThemeV1": SAMPLE_FUSED_RESULT["themes"][0],
    "P2T4ConflictV1": SAMPLE_CONFLICT,
    "P2T4ObservationUncertaintyV1": _row("e-1", "ENTITY", "MEASURED", 0.9),
    "P2T4UncertaintySummaryV1": SAMPLE_FUSED_RESULT["uncertainty"],
    "P2T4FusedResultV1": SAMPLE_FUSED_RESULT,
}

# Nullable fields whose null form needs a coupled change to stay valid.
_NULL_COUPLING: dict[tuple[str, str], dict[str, Any]] = {
    ("P2T4FusionInputRejectionV1", "observed_status"): {
        "phase": "IDENTITY_VERSION",
        "code": "UNKNOWN_INPUT",
        "observed_identity": "UNKNOWN",
        "field_code": "UPSTREAM_TYPE",
    },
    ("P2T4FusedEntityV1", "narration_support_ref"): {"narration_support_applied": False},
    ("P2T4FusedActionV1", "narration_support_ref"): {"narration_support_applied": False},
    ("P2T4FusedRelationV1", "narration_support_ref"): {"narration_support_applied": False},
    ("P2T4ObservationUncertaintyV1", "certainty"): {"certainty_status": "NOT_MEASURED"},
    ("P2T4ConflictV1", "narration_claim_ref"): {
        "reason_code": "LOW_CONFIDENCE_EVIDENCE",
        "conflict_id": _conflict_id("LOW_CONFIDENCE_EVIDENCE", "e-2"),
    },
    ("P2T4UpstreamFailureRefV1", "asr_failure_ref"): {
        "failed_modality": "VISION",
        "vision_failure_ref": SAMPLE_VISION_FAILURE,
    },
}


def _validate(name: str, payload: dict[str, Any]) -> BaseModel:
    return MODELS[name].model_validate(payload)


def _mutated(name: str, **changes: Any) -> dict[str, Any]:
    payload = copy.deepcopy(SAMPLES[name])
    payload.update(changes)
    return payload


# --- field parity ------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(ORACLE_FIELDS))
def test_every_model_serializes_exactly_the_oracle_fields(name: str) -> None:
    instance = _validate(name, SAMPLES[name])
    assert set(instance.model_dump()) == set(ORACLE_FIELDS[name])
    assert set(MODELS) == set(ORACLE_FIELDS)


@pytest.mark.parametrize("name", sorted(ORACLE_FIELDS))
def test_required_non_literal_fields_cannot_be_omitted(name: str) -> None:
    literals = ORACLE_LITERALS.get(name, {})
    for field, (required, _) in ORACLE_FIELDS[name].items():
        assert required
        if field in literals:
            continue
        payload = copy.deepcopy(SAMPLES[name])
        payload.pop(field)
        with pytest.raises(ValidationError):
            _validate(name, payload)


@pytest.mark.parametrize("name", sorted(ORACLE_FIELDS))
def test_nullability_matches_the_oracle(name: str) -> None:
    for field, (_, nullable) in ORACLE_FIELDS[name].items():
        payload = _mutated(name, **{field: None})
        payload.update(_NULL_COUPLING.get((name, field), {}))
        if nullable:
            assert getattr(_validate(name, payload), field) is None
        else:
            with pytest.raises(ValidationError):
                _validate(name, payload)


@pytest.mark.parametrize("name", sorted(ORACLE_LITERALS))
def test_literal_fields_accept_only_their_frozen_value(name: str) -> None:
    for field, value in ORACLE_LITERALS[name].items():
        instance = _validate(name, SAMPLES[name])
        assert getattr(instance, field) == value
        replacement: object = (
            "1.1" if isinstance(value, str) else 4 if isinstance(value, int) else False
        )
        if field == "negation_cues":
            replacement = [["not"], ["no"], ["never"]]
        if field == "recommended_reviewer_attention":
            replacement = False
        with pytest.raises(ValidationError):
            _validate(name, _mutated(name, **{field: replacement}))


@pytest.mark.parametrize("name", sorted(ORACLE_FIELDS))
def test_models_are_strict_frozen_and_reject_arbitrary_maps(name: str) -> None:
    with pytest.raises(ValidationError):
        _validate(name, _mutated(name, metadata={"free": "form"}))
    instance = _validate(name, SAMPLES[name])
    first_field = next(iter(ORACLE_FIELDS[name]))
    with pytest.raises(ValidationError):
        setattr(instance, first_field, getattr(instance, first_field))


@pytest.mark.parametrize("enum_name", sorted(ORACLE_ENUMS))
def test_closed_vocabularies_match_the_oracle_exactly(enum_name: str) -> None:
    if enum_name in ENUM_TYPES:
        assert [member.value for member in ENUM_TYPES[enum_name]] == ORACLE_ENUMS[enum_name]
        with pytest.raises(ValueError):
            ENUM_TYPES[enum_name]("NOT_A_TOKEN")
        return
    if enum_name == "source_status":
        for value in ORACLE_ENUMS[enum_name]:
            _validate("P2T4SourceResultRefV1", {**_ASR_REF_OK, "status": value})
        with pytest.raises(ValidationError):
            _validate("P2T4SourceResultRefV1", {**_ASR_REF_OK, "status": "REJECTED"})
    if enum_name == "failed_policy_state":
        for value in ORACLE_ENUMS[enum_name]:
            _validate(
                "P2T4VisionFailureReferenceV1",
                _mutated(
                    "P2T4VisionFailureReferenceV1",
                    error_code="VISION_TIMEOUT",
                    error_detail="TIMEOUT_BUDGET_EXCEEDED",
                    policy_execution_state=value,
                ),
            )
        with pytest.raises(ValidationError):
            _validate(
                "P2T4VisionFailureReferenceV1",
                _mutated("P2T4VisionFailureReferenceV1", policy_execution_state="PASSED"),
            )


def test_rejection_precedence_and_phase_codes_follow_the_oracle() -> None:
    assert tuple(phase.value for phase in P2T4RejectionPhase) == ORACLE_REJECTION_PRECEDENCE
    for phase, codes in ORACLE_PHASE_CODES.items():
        for code in codes:
            payload = _mutated(
                "P2T4FusionInputRejectionV1",
                input_slot="ASR",
                phase=phase,
                code=code,
                expected_identity="P2.AsrResultV1@1.0",
                observed_identity="UNKNOWN",
                observed_status=None,
                field_code="NONE",
            )
            if phase == "ADMISSIBILITY":
                payload.update(
                    observed_identity="P2.AsrResultV1@1.0",
                    observed_status="SUCCEEDED",
                    field_code="DUPLICATE_SEGMENT_INDEX",
                )
            if phase == "CORRELATION":
                payload.update(
                    input_slot="BOTH", expected_identity="NONE", field_code="CORRELATION_ID"
                )
            _validate("P2T4FusionInputRejectionV1", payload)
        for code in ORACLE_ENUMS["rejection_code"]:
            if code in codes:
                continue
            with pytest.raises(ValidationError):
                _validate(
                    "P2T4FusionInputRejectionV1",
                    _mutated(
                        "P2T4FusionInputRejectionV1",
                        phase=phase,
                        code=code,
                        field_code="NONE",
                        observed_identity="UNKNOWN",
                    ),
                )


# --- cross-field invariants ---------------------------------------------------------------

INVARIANTS: list[tuple[str, str, Callable[[], dict[str, Any]]]] = [
    (
        "P2T4FusionInputRejectionV1",
        "BOTH requires CORRELATION/CORRELATION_MISMATCH/NONE/CORRELATION_ID",
        lambda: _mutated("P2T4FusionInputRejectionV1", input_slot="BOTH"),
    ),
    (
        "P2T4FusionInputRejectionV1",
        "correlation phase requires input_slot=BOTH",
        lambda: _mutated(
            "P2T4FusionInputRejectionV1",
            phase="CORRELATION",
            code="CORRELATION_MISMATCH",
            expected_identity="NONE",
            field_code="CORRELATION_ID",
        ),
    ),
    (
        "P2T4FusionInputRejectionV1",
        "expected identity must match the slot",
        lambda: _mutated(
            "P2T4FusionInputRejectionV1", expected_identity="P2.VisionUnderstandingResultV1@1.0"
        ),
    ),
    (
        "P2T4FusionInputRejectionV1",
        "DUPLICATE_SEGMENT_INDEX only in ADMISSIBILITY",
        lambda: _mutated("P2T4FusionInputRejectionV1", phase="STRICT_VALIDATION"),
    ),
    (
        "P2T4FusionInputRejectionV1",
        "ADMISSIBILITY requires the ASR slot",
        lambda: _mutated(
            "P2T4FusionInputRejectionV1",
            input_slot="VISION",
            expected_identity="P2.VisionUnderstandingResultV1@1.0",
            observed_identity="P2.VisionUnderstandingResultV1@1.0",
        ),
    ),
    (
        "P2T4NarrationClaimRefV1",
        "claim_end must exceed claim_start",
        lambda: {"segment_index": 0, "claim_start": 2, "claim_end": 2},
    ),
    (
        "P2T4NarrationClaimRefV1",
        "no negative coordinates",
        lambda: {"segment_index": -1, "claim_start": 0, "claim_end": 1},
    ),
    (
        "P2T4FusionPolicyConfigV1",
        "confidence floor bounded to [0, 1]",
        lambda: _mutated("P2T4FusionPolicyConfigV1", confidence_floor=1.5),
    ),
    (
        "P2T4FusionPolicyConfigV1",
        "config_version non-empty",
        lambda: _mutated("P2T4FusionPolicyConfigV1", config_version=""),
    ),
    (
        "P2T4SourceResultRefV1",
        "digest must be lowercase 64-hex",
        lambda: {**_ASR_REF_OK, "result_sha256": "A" * 64},
    ),
    (
        "P2T4AsrFailureReferenceV1",
        "ASR failure ref requires a FAILED ASR source ref",
        lambda: _mutated("P2T4AsrFailureReferenceV1", source_asr_result_ref=_ASR_REF_OK),
    ),
    (
        "P2T4AsrFailureReferenceV1",
        "attempt_number bounded to 0..2",
        lambda: _mutated("P2T4AsrFailureReferenceV1", attempt_number=3),
    ),
    (
        "P2T4VisionFailureReferenceV1",
        "Vision failure ref requires a FAILED Vision source ref",
        lambda: _mutated("P2T4VisionFailureReferenceV1", source_vision_result_ref=_ASR_REF_FAILED),
    ),
    (
        "P2T4UpstreamFailureRefV1",
        "ASR modality forbids a Vision failure ref",
        lambda: _mutated("P2T4UpstreamFailureRefV1", vision_failure_ref=SAMPLE_VISION_FAILURE),
    ),
    (
        "P2T4UpstreamFailureRefV1",
        "BOTH modality requires both refs",
        lambda: _mutated("P2T4UpstreamFailureRefV1", failed_modality="BOTH"),
    ),
    (
        "P2T4FusedEntityV1",
        "fused id equals source ref",
        lambda: _mutated("P2T4FusedEntityV1", source_observation_ref="e-9"),
    ),
    (
        "P2T4FusedEntityV1",
        "support flag iff support ref",
        lambda: _mutated("P2T4FusedEntityV1", narration_support_applied=False),
    ),
    (
        "P2T4FusedEntityV1",
        "observation IDs are lowercase [a-z0-9-]+",
        lambda: _mutated(
            "P2T4FusedEntityV1", fused_observation_id="E_1", source_observation_ref="E_1"
        ),
    ),
    (
        "P2T4FusedRelationV1",
        "relation subject differs from object",
        lambda: _mutated("P2T4FusedRelationV1", object_ref="e-1"),
    ),
    (
        "P2T4FusedThemeV1",
        "theme evidence non-empty",
        lambda: _mutated("P2T4FusedThemeV1", evidence_refs=[]),
    ),
    (
        "P2T4ConflictV1",
        "conflict_id must equal the canonical algorithm",
        lambda: _mutated("P2T4ConflictV1", conflict_id="P2T4-CONFLICT-" + "0" * 64),
    ),
    (
        "P2T4ConflictV1",
        "contradiction requires a refuting reference",
        lambda: _mutated("P2T4ConflictV1", narration_claim_ref=None),
    ),
    (
        "P2T4ObservationUncertaintyV1",
        "MEASURED requires a certainty value",
        lambda: _mutated("P2T4ObservationUncertaintyV1", certainty=None),
    ),
    (
        "P2T4ObservationUncertaintyV1",
        "certainty bounded to [0, 1]",
        lambda: _mutated("P2T4ObservationUncertaintyV1", certainty=1.2),
    ),
    (
        "P2T4UncertaintySummaryV1",
        "rows sorted by (kind rank, id)",
        lambda: {
            "formula_id": "AGREEMENT_WEIGHTED_V1",
            "per_observation": [
                _row("a-1", "ACTION", "MEASURED", 0.5),
                _row("e-1", "ENTITY", "MEASURED", 0.5),
            ],
        },
    ),
    (
        "P2T4UncertaintySummaryV1",
        "rows unique per observation",
        lambda: {
            "formula_id": "AGREEMENT_WEIGHTED_V1",
            "per_observation": [
                _row("e-1", "ENTITY", "MEASURED", 0.5),
                _row("e-1", "ENTITY", "MEASURED", 0.5),
            ],
        },
    ),
    (
        "P2T4FusedResultV1",
        "FUSED requires upstream_failure=null",
        lambda: _mutated(
            "P2T4FusedResultV1", upstream_failure=SAMPLE_UPSTREAM_FAILURE_RESULT["upstream_failure"]
        ),
    ),
    (
        "P2T4FusedResultV1",
        "FUSED requires both SUCCEEDED source refs",
        lambda: _mutated("P2T4FusedResultV1", source_asr_result_ref=_ASR_REF_FAILED),
    ),
    (
        "P2T4FusedResultV1",
        "UPSTREAM_FAILURE requires a failure ref",
        lambda: {**SAMPLE_UPSTREAM_FAILURE_RESULT, "upstream_failure": None},
    ),
    (
        "P2T4FusedResultV1",
        "UPSTREAM_FAILURE requires empty collections",
        lambda: {**SAMPLE_UPSTREAM_FAILURE_RESULT, "themes": SAMPLE_FUSED_RESULT["themes"]},
    ),
    (
        "P2T4FusedResultV1",
        "failed_modality must match failed source statuses",
        lambda: {
            **SAMPLE_UPSTREAM_FAILURE_RESULT,
            "source_vision_result_ref": _VISION_REF_FAILED,
        },
    ),
    (
        "P2T4FusedResultV1",
        "source slots carry their own identities",
        lambda: _mutated("P2T4FusedResultV1", source_asr_result_ref=_VISION_REF_OK),
    ),
    (
        "P2T4FusedResultV1",
        "naive executed_at rejected",
        lambda: _mutated("P2T4FusedResultV1", executed_at=datetime(2026, 9, 15, 12, 0)),
    ),
    (
        "P2T4FusedResultV1",
        "action actor must resolve to a fused entity",
        lambda: _mutated(
            "P2T4FusedResultV1",
            actions=[{**SAMPLE_FUSED_RESULT["actions"][0], "actor_ref": "r-1"}],
        ),
    ),
    (
        "P2T4FusedResultV1",
        "theme evidence must resolve to entity/action/relation",
        lambda: _mutated(
            "P2T4FusedResultV1",
            themes=[{**SAMPLE_FUSED_RESULT["themes"][0], "evidence_refs": ["t-1"]}],
        ),
    ),
    (
        "P2T4FusedResultV1",
        "fused IDs unique across collections",
        lambda: _mutated(
            "P2T4FusedResultV1",
            themes=[
                {
                    **SAMPLE_FUSED_RESULT["themes"][0],
                    "fused_observation_id": "e-1",
                    "source_observation_ref": "e-1",
                }
            ],
        ),
    ),
    (
        "P2T4FusedResultV1",
        "one uncertainty row per entity/action/relation and none for themes",
        lambda: _mutated(
            "P2T4FusedResultV1",
            uncertainty={
                "formula_id": "AGREEMENT_WEIGHTED_V1",
                "per_observation": SAMPLE_FUSED_RESULT["uncertainty"]["per_observation"][:-1],
            },
        ),
    ),
    (
        "P2T4FusedResultV1",
        "uncertainty candidate_kind matches the observation",
        lambda: _mutated(
            "P2T4FusedResultV1",
            uncertainty={
                "formula_id": "AGREEMENT_WEIGHTED_V1",
                "per_observation": [
                    _row("a-1", "ENTITY", "NOT_MEASURED", None),
                    _row("e-1", "ENTITY", "MEASURED", 0.9),
                    _row("e-2", "ENTITY", "NOT_APPLICABLE_CONFLICTING", None),
                    _row("r-1", "RELATION", "MEASURED", 0.4),
                ],
            },
        ),
    ),
    (
        "P2T4FusedResultV1",
        "conflict claim ref must resolve",
        lambda: _mutated(
            "P2T4FusedResultV1",
            conflicts=[
                {
                    **SAMPLE_CONFLICT,
                    "vision_claim_ref": "e-9",
                    "conflict_id": _conflict_id("ENTITY_ATTRIBUTE_CONTRADICTION", "e-9"),
                }
            ],
        ),
    ),
    (
        "P2T4FusedResultV1",
        "contradiction reason must match candidate kind",
        lambda: _mutated(
            "P2T4FusedResultV1",
            conflicts=[
                {
                    **SAMPLE_CONFLICT,
                    "reason_code": "ACTION_CONTRADICTION",
                    "conflict_id": _conflict_id("ACTION_CONTRADICTION", "e-2"),
                }
            ],
        ),
    ),
    (
        "P2T4FusedResultV1",
        "a conflicting candidate cannot be primary",
        lambda: _mutated(
            "P2T4FusedResultV1", entities=[_entity("e-1", _REF, True), _entity("e-2", None, True)]
        ),
    ),
    (
        "P2T4FusedResultV1",
        "NOT_APPLICABLE_CONFLICTING exactly for conflicting candidates",
        lambda: _mutated(
            "P2T4FusedResultV1",
            uncertainty={
                "formula_id": "AGREEMENT_WEIGHTED_V1",
                "per_observation": [
                    _row("e-1", "ENTITY", "MEASURED", 0.9),
                    _row("e-2", "ENTITY", "NOT_MEASURED", None),
                    _row("a-1", "ACTION", "NOT_MEASURED", None),
                    _row("r-1", "RELATION", "MEASURED", 0.4),
                ],
            },
        ),
    ),
    (
        "P2T4FusedResultV1",
        "conflicts in canonical (reason rank, claim ref, narration ref, id) order",
        lambda: _mutated(
            "P2T4FusedResultV1",
            conflicts=[
                {
                    "conflict_id": _conflict_id("LOW_CONFIDENCE_EVIDENCE", "e-2"),
                    "reason_code": "LOW_CONFIDENCE_EVIDENCE",
                    "vision_claim_ref": "e-2",
                    "narration_claim_ref": None,
                    "recommended_reviewer_attention": True,
                },
                SAMPLE_CONFLICT,
            ],
        ),
    ),
]


@pytest.mark.parametrize("name,description,build", INVARIANTS, ids=[i[1] for i in INVARIANTS])
def test_cross_field_invariants_reject(
    name: str, description: str, build: Callable[[], dict[str, Any]]
) -> None:
    with pytest.raises(ValidationError):
        _validate(name, build())


def test_valid_upstream_failure_and_low_confidence_shapes_are_accepted() -> None:
    _validate("P2T4FusedResultV1", SAMPLE_UPSTREAM_FAILURE_RESULT)
    accepted = _mutated(
        "P2T4FusedResultV1",
        conflicts=[
            SAMPLE_CONFLICT,
            {
                "conflict_id": _conflict_id("LOW_CONFIDENCE_EVIDENCE", "e-2"),
                "reason_code": "LOW_CONFIDENCE_EVIDENCE",
                "vision_claim_ref": "e-2",
                "narration_claim_ref": None,
                "recommended_reviewer_attention": True,
            },
            {
                "conflict_id": _conflict_id("LOW_CONFIDENCE_EVIDENCE", "t-1"),
                "reason_code": "LOW_CONFIDENCE_EVIDENCE",
                "vision_claim_ref": "t-1",
                "narration_claim_ref": None,
                "recommended_reviewer_attention": True,
            },
        ],
    )
    _validate("P2T4FusedResultV1", accepted)


# --- canonical sort keys and privacy rules -------------------------------------------------


def test_canonical_sort_keys_follow_the_oracle_ranks() -> None:
    assert {kind.value: rank for kind, rank in zip(P2T4CandidateKind, range(3), strict=True)} == (
        ORACLE_CANDIDATE_KIND_RANK
    )
    assert {
        reason.value: rank for reason, rank in zip(P2T4ConflictReasonCode, range(4), strict=True)
    } == (ORACLE_CONFLICT_REASON_RANK)
    rows = [
        P2T4ObservationUncertaintyV1.model_validate(_row("r-1", "RELATION", "MEASURED", 0.4)),
        P2T4ObservationUncertaintyV1.model_validate(_row("e-2", "ENTITY", "NOT_MEASURED", None)),
        P2T4ObservationUncertaintyV1.model_validate(_row("e-1", "ENTITY", "MEASURED", 0.9)),
    ]
    ordered = sorted(
        rows,
        key=lambda row: (ORACLE_CANDIDATE_KIND_RANK[row.candidate_kind.value], row.observation_id),
    )
    assert [row.observation_id for row in ordered] == ["e-1", "e-2", "r-1"]
    P2T4UncertaintySummaryV1(per_observation=tuple(ordered))
    with pytest.raises(ValidationError):
        P2T4UncertaintySummaryV1(per_observation=tuple(rows))


def test_rejection_carries_only_closed_tokens_and_no_free_text() -> None:
    instance = _validate("P2T4FusionInputRejectionV1", SAMPLES["P2T4FusionInputRejectionV1"])
    allowed = {token for values in ORACLE_ENUMS.values() for token in values} | {
        "P2T4FusionInputRejectionV1",
        "1.0",
        "REJECTED",
    }
    for value in instance.model_dump().values():
        assert value is None or str(value) in allowed


def test_canonical_json_is_compact_sorted_and_utc() -> None:
    text = canonical_json(_validate("P2T4FusedResultV1", SAMPLE_FUSED_RESULT))
    assert text.startswith('{"actions":[{"actor_ref":"e-1"')
    assert '"executed_at":"2026-09-15T12:00:00.000000Z"' in text
    assert ": " not in text and ", " not in text
    assert "\\u" not in text
