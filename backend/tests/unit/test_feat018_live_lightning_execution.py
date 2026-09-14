from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from sketch2life.benchmark import feat018_live_lightning_execution as execution
from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenPermanentRuntimeError,
    QwenTransientRuntimeError,
    QwenVisionAdapter,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_PROFILE = vision_profile_catalog_v2().profiles[0]
_PROMPT = "approved synthetic prompt"
_PROMPT_SHA256 = sha256(_PROMPT.encode("utf-8")).hexdigest()
_EXECUTED_AT = datetime(2026, 9, 13, tzinfo=UTC)
_EMPTY_RAW = json.dumps(
    {
        "entities": [],
        "actions": [],
        "relations": [],
        "themes": [],
        "ambiguous_regions": [],
    },
    separators=(",", ":"),
)


def _caps(
    *,
    total: float = 10.0,
    raw: int = 128,
    ipc: int = 512,
    stdout: int = 0,
    stderr: int = 0,
) -> execution.LiveLightningExecutionCaps:
    return execution.LiveLightningExecutionCaps(
        total_adapter_cap_seconds=total,
        raw_output_max_bytes=raw,
        ipc_envelope_max_bytes=ipc,
        stdout_max_bytes=stdout,
        stderr_max_bytes=stderr,
    )


def _policy() -> LexicalRegressionContentPolicy:
    return LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())


def _pass_validation() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:feat018:validation-pass",
        validation_artifact_sha256="c" * 64,
        decision="PASS",
        validator_policy_version="media-quality-policy-v1",
    )


def _request(artifact_ref: str = "drawing.png") -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id="feat018-live-test-correlation",
        source_image_ref=VisionImageReferenceV1(
            artifact_ref=artifact_ref,
            sha256="a" * 64,
        ),
        media_validation=_pass_validation(),
        requested_profile_id=_PROFILE.profile_id,
    )


def _request_with_digest(artifact_ref: str, digest: str) -> VisionUnderstandingRequestV2:
    return _request(artifact_ref).model_copy(
        update={
            "source_image_ref": VisionImageReferenceV1(
                artifact_ref=artifact_ref,
                sha256=digest,
            )
        }
    )


def _success_result(
    request: VisionUnderstandingRequestV2, *, attempt: int = 1
) -> VisionUnderstandingSuccessV2:
    return VisionUnderstandingSuccessV2(
        correlation_id=request.correlation_id,
        executed_at=_EXECUTED_AT,
        source_image_ref=request.source_image_ref,
        profile_id=_PROFILE.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        attempt_number=attempt,
        repair_attempted=False,
        content_policy_version="vision-prohibited-lexicon-fixture-v1",
        policy_match_view_version="vision-policy-match-view-v2",
        policy_execution_state="PASSED",
        entities=(),
        actions=(),
        relations=(),
        themes=(),
        ambiguous_regions=(),
        adapter_version=_PROFILE.adapter_version,
        config_hash=vision_profile_config_hash_v2(_PROFILE),
        model_provenance=_PROFILE.model_provenance,
    )


def _failure_result(
    request: VisionUnderstandingRequestV2,
    *,
    detail: VisionNonPolicyErrorDetailV2,
    attempt: int,
    retryable: bool = False,
) -> VisionUnderstandingFailureV2:
    return VisionUnderstandingFailureV2(
        correlation_id=request.correlation_id,
        executed_at=_EXECUTED_AT,
        source_image_ref=request.source_image_ref,
        profile_id=_PROFILE.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        attempt_number=attempt,
        repair_attempted=False,
        content_policy_version="vision-prohibited-lexicon-fixture-v1",
        policy_match_view_version="vision-policy-match-view-v2",
        policy_execution_state="NOT_EXECUTED",
        error_code=(
            VisionErrorCode.VISION_PROVIDER_FAILURE
            if detail
            in {
                VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE,
                VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
            }
            else VisionErrorCode.VISION_TIMEOUT
        ),
        error_detail=detail,
        retryable=retryable,
        model_provenance=_PROFILE.model_provenance,
    )


class _FakeAdapter:
    def __init__(self, *outcomes: object) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0
        self.attempt_trace: tuple[execution.GenerationAttemptOutcome, ...] | None = None

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        del request
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return cast(VisionUnderstandingResultV2, outcome)


