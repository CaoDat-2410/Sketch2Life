from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from threading import Thread

import pytest
from PIL import Image
from sqlalchemy import create_engine, text

from sketch2life.application.ports.story_run_lite import (
    AdmittedAssetPair,
    AssetBinding,
    ValidatedVisionResult,
)
from sketch2life.application.ports.vision_analysis import InvocationTerminalState
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.story_run_lite import OwnerScopeKind
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)
from sketch2life.infrastructure.story_run_lite.composition import (
    goal_database_url,
    verify_goal_database_owner,
)
from sketch2life.infrastructure.story_run_lite.photo_bridge import PhotoVisionBridge
from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineStore
from sketch2life.infrastructure.story_run_lite.repository import SqlStoryRunLiteRepository
from sketch2life.infrastructure.vision_analysis.invocation_guard import InvocationLedgerGuard
from sketch2life.infrastructure.vision_analysis.ledger import InvocationLedger, InvocationState

_PARENT = OwnerScopeKind.PARENT_ACCOUNT
_TECHNICAL_ORGANIZATION_ID = "storyrun-lite-photo-bridge-v1"


@pytest.fixture
def loopback_runtime(tmp_path):
    value = os.environ.get("STORYRUN_LITE_DATABASE_URL")
    if not value:
        pytest.skip("requires the verified goal-owned storyrun_lite_* loopback database")
    safe_url, database_name = goal_database_url(value)
    engine = create_engine(safe_url, pool_pre_ping=True, hide_parameters=True)
    assert verify_goal_database_owner(engine, database_name)
    repository = SqlStoryRunLiteRepository(
        engine=engine,
        quarantine=QuarantineStore(tmp_path / "quarantine"),
    )
    repository.acquire_singleton_lock()
    repository.recover_after_restart()
    server_state = {"mode": "success", "count": 0, "payloads": [], "port": 0}
    server_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *args: object) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload_bytes = self.rfile.read(length)
            with server_lock:
                server_state["count"] = int(server_state["count"]) + 1
                mode = str(server_state["mode"])
                server_state["payloads"].append(json.loads(payload_bytes))
            if mode in {"status", "redirect", "unauthorized", "server-error"}:
                status_code = {
                    "status": 503,
                    "redirect": 302,
                    "unauthorized": 401,
                    "server-error": 500,
                }[mode]
                self.send_response(status_code)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if mode == "reset":
                with suppress(OSError):
                    self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            if mode == "timeout":
                time.sleep(1.0)
                try:
                    self.send_response(200)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                except OSError:
                    pass
                return
            if mode == "malformed":
                body = b'{"status":'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            request = VisionUnderstandingRequestV2.model_validate(
                server_state["payloads"][-1]["request"]
            )
            catalog = vision_profile_catalog_v2()
            profile = catalog.resolve(request.requested_profile_id)
            policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
            result = VisionUnderstandingSuccessV2(
                correlation_id=request.correlation_id,
                executed_at=datetime.now(UTC),
                source_image_ref=request.source_image_ref,
                profile_id=request.requested_profile_id,
                profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
                attempt_number=1,
                repair_attempted=False,
                content_policy_version=policy.content_policy_version,
                policy_match_view_version=policy.policy_match_view_version,
                policy_execution_state="PASSED",
                entities=(),
                actions=(),
                relations=(),
                themes=(),
                ambiguous_regions=(),
                adapter_version=profile.adapter_version,
                config_hash=vision_profile_config_hash_v2(profile),
                model_provenance=profile.model_provenance,
            )
            body = json.dumps(result.model_dump(mode="json"), separators=(",", ":")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_state["port"] = server.server_port
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    bridge = PhotoVisionBridge(
        engine=engine,
        repository=repository,
        base_url=base_url,
        total_timeout_seconds=12.0,
    )
    try:
        yield engine, repository, bridge, server_state, server_lock
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        repository.release_singleton_lock()
        engine.dispose()


def _jpeg() -> bytes:
    output = BytesIO()
    Image.new("RGB", (48, 32), (10, 80, 140)).save(output, format="JPEG")
    return output.getvalue()


def _create_attached_run(repository: SqlStoryRunLiteRepository, suffix: str):
    owner = f"parent-loopback-{suffix}-{uuid.uuid4()}"
    run = repository.create_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        profile_ref="synthetic-parent-demo",
        key_sha256=hashlib.sha256(f"run:{suffix}:{owner}".encode()).hexdigest(),
        fingerprint_sha256=hashlib.sha256(f"run-fingerprint:{suffix}:{owner}".encode()).hexdigest(),
    )
    run_id = str(run.body["run_ref"])
    original_ref, derived_ref = str(uuid.uuid4()), str(uuid.uuid4())
    original_bytes = b"synthetic-original-" + suffix.encode()
    derived_bytes = _jpeg()
    original = AssetBinding(
        original_ref,
        1,
        "image/png",
        hashlib.sha256(original_bytes).hexdigest(),
        len(original_bytes),
        _PARENT,
        owner,
    )
    derived = AssetBinding(
        derived_ref,
        1,
        "image/jpeg",
        hashlib.sha256(derived_bytes).hexdigest(),
        len(derived_bytes),
        _PARENT,
        owner,
    )
    repository.store_asset(derived_ref, derived_bytes)
    pair = AdmittedAssetPair(original, derived, str(uuid.uuid4()), run_id)
    key_hash = hashlib.sha256(f"attach:{suffix}:{owner}".encode()).hexdigest()
    fingerprint = hashlib.sha256(f"attach-fingerprint:{suffix}:{owner}".encode()).hexdigest()
    _result, _job_id, claimed_version = repository.attach_asset(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        run_id=run_id,
        pair=pair,
        expected_revision=1,
        expected_version=1,
        key_sha256=key_hash,
        fingerprint_sha256=fingerprint,
    )
    assert claimed_version is not None
    repository.finalize_attach_command(
        run_id=run_id, key_sha256=key_hash, claimed_version=claimed_version
    )
    assert repository.open_story_dispatch_gate(run_id=run_id, claimed_version=claimed_version)
    return owner, run_id, derived, claimed_version


