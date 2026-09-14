"""Quality, coverage, diversity and revision reports for the curated catalog."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    SemanticActivityProfileV2,
)
from sketch2life.contracts.schemas.workflow_demo import AgeBand
from sketch2life.infrastructure.catalog.curated_catalog import CuratedCatalogV2

_AGE_BANDS: tuple[AgeBand, ...] = ("0-3", "3-6", "6-9", "9-12")


@dataclass(frozen=True, slots=True)
class CatalogQualityPolicyV2:
    minimum_selectable_variants: int = 200
    maximum_selectable_variants: int = 300
    minimum_activity_families: int = 60
    minimum_objective_candidates: int = 2
    tier_a_concepts: tuple[str, ...] = (
        "ANIMAL_GENERIC",
        "PLANT_FLOWER",
        "PEOPLE_FAMILY",
        "COLOR_BASIC",
        "SHAPE_GEOMETRY",
        "MOVEMENT_COORDINATION",
        "COUNTING_NUMBER",
    )
    tier_b_concepts: tuple[str, ...] = (
        "VEHICLE_TRANSPORT",
        "WEATHER_NATURE",
        "SUN_LIGHT",
        "MOON_PHASE",
        "WATER_NATURE",
        "SOUND_MUSIC",
        "NATURE_OBSERVATION",
    )
    tier_c_concepts: tuple[str, ...] = (
        "LANGUAGE_PRINT",
        "PRACTICAL_LIFE",
        "SCIENCE_NATURE",
    )

    def target_for(self, concept_id: str) -> int:
        if concept_id in self.tier_a_concepts:
            return 5
        if concept_id in self.tier_b_concepts:
            return 3
        return 2

    @property
    def scoped_concepts(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (*self.tier_a_concepts, *self.tier_b_concepts, *self.tier_c_concepts)
            )
        )


_DEFAULT_POLICY = CatalogQualityPolicyV2()


@dataclass(frozen=True, slots=True)
class CatalogQualityIssueV2:
    code: str
    message: str
    activity_id: str | None = None
    family_id: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogLintReportV2:
    catalog_revision: str
    selectable_variant_count: int
    activity_family_count: int
    issues: tuple[CatalogQualityIssueV2, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    def model_dump(self) -> dict[str, object]:
        return {
            "catalog_revision": self.catalog_revision,
            "selectable_variant_count": self.selectable_variant_count,
            "activity_family_count": self.activity_family_count,
            "passed": self.passed,
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "activity_id": issue.activity_id,
                    "family_id": issue.family_id,
                }
                for issue in self.issues
            ],
        }


@dataclass(frozen=True, slots=True)
class CoverageQualityGapV2:
    concept_id: str
    age_band: AgeBand
    candidate_count: int
    target_count: int


@dataclass(frozen=True, slots=True)
class CoverageQualityReportV2:
    catalog_revision: str
    selectable_variant_count: int
    activity_family_count: int
    candidate_counts: tuple[tuple[str, AgeBand, int], ...]
    gaps: tuple[CoverageQualityGapV2, ...]

    @property
    def covered_pair_ratio(self) -> float:
        total = len(self.candidate_counts)
        return 0.0 if total == 0 else (total - len(self.gaps)) / total

    def model_dump(self) -> dict[str, object]:
        return {
            "catalog_revision": self.catalog_revision,
            "selectable_variant_count": self.selectable_variant_count,
            "activity_family_count": self.activity_family_count,
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
            "covered_pair_ratio": self.covered_pair_ratio,
        }


@dataclass(frozen=True, slots=True)
class ObjectiveCoverageGapV2:
    objective_id: str
    age_band: AgeBand
    candidate_count: int
    target_count: int


@dataclass(frozen=True, slots=True)
class ObjectiveCoverageReportV2:
    catalog_revision: str
    objective_count: int
    objective_age_pair_count: int
    candidate_counts: tuple[tuple[str, AgeBand, int], ...]
    gaps: tuple[ObjectiveCoverageGapV2, ...]

    @property
    def covered_pair_ratio(self) -> float:
        total = len(self.candidate_counts)
        return 0.0 if total == 0 else (total - len(self.gaps)) / total

    def model_dump(self) -> dict[str, object]:
        return {
            "catalog_revision": self.catalog_revision,
            "objective_count": self.objective_count,
            "objective_age_pair_count": self.objective_age_pair_count,
            "candidate_counts": [
                {
                    "objective_id": objective_id,
                    "age_band": age_band,
                    "candidate_count": count,
                }
                for objective_id, age_band, count in self.candidate_counts
            ],
            "gaps": [
                {
                    "objective_id": gap.objective_id,
                    "age_band": gap.age_band,
                    "candidate_count": gap.candidate_count,
                    "target_count": gap.target_count,
                }
                for gap in self.gaps
            ],
            "covered_pair_ratio": self.covered_pair_ratio,
        }


@dataclass(frozen=True, slots=True)
class ActivityDiversityReportV2:
    catalog_revision: str
    recommendation_count: int
    distinct_activity_count: int
    distinct_family_count: int
    top_activity_share: float
    top_family_share: float
    immediate_repeat_rate: float

    def model_dump(self) -> dict[str, object]:
        return {
            "catalog_revision": self.catalog_revision,
            "recommendation_count": self.recommendation_count,
            "distinct_activity_count": self.distinct_activity_count,
            "distinct_family_count": self.distinct_family_count,
            "top_activity_share": self.top_activity_share,
            "top_family_share": self.top_family_share,
            "immediate_repeat_rate": self.immediate_repeat_rate,
        }


@dataclass(frozen=True, slots=True)
class CatalogDiffV2:
    from_revision: str
    to_revision: str
    added_activity_ids: tuple[str, ...]
    removed_activity_ids: tuple[str, ...]
    changed_activity_ids: tuple[str, ...]
    added_family_ids: tuple[str, ...]
    removed_family_ids: tuple[str, ...]

    def model_dump(self) -> dict[str, object]:
        return {
            "from_revision": self.from_revision,
            "to_revision": self.to_revision,
            "added_activity_ids": list(self.added_activity_ids),
            "removed_activity_ids": list(self.removed_activity_ids),
            "changed_activity_ids": list(self.changed_activity_ids),
            "added_family_ids": list(self.added_family_ids),
            "removed_family_ids": list(self.removed_family_ids),
        }


def lint_curated_catalog_v2(
    catalog: CuratedCatalogV2,
    *,
    baseline_profiles: Iterable[SemanticActivityProfileV2] = (),
    policy: CatalogQualityPolicyV2 | None = None,
) -> CatalogLintReportV2:
    policy = policy or _DEFAULT_POLICY
    issues: list[CatalogQualityIssueV2] = []
    variants = catalog.variants
    baseline = tuple(baseline_profiles)
    total_variant_count = len(variants) + len(baseline)
    family_ids = {
        *catalog.by_family_id(),
        *(profile.activity_family_id for profile in baseline if profile.activity_family_id),
    }
    if not (
        policy.minimum_selectable_variants
        <= total_variant_count
        <= policy.maximum_selectable_variants
    ):
        issues.append(
            CatalogQualityIssueV2(
                "CATALOG_SIZE_OUT_OF_RANGE",
                (
                    f"expected {policy.minimum_selectable_variants}-"
                    f"{policy.maximum_selectable_variants} variants"
                ),
            )
        )
    if len(family_ids) < policy.minimum_activity_families:
        issues.append(
            CatalogQualityIssueV2(
                "ACTIVITY_FAMILY_COUNT_BELOW_TARGET",
                f"expected at least {policy.minimum_activity_families} families",
            )
        )
    objective_counts: Counter[tuple[str, AgeBand]] = Counter()
    for variant in variants:
        for objective_id in variant.objective_ids:
            objective_counts[(objective_id, variant.age_band)] += 1
        if not variant.material_option_ids:
            issues.append(
                CatalogQualityIssueV2(
                    "MATERIALS_MISSING",
                    "variant must provide at least one material",
                    variant.activity_id,
                    variant.activity_family_id,
                )
            )
        if len(variant.material_option_ids) < 2:
            issues.append(
                CatalogQualityIssueV2(
                    "MATERIAL_SUBSTITUTE_MISSING",
                    "variant must provide an ideal material and a safe substitute",
                    variant.activity_id,
                    variant.activity_family_id,
                )
            )
        if not variant.safety_vi:
            issues.append(
                CatalogQualityIssueV2(
                    "SAFETY_REVIEW_MISSING",
                    "variant must provide reviewed safety text",
                    variant.activity_id,
                    variant.activity_family_id,
                )
            )
        if len(variant.action_vi.strip()) < 12 or len(variant.challenge_vi.strip()) < 12:
            issues.append(
                CatalogQualityIssueV2(
                    "AGE_ADAPTATION_TOO_THIN",
                    "age variant must contain a concrete action and challenge",
                    variant.activity_id,
                    variant.activity_family_id,
                )
            )
    objective_ids = sorted({objective_id for objective_id, _ in objective_counts})
    for objective_id in objective_ids:
        for age_band in _AGE_BANDS:
            if objective_counts[(objective_id, age_band)] < policy.minimum_objective_candidates:
                issues.append(
                    CatalogQualityIssueV2(
                        "OBJECTIVE_AGE_COVERAGE_BELOW_TARGET",
                        (
                            f"objective {objective_id} has "
                            f"{objective_counts[(objective_id, age_band)]} candidates "
                            f"for {age_band}"
                        ),
                    )
                )
    return CatalogLintReportV2(
        catalog_revision=catalog.catalog_revision,
        selectable_variant_count=total_variant_count,
        activity_family_count=len(family_ids),
        issues=tuple(issues),
    )


def build_coverage_quality_report(
    profiles: Iterable[SemanticActivityProfileV2],
    *,
    policy: CatalogQualityPolicyV2 | None = None,
) -> CoverageQualityReportV2:
    policy = policy or _DEFAULT_POLICY
    profile_items = tuple(profiles)
    counts: Counter[tuple[str, AgeBand]] = Counter()
    for profile in profile_items:
        for concept_id in profile.concept_ids:
            if not concept_id.startswith("ACTIVITY_") and concept_id in policy.scoped_concepts:
                counts[(concept_id, profile.age_band)] += 1
    ordered = tuple(
        (concept_id, age_band, counts[(concept_id, age_band)])
        for concept_id in policy.scoped_concepts
        for age_band in _AGE_BANDS
    )
    gaps = tuple(
        CoverageQualityGapV2(
            concept_id=concept_id,
            age_band=age_band,
            candidate_count=count,
            target_count=policy.target_for(concept_id),
        )
        for concept_id, age_band, count in ordered
        if count < policy.target_for(concept_id)
    )
    revisions = {profile.catalog_revision for profile in profile_items}
    revision = next(iter(revisions), "unknown") if len(revisions) == 1 else "mixed"
    return CoverageQualityReportV2(
        catalog_revision=revision,
        selectable_variant_count=len(profile_items),
        activity_family_count=len(
            {profile.activity_family_id for profile in profile_items if profile.activity_family_id}
        ),
        candidate_counts=ordered,
        gaps=gaps,
    )


def build_objective_age_coverage_report(
    catalog: CuratedCatalogV2,
    *,
    minimum_candidates: int = 2,
) -> ObjectiveCoverageReportV2:
    counts: Counter[tuple[str, AgeBand]] = Counter()
    for variant in catalog.variants:
        for objective_id in variant.objective_ids:
            counts[(objective_id, variant.age_band)] += 1
    objective_ids = tuple(sorted({objective_id for objective_id, _ in counts}))
    ordered = tuple(
        (objective_id, age_band, counts[(objective_id, age_band)])
        for objective_id in objective_ids
        for age_band in _AGE_BANDS
    )
    gaps = tuple(
        ObjectiveCoverageGapV2(
            objective_id=objective_id,
            age_band=age_band,
            candidate_count=count,
            target_count=minimum_candidates,
        )
        for objective_id, age_band, count in ordered
        if count < minimum_candidates
    )
    return ObjectiveCoverageReportV2(
        catalog_revision=catalog.catalog_revision,
        objective_count=len(objective_ids),
        objective_age_pair_count=len(ordered),
        candidate_counts=ordered,
        gaps=gaps,
    )


def build_activity_diversity_report(
    profiles: Iterable[SemanticActivityProfileV2],
    selected_activity_ids: Iterable[str] = (),
) -> ActivityDiversityReportV2:
    profile_items = tuple(profiles)
    by_id = {profile.activity_id: profile for profile in profile_items}
    selected = tuple(selected_activity_ids)
    activity_counts = Counter(selected)
    family_counts = Counter(
        by_id[activity_id].activity_family_id
        for activity_id in selected
        if activity_id in by_id
    )
    repeats = sum(left == right for left, right in zip(selected, selected[1:], strict=False))
    recommendation_count = len(selected)
    return ActivityDiversityReportV2(
        catalog_revision=(
            next(iter({profile.catalog_revision for profile in profile_items}), "unknown")
            if profile_items
            else "unknown"
        ),
        recommendation_count=recommendation_count,
        distinct_activity_count=len(activity_counts),
        distinct_family_count=len(family_counts),
        top_activity_share=(
            max(activity_counts.values(), default=0) / recommendation_count
            if recommendation_count
            else 0.0
        ),
        top_family_share=(
            max(family_counts.values(), default=0) / recommendation_count
            if recommendation_count
            else 0.0
        ),
        immediate_repeat_rate=(
            repeats / max(1, recommendation_count - 1)
            if recommendation_count > 1
            else 0.0
        ),
    )


def diff_catalogs(
    before: Iterable[SemanticActivityProfileV2],
    after: Iterable[SemanticActivityProfileV2],
) -> CatalogDiffV2:
    old = {profile.activity_id: profile for profile in before}
    new = {profile.activity_id: profile for profile in after}
    added = tuple(sorted(set(new) - set(old)))
    removed = tuple(sorted(set(old) - set(new)))
    changed = tuple(
        sorted(
            activity_id
            for activity_id in set(old) & set(new)
            if old[activity_id].model_dump(mode="json")
            != new[activity_id].model_dump(mode="json")
        )
    )
    old_families = {profile.activity_family_id for profile in old.values()}
    new_families = {profile.activity_family_id for profile in new.values()}
    old_revisions = {profile.catalog_revision for profile in old.values()}
    new_revisions = {profile.catalog_revision for profile in new.values()}
    return CatalogDiffV2(
        from_revision=next(iter(old_revisions), "unknown") if len(old_revisions) == 1 else "mixed",
        to_revision=next(iter(new_revisions), "unknown") if len(new_revisions) == 1 else "mixed",
        added_activity_ids=added,
        removed_activity_ids=removed,
        changed_activity_ids=changed,
        added_family_ids=tuple(sorted(new_families - old_families)),
        removed_family_ids=tuple(sorted(old_families - new_families)),
    )


__all__ = [
    "ActivityDiversityReportV2",
    "CatalogDiffV2",
    "CatalogLintReportV2",
    "CatalogQualityIssueV2",
    "CatalogQualityPolicyV2",
    "CoverageQualityGapV2",
    "CoverageQualityReportV2",
    "ObjectiveCoverageGapV2",
    "ObjectiveCoverageReportV2",
    "build_activity_diversity_report",
    "build_coverage_quality_report",
    "build_objective_age_coverage_report",
    "diff_catalogs",
    "lint_curated_catalog_v2",
]
