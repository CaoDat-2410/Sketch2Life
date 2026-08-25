from __future__ import annotations

from typing import Any

SUPERVISION_RANK = {"NONE": 0, "NEARBY": 1, "DIRECT": 2}
INPUT_FIELDS = {
    "age_months",
    "readiness_ids",
    "completed_activity_ids",
    "available_material_option_ids",
    "supervision_level",
    "policy_flags",
    "candidate_status",
}
ALLOWED_CANDIDATE_STATUSES = {"ACTIVE_FIXTURE", "INACTIVE_FIXTURE", "INACTIVE"}
ALLOWED_POLICY_FLAGS = {"CAREGIVER_PRESENT"}


class ScenarioValidationError(ValueError):
    """Raised when a console scenario is malformed or references unknown IDs."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ScenarioValidationError(message)


def _validate_id_list(value: Any, field: str) -> list[str]:
    _require(isinstance(value, list), f"{field} must be an array")
    _require(
        all(isinstance(item, str) and item for item in value),
        f"{field} must contain non-empty string IDs",
    )
    _require(len(value) == len(set(value)), f"{field} contains duplicate IDs")
    return value


def validate_case_input(
    activity: dict[str, Any],
    material_doc: dict[str, Any],
    case_input: dict[str, Any],
    known_activity_ids: set[str],
) -> None:
    """Validate the closed synthetic input contract before evaluating hard rules."""
    _require(isinstance(case_input, dict), "input must be an object")
    _require(
        set(case_input) == INPUT_FIELDS,
        f"input fields mismatch: expected={sorted(INPUT_FIELDS)} actual={sorted(case_input)}",
    )
    age = case_input["age_months"]
    _require(
        isinstance(age, int) and not isinstance(age, bool) and 0 <= age <= 155,
        "age_months must be an integer from 0 through 155",
    )
    readiness = _validate_id_list(case_input["readiness_ids"], "readiness_ids")
    completed = _validate_id_list(
        case_input["completed_activity_ids"], "completed_activity_ids"
    )
    materials = _validate_id_list(
        case_input["available_material_option_ids"],
        "available_material_option_ids",
    )
    policies = _validate_id_list(case_input["policy_flags"], "policy_flags")
    _require(
        case_input["supervision_level"] in SUPERVISION_RANK,
        f"invalid supervision_level: {case_input['supervision_level']}",
    )
    _require(
        case_input["candidate_status"] in ALLOWED_CANDIDATE_STATUSES,
        f"invalid candidate_status: {case_input['candidate_status']}",
    )

    allowed_readiness = {item["id"] for item in activity["readiness_criteria"]}
    _require(
        set(readiness) <= allowed_readiness,
        f"unknown or cross-activity readiness IDs: {sorted(set(readiness) - allowed_readiness)}",
    )
    _require(
        set(completed) <= known_activity_ids,
        f"unknown completed activity IDs: {sorted(set(completed) - known_activity_ids)}",
    )
    _require(
        set(policies) <= ALLOWED_POLICY_FLAGS,
        f"unknown policy flags: {sorted(set(policies) - ALLOWED_POLICY_FLAGS)}",
    )

    groups = {item["id"]: item for item in material_doc["groups"]}
    activity_option_ids = {
        option_id
        for group_id in activity["material_group_ids"]
        for option_id in groups[group_id]["any_of"]
    }
    _require(
        set(materials) <= activity_option_ids,
        f"unknown or cross-activity material IDs: {sorted(set(materials) - activity_option_ids)}",
    )


def evaluate_case(
    activity: dict[str, Any], material_doc: dict[str, Any], case_input: dict[str, Any]
) -> dict[str, Any]:
    """Evaluate one explicitly selected activity using ordered mandatory hard rules."""
    reasons: list[str] = []
    if case_input["candidate_status"] != "ACTIVE_FIXTURE":
        reasons.append("BLOCK_INACTIVE")
    if case_input["age_months"] < activity["age_months"]["min"]:
        reasons.append("BLOCK_AGE_BELOW_MIN")
    if case_input["age_months"] > activity["age_months"]["max"]:
        reasons.append("BLOCK_AGE_ABOVE_MAX")
    required_readiness = {item["id"] for item in activity["readiness_criteria"]}
    if not required_readiness <= set(case_input["readiness_ids"]):
        reasons.append("BLOCK_MISSING_READINESS")
    if not set(activity["prerequisite_activity_ids"]) <= set(
        case_input["completed_activity_ids"]
    ):
        reasons.append("BLOCK_MISSING_PREREQUISITE")
    if (
        SUPERVISION_RANK[case_input["supervision_level"]]
        < SUPERVISION_RANK[activity["safety"]["minimum_supervision"]]
    ):
        reasons.append("BLOCK_INSUFFICIENT_SUPERVISION")
    if not set(activity["policy_constraints"]) <= set(case_input["policy_flags"]):
        reasons.append("BLOCK_POLICY_CONSTRAINT")
    groups = {item["id"]: item for item in material_doc["groups"]}
    available = set(case_input["available_material_option_ids"])
    if any(
        not (set(groups[group_id]["any_of"]) & available)
        for group_id in activity["material_group_ids"]
    ):
        reasons.append("BLOCK_MISSING_MATERIAL")
    if reasons:
        return {
            "status": "NO_VALID_ACTIVITY",
            "allowed_activity_ids": [],
            "blocked": {activity["id"]: reasons},
        }
    return {
        "status": "VALID_CANDIDATE",
        "allowed_activity_ids": [activity["id"]],
        "blocked": {},
    }
