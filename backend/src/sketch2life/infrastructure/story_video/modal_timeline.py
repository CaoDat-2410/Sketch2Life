"""Modal adapter of the video timeline workload (FEAT-093); implements ``VideoTimelineGeneratorPort``."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from sketch2life.application.video_pipeline.ports import VideoPipelineError
from sketch2life.infrastructure.ai.modal_function_client import (
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,
)

WORKLOAD: Final = "video.timeline.generate"
OUTPUT_SCHEMA: Final = "sketch2life.video-timeline-draft.v1"


class VideoPlanningUnavailable(VideoPipelineError):
    """The timeline worker failed or its outcome is unknown; the code is safe to store and show."""

    def __init__(self, code: str, *, outcome_unknown: bool = False) -> None:
        self.outcome_unknown = outcome_unknown
        super().__init__(code)


class ModalVideoTimelineGenerator:
    def __init__(self, *, client: ModalJsonFunctionClient | None = None) -> None:
        self._client = client or ModalJsonFunctionClient()

    def generate(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            response = self._client.invoke(WORKLOAD, dict(request))
        except ModalFunctionOutcomeUnknown:
            raise VideoPlanningUnavailable("VIDEO_PLAN_OUTCOME_UNKNOWN", outcome_unknown=True) from None
        except ModalFunctionExecutionFailed as failure:
            raise VideoPlanningUnavailable(failure.code) from None
        except ValueError:
            raise VideoPlanningUnavailable("VIDEO_PLAN_INPUT_INVALID") from None
        result = response.output.get("result")
        if not isinstance(result, dict) or result.get("schema_version") != OUTPUT_SCHEMA:
            raise VideoPlanningUnavailable("VIDEO_PLAN_OUTPUT_INVALID")
        return {key: value for key, value in result.items() if key != "schema_version"}
