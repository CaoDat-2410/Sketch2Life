"""Bounded11 broad discovery source for BE1 CMD-59; no readiness/material filters."""

from dataclasses import dataclass, replace

from sketch2life.application.learning_content_eligibility import PublishedContent
from sketch2life.application.ports.activity_execution import (
    Actor,
    DiscoveryBoundary,
    DiscoveryQuery,
    Recommender,
)
from sketch2life.contracts.schemas.learning_content import ContentWrite
from sketch2life.domain.activity_execution.model import Definition, fail, text
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError


def map_published_definition(definition: Definition, published: PublishedContent) -> Definition:
    """Join only exact reviewed asset reference, not title/editorial-note inference.
    Resolver must authenticate full definition bytes against definition_ref and
    CURRENT publication/rights; this helper isn't a replacement for held authority.
    """
    definition = replace(definition)
    body = ContentWrite.model_validate(published.content.model_dump(mode="python"), strict=True)
    source = definition.source_ref
    asset = definition.definition_ref
    if (
        (source.ref, source.version, source.hash)
        != (published.record_id, published.version, published.hash)
        or body.content_kind != "activity"
        or not any(
            (item.ref, item.version, item.hash) == (asset.ref, asset.version, asset.hash)
            for item in body.asset_refs
        )
        or (definition.age_min_months, definition.age_max_months)
        != (body.age_eligibility.min_months, body.age_eligibility.max_months)
        or definition.title != body.title
    ):
        fail("SOURCE_MISMATCH")
    return definition


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    rows: tuple[Definition, ...]
    warnings: tuple[tuple[ExactRef, tuple[str, ...]], ...]
    recommendations: tuple[tuple[ExactRef, str], ...]
    recommendation_status: str  # not_requested/available/unavailable


class ActivityDiscovery:
    def __init__(self, boundary: DiscoveryBoundary, recommender: Recommender | None = None) -> None:
        self.boundary, self.recommender = boundary, recommender

    def discover(
        self, actor: Actor, query: DiscoveryQuery, *, recommend: bool = False
    ) -> DiscoveryResult:
        actor, query = replace(actor), replace(query)
        if type(recommend) is not bool:
            fail("INVALID_QUERY")
        try:
            with self.boundary.guard(actor) as access:
                raw = access.candidates(query)
                if type(raw) is not tuple or len(raw) > 100:
                    fail("INVALID_CATALOG")
                rows = tuple(replace(row) for row in raw)
                if len({(r.source_ref.ref, r.source_ref.version) for r in rows}) != len(rows):
                    fail("INVALID_CATALOG")
                # All requested topics, not merely the first topic. Exact months,
                # not legacy age buckets. No readiness/material/history fields.
                rows = tuple(
                    row
                    for row in rows
                    if set(query.topic_ids) & set(row.topic_ids)
                    and row.age_min_months <= query.age_months <= row.age_max_months
                )[: query.limit]
                warnings = tuple((r.source_ref, access.warnings(r)) for r in rows)
                for _, values in warnings:
                    if type(values) is not tuple or len(values) > 64:
                        fail("INVALID_CATALOG")
                    for value in values:
                        text(value, 200)
                ranked: tuple[tuple[ExactRef, str], ...] = ()
                status = "not_requested"
                if recommend:
                    status = "unavailable"
                    if self.recommender is not None:
                        try:
                            proposed = self.recommender.rank(query, rows)
                            if type(proposed) is not tuple or len(proposed) > len(rows):
                                fail("INVALID_RECOMMENDATION")
                            known = {r.source_ref for r in rows}
                            seen: set[ExactRef] = set()
                            for ref, reason in proposed:
                                if ref not in known or ref in seen:
                                    fail("INVALID_RECOMMENDATION")
                                text(reason, 200)
                                seen.add(ref)
                            ranked = proposed
                            status = "available"
                        except Exception:
                            ranked = ()
                access.check()
                return DiscoveryResult(rows, warnings, ranked, status)
        except VideoError:
            raise
        except Exception:
            fail("DEPENDENCY_UNAVAILABLE")
