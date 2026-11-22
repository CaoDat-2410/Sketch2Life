"""PostgreSQL acceptance checks for S9 class lifecycle and profile commands."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import TypedDict

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s1_core import count_rows, run_s1
from tools.seed.s7a_runs import run_s7a
from tools.seed.s8_lessons import run_s8
from tools.seed.s9_classes import count_s9_rows, run_s9
from tools.seed.s9_classes_data import (
    CLASS_STATES,
    EXPECTED,
    MOVED_CHILD_ID,
    PROFILE_CREATE_CHILD_IDS,
    audit_id,
    class_assignment_event_id,
    class_state_event_id,
    lifecycle_profile_rows,
    move_enrollment_id,
    move_event_id,
    profile_event_id,
    stage_enrollment_id,
)
from tools.seed.stage_common import StageResult, check_database_prefix

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)


class SeededRows(TypedDict):
    first: StageResult
    second: StageResult
    totals: dict[str, int]
    s1_totals: dict[str, int]


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
    from sketch2life.infrastructure.config.settings import (
        get_core_database_settings,
        get_settings,
    )

    previous = os.environ.get("SKETCH2LIFE_DATABASE_URL")
    try:
        check_database_prefix()
        engine, _target = guarded_engine()
        try:
            yield engine
        finally:
            engine.dispose()
    finally:
        if previous is None:
            os.environ.pop("SKETCH2LIFE_DATABASE_URL", None)
        else:
            os.environ["SKETCH2LIFE_DATABASE_URL"] = previous
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(scope="module")
def seeded(seed_engine: Engine) -> SeededRows:
    run_s1(seed_engine)
    run_s7a(seed_engine)
    run_s8(seed_engine)
    first = run_s9(seed_engine)
    second = run_s9(seed_engine)
    with seed_engine.connect() as connection:
        totals = count_s9_rows(connection)
        s1_totals = count_rows(connection)
    return {"first": first, "second": second, "totals": totals, "s1_totals": s1_totals}


def test_s9_twice_adds_no_rows_and_preserves_s1(seeded: SeededRows) -> None:
    first = seeded["first"]
    second = seeded["second"]
    assert first.ok
    assert second.ok
    assert first.after == EXPECTED
    assert second.before == EXPECTED
    assert second.after == EXPECTED
    assert all(second.after[name] - second.before[name] == 0 for name in EXPECTED)
    assert seeded["totals"] == EXPECTED
    assert seeded["s1_totals"] == data.EXPECTED_COUNTS


def test_lifecycle_rosters_assignment_and_move_match_route_results(
    seed_engine: Engine, seeded: SeededRows
) -> None:
    session = Session(seed_engine)
    try:
        for spec in CLASS_STATES:
            class_id = data.class_id("a", spec.class_number)
            classroom = session.get(ClassroomModel, class_id)
            assert classroom is not None
            assert classroom.state == spec.target_state
            assert classroom.revision == (2 if spec.class_number == 5 else 3)

        assignment = session.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == data.org_id("a"),
                OrganizationAssignmentModel.subject == data.ORG_A_TEACHERS[1],
                OrganizationAssignmentModel.class_id == data.class_id("a", 6),
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            )
        )
        assert assignment is not None

        lifecycle_ids = [row["child_id"] for row in lifecycle_profile_rows()]
        for child_id in lifecycle_ids:
            profile = session.get(ManagedProfileModel, child_id)
            enrollment = session.get(EnrollmentModel, stage_enrollment_id(child_id))
            assert profile is not None and enrollment is not None
            assert profile.data_origin == "SYNTHETIC_DEV"
            assert profile.age_source == "SYNTHETIC_FIXTURE"
            assert enrollment.state == "active"

        for child_id in PROFILE_CREATE_CHILD_IDS:
            profile = session.get(ManagedProfileModel, child_id)
            assert profile is not None
            assert profile.data_origin == "SYNTHETIC_DEV"
            assert profile.age_source == "SYNTHETIC_FIXTURE"
        moved = session.get(ManagedProfileModel, MOVED_CHILD_ID)
        assert moved is not None and moved.class_id == data.class_id("a", 3)
        old_enrollment = session.get(EnrollmentModel, stage_enrollment_id(MOVED_CHILD_ID))
        new_enrollment = session.get(EnrollmentModel, move_enrollment_id())
        assert old_enrollment is not None and old_enrollment.state == "withdrawn"
        assert new_enrollment is not None
        assert new_enrollment.state == "active"
        assert new_enrollment.class_id == data.class_id("a", 3)

        audit_keys = [
            audit_id(f"class-{spec.command}-{spec.class_number}") for spec in CLASS_STATES
        ]
        audit_keys.append(audit_id(f"assignment:{data.class_id('a', 6)}"))
        audit_keys.extend(
            audit_id(f"profile-enroll:{child_id}") for child_id in PROFILE_CREATE_CHILD_IDS
        )
        audit_keys.append(audit_id(f"profile-move:{MOVED_CHILD_ID}"))
        audit_rows = [session.get(CoreAuditEntryModel, key) for key in audit_keys]
        assert all(row is not None and row.decision == "allowed" for row in audit_rows)
        assert {row.action for row in audit_rows if row is not None} == {
            "class.archive",
            "class.suspend",
            "identity.assignment.create",
            "profile.enroll",
            "profile.move",
        }

        event_keys = [class_state_event_id(spec) for spec in CLASS_STATES]
        event_keys.append(class_assignment_event_id(data.class_id("a", 6)))
        event_keys.extend(
            profile_event_id(child_id, "enrolled") for child_id in PROFILE_CREATE_CHILD_IDS
        )
        event_keys.append(move_event_id())
        events = [session.get(CoreOutboxEventModel, key) for key in event_keys]
        assert all(row is not None and row.status == "pending" for row in events)

        for aggregate_id, expected_revision in (
            (data.class_id("a", 5), 2),
            (data.class_id("a", 6), 3),
            (data.org_id("a"), 1),
            (MOVED_CHILD_ID, 2),
            (PROFILE_CREATE_CHILD_IDS[1], 1),
            (PROFILE_CREATE_CHILD_IDS[2], 1),
        ):
            aggregate = session.get(CoreAggregateRevisionModel, aggregate_id)
            assert aggregate is not None and aggregate.revision == expected_revision
    finally:
        session.rollback()
        session.close()
