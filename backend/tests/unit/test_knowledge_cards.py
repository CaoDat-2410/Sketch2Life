"""FEAT-094: knowledge cards about the main drawn subject (plan sections 4 and 6.2)."""

from __future__ import annotations

import copy
import json

import pytest

from sketch2life.domain.knowledge_card import (
    KnowledgeCardError,
    approve_card,
    card_for_subject,
    content_sha256,
    facts_for_child,
    parse_card,
)
from sketch2life.infrastructure.knowledge.card_repository import KnowledgeCardRepository


def _fact(
    fact_id: str,
    kind: str,
    text: str,
    terms: list[str],
    *,
    part: str | None = None,
    months: int = 36,
):
    fact = {"id": fact_id, "kind": kind, "min_age_months": months, "text": text, "key_terms": terms}
    if part is not None:
        fact["part"] = part
    return fact


def _card(**override):
    card = {
        "card_id": "vi.transport.bicycle",
        "version": 1,
        "status": "DRAFT",
        "subject_labels": ["xe đạp", "chiếc xe đạp"],
        "topic_ids": ["transport"],
        "facts": [
            _fact("what", "WHAT_IT_IS", "Xe đạp chạy khi người đi đạp chân.", ["xe đạp", "đạp"]),
            _fact(
                "wheel",
                "PART",
                "Hai bánh xe lăn đưa xe tiến tới.",
                ["bánh xe", "lăn"],
                part="bánh xe",
            ),
            _fact(
                "handle",
                "PART",
                "Tay lái giúp xe rẽ trái, rẽ phải.",
                ["tay lái", "rẽ"],
                part="tay lái",
            ),
            _fact(
                "saddle", "PART", "Yên xe là chỗ để người ngồi.", ["yên xe", "ngồi"], part="yên xe"
            ),
            _fact(
                "chain",
                "PART",
                "Dây xích truyền sức đạp tới bánh sau.",
                ["dây xích", "bánh sau"],
                part="dây xích",
                months=72,
            ),
            _fact(
                "use", "USE", "Người ta đi xe đạp tới trường, tới chợ.", ["xe đạp", "tới trường"]
            ),
        ],
        "motion_hints": ["bánh xe lăn", "xe tiến nhẹ"],
        "setting": "đường nhỏ trong công viên",
        "sources": [],
        "reviewed_by": None,
        "reviewed_on": None,
        "approved_sha256": None,
    }
    card.update(override)
    return card


_SOURCE = {
    "title": "Nguồn tổng hợp cho test",
    "url": "https://example.test/xe-dap",
    "checked_on": "2026-11-26",
}


def _approved(**override):
    return approve_card(
        parse_card(_card(sources=[_SOURCE], **override)), reviewer="owner", reviewed_on="2026-11-26"
    )


def test_a_card_needs_what_it_is_a_use_and_unique_fact_ids() -> None:
    parse_card(_card())
    for facts, code in (
        (
            [f for f in _card()["facts"] if f["kind"] != "WHAT_IT_IS"],
            "KNOWLEDGE_CARD_MISSING_WHAT_IT_IS",
        ),
        ([f for f in _card()["facts"] if f["kind"] != "USE"], "KNOWLEDGE_CARD_MISSING_USE"),
        ([*_card()["facts"], _card()["facts"][0]], "KNOWLEDGE_CARD_DUPLICATE_FACT"),
    ):
        with pytest.raises(KnowledgeCardError) as caught:
            parse_card(_card(facts=facts))
        assert caught.value.code == code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"key_terms": ["máy bay"]}, "KNOWLEDGE_FACT_TERM_NOT_IN_TEXT"),
        ({"text": "Bánh xe lăn"}, "KNOWLEDGE_FACT_NOT_A_SENTENCE"),
        ({"text": "Bánh xe " + "lăn " * 20 + "tới."}, "KNOWLEDGE_FACT_TOO_LONG"),
        ({"part": None}, "KNOWLEDGE_FACT_PART_REQUIRED"),
    ],
)
def test_each_fact_is_one_short_sentence_with_its_terms(change, code) -> None:
    card = _card()
    card["facts"][1] = {**card["facts"][1], **change}
    with pytest.raises(KnowledgeCardError) as caught:
        parse_card(card)
    assert caught.value.code == code


