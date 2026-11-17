"""Versioned, pure text preparation for Vietnamese ASR WER and CER scoring.

These functions derive benchmark scoring views from a raw transcript.  They never mutate,
persist, translate, spell-correct, or otherwise become canonical product text.
"""

import unicodedata
from collections.abc import Sequence

VIETNAMESE_ASR_NORMALIZER_VERSION = "vi-asr-normalizer-v1"


def normalize_vietnamese_text(text: str) -> str:
    """Apply the frozen v1 text rules and return the whitespace-preserving view.

    Rules, in order: NFC normalization, Unicode casefolding, punctuation-to-space
    conversion, and Unicode whitespace collapsing.  Diacritics and ``đ`` are retained.
    """

    normalized = unicodedata.normalize("NFC", text).casefold()
    normalized = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in normalized
    )
    return " ".join(normalized.split())


def tokenize_vietnamese_for_wer(text: str) -> tuple[str, ...]:
    """Return the independent normalized token sequence used by WER."""

    normalized = normalize_vietnamese_text(text)
    return tuple(normalized.split())


def normalize_vietnamese_for_cer(text: str) -> str:
    """Return the independent normalized character sequence used by CER."""

    normalized = normalize_vietnamese_text(text)
    return "".join(normalized.split())


# Concise aliases for callers that already know the input is a scoring-only view.
normalize_for_wer = tokenize_vietnamese_for_wer
normalize_for_cer = normalize_vietnamese_for_cer


class VietnameseAsrScoringNormalizerV1:
    """Stateless versioned façade for the two separate scoring outputs."""

    version = VIETNAMESE_ASR_NORMALIZER_VERSION

    @staticmethod
    def normalize_for_wer(text: str) -> tuple[str, ...]:
        return tokenize_vietnamese_for_wer(text)

    @staticmethod
    def normalize_for_cer(text: str) -> str:
        return normalize_vietnamese_for_cer(text)


def _levenshtein_distance(reference: Sequence[object], hypothesis: Sequence[object]) -> int:
    """Classic single-operation (insert/delete/substitute) edit distance, O(len product) space."""

    if not reference:
        return len(hypothesis)
    if not hypothesis:
        return len(reference)

    previous_row = list(range(len(hypothesis) + 1))
    for i, ref_item in enumerate(reference, start=1):
        current_row = [i] + [0] * len(hypothesis)
        for j, hyp_item in enumerate(hypothesis, start=1):
            deletion = previous_row[j] + 1
            insertion = current_row[j - 1] + 1
            substitution = previous_row[j - 1] + (ref_item != hyp_item)
            current_row[j] = min(deletion, insertion, substitution)
        previous_row = current_row
    return previous_row[-1]


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Normalized-token WER using the frozen `vi-asr-normalizer-v1` WER view.

    Undefined (raises `ValueError`) when the reference normalizes to zero tokens: WER-eligible
    fixtures always carry a non-empty reference transcript per the Round-1 fixture contract, so
    an empty reference here signals a caller error, not a legitimate zero-length denominator.
    """

    reference_tokens = tokenize_vietnamese_for_wer(reference)
    hypothesis_tokens = tokenize_vietnamese_for_wer(hypothesis)
    if not reference_tokens:
        raise ValueError("WER reference must normalize to at least one token")
    return _levenshtein_distance(reference_tokens, hypothesis_tokens) / len(reference_tokens)


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Normalized-character CER using the frozen `vi-asr-normalizer-v1` CER view.

    Undefined (raises `ValueError`) when the reference normalizes to zero characters, for the
    same reason as `word_error_rate`.
    """

    reference_chars = normalize_vietnamese_for_cer(reference)
    hypothesis_chars = normalize_vietnamese_for_cer(hypothesis)
    if not reference_chars:
        raise ValueError("CER reference must normalize to at least one character")
    return _levenshtein_distance(reference_chars, hypothesis_chars) / len(reference_chars)
