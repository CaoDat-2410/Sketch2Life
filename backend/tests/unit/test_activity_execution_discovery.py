"""Discovery/mapping/ranking candidate parity, not real publication or provider."""

from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import Mock

import pytest

from sketch2life.application.activity_discovery import ActivityDiscovery, map_published_definition
from sketch2life.application.learning_content_eligibility import PublishedContent
from sketch2life.application.ports.activity_execution import DiscoveryQuery
from sketch2life.contracts.schemas.activity_ranking import (
    ActivityRankingCandidateV1,
    ActivityRankingResultV1,
)
from sketch2life.contracts.schemas.learning_content import ContentWrite
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.infrastructure.activity_execution.ranking import LegacyRankingAdapter
from tests.activity_execution_fixtures import actor, definition, ref


def query(**changes):
    return DiscoveryQuery(
        **dict(topic_ids=("plants", "colors"), age_months=48, preferences=(), limit=10) | changes
    )


class Boundary:
    def __init__(self, rows):
        self.rows = rows
        self.denied = False

    @contextmanager
    def guard(self, a):
        yield self

    def candidates(self, q):
        return self.rows

    def warnings(self, row):
        return ("materials_not_yet_confirmed", "readiness_unknown")

    def check(self):
        if self.denied:
            raise VideoError("ACTIVITY_FORBIDDEN")


@pytest.mark.parametrize("age,expected", [(35, 0), (36, 1), (48, 1), (100, 1), (101, 0)])
def test_exact_age_not_old_age_buckets_and_warnings_not_filter(age, expected):
    result = ActivityDiscovery(Boundary((definition(),))).discover(actor(), query(age_months=age))
    assert len(result.rows) == expected
    if expected:
        assert "readiness_unknown" in result.warnings[0][1]
    assert result.recommendation_status == "not_requested"


def test_full_topic_not_first_only_and_no_material_or_readiness_hardfilter():
    a = definition(topic_ids=("colors",))
    b = definition(source_ref=ref("second"), topic_ids=("plants",))
    result = ActivityDiscovery(Boundary((a, b))).discover(actor(), query())
    assert result.rows == (a, b)
    assert not {"readiness", "history", "materials"} & set(query().__dataclass_fields__)


@pytest.mark.parametrize("value", [0, True, 101, "10"])
def test_discovery_bound_explicit(value):
    with pytest.raises(VideoError):
        query(limit=value)


def test_recommendations_source_subset_no_instructions_or_teacher_choice():
    source = definition()
    ranker = Mock(rank=Mock(return_value=((source.source_ref, "candidate preference reason"),)))
    result = ActivityDiscovery(Boundary((source,)), ranker).discover(
        actor(), query(), recommend=True
    )
    assert result.rows == (source,) and result.recommendation_status == "available"
    assert result.recommendations[0][0] == source.source_ref
    assert not hasattr(result, "assignment")
    missing = ActivityDiscovery(Boundary((source,))).discover(actor(), query(), recommend=True)
    assert missing.recommendation_status == "unavailable" and missing.rows == (source,)


@pytest.mark.parametrize(
    "output",
    [
        ((ref("foreign"), "reason"),),
        ((ref("activity"), "a"), (ref("activity"), "b")),
        ((ref("activity"), ""),),
        "raw",
    ],
)
def test_foreign_duplicate_malformed_recommendation_unavailable_not_hidden_fallback(output):
    row = definition()
    result = ActivityDiscovery(Boundary((row,)), Mock(rank=Mock(return_value=output))).discover(
        actor(), query(), recommend=True
    )
    assert result.recommendation_status == "unavailable" and not result.recommendations
    assert result.rows == (row,)


def published():
    row = definition()
    body = ContentWrite.model_validate(
        {
            "content_kind": "activity",
            "title": row.title,
            "asset_refs": (row.definition_ref.material(),),
            "source_refs": (ref("authored.source").material(),),
            "age_eligibility": {"age_policy_ref": "age", "min_months": 36, "max_months": 100},
            "purpose_codes": ("learning",),
            "editorial_note": "Not trusted instructions/safety",
            "content_policy_ref": "content.policy",
        }
    )
    return PublishedContent(
        "activity", "school", 1, 5, "a" * 64, body, ("safety.review", "pedagogy.review"), "policy"
    )


def test_reviewed12_exact_definition_asset_mapping_no_editorial_inference():
    row = definition()
    assert map_published_definition(row, published()) == row
    assert row.instructions != published().content.editorial_note


@pytest.mark.parametrize(
    "field,value", [("record_id", "foreign"), ("version", 2), ("hash", "f" * 64)]
)
def test_publication_ref_namespace_exact(field, value):
    with pytest.raises(VideoError, match="SOURCE_MISMATCH"):
        map_published_definition(definition(), replace(published(), **{field: value}))


def test_missing_definition_asset_not_guessed_from_generic_title_or_note():
    p = published()
    p = replace(p, content=p.content.model_copy(update={"asset_refs": ()}))
    with pytest.raises(VideoError, match="SOURCE_MISMATCH"):
        map_published_definition(definition(), p)


def test_legacy_ranker_adapter_explicit_exact_aliases_preserve_full_topic_age_preference():
    row = definition()
    candidate = ActivityRankingCandidateV1(
        activity_id="ACT-0001",
        title_vi=row.title,
        summary_vi="Candidate",
        match_reason_vi="Reviewed candidate reason",
        concept_ids=("plants",),
        objective_ids=("objective",),
    )
    provider = Mock(
        rank=Mock(
            return_value=ActivityRankingResultV1(
                request_id="request", ranked_activity_ids=("ACT-0001",)
            )
        )
    )
    adapter = LegacyRankingAdapter(
        provider,
        ((row.source_ref, candidate),),
        request_ids=lambda: "request",
        topic_label=lambda topics: ",".join(topics),
    )
    assert adapter.rank(query(preferences=("plants",)), (row,)) == (
        (row.source_ref, "Reviewed candidate reason"),
    )
    request = provider.rank.call_args.args[0]
    assert request.age_months == 48 and request.topic_label_vi == "plants,colors"
    assert request.confirmed_interest_ids == ("plants",)
    provider.rank.return_value = ActivityRankingResultV1(
        request_id="request", ranked_activity_ids=("ACT-9999",)
    )
    with pytest.raises(VideoError, match="INVALID_RECOMMENDATION"):
        adapter.rank(query(), (row,))


def test_current_authority_denial_after_ranking_does_not_leak_catalog():
    boundary = Boundary((definition(),))
    boundary.denied = True
    with pytest.raises(VideoError, match="FORBIDDEN"):
        ActivityDiscovery(boundary).discover(actor(), query())
