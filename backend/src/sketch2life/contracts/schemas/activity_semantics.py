"""Versioned, provider-neutral contracts for semantic activity compatibility."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SemanticAnchorKind = Literal["subject", "action", "visual_feature", "story"]
SemanticMatchMode = Literal["EXACT", "ALIAS", "SAFE_FALLBACK"]
FallbackTier = Literal["NONE", "AGE_BASELINE"]


class SemanticActivityProfileV1(BaseModel):
    """Reviewed semantic boundary for one catalog activity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["SemanticActivityProfileV1"] = "SemanticActivityProfileV1"
    contract_version: Literal["1.0"] = "1.0"
    profile_id: str = Field(min_length=1, max_length=120)
    profile_version: int = Field(ge=1)
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    activity_version: int = Field(ge=1)
    age_band: Literal["0-3", "3-6", "6-9", "9-12"]
    age_months_min: int = Field(ge=0, le=155)
    age_months_max: int = Field(ge=0, le=155)
    exact_phrases_vi: tuple[str, ...] = Field(min_length=1)
    aliases_vi: tuple[str, ...] = ()
    accepted_anchor_kinds: tuple[SemanticAnchorKind, ...] = Field(min_length=1)
    required_concept_groups: tuple[tuple[str, ...], ...] = ()
    ambiguous_tokens_vi: tuple[str, ...] = ()
    negative_phrases_vi: tuple[str, ...] = ()
    positive_examples_vi: tuple[str, ...] = Field(min_length=1)
    negative_examples_vi: tuple[str, ...] = Field(min_length=1)
    fallback_tier: FallbackTier = "NONE"
    fallback_any_confirmed_anchor: bool = False
    provenance_source: str = Field(min_length=1, max_length=240)
    provenance_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_status: Literal["PROVISIONAL_OWNER_REVIEWED", "SEMANTIC_REVIEWED", "DEMO_ELIGIBLE"]
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def validate_profile(self) -> SemanticActivityProfileV1:
        if self.age_months_max < self.age_months_min:
            raise ValueError("semantic profile age max must be >= min")
        if self.fallback_tier == "AGE_BASELINE" and not self.fallback_any_confirmed_anchor:
            raise ValueError("age baseline fallback must declare confirmed-anchor policy")
        if not self.negative_examples_vi:
            raise ValueError("semantic profile requires negative examples")
        return self


__all__ = [
    "FallbackTier",
    "SemanticActivityProfileV1",
    "SemanticAnchorKind",
    "SemanticMatchMode",
]