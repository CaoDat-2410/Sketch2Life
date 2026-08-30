from __future__ import annotations

import pytest

from sketch2life.benchmark.asr_scoring import (
    VIETNAMESE_ASR_NORMALIZER_VERSION,
    VietnameseAsrScoringNormalizerV1,
    character_error_rate,
    normalize_vietnamese_for_cer,
    normalize_vietnamese_text,
    tokenize_vietnamese_for_wer,
    word_error_rate,
)


def test_normalizer_applies_nfc_casefold_whitespace_and_punctuation_rules() -> None:
    raw = "\tĐI   ca\u0301, học—nhé!\n"

    assert normalize_vietnamese_text(raw) == "đi cá học nhé"
    assert tokenize_vietnamese_for_wer(raw) == ("đi", "cá", "học", "nhé")
    assert normalize_vietnamese_for_cer(raw) == "đicáhọcnhé"
    assert raw == "\tĐI   ca\u0301, học—nhé!\n"


def test_wer_tokens_and_cer_characters_are_separate_outputs() -> None:
    text = "Bé vẽ con đà điểu."

    assert tokenize_vietnamese_for_wer(text) == ("bé", "vẽ", "con", "đà", "điểu")
    assert normalize_vietnamese_for_cer(text) == "bévẽconđàđiểu"


def test_normalizer_does_not_translate_or_spell_correct() -> None:
    text = "khong biet red car"

    assert tokenize_vietnamese_for_wer(text) == ("khong", "biet", "red", "car")
    assert normalize_vietnamese_for_cer(text) == "khongbietredcar"


def test_normalizer_is_versioned_and_stateless() -> None:
    normalizer = VietnameseAsrScoringNormalizerV1()

    assert normalizer.version == VIETNAMESE_ASR_NORMALIZER_VERSION
    assert normalizer.normalize_for_wer("Đỏ!") == ("đỏ",)
    assert normalizer.normalize_for_cer("Đỏ!") == "đỏ"


def test_wer_and_cer_are_zero_for_an_identical_normalized_transcript() -> None:
    reference = "Bé vẽ con đà điểu."
    hypothesis = "bé vẽ con đà điểu"

    assert word_error_rate(reference, hypothesis) == pytest.approx(0.0)
    assert character_error_rate(reference, hypothesis) == pytest.approx(0.0)


def test_wer_counts_one_substitution_over_reference_token_count() -> None:
    reference = "con buom bay"
    hypothesis = "con buom bai"

    assert word_error_rate(reference, hypothesis) == pytest.approx(1 / 3)


def test_wer_counts_a_deletion_over_reference_token_count() -> None:
    reference = "con buom bay cao"
    hypothesis = "con buom cao"

    assert word_error_rate(reference, hypothesis) == pytest.approx(1 / 4)


def test_cer_counts_character_edits_over_reference_character_count() -> None:
    reference = "hello"
    hypothesis = "hallo"

    assert character_error_rate(reference, hypothesis) == pytest.approx(1 / 5)


def test_wer_and_cer_can_exceed_one_for_a_very_wrong_hypothesis() -> None:
    reference = "vi"
    hypothesis = "hoan toan khac"

    assert word_error_rate(reference, hypothesis) > 1.0
    assert character_error_rate(reference, hypothesis) > 1.0


def test_wer_and_cer_reject_an_empty_reference() -> None:
    with pytest.raises(ValueError, match="WER reference"):
        word_error_rate("", "anything")
    with pytest.raises(ValueError, match="CER reference"):
        character_error_rate("   ", "anything")
