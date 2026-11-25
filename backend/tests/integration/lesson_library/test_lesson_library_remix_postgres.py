"""PostgreSQL acceptance coverage for T-10b public lesson remixes.

The regular cases use the disposable BE1 acceptance database fixture from
``test_lesson_library_api``. Destination-owned remix rows are removed during teardown; the
append-only lineage trigger is disabled only for that scoped teardown. The occurrence pin test
uses a transaction-bound request session and rolls back its synthetic immutable occurrence.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, delete, event, func, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from test_lesson_library_api import (  # type: ignore[import-not-found]
    LessonApiAcceptance,
    _approve_public_grant,
    _create_lesson,
    _create_public_grant,
    _headers,
    _keyed,
)
from test_lesson_library_api import (
    lesson_api_acceptance as lesson_api_acceptance,
)

from alembic import command
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSION_LINEAGE,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.be1_runtime import get_db

_REMIX_SCOPE = "POST /lesson-library/remixes"
_LINEAGE_TRIGGER = "trg_lesson_version_lineage_append_only"
_BACKEND = Path(__file__).resolve().parents[3]
_MIGRATION_PARENT = "20261120_sel_0001"
_MIGRATION_HEAD = "20261121_pg_0001"
_LIVE_HEAD = "20261125_nt_0003"  # the lesson_library branch head since T-NTF1
_MIGRATION_REFUSAL = "DDL-D T-10b downgrade refused"


@pytest.fixture
def remix_destination(
    lesson_api_acceptance: LessonApiAcceptance,
) -> Iterator[dict[str, str]]:
    accepted = lesson_api_acceptance
    runtime = accepted.app.state.be1_runtime
    organization_id = f"synthetic-remix-destination-{uuid4()}"
    teacher = f"synthetic-remix-teacher-{uuid4()}"
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name="Synthetic Remix Destination",
                state="active",
            )
        )
        db.add(
            AdultIdentityModel(
                subject=teacher,
                issuer="synthetic-lesson-test-issuer",
                state="active",
                account_role="teacher",
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=teacher,
                class_id=None,
                role="teacher",
                active=True,
            )
        )
    try:
        yield {"organization_id": organization_id, "teacher": teacher}
    finally:
        engine = runtime.engine
        assert engine is not None
        with engine.begin() as connection:
            connection.exec_driver_sql(
                f"ALTER TABLE lesson.library_version_lineage DISABLE TRIGGER {_LINEAGE_TRIGGER}"
            )
            try:
                lesson_ids = select(LIBRARY_ITEMS.c.lesson_id).where(
                    LIBRARY_ITEMS.c.organization_id == organization_id
                )
                version_ids = select(LIBRARY_VERSIONS.c.version_id).where(
                    LIBRARY_VERSIONS.c.lesson_id.in_(lesson_ids)
                )
                connection.execute(
                    delete(LIBRARY_VERSION_LINEAGE).where(
                        LIBRARY_VERSION_LINEAGE.c.derived_version_id.in_(version_ids)
                    )
                )
                connection.execute(
                    delete(VERSION_ACTIVITIES).where(
                        VERSION_ACTIVITIES.c.version_id.in_(version_ids)
                    )
                )
                connection.execute(
                    delete(ACCESS_GRANTS).where(ACCESS_GRANTS.c.lesson_id.in_(lesson_ids))
                )
                connection.execute(
                    update(LIBRARY_ITEMS)
                    .where(LIBRARY_ITEMS.c.lesson_id.in_(lesson_ids))
                    .values(current_version_id=None)
                )
                connection.execute(
                    delete(LIBRARY_VERSIONS).where(LIBRARY_VERSIONS.c.lesson_id.in_(lesson_ids))
                )
                connection.execute(
                    delete(LIBRARY_ITEMS).where(LIBRARY_ITEMS.c.lesson_id.in_(lesson_ids))
                )
                connection.execute(
                    delete(Be1CommandReceiptModel).where(
                        Be1CommandReceiptModel.organization_id == organization_id,
                        Be1CommandReceiptModel.operation_scope == _REMIX_SCOPE,
                    )
                )
                connection.execute(
                    delete(CoreAuditEntryModel).where(
                        CoreAuditEntryModel.organization_id == organization_id,
                        CoreAuditEntryModel.action == "lesson.remix.create",
                    )
                )
                connection.execute(
                    delete(OrganizationAssignmentModel).where(
                        OrganizationAssignmentModel.organization_id == organization_id
                    )
                )
                connection.execute(
                    delete(OrganizationModel).where(
                        OrganizationModel.organization_id == organization_id
                    )
                )
                connection.execute(
                    delete(AdultIdentityModel).where(AdultIdentityModel.subject == teacher)
                )
            finally:
                connection.exec_driver_sql(
                    f"ALTER TABLE lesson.library_version_lineage ENABLE TRIGGER {_LINEAGE_TRIGGER}"
                )


def _create_reuse_source(
    accepted: LessonApiAcceptance, *, title: str = "Synthetic public remix source"
) -> dict[str, Any]:
    lesson = _create_lesson(accepted, title=title, visibility="PRIVATE")
    grant = _create_public_grant(accepted, lesson, capability="REUSE")
    _approve_public_grant(accepted, grant)
    current = lesson["current_version"]
    return {
        "lesson": lesson,
        "grant": grant,
        "version_id": current["version_id"],
        "content_sha256": current["structured_content_hash"],
    }


def _post_remix(
    accepted: LessonApiAcceptance,
    destination: dict[str, str],
    source: dict[str, Any],
    *,
    key: str | None = None,
    lesson_id: str | None = None,
    version_id: str | None = None,
    content_sha256: str | None = None,
) -> Any:
    return accepted.client.post(
        f"/api/lesson-library/v1/organizations/{destination['organization_id']}/lessons/"
        f"{lesson_id or source['lesson']['lesson_id']}/remixes",
        json={
            "contract": "RemixLessonRequestV1",
            "source_version_id": version_id or source["version_id"],
            "source_content_sha256": content_sha256 or source["content_sha256"],
        },
        headers=_headers(
            destination["teacher"],
            **{"Idempotency-Key": key or f"remix-{uuid4()}"},
        ),
    )


def _count_destination_items(accepted: LessonApiAcceptance, organization_id: str) -> int:
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        return int(
            db.scalar(
                select(func.count()).select_from(LIBRARY_ITEMS).where(
                    LIBRARY_ITEMS.c.organization_id == organization_id
                )
            )
            or 0
        )


def _count_destination_remix_receipts(
    accepted: LessonApiAcceptance, organization_id: str
) -> int:
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        return int(
            db.scalar(
                select(func.count()).select_from(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.organization_id == organization_id,
                    Be1CommandReceiptModel.operation_scope == _REMIX_SCOPE,
                )
            )
            or 0
        )


def test_remix_public_cross_org_creates_private_draft_and_lineage(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)

    response = _post_remix(accepted, remix_destination, source, key="remix-cross-org")

    assert response.status_code == 201, response.text
    assert response.headers["ETag"] == '"1"'
    assert response.headers["Cache-Control"] == "private, no-store"
    body = response.json()
    derived = body["lesson"]
    assert derived["organization_id"] == remix_destination["organization_id"]
    assert derived["visibility"] == "PRIVATE"
    assert derived["current_version"]["review_state"] == "DRAFT"
    assert derived["current_version"]["version_no"] == 1
    assert body["source"] == {
        "lesson_id": source["lesson"]["lesson_id"],
        "version_id": source["version_id"],
        "content_sha256": source["content_sha256"],
    }
    stale = _post_remix(
        accepted,
        remix_destination,
        source,
        key="remix-stale-source-pin",
        content_sha256="0" * 64,
    )
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "STALE_SOURCE_VERSION"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 1
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        lineage = db.execute(
            select(LIBRARY_VERSION_LINEAGE).where(
                LIBRARY_VERSION_LINEAGE.c.derived_version_id
                == derived["current_version"]["version_id"]
            )
        ).mappings().one()
        source_grant = db.execute(
            select(ACCESS_GRANTS).where(
                ACCESS_GRANTS.c.access_grant_id == source["grant"]["access_grant_id"]
            )
        ).mappings().one()
        copied_grants = db.scalar(
            select(func.count()).select_from(ACCESS_GRANTS).where(
                ACCESS_GRANTS.c.lesson_id == derived["lesson_id"]
            )
        )
        source_row = db.execute(
            select(LIBRARY_VERSIONS).where(
                LIBRARY_VERSIONS.c.version_id == source["version_id"]
            )
        ).mappings().one()
        derived_row = db.execute(
            select(LIBRARY_VERSIONS).where(
                LIBRARY_VERSIONS.c.version_id == derived["current_version"]["version_id"]
            )
        ).mappings().one()
        service = LessonLibraryService(
            db,
            storage=accepted.storage,
            parser=accepted.app.state.lesson_document_parser,
            scanner=accepted.app.state.lesson_document_scanner,
        )
        assert service._full_content(source_row) == service._full_content(derived_row)
        assert lineage["source_version_id"] == source["version_id"]
        assert lineage["source_content_hash"] == source["content_sha256"]
        assert source_grant["capability"] == "REUSE"
        assert copied_grants == 0


@pytest.mark.parametrize(
    "case",
    [
        "private",
        "hidden",
        "revoked",
        "expired",
        "unapproved",
        "view_only",
        "download_only",
        "unknown",
    ],
)
def test_remix_nonpublic_hidden_revoked_expired_unapproved_404(
    case: str,
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(
        accepted, title=f"Synthetic ineligible source {case}", visibility="PRIVATE"
    )
    source: dict[str, Any] = {
        "lesson": lesson,
        "version_id": lesson["current_version"]["version_id"],
        "content_sha256": lesson["current_version"]["structured_content_hash"],
    }
    if case not in {"private", "unknown"}:
        capability = {
            "view_only": "VIEW",
            "download_only": "DOWNLOAD",
        }.get(case, "REUSE")
        grant = _create_public_grant(accepted, lesson, capability=capability)
        source["grant"] = grant
        if case != "unapproved":
            _approve_public_grant(accepted, grant)
        if case == "hidden":
            hidden = accepted.client.patch(
                f"/api/lesson-library/v1/platform/lessons/{lesson['lesson_id']}/moderation",
                json={
                    "contract": "ModerateLessonRequestV1",
                    "state": "HIDDEN",
                    "reason": "Synthetic remix guard case",
                },
                headers=_keyed(accepted.platform_admin, 1, f"hide-remix-{uuid4()}"),
            )
            assert hidden.status_code == 200, hidden.text
        elif case == "revoked":
            revoked = accepted.client.delete(
                f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
                f"{lesson['lesson_id']}/access-grants/{grant['access_grant_id']}",
                headers=_keyed(accepted.teacher, 2, f"revoke-remix-{uuid4()}"),
            )
            assert revoked.status_code == 200, revoked.text
        elif case == "expired":
            with accepted.app.state.be1_runtime.session_factory.begin() as db:
                db.execute(
                    update(ACCESS_GRANTS)
                    .where(ACCESS_GRANTS.c.access_grant_id == grant["access_grant_id"])
                    .values(expires_at=text("clock_timestamp() - interval '1 minute'"))
                )

    response = _post_remix(
        accepted,
        remix_destination,
        source,
        key=f"remix-ineligible-{case}",
        lesson_id="lesson-does-not-exist" if case == "unknown" else None,
    )
    assert response.status_code == 404, response.text
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 0


def test_remix_source_version_belongs_to_lesson(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    requested = _create_reuse_source(accepted, title="Synthetic requested public source")
    other = _create_reuse_source(accepted, title="Synthetic foreign exact source")

    response = _post_remix(
        accepted,
        remix_destination,
        requested,
        key="remix-foreign-version",
        version_id=other["version_id"],
        content_sha256=other["content_sha256"],
    )

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_remix_concurrent_same_key_one_copy_and_same_response(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    key = "remix-concurrent-same-key"
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_post_remix, accepted, remix_destination, source, key=key)
            for _ in range(2)
        ]
        responses = [future.result(timeout=30) for future in futures]

    assert [response.status_code for response in responses] == [201, 201]
    assert responses[0].json() == responses[1].json()
    assert responses[0].headers["ETag"] == responses[1].headers["ETag"] == '"1"'
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 1
    assert _count_destination_remix_receipts(accepted, remix_destination["organization_id"]) == 1


def test_remix_concurrent_same_key_different_payload_conflicts(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    accepted = lesson_api_acceptance
    sources = [
        _create_reuse_source(accepted, title=f"Synthetic concurrent source {index}")
        for index in range(2)
    ]
    key = "remix-concurrent-different-payload"
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_post_remix, accepted, remix_destination, source, key=key)
            for source in sources
        ]
        responses = [future.result(timeout=30) for future in futures]

    assert sorted(response.status_code for response in responses) == [201, 400]
    refused = next(response for response in responses if response.status_code == 400)
    assert refused.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 1
    assert _count_destination_remix_receipts(accepted, remix_destination["organization_id"]) == 1


def test_remix_revocation_race_serializes_guard(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    key = "remix-revoke-race"
    guard_complete = threading.Event()
    allow_remix_commit = threading.Event()
    revoke_started = threading.Event()
    revoke_lock_attempted = threading.Event()
    item_lock_count = 0
    item_lock_count_lock = threading.Lock()
    original_find_receipt = LessonLibraryService._find_remix_receipt

    def pause_after_guard(service: LessonLibraryService, actor: str, idempotency_key: str):
        if idempotency_key == key:
            guard_complete.set()
            if not allow_remix_commit.wait(timeout=15):
                raise AssertionError("revocation race did not release the remix transaction")
        return original_find_receipt(service, actor, idempotency_key)

    monkeypatch.setattr(LessonLibraryService, "_find_remix_receipt", pause_after_guard)
    engine = accepted.app.state.be1_runtime.engine
    assert engine is not None

    def observe_item_lock(connection, cursor, statement, parameters, context, executemany) -> None:
        nonlocal item_lock_count
        normalized = statement.lower()
        if (
            "library_items" in normalized
            and "for update" in normalized
            and source["lesson"]["lesson_id"] in str(parameters)
        ):
            with item_lock_count_lock:
                item_lock_count += 1
                if item_lock_count >= 2:
                    revoke_lock_attempted.set()

    event.listen(engine, "before_cursor_execute", observe_item_lock)
    revoke_path = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{source['lesson']['lesson_id']}/access-grants/{source['grant']['access_grant_id']}"
    )

    def revoke():
        revoke_started.set()
        return accepted.client.delete(
            revoke_path,
            headers=_keyed(accepted.teacher, 2, "revoke-during-remix-race"),
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            remix_future = pool.submit(
                _post_remix, accepted, remix_destination, source, key=key
            )
            assert guard_complete.wait(timeout=10)
            revoke_future = pool.submit(revoke)
            assert revoke_started.wait(timeout=5)
            assert revoke_lock_attempted.wait(timeout=10)
            allow_remix_commit.set()
            remix_response = remix_future.result(timeout=30)
            revoke_response = revoke_future.result(timeout=30)
    finally:
        allow_remix_commit.set()
        event.remove(engine, "before_cursor_execute", observe_item_lock)

    assert remix_response.status_code == 201, remix_response.text
    assert revoke_response.status_code == 200, revoke_response.text
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        grant = db.execute(
            select(ACCESS_GRANTS).where(
                ACCESS_GRANTS.c.access_grant_id == source["grant"]["access_grant_id"]
            )
        ).mappings().one()
        assert grant["state"] == "REVOKED"


def test_remix_replay_after_revocation_is_404(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    key = "remix-replay-after-revoke"
    first = _post_remix(accepted, remix_destination, source, key=key)
    assert first.status_code == 201, first.text
    revoked = accepted.client.delete(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{source['lesson']['lesson_id']}/access-grants/{source['grant']['access_grant_id']}",
        headers=_keyed(accepted.teacher, 2, f"revoke-after-remix-{uuid4()}"),
    )
    assert revoked.status_code == 200, revoked.text

    replay = _post_remix(accepted, remix_destination, source, key=key)

    assert replay.status_code == 404, replay.text
    assert replay.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 1


def test_remix_assignment_revoke_before_replay_404(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    key = "remix-replay-after-assignment-revoke"
    first = _post_remix(accepted, remix_destination, source, key=key)
    assert first.status_code == 201, first.text
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id
                == remix_destination["organization_id"],
                OrganizationAssignmentModel.subject == remix_destination["teacher"],
            )
            .values(active=False)
        )

    replay = _post_remix(accepted, remix_destination, source, key=key)

    assert replay.status_code == 404, replay.text
    assert replay.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 1


def test_remix_real_receipt_primary_key_race_returns_400_and_rolls_back(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    from sqlalchemy import insert

    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    engine = accepted.app.state.be1_runtime.engine
    assert engine is not None
    key = "remix-real-receipt-pk-race"
    injected = {"done": False}

    def race_receipt(connection, cursor, statement, parameters, context, executemany) -> None:
        normalized = statement.lower()
        if (
            injected["done"]
            or "insert into" not in normalized
            or "be1_command_receipts" not in normalized
        ):
            return
        injected["done"] = True
        with engine.begin() as other:
            other.execute(
                insert(Be1CommandReceiptModel).values(
                    principal_ref=remix_destination["teacher"],
                    operation_scope=_REMIX_SCOPE,
                    idempotency_key=key,
                    organization_id=remix_destination["organization_id"],
                    request_fingerprint="f" * 64,
                    response_json={"contract": "RemixLessonResponseV1"},
                )
            )

    event.listen(engine, "before_cursor_execute", race_receipt)
    try:
        response = _post_remix(accepted, remix_destination, source, key=key)
    finally:
        event.remove(engine, "before_cursor_execute", race_receipt)

    assert injected["done"]
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 0
    assert _count_destination_remix_receipts(accepted, remix_destination["organization_id"]) == 1


@pytest.mark.parametrize("failure_target", ["lineage", "receipt"])
def test_remix_atomic_rollback_on_receipt_or_lineage_failure(
    failure_target: str,
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    engine = accepted.app.state.be1_runtime.engine
    assert engine is not None

    def reject_target(connection, cursor, statement, parameters, context, executemany) -> None:
        normalized = statement.lower()
        is_insert = "insert into" in normalized
        matches_lineage = "library_version_lineage" in normalized
        matches_receipt = "be1_command_receipts" in normalized
        if is_insert and (
            (failure_target == "lineage" and matches_lineage)
            or (failure_target == "receipt" and matches_receipt)
        ):
            raise IntegrityError(statement, parameters, RuntimeError("synthetic atomicity failure"))

    event.listen(engine, "before_cursor_execute", reject_target)
    try:
        response = _post_remix(
            accepted,
            remix_destination,
            source,
            key=f"remix-atomic-{failure_target}",
        )
    finally:
        event.remove(engine, "before_cursor_execute", reject_target)

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "RESOURCE_CONFLICT"
    assert _count_destination_items(accepted, remix_destination["organization_id"]) == 0
    assert _count_destination_remix_receipts(accepted, remix_destination["organization_id"]) == 0
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        assert db.scalar(
            select(func.count())
            .select_from(
                LIBRARY_VERSION_LINEAGE.join(
                    LIBRARY_VERSIONS,
                    LIBRARY_VERSIONS.c.version_id
                    == LIBRARY_VERSION_LINEAGE.c.derived_version_id,
                ).join(
                    LIBRARY_ITEMS,
                    LIBRARY_ITEMS.c.lesson_id == LIBRARY_VERSIONS.c.lesson_id,
                )
            )
            .where(LIBRARY_ITEMS.c.organization_id == remix_destination["organization_id"])
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(CoreAuditEntryModel).where(
                CoreAuditEntryModel.organization_id == remix_destination["organization_id"],
                CoreAuditEntryModel.action == "lesson.remix.create",
            )
        ) == 0


def test_remix_old_occurrence_and_source_unchanged(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    runtime = accepted.app.state.be1_runtime
    assert runtime.engine is not None
    connection = runtime.engine.connect()
    transaction = connection.begin()
    original_overrides = dict(accepted.app.dependency_overrides)

    def transaction_bound_db() -> Iterator[Session]:
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            yield db

    accepted.app.dependency_overrides[get_db] = transaction_bound_db
    occurrence_id = str(uuid4())
    version = source["lesson"]["current_version"]
    try:
        connection.execute(
            OCCURRENCES.insert().values(
                occurrence_id=occurrence_id,
                organization_ref=accepted.organization_id,
                class_ref="synthetic-remix-class",
                responsible_teacher_ref=str(uuid4()),
                created_by=str(uuid4()),
                title="Synthetic immutable source pin",
                source_lesson_id=source["lesson"]["lesson_id"],
                source_lesson_version_id=source["version_id"],
                source_lesson_version_no=version["version_no"],
                source_lesson_version_hash=source["content_sha256"],
            )
        )
        before_pin = connection.execute(
            select(
                OCCURRENCES.c.source_lesson_id,
                OCCURRENCES.c.source_lesson_version_id,
                OCCURRENCES.c.source_lesson_version_no,
                OCCURRENCES.c.source_lesson_version_hash,
            ).where(OCCURRENCES.c.occurrence_id == occurrence_id)
        ).one()
        source_before = connection.execute(
            select(
                LIBRARY_VERSIONS.c.content_json,
                LIBRARY_VERSIONS.c.structured_content_hash,
                LIBRARY_VERSIONS.c.review_state,
            ).where(LIBRARY_VERSIONS.c.version_id == source["version_id"])
        ).one()

        response = _post_remix(
            accepted, remix_destination, source, key="remix-old-occurrence-pin"
        )

        assert response.status_code == 201, response.text
        after_pin = connection.execute(
            select(
                OCCURRENCES.c.source_lesson_id,
                OCCURRENCES.c.source_lesson_version_id,
                OCCURRENCES.c.source_lesson_version_no,
                OCCURRENCES.c.source_lesson_version_hash,
            ).where(OCCURRENCES.c.occurrence_id == occurrence_id)
        ).one()
        source_after = connection.execute(
            select(
                LIBRARY_VERSIONS.c.content_json,
                LIBRARY_VERSIONS.c.structured_content_hash,
                LIBRARY_VERSIONS.c.review_state,
            ).where(LIBRARY_VERSIONS.c.version_id == source["version_id"])
        ).one()
        assert tuple(after_pin) == tuple(before_pin)
        assert tuple(source_after) == tuple(source_before)
    finally:
        accepted.app.dependency_overrides.clear()
        accepted.app.dependency_overrides.update(original_overrides)
        transaction.rollback()
        connection.close()


def test_remix_lineage_fk_immutable_and_cycle_rejected(
    lesson_api_acceptance: LessonApiAcceptance,
    remix_destination: dict[str, str],
) -> None:
    accepted = lesson_api_acceptance
    source = _create_reuse_source(accepted)
    response = _post_remix(accepted, remix_destination, source, key="remix-lineage-guard")
    assert response.status_code == 201, response.text
    derived_version_id = response.json()["lesson"]["current_version"]["version_id"]
    source_version_id = source["version_id"]
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        def expect_integrity(statement) -> None:
            with pytest.raises((IntegrityError, DBAPIError)), db.begin_nested():
                db.execute(statement)

        expect_integrity(
            LIBRARY_VERSION_LINEAGE.update()
            .where(LIBRARY_VERSION_LINEAGE.c.derived_version_id == derived_version_id)
            .values(source_version_id=str(uuid4()))
        )
        expect_integrity(
            LIBRARY_VERSION_LINEAGE.delete().where(
                LIBRARY_VERSION_LINEAGE.c.derived_version_id == derived_version_id
            )
        )
        expect_integrity(
            LIBRARY_VERSION_LINEAGE.insert().values(
                derived_version_id=str(uuid4()),
                source_version_id=source_version_id,
                source_content_hash=source["content_sha256"],
            )
        )
        expect_integrity(
            LIBRARY_VERSION_LINEAGE.insert().values(
                derived_version_id=derived_version_id,
                source_version_id=str(uuid4()),
                source_content_hash=source["content_sha256"],
            )
        )
        expect_integrity(
            LIBRARY_VERSION_LINEAGE.insert().values(
                derived_version_id=source_version_id,
                source_version_id=derived_version_id,
                source_content_hash=source["content_sha256"],
            )
        )
        assert db.execute(
            select(LIBRARY_VERSION_LINEAGE.c.source_version_id).where(
                LIBRARY_VERSION_LINEAGE.c.derived_version_id == derived_version_id
            )
        ).scalar_one() == source_version_id


@pytest.fixture
def remix_migration_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("LESSON_LIBRARY_MIGRATION_TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "set LESSON_LIBRARY_MIGRATION_TEST_DATABASE_URL to a disposable migration database"
        )
    database_name = url.rsplit("/", 1)[-1]
    if not all(part in database_name for part in ("lesson_library_migration", "roundtrip")):
        pytest.fail(
            "LESSON_LIBRARY_MIGRATION_TEST_DATABASE_URL must name a dedicated "
            "lesson_library_migration*roundtrip* database"
        )
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(_BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        try:
            command.upgrade(config, "heads")
        finally:
            engine.dispose()
            get_settings.cache_clear()
            get_core_database_settings.cache_clear()


def _migration_versions(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0]
            for row in connection.execute(text("select version_num from alembic_version"))
        }


def test_remix_migration_empty_downgrade_and_nonempty_refusal(
    remix_migration_roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = remix_migration_roundtrip
    assert _LIVE_HEAD in _migration_versions(engine)
    with engine.connect() as connection:
        assert connection.execute(
            text("select count(*) from lesson.library_version_lineage")
        ).scalar_one() == 0
        database_columns = set(
            connection.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema = 'lesson' and table_name = 'library_version_lineage'"
                )
            ).scalars()
        )
        database_constraints = set(
            connection.execute(
                text(
                    "select conname from pg_constraint "
                    "where conrelid = 'lesson.library_version_lineage'::regclass"
                )
            ).scalars()
        )
        database_indexes = set(
            connection.execute(
                text(
                    "select indexname from pg_indexes "
                    "where schemaname = 'lesson' and tablename = 'library_version_lineage'"
                )
            ).scalars()
        )
    assert database_columns == set(LIBRARY_VERSION_LINEAGE.c.keys())
    metadata_constraints = {constraint.name for constraint in LIBRARY_VERSION_LINEAGE.constraints}
    assert metadata_constraints <= database_constraints
    assert {index.name for index in LIBRARY_VERSION_LINEAGE.indexes} <= database_indexes

    command.downgrade(config, _MIGRATION_PARENT)
    assert _MIGRATION_HEAD not in _migration_versions(engine)
    command.upgrade(config, _MIGRATION_HEAD)
    assert _MIGRATION_HEAD in _migration_versions(engine)
    lesson_id = str(uuid4())
    source_version_id, derived_version_id = str(uuid4()), str(uuid4())
    try:
        with engine.begin() as connection:
            for item_id in (lesson_id,):
                connection.execute(
                    text(
                        "insert into lesson.library_items "
                        "(lesson_id, organization_id, owner_kind, created_by, state, visibility, "
                        "internal_visibility, moderation_state, revision, created_at, updated_at) "
                        "values (:id, 'synthetic-migration-org', 'ORGANIZATION', "
                        "'synthetic-teacher', "
                        "'ACTIVE', 'PRIVATE', 'PRIVATE', 'VISIBLE', 1, now(), now())"
                    ),
                    {"id": item_id},
                )
            for version_id, version_no in ((source_version_id, 1), (derived_version_id, 2)):
                connection.execute(
                    text(
                        "insert into lesson.library_versions "
                        "(version_id, lesson_id, version_no, content_json, "
                        "structured_content_hash, "
                        "review_state, authored_by, created_at) values "
                        "(:version, :lesson, :number, '{}'::jsonb, :hash, 'DRAFT', "
                        "'synthetic-teacher', now())"
                    ),
                    {
                        "version": version_id,
                        "lesson": lesson_id,
                        "number": version_no,
                        "hash": "a" * 64,
                    },
                )
            connection.execute(
                text(
                    "insert into lesson.library_version_lineage "
                    "(derived_version_id, source_version_id, source_content_hash, created_at) "
                    "values (:derived, :source, :hash, now())"
                ),
                {
                    "derived": derived_version_id,
                    "source": source_version_id,
                    "hash": "a" * 64,
                },
            )

        with pytest.raises(DBAPIError, match=_MIGRATION_REFUSAL):
            command.downgrade(config, _MIGRATION_PARENT)
        assert _MIGRATION_HEAD in _migration_versions(engine)
        with engine.connect() as connection:
            assert connection.execute(
                text(
                    "select count(*) from lesson.library_version_lineage "
                    "where derived_version_id = :derived"
                ),
                {"derived": derived_version_id},
            ).scalar_one() == 1
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                f"ALTER TABLE lesson.library_version_lineage DISABLE TRIGGER {_LINEAGE_TRIGGER}"
            )
            try:
                connection.execute(
                    text(
                        "delete from lesson.library_version_lineage "
                        "where derived_version_id = :derived"
                    ),
                    {"derived": derived_version_id},
                )
                connection.execute(
                    text(
                        "update lesson.library_items set current_version_id = null "
                        "where lesson_id = :lesson"
                    ),
                    {"lesson": lesson_id},
                )
                connection.execute(
                    text("delete from lesson.library_versions where lesson_id = :lesson"),
                    {"lesson": lesson_id},
                )
                connection.execute(
                    text("delete from lesson.library_items where lesson_id = :lesson"),
                    {"lesson": lesson_id},
                )
            finally:
                connection.exec_driver_sql(
                    f"ALTER TABLE lesson.library_version_lineage ENABLE TRIGGER {_LINEAGE_TRIGGER}"
                )
