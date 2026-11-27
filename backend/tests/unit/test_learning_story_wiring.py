"""FEAT-094 phase 4: the learning script travels from the request to the stored story."""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

import pytest

import sketch2life.infrastructure.knowledge.learning_request as learning_request
from sketch2life.application.services.story_output import (
    STORY_OUTPUT_INVALID,
    StoryOutputInvalid,
    complete_generated_story,
)
from sketch2life.application.story_staging import pack_story_content, unpack_sections
from sketch2life.domain.knowledge_card import approve_card, parse_card
from sketch2life.infrastructure.ai.modal_function_client import ModalStoryFunctionClient

from test_learning_script import FACTS, NARRATIONS, _learning
from test_modal_story_function_client import _Function, _story_context, _Volume
from test_story_output import PRINCIPAL, _Repository, _reservation


class _Cards:
    def __init__(self, card: Any = None) -> None:
        self.card = card
        self.asked: list[str] = []

    def approved_for_subject(self, label: str) -> Any:
        self.asked.append(label)
        return self.card


def _card() -> Any:
    facts = [
        {"id": "what", "kind": "WHAT_IT_IS", "min_age_months": 36, "text": "Gà là một loài chim.",
         "key_terms": ["loài chim"]},
        {"id": "beak", "kind": "PART", "part": "mỏ", "min_age_months": 36, "text": "Gà dùng mỏ để mổ thóc.",
         "key_terms": ["mỏ"]},
        {"id": "use", "kind": "USE", "min_age_months": 36, "text": "Gà mái đẻ trứng.", "key_terms": ["trứng"]},
    ]
    card = parse_card(
        {
            "card_id": "vi.birds.chicken", "version": 1, "status": "DRAFT", "subject_labels": ["con gà"],
            "topic_ids": ["birds"], "facts": facts, "motion_hints": ["con gà mổ thóc"], "setting": "sân vườn",
            "sources": [{"title": "Nguồn", "url": "https://example.org/ga", "checked_on": "2026-11-26"}],
        }
    )
    return approve_card(card, reviewer="owner", reviewed_on="2026-11-26")


def _build(**changes: Any) -> dict[str, Any] | None:
    arguments: dict[str, Any] = {
        "context": {"age_months": 48, "interests_summary": "Con thích xe ô tô, tên là Minh, số 0900000000"},
        "subject": "con gà",
        "visible_features": ["mỏ cam"],
        "lesson_notes": None,
        "cards": _Cards(),
        "enabled": True,
    }
    arguments.update(changes)
    return learning_request.build_learning_request(**arguments)


def test_the_request_carries_the_age_numbers_and_only_controlled_interest_tags() -> None:
    block = _build()

    assert block is not None
    assert (block["scene_count"], block["scene_seconds"], block["max_words"], block["fact_count"]) == (5, 10, 18, 3)
    assert block["fact_source"] == "AI_DRAFT" and block["facts"] == []
    sent = str(block)
    assert "Minh" not in sent and "0900000000" not in sent and "tên" not in sent
    assert all(len(tag) <= 40 for tag in block["interest_tags"])


def test_an_approved_card_gives_the_facts_motion_and_setting() -> None:
    block = _build(cards=_Cards(_card()))

    assert block["fact_source"] == "CARD"
    assert block["facts"] == FACTS
    assert block["motion_hints"] == ["con gà mổ thóc"] and block["setting"] == "sân vườn"


def test_lesson_notes_come_before_the_card() -> None:
    block = _build(cards=_Cards(_card()), lesson_notes="Gà có mỏ.")

    assert block["fact_source"] == "LESSON" and block["facts"] == []


def test_a_card_without_enough_facts_falls_back_to_drafting() -> None:
    block = _build(cards=_Cards(_card()), context={"age_months": 100})

    assert block["fact_source"] == "AI_DRAFT" and block["facts"] == [] and block["fact_count"] == 4


@pytest.mark.parametrize("changes", [{"enabled": False}, {"context": {"age_months": 20}}, {"context": {}}])
def test_no_request_when_switched_off_or_the_age_is_unsupported(changes: dict[str, Any]) -> None:
    assert _build(**changes) is None


