from __future__ import annotations

import pytest

from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    ObservedTextV1,
    ProhibitedLexiconEntryV1,
    ProhibitedLexiconV1,
    TextLanguageDeclarationV1,
    VisionProhibitedClaimCategory,
    vision_policy_match_view,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    SYNTHETIC_LEXICON_TERMS,
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)


def _text(value: str) -> ObservedTextV1:
    return ObservedTextV1(value=value, language=TextLanguageDeclarationV1(status="NOT_DETERMINED"))


def _single_entry_lexicon(
    term_normalized: str,
    match_mode: str = "WHOLE_TOKEN_SEQUENCE",
    category: VisionProhibitedClaimCategory = VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
) -> ProhibitedLexiconV1:
    return ProhibitedLexiconV1(
        lexicon_version="test-lexicon-v1",
        match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
        entries=(
            ProhibitedLexiconEntryV1(
                term_normalized=term_normalized, category=category, match_mode=match_mode
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Match-view mechanics
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ("marker word", "Marker Word", "MARKER WORD", "MaRkEr WoRd"))
def test_match_view_case_variants_produce_the_same_view(variant: str) -> None:
    assert vision_policy_match_view(variant) == "marker word"


@pytest.mark.parametrize(
    "field",
    (
        "marker-word.",
        "(marker-word)",
        "marker_word!",
        "marker, word",
    ),
)
def test_match_view_punctuation_at_and_between_boundaries_is_mapped_to_space(field: str) -> None:
    policy = LexicalRegressionContentPolicy(_single_entry_lexicon("marker word"))
    assert policy.evaluate((_text(field),)) is not None


def test_match_view_non_adjacent_tokens_do_not_trigger() -> None:
    policy = LexicalRegressionContentPolicy(_single_entry_lexicon("marker word"))
    assert policy.evaluate((_text("marker unrelated word"),)) is None


def test_match_view_never_matches_a_substring_inside_a_larger_word() -> None:
    policy = LexicalRegressionContentPolicy(_single_entry_lexicon("cam"))
    assert policy.evaluate((_text("camera"),)) is None
    assert policy.evaluate((_text("a cam nearby"),)) is not None


def test_match_view_preserves_and_matches_vietnamese_diacritics() -> None:
    policy = LexicalRegressionContentPolicy(_single_entry_lexicon("đáng lo tâm lý"))
    assert policy.evaluate((_text("rất Đáng Lo Tâm Lý, có thể"),)) is not None
    assert vision_policy_match_view("Đ") == "đ"


def test_match_view_symbol_category_does_not_create_a_token_boundary() -> None:
    assert vision_policy_match_view("a★b") == "a★b"
    assert vision_policy_match_view("a+b") == "a+b"


def test_match_view_stored_value_is_never_mutated_by_policy_evaluation() -> None:
    text = _text("Marker, Word!")
    policy = LexicalRegressionContentPolicy(_single_entry_lexicon("marker word"))

    policy.evaluate((text,))

    assert text.value == "Marker, Word!"


def test_whole_field_mode_requires_an_exact_field_match() -> None:
    policy = LexicalRegressionContentPolicy(
        _single_entry_lexicon("marker word", match_mode="WHOLE_FIELD")
    )
    assert policy.evaluate((_text("marker word"),)) is not None
    assert policy.evaluate((_text("a marker word here"),)) is None


def test_lexicon_match_view_version_mismatch_fails_construction_deterministically() -> None:
    mismatched = ProhibitedLexiconV1(
        lexicon_version="test-lexicon-v1",
        match_view_version="vision-policy-match-view-v1",
        entries=(),
    )
    with pytest.raises(ValueError, match="match_view_version"):
        LexicalRegressionContentPolicy(mismatched)


# ---------------------------------------------------------------------------
# Canonical lexicon-entry enforcement: term_normalized must already be in
# vision-policy-match-view-v2 form; it is never silently normalized.
# ---------------------------------------------------------------------------


def test_canonical_lexicon_entry_is_accepted() -> None:
    entry = ProhibitedLexiconEntryV1(
        term_normalized="marker word",
        category=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
        match_mode="WHOLE_TOKEN_SEQUENCE",
    )
    assert entry.term_normalized == "marker word"


@pytest.mark.parametrize(
    "term_normalized",
    (
        "Marker Word",
        "MARKER WORD",
        "marker-word",
        "marker, word",
        "marker_word",
        "  marker word  ",
        "marker  word",
        "marker\tword",
    ),
)
def test_non_canonical_lexicon_entry_forms_are_rejected(term_normalized: str) -> None:
    with pytest.raises(ValueError, match="canonical"):
        ProhibitedLexiconEntryV1(
            term_normalized=term_normalized,
            category=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
            match_mode="WHOLE_TOKEN_SEQUENCE",
        )


def test_lexicon_entry_that_tokenizes_to_nothing_is_rejected() -> None:
    with pytest.raises(ValueError):
        ProhibitedLexiconEntryV1(
            term_normalized="---",
            category=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
            match_mode="WHOLE_TOKEN_SEQUENCE",
        )


def test_lexicon_entry_term_is_never_silently_normalized() -> None:
    with pytest.raises(ValueError):
        ProhibitedLexiconEntryV1(
            term_normalized="Marker Word",
            category=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
            match_mode="WHOLE_TOKEN_SEQUENCE",
        )
    # Constructing with the already-canonical form succeeds and preserves it verbatim.
    entry = ProhibitedLexiconEntryV1(
        term_normalized=vision_policy_match_view("Marker Word"),
        category=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
        match_mode="WHOLE_TOKEN_SEQUENCE",
    )
    assert entry.term_normalized == "marker word"


def test_canonical_entry_matching_behavior_is_preserved() -> None:
    policy = LexicalRegressionContentPolicy(_single_entry_lexicon("marker word"))
    assert policy.evaluate((_text("Marker, Word!"),)) is not None
    assert policy.evaluate((_text("unrelated text"),)) is None


# ---------------------------------------------------------------------------
# Synthetic default lexicon: one entry per closed category
# ---------------------------------------------------------------------------


def test_synthetic_lexicon_covers_exactly_the_six_closed_categories() -> None:
    lexicon = synthetic_prohibited_lexicon()
    categories = {entry.category for entry in lexicon.entries}
    assert categories == set(VisionProhibitedClaimCategory)
    assert lexicon.match_view_version == VISION_POLICY_MATCH_VIEW_VERSION


@pytest.mark.parametrize(("term", "category"), SYNTHETIC_LEXICON_TERMS)
def test_synthetic_lexicon_blocks_its_own_category_and_no_other(
    term: str, category: VisionProhibitedClaimCategory
) -> None:
    policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
    result = policy.evaluate((_text(term),))
    assert result is category


def test_compliant_text_passes_the_synthetic_lexicon() -> None:
    policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
    assert policy.evaluate((_text("a child drew a sun and a house"),)) is None


def test_policy_never_returns_more_than_the_closed_category_token() -> None:
    policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
    term, category = SYNTHETIC_LEXICON_TERMS[0]
    result = policy.evaluate((_text(term),))
    assert result is category
    assert isinstance(result, VisionProhibitedClaimCategory)
