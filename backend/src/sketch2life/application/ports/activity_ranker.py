"""Application-owned, bounded activity ranking port."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.activity_ranking import (
    ActivityRankingRequestV1,
    ActivityRankingResultV1,
)


class ActivityRankingUnavailable(Exception):
    """Sanitized provider failure; no catalog text or provider body is retained."""

    def __init__(self, code: str, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class ActivityRankerPort(Protocol):
    def rank(self, request: ActivityRankingRequestV1) -> ActivityRankingResultV1: ...


__all__ = ["ActivityRankerPort", "ActivityRankingUnavailable"]
