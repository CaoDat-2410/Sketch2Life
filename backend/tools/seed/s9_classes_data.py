"""Deterministic roster and lifecycle fixtures for the SEED-2 class stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.seed import data


@dataclass(frozen=True, slots=True)
class ClassStateSpec:
    key: str
    class_number: int
    target_state: str
    command: str
    children: int


CLASS_STATES = (
    ClassStateSpec("class-5-archive", 5, "archived", "archive", 2),
    ClassStateSpec("class-6-suspend", 6, "suspended", "suspend", 2),
)

PROFILE_CREATE_CHILD_IDS = (
    "seed-ch-a-1-6",
    "seed-ch-a-1-7",
    "seed-ch-a-1-8",
)
MOVED_CHILD_ID = PROFILE_CREATE_CHILD_IDS[0]
MOVE_FROM_CLASS_NUMBER = 1
MOVE_TO_CLASS_NUMBER = 3


def lifecycle_profile_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for class_spec in CLASS_STATES:
        for child_number in range(1, class_spec.children + 1):
            child_id = f"seed-ch-a-{class_spec.class_number}-{child_number}"
            rows.append(
                data.managed_profile_row(
                    child_id,
                    "a",
                    class_spec.class_number,
                    child_number,
                    class_spec.children,
                )
            )
    return rows


def keyed_profile_rows() -> list[dict[str, Any]]:
    rows = []
    for child_number, child_id in enumerate(PROFILE_CREATE_CHILD_IDS, start=6):
        profile = data.managed_profile_row(
            child_id,
            "a",
            1,
            child_number,
            8,
            created_by=data.ORG_A_TEACHERS[0],
        )
        # The keyed profile route requires this visible synthetic-development prefix.
        profile["display_name"] = f"Synthetic {profile['display_name']}"
        rows.append(profile)
    return rows


EXPECTED = {
    # The stage adds classes 5 and 6, and moves the revisions of existing classes 1 and 3.
    "be1_classrooms": 4,
    "be1_organization_assignments": 1,
    "be1_managed_profiles": 7,
    "be1_enrollments": 8,
    "be1_command_receipts": 7,
    "core_audit_entries": 7,
    "core_aggregate_revisions": 6,
    "core_outbox_events": 7,
}


def class_state_key(class_spec: ClassStateSpec) -> str:
    return f"seed:s9:{class_spec.key}"


def class_state_scope(class_id: str, command: str) -> str:
    return f"POST /classes/{class_id}/{command}"


def class_assignment_key(class_id: str) -> str:
    return f"seed:s9:class-assignment:{class_id}"


def class_assignment_scope(class_id: str) -> str:
    return f"POST /classes/{class_id}/assignments"


def class_assignment_id(class_id: str) -> str:
    return data.seed_uuid_text(f"assignment:a:{data.ORG_A_TEACHERS[1]}:{class_id}:teacher")


def class_assignment_event_id(class_id: str) -> str:
    return data.seed_uuid_text(f"s9:event:assignment:{class_id}")


def profile_create_key(child_id: str) -> str:
    return f"seed:s9:profile-create:{child_id}"


def profile_create_scope() -> str:
    return f"POST /organizations/{data.org_id('a')}/classes/{data.class_id('a', 1)}/profiles"


def move_key() -> str:
    return f"seed:s9:profile-move:{MOVED_CHILD_ID}"


def move_scope() -> str:
    return (
        f"POST /classes/{data.class_id('a', MOVE_FROM_CLASS_NUMBER)}/profiles/{MOVED_CHILD_ID}/move"
    )


def class_state_event_id(class_spec: ClassStateSpec) -> str:
    return data.seed_uuid_text(f"s9:event:{class_spec.key}")


def profile_event_id(child_id: str, event_type: str) -> str:
    return data.seed_uuid_text(f"s9:event:{event_type}:{child_id}")


def move_event_id() -> str:
    return data.seed_uuid_text(f"s9:event:moved:{MOVED_CHILD_ID}")


def audit_id(key: str) -> str:
    return data.seed_uuid_text(f"s9:audit:{key}")


def move_enrollment_id() -> str:
    return data.seed_uuid_text(f"s9:move-enrollment:{MOVED_CHILD_ID}")


def stage_enrollment_id(child_id: str) -> str:
    return data.seed_uuid_text(f"enrollment:{child_id}")