def _persist_callback(repository, engine, run_id, claim_version, observed_order):
    ledger = InvocationLedger(engine)

    def persist(result: ValidatedVisionResult) -> bool:
        record = ledger.get(run_id)
        assert record is not None and record.state is InvocationState.SENT
        observed_order.append("ledger-sent")
        committed = repository.commit_vision_success(
            run_id=run_id,
            claimed_version=claim_version,
            result_snapshot=result.result_snapshot,
            subject_label=result.subject_label,
            confidence=result.confidence,
            canonical_result_sha256=result.canonical_result_sha256,
            raw_body_sha256=result.raw_body_sha256,
        )
        assert committed
        observed_order.append("story-committed")
        assert ledger.get(run_id).state is InvocationState.SENT
        return committed

    return persist


def test_photo_bridge_is_single_send_loopback_and_result_precedes_ledger_finalization(
    loopback_runtime,
) -> None:
    engine, repository, bridge, server_state, _server_lock = loopback_runtime
    owner, run_id, derived, claim = _create_attached_run(repository, "success")
    order: list[str] = []
    outcome = bridge.analyze(
        run_id=run_id,
        binding=derived,
        persist_success=_persist_callback(repository, engine, run_id, claim, order),
    )
    assert outcome.state == "SUCCEEDED"
    assert outcome.provider_invoked is True
    assert order == ["ledger-sent", "story-committed"]
    assert int(server_state["count"]) == 1
    request_payload = server_state["payloads"][0]["source_image"]
    assert request_payload["sha256"] == derived.sha256
    assert (
        hashlib.sha256(base64.b64decode(request_payload["content_base64"])).hexdigest()
        == derived.sha256
    )
    assert (
        repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=run_id).body[
            "run_state"
        ]
        == "SUBJECT_REVIEW"
    )
    record = InvocationLedger(engine).get(run_id)
    assert record is not None and record.state is InvocationState.SUCCEEDED
    with engine.connect() as connection:
        hashes = connection.execute(
            text(
                "SELECT raw_body_sha256, canonical_result_sha256 "
                "FROM story.understanding_revisions WHERE run_id = :run_id"
            ),
            {"run_id": run_id},
        ).one()
    assert record.result_sha256 == hashes.raw_body_sha256
    assert hashes.raw_body_sha256 != hashes.canonical_result_sha256


