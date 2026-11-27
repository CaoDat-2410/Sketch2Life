"""The learning script of a Parent video (FEAT-094 plan Rev 2, section 6, and Amendment A).

One text: what the adult confirms is what the video says. The story model writes it; these rules are checked again here
so that a worker answer can never skip them. Pure code: no files, HTTP or model.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

SCENE_SECONDS: Final = 10
MIN_FACTS: Final = 3  # drafted facts may fall short of the band's number, never below this
FACT_SOURCES: Final = ("CARD", "LESSON", "AI_DRAFT")
_VERIFIED_SOURCES: Final = ("CARD",)
_FACT_KEYS: Final = ("id", "kind", "part", "text", "key_terms")
_CLASSIFIERS: Final = frozenset({"con", "chiếc", "cái"})
_PERSON_WORDS: Final = frozenset({"bé", "người", "mẹ", "bố", "bà", "ông", "gái", "trai"})
_CHILD_OPENINGS: Final = ("bé ", "em bé ", "con yêu ")
_PEOPLE_EN: Final = re.compile(
    r"\b(child|children|kid|kids|boy|boys|girl|girls|baby|toddler|person|people|man|woman|mother|father|mom|dad|"
    r"parent|parents|adult|adults|human|someone|hand|hands|finger|fingers)\b",
    re.IGNORECASE,
)


class LearningScriptError(ValueError):
    """A content-free code naming the first broken rule."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class LearningBand:
    min_months: int
    max_months: int
    scene_count: int
    scene_seconds: int
    max_words: int
    fact_count: int


BANDS: Final = (
    # FEAT-098: about twice the words and more facts in the same scene length. The word caps keep
    # today's caption reading speed inside a 10 s scene.
    LearningBand(36, 71, 5, SCENE_SECONDS, 25, 5),
    LearningBand(72, 107, 6, SCENE_SECONDS, 32, 6),
    LearningBand(108, 120, 7, SCENE_SECONDS, 32, 7),
)


def band_for_age_months(age_months: int) -> LearningBand:
    for band in BANDS:
        if type(age_months) is int and band.min_months <= age_months <= band.max_months:
            return band
    raise LearningScriptError("LEARNING_AGE_UNSUPPORTED")


