"""Concept-family semantic catalog for the V2 personalization path."""

from __future__ import annotations

import hashlib
import json
import re
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
        }.get(profile.review_status, 0.0)
        overall = min(
            1.0,
            0.30 * concept_confidence
            + 0.35 * child_interest_alignment
            + 0.15
            + 0.10
            + 0.10 * catalog_quality_score,
        )
        evidence_claim_ids = tuple(
            dict.fromkeys(
                claim_id
                for concept in (scene.primary_concept, *scene.secondary_concepts)
                if not concept_ids or concept.concept_id in concept_ids
                for claim_id in concept.evidence_claim_ids
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
            matched_concept_ids=matched_concepts,
            matched_phrases_vi=matched_phrases,
            matched_anchor_labels_vi=matched_labels,
            evidence_claim_ids=evidence_claim_ids or ("fusion:scene",),
            reason_codes=reason_codes,
            fallback_reason=fallback_reason,
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
            evidence_claim_ids=match.evidence_claim_ids,
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
    )


def _concepts_for_profile(activity_id: str, phrases: tuple[str, ...]) -> tuple[str, ...]:
    if activity_id in _ACTIVITY_CONCEPT_OVERRIDES:
        return _ACTIVITY_CONCEPT_OVERRIDES[activity_id]
    text = " ".join(phrases).casefold()
    concepts: list[str] = []
    if any(token in text for token in ("hoa", "cây", "lá", "cỏ")):
        concepts.extend(("PLANT_STRUCTURE", "NATURE_OBSERVATION"))
    if any(token in text for token in ("bướm", "chim", "động vật")):
        concepts.extend(("ANIMAL", "NATURE_OBSERVATION"))
    if any(token in text for token in ("mặt trời", "ánh sáng", "mặt trăng")):
        concepts.extend(("SUN_LIGHT", "SCIENCE_OBSERVATION"))
    if any(token in text for token in ("đếm", "số", "toán", "biểu đồ")):
        concepts.append("COUNTING_DATA")
    if any(token in text for token in ("động vật", "con vật", "chim", "cá", "chó", "mèo")):
        concepts.append("ANIMAL_GENERIC")
    if any(token in text for token in ("gia đình", "người", "cơ thể")):
        concepts.append("PEOPLE_FAMILY")
    if any(token in text for token in ("phương tiện", "xe", "giao thông")):
        concepts.append("VEHICLE_TRANSPORT")
    if any(token in text for token in ("thời tiết", "mưa", "mây", "gió")):
        concepts.append("WEATHER_NATURE")
    if any(token in text for token in ("nước", "sông", "hồ", "biển")):
        concepts.append("WATER_NATURE")
    if any(token in text for token in ("khối hình", "hình học", "hình tròn", "hình vuông")):
        concepts.append("SHAPE_GEOMETRY")
    if any(token in text for token in ("âm thanh", "tiếng", "nhạc")):
        concepts.append("SOUND_MUSIC")
    if any(token in text for token in ("chữ cái", "đọc", "âm vị", "nét")):
        concepts.append("LANGUAGE_PRINT")
    if any(
        token in text
        for token in (
            "rửa tay", "lau", "mang khay", "cắt", "cài", "chào hỏi", "sắp bàn", "quét"
        )
    ):
        concepts.append("PRACTICAL_LIFE")
    if any(
        token in text
        for token in ("vũ trụ", "trái đất", "địa hình", "vật chất", "máy cơ", "chuỗi thức ăn")
    ):
        concepts.append("SCIENCE_NATURE")
    if any(token in text for token in ("rót", "chuyển", "gấp", "xếp")):
        concepts.extend(("OBJECT_TRANSFER", "SEQUENCE"))
    if not concepts:
        concepts.append("ACTIVITY_" + activity_id)
    return tuple(dict.fromkeys(concepts))


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
