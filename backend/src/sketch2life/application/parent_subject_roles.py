"""Subject roles of a Parent drawing understanding (FEAT-087).

The AI worker proposes one main subject and up to three secondary subjects, each with a coarse
box. The adult reviews them and the final roles are stored beside the understanding result, so
no consumer ever uses an object the adult did not approve. Records written before FEAT-087 carry
no entities and keep working as a single main subject.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

from sketch2life.application.subject_role_scoring import propose_roles

MAIN_ENTITY_ID = "main"
MAX_SECONDARY_SUBJECTS = 3
ROLE_VALUES = ("main", "secondary", "excluded")
_ENTITY_IDS = (MAIN_ENTITY_ID, *(f"sec-{index}" for index in range(1, MAX_SECONDARY_SUBJECTS + 1)))
_PROMOTED_FACING = "front"  # a promoted secondary has no facing; "front" means do not mirror


class SubjectRoleError(ValueError):
    """Content-free subject role violation (never carries labels)."""

    def __init__(self, code: str = "PARENT_SUBJECT_ROLES_INVALID") -> None:
        super().__init__(code)
        self.code = code


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return " ".join("".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").split())


def _valid_box(box: Any) -> bool:
    if not isinstance(box, list) or len(box) != 4:
        return False
    if any(type(value) is not int or not 0 <= value <= 20 for value in box):
        return False
    x0, y0, x1, y1 = box
    return x0 < x1 and y0 < y1


def _valid_subject(item: Any, *, main: bool) -> bool:
    return (
        isinstance(item, dict)
        and isinstance(item.get("label"), str)
        and 1 <= len(item["label"].strip()) <= 100
        and isinstance(item.get("visible_features"), list)
        and all(isinstance(value, str) for value in item["visible_features"])
        and _valid_box(item.get("box"))
        and (not main or item.get("facing") in ("left", "right", "front"))
    )


def normalize_worker_candidate(raw: dict[str, Any]) -> dict[str, Any]:
    """Project the worker ``result`` into the stored candidate (v2 gets stable entity ids)."""

    candidate: dict[str, Any] = {
        "candidate_subject": raw.get("candidate_subject"),
        "visible_features": list(raw.get("visible_features") or []),
        "confidence": raw.get("confidence"),
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }
    main = raw.get("main_subject")
    secondaries = raw.get("secondary_subjects")
    if (
        _valid_subject(main, main=True)
        and isinstance(secondaries, list)
        and len(secondaries) <= MAX_SECONDARY_SUBJECTS
        and all(_valid_subject(item, main=False) for item in secondaries)
    ):
        candidate["understanding_schema"] = raw.get("understanding_schema")
        candidate["main_subject"] = {"entity_id": MAIN_ENTITY_ID, **deepcopy(main)}
        candidate["secondary_subjects"] = [
            {"entity_id": f"sec-{index}", **deepcopy(item)}
            for index, item in enumerate(secondaries[:MAX_SECONDARY_SUBJECTS], start=1)
        ]
    return candidate


def _entities(candidate: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    main = candidate.get("main_subject")
    secondaries = candidate.get("secondary_subjects")
    if not isinstance(main, dict) or not isinstance(secondaries, list):
        return None
    entities = {str(main["entity_id"]): main}
    for item in secondaries:
        entities[str(item["entity_id"])] = item
    return entities


def _original_entities(candidate: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    """Entities as the AI proposed them (kept even after a promotion swaps the main)."""

    stored = candidate.get("entities_snapshot")
    if isinstance(stored, dict):
        return stored
    return _entities(candidate)


def apply_subject_roles(candidate: dict[str, Any], roles: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a new candidate carrying the adult's final roles, or raise ``SubjectRoleError``."""

    entities = _original_entities(candidate)
    if entities is None or not isinstance(roles, list) or len(roles) != len(entities):
        raise SubjectRoleError()
    seen: dict[str, dict[str, Any]] = {}
    for item in roles:
        if not isinstance(item, dict) or set(item) != {"entity_id", "label", "role"}:
            raise SubjectRoleError()
        entity_id, label, role = item["entity_id"], item["label"], item["role"]
        if (
            entity_id not in entities
            or entity_id in seen
            or role not in ROLE_VALUES
            or not isinstance(label, str)
        ):
            raise SubjectRoleError()
        label = label.strip()
        if not 1 <= len(label) <= 100:
            raise SubjectRoleError()
        seen[entity_id] = {"entity_id": entity_id, "label": label, "role": role}
    if sum(1 for item in seen.values() if item["role"] == "main") != 1:
        raise SubjectRoleError()
    used = [_normalized(item["label"]) for item in seen.values() if item["role"] != "excluded"]
    if len(set(used)) != len(used):
        raise SubjectRoleError()

    ordered = [seen[key] for key in _ENTITY_IDS if key in seen]
    new_main_id = next(item["entity_id"] for item in ordered if item["role"] == "main")
    new_main_label = seen[new_main_id]["label"]
    source = entities[new_main_id]
    updated = deepcopy(candidate)
    updated["entities_snapshot"] = deepcopy(entities)
    updated["approved_roles"] = ordered
    updated["decision"] = "CORRECTED_BY_ADULT"
    updated["candidate_subject"] = new_main_label
    updated["visible_features"] = list(source.get("visible_features") or []) or list(
        candidate.get("visible_features") or []
    )
    updated["main_subject"] = {
        "entity_id": new_main_id,
        "label": new_main_label,
        "visible_features": list(updated["visible_features"]),
        "facing": source.get("facing", _PROMOTED_FACING),
        "box": list(source["box"]),
    }
    updated["secondary_subjects"] = [
        {
            "entity_id": key,
            "label": seen[key]["label"],
            "visible_features": list(entities[key].get("visible_features") or []),
            "box": list(entities[key]["box"]),
        }
        for key in _ENTITY_IDS
        if key in seen and key != new_main_id
    ]
    return updated


