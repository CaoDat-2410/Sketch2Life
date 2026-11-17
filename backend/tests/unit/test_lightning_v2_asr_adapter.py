from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

import pytest

from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrProfileId,
    AsrRequestV1,
    MediaValidationProvenanceV1,
)
from sketch2life.infrastructure.ai.lightning_client import LightningAsrV2Adapter


class _DisconnectingTransport:
    def __init__(self, error: OSError) -> None:
        self.error = error
        self.calls = 0

    def post_json(self, _path: str, _payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls += 1
        raise self.error


@pytest.mark.parametrize("error", (ConnectionResetError("synthetic reset"),))
def test_asr_connection_reset_is_one_attempt_and_returns_recoverable_typed_failure(
    error: OSError,
) -> None:
    audio = b"synthetic-audio"
    transport = _DisconnectingTransport(error)
    adapter = LightningAsrV2Adapter(
        transport=transport,
        artifact_loader=lambda _ref: audio,
    )
    request = AsrRequestV1(
        correlation_id="synthetic-asr-request",
        source_audio_ref=AsrAudioReferenceV1(
            artifact_ref="synthetic:audio", sha256=sha256(audio).hexdigest()
        ),
        media_validation=MediaValidationProvenanceV1(
            validation_artifact_ref="synthetic:validation",
            validation_artifact_sha256="a" * 64,
            decision="PASS",
            validator_policy_version="test-v1",
        ),
        requested_profile_id=AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1,
    )

    result = adapter.transcribe(request)

    assert result.status == "FAILED"
    assert result.error_code is AsrErrorCode.ASR_PROVIDER_FAILURE
    assert result.error_detail is AsrErrorDetail.TRANSIENT_RUNTIME_FAILURE
    assert result.retryable is True
    assert result.attempt_number == 1
    assert transport.calls == 1
