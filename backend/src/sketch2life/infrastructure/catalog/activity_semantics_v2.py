"""Concept-family semantic catalog for the V2 personalization path."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from sketch2life.contracts.schemas.p1_experience import SemanticMatchEvidenceV1
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    ConfirmedSceneUnderstandingV2,
    SceneConceptV2,
    SemanticActivityMatchV2,
    SemanticActivityProfileV2,
)
from sketch2life.infrastructure.catalog.activity_semantics import (
    ActivitySemanticCatalog,
    load_activity_semantic_catalog,
)
from sketch2life.infrastructure.catalog.curated_catalog import (
    CuratedActivityVariant,
    load_curated_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library


class SemanticCatalogV2Error(ValueError):
    """Raised when the V2 concept catalog is not safe to use."""


_ACTIVITY_CONCEPT_OVERRIDES: dict[str, tuple[str, ...]] = {
    "ACT-0001": ("VISUAL_TRACKING", "CONTRAST"),
    "ACT-0004": ("OBJECT_PERMANENCE",),
    "ACT-0026": ("OBJECT_TRANSFER", "SEQUENCE"),
    "ACT-0055": ("PLANT_FLOWER", "PLANT_STRUCTURE", "NATURE_OBSERVATION"),
    "ACT-0058": ("WATER_CYCLE", "SCIENCE_OBSERVATION"),
    "ACT-0091": ("SUN_LIGHT", "MOON_PHASE", "SCIENCE_OBSERVATION"),
    "ACT-0003": ("MOVEMENT_COORDINATION",),
    "ACT-0005": ("OBJECT_TRANSFER",),
    "ACT-0006": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0007": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0012": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0013": ("OBJECT_TRANSFER",),
    "ACT-0021": ("PRACTICAL_LIFE",),
    "ACT-0031": ("PRACTICAL_LIFE",),
    "ACT-0036": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0037": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0038": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0039": ("COLOR_BASIC", "SENSORIAL_COLOR"),
    "ACT-0041": ("SENSORIAL_DISCRIMINATION",),
    "ACT-0043": ("LANGUAGE_PRINT",),
    "ACT-0044": ("LANGUAGE_PRINT",),
    "ACT-0049": ("COUNTING_NUMBER",),
    "ACT-0050": ("MATHEMATICAL_REASONING", "COUNTING_NUMBER"),
    "ACT-0053": ("SCIENCE_NATURE",),
    "ACT-0057": ("ANIMAL_GENERIC", "SCIENCE_NATURE"),
    "ACT-0061": ("MATHEMATICAL_REASONING", "COUNTING_NUMBER"),
    "ACT-0062": ("MATHEMATICAL_REASONING",),
    "ACT-0065": ("MATHEMATICAL_REASONING", "SHAPE_GEOMETRY"),
    "ACT-0066": ("MATHEMATICAL_REASONING",),
    "ACT-0067": ("LANGUAGE_PRINT",),
    "ACT-0068": ("LANGUAGE_PRINT",),
    "ACT-0069": ("LANGUAGE_PRINT",),
    "ACT-0070": ("SCIENTIFIC_INQUIRY",),
    "ACT-0071": ("SCIENCE_NATURE",),
    "ACT-0072": ("GEOGRAPHY",),
    "ACT-0073": ("PEOPLE_FAMILY",),
    "ACT-0074": ("PRACTICAL_LIFE", "MATHEMATICAL_REASONING"),
    "ACT-0075": ("SOCIAL_STUDIES",),
    "ACT-0076": ("MATHEMATICAL_REASONING",),
    "ACT-0077": ("MATHEMATICAL_REASONING",),
    "ACT-0078": ("MATHEMATICAL_REASONING",),
    "ACT-0079": ("MATHEMATICAL_REASONING",),
    "ACT-0080": ("MATHEMATICAL_REASONING",),
    "ACT-0081": ("MATHEMATICAL_REASONING",),
    "ACT-0082": ("SHAPE_GEOMETRY", "MATHEMATICAL_REASONING"),
    "ACT-0083": ("SHAPE_GEOMETRY", "MATHEMATICAL_REASONING"),
    "ACT-0084": ("MATHEMATICAL_REASONING",),
    "ACT-0085": ("MATHEMATICAL_REASONING", "SCIENTIFIC_INQUIRY"),
    "ACT-0086": ("SCIENCE_NATURE",),
    "ACT-0087": ("ANIMAL_GENERIC", "NATURE_OBSERVATION"),
    "ACT-0088": ("SCIENCE_NATURE", "NATURE_OBSERVATION"),
    "ACT-0089": ("SCIENCE_NATURE",),
    "ACT-0090": ("SCIENCE_NATURE",),
    "ACT-0092": ("SCIENCE_NATURE",),
    "ACT-0093": ("HISTORY_CULTURE",),
    "ACT-0094": ("GEOGRAPHY",),
    "ACT-0095": ("SOCIAL_STUDIES",),
    "ACT-0096": ("SOCIAL_STUDIES", "MATHEMATICAL_REASONING"),
    "ACT-0097": ("LANGUAGE_PRINT", "SCIENTIFIC_INQUIRY"),
    "ACT-0098": ("ARTS_VISUAL",),
    "ACT-0099": ("SCIENTIFIC_INQUIRY",),
}

_CONCEPT_SCORE = {
    "MOON_PHASE": 97,
    "SUN_LIGHT": 96,
    "ANIMAL_BUTTERFLY": 94,
    "PLANT_FLOWER": 93,
    "PLANT_STRUCTURE": 90,
    "NATURE_OBSERVATION": 88,
    "ANIMAL_MOVEMENT": 86,
    "ANIMAL_GENERIC": 84,
    "PEOPLE_FAMILY": 83,
    "VEHICLE_TRANSPORT": 82,
    "WEATHER_NATURE": 81,
    "WATER_NATURE": 80,
    "SHAPE_GEOMETRY": 79,
    "SOUND_MUSIC": 78,
    "COUNTING_NUMBER": 77,
    "LANGUAGE_PRINT": 76,
    "PRACTICAL_LIFE": 75,
    "SCIENCE_NATURE": 74,
    "COLOR_BASIC": 79,
    "SENSORIAL_COLOR": 78,
    "SENSORIAL_DISCRIMINATION": 78,
    "MOVEMENT_COORDINATION": 86,
    "MATHEMATICAL_REASONING": 82,
}


@dataclass(frozen=True, slots=True)
class ActivitySemanticCatalogV2:
    profiles: tuple[SemanticActivityProfileV2, ...]
    legacy_catalog: ActivitySemanticCatalog

    def __post_init__(self) -> None:
        ids = tuple(profile.activity_id for profile in self.profiles)
        if len(ids) < 100 or len(set(ids)) != len(ids):
            raise SemanticCatalogV2Error(
                "V2 semantic catalog must contain at least 100 unique activities"
            )

    def profile_for(self, activity_id: str) -> SemanticActivityProfileV2:
        try:
            return next(profile for profile in self.profiles if profile.activity_id == activity_id)
        except StopIteration as exc:
            raise SemanticCatalogV2Error(f"V2 semantic profile missing: {activity_id}") from exc

    def match_scene(
        self,
        scene: ConfirmedSceneUnderstandingV2,
        profile: SemanticActivityProfileV2,
    ) -> SemanticActivityMatchV2 | None:
        observed_text = " ".join(
            (*scene.observed_anchor_labels_vi, scene.asr_transcript_vi)
        ).casefold()
        matched_concepts = _matched_concepts_for_profile(scene, profile)
        for phrase in profile.exact_phrases_vi:
            if _phrase_match(observed_text, phrase) and not _negative_match(observed_text, profile):
                return self._match(
                    scene,
                    profile,
                    "PERSONALIZED_EXACT",
                    98,
                    matched_phrases=(phrase,),
                    matched_concepts=matched_concepts,
                    reason_codes=("EXACT_REVIEWED_PHRASE",),
                )
        if not _negative_match(observed_text, profile):
            for alias in profile.aliases_vi:
                if _phrase_match(observed_text, alias):
                    return self._match(
                        scene,
                        profile,
                        "PERSONALIZED_ALIAS",
                        88,
                        matched_phrases=(alias,),
                        matched_concepts=matched_concepts,
                        reason_codes=("REVIEWED_ALIAS",),
                    )
        if matched_concepts:
            score = max(_CONCEPT_SCORE.get(concept_id, 82) for concept_id in matched_concepts)
            return self._match(
                scene,
                profile,
                "PERSONALIZED_CONCEPT",
                score,
                matched_concepts=matched_concepts,
                reason_codes=("REVIEWED_CONCEPT_FAMILY",),
            )
        if profile.fallback_tier == "AGE_BASELINE":
            return self._match(
                scene,
                profile,
                "AGE_BASELINE_FALLBACK",
                55,
                reason_codes=("NO_PERSONALIZED_MATCH", "AGE_BASELINE_FALLBACK"),
                fallback_reason=(
                    "no exact, alias or reviewed concept-family match; selected age baseline"
                ),
            )
        return None

    def _match(
        self,
        scene: ConfirmedSceneUnderstandingV2,
        profile: SemanticActivityProfileV2,
        mode: str,
        relevance: int,
        *,
        matched_phrases: tuple[str, ...] = (),
        matched_concepts: tuple[str, ...] = (),
        reason_codes: tuple[str, ...],
        fallback_reason: str | None = None,
    ) -> SemanticActivityMatchV2:
        concept_ids = set(matched_concepts)
        matched_labels = tuple(
            concept.label_vi
            for concept in (
                scene.primary_concept,
                *scene.secondary_concepts,
            )
            if concept.concept_id in concept_ids
        )
        if mode == "AGE_BASELINE_FALLBACK" and not matched_labels:
            matched_labels = (scene.primary_anchor_label_vi,)
        selected_concept = _selected_scene_concept(scene, matched_concepts)
        concept_confidence = (
            selected_concept.confidence if selected_concept is not None else 0.5
        )
        child_interest_alignment = (
            selected_concept.child_interest_alignment
            if selected_concept is not None
            else 0.85
            if matched_phrases and _phrase_match(scene.asr_transcript_vi, matched_phrases[0])
            else 0.0
        )
        catalog_quality_score = {
            "PROVISIONAL_OWNER_REVIEWED": 0.60,
            "SEMANTIC_REVIEWED": 0.85,
            "DEMO_ELIGIBLE": 1.0,
            "OWNER_REVIEWED": 0.95,
            "PRODUCTION_APPROVED": 1.0,
            "DEPRECATED": 0.0,
            "BLOCKED": 0.0,
        }.get(profile.review_status, 0.0)
        objective_activity_alignment = _pedagogical_alignment_score(profile)
        base_overall = (
            0.30 * concept_confidence
            + 0.35 * child_interest_alignment
            + 0.15
            + 0.10
            + 0.10 * catalog_quality_score
        )
        continuity_penalty = {
            "DIRECT_CONTINUATION": 0.02,
            "RELATED_EXPANSION": 0.25,
        }[profile.continuity_mode]
        if mode == "AGE_BASELINE_FALLBACK":
            continuity_penalty = 0.35
        overall = max(0.0, min(0.99, base_overall - continuity_penalty))
        planned_video_continuity_score = {
            "DIRECT_CONTINUATION": 0.90,
            "RELATED_EXPANSION": 0.62,
        }[profile.continuity_mode]
        if mode == "AGE_BASELINE_FALLBACK":
            planned_video_continuity_score = 0.45
        effective_reason_codes = list(reason_codes)
        if profile.continuity_mode == "RELATED_EXPANSION":
            effective_reason_codes.extend(
                (
                    "RELATED_EXPANSION",
                    "TOPIC_NOT_DIRECTLY_OBSERVED",
                    "EXPLICIT_BRIDGE_REQUIRED",
                )
            )
        evidence_claim_ids = tuple(
            dict.fromkeys(
                claim_id
                for concept in (scene.primary_concept, *scene.secondary_concepts)
                if not concept_ids or concept.concept_id in concept_ids
                for claim_id in concept.evidence_claim_ids
            )
        )
        evidence_adult_assertion_ids = tuple(
            dict.fromkeys(
                assertion_id
                for concept in (scene.primary_concept, *scene.secondary_concepts)
                if not concept_ids or concept.concept_id in concept_ids
                for assertion_id in concept.evidence_adult_assertion_ids
            )
        )
        return SemanticActivityMatchV2(
            match_mode=mode,  # type: ignore[arg-type]
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            activity_id=profile.activity_id,
            activity_version=profile.activity_version,
            activity_family_id=profile.activity_family_id or f"FAMILY-{profile.activity_id}",
            variant_id=profile.variant_id or f"{profile.activity_id}-{profile.age_band}",
            catalog_revision=profile.catalog_revision,
            semantic_relevance=round(overall * 100),
            selected_concept_id=(selected_concept.concept_id if selected_concept else None),
            selected_concept_role=(selected_concept.concept_role if selected_concept else None),
            concept_match_confidence=concept_confidence,
            child_interest_alignment=child_interest_alignment,
            age_fit_score=1.0,
            activity_safety_score=1.0,
            catalog_quality_score=catalog_quality_score,
            overall_personalization_score=overall,
            selected_objective_id=profile.primary_objective_id,
            objective_activity_alignment=objective_activity_alignment,
            matched_objective_ids=(
                profile.primary_objective_id,
                *profile.secondary_objective_ids,
            ),
            matched_concept_ids=matched_concepts,
            matched_phrases_vi=matched_phrases,
            matched_anchor_labels_vi=matched_labels,
            evidence_claim_ids=evidence_claim_ids,
            evidence_adult_assertion_ids=evidence_adult_assertion_ids,
            reason_codes=tuple(dict.fromkeys(effective_reason_codes)),
            fallback_reason=fallback_reason,
            continuity_mode=profile.continuity_mode,
            planned_video_continuity_score=planned_video_continuity_score,
            expansion_bridge_required=profile.expansion_bridge_required,
            age_specific_goal_vi=profile.age_specific_goal_vi,
            video_setup_vi=profile.video_setup_vi,
            video_focus_cues_vi=profile.video_focus_cues_vi,
            video_handoff_prompt_vi=profile.video_handoff_prompt_vi,
            offscreen_instruction_vi=profile.offscreen_instruction_vi,
        )

    def to_legacy_evidence(
        self,
        match: SemanticActivityMatchV2,
    ) -> SemanticMatchEvidenceV1:
        legacy_mode: Literal["EXACT", "ALIAS", "SAFE_FALLBACK"] = (
            "SAFE_FALLBACK"
            if match.match_mode == "AGE_BASELINE_FALLBACK"
            else "EXACT"
            if match.match_mode == "PERSONALIZED_EXACT"
            else "ALIAS"
        )
        return SemanticMatchEvidenceV1(
            match_mode=legacy_mode,
            profile_id=match.profile_id,
            profile_version=match.profile_version,
            score=match.semantic_relevance,
            matched_phrases_vi=match.matched_phrases_vi,
            matched_concept_ids=match.matched_concept_ids,
            matched_objective_ids=match.matched_objective_ids,
            evidence_claim_ids=match.evidence_claim_ids,
            evidence_adult_assertion_ids=match.evidence_adult_assertion_ids,
            reason_codes=match.reason_codes,
            fallback_reason=match.fallback_reason,
        )


def load_activity_semantic_catalog_v2(
    root: Path,
    *,
    include_expansion: bool = False,
) -> ActivitySemanticCatalogV2:
    legacy = load_activity_semantic_catalog(root)
    library = load_p1_template_library(root, include_mvp=True)
    templates_by_activity = {template.activity_ref.id: template for template in library.templates}
    curated_catalog = load_curated_catalog_v2(root) if include_expansion else None
    profiles: list[SemanticActivityProfileV2] = []
    for legacy_profile in legacy.profiles:
        concepts = _concepts_for_profile(
            legacy_profile.activity_id, legacy_profile.exact_phrases_vi
        )
        template = templates_by_activity[legacy_profile.activity_id]
        effective_activity_version = template.activity_ref.version
        profile_payload = {
            "activity_id": legacy_profile.activity_id,
            "activity_version": effective_activity_version,
            "concept_ids": concepts,
            "phrases": legacy_profile.exact_phrases_vi,
            "primary_objective_id": template.objective_refs[0].id,
            "secondary_objective_ids": [
                ref.id for ref in template.objective_refs[1:]
            ],
        }
        profile_hash = hashlib.sha256(
            json.dumps(profile_payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        profiles.append(
            SemanticActivityProfileV2(
                profile_id=(
                    f"SAP2-{legacy_profile.activity_id}-V{effective_activity_version}"
                ),
                profile_version=1,
                activity_id=legacy_profile.activity_id,
                activity_version=effective_activity_version,
                age_band=legacy_profile.age_band,
                concept_ids=concepts,
                parent_concept_ids=tuple(
                    sorted({parent for concept in concepts for parent in _parents(concept)})
                ),
                exact_phrases_vi=legacy_profile.exact_phrases_vi,
                aliases_vi=legacy_profile.aliases_vi,
                negative_phrases_vi=legacy_profile.negative_phrases_vi,
                fallback_tier=legacy_profile.fallback_tier,
                provenance_source=(
                    f"{legacy_profile.provenance_source};"
                    f"derived-v2:{template.provenance_source}"
                ),
                provenance_sha256=profile_hash,
                review_status=legacy_profile.review_status,
                activity_family_id=f"FAMILY-{legacy_profile.activity_id}",
                variant_id=(
                    f"{legacy_profile.activity_id}-{legacy_profile.age_band}"
                    f"-V{legacy_profile.activity_version}"
                ),
                catalog_revision="catalog-2026-09",
                primary_objective_id=template.objective_refs[0].id,
                secondary_objective_ids=tuple(
                    ref.id for ref in template.objective_refs[1:]
                ),
                pedagogical_alignment_status="DEMO_REVIEWED",
                pedagogical_observable_behavior_vi=(
                    f"Kiểm tra hành vi quan sát được cho mục tiêu {template.objective_refs[0].id}."
                ),
            )
        )
    if curated_catalog is not None:
        profiles.extend(
            _profile_from_curated_variant(variant)
            for variant in curated_catalog.variants
        )
    return ActivitySemanticCatalogV2(tuple(profiles), legacy)


def _profile_from_curated_variant(
    variant: CuratedActivityVariant,
) -> SemanticActivityProfileV2:
    return SemanticActivityProfileV2(
        profile_id=f"SAP2-{variant.activity_id}-V{variant.activity_version}",
        profile_version=1,
        activity_id=variant.activity_id,
        activity_version=variant.activity_version,
        age_band=variant.age_band,
        concept_ids=variant.concept_ids,
        parent_concept_ids=tuple(
            sorted({parent for concept in variant.concept_ids for parent in _parents(concept)})
        ),
        exact_phrases_vi=variant.phrases_vi,
        aliases_vi=variant.aliases_vi,
        negative_phrases_vi=(),
        fallback_tier="NONE",
        provenance_source=variant.provenance_source,
        provenance_sha256=variant.provenance_sha256,
        review_status="DEMO_ELIGIBLE",
        production_eligible=variant.to_template().production_eligible,
        activity_family_id=variant.activity_family_id,
        variant_id=variant.variant_id,
        catalog_revision=variant.catalog_revision,
        primary_objective_id=variant.primary_objective_id,
        secondary_objective_ids=variant.secondary_objective_ids,
        pedagogical_alignment_status=variant.pedagogical_alignment.reviewer_status,
        pedagogical_observable_behavior_vi=(
            variant.pedagogical_alignment.expected_observable_behavior_vi
        ),
        continuity_mode=variant.continuity_mode,
        expansion_bridge_required=variant.expansion_bridge_required,
        direct_observation_concept_ids=variant.direct_observation_concept_ids,
        age_specific_goal_vi=variant.age_specific_goal_vi,
        video_setup_vi=variant.video_setup_vi,
        video_focus_cues_vi=variant.video_focus_cues_vi,
        video_handoff_prompt_vi=variant.video_handoff_prompt_vi,
        offscreen_instruction_vi=variant.offscreen_instruction_vi,
    )


def _pedagogical_alignment_score(profile: SemanticActivityProfileV2) -> float:
    reviewed_states = {"DEMO_REVIEWED", "OWNER_REVIEWED", "PRODUCTION_APPROVED"}
    return (
        1.0
        if profile.pedagogical_alignment_status in reviewed_states
        and profile.primary_objective_id
        else 0.0
    )


def _concepts_for_profile(activity_id: str, phrases: tuple[str, ...]) -> tuple[str, ...]:
    if activity_id in _ACTIVITY_CONCEPT_OVERRIDES:
        return _ACTIVITY_CONCEPT_OVERRIDES[activity_id]
    text = unicodedata.normalize("NFC", " ".join(phrases).casefold())
    concepts: list[str] = []
    if _has_any_term(text, "hoa", "cây", "lá", "cỏ", "flower", "plant", "leaf"):
        concepts.extend(("PLANT_STRUCTURE", "NATURE_OBSERVATION"))
    if _has_any_term(
        text,
        "bướm", "butterfly", "chim", "bird", "động vật", "con vật", "animal",
        "hươu cao cổ", "giraffe", "hươu", "voi", "elephant", "sư tử", "lion",
        "hổ", "tiger", "ngựa", "horse", "khỉ", "monkey", "thỏ", "rabbit",
        "chó", "dog", "mèo", "cat", "cá", "fish", "cá voi", "whale",
        "cá heo", "dolphin", "rùa", "turtle", "ếch", "frog", "côn trùng", "insect",
    ):
        concepts.extend(("ANIMAL_GENERIC", "NATURE_OBSERVATION"))
    if _has_any_term(text, "bướm", "butterfly"):
        concepts.append("ANIMAL_BUTTERFLY")
    if _has_any_term(text, "mặt trời", "ánh sáng", "mặt trăng", "sun", "moon"):
        concepts.extend(("SUN_LIGHT", "SCIENCE_OBSERVATION"))
    if _has_any_term(text, "đếm", "số", "toán", "biểu đồ", "count", "number", "math"):
        concepts.append("COUNTING_DATA")
    if _has_any_term(text, "gia đình", "người", "cơ thể", "family", "people", "body"):
        concepts.append("PEOPLE_FAMILY")
    if _has_any_term(text, "phương tiện", "xe", "giao thông", "transport", "vehicle"):
        concepts.append("VEHICLE_TRANSPORT")
    if _has_any_term(text, "thời tiết", "mưa", "mây", "gió", "weather"):
        concepts.append("WEATHER_NATURE")
    if _has_any_term(text, "nước", "sông", "hồ", "biển", "water", "river", "ocean"):
        concepts.append("WATER_NATURE")
    if _has_any_term(text, "khối hình", "hình học", "hình tròn", "hình vuông", "geometry"):
        concepts.append("SHAPE_GEOMETRY")
    if _has_any_term(text, "âm thanh", "tiếng", "nhạc", "sound", "music"):
        concepts.append("SOUND_MUSIC")
    if _has_any_term(text, "chữ cái", "đọc", "âm vị", "nét", "language", "letter"):
        concepts.append("LANGUAGE_PRINT")
    if _has_any_term(
        text, "rửa tay", "lau", "mang khay", "cắt", "cài", "chào hỏi", "sắp bàn", "quét"
    ):
        concepts.append("PRACTICAL_LIFE")
    if _has_any_term(text, "vũ trụ", "trái đất", "địa hình", "vật chất", "máy cơ", "chuỗi thức ăn"):
        concepts.append("SCIENCE_NATURE")
    if _has_any_term(text, "rót", "chuyển", "gấp", "xếp"):
        concepts.extend(("OBJECT_TRANSFER", "SEQUENCE"))
    if not concepts:
        concepts.append("MONTESSORI_MATERIAL")
    return tuple(dict.fromkeys(concepts))


def _has_any_term(text: str, *terms: str) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(unicodedata.normalize('NFC', term.casefold()))}(?!\w)", text)
        for term in terms
    )


def _parents(concept_id: str) -> tuple[str, ...]:
    if concept_id in {"PLANT_FLOWER", "PLANT_STRUCTURE"}:
        return ("PLANT",)
    if concept_id in {"ANIMAL_BUTTERFLY", "ANIMAL_MOVEMENT"}:
        return ("ANIMAL",)
    if concept_id in {"SUN_LIGHT", "MOON_PHASE"}:
        return ("SKY_NATURE",)
    if concept_id in {"OBJECT_TRANSFER", "SEQUENCE"}:
        return ("PRACTICAL_LIFE",)
    if concept_id in {"ANIMAL_GENERIC", "ANIMAL_MOVEMENT"}:
        return ("ANIMAL",)
    if concept_id == "PEOPLE_FAMILY":
        return ("PEOPLE",)
    if concept_id == "VEHICLE_TRANSPORT":
        return ("TRANSPORT",)
    if concept_id in {"WEATHER_NATURE", "WATER_NATURE", "SCIENCE_NATURE"}:
        return ("NATURE",)
    if concept_id == "SHAPE_GEOMETRY":
        return ("GEOMETRY",)
    if concept_id == "SOUND_MUSIC":
        return ("SOUND",)
    if concept_id == "COUNTING_NUMBER":
        return ("NUMBER",)
    if concept_id == "LANGUAGE_PRINT":
        return ("LANGUAGE",)
    if concept_id == "PRACTICAL_LIFE":
        return ("PRACTICAL_LIFE",)
    if concept_id in {"COLOR_BASIC", "SENSORIAL_COLOR"}:
        return ("COLOR",)
    if concept_id == "SENSORIAL_DISCRIMINATION":
        return ("SENSORIAL",)
    if concept_id == "MOVEMENT_COORDINATION":
        return ("MOVEMENT",)
    if concept_id in {"MATHEMATICAL_REASONING", "COUNTING_NUMBER"}:
        return ("MATHEMATICS",)
    return ()


def _scene_concept_ids(scene: ConfirmedSceneUnderstandingV2) -> set[str]:
    return {
        concept.concept_id
        for concept in (scene.primary_concept, *scene.secondary_concepts)
    }


def _matched_concepts_for_profile(
    scene: ConfirmedSceneUnderstandingV2,
    profile: SemanticActivityProfileV2,
) -> tuple[str, ...]:
    return tuple(
        concept_id
        for concept_id in profile.concept_ids
        if concept_id in _scene_concept_ids(scene)
    )


def _selected_scene_concept(
    scene: ConfirmedSceneUnderstandingV2,
    matched_concept_ids: tuple[str, ...],
) -> SceneConceptV2 | None:
    concepts = (scene.primary_concept, *scene.secondary_concepts)
    matching = tuple(
        concept for concept in concepts if concept.concept_id in matched_concept_ids
    )
    if not matching:
        return None
    return sorted(
        matching,
        key=lambda concept: (
            0 if concept.concept_role == "PRIMARY_CHILD_INTEREST" else 1,
            0 if concept.concept_role == "SECONDARY_CHILD_INTEREST" else 1,
            -concept.child_interest_alignment,
            -concept.confidence,
            concept.concept_id,
        ),
    )[0]


def _negative_match(text: str, profile: SemanticActivityProfileV2) -> bool:
    return any(_phrase_match(text, phrase) for phrase in profile.negative_phrases_vi)


def _phrase_match(text: str, phrase: str) -> bool:
    normalized_phrase = re.sub(r"\\s+", " ", phrase.casefold().strip())
    normalized_text = re.sub(r"\\s+", " ", text.casefold().strip())
    return bool(
        normalized_phrase
        and re.search(rf"(?<!\\w){re.escape(normalized_phrase)}(?!\\w)", normalized_text)
    )


__all__ = [
    "ActivitySemanticCatalogV2",
    "SemanticCatalogV2Error",
    "load_activity_semantic_catalog_v2",
]