class _FakeMapper:
    def __init__(self, result: object = "mapped") -> None:
        self.result = result
        self.calls: list[tuple[object, dict[str, object]]] = []

    def __call__(self, result: object, **kwargs: object) -> object:
        self.calls.append((result, kwargs))
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


class _FakeReceiver:
    def __init__(self, payload: bytes, *, poll_result: bool = True) -> None:
        self.payload = payload
        self.poll_result = poll_result
        self.poll_timeouts: list[float] = []
        self.closed = False

    def poll(self, timeout: float) -> bool:
        self.poll_timeouts.append(timeout)
        return self.poll_result

    def recv_bytes(self, maxlength: int = -1) -> bytes:
        if len(self.payload) > maxlength:
            raise OSError("oversized envelope detail must not cross the boundary")
        return self.payload

    def send_bytes(self, buffer: bytes) -> None:
        del buffer

    def close(self) -> None:
        self.closed = True


class _FakeSender:
    def __init__(self) -> None:
        self.closed = False
        self.sent: list[bytes] = []

    def poll(self, timeout: float) -> bool:
        del timeout
        return False

    def recv_bytes(self, maxlength: int = -1) -> bytes:
        del maxlength
        return b""

    def send_bytes(self, buffer: bytes) -> None:
        self.sent.append(buffer)

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    def __init__(self, *, alive: bool = False) -> None:
        self.pid = 9911
        self.alive = alive
        self.started = False
        self.join_calls: list[float | None] = []
        self.terminate_calls = 0
        self.kill_calls = 0

    def start(self) -> None:
        self.started = True

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout: float | None = None) -> None:
        self.join_calls.append(timeout)

    def terminate(self) -> None:
        self.terminate_calls += 1
        self.alive = False

    def kill(self) -> None:
        self.kill_calls += 1
        self.alive = False


class _ProcessFactory:
    def __init__(self, *, alive: bool = False) -> None:
        self.alive = alive
        self.processes: list[_FakeProcess] = []
        self.args: list[tuple[object, ...]] = []

    def __call__(self, *args: object, **kwargs: object) -> _FakeProcess:
        del args
        process = _FakeProcess(alive=self.alive)
        self.processes.append(process)
        self.args.append(cast(tuple[object, ...], kwargs["args"]))
        return process


class _PipeFactory:
    def __init__(self, payloads: list[bytes], *, poll_result: bool = True) -> None:
        self.receivers = [_FakeReceiver(payload, poll_result=poll_result) for payload in payloads]
        self.senders = [_FakeSender() for _ in payloads]

    def __call__(self) -> tuple[_FakeReceiver, _FakeSender]:
        return self.receivers.pop(0), self.senders.pop(0)


def _payload(kind: str, raw_output: str | None = None) -> bytes:
    body: dict[str, object] = {"kind": kind}
    if raw_output is not None:
        body["raw_output"] = raw_output
    return json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def _runner(
    payloads: list[bytes],
    *,
    caps: execution.LiveLightningExecutionCaps | None = None,
    poll_result: bool = True,
    alive: bool = False,
    clock: Any = None,
    cleanup_calls: list[str] | None = None,
    terminations: list[int] | None = None,
) -> tuple[execution.Feat018BoundedKillableQwenGenerationRunner, _PipeFactory, _ProcessFactory]:
    pipe_factory = _PipeFactory(payloads, poll_result=poll_result)
    process_factory = _ProcessFactory(alive=alive)
    if cleanup_calls is None:
        cleanup_calls = []
    if terminations is None:
        terminations = []

    def terminate(process: Any) -> None:
        terminations.append(process.pid)
        process.alive = False

    runner = execution.Feat018BoundedKillableQwenGenerationRunner(
        caps or _caps(),
        process_factory=cast(Any, process_factory),
        pipe_factory=pipe_factory,
        process_tree_terminator=terminate,
        resource_cleanup=lambda: cleanup_calls.append("cleanup"),
        clock=clock or (lambda: 0.0),
    )
    return runner, pipe_factory, process_factory


