from __future__ import annotations

from uuid import UUID

import pytest

from sketch2life.application.services.parent_topic_suggestions import (
    ParentTopicSuggestionService,
)


def test_topic_cards_are_stable_for_a_draft_and_rotate_away_from_excluded_set() -> None:
    service = ParentTopicSuggestionService()
    draft_id = UUID("82ea8c04-8f1d-4b7d-b707-6cb1cf395f78")

    first = service.topic_set(draft_id=draft_id)
    replay = service.topic_set(draft_id=draft_id)
    next_set = service.topic_set(
        draft_id=draft_id,
        excluded_set_ids=(first["set_id"],),
    )

    assert first == replay
    assert first["draft_id"] == draft_id
    assert isinstance(first["draft_id"], UUID)
    assert len(first["cards"]) == 3
    assert len({card["topic_id"] for card in first["cards"]}) == 3
    assert next_set["set_id"] != first["set_id"]
    assert next_set["cards"] != first["cards"]

    new_draft = service.topic_set(
        draft_id=UUID("8b77fa21-e414-4954-bd80-d5bc7b7261d0"),
        excluded_set_ids=(first["set_id"],),
    )
    assert new_draft["set_id"] != first["set_id"]
    assert new_draft["cards"] != first["cards"]


def test_catalog_subject_cards_are_exactly_three_and_topic_scoped() -> None:
    result = ParentTopicSuggestionService().drawing_subject_set(
        draft_id=UUID("3492fab9-6973-420b-88f1-c7f14c1d4e4e"),
        topic_id="animals",
        topic="Động vật",
    )

    assert result["generation_source"] == "CURATED_CATALOG"
    assert result["review_required"] is True
    assert result["topic_id"] == "animals"
    assert len(result["cards"]) == 3
    assert len({card["subject_id"] for card in result["cards"]}) == 3


def test_catalog_subject_refresh_excludes_every_subject_already_shown() -> None:
    service = ParentTopicSuggestionService()
    draft_id = UUID("3492fab9-6973-420b-88f1-c7f14c1d4e4e")
    first = service.drawing_subject_set(
        draft_id=draft_id,
        topic_id="animals",
        topic="Động vật",
    )
    next_set = service.drawing_subject_set(
        draft_id=draft_id,
        topic_id="animals",
        topic="Động vật",
        excluded_set_ids=(first["set_id"],),
        excluded_subjects=tuple(
            label
            for card in first["cards"]
            for label in (card["title_vi"], card["guide_subject"])
        ),
    )

    assert next_set["generation_source"] == "CURATED_CATALOG"
    assert not {
        card["subject_id"] for card in first["cards"]
    }.intersection(card["subject_id"] for card in next_set["cards"])


def test_unknown_custom_topic_fails_closed_without_qwen_draft() -> None:
    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECTS_NEEDS_AI_DRAFT"):
        ParentTopicSuggestionService().drawing_subject_set(
            draft_id=UUID("70878657-899c-4758-bae2-9e4f856f4aab"),
            topic_id="custom",
            topic="Khủng long",
        )


def test_custom_topic_qwen_draft_is_labeled_and_reviewable() -> None:
    service = ParentTopicSuggestionService()
    draft_id = UUID("70878657-899c-4758-bae2-9e4f856f4aab")
    generated = (
        {
            "title_vi": "Khủng long cổ dài",
            "guide_subject": "khủng long cổ dài",
            "relation_to_topic_vi": "Là một loài khủng long ăn thực vật.",
        },
        {
            "title_vi": "Khủng long ba sừng",
            "guide_subject": "khủng long ba sừng",
            "relation_to_topic_vi": "Đây là một loài khủng long có ba sừng.",
        },
        {
            "title_vi": "Khủng long bạo chúa",
            "guide_subject": "khủng long bạo chúa",
            "relation_to_topic_vi": "Đây là một loài khủng long nổi tiếng.",
        },
    )

    result = service.drawing_subject_set(
        draft_id=draft_id,
        topic_id="custom",
        topic="  Khủng long  ",
        generated_subjects=generated,
    )

    assert result["generation_source"] == "QWEN_DRAFT"
    assert result["review_required"] is True
    assert result["topic"] == "Khủng long"
    assert result["topic_id"].startswith("custom-")
    assert len(result["cards"]) == 3
    assert all(card["relation_to_topic_vi"] for card in result["cards"])

    duplicate = (generated[0], generated[0], generated[2])
    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID"):
        service.drawing_subject_set(
            draft_id=draft_id,
            topic_id="custom",
            topic="Khủng long",
            generated_subjects=duplicate,
        )

    with pytest.raises(ValueError, match="SUGGESTION_SET_UNAVAILABLE"):
        service.drawing_subject_set(
            draft_id=draft_id,
            topic_id="custom",
            topic="Khủng long",
            excluded_set_ids=(result["set_id"],),
            generated_subjects=generated,
        )


def test_qwen_fills_catalog_only_after_fewer_than_three_unseen_items_remain() -> None:
    service = ParentTopicSuggestionService()
    generated = (
        {
            "title_vi": "Khủng long cổ dài",
            "guide_subject": "khủng long cổ dài",
            "relation_to_topic_vi": "Là một loài khủng long ăn thực vật.",
        },
        {
            "title_vi": "Khủng long ba sừng",
            "guide_subject": "khủng long ba sừng",
            "relation_to_topic_vi": "Đây là một loài khủng long có ba sừng.",
        },
        {
            "title_vi": "Khủng long bạo chúa",
            "guide_subject": "khủng long bạo chúa",
            "relation_to_topic_vi": "Đây là một loài khủng long nổi tiếng.",
        },
    )
    excluded = (
        "Con bướm", "Gà mái", "Con mèo", "Rùa con", "Chú chó", "Cá nhỏ", "Hươu con"
    )
    assert len(
        service.eligible_catalog_subjects(
            topic_id="animals", topic="Động vật", excluded_subjects=excluded
        )
    ) == 2

    result = service.drawing_subject_set(
        draft_id=UUID("70878657-899c-4758-bae2-9e4f856f4aab"),
        topic_id="animals",
        topic="Động vật",
        excluded_subjects=excluded,
        generated_subjects=generated,
    )

    assert len(result["cards"]) == 3
    assert result["generation_source"] == "QWEN_DRAFT"
    assert sum(card["subject_id"].startswith("ai-") for card in result["cards"]) == 1
    assert not {card["title_vi"] for card in result["cards"]}.intersection(excluded)


def test_custom_subject_gate_rejects_cross_topic_and_holds_ambiguous_input() -> None:
    service = ParentTopicSuggestionService()

    off_topic = service.validate_custom_subject(
        topic_id="nature", topic="Thiên nhiên", subject="con hươu"
    )
    ambiguous = service.validate_custom_subject(
        topic_id="nature", topic="Thiên nhiên", subject="chiếc đĩa bay"
    )

    assert off_topic["decision"] == "OUT_OF_TOPIC"
    assert off_topic["normalized_subject"] is None
    assert ambiguous["decision"] == "NEEDS_CLARIFICATION"
    assert ambiguous["normalized_subject"] is None
