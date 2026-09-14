"""Reviewed semantic activity profiles and deterministic compatibility matching."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from sketch2life.contracts.schemas.activity_semantics import (
    SemanticActivityProfileV1,
    SemanticMatchMode,
)
from sketch2life.contracts.schemas.p1_experience import (
    SemanticAnchorSetV1,
    SemanticAnchorV1,
    SemanticMatchEvidenceV1,
)


class SemanticCatalogError(ValueError):
    """Raised when semantic activity profiles are incomplete or invalid."""


@dataclass(frozen=True, slots=True)
class ActivitySemanticCatalog:
    profiles: tuple[SemanticActivityProfileV1, ...]
    catalog_source: str

    def __post_init__(self) -> None:
        ids = [profile.activity_id for profile in self.profiles]
        if len(ids) != len(set(ids)):
            raise SemanticCatalogError("semantic catalog contains duplicate activity IDs")

    @property
    def by_activity_id(self) -> dict[str, SemanticActivityProfileV1]:
        return {profile.activity_id: profile for profile in self.profiles}

    def profile_for(self, activity_id: str) -> SemanticActivityProfileV1:
        try:
            return self.by_activity_id[activity_id]
        except KeyError as exc:
            raise SemanticCatalogError(f"semantic profile missing: {activity_id}") from exc

    def validate_all_age_bands(self, *, expected_activity_count: int = 100) -> None:
        if len(self.profiles) != expected_activity_count:
            raise SemanticCatalogError(
                f"semantic catalog must contain {expected_activity_count} profiles"
            )
        fallback_bands = {
            profile.age_band
            for profile in self.profiles
            if profile.fallback_tier == "AGE_BASELINE"
        }
        if fallback_bands != {"0-3", "3-6", "6-9", "9-12"}:
            missing = sorted({"0-3", "3-6", "6-9", "9-12"} - fallback_bands)
            raise SemanticCatalogError("missing age baseline fallback: " + ",".join(missing))

    def match(
        self,
        anchor_set: SemanticAnchorSetV1,
        profile: SemanticActivityProfileV1,
    ) -> SemanticMatchEvidenceV1 | None:
        anchor = anchor_set.primary_anchor
        if anchor.kind not in profile.accepted_anchor_kinds:
            return None
        label = _normalize(anchor.normalized_label)
        original = _normalize(anchor.original_label)
        negative_match = any(
            _phrase_match(label, phrase) or _phrase_match(original, phrase)
            for phrase in profile.negative_phrases_vi
        )
        if not negative_match:
            for phrase in profile.exact_phrases_vi:
                if _phrase_match(label, phrase) or _phrase_match(original, phrase):
                    return _evidence(
                        profile,
                        anchor,
                        "EXACT",
                        score=98,
                        phrase=phrase,
                        reason_codes=("EXACT_REVIEWED_PHRASE",),
                    )
            for alias in profile.aliases_vi:
                if _phrase_match(label, alias) or _phrase_match(original, alias):
                    return _evidence(
                        profile,
                        anchor,
                        "ALIAS",
                        score=88,
                        phrase=alias,
                        reason_codes=("REVIEWED_ALIAS",),
                    )
        if profile.fallback_tier == "AGE_BASELINE" and profile.fallback_any_confirmed_anchor:
            return _evidence(
                profile,
                anchor,
                "SAFE_FALLBACK",
                score=55,
                phrase=None,
                reason_codes=("NO_EXACT_SEMANTIC_MATCH", "AGE_BASELINE_FALLBACK"),
                fallback_reason="no exact or reviewed alias match; selected age baseline",
            )
        return None

def load_activity_semantic_catalog(root: Path) -> ActivitySemanticCatalog:
    path = root / "data" / "activity-catalog" / "golden" / "v1" / "semantic-anchor-profiles.v1.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticCatalogError("cannot read semantic activity profile catalog") from exc
    profiles_raw = document.get("profiles")
    if document.get("schema_version") != 1 or not isinstance(profiles_raw, list):
        raise SemanticCatalogError("semantic activity profile catalog schema is invalid")
    try:
        profiles = tuple(SemanticActivityProfileV1.model_validate(item) for item in profiles_raw)
    except ValueError as exc:
        raise SemanticCatalogError("semantic activity profile validation failed") from exc
    catalog = ActivitySemanticCatalog(
        profiles=profiles,
        catalog_source="golden/v1:semantic-anchor-profiles.v1.json",
    )
    catalog.validate_all_age_bands()
    return catalog


def semantic_profile_digest(profile: SemanticActivityProfileV1) -> str:
    payload = profile.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _evidence(
    profile: SemanticActivityProfileV1,
    anchor: SemanticAnchorV1,
    mode: SemanticMatchMode,
    *,
    score: int,
    phrase: str | None,
    reason_codes: tuple[str, ...],
    fallback_reason: str | None = None,
) -> SemanticMatchEvidenceV1:
    claim_ids = tuple(anchor.provenance.source_claim_ids)
    return SemanticMatchEvidenceV1(
        match_mode=mode,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        score=score,
        matched_phrases_vi=(phrase,) if phrase else (),
        matched_concept_ids=(profile.profile_id,),
        evidence_claim_ids=claim_ids,
        reason_codes=reason_codes,
        fallback_reason=fallback_reason,
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().strip())


def _phrase_match(value: str, phrase: str) -> bool:
    normalized_phrase = _normalize(phrase)
    if len(normalized_phrase.split()) < 2:
        return False
    return value == normalized_phrase or normalized_phrase in value


__all__ = [
    "ActivitySemanticCatalog",
    "SemanticCatalogError",
    "load_activity_semantic_catalog",
    "semantic_profile_digest",
]