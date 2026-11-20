"""FEAT-066 T-3a: DDL-A constraints and triggers on PostgreSQL (migration ``20261119_oc_0001``).

Runs only against a disposable database whose name contains ``be1_acceptance`` and
``frc08``. Every negative case runs in its own transaction and is rolled back; rows that a
positive case writes stay (DELETE is forbidden by design), under unique ids. Only synthetic data.
"""

from __future__ import annotations

import hashlib
import os
import threading
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import Connection, Engine, create_engine, null, text, update
from sqlalchemy.exc import DBAPIError

from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
    SOURCE_DOCUMENTS,
)

HEX = "c" * 64
PIN = {
    "source_lesson_id": "lesson-1",
    "source_lesson_version_id": "version-1",
    "source_lesson_version_no": 2,
    "source_lesson_version_hash": HEX,
}


def sha(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    name = url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in name or "frc08" not in name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08*be1_acceptance db")
    created = create_engine(url)
    yield created
    created.dispose()


class Builder:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    # ------------------------------------------------------------------ rows
    def occurrence(self, **over: Any) -> str:
        values: dict[str, Any] = {
            "occurrence_id": str(uuid4()),
            "organization_ref": "org-1",
            "class_ref": "class-1",
            "responsible_teacher_ref": "acct-1",
            "created_by": "acct-1",
            "title": "Bài học",
        }
        values.update(over)
        with self.engine.begin() as conn:
            conn.execute(OCCURRENCES.insert().values(**values))
        return str(values["occurrence_id"])

    def document(self, occurrence_id: str, **over: Any) -> str:
        values: dict[str, Any] = {
            "source_document_id": str(uuid4()),
            "occurrence_id": occurrence_id,
            "asset_ref": f"asset-{uuid4()}",
            "upload_session_ref": str(uuid4()),
            "extraction_job_ref": f"job-{uuid4()}",
            "safe_file_name": "plan.pdf",
            "file_extension": ".pdf",
            "page_or_slide_count": 3,
            "uploaded_by": "acct-1",
        }
        values.update(over)
        with self.engine.begin() as conn:
            conn.execute(SOURCE_DOCUMENTS.insert().values(**values))
        return str(values["source_document_id"])

    @staticmethod
    def revision_values(document_id: str, number: int, **over: Any) -> dict[str, Any]:
        body = f"Văn bản trích xuất {number}"
        values: dict[str, Any] = {
            "document_revision_id": str(uuid4()),
            "source_document_id": document_id,
            "revision_no": number,
            "origin": "EXTRACTION" if number == 1 else "TEACHER_EDIT",
            "base_revision_no": None if number == 1 else number - 1,
            "extracted_text": body,
            "extracted_text_hash": sha(body),
            "parser_name": "deterministic" if number == 1 else None,
            "parser_version": "1" if number == 1 else None,
            "created_by": "acct-1",
        }
        values.update(over)
        return values

    def revision(self, document_id: str, number: int = 1, **over: Any) -> str:
        values = self.revision_values(document_id, number, **over)
        with self.engine.begin() as conn:
            conn.execute(DOCUMENT_REVISIONS.insert().values(**values))
        return str(values["document_revision_id"])

    @staticmethod
    def plan_values(occurrence_id: str, number: int, **over: Any) -> dict[str, Any]:
        values: dict[str, Any] = {
            "plan_revision_id": str(uuid4()),
            "occurrence_id": occurrence_id,
            "revision_no": number,
            "objectives": ["Nhận biết hình tròn"],
            "teacher_direction": "Kể chuyện chú mèo",
            "content_hash": HEX,
            "created_by": "acct-1",
        }
        values.update(over)
        return values

    def plan(self, occurrence_id: str, number: int = 1, **over: Any) -> str:
        values = self.plan_values(occurrence_id, number, **over)
        with self.engine.begin() as conn:
            conn.execute(PLAN_REVISIONS.insert().values(**values))
        return str(values["plan_revision_id"])

    @staticmethod
    def activity_values(
        plan_id: str, order: int, kind: str = "CUSTOM", **over: Any
    ) -> dict[str, Any]:
        values: dict[str, Any] = {
            "plan_activity_id": str(uuid4()),
            "plan_revision_id": plan_id,
            "activity_order": order,
            "activity_kind": kind,
        }
        if kind == "CUSTOM":
            values.update(custom_title="Vẽ theo mẫu", custom_description="Trẻ vẽ hình tròn")
        else:
            values.update(
                catalog_activity_ref="activity-1",
                activity_version=1,
                activity_snapshot={"title": "Hoạt động"},
                activity_snapshot_hash=HEX,
            )
        values.update(over)
        return values

    def activity(self, plan_id: str, order: int = 1, kind: str = "CUSTOM", **over: Any) -> str:
        values = self.activity_values(plan_id, order, kind, **over)
        with self.engine.begin() as conn:
            conn.execute(PLAN_ACTIVITIES.insert().values(**values))
        return str(values["plan_activity_id"])

    # ------------------------------------------------------------------ transitions
    def approve(self, plan_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                update(PLAN_REVISIONS)
                .where(PLAN_REVISIONS.c.plan_revision_id == plan_id)
                .values(state="APPROVED", approved_by="acct-1", approved_at=datetime.now(UTC))
            )

    def confirm_activity(self, activity_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                update(PLAN_ACTIVITIES)
                .where(PLAN_ACTIVITIES.c.plan_activity_id == activity_id)
                .values(
                    safety_checklist_version="1",
                    checklist_result={"items": []},
                    confirmed_by="acct-1",
                    confirmed_at=datetime.now(UTC),
                )
            )

    # ------------------------------------------------------------------ assertions
    def refuse(self, work: Callable[[Connection], object], *needles: str) -> None:
        """Run ``work`` in one transaction; it must fail with a database error naming a needle."""
        with self.engine.connect() as conn:
            transaction = conn.begin()
            try:
                try:
                    work(conn)
                except DBAPIError as error:
                    message = str(error)
                    assert any(needle in message for needle in needles), (needles, message[:300])
                else:
                    pytest.fail(f"the statement was accepted; expected one of {needles}")
            finally:
                transaction.rollback()


@pytest.fixture
def build(engine: Engine) -> Builder:
    return Builder(engine)


def set_values(table: Any, key: Any, value: str, **values: Any) -> Callable[[Connection], object]:
    return lambda conn: conn.execute(update(table).where(key == value).values(**values))


# ============================================================================ occurrences
def test_occurrence_defaults_and_value_checks(build: Builder, engine: Engine) -> None:
    occurrence_id = build.occurrence(scheduled_date=date(2026, 11, 20))
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "select state, revision, sample_slot_state, created_at, updated_at, "
                "approved_plan_revision_id from lesson.occurrences where occurrence_id = :i"
            ),
            {"i": occurrence_id},
        ).one()
    assert row.state == "DRAFT" and row.revision == 1 and row.sample_slot_state == "AVAILABLE"
    assert row.created_at is not None and row.updated_at is not None
    assert row.approved_plan_revision_id is None
    for bad in (
        {"title": "   "},
        {"title": "x" * 201},
        {"revision": 0},
        {"state": "DONE"},
        {"source_lesson_id": "only-one"},
        {**PIN, "source_lesson_version_no": 0},
        {**PIN, "source_lesson_version_hash": "XYZ"},
        {"sample_slot_state": "CLAIMED"},
        {"sample_slot_state": "CLOSED"},
        {"sample_claimed_at": datetime.now(UTC)},
        {"class_projection_confirmed_by_ref": "acct-1"},
    ):
        build.refuse(
            lambda c, b=bad: c.execute(
                OCCURRENCES.insert().values(
                    **{
                        "occurrence_id": str(uuid4()),
                        "organization_ref": "o",
                        "class_ref": "c",
                        "responsible_teacher_ref": "a",
                        "created_by": "a",
                        "title": "t",
                        **b,
                    }
                )
            ),
            "ck_occ_",
            "OCCURRENCE_INSERT_NOT_DRAFT",
            "too long",
        )
    pinned = build.occurrence(**PIN)
    assert pinned


