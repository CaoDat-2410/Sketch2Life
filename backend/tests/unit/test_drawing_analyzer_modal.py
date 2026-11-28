from __future__ import annotations

import hashlib
import io
import re
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

from sketch2life.application.ports.parent_story_inputs import (
    DRAWING_ANALYSIS_FAILED,
    DRAWING_ANALYSIS_UNAVAILABLE,
    DrawingAnalysisFailure,
    DrawingAnalysisOutcomeUnknown,
    DrawingAnalysisRequest,
    DrawingAnalysisResult,
)
from sketch2life.infrastructure.ai.drawing_analyzer_modal import ModalDrawingAnalyzer
from sketch2life.infrastructure.ai.modal_function_client import (
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
)


def _png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (2, 2), color=(20, 40, 60)).save(output, format="PNG")
    return output.getvalue()


class _Storage:
    def __init__(
        self,
        data: bytes,
        *,
        content_length: int | None = None,
        content_type: str = "image/png",
        error: Exception | None = None,
    ) -> None:
        self.data = data
        self.content_length = len(data) if content_length is None else content_length
        self.content_type = content_type
        self.error = error
        self.read_sizes: list[int] = []
        self.keys: list[str] = []

    def get_object(self, key: str) -> Any:
        self.keys.append(key)
        if self.error is not None:
            raise self.error
        body = _TrackingBody(self.data, self.read_sizes)
        return type(
            "Stored",
            (),
            {
                "body": body,
                "content_length": self.content_length,
                "content_type": self.content_type,
                "metadata": {},
            },
        )()


class _TrackingBody(io.BytesIO):
    def __init__(self, data: bytes, read_sizes: list[int]) -> None:
        super().__init__(data)
        self._read_sizes = read_sizes

    def read(self, size: int = -1) -> bytes:
        self._read_sizes.append(size)
        return super().read(size)


class _Client:
    def __init__(
        self, output: dict[str, Any] | None = None, error: Exception | None = None
    ) -> None:
        self.output = output or {}
        self.error = error
        self.calls = 0
        self.prepared: list[Any] = []

    def invoke(self, prepared: Any) -> Any:
        self.calls += 1
        self.prepared.append(prepared)
        if self.error is not None:
            raise self.error
        return type("WorkerResult", (), {"output": self.output})()


def _request(data: bytes, **changes: Any) -> DrawingAnalysisRequest:
    values: dict[str, Any] = {
        "run_id": "run-id",
        "input_revision": 2,
        "derived_asset_ref": "parent/run-id/derived.png",
        "derived_sha256": hashlib.sha256(data).hexdigest(),
        "derived_size_bytes": len(data),
    }
    values.update(changes)
    return DrawingAnalysisRequest(**values)


def _analyzer(
    data: bytes,
    *,
    output: dict[str, Any] | None = None,
    error: Exception | None = None,
    storage_error: Exception | None = None,
    content_length: int | None = None,
) -> tuple[ModalDrawingAnalyzer, _Storage, _Client]:
    storage = _Storage(data, content_length=content_length, error=storage_error)
    client = _Client(output=output, error=error)
    return ModalDrawingAnalyzer(storage, client), storage, client


def test_success_maps_worker_candidate_and_uses_fresh_opaque_ids() -> None:
    data = _png_bytes()
    output = {
        "result": {
            "adult_confirmation_required": True,
            "candidate_subject": "  paper kite  ",
            "visible_features": [" long tail ", "red diamond", "blue bow", "clouds", "extra"],
            "confidence": 0.75,
        }
    }
    analyzer, storage, client = _analyzer(data, output=output)

    result = analyzer.analyze(_request(data))

    assert result == DrawingAnalysisResult(
        subject="paper kite",
        visible_features=("long tail", "red diamond", "blue bow", "clouds"),
        confidence=0.75,
        child_count=1,
    )
    assert storage.keys == ["parent/run-id/derived.png"]
    assert client.calls == 1
    prepared = client.prepared[0]
    for name in ("job_id", "generation_id", "attempt_id"):
        assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", prepared.payload[name])


