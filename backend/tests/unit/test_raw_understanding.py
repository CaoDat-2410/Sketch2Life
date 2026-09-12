from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.services.raw_understanding_mapper import (
    RawUnderstandingMappingError,
    map_vision_result_to_raw,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrProfileId,
)
from sketch2life.contracts.schemas.raw_understanding import (
    RawFailureCode,
    RawNarrationStatus,
    RawRelationObservationV1,
    RawUncertaintyStatus,
    RawUnderstandingFailureV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    EntityCandidateV1,
    ObservedTextV1,
    TextLanguageDeclarationV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionNonPolicyErrorDetail,
    VisionProhibitedClaimCategory,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingFailureV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)

_SOURCE_HASH = "a" * 64
_EXECUTED_AT = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
_SOURCE = VisionImageReferenceV1(artifact_ref="fixture:raw:one.png", sha256=_SOURCE_HASH)
_PROFILE = vision_profile_catalog_v2().profiles[0]
_CATALOG_HASH = vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
_LANGUAGE = TextLanguageDeclarationV1(status="NOT_DETERMINED")


def _text(value: str) -> ObservedTextV1:
    return ObservedTextV1(value=value, language=_LANGUAGE)


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    values: dict[str, Any] = {
        "correlation_id": "raw-map-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE,
        "profile_id": _PROFILE.profile_id,
        "profile_catalog_hash": _CATALOG_HASH,
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "policy-test-v1",
        "policy_match_view_version": "policy-view-v1",
        "policy_execution_state": "PASSED",
        "adapter_version": _PROFILE.adapter_version,
        "config_hash": vision_profile_config_hash_v2(_PROFILE),
        "model_provenance": _PROFILE.model_provenance,
        "entities": (
            EntityCandidateV1(
                observation_id="entity-ball", label=_text("ball"), confidence=0.9
            ),
        ),
        "actions": (
            ActionCandidateV1(
                observation_id="action-roll",
                label=_text("roll"),
                actor_ref="entity-ball",
                confidence=0.8,
            ),
        ),
        "relations": (),
        "themes": (),
        "ambiguous_regions": (),
    }
    values.update(overrides)
    return VisionUnderstandingSuccessV2(**values)


def _failure(**overrides: Any) -> VisionUnderstandingFailureV2:
    values: dict[str, Any] = {
        "correlation_id": "raw-map-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE,
        "profile_id": _PROFILE.profile_id,
        "profile_catalog_hash": _CATALOG_HASH,
        "attempt_number": 0,
        "repair_attempted": False,
        "content_policy_version": "policy-test-v1",
        "policy_match_view_version": "policy-view-v1",
        "policy_execution_state": "NOT_EXECUTED",
        "error_code": VisionErrorCode.INPUT_NOT_VALIDATED,
        "error_detail": VisionNonPolicyErrorDetail.MEDIA_VALIDATION_NOT_PASSED,
        "retryable": False,
    }
    values.update(overrides)
    return VisionUnderstandingFailureV2(**values)


def test_maps_typed_v2_groups_and_gate_a_boundary() -> None:
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )

    assert isinstance(mapped, RawUnderstandingSuccessV1)
    assert mapped.gate_a_required is True
    assert mapped.source_image_ref.sha256 == _SOURCE_HASH
    assert mapped.entities[0].label.value == "ball"
    assert mapped.actions[0].actor_ref == "entity-ball"
    assert mapped.uncertainty is None
    assert mapped.uncertainty_status is RawUncertaintyStatus.NOT_PROVIDED
    assert mapped.narration_status is RawNarrationStatus.NOT_SUPPLIED
    assert mapped.provenance.upstream_contract == "VisionUnderstandingResultV2"


