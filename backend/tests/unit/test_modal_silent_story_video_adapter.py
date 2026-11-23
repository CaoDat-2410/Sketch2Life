"""Offline tests for one-shot Modal video dispatch and volume transfer."""

from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO

from sketch2life.infrastructure.ai.modal_silent_story_video import ModalSilentStoryVideoWorker


class _Batch:
    def __init__(self, volume: _Volume) -> None:
        self.volume = volume

    def put_file(self, file_obj: BytesIO, path: str) -> None:
        self.volume.files[path.lstrip("/")] = file_obj.read()


class _Volume:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    @contextmanager
    def batch_upload(self):
        yield _Batch(self)

    def read_file(self, path: str):
        return iter((self.files[path],))


class _Function:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def spawn(self, payload: dict[str, object]):
        self.calls.append(payload)
        return type("CallHandle", (), {"object_id": "fc-test-candidate-001"})()


class _Call:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result

    def get(self, *, timeout: int):
        assert timeout == 0
        return self.result


def test_adapter_stages_inputs_spawns_once_and_reads_committed_outputs() -> None:
    volume = _Volume()
    function = _Function()
    result = {"job_id": "job-1", "generation_id": "generation-1", "attempt_id": "attempt-1"}
    adapter = ModalSilentStoryVideoWorker(
        volume=volume,
        function_resolver=lambda app, name: (app, name, function)[2],
        call_resolver=lambda call_id: _Call(result),
    )
    attempt_prefix = "sketch2life/dev/job-1/generation-1/attempt-1/"
    worker_input = {
        "job_id": "job-1",
        "generation_id": "generation-1",
        "attempt_id": "attempt-1",
        "attempt_prefix": attempt_prefix,
    }

    call_id = adapter.dispatch(
        worker_input=worker_input,
        drawing_bytes=b"synthetic-drawing-bytes",
        manifest_bytes=b"synthetic-manifest",
    )

    assert call_id == "fc-test-candidate-001"
    assert len(function.calls) == 1
    assert volume.files[f"{attempt_prefix}input/drawing.png"] == b"synthetic-drawing-bytes"
    assert volume.files[f"{attempt_prefix}input/manifest.json"] == b"synthetic-manifest"

    video_bytes = b"synthetic-mp4-bytes"
    manifest_bytes = b"synthetic-output-manifest"
    volume.files[f"{attempt_prefix}output/video.mp4"] = video_bytes
    volume.files[f"{attempt_prefix}output/video-manifest.json"] = manifest_bytes
    output = adapter.collect_if_ready(
        modal_call_id=call_id,
        job_id="job-1",
        generation_id="generation-1",
        attempt_id="attempt-1",
        attempt_prefix=attempt_prefix,
    )

    assert output is not None
    assert output.result == result
    assert output.video_bytes == video_bytes
    assert output.output_manifest_bytes == manifest_bytes
    assert len(function.calls) == 1
