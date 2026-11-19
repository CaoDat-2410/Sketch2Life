"""FEAT-081 C3b: the Parent run-history list on PostgreSQL.

Runs only against a disposable database whose name contains ``be1_acceptance``; synthetic rows only.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.parent_story_repository import _principal_scope_ref
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-c3b-issuer"
SUMMARY_KEYS = {
    "run_id",
    "parent_profile_id",
    "run_state",
    "revision",
    "deleting",
    "can_cancel",
    "can_delete",
    "created_at",
    "updated_at",
}


@dataclass
class HistoryApi:
    app: FastAPI
    client: TestClient
    parent: str
    other_parent: str
    teacher: str

    def session(self) -> Any:
        return self.app.state.be1_runtime.session_factory


@pytest.fixture
def history_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[HistoryApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    parent, other_parent, teacher = (
        f"synthetic-c3b-parent-{token}",
        f"synthetic-c3b-other-{token}",
        f"synthetic-c3b-teacher-{token}",
    )
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

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield HistoryApi(app, client, parent, other_parent, teacher)
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _principal(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def _profile(api: HistoryApi, owner: str, state: str = "ACTIVE") -> UUID:
    profile_id = uuid4()
    with api.session().begin() as db:
        db.add(
            ParentChildProfileModel(
                parent_profile_id=profile_id,
                owner_issuer=ISSUER,
                owner_subject=owner,
                state=state,
                current_revision_no=1,
            )
        )
        db.add(
            ParentProfileRevisionModel(
                profile_revision_id=uuid4(),
                parent_profile_id=profile_id,
                revision_no=1,
                age_months=72,
                display_name="Synthetic child",
                authored_by_issuer=ISSUER,
                authored_by_subject=owner,
                revision_hash="a" * 64,
            )
        )
    return profile_id


def _run(
    api: HistoryApi,
    owner: str,
    state: str,
    created_at: datetime,
    profile_id: UUID | None,
) -> str:
    run_id = str(uuid4())
    with api.session().begin() as db:
        db.execute(
            story_tables.story_runs.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=_principal_scope_ref(_principal(owner)),
                profile_ref=str(profile_id) if profile_id else None,
                run_state=state,
                revision=2,
                version=2,
                created_at=created_at,
                updated_at=created_at,
            )
        )
    return run_id


def _get(api: HistoryApi, query: str = "", subject: str | None = None) -> Any:
    return api.client.get(
        f"/v1/story-runs{query}", headers={"X-Test-Principal": subject or api.parent}
    )


def test_c3b_history_scope_order_states_and_paging(history_api: HistoryApi) -> None:
    api = history_api
    profile = _profile(api, api.parent)
    base = datetime(2026, 11, 19, 8, 0, tzinfo=UTC)
    tied = [_run(api, api.parent, "COMPLETED", base, profile) for _ in range(3)]
    newer = _run(api, api.parent, "INPUT_PROCESSING", base + timedelta(minutes=5), profile)
    failed = _run(api, api.parent, "FAILED", base - timedelta(minutes=5), profile)
    pending_with_ref = _run(api, api.parent, "DELETE_PENDING", base - timedelta(minutes=6), profile)
    pending_no_ref = _run(api, api.parent, "DELETE_PENDING", base - timedelta(minutes=7), None)
    deleted = _run(api, api.parent, "DELETED", base - timedelta(minutes=8), None)
    foreign = _run(api, api.other_parent, "COMPLETED", base, None)

    page = _get(api)
    assert page.status_code == 200, page.text
    body = page.json()
    assert set(body) == {"request_id", "items", "next_cursor"}
    ids = [item["run_id"] for item in body["items"]]
    assert deleted not in ids and foreign not in ids
    expected_tied = sorted(tied, reverse=True)
    assert ids == [newer, *expected_tied, failed, pending_with_ref, pending_no_ref]
    assert all(set(item) == SUMMARY_KEYS for item in body["items"])
    by_id = {item["run_id"]: item for item in body["items"]}
    assert by_id[newer]["can_cancel"] is True and by_id[newer]["can_delete"] is False
    assert by_id[tied[0]]["can_delete"] is True and by_id[tied[0]]["can_cancel"] is False
    assert by_id[failed]["can_delete"] is True
    for pending in (pending_with_ref, pending_no_ref):
        item = by_id[pending]
        assert item["deleting"] is True and item["parent_profile_id"] is None
        assert item["can_cancel"] is False and item["can_delete"] is False
    assert by_id[newer]["parent_profile_id"] == str(profile)

    walked: list[str] = []
    cursor: str | None = None
    while True:
        response = _get(api, f"?limit=2{'&cursor=' + cursor if cursor else ''}")
        assert response.status_code == 200, response.text
        walked += [item["run_id"] for item in response.json()["items"]]
        cursor = response.json()["next_cursor"]
        if cursor is None:
            break
    assert walked == ids
    assert _get(api, "?limit=101").status_code == 400
    bad = _get(api, "?cursor=bm90LWEtY3Vyc29y")
    assert bad.status_code == 400 and bad.json()["field_errors"] is None
    assert _get(api, subject=api.teacher).status_code == 403


def test_c3b_history_profile_filter(history_api: HistoryApi) -> None:
    api = history_api
    active = _profile(api, api.parent)
    closing = _profile(api, api.parent, state="DELETE_PENDING")
    foreign = _profile(api, api.other_parent)
    base = datetime(2026, 11, 19, 9, 0, tzinfo=UTC)
    on_active = _run(api, api.parent, "COMPLETED", base, active)
    purge = _run(api, api.parent, "DELETE_PENDING", base - timedelta(minutes=1), active)
    on_closing = _run(api, api.parent, "FAILED", base, closing)

    filtered = _get(api, f"?parent_profile_id={active}")
    assert filtered.status_code == 200, filtered.text
    ids = [item["run_id"] for item in filtered.json()["items"]]
    assert ids == [on_active] and purge not in ids
    closing_page = _get(api, f"?parent_profile_id={closing}")
    assert [item["run_id"] for item in closing_page.json()["items"]] == [on_closing]
    for profile_id in (foreign, uuid4()):
        response = _get(api, f"?parent_profile_id={profile_id}")
        assert response.status_code == 404, response.text
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
