"""Offline BE2-02 bridge from ``VisionObservationPort`` to the existing Vision V2 adapter.

Reuses ``LightningVisionV2Adapter`` unchanged through an injected ``JsonTransport``,
artifact loader and clock. It is explicitly ``image_only``: V2 has no typed topic/age/context
field, so a typed-context request is refused before any call and no Child intent, topic, age or
actor is ever placed in the adult ``narration_context`` hint (the bridge only calls
``understand``). The real network transport is refused under C1. Beyond the adapter's own
correlation/image/profile check it verifies the canonical catalog and config hashes, adapter
version, model provenance, policy versions and the raw confidence types, and it maps the whole
original typed result and returns its canonical document for retention. There is no retry: at
most one transport call per observation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from pydantic import ValidationError

from sketch2life.application.ports.vision_analysis import (
    ObservationFailed,
    ObservationFailureCode,
    ObservationOutcome,
    ObservationRequest,
    ObservationSucceeded,
)
from sketch2life.contracts.schemas.vision import (
    ObservedTextV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.domain.vision_analysis import (
    SUPPORTED_RENDER_MEDIA_TYPES,
    ActionObservation,
    AmbiguousRegionObservation,
    AnalysisRuleViolation,
    EntityObservation,
    EvidenceKind,
    LexicalOutcome,
    ModerationOutcome,
    ObservationEvidence,
    ObservedLabel,
    OriginalObservation,
    ProviderContextMode,
    RelationObservation,
    ThemeObservation,
    document_sha256,
    observation_bounds_violation,
    require_confidence,
)
from sketch2life.infrastructure.ai.lightning_client import JsonTransport, UrllibJsonTransport
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

BRIDGE_ADAPTER_ID = "lightning-vision-v2-bridge"
RESULT_CONTRACT = "VisionUnderstandingResultV2/2.0"
_CANDIDATE_KEYS = ("entities", "actions", "relations", "themes")

_FAILURE_CODES: Mapping[VisionErrorCode, ObservationFailureCode] = {
    VisionErrorCode.INPUT_NOT_VALIDATED: ObservationFailureCode.SOURCE_REJECTED,
    VisionErrorCode.VISION_TIMEOUT: ObservationFailureCode.PROVIDER_TIMEOUT,
    VisionErrorCode.VISION_MODEL_UNAVAILABLE: ObservationFailureCode.PROVIDER_UNAVAILABLE,
    VisionErrorCode.VISION_PROVIDER_FAILURE: ObservationFailureCode.PROVIDER_ERROR,
    VisionErrorCode.VISION_SCHEMA_INVALID: ObservationFailureCode.OUTPUT_MALFORMED,
    VisionErrorCode.PROHIBITED_CLAIM_DETECTED: ObservationFailureCode.UNSAFE_CONTENT,
}


class LiveTransportForbidden(ValueError):
    """C1 is offline: the real HTTP transport cannot be injected into this bridge."""


class _RecordingTransport:
    """Counts calls and keeps the raw response for strict post-validation; never retries."""

    def __init__(self, inner: JsonTransport) -> None:
        self._inner = inner
        self.calls = 0
        self.raw: Mapping[str, object] | None = None

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        if self.calls:
            raise RuntimeError("the BE2-02 bridge never repeats a provider call")
        self.calls += 1
        response = self._inner.post_json(path, payload)
        self.raw = response
        return response


class LegacyVisionV2Bridge:
    def __init__(
        self,
        *,
        transport: JsonTransport,
        render_loader: Callable[[str], bytes],
        profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        endpoint_path: str = "/v2/vision",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if isinstance(transport, UrllibJsonTransport):
            raise LiveTransportForbidden("real provider transport is not authorized in C1")
        self._transport = transport
        self._render_loader = render_loader
        self._endpoint_path = endpoint_path
        self._clock = clock
        self._catalog = vision_profile_catalog_v2()
        self._profile = self._catalog.resolve(profile_id)
        self._policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())

    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]:
        return frozenset({ProviderContextMode.IMAGE_ONLY})

    def observe(self, request: ObservationRequest) -> ObservationOutcome:
        if (
            request.context_mode is not ProviderContextMode.IMAGE_ONLY
            or request.typed_context is not None
        ):
            return ObservationFailed(ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED, False)
        if request.processing_image_ref is not None:
            return ObservationFailed(ObservationFailureCode.DERIVED_INPUT_UNSUPPORTED, False)
        render, admission = request.render, request.admission
        if render.media_type not in SUPPORTED_RENDER_MEDIA_TYPES:
            return ObservationFailed(ObservationFailureCode.MEDIA_TYPE_UNSUPPORTED, False)
        if (
            admission.render_ref != render.render_ref
            or admission.render_sha256 != render.render_sha256
            or admission.decision != "PASS"
        ):
            return ObservationFailed(ObservationFailureCode.ADMISSION_NOT_BOUND, False)

        v2_request = VisionUnderstandingRequestV2(
            correlation_id=request.correlation_id,
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=render.render_ref, sha256=render.render_sha256
            ),
            # Legacy field filled only from the trusted receipt already bound to this render.
            media_validation=VisionMediaValidationProvenanceV1(
                validation_artifact_ref=admission.receipt_id,
                validation_artifact_sha256=admission.receipt_sha256,
                decision="PASS",
                validator_policy_version=admission.policy_version,
            ),
            requested_profile_id=self._profile.profile_id,
        )
        recorder = _RecordingTransport(self._transport)
        adapter = LightningVisionV2Adapter(
            transport=recorder,
            artifact_loader=self._render_loader,
            endpoint_path=self._endpoint_path,
            clock=self._clock,
        )
        try:
            result = adapter.understand(v2_request)
        except ValidationError:
            # The unchanged legacy adapter can build an invalid V2 failure (its OSError branch
            # uses attempt 1 where the V2 matrix requires 2); contain it as a typed failure.
            return ObservationFailed(ObservationFailureCode.PROVIDER_ERROR, recorder.calls > 0,
                                     detail="LEGACY_ADAPTER_CONTRACT_ERROR")
        invoked = recorder.calls > 0
        if isinstance(result, VisionUnderstandingFailureV2):
            return ObservationFailed(
                _FAILURE_CODES[result.error_code],
                invoked,
                retryable=result.retryable,
                detail=str(result.error_detail),
            )
        mismatch = self._verify(result, v2_request, recorder.raw)
        if mismatch is not None:
            return ObservationFailed(ObservationFailureCode.OUTPUT_MALFORMED, invoked,
                                     detail=mismatch)
        observation = _map_observation(result)
        # Every mapped bound the DATA-22 contracts enforce is checked before acceptance, so an
        # accepted analysis always projects (C1-R04); the original is never truncated.
        violation = observation_bounds_violation(observation)
        if violation is not None:
            return ObservationFailed(ObservationFailureCode.OUTPUT_MALFORMED, invoked,
                                     detail=violation)
        document = canonical_json(result.model_dump(mode="json"))
        evidence = ObservationEvidence(
            evidence_kind=EvidenceKind.OFFLINE_LEGACY_BRIDGE,
            provider_context_mode=ProviderContextMode.IMAGE_ONLY,
            adapter_id=BRIDGE_ADAPTER_ID,
            result_contract=RESULT_CONTRACT,
            result_sha256=document_sha256(document),
            executed_at=result.executed_at,
            transport_attempts=recorder.calls,
            profile_id=str(result.profile_id),
            profile_catalog_hash=result.profile_catalog_hash,
            config_hash=result.config_hash,
            adapter_version=result.adapter_version,
            model_identifier=result.model_provenance.model_identifier,
            model_revision=result.model_provenance.model_revision,
            content_policy_version=result.content_policy_version,
            policy_match_view_version=result.policy_match_view_version,
        )
        # The adapter's lexical regression passed; that is not comprehensive moderation.
        moderation = ModerationOutcome(
            LexicalOutcome.PASSED, result.content_policy_version, result.policy_match_view_version
        )
        return ObservationSucceeded(observation, evidence, moderation, result_document=document)

    def _verify(
        self,
        result: VisionUnderstandingSuccessV2,
        request: VisionUnderstandingRequestV2,
        raw: Mapping[str, object] | None,
    ) -> str | None:
        if (
            result.correlation_id != request.correlation_id
            or result.source_image_ref != request.source_image_ref
            or result.profile_id is not request.requested_profile_id
        ):
            return "IDENTITY_MISMATCH"
        if result.profile_catalog_hash != vision_profile_catalog_hash_v2(self._catalog):
            return "CATALOG_HASH_MISMATCH"
        if result.config_hash != vision_profile_config_hash_v2(self._profile):
            return "CONFIG_HASH_MISMATCH"
        if result.adapter_version != self._profile.adapter_version:
            return "ADAPTER_VERSION_MISMATCH"
        if result.model_provenance != self._profile.model_provenance:
            return "MODEL_PROVENANCE_MISMATCH"
        if (
            result.content_policy_version != self._policy.content_policy_version
            or result.policy_match_view_version != self._policy.policy_match_view_version
        ):
            return "POLICY_VERSION_MISMATCH"
        if raw is None or not _raw_confidences_strict(raw):
            return "CONFIDENCE_NOT_STRICT"
        return None


def _raw_confidences_strict(raw: Mapping[str, object]) -> bool:
    """V2 validates in lax mode (``"0.5"``/``true`` would coerce); re-check the raw values."""

    for key in _CANDIDATE_KEYS:
        items = raw.get(key)
        if not isinstance(items, list | tuple):
            return False
        for item in items:
            if not isinstance(item, Mapping) or "confidence" not in item:
                return False
            try:
                require_confidence(item["confidence"])
            except AnalysisRuleViolation:
                return False
    return True


def _label(text: ObservedTextV1) -> ObservedLabel:
    return ObservedLabel(text.value, text.language.status, text.language.tags)


def _map_observation(result: VisionUnderstandingSuccessV2) -> OriginalObservation:
    return OriginalObservation(
        entities=tuple(
            EntityObservation(e.observation_id, _label(e.label), e.confidence)
            for e in result.entities
        ),
        actions=tuple(
            ActionObservation(a.observation_id, _label(a.label), a.actor_ref, a.object_ref,
                              a.confidence)
            for a in result.actions
        ),
        relations=tuple(
            RelationObservation(r.observation_id, _label(r.predicate), r.subject_ref,
                                r.object_ref, r.confidence)
            for r in result.relations
        ),
        themes=tuple(
            ThemeObservation(t.observation_id, _label(t.label), t.evidence_refs, t.confidence)
            for t in result.themes
        ),
        ambiguous_regions=tuple(
            AmbiguousRegionObservation(g.observation_id, _label(g.note))
            for g in result.ambiguous_regions
        ),
    )


__all__ = [
    "BRIDGE_ADAPTER_ID",
    "RESULT_CONTRACT",
    "LegacyVisionV2Bridge",
    "LiveTransportForbidden",
]
