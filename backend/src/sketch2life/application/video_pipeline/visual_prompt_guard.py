"""Keep each scene to what the child drew (FEAT-093 Amendment D, live Run 1).

A scene prompt that mentions a child made the video model paint a new person in another style beside the drawing. When
no person is in the drawing, clauses that name people are removed before the prompt reaches the image and video models,
and the prompt says that nothing new enters. This never fails a run. It also tells which main subjects fly or float, so
that every other one is placed on the ground instead of in the middle of the frame.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Final

from sketch2life.application.subject_role_scoring import fold

CLOSING: Final = "Only the drawn subjects are visible; nothing new enters the frame."
_FALLBACK_SUBJECT: Final = "The drawn subject moves gently."
_PEOPLE: Final = re.compile(
    r"\b(child|children|kid|kids|boy|boys|girl|girls|baby|toddler|person|people|man|woman|mother|father|mom|dad|"
    r"parent|parents|adult|adults|human|someone|hand|hands|finger|fingers)\b",
    re.IGNORECASE,
)
_PERSON_LABELS: Final = ("nguoi", "be gai", "be trai", "em be", "ban nho", "cong chua", "hoang tu", "cau be", "co be", "gia dinh")
_PERSON_EXACT: Final = frozenset({"me", "bo", "ba", "be"})
_AIRBORNE: Final = (
    "chim", "buom", "may bay", "bong bay", "bong bong", "dieu", "may", "mat troi", "mat trang", "ngoi sao", "ong",
    "chuon chuon", "ca", "thuyen",
)


def _has_phrase(folded: str, phrases: Iterable[str]) -> bool:
    padded = f" {' '.join(folded.split())} "
    return any(f" {phrase} " in padded for phrase in phrases)


def person_is_drawn(labels: Iterable[str]) -> bool:
    return any(
        fold(label).strip() in _PERSON_EXACT or _has_phrase(fold(label), _PERSON_LABELS) for label in labels
    )


def is_airborne(label: str) -> bool:
    return _has_phrase(fold(label), _AIRBORNE)


def drawn_only_prompt(prompt: str, *, person_drawn: bool) -> str:
    if person_drawn:
        return prompt
    clauses = [part for part in re.split(r"(?<=[.!?;,])\s+", prompt.strip()) if part]
    kept = [part for part in clauses if not _PEOPLE.search(part)]
    body = " ".join(kept).strip().rstrip(" ,;")
    if len(kept) != len(clauses) or len(body) < 8:
        body = f"{_FALLBACK_SUBJECT} {body}".strip()
    if not body.endswith((".", "!", "?")):
        body = f"{body}."
    return f"{body} {CLOSING}"


__all__ = ["CLOSING", "drawn_only_prompt", "is_airborne", "person_is_drawn"]