def test_an_occurrence_is_born_draft_without_a_plan_pointer(build: Builder) -> None:
    for over in (
        {"state": "APPROVED"},
        {"state": "ARCHIVED"},
        {"approved_plan_revision_id": "p"},
    ):
        build.refuse(
            lambda c, o=over: c.execute(
                OCCURRENCES.insert().values(
                    occurrence_id=str(uuid4()),
                    organization_ref="o",
                    class_ref="c",
                    responsible_teacher_ref="a",
                    created_by="a",
                    title="t",
                    **o,
                )
            ),
            "OCCURRENCE_INSERT_NOT_DRAFT",
            "ck_occ_plan_state",
            "fk_occ_approved_plan",
        )


def test_occurrence_identity_columns_are_immutable_and_delete_is_forbidden(build: Builder) -> None:
    occurrence_id = build.occurrence(**PIN)
    key = OCCURRENCES.c.occurrence_id
    for column, value in (
        ("organization_ref", "org-2"),
        ("class_ref", "class-2"),
        ("created_by", "acct-2"),
        ("created_at", datetime(2020, 1, 1, tzinfo=UTC)),
        ("source_lesson_id", "other"),
        ("source_lesson_version_id", "other"),
        ("source_lesson_version_no", 9),
        ("source_lesson_version_hash", "d" * 64),
        ("occurrence_id", str(uuid4())),
    ):
        build.refuse(
            set_values(OCCURRENCES, key, occurrence_id, **{column: value}),
            "OCCURRENCE_IMMUTABLE_COLUMN",
        )
    build.refuse(
        lambda c: c.execute(
            text("delete from lesson.occurrences where occurrence_id = :i"), {"i": occurrence_id}
        ),
        "OCCURRENCE_DELETE_FORBIDDEN",
    )
    with build.engine.begin() as conn:
        for values in (
            {"title": "Mới", "revision": 2, "updated_at": datetime.now(UTC)},
            {"responsible_teacher_ref": "acct-2"},
            {"state": "ARCHIVED"},
        ):
            conn.execute(update(OCCURRENCES).where(key == occurrence_id).values(**values))
    build.refuse(set_values(OCCURRENCES, key, occurrence_id, state="APPROVED"), "ck_occ_plan_state")


