"""S1 core-data seed writer (FEAT-066 SEED-1, package §3.3 and §3.5).

Run from ``backend/`` as ``python -m tools.seed.s1_core``. The guard runs first. Every
row is insert-if-absent on its primary key (never an update), and all of S1 runs in one
transaction. The output is a table of counts only: no row contents and no URL.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Connection, Engine, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.story_run_lite.tables import run_inputs, story_runs
from tools.seed import data
from tools.seed.guard import SeedGuardError, guarded_engine


@dataclass(frozen=True, slots=True)
class SeedStep:
    name: str
    table: sa.Table
    rows: Callable[[], list[dict[str, Any]]]


def _table(model: Any) -> sa.Table:
    table = model.__table__
    assert isinstance(table, sa.Table)
    return table


# Parent rows come before child rows. ``child_profiles`` points at ``profile_revisions``
# through a deferred FK, so both are written in this one transaction.
SEED_STEPS: tuple[SeedStep, ...] = (
    SeedStep("be1_organizations", _table(OrganizationModel), data.organization_rows),
    SeedStep("be1_adult_identities", _table(AdultIdentityModel), data.adult_rows),
    SeedStep("be1_classrooms", _table(ClassroomModel), data.classroom_rows),
    SeedStep(
        "be1_organization_assignments", _table(OrganizationAssignmentModel), data.assignment_rows
    ),
    SeedStep("be1_managed_profiles", _table(ManagedProfileModel), data.managed_profile_rows),
    SeedStep("be1_enrollments", _table(EnrollmentModel), data.enrollment_rows),
    SeedStep("be1_parent_groups", PARENT_GROUPS, data.parent_group_rows),
    SeedStep("be1_parent_group_members", PARENT_GROUP_MEMBERS, data.parent_group_member_rows),
    SeedStep("parent.child_profiles", _table(ParentChildProfileModel), data.child_profile_rows),
    SeedStep(
        "parent.profile_revisions", _table(ParentProfileRevisionModel), data.profile_revision_rows
    ),
    SeedStep("lesson.library_items", LIBRARY_ITEMS, data.library_item_rows),
    SeedStep("lesson.library_versions", LIBRARY_VERSIONS, data.library_version_rows),
    SeedStep("lesson.version_activities", VERSION_ACTIVITIES, data.version_activity_rows),
    SeedStep("lesson.access_grants", ACCESS_GRANTS, data.access_grant_rows),
    SeedStep("story.runs", story_runs, data.story_run_rows),
    SeedStep("story.run_inputs", run_inputs, data.run_input_rows),
)


class SeedWriteError(RuntimeError):
    """A write failure, reported without driver text that could name the target."""


def _insert_if_absent(
    connection: Connection, table: sa.Table, rows: Sequence[dict[str, Any]]
) -> int:
    primary_key = list(table.primary_key.columns)
    statement = (
        insert(table)
        .values(list(rows))
        .on_conflict_do_nothing(index_elements=[column.name for column in primary_key])
        .returning(*primary_key)
    )
    return len(connection.execute(statement).all())


def _count_s1_rows(connection: Connection, step: SeedStep) -> int:
    """Count only the rows that S1 owns, by primary key (SEED-7a adds rows to story tables)."""

    key_columns = list(step.table.primary_key.columns)
    keys = [tuple(row[column.name] for column in key_columns) for row in step.rows()]
    statement = (
        select(func.count()).select_from(step.table).where(sa.tuple_(*key_columns).in_(keys))
    )
    return int(connection.execute(statement).scalar_one())


def count_rows(connection: Connection) -> dict[str, int]:
    return {step.name: _count_s1_rows(connection, step) for step in SEED_STEPS}


def _describe(exc: BaseException) -> str:
    original = getattr(exc, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint = getattr(diagnostic, "constraint_name", None)
    kind = type(original).__name__ if original is not None else type(exc).__name__
    return f"{kind} (constraint: {constraint})" if constraint else kind


def run_s1(engine: Engine) -> dict[str, int]:
    """Write S1 in one transaction and return the number of new rows per table."""

    inserted: dict[str, int] = {}
    current = ""
    try:
        with engine.begin() as connection:
            for step in SEED_STEPS:
                current = step.name
                inserted[step.name] = _insert_if_absent(connection, step.table, step.rows())
    except SQLAlchemyError as exc:
        reason = _describe(exc) if isinstance(exc, DBAPIError) else type(exc).__name__
        raise SeedWriteError(f"seed write failed at {current}: {reason}") from None
    return inserted


def format_counts(
    inserted: dict[str, int], totals: dict[str, int], expected: dict[str, int]
) -> str:
    width = max(len(name) for name in totals)
    lines = [f"{'table'.ljust(width)}  new  total  expected  ok"]
    for name, total in totals.items():
        ok = "yes" if total == expected.get(name) else "NO"
        new = inserted.get(name, 0)
        lines.append(f"{name.ljust(width)}  {new:>3}  {total:>5}  {expected.get(name, 0):>8}  {ok}")
    return "\n".join(lines)


def main() -> int:
    try:
        engine, _target = guarded_engine()
    except SeedGuardError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        try:
            inserted = run_s1(engine)
        except SeedWriteError as exc:
            print(str(exc), file=sys.stderr)
            return 3
        try:
            with engine.connect() as connection:
                totals = count_rows(connection)
        except SQLAlchemyError:
            print("seed count failed", file=sys.stderr)
            return 3
    finally:
        engine.dispose()
    print(format_counts(inserted, totals, data.EXPECTED_COUNTS))
    return 0 if totals == data.EXPECTED_COUNTS else 1


if __name__ == "__main__":
    raise SystemExit(main())
