"""FEAT-066 goal v4 T-12a: the Parent context entries and their selection, on PostgreSQL.

SRS l.263-265 (BR-19 to BR-21), l.497-499 (FR-C-05 to FR-C-07), l.2349 (FR-P-06), l.864-865 (one 404
for a caller out of scope), l.1697-1699 (replay). Runs only against a disposable database whose
name contains ``be1_acceptance`` and ``frc08_v4_t12a``. The migration round trip needs
``T12A_ROUNDTRIP_DATABASE_URL`` naming a ``frc08_v4_t12a*roundtrip*be1_acceptance`` database.

Profiles are made through the real repository, entries through the real routes, and the runs are
seeded straight into the Story tables (a drawing, an understanding, a v1 context built like
``create_run`` does for the real profile) because the upload and analysis steps have their own
PostgreSQL tests. The Lesson Library catalog and the story generator are doubles; the Story side is
the real repository, so the run lock, the receipts, the new input row and the story start are the
production code. No object storage and no provider is used.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.domain.parent_profile_context import (
    PARENT_CONTEXT_V1_SCHEMA,
    PARENT_CONTEXT_V2_SCHEMA,
    SNAPSHOT_MAX_BYTES,
    SelectedContextEntry,
    build_selected_context_snapshot,
    jsonb_text_size,
)
from sketch2life.domain.parent_profiles import ProfileSnapshot
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentCommandReceiptModel,
    ParentProfileContextEntryModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _principal_scope_ref,
    _sha256_json,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import SqlStoryLifecycleStore
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.parent_runtime import get_parent_principal
from sketch2life.interfaces.http.routers import parent_story_activities as activity_routes
from sketch2life.interfaces.http.routers import parent_story_runs as story_routes
from tests.integration.test_parent_activity_selection_postgres import (
    AccessSpy,
    ActivityApi,
    Catalog,
    RecordingGenerator,
    first_ref,
    lesson,
    revision_of,
    run_row,
    select_activity,
    sha,
    story_rows,
)

ISSUER = "synthetic-t12a-issuer"
TYPED = "A friendly dragon learns to share"
SUBJECT = "dragon"
BACKEND = Path(__file__).resolve().parents[2]
EMOJI = "\U0001f600"


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[ActivityApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v4_t12a" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v4_t12a*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    catalog, generator, spy = Catalog(), RecordingGenerator(), AccessSpy()
    monkeypatch.setattr(
        activity_routes,
        "_selection_service",
        lambda _request, db: ParentActivitySelectionService(
            SqlParentStoryRunRepository(db), catalog
        ),
    )
    monkeypatch.setattr(story_routes, "get_lesson_library_service", spy)
    application.state.story_generator = generator
    token = uuid4().hex[:8]
    parent, other_parent = f"synthetic-t12a-parent-{token}", f"synthetic-t12a-parent2-{token}"
    teacher = f"synthetic-t12a-teacher-{token}"
    with runtime.session_factory.begin() as db:
        for subject, role in ((parent, "parent"), (other_parent, "parent"), (teacher, "teacher")):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=role
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_parent_principal] = verified
    try:
        with TestClient(application) as client:
            yield ActivityApi(
                application, client, catalog, generator, spy, parent, other_parent, teacher
            )
    finally:
        application.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def principal_of(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def headers(subject: str, key: str | None = None) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def make_profile(api: ActivityApi, owner: str) -> str:
    with api.sessions()() as db:
        result = SqlParentProfileRepository(db).create_profile(
            principal=principal_of(owner),
            snapshot=ProfileSnapshot("Mina", 60, "thich ve ca"),
            idempotency_key=uuid4().hex,
            request_id="t12a",
        )
    return str(result.body["profile_id"])


def entry_body(text_value: str = "thich cho ca an", **changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "entry_kind": "OBSERVATION",
        "short_text": text_value,
        "source_kind": "PARENT_NOTE",
    }
    body.update(changes)
    return body


def add_entry(
    api: ActivityApi,
    owner: str,
    profile_id: str,
    text_value: str = "thich cho ca an",
    *,
    key: str | None = None,
    **changes: Any,
) -> Any:
    return api.client.post(
        f"/v1/parent/profiles/{profile_id}/context-entries",
        json=entry_body(text_value, **changes),
        headers=headers(owner, key or uuid4().hex),
    )


def entry_id_of(response: Any) -> str:
    assert response.status_code == 201, response.text
    return str(response.json()["context_entry"]["context_entry_id"])


def list_entries(api: ActivityApi, owner: str, profile_id: str, query: str = "") -> Any:
    return api.client.get(
        f"/v1/parent/profiles/{profile_id}/context-entries{query}", headers=headers(owner)
    )


def entry_rows(api: ActivityApi, profile_id: str) -> list[ParentProfileContextEntryModel]:
    with api.sessions()() as db:
        return list(
            db.scalars(
                select(ParentProfileContextEntryModel)
                .where(ParentProfileContextEntryModel.parent_profile_id == UUID(profile_id))
                .order_by(
                    ParentProfileContextEntryModel.created_at,
                    ParentProfileContextEntryModel.context_entry_id,
                )
            )
        )


def seed_run(
    api: ActivityApi,
    owner: str,
    profile_id: str,
    context_overrides: dict[str, Any] | None = None,
) -> str:
    """A run in ``SUBJECT_REVIEW`` for the real profile: one drawing, understanding 1, a v1
    context built like ``create_run`` builds it, not yet confirmed."""

    run_id, now = str(uuid4()), datetime.now(UTC)
    scope_ref = parent_scope_ref(principal_of(owner))
    token = uuid4().hex
    input_one, input_two = str(uuid4()), str(uuid4())
    with api.sessions().begin() as db:
        revision_ref = db.scalar(
            select(ParentProfileRevisionModel.profile_revision_id).where(
                ParentProfileRevisionModel.parent_profile_id == UUID(profile_id)
            )
        )
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == owner)
        )
        context = {
            "schema_version": PARENT_CONTEXT_V1_SCHEMA,
            "profile_revision_ref": str(revision_ref),
            "age_months": 60,
            "interests_summary": "thich ve ca",
            "topic": "dragon wings",
            "adult_confirmed_idea": TYPED,
            **(context_overrides or {}),
        }
        db.execute(
            story_tables.story_runs.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=scope_ref,
                profile_ref=profile_id,
                run_state="SUBJECT_REVIEW",
                job_state="SUCCEEDED",
                revision=5,
                version=5,
                current_input_revision=2,
                understanding_revision=1,
                subject_label=SUBJECT,
                confidence=0.9,
                active_owner_parent_account_id=str(account_id),
                created_at=now,
                updated_at=now,
            )
        )
        common = {
            "run_id": run_id,
            "typed_idea": TYPED,
            "idea_source": "TEXT",
            "source_profile_revision_ref": str(revision_ref),
            "context_revision": 1,
            "context_snapshot": context,
            "context_snapshot_sha256": _sha256_json(context),
            "context_confirmed_by": None,
            "context_confirmed_at": None,
            "created_at": now,
        }
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=input_one, input_revision=1, **common
            )
        )
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=input_two,
                input_revision=2,
                original_asset_ref=f"parent/{run_id}/{token}/original",
                original_asset_version=1,
                original_sha256=sha(f"original-{run_id}".encode()),
                original_media_type="image/png",
                original_size_bytes=100,
                derived_asset_ref=f"parent/{run_id}/{token}/normalized.png",
                derived_asset_version=1,
                derived_sha256=sha(f"derived-{run_id}".encode()),
                derived_media_type="image/png",
                derived_size_bytes=90,
                **common,
            )
        )
        db.execute(
            story_tables.understanding_revisions.insert().values(
                understanding_revision_id=str(uuid4()),
                run_id=run_id,
                run_input_id=input_two,
                revision_no=1,
                subject_label=SUBJECT,
                confidence=0.9,
                canonical_result_sha256="d" * 64,
                result_snapshot={
                    "result": {
                        "candidate_subject": SUBJECT,
                        "visible_features": ["wings", "tail"],
                        "confidence": 0.9,
                        "adult_confirmation_required": True,
                        "decision": "REVIEW_REQUIRED",
                    }
                },
                created_at=now,
            )
        )
    return run_id


def ready_run(
    api: ActivityApi,
    owner: str,
    profile_id: str,
    context_overrides: dict[str, Any] | None = None,
) -> str:
    """``PREPARATION_REVIEW`` with the subject confirmed and a main activity chosen; only the
    context confirmation is missing."""

    api.catalog.lessons = [lesson("a", "Find dragon wings")]
    run_id = seed_run(api, owner, profile_id, context_overrides)
    response = api.client.post(
        f"/v1/story-runs/{run_id}/subject-confirmation",
        json={"expected_understanding_revision": 1, "confirmed_subject": SUBJECT},
        headers=headers(owner, uuid4().hex),
    )
    assert response.status_code == 202, response.text
    chosen = select_activity(api, owner, run_id, first_ref(api, owner, run_id))
    assert chosen.status_code == 200, chosen.text
    assert story_rows(api, run_id) == []  # the context is not confirmed: no story yet
    return run_id


def input_rows(api: ActivityApi, run_id: str) -> list[Any]:
    table = story_tables.run_inputs
    with api.sessions()() as db:
        return list(
            db.execute(
                select(table).where(table.c.run_id == run_id).order_by(table.c.input_revision)
            )
            .mappings()
            .all()
        )


def context_receipts(api: ActivityApi, run_id: str) -> list[Any]:
    table = story_tables.story_command_receipts
    with api.sessions()() as db:
        return list(
            db.execute(
                select(table).where(
                    table.c.resource_ref == run_id, table.c.operation == "CONFIRM_CONTEXT"
                )
            )
            .mappings()
            .all()
        )


def confirm(
    api: ActivityApi,
    owner: str,
    run_id: str,
    ids: list[str] | None | str = "absent",
    *,
    key: str | None = None,
    revision: int = 1,
    context_hash: str | None = None,
) -> Any:
    current = input_rows(api, run_id)[-1]
    body: dict[str, Any] = {
        "expected_context_revision": revision,
        "context_snapshot_sha256": context_hash or current["context_snapshot_sha256"],
        "confirmed": True,
    }
    if ids != "absent":
        body["selected_context_entry_ids"] = ids
    return api.client.post(
        f"/v1/story-runs/{run_id}/context-confirmation",
        json=body,
        headers=headers(owner, key or uuid4().hex),
    )


def code_of(response: Any) -> str:
    return str(response.json()["code"])


# ============================================================================= the entries
def test_context_entry_page_order_and_cursor_are_stable(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    created = [entry_id_of(add_entry(api, api.parent, profile, f"entry {n}")) for n in range(5)]
    assert [row.short_text for row in entry_rows(api, profile)] == [f"entry {n}" for n in range(5)]
    seen: list[str] = []
    page = list_entries(api, api.parent, profile, "?limit=2")
    assert page.status_code == 200 and page.json()["limit"] == 2
    cursors = 0
    while True:
        body = page.json()
        seen += [item["context_entry_id"] for item in body["context_entries"]]
        if body["next_cursor"] is None:
            break
        cursors += 1
        if cursors == 1:  # an entry added between two pages is seen by the keyset, not skipped
            created.append(entry_id_of(add_entry(api, api.parent, profile, "late entry")))
        page = list_entries(api, api.parent, profile, f"?limit=2&cursor={body['next_cursor']}")
        assert page.status_code == 200
    assert seen == created  # oldest first, no duplicate, no gap
    first = list_entries(api, api.parent, profile).json()
    assert [item["short_text"] for item in first["context_entries"]][:2] == ["entry 0", "entry 1"]
    assert set(first["context_entries"][0]) == {
        "context_entry_id",
        "entry_kind",
        "short_text",
        "source_kind",
        "approximate_date",
        "created_at",
    }
    assert list_entries(api, api.parent, profile, "?limit=0").status_code == 400
    assert list_entries(api, api.parent, profile, "?limit=101").status_code == 400
    empty = list_entries(api, api.parent, make_profile(api, api.parent)).json()
    assert empty == {"context_entries": [], "next_cursor": None, "limit": 25}


def test_context_entry_cursor_is_bound_to_the_profile_and_the_owner(api: ActivityApi) -> None:
    mine, also_mine = make_profile(api, api.parent), make_profile(api, api.parent)
    for n in range(3):
        add_entry(api, api.parent, mine, f"m{n}")
        add_entry(api, api.parent, also_mine, f"a{n}")
    cursor = list_entries(api, api.parent, mine, "?limit=1").json()["next_cursor"]
    assert cursor
    reused = list_entries(api, api.parent, also_mine, f"?cursor={cursor}")
    assert reused.status_code == 400 and code_of(reused) == "INVALID_REQUEST"
    assert reused.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    # another owner cannot use the cursor on the profile either: the profile is simply not theirs
    stolen = list_entries(api, api.other_parent, mine, f"?cursor={cursor}")
    assert stolen.status_code == 404 and code_of(stolen) == "PROFILE_NOT_FOUND"
    for bad in ("not-a-cursor", "e30", "%20", "a" * 3000):
        assert list_entries(api, api.parent, mine, f"?cursor={bad}").status_code == 400, bad


def test_same_key_concurrent_create_commits_one_entry(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    barrier = Barrier(4)

    def call(_: int) -> Any:
        barrier.wait()
        return add_entry(api, api.parent, profile, "concurrent", key="same-key-1")

    with ThreadPoolExecutor(4) as pool:
        responses = list(pool.map(call, range(4)))
    assert [response.status_code for response in responses] == [201] * 4
    assert len({entry_id_of(response) for response in responses}) == 1
    assert len(entry_rows(api, profile)) == 1


def test_create_replay_and_payload_mismatch_use_the_durable_receipt(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    first = add_entry(
        api,
        api.parent,
        profile,
        "  an entry  ",
        key="key-a",
        source_ref="note-9",
        approximate_date="2026-05-01",
    )
    assert first.status_code == 201, first.text
    stored = first.json()["context_entry"]
    assert stored["short_text"] == "an entry"  # stored trimmed
    assert stored["approximate_date"] == "2026-05-01"
    assert "source_ref" not in first.text and "note-9" not in first.text
    replay = add_entry(
        api,
        api.parent,
        profile,
        "  an entry  ",
        key="key-a",
        source_ref="note-9",
        approximate_date="2026-05-01",
    )
    assert replay.status_code == 201 and replay.json() == first.json()
    assert len(entry_rows(api, profile)) == 1
    mismatch = add_entry(api, api.parent, profile, "another text", key="key-a")
    assert mismatch.status_code == 400 and code_of(mismatch) == "INVALID_IDEMPOTENCY_KEY"
    other_profile = make_profile(api, api.parent)  # the same key on another profile is its own
    assert add_entry(api, api.parent, other_profile, "x", key="key-a").status_code == 201
    assert len(entry_rows(api, profile)) == 1
    with api.sessions()() as db:
        receipts = list(
            db.scalars(
                select(ParentCommandReceiptModel).where(
                    ParentCommandReceiptModel.operation_scope == "create_context_entry",
                    ParentCommandReceiptModel.resource_scope == profile,
                )
            )
        )
    assert len(receipts) == 1
    assert receipts[0].response_status == 201
    assert receipts[0].response_body == {"context_entry_id": stored["context_entry_id"]}
    row = entry_rows(api, profile)[0]
    assert row.source_ref == "note-9" and row.created_by == _principal_scope_ref(
        principal_of(api.parent)
    )
    assert api.parent not in row.created_by  # a hashed reference, never the raw subject
    for bad in ({"entry_kind": "DIAGNOSIS"}, {"short_text": "   "}, {"source_kind": "bad"}):
        response = api.client.post(
            f"/v1/parent/profiles/{profile}/context-entries",
            json=entry_body(**bad),
            headers=headers(api.parent, uuid4().hex),
        )
        assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST"
    assert len(entry_rows(api, profile)) == 1


def test_cross_tenant_read_create_and_selection_return_404(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    entry = entry_id_of(add_entry(api, api.parent, profile))
    for caller in (api.other_parent, api.teacher, f"unknown-{uuid4().hex}"):
        assert list_entries(api, caller, profile).status_code == 404, caller
        assert add_entry(api, caller, profile, "intruder").status_code == 404, caller
    assert list_entries(api, api.parent, str(uuid4())).status_code == 404
    assert len(entry_rows(api, profile)) == 1
    # the run of another Parent: the selection names an entry of a profile that is not theirs
    other_profile = make_profile(api, api.other_parent)
    run_id = ready_run(api, api.other_parent, other_profile)
    before = len(input_rows(api, run_id))
    response = confirm(api, api.other_parent, run_id, [entry])
    assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
    assert len(input_rows(api, run_id)) == before and story_rows(api, run_id) == []
    # the owner of the entry cannot confirm a run that is not theirs either
    assert confirm(api, api.parent, run_id, [entry]).status_code == 404


def test_an_entry_is_append_only_and_a_profile_with_entries_cannot_be_removed(
    api: ActivityApi,
) -> None:
    profile = make_profile(api, api.parent)
    entry = entry_id_of(add_entry(api, api.parent, profile, "kept"))
    with (
        pytest.raises(DBAPIError, match="PARENT_PROFILE_CONTEXT_ENTRY_UPDATE_FORBIDDEN"),
        api.sessions().begin() as db,
    ):
        db.execute(
            update(ParentProfileContextEntryModel)
            .where(ParentProfileContextEntryModel.context_entry_id == UUID(entry))
            .values(short_text="changed")
        )
    assert entry_rows(api, profile)[0].short_text == "kept"
    with (
        pytest.raises(IntegrityError, match="foreign key constraint"),
        api.sessions().begin() as db,
    ):
        db.execute(
            text("DELETE FROM parent.child_profiles WHERE parent_profile_id = :id"),
            {"id": profile},
        )
    with api.sessions()() as db:  # the entry key itself is RESTRICT (like the other Parent keys)
        action = db.scalar(
            text(
                "SELECT confdeltype FROM pg_constraint "
                "WHERE conname = 'fk_parent_profile_context_entries_profile'"
            )
        )
    assert action == "r"
    # a deletion request only marks the profile: reads, creates and selections then refuse it
    run_id = ready_run(api, api.parent, profile)
    deleted = api.client.delete(
        f"/v1/parent/profiles/{profile}", headers=headers(api.parent, uuid4().hex)
    )
    assert deleted.status_code == 202, deleted.text
    assert list_entries(api, api.parent, profile).status_code == 404
    assert add_entry(api, api.parent, profile, "late").status_code == 404
    refused = confirm(api, api.parent, run_id, [entry])
    assert refused.status_code == 404 and code_of(refused) == "RESOURCE_NOT_FOUND"
    assert len(input_rows(api, run_id)) == 2 and story_rows(api, run_id) == []
    assert len(entry_rows(api, profile)) == 1
    with api.sessions()() as db:
        state = db.scalar(
            select(ParentChildProfileModel.state).where(
                ParentChildProfileModel.parent_profile_id == UUID(profile)
            )
        )
    assert state == "DELETE_PENDING"
    # the plain v1 confirmation of the same run still works (no selection, no entry read)
    assert confirm(api, api.parent, run_id).status_code == 200


# ============================================================================= the selection
def test_selected_entries_create_a_hashed_v2_snapshot_and_the_next_input_revision(
    api: ActivityApi,
) -> None:
    profile = make_profile(api, api.parent)
    chosen = [
        entry_id_of(
            add_entry(api, api.parent, profile, "thich cho ca an", source_ref="secret-ref")
        ),
        entry_id_of(
            add_entry(
                api,
                api.parent,
                profile,
                "tu dap xe",
                entry_kind="ACHIEVEMENT",
                source_kind="TEACHER_NOTE",
                approximate_date="2026-04-02",
            )
        ),
    ]
    left_out = entry_id_of(
        add_entry(api, api.parent, profile, "khong chon", entry_kind="OBSERVATION")
    )
    run_id = ready_run(api, api.parent, profile)
    before = input_rows(api, run_id)
    assert [row["input_revision"] for row in before] == [1, 2]
    before_run = run_row(api, run_id)
    response = confirm(api, api.parent, run_id, [chosen[1], chosen[0]], key="select-1")  # any order
    assert response.status_code == 200, response.text
    after = input_rows(api, run_id)
    assert [row["input_revision"] for row in after] == [1, 2, 3]
    assert after[0] == before[0] and after[1] == before[1]  # the old rows are untouched
    new = after[2]
    expected = {
        **before[1]["context_snapshot"],
        "schema_version": PARENT_CONTEXT_V2_SCHEMA,
        "selected_entries": [
            {"kind": "OBSERVATION", "text": "thich cho ca an"},
            {"kind": "ACHIEVEMENT", "text": "tu dap xe"},
        ],  # (created_at, id) order, whatever order the ids were sent in
    }
    assert new["context_snapshot"] == expected
    assert new["context_snapshot_sha256"] == _sha256_json(expected)
    assert new["context_revision"] == 2 and new["context_confirmed_by"] is not None
    assert new["context_confirmed_at"] is not None
    for column in (
        "original_asset_ref",
        "original_sha256",
        "derived_asset_ref",
        "typed_idea",
        "source_profile_revision_ref",
        "lesson_pin_snapshot",
    ):
        assert new[column] == before[1][column], column  # copied forward
    with api.sessions()() as db:
        stored_size = db.scalar(
            text(
                "SELECT octet_length(context_snapshot::text) FROM story.run_inputs "
                "WHERE run_input_id = :id"
            ),
            {"id": new["run_input_id"]},
        )
    assert stored_size == jsonb_text_size(expected)  # the guard measures the stored form
    run = run_row(api, run_id)
    assert run["current_input_revision"] == 3 and run["version"] > before_run["version"]
    story_run = response.json()["story_run"]
    assert story_run["context_confirmed"] is True and story_run["context_revision"] == 2
    assert story_run["current_input_revision"] == 3
    assert story_run["context_snapshot"] == expected
    assert story_run["context_snapshot_sha256"] == new["context_snapshot_sha256"]
    for hidden in (*chosen, left_out, "secret-ref", "TEACHER_NOTE", "2026-04-02", "khong chon"):
        assert hidden not in response.text, hidden
    (receipt,) = context_receipts(api, run_id)
    assert receipt["response_body"] == {"context_revision": 2}
    # the story started on the new row, with the chosen entries and nothing else of them
    (story,) = story_rows(api, run_id)
    assert story["context_revision"] == 2 and story["revision_no"] == 1
    worker = api.generator.inputs[0]
    assert worker["schema_version"] == "sketch2life.story-generation-input.v3"
    assert worker["context_entries"] == expected["selected_entries"]
    assert worker["context_revision"] == 2 and worker["child_age_months"] == 60
    assert story["request_sha256"] == _sha256_json(worker)
    for hidden in (*chosen, left_out, "secret-ref", "TEACHER_NOTE", "2026-04-02", "khong chon"):
        assert hidden not in str(worker), hidden


def test_an_empty_selection_is_a_confirmed_v2_snapshot_with_no_entry(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    entry_id_of(add_entry(api, api.parent, profile))
    run_id = ready_run(api, api.parent, profile)
    response = confirm(api, api.parent, run_id, [])
    assert response.status_code == 200, response.text
    new = input_rows(api, run_id)[-1]
    assert new["context_snapshot"]["schema_version"] == PARENT_CONTEXT_V2_SCHEMA
    assert new["context_snapshot"]["selected_entries"] == []
    assert api.generator.inputs[0]["context_entries"] == []


def test_the_legacy_confirmation_without_the_field_is_unchanged(api: ActivityApi) -> None:
    for owner, body_ids in ((api.parent, "absent"), (api.other_parent, None)):
        profile = make_profile(api, owner)
        entry_id_of(add_entry(api, owner, profile))
        run_id = ready_run(api, owner, profile)
        response = confirm(api, owner, run_id, body_ids, key=f"legacy-{owner[-8:]}")
        assert response.status_code == 200, response.text
        rows = input_rows(api, run_id)
        assert [row["input_revision"] for row in rows] == [1, 2]  # no new row
        assert rows[1]["context_snapshot"]["schema_version"] == PARENT_CONTEXT_V1_SCHEMA
        assert rows[1]["context_confirmed_by"] is not None and rows[1]["context_revision"] == 1
        assert response.json()["story_run"]["context_snapshot"]["schema_version"] == (
            PARENT_CONTEXT_V1_SCHEMA
        )
        assert api.generator.inputs[-1]["context_entries"] == []
        # the receipt is the old shape and replays: same key, same body, no second effect
        (receipt,) = context_receipts(api, run_id)
        assert receipt["response_body"] == {"context_revision": 1}
        replay = confirm(api, owner, run_id, body_ids, key=f"legacy-{owner[-8:]}")
        assert replay.status_code == 200 and len(input_rows(api, run_id)) == 2
        # a legacy request is not an empty selection (the fingerprint differs)
        retry = confirm(api, owner, run_id, [], key="a-fresh-key")
        # the story already started, so a second confirmation is a state conflict, not a 200
        assert retry.status_code == 409 and code_of(retry) == "INVALID_STATE_TRANSITION"


def test_confirmation_replay_does_not_append_a_second_input_revision(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    first_entry = entry_id_of(add_entry(api, api.parent, profile, "one"))
    second_entry = entry_id_of(add_entry(api, api.parent, profile, "two"))
    run_id = ready_run(api, api.parent, profile)
    first = confirm(api, api.parent, run_id, [first_entry, second_entry], key="replay-key")
    assert first.status_code == 200, first.text
    assert len(input_rows(api, run_id)) == 3
    again = confirm(
        api,
        api.parent,
        run_id,
        [second_entry, first_entry],
        key="replay-key",
        revision=1,
        context_hash=input_rows(api, run_id)[1]["context_snapshot_sha256"],
    )  # the same selection in another order is the same request
    assert again.status_code == 200
    assert (
        again.json()["story_run"]["context_snapshot"]
        == first.json()["story_run"]["context_snapshot"]
    )
    assert len(input_rows(api, run_id)) == 3 and len(story_rows(api, run_id)) == 1
    assert len(context_receipts(api, run_id)) == 1
    other = confirm(
        api,
        api.parent,
        run_id,
        [first_entry],
        key="replay-key",
        revision=1,
        context_hash=input_rows(api, run_id)[1]["context_snapshot_sha256"],
    )
    assert other.status_code == 400 and code_of(other) == "INVALID_IDEMPOTENCY_KEY"
    assert len(input_rows(api, run_id)) == 3
    # a confirmed current input takes no second selection: no second confirmed row
    third = confirm(api, api.parent, run_id, [first_entry], key="another-key", revision=2)
    assert third.status_code == 409 and code_of(third) == "INVALID_STATE_TRANSITION"
    assert len(input_rows(api, run_id)) == 3 and len(context_receipts(api, run_id)) == 1


def test_a_selection_after_a_legacy_confirmation_is_a_409_with_no_second_row(
    api: ActivityApi,
) -> None:
    profile = make_profile(api, api.parent)
    entry = entry_id_of(add_entry(api, api.parent, profile))
    run_id = ready_run(api, api.parent, profile)
    assert confirm(api, api.parent, run_id).status_code == 200
    late = confirm(api, api.parent, run_id, [entry], key="late-key")
    assert late.status_code == 409 and code_of(late) == "INVALID_STATE_TRANSITION"
    assert len(input_rows(api, run_id)) == 2 and len(context_receipts(api, run_id)) == 1


def test_stale_context_hash_returns_409_without_write(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    entry = entry_id_of(add_entry(api, api.parent, profile))
    run_id = ready_run(api, api.parent, profile)
    before = run_row(api, run_id)
    stale = confirm(api, api.parent, run_id, [entry], context_hash="0" * 64)
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    wrong_revision = confirm(api, api.parent, run_id, [entry], revision=9)
    assert wrong_revision.status_code == 409 and code_of(wrong_revision) == "STALE_REVISION"
    assert len(input_rows(api, run_id)) == 2 and context_receipts(api, run_id) == []
    after = run_row(api, run_id)
    assert (after["version"], after["revision"], after["current_input_revision"]) == (
        before["version"],
        before["revision"],
        before["current_input_revision"],
    )
    assert story_rows(api, run_id) == []


def test_a_foreign_profile_entry_id_is_not_disclosed(api: ActivityApi) -> None:
    mine, second = make_profile(api, api.parent), make_profile(api, api.parent)
    others = make_profile(api, api.other_parent)
    own_entry = entry_id_of(add_entry(api, api.parent, mine, "mine"))
    sibling_entry = entry_id_of(add_entry(api, api.parent, second, "same parent, other profile"))
    foreign_entry = entry_id_of(add_entry(api, api.other_parent, others, "someone else"))
    run_id = ready_run(api, api.parent, mine)
    bodies = []
    for ids in ([foreign_entry], [sibling_entry], [str(uuid4())], [own_entry, foreign_entry]):
        response = confirm(api, api.parent, run_id, ids)
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND", ids
        bodies.append(
            {key: value for key, value in response.json().items() if key != "correlation_id"}
        )
    assert all(body == bodies[0] for body in bodies)  # one answer for every kind of miss
    assert len(input_rows(api, run_id)) == 2 and context_receipts(api, run_id) == []
    assert confirm(api, api.parent, run_id, [own_entry]).status_code == 200


def test_snapshot_byte_limit_rejects_without_partial_confirmation(api: ActivityApi) -> None:
    """The repository guard with a resolver double that returns too many entries (the route
    case that reaches the bound with real entries is the next test)."""

    profile = make_profile(api, api.parent)
    run_id = ready_run(api, api.parent, profile)
    current = input_rows(api, run_id)[-1]
    big = [SelectedContextEntry("OBSERVATION", EMOJI * 500)] * 17
    with api.sessions()() as db:
        repository = SqlParentStoryRunRepository(db)
        with pytest.raises(ParentStoryRunError) as raised:
            repository.confirm_context(
                principal=principal_of(api.parent),
                run_id=run_id,
                expected_context_revision=1,
                expected_context_snapshot_sha256=str(current["context_snapshot_sha256"]),
                idempotency_key="big-key",
                selected_context_entry_ids=tuple(uuid4() for _ in range(17)),
                resolve_context_entries=lambda _profile, _ids: big,
            )
    assert (raised.value.status_code, raised.value.code) == (400, "INVALID_REQUEST")
    assert raised.value.field_errors == [
        {"field": "selected_context_entry_ids", "code": "TOO_LONG"}
    ]
    assert len(input_rows(api, run_id)) == 2 and context_receipts(api, run_id) == []
    assert run_row(api, run_id)["current_input_revision"] == 2


def test_a_large_base_context_makes_the_32_kib_guard_reachable_through_the_route(
    api: ActivityApi,
) -> None:
    """Control characters are refused in entries, so ten entries stay near 20 KB; but the stored
    base context (profile summary, topic and idea) accepts them, and each costs six bytes in
    ``jsonb::text``. Such a run plus ten maximal real entries passes 32,768 bytes: the answer is
    a clean 400 with the field error, and nothing is written."""

    profile = make_profile(api, api.parent)
    ids = [
        entry_id_of(add_entry(api, api.parent, profile, EMOJI * 500, source_kind=f"KIND_{n}"))
        for n in range(10)
    ]
    heavy = {
        "interests_summary": "\x01" * 2000,
        "topic": "\x01" * 120,
        "adult_confirmed_idea": "\x01" * 500,
    }
    run_id = ready_run(api, api.parent, profile, heavy)
    base = input_rows(api, run_id)[-1]["context_snapshot"]
    entries = [SelectedContextEntry("OBSERVATION", EMOJI * 500)] * 10
    assert jsonb_text_size(build_selected_context_snapshot(base, entries)) > SNAPSHOT_MAX_BYTES
    too_big = confirm(api, api.parent, run_id, ids)
    assert too_big.status_code == 400, too_big.text
    assert code_of(too_big) == "INVALID_REQUEST"
    assert too_big.json()["field_errors"][0]["field"] == "selected_context_entry_ids"
    assert too_big.json()["field_errors"][0]["code"] == "TOO_LONG"
    assert len(input_rows(api, run_id)) == 2 and context_receipts(api, run_id) == []
    assert story_rows(api, run_id) == []
    assert run_row(api, run_id)["current_input_revision"] == 2
    # fewer entries fit and the confirmation then succeeds on the same run
    assert confirm(api, api.parent, run_id, ids[:3]).status_code == 200


def test_nul_and_control_characters_are_a_400_with_no_write_and_newline_is_kept(
    api: ActivityApi,
) -> None:
    profile = make_profile(api, api.parent)
    for bad in ("a\x00b", "a\x01b", "a\x7fb"):
        response = add_entry(api, api.parent, profile, bad)
        assert response.status_code == 400, repr(bad)
        assert code_of(response) == "INVALID_REQUEST"
        assert {"field": "short_text", "code": "INVALID_FORMAT"} in response.json()["field_errors"]
    refused = add_entry(api, api.parent, profile, "ok", source_ref="r\x00")
    assert refused.status_code == 400 and code_of(refused) == "INVALID_REQUEST"
    assert entry_rows(api, profile) == []
    kept = add_entry(api, api.parent, profile, "line one\n\tline two")
    assert kept.status_code == 201
    assert kept.json()["context_entry"]["short_text"] == "line one\n\tline two"
    # the database check is the second line: a direct insert of a control character is refused
    with (
        pytest.raises(IntegrityError, match="ck_parent_profile_context_entries_text"),
        api.sessions().begin() as db,
    ):
        db.add(
            ParentProfileContextEntryModel(
                context_entry_id=uuid4(),
                parent_profile_id=UUID(profile),
                entry_kind="OBSERVATION",
                short_text="a\x01b",
                source_kind="PARENT_NOTE",
                created_by="c",
            )
        )
    with (
        pytest.raises(IntegrityError, match="ck_parent_profile_context_entries_source_ref"),
        api.sessions().begin() as db,
    ):
        db.add(
            ParentProfileContextEntryModel(
                context_entry_id=uuid4(),
                parent_profile_id=UUID(profile),
                entry_kind="OBSERVATION",
                short_text="ok",
                source_kind="PARENT_NOTE",
                source_ref="r\nx",
                created_by="c",
            )
        )


def test_a_resolver_failure_rolls_back_and_the_database_bound_holds(
    api: ActivityApi,
) -> None:
    profile = make_profile(api, api.parent)
    run_id = ready_run(api, api.parent, profile)
    current = input_rows(api, run_id)[-1]
    before = run_row(api, run_id)

    def failing_resolver(_profile: UUID, _ids: tuple[UUID, ...]) -> list[SelectedContextEntry]:
        raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")

    with api.sessions()() as db, pytest.raises(ParentStoryRunError) as raised:
        SqlParentStoryRunRepository(db).confirm_context(
            principal=principal_of(api.parent),
            run_id=run_id,
            expected_context_revision=1,
            expected_context_snapshot_sha256=str(current["context_snapshot_sha256"]),
            idempotency_key="failing-key",
            selected_context_entry_ids=(uuid4(),),
            resolve_context_entries=failing_resolver,
        )
    assert raised.value.status_code == 503
    assert len(input_rows(api, run_id)) == 2
    assert run_row(api, run_id)["version"] == before["version"]
    # the row bound itself: a snapshot over 32,768 bytes of jsonb text is refused by the database
    oversize = {"schema_version": PARENT_CONTEXT_V2_SCHEMA, "x": "y" * 33000}
    with (
        pytest.raises(IntegrityError, match="ck_story_run_input_parent_context"),
        api.sessions().begin() as db,
    ):
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=9,
                source_profile_revision_ref=str(uuid4()),
                context_revision=9,
                context_snapshot=oversize,
                context_snapshot_sha256="e" * 64,
                created_at=datetime.now(UTC),
            )
        )


def test_the_run_purge_removes_the_v2_row_with_the_run(api: ActivityApi) -> None:
    profile = make_profile(api, api.parent)
    entry = entry_id_of(add_entry(api, api.parent, profile, "to be purged with the run"))
    run_id = ready_run(api, api.parent, profile)
    assert confirm(api, api.parent, run_id, [entry]).status_code == 200
    assert len(input_rows(api, run_id)) == 3
    cancel = api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": revision_of(api, run_id)},
        headers=headers(api.parent, uuid4().hex),
    )
    assert cancel.status_code == 202, cancel.text
    store = SqlStoryLifecycleStore(api.sessions())
    store.purge_story_content(store.plan_story_purge(run_id))
    assert input_rows(api, run_id) == []  # the selected texts went with the run content
    assert len(entry_rows(api, profile)) == 1  # the profile entries stay with the profile
    with api.sessions()() as db:
        left = db.scalar(
            select(func.count())
            .select_from(story_tables.run_inputs)
            .where(story_tables.run_inputs.c.run_id == run_id)
        )
    assert left == 0


# ============================================================================= the round trip
@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T12A_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip(
            "set T12A_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database"
        )
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v4_t12a", "roundtrip")):
        pytest.fail(
            "T12A_ROUNDTRIP_DATABASE_URL must name a frc08_v4_t12a*roundtrip*be1_acceptance db"
        )
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_the_migration_round_trip_refuses_data_and_restores_cleanly(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    parent_root = "20261109_m2_parent_profiles"
    # T-12c: 20261121_psn_0001 sits on 20261121_pce_0001, so `upgrade heads` leaves this row
    live = "20261121_psn_0001"

    def has_table() -> bool:
        with engine.connect() as connection:
            return bool(
                connection.scalar(text("SELECT to_regclass('parent.profile_context_entries')"))
            )

    def versions() -> set[str]:
        with engine.connect() as connection:
            return {
                str(v) for v in connection.scalars(text("SELECT version_num FROM alembic_version"))
            }

    assert has_table() and live in versions() and parent_root not in versions()
    profile, entry = uuid4(), uuid4()
    # a row needs a real profile (deferred current-revision key): build one in one transaction
    with engine.begin() as connection:
        connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        connection.execute(
            text(
                "INSERT INTO parent.child_profiles (parent_profile_id, owner_issuer, "
                "owner_subject, current_revision_no) VALUES (:p, 'i', 's', 1)"
            ),
            {"p": profile},
        )
        connection.execute(
            text(
                "INSERT INTO parent.profile_revisions (profile_revision_id, parent_profile_id, "
                "revision_no, age_months, display_name, authored_by_issuer, authored_by_subject, "
                "revision_hash) VALUES (:rev, :p, 1, 60, 'Mina', 'i', 's', repeat('a', 64))"
            ),
            {"rev": uuid4(), "p": profile},
        )
        connection.execute(
            text(
                "INSERT INTO parent.profile_context_entries (context_entry_id, parent_profile_id, "
                "entry_kind, short_text, source_kind, created_by) VALUES "
                "(:e, :p, 'OBSERVATION', 'x', 'PARENT_NOTE', 'c')"
            ),
            {"e": entry, "p": profile},
        )
    with pytest.raises(Exception, match="downgrade refused"):
        command.downgrade(config, parent_root)
    assert has_table() and live in versions()  # nothing was removed
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM parent.profile_context_entries WHERE context_entry_id = :e"),
            {"e": entry},
        )
    command.downgrade(config, parent_root)
    assert not has_table() and parent_root in versions()
    with engine.connect() as connection:
        leftovers = connection.scalar(
            text(
                "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                "WHERE n.nspname = 'parent' AND p.proname = 'reject_profile_context_entry_update'"
            )
        )
    assert leftovers == 0
    command.upgrade(config, "heads")
    assert has_table() and live in versions()
