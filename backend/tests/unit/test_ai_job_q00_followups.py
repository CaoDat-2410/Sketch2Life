"""Regressions for the Q00 closure-review follow-ups R03a, R04a and A18a (fake scope only)."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, replace

import pytest
from sketch2life.application.services.ai_jobs import AiJobError, CancelJobCommand
from sketch2life.domain.ai_jobs.completion import Moderation
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.ai_jobs.provider_copy import CopyKind, CopyStatus, ProviderCopy
from sketch2life.infrastructure.ai_jobs.harness import (
    ORG,
    OTHER_ORG,
    TEACHER,
    FixtureHarness,
    build_fixture_harness,
)


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


def projected_refs(h: FixtureHarness, job_id: str) -> list[str]:
    view = h.service.get_job_status(TEACHER, job_id).view
    assert view is not None
    return [ref["artifact_ref"] for ref in view["result_refs"]]  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------- R03a
def test_r03a_invalid_state_then_accepted_output_is_available(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.next_message()
    cap = h.capability(job_id)
    claim = h.success_claim(message)
    early = h.service.accept_completion(cap, claim)
    assert early.reason_code == "INVALID_STATE"
    assert h.artifacts.quarantined == {}
    h.service.start_attempt(cap, job_id, message.attempt_id)
    accepted = h.service.accept_completion(cap, claim)
    refs = projected_refs(h, job_id)
    assert accepted.disposition.value == "accepted"
    assert refs == [claim.outputs[0].artifact_ref]
    assert not set(refs) & set(h.artifacts.quarantined)
    assert h.service.accept_completion(cap, claim) == accepted


def test_r03a_corrected_input_mismatch_output_is_available(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    good = h.success_claim(message)
    rejected = h.service.accept_completion(cap, replace(good, input_hash="0" * 64))
    assert (rejected.reason_code, rejected.authoritative) == ("INPUT_MISMATCH", False)
    assert any(e.event_type == "job.completion_input_mismatch" for e in h.audit.events)
    assert h.artifacts.quarantined == {}
    accepted = h.service.accept_completion(cap, good)
    refs = projected_refs(h, job_id)
    assert accepted.disposition.value == "accepted"
    assert refs == [good.outputs[0].artifact_ref]
    assert not set(refs) & set(h.artifacts.quarantined)
    with pytest.raises(AiJobError) as caught:
        h.service.accept_completion(cap, h.success_claim(message, body=b"other"))
    assert caught.value.code == "COMPLETION_CONFLICT"


def test_r03a_quarantined_ref_is_never_admitted(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    claim = h.success_claim(message)
    h.artifacts.owner_quarantine((claim.outputs[0].artifact_ref,), "UNSAFE_CONTENT")
    receipt = h.service.accept_completion(h.capability(job_id), claim)
    assert receipt.reason_code == "OUTPUT_MALFORMED"
    assert projected_refs(h, job_id) == []
    assert h.artifacts.quarantined == {claim.outputs[0].artifact_ref: "UNSAFE_CONTENT"}


def test_r03a_final_rejections_still_quarantine_own_output(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    unsafe = h.success_claim(message, moderation=Moderation.UNSAFE)
    h.service.accept_completion(h.capability(job_id), unsafe)
    assert h.artifacts.quarantined == {unsafe.outputs[0].artifact_ref: "UNSAFE_CONTENT"}

    revoked = build_fixture_harness()
    jid = revoked.service.create_job(revoked.create()).job_id
    msg = revoked.start_next()
    claim = revoked.success_claim(msg)
    revoked.eligibility.revoked_subjects.add("child_fx_001")
    receipt = revoked.service.accept_completion(revoked.capability(jid), claim)
    assert receipt.reason_code == "CONSENT_REVOKED"
    assert claim.outputs[0].artifact_ref in revoked.artifacts.quarantined

    cancelled = build_fixture_harness()
    jid = cancelled.service.create_job(cancelled.create()).job_id
    msg = cancelled.start_next()
    claim = cancelled.success_claim(msg)
    cancelled.service.cancel_job(CancelJobCommand(TEACHER, "c1", jid, 2))
    assert cancelled.service.accept_completion(cancelled.capability(jid), claim).reason_code == (
        "JOB_CANCELLED"
    )
    assert claim.outputs[0].artifact_ref in cancelled.artifacts.quarantined


def test_r03a_foreign_refs_untouched_on_temporary_rejection(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    foreign = h.artifacts.put(OTHER_ORG, b"foreign")
    claim = replace(h.success_claim(message), input_hash="0" * 64, outputs=(foreign,))
    assert h.service.accept_completion(h.capability(job_id), claim).reason_code == (
        "INPUT_MISMATCH"
    )
    assert h.artifacts.quarantined == {}


# ---------------------------------------------------------------------------- R04a
SENSITIVE_FRAGMENT = "token=sk-fixture-secret"


@pytest.mark.parametrize(
    "code",
    [[], {}, [SENSITIVE_FRAGMENT], {"detail": SENSITIVE_FRAGMENT}, 7, True, b"raw",
     {SENSITIVE_FRAGMENT}],
    ids=["list", "dict", "list_secret", "dict_secret", "int", "bool", "bytes", "set"],
)
def test_r04a_non_string_failure_code_is_non_authoritative(
    h: FixtureHarness, code: object
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    bad = replace(h.failure_claim(message, retryable=False), failure_code=code)
    receipt = h.service.accept_completion(cap, bad)  # type: ignore[arg-type]
    assert (receipt.reason_code, receipt.authoritative) == ("MALFORMED_CLAIM", False)
    assert receipt.disposition.value == "rejected"
    with h.store.transaction() as tx:
        job = tx.get_job(job_id)
    assert job is not None and job.state is JobState.RUNNING
    rendered = json.dumps(
        [h.service.get_job_status(TEACHER, job_id).view, [asdict(e) for e in h.audit.events]],
        default=str,
    )
    assert "sk-fixture-secret" not in rendered and "provider_code_sha256" in rendered
    valid = h.success_claim(message)
    assert h.service.accept_completion(cap, valid).disposition.value == "accepted"
    assert projected_refs(h, job_id) == [valid.outputs[0].artifact_ref]


def test_r04a_string_codes_keep_r04_mapping(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    receipt = h.service.accept_completion(
        h.capability(job_id),
        replace(h.failure_claim(message, retryable=False), failure_code="http 503"),
    )
    assert (receipt.reason_code, receipt.authoritative) == ("PROVIDER_ERROR", True)


def test_r04a_non_string_identity_is_a_typed_error(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    bad = replace(h.success_claim(message), attempt_id=["att"])  # type: ignore[arg-type]
    with pytest.raises(AiJobError) as caught:
        h.service.accept_completion(h.capability(job_id), bad)
    assert (caught.value.code, caught.value.http_status) == ("MALFORMED_REQUEST", 400)


# ---------------------------------------------------------------------------- A18a
def _paused_cancel(h: FixtureHarness) -> tuple[threading.Event, threading.Event]:
    entered, release = threading.Event(), threading.Event()
    original = h.copy_adapter.request_cancel

    def paused(copy: ProviderCopy) -> None:
        entered.set()
        assert release.wait(5)
        original(copy)

    h.copy_adapter.request_cancel = paused  # type: ignore[method-assign]
    return entered, release


@pytest.mark.parametrize("profile", ["fixture-deletes", "fixture-pending", "fixture-exception"])
def test_a18a_paused_cancel_cannot_overwrite_purge_result(
    h: FixtureHarness, profile: str
) -> None:
    h.copy_service.register_copy(ProviderCopy("c1", ORG, "s1", CopyKind.OUTPUT, profile))
    entered, release = _paused_cancel(h)
    purged: list[str | None] = []
    cancel = threading.Thread(target=lambda: h.copy_service.cancel_scope(ORG, "s1"))
    purge = threading.Thread(
        target=lambda: purged.append(h.copy_service.purge_scope(ORG, "s1", "p1")[0].receipt_id)
    )
    cancel.start()
    assert entered.wait(5)
    purge.start()
    purge.join(0.3)
    assert purge.is_alive(), "purge must wait for the in-flight cancellation"
    assert h.copy_adapter.purge_requests == []
    release.set()
    cancel.join(5)
    purge.join(5)
    assert not cancel.is_alive() and not purge.is_alive()
    current = h.copy_registry.get("c1")
    assert current is not None and current.receipt_id == purged[0] is not None
    assert current.status is not CopyStatus.CANCEL_REQUESTED
    assert [o.receipt_id for o in h.copy_service.discover(ORG, "s1")] == purged
    assert h.copy_service.purge_scope(ORG, "s1", "p1")[0].receipt_id == purged[0]
    assert len(h.copy_adapter.purge_requests) == 1


def test_a18a_cancel_after_purge_keeps_deleted_and_receipt(h: FixtureHarness) -> None:
    h.copy_service.register_copy(ProviderCopy("c1", ORG, "s1", CopyKind.OUTPUT,
                                              "fixture-deletes"))
    deleted = h.copy_service.purge_scope(ORG, "s1", "p1")[0]
    after = h.copy_service.cancel_scope(ORG, "s1")[0]
    assert after == deleted and h.copy_adapter.cancel_requests == []
    current = h.copy_registry.get("c1")
    assert current is not None and current.status is CopyStatus.DELETED
