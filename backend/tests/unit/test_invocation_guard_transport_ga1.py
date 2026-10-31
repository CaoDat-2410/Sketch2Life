from __future__ import annotations

import json
import socket
import ssl
import threading
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sketch2life.application.ports.vision_analysis import (
    ObservationFailed,
    ObservationFailureCode,
    ObservationRequest,
    ObservationSucceeded,
    ProviderContextMode,
)
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.contracts.schemas.analysis_results import ProvenanceV1
from sketch2life.contracts.schemas.vision import VISION_POLICY_MATCH_VIEW_VERSION, VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.domain.vision_analysis import EvidenceKind
from sketch2life.infrastructure.ai.vision_lexical_policy import synthetic_prohibited_lexicon
from sketch2life.infrastructure.vision_analysis.harness import (
    ORG,
    AnalysisHarness,
    build_analysis_harness,
    synthetic_v2_response,
)
from sketch2life.infrastructure.vision_analysis.invocation_guard import (
    InvocationGuardedVisionObservationPort,
    InvocationLedgerGuard,
)
from sketch2life.infrastructure.vision_analysis.ledger import InvocationRecord, InvocationState
from sketch2life.infrastructure.vision_analysis.legacy_v2 import LegacyVisionV2Bridge
from sketch2life.infrastructure.vision_analysis.pilot_policy import PILOT_VISION_RETRY_POLICY
from sketch2life.infrastructure.vision_analysis.transport import (
    _PROCESS_RESOLVER_POOL,
    HttpJsonTransport,
)