def _adapter_with_runner(
    runner: execution.Feat018BoundedKillableQwenGenerationRunner,
) -> QwenVisionAdapter:
    return QwenVisionAdapter(
        QwenVisionRuntimeConfig(model_dir=Path("model")),
        content_policy=_policy(),
        prompt=_PROMPT,
        generation_runner=runner,
    )


def _write_source(tmp_path: Path) -> tuple[str, str]:
    content = b"synthetic-feat018-live-image"
    path = tmp_path / "drawing.png"
    path.write_bytes(content)
    return path.name, sha256(content).hexdigest()


def test_caps_require_explicit_non_plan_values_and_fix_120_second_attempt_deadline() -> None:
    caps = _caps()

    assert caps.per_attempt_timeout_seconds == 120.0
    with pytest.raises(ValueError):
        execution.LiveLightningExecutionCaps(
            total_adapter_cap_seconds=1.0,
            raw_output_max_bytes=1,
            ipc_envelope_max_bytes=1,
            stdout_max_bytes=0,
            stderr_max_bytes=0,
            per_attempt_timeout_seconds=119.0,
        )
    with pytest.raises(ValueError):
        execution.LiveLightningExecutionCaps(
            total_adapter_cap_seconds=1.0,
            raw_output_max_bytes=0,
            ipc_envelope_max_bytes=1,
            stdout_max_bytes=0,
            stderr_max_bytes=0,
        )


def test_pre_adapter_rejection_keeps_zero_call_and_null_attempt_and_cleans_up() -> None:
    request = _request()
    adapter = _FakeAdapter(_success_result(request))
    cleaned: list[str] = []

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=adapter,
        caps=_caps(),
        pre_adapter_check=lambda: False,
        cleanup=lambda: cleaned.append("cleanup"),
    )

    assert result.status == "FAILED"
    assert (
        result.run_failure_code
        is execution.LiveLightningExecutionFailureCode.PRE_ADAPTER_REJECTED
    )
    assert result.adapter_call_count == 0
    assert result.attempt_count is None
    assert adapter.calls == 0
    assert cleaned == ["cleanup"]


def test_prompt_hash_mismatch_is_a_pre_adapter_stop() -> None:
    request = _request()
    adapter = _FakeAdapter(_success_result(request))

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=adapter,
        caps=_caps(),
        prompt_text="different prompt",
        expected_prompt_sha256=_PROMPT_SHA256,
    )

    assert (
        result.run_failure_code is execution.LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH
    )
    assert result.adapter_call_count == 0
    assert result.attempt_count is None
    assert adapter.calls == 0


def test_adapter_input_rejection_is_one_call_and_zero_model_attempts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    request = _request_with_digest(artifact_ref, digest).model_copy(
        update={"media_validation": _pass_validation().model_copy(update={"decision": "RECAPTURE"})}
    )
    runner, pipe, _process = _runner([])
    mapper = _FakeMapper()

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_adapter_with_runner(runner),
        caps=runner.caps,
        runner=runner,
        prompt_text=_PROMPT,
        expected_prompt_sha256=_PROMPT_SHA256,
        mapper=mapper,
    )

    assert result.status == "FAILED"
    assert result.run_failure_code is None
    assert result.adapter_call_count == 1
    assert result.attempt_count == 0
    assert isinstance(result.vision_result, VisionUnderstandingFailureV2)
    assert result.vision_result.error_code is VisionErrorCode.INPUT_NOT_VALIDATED
    assert runner.last_attempt_trace == ()
    assert not pipe.receivers
    assert len(mapper.calls) == 1


def test_success_maps_once_and_preserves_explicit_prompt_and_exact_counter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    request = _request_with_digest(artifact_ref, digest)
    runner, pipe, process_factory = _runner([_payload("success", _EMPTY_RAW)])
    mapper = _FakeMapper()

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_adapter_with_runner(runner),
        caps=runner.caps,
        runner=runner,
        prompt_text=_PROMPT,
        expected_prompt_sha256=_PROMPT_SHA256,
        mapper=mapper,
    )

    assert result.status == "SUCCEEDED"
    assert result.run_failure_code is None
    assert result.adapter_call_count == 1
    assert result.attempt_count == 1
    assert isinstance(result.vision_result, VisionUnderstandingSuccessV2)
    assert result.mapped_result == "mapped"
    assert runner.last_attempt_trace == (execution.GenerationAttemptOutcome.SUCCESS,)
    assert process_factory.args[0][3] == artifact_ref
    assert len(pipe.receivers) == 0
    assert mapper.calls[0][1] == {
        "session_id": "feat018-live-smoke",
        "expected_source_sha256": digest,
        "expected_correlation_id": request.correlation_id,
        "asr_result": None,
    }