def test_the_approved_plan_pointer_is_a_composite_immediate_foreign_key(build: Builder) -> None:
    first, second = build.occurrence(), build.occurrence()
    plan_of_first = build.plan(first)
    plan_of_second = build.plan(second)
    build.approve(plan_of_first)
    build.approve(plan_of_second)
    key = OCCURRENCES.c.occurrence_id

    foreign = {"approved_plan_revision_id": plan_of_first, "state": "APPROVED"}
    # Layer 1: the trigger refuses a plan of another occurrence before the foreign key is asked.
    build.refuse(set_values(OCCURRENCES, key, second, **foreign), "OCCURRENCE_PLAN_NOT_APPROVED")

    def without_the_trigger(conn: Connection) -> None:
        # Layer 2: with the trigger off, the immediate composite foreign key still answers at the
        # statement (not at COMMIT) and names the constraint.
        conn.execute(text("alter table lesson.occurrences disable trigger protect_occurrence"))
        conn.execute(update(OCCURRENCES).where(key == second).values(**foreign))

    build.refuse(without_the_trigger, "fk_occ_approved_plan")
    with build.engine.connect() as conn:
        definition, deferrable = conn.execute(
            text(
                "select pg_get_constraintdef(oid), condeferrable from pg_constraint "
                "where conname = 'fk_occ_approved_plan'"
            )
        ).one()
    assert "FOREIGN KEY (approved_plan_revision_id, occurrence_id)" in definition
    assert "REFERENCES lesson.plan_revisions(plan_revision_id, occurrence_id)" in definition
    assert deferrable is False
    with build.engine.begin() as conn:
        conn.execute(
            update(OCCURRENCES)
            .where(key == first)
            .values(approved_plan_revision_id=plan_of_first, state="APPROVED")
        )
    with build.engine.connect() as conn:
        assert (
            conn.execute(
                text(
                    "select approved_plan_revision_id from lesson.occurrences "
                    "where occurrence_id = :i"
                ),
                {"i": first},
            ).scalar()
            == plan_of_first
        )


def test_the_pointer_must_name_an_approved_plan(build: Builder) -> None:
    occurrence_id = build.occurrence()
    draft = build.plan(occurrence_id)
    key = OCCURRENCES.c.occurrence_id
    build.refuse(
        set_values(
            OCCURRENCES, key, occurrence_id, approved_plan_revision_id=draft, state="APPROVED"
        ),
        "OCCURRENCE_PLAN_NOT_APPROVED",
    )
    build.approve(draft)
    with build.engine.begin() as conn:
        conn.execute(
            update(OCCURRENCES)
            .where(key == occurrence_id)
            .values(approved_plan_revision_id=draft, state="APPROVED")
        )
    # After supersession a different pointer must again name an approved plan.
    second = build.plan(occurrence_id, 2)
    with build.engine.begin() as conn:
        conn.execute(
            update(PLAN_REVISIONS)
            .where(PLAN_REVISIONS.c.plan_revision_id == draft)
            .values(state="SUPERSEDED", superseded_at=datetime.now(UTC))
        )
    build.refuse(
        set_values(OCCURRENCES, key, occurrence_id, approved_plan_revision_id=second),
        "OCCURRENCE_PLAN_NOT_APPROVED",
    )
    build.approve(second)
    with build.engine.begin() as conn:
        conn.execute(
            update(OCCURRENCES).where(key == occurrence_id).values(approved_plan_revision_id=second)
        )


# ============================================================================ source documents
def test_source_document_rules(build: Builder) -> None:
    occurrence_id = build.occurrence()
    document_id = build.document(occurrence_id)
    asset = f"asset-{uuid4()}"
    first = build.document(occurrence_id, asset_ref=asset)
    session = str(uuid4())
    build.refuse(
        lambda c: c.execute(
            SOURCE_DOCUMENTS.insert().values(
                source_document_id=str(uuid4()),
                occurrence_id=occurrence_id,
                asset_ref=asset,
                upload_session_ref=session,
                extraction_job_ref="j",
                safe_file_name="a.pdf",
                file_extension=".pdf",
                uploaded_by="acct-1",
            )
        ),
        "uq_srcdoc_asset",
    )
    same_session = build.document(occurrence_id, upload_session_ref=session)
    assert same_session and first
    build.refuse(
        lambda c: c.execute(
            SOURCE_DOCUMENTS.insert().values(
                source_document_id=str(uuid4()),
                occurrence_id=occurrence_id,
                asset_ref="another-asset",
                upload_session_ref=session,
                extraction_job_ref="j",
                safe_file_name="a.pdf",
                file_extension=".pdf",
                uploaded_by="acct-1",
            )
        ),
        "uq_srcdoc_upload_session",
    )
    for bad in (
        {"file_extension": ".exe"},
        {"page_or_slide_count": 101},
        {"page_or_slide_count": 0},
        {"safe_file_name": "  "},
        {"asset_version": 0},
        {"document_state": "DELETED"},
        {"document_state": "GONE"},
    ):
        build.refuse(
            lambda c, b=bad: c.execute(
                SOURCE_DOCUMENTS.insert().values(
                    **{
                        "source_document_id": str(uuid4()),
                        "occurrence_id": occurrence_id,
                        "asset_ref": f"a-{uuid4()}",
                        "upload_session_ref": str(uuid4()),
                        "extraction_job_ref": "j",
                        "safe_file_name": "a.pdf",
                        "file_extension": ".pdf",
                        "uploaded_by": "acct-1",
                        **b,
                    }
                )
            ),
            "ck_srcdoc_",
            "SOURCE_DOCUMENT_INSERT_NOT_EXTRACTED",
        )
    build.document(occurrence_id, page_or_slide_count=None, file_extension=".docx")
    build.document(occurrence_id, page_or_slide_count=100, file_extension=".pptx")
    key = SOURCE_DOCUMENTS.c.source_document_id
    for column, value in (
        ("asset_ref", "x"),
        ("extraction_job_ref", "x"),
        ("safe_file_name", "x.pdf"),
        ("page_or_slide_count", 4),
        ("uploaded_by", "acct-9"),
        ("occurrence_id", build.occurrence()),
    ):
        build.refuse(
            set_values(SOURCE_DOCUMENTS, key, document_id, **{column: value}),
            "SOURCE_DOCUMENT_IMMUTABLE",
        )
    build.refuse(
        lambda c: c.execute(
            text("delete from lesson.source_documents where source_document_id = :i"),
            {"i": document_id},
        ),
        "SOURCE_DOCUMENT_DELETE_FORBIDDEN",
    )
    build.refuse(
        set_values(SOURCE_DOCUMENTS, key, document_id, document_state="DELETED"),
        "ck_srcdoc_deleted",
    )
    with build.engine.begin() as conn:
        conn.execute(
            update(SOURCE_DOCUMENTS)
            .where(key == document_id)
            .values(document_state="DELETED", deleted_at=datetime.now(UTC))
        )
    build.refuse(
        set_values(SOURCE_DOCUMENTS, key, document_id, document_state="EXTRACTED", deleted_at=None),
        "SOURCE_DOCUMENT_STATE_ONE_WAY",
    )


