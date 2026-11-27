"""FEAT-098 amendment A: the spoken-text filter compares Vietnamese words with their accents.

Without accents "sừng" (horn) read as "súng" (gun) and "từ từ" (slowly) as "tự tử"; both the video's check and the story
writer's check must refuse the listed words and nothing that only looks like them.
"""

from __future__ import annotations

import unicodedata

import pytest

from sketch2life.application.video_pipeline.story_timeline import TimelineError, check_line_text

from test_learning_rule_parity import _worker

ALLOWED = [
    "Nhiều hươu đực có sừng và thay sừng theo mùa.",
    "Rùa bò từ từ về phía hồ nước.",
    "Cây cần bổ sung thêm nước mỗi ngày.",
    "Gà con sung sướng chạy quanh sân.",
    "Quả sung chín mọc trên thân cây.",
    "Mùa thu lá cây đổi sang nhiều màu mè.",
    "Tủ gỗ đựng sách nằm ở góc phòng.",
]
REFUSED = [
    "Bạn nhỏ cầm khẩu súng đồ chơi.",
    "Con cá nằm im vì đã chết.",
    "Hai bạn đánh nhau ở sân trường.",
    "Chú ấy uống rượu say khướt.",
    "Trong rừng có ma quỷ rình rập.",
    "Trong rừng có ma quỉ rình rập.",
    "Sói muốn giết chú thỏ nhỏ.",
    "Khắp nơi đầy máu me đáng sợ.",
    "Chuyện TỰ TỬ không dành cho trẻ.",
    unicodedata.normalize("NFD", "Chuyện tự tử không dành cho trẻ."),
    # Typed without any accent, a listed word is still refused.
    "Con ca nam im vi da chet.",
    "Ban nho cam khau sung do choi.",
]


@pytest.mark.parametrize("text", ALLOWED)
def test_ordinary_words_are_spoken(text: str) -> None:
    assert check_line_text(text)
    assert _worker().has_banned_word(text) is False


@pytest.mark.parametrize("text", REFUSED)
def test_listed_words_are_refused_by_both_checks(text: str) -> None:
    with pytest.raises(TimelineError) as error:
        check_line_text(text)
    assert error.value.code == "LINE_TEXT_NOT_ALLOWED"
    assert _worker().has_banned_word(text) is True


def test_a_listed_word_is_matched_as_a_whole_word() -> None:
    assert check_line_text("Bạn nhỏ thích chơi xếp hình chữ nhật.")
    assert _worker().has_banned_word("Rượung") is False
