"""Backend-only Lightning adapter for AI ranking of reviewed eligible activities."""

from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.activity_ranker import (
    ActivityRankerPort,
    ActivityRankingUnavailable,
)
from sketch2life.contracts.schemas.activity_ranking import (
    ActivityRankingRequestV1,
    ActivityRankingResultV1,
)
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)

_RESULT_ADAPTER: TypeAdapter[ActivityRankingResultV1] = TypeAdapter(
    ActivityRankingResultV1
)


class LightningActivityRanker(ActivityRankerPort):
    def __init__(
        self,
        *,
        transport: JsonTransport,
        endpoint_path: str = "/v2/p1/activity-rank",
    ) -> None:
        if not endpoint_path.startswith("/"):
            raise ValueError("activity ranking path must be absolute")
        self._transport = transport
        self._endpoint_path = endpoint_path

    def rank(self, request: ActivityRankingRequestV1) -> ActivityRankingResultV1:
        try:
            raw = self._transport.post_json(
                self._endpoint_path,
                request.model_dump(mode="json"),
            )
        except TimeoutError:
            raise ActivityRankingUnavailable("ACTIVITY_RANKING_TIMEOUT", True) from None
        except LightningProviderError as error:
            code = (
                "ACTIVITY_RANKING_ENDPOINT_UNAVAILABLE"
                if error.code == "ENDPOINT_NOT_FOUND"
                else "ACTIVITY_RANKING_UNAVAILABLE"
            )
            raise ActivityRankingUnavailable(code, error.retryable) from None
        except OSError:
            raise ActivityRankingUnavailable("ACTIVITY_RANKING_UNAVAILABLE", True) from None
        try:
            result = _RESULT_ADAPTER.validate_python(raw)
        except ValidationError:
            raise ActivityRankingUnavailable("ACTIVITY_RANKING_INVALID_RESULT", False) from None
        allowed_ids = {item.activity_id for item in request.candidates}
        expected_count = min(3, len(allowed_ids))
        if (
            result.request_id != request.request_id
            or len(result.ranked_activity_ids) != expected_count
            or not set(result.ranked_activity_ids) <= allowed_ids
        ):
            raise ActivityRankingUnavailable("ACTIVITY_RANKING_INVALID_RESULT", False)
        return result


__all__ = ["LightningActivityRanker"]
