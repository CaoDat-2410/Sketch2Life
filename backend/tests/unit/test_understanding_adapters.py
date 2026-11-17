from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1
from sketch2life.contracts.schemas.understanding import (
    AsrQualityV1,
    AsrRequestV1,
    AsrResultV1,
    AsrSegmentV1,
    ModelProvenanceV1,
    VisionCandidateV1,
    VisionRequestV1,
    VisionUnderstandingResultV1,
)
from sketch2life.infrastructure.understanding.fixture_adapters import (
    FixtureAsrAdapter,
    FixtureVisionAdapter,
)
from sketch2life.infrastructure.understanding.qwen3_vl_adapter import Qwen3VLStructuredAdapter
from sketch2life.infrastructure.understanding.whisper_adapter import (
    WhisperAsrAdapter,
    WhisperEngineResult,
    WhisperSegment,
)

PROVENANCE = ModelProvenanceV1(
    provider="fixture",
    model="fixture-v1",
    adapter_version="1.0",
    config_version="config-v1",
)
SOURCE_AUDIO = SourceMediaReferenceV1(
    artifact_ref="fixture:audio:1",
    sha256="a" * 64,
)
SOURCE_IMAGE = SourceMediaReferenceV1(
    artifact_ref="fixture:image:1",
    sha256="b" * 64,
)


def test_fixture_asr_preserves_source_and_round_trips_contract() -> None:
    result = AsrResultV1(
        status="SUCCEEDED",
        source_audio=SOURCE_AUDIO,
        transcript="xin chao",
        language="vi",
        language_confidence=0.99,
        segments=(AsrSegmentV1(start_seconds=0, end_seconds=1, text="xin chao"),),
        quality=AsrQualityV1(segment_count=1),
        provenance=PROVENANCE,
    )
    request = AsrRequestV1(source_audio=SOURCE_AUDIO, media_validation="PASS")

    mapped = FixtureAsrAdapter({SOURCE_AUDIO.artifact_ref: result}).transcribe(request)

    assert mapped.status == "SUCCEEDED"
    assert mapped.source_audio == SOURCE_AUDIO
    assert AsrResultV1.model_validate(mapped.model_dump()) == mapped


def test_whisper_timeout_is_typed_and_contains_no_provider_payload() -> None:
    class TimeoutEngine:
        def transcribe(self, _source: object) -> object:
            raise TimeoutError

    request = AsrRequestV1(source_audio=SOURCE_AUDIO, media_validation="PASS")
    result = WhisperAsrAdapter(TimeoutEngine(), PROVENANCE).transcribe(request)

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "TIMEOUT"
    assert result.source_audio == SOURCE_AUDIO


def test_whisper_maps_typed_engine_output() -> None:
    class Engine:
        def transcribe(self, _source: object) -> object:
            return WhisperEngineResult(
                transcript="hello",
                language="en",
                language_confidence=0.95,
                segments=(WhisperSegment(0, 1.2, "hello", 0.9),),
                no_speech_probability=0.02,
            )

    request = AsrRequestV1(source_audio=SOURCE_AUDIO, media_validation="PASS")
    result = WhisperAsrAdapter(Engine(), PROVENANCE).transcribe(request)

    assert result.status == "SUCCEEDED"
    assert result.transcript == "hello"
    assert result.segments[0].end_seconds == 1.2
    assert result.quality is not None and result.quality.segment_count == 1


def test_fixture_vision_preserves_source() -> None:
    result = VisionUnderstandingResultV1(
        status="SUCCEEDED",
        source_image=SOURCE_IMAGE,
        entities=(VisionCandidateV1(label="tree", confidence=0.8),),
        uncertainty=0.2,
        provenance=PROVENANCE,
    )
    request = VisionRequestV1(source_image=SOURCE_IMAGE, media_validation="PASS")

    mapped = FixtureVisionAdapter({SOURCE_IMAGE.artifact_ref: result}).understand(request)

    assert mapped.entities[0].label == "tree"
    assert mapped.source_image.sha256 == "b" * 64


def test_qwen_rejects_free_text_and_prohibited_fields() -> None:
    @dataclass
    class Client:
        payload: object

        def understand(self, _source: object, _schema: str) -> object:
            return self.payload

    request = VisionRequestV1(source_image=SOURCE_IMAGE, media_validation="PASS")

    free_text = Qwen3VLStructuredAdapter(Client("a free-form answer"), PROVENANCE).understand(
        request
    )
    prohibited = Qwen3VLStructuredAdapter(
        Client({"uncertainty": 0.1, "personality": "not allowed"}), PROVENANCE
    ).understand(request)

    assert free_text.failure is not None and free_text.failure.code == "MALFORMED_OUTPUT"
    assert prohibited.failure is not None and prohibited.failure.code == "PROHIBITED_FIELD"


def test_qwen_maps_structured_payload_and_rejects_unknown_fields() -> None:
    @dataclass
    class Client:
        payload: object

        def understand(self, _source: object, _schema: str) -> object:
            return self.payload

    request = VisionRequestV1(source_image=SOURCE_IMAGE, media_validation="PASS")
    valid = {"uncertainty": 0.1, "entities": [{"label": "sun", "confidence": 0.9}]}
    invalid = {"uncertainty": 0.1, "unsupported": True}

    result = Qwen3VLStructuredAdapter(Client(valid), PROVENANCE).understand(request)
    rejected = Qwen3VLStructuredAdapter(Client(invalid), PROVENANCE).understand(request)

    assert result.status == "SUCCEEDED"
    assert result.entities[0].label == "sun"
    assert rejected.failure is not None and rejected.failure.code == "MALFORMED_OUTPUT"


def test_understanding_requests_reject_unavailable_source_references() -> None:
    unavailable = SourceMediaReferenceV1(
        artifact_ref="fixture:missing",
        source_status="MISSING",
    )

    with pytest.raises(ValidationError):
        AsrRequestV1(source_audio=unavailable, media_validation="PASS")
    with pytest.raises(ValidationError):
        VisionRequestV1(source_image=unavailable, media_validation="PASS")