def test_maps_typed_v2_failure_without_inventing_provenance() -> None:
    mapped = map_vision_result_to_raw(
        _failure(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )

    assert isinstance(mapped, RawUnderstandingFailureV1)
    assert mapped.gate_a_required is True
    assert mapped.failure.code is RawFailureCode.VALIDATION_REJECTED
    assert mapped.provenance is None


def test_rejects_source_hash_mismatch_before_mapping() -> None:
    with pytest.raises(RawUnderstandingMappingError, match="source image hash mismatch"):
        map_vision_result_to_raw(
            _success(),
            session_id="session-1",
            expected_source_sha256="b" * 64,
            expected_correlation_id="raw-map-test",
        )


def test_rejects_stale_correlation_before_mapping() -> None:
    with pytest.raises(RawUnderstandingMappingError, match="stale correlation id"):
        map_vision_result_to_raw(
            _success(),
            session_id="session-1",
            expected_source_sha256=_SOURCE_HASH,
            expected_correlation_id="current-request",
        )


def test_rejects_missing_v2_confidence_without_defaulting() -> None:
    result = _success(
        entities=(
            EntityCandidateV1(
                observation_id="entity-ball", label=_text("ball"), confidence=None
            ),
        )
    )
    with pytest.raises(RawUnderstandingMappingError, match="missing confidence"):
        map_vision_result_to_raw(
            result,
            session_id="session-1",
            expected_source_sha256=_SOURCE_HASH,
            expected_correlation_id="raw-map-test",
        )


def test_raw_schema_rejects_extra_fields_and_invalid_confidence() -> None:
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )
    payload = mapped.model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        RawUnderstandingSuccessV1.model_validate(payload)

    payload = mapped.model_dump(mode="json")
    payload["entities"][0]["confidence"] = 1.1
    with pytest.raises(ValidationError):
        RawUnderstandingSuccessV1.model_validate(payload)


def test_raw_success_rejects_incomplete_provenance() -> None:
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )
    payload = mapped.model_dump(mode="json")
    payload["provenance"]["config_hash"] = None
    with pytest.raises(ValidationError, match="complete model provenance"):
        RawUnderstandingSuccessV1.model_validate(payload)


def test_raw_schema_rejects_broken_references_and_forbids_gate_b_decisions() -> None:
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )
    payload = mapped.model_dump(mode="json")
    payload["actions"][0]["actor_ref"] = "missing-entity"
    with pytest.raises(ValidationError, match="reference integrity"):
        RawUnderstandingSuccessV1.model_validate(payload)

    payload = mapped.model_dump(mode="json")
    payload["eligibility"] = "ELIGIBLE"
    with pytest.raises(ValidationError):
        RawUnderstandingSuccessV1.model_validate(payload)


def test_raw_schema_rejects_false_gate_a_and_self_relation() -> None:
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )
    payload = mapped.model_dump(mode="json")
    payload["gate_a_required"] = False
    with pytest.raises(ValidationError):
        RawUnderstandingSuccessV1.model_validate(payload)

    with pytest.raises(ValidationError, match="self-reference"):
        RawRelationObservationV1(
            observation_id="relation-self",
            predicate=_text("near"),
            subject_ref="entity-ball",
            object_ref="entity-ball",
            confidence=0.5,
        )


def test_raw_schema_rejects_oversized_observation_collection() -> None:
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )
    payload = mapped.model_dump(mode="json")
    payload["actions"] = []
    payload["entities"] = [
        {
            "observation_id": f"entity-{index}",
            "label": _text(f"object {index}").model_dump(mode="json"),
            "confidence": 0.5,
            "source": "VISION",
        }
        for index in range(129)
    ]
    with pytest.raises(ValidationError):
        RawUnderstandingSuccessV1.model_validate(payload)


def test_asr_failure_is_not_collapsed_into_missing_narration() -> None:
    asr_failure = AsrFailureV1(
        correlation_id="raw-map-test",
        executed_at=_EXECUTED_AT,
        source_audio_ref=AsrAudioReferenceV1(
            artifact_ref="fixture:raw:one.wav", sha256="b" * 64
        ),
        profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1,
        attempt_number=1,
        repair_attempted=False,
        error_code=AsrErrorCode.ASR_TIMEOUT,
        retryable=False,
        error_detail=AsrErrorDetail.TIMEOUT_BUDGET_EXCEEDED,
    )
    mapped = map_vision_result_to_raw(
        _success(),
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
        asr_result=asr_failure,
    )
    assert isinstance(mapped, RawUnderstandingSuccessV1)
    assert mapped.narration_status is RawNarrationStatus.ASR_FAILED
    assert mapped.asr_failure is not None
    assert mapped.asr_failure.detail == "TIMEOUT_BUDGET_EXCEEDED"


def test_prohibited_v2_failure_maps_to_typed_prohibited_field() -> None:
    result = _failure(
        attempt_number=1,
        error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
        error_detail=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
        policy_execution_state="BLOCKED",
        model_provenance=_PROFILE.model_provenance,
    )
    mapped = map_vision_result_to_raw(
        result,
        session_id="session-1",
        expected_source_sha256=_SOURCE_HASH,
        expected_correlation_id="raw-map-test",
    )
    assert isinstance(mapped, RawUnderstandingFailureV1)
    assert mapped.failure.code is RawFailureCode.PROHIBITED_FIELD
