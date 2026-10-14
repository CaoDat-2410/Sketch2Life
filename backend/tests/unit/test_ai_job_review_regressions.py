"""Regressions for the Phase A independent review findings R01-R11 (Q00, fake scope only)."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sketch2life.application.services.ai_jobs import AiJobError
from sketch2life.contracts.schemas.ai_contract_candidates import check_shape
from sketch2life.contracts.schemas.ai_jobs import AsyncJobChildViewV1, AsyncJobViewV1
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.ai_jobs.provider_copy import (
    CopyKind,
    CopyStatus,
    ProviderCopy,
    PurgeReceipt,
)
from sketch2life.infrastructure.ai_jobs.harness import (
    ORG,
    OTHER_ORG,
    TEACHER,
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)
from sketch2life.interfaces.http.ai_jobs_fixture_app import create_ai_jobs_fixture_app

FIXTURES = Path(__file__).resolve().parents[3] / "features/FEAT-044-be2-ai-job-foundation/fixtures"


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


def state(h: FixtureHarness, job_id: str) -> JobState:
    with h.store.transaction() as tx:
        job = tx.get_job(job_id)
    assert job is not None
    return job.state


# ----------------------------------------------------------------------------- R01
@pytest.mark.parametrize("mismatch", [True, False], ids=["input_mismatch", "malformed_output"])
def test_r01_rejections_never_quarantine_foreign_or_unowned_artifacts(
    h: FixtureHarness, mismatch: bool
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    other_job = h.service.create_job(h.create(key="k2", ref=request_ref("req_2"))).job_id
    message = h.start_next()
    foreign_org = h.artifacts.put(OTHER_ORG, b"foreign")
    no_lineage = h.artifacts.put(ORG, b"no-lineage")
    other_jobs = h.artifacts.put(ORG, b"other-job", job_id=other_job, attempt_id="att_x")
    claim = replace(h.success_claim(message), outputs=(foreign_org, no_lineage, other_jobs))
    if mismatch:
        claim = replace(claim, input_hash="0" * 64)
    receipt = h.service.accept_completion(h.capability(job_id), claim)
    assert receipt.reason_code == ("INPUT_MISMATCH" if mismatch else "OUTPUT_MALFORMED")
    assert h.artifacts.quarantined == {}


def test_r01_own_output_of_a_final_rejection_is_still_quarantined(h: FixtureHarness) -> None:
    from sketch2life.application.services.ai_jobs import CancelJobCommand

    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    own = h.success_claim(message)
    h.service.cancel_job(CancelJobCommand(TEACHER, "c1", job_id, 2))
    receipt = h.service.accept_completion(h.capability(job_id), own)
    assert receipt.reason_code == "JOB_CANCELLED"
    assert own.outputs[0].artifact_ref in h.artifacts.quarantined


def test_r01_output_from_another_attempt_is_not_a_valid_result(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    stolen = h.artifacts.put(ORG, b"x", job_id=job_id, attempt_id="att_other")
    receipt = h.service.accept_completion(
        h.capability(job_id), replace(h.success_claim(message), outputs=(stolen,))
    )
    assert receipt.reason_code == "OUTPUT_MALFORMED"
    assert stolen.artifact_ref not in h.artifacts.quarantined


# ----------------------------------------------------------------------------- R02
@pytest.mark.parametrize(
    "change",
    [{"target": "target_fx_other"}, {"session_id": "session_fx_other"},
     {"subjects": ("child_fx_other",)}],
    ids=["target", "session", "subjects"],
)
def test_r02_semantic_dedup_keeps_scope(h: FixtureHarness, change: dict[str, object]) -> None:
    first = h.service.create_job(h.create(key="a"))
    other = h.service.create_job(h.create(key="b", **change))  # type: ignore[arg-type]
    assert other.job_id != first.job_id and other.outcome == "created"


def test_r02_purpose_change_is_a_different_semantic_request(h: FixtureHarness) -> None:
    first = h.service.create_job(h.create(key="a"))
    other = h.service.create_job(replace(h.create(key="b"), purpose_code="purpose_fx_other"))
    assert other.job_id != first.job_id


def test_r02_matching_scope_still_dedups_across_principals(h: FixtureHarness) -> None:
    from sketch2life.infrastructure.ai_jobs.harness import TEACHER_2

    first = h.service.create_job(h.create(key="a"))
    peer = h.service.create_job(h.create(TEACHER_2, key="z"))
    assert peer.job_id == first.job_id and peer.outcome == "deduplicated"


# ----------------------------------------------------------------------------- R03
def test_r03_completion_before_start_does_not_poison_the_attempt(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.next_message()
    cap = h.capability(job_id)
    claim = h.success_claim(message)
    early = h.service.accept_completion(cap, claim)
    assert (early.reason_code, early.authoritative) == ("INVALID_STATE", False)
    h.service.start_attempt(cap, job_id, message.attempt_id)
    later = h.service.accept_completion(cap, claim)
    assert later.disposition.value == "accepted" and later.authoritative
    assert h.artifacts.quarantined == {}  # R03a: accepted output stays available
    assert state(h, job_id) is JobState.SUCCEEDED
    assert h.service.accept_completion(cap, claim) == later


def test_r03_corrected_claim_lands_and_genuine_conflict_remains(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    good = h.success_claim(message)
    bad = h.service.accept_completion(cap, replace(good, input_hash="0" * 64))
    assert (bad.reason_code, bad.authoritative) == ("INPUT_MISMATCH", False)
    accepted = h.service.accept_completion(cap, good)
    assert accepted.disposition.value == "accepted"
    assert good.outputs[0].artifact_ref not in h.artifacts.quarantined  # R03a
    with pytest.raises(AiJobError) as caught:
        h.service.accept_completion(cap, h.success_claim(message, body=b"different"))
    assert caught.value.code == "COMPLETION_CONFLICT"
    snap = h.store.snapshot()
    assert list(snap.completion_receipts.values()) == [accepted]


# ----------------------------------------------------------------------------- R04
@pytest.mark.parametrize(
    "code", ["http 503 from provider", "SOME_VENDOR_CODE", "token=sk-fixture-secret", None]
)
def test_r04_unknown_failure_codes_map_safely_and_stay_pollable(
    h: FixtureHarness, code: str | None
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    claim = replace(h.failure_claim(message, retryable=False), failure_code=code)
    receipt = h.service.accept_completion(h.capability(job_id), claim)
    assert receipt.disposition.value == "accepted" and receipt.reason_code == "PROVIDER_ERROR"
    client = TestClient(create_ai_jobs_fixture_app(h.service, {"t": TEACHER}),
                        raise_server_exceptions=False)
    response = client.get(f"/api/collaboration/v1/jobs/{job_id}",
                          headers={"Authorization": "Fixture t"})
    assert response.status_code == 200
    assert response.json()["data"]["failure"]["code"] == "PROVIDER_ERROR"
    if code:
        assert code not in response.text
        assert code not in json.dumps([e.details for e in h.audit.events])


@pytest.mark.parametrize(
    "change",
    [{"kind": "partial"}, {"moderation": "maybe"}, {"retryable": "yes"},
     {"failure_code": "PROVIDER_ERROR"}],
)
def test_r04_malformed_claim_is_rejected_without_poisoning(
    h: FixtureHarness, change: dict[str, object]
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    good = h.success_claim(message)
    receipt = h.service.accept_completion(h.capability(job_id), replace(good, **change))  # type: ignore[arg-type]
    assert (receipt.reason_code, receipt.authoritative) == ("MALFORMED_CLAIM", False)
    assert state(h, job_id) is JobState.RUNNING
    assert h.service.accept_completion(h.capability(job_id), good).disposition.value == "accepted"


# --------------------------------------------------------------------- R05 / R06
def test_r05_concurrent_same_key_purge_dispatches_once(h: FixtureHarness) -> None:
    h.copy_service.register_copy(ProviderCopy("c1", ORG, "s1", CopyKind.OUTPUT,
                                              "fixture-deletes"))
    original = h.copy_adapter.request_purge

    def slow(copy: ProviderCopy) -> PurgeReceipt:
        time.sleep(0.2)
        return original(copy)

    h.copy_adapter.request_purge = slow  # type: ignore[method-assign]
    receipts: list[str | None] = []

    def purge() -> None:
        receipts.append(h.copy_service.purge_scope(ORG, "s1", "same")[0].receipt_id)

    threads = [threading.Thread(target=purge) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    stored = h.copy_registry.get_purge_receipt(f"{ORG}:s1:same:c1")
    copy = h.copy_registry.get("c1")
    assert len(h.copy_adapter.purge_requests) == 1 and len(set(receipts)) == 1
    assert stored is not None and copy is not None
    assert copy.receipt_id == stored.receipt_id == receipts[0]


@pytest.mark.parametrize("first_profile", ["fixture-pending", "fixture-exception"])
def test_r06_old_key_replay_after_retry_keeps_newer_state(
    h: FixtureHarness, first_profile: str
) -> None:
    h.copy_service.register_copy(ProviderCopy("c1", ORG, "s1", CopyKind.OUTPUT, first_profile))
    first = h.copy_service.purge_scope(ORG, "s1", "p1")[0]
    current = h.copy_registry.get("c1")
    assert current is not None
    h.copy_registry.save(replace(current, provider_profile="fixture-deletes"))
    retried = h.copy_service.purge_scope(ORG, "s1", "p2")[0]
    replay = h.copy_service.purge_scope(ORG, "s1", "p1")[0]
    again = h.copy_service.purge_scope(ORG, "s1", "p2")[0]
    after = h.copy_registry.get("c1")
    assert replay == first and again == retried
    assert after is not None and after.status is CopyStatus.DELETED
    assert after.receipt_id == retried.receipt_id
    assert len(h.copy_adapter.purge_requests) == 2


# ----------------------------------------------------------------------------- R07
@pytest.mark.parametrize("path", sorted((FIXTURES / "shapes/negative_types").glob("*.json")),
                         ids=lambda p: p.stem)
def test_r07_non_string_enum_values_give_errors_not_exceptions(path: Path) -> None:
    case = json.loads(path.read_bytes())
    assert check_shape(case["data_id"], case["payload"]) != []


# --------------------------------------------------------------------- R08 / R11
def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_bytes())


@pytest.mark.parametrize(
    "name", ["queued_with_refs", "queued_refs_without_disposition", "running_with_disposition",
             "cancelled_with_refs"],
)
def test_r08_result_refs_only_with_succeeded_accepted(name: str) -> None:
    with pytest.raises(ValidationError):
        AsyncJobViewV1.model_validate_json(
            json.dumps(_fixture(f"data25/negative/{name}.json")), strict=True
        )


@pytest.mark.parametrize(
    "name", ["child_terminal_keeps_polling", "child_failed_without_failure",
             "child_succeeded_with_failure"],
)
def test_r11_child_schema_shares_state_rules(name: str) -> None:
    with pytest.raises(ValidationError):
        AsyncJobChildViewV1.model_validate_json(
            json.dumps(_fixture(f"data25_child/negative/{name}.json")), strict=True
        )


# --------------------------------------------------------------------- R09 / R10
@pytest.mark.parametrize(
    "apply",
    [
        lambda h: h.eligibility.revoked_subjects.add("child_fx_001"),
        lambda h: h.eligibility.ended_sessions.add("session_fx_001"),
        lambda h: h.eligibility.recalled_requests.add("req_fx_001"),
        lambda h: h.eligibility.expired_requests.add("req_fx_001"),
        lambda h: h.eligibility.killed_job_types.add("sketch_assistance"),
    ],
    ids=["consent", "session", "recall", "expiry", "kill_switch"],
)
def test_r09_dispatch_rechecks_eligibility(h: FixtureHarness, apply) -> None:  # type: ignore[no-untyped-def]
    job_id = h.service.create_job(h.create()).job_id
    apply(h)
    assert h.service.dispatch_outbox() == 0
    assert h.queue.messages == [] and not h.store.snapshot().outbox
    assert state(h, job_id) is JobState.CANCELLED
    assert any(e.event_type == "job.dispatch_denied" for e in h.audit.events)


def test_r09_retry_requeue_is_also_rechecked_at_dispatch(h: FixtureHarness) -> None:
    from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY

    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(job_id), h.failure_claim(message))
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_max_ms)
    assert h.service.run_due_retries() == (job_id,)
    h.eligibility.ended_sessions.add("session_fx_001")
    assert h.service.dispatch_outbox() == 0 and state(h, job_id) is JobState.CANCELLED


def test_r10_conditional_poll_receives_changed_backoff_hint(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    first = h.service.get_job_status(TEACHER, job_id)
    assert h.service.get_job_status(TEACHER, job_id, first.etag).not_modified
    h.clock.advance(seconds=60)
    later = h.service.get_job_status(TEACHER, job_id, first.etag)
    assert not later.not_modified and later.view is not None
    assert later.view["poll_after_ms"] == 10000 and later.etag != first.etag
    assert h.service.get_job_status(TEACHER, job_id, later.etag).not_modified


def test_r10_retry_wait_hint_is_quantised_to_seconds(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(job_id), h.failure_claim(message))
    first = h.service.get_job_status(TEACHER, job_id)
    h.clock.advance(milliseconds=1)
    assert h.service.get_job_status(TEACHER, job_id, first.etag).not_modified