class MemoryInvocationLedger:
    """Thread-safe ledger double; stores only invocation identity/state and result hash."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, InvocationRecord] = {}
        self.raise_on_claim = False
        self.fail_complete = False

    def claim(self, *, run_id: str, job_id: str, attempt_id: str, organization_id: str) -> bool:
        with self._lock:
            if self.raise_on_claim:
                raise RuntimeError("ledger unavailable")
            if run_id in self._records:
                return False
            self._records[run_id] = InvocationRecord(
                run_id,
                job_id,
                attempt_id,
                organization_id,
                InvocationState.CLAIMED,
                datetime.now(UTC),
                None,
                None,
                None,
            )
            return True

    def mark_sent(self, *, run_id: str, job_id: str, attempt_id: str, organization_id: str) -> bool:
        with self._lock:
            row = self._records.get(run_id)
            if not _matches(row, job_id, attempt_id, organization_id, InvocationState.CLAIMED):
                return False
            assert row is not None
            self._records[run_id] = InvocationRecord(
                row.run_id,
                row.job_id,
                row.attempt_id,
                row.organization_id,
                InvocationState.SENT,
                row.claimed_at,
                datetime.now(UTC),
                None,
                None,
            )
            return True

    def complete(
        self,
        *,
        run_id: str,
        job_id: str,
        attempt_id: str,
        organization_id: str,
        state: str,
        result_sha256: str | None = None,
    ) -> bool:
        with self._lock:
            if self.fail_complete:
                return False
            row = self._records.get(run_id)
            if not _matches(row, job_id, attempt_id, organization_id, InvocationState.SENT):
                return False
            assert row is not None
            self._records[run_id] = InvocationRecord(
                row.run_id,
                row.job_id,
                row.attempt_id,
                row.organization_id,
                InvocationState(state),
                row.claimed_at,
                row.sent_at,
                datetime.now(UTC),
                result_sha256,
            )
            return True

    def get(self, run_id: str) -> InvocationRecord | None:
        with self._lock:
            return self._records.get(run_id)


class ClaimBarrierLedger(MemoryInvocationLedger):
    """Force independent claim callers to meet before touching the shared ledger."""

    def __init__(self) -> None:
        super().__init__()
        self.claim_barrier = threading.Barrier(2)
        self.claim_results: list[bool] = []
        self._claim_results_lock = threading.Lock()

    def claim(self, *, run_id: str, job_id: str, attempt_id: str, organization_id: str) -> bool:
        self.claim_barrier.wait(timeout=2)
        claimed = super().claim(
            run_id=run_id,
            job_id=job_id,
            attempt_id=attempt_id,
            organization_id=organization_id,
        )
        with self._claim_results_lock:
            self.claim_results.append(claimed)
        return claimed


class StaticBoundOutcomePort:
    """Test a malformed bridge outcome while its advertised attempt guard remains NEW."""

    def __init__(self, guard: InvocationLedgerGuard, outcome: object) -> None:
        self._guard = guard
        self._outcome = outcome

    @property
    def invocation_guard_identity(self) -> object:
        return self._guard

    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]:
        return frozenset({ProviderContextMode.IMAGE_ONLY})

    @property
    def context_capability(self):
        return None

    def observe(self, _request: ObservationRequest) -> object:
        return self._outcome


class UnGuardedTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, _path: str, _payload: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        raise AssertionError("un-guarded transport must be rejected before use")


def _matches(
    row: InvocationRecord | None,
    job_id: str,
    attempt_id: str,
    organization_id: str,
    state: InvocationState,
) -> bool:
    return row is not None and (row.job_id, row.attempt_id, row.organization_id, row.state) == (
        job_id,
        attempt_id,
        organization_id,
        state,
    )


class _Fixture:
    def __init__(self) -> None:
        self.harness: AnalysisHarness = build_analysis_harness()
        self.request = ObservationRequest(
            correlation_id="corr_fx_1",
            organization_id=ORG,
            render=self.harness.snapshot.render,
            admission=self.harness.receipt,
            context_mode=ProviderContextMode.IMAGE_ONLY,
        )

    def bridge(self, transport: HttpJsonTransport) -> LegacyVisionV2Bridge:
        return LegacyVisionV2Bridge(
            transport=transport,
            render_loader=self.harness.sources.read_render,
            clock=self.harness.clock.now,
        )


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, behavior: Callable[[BaseHTTPRequestHandler], None]) -> None:
        self.behavior = behavior
        self.hit_count = 0
        self.hit_lock = threading.Lock()
        self.request_states: list[InvocationState | None] = []
        self.state_reader: Callable[[], InvocationState | None] | None = None
        super().__init__(("127.0.0.1", 0), _Handler)


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:
        _ = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        server = self.server
        assert isinstance(server, _Server)
        with server.hit_lock:
            server.hit_count += 1
            state = server.state_reader() if server.state_reader is not None else None
            server.request_states.append(state)
        server.behavior(self)

    def log_message(self, _format: str, *_args: object) -> None:
        return


@contextmanager
def _serve(behavior: Callable[[BaseHTTPRequestHandler], None]) -> Iterator[_Server]:
    server = _Server(behavior)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def _response(handler: BaseHTTPRequestHandler, status: int, body: bytes) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
    handler.wfile.flush()


def _guard(
    ledger: MemoryInvocationLedger,
    *,
    run_id: str | None = None,
    job_id: str = "job_fx_t6",
    attempt_id: str = "attempt_fx_t6",
) -> InvocationLedgerGuard:
    return InvocationLedgerGuard(
        ledger=ledger,
        run_id=run_id or str(uuid4()),
        job_id=job_id,
        attempt_id=attempt_id,
        organization_id=ORG,
    )


def _port(
    base_url: str,
    fixture: _Fixture,
    ledger: MemoryInvocationLedger,
    guard: InvocationLedgerGuard,
    *,
    timeout: float = 1.0,
    resolver=None,
) -> InvocationGuardedVisionObservationPort:
    transport = HttpJsonTransport(
        base_url=base_url,
        guard=guard,
        total_timeout_seconds=timeout,
        resolver=resolver,
    )
    return InvocationGuardedVisionObservationPort(fixture.bridge(transport), guard)


def _state(ledger: MemoryInvocationLedger, run_id: str) -> InvocationState | None:
    record = ledger.get(run_id)
    return None if record is None else record.state


def _wait_for_resolver_pool_idle(timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while _PROCESS_RESOLVER_POOL.active_worker_count:
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.001)
    return True


def _typed_failure() -> dict[str, object]:
    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1)
    fixture = _Fixture()
    render = fixture.harness.snapshot.render
    return VisionUnderstandingFailureV2(
        correlation_id="corr_fx_1",
        executed_at=datetime(2026, 10, 16, 12, 0, 5, tzinfo=UTC),
        source_image_ref={"artifact_ref": render.render_ref, "sha256": render.render_sha256},
        profile_id=profile.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        attempt_number=1,
        repair_attempted=False,
        content_policy_version=synthetic_prohibited_lexicon().lexicon_version,
        policy_match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
        policy_execution_state="NOT_EXECUTED",
        error_code=VisionErrorCode.VISION_TIMEOUT,
        error_detail=VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED,
        retryable=False,
        model_provenance=profile.model_provenance,
    ).model_dump(mode="json")


def test_complete_v2_success_is_one_live_call_and_sent_precedes_request() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    run_id = guard.run_id
    body = json.dumps(synthetic_v2_response()).encode()
    with _serve(lambda handler: _response(handler, 200, body)) as server:
        server.state_reader = lambda: _state(ledger, run_id)
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)

    assert server.hit_count == 1
    assert server.request_states == [InvocationState.SENT]
    assert result.evidence.evidence_kind is EvidenceKind.LIVE_LEGACY_BRIDGE
    assert _state(ledger, run_id) is InvocationState.SUCCEEDED


def server_url(server: _Server) -> str:
    host, port = server.server_address
    return f"http://{host}:{port}"


def test_transport_and_bridge_expose_the_same_read_only_guard_identity() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    transport = HttpJsonTransport(base_url="http://127.0.0.1:1", guard=guard)
    bridge = fixture.bridge(transport)

    assert transport.invocation_guard_identity is guard
    assert bridge.invocation_guard_identity is guard


def test_mismatched_transport_guard_is_rejected_before_http_send() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    transport_guard = _guard(ledger)
    decorator_guard = _guard(ledger)
    with _serve(lambda handler: _response(handler, 200, b"{}")) as server:
        bridge = fixture.bridge(
            HttpJsonTransport(base_url=server_url(server), guard=transport_guard)
        )
        with pytest.raises(ValueError, match="same invocation guard"):
            InvocationGuardedVisionObservationPort(bridge, decorator_guard)

    assert server.hit_count == 0


def test_guard_identity_is_rechecked_before_each_bridge_call() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    other_guard = _guard(ledger)
    with _serve(lambda handler: _response(handler, 200, b"{}")) as server:
        bridge = fixture.bridge(HttpJsonTransport(base_url=server_url(server), guard=guard))
        guarded = InvocationGuardedVisionObservationPort(bridge, guard)
        bridge._transport = HttpJsonTransport(base_url=server_url(server), guard=other_guard)

        outcome = guarded.observe(fixture.request)

    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.NOT_SENT_GUARD_REFUSED
    assert outcome.provider_invoked is False
    assert guard.state.value == "NEW"
    assert server.hit_count == 0


def test_unguarded_transport_is_rejected_before_bridge_call() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    transport = UnGuardedTransport()
    bridge = LegacyVisionV2Bridge(
        transport=transport,
        render_loader=fixture.harness.sources.read_render,
        clock=fixture.harness.clock.now,
    )

    with pytest.raises(ValueError, match="same invocation guard"):
        InvocationGuardedVisionObservationPort(bridge, guard)

    assert bridge.invocation_guard_identity is None
    assert transport.calls == 0


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(Mock(spec=ObservationSucceeded), id="success-before-claim"),
        pytest.param(
            ObservationFailed(ObservationFailureCode.PROVIDER_ERROR, provider_invoked=True),
            id="invoked-failure-before-claim",
        ),
    ],
)
def test_new_guard_rejects_success_or_invoked_failure_without_downgrade(outcome: object) -> None:
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    guarded = InvocationGuardedVisionObservationPort(StaticBoundOutcomePort(guard, outcome), guard)

    with pytest.raises(RuntimeError, match="before guard claim"):
        guarded.observe(_Fixture().request)

    assert guard.state.value == "NEW"
    assert ledger.get(guard.run_id) is None


def test_valid_identity_matched_typed_v2_failure_is_terminal_failed() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    run_id = guard.run_id
    body = json.dumps(_typed_failure()).encode()
    with _serve(lambda handler: _response(handler, 200, body)) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)

    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_TIMEOUT
    assert result.provider_invoked is True
    assert _state(ledger, run_id) is InvocationState.FAILED


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (302, b'{"redirect":"/elsewhere"}'),
        (401, b'{"detail":"unauthorized"}'),
        (422, b'{"detail":"invalid"}'),
        (500, b'{"detail":"server error"}'),
    ],
)
def test_non_200_responses_are_unknown_without_redirect_or_retry(status: int, body: bytes) -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    run_id = guard.run_id
    with _serve(lambda handler: _response(handler, status, body)) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)

    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert result.provider_invoked is True
    assert server.hit_count == 1
    assert _state(ledger, run_id) is InvocationState.UNKNOWN


def test_guard_refusal_and_ledger_error_send_zero_requests() -> None:
    body = json.dumps(synthetic_v2_response()).encode()
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    assert guard.claim() is None
    assert guard.mark_sent() is None
    assert ledger.complete(
        run_id=guard.run_id,
        job_id=guard.job_id,
        attempt_id=guard.attempt_id,
        organization_id=ORG,
        state=InvocationState.SUCCEEDED.value,
    )
    refused_guard = _guard(ledger, run_id=guard.run_id)
    with _serve(lambda handler: _response(handler, 200, body)) as server:
        outcome = _port(server_url(server), fixture, ledger, refused_guard).observe(fixture.request)
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.NOT_SENT_RUN_ALREADY_USED
    assert outcome.provider_invoked is False
    assert server.hit_count == 0

    broken_ledger = MemoryInvocationLedger()
    broken_ledger.raise_on_claim = True
    refused_guard = _guard(broken_ledger)
    with _serve(lambda handler: _response(handler, 200, body)) as server:
        outcome = _port(server_url(server), fixture, broken_ledger, refused_guard).observe(
            fixture.request
        )
    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.NOT_SENT_GUARD_REFUSED
    assert server.hit_count == 0


def test_bridge_precheck_refusal_does_not_claim_or_send() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    derived_request = replace(fixture.request, processing_image_ref="synthetic:derived.png")
    with _serve(lambda handler: _response(handler, 200, b"{}")) as server:
        outcome = _port(server_url(server), fixture, ledger, guard).observe(derived_request)

    assert isinstance(outcome, ObservationFailed)
    assert outcome.code is ObservationFailureCode.DERIVED_INPUT_UNSUPPORTED
    assert outcome.provider_invoked is False
    assert guard.state.value == "NEW"
    assert ledger.get(guard.run_id) is None
    assert server.hit_count == 0


def test_restart_after_durable_sent_never_calls_again() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    prior = _guard(ledger)
    assert prior.claim() is None
    assert prior.mark_sent() is None
    restarted = _guard(ledger, run_id=prior.run_id)
    with _serve(lambda handler: _response(handler, 200, b"{}")) as server:
        result = _port(server_url(server), fixture, ledger, restarted).observe(fixture.request)
    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert result.provider_invoked is True
    assert server.hit_count == 0
    assert _state(ledger, prior.run_id) is InvocationState.SENT


def test_inflight_duplicate_after_sent_does_not_send_again() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    first_guard = _guard(ledger)
    second_guard = _guard(ledger, run_id=first_guard.run_id)
    body = json.dumps(synthetic_v2_response()).encode()
    request_entered = threading.Event()
    release_response = threading.Event()

    def behavior(handler: BaseHTTPRequestHandler) -> None:
        request_entered.set()
        release_response.wait(timeout=2)
        _response(handler, 200, body)

    with _serve(behavior) as server:
        server.state_reader = lambda: _state(ledger, first_guard.run_id)
        first_port = _port(server_url(server), fixture, ledger, first_guard)
        duplicate_port = _port(server_url(server), fixture, ledger, second_guard)
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(first_port.observe, fixture.request)
            assert request_entered.wait(timeout=1)
            try:
                duplicate = duplicate_port.observe(fixture.request)
            finally:
                release_response.set()
            first_result = first.result(timeout=3)

    assert isinstance(first_result, ObservationSucceeded)
    assert isinstance(duplicate, ObservationFailed)
    assert duplicate.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert duplicate.provider_invoked is True
    assert server.hit_count == 1
    assert server.request_states == [InvocationState.SENT]
    assert _state(ledger, first_guard.run_id) is InvocationState.SUCCEEDED


def test_two_workers_racing_for_same_run_make_at_most_one_request() -> None:
    fixture = _Fixture()
    ledger = ClaimBarrierLedger()
    first_guard = _guard(ledger)
    second_guard = _guard(ledger, run_id=first_guard.run_id)
    body = json.dumps(synthetic_v2_response()).encode()

    with _serve(lambda handler: _response(handler, 200, body)) as server:
        server.state_reader = lambda: _state(ledger, first_guard.run_id)
        first_port = _port(server_url(server), fixture, ledger, first_guard)
        second_port = _port(server_url(server), fixture, ledger, second_guard)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(first_port.observe, fixture.request)
            second = pool.submit(second_port.observe, fixture.request)
            outcomes = (first.result(timeout=3), second.result(timeout=3))

    assert ledger.claim_results.count(True) == 1
    assert ledger.claim_results.count(False) == 1
    assert server.hit_count == 1
    assert all(state is InvocationState.SENT for state in server.request_states)
    assert sum(not isinstance(outcome, ObservationFailed) for outcome in outcomes) == 1
    assert _state(ledger, first_guard.run_id) is InvocationState.SUCCEEDED


@pytest.mark.parametrize("body", [b"{not-json", b'{"status":"SUCCEEDED"'])
def test_malformed_or_truncated_response_is_unknown(body: bytes) -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)

    def behavior(handler: BaseHTTPRequestHandler) -> None:
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body) + 30))
        handler.end_headers()
        handler.wfile.write(body)
        handler.wfile.flush()
        handler.close_connection = True

    with _serve(behavior) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)
    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert server.hit_count == 1
    assert _state(ledger, guard.run_id) is InvocationState.UNKNOWN


def test_connection_reset_after_sent_is_unknown() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)

    def behavior(handler: BaseHTTPRequestHandler) -> None:
        handler.close_connection = True
        handler.connection.shutdown(2)
        handler.connection.close()

    with _serve(behavior) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)
    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert server.hit_count == 1
    assert _state(ledger, guard.run_id) is InvocationState.UNKNOWN


def test_connection_failure_before_sent_sends_no_http_request() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    result = _port(f"http://127.0.0.1:{port}", fixture, ledger, guard).observe(fixture.request)

    assert isinstance(result, ObservationFailed)
    assert result.provider_invoked is False
    assert _state(ledger, guard.run_id) is InvocationState.CLAIMED


def test_stalled_dns_resolution_is_bounded_by_total_deadline() -> None:
    assert _wait_for_resolver_pool_idle()
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    resolver_started = threading.Event()
    release_resolver = threading.Event()

    def stalled_resolver(
        _host: str, _port: int
    ) -> list[tuple[int, int, int, str, tuple[object, ...]]]:
        resolver_started.set()
        release_resolver.wait(timeout=2)
        return []

    with _serve(lambda handler: _response(handler, 200, b"{}")) as server:
        started_at = time.monotonic()
        try:
            result = _port(
                server_url(server),
                fixture,
                ledger,
                guard,
                timeout=0.08,
                resolver=stalled_resolver,
            ).observe(fixture.request)
        finally:
            release_resolver.set()
        elapsed = time.monotonic() - started_at

    assert resolver_started.is_set()
    assert elapsed < 0.5
    assert isinstance(result, ObservationFailed)
    assert result.provider_invoked is False
    assert guard.state.value == "CLAIMED"
    assert server.hit_count == 0
    assert _state(ledger, guard.run_id) is InvocationState.CLAIMED
    assert _wait_for_resolver_pool_idle()


def test_resolver_capacity_lock_wait_is_bounded_by_total_deadline() -> None:
    assert _wait_for_resolver_pool_idle()
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    resolver_called = False

    def resolver(_host: str, _port: int) -> list[tuple[int, int, int, str, tuple[object, ...]]]:
        nonlocal resolver_called
        resolver_called = True
        return []

    with _serve(lambda handler: _response(handler, 200, b"{}")) as server:
        started_at = time.monotonic()
        with _PROCESS_RESOLVER_POOL._lock:
            result = _port(
                server_url(server),
                fixture,
                ledger,
                guard,
                timeout=0.08,
                resolver=resolver,
            ).observe(fixture.request)
        elapsed = time.monotonic() - started_at

    assert elapsed < 0.5
    assert resolver_called is False
    assert isinstance(result, ObservationFailed)
    assert result.provider_invoked is False
    assert guard.state.value == "CLAIMED"
    assert server.hit_count == 0
    assert _state(ledger, guard.run_id) is InvocationState.CLAIMED


def test_process_resolver_pool_caps_stalled_lookups_and_recovers() -> None:
    assert _wait_for_resolver_pool_idle()
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    lock = threading.Lock()
    release_resolvers = threading.Event()
    two_resolvers_started = threading.Event()
    active_resolvers = 0
    resolver_calls = 0
    max_active_resolvers = 0

    with _serve(
        lambda handler: _response(handler, 200, json.dumps(synthetic_v2_response()).encode())
    ) as server:

        def resolver(_host: str, port: int) -> list[tuple[int, int, int, str, tuple[object, ...]]]:
            nonlocal active_resolvers, max_active_resolvers, resolver_calls
            with lock:
                resolver_calls += 1
                active_resolvers += 1
                max_active_resolvers = max(max_active_resolvers, active_resolvers)
                if active_resolvers == 2:
                    two_resolvers_started.set()
            try:
                release_resolvers.wait(timeout=10)
                return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", port))]
            finally:
                with lock:
                    active_resolvers -= 1

        start_barrier = threading.Barrier(4)
        guards = [_guard(ledger) for _ in range(4)]

        def invoke(guard: InvocationLedgerGuard) -> object:
            start_barrier.wait(timeout=2)
            return _port(
                server_url(server),
                fixture,
                ledger,
                guard,
                timeout=0.12,
                resolver=resolver,
            ).observe(fixture.request)

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(invoke, guard) for guard in guards]
                assert two_resolvers_started.wait(timeout=1)
                results = [future.result(timeout=2) for future in futures]

            for result in results:
                assert isinstance(result, ObservationFailed)
                assert result.provider_invoked is False
            with lock:
                assert resolver_calls == 2
                assert active_resolvers == 2
                assert max_active_resolvers == 2
            assert _PROCESS_RESOLVER_POOL.worker_count == 2
            assert _PROCESS_RESOLVER_POOL.active_worker_count == 2
            assert server.hit_count == 0

            saturated_guard = _guard(ledger)
            saturated = _port(
                server_url(server),
                fixture,
                ledger,
                saturated_guard,
                timeout=0.5,
                resolver=resolver,
            ).observe(fixture.request)
            assert isinstance(saturated, ObservationFailed)
            assert saturated.provider_invoked is False
            with lock:
                assert resolver_calls == 2
            assert server.hit_count == 0
        finally:
            release_resolvers.set()

        assert _wait_for_resolver_pool_idle(timeout=1)
        recovered_guard = _guard(ledger)
        recovered = _port(
            server_url(server),
            fixture,
            ledger,
            recovered_guard,
            resolver=resolver,
        ).observe(fixture.request)

    assert isinstance(recovered, ObservationSucceeded)
    with lock:
        assert resolver_calls == 3
        assert max_active_resolvers == 2
    assert server.hit_count == 1
    assert _state(ledger, recovered_guard.run_id) is InvocationState.SUCCEEDED


def test_https_uses_original_hostname_and_requires_certificate_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSocket:
        def __init__(self) -> None:
            self.connected_address = None
            self.closed = False

        def settimeout(self, _timeout: float) -> None:
            return

        def connect(self, address: object) -> None:
            self.connected_address = address

        def close(self) -> None:
            self.closed = True

    class FakeTlsSocket(FakeSocket):
        def __init__(self) -> None:
            super().__init__()
            self.handshake_complete = False

        def do_handshake(self) -> None:
            self.handshake_complete = True

    class FakeContext:
        check_hostname = True
        verify_mode = ssl.CERT_REQUIRED

        def __init__(self) -> None:
            self.server_hostname = None
            self.handshake_on_connect = None
            self.tls_socket = FakeTlsSocket()

        def wrap_socket(
            self,
            _raw_socket: FakeSocket,
            *,
            server_hostname: str,
            do_handshake_on_connect: bool,
        ) -> FakeTlsSocket:
            self.server_hostname = server_hostname
            self.handshake_on_connect = do_handshake_on_connect
            return self.tls_socket

    guard = _guard(MemoryInvocationLedger())
    transport = HttpJsonTransport(
        base_url="https://vision.example.test",
        guard=guard,
        resolver=lambda _host, _port: [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 443))
        ],
    )
    connection = transport._connection(1.0)
    fake_raw_socket = FakeSocket()
    context = FakeContext()
    connection._context = context
    monkeypatch.setattr(socket, "socket", lambda *_args: fake_raw_socket)

    transport._connect_before_deadline(connection, time.monotonic() + 1.0)

    assert fake_raw_socket.connected_address == ("127.0.0.1", 443)
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.server_hostname == "vision.example.test"
    assert context.handshake_on_connect is False
    assert context.tls_socket.handshake_complete is True
    connection.close()


def test_ledger_finalize_uncertainty_overrides_valid_v2_success_to_unknown() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    ledger.fail_complete = True
    guard = _guard(ledger)
    body = json.dumps(synthetic_v2_response()).encode()
    with _serve(lambda handler: _response(handler, 200, body)) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)

    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert result.provider_invoked is True
    assert server.hit_count == 1


@pytest.mark.parametrize("kind", ["success", "failure"])
def test_v2_identity_mismatch_is_unknown(kind: str) -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    body = synthetic_v2_response() if kind == "success" else _typed_failure()
    body["correlation_id"] = "corr_not_requested"
    payload = json.dumps(body).encode()
    with _serve(lambda handler: _response(handler, 200, payload)) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)

    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert result.provider_invoked is True
    assert _state(ledger, guard.run_id) is InvocationState.UNKNOWN


def test_slow_drip_obeys_one_total_monotonic_deadline() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    payload = json.dumps(synthetic_v2_response()).encode()

    def behavior(handler: BaseHTTPRequestHandler) -> None:
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(payload)))
        handler.end_headers()
        for part in (payload[:8], payload[8:16], payload[16:]):
            threading.Event().wait(0.055)
            try:
                handler.wfile.write(part)
                handler.wfile.flush()
            except OSError:
                return

    with _serve(behavior) as server:
        result = _port(server_url(server), fixture, ledger, guard, timeout=0.12).observe(
            fixture.request
        )
    assert isinstance(result, ObservationFailed)
    assert result.code is ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
    assert server.hit_count == 1
    assert _state(ledger, guard.run_id) is InvocationState.UNKNOWN


def test_live_provenance_and_single_attempt_policy_are_closed() -> None:
    fixture = _Fixture()
    ledger = MemoryInvocationLedger()
    guard = _guard(ledger)
    body = json.dumps(synthetic_v2_response()).encode()
    with _serve(lambda handler: _response(handler, 200, body)) as server:
        result = _port(server_url(server), fixture, ledger, guard).observe(fixture.request)

    assert result.evidence.evidence_kind is EvidenceKind.LIVE_LEGACY_BRIDGE
    evidence = result.evidence
    provenance = ProvenanceV1(
        evidence_kind=evidence.evidence_kind.value,
        provider_context_mode=evidence.provider_context_mode.value,
        adapter_id=evidence.adapter_id,
        result_contract=evidence.result_contract,
        executed_at=evidence.executed_at,
        transport_attempts=evidence.transport_attempts,
        profile_id=evidence.profile_id,
        profile_catalog_hash=evidence.profile_catalog_hash,
        config_hash=evidence.config_hash,
        adapter_version=evidence.adapter_version,
        model_identifier=evidence.model_identifier,
        model_revision=evidence.model_revision,
        content_policy_version=evidence.content_policy_version,
        policy_match_view_version=evidence.policy_match_view_version,
    )
    assert provenance.evidence_kind == "live_legacy_bridge"
    incomplete = provenance.model_dump(mode="python")
    incomplete["profile_id"] = None
    with pytest.raises(ValidationError):
        ProvenanceV1.model_validate(incomplete)
    typed_context = provenance.model_dump(mode="python")
    typed_context["provider_context_mode"] = "typed_context"
    with pytest.raises(ValidationError):
        ProvenanceV1.model_validate(typed_context)
    assert PILOT_VISION_RETRY_POLICY.policy_id == "pilot.vision_single_attempt.v1"
    assert PILOT_VISION_RETRY_POLICY.max_attempts == 1
    assert PILOT_VISION_RETRY_POLICY.attempt_timeout_ms == 180000
    assert FIXTURE_RETRY_POLICY.max_attempts == 3
    assert FIXTURE_RETRY_POLICY.attempt_timeout_ms == 30000