def relabel_main_subject(candidate: dict[str, Any], label: str) -> dict[str, Any]:
    """Adult renamed the main subject without sending roles (older client): keep v2 data coherent."""

    updated = deepcopy(candidate)
    updated["candidate_subject"] = label
    updated["decision"] = "CORRECTED_BY_ADULT"
    if isinstance(updated.get("main_subject"), dict):
        updated["main_subject"]["label"] = label
    return updated


def approved_subjects(
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Main subject and the secondaries an adult approved (none without approval)."""

    main = candidate.get("main_subject")
    if not isinstance(main, dict):
        return (
            {
                "entity_id": MAIN_ENTITY_ID,
                "label": candidate.get("candidate_subject"),
                "visible_features": list(candidate.get("visible_features") or []),
            },
            [],
        )
    approved = candidate.get("approved_roles")
    if not isinstance(approved, list):
        return main, []
    chosen = {item["entity_id"] for item in approved if item.get("role") == "secondary"}
    return main, [
        item for item in candidate.get("secondary_subjects", []) if item["entity_id"] in chosen
    ]


def present_candidate(
    candidate: dict[str, Any], *, intent_terms: Iterable[str] = ()
) -> dict[str, Any]:
    """Client-facing candidate: no boxes or internal snapshots, plus entities and roles.

    FEAT-093 M1: the proposal comes from ``propose_roles`` (scores, scenery, ambiguity) and the
    adult's intent words; ``needs_choice`` makes the app require an explicit main subject."""

    internal = {
        "main_subject",
        "secondary_subjects",
        "approved_roles",
        "entities_snapshot",
        "understanding_schema",
    }
    shown = {key: value for key, value in candidate.items() if key not in internal}
    entities = _original_entities(candidate)
    approved = candidate.get("approved_roles")
    proposal = (
        None
        if entities is None
        else propose_roles(
            [{"entity_id": key, **entities[key]} for key in _ENTITY_IDS if key in entities],
            intent_terms=intent_terms,
        )
    )
    proposed_main = proposal.main_entity_id if proposal is not None else None
    if proposed_main is None:
        proposed_main = MAIN_ENTITY_ID
    excluded = set(proposal.excluded_entity_ids) if proposal is not None else set()
    shown["entities"] = (
        []
        if entities is None
        else [
            {
                "entity_id": key,
                "label": str(entities[key]["label"]),
                "suggested_role": "main" if key == proposed_main else "secondary",
                "suggested_included": key not in excluded,
            }
            for key in _ENTITY_IDS
            if key in entities
        ]
    )
    shown["needs_choice"] = bool(proposal.needs_choice) if proposal is not None else False
    shown["subject_roles"] = deepcopy(approved) if isinstance(approved, list) else None
    return shown
