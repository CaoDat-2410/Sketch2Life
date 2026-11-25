"""FEAT-093 M1: role proposal rules (plan Rev 2, section 5)."""

from __future__ import annotations

from sketch2life.application.subject_role_scoring import fold, propose_roles


def _e(entity_id: str, label: str, box: list[int]) -> dict:
    return {"entity_id": entity_id, "label": label, "box": box}


def test_fold_removes_vietnamese_accents() -> None:
    assert fold("Con Rùa  đẹp!") == "con rua dep"


def test_the_animal_is_main_and_scenery_is_excluded() -> None:
    proposal = propose_roles(
        [
            _e("main", "con gà con", [4, 3, 17, 18]),
            _e("sec-1", "mặt trời", [0, 0, 5, 5]),
            _e("sec-2", "cỏ", [0, 16, 20, 20]),
        ]
    )

    assert proposal.main_entity_id == "main"
    assert set(proposal.excluded_entity_ids) == {"sec-1", "sec-2"}
    assert proposal.needs_choice is False


def test_an_animal_and_its_food_keep_the_animal_as_main() -> None:
    proposal = propose_roles(
        [_e("main", "con rùa", [3, 6, 14, 17]), _e("sec-1", "chiếc lá", [14, 9, 19, 15])]
    )

    assert proposal.main_entity_id == "main"
    assert proposal.excluded_entity_ids == ()
    assert proposal.needs_choice is False


def test_two_similar_animals_require_an_explicit_choice() -> None:
    proposal = propose_roles(
        [_e("main", "con mèo", [1, 6, 10, 17]), _e("sec-1", "con chó", [10, 6, 19, 17])]
    )

    assert proposal.needs_choice is True
    assert proposal.main_entity_id in {"main", "sec-1"}


def test_the_adult_intent_can_decide_between_two_animals() -> None:
    proposal = propose_roles(
        [_e("main", "con mèo", [1, 6, 10, 17]), _e("sec-1", "con chó", [10, 6, 19, 17])],
        intent_terms=["chú chó chạy trong vườn"],
    )

    assert proposal.main_entity_id == "sec-1"
    assert proposal.needs_choice is False


def test_scenery_named_by_the_adult_is_not_excluded() -> None:
    proposal = propose_roles(
        [_e("main", "con gà con", [4, 3, 17, 18]), _e("sec-1", "mặt trời", [0, 0, 5, 5])],
        intent_terms=["gà con ngắm mặt trời"],
    )

    assert proposal.excluded_entity_ids == ()


def test_a_big_object_beats_a_tiny_animal_only_when_the_animal_cannot_win_on_acting() -> None:
    proposal = propose_roles(
        [_e("main", "con kiến", [9, 9, 11, 11]), _e("sec-1", "cái bàn", [2, 6, 18, 18])]
    )

    assert proposal.main_entity_id == "main"  # acting weight 0.35 outweighs the area share


def test_a_cropped_subject_loses_the_completeness_bonus() -> None:
    full = propose_roles([_e("main", "con voi", [4, 4, 16, 16])]).ranked[0].score
    cropped = propose_roles([_e("main", "con voi", [0, 4, 20, 20])]).ranked[0].score
    assert full > 0 and cropped != full


def test_invalid_boxes_are_ignored_and_nothing_valid_asks_for_a_choice() -> None:
    proposal = propose_roles([_e("main", "con gà", [4, 3, 17]), _e("sec-1", "", [1, 1, 4, 4])])

    assert proposal.main_entity_id is None
    assert proposal.needs_choice is True


def test_only_scenery_asks_for_a_choice() -> None:
    proposal = propose_roles([_e("main", "mặt trời", [0, 0, 5, 5]), _e("sec-1", "cỏ", [0, 16, 20, 20])])

    assert proposal.main_entity_id is None and proposal.needs_choice is True
