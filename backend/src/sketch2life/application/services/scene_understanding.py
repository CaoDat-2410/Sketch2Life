"""Build one age-invariant, provider-neutral scene understanding after fusion."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, cast

from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    ConfirmedSceneUnderstandingV2,
    SceneConceptV2,
)

SceneCandidateKind = Literal["subject", "action", "visual_feature", "story"]
SceneSourceKind = Literal["ASR", "VLM"]


@dataclass(frozen=True, slots=True)
class SceneCandidateV2Input:
    label_vi: str
    kind: SceneCandidateKind
    confidence: float
    claim_ids: tuple[str, ...]
    source_kind: SceneSourceKind


@dataclass(frozen=True, slots=True)
class _ConceptRoute:
    concept_id: str
    label_vi: str
    phrases_vi: tuple[str, ...]
    parent_concept_ids: tuple[str, ...]
    priority: int


_CONCEPT_ROUTES = (
    _ConceptRoute(
        "ANIMAL_BUTTERFLY",
        "con bướm",
        ("con bướm", "bướm"),
        ("ANIMAL",),
        100,
    ),
    _ConceptRoute(
        "PLANT_FLOWER",
        "bông hoa",
        ("bông hoa", "hoa"),
        ("PLANT", "NATURE_OBSERVATION"),
        96,
    ),
    _ConceptRoute(
        "SUN_LIGHT",
        "mặt trời",
        ("mặt trời", "ánh sáng mặt trời", "ánh nắng"),
        ("SKY_NATURE",),
        95,
    ),
    _ConceptRoute(
        "MOON_PHASE",
        "mặt trăng",
        ("mặt trăng", "pha mặt trăng"),
        ("SKY_NATURE",),
        94,
    ),
    _ConceptRoute(
        "ANIMAL_MOVEMENT",
        "động vật đang bay",
        ("bướm bay", "đang bay"),
        ("ANIMAL", "MOVEMENT"),
        92,
    ),
    _ConceptRoute(
        "PLANT_STRUCTURE",
        "cấu trúc cây",
        ("cây", "lá", "cỏ"),
        ("PLANT", "NATURE_OBSERVATION"),
        72,
    ),
    _ConceptRoute(
        "COLOR_RED",
        "màu đỏ",
        ("màu đỏ", "đỏ"),
        ("COLOR",),
        20,
    ),
)


def build_confirmed_scene_understanding(
    *,
    scene_understanding_id: str,
    image_artifact_ref: str,
    image_sha256: str,
    audio_artifact_ref: str,
    audio_sha256: str,
    candidates: tuple[SceneCandidateV2Input, ...],
    asr_transcript_vi: str,
) -> ConfirmedSceneUnderstandingV2:
    """Normalize fused observations once; age-band code must not call this again."""

    observed_labels = _unique(
        candidate.label_vi.strip()
        for candidate in candidates
        if candidate.label_vi.strip()
    )
    concepts = tuple(
        _concept_from_route(route, candidates, asr_transcript_vi)
        for route in _CONCEPT_ROUTES
        if _route_matches(route, candidates, asr_transcript_vi)
    )
    if concepts:
        primary_concept = concepts[0]
    else:
        fallback_label = _stable_fallback_label(candidates)
        fallback_claims = _claims_for_label(fallback_label, candidates)
        primary_concept = SceneConceptV2(
            concept_id="UNCLASSIFIED_OBSERVATION",
            label_vi=fallback_label,
            confidence=0.5,
            evidence_claim_ids=fallback_claims or ("fusion:unclassified",),
            source_kinds=("FUSION",),
        )
    secondary_concepts = tuple(concept for concept in concepts if concept != primary_concept)
    primary_label = primary_concept.label_vi
    payload = {
        "image_sha256": image_sha256,
        "audio_sha256": audio_sha256,
        "primary": primary_concept.model_dump(mode="json"),
        "secondary": [concept.model_dump(mode="json") for concept in secondary_concepts],
        "observed_labels": observed_labels,
        "transcript": asr_transcript_vi,
    }
    digest = _canonical_hash(payload)
    scene_id = scene_understanding_id or f"SCENE-{digest[:16]}"
    return ConfirmedSceneUnderstandingV2(
        scene_understanding_id=scene_id,
        source_image_artifact_ref=image_artifact_ref,
        source_image_sha256=image_sha256,
        source_audio_artifact_ref=audio_artifact_ref,
        source_audio_sha256=audio_sha256,
        primary_anchor_label_vi=primary_label,
        primary_concept=primary_concept,
        secondary_concepts=secondary_concepts,
        observed_anchor_labels_vi=observed_labels or (primary_label,),
        observed_entity_labels_vi=_unique(
            candidate.label_vi for candidate in candidates if candidate.kind == "subject"
        ),
        observed_action_labels_vi=_unique(
            candidate.label_vi for candidate in candidates if candidate.kind == "action"
        ),
        observed_theme_labels_vi=_unique(
            candidate.label_vi for candidate in candidates if candidate.kind == "story"
        ),
        asr_transcript_vi=asr_transcript_vi,
        supported_modalities=tuple(
            cast(Literal["ASR", "VLM"], source)
            for source in ("ASR", "VLM")
            if any(candidate.source_kind == source for candidate in candidates)
        ) or ("VLM",),
        conflict_preserved=True,
        normalization_policy_version="SCENE_NORMALIZATION_V2",
        scene_sha256=digest,
    )


def route_concept_ids() -> tuple[str, ...]:
    return tuple(route.concept_id for route in _CONCEPT_ROUTES)


def route_phrases(concept_id: str) -> tuple[str, ...]:
    return next(
        (route.phrases_vi for route in _CONCEPT_ROUTES if route.concept_id == concept_id),
        (),
    )


def _concept_from_route(
    route: _ConceptRoute,
    candidates: tuple[SceneCandidateV2Input, ...],
    transcript: str,
) -> SceneConceptV2:
    matched_candidates = tuple(
        candidate
        for candidate in candidates
        if any(_contains_phrase(candidate.label_vi, phrase) for phrase in route.phrases_vi)
    )
    claims = _unique(
        claim_id
        for candidate in matched_candidates
        for claim_id in candidate.claim_ids
    )
    if any(_contains_phrase(transcript, phrase) for phrase in route.phrases_vi):
        claims = _unique((*claims, "asr:transcript"))
    source_kinds = tuple(
        cast(Literal["ASR", "VLM", "FUSION"], source)
        for source in ("ASR", "VLM", "FUSION")
        if (
            source == "ASR"
            and "asr:transcript" in claims
        )
        or (
            source == "VLM"
            and any(candidate.source_kind == "VLM" for candidate in matched_candidates)
        )
    )
    confidence = max(
        (candidate.confidence for candidate in matched_candidates),
        default=0.5,
    )
    if len(source_kinds) > 1:
        confidence = min(1.0, confidence + 0.05)
    return SceneConceptV2(
        concept_id=route.concept_id,
        label_vi=route.label_vi,
        parent_concept_ids=route.parent_concept_ids,
        confidence=confidence,
        evidence_claim_ids=claims or ("fusion:concept-route",),
        source_kinds=source_kinds or ("FUSION",),
    )


def _route_matches(
    route: _ConceptRoute,
    candidates: tuple[SceneCandidateV2Input, ...],
    transcript: str,
) -> bool:
    return _contains_phrase(transcript, route.phrases_vi[0]) or any(
        _contains_phrase(candidate.label_vi, phrase)
        for candidate in candidates
        for phrase in route.phrases_vi
    )


def _stable_fallback_label(candidates: tuple[SceneCandidateV2Input, ...]) -> str:
    if not candidates:
        return "bức tranh của con"
    return sorted(
        (candidate.label_vi.strip() for candidate in candidates if candidate.label_vi.strip()),
        key=lambda value: (-len(value.split()), value.casefold()),
    )[0]


def _claims_for_label(
    label: str,
    candidates: tuple[SceneCandidateV2Input, ...],
) -> tuple[str, ...]:
    return _unique(
        claim_id
        for candidate in candidates
        if candidate.label_vi.strip() == label
        for claim_id in candidate.claim_ids
    )


def _contains_phrase(value: str, phrases: tuple[str, ...] | list[str] | str) -> bool:
    phrase_values = (phrases,) if isinstance(phrases, str) else tuple(phrases)
    normalized_value = _normalize(value)
    return any(
        re.search(rf"(?<!\\w){re.escape(_normalize(phrase))}(?!\\w)", normalized_value)
        for phrase in phrase_values
        if _normalize(phrase)
    )


def _normalize(value: str) -> str:
    return re.sub(r"\\s+", " ", value.casefold().strip())


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return tuple(result)


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "SceneCandidateV2Input",
    "build_confirmed_scene_understanding",
    "route_concept_ids",
    "route_phrases",
]