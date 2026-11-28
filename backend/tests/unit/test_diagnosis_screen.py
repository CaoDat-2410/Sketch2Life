"""BR-20 no-diagnosis screen (V4-B T-12b-fix; SRS l.266 and FR-C-07 l.501)."""

from __future__ import annotations

import pytest

from sketch2life.domain.be1_profile_revisions import (
    ProfileRevisionRuleViolation,
    normalize_interests,
)
from sketch2life.domain.diagnosis_screen import fold, looks_like_diagnosis
from sketch2life.domain.parent_profiles import (
    ParentProfileError,
    ProfileSnapshot,
    validate_snapshot,
)
from sketch2life.domain.support_needs import SupportNeedsRuleViolation, validate_payload

ECHO_MARKER = "Synthetic-secret-marker"


@pytest.mark.parametrize(
    "text",
    [
        "autism",
        "He has Autism",
        "autistic spectrum",
        "ADHD",
        "adhd.",
        "dyslexia",
        "Down syndrome",
        "anxiety disorder",
        "depression",
        "the doctor made a diagnosis",
        "chẩn đoán",
        "CHẨN ĐOÁN tự kỷ",
        "tự kỷ",
        "tăng động giảm chú ý",
        "rối loạn ngôn ngữ",
        "hội chứng Down",
        "trầm cảm",
        "động kinh",
        "bại não",
    ],
)
def test_a_text_that_names_a_diagnosis_is_caught(text: str) -> None:
    assert looks_like_diagnosis(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "xếp hình khủng long",
        "vẽ tranh",
        "dinosaurs and trains",
        "football",
        "add and subtract",
        "reading with mum",
        "needs a quiet corner after lunch",
        "thích nghe nhạc",
        "tập đếm",
        "paradise island",
        "",
    ],
)
def test_ordinary_interests_and_support_wording_pass(text: str) -> None:
    assert looks_like_diagnosis(text) is False


def test_the_fold_removes_marks_and_the_stroked_d_and_lower_cases() -> None:
    assert fold("Chẩn Đoán") == "chan doan"
    assert fold("ĐÃ") == "da"


def test_the_screen_matches_at_a_word_start_only() -> None:
    assert looks_like_diagnosis("misdiagnosis") is False  # inside a word, not a word start
    assert looks_like_diagnosis("adhdx") is False  # an acronym needs a whole word


def test_teacher_interests_refuse_a_diagnosis_with_a_code_and_no_echo() -> None:
    with pytest.raises(ProfileRevisionRuleViolation) as caught:
        normalize_interests(["dinosaurs", f"autism {ECHO_MARKER}"])
    assert caught.value.code == "DIAGNOSIS_LIKE"
    assert ECHO_MARKER not in str(caught.value)
    assert normalize_interests(["dinosaurs", "trains"]) == ("dinosaurs", "trains")


@pytest.mark.parametrize("field", ["category", "note"])
def test_support_needs_input_refuses_a_diagnosis_in_either_field(field: str) -> None:
    kwargs = {"category": None, "note": None, field: f"has autism {ECHO_MARKER}"}
    with pytest.raises(SupportNeedsRuleViolation) as caught:
        validate_payload(**kwargs)  # type: ignore[arg-type]
    assert (caught.value.field, caught.value.code) == (field, "DIAGNOSIS_LIKE")
    assert ECHO_MARKER not in str(caught.value)
    assert validate_payload("sensory", "needs a quiet corner").note == "needs a quiet corner"


def test_the_parent_interests_summary_refuses_a_diagnosis() -> None:
    snapshot = ProfileSnapshot(
        display_name="Synthetic Mina", age_months=60, interests_summary=f"adhd {ECHO_MARKER}"
    )
    with pytest.raises(ParentProfileError) as caught:
        validate_snapshot(snapshot)
    assert caught.value.field_errors == [{"field": "interests_summary", "code": "DIAGNOSIS_LIKE"}]
    assert ECHO_MARKER not in str(caught.value)
    ok = ProfileSnapshot(
        display_name="Synthetic Mina", age_months=60, interests_summary="dinosaurs"
    )
    validate_snapshot(ok)


@pytest.mark.parametrize(
    "text",
    [
        "tự  kỷ",  # double space
        "cerebral   palsy",
        "tự kỉ",  # the common spelling
        "tu ki",
        "tu ky",
        "tự k​ỷ",  # zero-width space inside a word
        "ch‍ẩn đoán",
        "chẩn-đoán",
        "tự_kỷ",
        "tăng-động",
        "a.d.h.d",
        "A D H D",
        "ＡＤＨＤ",  # fullwidth
        "ASD",
        "tăng động giảm chú ý",
        "tang dong",
        "hội chứng Down",
        "hoi chung down",
        "bại não",
        "bai nao",
        "tự kỷ",  # a decomposed hook above
    ],
)
def test_the_screen_catches_separator_spacing_and_spelling_variants(text: str) -> None:
    assert looks_like_diagnosis(text) is True


@pytest.mark.parametrize(
    "text",
    ["tặng đồng hồ", "hỏi chung chung", "bãi nào", "asdf", "a b", "ý tưởng", "task done"],
)
def test_the_toned_vietnamese_phrases_do_not_hit_look_alikes(text: str) -> None:
    assert looks_like_diagnosis(text) is False
