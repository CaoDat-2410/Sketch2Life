"""The unsafe-action filter must catch accented Vietnamese text, including the d-stroke letter."""

from __future__ import annotations

import pytest

from sketch2life.application.services.parent_activity_suggestions import (
    _contains_unsafe_action,
)


@pytest.mark.parametrize(
    "text",
    [
        "Cho trẻ chơi gần ổ điện trong phòng",
        "Trẻ nghịch dây điện để quan sát",
        "Cùng băng qua đường lớn để đếm xe",
        "Đốt lửa nhỏ để xem khói",
        "ĐỐT LỬA trong sân",
    ],
)
def test_accented_unsafe_actions_are_refused(text: str) -> None:
    assert _contains_unsafe_action(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Không chơi gần ổ điện, chỉ quan sát màu lá",
        "Cùng quan sát hình tròn trên giấy",
    ],
)
def test_negated_or_safe_text_is_allowed(text: str) -> None:
    assert _contains_unsafe_action(text) is False
