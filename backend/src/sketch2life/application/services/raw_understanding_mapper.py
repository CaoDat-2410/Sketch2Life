"""Map the FEAT-003 V2 vision union into FEAT-018's Gate A proposal contract."""

from __future__ import annotations

from typing import Final

from sketch2life.contracts.schemas.asr import (
    AsrErrorCode,
    AsrFailureV1,
    AsrResultV1,
    AsrSuccessV1,
)
from sketch2life.contracts.schemas.raw_understanding import (
    RawActionObservationV1,
    RawAmbiguousObservationV1,
    RawAsrClaimV1,
    RawAsrFailureCode,
    RawAsrFailureV1,
    RawEntityObservationV1,
    RawFailureCode,
    RawFailureV1,
    RawNarrationStatus,
    RawProvenanceV1,
    RawRelationObservationV1,
    RawThemeObservationV1,
    RawUncertaintyStatus,
    RawUnderstandingFailureV1,
    RawUnderstandingResultV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
)


class RawUnderstandingMappingError(ValueError):
    """A deterministic boundary rejection with no raw provider payload."""


_ERROR_CODE_MAP: Final[dict[VisionErrorCode, RawFailureCode]] = {
    VisionErrorCode.INPUT_NOT_VALIDATED: RawFailureCode.VALIDATION_REJECTED,
    VisionErrorCode.VISION_MODEL_UNAVAILABLE: RawFailureCode.MODEL_UNAVAILABLE,
    VisionErrorCode.VISION_TIMEOUT: RawFailureCode.TIMEOUT,
    VisionErrorCode.VISION_PROVIDER_FAILURE: RawFailureCode.PROVIDER_ERROR,
    VisionErrorCode.VISION_SCHEMA_INVALID: RawFailureCode.SCHEMA_INVALID,
    VisionErrorCode.PROHIBITED_CLAIM_DETECTED: RawFailureCode.PROHIBITED_FIELD,
}

_ASR_ERROR_CODE_MAP: Final[dict[AsrErrorCode, RawAsrFailureCode]] = {
    AsrErrorCode.INPUT_NOT_VALIDATED: RawAsrFailureCode.VALIDATION_REJECTED,
    AsrErrorCode.ASR_TIMEOUT: RawAsrFailureCode.TIMEOUT,
    AsrErrorCode.ASR_MODEL_UNAVAILABLE: RawAsrFailureCode.MODEL_UNAVAILABLE,
    AsrErrorCode.ASR_PROVIDER_FAILURE: RawAsrFailureCode.PROVIDER_ERROR,
    AsrErrorCode.ASR_SCHEMA_INVALID: RawAsrFailureCode.SCHEMA_INVALID,
}


def map_vision_result_to_raw(
    result: VisionUnderstandingResultV2,
    *,
    session_id: str,
    expected_source_sha256: str,
    expected_correlation_id: str,
    asr_result: AsrResultV1 | None = None,
) -> RawUnderstandingResultV1:
    """Map one already-validated V2 result without executing a model or provider."""

    if not session_id:
        raise RawUnderstandingMappingError("session_id is required")
    if result.source_image_ref.sha256 != expected_source_sha256:
        raise RawUnderstandingMappingError("source image hash mismatch")
    if result.correlation_id != expected_correlation_id:
        raise RawUnderstandingMappingError("stale correlation id")
    if isinstance(result, VisionUnderstandingSuccessV2):
        return _map_success(result, session_id=session_id, asr_result=asr_result)
    if isinstance(result, VisionUnderstandingFailureV2):
        return _map_failure(result, session_id=session_id)
    raise RawUnderstandingMappingError("unsupported V2 result variant")


