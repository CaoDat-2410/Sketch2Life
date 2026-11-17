"""Deterministic, synthetic-only lexical regression content policy (P2-T3 Phase A).

Stated limitation: this is a known-violation regression check against an approved closed
term list, not a semantic-safety guarantee. A paraphrase absent from the lexicon is not
detected. See `plan/P2_T3_VISION_RESEARCH_PLAN.md`, "Safety boundary, policy limitation,
and the Phase B semantic-safety gate".
"""

from __future__ import annotations

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    ObservedTextV1,
    ProhibitedLexiconEntryV1,
    ProhibitedLexiconV1,
    VisionProhibitedClaimCategory,
    vision_policy_match_view_tokens,
)


class LexicalRegressionContentPolicy(ObservableContentPolicyV1):
    """`ObservableContentPolicyV1` Phase A implementation. Never exposes matched text."""

    def __init__(self, lexicon: ProhibitedLexiconV1) -> None:
        if lexicon.match_view_version != VISION_POLICY_MATCH_VIEW_VERSION:
            raise ValueError(
                "lexicon match_view_version "
                f"{lexicon.match_view_version!r} does not match the active "
                f"{VISION_POLICY_MATCH_VIEW_VERSION!r}"
            )
        self._lexicon = lexicon

    @property
    def content_policy_version(self) -> str:
        return self._lexicon.lexicon_version

    @property
    def policy_match_view_version(self) -> str:
        return self._lexicon.match_view_version

    def evaluate(self, texts: tuple[ObservedTextV1, ...]) -> VisionProhibitedClaimCategory | None:
        for text in texts:
            field_tokens = vision_policy_match_view_tokens(text.value)
            for entry in self._lexicon.entries:
                if _matches(field_tokens, entry):
                    return entry.category
        return None


def _matches(field_tokens: tuple[str, ...], entry: ProhibitedLexiconEntryV1) -> bool:
    entry_tokens = tuple(entry.term_normalized.split(" "))
    if entry.match_mode == "WHOLE_FIELD":
        return field_tokens == entry_tokens
    return _contains_subsequence(field_tokens, entry_tokens)


def _contains_subsequence(haystack: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    if not needle:
        return False
    span = len(needle)
    return any(
        haystack[index : index + span] == needle for index in range(len(haystack) - span + 1)
    )


SYNTHETIC_LEXICON_TERMS: tuple[tuple[str, VisionProhibitedClaimCategory], ...] = (
    (
        "synthetic psychological inference marker",
        VisionProhibitedClaimCategory.PSYCHOLOGICAL_INFERENCE_CLAIM,
    ),
    ("synthetic personality claim marker", VisionProhibitedClaimCategory.PERSONALITY_CLAIM),
    ("synthetic diagnostic claim marker", VisionProhibitedClaimCategory.DIAGNOSTIC_CLAIM),
    ("synthetic mental state claim marker", VisionProhibitedClaimCategory.MENTAL_STATE_CLAIM),
    ("synthetic trauma claim marker", VisionProhibitedClaimCategory.TRAUMA_CLAIM),
    ("synthetic developmental claim marker", VisionProhibitedClaimCategory.DEVELOPMENTAL_CLAIM),
)


def synthetic_prohibited_lexicon() -> ProhibitedLexiconV1:
    """Deterministic, synthetic-only Phase A lexicon. Contains no real child data.

    Governance: reviewed by the project owner; changing the category set, governance, or
    policy/match-view contract needs a new plan-and-approval review. A synthetic-entry
    update must bump `lexicon_version` and be recorded in feature-local evidence.
    """

    entries = tuple(
        ProhibitedLexiconEntryV1(
            term_normalized=term,
            category=category,
            match_mode="WHOLE_TOKEN_SEQUENCE",
        )
        for term, category in SYNTHETIC_LEXICON_TERMS
    )
    return ProhibitedLexiconV1(
        lexicon_version="vision-prohibited-lexicon-fixture-v1",
        match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
        entries=entries,
    )