def test_committed_story_result_recovers_sent_ledger_without_redispatch(
    loopback_runtime, monkeypatch
) -> None:
    engine, repository, bridge, server_state, _server_lock = loopback_runtime
    owner, run_id, binding, claim = _create_attached_run(repository, "ledger-recovery")
    original_finalize = InvocationLedgerGuard.finalize

    def crash_after_story_commit(
        guard: InvocationLedgerGuard,
        state: InvocationTerminalState,
        result_sha256: str | None = None,
    ) -> bool:
        if state is InvocationTerminalState.SUCCEEDED:
            raise RuntimeError("synthetic process-stop boundary")
        return original_finalize(guard, state, result_sha256)

    monkeypatch.setattr(InvocationLedgerGuard, "finalize", crash_after_story_commit)
    with pytest.raises(RuntimeError, match="synthetic process-stop boundary"):
        bridge.analyze(
            run_id=run_id,
            binding=binding,
            persist_success=_persist_callback(repository, engine, run_id, claim, []),
        )
    monkeypatch.setattr(InvocationLedgerGuard, "finalize", original_finalize)

    record_before_recovery = InvocationLedger(engine).get(run_id)
    assert record_before_recovery is not None
    assert record_before_recovery.state is InvocationState.SENT
    assert (
        repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=run_id).body[
            "run_state"
        ]
        == "SUBJECT_REVIEW"
    )
    pending_story_result = next(
        row for row in repository.pending_vision_ledger_reconciliation() if row["run_id"] == run_id
    )
    expected_raw_body_sha256 = str(pending_story_result["raw_body_sha256"])
    assert bridge.reconcile_completed_results() == {"completed": 1, "unavailable": 0}
    recovered = InvocationLedger(engine).get(run_id)
    assert recovered is not None and recovered.state is InvocationState.SUCCEEDED
    assert recovered.result_sha256 == expected_raw_body_sha256
    replay = bridge.analyze(
        run_id=run_id,
        binding=binding,
        persist_success=lambda _result: pytest.fail("completed tuple must not be dispatched"),
    )
    assert replay.provider_invoked is False
    assert int(server_state["count"]) == 1


def test_guard_denial_race_unknown_and_cancel_late_cas(loopback_runtime) -> None:
    engine, repository, bridge, server_state, server_lock = loopback_runtime
    sent_before = int(server_state["count"])

    # Existing CLAIMED row makes the A1 guard refuse this tuple before any local HTTP bytes.
    owner_denied, run_denied, binding_denied, _claim_denied = _create_attached_run(
        repository, "guard-denied"
    )
    context = repository.get_dispatch_context(run_id=run_denied)
    ledger = InvocationLedger(engine)
    assert ledger.claim(
        run_id=run_denied,
        job_id=str(context["provider_job_id"]),
        attempt_id=str(context["provider_attempt_id"]),
        organization_id=_TECHNICAL_ORGANIZATION_ID,
    )
    denied = bridge.analyze(
        run_id=run_denied,
        binding=binding_denied,
        persist_success=lambda _result: pytest.fail("guard-denied response must not be persisted"),
    )
    assert denied.state == "FAILED"
    assert denied.provider_invoked is False
    assert int(server_state["count"]) == sent_before
    assert (
        repository.get_run(
            actor_scope_kind=_PARENT, actor_scope_ref=owner_denied, run_id=run_denied
        ).body["run_state"]
        == "INPUT_PROCESSING"
    )

    # Two callers racing the same A1 tuple can produce at most one loopback HTTP request.
    owner_race, run_race, binding_race, claim_race = _create_attached_run(
        repository, "same-tuple-race"
    )
    outcomes = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                bridge.analyze,
                run_id=run_race,
                binding=binding_race,
                persist_success=_persist_callback(repository, engine, run_race, claim_race, []),
            )
            for _ in range(2)
        ]
        outcomes = [future.result(timeout=20) for future in futures]
    assert sum(outcome.state == "SUCCEEDED" for outcome in outcomes) == 1
    assert int(server_state["count"]) == sent_before + 1
    race_record = InvocationLedger(engine).get(run_race)
    assert race_record is not None
    assert race_record.state is InvocationState.SUCCEEDED
    assert (
        repository.get_run(
            actor_scope_kind=_PARENT, actor_scope_ref=owner_race, run_id=run_race
        ).body["run_state"]
        == "SUBJECT_REVIEW"
    )

    # Any ambiguous HTTP result after SENT is UNKNOWN, and the same tuple is never retried.
    failure_modes = (
        ("status-unknown", "status"),
        ("redirect-unknown", "redirect"),
        ("unauthorized-unknown", "unauthorized"),
        ("server-error-unknown", "server-error"),
        ("reset-unknown", "reset"),
        ("timeout-unknown", "timeout"),
        ("malformed-unknown", "malformed"),
    )
    for suffix, mode in failure_modes:
        owner, run_id, binding, claim = _create_attached_run(repository, suffix)
        with server_lock:
            server_state["mode"] = mode
        attempt_bridge = bridge
        if mode == "timeout":
            attempt_bridge = PhotoVisionBridge(
                engine=engine,
                repository=repository,
                base_url=f"http://127.0.0.1:{server_state['port']}",
                total_timeout_seconds=0.5,
            )
        no_result = attempt_bridge.analyze(
            run_id=run_id,
            binding=binding,
            persist_success=lambda _result: pytest.fail("invalid response must not be persisted"),
        )
        assert no_result.state == "UNKNOWN"
        assert no_result.provider_invoked is True
        repository.mark_vision_unknown(
            run_id=run_id,
            claimed_version=claim,
            error_code=no_result.error_code or "VISION_OUTCOME_UNKNOWN",
        )
        record = InvocationLedger(engine).get(run_id)
        assert record is not None and record.state is InvocationState.UNKNOWN
        assert int(server_state["count"]) == sent_before + 2 + failure_modes.index((suffix, mode))
        assert (
            repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=run_id).body[
                "job_state"
            ]
            == "AWAITING_RECONCILIATION"
        )
        sent_count = int(server_state["count"])
        retry = attempt_bridge.analyze(
            run_id=run_id,
            binding=binding,
            persist_success=lambda _result: pytest.fail("UNKNOWN must never be retried"),
        )
        assert retry.state == "UNKNOWN"
        assert retry.provider_invoked is True
        assert int(server_state["count"]) == sent_count
        with server_lock:
            server_state["mode"] = "success"

    # Cancel wins the run CAS; a late validated result cannot move the head.
    owner_cancel, run_cancel, _binding_cancel, claim_cancel = _create_attached_run(
        repository, "cancel-late"
    )
    current = repository.get_run(
        actor_scope_kind=_PARENT, actor_scope_ref=owner_cancel, run_id=run_cancel
    )
    cancelled = repository.cancel_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_cancel,
        run_id=run_cancel,
        expected_revision=int(current.body["revision"]),
        expected_version=int(current.body["version"]),
        key_sha256=hashlib.sha256(b"cancel-late").hexdigest(),
        fingerprint_sha256=hashlib.sha256(b"cancel-late-fingerprint").hexdigest(),
    )
    assert cancelled.status_code == 202
    assert not repository.commit_vision_success(
        run_id=run_cancel,
        claimed_version=claim_cancel,
        result_snapshot={"contract_name": "synthetic-late-result"},
        subject_label="Late result",
        confidence=0.5,
        canonical_result_sha256=hashlib.sha256(b"late-result").hexdigest(),
        raw_body_sha256=None,
    )
    assert int(server_state["count"]) == sent_before + 1 + len(failure_modes)