def _map_success(
    result: VisionUnderstandingSuccessV2,
    *,
    session_id: str,
    asr_result: AsrResultV1 | None,
) -> RawUnderstandingSuccessV1:
    asr_claims, narration_status, asr_failure = _map_asr(asr_result)
    return RawUnderstandingSuccessV1(
        correlation_id=result.correlation_id,
        session_id=session_id,
        source_image_ref=result.source_image_ref,
        entities=tuple(
            RawEntityObservationV1(
                observation_id=item.observation_id,
                label=item.label,
                confidence=_required_confidence(item.confidence, item.observation_id),
            )
            for item in result.entities
        ),
        actions=tuple(
            RawActionObservationV1(
                observation_id=item.observation_id,
                label=item.label,
                actor_ref=item.actor_ref,
                object_ref=item.object_ref,
                confidence=_required_confidence(item.confidence, item.observation_id),
            )
            for item in result.actions
        ),
        relations=tuple(
            RawRelationObservationV1(
                observation_id=item.observation_id,
                predicate=item.predicate,
                subject_ref=item.subject_ref,
                object_ref=item.object_ref,
                confidence=_required_confidence(item.confidence, item.observation_id),
            )
            for item in result.relations
        ),
        themes=tuple(
            RawThemeObservationV1(
                observation_id=item.observation_id,
                label=item.label,
                evidence_refs=item.evidence_refs,
                confidence=_required_confidence(item.confidence, item.observation_id),
            )
            for item in result.themes
        ),
        ambiguous_regions=tuple(
            RawAmbiguousObservationV1(observation_id=item.observation_id, note=item.note)
            for item in result.ambiguous_regions
        ),
        asr_claims=asr_claims,
        narration_status=narration_status,
        asr_failure=asr_failure,
        fused_claims=tuple(),
        conflicts=tuple(),
        uncertainty=None,
        uncertainty_status=RawUncertaintyStatus.NOT_PROVIDED,
        provenance=RawProvenanceV1(
            upstream_contract=result.contract_name,
            upstream_contract_version=result.contract_version,
            profile_id=result.profile_id,
            profile_catalog_hash=result.profile_catalog_hash,
            adapter_version=result.adapter_version,
            config_hash=result.config_hash,
            model_provenance=result.model_provenance,
        ),
    )


def _map_failure(
    result: VisionUnderstandingFailureV2, *, session_id: str
) -> RawUnderstandingFailureV1:
    raw_code = _ERROR_CODE_MAP[result.error_code]
    upstream_detail = _safe_detail(result)
    provenance = None
    if result.model_provenance is not None:
        provenance = RawProvenanceV1(
            upstream_contract=result.contract_name,
            upstream_contract_version=result.contract_version,
            profile_id=result.profile_id,
            profile_catalog_hash=result.profile_catalog_hash,
            model_provenance=result.model_provenance,
        )
    return RawUnderstandingFailureV1(
        correlation_id=result.correlation_id,
        session_id=session_id,
        source_image_ref=result.source_image_ref,
        provenance=provenance,
        failure=RawFailureV1(
            code=raw_code,
            retryable=result.retryable,
            upstream_detail=upstream_detail,
        ),
    )


def _map_asr(
    asr_result: AsrResultV1 | None,
) -> tuple[tuple[RawAsrClaimV1, ...], RawNarrationStatus, RawAsrFailureV1 | None]:
    if asr_result is None:
        return tuple(), RawNarrationStatus.NOT_SUPPLIED, None
    if isinstance(asr_result, AsrSuccessV1):
        claims = tuple(
            RawAsrClaimV1(claim_id=f"asr-{segment.index}", text=segment.text)
            for segment in asr_result.segments
        )
        return claims, RawNarrationStatus.ASR_SUCCEEDED, None
    if isinstance(asr_result, AsrFailureV1):
        return (
            tuple(),
            RawNarrationStatus.ASR_FAILED,
            RawAsrFailureV1(
                code=_ASR_ERROR_CODE_MAP[asr_result.error_code],
                retryable=asr_result.retryable,
                detail=asr_result.error_detail.value,
            ),
        )
    raise RawUnderstandingMappingError("unsupported ASR result variant")


def _required_confidence(value: float | None, observation_id: str) -> float:
    if value is None:
        raise RawUnderstandingMappingError(
            f"missing confidence for observation {observation_id}"
        )
    return value


def _safe_detail(result: VisionUnderstandingFailureV2) -> str:
    detail = result.error_detail
    if isinstance(detail, VisionNonPolicyErrorDetailV2):
        return detail.value
    return "PROHIBITED_CLAIM"


__all__ = ["RawUnderstandingMappingError", "map_vision_result_to_raw"]
