"""Safety checklist of a Teacher-written activity (FEAT-066 goal v3, T-3d; SRS l.548, l.1660).

SRS FR-T-09 (l.548) requires a safety checklist for every Teacher-written (``CUSTOM``) activity
before its plan can be approved, and l.1660 and l.1708 repeat it for the confirm command. The SRS
names no item, wording or version, so the content is a product and safety decision that this code
does not invent (T-3d-DEC-3, BLOCKED_OPEN). The production registry is therefore a frozen empty
constant: no checklist version exists, a ``CUSTOM`` activity is refused when a plan revision is
created and again at confirm, and the gate below is exercised only with a definition that a test
builds and injects through the service constructor or a dependency override.

Every item of a definition is required (the SRS names no optional item; assumption recorded in
T-3d-DEC-3 until the owner answers). Nothing here knows HTTP, SQL or a framework.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

CHECKLIST_VERSION_MAX_LENGTH: Final = 32
CHECKLIST_ITEM_ID_MAX_LENGTH: Final = 64
CHECKLIST_ITEMS_MAX: Final = 64
ITEM_ID_PATTERN: Final = r"^[A-Za-z0-9._-]{1,64}$"
_ITEM_ID = re.compile(ITEM_ID_PATTERN)


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    item_id: str
    text: str

    def __post_init__(self) -> None:
        if not _ITEM_ID.fullmatch(self.item_id) or not self.text.strip():
            raise ValueError("invalid checklist item")


@dataclass(frozen=True, slots=True)
class ChecklistDefinition:
    """One immutable version of the checklist: an ordered list of required items."""

    version: str
    items: tuple[ChecklistItem, ...]

    def __post_init__(self) -> None:
        if not 0 < len(self.version) <= CHECKLIST_VERSION_MAX_LENGTH:
            raise ValueError("invalid checklist version")
        if not 0 < len(self.items) <= CHECKLIST_ITEMS_MAX:
            raise ValueError("a checklist has 1 to 64 items")
        if len({item.item_id for item in self.items}) != len(self.items):
            raise ValueError("duplicate checklist item id")


@dataclass(frozen=True, slots=True)
class ChecklistRegistry:
    """The checklist versions known to the process; the last one is the current version."""

    definitions: tuple[ChecklistDefinition, ...] = ()

    @property
    def current(self) -> ChecklistDefinition | None:
        return self.definitions[-1] if self.definitions else None


# The shipped registry: empty and frozen until the owner supplies the checklist (T-3d-DEC-3).
PRODUCTION_REGISTRY: Final = ChecklistRegistry()


@dataclass(frozen=True, slots=True)
class ChecklistAnswer:
    item_id: str
    checked: bool


@dataclass(frozen=True, slots=True)
class ChecklistEntry:
    """The Teacher's answers for one ``CUSTOM`` activity (``activity_order`` of the plan)."""

    activity_order: int
    checklist_version: str
    items: tuple[ChecklistAnswer, ...]


def _item_path(order: int, item_id: str) -> str:
    return f"checklist[{order}].items.{item_id}"


def evaluate_checklist(
    *,
    custom_orders: Sequence[int],
    entries: Sequence[ChecklistEntry],
    registry: ChecklistRegistry,
) -> list[dict[str, str]]:
    """Field errors that stop the approval; an empty list means the gate is satisfied.

    Without a current definition no ``CUSTOM`` activity can be confirmed (fail closed): each one is
    ``NOT_SUPPORTED`` on ``checklist[<activity order>]`` (a confirm request has no ``activities``
    array, so the path names the plan activity order, like every other gate error). Otherwise
    every ``CUSTOM`` activity needs one entry for the current version whose required items are
    all ``checked``. A missing or unchecked item is
    ``REQUIRED``; an entry for a non-custom or unknown activity, or an item that is not in the
    definition, is ``UNKNOWN_FIELD``; a repeated entry or item and a version other than the
    current one are ``INVALID_FORMAT``.
    """
    definition = registry.current
    errors: list[dict[str, str]] = []
    if custom_orders and definition is None:
        return [
            {"field": f"checklist[{order}]", "code": "NOT_SUPPORTED"} for order in custom_orders
        ]
    custom = set(custom_orders)
    seen_orders: set[int] = set()
    by_order: dict[int, ChecklistEntry] = {}
    for entry in entries:
        path = f"checklist[{entry.activity_order}]"
        if entry.activity_order not in custom:
            errors.append({"field": path, "code": "UNKNOWN_FIELD"})
        elif entry.activity_order in seen_orders:
            errors.append({"field": path, "code": "INVALID_FORMAT"})
        else:
            by_order[entry.activity_order] = entry
        seen_orders.add(entry.activity_order)
    if definition is None:
        return errors
    required = [item.item_id for item in definition.items]
    for order in custom_orders:
        found = by_order.get(order)
        if found is None:
            errors.extend(
                {"field": _item_path(order, item), "code": "REQUIRED"} for item in required
            )
            continue
        if found.checklist_version != definition.version:
            errors.append(
                {"field": f"checklist[{order}].checklist_version", "code": "INVALID_FORMAT"}
            )
            continue
        answers: dict[str, bool] = {}
        for answer in found.items:
            if answer.item_id not in required:
                errors.append({"field": _item_path(order, answer.item_id), "code": "UNKNOWN_FIELD"})
            elif answer.item_id in answers:
                errors.append(
                    {"field": _item_path(order, answer.item_id), "code": "INVALID_FORMAT"}
                )
            else:
                answers[answer.item_id] = answer.checked
        errors.extend(
            {"field": _item_path(order, item), "code": "REQUIRED"}
            for item in required
            if answers.get(item) is not True
        )
    return errors


def checklist_result(definition: ChecklistDefinition) -> dict[str, object]:
    """The stored result of a satisfied gate: every item of the definition, checked."""
    return {"items": [{"item_id": item.item_id, "checked": True} for item in definition.items]}


__all__ = [
    "CHECKLIST_ITEMS_MAX",
    "CHECKLIST_ITEM_ID_MAX_LENGTH",
    "CHECKLIST_VERSION_MAX_LENGTH",
    "ITEM_ID_PATTERN",
    "PRODUCTION_REGISTRY",
    "ChecklistAnswer",
    "ChecklistDefinition",
    "ChecklistEntry",
    "ChecklistItem",
    "ChecklistRegistry",
    "checklist_result",
    "evaluate_checklist",
]
