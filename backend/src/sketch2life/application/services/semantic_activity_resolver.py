"""Application adapter from confirmed anchors to reviewed P1 activity options."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from hashlib import sha256

from sketch2life.application.ports.workflow_dependencies import (
    SemanticCatalogPort,
    SemanticCatalogV2Port,
)
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.contracts.schemas.child_learning_profile import (
    AdultConfirmedProgressV1,
    ChildLearningProfileContextV1,
)
from sketch2life.contracts.schemas.p1_experience import (
    P1ContextOptionV1,
    SemanticAnchorSetV1,
    SemanticMatchEvidenceV1,
)
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    ConfirmedSceneUnderstandingV2,
    SceneConceptV2,
    SemanticActivityMatchV2,
    SemanticActivityProfileV2,
)

ActivityOptionRow = tuple[
    float,
    int,
    str,
    str,
    SemanticActivityMatchV2,
    tuple[str, ...],
]


@dataclass(frozen=True, slots=True)
class ActivityRecommendation:
    options: tuple[P1ContextOptionV1, ...]
    evidence_by_activity_id: tuple[tuple[str, SemanticMatchEvidenceV1], ...]
    template_by_activity_id: tuple[tuple[str, str], ...]
    rejected_reason_codes: tuple[str, ...] = ()
    v2_match_by_activity_id: tuple[tuple[str, SemanticActivityMatchV2], ...] = ()
    personalization_reasons_by_activity_id: tuple[tuple[str, tuple[str, ...]], ...] = ()
    progress_evidence_by_activity_id: tuple[
        tuple[str, tuple[AdultConfirmedProgressV1, ...]], ...
    ] = ()
    excluded_by_profile: tuple[tuple[str, str], ...] = ()

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

    def personalization_reasons_for(self, activity_id: str) -> tuple[str, ...]:
        return dict(self.personalization_reasons_by_activity_id).get(activity_id, ())

    def progress_evidence_for(self, activity_id: str) -> tuple[AdultConfirmedProgressV1, ...]:
        return dict(self.progress_evidence_by_activity_id).get(activity_id, ())

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
    limit: int | None = 3,
    child_profile: ChildLearningProfileContextV1 | None = None,
    candidate_activity_ids: tuple[str, ...] = (),
    require_authored_readiness: bool = False,
    order_by_relevance: bool = True,
    complete_discovery: bool = False,
    adult_participating: bool = False,
    caregiver_participating: bool = False,
) -> ActivityRecommendation:
    """Return only reviewed semantic matches from the expanded V2 catalog.

    Age-only fallbacks are deliberately excluded. A missing semantic match is
    safer than presenting an unrelated activity as though it came from the
    child's picture.
    """

    scene = _scene_from_anchor_set(
        anchor_set,
        narration_text=narration_text,
        complete_discovery=complete_discovery,
    )
    age_band = _age_band(age_months)
    rows: list[ActivityOptionRow] = []
    rejected: list[str] = []
    excluded_by_profile: list[tuple[str, str]] = []
    progress_evidence: dict[str, tuple[AdultConfirmedProgressV1, ...]] = {}
    candidate_allowlist = set(candidate_activity_ids)
    for profile in catalog.profiles:
        if profile.age_band != age_band or profile.review_status in {"BLOCKED", "DEPRECATED"}:
            continue
        if candidate_allowlist and profile.activity_id not in candidate_allowlist:
            continue
        template_id = compiler.template_id_for_activity_id(profile.activity_id)
        if template_id is None:
            rejected.append("STALE_TEMPLATE")
            continue
        matching_profile = (
            _complete_discovery_profile(profile) if complete_discovery else profile
        )
        match = catalog.match_scene(scene, matching_profile)
        if match is None or match.match_mode == "AGE_BASELINE_FALLBACK":
            continue
        template = compiler.template_for_activity_id(profile.activity_id)
        if template is None:
            rejected.append("STALE_TEMPLATE")
            continue
        if complete_discovery and not (
            template.age_months_min <= age_months <= template.age_months_max
        ):
            continue
        if (
            require_authored_readiness
            and not complete_discovery
            and template.readiness_metadata_status != "AUTHORED"
        ):
            rejected.append("READINESS_METADATA_MISSING")
            continue
        if (
            child_profile is not None
            and not complete_discovery
            and template.readiness_metadata_status != "AUTHORED"
        ):
            rejected.append("READINESS_METADATA_MISSING")
            continue
        activity_concepts = set(profile.concept_ids) | set(profile.parent_concept_ids)
        matched_dislikes = (
            _expanded_profile_concepts(child_profile.dislikes) & activity_concepts
            if child_profile is not None
            else set()
        )
        if complete_discovery:
            if not adult_participating:
                excluded_by_profile.append((profile.activity_id, "ADULT_PARTICIPATION_REQUIRED"))
                continue
            if "CAREGIVER_PRESENT" in template.policy_constraints and not (
                caregiver_participating or adult_participating
            ):
                excluded_by_profile.append((profile.activity_id, "SUPERVISION_UNAVAILABLE"))
                continue
        if child_profile is not None and not complete_discovery:
            supervision_rank = {"NONE": 0, "NEARBY": 1, "DIRECT": 2}
            if supervision_rank[template.minimum_supervision] > supervision_rank[
                child_profile.adult_supervision_available
            ]:
                excluded_by_profile.append((profile.activity_id, "SUPERVISION_UNAVAILABLE"))
                continue
            confirmed_activity_ids = {
                item.activity_id for item in child_profile.adult_confirmed_progress
            }
            if not set(template.prerequisite_activity_ids) <= confirmed_activity_ids:
                excluded_by_profile.append((profile.activity_id, "PREREQUISITE_NOT_CONFIRMED"))
                continue
            required_readiness = set(template.readiness_ids)
            if required_readiness and child_profile.readiness_ids is None:
                excluded_by_profile.append((profile.activity_id, "READINESS_PROFILE_REQUIRED"))
                continue
            known_readiness = set(child_profile.readiness_ids or ())
            if not required_readiness <= known_readiness:
                excluded_by_profile.append((profile.activity_id, "READINESS_NOT_CONFIRMED"))
                continue
            if child_profile.available_material_option_ids is None:
                excluded_by_profile.append((profile.activity_id, "MATERIAL_PROFILE_REQUIRED"))
                continue
            if not compiler.materials_available_for_template(
                template, child_profile.available_material_option_ids
            ):
                excluded_by_profile.append((profile.activity_id, "MATERIAL_NOT_AVAILABLE"))
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
        reasons: list[str] = []
        score_adjustment = 0.0
        if child_profile is not None:
            matched_interests = (
                _expanded_profile_concepts(child_profile.interests) & activity_concepts
            )
            if matched_interests:
                score_adjustment += 0.12
                reasons.append("EXPLICIT_INTEREST_MATCH")
            if matched_dislikes:
                score_adjustment -= 0.12
                reasons.append("EXPLICIT_AVOIDANCE_MATCH")
            activity_objective_ids = {
                profile.primary_objective_id,
                *profile.secondary_objective_ids,
            }
            matched_progress = tuple(
                item
                for item in child_profile.adult_confirmed_progress
                if item.objective_id in activity_objective_ids
            )
            if matched_progress:
                score_adjustment += 0.05
                reasons.append("ADULT_CONFIRMED_PROGRESS_MATCH")
                progress_evidence[profile.activity_id] = matched_progress
            support_match = _support_matches(
                child_profile, template.interaction_mode, profile.primary_objective_id
            )
            if support_match:
                score_adjustment += 0.03
                reasons.append("EXPLICIT_LEARNING_SUPPORT_MATCH")
        adjusted_match = match.model_copy(
            update={
                "overall_personalization_score": min(
                    0.99, max(0.0, match.overall_personalization_score + score_adjustment)
                ),
                "reason_codes": tuple((*match.reason_codes, *reasons)),
            }
        )
        rows.append(
            (
                adjusted_match.overall_personalization_score,
                match.semantic_relevance,
                profile.activity_id,
                template_id,
                adjusted_match,
                tuple(reasons),
            )
        )

    selected = _select_activity_rows(
        rows,
        limit=limit,
        order_by_relevance=order_by_relevance,
        deduplicate_families=not complete_discovery,
    )
    activity_ids = tuple(row[2] for row in selected)
    return ActivityRecommendation(
        options=compiler.context_options_for_template_ids(activity_ids, age_months),
        evidence_by_activity_id=tuple(
            (row[2], catalog.to_legacy_evidence(row[4])) for row in selected
        ),
        template_by_activity_id=tuple((row[2], row[3]) for row in selected),
        rejected_reason_codes=tuple(dict.fromkeys(rejected)),
        v2_match_by_activity_id=tuple((row[2], row[4]) for row in selected),
        personalization_reasons_by_activity_id=tuple((row[2], row[5]) for row in selected),
        progress_evidence_by_activity_id=tuple(
            (row[2], progress_evidence[row[2]])
            for row in selected
            if row[2] in progress_evidence
        ),
        excluded_by_profile=tuple(excluded_by_profile),
    )


def confirmed_topic_scene(
    anchor_set: SemanticAnchorSetV1,
    *,
    narration_text: str = "",
) -> ConfirmedSceneUnderstandingV2:
    """Build the same reviewed concept projection used by complete discovery."""

    return _scene_from_anchor_set(
        anchor_set,
        narration_text=narration_text,
        complete_discovery=True,
    )


def _select_activity_rows(
    rows: list[ActivityOptionRow],
    *,
    limit: int | None,
    order_by_relevance: bool,
    deduplicate_families: bool = True,
) -> list[ActivityOptionRow]:
    """Select a bounded, family-diverse list, optionally postponing relevance ranking."""
    ordered = (
        sorted(rows, key=lambda row: (-row[0], -row[1], row[2], row[3]))
        if order_by_relevance
        else sorted(rows, key=lambda row: (row[2], row[3]))
    )
    selected: list[ActivityOptionRow] = []
    seen_families: set[str] = set()
    for row in ordered:
        family_id = row[4].activity_family_id or row[2]
        if deduplicate_families and family_id in seen_families:
            continue
        selected.append(row)
        seen_families.add(family_id)
        if limit is not None and len(selected) >= max(1, min(limit, 3)):
            break
    return selected


def _support_matches(
    profile: ChildLearningProfileContextV1,
    interaction_mode: str,
    objective_id: str,
) -> bool:
    support_modes = {
        "HANDS_ON": {"TRANSFER", "CARE", "SORTING", "TRACING"},
        "MOVEMENT": {"OBJ_MOVEMENT_COORDINATION"},
        "VISUAL_SEQUENCE": {"SEQUENCE"},
        "OBSERVATION": {"OBSERVATION", "RESEARCH"},
    }
    return any(
        interaction_mode in support_modes.get(support, set())
        or objective_id in support_modes.get(support, set())
        for support in profile.learning_support_ids
    )


def _expanded_profile_concepts(concepts: tuple[str, ...]) -> set[str]:
    parents = {
        "ANIMAL_BUTTERFLY": "ANIMAL",
        "ANIMAL_GENERIC": "ANIMAL",
        "ANIMAL_MOVEMENT": "ANIMAL",
        "PLANT_FLOWER": "PLANT",
        "PLANT_STRUCTURE": "PLANT",
        "NATURE_OBSERVATION": "NATURE",
        "SCIENCE_OBSERVATION": "SCIENCE",
    }
    return set(concepts) | {parents[item] for item in concepts if item in parents}


def _scene_from_anchor_set(
    anchor_set: SemanticAnchorSetV1,
    *,
    narration_text: str,
    complete_discovery: bool = False,
) -> ConfirmedSceneUnderstandingV2:
    anchors = (anchor_set.primary_anchor, *anchor_set.secondary_anchors)
    concepts: list[SceneConceptV2] = []
    seen: set[str] = set()
    for anchor_index, anchor in enumerate(anchors):
        for concept_id in _concept_ids(
            anchor.normalized_label,
            anchor.semantic_tags,
            complete_discovery=complete_discovery,
        ):
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
                    evidence_adult_assertion_ids=(
                        (anchor.provenance.source_adult_assertion_id,)
                        if anchor.provenance.source_adult_assertion_id
                        else ()
                    ),
                    source_kinds=(
                        ("ADULT",)
                        if anchor.provenance.source_adult_assertion_id
                        and not anchor.provenance.source_claim_ids
                        else ("FUSION",) if narration_text.strip() else ("VLM",)
                    ),
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
                evidence_adult_assertion_ids=(
                    (anchor_set.primary_anchor.provenance.source_adult_assertion_id,)
                    if anchor_set.primary_anchor.provenance.source_adult_assertion_id
                    else ()
                ),
                source_kinds=("ADULT",)
                if anchor_set.primary_anchor.provenance.source_adult_assertion_id
                and not anchor_set.primary_anchor.provenance.source_claim_ids
                else ("VLM",),
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


def _concept_ids(
    label: str,
    tags: tuple[str, ...],
    *,
    complete_discovery: bool = False,
) -> tuple[str, ...]:
    text = unicodedata.normalize("NFC", " ".join((label, *tags)).casefold())
    result: list[str] = []

    def has(*terms: str) -> bool:
        return any(_contains_term(text, term) for term in terms)

    butterfly_topic = has("bướm", "butterfly")
    animal_topic = butterfly_topic or has(
        "động vật",
        "con vật",
        "animal",
        "mammal",
        "hươu cao cổ",
        "giraffe",
        "hươu",
        "nai",
        "voi",
        "elephant",
        "sư tử",
        "lion",
        "hổ",
        "tiger",
        "ngựa vằn",
        "zebra",
        "ngựa",
        "horse",
        "khỉ",
        "monkey",
        "gấu",
        "bear",
        "thỏ",
        "rabbit",
        "chó",
        "dog",
        "mèo",
        "cat",
        "bò",
        "cừu",
        "dê",
        "he-goat",
        "chim",
        "bird",
        "bồ câu",
        "pigeon",
        "đại bàng",
        "eagle",
        "vịt",
        "duck",
        "gà",
        "chicken",
        "cá",
        "fish",
        "cá voi",
        "whale",
        "cá heo",
        "dolphin",
        "cá sấu",
        "crocodile",
        "rùa",
        "turtle",
        "rắn",
        "snake",
        "ếch",
        "frog",
        "côn trùng",
        "insect",
        "ong",
        "bee",
        "kiến",
        "ant",
    )
    if butterfly_topic:
        result.extend(("ANIMAL_BUTTERFLY", "ANIMAL_GENERIC"))
    elif animal_topic:
        result.extend(
            ("ANIMAL_GENERIC",)
            if complete_discovery
            else ("ANIMAL_GENERIC", "NATURE_OBSERVATION")
        )
        if has("bay", "flying", "đậu", "perching", "chuyển động"):
            result.append("ANIMAL_MOVEMENT")
    if has("hoa", "cây", "lá", "flower", "plant", "leaf") and not (
        complete_discovery and animal_topic
    ):
        result.extend(("PLANT_STRUCTURE", "NATURE_OBSERVATION"))
    if has("mặt trời", "sun", "ánh sáng"):
        result.extend(("SUN_LIGHT", "SCIENCE_OBSERVATION"))
    return tuple(dict.fromkeys(result))


def _contains_term(text: str, term: str) -> bool:
    normalized = unicodedata.normalize("NFC", term.casefold().strip())
    return bool(re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", text))


def _complete_discovery_profile(
    profile: SemanticActivityProfileV2,
) -> SemanticActivityProfileV2:
    """Correct known cross-topic tags only for the new complete-list contract.

    The legacy V2 route remains byte-for-byte governed by its existing catalog
    matching. These three catalog rows currently carry topic tags contradicted
    by their reviewed activity descriptions.
    """
    update: dict[str, object] = {"exact_phrases_vi": (), "aliases_vi": ()}
    return profile.model_copy(update=update)


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