# ============================================================================ document revisions
def test_document_revision_lineage_numbering_and_text_checks(build: Builder) -> None:
    document_id = build.document(build.occurrence())
    first = build.revision(document_id, 1)
    assert first
    build.refuse(
        lambda c: c.execute(
            DOCUMENT_REVISIONS.insert().values(**Builder.revision_values(document_id, 3))
        ),
        "DOCUMENT_REVISION_NUMBER_GAP",
    )
    build.refuse(
        lambda c: c.execute(
            DOCUMENT_REVISIONS.insert().values(**Builder.revision_values(document_id, 1))
        ),
        "uq_docrev_number",
        "DOCUMENT_REVISION_NUMBER_GAP",
    )
    build.revision(document_id, 2)
    base = Builder.revision_values(document_id, 3)
    for bad in (
        {"origin": "EXTRACTION"},
        {"base_revision_no": None},
        {"base_revision_no": 3},
        {"parser_name": "p", "parser_version": "1"},
        {"extracted_text": ""},
        {"extracted_text": "Khác", "extracted_text_hash": sha("Văn bản trích xuất 3")},
        {"extracted_text_hash": "g" * 64},
        {"extraction_warnings": {"a": 1}},
        {"page_coverage": "[]"},
        {"review_state": "CONFIRMED", "reviewed_by": "acct-1", "reviewed_at": datetime.now(UTC)},
        {"origin": "ANYTHING"},
    ):
        build.refuse(
            lambda c, b=bad: c.execute(DOCUMENT_REVISIONS.insert().values(**{**base, **b})),
            "ck_docrev_",
            "DOCUMENT_REVISION_INSERT_NOT_PENDING",
            "invalid input",
        )
    edit = Builder.revision_values(document_id, 1, document_revision_id=str(uuid4()))
    build.refuse(
        lambda c: c.execute(
            DOCUMENT_REVISIONS.insert().values(**{**edit, "origin": "TEACHER_EDIT"})
        ),
        "ck_docrev_lineage",
        "DOCUMENT_REVISION_NUMBER_GAP",
        "uq_docrev_number",
    )


def test_extracted_text_is_bounded_in_bytes_and_hashed(build: Builder) -> None:
    document_id = build.document(build.occurrence())
    exact = "a" * 2_097_152
    build.revision(document_id, 1, extracted_text=exact, extracted_text_hash=sha(exact))
    over = "a" * 2_097_153
    build.refuse(
        lambda c: c.execute(
            DOCUMENT_REVISIONS.insert().values(
                **Builder.revision_values(
                    document_id, 2, extracted_text=over, extracted_text_hash=sha(over)
                )
            )
        ),
        "ck_docrev_text_size",
    )
    multibyte = "ề" * 700_000  # 3 bytes each: 2,100,000 bytes, 700,000 characters
    build.refuse(
        lambda c: c.execute(
            DOCUMENT_REVISIONS.insert().values(
                **Builder.revision_values(
                    document_id, 2, extracted_text=multibyte, extracted_text_hash=sha(multibyte)
                )
            )
        ),
        "ck_docrev_text_size",
    )
    smaller = "ề" * 699_000  # 2,097,000 bytes
    build.revision(document_id, 2, extracted_text=smaller, extracted_text_hash=sha(smaller))