def test_transient_runtime_failure_retries_inside_one_adapter_call_only_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    request = _request_with_digest(artifact_ref, digest)
    runner, _pipe, process_factory = _runner(
        [_payload("transient_runtime_failure"), _payload("success", _EMPTY_RAW)]
    )

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_adapter_with_runner(runner),
        caps=runner.caps,
        runner=runner,
        prompt_text=_PROMPT,
        expected_prompt_sha256=_PROMPT_SHA256,
    )

    assert result.status == "SUCCEEDED"
    assert result.adapter_call_count == 1
    assert result.attempt_count == 2
    assert runner.last_attempt_trace == (
        execution.GenerationAttemptOutcome.TRANSIENT_RUNTIME_FAILURE,
        execution.GenerationAttemptOutcome.SUCCESS,
    )
    assert len(process_factory.processes) == 2


def test_non_transient_failure_does_not_retry() -> None:
    request = _request()
    failure = _failure_result(
        request,
        detail=VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
        attempt=1,
    )
    adapter = _FakeAdapter(failure)

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=adapter,
        caps=_caps(),
    )

    assert result.status == "FAILED"
    assert result.adapter_call_count == 1
    assert result.attempt_count == 1
    assert adapter.calls == 1
    assert isinstance(result.vision_result, VisionUnderstandingFailureV2)


def test_per_attempt_timeout_terminates_process_tree_and_returns_typed_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    request = _request_with_digest(artifact_ref, digest)
    cleanup_calls: list[str] = []
    terminations: list[int] = []
    runner, pipe, process_factory = _runner(
        [_payload("success", _EMPTY_RAW)],
        caps=_caps(total=120.0),
        poll_result=False,
        alive=True,
        cleanup_calls=cleanup_calls,
        terminations=terminations,
    )

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_adapter_with_runner(runner),
        caps=runner.caps,
        runner=runner,
        prompt_text=_PROMPT,
        expected_prompt_sha256=_PROMPT_SHA256,
    )

    assert result.status == "FAILED"
    assert result.adapter_call_count == 1
    assert result.attempt_count == 1
    assert isinstance(result.vision_result, VisionUnderstandingFailureV2)
    assert result.vision_result.error_code is VisionErrorCode.VISION_TIMEOUT
    assert (
        result.run_failure_code is execution.LiveLightningExecutionFailureCode.PER_ATTEMPT_TIMEOUT
    )
    assert not pipe.receivers
    assert terminations == [process_factory.processes[0].pid]
    assert process_factory.processes[0].alive is False
    assert cleanup_calls == ["cleanup"]


def test_per_attempt_deadline_starts_after_child_process_start() -> None:
    now = [0.0]
    receiver = _FakeReceiver(_payload("success", _EMPTY_RAW))
    sender = _FakeSender()

    class DelayedStartProcess(_FakeProcess):
        def start(self) -> None:
            super().start()
            now[0] = 5.0

    process = DelayedStartProcess()

    def process_factory(*args: object, **kwargs: object) -> _FakeProcess:
        del args
        del kwargs
        return process

    runner = execution.Feat018BoundedKillableQwenGenerationRunner(
        _caps(total=500.0),
        process_factory=cast(Any, process_factory),
        pipe_factory=lambda: (receiver, sender),
        process_tree_terminator=lambda child: setattr(child, "alive", False),
        resource_cleanup=lambda: None,
        clock=lambda: now[0],
    )

    assert (
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )
        == _EMPTY_RAW
    )
    assert receiver.poll_timeouts == [120.0]


