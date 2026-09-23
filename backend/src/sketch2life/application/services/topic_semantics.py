"""Deterministic, provider-neutral topic labels and claim ranking.

This module is deliberately bounded: it may translate a small reviewed label
lexicon and compose a display topic, but it never invents an observation.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from sketch2life.contracts.schemas.p1_experience import (
    AnchorProvenanceV1,
    SemanticAnchorSetV1,
)
from sketch2life.contracts.schemas.raw_understanding import RawUnderstandingSuccessV1
from sketch2life.contracts.schemas.vision import vision_label_normalize

ClaimKind = Literal["subject", "action", "story"]

# Only closed, reviewed labels are translated. Unknown model output remains
# visible as-is and is never guessed from a fuzzy dictionary.
_LABELS_VI: dict[str, str] = {
    "butterfly": "con bướm",
    "grass": "bãi cỏ",
    "flower": "bông hoa",
    "flowers": "bông hoa",
    "plant": "cây",
    "tree": "cây",
    "sun": "mặt trời",
    "sky": "bầu trời",
    "flying": "bay",
    "fly": "bay",
    "moving": "chuyển động",
    "nature": "thiên nhiên",
    "garden": "khu vườn",
    "animal": "động vật",
    "bird": "con chim",
    "branch": "cành cây",
    "leaf": "chiếc lá",
    "leaves": "những chiếc lá",
    "perching": "đậu trên cành",
    "bird on branch": "con chim đậu trên cành cây",
    "outdoor scene": "khung cảnh ngoài trời",
    "cat": "con mèo",
    "dog": "con chó",
    "water": "nước",
    "rain": "mưa",
}

_SEMANTIC_TAGS: dict[str, tuple[str, ...]] = {
    "butterfly": ("động vật", "chuyển động"),
    "grass": ("thiên nhiên", "quan sát cây"),
    "flower": ("cây", "thiên nhiên", "quan sát cây"),
    "flowers": ("cây", "thiên nhiên", "quan sát cây"),
    "plant": ("cây", "quan sát cây"),
    "tree": ("cây", "quan sát cây"),
    "nature": ("thiên nhiên", "quan sát cây"),
    "garden": ("thiên nhiên", "quan sát cây"),
    "animal": ("động vật",),
    "bird": ("động vật", "chuyển động"),
    "branch": ("cây", "thiên nhiên", "quan sát cây"),
    "leaf": ("cây", "thiên nhiên", "quan sát cây"),
    "leaves": ("cây", "thiên nhiên", "quan sát cây"),
    "perching": ("động vật", "chuyển động"),
    "bird on branch": ("động vật", "thiên nhiên", "chuyển động"),
    "flying": ("chuyển động",),
    "fly": ("chuyển động",),
    "moving": ("chuyển động",),
}

_BACKGROUND_LABELS = {
    "grass",
    "ground",
    "nature",
    "background",
    "sky",
    "cỏ",
    "bãi cỏ",
    "thiên nhiên",
    "bầu trời",
}

_CANONICAL_DISPLAY_KEYS: dict[str, str] = {
    "leaf": "leaf",
    "leaves": "leaf",
    "chiếc lá": "leaf",
    "những chiếc lá": "leaf",
}


@dataclass(frozen=True, slots=True)
class RankedClaim:
    observation_id: str
    label: str
    display_label: str
    kind: ClaimKind
    confidence: float


@dataclass(frozen=True, slots=True)
class TopicDirection:
    direction_id: str
    priority: int
    title_vi: str
    summary_vi: str
    primary_claim_id: str
    source_claim_ids: tuple[str, ...]
    confidence_band: Literal["HIGH", "MEDIUM", "LOW"]
    image_covered: bool
    narration_covered: bool
    requires_requery: bool

    def as_payload(self) -> dict[str, object]:
        return {
            "direction_id": self.direction_id,
            "priority": self.priority,
            "title_vi": self.title_vi,
            "summary_vi": self.summary_vi,
            "primary_claim_id": self.primary_claim_id,
            "source_claim_ids": list(self.source_claim_ids),
            "confidence_band": self.confidence_band,
            "image_covered": self.image_covered,
            "narration_covered": self.narration_covered,
            "requires_requery": self.requires_requery,
        }


def _key(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().strip())


def display_label_vi(label: str) -> str:
    """Return a closed Vietnamese display label or the original label."""

    translated = _LABELS_VI.get(_key(label))
    if translated is not None:
        return translated
    cleaned = label.strip()
    if cleaned and cleaned.isascii() and re.fullmatch(r"[A-Za-z][A-Za-z\s-]*", cleaned):
        return "chi tiết trong tranh"
    return cleaned


def semantic_tags_for_label(label: str) -> tuple[str, ...]:
    """Return reviewed matching hints for one raw model label."""

    return _SEMANTIC_TAGS.get(_key(label), ())


def rank_claims(claims: Iterable[RankedClaim]) -> tuple[RankedClaim, ...]:
    """Prefer specific evidence and remove canonical duplicate display claims."""

    def sort_key(claim: RankedClaim) -> tuple[int, int, float, str]:
        normalized = _key(claim.label)
        role_rank = {"subject": 0, "action": 1, "story": 2}[claim.kind]
        background_penalty = 1 if normalized in _BACKGROUND_LABELS else 0
        specificity = min(len(normalized.split()), 4)
        return (
            background_penalty,
            role_rank,
            -claim.confidence,
            f"{-specificity}:{claim.observation_id}",
        )

    ranked = sorted(claims, key=sort_key)
    deduplicated: list[RankedClaim] = []
    seen: set[tuple[str, str]] = set()
    for claim in ranked:
        display_key = _key(claim.display_label)
        canonical = _CANONICAL_DISPLAY_KEYS.get(
            _key(claim.label),
            _CANONICAL_DISPLAY_KEYS.get(display_key, display_key),
        )
        key = (claim.kind, canonical)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(claim)
    return tuple(deduplicated)


def claims_from_raw(raw: RawUnderstandingSuccessV1) -> tuple[RankedClaim, ...]:
    values: list[RankedClaim] = []
    for items, kind in (
        (raw.entities, "subject"),
        (raw.actions, "action"),
        (raw.themes, "story"),
    ):
        for item in items:
            if item.confidence is None:
                continue
            values.append(
                RankedClaim(
                    observation_id=item.observation_id,
                    label=item.label.value,
                    display_label=display_label_vi(item.label.value),
                    kind=kind,  # type: ignore[arg-type]
                    confidence=item.confidence,
                )
            )
    return rank_claims(values)


def compose_topic_vi(claims: Iterable[RankedClaim]) -> str:
    """Compose a truthful topic from the supplied claims only."""

    ranked = tuple(claims)
    if not ranked:
        return "Khám phá bức tranh"
    primary = ranked[0]
    actions = tuple(item.display_label for item in ranked if item.kind == "action")
    contexts = tuple(
        item.display_label
        for item in ranked
        if item.kind == "story" and item.observation_id != primary.observation_id
    )
    if primary.kind == "subject" and actions:
        action = actions[0]
        complete_context = next(
            (
                context
                for context in contexts
                if _key(primary.display_label) in _key(context)
                and _key(action).split()[0] in _key(context)
            ),
            None,
        )
        if complete_context:
            return f"Cùng khám phá {complete_context}!"
        if contexts:
            return (
                f"Cùng khám phá {primary.display_label} đang {action} "
                f"giữa {contexts[0]}!"
            )
        return f"Cùng khám phá {primary.display_label} đang {action}!"
    if primary.kind == "subject" and contexts:
        return f"Cùng khám phá {primary.display_label} trong {contexts[0]}!"
    if primary.kind == "action":
        return f"Cùng khám phá hoạt động {primary.display_label}!"
    return f"Cùng khám phá {primary.display_label}!"


def build_topic_directions(
    claims: Iterable[RankedClaim], *, narration_available: bool = False
) -> tuple[TopicDirection, ...]:
    """Build at most three complete, distinct and source-linked topic directions."""

    ranked = tuple(
        claim
        for claim in rank_claims(claims)
        if _key(claim.display_label) not in {"", "chi tiết trong tranh"}
    )
    if not ranked:
        return ()
    subjects = tuple(claim for claim in ranked if claim.kind == "subject")
    actions = tuple(claim for claim in ranked if claim.kind == "action")
    contexts = tuple(claim for claim in ranked if claim.kind == "story")
    primaries = subjects or actions or contexts
    candidates: list[tuple[str, RankedClaim, tuple[RankedClaim, ...]]] = []

    for primary in primaries[:3]:
        supporting: list[RankedClaim] = [primary]
        action = next(
            (item for item in actions if item.observation_id != primary.observation_id), None
        )
        context = next(
            (item for item in contexts if item.observation_id != primary.observation_id), None
        )
        if action is not None:
            supporting.append(action)
        if context is not None:
            supporting.append(context)
        title = compose_topic_vi(tuple(supporting))
        candidates.append((title, primary, tuple(supporting)))

    if len(candidates) < 3 and subjects:
        primary = subjects[0]
        for context in contexts[1:3]:
            context_supporting = (primary, context)
            candidates.append(
                (compose_topic_vi(context_supporting), primary, context_supporting)
            )

    directions: list[TopicDirection] = []
    seen_titles: set[str] = set()
    for title, primary, supporting_claims in candidates:
        normalized_title = _key(title)
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)
        confidence = sum(item.confidence for item in supporting_claims) / len(
            supporting_claims
        )
        band: Literal["HIGH", "MEDIUM", "LOW"] = (
            "HIGH" if confidence >= 0.8 else "MEDIUM" if confidence >= 0.55 else "LOW"
        )
        priority = len(directions) + 1
        directions.append(
            TopicDirection(
                direction_id=f"topic-direction-{priority}",
                priority=priority,
                title_vi=title,
                summary_vi=(
                    "Kết hợp những gì nhìn thấy trong tranh và lời kể của con."
                    if narration_available
                    else "Được ghép từ những chi tiết rõ nhất trong bức tranh."
                ),
                primary_claim_id=primary.observation_id,
                source_claim_ids=tuple(
                    dict.fromkeys(item.observation_id for item in supporting_claims)
                ),
                confidence_band=band,
                image_covered=True,
                narration_covered=narration_available,
                requires_requery=priority > 1,
            )
        )
        if len(directions) == 3:
            break
    return tuple(directions)


def enrich_anchor_set(
    *,
    raw: RawUnderstandingSuccessV1,
    anchor_set: SemanticAnchorSetV1,
    confirmed_claim_ids: tuple[str, ...],
) -> SemanticAnchorSetV1:
    """Attach reviewed semantic hints while preserving all source provenance."""

    claims = {
        claim.observation_id: claim
        for claim in claims_from_raw(raw)
        if claim.observation_id in confirmed_claim_ids
    }
    primary = anchor_set.primary_anchor
    primary_claim = claims.get(primary.provenance.source_claim_ids[0])
    tags: list[str] = list(primary.semantic_tags)
    if primary_claim is not None:
        tags.extend(semantic_tags_for_label(primary_claim.label))
    tags.extend(
        tag
        for claim in claims.values()
        for tag in semantic_tags_for_label(claim.label)
    )
    enriched_primary = primary.model_copy(
        update={
            "semantic_tags": tuple(dict.fromkeys(tag for tag in tags if tag.strip())),
            "provenance": AnchorProvenanceV1(
                source_artifact_id=primary.provenance.source_artifact_id,
                source_artifact_sha256=primary.provenance.source_artifact_sha256,
                source_contract_name=primary.provenance.source_contract_name,
                source_contract_version=primary.provenance.source_contract_version,
                source_claim_ids=tuple(confirmed_claim_ids),
            ),
        }
    )
    return anchor_set.model_copy(update={"primary_anchor": enriched_primary})


def normalized_display_label(label: str) -> str:
    """Normalize a user/model label without changing its meaning."""

    return vision_label_normalize(display_label_vi(label))


__all__ = [
    "RankedClaim",
    "TopicDirection",
    "build_topic_directions",
    "claims_from_raw",
    "compose_topic_vi",
    "display_label_vi",
    "enrich_anchor_set",
    "normalized_display_label",
    "rank_claims",
    "semantic_tags_for_label",
]
