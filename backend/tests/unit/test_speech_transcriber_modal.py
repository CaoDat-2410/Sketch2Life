"""The Modal speech adapter: verified audio in, bounded result out, nothing logged or retried."""

from __future__ import annotations

import hashlib
import io
from contextlib import contextmanager
from typing import Any

import pytest

from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.parent_story_inputs import (
    SpeechTranscriptionFailure,
    SpeechTranscriptionRequest,
)
from sketch2life.infrastructure.ai import speech_transcriber_modal as adapter

AUDIO = b"\x00\x00\x00\x18ftypM4A synthetic"


class _Storage:
    def get_object(self, key: str) -> StoredObject:
        return StoredObject(io.BytesIO(AUDIO), len(AUDIO), "audio/mp4", {})


class _Volume:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.removed: list[str] = []

    @contextmanager
    def batch_upload(self) -> Any:
        volume = self

        class _Batch:
            def put_file(self, body: io.BytesIO, path: str) -> None:
                volume.files[path] = body.read()

        yield _Batch()

    def remove_file(self, path: str, recursive: bool = False) -> None:
        self.removed.append(path)


class _Function:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.payloads: list[dict[str, Any]] = []

    def spawn(self, payload: dict[str, Any]) -> Any:
        self.payloads.append(payload)
        fail = self.fail

        class _Call:
            def get(self, timeout: int) -> dict[str, Any]:
                if fail:
                    raise RuntimeError("synthetic provider failure")
                return {
                    "workload": adapter.WORKLOAD,
                    "job_id": payload["job_id"],
                    "attempt_id": payload["attempt_id"],
                    "model": {"id": adapter.MODEL_ID, "revision": adapter.MODEL_REVISION},
                    "result": {
                        "language": "vi",
                        "text": "con bướm",
                        "segments": [{"start_seconds": 0.0, "end_seconds": 1.5, "text": "x"}],
                    },
                }

        return _Call()


def _request(**changes: Any) -> SpeechTranscriptionRequest:
    values: dict[str, Any] = {
        "run_id": "run",
        "transcript_revision_id": "rev",
        "audio_asset_ref": "parent/run/audio",
        "audio_sha256": hashlib.sha256(AUDIO).hexdigest(),
        "media_type": "audio/mp4",
        "duration_ms": 1_500,
    }
    return SpeechTranscriptionRequest(**{**values, **changes})


def test_the_mobile_m4a_is_staged_transcribed_and_removed() -> None:
    volume, function = _Volume(), _Function()

    result = adapter.ModalSpeechTranscriber(
        _Storage(), volume=volume, function=function
    ).transcribe(_request())

    assert (result.text, result.language) == ("con bướm", "vi")
    assert result.segment_timing == ({"start_ms": 0, "end_ms": 1500},)
    assert any(path.endswith("input/audio.m4a") for path in volume.files)
    assert len(function.payloads) == 1 and len(volume.removed) == 1


@pytest.mark.parametrize(
    "changes",
    [{"audio_sha256": "0" * 64}, {"media_type": "audio/webm"}, {"duration_ms": 120_001}],
)
def test_unverified_unsupported_or_long_audio_never_reaches_the_provider(
    changes: dict[str, Any],
) -> None:
    function = _Function()

    with pytest.raises(SpeechTranscriptionFailure):
        adapter.ModalSpeechTranscriber(_Storage(), volume=_Volume(), function=function).transcribe(
            _request(**changes)
        )

    assert function.payloads == []


def test_a_provider_failure_is_recoverable_cleaned_up_and_not_retried() -> None:
    volume, function = _Volume(), _Function(fail=True)

    with pytest.raises(SpeechTranscriptionFailure):
        adapter.ModalSpeechTranscriber(_Storage(), volume=volume, function=function).transcribe(
            _request()
        )

    assert len(function.payloads) == 1 and len(volume.removed) == 1