def _normal(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _words(value: str) -> list[str]:
    return re.findall(r"\w+", _normal(value), flags=re.UNICODE)


def _subject_core(subject: str) -> str:
    words = _words(subject)
    return " ".join(word for word in words if word not in _CLASSIFIERS) or " ".join(words)


def _contains(text: str, phrase: str) -> bool:
    return f" {phrase} " in f" {' '.join(_words(text))} "


def _text(value: Any, *, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise LearningScriptError("LEARNING_SHAPE_INVALID")
    return value.strip()


def _prompt(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not 8 <= len(value.strip()) <= 300
        or any(ch.isalpha() and not ch.isascii() for ch in value)
        or _PEOPLE_EN.search(value)
    ):
        raise LearningScriptError("LEARNING_PROMPT_NOT_ALLOWED")
    return value.strip()


def _facts(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, Sequence) or isinstance(raw, str) or not raw:
        raise LearningScriptError("LEARNING_SHAPE_INVALID")
    facts = []
    for item in raw:
        if not isinstance(item, Mapping) or item.get("kind") not in ("WHAT_IT_IS", "PART", "USE"):
            raise LearningScriptError("LEARNING_SHAPE_INVALID")
        terms = item.get("key_terms")
        if not isinstance(terms, Sequence) or isinstance(terms, str) or not 1 <= len(terms) <= 4:
            raise LearningScriptError("LEARNING_SHAPE_INVALID")
        part = item.get("part")
        facts.append(
            {
                "id": _text(item.get("id"), limit=40),
                "kind": item["kind"],
                "part": None if part is None else _text(part, limit=60),
                "text": _text(item.get("text"), limit=200),
                "key_terms": [_text(term, limit=40) for term in terms],
            }
        )
    if len({fact["id"] for fact in facts}) != len(facts):
        raise LearningScriptError("LEARNING_SHAPE_INVALID")
    return facts


def check_learning_script(
    story: Mapping[str, Any],
    learning: Any,
    *,
    request: Mapping[str, Any],
    subject: str,
) -> dict[str, Any]:
    """The learning block to store, or ``LearningScriptError``."""

    if not isinstance(learning, Mapping) or learning.get("fact_source") not in FACT_SOURCES:
        raise LearningScriptError("LEARNING_SHAPE_INVALID")
    facts = _facts(learning.get("facts"))
    given = request.get("facts") or []
    if given:
        wanted = {fact["id"]: (fact["text"], list(fact["key_terms"])) for fact in given}
        if any(wanted.get(fact["id"]) != (fact["text"], fact["key_terms"]) for fact in facts):
            raise LearningScriptError("LEARNING_FACT_CHANGED")
    scenes = story.get("scenes")
    plan = learning.get("scenes")
    count = request["scene_count"]
    if not isinstance(scenes, list) or not isinstance(plan, list) or len(scenes) != count or len(plan) != count:
        raise LearningScriptError("LEARNING_SCENE_COUNT")
    by_id = {fact["id"]: fact for fact in facts}
    core = _subject_core(subject)
    subject_is_person = bool(_PERSON_WORDS & set(_words(subject)))
    told: list[str] = []
    named = 0
    checked = []
    for index, (scene, entry) in enumerate(zip(scenes, plan, strict=True), start=1):
        if not isinstance(entry, Mapping) or entry.get("scene_index") != index:
            raise LearningScriptError("LEARNING_SHAPE_INVALID")
        narration = _text(scene.get("narration"), limit=500)
        if scene.get("duration_ms") != request["scene_seconds"] * 1000:
            raise LearningScriptError("LEARNING_SCENE_LENGTH")
        if len(narration.split()) > request["max_words"]:
            raise LearningScriptError("LEARNING_NARRATION_TOO_LONG")
        if not subject_is_person and _normal(narration).startswith(_CHILD_OPENINGS):
            raise LearningScriptError("LEARNING_CHILD_AS_PROTAGONIST")
        named += _contains(narration, core)
        fact_id, also = entry.get("fact_id"), entry.get("also_fact_id")
        if also is not None and fact_id is None:
            raise LearningScriptError("LEARNING_SHAPE_INVALID")  # a second fact needs a first one
        for told_id in (fact_id, also):
            if told_id is None:
                continue
            if told_id not in by_id:
                raise LearningScriptError("LEARNING_FACT_UNKNOWN")
            told.append(told_id)
            if any(_normal(term) not in _normal(narration) for term in by_id[told_id]["key_terms"]):
                raise LearningScriptError("LEARNING_FACT_TERM_MISSING")
        part = entry.get("part")
        checked.append(
            {
                "scene_index": index,
                "fact_id": fact_id,
                **({} if also is None else {"also_fact_id": also}),
                "key_term": _text(entry.get("key_term"), limit=60),
                "part": None if part is None else _text(part, limit=60),
                "action_en": _prompt(entry.get("action_en")),
                "setting_en": _prompt(entry.get("setting_en")),
            }
        )
    # Facts from a card or the lesson are all told; drafted facts may be fewer than asked, never
    # more.
    fewest = len(given) if given else MIN_FACTS
    if sorted(told) != sorted(by_id) or not fewest <= len(by_id) <= request["fact_count"]:
        raise LearningScriptError("LEARNING_FACT_NOT_TOLD_ONCE")
    if named < 3:
        raise LearningScriptError("LEARNING_SUBJECT_NOT_REPEATED")
    return {"fact_source": learning["fact_source"], "facts": facts, "scenes": checked}


def learning_view(learning: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """What the adult sees beside the story: the learning points and whether a person had checked them."""

    if not learning:
        return None
    return {
        "fact_source": learning["fact_source"],
        "verified": learning["fact_source"] in _VERIFIED_SOURCES,
        "points": [fact["text"] for fact in learning["facts"]],
    }


__all__ = [
    "BANDS",
    "FACT_SOURCES",
    "LearningBand",
    "LearningScriptError",
    "SCENE_SECONDS",
    "band_for_age_months",
    "check_learning_script",
    "learning_view",
]
