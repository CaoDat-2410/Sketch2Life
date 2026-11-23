"""FEAT-066 C5: Platform Admin account paging and keyed commands on PostgreSQL.

Runs only against a disposable database whose name contains ``be1_acceptance``. The identity
provider is a synthetic in-memory fake; no network is used.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProfile,
    IdentityAccountProvisioningUnavailable,
    ProvisionedIdentity,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-accounts-issuer"
BASE = "/api/platform-admin/v1/accounts"


@dataclass
class FakeProvisioner:
    """Synthetic identity provider; records every call."""

    profiles: dict[str, IdentityAccountProfile] = field(default_factory=dict)
    created: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    disabled_calls: list[tuple[str, bool]] = field(default_factory=list)
    down: bool = False
    next_subject: str | None = None
    delay_seconds: float = 0.0

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        raise AssertionError("not used")

    def create_account(self, *, email: str, display_name: str | None = None) -> ProvisionedIdentity:
        if self.down:
            raise IdentityAccountProvisioningUnavailable("down")
        if any(profile.email == email for profile in self.profiles.values()):
            raise IdentityAccountConflict("exists")
        subject = self.next_subject or f"synthetic-account-{uuid4()}"
        self.next_subject = None
        self.profiles[subject] = IdentityAccountProfile(subject, email, display_name)
        self.created.append(subject)
        return ProvisionedIdentity(subject=subject, issuer=ISSUER)

    def delete_account(self, subject: str) -> None:
        self.deleted.append(subject)
        self.profiles.pop(subject, None)

    def set_account_disabled(self, subject: str, disabled: bool) -> None:
        if self.down:
            raise IdentityAccountProvisioningUnavailable("down")
        self.disabled_calls.append((subject, disabled))
        # Hold the request inside its row locks so a concurrent duplicate must wait (C5-IMPL-R2-01).
        time.sleep(self.delay_seconds)

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        if self.down:
            raise IdentityAccountProvisioningUnavailable("down")
        return {subject: self.profiles[subject] for subject in subjects if subject in self.profiles}

    def find_account_by_email(self, email: str) -> ProvisionedIdentity | None:
        return None


@dataclass
class AccountsApi:
    app: FastAPI
    client: TestClient
    provisioner: FakeProvisioner
    admin: str
    parent: str
    token: str


@pytest.fixture
def accounts_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[AccountsApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    provisioner = FakeProvisioner()
    app = create_app(identity_account_provisioner=provisioner)
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:10]
    admin = f"synthetic-c5-admin-{uuid4()}"
    parent = f"synthetic-c5-parent-{uuid4()}"
    with runtime.session_factory.begin() as db:
        for subject, role in ((admin, "platform_admin"), (parent, "parent")):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=role
                )
            )
            provisioner.profiles[subject] = IdentityAccountProfile(
                subject, f"{subject}@example.test", role
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield AccountsApi(app, client, provisioner, admin, parent, token)
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _h(subject: str, **extra: str) -> dict[str, str]:
    return {"X-Test-Principal": subject, **extra}


def _seed_teachers(api: AccountsApi, count: int) -> list[str]:
    """Insert synthetic Teacher identities with tied created_at values, newest first per group."""
    base = datetime.now(UTC) - timedelta(days=1)
    subjects: list[str] = []
    with api.app.state.be1_runtime.session_factory.begin() as db:
        for index in range(count):
            subject = f"synthetic-c5-teacher-{api.token}-{index:02d}"
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    issuer=ISSUER,
                    state="active",
                    account_role="teacher",
                    created_at=base - timedelta(seconds=index // 3),
                )
            )
            api.provisioner.profiles[subject] = IdentityAccountProfile(
                subject, f"{subject}@example.test", f"C5 {api.token} giáo viên {index}"
            )
            subjects.append(subject)
    return subjects


def _expected_teacher_ids(api: AccountsApi) -> list[str]:
    with api.app.state.be1_runtime.session_factory() as db:
        return list(
            db.scalars(
                select(AdultIdentityModel.account_id)
                .where(AdultIdentityModel.account_role == "teacher")
                .order_by(AdultIdentityModel.created_at.desc(), AdultIdentityModel.account_id)
            )
        )


def _walk(api: AccountsApi, query: str) -> tuple[list[str], set[int]]:
    ids: list[str] = []
    totals: set[int] = set()
    cursor: str | None = None
    for _ in range(50):
        suffix = f"&cursor={cursor}" if cursor else ""
        page = api.client.get(f"{BASE}?{query}{suffix}", headers=_h(api.admin))
        assert page.status_code == 200, page.text
        body = page.json()
        ids += [item["account_id"] for item in body["items"]]
        totals.add(body["total"])
        assert body["offset"] == 0
        cursor = body["next_cursor"]
        if cursor is None:
            return ids, totals
    raise AssertionError("cursor walk did not end")


def test_c5_list_defaults_to_25_and_cursor_walks_without_gaps(accounts_api: AccountsApi) -> None:
    api = accounts_api
    _seed_teachers(api, 30)
    expected = _expected_teacher_ids(api)
    first = api.client.get(f"{BASE}?role=teacher", headers=_h(api.admin))
    assert first.status_code == 200, first.text
    assert first.json()["limit"] == 25
    assert len(first.json()["items"]) == min(25, len(expected))
    assert api.client.get(f"{BASE}?limit=101", headers=_h(api.admin)).status_code == 400

    walked, totals = _walk(api, "role=teacher&limit=7")
    assert walked == expected
    assert totals == {len(expected)}

    legacy = api.client.get(f"{BASE}?role=teacher&limit=5&offset=5", headers=_h(api.admin))
    assert [item["account_id"] for item in legacy.json()["items"]] == expected[5:10]

    cursor = first.json()["next_cursor"]
    both = api.client.get(f"{BASE}?cursor={cursor}&offset=3", headers=_h(api.admin))
    assert both.status_code == 400, both.text
    assert both.json()["field_errors"] == [{"field": "offset", "code": "INVALID_FORMAT"}]
    bad = api.client.get(f"{BASE}?cursor=not-a-cursor", headers=_h(api.admin))
    assert bad.status_code == 400, bad.text
    assert bad.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]


def test_c5_search_cursor_keeps_total_constant(accounts_api: AccountsApi) -> None:
    api = accounts_api
    subjects = _seed_teachers(api, 12)
    walked, totals = _walk(api, f"search={api.token}&limit=5")
    assert totals == {12}
    expected = [
        account_id
        for account_id in _expected_teacher_ids(api)
        if account_id in _account_ids(api, subjects)
    ]
    assert walked == expected


def _account_ids(api: AccountsApi, subjects: list[str]) -> set[str]:
    with api.app.state.be1_runtime.session_factory() as db:
        return set(
            db.scalars(
                select(AdultIdentityModel.account_id).where(
                    AdultIdentityModel.subject.in_(subjects)
                )
            )
        )


def test_c5_non_admin_is_refused_on_all_three_routes(accounts_api: AccountsApi) -> None:
    api = accounts_api
    key = {"Idempotency-Key": f"c5-{uuid4()}"}
    assert api.client.get(BASE, headers=_h(api.parent)).status_code == 403
    created = api.client.post(
        BASE,
        json={"email": f"x-{api.token}@example.test", "display_name": "X", "role": "parent"},
        headers=_h(api.parent, **key),
    )
    assert created.status_code == 403
    patched = api.client.patch(
        f"{BASE}/{uuid4()}", json={"state": "disabled"}, headers=_h(api.parent, **key)
    )
    assert patched.status_code == 403


def test_c5_create_is_keyed_replays_and_stores_no_email(accounts_api: AccountsApi) -> None:
    api = accounts_api
    body = {
        "email": f"c5-{api.token}@example.test",
        "display_name": "Giáo viên C5",
        "role": "teacher",
    }
    missing = api.client.post(BASE, json=body, headers=_h(api.admin))
    assert missing.status_code == 400, missing.text
    assert missing.json()["field_errors"] == [{"field": "Idempotency-Key", "code": "REQUIRED"}]

    key = f"c5-create-{uuid4()}"
    created = api.client.post(BASE, json=body, headers=_h(api.admin, **{"Idempotency-Key": key}))
    assert created.status_code == 201, created.text
    replayed = api.client.post(BASE, json=body, headers=_h(api.admin, **{"Idempotency-Key": key}))
    assert replayed.status_code == 201, replayed.text
    assert replayed.json() == created.json()
    assert len(api.provisioner.created) == 1
    other = api.client.post(
        BASE,
        json={**body, "display_name": "Khác"},
        headers=_h(api.admin, **{"Idempotency-Key": key}),
    )
    assert other.status_code == 400, other.text
    assert other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    account_id = created.json()["account_id"]
    with api.app.state.be1_runtime.session_factory() as db:
        receipt = db.get(Be1CommandReceiptModel, (api.admin, "POST /accounts", key))
        assert receipt is not None
        assert "email" not in receipt.response_json
        assert body["email"] not in str(receipt.response_json)
        audits = db.scalar(
            select(func.count())
            .select_from(CoreAuditEntryModel)
            .where(CoreAuditEntryModel.resource_id == account_id)
        )
        assert audits == 1


def test_c5_create_failures_delete_the_provider_account_and_store_nothing(
    accounts_api: AccountsApi,
) -> None:
    api = accounts_api
    api.provisioner.down = True
    down_key = f"c5-down-{uuid4()}"
    down = api.client.post(
        BASE,
        json={"email": f"down-{api.token}@example.test", "display_name": "D", "role": "parent"},
        headers=_h(api.admin, **{"Idempotency-Key": down_key}),
    )
    assert down.status_code == 503, down.text
    api.provisioner.down = False

    # The provider returns a subject that already exists, so the commit fails.
    api.provisioner.next_subject = api.parent
    clash_key = f"c5-clash-{uuid4()}"
    clash = api.client.post(
        BASE,
        json={"email": f"clash-{api.token}@example.test", "display_name": "C", "role": "parent"},
        headers=_h(api.admin, **{"Idempotency-Key": clash_key}),
    )
    assert clash.status_code == 409, clash.text
    assert api.parent in api.provisioner.deleted
    with api.app.state.be1_runtime.session_factory() as db:
        for key in (down_key, clash_key):
            assert db.get(Be1CommandReceiptModel, (api.admin, "POST /accounts", key)) is None


def test_c5_update_is_keyed_and_replays_without_a_second_provider_call(
    accounts_api: AccountsApi,
) -> None:
    api = accounts_api
    [subject] = _seed_teachers(api, 1)
    with api.app.state.be1_runtime.session_factory() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == subject)
        )
    url = f"{BASE}/{account_id}"
    missing = api.client.patch(url, json={"state": "disabled"}, headers=_h(api.admin))
    assert missing.status_code == 400, missing.text

    key = f"c5-update-{uuid4()}"
    updated = api.client.patch(
        url, json={"state": "disabled"}, headers=_h(api.admin, **{"Idempotency-Key": key})
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["state"] == "disabled"
    assert updated.json()["revision"] == 2
    replayed = api.client.patch(
        url, json={"state": "disabled"}, headers=_h(api.admin, **{"Idempotency-Key": key})
    )
    assert replayed.status_code == 200, replayed.text
    assert replayed.json() == updated.json()
    assert api.provisioner.disabled_calls == [(subject, True)]
    other = api.client.patch(
        url, json={"state": "active"}, headers=_h(api.admin, **{"Idempotency-Key": key})
    )
    assert other.status_code == 400, other.text
    assert other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    with api.app.state.be1_runtime.session_factory() as db:
        identity = db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.subject == subject)
        )
        assert identity is not None and identity.state == "disabled" and identity.role_revision == 2


def test_c5_concurrent_identical_updates_change_once(accounts_api: AccountsApi) -> None:
    """Two identical PATCHes with one key serialise on the row locks; the second replays."""
    api = accounts_api
    [subject] = _seed_teachers(api, 1)
    with api.app.state.be1_runtime.session_factory() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == subject)
        )
    key = f"c5-race-{uuid4()}"
    api.provisioner.delay_seconds = 0.5

    def patch() -> Any:
        return api.client.patch(
            f"{BASE}/{account_id}",
            json={"state": "disabled"},
            headers=_h(api.admin, **{"Idempotency-Key": key}),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [future.result() for future in [executor.submit(patch) for _ in range(2)]]
    assert [response.status_code for response in results] == [200, 200]
    assert results[0].json() == results[1].json()
    assert api.provisioner.disabled_calls == [(subject, True)]
    with api.app.state.be1_runtime.session_factory() as db:
        identity = db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.subject == subject)
        )
        assert identity is not None and identity.role_revision == 2


def test_c5_update_with_provider_down_is_503_and_changes_nothing(accounts_api: AccountsApi) -> None:
    api = accounts_api
    [subject] = _seed_teachers(api, 1)
    with api.app.state.be1_runtime.session_factory() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == subject)
        )
    api.provisioner.down = True
    key = f"c5-down-update-{uuid4()}"
    down = api.client.patch(
        f"{BASE}/{account_id}",
        json={"state": "disabled"},
        headers=_h(api.admin, **{"Idempotency-Key": key}),
    )
    assert down.status_code == 503, down.text
    api.provisioner.down = False
    with api.app.state.be1_runtime.session_factory() as db:
        identity = db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.subject == subject)
        )
        assert identity is not None and identity.state == "active" and identity.role_revision == 1
        assert (
            db.get(Be1CommandReceiptModel, (api.admin, f"PATCH /accounts/{account_id}", key))
            is None
        )
