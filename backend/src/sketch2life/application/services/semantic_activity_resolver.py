"""Application adapter from confirmed anchors to reviewed P1 activity options."""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.application.ports.workflow_dependencies import SemanticCatalogPort
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.contracts.schemas.p1_experience import (
    P1ContextOptionV1,
    SemanticAnchorSetV1,
    SemanticMatchEvidenceV1,
)


@dataclass(frozen=True, slots=True)
class ActivityRecommendation:
    options: tuple[P1ContextOptionV1, ...]
    evidence_by_activity_id: tuple[tuple[str, SemanticMatchEvidenceV1], ...]
    template_by_activity_id: tuple[tuple[str, str], ...]

    @property
    def selected_evidence(self) -> SemanticMatchEvidenceV1 | None:
        return self.evidence_by_activity_id[0][1] if self.evidence_by_activity_id else None

    @property
    def selected_template_id(self) -> str | None:
        return self.template_by_activity_id[0][1] if self.template_by_activity_id else None

    def evidence_for(self, activity_id: str) -> SemanticMatchEvidenceV1 | None:
        return dict(self.evidence_by_activity_id).get(activity_id)

    def template_for(self, activity_id: str) -> str | None:
        return dict(self.template_by_activity_id).get(activity_id)

    def metadata(self) -> dict[str, object]:
        evidence = self.selected_evidence
        if evidence is None:
            return {"status": "NO_MATCH", "reason_codes": ["NO_ELIGIBLE_ACTIVITY"]}
        status = "EXPANDED" if evidence.match_mode == "SAFE_FALLBACK" else "PERSONALIZED"
        return {
            "status": status,
            "match_mode": evidence.match_mode,
            "profile_id": evidence.profile_id,
            "profile_version": evidence.profile_version,
            "score": evidence.score,
            "reason_codes": list(evidence.reason_codes),
            "fallback_reason": evidence.fallback_reason,
            "activity_id": self.options[0].activity_ref.id if self.options else None,
        }


def resolve_activity_options(
    *,
    anchor_set: SemanticAnchorSetV1,
    age_months: int,
    catalog: SemanticCatalogPort,
    compiler: P1ExperienceCompiler,
) -> ActivityRecommendation:
    """Resolve reviewed semantic matches before exact P1 compilation.

    The V1 semantic catalog already owns the reviewed exact/alias/baseline rules.
    Semantic tags are derived by the bounded topic adapter and remain tied to the
    original confirmed claim IDs.
    """

    rows: list[tuple[int, int, str, str, SemanticMatchEvidenceV1]] = []
    for profile in catalog.profiles:
        if not profile.age_months_min <= age_months <= profile.age_months_max:
            continue
        template_id = compiler.template_id_for_activity_id(profile.activity_id)
        if template_id is None:
            continue
        evidence = catalog.match(anchor_set, profile)
        if evidence is None:
            continue
        mode_rank = {"EXACT": 3, "ALIAS": 2, "SAFE_FALLBACK": 1}[evidence.match_mode]
        rows.append((mode_rank, evidence.score, profile.activity_id, template_id, evidence))

    personalized = [row for row in rows if row[4].match_mode != "SAFE_FALLBACK"]
    eligible = personalized or [row for row in rows if row[4].match_mode == "SAFE_FALLBACK"][:1]
    eligible.sort(key=lambda row: (-row[0], -row[1], row[2], row[3]))
    activity_ids = tuple(row[2] for row in eligible)
    options = compiler.context_options_for_template_ids(activity_ids, age_months)
    evidence_by_activity = tuple((row[2], row[4]) for row in eligible)
    template_by_activity = tuple((row[2], row[3]) for row in eligible)
    return ActivityRecommendation(
        options=options,
        evidence_by_activity_id=evidence_by_activity,
        template_by_activity_id=template_by_activity,
    )


__all__ = ["ActivityRecommendation", "resolve_activity_options"]
