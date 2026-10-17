"""Offline BE2-02 C2 typed-context client over an injected transport (never live).

Implements ``VisionObservationPort`` for ``typed_context`` only. The static reviewed
capability (contract, version, fields, ``offline_injected`` transport) and the pinned request
integrity are checked before any image load or call; there is no image_only fallback, no
retry and the real HTTP transport is refused. The unchanged ``LightningVisionV2Adapter`` is
reused for image loading/validation, the V2 result contract, identity and lexical policy: its
single ``post_json`` is intercepted, wrapped as ``LightningVisionContextRequestV1`` with the
minimized ``VisionTypedContextV1`` and both digests, and posted once to the candidate path
``/v1/vision/context``. The ``LightningVisionContextResultV1`` wrapper must echo contract,
revision, digests, correlation and source image; the nested V2 result is then verified exactly
like the C1 bridge. The WHOLE wrapper document is retained and hashed. Evidence is truthful
``offline_context_adapter``: an echo binds the request, it does not prove the model used it.
"""

from __future__ import annotations

import math
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
from sketch2life.contracts.schemas.vision_context import (
    CONTEXT_CLIENT_VERSION,
    CONTEXT_ENDPOINT_PATH,
    CONTEXT_REQUEST_CONTRACT,
    LightningVisionContextRequestV1,
    LightningVisionContextResultV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    vision_profile_catalog_v2,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.domain.vision_analysis import (
    EvidenceKind,
    LexicalOutcome,
    ModerationOutcome,
    ObservationEvidence,
    ProviderContextMode,
    document_sha256,
    observation_bounds_violation,
)
from sketch2life.domain.vision_context import (
    C2_CONTEXT_CAPABILITY,
    CANONICAL_RULES_VERSION,
    ContextCapability,
    ProviderTypedContext,
    payload_digest,
)
from sketch2life.infrastructure.ai.lightning_client import JsonTransport, UrllibJsonTransport
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)
from sketch2life.infrastructure.vision_analysis.legacy_v2 import (
    LiveTransportForbidden,
    failure_for,
    map_v2_observation,
    precheck_image_request,
    v2_request_for,
    verify_v2_success,
)

CONTEXT_ADAPTER_ID = "lightning-vision-context-offline"
CONTEXT_RESULT_REF = "LightningVisionContextResultV1/0.1-candidate"


