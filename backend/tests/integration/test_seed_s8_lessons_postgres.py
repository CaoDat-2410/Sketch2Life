"""PostgreSQL acceptance checks for the S8 lesson occurrence seed stage."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import TypedDict

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from sketch2life.infrastructure.lesson_occurrences.documents import OccurrenceDocumentService
from sketch2life.infrastructure.lesson_occurrences.plans import PlanRevisionService
from sketch2life.infrastructure.lesson_occurrences.service import LessonOccurrenceService
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s1_core import count_rows, run_s1
from tools.seed.s7a_runs import run_s7a
from tools.seed.s8_lessons import count_s8_rows, run_s8
from tools.seed.s8_lessons_data import DOCUMENTS, EXPECTED, OCCURRENCES
from tools.seed.stage_common import StageResult, check_database_prefix, seed_principal

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
    first = run_s8(seed_engine)
    second = run_s8(seed_engine)
    with seed_engine.connect() as connection:
        totals = count_s8_rows(connection)
        s1_totals = count_rows(connection)
    return {"first": first, "second": second, "totals": totals, "s1_totals": s1_totals}


def test_s8_twice_adds_no_rows_and_preserves_s1(seeded: SeededRows) -> None:
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


def test_product_reads_return_document_and_plan_history_without_storage(
    seed_engine: Engine, seeded: SeededRows
) -> None:
    occurrence_ids: dict[str, str] = {}
    for spec in OCCURRENCES:
        session = Session(seed_engine)
        try:
            principal = seed_principal(spec.teacher_subject)
            body = LessonOccurrenceService(session).get(
                principal=principal,
                occurrence_id=_occurrence_id(seed_engine, spec.key),
            )
            occurrence_ids[spec.key] = str(body["occurrence_id"])
        finally:
            session.rollback()
            session.close()

    for document in DOCUMENTS:
        occurrence_id = occurrence_ids[document.occurrence_key]
        spec = next(row for row in OCCURRENCES if row.key == document.occurrence_key)
        session = Session(seed_engine)
        try:
            principal = seed_principal(spec.teacher_subject)
            service = OccurrenceDocumentService(session, storage=None, parser=None)
            page = service.list_documents(
                principal=principal, occurrence_id=occurrence_id, limit=10, cursor=None
            )
            assert len(page["items"]) == 1
            document_body = page["items"][0]
            assert document_body["file_name"] == document.safe_file_name
            assert document_body["page_or_slide_count"] == document.page_count
            assert (
                service.get_document(
                    principal=principal,
                    occurrence_id=occurrence_id,
                    document_id=document_body["source_document_id"],
                )["source_document_id"]
                == document_body["source_document_id"]
            )
            revisions = service.list_revisions(
                principal=principal,
                occurrence_id=occurrence_id,
                document_id=document_body["source_document_id"],
                limit=10,
                cursor=None,
            )["items"]
            assert len(revisions) == (2 if document.key == "doc-o1" else 1)
            for revision in revisions:
                body = service.get_revision(
                    principal=principal,
                    occurrence_id=occurrence_id,
                    document_id=document_body["source_document_id"],
                    revision_no=revision["revision_no"],
                )
                assert len(body["extracted_text"]) >= 400
                assert len(body["text_hash"]) == 64
            if document.key == "doc-o1":
                by_revision = {row["revision_no"]: row for row in revisions}
                assert by_revision[2]["origin"] == "TEACHER_EDIT"
                assert by_revision[1]["origin"] == "EXTRACTION"
            if document.key == "doc-o2":
                assert document_body["warnings"] == ["OCR_NOT_SUPPORTED_PAGES"]
            if document.key == "doc-o5":
                assert document_body["page_or_slide_count"] == 12
        finally:
            session.rollback()
            session.close()

    expected_states = {
        "o1": ["APPROVED"],
        "o2": ["DRAFT"],
        "o3": ["DRAFT", "APPROVED", "SUPERSEDED"],
        "o4": [],
        "o5": [],
    }
    for spec in OCCURRENCES:
        occurrence_id = occurrence_ids[spec.key]
        session = Session(seed_engine)
        try:
            principal = seed_principal(spec.teacher_subject)
            page = PlanRevisionService(session).list_revisions(
                principal=principal, occurrence_id=occurrence_id, limit=10, cursor=None
            )
            revisions = page["items"]
            assert [row["state"] for row in revisions] == expected_states[spec.key]
            for revision in revisions:
                body = PlanRevisionService(session).get_revision(
                    principal=principal,
                    occurrence_id=occurrence_id,
                    revision_no=revision["revision_no"],
                )
                assert body["objectives"]
                assert body["teacher_direction"].strip()
                assert body["safety_notes"].strip()
            if spec.key == "o1":
                assert revisions[0]["activity_count"] == 2
                occurrence = LessonOccurrenceService(session).get(
                    principal=principal, occurrence_id=occurrence_id
                )
                assert occurrence["state"] == "APPROVED"
                assert occurrence["approved_plan"]["revision_no"] == 1
            if spec.key == "o2":
                assert revisions[0]["activity_count"] == 2
            if spec.key == "o3":
                assert [row["revision_no"] for row in revisions] == [3, 2, 1]
                assert all(row["activity_count"] == 0 for row in revisions)
        finally:
            session.rollback()
            session.close()


def _occurrence_id(engine: Engine, key: str) -> str:
    """Resolve the service-created row by its unique seeded class/title pair."""
    from sqlalchemy import select

    from sketch2life.infrastructure.lesson_occurrences.tables import (
        OCCURRENCES as OCCURRENCE_TABLE,
    )

    spec = next(row for row in OCCURRENCES if row.key == key)
    with engine.connect() as connection:
        return str(
            connection.execute(
                select(OCCURRENCE_TABLE.c.occurrence_id).where(
                    OCCURRENCE_TABLE.c.class_ref == data.class_id("a", spec.class_number),
                    OCCURRENCE_TABLE.c.title == spec.title,
                )
            ).scalar_one()
        )