def test_the_story_client_sends_the_block_and_returns_the_learning_answer() -> None:
    context = _story_context()
    context["worker_input"]["learning"] = _build()
    function = _Function(extra_output={"learning": {"fact_source": "AI_DRAFT"}, "staging": None})

    result, _call_id = ModalStoryFunctionClient(volume=_Volume(), function=function).generate(context)

    assert result["_learning"] == {"fact_source": "AI_DRAFT"}


def test_the_story_client_refuses_an_answer_without_the_requested_learning_script() -> None:
    from sketch2life.infrastructure.ai.modal_function_client import ModalFunctionExecutionFailed

    context = _story_context()
    context["worker_input"]["learning"] = _build()

    with pytest.raises(ModalFunctionExecutionFailed, match="STORY_OUTPUT_INVALID"):
        ModalStoryFunctionClient(volume=_Volume(), function=_Function()).generate(context)


def _draft() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Gà Vàng trong vườn",
        "story": {"opening": NARRATIONS[0], "middle": " ".join(NARRATIONS[1:-1]), "ending": NARRATIONS[-1]},
        "duration_ms": 50_000,
        "scenes": [
            {
                "scene_index": index, "title": f"Cảnh vườn {index}", "action": text, "narration": text,
                "visual_prompt": "The chick pecks the ground gently.", "start_ms": (index - 1) * 10_000,
                "duration_ms": 10_000, "character_anchors": ["mỏ cam"],
            }
            for index, text in enumerate(NARRATIONS, start=1)
        ],
        "_learning": _learning(),
    }


def _learning_reservation() -> Any:
    reservation = _reservation()
    worker_input = {
        "confirmed_subject": "con gà",
        "learning": {"scene_count": 5, "scene_seconds": 10, "max_words": 18, "fact_count": 3, "facts": []},
    }
    return type(reservation)(**{**{k: getattr(reservation, k) for k in reservation.__dataclass_fields__}, "worker_input": worker_input})


def _complete(raw: dict[str, Any], reservation: Any) -> _Repository:
    repository = _Repository(record=SimpleNamespace())
    complete_generated_story(
        repository,  # type: ignore[arg-type]
        principal=PRINCIPAL,
        reservation=reservation,
        raw_story=raw,
        provider_call_id="call",
        model_id="m",
        model_revision="r",
    )
    return repository


def test_a_checked_learning_script_is_stored_with_the_story() -> None:
    repository = _complete(_draft(), _learning_reservation())

    stored = repository.calls[0][1]
    assert stored["learning"]["fact_source"] == "AI_DRAFT" and len(stored["learning"]["scenes"]) == 5
    assert "_learning" not in stored["story"]


@pytest.mark.parametrize("damage", ["missing", "wrong"])
def test_a_missing_or_broken_learning_script_fails_the_revision(damage: str) -> None:
    raw = _draft()
    if damage == "missing":
        raw.pop("_learning")
    else:
        raw["_learning"] = copy.deepcopy(raw["_learning"])
        raw["_learning"]["scenes"][1]["fact_id"] = None
    repository = _Repository()

    with pytest.raises(StoryOutputInvalid):
        complete_generated_story(
            repository,  # type: ignore[arg-type]
            principal=PRINCIPAL,
            reservation=_learning_reservation(),
            raw_story=raw,
            provider_call_id="call",
            model_id="m",
            model_revision="r",
        )

    assert repository.calls[0][0] == "fail" and repository.calls[0][1]["error_code"] == STORY_OUTPUT_INVALID


def test_a_story_that_asked_for_no_learning_script_stores_none() -> None:
    from test_story_output import valid_story

    repository = _complete({**valid_story(), "_learning": {"fact_source": "AI_DRAFT"}}, _reservation())

    assert repository.calls[0][1]["learning"] is None


def test_the_stored_content_keeps_the_learning_script_out_of_the_visible_sections() -> None:
    packed = pack_story_content(
        {"opening": "a", "middle": "b", "ending": "c"}, None, "STAGING_NOT_USED", _learning()
    )

    assert packed["learning"]["fact_source"] == "AI_DRAFT"
    assert set(unpack_sections(packed)) == {"opening", "middle", "ending"}
    assert "learning" not in pack_story_content({"opening": "a", "middle": "b", "ending": "c"}, None, None)
