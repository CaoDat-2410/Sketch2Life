"""Knowledge cards stored as one JSON file each in the backend package (FEAT-094)."""

from __future__ import annotations

import json
from pathlib import Path

from sketch2life.domain.knowledge_card import (
    KnowledgeCard,
    KnowledgeCardError,
    card_for_subject,
    is_servable,
    parse_card,
)

CARD_DIRECTORY = Path(__file__).resolve().parents[2] / "resources" / "knowledge_cards"


class KnowledgeCardRepository:
    def __init__(self, directory: Path = CARD_DIRECTORY) -> None:
        self._directory = Path(directory)
        self._cards: tuple[KnowledgeCard, ...] | None = None

    def all_cards(self) -> tuple[KnowledgeCard, ...]:
        """Every card on disk, drafts included. A broken file is an error, never skipped."""

        if self._cards is None:
            cards = []
            for path in sorted(self._directory.glob("*.json")):
                try:
                    cards.append(parse_card(json.loads(path.read_text(encoding="utf-8"))))
                except (OSError, UnicodeError, json.JSONDecodeError) as error:
                    raise KnowledgeCardError(
                        "KNOWLEDGE_CARD_UNREADABLE", detail=path.name
                    ) from error
            self._cards = tuple(cards)
        return self._cards

    def approved_for_subject(self, subject_label: str) -> KnowledgeCard | None:
        return card_for_subject(
            (card for card in self.all_cards() if is_servable(card)), subject_label
        )


__all__ = ["CARD_DIRECTORY", "KnowledgeCardRepository"]