class _WrapperRejected(Exception):
    """The context envelope (outgoing or echoed) broke its contract; closed detail token."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _json_native(value: object) -> bool:
    if value is None or isinstance(value, bool | str | int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(isinstance(k, str) and _json_native(v) for k, v in value.items())
    if isinstance(value, list | tuple):
        return all(_json_native(item) for item in value)
    return False


class _ContextEnvelope:
    """``JsonTransport`` seen by the reused V2 adapter. Wraps its single V2 body into the
    context request, posts once, validates the echo and hands back the nested V2 result."""

    def __init__(
        self,
        inner: JsonTransport,
        typed: ProviderTypedContext,
        v2_request: VisionUnderstandingRequestV2,
    ) -> None:
        self._inner = inner
        self._typed = typed
        self._v2_request = v2_request
        self.calls = 0
        self.document: str | None = None
        self.raw_result: Mapping[str, object] | None = None

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        if self.calls:
            raise RuntimeError("the BE2-02 context adapter never repeats a provider call")
        if path != CONTEXT_ENDPOINT_PATH or set(payload) != {
            "contract_name", "contract_version", "request", "source_image"
        }:
            # Never forward a narration hint or any other field into the context request.
            raise _WrapperRejected("REQUEST_SHAPE_UNEXPECTED")
        binding = self._typed.binding
        body: dict[str, object] = {
            "contract_name": CONTEXT_REQUEST_CONTRACT,
            "contract_version": CONTEXT_CLIENT_VERSION,
            "request": payload["request"],
            "source_image": payload["source_image"],
            "typed_context": self._typed.projection.canonical(),
            "payload_digest": binding.payload_digest,
            "context_digest": binding.context_digest,
        }
        try:
            LightningVisionContextRequestV1.model_validate_json(canonical_json(body))
        except ValidationError:
            raise _WrapperRejected("REQUEST_CONTRACT_INVALID") from None
        self.calls += 1
        raw = self._inner.post_json(CONTEXT_ENDPOINT_PATH, body)
        if not isinstance(raw, Mapping) or not _json_native(raw):
            raise _WrapperRejected("RESPONSE_NOT_JSON")
        document = canonical_json(raw)
        try:
            wrapper = LightningVisionContextResultV1.model_validate_json(document)
        except ValidationError:
            raise _WrapperRejected("WRAPPER_INVALID") from None
        if (
            wrapper.correlation_id != self._v2_request.correlation_id
            or wrapper.source_image_ref != self._v2_request.source_image_ref
        ):
            raise _WrapperRejected("ECHO_IDENTITY_MISMATCH")
        if (
            wrapper.context_contract != binding.context_contract
            or wrapper.context_contract_version != binding.context_contract_version
            or wrapper.context_revision != binding.context_revision
            or wrapper.payload_digest != binding.payload_digest
            or wrapper.context_digest != binding.context_digest
        ):
            raise _WrapperRejected("ECHO_CONTEXT_MISMATCH")
        nested = raw["result"]
        if not isinstance(nested, Mapping):  # pragma: no cover - the wrapper validated it
            raise _WrapperRejected("WRAPPER_INVALID")
        self.document = document
        self.raw_result = nested
        return nested


class OfflineVisionContextAdapter:
    def __init__(
        self,
        *,
        transport: JsonTransport,
        render_loader: Callable[[str], bytes],
        profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if isinstance(transport, UrllibJsonTransport):
            raise LiveTransportForbidden("real provider transport is not authorized in C2")
        self._transport = transport
        self._render_loader = render_loader
        self._clock = clock
        self._catalog = vision_profile_catalog_v2()
        self._profile = self._catalog.resolve(profile_id)
        self._policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())

    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]:
        return frozenset({ProviderContextMode.TYPED_CONTEXT})

    @property
    def context_capability(self) -> ContextCapability | None:
        return C2_CONTEXT_CAPABILITY

    def observe(self, request: ObservationRequest) -> ObservationOutcome:
        typed = request.typed_context
        if request.context_mode is not ProviderContextMode.TYPED_CONTEXT or typed is None:
            return ObservationFailed(ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED, False)
        refused = self._precheck(request, typed)
        if refused is not None:
            return refused
        v2_request = v2_request_for(request, self._profile.profile_id)
        envelope = _ContextEnvelope(self._transport, typed, v2_request)
        adapter = LightningVisionV2Adapter(
            transport=envelope,
            artifact_loader=self._render_loader,
            endpoint_path=CONTEXT_ENDPOINT_PATH,
            clock=self._clock,
        )
        try:
            result = adapter.understand(v2_request)
        except _WrapperRejected as exc:
            return ObservationFailed(ObservationFailureCode.OUTPUT_MALFORMED,
                                     envelope.calls > 0, detail=exc.detail)
        except ValidationError:
            # Same containment as the C1 bridge for the legacy adapter's F-01 branch.
            return ObservationFailed(ObservationFailureCode.PROVIDER_ERROR, envelope.calls > 0,
                                     detail="LEGACY_ADAPTER_CONTRACT_ERROR")
        invoked = envelope.calls > 0
        if isinstance(result, VisionUnderstandingFailureV2):
            return failure_for(result, invoked)
        mismatch = verify_v2_success(result, v2_request, envelope.raw_result,
                                     catalog=self._catalog, profile=self._profile,
                                     policy=self._policy)
        if mismatch is not None or envelope.document is None:
            return ObservationFailed(ObservationFailureCode.OUTPUT_MALFORMED, invoked,
                                     detail=mismatch or "WRAPPER_NOT_RETAINED")
        observation = map_v2_observation(result)
        violation = observation_bounds_violation(observation)
        if violation is not None:
            return ObservationFailed(ObservationFailureCode.OUTPUT_MALFORMED, invoked,
                                     detail=violation)
        evidence = ObservationEvidence(
            evidence_kind=EvidenceKind.OFFLINE_CONTEXT_ADAPTER,
            provider_context_mode=ProviderContextMode.TYPED_CONTEXT,
            adapter_id=CONTEXT_ADAPTER_ID,
            result_contract=CONTEXT_RESULT_REF,
            # The whole retained wrapper, not only the nested V2 result.
            result_sha256=document_sha256(envelope.document),
            executed_at=result.executed_at,
            transport_attempts=envelope.calls,
            profile_id=str(result.profile_id),
            profile_catalog_hash=result.profile_catalog_hash,
            config_hash=result.config_hash,
            adapter_version=result.adapter_version,
            model_identifier=result.model_provenance.model_identifier,
            model_revision=result.model_provenance.model_revision,
            content_policy_version=result.content_policy_version,
            policy_match_view_version=result.policy_match_view_version,
            context_binding=typed.binding,
        )
        moderation = ModerationOutcome(
            LexicalOutcome.PASSED, result.content_policy_version, result.policy_match_view_version
        )
        return ObservationSucceeded(observation, evidence, moderation,
                                    result_document=envelope.document)

    def _precheck(
        self, request: ObservationRequest, typed: ProviderTypedContext
    ) -> ObservationFailed | None:
        """Capability and pinned-request integrity, then the shared image pre-checks; all
        before any image load or transport call."""

        binding, projection = typed.binding, typed.projection
        capability = C2_CONTEXT_CAPABILITY
        if (
            binding.context_contract != capability.contract
            or binding.context_contract_version != capability.contract_version
            or binding.canonical_rules_version != CANONICAL_RULES_VERSION
        ):
            return ObservationFailed(ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED, False,
                                     detail="CONTEXT_CONTRACT_UNSUPPORTED")
        if (
            payload_digest(projection) != binding.payload_digest
            or projection.context_revision != binding.context_revision
            or projection.age_band_policy_ref != binding.age_band_policy_ref
            or projection.age_band_policy_version != binding.age_band_policy_version
        ):
            return ObservationFailed(ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED, False,
                                     detail="CONTEXT_BINDING_INCONSISTENT")
        if projection.source_image_sha256 != request.render.render_sha256:
            return ObservationFailed(ObservationFailureCode.SOURCE_REJECTED, False,
                                     detail="CONTEXT_SOURCE_MISMATCH")
        return precheck_image_request(request)


__all__ = [
    "CONTEXT_ADAPTER_ID",
    "CONTEXT_RESULT_REF",
    "OfflineVisionContextAdapter",
]
