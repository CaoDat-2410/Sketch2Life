"""FEAT-093: the narration adapter stages one clause, waits, verifies the WAV and maps failures to codes."""

from __future__ import annotations

import hashlib
import io
import json
from contextlib import contextmanager

import pytest

from sketch2life.application.video_pipeline.ports import VideoPipelineError
from sketch2life.infrastructure.story_video.modal_narration import (
    MANIFEST_SCHEMA,
    WORKER_OUTPUT_SCHEMA,
    ModalNarrationSynthesizer,
)

WAV = b"RIFF" + b"\x00" * 200


class _Batch:
    def __init__(self, files):
        self.files = files

    def put_file(self, stream: io.BytesIO, path: str) -> None:
        self.files[path] = stream.getvalue()


class _Volume:
    def __init__(self, fail=False):
        self.files, self.fail = {}, fail

    @contextmanager
    def batch_upload(self):
        if self.fail:
            raise OSError("boom")
        yield _Batch(self.files)


class _Call:
    def __init__(self, worker_input, *, pending=0, error=None, tamper=None, asset=None):
        self.input, self.pending, self.error, self.tamper, self.asset = worker_input, pending, error, tamper, asset

    def get(self, timeout):
        if self.pending > 0:
            self.pending -= 1
            raise TimeoutError
        if self.error:
            raise self.error
        result = {
            "schema_version": WORKER_OUTPUT_SCHEMA, "job_id": self.input["job_id"], "attempt_id": self.input["attempt_id"],
            "asset": self.asset or {"content_type": "audio/wav", "size_bytes": len(WAV), "bytes": WAV,
                                    "sha256": hashlib.sha256(WAV).hexdigest()},
        }
        result.update(self.tamper or {})
        return result


class _Function:
    def __init__(self, **kwargs):
        self.kwargs, self.inputs = kwargs, []

    def spawn(self, worker_input):
        self.inputs.append(worker_input)
        return _Call(worker_input, **self.kwargs)


def _synth(volume=None, **kwargs):
    volume, function = volume or _Volume(), _Function(**kwargs)
    return ModalNarrationSynthesizer(volume=volume, function=function, sleep=lambda _s: None), volume, function


def test_a_clause_is_staged_and_the_wav_returned() -> None:
    synth, volume, function = _synth(pending=2)

    assert synth.synthesize("Rùa con bò đi.") == WAV

    prefix = function.inputs[0]["attempt_prefix"]
    assert json.loads(volume.files[f"/{prefix}input/request.json"]) == {"text": "Rùa con bò đi.", "voice": "Hải Đăng"}
    manifest = json.loads(volume.files[f"/{prefix}input/manifest.json"])
    assert manifest["schema_version"] == MANIFEST_SCHEMA
    assert manifest["asset"]["size_bytes"] == len(volume.files[f"/{prefix}input/request.json"])
    assert function.inputs[0]["workload"] == "tts.narration.generate"


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"error": RuntimeError("x")}, "VIDEO_NARRATION_FAILED"),
        ({"tamper": {"job_id": "other"}}, "VIDEO_NARRATION_OUTPUT_INVALID"),
        ({"asset": {"content_type": "audio/wav", "size_bytes": 4, "bytes": b"RIFF", "sha256": "0" * 64}},
         "VIDEO_NARRATION_HASH_MISMATCH"),
    ],
)
def test_failures_become_safe_codes(kwargs, code) -> None:
    synth, _v, _f = _synth(**kwargs)

    with pytest.raises(VideoPipelineError) as error:
        synth.synthesize("Rùa con bò đi.")

    assert error.value.code == code


def test_invalid_clauses_staging_failures_and_timeouts() -> None:
    for text in ("", "   ", "a" * 101):
        with pytest.raises(VideoPipelineError) as error:
            _synth()[0].synthesize(text)
        assert error.value.code == "VIDEO_NARRATION_CLAUSE_INVALID"
    with pytest.raises(VideoPipelineError) as staging:
        _synth(_Volume(fail=True))[0].synthesize("Rùa đi.")
    assert staging.value.code == "VIDEO_NARRATION_STAGING_FAILED"
    slow = ModalNarrationSynthesizer(
        volume=_Volume(), function=_Function(pending=10**6), timeout_seconds=0.0, sleep=lambda _s: None
    )
    with pytest.raises(VideoPipelineError) as timeout:
        slow.synthesize("Rùa đi.")
    assert timeout.value.code == "VIDEO_NARRATION_TIMEOUT"
