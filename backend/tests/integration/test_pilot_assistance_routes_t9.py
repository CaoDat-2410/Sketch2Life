from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.routers.pilot_assistance as pilot_assistance
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.assistance import AssistanceError
from sketch2life.contracts.schemas.assistance_requests import AssistanceRequestCommandV1
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.assistance import RequestStatus, TargetKind
from sketch2life.domain.vision_analysis import VISION_ANALYSIS_JOB_TYPE
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.app import create_classroom_app
from sketch2life.interfaces.http.be1_runtime import (
    VerifiedDeviceStatusContext,
    get_db,
    get_runtime,
    get_verified_adult,
    get_verified_device,
    get_verified_device_status,
)

ORG_ID = "synthetic-org-064"
SESSION_ID = "synthetic-session-064"
GROUP_ID = "synthetic-group-064"
CHILD_ID = "synthetic-child-064"
GRANT_ID = "synthetic-grant-064"
ASSISTANCE_ID = "assist_synthetic_064"


class _JobUnitOfWork:
    def __init__(self, job: SimpleNamespace | None) -> None:
        self.job = job
        self.completion_reads = 0

    def get_job(self, job_id: str) -> SimpleNamespace | None:
        return self.job if self.job is not None and self.job.job_id == job_id else None

    def get_completion_receipt(self, job_id: str, attempt_id: str) -> None:
        del job_id, attempt_id
        self.completion_reads += 1
        return None


class _JobRepository:
    def __init__(self, uow: _JobUnitOfWork) -> None:
        self.uow = uow

    @contextmanager
    def transaction(self) -> Iterator[_JobUnitOfWork]:
        yield self.uow


class _ExplodingAnalysisRepository:
    def __init__(self) -> None:
        self.read_count = 0
        self.orphan_analysis_head = SimpleNamespace(
            analysis_id="analysis_synthetic_064",
            job_id="job_synthetic_064",
            attempt_id="attempt_synthetic_064",
            model_output="synthetic-private-model-output",
        )
        self.succeeded_invocation = SimpleNamespace(
            job_id="job_synthetic_064",
            attempt_id="attempt_synthetic_064",
            state="SUCCEEDED",
        )

    def transaction(self) -> None:
        self.read_count += 1
        raise AssertionError("T9 projection must not read analysis rows")


class _FakeEngine:
    def connect(self) -> Any:
        return nullcontext(object())


class _CapturingAssistanceService:
    poll_after_ms = 2000

    def __init__(self) -> None:
        self.submitted: list[Any] = []
        self.cancelled: list[Any] = []

    def submit(self, command: Any) -> None:
        self.submitted.append(command)
        raise AssistanceError("STALE_CONTEXT", current_revision=command.context_revision)

    def cancel(self, command: Any) -> None:
        self.cancelled.append(command)
        raise AssistanceError("INVALID_STATE")


class _FakeOwner:
    def canvas(self, organization_id: str, canvas_id: str) -> SimpleNamespace:
        assert organization_id == ORG_ID
        assert canvas_id == GROUP_ID
        return SimpleNamespace(context_revision=777)


def _runtime(repository: _JobRepository | None = None) -> SimpleNamespace:
    settings = Settings(
        env="test",
        synthetic_pilot_enabled=True,
        _env_file=None,  # type: ignore[call-arg]
    )
    vision = SimpleNamespace(analysis_repository=_ExplodingAnalysisRepository())
    return SimpleNamespace(
        settings=settings,
        pilot_vision=vision,
        pilot_job_repository=repository,
        engine=_FakeEngine(),
        artifact_store=SimpleNamespace(get=lambda _ref: None),
    )


def _request(
    *, status: RequestStatus = RequestStatus.ANALYSIS_READY, child_id: str = CHILD_ID
) -> SimpleNamespace:
    now = datetime.now(UTC)
    facts = SimpleNamespace(
        organization_id=ORG_ID,
        session_id=SESSION_ID,
        group_id=GROUP_ID,
        canvas_id=GROUP_ID,
        target=SimpleNamespace(kind=TargetKind.INDIVIDUAL, ref_id=child_id),
    )
    return SimpleNamespace(
        assistance_id=ASSISTANCE_ID,
        request_revision=3,
        job_id="job_synthetic_064",
        status=status,
        facts=facts,
        requester=SimpleNamespace(principal_id=f"device:{GRANT_ID}"),
        requested_level="level_fx_1",
        request_reason="child_request",
        created_at=now,
    )


