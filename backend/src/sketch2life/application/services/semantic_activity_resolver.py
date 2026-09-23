"""Application adapter from confirmed anchors to reviewed P1 activity options."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from sketch2life.application.ports.workflow_dependencies import (
    SemanticCatalogPort,
    SemanticCatalogV2Port,
)
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.contracts.schemas.p1_experience import (
    P1ContextOptionV1,
    SemanticAnchorSetV1,
    SemanticMatchEvidenceV1,
)
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    ConfirmedSceneUnderstandingV2,
    SceneConceptV2,
    SemanticActivityMatchV2,
)


@dataclass(frozen=True, slots=True)
class ActivityRecommendation:
    options: tuple[P1ContextOptionV1, ...]
    evidence_by_activity_id: tuple[tuple[str, SemanticMatchEvidenceV1], ...]
    template_by_activity_id: tuple[tuple[str, str], ...]
    rejected_reason_codes: tuple[str, ...] = ()
    v2_match_by_activity_id: tuple[tuple[str, SemanticActivityMatchV2], ...] = ()

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

    def v2_match_for(self, activity_id: str) -> SemanticActivityMatchV2 | None:
        return dict(self.v2_match_by_activity_id).get(activity_id)

    def metadata(self) -> dict[str, object]:
        evidence = self.selected_evidence
        if evidence is None:
            return {
                "status": "NO_MATCH",
                "reason_codes": list(
                    dict.fromkeys(("NO_ELIGIBLE_ACTIVITY", *self.rejected_reason_codes))
                ),
            }
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

    personalized = sorted(
        (row for row in rows if row[4].match_mode != "SAFE_FALLBACK"),
        key=lambda row: (-row[0], -row[1], row[2], row[3]),
    )
    fallbacks = sorted(
        (row for row in rows if row[4].match_mode == "SAFE_FALLBACK"),
        key=lambda row: (-row[0], -row[1], row[2], row[3]),
    )
    rejected: list[str] = []
    selected: tuple[int, int, str, str, SemanticMatchEvidenceV1] | None = None
    for row in (*personalized, *fallbacks):
        fit = compiler.candidate_fit(
            anchor_set,
            template_id=row[3],
            semantic_match=row[4],
        )
        if fit is not None and fit.status == "PASS":
            selected = row
            break
        if fit is None:
            rejected.append("STALE_TEMPLATE")
        else:
            rejected.extend(fit.reason_codes)

    eligible = (selected,) if selected is not None else ()
    activity_ids = tuple(row[2] for row in eligible)
    options = compiler.context_options_for_template_ids(activity_ids, age_months)
    evidence_by_activity = tuple((row[2], row[4]) for row in eligible)
    template_by_activity = tuple((row[2], row[3]) for row in eligible)
    return ActivityRecommendation(
        options=options,
        evidence_by_activity_id=evidence_by_activity,
        template_by_activity_id=template_by_activity,
        rejected_reason_codes=tuple(dict.fromkeys(rejected)),
    )


def resolve_activity_options_v2(
    *,
    anchor_set: SemanticAnchorSetV1,
    age_months: int,
    catalog: SemanticCatalogV2Port,
    compiler: P1ExperienceCompiler,
    narration_text: str = "",
    limit: int = 3,
) -> ActivityRecommendation:
    """Return only reviewed semantic matches from the expanded V2 catalog.

    Age-only fallbacks are deliberately excluded. A missing semantic match is
    safer than presenting an unrelated activity as though it came from the
    child's picture.
    """

    scene = _scene_from_anchor_set(anchor_set, narration_text=narration_text)
    age_band = _age_band(age_months)
    rows: list[tuple[float, int, str, str, SemanticActivityMatchV2]] = []
    rejected: list[str] = []
    for profile in catalog.profiles:
        if profile.age_band != age_band or profile.review_status in {"BLOCKED", "DEPRECATED"}:
            continue
        template_id = compiler.template_id_for_activity_id(profile.activity_id)
        if template_id is None:
            rejected.append("STALE_TEMPLATE")
            continue
        match = catalog.match_scene(scene, profile)
        if match is None or match.match_mode == "AGE_BASELINE_FALLBACK":
            continue
        legacy = catalog.to_legacy_evidence(match)
        fit = compiler.candidate_fit(
            anchor_set,
            template_id=template_id,
            semantic_match=legacy,
        )
        if fit is None:
            rejected.append("STALE_TEMPLATE")
            continue
        if fit.status != "PASS":
            rejected.extend(fit.reason_codes)
            continue
        rows.append(
            (
                match.overall_personalization_score,
                match.semantic_relevance,
                profile.activity_id,
                template_id,
                match,
            )
        )

    ranked = sorted(rows, key=lambda row: (-row[0], -row[1], row[2], row[3]))
    selected: list[tuple[float, int, str, str, SemanticActivityMatchV2]] = []
    seen_families: set[str] = set()
    for row in ranked:
        family_id = row[4].activity_family_id or row[2]
        if family_id in seen_families:
            continue
        selected.append(row)
        seen_families.add(family_id)
        if len(selected) >= max(1, min(limit, 3)):
            break

    activity_ids = tuple(row[2] for row in selected)
    return ActivityRecommendation(
        options=compiler.context_options_for_template_ids(activity_ids, age_months),
        evidence_by_activity_id=tuple(
            (row[2], catalog.to_legacy_evidence(row[4])) for row in selected
        ),
        template_by_activity_id=tuple((row[2], row[3]) for row in selected),
        rejected_reason_codes=tuple(dict.fromkeys(rejected)),
        v2_match_by_activity_id=tuple((row[2], row[4]) for row in selected),
    )


def _scene_from_anchor_set(
    anchor_set: SemanticAnchorSetV1,
    *,
    narration_text: str,
) -> ConfirmedSceneUnderstandingV2:
    anchors = (anchor_set.primary_anchor, *anchor_set.secondary_anchors)
    concepts: list[SceneConceptV2] = []
    seen: set[str] = set()
    for anchor_index, anchor in enumerate(anchors):
        for concept_id in _concept_ids(anchor.normalized_label, anchor.semantic_tags):
            if concept_id in seen:
                continue
            seen.add(concept_id)
            concepts.append(
                SceneConceptV2(
                    concept_id=concept_id,
                    label_vi=anchor.normalized_label,
                    parent_concept_ids=_parent_concepts(concept_id),
                    confidence=anchor.confidence,
                    concept_role=(
                        "PRIMARY_CHILD_INTEREST"
                        if anchor_index == 0
                        else "SECONDARY_VISUAL"
                    ),
                    child_interest_alignment=1.0 if anchor_index == 0 else 0.65,
                    evidence_claim_ids=anchor.provenance.source_claim_ids,
                    source_kinds=("FUSION",) if narration_text.strip() else ("VLM",),
                )
            )
    if not concepts:
        concepts.append(
            SceneConceptV2(
                concept_id="UNCLASSIFIED_SCENE",
                label_vi=anchor_set.primary_anchor.normalized_label,
                confidence=anchor_set.primary_anchor.confidence,
                concept_role="PRIMARY_VISUAL",
                child_interest_alignment=0.5,
                evidence_claim_ids=anchor_set.primary_anchor.provenance.source_claim_ids,
                source_kinds=("VLM",),
            )
        )
    primary = concepts[0]
    scene_source = {
        "anchor_set_id": anchor_set.anchor_set_id,
        "labels": [anchor.normalized_label for anchor in anchors],
        "concepts": [concept.concept_id for concept in concepts],
        "narration": narration_text.strip(),
    }
    scene_hash = sha256(
        json.dumps(scene_source, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    no_audio_hash = sha256(b"NO_AUDIO").hexdigest()
    return ConfirmedSceneUnderstandingV2(
        scene_understanding_id=f"scene-{anchor_set.anchor_set_id}",
        source_image_artifact_ref=anchor_set.source_artifact_id,
        source_image_sha256=anchor_set.source_artifact_sha256,
        source_audio_artifact_ref="none:narration",
        source_audio_sha256=no_audio_hash,
        adult_confirmation_actor=anchor_set.adult_confirmation_actor,
        primary_anchor_label_vi=anchor_set.primary_anchor.normalized_label,
        primary_concept=primary,
        secondary_concepts=tuple(concepts[1:]),
        child_interest_concept_id=primary.concept_id,
        asr_vlm_resolution="ASR_AND_VLM_AGREE" if narration_text.strip() else "VLM_ONLY",
        observed_anchor_labels_vi=tuple(anchor.normalized_label for anchor in anchors),
        observed_entity_labels_vi=tuple(
            anchor.normalized_label for anchor in anchors if anchor.kind == "subject"
        ),
        observed_action_labels_vi=tuple(
            anchor.normalized_label for anchor in anchors if anchor.kind == "action"
        ),
        observed_theme_labels_vi=tuple(
            anchor.normalized_label for anchor in anchors if anchor.kind == "story"
        ),
        asr_transcript_vi=narration_text.strip(),
        supported_modalities=("ASR", "VLM") if narration_text.strip() else ("VLM",),
        normalization_policy_version="topic-semantics-v2",
        scene_sha256=scene_hash,
    )


def _age_band(age_months: int) -> str:
    if age_months < 36:
        return "0-3"
    if age_months < 72:
        return "3-6"
    if age_months < 108:
        return "6-9"
    return "9-12"


def _concept_ids(label: str, tags: tuple[str, ...]) -> tuple[str, ...]:
    text = " ".join((label, *tags)).casefold()
    result: list[str] = []
    if "bướm" in text or "butterfly" in text:
        result.extend(("ANIMAL_BUTTERFLY", "ANIMAL_GENERIC", "ANIMAL_MOVEMENT"))
    elif any(token in text for token in ("chim", "bird", "động vật", "animal", "con vật")):
        result.extend(("ANIMAL_GENERIC", "NATURE_OBSERVATION"))
        if any(token in text for token in ("bay", "flying", "đậu", "perching", "chuyển động")):
            result.append("ANIMAL_MOVEMENT")
    if any(token in text for token in ("hoa", "cây", "lá", "flower", "plant", "leaf")):
        result.extend(("PLANT_STRUCTURE", "NATURE_OBSERVATION"))
    if any(token in text for token in ("mặt trời", "sun", "ánh sáng")):
        result.extend(("SUN_LIGHT", "SCIENCE_OBSERVATION"))
    return tuple(dict.fromkeys(result))


def _parent_concepts(concept_id: str) -> tuple[str, ...]:
    if concept_id in {"ANIMAL_BUTTERFLY", "ANIMAL_MOVEMENT", "ANIMAL_GENERIC"}:
        return ("ANIMAL",)
    if concept_id == "PLANT_STRUCTURE":
        return ("PLANT",)
    return ()


__all__ = [
    "ActivityRecommendation",
    "resolve_activity_options",
    "resolve_activity_options_v2",
]
