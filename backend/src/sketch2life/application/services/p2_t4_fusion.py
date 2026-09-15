"""P2-T4 offline fusion core: deterministic, model-free, provider-free, network-free.

Two boundaries exist. `validate_and_fuse` accepts `object` values only to classify them into
the safe typed `P2T4FusionInputRejectionV1` or, once both slots are exact validated P2 V1
results, to call the pure typed `fuse` boundary. Terminal precedence is exactly
`identity/version -> strict upstream-contract validation -> P2-T4 admissibility ->
correlation equality -> typed upstream status -> fusion`; within each stage ASR is inspected
before Vision and the first rejection is terminal.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Final

from pydantic import TypeAdapter, ValidationError

from sketch2life.contracts.schemas import understanding as feat018_live
from sketch2life.contracts.schemas.asr import AsrFailureV1, AsrResultV1, AsrSuccessV1
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
    canonical_sha256,
    conflict_id_for,
    fusion_policy_config_hash,
)
from sketch2life.contracts.schemas.vision import (
    VisionUnderstandingFailureV1,
    VisionUnderstandingResultV1,
    VisionUnderstandingSuccessV1,
    vision_policy_match_view,
    vision_policy_match_view_tokens,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingFailureV2,
    VisionUnderstandingSuccessV2,
)

AsrInput = AsrSuccessV1 | AsrFailureV1
VisionInput = VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1
FusionOutcome = P2T4FusedResultV1 | P2T4FusionInputRejectionV1

_ASR_ADAPTER: Final = TypeAdapter[AsrInput](AsrResultV1)
_VISION_ADAPTER: Final = TypeAdapter[VisionInput](VisionUnderstandingResultV1)

_SERIALIZED_IDENTITIES: Final[dict[tuple[str, str], P2T4ObservedIdentity]] = {
    ("AsrResultV1", "1.0"): P2T4ObservedIdentity.P2_ASR_RESULT_V1,
    ("VisionUnderstandingResultV1", "1.0"): (
        P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V1
    ),
    ("VisionUnderstandingResultV2", "2.0"): (
        P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V2
    ),
}
_KNOWN_SERIALIZED_NAMES: Final = frozenset(name for name, _ in _SERIALIZED_IDENTITIES)

_TYPED_IDENTITIES: Final[tuple[tuple[type[object], P2T4ObservedIdentity], ...]] = (
    (AsrSuccessV1, P2T4ObservedIdentity.P2_ASR_RESULT_V1),
    (AsrFailureV1, P2T4ObservedIdentity.P2_ASR_RESULT_V1),
    (VisionUnderstandingSuccessV1, P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V1),
    (VisionUnderstandingFailureV1, P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V1),
    (VisionUnderstandingSuccessV2, P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V2),
    (VisionUnderstandingFailureV2, P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V2),
    (feat018_live.AsrResultV1, P2T4ObservedIdentity.FEAT018_LIVE_ASR_RESULT_V1),
    (
        feat018_live.VisionUnderstandingResultV1,
        P2T4ObservedIdentity.FEAT018_LIVE_VISION_UNDERSTANDING_RESULT_V1,
    ),
)

_TOP_LEVEL_FIELD_CODES: Final[dict[str, P2T4RejectionFieldCode]] = {
    "contract_name": P2T4RejectionFieldCode.CONTRACT_NAME,
    "contract_version": P2T4RejectionFieldCode.CONTRACT_VERSION,
    "status": P2T4RejectionFieldCode.STATUS,
    "correlation_id": P2T4RejectionFieldCode.CORRELATION_ID,
    "source_audio_ref": P2T4RejectionFieldCode.SOURCE_REFERENCE,
    "source_image_ref": P2T4RejectionFieldCode.SOURCE_REFERENCE,
    "error_code": P2T4RejectionFieldCode.FAILURE_BRANCH,
    "error_detail": P2T4RejectionFieldCode.FAILURE_BRANCH,
    "retryable": P2T4RejectionFieldCode.FAILURE_BRANCH,
}

_CONTRADICTION_REASON: Final[dict[P2T4CandidateKind, P2T4ConflictReasonCode]] = {
    P2T4CandidateKind.ENTITY: P2T4ConflictReasonCode.ENTITY_ATTRIBUTE_CONTRADICTION,
    P2T4CandidateKind.ACTION: P2T4ConflictReasonCode.ACTION_CONTRADICTION,
    P2T4CandidateKind.RELATION: P2T4ConflictReasonCode.RELATION_CONTRADICTION,
}

_DECIMAL_ONE: Final = Decimal("1.0")


class P2T4FusionInputError(ValueError):
    """Raised by the pure boundary when a typed input fails admissibility or correlation.

    The message is the closed rejection code only; the safe typed rejection is attached.
    """

    def __init__(self, rejection: P2T4FusionInputRejectionV1) -> None:
        super().__init__(rejection.code.value)
        self.rejection = rejection


@dataclass(frozen=True)
class _Slot:
    slot: P2T4InputSlot
    expected: P2T4ExpectedIdentity
    own_identity: P2T4ObservedIdentity
    own_name: str
    own_types: tuple[type[object], ...]


_ASR_SLOT: Final = _Slot(
    P2T4InputSlot.ASR,
    P2T4ExpectedIdentity.P2_ASR_RESULT_V1,
    P2T4ObservedIdentity.P2_ASR_RESULT_V1,
    "AsrResultV1",
    (AsrSuccessV1, AsrFailureV1),
)
_VISION_SLOT: Final = _Slot(
    P2T4InputSlot.VISION,
    P2T4ExpectedIdentity.P2_VISION_UNDERSTANDING_RESULT_V1,
    P2T4ObservedIdentity.P2_VISION_UNDERSTANDING_RESULT_V1,
    "VisionUnderstandingResultV1",
    (VisionUnderstandingSuccessV1, VisionUnderstandingFailureV1),
)


# --- outer classification boundary --------------------------------------------------------


def _observed_status(value: object) -> P2T4ObservedStatus | None:
    if value is None:
        return None
    if value == "SUCCEEDED":
        return P2T4ObservedStatus.SUCCEEDED
    if value == "FAILED":
        return P2T4ObservedStatus.FAILED
    return P2T4ObservedStatus.UNKNOWN


def _reject(
    slot: _Slot,
    phase: P2T4RejectionPhase,
    code: P2T4RejectionCode,
    field_code: P2T4RejectionFieldCode,
    observed_identity: P2T4ObservedIdentity,
    observed_status: P2T4ObservedStatus | None,
) -> P2T4FusionInputRejectionV1:
    return P2T4FusionInputRejectionV1(
        input_slot=slot.slot,
        phase=phase,
        code=code,
        expected_identity=slot.expected,
        observed_identity=observed_identity,
        observed_status=observed_status,
        field_code=field_code,
    )


def _identity_stage(value: object, slot: _Slot) -> P2T4FusionInputRejectionV1 | None:
    phase = P2T4RejectionPhase.IDENTITY_VERSION
    if isinstance(value, slot.own_types):
        return None
    for model_type, identity in _TYPED_IDENTITIES:
        if isinstance(value, model_type):
            return _reject(
                slot,
                phase,
                P2T4RejectionCode.WRONG_FAMILY,
                P2T4RejectionFieldCode.UPSTREAM_TYPE,
                identity,
                _observed_status(getattr(value, "status", None)),
            )
    if not isinstance(value, Mapping):
        return _reject(
            slot,
            phase,
            P2T4RejectionCode.UNKNOWN_INPUT,
            P2T4RejectionFieldCode.UPSTREAM_TYPE,
            P2T4ObservedIdentity.UNKNOWN,
            None,
        )
    name = value.get("contract_name")
    version = value.get("contract_version")
    status = _observed_status(value.get("status"))
    if not isinstance(name, str):
        return _reject(
            slot,
            phase,
            P2T4RejectionCode.UNKNOWN_INPUT,
            P2T4RejectionFieldCode.CONTRACT_NAME,
            P2T4ObservedIdentity.UNKNOWN,
            status,
        )
    if name == slot.own_name:
        if version == "1.0":
            return None
        return _reject(
            slot,
            phase,
            P2T4RejectionCode.UNSUPPORTED_VERSION,
            P2T4RejectionFieldCode.CONTRACT_VERSION,
            P2T4ObservedIdentity.UNKNOWN,
            status,
        )
    if name in _KNOWN_SERIALIZED_NAMES:
        observed = P2T4ObservedIdentity.UNKNOWN
        if isinstance(version, str):
            observed = _SERIALIZED_IDENTITIES.get((name, version), P2T4ObservedIdentity.UNKNOWN)
        return _reject(
            slot,
            phase,
            P2T4RejectionCode.WRONG_FAMILY,
            P2T4RejectionFieldCode.CONTRACT_NAME,
            observed,
            status,
        )
    return _reject(
        slot,
        phase,
        P2T4RejectionCode.UNKNOWN_INPUT,
        P2T4RejectionFieldCode.CONTRACT_NAME,
        P2T4ObservedIdentity.UNKNOWN,
        status,
    )


def _field_code_from_validation_error(error: ValidationError) -> P2T4RejectionFieldCode:
    """Reduce a validation error to a closed top-level field token; nothing else escapes."""

    for detail in error.errors(include_url=False, include_context=False, include_input=False):
        for element in detail.get("loc", ()):
            if element in ("SUCCEEDED", "FAILED"):
                continue  # discriminated-union tag, not a field
            if isinstance(element, str) and element in _TOP_LEVEL_FIELD_CODES:
                return _TOP_LEVEL_FIELD_CODES[element]
            break
    return P2T4RejectionFieldCode.NONE


def _strict_stage(
    value: object, slot: _Slot, adapter: TypeAdapter[AsrInput] | TypeAdapter[VisionInput]
) -> tuple[AsrInput | VisionInput | None, P2T4FusionInputRejectionV1 | None]:
    phase = P2T4RejectionPhase.STRICT_VALIDATION
    if isinstance(value, slot.own_types):
        return value, None  # type: ignore[return-value]
    if not isinstance(value, Mapping):  # pragma: no cover - excluded by the identity stage
        raise TypeError("strict validation requires a mapping after identity classification")
    status = _observed_status(value.get("status"))
    if status is not P2T4ObservedStatus.SUCCEEDED and status is not P2T4ObservedStatus.FAILED:
        return None, _reject(
            slot,
            phase,
            P2T4RejectionCode.INVALID_DISCRIMINATOR,
            P2T4RejectionFieldCode.STATUS,
            slot.own_identity,
            status,
        )
    try:
        validated = adapter.validate_python(dict(value))
    except ValidationError as error:
        field_code = _field_code_from_validation_error(error)
    except (TypeError, ValueError):
        field_code = P2T4RejectionFieldCode.NONE
    else:
        return validated, None
    return None, _reject(
        slot,
        phase,
        P2T4RejectionCode.INVALID_STRUCTURE,
        field_code,
        slot.own_identity,
        status,
    )


def _admissibility_stage(asr: AsrInput) -> P2T4FusionInputRejectionV1 | None:
    if not isinstance(asr, AsrSuccessV1):
        return None
    indexes = [segment.index for segment in asr.segments]
    if len(indexes) != len(set(indexes)):
        return _reject(
            _ASR_SLOT,
            P2T4RejectionPhase.ADMISSIBILITY,
            P2T4RejectionCode.INVALID_STRUCTURE,
            P2T4RejectionFieldCode.DUPLICATE_SEGMENT_INDEX,
            P2T4ObservedIdentity.P2_ASR_RESULT_V1,
            P2T4ObservedStatus.SUCCEEDED,
        )
    return None


def _correlation_stage(asr: AsrInput, vision: VisionInput) -> P2T4FusionInputRejectionV1 | None:
    if asr.correlation_id == vision.correlation_id:
        return None
    return P2T4FusionInputRejectionV1(
        input_slot=P2T4InputSlot.BOTH,
        phase=P2T4RejectionPhase.CORRELATION,
        code=P2T4RejectionCode.CORRELATION_MISMATCH,
        expected_identity=P2T4ExpectedIdentity.NONE,
        observed_identity=P2T4ObservedIdentity.UNKNOWN,
        observed_status=None,
        field_code=P2T4RejectionFieldCode.CORRELATION_ID,
    )


def _admit(asr: AsrInput, vision: VisionInput) -> P2T4FusionInputRejectionV1 | None:
    return _admissibility_stage(asr) or _correlation_stage(asr, vision)


def validate_and_fuse(
    asr: object,
    vision: object,
    policy: P2T4FusionPolicyConfigV1,
    executed_at: datetime,
) -> FusionOutcome:
    """Classify two untrusted objects, then fuse only exact validated P2 V1 results.

    Only closed identity, version, and discriminator values are inspected for classification;
    the unknown object is never copied into a result. Every rejection is reduced to closed
    tokens: no `ValidationError`, exception text, field path, or input value escapes.
    """

    rejection = _identity_stage(asr, _ASR_SLOT) or _identity_stage(vision, _VISION_SLOT)
    if rejection is not None:
        return rejection
    validated_asr, rejection = _strict_stage(asr, _ASR_SLOT, _ASR_ADAPTER)
    if rejection is not None:
        return rejection
    validated_vision, rejection = _strict_stage(vision, _VISION_SLOT, _VISION_ADAPTER)
    if rejection is not None:
        return rejection
    if not isinstance(validated_asr, AsrSuccessV1 | AsrFailureV1) or not isinstance(
        validated_vision, VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1
    ):  # pragma: no cover - the adapters only return the exact P2 unions
        raise TypeError("strict validation returned a non-P2 model")
    rejection = _admit(validated_asr, validated_vision)
    if rejection is not None:
        return rejection
    return fuse(validated_asr, validated_vision, policy, executed_at)


# --- pure typed fusion boundary -----------------------------------------------------------


def fuse(
    asr: AsrInput,
    vision: VisionInput,
    policy: P2T4FusionPolicyConfigV1,
    executed_at: datetime,
) -> P2T4FusedResultV1:
    """Fuse two exact, already validated, immutable P2 V1 results under a validated policy.

    Raises `P2T4FusionInputError` (carrying the safe typed rejection) when the typed inputs
    fail P2-T4 admissibility or correlation equality; raises `ValueError` for a naive
    `executed_at`. Never performs model, provider, GPU, Lightning, or network work.
    """

    if not isinstance(asr, AsrSuccessV1 | AsrFailureV1):
        raise TypeError("asr must be an exact P2 AsrSuccessV1 or AsrFailureV1")
    if not isinstance(vision, VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1):
        raise TypeError("vision must be an exact P2 VisionUnderstandingSuccessV1/FailureV1")
    if not isinstance(policy, P2T4FusionPolicyConfigV1):
        raise TypeError("policy must be a validated P2T4FusionPolicyConfigV1")
    if executed_at.tzinfo is None or executed_at.utcoffset() is None:
        raise ValueError("executed_at must be timezone aware")
    rejection = _admit(asr, vision)
    if rejection is not None:
        raise P2T4FusionInputError(rejection)

    asr_ref = P2T4SourceResultRefV1(
        identity=P2T4SourceIdentity.P2_ASR_RESULT_V1,
        status=asr.status,
        result_sha256=canonical_sha256(asr),
    )
    vision_ref = P2T4SourceResultRefV1(
        identity=P2T4SourceIdentity.P2_VISION_UNDERSTANDING_RESULT_V1,
        status=vision.status,
        result_sha256=canonical_sha256(vision),
    )
    policy_hash = fusion_policy_config_hash(policy)

    if isinstance(asr, AsrSuccessV1) and isinstance(vision, VisionUnderstandingSuccessV1):
        return _fuse_successes(asr, vision, policy, executed_at, asr_ref, vision_ref, policy_hash)

    asr_failure = (
        P2T4AsrFailureReferenceV1(
            source_asr_result_ref=asr_ref,
            error_code=asr.error_code,
            error_detail=asr.error_detail,
            attempt_number=asr.attempt_number,
            retryable=asr.retryable,
            repair_attempted=asr.repair_attempted,
        )
        if isinstance(asr, AsrFailureV1)
        else None
    )
    vision_failure: P2T4VisionFailureReferenceV1 | None = None
    if isinstance(vision, VisionUnderstandingFailureV1):
        state = vision.policy_execution_state
        if state == "PASSED":  # pragma: no cover - the upstream failure matrix forbids it
            raise ValueError("a FAILED Vision result cannot carry policy_execution_state=PASSED")
        vision_failure = P2T4VisionFailureReferenceV1(
            source_vision_result_ref=vision_ref,
            error_code=vision.error_code,
            error_detail=vision.error_detail,
            attempt_number=vision.attempt_number,
            retryable=vision.retryable,
            repair_attempted=vision.repair_attempted,
            policy_execution_state=state,
        )
    if asr_failure is not None and vision_failure is not None:
        modality = P2T4FailedModality.BOTH
    elif asr_failure is not None:
        modality = P2T4FailedModality.ASR
    else:
        modality = P2T4FailedModality.VISION
    return P2T4FusedResultV1(
        status=P2T4FusedResultStatus.UPSTREAM_FAILURE,
        correlation_id=asr.correlation_id,
        executed_at=executed_at,
        source_asr_result_ref=asr_ref,
        source_vision_result_ref=vision_ref,
        fusion_policy_config_hash=policy_hash,
        entities=(),
        actions=(),
        relations=(),
        themes=(),
        conflicts=(),
        uncertainty=P2T4UncertaintySummaryV1(per_observation=()),
        upstream_failure=P2T4UpstreamFailureRefV1(
            failed_modality=modality,
            asr_failure_ref=asr_failure,
            vision_failure_ref=vision_failure,
        ),
    )


# --- matching, negation, and canonical references ----------------------------------------


@dataclass(frozen=True)
class _Evidence:
    positive_ref: P2T4NarrationClaimRefV1 | None
    refuting_ref: P2T4NarrationClaimRefV1 | None


_NO_EVIDENCE: Final = _Evidence(None, None)


def _segment_views(asr: AsrSuccessV1) -> tuple[tuple[int, tuple[str, ...]], ...]:
    """Per-segment match-view tokens, rebuilt from zero for every validated segment."""

    return tuple(
        (segment.index, vision_policy_match_view_tokens(segment.text)) for segment in asr.segments
    )


def _window_has_cue(window: tuple[str, ...], cues: tuple[tuple[str, ...], ...]) -> bool:
    for cue in cues:
        width = len(cue)
        if width == 0 or width > len(window):
            continue
        for offset in range(len(window) - width + 1):
            if window[offset : offset + width] == cue:
                return True
    return False


def _match_claim(
    claim_tokens: tuple[str, ...],
    segments: tuple[tuple[int, tuple[str, ...]], ...],
    policy: P2T4FusionPolicyConfigV1,
) -> _Evidence:
    if not claim_tokens:
        return _NO_EVIDENCE
    width = len(claim_tokens)
    window_size = policy.negation_window_tokens
    positive: set[tuple[int, int, int]] = set()
    refuting: set[tuple[int, int, int]] = set()
    for segment_index, tokens in segments:
        for start in range(len(tokens) - width + 1):
            if tokens[start : start + width] != claim_tokens:
                continue
            coordinate = (segment_index, start, start + width)
            window = tokens[max(0, start - window_size) : start]
            if _window_has_cue(window, policy.negation_cues):
                refuting.add(coordinate)
            else:
                positive.add(coordinate)
    return _Evidence(_earliest(positive), _earliest(refuting))


def _earliest(coordinates: set[tuple[int, int, int]]) -> P2T4NarrationClaimRefV1 | None:
    if not coordinates:
        return None
    segment_index, claim_start, claim_end = min(coordinates)
    return P2T4NarrationClaimRefV1(
        segment_index=segment_index, claim_start=claim_start, claim_end=claim_end
    )


# --- candidate records, conflicts, primary selection, and certainty ------------------------


@dataclass(frozen=True)
class _Candidate:
    kind: P2T4CandidateKind
    observation_id: str
    base_confidence: float | None
    group_key: tuple[str, str, str | None, str | None]
    evidence: _Evidence

    @property
    def supported(self) -> bool:
        return self.evidence.positive_ref is not None


def _collect_candidates(
    vision: VisionUnderstandingSuccessV1,
    segments: tuple[tuple[int, tuple[str, ...]], ...],
    policy: P2T4FusionPolicyConfigV1,
) -> tuple[_Candidate, ...]:
    candidates: list[_Candidate] = []
    for entity in vision.entities:
        claim = entity.label.value
        candidates.append(
            _Candidate(
                P2T4CandidateKind.ENTITY,
                entity.observation_id,
                entity.confidence,
                ("ENTITY", vision_policy_match_view(claim), None, None),
                _match_claim(vision_policy_match_view_tokens(claim), segments, policy),
            )
        )
    for action in vision.actions:
        claim = action.label.value
        candidates.append(
            _Candidate(
                P2T4CandidateKind.ACTION,
                action.observation_id,
                action.confidence,
                ("ACTION", vision_policy_match_view(claim), action.actor_ref, action.object_ref),
                _match_claim(vision_policy_match_view_tokens(claim), segments, policy),
            )
        )
    for relation in vision.relations:
        claim = relation.predicate.value
        candidates.append(
            _Candidate(
                P2T4CandidateKind.RELATION,
                relation.observation_id,
                relation.confidence,
                (
                    "RELATION",
                    vision_policy_match_view(claim),
                    relation.subject_ref,
                    relation.object_ref,
                ),
                _match_claim(vision_policy_match_view_tokens(claim), segments, policy),
            )
        )
    return tuple(candidates)


def _is_low_confidence(confidence: float | None, policy: P2T4FusionPolicyConfigV1) -> bool:
    return confidence is not None and confidence < policy.confidence_floor


def _conflict(
    reason: P2T4ConflictReasonCode, observation_id: str, ref: P2T4NarrationClaimRefV1 | None
) -> P2T4ConflictV1:
    return P2T4ConflictV1(
        conflict_id=conflict_id_for(reason, observation_id),
        reason_code=reason,
        vision_claim_ref=observation_id,
        narration_claim_ref=ref,
        recommended_reviewer_attention=True,
    )


def _rank_key(
    candidate: _Candidate, conflicting: frozenset[str]
) -> tuple[int, int, int, float, str]:
    """Conflict eligibility, positive support, original confidence (null last), then ID."""

    base = candidate.base_confidence
    return (
        int(candidate.observation_id in conflicting),
        int(not candidate.supported),
        int(base is None),
        -(base if base is not None else 0.0),
        candidate.observation_id,
    )


def _select_primaries(
    candidates: tuple[_Candidate, ...], conflicting: frozenset[str]
) -> frozenset[str]:
    groups: dict[tuple[str, str, str | None, str | None], list[_Candidate]] = {}
    for candidate in candidates:
        groups.setdefault(candidate.group_key, []).append(candidate)
    primaries: set[str] = set()
    for members in groups.values():
        best = min(members, key=lambda member: _rank_key(member, conflicting))
        if best.observation_id not in conflicting:
            primaries.add(best.observation_id)
    return frozenset(primaries)


def _certainty_row(
    candidate: _Candidate,
    conflicting: frozenset[str],
    primaries: frozenset[str],
    policy: P2T4FusionPolicyConfigV1,
) -> P2T4ObservationUncertaintyV1:
    base = candidate.base_confidence
    if candidate.observation_id in conflicting:
        status, certainty = P2T4CertaintyStatus.NOT_APPLICABLE_CONFLICTING, None
    elif base is None:
        status, certainty = P2T4CertaintyStatus.NOT_MEASURED, None
    else:
        status = P2T4CertaintyStatus.MEASURED
        certainty = base
        if candidate.observation_id in primaries and candidate.supported:
            adjusted = Decimal(str(base)) + policy.corroboration_increment_decimal()
            certainty = float(min(_DECIMAL_ONE, adjusted))
    return P2T4ObservationUncertaintyV1(
        observation_id=candidate.observation_id,
        candidate_kind=candidate.kind,
        certainty_status=status,
        certainty=certainty,
    )


def _fuse_successes(
    asr: AsrSuccessV1,
    vision: VisionUnderstandingSuccessV1,
    policy: P2T4FusionPolicyConfigV1,
    executed_at: datetime,
    asr_ref: P2T4SourceResultRefV1,
    vision_ref: P2T4SourceResultRefV1,
    policy_hash: str,
) -> P2T4FusedResultV1:
    segments = _segment_views(asr)
    candidates = _collect_candidates(vision, segments, policy)
    by_id = {candidate.observation_id: candidate for candidate in candidates}

    conflicts: list[P2T4ConflictV1] = []
    for candidate in candidates:
        if candidate.evidence.refuting_ref is not None:
            conflicts.append(
                _conflict(
                    _CONTRADICTION_REASON[candidate.kind],
                    candidate.observation_id,
                    candidate.evidence.refuting_ref,
                )
            )
        if _is_low_confidence(candidate.base_confidence, policy):
            conflicts.append(
                _conflict(
                    P2T4ConflictReasonCode.LOW_CONFIDENCE_EVIDENCE,
                    candidate.observation_id,
                    candidate.evidence.positive_ref,
                )
            )
    for theme in vision.themes:
        if _is_low_confidence(theme.confidence, policy):
            conflicts.append(
                _conflict(
                    P2T4ConflictReasonCode.LOW_CONFIDENCE_EVIDENCE, theme.observation_id, None
                )
            )
    conflicting = frozenset(conflict.vision_claim_ref for conflict in conflicts)
    primaries = _select_primaries(candidates, conflicting)

    def support(observation_id: str) -> tuple[bool, P2T4NarrationClaimRefV1 | None, bool]:
        candidate = by_id[observation_id]
        ref = candidate.evidence.positive_ref
        return ref is not None, ref, observation_id in primaries

    entities: list[P2T4FusedEntityV1] = []
    for entity in vision.entities:
        applied, ref, primary = support(entity.observation_id)
        entities.append(
            P2T4FusedEntityV1(
                fused_observation_id=entity.observation_id,
                source_observation_ref=entity.observation_id,
                label=entity.label,
                narration_support_applied=applied,
                narration_support_ref=ref,
                primary_interpretation=primary,
            )
        )
    actions: list[P2T4FusedActionV1] = []
    for action in vision.actions:
        applied, ref, primary = support(action.observation_id)
        actions.append(
            P2T4FusedActionV1(
                fused_observation_id=action.observation_id,
                source_observation_ref=action.observation_id,
                label=action.label,
                actor_ref=action.actor_ref,
                object_ref=action.object_ref,
                narration_support_applied=applied,
                narration_support_ref=ref,
                primary_interpretation=primary,
            )
        )
    relations: list[P2T4FusedRelationV1] = []
    for relation in vision.relations:
        applied, ref, primary = support(relation.observation_id)
        relations.append(
            P2T4FusedRelationV1(
                fused_observation_id=relation.observation_id,
                source_observation_ref=relation.observation_id,
                predicate=relation.predicate,
                subject_ref=relation.subject_ref,
                object_ref=relation.object_ref,
                narration_support_applied=applied,
                narration_support_ref=ref,
                primary_interpretation=primary,
            )
        )
    themes = tuple(
        P2T4FusedThemeV1(
            fused_observation_id=theme.observation_id,
            source_observation_ref=theme.observation_id,
            label=theme.label,
            evidence_refs=theme.evidence_refs,
        )
        for theme in vision.themes
    )
    rows = sorted(
        (_certainty_row(candidate, conflicting, primaries, policy) for candidate in candidates),
        key=P2T4ObservationUncertaintyV1.sort_key,
    )
    return P2T4FusedResultV1(
        status=P2T4FusedResultStatus.FUSED,
        correlation_id=asr.correlation_id,
        executed_at=executed_at,
        source_asr_result_ref=asr_ref,
        source_vision_result_ref=vision_ref,
        fusion_policy_config_hash=policy_hash,
        entities=tuple(entities),
        actions=tuple(actions),
        relations=tuple(relations),
        themes=themes,
        conflicts=tuple(sorted(conflicts, key=P2T4ConflictV1.sort_key)),
        uncertainty=P2T4UncertaintySummaryV1(per_observation=tuple(rows)),
        upstream_failure=None,
    )