def _p3_running_job() -> SimpleNamespace:
    request_ref = SimpleNamespace(request_id=ASSISTANCE_ID, request_revision=3)
    attempt = SimpleNamespace(
        attempt_id="attempt_synthetic_064",
        request_ref=request_ref,
        # The orphan invocation says succeeded while the owner job remains RUNNING.
        outcome="succeeded:accepted",
    )
    return SimpleNamespace(
        job_id="job_synthetic_064",
        organization_id=ORG_ID,
        job_type=VISION_ANALYSIS_JOB_TYPE,
        scope=SimpleNamespace(session_id=SESSION_ID, target_id=ASSISTANCE_ID),
        active_attempt=attempt,
        state=JobState.RUNNING,
        result_disposition=None,
        result_refs=(),
        completed_at=None,
    )


def _status_context(session_state: str = "paused") -> VerifiedDeviceStatusContext:
    return VerifiedDeviceStatusContext(
        grant=cast(
            Any,
            SimpleNamespace(
                grant_id=GRANT_ID,
                organization_id=ORG_ID,
                session_id=SESSION_ID,
            ),
        ),
        session=cast(Any, SimpleNamespace(state=session_state)),
        membership=cast(Any, SimpleNamespace(child_id=CHILD_ID, group_id=GROUP_ID)),
    )


def _settings_override(runtime: SimpleNamespace) -> Callable[[], SimpleNamespace]:
    return lambda: runtime


