"""Explicit mapping to existing bounded ranker contract; no provider/default weights."""

from collections.abc import Callable

from sketch2life.application.ports.activity_execution import DiscoveryQuery
from sketch2life.application.ports.activity_ranker import ActivityRankerPort
from sketch2life.contracts.schemas.activity_ranking import (
    ActivityRankingCandidateV1,
    ActivityRankingRequestV1,
    ActivityRankingResultV1,
)
from sketch2life.domain.activity_execution.model import Definition, fail
from sketch2life.domain.knowledge_video.model import ExactRef


class LegacyRankingAdapter:
    def __init__(
        self,
        ranker: ActivityRankerPort,
        aliases: tuple[tuple[ExactRef, ActivityRankingCandidateV1], ...],
        *,
        request_ids: Callable[[], str],
        topic_label: Callable[[tuple[str, ...]], str],
    ) -> None:
        self.ranker, self.request_ids, self.topic_label = ranker, request_ids, topic_label
        self.aliases = {
            ref: ActivityRankingCandidateV1.model_validate(row.model_dump(mode="python"))
            for ref, row in aliases
        }
        if len(self.aliases) != len(aliases) or len(
            {row.activity_id for row in self.aliases.values()}
        ) != len(aliases):
            fail("INVALID_RECOMMENDATION")

    def rank(
        self, query: DiscoveryQuery, rows: tuple[Definition, ...]
    ) -> tuple[tuple[ExactRef, str], ...]:
        # Exact version/hash mappings supplied by reviewed adapter owner, never
        # guess published refs from legacy ACT-* IDs or rewrite old routes.
        candidates = tuple(self.aliases[row.source_ref] for row in rows)
        if any(c.title_vi != row.title for c, row in zip(candidates, rows, strict=True)):
            fail("SOURCE_MISMATCH")
        request = ActivityRankingRequestV1(
            request_id=self.request_ids(),
            topic_label_vi=self.topic_label(query.topic_ids),
            age_months=query.age_months,
            confirmed_interest_ids=query.preferences,
            candidates=candidates,
        )
        result = self.ranker.rank(request)
        result = ActivityRankingResultV1.model_validate(result.model_dump(mode="python"))
        known = {
            c.activity_id: (row.source_ref, c.match_reason_vi)
            for c, row in zip(candidates, rows, strict=True)
        }
        if result.request_id != request.request_id or any(
            key not in known for key in result.ranked_activity_ids
        ):
            fail("INVALID_RECOMMENDATION")
        return tuple(known[key] for key in result.ranked_activity_ids)
