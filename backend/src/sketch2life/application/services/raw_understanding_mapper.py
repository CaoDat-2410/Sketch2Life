"""Map the FEAT-003 V2 vision union into FEAT-018's Gate A proposal contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
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
    RawConflictCode,
    RawConflictV1,
    RawEntityObservationV1,
    RawFailureCode,
    RawFailureV1,
    RawFusedClaimV1,
    RawNarrationStatus,
    RawProvenanceV1,
    RawRelationObservationV1,
    RawThemeObservationV1,
    RawUncertaintyStatus,
    RawUnderstandingFailureV1,
    RawUnderstandingResultV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision import VisionErrorCode, vision_label_normalize
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
    typed_narration: str | None = None,
) -> RawUnderstandingResultV1:
    """Map one already-validated V2 result without executing a model or provider."""

    if not session_id:
        raise RawUnderstandingMappingError("session_id is required")
    if result.source_image_ref.sha256 != expected_source_sha256:
        raise RawUnderstandingMappingError("source image hash mismatch")
    if result.correlation_id != expected_correlation_id:
        raise RawUnderstandingMappingError("stale correlation id")
    if asr_result is not None and asr_result.correlation_id != result.correlation_id:
        raise RawUnderstandingMappingError("stale correlation id")
    if typed_narration is not None and not typed_narration.strip():
        raise RawUnderstandingMappingError("typed narration must not be empty")
    if typed_narration is not None and asr_result is not None:
        raise RawUnderstandingMappingError("typed narration and ASR cannot both be supplied")
    if isinstance(result, VisionUnderstandingSuccessV2):
        return _map_success(
            result,
            session_id=session_id,
            asr_result=asr_result,
            typed_narration=typed_narration,
        )
    if isinstance(result, VisionUnderstandingFailureV2):
        return _map_failure(result, session_id=session_id)
    raise RawUnderstandingMappingError("unsupported V2 result variant")


def _map_success(
    result: VisionUnderstandingSuccessV2,
    *,
    session_id: str,
    asr_result: AsrResultV1 | None,
    typed_narration: str | None,
) -> RawUnderstandingSuccessV1:
    asr_claims, narration_status, asr_failure = _map_narration(asr_result, typed_narration)
    entities = tuple(
        RawEntityObservationV1(
            observation_id=item.observation_id,
            label=item.label,
            confidence=_required_confidence(item.confidence, item.observation_id),
        )
        for item in result.entities
    )
    actions = tuple(
        RawActionObservationV1(
            observation_id=item.observation_id,
            label=item.label,
            actor_ref=item.actor_ref,
            object_ref=item.object_ref,
            confidence=_required_confidence(item.confidence, item.observation_id),
        )
        for item in result.actions
    )
    relations = tuple(
        RawRelationObservationV1(
            observation_id=item.observation_id,
            predicate=item.predicate,
            subject_ref=item.subject_ref,
            object_ref=item.object_ref,
            confidence=_required_confidence(item.confidence, item.observation_id),
        )
        for item in result.relations
    )
    themes = tuple(
        RawThemeObservationV1(
            observation_id=item.observation_id,
            label=item.label,
            evidence_refs=item.evidence_refs,
            confidence=_required_confidence(item.confidence, item.observation_id),
        )
        for item in result.themes
    )
    fused_claims, conflicts = _build_fusion(
        entities=entities,
        actions=actions,
        relations=relations,
        themes=themes,
        asr_claims=asr_claims,
    )
    return RawUnderstandingSuccessV1(
        correlation_id=result.correlation_id,
        session_id=session_id,
        source_image_ref=result.source_image_ref,
        entities=entities,
        actions=actions,
        relations=relations,
        themes=themes,
        ambiguous_regions=tuple(
            RawAmbiguousObservationV1(observation_id=item.observation_id, note=item.note)
            for item in result.ambiguous_regions
        ),
        asr_claims=asr_claims,
        narration_status=narration_status,
        asr_failure=asr_failure,
        fused_claims=fused_claims,
        conflicts=conflicts,
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


def _map_narration(
    asr_result: AsrResultV1 | None,
    typed_narration: str | None,
) -> tuple[tuple[RawAsrClaimV1, ...], RawNarrationStatus, RawAsrFailureV1 | None]:
    if typed_narration is not None:
        return (
            (RawAsrClaimV1(claim_id="text-typed-0", text=typed_narration, source="TEXT_TYPED"),),
            RawNarrationStatus.TEXT_SUPPLIED,
            None,
        )
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


_FUSION_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "butterfly": ("butterfly", "con bướm", "bướm"),
    "flower": ("flower", "flowers", "bông hoa", "hoa"),
    "cat": ("cat", "con mèo", "mèo"),
    "dog": ("dog", "con chó", "chó"),
    "bird": ("bird", "con chim", "chim"),
    "tree": ("tree", "cây", "cây xanh"),
    "grass": ("grass", "cỏ", "bãi cỏ"),
    "sun": ("sun", "mặt trời"),
    "flying": ("flying", "fly", "bay", "đang bay"),
    "running": ("running", "run", "chạy", "đang chạy"),
    "moving": ("moving", "move", "chuyển động", "đang di chuyển"),
}


@dataclass(frozen=True, slots=True)
class _FusionVisualClaim:
    observation_id: str
    text: str
    confidence: float


def _build_fusion(
    *,
    entities: tuple[RawEntityObservationV1, ...],
    actions: tuple[RawActionObservationV1, ...],
    relations: tuple[RawRelationObservationV1, ...],
    themes: tuple[RawThemeObservationV1, ...],
    asr_claims: tuple[RawAsrClaimV1, ...],
) -> tuple[tuple[RawFusedClaimV1, ...], tuple[RawConflictV1, ...]]:
    """Create only deterministic, provenance-preserving multimodal links.

    Text/ASR is never allowed to overwrite a visual claim. A link is emitted only when a reviewed
    alias is present in both sources; otherwise a closed disagreement is preserved for Gate A.
    """

    visual_claims = tuple(
        _FusionVisualClaim(item.observation_id, item.label.value, item.confidence)
        for item in entities
    )
    visual_claims += tuple(
        _FusionVisualClaim(item.observation_id, item.label.value, item.confidence)
        for item in actions
    )
    visual_claims += tuple(
        _FusionVisualClaim(item.observation_id, item.label.value, item.confidence)
        for item in themes
    )
    visual_claims += tuple(
        _FusionVisualClaim(item.observation_id, item.predicate.value, item.confidence)
        for item in relations
    )
    fused: list[RawFusedClaimV1] = []
    conflicts: list[RawConflictV1] = []
    for narration in asr_claims:
        narration_concepts = _concepts_in_text(narration.text)
        matching_visuals = tuple(
            visual
            for visual in visual_claims
            if _claim_matches_concepts(visual.text, narration_concepts)
        )
        for visual in matching_visuals[:4]:
            fused.append(
                RawFusedClaimV1(
                    claim_id=f"fused-{visual.observation_id}-{narration.claim_id}",
                    source_refs=(visual.observation_id, narration.claim_id),
                    # The only numeric source confidence is the validated vision confidence.
                    confidence=visual.confidence,
                )
            )
        if narration_concepts and visual_claims and not matching_visuals:
            conflicts.append(
                RawConflictV1(
                    conflict_id=f"conflict-{visual_claims[0].observation_id}-{narration.claim_id}",
                    claim_refs=(visual_claims[0].observation_id, narration.claim_id),
                    code=RawConflictCode.SOURCE_DISAGREEMENT,
                )
            )
    return tuple(fused), tuple(conflicts[:16])


def _concepts_in_text(value: str) -> frozenset[str]:
    normalized = _search_text(value)
    return frozenset(
        concept
        for concept, aliases in _FUSION_ALIASES.items()
        if any(_search_text(alias) in normalized for alias in aliases)
    )


def _claim_matches_concepts(value: str, concepts: frozenset[str]) -> bool:
    return bool(concepts.intersection(_concepts_in_text(value)))


def _search_text(value: str) -> str:
    return re.sub(r"\s+", " ", vision_label_normalize(value).casefold()).strip()


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