def test_t9_mounts_exactly_four_assistance_operations_and_no_decision_route() -> None:
    application = create_classroom_app()
    application.openapi()
    paths = application.state.runtime_openapi_schema["paths"]
    routes = {
        (method.upper(), path)
        for path, path_item in paths.items()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    expected = {
        ("POST", "/api/be1/v1/assistance-requests"),
        ("POST", "/api/be1/v1/assistance-requests/{assistance_id}/cancel"),
        (
            "GET",
            "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status",
        ),
        (
            "GET",
            "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending",
        ),
    }

    assert {item for item in routes if item[1] in {path for _, path in expected}} == expected
    assert not any("approve" in path or "reject" in path for _, path in routes)
    assert {status.value for status in RequestStatus} == {
        "scheduling",
        "scheduled",
        "analysis_ready",
        "failed",
        "cancelled",
        "stale",
    }


def test_child_commands_use_verified_device_and_server_owned_context_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = create_classroom_app()
    runtime = _runtime()
    context = SimpleNamespace(
        principal=SimpleNamespace(principal_id=f"device:{GRANT_ID}"),
        session=SimpleNamespace(
            organization_id=ORG_ID,
            class_id="synthetic-class-064",
            session_id=SESSION_ID,
        ),
        membership=SimpleNamespace(child_id=CHILD_ID, group_id=GROUP_ID),
        turn=SimpleNamespace(
            canvas_id=GROUP_ID,
            turn_id="turn_synthetic_064",
            revision=4,
            document_epoch=1,
        ),
    )
    from sketch2life.interfaces.http.be1_runtime import VerifiedDeviceContext

    verified_context = VerifiedDeviceContext(
        principal=context.principal,
        grant=cast(Any, SimpleNamespace(grant_id=GRANT_ID)),
        session=context.session,
        membership=context.membership,
        turn=context.turn,
        scope=cast(Any, SimpleNamespace()),
    )
    service = _CapturingAssistanceService()
    monkeypatch.setattr(
        pilot_assistance,
        "_build_child_binding",
        lambda _runtime, _context, _connection: pilot_assistance._ChildAssistanceBinding(
            cast(Any, _FakeOwner()), cast(Any, service)
        ),
    )
    application.dependency_overrides[get_runtime] = _settings_override(runtime)
    application.dependency_overrides[get_verified_device] = lambda: verified_context

    command = {
        "canvas_id": GROUP_ID,
        "checkpoint_ref": {
            "checkpoint_id": "source_synthetic_064",
            "document_epoch": 1,
            "server_sequence": 8,
            "hash": "a" * 64,
        },
        "target_scope": {"kind": "individual", "participant_id": CHILD_ID},
        "target_region_id": "region_fx_open",
        "requested_level": "level_fx_1",
        "child_intent": "Please help me think.",
        "request_reason": "child_request",
        "context_revision": 1,
        "client_request_id": "client_synthetic_064",
    }
    with TestClient(application) as client:
        submitted = client.post(
            "/api/be1/v1/assistance-requests",
            headers={"Idempotency-Key": "request_synthetic_064"},
            json=command,
        )
        cancelled = client.post(
            f"/api/be1/v1/assistance-requests/{ASSISTANCE_ID}/cancel",
            headers={
                "Idempotency-Key": "cancel_synthetic_064",
                "If-Match": '"assistance:assist_synthetic_064:3"',
            },
            json={"reason": "child stopped"},
        )

    assert submitted.status_code == 409
    assert service.submitted[0].context_revision == 777
    assert service.submitted[0].principal.principal_id == f"device:{GRANT_ID}"
    assert cancelled.status_code == 409
    assert service.cancelled[0].principal.principal_id == f"device:{GRANT_ID}"
    assert AssistanceRequestCommandV1.model_validate(command).context_revision == 1


@pytest.mark.parametrize("session_state", ["active", "paused"])
def test_child_status_and_teacher_pending_fail_closed_on_b1_p3_orphan_without_analysis_reads(
    monkeypatch: pytest.MonkeyPatch,
    session_state: str,
) -> None:
    application = create_classroom_app()
    analysis_store = _ExplodingAnalysisRepository()
    job_uow = _JobUnitOfWork(_p3_running_job())
    runtime = _runtime(_JobRepository(job_uow))
    runtime.pilot_vision.analysis_repository = analysis_store
    request = _request()
    monkeypatch.setattr(pilot_assistance, "_read_request", lambda *_args: request)
    monkeypatch.setattr(pilot_assistance, "_read_requests", lambda *_args: (request,))
    monkeypatch.setattr(
        pilot_assistance,
        "get_session",
        lambda *_args: SimpleNamespace(
            class_id="synthetic-class-064", state=session_state
        ),
    )
    assignments: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    monkeypatch.setattr(
        pilot_assistance,
        "require_assignment",
        lambda *args, **kwargs: assignments.append((args, kwargs)),
    )
    application.dependency_overrides[get_runtime] = _settings_override(runtime)
    application.dependency_overrides[get_verified_device_status] = lambda: _status_context(
        session_state
    )
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject="synthetic-teacher-064",
        issuer="test-issuer",
        roles=frozenset({"teacher"}),
    )
    application.dependency_overrides[get_db] = lambda: object()

    with TestClient(application) as client:
        child = client.get(
            f"/api/be1/v1/organizations/{ORG_ID}/sessions/{SESSION_ID}/assistance-requests/{ASSISTANCE_ID}/status"
        )
        teacher = client.get(
            f"/api/be1/v1/organizations/{ORG_ID}/sessions/{SESSION_ID}/teacher/assistance-requests/pending"
        )

    assert child.status_code == 200
    child_body = child.json()
    assert child_body["status"] == "pending"
    assert child_body["processing_state"] == "processing"
    assert "accepted" not in child.text and "result_refs" not in child.text
    assert "synthetic-private-model-output" not in child.text
    assert teacher.status_code == 200
    teacher_item = teacher.json()["items"][0]
    assert teacher_item["processing_state"] == "processing"
    assert "analysis_id" not in teacher.text
    assert "input_hash" not in teacher.text
    assert "child_intent" not in teacher.text
    assert "synthetic-private-model-output" not in teacher.text
    assert analysis_store.orphan_analysis_head.job_id == "job_synthetic_064"
    assert analysis_store.succeeded_invocation.state == "SUCCEEDED"
    assert assignments and assignments[0][1]["roles"] == {"school_admin", "teacher"}
    assert job_uow.completion_reads == 2
    assert analysis_store.read_count == 0


def test_child_status_is_bound_to_own_child_request(monkeypatch: pytest.MonkeyPatch) -> None:
    application = create_classroom_app()
    runtime = _runtime()
    monkeypatch.setattr(
        pilot_assistance,
        "_read_request",
        lambda *_args: _request(child_id="other-child"),
    )
    application.dependency_overrides[get_runtime] = _settings_override(runtime)
    application.dependency_overrides[get_verified_device_status] = _status_context

    with TestClient(application) as client:
        response = client.get(
            f"/api/be1/v1/organizations/{ORG_ID}/sessions/{SESSION_ID}/assistance-requests/{ASSISTANCE_ID}/status"
        )

    assert response.status_code == 404
