from __future__ import annotations

import hashlib
from io import BytesIO

import pytest
from PIL import Image

from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisFailure,
    DrawingAnalysisOutcomeUnknown,
    DrawingAnalysisRequest,
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalFunctionDispatchRejected,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalFunctionResult,
)
from sketch2life.infrastructure.story_inputs.modal_adapters import (
    ModalParentDrawingAnalyzer,
    ModalParentStoryGenerator,
)


def _png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (32, 32), color=(250, 242, 255)).save(output, format="PNG")
    return output.getvalue()


class _Storage:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def get_object(self, key: str) -> StoredObject:
        assert key == "normalized/drawing.png"
        return StoredObject(
            body=BytesIO(self.value),
            content_length=len(self.value),
            content_type="image/png",
            metadata={},
        )


class _DrawingClient:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls = 0

    def invoke(self, prepared: object) -> ModalFunctionResult:
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        payload = prepared.payload
        output = {
            "schema_version": "sketch2life.modal.worker-output.v1",
            "workload": "drawing.analyze",
            "job_id": payload["job_id"],
            "generation_id": payload["generation_id"],
            "attempt_id": payload["attempt_id"],
            "input_sha256": prepared.drawing_sha256,
            "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
            "result": {
                "candidate_subject": "con bướm",
                "visible_features": ["hai cặp cánh", "thân nhỏ"],
                "confidence": 0.91,
                "adult_confirmation_required": True,
            },
        }
        return ModalFunctionResult(
            output=output,
            call_id="fc-test-drawing",
            output_sha256="b" * 64,
            elapsed_seconds=0.5,
        )


class _StoryClient:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls = 0

    def generate(self, _context: dict[str, object]) -> tuple[dict[str, object], str]:
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return (
            {
                "schema_version": "sketch2life.story-revision.v1",
                "language": "vi",
                "title": "Con bướm trong khu vườn",
                "story": {
                    "opening": "Con bướm bay qua khu vườn.",
                    "middle": "Nó dừng bên một bông hoa.",
                    "ending": "Con bướm lại bay về phía nắng.",
                },
                "duration_ms": 30_000,
                "scenes": [{"scene_index": 1}],
                "_staging_issue": "STAGING_ABSENT",
            },
            "fc-test-story",
        )


def test_drawing_adapter_hash_checks_asset_and_maps_worker_result() -> None:
    drawing = _png()
    client = _DrawingClient()
    analyzer = ModalParentDrawingAnalyzer(_Storage(drawing), client=client)  # type: ignore[arg-type]
    result = analyzer.analyze(
        DrawingAnalysisRequest(
            run_id="run-1",
            input_revision=1,
            derived_asset_ref="normalized/drawing.png",
            derived_sha256=hashlib.sha256(drawing).hexdigest(),
            derived_size_bytes=len(drawing),
        )
    )

    assert client.calls == 1
    assert result.subject == "con bướm"
    assert result.visible_features == ("hai cặp cánh", "thân nhỏ")
    assert result.confidence == pytest.approx(0.91)


def test_drawing_adapter_rejects_hash_mismatch_before_modal_dispatch() -> None:
    drawing = _png()
    client = _DrawingClient()
    analyzer = ModalParentDrawingAnalyzer(_Storage(drawing), client=client)  # type: ignore[arg-type]

    with pytest.raises(DrawingAnalysisFailure, match="DRAWING_INPUT_INVALID"):
        analyzer.analyze(
            DrawingAnalysisRequest(
                run_id="run-1",
                input_revision=1,
                derived_asset_ref="normalized/drawing.png",
                derived_sha256="0" * 64,
                derived_size_bytes=len(drawing),
            )
        )

    assert client.calls == 0


@pytest.mark.parametrize(
    ("modal_error", "expected"),
    [
        (ModalFunctionDispatchRejected(), DrawingAnalysisFailure),
        (ModalFunctionExecutionFailed("MODAL_MODEL_OUTPUT_INVALID"), DrawingAnalysisFailure),
        (ModalFunctionOutcomeUnknown("fc-unknown"), DrawingAnalysisOutcomeUnknown),
    ],
)
def test_drawing_adapter_preserves_terminal_vs_unknown_outcomes(
    modal_error: Exception, expected: type[Exception]
) -> None:
    drawing = _png()
    analyzer = ModalParentDrawingAnalyzer(
        _Storage(drawing),
        client=_DrawingClient(failure=modal_error),  # type: ignore[arg-type]
    )

    with pytest.raises(expected):
        analyzer.analyze(
            DrawingAnalysisRequest(
                run_id="run-1",
                input_revision=1,
                derived_asset_ref="normalized/drawing.png",
                derived_sha256=hashlib.sha256(drawing).hexdigest(),
                derived_size_bytes=len(drawing),
            )
        )


def test_story_adapter_keeps_model_provenance_and_hides_staging() -> None:
    client = _StoryClient()
    generator = ModalParentStoryGenerator(client=client)  # type: ignore[arg-type]
    result = generator.generate({"confirmed_subject": "con bướm"})

    assert client.calls == 1
    assert result.call_id == "fc-test-story"
    assert result.model_id == STORY_MODEL_ID
    assert result.model_revision == STORY_MODEL_REVISION
    assert result.story["title"] == "Con bướm trong khu vườn"
    assert "_staging_issue" not in result.story
    assert result.staging is None
    assert result.staging_issue == "STAGING_ABSENT"


@pytest.mark.parametrize(
    ("modal_error", "expected"),
    [
        (ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID"), StoryGenerationFailure),
        (ModalFunctionOutcomeUnknown("fc-unknown"), StoryGenerationOutcomeUnknown),
    ],
)
def test_story_adapter_preserves_terminal_vs_unknown_outcomes(
    modal_error: Exception, expected: type[Exception]
) -> None:
    generator = ModalParentStoryGenerator(client=_StoryClient(failure=modal_error))  # type: ignore[arg-type]

    with pytest.raises(expected):
        generator.generate({"confirmed_subject": "con bướm"})