def test_total_adapter_cap_is_shared_across_adapter_call_and_retry_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    request = _request_with_digest(artifact_ref, digest)
    times = iter((0.0, 0.0, 0.6, 0.6))
    runner, _pipe, _process_factory = _runner(
        [_payload("success", _EMPTY_RAW)],
        caps=_caps(total=0.5),
        clock=lambda: next(times),
    )

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_adapter_with_runner(runner),
        caps=runner.caps,
        runner=runner,
        prompt_text=_PROMPT,
        expected_prompt_sha256=_PROMPT_SHA256,
        content_policy=_policy(),
    )

    assert result.status == "FAILED"
    assert (
        result.run_failure_code
        is execution.LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED
    )
    assert result.adapter_call_count == 1
    assert result.attempt_count == 1
    assert isinstance(result.vision_result, VisionUnderstandingFailureV2)
    assert result.vision_result.error_code is VisionErrorCode.VISION_TIMEOUT
    assert runner.last_attempt_trace == (execution.GenerationAttemptOutcome.TIMEOUT,)


def test_raw_output_and_complete_serialized_ipc_envelopes_are_bounded() -> None:
    caps = _caps(raw=4, ipc=64)
    assert execution._worker_success_envelope("12345", caps) == {"kind": "raw_output_too_large"}
    assert execution._worker_success_envelope("1234", _caps(raw=4, ipc=20)) == {
        "kind": "ipc_envelope_too_large"
    }

    receiver = _FakeReceiver(_payload("success", "123456789"))
    sender = _FakeSender()
    process_factory = _ProcessFactory()
    runner = execution.Feat018BoundedKillableQwenGenerationRunner(
        _caps(raw=4, ipc=512),
        process_factory=cast(Any, process_factory),
        pipe_factory=lambda: (receiver, sender),
        process_tree_terminator=lambda process: setattr(process, "alive", False),
        resource_cleanup=lambda: None,
        clock=lambda: 0.0,
    )

    with pytest.raises(QwenPermanentRuntimeError):
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )
    assert (
        runner.last_failure_code
        is execution.LiveLightningExecutionFailureCode.RAW_OUTPUT_TOO_LARGE
    )


def test_worker_rejects_oversized_raw_output_before_ipc(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[bytes] = []

    class Connection:
        def send_bytes(self, payload: bytes) -> None:
            sent.append(payload)

        def close(self) -> None:
            return None

    monkeypatch.setattr(execution, "_default_model_factory", lambda _profile, _config: object())
    monkeypatch.setattr(execution, "_generate_from_bundle", lambda *_args: "12345")

    execution._bounded_qwen_worker_entry(
        cast(Any, Connection()),
        _PROFILE,
        QwenVisionRuntimeConfig(model_dir=Path("model")),
        "drawing.png",
        _PROMPT,
        _caps(raw=4),
    )

    assert json.loads(sent[0]) == {"kind": "raw_output_too_large"}


@pytest.mark.parametrize(
    ("stream_name", "patch_name"),
    [("stdout", "stdout"), ("stderr", "stderr")],
)
def test_worker_enforces_non_persistent_stdout_and_stderr_ceilings(
    monkeypatch: pytest.MonkeyPatch, stream_name: str, patch_name: str
) -> None:
    sent: list[bytes] = []

    class Connection:
        def send_bytes(self, payload: bytes) -> None:
            sent.append(payload)

        def close(self) -> None:
            return None

    def noisy_generate(*_args: object) -> str:
        print("too much", file=getattr(__import__("sys"), patch_name))
        return "{}"

    monkeypatch.setattr(execution, "_default_model_factory", lambda _profile, _config: object())
    monkeypatch.setattr(execution, "_generate_from_bundle", noisy_generate)

    execution._bounded_qwen_worker_entry(
        cast(Any, Connection()),
        _PROFILE,
        QwenVisionRuntimeConfig(model_dir=Path("model")),
        "drawing.png",
        _PROMPT,
        _caps(
            stdout=2 if stream_name == "stdout" else 0,
            stderr=2 if stream_name == "stderr" else 0,
        ),
    )

    assert json.loads(sent[0]) == {"kind": f"{stream_name}_too_large"}


def test_malformed_child_response_is_typed_and_fail_closed() -> None:
    runner, _pipe, _process_factory = _runner([b"not-json"])

    with pytest.raises(QwenPermanentRuntimeError) as error:
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )

    assert str(error.value) == ""
    assert (
        runner.last_failure_code
        is execution.LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
    )


