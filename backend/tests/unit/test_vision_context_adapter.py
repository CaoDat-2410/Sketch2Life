"""BE2-02 C2 offline typed-context adapter (C2-A04/A05/A06/A07/A10).

Every transport is an in-memory echo/fake: no network, server, provider, model or weights.
The candidate endpoint does not exist anywhere; only the client contract is exercised.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from hashlib import sha256

import pytest

from sketch2life.application.ports.vision_analysis import (
    ObservationFailed,
    ObservationFailureCode,
    ObservationRequest,
)
from sketch2life.application.services.vision_analysis import ObservationDisposition
from sketch2life.contracts.schemas.vision_context import (
    LightningVisionContextRequestV1,
    LightningVisionContextResultV1,
    VisionTypedContextV1,
)
from sketch2life.domain.ai_jobs.completion import canonical_json, canonical_sha256
from sketch2life.domain.vision_analysis import (
    EvidenceKind,
    ProviderContextMode,
    provider_result_ref,
)
from sketch2life.domain.vision_context import FIXTURE_AGE_BAND_POLICY, pin_context
from sketch2life.infrastructure.ai.lightning_client import (
    LightningProviderError,
    UrllibJsonTransport,
)
from sketch2life.infrastructure.vision_analysis.context_adapter import (
    CONTEXT_RESULT_REF,
    OfflineVisionContextAdapter,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    TEACHER,
    AnalysisHarness,
    EchoContextTransport,
    build_analysis_harness,
    build_context_harness,
    synthetic_v2_response,
)
from sketch2life.infrastructure.vision_analysis.legacy_v2 import (
    LegacyVisionV2Bridge,
    LiveTransportForbidden,
)


class _CountingLoader:
    def __init__(self, inner: Callable[[str], bytes]) -> None:
        self.inner = inner
        self.loads = 0

    def __call__(self, ref: str) -> bytes:
        self.loads += 1
        return self.inner(ref)


def _harness() -> tuple[AnalysisHarness, EchoContextTransport, _CountingLoader]:
    transport = EchoContextTransport()
    loaders: list[_CountingLoader] = []

    def factory(sources, clock):  # type: ignore[no-untyped-def]
        loaders.append(_CountingLoader(sources.read_render))
        return OfflineVisionContextAdapter(transport=transport, render_loader=loaders[0],
                                           clock=clock.now)

    h = build_analysis_harness(provider_factory=factory,
                               required_context_mode=ProviderContextMode.TYPED_CONTEXT)
    return h, transport, loaders[0]


def _typed_request(h: AnalysisHarness, **changes: object) -> ObservationRequest:
    snapshot = h.context_sources.resolve(h.pin, h.snapshot)
    assert snapshot is not None
    base = ObservationRequest(
        correlation_id="corr_fx_1", organization_id=h.pin.scope.organization_id,
        render=h.snapshot.render, admission=h.receipt,
        context_mode=ProviderContextMode.TYPED_CONTEXT,
        typed_context=pin_context(snapshot, FIXTURE_AGE_BAND_POLICY),
    )
    return replace(base, **changes)  # type: ignore[arg-type]


def _stored(h: AnalysisHarness) -> tuple[int, int, int]:
    state = h.store.snapshot()
    return len(state.heads), len(state.observations), len(state.provider_results)


# ------------------------------------------------ C2-A05 exact endpoint/body, once
def test_c2_a05_exact_context_request_is_posted_once_to_the_candidate_path() -> None:
    h, transport, loader = _harness()
    result = h.observe()
    assert result.authoritative and loader.loads == 1
    ((path, body),) = transport.posted
    assert path == "/v1/vision/context"
    assert set(body) == {"contract_name", "contract_version", "request", "source_image",
                         "typed_context", "payload_digest", "context_digest"}
    parsed = LightningVisionContextRequestV1.model_validate_json(canonical_json(body))
    assert parsed.request.correlation_id == "corr_fx_1"
    assert parsed.request.processing_image_ref is None
    typed = body["typed_context"]
    assert isinstance(typed, Mapping)
    VisionTypedContextV1.model_validate_json(json.dumps(typed))
    # payload_digest is independently recomputable from the sent projection alone.
    assert canonical_sha256(typed) == body["payload_digest"]
    assert body["payload_digest"] != body["context_digest"]
    # A second, sequential replay makes no new call.
    assert h.observe().replayed and len(transport.posted) == 1


def test_c2_a04_a05_serialized_bytes_carry_no_internal_or_child_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    h, transport, _ = _harness()
    # Shared canvas audience (no group, so the bound device A may still propose).
    h.pin = replace(h.pin, scope=replace(h.pin.scope,
                                         audience_participant_ids=(CHILD_A, CHILD_B)))
    h.requests.add(h.pin)
    h.set_job()
    with caplog.at_level(logging.DEBUG):
        analysis_id = h.accepted_analysis()
        h.service.submit_correction(h.correction(DEVICE_A, analysis_id,
                                                 explanation="It has stripes and a tail"))
    ((_, body),) = transport.posted
    wire = canonical_json(body)
    for forbidden in (CHILD_A, CHILD_B, "consent-record", "profile-age", "teacher_fx_001",
                      "device_fx", "participant", "narration_context", "stripes", "tiger",
                      "child_explanation", "feedback", "action", '"60"', "120",
                      "organization_id", "org_fx", "class_fx", "session_fx", "group_fx",
                      "assistance_fx"):
        assert forbidden not in wire, forbidden
    assert body["typed_context"]["audience_age_bands"] == [  # type: ignore[index]
        "completed-years-10", "completed-years-5"]
    logged = " ".join(record.getMessage() for record in caplog.records)
    for forbidden in (CHILD_A, "consent-record", "profile-age", "completed-years"):
        assert forbidden not in logged


def test_c2_a05_v2_endpoint_and_payload_are_unchanged_for_image_only() -> None:
    posted: list[tuple[str, Mapping[str, object]]] = []

    class V2Transport:
        def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
            posted.append((path, payload))
            return synthetic_v2_response()

    h = build_analysis_harness(provider_factory=lambda sources, clock: LegacyVisionV2Bridge(
        transport=V2Transport(), render_loader=sources.read_render, clock=clock.now))
    assert h.observe().authoritative
    ((path, payload),) = posted
    assert path == "/v2/vision"
    assert set(payload) == {"contract_name", "contract_version", "request", "source_image"}
    assert "typed_context" not in canonical_json(payload)


# ----------------------------------------------- C2-A06 unsupported -> zero loads/calls
@pytest.mark.parametrize(
    "changes",
    [
        {"context_mode": ProviderContextMode.IMAGE_ONLY, "typed_context": None},
        {"processing_image_ref": "render_fx_004_crop"},
    ],
)
def test_c2_a06_no_image_only_fallback_and_no_derived_input(changes: dict[str, object]) -> None:
    h, transport, loader = _harness()
    outcome = h.provider.observe(_typed_request(h, **changes))
    assert isinstance(outcome, ObservationFailed) and not outcome.provider_invoked
    assert loader.loads == 0 and transport.posted == []


@pytest.mark.parametrize(
    ("binding_change", "projection_change", "code"),
    [
        ({"context_contract_version": "0.2-candidate"}, {},
         ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED),
        ({"canonical_rules_version": "vision-context-canonical-v0"}, {},
         ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED),
        ({"payload_digest": "a" * 64}, {}, ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED),
        ({"context_revision": 4}, {}, ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED),
        # Projection edited without re-pinning: its payload digest no longer matches.
        ({}, {"source_image_sha256": "f" * 64}, ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED),
    ],
)
def test_c2_a06_inconsistent_pinned_context_refuses_before_image_load(
    binding_change: dict[str, object], projection_change: dict[str, object],
    code: ObservationFailureCode,
) -> None:
    h, transport, loader = _harness()
    request = _typed_request(h)
    assert request.typed_context is not None
    typed = replace(request.typed_context,
                    binding=replace(request.typed_context.binding,
                                    **binding_change),  # type: ignore[arg-type]
                    projection=replace(request.typed_context.projection,
                                       **projection_change))  # type: ignore[arg-type]
    outcome = h.provider.observe(replace(request, typed_context=typed))
    assert isinstance(outcome, ObservationFailed) and outcome.code is code
    assert not outcome.provider_invoked and loader.loads == 0 and transport.posted == []


def test_c2_a06_context_pinned_to_another_image_is_refused_before_load() -> None:
    h, transport, loader = _harness()
    request = _typed_request(h)
    other = replace(request, render=replace(request.render, render_sha256="f" * 64))
    outcome = h.provider.observe(other)
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.SOURCE_REJECTED
    assert outcome.detail == "CONTEXT_SOURCE_MISMATCH"
    assert loader.loads == 0 and transport.posted == []


def test_c2_a06_real_http_transport_is_refused_and_capability_is_static() -> None:
    with pytest.raises(LiveTransportForbidden):
        OfflineVisionContextAdapter(
            transport=UrllibJsonTransport(base_url="http://localhost:9", token=""),
            render_loader=lambda _ref: b"",
        )
    h, _, _ = _harness()
    assert h.provider.supported_context_modes == frozenset({ProviderContextMode.TYPED_CONTEXT})
    assert h.provider.context_capability is not None
    assert h.provider.context_capability.transport_kind == "offline_injected"
    bridge = build_analysis_harness(
        provider_factory=lambda sources, clock: LegacyVisionV2Bridge(
            transport=EchoContextTransport(), render_loader=sources.read_render,
            clock=clock.now),
        required_context_mode=ProviderContextMode.TYPED_CONTEXT)
    assert bridge.observe().code == "CONTEXT_MODE_UNSUPPORTED"


# ------------------------------------------------- C2-A07 strict echo, both layers
def _set(
    path: tuple[str | int, ...], value: object
) -> Callable[[dict[str, object]], dict[str, object]]:
    def tamper(response: dict[str, object]) -> dict[str, object]:
        doc = json.loads(json.dumps(response))
        target = doc
        for key in path[:-1]:
            target = target[key]
        if value is _DROP:
            del target[path[-1]]
        else:
            target[path[-1]] = value
        return doc  # type: ignore[no-any-return]
    return tamper


_DROP = object()


@pytest.mark.parametrize(
    ("tamper", "detail"),
    [
        (_set(("payload_digest",), "a" * 64), "ECHO_CONTEXT_MISMATCH"),
        (_set(("context_digest",), "b" * 64), "ECHO_CONTEXT_MISMATCH"),
        (_set(("context_revision",), 4), "ECHO_CONTEXT_MISMATCH"),
        (_set(("context_digest",), _DROP), "WRAPPER_INVALID"),
        (_set(("context_revision",), "3"), "WRAPPER_INVALID"),
        (_set(("context_contract_version",), "0.2-candidate"), "WRAPPER_INVALID"),
        (_set(("narration_context",), "a cat"), "WRAPPER_INVALID"),
        (_set(("correlation_id",), "corr_fx_2"), "WRAPPER_INVALID"),
        (_set(("source_image_ref", "sha256"), "e" * 64), "WRAPPER_INVALID"),
        (_set(("result", "config_hash"), "c" * 64), "CONFIG_HASH_MISMATCH"),
        (_set(("result", "entities", 0, "confidence"), "0.71"), "CONFIDENCE_NOT_STRICT"),
        (_set(("result", "entities", 0, "observation_id"), "ent-1\n"),
         "OBSERVATION_REF_INVALID"),
        (_set(("payload_digest",), float("nan")), "RESPONSE_NOT_JSON"),
    ],
)
def test_c2_a07_wrong_or_missing_echo_or_nested_identity_is_malformed_and_unstored(
    tamper: Callable[[dict[str, object]], dict[str, object]], detail: str
) -> None:
    h, transport, _ = _harness()
    transport.tamper = tamper
    outcome = h.provider.observe(_typed_request(h))
    assert isinstance(outcome, ObservationFailed) and outcome.provider_invoked
    assert outcome.code in {ObservationFailureCode.OUTPUT_MALFORMED,
                            ObservationFailureCode.UNSAFE_CONTENT}
    if detail not in {"OBSERVATION_REF_INVALID"}:
        assert outcome.detail == detail
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED and _stored(h) == (0, 0, 0)
    assert len(transport.posted) == 2  # one per observe call, never retried


def test_c2_a07_whole_wrapper_is_retained_and_hashed() -> None:
    h, transport, _ = _harness()
    analysis_id = h.accepted_analysis()
    record = h.service.resolve_provider_result(TEACHER, provider_result_ref(analysis_id))
    wrapper = LightningVisionContextResultV1.model_validate_json(record.canonical_json)
    ((_, body),) = transport.posted
    assert wrapper.payload_digest == body["payload_digest"]
    assert wrapper.context_digest == body["context_digest"]
    assert sha256(record.canonical_json.encode("utf-8")).hexdigest() == record.result_sha256
    assert record.result_contract == CONTEXT_RESULT_REF
    with h.store.transaction() as tx:
        observation = tx.get_observation(analysis_id)
    assert observation is not None
    evidence = observation.evidence
    assert evidence.result_sha256 == record.result_sha256
    assert evidence.evidence_kind is EvidenceKind.OFFLINE_CONTEXT_ADAPTER
    assert evidence.provider_context_mode is ProviderContextMode.TYPED_CONTEXT
    assert evidence.transport_attempts == 1
    # The nested V2 hash alone is NOT what is retained.
    nested = canonical_json(json.loads(record.canonical_json)["result"])
    assert sha256(nested.encode("utf-8")).hexdigest() != record.result_sha256


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (TimeoutError(), ObservationFailureCode.PROVIDER_TIMEOUT),
        (LightningProviderError("X", "y", False), ObservationFailureCode.PROVIDER_ERROR),
    ],
)
def test_c2_a07_transport_failures_map_once_without_retry(
    error: Exception, code: ObservationFailureCode
) -> None:
    h, transport, _ = _harness()

    def boom(_response: dict[str, object]) -> dict[str, object]:
        raise error

    transport.tamper = boom
    outcome = h.provider.observe(_typed_request(h))
    assert isinstance(outcome, ObservationFailed) and outcome.code is code
    assert outcome.provider_invoked and len(transport.posted) == 1


def test_c2_a10_unsafe_nested_text_is_blocked_by_the_reused_policy() -> None:
    h, transport, _ = _harness()
    transport.tamper = _set(("result", "entities", 0, "label", "value"),
                            "synthetic psychological inference marker")
    outcome = h.provider.observe(_typed_request(h))
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.UNSAFE_CONTENT
    assert h.observe().code == "UNSAFE_CONTENT" and _stored(h) == (0, 0, 0)


def test_c2_typed_handoff_harness_builds() -> None:
    assert build_context_harness().observe().authoritative
