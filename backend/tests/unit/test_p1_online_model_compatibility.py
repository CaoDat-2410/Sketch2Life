"""Offline compatibility tests for online-shaped ASR/VLM output entering P1.

The fake clients return payloads shaped like the approved Lightning profiles.  No
network, model weights, credentials or real media are used; the tests exercise the
same provider-neutral adapters and P1 Gate A/Gate B boundary used by a live run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.contracts.schemas.p1_experience import (
    ActivityTemplateV1,
    AnchorProvenanceV1,
    P1ContextV1,
    SemanticAnchorSetV1,
    SemanticAnchorV1,
    VersionedRefV1,
)
from sketch2life.contracts.schemas.understanding import (
    AsrRequestV1,
    AsrResultV1,
    ModelProvenanceV1,
    VisionRequestV1,
    VisionUnderstandingResultV1,
)
from sketch2life.infrastructure.understanding.qwen3_vl_adapter import (
    Qwen3VLStructuredAdapter,
)
from sketch2life.infrastructure.understanding.whisper_adapter import (
    WhisperAsrAdapter,
    WhisperEngineResult,
    WhisperSegment,
)

SOURCE_AUDIO = {
    "artifact_ref": "fixture:audio:online-compat-v1",
    "sha256": "a" * 64,
}
SOURCE_IMAGE = {
    "artifact_ref": "fixture:image:online-compat-v1",
    "sha256": "b" * 64,
}
VLM_PROVENANCE = ModelProvenanceV1(
    provider="lightning",
    model="Qwen/Qwen3-VL-8B-Instruct",
    adapter_version="1.0",
    config_version="live-lightning-v1",
)
ASR_PROVENANCE = ModelProvenanceV1(
    provider="lightning",
    model="large-v3-turbo",
    adapter_version="1.0",
    config_version="live-lightning-v1",
)


@dataclass
class StructuredClient:
    payload: object
    calls: list[tuple[object, str]] = field(default_factory=list)

    def understand(self, source_image: object, response_schema_version: str) -> object:
        self.calls.append((source_image, response_schema_version))
        return self.payload


@dataclass
class FlakyStructuredClient:
    responses: list[object]
    calls: int = 0

    def understand(self, _source_image: object, _response_schema_version: str) -> object:
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@dataclass
class WhisperClient:
    response: object
    calls: int = 0

    def transcribe(self, _source_audio: object) -> object:
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _vision_request() -> VisionRequestV1:
    from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1

    return VisionRequestV1(
        source_image=SourceMediaReferenceV1.model_validate(SOURCE_IMAGE),
        media_validation="PASS",
    )


def _asr_request() -> AsrRequestV1:
    from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1

    return AsrRequestV1(
        source_audio=SourceMediaReferenceV1.model_validate(SOURCE_AUDIO),
        media_validation="PASS",
    )


def _valid_vlm_payload() -> dict[str, Any]:
    return {
        "entities": [{"label": "butterfly", "confidence": 0.94}],
        "actions": [{"label": "fly", "confidence": 0.81}],
        "relations": [
            {
                "subject": "butterfly",
                "predicate": "has",
                "object": "wings",
                "confidence": 0.87,
            }
        ],
        "themes": [{"label": "nature", "confidence": 0.72}],
        "ambiguous_regions": [],
        "uncertainty": 0.06,
    }


def _butterfly_template() -> ActivityTemplateV1:
    return ActivityTemplateV1(
        template_id="TPL-COMPAT-BUTTERFLY-FOLD-PRINT-V1",
        template_version=1,
        activity_ref=VersionedRefV1(id="ACT-COMPAT-BUTTERFLY-FOLD-PRINT", version=1),
        objective_refs=(VersionedRefV1(id="OBJ_SENSORIAL_DISCRIMINATION", version=1),),
        supported_anchor_labels=("butterfly", "wings", "symmetry"),
        supported_anchor_kinds=("subject", "visual_feature"),
        interaction_mode="SORTING",
        age_months_min=36,
        age_months_max=71,
        material_option_ids=("MAT-COMPAT-PAPER",),
        minimum_supervision="NEARBY",
        safety_rule_ids=("COMPAT_NO_SMALL_PARTS",),
        steps_vi=(
            "Gấp giấy theo đường giữa.",
            "Chấm màu ở một bên cánh.",
            "Mở giấy và quan sát hai cánh đối xứng.",
        ),
        provenance_source="tests/fixtures/p1-online-model-compatibility/butterfly.json",
        provenance_sha256="c" * 64,
        review_status="PROVISIONAL_OWNER_REVIEWED",
    )


def _context(template: ActivityTemplateV1) -> P1ContextV1:
    return P1ContextV1(
        session_id="session-online-compat-001",
        expected_session_version=1,
        age_months=48,
        readiness_ids=template.readiness_ids,
        completed_activity_ids=template.prerequisite_activity_ids,
        available_material_option_ids=(template.material_option_ids[0],),
        supervision_level="NEARBY",
        policy_flags=("CAREGIVER_PRESENT",),
        candidate_status="ACTIVE_FIXTURE",
        gate_a_confirmed=True,
    )


def _anchor_set_from_vlm(
    result: VisionUnderstandingResultV1,
    *,
    adult_confirmed: bool = True,
    semantic_tags: tuple[str, ...] = ("wings", "symmetry"),
) -> SemanticAnchorSetV1:
    candidate = result.entities[0]
    return SemanticAnchorSetV1(
        anchor_set_id="anchors-online-compat-001",
        source_artifact_id=result.source_image.artifact_ref,
        source_artifact_sha256=result.source_image.sha256,
        gate_a_status="CONFIRMED",
        adult_confirmation_actor="CAREGIVER",
        primary_anchor=SemanticAnchorV1(
            anchor_id="anchor-online-butterfly",
            kind="subject",
            original_label=candidate.label,
            normalized_label=candidate.label.casefold(),
            semantic_tags=semantic_tags,
            confidence=candidate.confidence,
            adult_confirmed=adult_confirmed,
            provenance=AnchorProvenanceV1(
                source_artifact_id=result.source_image.artifact_ref,
                source_artifact_sha256=result.source_image.sha256,
                source_contract_name=result.contract_name,
                source_contract_version=result.contract_version,
                source_claim_ids=("vision-entity-0",),
            ),
        ),
    )


def test_online_shaped_qwen_output_maps_and_round_trips() -> None:
    client = StructuredClient(_valid_vlm_payload())
    request = _vision_request()

    result = Qwen3VLStructuredAdapter(client, VLM_PROVENANCE).understand(request)

    assert result.status == "SUCCEEDED"
    assert result.source_image == request.source_image
    assert result.provenance == VLM_PROVENANCE
    assert result.entities[0].label == "butterfly"
    assert result.relations[0].object == "wings"
    assert client.calls[0][1] == "VisionUnderstandingResultV1"
    assert TypeAdapter(VisionUnderstandingResultV1).validate_python(result.model_dump()) == result


def test_online_qwen_payload_cannot_override_source_or_contract_identity() -> None:
    payload = _valid_vlm_payload()
    payload["source_image"] = {"artifact_ref": "other", "sha256": "d" * 64}
    client = StructuredClient(payload)

    result = Qwen3VLStructuredAdapter(client, VLM_PROVENANCE).understand(_vision_request())

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "MALFORMED_OUTPUT"
    assert result.source_image.sha256 == "b" * 64


@pytest.mark.parametrize(
    "payload",
    [
        {"uncertainty": 0.1, "entities": [{"label": "butterfly", "confidence": 1.1}]},
        {"uncertainty": -0.1},
        {"uncertainty": 0.1, "entities": [{"label": "butterfly", "confidence": 0.9, "bbox": []}]},
        {
            "uncertainty": 0.1,
            "ambiguous_regions": [
                {
                    "label": "x",
                    "description": "shape",
                    "confidence": 0.2,
                    "mental_state": "blocked",
                }
            ],
        },
        "free-form model answer",
        None,
    ],
)
def test_malformed_or_unsafe_online_qwen_output_fails_closed(payload: object) -> None:
    result = Qwen3VLStructuredAdapter(StructuredClient(payload), VLM_PROVENANCE).understand(
        _vision_request()
    )

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code in {"MALFORMED_OUTPUT", "PROHIBITED_FIELD"}
    assert "free-form model answer" not in result.failure.message


def test_online_qwen_transient_exception_retries_once_then_succeeds() -> None:
    client = FlakyStructuredClient([RuntimeError("provider stack"), _valid_vlm_payload()])

    result = Qwen3VLStructuredAdapter(client, VLM_PROVENANCE).understand(_vision_request())

    assert result.status == "SUCCEEDED"
    assert client.calls == 2


def test_online_qwen_permanent_exception_is_typed_and_bounded() -> None:
    client = FlakyStructuredClient([RuntimeError("private provider details")] * 2)

    result = Qwen3VLStructuredAdapter(client, VLM_PROVENANCE).understand(_vision_request())

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "PROVIDER_ERROR"
    assert result.failure.retryable is True
    assert result.failure.message == "Vision provider request failed"
    assert client.calls == 2


def test_online_shaped_whisper_output_maps_and_round_trips() -> None:
    engine = WhisperClient(
        WhisperEngineResult(
            transcript="Con bướm bay",
            language="vi",
            language_confidence=0.96,
            segments=(WhisperSegment(0, 1.2, "Con bướm bay", 0.91),),
            no_speech_probability=0.02,
        )
    )

    result = WhisperAsrAdapter(engine, ASR_PROVENANCE).transcribe(_asr_request())

    assert result.status == "SUCCEEDED"
    assert result.source_audio == _asr_request().source_audio
    assert result.provenance == ASR_PROVENANCE
    assert result.quality is not None and result.quality.segment_count == 1
    assert result.segments[0].text == "Con bướm bay"
    assert AsrResultV1.model_validate(result.model_dump()) == result


@pytest.mark.parametrize(
    "engine_result",
    [
        object(),
        WhisperEngineResult(
            transcript="bad interval",
            language="vi",
            language_confidence=0.7,
            segments=(WhisperSegment(2, 1, "bad", 0.5),),
        ),
        WhisperEngineResult(
            transcript="bad confidence",
            language="vi",
            language_confidence=1.2,
            segments=(),
        ),
    ],
)
def test_malformed_online_whisper_output_fails_closed(engine_result: object) -> None:
    result = WhisperAsrAdapter(WhisperClient(engine_result), ASR_PROVENANCE).transcribe(
        _asr_request()
    )

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "MALFORMED_OUTPUT"
    assert result.source_audio.artifact_ref == SOURCE_AUDIO["artifact_ref"]


def test_online_whisper_transient_exception_retries_once_then_succeeds() -> None:
    valid = WhisperEngineResult(
        transcript="butterfly",
        language="en",
        language_confidence=0.9,
        segments=(),
    )

    class OneFailureEngine:
        calls = 0

        def transcribe(self, _source: object) -> object:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("transient")
            return valid

    retrying = OneFailureEngine()
    result = WhisperAsrAdapter(retrying, ASR_PROVENANCE).transcribe(_asr_request())

    assert result.status == "SUCCEEDED"
    assert retrying.calls == 2


def test_online_model_candidate_requires_adult_confirmation_before_p1() -> None:
    result = Qwen3VLStructuredAdapter(
        StructuredClient(_valid_vlm_payload()), VLM_PROVENANCE
    ).understand(_vision_request())

    with pytest.raises(ValidationError, match="adult-confirmed"):
        _anchor_set_from_vlm(result, adult_confirmed=False)


def test_online_model_entity_compiles_through_existing_p1_gate_b() -> None:
    result = Qwen3VLStructuredAdapter(
        StructuredClient(_valid_vlm_payload()), VLM_PROVENANCE
    ).understand(_vision_request())
    anchor_set = _anchor_set_from_vlm(result)
    assert SemanticAnchorSetV1.model_validate(anchor_set.model_dump()) == anchor_set
    template = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (template,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )

    compilation = compiler.compile(
        anchor_set,
        _context(template),
        preferred_template_id=template.template_id,
    )

    assert compilation.filter_result.status == "VALID_CANDIDATE"
    assert compilation.spec is not None
    assert compilation.gate_b.status == "APPROVED"
    assert compilation.handoff is not None
    assert (
        compilation.spec.anchor_set.primary_anchor.provenance.source_contract_name
        == "VisionUnderstandingResultV1"
    )
    assert compilation.handoff.spec_ref.id == compilation.spec.spec_id


def test_online_model_unrelated_entity_is_rejected_by_p1_catalog() -> None:
    payload = _valid_vlm_payload()
    payload["entities"] = [{"label": "spaceship", "confidence": 0.94}]
    result = Qwen3VLStructuredAdapter(StructuredClient(payload), VLM_PROVENANCE).understand(
        _vision_request()
    )
    anchor_set = _anchor_set_from_vlm(result, semantic_tags=())
    template = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (template,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )

    compilation = compiler.compile(
        anchor_set,
        _context(template),
        preferred_template_id=template.template_id,
    )

    assert compilation.filter_result.status == "NO_ELIGIBLE_ACTIVITY"
    assert "ANCHOR_TEMPLATE_MISMATCH" in compilation.filter_result.reason_codes
    assert compilation.fit_evaluation is not None
    assert compilation.fit_evaluation.status == "REJECT"
    assert compilation.gate_b.status == "BLOCKED"
    assert compilation.spec is None
    assert compilation.handoff is None


def test_online_model_with_no_entity_cannot_enter_p1() -> None:
    payload = _valid_vlm_payload()
    payload["entities"] = []
    result = Qwen3VLStructuredAdapter(StructuredClient(payload), VLM_PROVENANCE).understand(
        _vision_request()
    )

    assert result.status == "SUCCEEDED"
    assert result.entities == ()
    with pytest.raises(IndexError):
        _anchor_set_from_vlm(result)

def test_online_qwen_timeout_is_typed_without_unbounded_retry() -> None:
    client = FlakyStructuredClient([TimeoutError("deadline")])

    result = Qwen3VLStructuredAdapter(client, VLM_PROVENANCE).understand(_vision_request())

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "TIMEOUT"
    assert result.failure.retryable is True
    assert client.calls == 1


def test_online_whisper_timeout_is_typed_without_unbounded_retry() -> None:
    class TimeoutEngine:
        calls = 0

        def transcribe(self, _source: object) -> object:
            self.calls += 1
            raise TimeoutError("deadline")

    engine = TimeoutEngine()
    result = WhisperAsrAdapter(engine, ASR_PROVENANCE).transcribe(_asr_request())

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "TIMEOUT"
    assert result.failure.retryable is True
    assert engine.calls == 1


def test_low_confidence_online_candidate_still_requires_gate_a_confirmation() -> None:
    payload = _valid_vlm_payload()
    payload["entities"] = [{"label": "butterfly", "confidence": 0.01}]
    result = Qwen3VLStructuredAdapter(StructuredClient(payload), VLM_PROVENANCE).understand(
        _vision_request()
    )

    assert result.status == "SUCCEEDED"
    assert result.entities[0].confidence == 0.01
    with pytest.raises(ValidationError, match="adult-confirmed"):
        _anchor_set_from_vlm(result, adult_confirmed=False)
