"""BE2-02 C1 offline bridge over the existing Vision V2 adapter (V13, V14, V04 via bridge).

Every transport here is an in-memory fake: no network, provider, model or weights.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest

from sketch2life.application.ports.vision_analysis import (
    ObservationFailed,
    ObservationFailureCode,
    ObservationRequest,
    ObservationSucceeded,
)
from sketch2life.application.services.vision_analysis import (
    MeaningState,
    ObservationDisposition,
)
from sketch2life.contracts.schemas.analysis_results import AnalysisRecordV1
from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    VisionImageReferenceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.vision_analysis import ProviderContextMode
from sketch2life.domain.vision_context import FIXTURE_AGE_BAND_POLICY, pin_context
from sketch2life.infrastructure.ai.lightning_client import (
    LightningProviderError,
    UrllibJsonTransport,
)
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.ai.vision_lexical_policy import synthetic_prohibited_lexicon
from sketch2life.infrastructure.vision_analysis.harness import (
    DEVICE_A,
    ORG,
    RENDER_SHA256,
    TEACHER,
    AnalysisHarness,
    build_analysis_harness,
    synthetic_admission,
)
from sketch2life.infrastructure.vision_analysis.legacy_v2 import (
    LegacyVisionV2Bridge,
    LiveTransportForbidden,
)

PROFILE = vision_profile_catalog_v2().resolve(VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1)


def _label(value: str) -> dict[str, Any]:
    return {"value": value, "language": {"status": "DECLARED", "tags": ["en"]}}


def v2_success(*, first_entity: dict[str, Any] | None = None,
               **changes: Any) -> dict[str, Any]:
    catalog = vision_profile_catalog_v2()
    body = VisionUnderstandingSuccessV2(
        correlation_id="corr_fx_1",
        executed_at=datetime(2026, 10, 16, 12, 0, 5, tzinfo=UTC),
        source_image_ref=VisionImageReferenceV1(artifact_ref="render_fx_004",
                                                sha256=RENDER_SHA256),
        profile_id=PROFILE.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        attempt_number=1,
        repair_attempted=False,
        content_policy_version=synthetic_prohibited_lexicon().lexicon_version,
        policy_match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
        policy_execution_state="PASSED",
        entities=(),
        actions=(),
        relations=(),
        themes=(),
        ambiguous_regions=(),
        adapter_version=PROFILE.adapter_version,
        config_hash=vision_profile_config_hash_v2(PROFILE),
        model_provenance=PROFILE.model_provenance,
    ).model_dump(mode="json")
    body["entities"] = [
        first_entity or {"observation_id": "ent-1", "label": _label("cat"), "confidence": 0.71},
        {"observation_id": "ent-2", "label": _label("ball"), "confidence": None},
    ]
    body["actions"] = [{"observation_id": "act-1", "label": _label("sitting"),
                        "actor_ref": "ent-1", "object_ref": None, "confidence": 0.4}]
    body["relations"] = [{"observation_id": "rel-1", "predicate": _label("next to"),
                          "subject_ref": "ent-1", "object_ref": "ent-2", "confidence": None}]
    body["themes"] = [{"observation_id": "thm-1", "label": _label("play"),
                       "evidence_refs": ["ent-1"], "confidence": 0.3}]
    body["ambiguous_regions"] = [{"observation_id": "amb-1", "note": _label("striped area")}]
    body.update(changes)
    return body


class FakeTransport:
    def __init__(self, response: Mapping[str, object] | None = None) -> None:
        self.response = response
        self.calls: list[tuple[str, Mapping[str, object]]] = []
        self.raise_error: BaseException | None = None

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls.append((path, payload))
        if self.raise_error is not None:
            raise self.raise_error
        assert self.response is not None
        return self.response


def _harness(transport: FakeTransport,
             loader: Callable[[str], bytes] | None = None) -> AnalysisHarness:
    return build_analysis_harness(
        provider_factory=lambda sources, clock: LegacyVisionV2Bridge(
            transport=transport, render_loader=loader or sources.read_render, clock=clock.now
        )
    )


def _stored(h: AnalysisHarness) -> int:
    return len(h.store.snapshot().heads)


def test_v13_valid_result_maps_whole_original_with_image_only_provenance() -> None:
    transport = FakeTransport(v2_success())
    h = _harness(transport)
    result = h.observe()
    assert result.disposition is ObservationDisposition.ACCEPTED
    assert len(transport.calls) == 1
    path, payload = transport.calls[0]
    assert path == "/v2/vision"
    assert set(payload) == {"contract_name", "contract_version", "request", "source_image"}
    request = payload["request"]
    assert isinstance(request, dict)
    # Legacy media_validation is filled from the trusted admission receipt bound to the render.
    assert request["media_validation"]["validation_artifact_ref"] == h.receipt.receipt_id
    assert request["processing_image_ref"] is None
    record = AnalysisRecordV1.model_validate_json(
        json.dumps(h.service.analysis_record(TEACHER, result.analysis_id or ""))
    )
    provenance = record.candidate.provenance
    assert provenance.evidence_kind == "offline_legacy_bridge"
    assert provenance.provider_context_mode == "image_only"
    assert provenance.transport_attempts == 1
    assert provenance.model_revision == PROFILE.model_provenance.model_revision
    assert provenance.config_hash == vision_profile_config_hash_v2(PROFILE)
    original = record.original_observation
    assert [len(original.entities), len(original.actions), len(original.relations),
            len(original.themes), len(original.ambiguous_regions)] == [2, 1, 1, 1, 1]
    assert [(c.label, c.confidence) for c in record.candidate.object_candidates] == [
        ("cat", 0.71), ("ball", None)]
    assert record.candidate.uncertainty.unknown_confidence_refs == ("ent-2", "rel-1")
    assert record.candidate.uncertainty.ambiguous_region_refs == ("amb-1",)
    assert record.candidate.moderation_outcome.comprehensive_moderation == "not_run"


def test_v13_v04_wrong_label_is_corrected_without_touching_the_bridge_observation() -> None:
    transport = FakeTransport(v2_success())
    h = _harness(transport)
    analysis_id = h.accepted_analysis()
    proposal = h.service.submit_correction(
        h.correction(DEVICE_A, analysis_id, explanation="It is my tiger")
    )
    h.service.submit_correction(h.correction(TEACHER, analysis_id, revision=2,
                                             basis=proposal.correction.correction_id))
    meaning = h.service.downstream_meaning(TEACHER, analysis_id)
    assert meaning.state is MeaningState.CONFIRMED and meaning.confirmed_concepts == ("tiger",)
    assert meaning.model_candidates[0].label == "cat"
    # Child text never reached the provider: one call, made before any correction existed.
    assert len(transport.calls) == 1
    assert "tiger" not in json.dumps(transport.calls[0][1])


@pytest.mark.parametrize(
    ("response", "detail"),
    [
        (v2_success(correlation_id="corr_other"), "OUTPUT_MAPPING_FAILED"),
        (v2_success(source_image_ref={"artifact_ref": "render_fx_004", "sha256": "0" * 64}),
         "OUTPUT_MAPPING_FAILED"),
        (v2_success(profile_catalog_hash="1" * 64), "CATALOG_HASH_MISMATCH"),
        (v2_success(config_hash="2" * 64), "CONFIG_HASH_MISMATCH"),
        (v2_success(adapter_version="other-adapter"), "ADAPTER_VERSION_MISMATCH"),
        (v2_success(model_provenance={**PROFILE.model_provenance.model_dump(mode="json"),
                                      "model_revision": "3" * 40}),
         "MODEL_PROVENANCE_MISMATCH"),
        (v2_success(content_policy_version="other-lexicon"), "POLICY_VERSION_MISMATCH"),
        (v2_success(first_entity={"observation_id": "ent-1", "label": _label("cat"),
                               "confidence": "0.5"}), "CONFIDENCE_NOT_STRICT"),
        (v2_success(first_entity={"observation_id": "ent-1", "label": _label("cat"),
                               "confidence": True}), "CONFIDENCE_NOT_STRICT"),
        (v2_success(first_entity={"observation_id": "ent-1", "label": _label("c" * 200),
                               "confidence": 0.5}), "LABEL_NOT_SHORT_TEXT"),
        ({"status": "SUCCEEDED", "unexpected": True}, "OUTPUT_MAPPING_FAILED"),
    ],
)
def test_v13_identity_provenance_or_shape_mismatch_fails_safely(
    response: dict[str, Any], detail: str
) -> None:
    transport = FakeTransport(response)
    h = _harness(transport)
    outcome = h.provider.observe(_request(h))
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.OUTPUT_MALFORMED
    assert outcome.detail == detail and outcome.provider_invoked
    assert len(transport.calls) == 1
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED and _stored(h) == 0


@pytest.mark.parametrize(
    ("error", "code", "retryable"),
    [
        (TimeoutError(), ObservationFailureCode.PROVIDER_TIMEOUT, False),
        (LightningProviderError("X", "sanitized", False), ObservationFailureCode.PROVIDER_ERROR,
         False),
        (ConnectionResetError(), ObservationFailureCode.PROVIDER_ERROR, False),
    ],
)
def test_v13_runtime_failures_are_typed_and_never_retried(
    error: BaseException, code: ObservationFailureCode, retryable: bool
) -> None:
    transport = FakeTransport()
    transport.raise_error = error
    h = _harness(transport)
    outcome = h.provider.observe(_request(h))
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is code and outcome.retryable is retryable
    assert len(transport.calls) == 1


def test_v13_legacy_adapter_transient_branch_defect_is_contained() -> None:
    """Finding F-01: the unchanged V2 adapter builds an invalid failure for an OSError; the
    bridge contains the ValidationError as a typed, non-retried provider error."""

    transport = FakeTransport()
    transport.raise_error = ConnectionResetError()
    h = _harness(transport)
    outcome = h.provider.observe(_request(h))
    assert isinstance(outcome, ObservationFailed)
    assert outcome.detail == "LEGACY_ADAPTER_CONTRACT_ERROR" and outcome.provider_invoked
    result = h.observe()
    assert result.code == "PROVIDER_ERROR" and _stored(h) == 0


def test_v13_prohibited_output_is_unsafe_and_nothing_is_stored() -> None:
    unsafe = v2_success(first_entity={"observation_id": "ent-1",
                                   "label": _label("synthetic psychological inference marker"),
                                   "confidence": 0.9})
    transport = FakeTransport(unsafe)
    h = _harness(transport)
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED
    assert result.code == "UNSAFE_CONTENT" and result.analysis_id is None
    assert _stored(h) == 0 and len(transport.calls) == 1


def _request(h: AnalysisHarness, **changes: Any) -> ObservationRequest:
    base = ObservationRequest(
        correlation_id="corr_fx_1",
        organization_id=ORG,
        render=h.snapshot.render,
        admission=h.receipt,
        context_mode=ProviderContextMode.IMAGE_ONLY,
    )
    return replace(base, **changes)


def test_v14_typed_context_is_refused_before_any_call() -> None:
    transport = FakeTransport(v2_success())
    h = _harness(transport)
    assert h.provider.supported_context_modes == frozenset({ProviderContextMode.IMAGE_ONLY})
    # C2 superseded the C1 fake-only ObservationContext with the pinned ProviderTypedContext;
    # the refusal (no call, no fallback) asserted below is unchanged.
    snapshot = h.context_sources.resolve(h.pin, h.snapshot)
    assert snapshot is not None
    typed = _request(h, context_mode=ProviderContextMode.TYPED_CONTEXT,
                     typed_context=pin_context(snapshot, FIXTURE_AGE_BAND_POLICY))
    outcome = h.provider.observe(typed)
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.CONTEXT_MODE_UNSUPPORTED
    assert not outcome.provider_invoked and transport.calls == []
    required = build_analysis_harness(
        provider_factory=lambda sources, clock: LegacyVisionV2Bridge(
            transport=transport, render_loader=sources.read_render, clock=clock.now),
        required_context_mode=ProviderContextMode.TYPED_CONTEXT,
    )
    assert required.observe().code == "CONTEXT_MODE_UNSUPPORTED" and transport.calls == []


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"processing_image_ref": "render_fx_004_crop"},
         ObservationFailureCode.DERIVED_INPUT_UNSUPPORTED),
        ({"admission": "other_render"}, ObservationFailureCode.ADMISSION_NOT_BOUND),
        ({"admission": "recapture"}, ObservationFailureCode.ADMISSION_NOT_BOUND),
        ({"render": "gif"}, ObservationFailureCode.MEDIA_TYPE_UNSUPPORTED),
    ],
)
def test_v14_source_only_and_bound_admission_are_required(
    changes: dict[str, str], code: ObservationFailureCode
) -> None:
    transport = FakeTransport(v2_success())
    h = _harness(transport)
    resolved: dict[str, Any] = dict(changes)
    if changes.get("admission") == "other_render":
        resolved["admission"] = replace(h.receipt, render_sha256="4" * 64)
    elif changes.get("admission") == "recapture":
        resolved["admission"] = synthetic_admission(h.snapshot, decision="RECAPTURE")
    if changes.get("render") == "gif":
        resolved["render"] = replace(h.snapshot.render, media_type="image/gif")
    outcome = h.provider.observe(_request(h, **resolved))
    assert isinstance(outcome, ObservationFailed) and outcome.code is code
    assert not outcome.provider_invoked and transport.calls == []


def test_v14_render_bytes_must_match_the_bound_hash_before_any_call() -> None:
    transport = FakeTransport(v2_success())
    h = _harness(transport, loader=lambda _ref: b"\x89PNG\r\n\x1a\ndifferent synthetic bytes")
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED
    assert result.code == "SOURCE_REJECTED" and not result.provider_invoked
    assert transport.calls == [] and _stored(h) == 0
    def unreadable(ref: str) -> bytes:
        raise KeyError(ref)

    missing = _harness(FakeTransport(v2_success()), loader=unreadable)
    assert missing.observe().code == "SOURCE_REJECTED"


def test_v14_bridge_never_uses_the_adult_narration_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("narration_context must not carry child or context data")

    monkeypatch.setattr(LightningVisionV2Adapter, "understand_with_narration", forbidden)
    transport = FakeTransport(v2_success())
    h = _harness(transport)
    outcome = h.provider.observe(_request(h))
    assert isinstance(outcome, ObservationSucceeded)
    assert "narration_context" not in transport.calls[0][1]


def test_v14_real_network_transport_is_refused_under_c1() -> None:
    live = UrllibJsonTransport(base_url="http://localhost:9", token="")
    with pytest.raises(LiveTransportForbidden):
        LegacyVisionV2Bridge(transport=live, render_loader=lambda _ref: b"")
