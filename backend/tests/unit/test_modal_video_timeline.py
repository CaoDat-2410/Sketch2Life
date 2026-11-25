"""FEAT-093: the Modal timeline adapter maps results and failures to safe codes."""

from __future__ import annotations

import pytest

from sketch2life.infrastructure.ai.modal_function_client import (
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionResult,
    _JSON_WORKERS,
)
from sketch2life.infrastructure.story_video.modal_timeline import (
    OUTPUT_SCHEMA,
    ModalVideoTimelineGenerator,
    VideoPlanningUnavailable,
)


class _Client:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    def invoke(self, workload, request_data):
        self.calls.append((workload, request_data))
        if self.error is not None:
            raise self.error
        return self.result


def test_the_workload_is_allowlisted_on_the_shared_qwen_worker() -> None:
    assert _JSON_WORKERS["video.timeline.generate"][1] == "qwen-worker"


def test_the_draft_is_returned_without_the_schema_marker() -> None:
    output = {"result": {"schema_version": OUTPUT_SCHEMA, "title": "T", "scenes": []}}
    client = _Client(ModalJsonFunctionResult(output=output, call_id="fc-1", elapsed_seconds=1.0))

    draft = ModalVideoTimelineGenerator(client=client).generate({"a": 1})

    assert draft == {"title": "T", "scenes": []}
    assert client.calls == [("video.timeline.generate", {"a": 1})]


@pytest.mark.parametrize(
    ("error", "code", "unknown"),
    [
        (ModalFunctionOutcomeUnknown(), "VIDEO_PLAN_OUTCOME_UNKNOWN", True),
        (ModalFunctionExecutionFailed("MODAL_MODEL_OUTPUT_TRUNCATED"), "MODAL_MODEL_OUTPUT_TRUNCATED", False),
        (ValueError("x"), "VIDEO_PLAN_INPUT_INVALID", False),
    ],
)
def test_failures_become_safe_codes(error, code, unknown) -> None:
    with pytest.raises(VideoPlanningUnavailable) as raised:
        ModalVideoTimelineGenerator(client=_Client(error=error)).generate({})

    assert raised.value.code == code and raised.value.outcome_unknown is unknown


def test_a_wrong_schema_marker_is_rejected() -> None:
    client = _Client(ModalJsonFunctionResult(output={"result": {"schema_version": "x"}}, call_id="fc-1", elapsed_seconds=1.0))

    with pytest.raises(VideoPlanningUnavailable) as raised:
        ModalVideoTimelineGenerator(client=client).generate({})

    assert raised.value.code == "VIDEO_PLAN_OUTPUT_INVALID"