def test_document_revisions_are_immutable_except_the_one_way_review_stamp(build: Builder) -> None:
    document_id = build.document(build.occurrence())
    revision_id = build.revision(document_id, 1)
    other = build.revision(document_id, 2)
    key = DOCUMENT_REVISIONS.c.document_revision_id
    for column, value in (
        ("extracted_text", "Sửa"),
        ("extracted_text_hash", HEX),
        ("revision_no", 9),
        ("origin", "TEACHER_EDIT"),
        ("parser_name", "x"),
        ("created_by", "acct-2"),
        ("extraction_warnings", ["W"]),
        ("page_coverage", [1]),
    ):
        build.refuse(
            set_values(DOCUMENT_REVISIONS, key, revision_id, **{column: value}),
            "DOCUMENT_REVISION_IMMUTABLE",
            "ck_docrev_",
        )
    build.refuse(
        lambda c: c.execute(
            text("delete from lesson.document_revisions where document_revision_id = :i"),
            {"i": revision_id},
        ),
        "DOCUMENT_REVISION_DELETE_FORBIDDEN",
    )
    build.refuse(
        set_values(DOCUMENT_REVISIONS, key, revision_id, review_state="CONFIRMED"),
        "ck_docrev_review",
    )
    stamp = {"review_state": "CONFIRMED", "reviewed_by": "acct-1", "reviewed_at": datetime.now(UTC)}
    with build.engine.begin() as conn:
        conn.execute(update(DOCUMENT_REVISIONS).where(key == revision_id).values(**stamp))
    build.refuse(
        set_values(
            DOCUMENT_REVISIONS,
            key,
            revision_id,
            review_state="NEEDS_REVIEW",
            reviewed_by=None,
            reviewed_at=None,
        ),
        "DOCUMENT_REVISION_REVIEW_ONE_WAY",
    )
    build.refuse(
        set_values(DOCUMENT_REVISIONS, key, revision_id, reviewed_by="acct-2"),
        "DOCUMENT_REVISION_REVIEW_ONE_WAY",
    )
    with build.engine.connect() as conn:
        assert (
            conn.execute(
                text(
                    "select review_state from lesson.document_revisions "
                    "where document_revision_id = :i"
                ),
                {"i": other},
            ).scalar()
            == "NEEDS_REVIEW"
        )


def test_concurrent_revisions_of_one_number_leave_exactly_one(build: Builder) -> None:
    document_id = build.document(build.occurrence())
    build.revision(document_id, 1)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    reasons: list[str] = []

    def insert() -> None:
        values = Builder.revision_values(document_id, 2)
        try:
            with build.engine.begin() as conn:
                barrier.wait(timeout=10)
                conn.execute(DOCUMENT_REVISIONS.insert().values(**values))
            outcomes.append("ok")
        except DBAPIError as error:
            outcomes.append("refused")
            reasons.append(str(error))

    threads = [threading.Thread(target=insert) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert sorted(outcomes) == ["ok", "refused"]
    assert len(reasons) == 1 and (
        "uq_docrev_number" in reasons[0] or "DOCUMENT_REVISION_NUMBER_GAP" in reasons[0]
    )


# ============================================================================ plan revisions
def test_plan_revision_value_checks_and_defaults(build: Builder, engine: Engine) -> None:
    occurrence_id = build.occurrence()
    plan_id = build.plan(occurrence_id)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "select state, created_at, approved_by from lesson.plan_revisions "
                "where plan_revision_id = :i"
            ),
            {"i": plan_id},
        ).one()
    assert row.state == "DRAFT" and row.created_at is not None and row.approved_by is None
    base = Builder.plan_values(occurrence_id, 2)
    for bad in (
        {"objectives": []},
        {"objectives": [f"o{i}" for i in range(13)]},
        {"objectives": "text"},
        {"objectives": {"a": 1}},
        {"objectives": [1]},
        {"objectives": [""]},
        {"objectives": ["x" * 1001]},
        {"teacher_direction": "  "},
        {"teacher_direction": "x" * 2001},
        {"safety_notes": "x" * 2001},
        {"content_hash": "short"},
        {"state": "APPROVED", "approved_by": "a", "approved_at": datetime.now(UTC)},
        {"state": "SUPERSEDED"},
        {"approved_by": "acct-1"},
        {"superseded_at": datetime.now(UTC)},
        {"revision_no": 0},
        {"source_lesson_id": "only-one"},
    ):
        build.refuse(
            lambda c, b=bad: c.execute(PLAN_REVISIONS.insert().values(**{**base, **b})),
            "ck_plan_",
            "PLAN_",
            "invalid input",
            "uq_plan_number",
        )
    build.plan(occurrence_id, 2, objectives=[f"mục tiêu {i}" for i in range(12)])
    build.plan(
        occurrence_id,
        3,
        objectives=["x" * 1000],
        safety_notes="y" * 2000,
        teacher_direction="d" * 2000,
    )


