"""BE2-01 Phase B batch B5 offline checks: HMAC attempt-bound worker capability (Δ8/Δ14),
the worker loop on fakes and capability redaction in log records.

Fakes and an in-memory clock only: real Redis/RQ/PostgreSQL evidence is in
tests/integration/ai_jobs/test_capability.py (skipped without services = NOT_RUN).
"""

from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest

from sketch2life.application.ports.ai_jobs import DispatchMessage, WorkerDispatchEnvelope
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    FIXTURE_RETRY_POLICY,
    AiJobDependencies,
    AiJobError,
    AiJobService,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim
from sketch2life.domain.ai_jobs.model import JobState, ProgressKind
from sketch2life.infrastructure.ai_jobs import rq_queue
from sketch2life.infrastructure.ai_jobs.fakes import FakeClock, FakeProvider
from sketch2life.infrastructure.ai_jobs.harness import (
    FIXTURE_START,
    FixtureHarness,
    build_fixture_harness,
)
from sketch2life.infrastructure.ai_jobs.worker import (
    REDACTED,
    CapabilityRedactionFilter,
    DispatchWorker,
    install_worker,
)
from sketch2life.infrastructure.ai_jobs.worker_capability import (
    FIXTURE_CAPABILITY_TTL,
    CapabilityKey,
    HmacCapabilityIssuer,
    HmacCapabilityVerifier,
)

TTL = FIXTURE_CAPABILITY_TTL


def _key(key_id: str = "k1") -> CapabilityKey:
    return CapabilityKey(key_id, os.urandom(32))  # ephemeral per test, never persisted


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(FIXTURE_START)


@pytest.fixture
def h() -> FixtureHarness:
    """Fixture harness whose service issues and verifies real HMAC capabilities."""

    h = build_fixture_harness()
    key = _key()
    issuer = HmacCapabilityIssuer(key)
    deps = h.service._d
    values = {name: getattr(deps, name) for name in deps.__dataclass_fields__}
    values.update(capability_issuer=issuer,
                  worker_capability=HmacCapabilityVerifier(key, h.clock))
    h.service = AiJobService(AiJobDependencies(**values))
    h.capabilities = issuer  # type: ignore[assignment]  # h.capability() mints HMAC tokens
    return h


# ----------------------------------------------------------------------- HMAC token unit
def test_round_trip_binds_job_attempt_times_and_key(clock: FakeClock) -> None:
    key = _key("k_main")
    token = HmacCapabilityIssuer(key).issue("job_1", "att_1", clock.now())
    verified = HmacCapabilityVerifier(key, clock).verify(token)
    assert verified is not None
    assert (verified.job_id, verified.attempt_id, verified.key_id) == ("job_1", "att_1", "k_main")
    assert (verified.issued_at, verified.expires_at) == (clock.now(), clock.now() + TTL)


@pytest.mark.parametrize(
    "token",
    ["", "wcap.v1", "wcap.v2.k1.e30.AAAA", "not-a-token", "wcap.v1.k1.%%%.%%%",
     "wcap.v1.k1.e30", "x" * 5000],
)
def test_malformed_tokens_are_denied(clock: FakeClock, token: str) -> None:
    assert HmacCapabilityVerifier(_key(), clock).verify(token) is None


def test_non_string_tokens_are_denied(clock: FakeClock) -> None:
    verifier = HmacCapabilityVerifier(_key(), clock)
    for value in (None, 7, b"wcap.v1"):
        assert verifier.verify(value) is None  # type: ignore[arg-type]


def test_tampered_claims_or_signature_are_denied(clock: FakeClock) -> None:
    key = _key()
    token = HmacCapabilityIssuer(key).issue("job_1", "att_1", clock.now())
    prefix, version, key_id, body, signature = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(body + "=="))
    forged_body = _b64(json.dumps({**claims, "a": "att_2"}, sort_keys=True,
                                  separators=(",", ":")).encode())
    verifier = HmacCapabilityVerifier(key, clock)
    assert verifier.verify(".".join([prefix, version, key_id, forged_body, signature])) is None
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    assert verifier.verify(".".join([prefix, version, key_id, body, flipped])) is None
    assert verifier.verify(token) is not None


