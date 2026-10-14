"""CMD-44 polling through the isolated fixture app (BE2-01 Phase A; fakes only)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sketch2life.application.services.ai_jobs import FIXTURE_POLL_POLICY
from sketch2life.contracts.schemas.ai_jobs import (
    AsyncJobChildEnvelopeV1,
    AsyncJobEnvelopeV1,
    CollaborationErrorV1,
)
from sketch2life.infrastructure.ai_jobs.harness import (
    ADMIN,
    DEVICE,
    OUTSIDER,
    TEACHER,
    UNGRANTED,
    FixtureHarness,
    build_fixture_harness,
)
from sketch2life.interfaces.http.ai_jobs_fixture_app import (
    create_ai_jobs_fixture_app,
    route_surface,
)

PREFIX = "/api/collaboration/v1"
FIXTURE_PRINCIPALS = {"teacher": TEACHER, "admin": ADMIN, "device": DEVICE, "outsider": OUTSIDER,
          "ungranted": UNGRANTED}


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


@pytest.fixture
def client(h: FixtureHarness) -> TestClient:
    return TestClient(create_ai_jobs_fixture_app(h.service, FIXTURE_PRINCIPALS))


def get(client: TestClient, job_id: str, who: str | None = "teacher", **headers: str):  # type: ignore[no-untyped-def]
    if who is not None:
        headers["Authorization"] = f"Fixture {who}"
    return client.get(f"{PREFIX}/jobs/{job_id}", headers=headers)


def succeeded_job(h: FixtureHarness) -> str:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(job_id), h.success_claim(message))
    return job_id


def assert_error(response, status: int, code: str) -> None:  # type: ignore[no-untyped-def]
    assert response.status_code == status
    body = CollaborationErrorV1.model_validate(response.json(), strict=False)
    assert body.error.code == code
    assert "job_fx" not in body.error.message and "artifact" not in response.text


def test_unauthenticated_and_malformed_requests(client: TestClient, h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    assert_error(get(client, job_id, who=None), 401, "UNAUTHENTICATED")
    assert_error(get(client, job_id, who="unknown-token"), 401, "UNAUTHENTICATED")
    assert_error(get(client, "bad id!"), 400, "MALFORMED_REQUEST")


@pytest.mark.parametrize("who", ["outsider", "ungranted"])
def test_out_of_scope_poll_is_indistinguishable_from_missing(
    client: TestClient, h: FixtureHarness, who: str
) -> None:
    job_id = succeeded_job(h)
    denied = get(client, job_id, who=who)
    missing = get(client, "job_fx9999", who=who)
    assert_error(denied, 404, "RESOURCE_NOT_FOUND")
    assert denied.json()["error"] == missing.json()["error"]
    assert "ETag" not in denied.headers


def test_teacher_projection_envelope_headers_and_exact_refs(
    client: TestClient, h: FixtureHarness
) -> None:
    job_id = succeeded_job(h)
    response = get(client, job_id, **{"X-Correlation-Id": "corr_fx_test"})
    assert response.status_code == 200
    body = AsyncJobEnvelopeV1.model_validate(response.json(), strict=False)
    assert body.correlation_id == "corr_fx_test" and body.meta.projection == "teacher"
    assert body.data.state == "succeeded" and body.data.result_disposition == "accepted"
    assert len(body.data.result_refs) == 1 and body.data.poll_after_ms is None
    assert response.headers["ETag"].startswith(f'"job:{job_id}:{body.data.job_revision}:')
    assert response.headers["Cache-Control"] == "private, no-cache"
    assert "Authorization" in response.headers["Vary"]


def test_admin_and_device_projections_withhold_results(
    client: TestClient, h: FixtureHarness
) -> None:
    job_id = succeeded_job(h)
    admin = AsyncJobEnvelopeV1.model_validate(get(client, job_id, who="admin").json(),
                                              strict=False)
    assert admin.meta.projection == "admin" and admin.data.result_refs == ()
    raw = get(client, job_id, who="device").json()
    device = AsyncJobChildEnvelopeV1.model_validate(raw, strict=False)
    assert device.contract_name == "AsyncJobChildView"
    assert not {"result_refs", "request_ref", "result_disposition", "attempt_id",
                "organization_id"} & set(raw["data"])


def test_conditional_poll_returns_304_only_while_authorized_and_unchanged(
    client: TestClient, h: FixtureHarness
) -> None:
    job_id = succeeded_job(h)
    first = get(client, job_id)
    etag = first.headers["ETag"]
    cached = get(client, job_id, **{"If-None-Match": etag})
    assert cached.status_code == 304 and cached.content == b""
    h.eligibility.revoked_subjects.add("child_fx_001")
    after_consent = get(client, job_id, **{"If-None-Match": etag})
    assert after_consent.status_code == 200
    assert after_consent.headers["ETag"] != etag
    assert after_consent.json()["data"]["result_refs"] == []
    h.authorization.revoke(TEACHER.principal_id)
    assert_error(get(client, job_id, **{"If-None-Match": etag}), 404, "RESOURCE_NOT_FOUND")


def test_etag_changes_with_job_revision(client: TestClient, h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    queued = get(client, job_id)
    assert queued.json()["data"]["poll_after_ms"] == FIXTURE_POLL_POLICY.min_interval_ms
    h.start_next()
    running = get(client, job_id, **{"If-None-Match": queued.headers["ETag"]})
    assert running.status_code == 200 and running.json()["data"]["state"] == "running"
    assert running.json()["data"]["progress"] == {"kind": "unknown", "value": None,
                                                  "stage_label": None}
    h.clock.advance(seconds=3600)
    assert get(client, job_id).json()["data"]["poll_after_ms"] == (
        FIXTURE_POLL_POLICY.max_interval_ms
    )


def test_pending_child_poll_never_returns_result_or_internal_refs(
    client: TestClient, h: FixtureHarness
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    pending = get(client, job_id, who="device").json()
    assert pending["data"]["state"] == "running"
    h.service.accept_completion(h.capability(job_id), h.success_claim(message))
    done = get(client, job_id, who="device")
    assert "artifact_fx" not in done.text and "input_hash" not in done.text


def test_fixture_app_exposes_only_get_and_no_completion_route(
    client: TestClient, h: FixtureHarness
) -> None:
    job_id = succeeded_job(h)
    surface = route_surface(client.app.routes)  # type: ignore[attr-defined]
    assert surface == {(f"{PREFIX}/jobs/{{job_id}}", "GET")}
    for path in (f"{PREFIX}/jobs/{job_id}", f"{PREFIX}/jobs/{job_id}/completion"):
        response = client.post(path, headers={"Authorization": "Fixture teacher"}, json={})
        assert response.status_code in {404, 405}


def test_live_app_source_does_not_import_fixture_composition() -> None:
    app_source = Path(__file__).resolve().parents[2] / "src/sketch2life/interfaces/http/app.py"
    tree = ast.parse(app_source.read_text(encoding="utf-8"))
    imported = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    } | {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
         for alias in node.names}
    assert not {m for m in imported if "ai_jobs" in m}
    assert "Fixture " not in app_source.read_text(encoding="utf-8")


def test_live_app_routes_have_no_candidate_job_route() -> None:
    pytest.importorskip("PIL", reason="live app import needs Pillow (not in this env)")
    from sketch2life.interfaces.http.app import create_app

    live = route_surface(create_app().routes)
    assert live, "route walk found no live routes"
    assert not any(path.endswith("/jobs/{job_id}") and "collaboration" in path
                   for path, _ in live)
