"""Coverage measurement for the curated activity catalog.

This module never creates activities. It measures whether the reviewed catalog
has enough candidates after concept and age-band partitioning.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sketch2life.contracts.schemas.workflow_demo import AgeBand
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    ActivitySemanticCatalogV2,
)


@dataclass(frozen=True, slots=True)
class ActivityCoverageGapV2:
    concept_id: str
    age_band: AgeBand
    candidate_count: int
    target_count: int


@dataclass(frozen=True, slots=True)
class ActivityCoverageReportV2:
    catalog_revision: str
    profile_count: int
    unmapped_profile_count: int
    minimum_candidates_per_concept_age: int
    candidate_counts: tuple[tuple[str, AgeBand, int], ...]
    gaps: tuple[ActivityCoverageGapV2, ...]

    @property
    def covered_pairs(self) -> int:
        return len(self.candidate_counts) - len(self.gaps)

    @property
    def coverage_ratio(self) -> float:
        if not self.candidate_counts:
            return 0.0
        return self.covered_pairs / len(self.candidate_counts)

    def model_dump(self) -> dict[str, object]:
        return {
            "catalog_revision": self.catalog_revision,
            "profile_count": self.profile_count,
            "unmapped_profile_count": self.unmapped_profile_count,
            "minimum_candidates_per_concept_age": self.minimum_candidates_per_concept_age,
            "candidate_counts": [
                {
                    "concept_id": concept_id,
                    "age_band": age_band,
                    "candidate_count": count,
                }
                for concept_id, age_band, count in self.candidate_counts
            ],
            "gaps": [
                {
                    "concept_id": gap.concept_id,
                    "age_band": gap.age_band,
                    "candidate_count": gap.candidate_count,
                    "target_count": gap.target_count,
                }
                for gap in self.gaps
            ],
            "coverage_ratio": self.coverage_ratio,
        }


def build_activity_coverage_report(
    catalog: ActivitySemanticCatalogV2,
    *,
    minimum_candidates_per_concept_age: int = 3,
) -> ActivityCoverageReportV2:
    if minimum_candidates_per_concept_age < 1:
        raise ValueError("minimum_candidates_per_concept_age must be positive")

    counts: Counter[tuple[str, AgeBand]] = Counter()
    unmapped_profile_count = 0
    for profile in catalog.profiles:
        concept_ids = tuple(
            concept_id
            for concept_id in profile.concept_ids
            if not concept_id.startswith("ACTIVITY_")
        )
        if not concept_ids:
            unmapped_profile_count += 1
        for concept_id in concept_ids:
            counts[(concept_id, profile.age_band)] += 1

    ordered_counts = tuple(
        (concept_id, age_band, count)
        for (concept_id, age_band), count in sorted(counts.items())
    )
    gaps = tuple(
        ActivityCoverageGapV2(
            concept_id=concept_id,
            age_band=age_band,
            candidate_count=count,
            target_count=minimum_candidates_per_concept_age,
        )
        for concept_id, age_band, count in ordered_counts
        if count < minimum_candidates_per_concept_age
    )
    revision = next(
        (profile.catalog_revision for profile in catalog.profiles),
        "unknown",
    )
    return ActivityCoverageReportV2(
        catalog_revision=revision,
        profile_count=len(catalog.profiles),
        unmapped_profile_count=unmapped_profile_count,
        minimum_candidates_per_concept_age=minimum_candidates_per_concept_age,
        candidate_counts=ordered_counts,
        gaps=gaps,
    )


__all__ = [
    "ActivityCoverageGapV2",
    "ActivityCoverageReportV2",
    "build_activity_coverage_report",
]
