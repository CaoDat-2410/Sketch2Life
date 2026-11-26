"""FEAT-093 Amendment D: backend gates and helpers that turned recoverable cases into failures."""

from __future__ import annotations

from typing import Any

import pytest

from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    _has_incomplete_vietnamese_sentence_tail,
    generate_activity_suggestions,
)
from sketch2life.infrastructure.ai.modal_qwen_warm_up import QwenWarmUp
from sketch2life.infrastructure.config.settings import Settings


@pytest.mark.parametrize("text", ["Que dài khoảng 5 cm.", "Chuẩn bị một vòng tròn rộng 1 m."])
def test_a_measurement_after_a_number_ends_a_sentence(text: str) -> None:
    assert not _has_incomplete_vietnamese_sentence_tail(text)


@pytest.mark.parametrize("text", ["Bé đi tới cái c.", "Que dài khoảng vài cm."])
def test_a_clipped_syllable_is_still_incomplete(text: str) -> None:
    assert _has_incomplete_vietnamese_sentence_tail(text)


def _rejected() -> ParentActivitySuggestionError:
    return ParentActivitySuggestionError("PARENT_ACTIVITY_QUALITY_GATE_REJECTED", diagnostic_code="X")


def test_a_rejected_activity_answer_is_generated_once_more() -> None:
    calls: list[int] = []

    def resolve(answer: int) -> dict[str, Any]:
        if answer == 1:
            raise _rejected()
        return {"answer": answer}

    refused: list[str | None] = []

    answer, result = generate_activity_suggestions(
        lambda: calls.append(1) or len(calls), resolve, on_rejected=lambda error: refused.append(error.diagnostic_code)
    )

    assert (answer, result) == (2, {"answer": 2})
    assert refused == ["X"]


def test_a_second_rejection_and_other_errors_are_final() -> None:
    calls: list[int] = []

    def reject(_answer: Any) -> dict[str, Any]:
        raise _rejected()

    with pytest.raises(ParentActivitySuggestionError):
        generate_activity_suggestions(lambda: calls.append(1), reject)
    assert len(calls) == 2

    def broken(_answer: Any) -> dict[str, Any]:
        raise ParentActivitySuggestionError("MODAL_OUTPUT_CONTRACT_INVALID")

    calls.clear()
    with pytest.raises(ParentActivitySuggestionError):
        generate_activity_suggestions(lambda: calls.append(1), broken)
    assert len(calls) == 1


def test_the_custom_topic_switch_exists_and_is_off_by_default() -> None:
    assert Settings.model_fields["parent_topic_subject_ai_enabled"].default is False


class _Function:
    def __init__(self, error: Exception | None = None) -> None:
        self.payloads: list[dict[str, Any]] = []
        self.error = error

    def spawn(self, payload: dict[str, Any]) -> None:
        self.payloads.append(payload)
        if self.error is not None:
            raise self.error


def test_the_engine_is_warmed_at_most_once_per_window() -> None:
    clock = [1_000.0]
    function = _Function()
    warm_up = QwenWarmUp(function=function, clock=lambda: clock[0])

    assert warm_up.request() is True
    assert warm_up.request() is False
    clock[0] += 301
    assert warm_up.request() is True
    assert function.payloads == [{"warmup": True}, {"warmup": True}]


def test_a_failed_warm_up_is_silent_and_can_be_tried_again() -> None:
    warm_up = QwenWarmUp(function=_Function(RuntimeError("provider down")), clock=lambda: 1.0)

    assert warm_up.request() is False
    assert warm_up.request() is False