def test_a_plan_is_born_a_draft_with_the_occurrence_pin_and_a_matching_document(
    build: Builder,
) -> None:
    pinned = build.occurrence(**PIN)
    plain = build.occurrence()
    build.plan(pinned, 1, **PIN)
    build.plan(plain, 1)
    for occurrence_id, over in (
        (pinned, {}),  # a plan without the pin of its pinned occurrence
        (pinned, {**PIN, "source_lesson_version_no": 3}),
        (pinned, {**PIN, "source_lesson_version_hash": "e" * 64}),
        (plain, PIN),  # a pin the occurrence does not have
    ):
        build.refuse(
            lambda c, o=occurrence_id, v=over: c.execute(
                PLAN_REVISIONS.insert().values(**Builder.plan_values(o, 2, **v))
            ),
            "PLAN_PIN_MISMATCH",
        )
    document_id = build.document(plain)
    revision_id = build.revision(document_id, 1)
    other_revision = build.revision(build.document(build.occurrence()), 1)
    build.plan(plain, 2, source_document_revision_id=revision_id)
    build.refuse(
        lambda c: c.execute(
            PLAN_REVISIONS.insert().values(
                **Builder.plan_values(plain, 3, source_document_revision_id=other_revision)
            )
        ),
        "PLAN_DOCUMENT_MISMATCH",
    )
    build.refuse(
        lambda c: c.execute(
            PLAN_REVISIONS.insert().values(
                **Builder.plan_values(plain, 3, source_document_revision_id=str(uuid4()))
            )
        ),
        "PLAN_DOCUMENT_MISMATCH",
    )
    with build.engine.begin() as conn:
        conn.execute(
            update(SOURCE_DOCUMENTS)
            .where(SOURCE_DOCUMENTS.c.source_document_id == document_id)
            .values(document_state="DELETED", deleted_at=datetime.now(UTC))
        )
    build.refuse(
        lambda c: c.execute(
            PLAN_REVISIONS.insert().values(
                **Builder.plan_values(plain, 3, source_document_revision_id=revision_id)
            )
        ),
        "PLAN_DOCUMENT_MISMATCH",
    )


def test_plan_numbers_have_no_gaps_and_a_born_approved_plan_is_refused(build: Builder) -> None:
    occurrence_id = build.occurrence()
    build.plan(occurrence_id, 1)
    for number in (3, 1, 0):
        build.refuse(
            lambda c, n=number: c.execute(
                PLAN_REVISIONS.insert().values(**Builder.plan_values(occurrence_id, n))
            ),
            "PLAN_REVISION_NUMBER_GAP",
            "ck_plan_number",
            "uq_plan_number",
        )
    build.refuse(
        lambda c: c.execute(
            PLAN_REVISIONS.insert().values(
                **Builder.plan_values(
                    occurrence_id,
                    2,
                    state="APPROVED",
                    approved_by="acct-1",
                    approved_at=datetime.now(UTC),
                )
            )
        ),
        "PLAN_INSERT_NOT_DRAFT",
    )


def test_the_plan_state_machine_and_content_immutability(build: Builder) -> None:
    occurrence_id = build.occurrence()
    first = build.plan(occurrence_id, 1)
    second = build.plan(occurrence_id, 2)
    key = PLAN_REVISIONS.c.plan_revision_id
    for column, value in (
        ("objectives", ["Khác"]),
        ("teacher_direction", "Khác"),
        ("safety_notes", "n"),
        ("content_hash", "f" * 64),
        ("revision_no", 8),
        ("source_document_revision_id", "x"),
        ("created_by", "acct-2"),
        ("occurrence_id", build.occurrence()),
        ("source_lesson_id", "l"),
    ):
        build.refuse(
            set_values(PLAN_REVISIONS, key, first, **{column: value}),
            "PLAN_IMMUTABLE_CONTENT",
            "ck_plan_",
            "fk_plan_",
        )
    build.refuse(
        lambda c: c.execute(
            text("delete from lesson.plan_revisions where plan_revision_id = :i"), {"i": first}
        ),
        "PLAN_REVISION_DELETE_FORBIDDEN",
    )
    build.refuse(
        set_values(
            PLAN_REVISIONS,
            key,
            first,
            state="SUPERSEDED",
            approved_by="a",
            approved_at=datetime.now(UTC),
            superseded_at=datetime.now(UTC),
        ),
        "PLAN_ILLEGAL_TRANSITION",
    )
    build.refuse(set_values(PLAN_REVISIONS, key, first, state="APPROVED"), "ck_plan_approval")
    build.approve(first)
    build.refuse(
        set_values(PLAN_REVISIONS, key, first, approved_by="acct-2"), "PLAN_ILLEGAL_TRANSITION"
    )
    build.refuse(
        set_values(PLAN_REVISIONS, key, first, state="DRAFT", approved_by=None, approved_at=None),
        "PLAN_ILLEGAL_TRANSITION",
    )
    # One APPROVED plan per occurrence (SRS l.775): the second approval collides until the first
    # is superseded, which is the order of the confirm command.
    build.refuse(
        lambda c: c.execute(
            update(PLAN_REVISIONS)
            .where(key == second)
            .values(state="APPROVED", approved_by="acct-1", approved_at=datetime.now(UTC))
        ),
        "uq_plan_one_approved",
    )
    with build.engine.begin() as conn:
        conn.execute(
            update(PLAN_REVISIONS)
            .where(key == first)
            .values(state="SUPERSEDED", superseded_at=datetime.now(UTC))
        )
    build.approve(second)
    build.refuse(
        set_values(PLAN_REVISIONS, key, first, state="APPROVED", superseded_at=None),
        "PLAN_ILLEGAL_TRANSITION",
    )
    build.refuse(
        set_values(PLAN_REVISIONS, key, first, approved_by="acct-2"),
        "PLAN_IMMUTABLE_CONTENT",
        "PLAN_ILLEGAL_TRANSITION",
    )


