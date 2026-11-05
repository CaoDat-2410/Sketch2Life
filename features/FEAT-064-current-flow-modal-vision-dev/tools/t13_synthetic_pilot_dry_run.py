"""Run the T13 synthetic gateway and slow-stub dry run without credentials or a database."""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import os
import socket
import tempfile
import threading
import time
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NoReturn, cast
from unittest.mock import patch
from uuid import uuid4

import uvicorn

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.pilot_assistance as pilot_assistance
from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.assistance import (
    CancelCommand,
    CommandResult,
    SubmitCommand,
)
from sketch2life.contracts.schemas.assistance_requests import AssistanceRequestCommandV1
from sketch2life.domain.assistance import (
    AssistanceRequest,
    DeviceStatus,
    RequestStatus,
    TargetKind,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.app import create_classroom_app
from sketch2life.interfaces.http.be1_runtime import (
    VerifiedDeviceContext,
    VerifiedDeviceStatusContext,
    get_db,
    get_runtime,
    get_verified_adult,
    get_verified_device,
    get_verified_device_status,
)

STUB_DEADLINE_SECONDS = 0.15
STUB_SLOW_RESPONSE_SECONDS = 0.40
_FLOW_STEPS = (
    ("/fixture/organizations", "organization"),
    ("/fixture/classes", "class"),
    ("/fixture/sessions", "session"),
    ("/fixture/synthetic-proof", "synthetic_proof"),
    ("/fixture/canvas/strokes", "accepted_stroke"),
)


@dataclass(slots=True)
class _FixtureState:
    run_id: str
    flow_steps: list[str]
    lock: threading.Lock
    provider_started: threading.Event
    provider_finished: threading.Event
    provider_requests: int = 0
    classroom_route: (
        Callable[[str, str, dict[str, Any], dict[str, str]], tuple[int, dict[str, Any]]]
        | None
    ) = None
    ids: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        self.ids = {
            "organization": f"synthetic_org_{self.run_id}",
            "class": f"synthetic_class_{self.run_id}",
            "session": f"synthetic_session_{self.run_id}",
            "group": f"synthetic_group_{self.run_id}",
            "child": f"synthetic_child_{self.run_id}",
            "grant": f"synthetic_grant_{self.run_id}",
            "assistance": f"assist_{self.run_id}",
            "source": f"synthetic_source_{self.run_id}",
            "turn": f"synthetic_turn_{self.run_id}",
        }

    def handle(
        self,
        method: str,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[int, dict[str, Any]]:
        if path == "/fixture/provider/slow":
            if method != "POST":
                return 405, {"code": "METHOD_NOT_ALLOWED"}
            with self.lock:
                self.provider_requests += 1
            self.provider_started.set()
            time.sleep(STUB_SLOW_RESPONSE_SECONDS)
            self.provider_finished.set()
            return 200, {"accepted": True, "synthetic": True}

        route_step: tuple[str, str, str] | None = None
        if path == "/fixture/assistance/request":
            route_step = (
                "request",
                "POST",
                "/api/be1/v1/assistance-requests",
            )
        elif path == "/fixture/child-status":
            route_step = (
                "child_status",
                "GET",
                "/api/be1/v1/organizations/"
                f"{self.ids['organization']}/sessions/{self.ids['session']}"
                f"/assistance-requests/{self.ids['assistance']}/status",
            )
        elif path == "/fixture/teacher-pending":
            route_step = (
                "teacher_pending",
                "GET",
                "/api/be1/v1/organizations/"
                f"{self.ids['organization']}/sessions/{self.ids['session']}"
                "/teacher/assistance-requests/pending",
            )
        if route_step is not None:
            completed_routes = self.flow_steps[len(_FLOW_STEPS) :]
            expected_routes = ("request", "child_status", "teacher_pending")
            step, forwarded_method, forwarded_path = route_step
            if (
                len(self.flow_steps) < len(_FLOW_STEPS)
                or len(completed_routes) >= len(expected_routes)
                or completed_routes != list(expected_routes[: len(completed_routes)])
                or step != expected_routes[len(completed_routes)]
                or method != forwarded_method
                or self.classroom_route is None
            ):
                return 409, {"code": "SYNTHETIC_FLOW_ORDER_INVALID"}
            forwarded_headers = (
                {
                    "Idempotency-Key": headers["Idempotency-Key"],
                    "Content-Type": "application/json",
                }
                if step == "request" and "Idempotency-Key" in headers
                else {}
            )
            status, response = self.classroom_route(
                forwarded_method,
                forwarded_path,
                body,
                forwarded_headers,
            )
            if status in {200, 202}:
                self.flow_steps.append(step)
            return status, response

        index = len(self.flow_steps)
        if index >= len(_FLOW_STEPS) or path != _FLOW_STEPS[index][0]:
            return 409, {"code": "SYNTHETIC_FLOW_ORDER_INVALID"}
        step = _FLOW_STEPS[index][1]
        expected = {
            "organization": {},
            "class": {"organization_id": self.ids["organization"]},
            "session": {
                "organization_id": self.ids["organization"],
                "class_id": self.ids["class"],
            },
            "synthetic_proof": {"session_id": self.ids["session"]},
            "accepted_stroke": {
                "session_id": self.ids["session"],
                "child_id": self.ids["child"],
                "synthetic_proof_id": f"proof_{self.run_id}",
            },
        }[step]
        if any(body.get(key) != value for key, value in expected.items()):
            return 409, {"code": "SYNTHETIC_FLOW_BINDING_INVALID"}
        self.flow_steps.append(step)
        responses: dict[str, dict[str, Any]] = {
            "organization": {"organization_id": self.ids["organization"]},
            "class": {"class_id": self.ids["class"]},
            "session": {"session_id": self.ids["session"], "state": "active"},
            "synthetic_proof": {
                "proof_id": f"proof_{self.run_id}",
                "child_id": self.ids["child"],
                "purpose_ref": "ai_drawing_assistance",
            },
            "accepted_stroke": {
                "accepted": True,
                "canvas_id": self.ids["group"],
                "document_epoch": 1,
                "document_revision": 1,
                "source_ref": self.ids["source"],
                "source_sha256": "b" * 64,
            },
        }
        return 201 if step != "accepted_stroke" else 200, responses[step]


class _StubHandler(BaseHTTPRequestHandler):
    state: _FixtureState

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            status, result = 400, {"code": "INVALID_STUB_BODY"}
        else:
            status, result = self.state.handle(
                "POST", self.path, body, dict(self.headers.items())
            )
        self._respond(status, result)

    def do_GET(self) -> None:
        status, result = self.state.handle(
            "GET", self.path, {}, dict(self.headers.items())
        )
        self._respond(status, result)

    def _respond(self, status: int, result: dict[str, Any]) -> None:
        payload = json.dumps(result, separators=(",", ":")).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except OSError:
            # The deliberately late provider response is discarded after client timeout.
            pass

    def log_message(self, _format: str, *_args: object) -> None:
        return


class _LoopbackServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class _LoopbackAsgiServer:
    def __init__(self, application: Any) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(16)
        listener.setblocking(False)
        host, port = listener.getsockname()[:2]
        self.host = str(host)
        self.port = int(port)
        self._listener = listener
        self._server = uvicorn.Server(
            uvicorn.Config(
                application,
                host=self.host,
                port=self.port,
                log_config=None,
                log_level="critical",
                access_log=False,
            )
        )
        self._thread = threading.Thread(
            target=self._server.run,
            kwargs={"sockets": [self._listener]},
            daemon=True,
        )

    def start(self) -> None:
        if not ipaddress.ip_address(self.host).is_loopback:
            raise RuntimeError("T13 classroom server is restricted to loopback")
        self._thread.start()
        deadline = time.monotonic() + 2.0
        while not self._server.started and self._thread.is_alive():
            if time.monotonic() >= deadline:
                self.stop()
                raise RuntimeError("T13 classroom loopback server did not start")
            time.sleep(0.01)
        if not self._server.started:
            self.stop()
            raise RuntimeError("T13 classroom loopback server stopped before startup")

    def stop(self) -> None:
        if self._thread.is_alive():
            self._server.should_exit = True
            self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            self._server.force_exit = True
            self._thread.join(timeout=2.0)
        self._listener.close()


class _DryRunRequest:
    def __init__(self, state: _FixtureState, principal_id: str, command: Any) -> None:
        assert state.ids is not None
        self.assistance_id = state.ids["assistance"]
        self.request_revision = 1
        self.job_id = None
        self.status = RequestStatus.SCHEDULED
        self.facts = SimpleNamespace(
            organization_id=state.ids["organization"],
            session_id=state.ids["session"],
            group_id=state.ids["group"],
            canvas_id=state.ids["group"],
            target=SimpleNamespace(kind=TargetKind.INDIVIDUAL, ref_id=state.ids["child"]),
        )
        self.requester = SimpleNamespace(principal_id=principal_id)
        self.requested_level = command.requested_level
        self.request_reason = command.request_reason
        self.created_at = datetime.now(UTC)

    def device_status(self) -> DeviceStatus:
        return DeviceStatus.PENDING

    def etag(self) -> str:
        return f'"assistance:{self.assistance_id}:{self.request_revision}"'


class _DryRunAssistanceService:
    poll_after_ms = 2000

    def __init__(self, state: _FixtureState, record: dict[str, Any]) -> None:
        self._state = state
        self._record = record
        self.context_revision: int | None = None

    def submit(self, command: SubmitCommand) -> CommandResult:
        self.context_revision = command.context_revision
        assert command.checkpoint_ref.checkpoint_id == self._state.ids["source"]
        assert command.checkpoint_ref.hash == "b" * 64
        assert command.checkpoint_ref.server_sequence == 1
        request = _DryRunRequest(
            self._state,
            command.principal.principal_id,
            command,
        )
        self._record["request"] = request
        return CommandResult(
            cast(AssistanceRequest, request), ReceiptOutcome.CREATED, False
        )

    def cancel(self, _command: CancelCommand) -> NoReturn:
        raise AssertionError("The T13 flow does not issue a cancel command")


class _DryRunOwner:
    def __init__(self, context_revision: int) -> None:
        self._context_revision = context_revision

    def canvas(
        self, _organization_id: str, _canvas_id: str
    ) -> SimpleNamespace:
        return SimpleNamespace(context_revision=self._context_revision)


def _post_json(
    host: str,
    port: int,
    path: str,
    body: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    status, result = _request_json(
        host,
        port,
        "POST",
        path,
        body,
        {"Content-Type": "application/json", **(headers or {})},
    )
    if status >= 400:
        raise RuntimeError(f"T13 loopback fixture rejected a synthetic step (HTTP {status})")
    return result


def _get_json(host: str, port: int, path: str) -> dict[str, Any]:
    status, result = _request_json(host, port, "GET", path, {}, {})
    if status >= 400:
        raise RuntimeError(f"T13 loopback fixture rejected a synthetic step (HTTP {status})")
    return result


def _request_json(
    host: str,
    port: int,
    method: str,
    path: str,
    body: dict[str, Any],
    headers: dict[str, str],
) -> tuple[int, dict[str, Any]]:
    if not ipaddress.ip_address(host).is_loopback:
        raise RuntimeError("T13 HTTP calls are restricted to loopback")
    connection = http.client.HTTPConnection(host, port, timeout=2.0)
    try:
        encoded = (
            json.dumps(body, separators=(",", ":")).encode("utf-8")
            if method == "POST"
            else None
        )
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        result = json.loads(response.read())
        if not isinstance(result, dict):
            raise RuntimeError("T13 loopback server returned a non-object response")
        return response.status, result
    finally:
        connection.close()


def _invoke_slow_stub_once(host: str, port: int, payload: dict[str, Any]) -> str:
    if not ipaddress.ip_address(host).is_loopback:
        raise RuntimeError("T13 provider stub is restricted to loopback")
    connection = http.client.HTTPConnection(
        host,
        port,
        timeout=STUB_DEADLINE_SECONDS,
    )
    try:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        connection.request(
            "POST",
            "/fixture/provider/slow",
            body=encoded,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        response.read()
        return "known_response"
    except (TimeoutError, OSError):
        return "unknown"
    finally:
        connection.close()


def run_dry_run(
    *,
    provider_url_file: Path | None = None,
    provider_token_file: Path | None = None,
) -> dict[str, Any]:
    """Exercise synthetic BE1 steps, actual T9 HTTP routes, and one slow loopback send."""
    for candidate in (provider_url_file, provider_token_file):
        if candidate is not None and not isinstance(candidate, Path):
            raise TypeError("provider URL/token inputs must be file paths")
    if os.environ.get("OWNER_MODAL_CALL_APPROVED", "NO").strip().upper() != "NO":
        raise RuntimeError("T13 dry-run requires OWNER_MODAL_CALL_APPROVED=NO")

    run_id = uuid4().hex
    state = _FixtureState(
        run_id=run_id,
        flow_steps=[],
        lock=threading.Lock(),
        provider_started=threading.Event(),
        provider_finished=threading.Event(),
    )
    handler = type("T13StubHandler", (_StubHandler,), {"state": state})
    server = _LoopbackServer(("127.0.0.1", 0), handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    host, port = server.server_address[:2]
    host = str(host)
    port = int(port)
    record: dict[str, Any] = {}
    try:
        assert state.ids is not None
        organization = _post_json(host, port, _FLOW_STEPS[0][0], {})
        classroom = _post_json(
            host,
            port,
            _FLOW_STEPS[1][0],
            {"organization_id": organization["organization_id"]},
        )
        session = _post_json(
            host,
            port,
            _FLOW_STEPS[2][0],
            {
                "organization_id": organization["organization_id"],
                "class_id": classroom["class_id"],
            },
        )
        proof = _post_json(
            host,
            port,
            _FLOW_STEPS[3][0],
            {"session_id": session["session_id"], "child_id": state.ids["child"]},
        )
        stroke = _post_json(
            host,
            port,
            _FLOW_STEPS[4][0],
            {
                "session_id": session["session_id"],
                "child_id": proof["child_id"],
                "synthetic_proof_id": proof["proof_id"],
                "operation_id": f"stroke_{run_id}",
            },
        )

        checkpoint = {
            "checkpoint_id": stroke["source_ref"],
            "document_epoch": stroke["document_epoch"],
            "server_sequence": stroke["document_revision"],
            "hash": stroke["source_sha256"],
        }
        command = {
            "canvas_id": stroke["canvas_id"],
            "checkpoint_ref": checkpoint,
            "target_scope": {"kind": "individual", "participant_id": proof["child_id"]},
            "target_region_id": "region_fx_open",
            "requested_level": "level_fx_1",
            "child_intent": "Please help with this synthetic drawing.",
            "request_reason": "child_request",
            "context_revision": 1,
            "client_request_id": f"client_{run_id}",
        }
        AssistanceRequestCommandV1.model_validate(command)

        local_settings = Settings(
            env="local",
            synthetic_pilot_enabled=True,
            ai_provider="disabled",
            be1_artifact_root=Path(tempfile.gettempdir()) / f"s2l-t13-{run_id}",
            _env_file=None,  # type: ignore[call-arg]
        )
        with (
            patch.object(app_module, "get_settings", return_value=local_settings),
            patch.object(
                runtime_module,
                "get_core_database_settings",
                return_value=SimpleNamespace(database_url=None),
            ),
        ):
            application = create_classroom_app()
        runtime = replace(
            application.state.be1_runtime,
            settings=local_settings,
            engine=_NoDatabaseEngine(),
            database_error=None,
            pilot_vision=SimpleNamespace(),
            pilot_job_repository=None,
        )
        application.state.be1_runtime = runtime

        principal_id = f"device:{state.ids['grant']}"
        device_context = VerifiedDeviceContext(
            principal=cast(Any, SimpleNamespace(principal_id=principal_id)),
            grant=cast(Any, SimpleNamespace(grant_id=state.ids["grant"])),
            session=cast(
                Any,
                SimpleNamespace(
                    organization_id=state.ids["organization"],
                    class_id=state.ids["class"],
                    session_id=state.ids["session"],
                ),
            ),
            membership=cast(
                Any,
                SimpleNamespace(
                    child_id=state.ids["child"],
                    group_id=state.ids["group"],
                ),
            ),
            turn=cast(
                Any,
                SimpleNamespace(
                    canvas_id=state.ids["group"],
                    turn_id=state.ids["turn"],
                    revision=1,
                    document_epoch=1,
                ),
            ),
            scope=cast(Any, SimpleNamespace()),
        )
        device_status_context = VerifiedDeviceStatusContext(
            grant=cast(
                Any,
                SimpleNamespace(
                    grant_id=state.ids["grant"],
                    organization_id=state.ids["organization"],
                    session_id=state.ids["session"],
                ),
            ),
            session=cast(Any, SimpleNamespace(state="paused")),
            membership=cast(
                Any,
                SimpleNamespace(
                    child_id=state.ids["child"],
                    group_id=state.ids["group"],
                ),
            ),
        )
        service = _DryRunAssistanceService(state, record)
        binding = SimpleNamespace(
            owner=_DryRunOwner(context_revision=41),
            service=service,
        )
        application.dependency_overrides[get_runtime] = lambda: runtime
        application.dependency_overrides[get_verified_device] = lambda: device_context
        application.dependency_overrides[get_verified_device_status] = (
            lambda: device_status_context
        )
        application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
            subject=f"synthetic_teacher_{run_id}",
            issuer="t13-synthetic-fixture",
            roles=frozenset({"teacher"}),
        )
        application.dependency_overrides[get_db] = lambda: object()

        def assigned_session(
            _db: object, organization_id: str, session_id: str
        ) -> SimpleNamespace:
            assert organization_id == state.ids["organization"]
            assert session_id == state.ids["session"]
            return SimpleNamespace(class_id=state.ids["class"], state="paused")

        def assigned_teacher(
            _db: object,
            principal: VerifiedPrincipal,
            organization_id: str,
            **kwargs: Any,
        ) -> tuple[SimpleNamespace, ...]:
            assert principal.subject == f"synthetic_teacher_{run_id}"
            assert organization_id == state.ids["organization"]
            assert kwargs["class_id"] == state.ids["class"]
            assert kwargs["roles"] == {"school_admin", "teacher"}
            return (SimpleNamespace(assignment_id=f"assignment_{run_id}"),)

        def read_request(*_args: object) -> Any:
            return record.get("request")

        def read_requests(*_args: object) -> tuple[Any, ...]:
            return (record["request"],)

        with (
            patch.object(pilot_assistance, "_build_child_binding", return_value=binding),
            patch.object(pilot_assistance, "_read_request", side_effect=read_request),
            patch.object(pilot_assistance, "_read_requests", side_effect=read_requests),
            patch.object(pilot_assistance, "get_session", side_effect=assigned_session),
            patch.object(pilot_assistance, "require_assignment", side_effect=assigned_teacher),
        ):
            classroom_server = _LoopbackAsgiServer(application)
            classroom_server.start()
            try:
                def forward_classroom_route(
                    method: str,
                    path: str,
                    body: dict[str, Any],
                    headers: dict[str, str],
                ) -> tuple[int, dict[str, Any]]:
                    return _request_json(
                        classroom_server.host,
                        classroom_server.port,
                        method,
                        path,
                        body,
                        headers,
                    )

                state.classroom_route = forward_classroom_route
                try:
                    _post_json(
                        host,
                        port,
                        "/fixture/assistance/request",
                        command,
                        headers={"Idempotency-Key": f"request_{run_id}"},
                    )
                    child_status = _get_json(host, port, "/fixture/child-status")
                    teacher_pending = _get_json(host, port, "/fixture/teacher-pending")
                finally:
                    state.classroom_route = None
            finally:
                classroom_server.stop()
        application.dependency_overrides.clear()

        if service.context_revision != 41 or not stroke["accepted"]:
            raise RuntimeError("T13 request did not use server-owned source context")
        if child_status["processing_state"] != "unknown":
            raise RuntimeError("T13 unknown job evidence did not fail closed")
        if teacher_pending["items"][0]["processing_state"] != "unknown":
            raise RuntimeError("T13 teacher projection did not fail closed")

        provider_outcome = _invoke_slow_stub_once(
            host,
            port,
            {"request_id": state.ids["assistance"], "synthetic": True},
        )
        if not state.provider_started.wait(timeout=1.0):
            raise RuntimeError("T13 slow stub did not receive the single request")
        if not state.provider_finished.wait(timeout=2.0):
            raise RuntimeError("T13 slow stub did not finish its late response")
        with state.lock:
            provider_requests = state.provider_requests
        if provider_outcome != "unknown" or provider_requests != 1:
            raise RuntimeError("T13 slow response did not remain UNKNOWN after one send")
        expected_flow_steps = [
            *(name for _path, name in _FLOW_STEPS),
            "request",
            "child_status",
            "teacher_pending",
        ]
        if state.flow_steps != expected_flow_steps:
            raise RuntimeError("T13 synthetic BE1 flow was incomplete")

        return {
            "result": "PASS",
            "run_id": run_id,
            "flow_steps": list(state.flow_steps),
            "context_revision_used": service.context_revision,
            "child_processing_state": child_status["processing_state"],
            "teacher_processing_state": teacher_pending["items"][0]["processing_state"],
            "provider_outcome": provider_outcome,
            "provider_stub_requests": provider_requests,
            "external_requests": 0,
            "provider_token_read": False,
            "provider_url_file_supplied": provider_url_file is not None,
            "provider_token_file_supplied": provider_token_file is not None,
            "owner_modal_call_approved": "NO",
            "stub_deadline_seconds": STUB_DEADLINE_SECONDS,
            "slow_response_seconds": STUB_SLOW_RESPONSE_SECONDS,
        }
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2.0)


class _NoDatabaseEngine:
    def connect(self) -> AbstractContextManager[object]:
        return nullcontext(object())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-url-file", type=Path, default=None)
    parser.add_argument("--provider-token-file", type=Path, default=None)
    arguments = parser.parse_args(argv)
    summary = run_dry_run(
        provider_url_file=arguments.provider_url_file,
        provider_token_file=arguments.provider_token_file,
    )
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
