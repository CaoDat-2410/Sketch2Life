from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1
from sketch2life.contracts.schemas.understanding import (
    AsrRequestV1,
    ModelProvenanceV1,
    VisionRequestV1,
)
from sketch2life.infrastructure.ai.fixture_inputs import FixtureInputs
from sketch2life.infrastructure.ai.lightning_client import (
    LightningAsrAdapter,
    LightningProviderError,
    LightningVisionAdapter,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1"
)
PROVENANCE = ModelProvenanceV1(
    provider="lightning",
    model="live-p2-test",
    adapter_version="1.0",
    config_version="live-lightning-v1",
)


class FakeTransport:
    def __init__(self, responses: list[Mapping[str, object] | Exception]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, Mapping[str, object]]] = []

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls.append((path, payload))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _fixture() -> FixtureInputs:
    return FixtureInputs.load(FIXTURE_ROOT, "integration-fixture-v1")


def test_live_adapters_map_success_and_preserve_hashes() -> None:
    fixture = _fixture()
    transport = FakeTransport(
        [
            {
                "transcript": "Con bướm bay",
                "language": "vi",
                "language_confidence": 0.91,
                "segments": [
                    {
                        "start_seconds": 0,
                        "end_seconds": 1.2,
                        "text": "Con bướm bay",
                        "confidence": 0.9,
                    }
                ],
                "quality": {"segment_count": 1, "no_speech_probability": 0.02},
            },
            {
                "entities": [{"label": "butterfly", "confidence": 0.94}],
                "actions": [{"label": "fly", "confidence": 0.81}],
                "relations": [],
                "themes": [],
                "ambiguous_regions": [],
                "uncertainty": 0.06,
            },
        ]
    )
    asr = LightningAsrAdapter(transport, fixture.read, PROVENANCE)
    vision = LightningVisionAdapter(transport, fixture.read, PROVENANCE)

    asr_result = asr.transcribe(AsrRequestV1(source_audio=fixture.audio, media_validation="PASS"))
    vision_result = vision.understand(
        VisionRequestV1(source_image=fixture.image, media_validation="PASS")
    )

    assert asr_result.status == "SUCCEEDED"
    assert asr_result.source_audio.sha256 == fixture.audio.sha256
    assert vision_result.status == "SUCCEEDED"
    assert vision_result.source_image.sha256 == fixture.image.sha256
    assert transport.calls[0][0] == "/v1/asr"
    assert transport.calls[1][0] == "/v1/vision"
    assert transport.calls[0][1]["source_audio"]["sha256"] == fixture.audio.sha256  # type: ignore[index]


def test_timeout_retries_once_then_returns_success() -> None:
    fixture = _fixture()
    transport = FakeTransport(
        [
            TimeoutError("synthetic timeout"),
            {"transcript": "butterfly", "segments": [], "quality": {"segment_count": 0}},
        ]
    )
    adapter = LightningAsrAdapter(transport, fixture.read, PROVENANCE)
    result = adapter.transcribe(AsrRequestV1(source_audio=fixture.audio, media_validation="PASS"))

    assert result.status == "SUCCEEDED"
    assert len(transport.calls) == 2


def test_rate_limit_is_typed_and_does_not_leak_provider_payload() -> None:
    fixture = _fixture()
    transport = FakeTransport(
        [LightningProviderError("RATE_LIMITED", "Lightning rate limit reached", True)]
    )
    adapter = LightningAsrAdapter(transport, fixture.read, PROVENANCE, max_retries=0)
    result = adapter.transcribe(AsrRequestV1(source_audio=fixture.audio, media_validation="PASS"))

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "RATE_LIMITED"
    assert "provider" not in result.failure.message.lower()


def test_source_hash_mismatch_fails_closed() -> None:
    source = SourceMediaReferenceV1(artifact_ref="x", sha256="0" * 64, source_status="AVAILABLE")
    transport = FakeTransport([{"transcript": "never reached"}])
    adapter = LightningAsrAdapter(transport, lambda _: b"different", PROVENANCE)

    result = adapter.transcribe(AsrRequestV1(source_audio=source, media_validation="PASS"))

    assert result.status == "FAILED"
    assert result.failure is not None
    assert result.failure.code == "MALFORMED_OUTPUT"
    assert transport.calls == []