def test_two_concurrent_approvals_of_one_occurrence_leave_one_approved(build: Builder) -> None:
    occurrence_id = build.occurrence()
    plans = [build.plan(occurrence_id, 1), build.plan(occurrence_id, 2)]
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    reasons: list[str] = []

    def approve(plan_id: str) -> None:
        try:
            with build.engine.begin() as conn:
                barrier.wait(timeout=10)
                conn.execute(
                    update(PLAN_REVISIONS)
                    .where(PLAN_REVISIONS.c.plan_revision_id == plan_id)
                    .values(state="APPROVED", approved_by="acct-1", approved_at=datetime.now(UTC))
                )
            outcomes.append("ok")
        except DBAPIError as error:
            outcomes.append("refused")
            reasons.append(str(error))

    threads = [threading.Thread(target=approve, args=(plan,)) for plan in plans]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert sorted(outcomes) == ["ok", "refused"]
    assert len(reasons) == 1 and "uq_plan_one_approved" in reasons[0]


# ============================================================================ plan activities
def test_plan_activity_shapes(build: Builder) -> None:
    plan_id = build.plan(build.occurrence())
    build.activity(plan_id, 1, "CUSTOM")
    build.activity(plan_id, 2, "LESSON")
    build.activity(plan_id, 3, "CATALOG")
    build.activity(plan_id, 24, "CUSTOM", custom_title="t" * 200, custom_description="d" * 4000)
    for bad in (
        {"activity_order": 0},
        {"activity_order": 25},
        {"activity_order": 1},
        {"activity_kind": "OTHER"},
        {"custom_title": "t" * 201},
        {"custom_title": "  "},
        {"custom_description": "d" * 4001},
        {"custom_description": None},
        {"catalog_activity_ref": "x"},
        {"activity_snapshot_hash": "z" * 64},
        {"safety_checklist_version": "1"},
    ):
        build.refuse(
            lambda c, b=bad: c.execute(
                PLAN_ACTIVITIES.insert().values(
                    **{**Builder.activity_values(plan_id, 5, "CUSTOM"), **b}
                )
            ),
            "ck_planact_",
            "uq_planact_order",
            "PLAN_ACTIVITY_INSERT_CONFIRMED",
            "too long",
        )
    for bad in (
        {"catalog_activity_ref": None},
        {"activity_snapshot": null()},
        {"activity_snapshot": None},  # a JSON null is not an object
        {"activity_snapshot": ["array"]},
        {"activity_snapshot_hash": None},
        {"activity_snapshot_hash": "short"},
        {"custom_title": "t"},
        {"activity_version": 0},
    ):
        build.refuse(
            lambda c, b=bad: c.execute(
                PLAN_ACTIVITIES.insert().values(
                    **{**Builder.activity_values(plan_id, 6, "LESSON"), **b}
                )
            ),
            "ck_planact_",
        )


def test_the_checklist_gate_blocks_approval_until_every_custom_activity_is_confirmed(
    build: Builder,
) -> None:
    occurrence_id = build.occurrence()
    plan_id = build.plan(occurrence_id)
    lesson = build.activity(plan_id, 1, "LESSON")
    custom = build.activity(plan_id, 2, "CUSTOM")
    key = PLAN_REVISIONS.c.plan_revision_id
    approval = {"state": "APPROVED", "approved_by": "acct-1", "approved_at": datetime.now(UTC)}
    build.refuse(
        set_values(PLAN_REVISIONS, key, plan_id, **approval), "LESSON_PLAN_CHECKLIST_REQUIRED"
    )
    activity_key = PLAN_ACTIVITIES.c.plan_activity_id
    build.refuse(
        set_values(
            PLAN_ACTIVITIES,
            activity_key,
            lesson,
            safety_checklist_version="1",
            checklist_result={},
            confirmed_by="a",
            confirmed_at=datetime.now(UTC),
        ),
        "ck_planact_checklist",
    )
    build.refuse(
        set_values(PLAN_ACTIVITIES, activity_key, custom, safety_checklist_version="1"),
        "ck_planact_checklist",
    )
    build.refuse(
        set_values(
            PLAN_ACTIVITIES,
            activity_key,
            custom,
            safety_checklist_version="1",
            checklist_result=["list"],
            confirmed_by="a",
            confirmed_at=datetime.now(UTC),
        ),
        "ck_planact_checklist",
    )
    build.confirm_activity(custom)
    build.refuse(
        set_values(
            PLAN_ACTIVITIES,
            activity_key,
            custom,
            safety_checklist_version="2",
            checklist_result={"x": 1},
            confirmed_by="b",
            confirmed_at=datetime.now(UTC),
        ),
        "PLAN_ACTIVITY_CHECKLIST_LOCKED",
    )
    build.approve(plan_id)
    # A plan with no activity, or with only library activities, approves without a checklist.
    bare = build.plan(build.occurrence())
    build.approve(bare)
    only_lesson = build.plan(build.occurrence())
    build.activity(only_lesson, 1, "LESSON")
    build.approve(only_lesson)


