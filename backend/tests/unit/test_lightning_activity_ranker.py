from __future__ import annotations

import pytest

from sketch2life.application.ports.activity_ranker import ActivityRankingUnavailable
from sketch2life.contracts.schemas.activity_ranking import (
    ActivityRankingCandidateV1,
    ActivityRankingRequestV1,
)
from sketch2life.infrastructure.ai.lightning_activity_ranker import LightningActivityRanker
from sketch2life.infrastructure.ai.lightning_client import LightningProviderError


class _Transport:
    def __init__(self, response: dict[str, object] | Exception) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, object]]] = []

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((path, payload))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _request() -> ActivityRankingRequestV1:
    return ActivityRankingRequestV1(
        request_id="rank-fixture-1",
        topic_label_vi="hươu cao cổ",
        age_months=54,
        confirmed_interest_ids=("ANIMAL_GENERIC",),
        candidates=tuple(
            ActivityRankingCandidateV1(
                activity_id=f"ACT-{index:04d}",
                title_vi=f"Hoạt động {index}",
                summary_vi="Mô tả hoạt động fixture.",
                match_reason_vi="Khớp chủ đề và độ tuổi đã xác nhận.",
                concept_ids=("ANIMAL_GENERIC",),
                objective_ids=("OBJ_SCIENTIFIC_OBSERVATION",),
            )
            for index in range(1, 5)
        ),
    )


def test_ranker_accepts_exactly_three_ids_from_eligible_catalog_set() -> None:
    transport = _Transport(
        {
            "contract_name": "ActivityRankingResultV1",
            "contract_version": "1.0",
            "request_id": "rank-fixture-1",
            "ranked_activity_ids": ["ACT-0003", "ACT-0001", "ACT-0004"],
        }
    )
    result = LightningActivityRanker(transport=transport).rank(_request())

    assert result.ranked_activity_ids == ("ACT-0003", "ACT-0001", "ACT-0004")
    assert transport.calls[0][0] == "/v2/p1/activity-rank"
    assert "child_profile" not in transport.calls[0][1]


@pytest.mark.parametrize(
    "ranked_ids",
    [
        ["ACT-0001", "ACT-0002"],
        ["ACT-0001", "ACT-0002", "ACT-9999"],
        ["ACT-0001", "ACT-0001", "ACT-0002"],
    ],
)
def test_ranker_rejects_incomplete_duplicate_or_out_of_set_ids(ranked_ids: list[str]) -> None:
    transport = _Transport(
        {
            "contract_name": "ActivityRankingResultV1",
            "contract_version": "1.0",
            "request_id": "rank-fixture-1",
            "ranked_activity_ids": ranked_ids,
        }
    )

    with pytest.raises(ActivityRankingUnavailable) as raised:
        LightningActivityRanker(transport=transport).rank(_request())

    assert raised.value.code == "ACTIVITY_RANKING_INVALID_RESULT"
    assert "ACT-9999" not in str(raised.value)


def test_ranker_sanitizes_provider_error() -> None:
    transport = _Transport(
        LightningProviderError("PROVIDER_ERROR", "synthetic private error", True)
    )

    with pytest.raises(ActivityRankingUnavailable) as raised:
        LightningActivityRanker(transport=transport).rank(_request())

    assert raised.value.code == "ACTIVITY_RANKING_UNAVAILABLE"
    assert raised.value.retryable is True
    assert "synthetic private error" not in str(raised.value)
