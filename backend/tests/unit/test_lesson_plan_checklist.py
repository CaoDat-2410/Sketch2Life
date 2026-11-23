"""FEAT-066 T-3d: the safety checklist gate (SRS l.548, l.1660, l.1708, l.2189).

The SRS names no checklist item, wording or version, so the shipped registry is a frozen empty
constant (BLOCKED_OPEN, T-3d-DEC-3). The gate is exercised here only with a definition that this
test package builds; no module of the application can be made to hold it.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from sketch2life.contracts.schemas.lesson_occurrences import ConfirmPlanRevisionRequestV1
from sketch2life.domain.lesson_occurrences import safety_checklist as checklist
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    PRODUCTION_REGISTRY,
    ChecklistAnswer,
    ChecklistDefinition,
    ChecklistEntry,
    ChecklistItem,
    ChecklistRegistry,
    checklist_result,
    evaluate_checklist,
)
from sketch2life.interfaces.http.error_envelope import FIELD_ERROR_CODES, safe_field_errors
from sketch2life.interfaces.http.routers.lesson_occurrences import get_checklist_registry

# A test-only definition: synthetic ids and wording, never shipped.
TEST_DEFINITION = ChecklistDefinition(
    "test-v1",
    (
        ChecklistItem("synthetic_a", "Synthetic item A"),
        ChecklistItem("synthetic_b", "Synthetic item B"),
    ),
)
TEST_REGISTRY = ChecklistRegistry((TEST_DEFINITION,))


def answers(*pairs: tuple[str, bool]) -> tuple[ChecklistAnswer, ...]:
    return tuple(ChecklistAnswer(item, checked) for item, checked in pairs)


def entry(order: int, *pairs: tuple[str, bool], version: str = "test-v1") -> ChecklistEntry:
    return ChecklistEntry(order, version, answers(*pairs))


FULL = (("synthetic_a", True), ("synthetic_b", True))


# ----------------------------------------------------------------------------- the registry
def test_the_production_registry_is_empty_and_frozen() -> None:
    assert PRODUCTION_REGISTRY.definitions == ()
    assert PRODUCTION_REGISTRY.current is None
    assert isinstance(PRODUCTION_REGISTRY.definitions, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        PRODUCTION_REGISTRY.definitions = (TEST_DEFINITION,)  # type: ignore[misc]
    assert get_checklist_registry() is PRODUCTION_REGISTRY
    assert checklist.PRODUCTION_REGISTRY is PRODUCTION_REGISTRY


def test_no_module_of_the_application_defines_a_checklist_item() -> None:
    # The registry type accepts a definition only through its constructor; the shipped constant is
    # built with no argument, and the test definition above is not importable from the package.
    assert ChecklistRegistry().definitions == ()
    source = Path(checklist.__file__).read_text(encoding="utf-8")
    assert "ChecklistItem(" not in source  # no item is ever constructed by the module
    assert "synthetic_a" not in source and "test-v1" not in source


def test_the_current_definition_is_the_last_one() -> None:
    newer = ChecklistDefinition("test-v2", (ChecklistItem("synthetic_c", "Synthetic item C"),))
    assert ChecklistRegistry((TEST_DEFINITION, newer)).current is newer
    assert TEST_REGISTRY.current is TEST_DEFINITION


def test_definitions_validate_their_shape() -> None:
    with pytest.raises(ValueError):
        ChecklistDefinition("", (ChecklistItem("a", "text"),))
    with pytest.raises(ValueError):
        ChecklistDefinition("v" * 33, (ChecklistItem("a", "text"),))
    with pytest.raises(ValueError):
        ChecklistDefinition("v1", ())
    with pytest.raises(ValueError):
        ChecklistDefinition("v1", (ChecklistItem("a", "x"), ChecklistItem("a", "y")))
    with pytest.raises(ValueError):
        ChecklistItem("bad id", "text")
    with pytest.raises(ValueError):
        ChecklistItem("a", "   ")


# ----------------------------------------------------------------------------- the gate
def test_without_a_definition_no_custom_activity_can_be_confirmed() -> None:
    found = evaluate_checklist(
        custom_orders=[2, 5], entries=[entry(2, *FULL)], registry=PRODUCTION_REGISTRY
    )
    assert found == [
        {"field": "checklist[2]", "code": "NOT_SUPPORTED"},
        {"field": "checklist[5]", "code": "NOT_SUPPORTED"},
    ]


def test_without_custom_activities_and_without_a_definition_the_gate_is_open() -> None:
    assert evaluate_checklist(custom_orders=[], entries=[], registry=PRODUCTION_REGISTRY) == []
    assert evaluate_checklist(custom_orders=[], entries=[], registry=TEST_REGISTRY) == []


def test_a_complete_answer_passes() -> None:
    assert (
        evaluate_checklist(custom_orders=[1], entries=[entry(1, *FULL)], registry=TEST_REGISTRY)
        == []
    )
    assert (
        evaluate_checklist(
            custom_orders=[1, 3],
            entries=[entry(3, *reversed(FULL)), entry(1, *FULL)],
            registry=TEST_REGISTRY,
        )
        == []
    )


def test_a_missing_entry_names_every_required_item() -> None:
    found = evaluate_checklist(custom_orders=[4], entries=[], registry=TEST_REGISTRY)
    assert found == [
        {"field": "checklist[4].items.synthetic_a", "code": "REQUIRED"},
        {"field": "checklist[4].items.synthetic_b", "code": "REQUIRED"},
    ]


def test_an_unchecked_or_unanswered_item_is_required() -> None:
    found = evaluate_checklist(
        custom_orders=[1],
        entries=[entry(1, ("synthetic_a", True), ("synthetic_b", False))],
        registry=TEST_REGISTRY,
    )
    assert found == [{"field": "checklist[1].items.synthetic_b", "code": "REQUIRED"}]
    found = evaluate_checklist(
        custom_orders=[1], entries=[entry(1, ("synthetic_a", True))], registry=TEST_REGISTRY
    )
    assert found == [{"field": "checklist[1].items.synthetic_b", "code": "REQUIRED"}]


def test_a_version_other_than_the_current_one_is_refused() -> None:
    found = evaluate_checklist(
        custom_orders=[1], entries=[entry(1, *FULL, version="test-v0")], registry=TEST_REGISTRY
    )
    assert found == [{"field": "checklist[1].checklist_version", "code": "INVALID_FORMAT"}]


def test_entries_for_other_activities_and_unknown_items_are_unknown_fields() -> None:
    found = evaluate_checklist(
        custom_orders=[1],
        entries=[entry(1, *FULL, ("extra", True)), entry(2, *FULL), entry(9, *FULL)],
        registry=TEST_REGISTRY,
    )
    assert found == [
        {"field": "checklist[2]", "code": "UNKNOWN_FIELD"},
        {"field": "checklist[9]", "code": "UNKNOWN_FIELD"},
        {"field": "checklist[1].items.extra", "code": "UNKNOWN_FIELD"},
    ]


def test_repeated_entries_and_items_are_invalid() -> None:
    found = evaluate_checklist(
        custom_orders=[1],
        entries=[entry(1, *FULL), entry(1, *FULL)],
        registry=TEST_REGISTRY,
    )
    assert found == [{"field": "checklist[1]", "code": "INVALID_FORMAT"}]
    found = evaluate_checklist(
        custom_orders=[1],
        entries=[entry(1, *FULL, ("synthetic_a", True))],
        registry=TEST_REGISTRY,
    )
    assert found == [{"field": "checklist[1].items.synthetic_a", "code": "INVALID_FORMAT"}]


def test_the_result_stores_every_item_checked() -> None:
    assert checklist_result(TEST_DEFINITION) == {
        "items": [
            {"item_id": "synthetic_a", "checked": True},
            {"item_id": "synthetic_b", "checked": True},
        ]
    }


# ----------------------------------------------------------------------------- the envelope
def test_not_supported_is_a_known_field_error_code_and_survives_the_envelope() -> None:
    assert "NOT_SUPPORTED" in FIELD_ERROR_CODES
    refused = [{"field": "activities[0].kind", "code": "NOT_SUPPORTED"}]
    assert safe_field_errors(refused) == refused
    # an unknown code is still dropped (the set stays closed)
    assert safe_field_errors([{"field": "x", "code": "MADE_UP"}]) is None


def test_field_paths_of_the_gate_fit_the_envelope_limit() -> None:
    longest = "checklist[24].items." + "i" * 64
    assert len(longest) <= 120
    assert safe_field_errors([{"field": longest, "code": "REQUIRED"}]) is not None


def test_the_confirm_schema_bounds_the_checklist() -> None:
    body = {
        "expected_plan_hash": "a" * 64,
        "checklist": [
            {
                "activity_order": 1,
                "checklist_version": "v1",
                "items": [{"item_id": "a", "checked": True}],
            }
        ],
    }
    ConfirmPlanRevisionRequestV1.model_validate(body)
    for bad in (
        {**body, "expected_plan_hash": "A" * 64},
        {**body, "expected_plan_hash": "a" * 63},
        {**body, "checklist": [body["checklist"][0]] * 25},
        {**body, "unknown": 1},
        {
            **body,
            "checklist": [
                {**body["checklist"][0], "items": [{"item_id": "bad id", "checked": True}]}
            ],
        },
        {
            **body,
            "checklist": [{**body["checklist"][0], "items": [{"item_id": "a", "checked": "yes"}]}],
        },
        {
            **body,
            "checklist": [
                {
                    **body["checklist"][0],
                    "items": [{"item_id": f"i{n}", "checked": True} for n in range(65)],
                }
            ],
        },
        {**body, "checklist": [{**body["checklist"][0], "activity_order": 0}]},
        {**body, "checklist": [{**body["checklist"][0], "activity_order": 25}]},
    ):
        with pytest.raises(ValueError):
            ConfirmPlanRevisionRequestV1.model_validate(bad)
