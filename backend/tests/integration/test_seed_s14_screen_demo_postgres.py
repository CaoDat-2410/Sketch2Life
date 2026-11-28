"""Opt-in PostgreSQL acceptance checks for the S14 web-screen seed."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import TypedDict

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.learning_content.tables import VERSION
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_VERSIONS
from sketch2life.infrastructure.persistence.be1_models import ConsentRecordModel
from sketch2life.infrastructure.persistence.platform_models import (
    AdminCommandReceiptModel,
    InboxItemModel,
)
from tools.seed import data, s13_system_demo, s14_screen_demo_data
from tools.seed import s14_screen_demo as stage
from tools.seed.guard import SEED_URL_VARIABLE
from tools.seed.s1_core import run_s1
from tools.seed.s7a_runs import run_s7a
from tools.seed.s7b_story_states import run_s7b
from tools.seed.s8_lessons import run_s8
from tools.seed.s12_story_v4a import run_s12
from tools.seed.stage_common import open_guarded_engine

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)


class SeededRows(TypedDict):
    first_ok: bool
    second_ok: bool
    before_second: dict[str, int]
    totals: dict[str, int]


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
    engine = open_guarded_engine()
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def seeded(seed_engine: Engine) -> SeededRows:
    # The S13 acceptance setup's prerequisite sequence is retained; S14 runs immediately after S13.
    run_s1(seed_engine)
    run_s7a(seed_engine)
    run_s8(seed_engine)
    run_s7b(seed_engine)
    run_s12(seed_engine)
    s13_system_demo.run_s13(seed_engine)
    first = stage.run_s14(seed_engine)
    with seed_engine.connect() as connection:
        before_second = stage.count_s14_rows(connection)
    second = stage.run_s14(seed_engine)
    with seed_engine.connect() as connection:
        totals = stage.count_s14_rows(connection)
    return {
        "first_ok": first.ok,
        "second_ok": second.ok,
        "before_second": before_second,
        "totals": totals,
    }


def test_s14_twice_adds_no_duplicate_rows_and_matches_expected(seeded: SeededRows) -> None:
    assert seeded["first_ok"]
    assert seeded["second_ok"]
    assert seeded["before_second"] == stage.EXPECTED
    assert seeded["totals"] == stage.EXPECTED


def test_demo_rows_remain_pending_or_submitted_for_review(
    seed_engine: Engine, seeded: SeededRows
) -> None:
    del seeded
    with Session(seed_engine) as session:
        consent = session.scalar(
            select(ConsentRecordModel).where(
                ConsentRecordModel.organization_id
                == s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
                ConsentRecordModel.class_id == s14_screen_demo_data.CONSENT_CLASS_ID,
                ConsentRecordModel.child_id == stage.CONSENT_CHILD_ID,
                ConsentRecordModel.purpose_ref == s14_screen_demo_data.CONSENT_PURPOSE_REF,
            )
        )
        assert consent is not None
        assert consent.state == "pending"
        assert consent.evidence_ref is None

        catalog_receipt = session.get(
            AdminCommandReceiptModel,
            (data.PLATFORM_ADMIN_SUBJECT, "catalog.write:new", stage.CREATE_KEY),
        )
        assert catalog_receipt is not None
        catalog_record_id = str(catalog_receipt.response_json["record_id"])
        assert session.scalar(
            select(VERSION.c.state).where(
                VERSION.c.organization_id == "platform",
                VERSION.c.record_id == catalog_record_id,
                VERSION.c.version == 1,
            )
        ) == "submitted"

        lesson_receipt = session.get(
            AdminCommandReceiptModel,
            (data.PLATFORM_ADMIN_SUBJECT, "lesson.write:new", stage.LESSON_CREATE_KEY),
        )
        assert lesson_receipt is not None
        lesson_version_id = str(lesson_receipt.response_json["version_id"])
        assert session.scalar(
            select(LIBRARY_VERSIONS.c.review_state).where(
                LIBRARY_VERSIONS.c.version_id == lesson_version_id
            )
        ) == "PENDING_REVIEW"

        notice = session.scalar(
            select(InboxItemModel).where(
                InboxItemModel.recipient_ref == data.PLATFORM_ADMIN_SUBJECT,
                InboxItemModel.kind == s14_screen_demo_data.NOTIFICATION_KIND,
                InboxItemModel.resource_ref == s14_screen_demo_data.NOTIFICATION_RESOURCE,
            )
        )
        assert notice is not None
        assert notice.is_read is False
