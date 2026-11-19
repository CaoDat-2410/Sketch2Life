"""Owner-run S1 seed check against the seed database (FEAT-066 SEED-1, package §4 test 7).

Skipped unless ``S2L_SEED_DATABASE_URL`` is set. The guard runs first, so this test can
only touch a loopback database whose name contains ``seed`` on a port other than 5432 or
5433. It writes S1 twice, compares the counts, checks visibility parity and rolls that
back, then reads every seeded run back as its Parent through the product repository.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import fields
from typing import Any, cast

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import LessonDocumentParser, MalwareScanner
from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunResponseV1
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_ITEMS
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s1_core import count_rows, run_s1

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
    from sketch2life.infrastructure.config.settings import (
        get_core_database_settings,
        get_settings,
    )

    previous = os.environ.get("SKETCH2LIFE_DATABASE_URL")
    try:
        engine, _target = guarded_engine()
        try:
            yield engine
        finally:
            engine.dispose()
    finally:
        # The guard points this process at the seed database; undo that for later tests.
        if previous is None:
            os.environ.pop("SKETCH2LIFE_DATABASE_URL", None)
        else:
            os.environ["SKETCH2LIFE_DATABASE_URL"] = previous
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(scope="module")
def seeded(seed_engine: Engine) -> dict[str, dict[str, int]]:
    first = run_s1(seed_engine)
    second = run_s1(seed_engine)
    with seed_engine.connect() as connection:
        totals = count_rows(connection)
    return {"first": first, "second": second, "totals": totals}


def test_second_run_adds_nothing_and_counts_match(seeded: dict[str, dict[str, int]]) -> None:
    assert all(value == 0 for value in seeded["second"].values()), seeded["second"]
    assert seeded["totals"] == data.EXPECTED_COUNTS
    # The first run either seeded a fresh database or found every row already present.
    for name, value in seeded["first"].items():
        assert value in {0, data.EXPECTED_COUNTS[name]}, name


def test_visibility_parity_with_product_rule(
    seed_engine: Engine, seeded: dict[str, dict[str, int]]
) -> None:
    session = Session(seed_engine)
    try:
        service = LessonLibraryService(
            session,
            storage=cast(ObjectStoragePort, object()),
            parser=cast(LessonDocumentParser, object()),
            scanner=cast(MalwareScanner, object()),
        )
        for key, expected in data.EXPECTED_VISIBILITY.items():
            lesson_id = data.lesson_id(key)
            before = session.scalar(
                select(LIBRARY_ITEMS.c.visibility).where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
            )
            service._recalculate_visibility(lesson_id)
            after = session.scalar(
                select(LIBRARY_ITEMS.c.visibility).where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
            )
            assert before == expected == after, key
    finally:
        # The product method also rewrites updated_at; nothing from this check is kept.
        session.rollback()
        session.close()


def _response(record: Any) -> ParentStoryRunResponseV1:
    values = {field.name: getattr(record, field.name) for field in fields(record)}
    values["story"] = values.pop("story_content")
    return ParentStoryRunResponseV1.model_validate(values)


@pytest.mark.parametrize("spec", data.STORY_RUN_SPECS, ids=lambda spec: spec[0])
def test_runs_read_back_through_the_product(
    seed_engine: Engine, seeded: dict[str, dict[str, int]], spec: tuple[Any, ...]
) -> None:
    key, parent_key, profile_key, state, _active, topic, idea = spec
    principal = VerifiedPrincipal(
        subject=data.PARENT_SUBJECTS[parent_key],
        issuer=data.SEED_ISSUER,
        roles=frozenset({"parent"}),
    )
    session = Session(seed_engine)
    try:
        record = SqlParentStoryRunRepository(session).get_run(
            principal=principal, run_id=data.run_id(key)
        )
        response = _response(record)
    finally:
        session.rollback()
        session.close()
    assert response.run_state == state
    assert str(response.parent_profile_id) == str(data.parent_profile_id(profile_key))
    assert response.current_input_revision == 1
    assert response.context_snapshot.topic == topic
    assert response.context_snapshot.adult_confirmed_idea == (idea or "")
    assert response.lesson_pin_snapshot is None