def test_activities_are_immutable_and_cannot_join_a_plan_that_is_no_longer_a_draft(
    build: Builder,
) -> None:
    plan_id = build.plan(build.occurrence())
    activity = build.activity(plan_id, 1, "CUSTOM")
    key = PLAN_ACTIVITIES.c.plan_activity_id
    for column, value in (
        ("custom_title", "Khác"),
        ("custom_description", "Khác"),
        ("activity_order", 9),
        ("activity_kind", "LESSON"),
        ("plan_revision_id", build.plan(build.occurrence())),
        ("catalog_activity_ref", "x"),
        ("activity_snapshot_hash", HEX),
    ):
        build.refuse(
            set_values(PLAN_ACTIVITIES, key, activity, **{column: value}),
            "PLAN_ACTIVITY_IMMUTABLE",
            "ck_planact_",
        )
    build.refuse(
        lambda c: c.execute(
            text("delete from lesson.plan_activities where plan_activity_id = :i"), {"i": activity}
        ),
        "PLAN_ACTIVITY_DELETE_FORBIDDEN",
    )
    build.confirm_activity(activity)
    build.approve(plan_id)
    build.refuse(
        lambda c: c.execute(
            PLAN_ACTIVITIES.insert().values(**Builder.activity_values(plan_id, 2, "LESSON"))
        ),
        "PLAN_ACTIVITY_PLAN_NOT_DRAFT",
    )
    other = build.plan(build.occurrence())
    late = build.activity(other, 1, "CUSTOM")
    with build.engine.begin() as conn:
        conn.execute(
            update(PLAN_ACTIVITIES)
            .where(key == late)
            .values(
                safety_checklist_version="1",
                checklist_result={"items": [{"item_id": "a"}]},
                confirmed_by="acct-1",
                confirmed_at=datetime.now(UTC),
            )
        )


def test_the_full_confirm_order_commits_in_one_transaction(build: Builder) -> None:
    """The order of the confirm command: checklist, supersede, approve, pointer, state."""
    occurrence_id = build.occurrence()
    first = build.plan(occurrence_id, 1)
    build.approve(first)
    second = build.plan(occurrence_id, 2)
    custom = build.activity(second, 1, "CUSTOM")
    now = datetime.now(UTC)
    with build.engine.begin() as conn:
        conn.execute(
            update(PLAN_ACTIVITIES)
            .where(PLAN_ACTIVITIES.c.plan_activity_id == custom)
            .values(
                safety_checklist_version="1",
                checklist_result={"items": []},
                confirmed_by="acct-1",
                confirmed_at=now,
            )
        )
        conn.execute(
            update(PLAN_REVISIONS)
            .where(PLAN_REVISIONS.c.plan_revision_id == first)
            .values(state="SUPERSEDED", superseded_at=now)
        )
        conn.execute(
            update(PLAN_REVISIONS)
            .where(PLAN_REVISIONS.c.plan_revision_id == second)
            .values(state="APPROVED", approved_by="acct-1", approved_at=now)
        )
        conn.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(approved_plan_revision_id=second, state="APPROVED", revision=2)
        )
    with build.engine.connect() as conn:
        row = conn.execute(
            text(
                "select state, revision, approved_plan_revision_id "
                "from lesson.occurrences where occurrence_id = :i"
            ),
            {"i": occurrence_id},
        ).one()
        states = conn.execute(
            text(
                "select revision_no, state from lesson.plan_revisions "
                "where occurrence_id = :i order by revision_no"
            ),
            {"i": occurrence_id},
        ).all()
    assert (row.state, row.revision, row.approved_plan_revision_id) == ("APPROVED", 2, second)
    assert [tuple(item) for item in states] == [(1, "SUPERSEDED"), (2, "APPROVED")]


def test_every_ddl_a_table_forbids_delete(build: Builder) -> None:
    occurrence_id = build.occurrence()
    document_id = build.document(occurrence_id)
    build.revision(document_id, 1)
    plan_id = build.plan(occurrence_id)
    build.activity(plan_id, 1, "LESSON")
    for table in (
        "occurrences",
        "source_documents",
        "document_revisions",
        "plan_revisions",
        "plan_activities",
    ):
        build.refuse(
            lambda c, t=table: c.execute(text(f"delete from lesson.{t}")), "_DELETE_FORBIDDEN"
        )


def test_occurrence_states_are_the_srs_names(build: Builder) -> None:
    """SRS §6.1.1 (l.396): the CHECK allows the whole set; the pointer is set from APPROVED on."""
    occurrence_id = build.occurrence()
    key = OCCURRENCES.c.occurrence_id
    with build.engine.begin() as conn:
        for state in ("DOCUMENT_REVIEW", "PLAN_REVIEW", "DRAFT", "ARCHIVED"):
            conn.execute(update(OCCURRENCES).where(key == occurrence_id).values(state=state))
    for state in ("PLANNING", "PLAN_APPROVED", "DONE"):
        build.refuse(
            set_values(OCCURRENCES, key, occurrence_id, state=state),
            "ck_occ_state",
            "ck_occ_plan_state",
        )
    for state in ("APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"):
        build.refuse(set_values(OCCURRENCES, key, occurrence_id, state=state), "ck_occ_plan_state")
    plan_id = build.plan(occurrence_id)
    build.approve(plan_id)
    fresh = build.occurrence()
    fresh_plan = build.plan(fresh)
    build.approve(fresh_plan)
    with build.engine.begin() as conn:
        for state in ("APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"):
            conn.execute(
                update(OCCURRENCES)
                .where(key == fresh)
                .values(approved_plan_revision_id=fresh_plan, state=state)
            )
    build.refuse(set_values(OCCURRENCES, key, fresh, state="PLAN_REVIEW"), "ck_occ_plan_state")
