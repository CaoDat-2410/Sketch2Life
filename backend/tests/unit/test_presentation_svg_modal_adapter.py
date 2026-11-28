"""Contract tests for the one-shot Modal presentation SVG adapter."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from typing import Any

import pytest
from structlog.testing import capture_logs

from sketch2life.application.ports.presentation_svg import (
    PresentationSvgDrafterUnavailable,
    PresentationSvgDraftInput,
)
from sketch2life.contracts.schemas.svg_engine import SvgDocumentV1
from sketch2life.domain.lesson_occurrences.presentation_svg_shapes import (
    build_presentation_svg_source,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionResult,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.lesson_occurrences.presentation_svg_modal import (
    ModalPresentationSvgDrafter,
    build_presentation_svg_drafter,
)
from sketch2life.infrastructure.svg.renderer import render_svg_document
from sketch2life.infrastructure.svg.sanitizer import sanitize_svg_source

_REQUEST = PresentationSvgDraftInput(
    schema_version="sketch2life.presentation-svg-input.v1",
    activity_title="Draw a butterfly",
    subject_text="butterfly",
)
_DRAFT: dict[str, Any] = {
    "schema_version": "sketch2life.presentation-svg-draft.v1",
    "review_required": True,
    "viewbox": [0, 0, 100, 100],
    "shapes": [
        {
            "kind": "circle",
            "cx": 20,
            "cy": 20,
            "r": 8,
            "stroke": "#1f2937",
            "stroke_width": 2,
        },
        {
            "kind": "rect",
            "x": 40,
            "y": 12,
            "w": 24,
            "h": 18,
            "stroke": "#2563eb",
            "stroke_width": 3,
        },
        {
            "kind": "polyline",
            "points": [[12, 72], [22, 60], [32, 72]],
            "stroke": "#16a34a",
            "stroke_width": 2,
        },
        {
            "kind": "line",
            "x1": 5,
            "y1": 40,
            "x2": 20,
            "y2": 45,
            "stroke": "#dc2626",
            "stroke_width": 1,
        },
        {
            "kind": "ellipse",
            "cx": 70,
            "cy": 70,
            "rx": 12,
            "ry": 8,
            "stroke": "#d97706",
            "stroke_width": 4,
        },
    ],
}


class _FakeClient:
    def __init__(
        self,
        *,
        draft: object = _DRAFT,
        model: object | None = None,
        failure: Exception | None = None,
    ) -> None:
        self.draft = draft
        self.model = model if model is not None else {"id": MODEL_ID, "revision": MODEL_REVISION}
        self.failure = failure
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, workload: str, request_data: dict[str, Any]) -> ModalJsonFunctionResult:
        self.calls.append((workload, copy.deepcopy(request_data)))
        if self.failure is not None:
            raise self.failure
        return ModalJsonFunctionResult(
            output={"model": self.model, "result": self.draft},
            call_id="fc-presentation-svg-test",
            elapsed_seconds=1.25,
        )


def _request_hash(request: PresentationSvgDraftInput) -> str:
    payload = {
        "schema_version": request.schema_version,
        "activity_title": request.activity_title,
        "subject_text": request.subject_text,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def test_happy_path_serializes_geometry_and_sends_only_bounded_fields() -> None:
    client = _FakeClient()
    output = ModalPresentationSvgDrafter(client).draft(_REQUEST)

    assert output.source.startswith(b'<svg xmlns="http://www.w3.org/2000/svg"')
    sanitized = sanitize_svg_source(output.source)
    document = SvgDocumentV1.model_validate(sanitized.document).model_dump(mode="json")
    assert render_svg_document(document).startswith("<svg")
    assert b"<circle" in output.source and b"<path" in output.source
    assert all(tag not in output.source for tag in (b"<ellipse", b"<line", b"<polyline", b"<rect"))
    assert len(document["paths"]) == 5
    assert sanitized.readiness["classification"] in {
        "REQUIRES_MANUAL_AUTHORING",
        "STROKE_READY",
    }
    assert (output.generator_name, output.generator_version, output.license_id) == (
        "qwen3.8-27b-fp8-modal",
        MODEL_REVISION,
        "CC0-1.0",
    )
    assert len(client.calls) == 1
    workload, request_data = client.calls[0]
    assert workload == "presentation.svg-draft.generate"
    assert set(request_data) == {
        "schema_version",
        "activity_title",
        "subject_text",
        "content_hash",
    }
    assert request_data["content_hash"] == _request_hash(_REQUEST)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["shapes"][0].update(kind="text"),
        lambda value: value["shapes"][0].update(cx=101),
        lambda value: value["shapes"][0].update(cy=float("nan")),
        lambda value: value["shapes"][0].update(cy=float("inf")),
        lambda value: value["shapes"].extend(copy.deepcopy(value["shapes"] * 4)),
        lambda value: value["shapes"][0].update(stroke="#ffffff"),
        lambda value: value["shapes"][0].update(extra="value"),
        lambda value: value["shapes"][0].update(text="unsafe"),
        lambda value: value["shapes"][0].update(href="javascript:alert(1)"),
        lambda value: value["shapes"][0].update(style="fill:url(https://example.invalid)"),
        lambda value: value.update(shapes=value["shapes"][:3]),
    ],
    ids=[
        "unknown-kind",
        "out-of-range",
        "nan",
        "infinity",
        "too-many-shapes",
        "bad-palette",
        "extra-key",
        "text-injection",
        "href-injection",
        "style-injection",
        "too-few-shapes",
    ],
)
def test_invalid_shapes_fail_without_retry(mutate: Any) -> None:
    draft = copy.deepcopy(_DRAFT)
    mutate(draft)
    client = _FakeClient(draft=draft)

    with pytest.raises((TypeError, ValueError)) as raised:
        ModalPresentationSvgDrafter(client).draft(_REQUEST)

    assert not isinstance(raised.value, PresentationSvgDrafterUnavailable)
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    "failure",
    [
        ModalFunctionOutcomeUnknown("fc-outcome-unknown"),
        ModalFunctionExecutionFailed("PROVIDER_UNAVAILABLE"),
        TimeoutError("finite Modal wait expired"),
    ],
    ids=["unknown-outcome", "provider-unavailable", "timeout"],
)
def test_unavailable_modal_outcomes_map_to_unavailable_once(failure: Exception) -> None:
    client = _FakeClient(failure=failure)

    with pytest.raises(PresentationSvgDrafterUnavailable):
        ModalPresentationSvgDrafter(client).draft(_REQUEST)

    assert len(client.calls) == 1


def test_terminal_modal_failure_is_a_bad_response_and_is_not_retried() -> None:
    client = _FakeClient(failure=ModalFunctionExecutionFailed("MODAL_WORKER_FAILED_TERMINAL"))

    with pytest.raises(ModalFunctionExecutionFailed) as raised:
        ModalPresentationSvgDrafter(client).draft(_REQUEST)

    assert raised.value.code == "MODAL_WORKER_FAILED_TERMINAL"
    assert len(client.calls) == 1


def test_model_mismatch_is_a_bad_response_and_is_not_retried() -> None:
    client = _FakeClient(model={"id": "Qwen/other", "revision": "wrong"})

    with pytest.raises(ValueError, match="model identity"):
        ModalPresentationSvgDrafter(client).draft(_REQUEST)

    assert len(client.calls) == 1


def test_logging_does_not_include_subject_text(caplog: pytest.LogCaptureFixture) -> None:
    private_subject = "subject-sentinel-for-log-check"
    request = PresentationSvgDraftInput(
        schema_version=_REQUEST.schema_version,
        activity_title="Draw a test",
        subject_text=private_subject,
    )
    caplog.set_level(logging.INFO)
    client = _FakeClient()

    with capture_logs() as events:
        ModalPresentationSvgDrafter(client).draft(request)

    assert private_subject not in caplog.text
    assert private_subject not in repr(events)
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    ("ai_provider", "env", "expected"),
    [
        ("disabled", "local", False),
        ("modal_dev", "production", False),
        ("modal_dev", "staging", False),
        ("modal_dev", "local", True),
        ("modal_dev", "test", True),
    ],
)
def test_composition_builder_is_fail_closed(ai_provider: str, env: str, expected: bool) -> None:
    settings = Settings.model_construct(ai_provider=ai_provider, env=env)

    drafter = build_presentation_svg_drafter(settings)

    assert isinstance(drafter, ModalPresentationSvgDrafter) is expected


def test_shape_builder_is_pure_and_rejects_non_object_markup() -> None:
    source = build_presentation_svg_source(_DRAFT)
    assert b"<script" not in source
    assert b'fill="none"' in source
    invalid = copy.deepcopy(_DRAFT)
    invalid["shapes"][0]["href"] = "javascript:alert(1)"
    with pytest.raises(ValueError):
        build_presentation_svg_source(invalid)