@pytest.mark.parametrize(("age", "count"), [(48, 3), (84, 4), (114, 5)])
def test_the_child_gets_the_name_then_parts_then_the_use(age: int, count: int) -> None:
    facts = facts_for_child(parse_card(_card()), age_months=age, visible_features=[])

    assert len(facts) == count
    assert facts[0].kind == "WHAT_IT_IS" and facts[-1].kind == "USE"
    assert {fact.kind for fact in facts[1:-1]} == {"PART"}


def test_parts_seen_in_the_drawing_come_first_and_older_facts_are_withheld() -> None:
    card = parse_card(_card())

    young = facts_for_child(card, age_months=48, visible_features=["yên xe màu đen", "hai bánh"])
    old = facts_for_child(card, age_months=114, visible_features=["dây xích"])

    assert [fact.id for fact in young] == ["what", "saddle", "use"]
    assert old[1].id == "chain"
    assert "chain" not in [
        fact.id for fact in facts_for_child(card, age_months=60, visible_features=["dây xích"])
    ]


def test_too_few_facts_for_the_age_is_not_a_usable_card() -> None:
    card = parse_card(_card(facts=[_card()["facts"][0], _card()["facts"][1], _card()["facts"][-1]]))

    with pytest.raises(KnowledgeCardError) as caught:
        facts_for_child(card, age_months=114, visible_features=[])

    assert caught.value.code == "KNOWLEDGE_CARD_TOO_FEW_FACTS"


def test_only_a_reviewer_with_a_source_can_approve_and_the_hash_pins_the_content() -> None:
    with pytest.raises(KnowledgeCardError) as caught:
        approve_card(parse_card(_card()), reviewer="owner", reviewed_on="2026-11-26")
    assert caught.value.code == "KNOWLEDGE_CARD_SOURCE_REQUIRED"

    approved = _approved()

    assert approved.status == "APPROVED" and approved.reviewed_by == "owner"
    assert approved.approved_sha256 == content_sha256(approved)


def test_the_subject_label_matches_ignoring_case_and_accents_but_not_partial_words() -> None:
    cards = [parse_card(_card())]

    assert card_for_subject(cards, "Chiếc Xe Đạp") is cards[0]
    assert card_for_subject(cards, "xe dap") is cards[0]
    assert card_for_subject(cards, "xe") is None
    assert card_for_subject(cards, "xe đạp điện") is None


def test_the_repository_serves_only_approved_unchanged_cards(tmp_path) -> None:
    approved = _approved().to_dict()
    tampered = copy.deepcopy(approved)
    tampered["card_id"] = "vi.transport.car"
    tampered["subject_labels"] = ["ô tô"]
    draft = _card(card_id="vi.transport.boat", subject_labels=["thuyền"])
    for index, card in enumerate((approved, tampered, draft)):
        (tmp_path / f"{index}.json").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8"
        )

    repository = KnowledgeCardRepository(tmp_path)

    assert repository.approved_for_subject("xe đạp").card_id == "vi.transport.bicycle"
    assert repository.approved_for_subject("ô tô") is None  # edited after approval
    assert repository.approved_for_subject("thuyền") is None  # still a draft


def test_every_card_shipped_with_the_backend_is_valid_and_has_unique_labels() -> None:
    repository = KnowledgeCardRepository()
    cards = repository.all_cards()

    assert len(cards) >= 40
    labels = [label.casefold() for card in cards for label in card.subject_labels]
    assert len(labels) == len(set(labels))
    for card in cards:
        assert len(facts_for_child(card, age_months=48, visible_features=[])) == 3, card.card_id
        assert len(facts_for_child(card, age_months=114, visible_features=[])) == 5, card.card_id
        if card.status == "APPROVED":
            assert card.approved_sha256 == content_sha256(card), card.card_id