@pytest.mark.parametrize("transition", ["confirm", "cancel", "confirm-cancel"])
@pytest.mark.parametrize("finalize_failure", ["crash", "returns-false"])
def test_committed_result_reconciles_after_state_transition_before_finalize(
    loopback_runtime,
    monkeypatch,
    transition: str,
    finalize_failure: str,
) -> None:
    engine, repository, bridge, server_state, _server_lock = loopback_runtime
    owner, run_id, binding, claim = _create_attached_run(
        repository, "review-ledger-" + transition + "-" + finalize_failure
    )
    original_finalize = InvocationLedgerGuard.finalize
    persisted = _persist_callback(repository, engine, run_id, claim, [])

    def commit_and_transition(result: ValidatedVisionResult) -> bool:
        assert persisted(result)
        if transition in {"confirm", "confirm-cancel"}:
            current = repository.get_run(
                actor_scope_kind=_PARENT,
                actor_scope_ref=owner,
                run_id=run_id,
            )
            accepted = repository.confirm_subject(
                actor_scope_kind=_PARENT,
                actor_scope_ref=owner,
                run_id=run_id,
                expected_version=int(current.body["version"]),
                expected_understanding_revision=1,
                key_sha256=hashlib.sha256((run_id + "confirm").encode()).hexdigest(),
                fingerprint_sha256=hashlib.sha256((run_id + "confirm-fp").encode()).hexdigest(),
            )
            assert accepted.status_code == 202
            assert accepted.body["run_state"] == "PREPARATION_REVIEW"
        if transition in {"cancel", "confirm-cancel"}:
            current = repository.get_run(
                actor_scope_kind=_PARENT,
                actor_scope_ref=owner,
                run_id=run_id,
            )
            accepted = repository.cancel_run(
                actor_scope_kind=_PARENT,
                actor_scope_ref=owner,
                run_id=run_id,
                expected_version=int(current.body["version"]),
                expected_revision=int(current.body["revision"]),
                key_sha256=hashlib.sha256((run_id + "cancel").encode()).hexdigest(),
                fingerprint_sha256=hashlib.sha256((run_id + "cancel-fp").encode()).hexdigest(),
            )
            assert accepted.status_code == 202
            assert accepted.body["run_state"] == "DELETE_PENDING"
        return True

    def fail_after_story_commit(guard, state, result_sha256=None):
        if state is InvocationTerminalState.SUCCEEDED:
            if finalize_failure == "crash":
                raise RuntimeError("review crash after confirmed/canceled result")
            return False
        return original_finalize(guard, state, result_sha256)

    monkeypatch.setattr(InvocationLedgerGuard, "finalize", fail_after_story_commit)
    if finalize_failure == "crash":
        with pytest.raises(RuntimeError, match="review crash"):
            bridge.analyze(run_id=run_id, binding=binding, persist_success=commit_and_transition)
    else:
        outcome = bridge.analyze(
            run_id=run_id,
            binding=binding,
            persist_success=commit_and_transition,
        )
        assert outcome.state == "UNKNOWN" and outcome.result_committed
    monkeypatch.setattr(InvocationLedgerGuard, "finalize", original_finalize)
    ledger = InvocationLedger(engine)
    sent = ledger.get(run_id)
    assert sent is not None and sent.state is InvocationState.SENT
    before_count = int(server_state["count"])
    with engine.connect() as connection:
        immutable = connection.execute(
            text(
                "SELECT raw_body_sha256, canonical_result_sha256, result_snapshot "
                "FROM story.understanding_revisions WHERE run_id = :run"
            ),
            {"run": run_id},
        ).one()
    assert any(row["run_id"] == run_id for row in repository.pending_vision_ledger_reconciliation())
    repository.recover_after_restart()
    bridge.reconcile_completed_results()
    finished = ledger.get(run_id)
    assert finished is not None and finished.state is InvocationState.SUCCEEDED
    assert finished.result_sha256 == immutable.raw_body_sha256
    assert int(server_state["count"]) == before_count == 1
    bridge.reconcile_completed_results()
    assert int(server_state["count"]) == before_count
    after = repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=run_id)
    assert after.body["run_state"] == (
        "PREPARATION_REVIEW" if transition == "confirm" else "DELETE_PENDING"
    )
    with engine.connect() as connection:
        unchanged = connection.execute(
            text(
                "SELECT raw_body_sha256, canonical_result_sha256, result_snapshot "
                "FROM story.understanding_revisions WHERE run_id = :run"
            ),
            {"run": run_id},
        ).one()
    assert unchanged == immutable