def test_ipc_recv_overflow_is_distinguished_from_malformed_payload() -> None:
    oversized = b"x" * 600
    runner, _pipe, _process_factory = _runner([oversized])

    with pytest.raises(QwenPermanentRuntimeError):
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )

    assert (
        runner.last_failure_code
        is execution.LiveLightningExecutionFailureCode.IPC_ENVELOPE_TOO_LARGE
    )


def test_process_cleanup_runs_on_success_even_when_child_is_still_alive() -> None:
    terminations: list[int] = []
    cleanup_calls: list[str] = []
    runner, _pipe, process_factory = _runner(
        [_payload("success", _EMPTY_RAW)],
        alive=True,
        cleanup_calls=cleanup_calls,
        terminations=terminations,
    )

    assert (
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )
        == _EMPTY_RAW
    )
    assert terminations == [process_factory.processes[0].pid]
    assert cleanup_calls == ["cleanup"]


def test_cleanup_failure_is_typed_and_overrides_success() -> None:
    runner, _pipe, _process_factory = _runner([_payload("success", _EMPTY_RAW)])

    def fail_cleanup() -> None:
        raise RuntimeError("secret cleanup detail")

    runner._resource_cleanup = fail_cleanup
    with pytest.raises(QwenPermanentRuntimeError) as error:
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )

    assert str(error.value) == ""
    assert runner.last_failure_code is execution.LiveLightningExecutionFailureCode.CLEANUP_FAILED


def test_typed_adapter_failure_has_no_outer_retry() -> None:
    request = _request()
    transient_terminal = _failure_result(
        request,
        detail=VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE,
        attempt=2,
        retryable=True,
    )
    adapter = _FakeAdapter(transient_terminal)
    adapter.attempt_trace = (
        execution.GenerationAttemptOutcome.TRANSIENT_RUNTIME_FAILURE,
        execution.GenerationAttemptOutcome.TRANSIENT_RUNTIME_FAILURE,
    )

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=adapter,
        caps=_caps(),
    )

    assert result.status == "FAILED"
    assert result.adapter_call_count == 1
    assert result.attempt_count == 2
    assert adapter.calls == 1


def test_invalid_attempt_two_without_transient_trace_fails_closed() -> None:
    request = _request()
    adapter = _FakeAdapter(_success_result(request, attempt=2))

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=adapter,
        caps=_caps(),
        runner=None,
    )

    assert result.status == "FAILED"
    assert (
        result.run_failure_code is execution.LiveLightningExecutionFailureCode.INVALID_CARDINALITY
    )


def test_cleanup_runs_for_typed_failure_mapper_failure_and_pre_adapter_stop() -> None:
    request = _request()
    cleaned: list[str] = []
    failure = _failure_result(
        request,
        detail=VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
        attempt=1,
    )

    for adapter, mapper, precheck in (
        (_FakeAdapter(failure), None, None),
        (_FakeAdapter(_success_result(request)), _FakeMapper(RuntimeError("raw secret")), None),
        (_FakeAdapter(_success_result(request)), None, lambda: False),
    ):
        execution.run_feat018_live_lightning_execution(
            request,
            adapter=adapter,
            caps=_caps(),
            mapper=mapper,
            pre_adapter_check=precheck,
            cleanup=lambda: cleaned.append("cleanup"),
        )

    assert cleaned == ["cleanup", "cleanup", "cleanup"]


def test_safe_evidence_is_allowlisted_and_contains_no_raw_or_path_values() -> None:
    request = _request()
    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_FakeAdapter(_success_result(request)),
        caps=_caps(),
    )
    evidence = result.sanitized_evidence(
        run_id="run-001",
        correlation_id=request.correlation_id,
        session_id="feat018-live-smoke",
        caps=_caps(),
        prompt_protocol_id="prompt-v1",
        prompt_sha256=_PROMPT_SHA256,
        fixture_id="fixture-001",
        source_sha256="a" * 64,
    )
    serialized = json.dumps(evidence, sort_keys=True)

    assert "raw provider output" not in serialized
    assert "secret" not in serialized
    assert "C:\\Users" not in serialized
    assert "/private/" not in serialized
    assert "prompt text" not in serialized
    assert evidence["adapter_call_count"] == 1
    assert evidence["attempt_count"] == 1

    with pytest.raises(ValueError):
        execution._validate_safe_evidence({**evidence, "raw_output": "secret"})
    with pytest.raises(ValueError):
        execution._validate_safe_evidence({**evidence, "narration_status": "secret"})


