"""FEAT-093 M1: propose which detected subject is the main one, and when the adult must choose.

Pure domain code: no framework, storage or provider. Inputs are the entities of a drawing candidate
(label, 20x20 grid box, visible features) plus the adult's intent words (typed idea, topic card,
intended subject). The result is a proposal only; the adult confirms or changes it.

Scores (plan Rev 2, section 5, R2): can act 0.35, area share 0.25, centrality 0.15, match with the
adult's intent 0.20, completeness 0.05. Scenery (sun, grass, ground, frame) is ``excluded`` unless the
adult's intent names it. The proposal is flagged ``needs_choice`` when the top two scores differ by
less than ``AMBIGUITY_MARGIN`` or when two subjects can both act and both take a real share of the page.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

GRID = 20
AMBIGUITY_MARGIN = 0.10
MIN_ACTING_AREA_SHARE = 0.08
WEIGHT_CAN_ACT = 0.35
WEIGHT_AREA = 0.25
WEIGHT_CENTRALITY = 0.15
WEIGHT_INTENT = 0.20
WEIGHT_COMPLETE = 0.05
AREA_SHARE_CAP = 0.5  # a subject filling half of the page already gets the full area score

# Lexicons keep Vietnamese accents ("bàn" the table must not match "bạn" the friend). Unknown labels
# score "cannot act". Only the match with the adult's intent compares accent-free text.
_ACTING_WORDS = frozenset(
    {
        "gà", "chim", "vịt", "ngan", "ngỗng", "cá", "mèo", "chó", "thỏ", "voi", "hổ", "khỉ", "gấu",
        "cáo", "ngựa", "bò", "heo", "lợn", "dê", "cừu", "ruồi", "kiến", "ong", "bướm", "chuồn",
        "ếch", "rùa", "rắn", "cua", "tôm", "mực", "rồng", "tiên", "robot", "bé", "cô", "chú", "bạn",
        "người", "em", "bà", "ông", "mẹ", "bố", "anh", "chị", "thú", "sâu", "sói", "hươu", "nai",
        "cú", "vẹt", "sóc", "chuột", "nhím", "dơi", "ốc", "sên", "trâu", "lạc", "đà", "cáo",
    }
)
_ACTING_PHRASES = ("nhân vật", "sư tử", "khủng long", "hươu cao cổ", "ngựa vằn", "chim cánh cụt")
_ANIMAL_CLASSIFIER = "con"
_SCENERY_PHRASES = (
    "mặt trời", "mặt trăng", "mặt đất", "bầu trời", "khung tranh", "viền tranh", "bãi cỏ", "đám mây",
    "nền", "ánh nắng", "cầu vồng",
)
_SCENERY_WORDS = frozenset({"cỏ", "mây", "trăng", "sao", "viền", "khung", "đất", "đường", "sân"})


@dataclass(frozen=True, slots=True)
class ScoredSubject:
    entity_id: str
    label: str
    score: float
    can_act: bool
    scenery: bool
    area_share: float
    intent_match: bool


@dataclass(frozen=True, slots=True)
class RoleProposal:
    main_entity_id: str | None
    needs_choice: bool
    excluded_entity_ids: tuple[str, ...]
    ranked: tuple[ScoredSubject, ...]


def fold(text: str) -> str:
    """Lower-case, accent-free, single-spaced text (Vietnamese ``đ`` becomes ``d``)."""

    decomposed = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join("".join(ch if ch.isalnum() else " " for ch in stripped).split())


def _words(text: str) -> list[str]:
    """Lower-case words that keep their accents."""

    lowered = unicodedata.normalize("NFC", text.casefold())
    return "".join(ch if ch.isalnum() else " " for ch in lowered).split()


def _tokens(text: str) -> list[str]:
    return fold(text).split()


def _box(value: Any) -> tuple[int, int, int, int] | None:
    if (
        isinstance(value, Sequence)
        and not isinstance(value, str)
        and len(value) == 4
        and all(type(item) is int for item in value)
    ):
        x0, y0, x1, y1 = value
        if 0 <= x0 < x1 <= GRID and 0 <= y0 < y1 <= GRID:
            return x0, y0, x1, y1
    return None


def _can_act(label: str) -> bool:
    words = _words(label)
    if not words:
        return False
    joined = " ".join(words)
    if any(phrase in joined for phrase in _ACTING_PHRASES):
        return True
    if words[0] == _ANIMAL_CLASSIFIER and len(words) > 1:
        return True
    return any(word in _ACTING_WORDS for word in words)


def _scenery(label: str) -> bool:
    words = _words(label)
    if not words:
        return False
    joined = " ".join(words)
    if _can_act(label):
        return False
    if any(phrase in joined for phrase in _SCENERY_PHRASES):
        return True
    return len(words) <= 2 and any(word in _SCENERY_WORDS for word in words)


def _intent_match(label: str, intent_terms: Iterable[str]) -> bool:
    label_tokens = {token for token in _tokens(label) if len(token) > 1 and token != _ANIMAL_CLASSIFIER}
    if not label_tokens:
        return False
    for term in intent_terms:
        term_tokens = {token for token in _tokens(term) if len(token) > 1}
        if term_tokens & label_tokens:
            return True
    return False


def _area_share(box: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = box
    return ((x1 - x0) * (y1 - y0)) / float(GRID * GRID)


def _centrality(box: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = GRID / 2
    return max(0.0, 1.0 - math.hypot(cx - half, cy - half) / math.hypot(half, half))


def _complete(box: tuple[int, int, int, int]) -> bool:
    x0, y0, x1, y1 = box
    edges = sum((x0 == 0, y0 == 0, x1 == GRID, y1 == GRID))
    return edges < 2


def propose_roles(
    entities: Sequence[Mapping[str, Any]], *, intent_terms: Iterable[str] = ()
) -> RoleProposal:
    """Rank the entities (``entity_id``, ``label``, ``box``) and propose the main subject."""

    terms = [term for term in intent_terms if isinstance(term, str) and term.strip()]
    scored: list[ScoredSubject] = []
    for entity in entities:
        box = _box(entity.get("box"))
        label = str(entity.get("label") or "")
        entity_id = str(entity.get("entity_id") or "")
        if box is None or not label.strip() or not entity_id:
            continue
        can_act = _can_act(label)
        intent = _intent_match(label, terms)
        scenery = _scenery(label) and not intent
        share = _area_share(box)
        score = (
            WEIGHT_CAN_ACT * (1.0 if can_act else 0.0)
            + WEIGHT_AREA * min(1.0, share / AREA_SHARE_CAP)
            + WEIGHT_CENTRALITY * _centrality(box)
            + WEIGHT_INTENT * (1.0 if intent else 0.0)
            + WEIGHT_COMPLETE * (1.0 if _complete(box) else 0.0)
        )
        scored.append(
            ScoredSubject(
                entity_id=entity_id,
                label=label,
                score=round(score, 4),
                can_act=can_act,
                scenery=scenery,
                area_share=round(share, 4),
                intent_match=intent,
            )
        )
    ranked = tuple(sorted(scored, key=lambda item: (-item.score, item.entity_id)))
    candidates = [item for item in ranked if not item.scenery]
    excluded = tuple(item.entity_id for item in ranked if item.scenery)
    if not candidates:
        return RoleProposal(None, True, excluded, ranked)
    main = candidates[0]
    needs_choice = False
    if len(candidates) > 1:
        runner_up = candidates[1]
        if main.score - runner_up.score < AMBIGUITY_MARGIN:
            needs_choice = True
        actors = [
            item
            for item in candidates
            if item.can_act and item.area_share >= MIN_ACTING_AREA_SHARE
        ]
        if len(actors) >= 2 and not (main.intent_match and not runner_up.intent_match):
            needs_choice = True
    return RoleProposal(main.entity_id, needs_choice, excluded, ranked)


__all__ = ["RoleProposal", "ScoredSubject", "fold", "propose_roles"]