def test_reconcile_does_not_finalize_mismatching_tuple_or_result_hash(
    loopback_runtime,
    monkeypatch,
) -> None:
    engine, repository, bridge, server_state, _server_lock = loopback_runtime
    _owner, run_id, binding, claim = _create_attached_run(repository, "review-ledger-mismatch")
    original_finalize = InvocationLedgerGuard.finalize

    def hold_finalize(guard, state, result_sha256=None):
        if state is InvocationTerminalState.SUCCEEDED:
            return False
        return original_finalize(guard, state, result_sha256)

    monkeypatch.setattr(InvocationLedgerGuard, "finalize", hold_finalize)
    outcome = bridge.analyze(
        run_id=run_id,
        binding=binding,
        persist_success=_persist_callback(repository, engine, run_id, claim, []),
    )
    assert outcome.result_committed
    monkeypatch.setattr(InvocationLedgerGuard, "finalize", original_finalize)
    ledger = InvocationLedger(engine)
    original = ledger.get(run_id)
    assert original is not None and original.state is InvocationState.SENT
    with engine.begin() as connection:
        raw_hash = connection.execute(
            text("SELECT raw_body_sha256 FROM story.runs WHERE run_id = :run"), {"run": run_id}
        ).scalar_one()
        connection.execute(
            text("UPDATE story.runs SET provider_attempt_id = :attempt WHERE run_id = :run"),
            {"run": run_id, "attempt": str(uuid.uuid4())},
        )
    bridge.reconcile_completed_results()
    assert ledger.get(run_id).state is InvocationState.SENT
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE story.runs SET provider_attempt_id = :attempt, raw_body_sha256 = :hash "
                "WHERE run_id = :run"
            ),
            {"run": run_id, "attempt": original.attempt_id, "hash": "0" * 64},
        )
    bridge.reconcile_completed_results()
    assert ledger.get(run_id).state is InvocationState.SENT
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE story.runs SET raw_body_sha256 = :hash WHERE run_id = :run"),
            {"run": run_id, "hash": raw_hash},
        )
    bridge.reconcile_completed_results()
    assert ledger.get(run_id).state is InvocationState.SUCCEEDED
    assert int(server_state["count"]) == 1
