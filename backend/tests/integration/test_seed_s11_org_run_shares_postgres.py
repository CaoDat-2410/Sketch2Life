"""PostgreSQL acceptance coverage for the S11 run and private lesson-share seed."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.lesson_documents import LessonDocumentParser, MalwareScanner
from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.story_run_lifecycle import (
    AUDIT_CANCEL_ACCEPTED,
    CANCEL_EVENT_TYPE,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s11_org_run_shares import count_stage_rows
from tools.seed.s11_org_run_shares_data import (
    EXPECTED,
    LESSON_CONTENTS,
    MANAGER_A,
    ORG_A,
    PARENT_GROUP_A1,
    PARENT_P1,
    PRIVATE_SHARE_SPECS,
    REVIEW_CHANGE_REASON,
    TEACHER_A1,
    TEACHER_RUN_CANCEL_KEY,
    TEACHER_RUN_ID,
    TEACHER_RUN_INPUT_ID,
    TEACHER_RUN_PROFILE_REF,
)
from tools.seed.stage_common import check_database_prefix, stage_key

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)

BACKEND = Path(__file__).resolve().parents[2]
ROW = re.compile(r"^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(yes|NO)$", re.MULTILINE)
StageRun = tuple[int, dict[str, tuple[int, int, int, str]], str]


def _run_module(module: str) -> StageRun:
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join((str(BACKEND / "src"), str(BACKEND))),
    }
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", module],
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    rows = {
        name: (int(new), int(total), int(expected), ok)
        for name, new, total, expected, ok in ROW.findall(result.stdout)
    }
    return result.returncode, rows, result.stdout + result.stderr


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
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
def stage_runs() -> tuple[StageRun, ...]:
    core = _run_module("tools.seed.s1_core")
    s7a = _run_module("tools.seed.s7a_runs")
    first = _run_module("tools.seed.s11_org_run_shares")
    second = _run_module("tools.seed.s11_org_run_shares")
    assert core[0] == 0 and s7a[0] == 0, (core[2], s7a[2])
    return core, s7a, first, second


def test_s11_is_idempotent_and_reports_all_expected_counts(
    stage_runs: tuple[StageRun, ...],
) -> None:
    first, second = stage_runs[2:]
    assert first[0] == second[0] == 0, (first[2], second[2])
    assert set(second[1]) == set(EXPECTED)
    for table, expected in EXPECTED.items():
        assert second[1][table] == (0, expected, expected, "yes")


def test_teacher_cancel_writes_the_t13a_lifecycle_transaction_and_keeps_synthetic_input(
    seed_engine: Engine,
    stage_runs: tuple[StageRun, ...],
) -> None:
    with Session(seed_engine) as session:
        run = (
            session.execute(
                select(story_tables.story_runs).where(
                    story_tables.story_runs.c.run_id == TEACHER_RUN_ID
                )
            )
            .mappings()
            .one()
        )
        run_input = (
            session.execute(
                select(story_tables.run_inputs).where(
                    story_tables.run_inputs.c.run_input_id == TEACHER_RUN_INPUT_ID
                )
            )
            .mappings()
            .one()
        )
        aggregate = session.get(CoreAggregateRevisionModel, TEACHER_RUN_ID)
        outbox = list(
            session.scalars(
                select(CoreOutboxEventModel).where(
                    CoreOutboxEventModel.aggregate_id == TEACHER_RUN_ID
                )
            )
        )
        audits = list(
            session.scalars(
                select(CoreAuditEntryModel).where(CoreAuditEntryModel.resource_id == TEACHER_RUN_ID)
            )
        )
        receipt = (
            session.execute(
                select(story_tables.story_command_receipts).where(
                    story_tables.story_command_receipts.c.resource_ref == TEACHER_RUN_ID,
                    story_tables.story_command_receipts.c.operation == "CANCEL_RUN",
                )
            )
            .mappings()
            .all()
        )

    assert run["actor_scope_kind"] == "ORGANIZATION" and run["actor_scope_ref"] == ORG_A
    assert run["profile_ref"] == TEACHER_RUN_PROFILE_REF == "seed-ch-a-1-1"
    assert run["run_state"] == "DELETE_PENDING"
    assert run["revision"] == 2 and run["version"] == 2
    assert run["active_owner_parent_account_id"] is None
    assert all(
        run[column] is None
        for column in ("asset_ref", "derived_asset_ref", "current_video_generation_id")
    )
    assert run_input["context_snapshot"]["schema_version"] == data.PARENT_CONTEXT_SCHEMA
    assert run_input["context_snapshot_sha256"] == data.sha256_json(run_input["context_snapshot"])
    assert run_input["original_asset_ref"] is None and run_input["derived_asset_ref"] is None
    assert aggregate is not None
    assert aggregate.owner_scope_kind == "ORGANIZATION"
    assert aggregate.owner_scope_ref == ORG_A and aggregate.revision == 2
    assert len(outbox) == 1 and outbox[0].event_type == CANCEL_EVENT_TYPE
    assert outbox[0].status == "pending"
    assert outbox[0].owner_scope_kind == "ORGANIZATION" and outbox[0].owner_scope_ref == ORG_A
    assert len(audits) == 1 and audits[0].action == AUDIT_CANCEL_ACCEPTED
    assert audits[0].owner_scope_kind == "ORGANIZATION" and audits[0].owner_scope_ref == ORG_A
    assert len(receipt) == 1 and receipt[0]["state"] == "FINAL"
    assert receipt[0]["response_body"]["run_state"] == "DELETE_PENDING"
    with seed_engine.connect() as connection:
        assert count_stage_rows(connection) == EXPECTED


def test_private_nonapproved_versions_are_visible_to_the_seeded_parent(
    seed_engine: Engine,
    stage_runs: tuple[StageRun, ...],
) -> None:
    versions_by_title: dict[str, dict[str, Any]] = {}
    with Session(seed_engine) as session:
        rows = (
            session.execute(
                select(
                    LIBRARY_ITEMS.c.lesson_id,
                    LIBRARY_ITEMS.c.visibility,
                    LIBRARY_VERSIONS.c.version_id,
                    LIBRARY_VERSIONS.c.review_state,
                    LIBRARY_VERSIONS.c.content_json["title"].astext.label("title"),
                )
                .select_from(
                    LIBRARY_ITEMS.join(
                        LIBRARY_VERSIONS,
                        LIBRARY_ITEMS.c.current_version_id == LIBRARY_VERSIONS.c.version_id,
                    )
                )
                .where(LIBRARY_ITEMS.c.organization_id == ORG_A)
            )
            .mappings()
            .all()
        )
        wanted_titles = {content["title"] for content in LESSON_CONTENTS.values()}
        versions_by_title = {
            row["title"]: dict(row) for row in rows if row["title"] in wanted_titles
        }
        assert len(versions_by_title) == 3
        by_lesson_key = {
            key: versions_by_title[content["title"]] for key, content in LESSON_CONTENTS.items()
        }

        grants_by_lesson: dict[str, list[Any]] = {}
        for row in session.execute(select(ACCESS_GRANTS)).mappings().all():
            if row["lesson_id"] in {item["lesson_id"] for item in by_lesson_key.values()}:
                grants_by_lesson.setdefault(row["lesson_id"], []).append(dict(row))

        parent_page = LessonLibraryService(
            session,
            storage=cast(ObjectStoragePort, None),
            parser=cast(LessonDocumentParser, None),
            scanner=cast(MalwareScanner, None),
        ).list_parent_lessons(
            parent_principal_ref=PARENT_P1,
            source="SHARED",
            limit=100,
            cursor=None,
        )

    chicken = by_lesson_key["chicken"]
    sailing = by_lesson_key["sailing"]
    sunflower = by_lesson_key["sunflower"]
    assert chicken["review_state"] == "DRAFT" and chicken["visibility"] == "SCHOOL"
    assert sailing["review_state"] == "PENDING_REVIEW"
    assert sailing["visibility"] == "SELECTED_AUDIENCE"
    assert sunflower["review_state"] == "CHANGES_REQUESTED"
    assert sunflower["visibility"] == "SELECTED_AUDIENCE"

    sailing_grants = grants_by_lesson[sailing["lesson_id"]]
    assert any(
        grant["audience_kind"] == "PRINCIPAL"
        and grant["audience_ref"] == PARENT_P1
        and grant["capability"] == "VIEW"
        and grant["state"] == "INVITED"
        for grant in sailing_grants
    )
    assert any(
        grant["audience_kind"] == "PARENT_GROUP"
        and grant["audience_ref"] == PARENT_GROUP_A1
        and grant["state"] == "ACTIVE"
        for grant in sailing_grants
    )
    sunflower_public_request = next(
        grant
        for grant in grants_by_lesson[sunflower["lesson_id"]]
        if grant["audience_kind"] == "PUBLIC"
    )
    assert sunflower_public_request["state"] == "CHANGES_REQUESTED"
    assert sunflower_public_request["decision_reason"] == REVIEW_CHANGE_REASON
    parent_titles = {item["title"] for item in parent_page["items"]}
    assert LESSON_CONTENTS["sailing"]["title"] in parent_titles
    assert LESSON_CONTENTS["sunflower"]["title"] in parent_titles
    assert LESSON_CONTENTS["chicken"]["title"] not in parent_titles


def test_s11_counts_are_limited_to_its_seeded_records(
    seed_engine: Engine,
    stage_runs: tuple[StageRun, ...],
) -> None:
    with seed_engine.connect() as connection:
        counts = count_stage_rows(connection)
    assert counts == EXPECTED
    assert stage_key("s11", TEACHER_RUN_CANCEL_KEY) == "seed:s11:teacher-run-cancel"


def test_lesson_share_specs_reference_only_seeded_adults() -> None:
    assert {spec["author"] for spec in PRIVATE_SHARE_SPECS} == {
        TEACHER_A1,
        data.ORG_A_TEACHERS[1],
    }
    assert data.manager_subject("a") == MANAGER_A
