"""Rules of the knowledge cards that feed the Parent learning script (FEAT-094, plan 4 and 6.2).

A card holds short facts about one kind of drawn subject: what it is, its parts, and what it is
used for. A card is served only after a person approved it with at least one source; the approval
stores a hash of the content, so an edit without a new approval makes the card unusable. Nothing
here knows files, HTTP or a model.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from typing import Any, Final

KINDS: Final = ("WHAT_IT_IS", "PART", "USE")
STATUSES: Final = ("DRAFT", "APPROVED")
# One fact has to fit inside one scene's narration together with the story sentence around it.
MAX_FACT_WORDS: Final = 14
# Age in months -> number of facts in one video (plan 6.2).
_FACTS_BY_AGE: Final = ((36, 71, 3), (72, 107, 4), (108, 120, 5))
_SENTENCE_ENDINGS: Final = (".", "!")


class KnowledgeCardError(ValueError):
    def __init__(self, code: str, *, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass(frozen=True)
class KnowledgeFact:
    id: str
    kind: str
    min_age_months: int
    text: str
    key_terms: tuple[str, ...]
    part: str | None = None


@dataclass(frozen=True)
class KnowledgeSource:
    title: str
    url: str
    checked_on: str


@dataclass(frozen=True)
class KnowledgeCard:
    card_id: str
    version: int
    status: str
    subject_labels: tuple[str, ...]
    topic_ids: tuple[str, ...]
    facts: tuple[KnowledgeFact, ...]
    motion_hints: tuple[str, ...]
    setting: str
    sources: tuple[KnowledgeSource, ...]
    reviewed_by: str | None = None
    reviewed_on: str | None = None
    approved_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))


def _folded(value: str) -> str:
    """Case and accent insensitive form used to match labels and part names."""

    decomposed = unicodedata.normalize("NFD", value.casefold())
    plain = "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )
    return " ".join("".join(char if char.isalnum() else " " for char in plain).split())


def _normal(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeCardError(code)
    return unicodedata.normalize("NFC", " ".join(value.split()))


def _texts(value: Any, code: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str) or not value:
        raise KnowledgeCardError(code)
    return tuple(_text(item, code) for item in value)


def _fact(raw: Mapping[str, Any]) -> KnowledgeFact:
    fact_id = _text(raw.get("id"), "KNOWLEDGE_FACT_INVALID")
    kind = raw.get("kind")
    months = raw.get("min_age_months")
    if kind not in KINDS or type(months) is not int or not 36 <= months <= 120:
        raise KnowledgeCardError("KNOWLEDGE_FACT_INVALID", detail=fact_id)
    text = _text(raw.get("text"), "KNOWLEDGE_FACT_INVALID")
    if not text.endswith(_SENTENCE_ENDINGS):
        raise KnowledgeCardError("KNOWLEDGE_FACT_NOT_A_SENTENCE", detail=fact_id)
    if len(text.split()) > MAX_FACT_WORDS:
        raise KnowledgeCardError("KNOWLEDGE_FACT_TOO_LONG", detail=fact_id)
    terms = _texts(raw.get("key_terms"), "KNOWLEDGE_FACT_INVALID")
    if any(_normal(term) not in _normal(text) for term in terms):
        raise KnowledgeCardError("KNOWLEDGE_FACT_TERM_NOT_IN_TEXT", detail=fact_id)
    part = raw.get("part")
    if kind == "PART" and (not isinstance(part, str) or not part.strip()):
        raise KnowledgeCardError("KNOWLEDGE_FACT_PART_REQUIRED", detail=fact_id)
    return KnowledgeFact(
        fact_id, kind, months, text, terms, part.strip() if kind == "PART" else None
    )


def parse_card(raw: Mapping[str, Any]) -> KnowledgeCard:
    card_id = _text(raw.get("card_id"), "KNOWLEDGE_CARD_INVALID")
    version = raw.get("version")
    status = raw.get("status")
    if type(version) is not int or version < 1 or status not in STATUSES:
        raise KnowledgeCardError("KNOWLEDGE_CARD_INVALID", detail=card_id)
    raw_facts = raw.get("facts")
    if not isinstance(raw_facts, Sequence) or isinstance(raw_facts, str):
        raise KnowledgeCardError("KNOWLEDGE_CARD_INVALID", detail=card_id)
    facts = tuple(_fact(item) for item in raw_facts)
    if len({fact.id for fact in facts}) != len(facts):
        raise KnowledgeCardError("KNOWLEDGE_CARD_DUPLICATE_FACT", detail=card_id)
    for kind in ("WHAT_IT_IS", "USE"):
        if not any(fact.kind == kind for fact in facts):
            raise KnowledgeCardError(f"KNOWLEDGE_CARD_MISSING_{kind}", detail=card_id)
    try:
        sources = tuple(
            KnowledgeSource(
                _text(item.get("title"), "KNOWLEDGE_CARD_INVALID"),
                _text(item.get("url"), "KNOWLEDGE_CARD_INVALID"),
                _text(item.get("checked_on"), "KNOWLEDGE_CARD_INVALID"),
            )
            for item in raw.get("sources", ())
        )
    except AttributeError:
        raise KnowledgeCardError("KNOWLEDGE_CARD_INVALID", detail=card_id) from None
    if any(not source.url.startswith("https://") for source in sources):
        raise KnowledgeCardError("KNOWLEDGE_CARD_INVALID", detail=card_id)
    return KnowledgeCard(
        card_id=card_id,
        version=version,
        status=status,
        subject_labels=_texts(raw.get("subject_labels"), "KNOWLEDGE_CARD_INVALID"),
        topic_ids=_texts(raw.get("topic_ids"), "KNOWLEDGE_CARD_INVALID"),
        facts=facts,
        motion_hints=_texts(raw.get("motion_hints"), "KNOWLEDGE_CARD_INVALID"),
        setting=_text(raw.get("setting"), "KNOWLEDGE_CARD_INVALID"),
        sources=sources,
        reviewed_by=raw.get("reviewed_by"),
        reviewed_on=raw.get("reviewed_on"),
        approved_sha256=raw.get("approved_sha256"),
    )


def content_sha256(card: KnowledgeCard) -> str:
    """Hash of everything a reviewer approved (not of the approval fields themselves)."""

    content = card.to_dict()
    for key in ("status", "reviewed_by", "reviewed_on", "approved_sha256"):
        content.pop(key)
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def approve_card(card: KnowledgeCard, *, reviewer: str, reviewed_on: str) -> KnowledgeCard:
    if not card.sources:
        raise KnowledgeCardError("KNOWLEDGE_CARD_SOURCE_REQUIRED", detail=card.card_id)
    if not reviewer.strip() or not reviewed_on.strip():
        raise KnowledgeCardError("KNOWLEDGE_CARD_REVIEWER_REQUIRED", detail=card.card_id)
    return replace(
        card,
        status="APPROVED",
        reviewed_by=reviewer.strip(),
        reviewed_on=reviewed_on.strip(),
        approved_sha256=content_sha256(card),
    )


def is_servable(card: KnowledgeCard) -> bool:
    return card.status == "APPROVED" and card.approved_sha256 == content_sha256(card)


def card_for_subject(cards: Iterable[KnowledgeCard], subject_label: str) -> KnowledgeCard | None:
    """The card whose label equals the confirmed main subject; a part of a label never matches."""

    wanted = _folded(subject_label)
    exact = _normal(subject_label)
    candidates = list(cards)
    # Prefer the accented spelling; the folded form counts only when it names a single card.
    for card in candidates:
        if any(_normal(label) == exact for label in card.subject_labels):
            return card
    folded = [
        card
        for card in candidates
        if any(_folded(label) == wanted for label in card.subject_labels)
    ]
    return folded[0] if len(folded) == 1 else None


def facts_for_child(
    card: KnowledgeCard, *, age_months: int, visible_features: Sequence[str]
) -> tuple[KnowledgeFact, ...]:
    """The facts of one video in story order: name, parts (seen ones first), then the use."""

    count = next((n for low, high, n in _FACTS_BY_AGE if low <= age_months <= high), None)
    if count is None:
        raise KnowledgeCardError("KNOWLEDGE_CARD_AGE_UNSUPPORTED", detail=str(age_months))
    suitable = [fact for fact in card.facts if fact.min_age_months <= age_months]
    names = [fact for fact in suitable if fact.kind == "WHAT_IT_IS"]
    uses = [fact for fact in suitable if fact.kind == "USE"]
    seen = f" {_folded(' '.join(visible_features))} "
    parts = sorted(
        (fact for fact in suitable if fact.kind == "PART"),
        key=lambda fact: (
            f" {_folded(fact.part or '')} " not in seen,
            # An older child first gets the facts written for that age.
            -fact.min_age_months,
        ),
    )
    if not names or not uses or len(parts) < count - 2:
        raise KnowledgeCardError("KNOWLEDGE_CARD_TOO_FEW_FACTS", detail=card.card_id)
    return (names[0], *parts[: count - 2], uses[0])


__all__ = [
    "KnowledgeCard",
    "KnowledgeCardError",
    "KnowledgeFact",
    "KnowledgeSource",
    "MAX_FACT_WORDS",
    "approve_card",
    "card_for_subject",
    "content_sha256",
    "facts_for_child",
    "is_servable",
    "parse_card",
]
