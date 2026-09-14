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
    SemanticActivityMatchV2,
    SemanticActivityProfileV2,
)
from sketch2life.infrastructure.catalog.activity_semantics import (
    ActivitySemanticCatalog,
    load_activity_semantic_catalog,
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
}


@dataclass(frozen=True, slots=True)
class ActivitySemanticCatalogV2:
    profiles: tuple[SemanticActivityProfileV2, ...]
    legacy_catalog: ActivitySemanticCatalog

    def __post_init__(self) -> None:
        ids = tuple(profile.activity_id for profile in self.profiles)
        if len(ids) != 100 or len(set(ids)) != 100:
            raise SemanticCatalogV2Error("V2 semantic catalog must contain 100 unique activities")

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
        for phrase in profile.exact_phrases_vi:
            if _phrase_match(observed_text, phrase) and not _negative_match(observed_text, profile):
                return self._match(
                    scene,
                    profile,
                    "PERSONALIZED_EXACT",
                    98,
                    matched_phrases=(phrase,),
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
                        reason_codes=("REVIEWED_ALIAS",),
                    )
        matched_concepts = tuple(
            concept_id
            for concept_id in profile.concept_ids
            if concept_id in _scene_concept_ids(scene)
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
            semantic_relevance=relevance,
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


def load_activity_semantic_catalog_v2(root: Path) -> ActivitySemanticCatalogV2:
    legacy = load_activity_semantic_catalog(root)
    library = load_p1_template_library(root, include_mvp=True)
    templates_by_activity = {template.activity_ref.id: template for template in library.templates}
    profiles: list[SemanticActivityProfileV2] = []
    for legacy_profile in legacy.profiles:
        concepts = _concepts_for_profile(
            legacy_profile.activity_id, legacy_profile.exact_phrases_vi
        )
        template = templates_by_activity[legacy_profile.activity_id]
        profile_payload = {
            "activity_id": legacy_profile.activity_id,
            "activity_version": legacy_profile.activity_version,
            "concept_ids": concepts,
            "phrases": legacy_profile.exact_phrases_vi,
        }
        profile_hash = hashlib.sha256(
            json.dumps(profile_payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        profiles.append(
            SemanticActivityProfileV2(
                profile_id=f"SAP2-{legacy_profile.activity_id}-V1",
                profile_version=1,
                activity_id=legacy_profile.activity_id,
                activity_version=legacy_profile.activity_version,
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
            )
        )
    return ActivitySemanticCatalogV2(tuple(profiles), legacy)


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
    return ()


def _scene_concept_ids(scene: ConfirmedSceneUnderstandingV2) -> set[str]:
    return {
        concept.concept_id
        for concept in (scene.primary_concept, *scene.secondary_concepts)
    }


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