def test_sanitized_pair_and_ignored_incident_do_not_overwrite_and_do_not_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    request = _request()
    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=_FakeAdapter(_success_result(request)),
        caps=_caps(),
    )
    evidence = result.sanitized_evidence(
        run_id="run-002",
        correlation_id=request.correlation_id,
        session_id="feat018-live-smoke",
        caps=_caps(),
    )
    json_path = Path("evidence") / "run.json"
    markdown_path = Path("evidence") / "run.md"

    execution.write_sanitized_evidence_pair(evidence, json_path, markdown_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "SUCCEEDED"
    with pytest.raises(FileExistsError):
        execution.write_sanitized_evidence_pair(evidence, json_path, markdown_path)

    incident = execution.write_ignored_incident(
        "run-003",
        execution.LiveLightningExecutionFailureCode.EVIDENCE_FAILED,
    )
    text = incident.read_text(encoding="utf-8")
    assert "NOT_RECORDED" in text
    assert "secret" not in text
    with pytest.raises(FileExistsError):
        execution.write_ignored_incident(
            "run-003",
            execution.LiveLightningExecutionFailureCode.EVIDENCE_FAILED,
        )


def test_repeated_fake_execution_is_deterministic_and_does_not_add_an_outer_attempt() -> None:
    request = _request()
    caps = _caps()
    results = [
        execution.run_feat018_live_lightning_execution(
            request,
            adapter=_FakeAdapter(_success_result(request)),
            caps=caps,
        )
        for _ in range(2)
    ]
    evidences = [
        result.sanitized_evidence(
            run_id="repeat-001",
            correlation_id=request.correlation_id,
            session_id="feat018-live-smoke",
            caps=caps,
        )
        for result in results
    ]

    assert evidences[0] == evidences[1]
    assert all(result.adapter_call_count == 1 for result in results)
    assert all(result.attempt_count == 1 for result in results)


def test_create_adapter_requires_explicit_prompt_and_runner() -> None:
    runner, _pipe, _process_factory = _runner([_payload("success", _EMPTY_RAW)])
    config = QwenVisionRuntimeConfig(model_dir=Path("model"))

    with pytest.raises(ValueError):
        execution.create_qwen_vision_adapter(
            config,
            content_policy=_policy(),
            prompt="",
            generation_runner=runner,
        )

    adapter = execution.create_qwen_vision_adapter(
        config,
        content_policy=_policy(),
        prompt=_PROMPT,
        generation_runner=runner,
    )
    assert isinstance(adapter, QwenVisionAdapter)


def test_unknown_runner_exception_is_sanitized_and_not_retried() -> None:
    request = _request()
    adapter = _FakeAdapter(RuntimeError("provider secret /absolute/path"))

    result = execution.run_feat018_live_lightning_execution(
        request,
        adapter=adapter,
        caps=_caps(),
    )

    assert result.status == "FAILED"
    assert result.run_failure_code is execution.LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION
    assert adapter.calls == 1
    assert result.vision_result is None


def test_runner_transient_exception_is_the_only_retryable_runner_signal() -> None:
    runner, _pipe, _process_factory = _runner([_payload("transient_runtime_failure")])

    with pytest.raises(QwenTransientRuntimeError):
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )

    assert runner.last_attempt_trace == (
        execution.GenerationAttemptOutcome.TRANSIENT_RUNTIME_FAILURE,
    )


def test_permanent_runner_failure_is_not_translated_to_retryable_output() -> None:
    runner, _pipe, _process_factory = _runner([_payload("permanent_runtime_failure")])

    with pytest.raises(QwenPermanentRuntimeError):
        runner.generate(
            _PROFILE,
            QwenVisionRuntimeConfig(model_dir=Path("model")),
            Path("drawing.png"),
            _PROMPT,
        )

    assert runner.last_attempt_trace == (
        execution.GenerationAttemptOutcome.PERMANENT_RUNTIME_FAILURE,
    )