def test_missing_confidence_defaults_to_zero() -> None:
    data = _png_bytes()
    analyzer, _, client = _analyzer(
        data,
        output={
            "result": {
                "adult_confirmation_required": True,
                "candidate_subject": None,
                "visible_features": ["round shape"],
            }
        },
    )

    result = analyzer.analyze(_request(data))

    assert result.subject == ""
    assert result.confidence == 0.0
    assert client.calls == 1


@pytest.mark.parametrize(
    "request_changes",
    [
        {"derived_sha256": "0" * 64},
        {"derived_size_bytes": 1},
    ],
)
def test_hash_or_size_mismatch_never_reaches_client(request_changes: dict[str, Any]) -> None:
    data = _png_bytes()
    analyzer, _, client = _analyzer(data)

    with pytest.raises(DrawingAnalysisFailure) as failure:
        analyzer.analyze(_request(data, **request_changes))

    assert failure.value.code == DRAWING_ANALYSIS_FAILED
    assert client.calls == 0


def test_unknown_outcome_is_not_retried() -> None:
    data = _png_bytes()
    analyzer, _, client = _analyzer(data, error=ModalFunctionOutcomeUnknown("fc-test"))

    with pytest.raises(DrawingAnalysisOutcomeUnknown):
        analyzer.analyze(_request(data))

    assert client.calls == 1


def test_execution_failure_maps_to_existing_failure_code_without_retry() -> None:
    data = _png_bytes()
    analyzer, _, client = _analyzer(
        data, error=ModalFunctionExecutionFailed("DRAWING_WORKER_FAILED_TERMINAL")
    )

    with pytest.raises(DrawingAnalysisFailure) as failure:
        analyzer.analyze(_request(data))

    assert failure.value.code == DRAWING_ANALYSIS_FAILED
    assert client.calls == 1


def test_storage_fault_maps_to_unavailable_without_invoking_client() -> None:
    data = _png_bytes()
    analyzer, _, client = _analyzer(data, storage_error=OSError("storage unavailable"))

    with pytest.raises(DrawingAnalysisFailure) as failure:
        analyzer.analyze(_request(data))

    assert failure.value.code == DRAWING_ANALYSIS_UNAVAILABLE
    assert client.calls == 0


@pytest.mark.parametrize(
    "output",
    [
        {"result": {"adult_confirmation_required": False, "visible_features": ["line"]}},
        {"result": {"adult_confirmation_required": True, "visible_features": []}},
    ],
)
def test_bad_worker_answer_maps_to_analysis_failure(output: dict[str, Any]) -> None:
    data = _png_bytes()
    analyzer, _, client = _analyzer(data, output=output)

    with pytest.raises(DrawingAnalysisFailure) as failure:
        analyzer.analyze(_request(data))

    assert failure.value.code == DRAWING_ANALYSIS_FAILED
    assert client.calls == 1


@pytest.mark.parametrize("env", ["local", "test"])
def test_app_composes_drawing_analyzer_for_modal_dev_in_local_and_test(env: str) -> None:
    import sketch2life.interfaces.http.app as app_module
    from sketch2life.infrastructure.config.settings import Settings

    storage = object()
    settings = Settings(env=env, ai_provider="modal_dev", _env_file=None)

    analyzer = app_module._build_drawing_analyzer(settings, storage)

    assert isinstance(analyzer, ModalDrawingAnalyzer)
    assert analyzer._storage is storage


@pytest.mark.parametrize(
    ("env", "provider", "has_storage"),
    [
        ("staging", "modal_dev", True),
        ("production", "modal_dev", True),
        ("test", "lightning_dev", True),
        ("local", "disabled", True),
        ("local", "modal_dev", False),
    ],
)
def test_app_does_not_compose_drawing_analyzer_outside_allowed_profiles(
    env: str, provider: str, has_storage: bool
) -> None:
    import sketch2life.interfaces.http.app as app_module

    settings = SimpleNamespace(env=env, ai_provider=provider)
    storage = object() if has_storage else None

    assert app_module._build_drawing_analyzer(settings, storage) is None
