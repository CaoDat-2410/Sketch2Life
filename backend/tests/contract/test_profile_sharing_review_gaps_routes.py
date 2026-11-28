# ruff: noqa: E501, F811, SIM117, B023
"""Offline contract tests for E3 (T-SHARE1) review gaps."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import ParentRoleStoreUnavailable
from sketch2life.domain.profile_sharing import ProfileShareConflict
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.routers.parent_share_grants import (
    get_share_grant_role_reader,
)


class _RoleReader:
    def __init__(self, *, active: bool = True, unavailable: bool = False) -> None:
        self.active = active
        self.unavailable = unavailable

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        if self.unavailable:
            raise ParentRoleStoreUnavailable("db down")
        return self.active


@pytest.fixture
def application(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=str(UUID(int=1)), issuer="contract-test", roles=frozenset()
    )
    app.dependency_overrides[get_share_grant_role_reader] = lambda: _RoleReader(active=True)
    app.dependency_overrides[get_db] = lambda: object()
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize("refused_field", ["SUPPORT_NEEDS", "CONTEXT_ENTRIES", "AGE_MONTHS"])
def test_refused_share_fields_return_400_not_supported(
    application: FastAPI, refused_field: str
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md Checks-Least-privilege (all 3 refused fields -> 400 NOT_SUPPORTED)"""
    with TestClient(application) as client:
        res = client.post(
            "/v1/parent/share-grants",
            json={
                "profile_id": "00000000-0000-0000-0000-000000000001",
                "granted_fields": [refused_field],
            },
            headers={"Idempotency-Key": f"e3-refused-{refused_field}"},
        )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_REQUEST"
    assert res.json()["field_errors"] == [{"field": "granted_fields", "code": "NOT_SUPPORTED"}]


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/v1/parent/share-grants?profile_id=00000000-0000-0000-0000-000000000001&limit=0"),
        ("GET", "/v1/parent/share-grants?profile_id=00000000-0000-0000-0000-000000000001&limit=101"),
        ("GET", "/v1/parent/share-grants?profile_id=00000000-0000-0000-0000-000000000001&limit=abc"),
        ("GET", "/v1/parent/share-grants?profile_id=00000000-0000-0000-0000-000000000001&extra=1"),
        ("GET", "/v1/parent/share-grants/not-a-uuid"),
        ("POST", "/v1/parent/share-grants/not-a-uuid/revoke"),
        ("GET", "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/deliveries?limit=0"),
        ("GET", "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/deliveries?extra=1"),
        ("GET", "/v1/parent/share-grants/not-a-uuid/deliveries"),
    ],
)
def test_parent_share_query_and_uuid_path_faults_are_400_not_422(
    application: FastAPI, method: str, path: str
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-5 (400 not 422 for query/path faults)"""
    headers = (
        {"If-Match": '"1"', "Idempotency-Key": "e3-uuid-fault"} if method == "POST" else {}
    )
    with TestClient(application) as client:
        res = client.request(method, path, headers=headers)
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_REQUEST"


def test_missing_idempotency_key_on_revoke_and_accept_is_400_not_422(
    application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-5 (Idempotency-Key fault on revoke & accept)"""
    monkeypatch.setattr(be1_registry, "_require_profile_teacher", lambda *args, **kwargs: None)
    with TestClient(application) as client:
        revoke_res = client.post(
            "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/revoke",
            headers={"If-Match": '"1"'},
        )
        assert revoke_res.status_code == 400
        assert {"field": "Idempotency-Key", "code": "REQUIRED"} in revoke_res.json()[
            "field_errors"
        ]

        accept_res = client.post(
            "/api/be1/v1/organizations/org-1/classes/class-1/profiles/child-1/parent-share/accept",
            json={"invitation_code": "SyntheticShareCode012345"},
        )
        assert accept_res.status_code == 400
        assert {"field": "Idempotency-Key", "code": "REQUIRED"} in accept_res.json()[
            "field_errors"
        ]


def test_non_active_parent_and_unavailable_role_store_on_parent_routes(
    application: FastAPI,
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-5 & Plan §4 (inactive parent 404, store down 503)"""
    application.dependency_overrides[get_share_grant_role_reader] = lambda: _RoleReader(active=False)
    with TestClient(application) as client:
        not_parent = client.get(
            "/v1/parent/share-grants?profile_id=00000000-0000-0000-0000-000000000001"
        )
        assert not_parent.status_code == 404
        assert not_parent.json()["code"] == "RESOURCE_NOT_FOUND"

    application.dependency_overrides[get_share_grant_role_reader] = lambda: _RoleReader(
        unavailable=True
    )
    with TestClient(application) as client:
        store_down = client.get(
            "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001"
        )
        assert store_down.status_code == 503
        assert store_down.json()["code"] == "DATABASE_UNAVAILABLE"


def test_teacher_accept_validation_headers_and_conflict_codes(
    application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-5 (accept validation, headers, 403/409 codes)"""
    path = "/api/be1/v1/organizations/org-1/classes/class-1/profiles/child-1/parent-share/accept"
    monkeypatch.setattr(be1_registry, "_require_profile_teacher", lambda *args, **kwargs: None)
    with TestClient(application) as client:
        for bad_payload in (
            {"invitation_code": "short"},
            {"invitation_code": "bad!code!0123456789"},
            {"invitation_code": "SyntheticShareCode012345", "extra": 1},
        ):
            bad = client.post(
                path, json=bad_payload, headers={"Idempotency-Key": "e3-accept-bad"}
            )
            assert bad.status_code == 400
            assert bad.json()["code"] == "INVALID_REQUEST"

        now = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
        monkeypatch.setattr(
            be1_registry,
            "accept_teacher_share",
            lambda *args, **kwargs: (
                {
                    "contract": "Be1ParentShareLinkV1",
                    "share_grant_id": uuid4(),
                    "child_id": "child-1",
                    "state": "ACTIVE",
                    "granted_fields": ["DISPLAY_NAME"],
                    "accepted_at": now,
                    "expires_at": now + timedelta(days=90),
                    "revision": 2,
                },
                '"2"',
            ),
        )
        ok = client.post(
            path,
            json={"invitation_code": "SyntheticShareCode012345"},
            headers={"Idempotency-Key": "e3-accept-ok"},
        )
        assert ok.status_code == 200
        assert ok.headers["etag"] == '"2"'
        assert ok.headers["vary"] == "Authorization"

        for conflict_code in (
            "INVITATION_EXPIRED",
            "CONSENT_NOT_EFFECTIVE",
            "RESOURCE_CONFLICT",
            "INVALID_STATE_TRANSITION",
        ):
            monkeypatch.setattr(
                be1_registry,
                "accept_teacher_share",
                lambda *args, _code=conflict_code, **kwargs: (_ for _ in ()).throw(
                    ProfileShareConflict(_code)
                ),
            )
            res = client.post(
                path,
                json={"invitation_code": "SyntheticShareCode012345"},
                headers={"Idempotency-Key": f"e3-accept-{conflict_code}"},
            )
            assert res.status_code == 409
            assert res.json()["code"] == conflict_code

        monkeypatch.setattr(
            be1_registry,
            "_require_profile_teacher",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                HTTPException(status_code=403, detail={"code": "ACTION_NOT_ALLOWED"})
            ),
        )
        forbidden = client.post(
            path,
            json={"invitation_code": "SyntheticShareCode012345"},
            headers={"Idempotency-Key": "e3-accept-403"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ACTION_NOT_ALLOWED"


def test_catalog_and_idempotency_keys_cover_all_three_keyed_share_commands() -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-5 (catalog & idempotency rows for E3)"""
    expected_keyed = {
        ("post", "/v1/parent/share-grants"),
        ("post", "/v1/parent/share-grants/{share_grant_id}/revoke"),
        (
            "post",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}"
            "/profiles/{child_id}/parent-share/accept",
        ),
    }
    assert expected_keyed <= set(IDEMPOTENCY_MISMATCH_OPERATION_KEYS)
    assert expected_keyed <= set(MOUNTED_OPERATIONS)
