"""The ``learning`` block of a Parent story request (FEAT-094 phase 4).

Facts come from the pinned lesson notes, else from an approved card of the confirmed main subject, else the worker
drafts them. Only age, the allow-listed interest tags and card text leave the backend; no profile identity or free text.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from sketch2life.application.services.parent_activity_suggestions import interest_tags
from sketch2life.domain.knowledge_card import KnowledgeCardError, facts_for_child
from sketch2life.domain.learning_script import LearningScriptError, band_for_age_months
from sketch2life.infrastructure.knowledge.card_repository import KnowledgeCardRepository

REQUEST_SCHEMA: Final = "sketch2life.learning-request.v1"
MAX_INTEREST_TAGS: Final = 8


def build_learning_request(
    *,
    context: Mapping[str, Any],
    subject: str,
    visible_features: Sequence[str],
    lesson_notes: str | None,
    enabled: bool,
    cards: KnowledgeCardRepository | None = None,
) -> dict[str, Any] | None:
    """The block to send, or ``None`` when learning scripts are off or the age has no band."""

    age = context.get("age_months")
    if not enabled or type(age) is not int:
        return None
    try:
        band = band_for_age_months(age)
    except LearningScriptError:
        return None
    facts: list[dict[str, Any]] = []
    fact_count = band.fact_count
    motion: list[str] = []
    setting = ""
    source = "LESSON" if lesson_notes else "AI_DRAFT"
    if not lesson_notes:
        try:
            card = (cards or KnowledgeCardRepository()).approved_for_subject(subject)
            if card is not None:
                chosen = facts_for_child(card, age_months=age, visible_features=visible_features)
                if chosen and len(chosen) <= band.fact_count:
                    fact_count = len(chosen)
                    facts = [
                        {
                            "id": fact.id,
                            "kind": fact.kind,
                            "part": fact.part,
                            "text": fact.text,
                            "key_terms": list(fact.key_terms),
                        }
                        for fact in chosen
                    ]
                    motion = [hint[:120] for hint in card.motion_hints[:6]]
                    setting = card.setting[:200]
                    source = "CARD"
        except KnowledgeCardError:
            facts = []  # a card that cannot serve this child never blocks the story
    return {
        "schema_version": REQUEST_SCHEMA,
        "scene_count": band.scene_count,
        "scene_seconds": band.scene_seconds,
        "max_words": band.max_words,
        "fact_count": fact_count,
        "facts": facts,
        "fact_source": source,
        "motion_hints": motion,
        "setting": setting,
        "interest_tags": [
            tag[:40] for tag in interest_tags(str(context.get("interests_summary") or ""))[:MAX_INTEREST_TAGS]
        ],
    }


__all__ = ["REQUEST_SCHEMA", "build_learning_request"]