def test_unknown_key_and_rotation(clock: FakeClock) -> None:
    old, new = _key("k_old"), _key("k_new")
    old_token = HmacCapabilityIssuer(old).issue("job_1", "att_1", clock.now())
    new_token = HmacCapabilityIssuer(new).issue("job_1", "att_1", clock.now())
    both = HmacCapabilityVerifier({"k_old": old, "k_new": new}, clock)
    assert both.verify(old_token) is not None and both.verify(new_token) is not None
    only_new = HmacCapabilityVerifier(new, clock)
    assert only_new.verify(old_token) is None and only_new.verify(new_token) is not None
    # Same key id, different key bytes: signature does not verify.
    impostor = HmacCapabilityVerifier(CapabilityKey("k_new", os.urandom(32)), clock)
    assert impostor.verify(new_token) is None


def test_expiry_is_exclusive_at_expires_at(clock: FakeClock) -> None:
    key = _key()
    token = HmacCapabilityIssuer(key).issue("job_1", "att_1", clock.now())
    verifier = HmacCapabilityVerifier(key, clock)
    clock.advance(milliseconds=TTL // timedelta(milliseconds=1) - 1)
    assert verifier.verify(token) is not None
    clock.advance(milliseconds=1)
    assert verifier.verify(token) is None


def test_key_material_never_appears_in_repr_or_tokens(clock: FakeClock) -> None:
    raw = os.urandom(32)
    key = CapabilityKey("k1", raw)
    token = HmacCapabilityIssuer(key).issue("job_1", "att_1", clock.now())
    for text in (repr(key), str(key), repr(HmacCapabilityIssuer(key)),
                 repr(HmacCapabilityVerifier(key, clock)), token):
        assert raw.hex() not in text and _b64(raw) not in text
    with pytest.raises(ValueError):
        CapabilityKey("k1", b"short")
    with pytest.raises(ValueError):
        CapabilityKey("Bad.Id", raw)


def test_fixture_ttl_matches_the_dispatch_profile() -> None:
    assert timedelta(milliseconds=FIXTURE_DISPATCH_POLICY.capability_ttl_ms) == TTL
    assert FIXTURE_DISPATCH_POLICY.notice_atomic_max == 100


# --------------------------------------------------------------- service attempt binding
def _code(fn: Any) -> str:
    with pytest.raises(AiJobError) as error:
        fn()
    assert error.value.http_status == 403
    return error.value.code


def _retry_to_second_attempt(h: FixtureHarness) -> tuple[str, DispatchMessage, DispatchMessage]:
    job_id = h.service.create_job(h.create()).job_id
    first = h.start_next()
    h.service.accept_completion(h.last_envelope.capability,  # type: ignore[union-attr]
                                h.failure_claim(first))
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert h.service.run_due_retries() == (job_id,)
    second = h.next_message()
    return job_id, first, second


def test_token_for_attempt_a_cannot_start_progress_or_complete_attempt_b(
    h: FixtureHarness,
) -> None:
    job_id, first, second = _retry_to_second_attempt(h)
    token_a = h.capability(job_id, first.attempt_id)
    assert _code(lambda: h.service.start_attempt(token_a, job_id, second.attempt_id)) == (
        "WORKER_CAPABILITY_INVALID"
    )
    assert h.store.snapshot().jobs[job_id].state is JobState.QUEUED
    token_b = h.last_envelope.capability  # type: ignore[union-attr]
    assert h.service.start_attempt(token_b, job_id, second.attempt_id).started
    progress = h.store.snapshot().jobs[job_id].progress
    assert _code(lambda: h.service.report_progress(
        token_a, job_id, second.attempt_id, replace(progress, kind=ProgressKind.UNKNOWN)
    )) == "WORKER_CAPABILITY_INVALID"
    assert _code(lambda: h.service.accept_completion(token_a, h.success_claim(second))) == (
        "WORKER_CAPABILITY_INVALID"
    )
    assert h.service.accept_completion(token_b, h.success_claim(second)).authoritative


def test_wrong_job_tampered_and_expired_tokens_are_denied(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    other = h.service.create_job(h.create(key="idem_other",
                                          ref=replace(h.create().request_ref,
                                                      request_id="req_other"))).job_id
    message = h.next_message()
    token = h.last_envelope.capability  # type: ignore[union-attr]
    other_attempt = h.store.snapshot().jobs[other].active_attempt.attempt_id
    assert _code(lambda: h.service.start_attempt(token, other, other_attempt))
    assert _code(lambda: h.service.start_attempt(token[:-2] + "AA", job_id, message.attempt_id))
    h.clock.advance(milliseconds=TTL // timedelta(milliseconds=1))
    assert _code(lambda: h.service.start_attempt(token, job_id, message.attempt_id))
    assert h.store.snapshot().jobs[job_id].state is JobState.QUEUED


def test_service_rejects_an_expired_claim_even_if_the_verifier_does_not() -> None:
    """Defence in depth: the fake verifier returns expired claims; the service clock denies."""

    fake = build_fixture_harness()
    job_id = fake.service.create_job(fake.create()).job_id
    message = fake.next_message()
    token = fake.capability(job_id)
    fake.clock.advance(milliseconds=TTL // timedelta(milliseconds=1))
    assert fake.capabilities.verify(token) is not None  # the fake does not check expiry
    assert _code(lambda: fake.service.start_attempt(token, job_id, message.attempt_id))
    assert fake.store.snapshot().jobs[job_id].state is JobState.QUEUED


def test_stored_receipt_replay_needs_a_live_token_of_that_attempt(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    token = h.last_envelope.capability  # type: ignore[union-attr]
    claim = h.success_claim(message)
    receipt = h.service.accept_completion(token, claim)
    assert h.service.accept_completion(token, claim) == receipt  # same attempt, still valid
    foreign = h.capability(job_id, "att_not_this_one")
    assert _code(lambda: h.service.accept_completion(foreign, claim))
    h.clock.advance(milliseconds=TTL // timedelta(milliseconds=1))
    assert _code(lambda: h.service.accept_completion(token, claim))  # expired: denied
    assert _code(lambda: h.service.accept_completion(h.capability(job_id, message.attempt_id),
                                                     replace(claim, attempt_id="att_x")))


# --------------------------------------------------------------------- worker on fakes
def test_worker_starts_before_the_provider_then_reports_progress_and_completes(
    h: FixtureHarness,
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    seen: list[tuple[JobState, ProgressKind]] = []

    def script(message: DispatchMessage) -> CompletionClaim:
        job = h.store.snapshot().jobs[message.job_id]
        seen.append((job.state, job.progress.kind))
        return h.success_claim(message)

    provider = FakeProvider(script)
    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    outcome = DispatchWorker(h.service, provider).handle(envelope)
    assert outcome.status == "completed" and outcome.receipt is not None
    assert seen == [(JobState.RUNNING, ProgressKind.STAGES)]  # durable start came first
    assert h.store.snapshot().jobs[job_id].state is JobState.SUCCEEDED
    duplicate = DispatchWorker(h.service, provider).handle(envelope)
    assert (duplicate.status, duplicate.reason_code) == ("not_started", "JOB_NOT_QUEUED")
    assert provider.calls[job_id] == 1  # settled delivery never reaches the provider again


def test_duplicate_delivery_of_a_running_attempt_skips_the_provider(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    provider = FakeProvider(lambda m: h.success_claim(m))
    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    assert h.service.start_attempt(envelope.capability, job_id, envelope.message.attempt_id)
    outcome = DispatchWorker(h.service, provider).handle(envelope)
    assert (outcome.status, outcome.reason_code) == ("not_started", "DUPLICATE_DELIVERY")
    assert provider.calls[job_id] == 0


def test_provider_crash_invents_no_claim_and_timeout_retry_recovers(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id

    def explode(message: DispatchMessage) -> CompletionClaim:
        raise RuntimeError("provider died")

    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    outcome = DispatchWorker(h.service, FakeProvider(explode)).handle(envelope)
    assert (outcome.status, outcome.reason_code) == ("provider_failed", "PROVIDER_ERROR")
    assert h.store.snapshot().completion_receipts == {}
    assert h.store.snapshot().jobs[job_id].state is JobState.RUNNING
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert h.service.expire_overdue_attempts() == (job_id,)
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert h.service.run_due_retries() == (job_id,)
    retried = h.store.snapshot().jobs[job_id]
    assert retried.active_attempt.attempt_number == 2 and retried.state is JobState.QUEUED


def test_capability_is_absent_from_store_receipts_audit_and_history(h: FixtureHarness) -> None:
    h.service.create_job(h.create())
    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    DispatchWorker(h.service, FakeProvider(lambda m: h.success_claim(m))).handle(envelope)
    snapshot = h.store.snapshot()
    stored = repr((snapshot.jobs, snapshot.completion_receipts, snapshot.outbox,
                   snapshot.audit_intents, snapshot.quarantine_intents, h.audit.events))
    assert envelope.capability not in stored and "wcap.v1" not in stored


# ------------------------------------------------------------------- log redaction
class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []
        self.text: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        self.text.append(self.format(record))


def _logger(name: str) -> tuple[logging.Logger, _Capture]:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.filters.clear()
    capture = _Capture()
    logger.addHandler(capture)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addFilter(CapabilityRedactionFilter())
    return logger, capture


def test_redaction_filter_covers_message_args_extras_and_exceptions(clock: FakeClock) -> None:
    token = HmacCapabilityIssuer(_key()).issue("job_1", "att_1", clock.now())
    logger, capture = _logger("b5.redaction.test")
    logger.error("job args %s", ({"job_id": "job_1"}, token),
                 extra={"arguments": ({"job_id": "job_1"}, token), "kwargs": {"c": token}})
    logger.warning(f"inline {token}")
    try:
        raise RuntimeError(f"failure carrying {token}")
    except RuntimeError:
        logger.exception("worker failed")
    for record, text in zip(capture.records, capture.text, strict=True):
        assert token not in text
        assert token not in repr(record.__dict__)
    assert capture.records[0].__dict__["arguments"] == REDACTED
    assert REDACTED in capture.text[1]


def test_rq_entry_point_never_raises_and_never_logs_the_capability(
    h: FixtureHarness, caplog: pytest.LogCaptureFixture
) -> None:
    h.service.create_job(h.create())
    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    payload, token = rq_queue.envelope_args(envelope)
    caplog.set_level(logging.DEBUG)
    # Another suite may have run logging.config.fileConfig (Alembic), which disables loggers
    # that already existed; re-enable ours so the absence check below is not vacuous.
    entry_logger = logging.getLogger("sketch2life.ai_jobs.rq")
    was_disabled, entry_logger.disabled = entry_logger.disabled, False
    install_worker(None)
    try:
        assert rq_queue.receive_dispatch(payload, token) == "NOT_INSTALLED"

        class Broken:
            def handle(self, envelope: WorkerDispatchEnvelope) -> Any:
                raise RuntimeError(f"bad {envelope.capability}")

        install_worker(Broken())  # type: ignore[arg-type]
        assert rq_queue.receive_dispatch(payload, token) == "WORKER_ERROR"
        assert rq_queue.receive_dispatch({"message_id": "m"}, token) == "MALFORMED"
        install_worker(DispatchWorker(h.service, FakeProvider(lambda m: h.success_claim(m))))
        assert rq_queue.receive_dispatch(payload, token) == "completed"
    finally:
        install_worker(None)
        entry_logger.disabled = was_disabled
    assert caplog.records
    for record in caplog.records:
        assert token not in record.getMessage() and token not in repr(record.__dict__)


# ------------------------------------------- B5-R02 strict token shape + defensive redaction
def _variants(token: str) -> dict[str, str]:
    """Malformed representations of a valid token (same MAC bytes under permissive decoding)."""

    head, signature = token.rsplit(".", 1)
    prefix, version, key_id, body = head.split(".")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    last = alphabet.index(signature[-1])
    spare_bits = alphabet[last ^ 0b01]  # 43 chars carry 2 unused bits: same 32 decoded bytes
    return {
        "nonalphabet_prefix": f"{head}.!!!{signature}",
        "nonalphabet_suffix": f"{head}.{signature}!",
        "nonalphabet_inside": f"{head}.{signature[:10]}*{signature[10:]}",
        "body_nonalphabet": f"{prefix}.{version}.{key_id}.{body[:4]}~{body[4:]}.{signature}",
        "padding": f"{head}.{signature}=",
        "double_padding": f"{head}.{signature}==",
        "body_padding": f"{prefix}.{version}.{key_id}.{body}=.{signature}",
        "trailing_dot": f"{token}.",
        "trailing_space": f"{token} ",
        "leading_space": f" {token}",
        "trailing_newline": f"{token}\n",
        "noncanonical_spare_bits": f"{head}.{signature[:-1]}{spare_bits}",
        "uppercase_prefix": token.replace("wcap.v1", "WCAP.V1", 1),
        "standard_alphabet": f"{head}.{signature.replace('-', '+').replace('_', '/')}",
    }


def test_malformed_representations_of_a_valid_token_are_denied(clock: FakeClock) -> None:
    key = _key()
    token = HmacCapabilityIssuer(key).issue("job_1", "att_1", clock.now())
    verifier = HmacCapabilityVerifier(key, clock)
    assert verifier.verify(token) is not None
    for name, variant in _variants(token).items():
        if variant == token:  # e.g. no '-'/'_' to swap in this signature
            continue
        assert verifier.verify(variant) is None, name


def test_service_and_worker_reject_a_noncanonical_token(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    provider = FakeProvider(lambda m: h.success_claim(m))
    for variant in (_variants(envelope.capability)["nonalphabet_prefix"],
                    _variants(envelope.capability)["noncanonical_spare_bits"]):
        outcome = DispatchWorker(h.service, provider).handle(replace(envelope,
                                                                     capability=variant))
        assert (outcome.status, outcome.reason_code) == ("rejected", "WORKER_CAPABILITY_INVALID")
    assert provider.calls[job_id] == 0
    assert h.store.snapshot().jobs[job_id].state is JobState.QUEUED
    assert DispatchWorker(h.service, provider).handle(envelope).status == "completed"


class _Holder:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return f"Holder({self.value})"


def test_redaction_covers_malformed_tokens_in_every_record_field(clock: FakeClock) -> None:
    token = HmacCapabilityIssuer(_key()).issue("job_1", "att_1", clock.now())
    logger, capture = _logger("b5.redaction.malformed")
    for variant in _variants(token).values():
        logger.error("msg %s %s", variant, _Holder(variant),
                     extra={"arguments": (variant,), "envelope": {"capability": variant},
                            "token_note": f"saw {variant}"})
        logger.error(_Holder(variant))
        try:
            raise RuntimeError(f"failure carrying {variant}")
        except RuntimeError:
            logger.exception("worker failed on %s", variant)
    core = token.split(".", 3)[3]  # body+signature: the bearer material in any variant
    for record, text in zip(capture.records, capture.text, strict=True):
        assert core[:20] not in text, text
        assert core[:20] not in repr(record.__dict__)


def test_redaction_covers_capabilities_in_mapping_keys(clock: FakeClock) -> None:
    token = HmacCapabilityIssuer(_key()).issue("job_1", "att_1", clock.now())
    logger, capture = _logger("b5.redaction.mapping_keys")
    logger.warning("metadata %s", {token: "value"},
                   extra={"metadata": {token: {"nested": {token: "value"}}}})
    logger.warning({token: "value"})
    for record, text in zip(capture.records, capture.text, strict=True):
        assert token not in text
        assert token not in repr(record.__dict__)
        assert record.args == ()
    assert capture.records[0].__dict__["metadata"] == {
        REDACTED: {"nested": {REDACTED: "value"}},
    }


def test_redaction_formats_a_capability_prefix_template_before_scrubbing(clock: FakeClock) -> None:
    token = HmacCapabilityIssuer(_key()).issue("job_1", "att_1", clock.now())
    logger, capture = _logger("b5.redaction.prefix_template")
    # The complete bearer only exists after message interpolation; scrubbing the template
    # alone also consumes its %s placeholder and breaks logging with leftover arguments.
    logger.warning("Malformed capability wcap.v1.%s", token.removeprefix("wcap.v1."))
    logger.warning("Malformed capability wcap.v1.%s", "invalid!")
    assert capture.text == [f"Malformed capability {REDACTED}"] * 2
    for record in capture.records:
        assert record.args == ()
        assert token not in repr(record.__dict__)
