"""BE2-01 Phase B batch B3 offline checks on the deterministic fakes (Δ1–Δ5 parity).

These cover the service's fence/round logic and the canonical semantic key without a
database. They are not PostgreSQL evidence: the SQL proofs live in
``tests/integration/ai_jobs`` (B-03, B-07, B-08, B-09a–d).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import replace

import pytest
from sketch2life.application.ports.ai_jobs import (
    OWNER_FENCE_CONTRACT,
    AuthorizationAction,
    AuthorizationDecision,
    EligibilityDecision,
    Principal,
    QuarantineIntent,
    SemanticRequestKey,
    UniqueConflict,
)
from sketch2life.application.services.ai_jobs import (
    AiJobDependencies,
    AiJobError,
    AiJobService,
    CancelJobCommand,
    StartResult,
)
from sketch2life.domain.ai_jobs.model import JobScope, JobState, RequestRef, ResultDisposition
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeAuthorization,
    FakeEligibility,
    artifact_fence_scope,
    eligibility_fence_scope,
    grant_fence_scope,
)
from sketch2life.infrastructure.ai_jobs.harness import (
    ORG,
    TEACHER,
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)
from sketch2life.infrastructure.ai_jobs.sql.owner_fence_fixture import (
    DISPOSABLE_DATABASE,
    FixtureFenceHold,
    OwnerFixture,
)

SHA = "a" * 64


def _key(**changes: object) -> SemanticRequestKey:
    base = SemanticRequestKey(
        ORG,
        "sketch_assistance",
        "req_1",
        1,
        SHA,
        1,
        "target_1",
        "purpose_1",
        None,
        ("child_1", "child_2"),
    )
    return replace(base, **changes)  # type: ignore[arg-type]


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


def _service(h: FixtureHarness, **changes: object) -> AiJobService:
    values = {name: getattr(h.service._d, name) for name in AiJobDependencies.__dataclass_fields__}
    values.update(changes)
    return AiJobService(AiJobDependencies(**values))


class _AfterEligibility:
    def __init__(self, port: FakeEligibility, after: Callable[[int], None]) -> None:
        self._port, self._after, self.calls = port, after, 0

    def check(
        self, *, scope: JobScope, request_ref: RequestRef, job_type: str
    ) -> EligibilityDecision:
        decision = self._port.check(scope=scope, request_ref=request_ref, job_type=job_type)
        self.calls += 1
        self._after(self.calls)
        return decision


class _AfterAuthorization:
    def __init__(
        self, port: FakeAuthorization, after: Callable[[AuthorizationAction, int], None]
    ) -> None:
        self._port, self._after, self.calls = port, after, 0

    def decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision:
        decision = self._port.decide(principal, action, scope)
        self.calls += 1
        self._after(action, self.calls)
        return decision


# ------------------------------------------------------------------------------------- Δ4
def test_semantic_key_matches_an_independent_canonical_encoding() -> None:
    expected = hashlib.sha256(
        json.dumps(
            {
                "context_revision": 1,
                "input_hash": SHA,
                "job_type": "sketch_assistance",
                "organization_id": ORG,
                "purpose_code": "purpose_1",
                "request_id": "req_1",
                "request_revision": 1,
                "session_id": None,
                "subject_refs": ["child_1", "child_2"],
                "target_id": "target_1",
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    assert _key().sha256() == expected


def test_semantic_key_canonicalisation_rules() -> None:
    assert _key(subject_refs=("child_2", "child_1")).sha256() == _key().sha256()
    assert _key(subject_refs=("child_é",)).sha256() == _key(subject_refs=("child_é",)).sha256()
    assert _key(target_id="té").sha256() == _key(target_id="té").sha256()
    distinct = {
        _key().sha256(),
        _key(session_id="").sha256(),
        _key(session_id="session_1").sha256(),
        _key(subject_refs=("child_1", "child_1", "child_2")).sha256(),  # duplicates kept
        _key(subject_refs=("child_1",)).sha256(),
    }
    assert len(distinct) == 5


# ------------------------------------------------------------------------------------- Δ5
def test_fake_plain_inserts_raise_typed_conflicts_and_roll_back(h: FixtureHarness) -> None:
    created = h.service.create_job(h.create())
    snapshot = h.store.snapshot()
    with pytest.raises(UniqueConflict) as conflict, h.store.transaction() as tx:
        tx.put_semantic(_key(), created.job_id)
        tx.put_semantic(_key(), created.job_id)
    assert conflict.value.kind == "semantic_request"
    receipt = next(iter(snapshot.command_receipts.values()))
    with pytest.raises(UniqueConflict) as conflict, h.store.transaction() as tx:
        tx.put_command_receipt(receipt)
    assert conflict.value.kind == "command_receipt"
    assert h.store.snapshot() == snapshot


def test_create_and_dedup_each_commit_one_audit_intent(h: FixtureHarness) -> None:
    first = h.service.create_job(h.create(key="k1"))
    second = h.service.create_job(h.create(key="k2"))
    assert (second.outcome, second.job_id) == ("deduplicated", first.job_id)
    intents = h.store.snapshot().audit_intents
    assert sorted(e.event_type for e in intents.values()) == [
        "job.create.deduplicated",
        "job.created",
    ]
    assert all(len(event_id) == 64 for event_id in intents)
    h.store.fail_next_commit = True
    with pytest.raises(RuntimeError):
        h.service.create_job(h.create(key="k3", ref=request_ref("req_other")))
    assert len(h.store.snapshot().audit_intents) == 2


def test_unique_conflict_twice_returns_retryable_idempotency_conflict(
    h: FixtureHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sketch2life.infrastructure.ai_jobs import fakes

    def conflict(self: object, key: object, job_id: str) -> None:
        raise UniqueConflict("semantic_request")

    monkeypatch.setattr(fakes._UnitOfWork, "put_semantic", conflict)
    with pytest.raises(AiJobError) as error:
        h.service.create_job(h.create())
    assert (error.value.code, error.value.http_status, error.value.retryable) == (
        "IDEMPOTENCY_CONFLICT",
        409,
        True,
    )
    assert h.store.snapshot().jobs == {}


# ---------------------------------------------------------------------------------- Δ1–Δ3
def test_decisions_carry_owner_fences(h: FixtureHarness) -> None:
    scope = JobScope(ORG, None, ("c",), "p", "t")
    assert h.authorization.decide(TEACHER, AuthorizationAction.CREATE_JOB, scope).fence == (
        h.fences.fence(grant_fence_scope(ORG, TEACHER.principal_id))
    )
    assert h.eligibility.check(scope=scope, request_ref=request_ref(), job_type="x").fence == (
        h.fences.fence(eligibility_fence_scope(ORG))
    )
    output = h.artifacts.put(ORG, b"x")
    descriptor = h.artifacts.describe(output.artifact_ref)
    assert descriptor is not None
    assert descriptor.fence == h.fences.fence(artifact_fence_scope(output.artifact_ref))


def test_create_redecides_once_after_a_stale_grant_fence(h: FixtureHarness) -> None:
    def bump(action: AuthorizationAction, call: int) -> None:
        if call == 1:
            h.fences.bump(grant_fence_scope(ORG, TEACHER.principal_id))

    service = _service(h, authorization=_AfterAuthorization(h.authorization, bump))
    result = service.create_job(h.create())
    assert result.outcome == "created"
    assert [hold.current for hold in h.fences.holds] == [False, True]
    assert len(h.store.snapshot().jobs) == 1


def test_create_stale_twice_is_typed_and_writes_nothing(h: FixtureHarness) -> None:
    def bump(call: int) -> None:
        h.fences.bump(eligibility_fence_scope(ORG))

    service = _service(h, eligibility=_AfterEligibility(h.eligibility, bump))
    with pytest.raises(AiJobError) as error:
        service.create_job(h.create())
    assert (error.value.code, error.value.http_status, error.value.retryable) == (
        "STALE_CONTEXT",
        409,
        True,
    )
    snapshot = h.store.snapshot()
    assert snapshot.jobs == {} and snapshot.command_receipts == {} and not snapshot.audit_intents


def test_missing_fence_is_never_current(h: FixtureHarness) -> None:
    class Unfenced:
        def decide(
            self, principal: Principal, action: AuthorizationAction, scope: JobScope
        ) -> AuthorizationDecision:
            return replace(h.authorization.decide(principal, action, scope), fence=None)

    with pytest.raises(AiJobError) as error:
        _service(h, authorization=Unfenced()).create_job(h.create())
    assert error.value.code == "STALE_CONTEXT"
    assert h.store.snapshot().jobs == {}


def test_start_with_consent_revoked_after_precheck_is_cancelled_not_started(
    h: FixtureHarness,
) -> None:
    created = h.service.create_job(h.create())
    message = h.next_message()

    def revoke(call: int) -> None:
        if call == 1:
            h.eligibility.revoked_subjects.add("child_fx_001")
            h.fences.bump(eligibility_fence_scope(ORG))

    service = _service(h, eligibility=_AfterEligibility(h.eligibility, revoke))
    result = service.start_attempt(h.capability(created.job_id), created.job_id, message.attempt_id)
    assert result == StartResult(False, "CONSENT_REVOKED")
    job = h.store.snapshot().jobs[created.job_id]
    assert job.state is JobState.CANCELLED and job.active_attempt.started_at is None


def test_completion_with_output_quarantined_after_precheck_is_not_accepted(
    h: FixtureHarness,
) -> None:
    created = h.service.create_job(h.create())
    message = h.start_next()
    claim = h.success_claim(message)
    ref = claim.outputs[0].artifact_ref

    class QuarantineAfterDescribe:
        def __init__(self, port: FakeArtifacts) -> None:
            self._port, self.done = port, False

        def describe(self, artifact_ref: str) -> object:
            descriptor = self._port.describe(artifact_ref)
            if not self.done:
                self.done = True
                self._port.owner_quarantine((artifact_ref,), "OWNER_QUARANTINE")
            return descriptor

        def quarantine(self, intent: QuarantineIntent) -> None:
            self._port.quarantine(intent)

    service = _service(h, artifacts=QuarantineAfterDescribe(h.artifacts))
    receipt = service.accept_completion(h.capability(created.job_id), claim)
    assert (receipt.disposition, receipt.reason_code) == (
        ResultDisposition.REJECTED,
        "OUTPUT_MALFORMED",
    )
    assert h.artifacts.quarantined[ref] == "OWNER_QUARANTINE"
    assert h.store.snapshot().jobs[created.job_id].state is JobState.FAILED_EXHAUSTED


def test_cancel_with_stale_grant_redecides_and_records_one_audit_intent(
    h: FixtureHarness,
) -> None:
    created = h.service.create_job(h.create())

    def bump(action: AuthorizationAction, call: int) -> None:
        if action is AuthorizationAction.CANCEL_JOB and call == 2:
            h.fences.bump(grant_fence_scope(ORG, TEACHER.principal_id))

    service = _service(h, authorization=_AfterAuthorization(h.authorization, bump))
    h.fences.holds.clear()
    result = service.cancel_job(
        CancelJobCommand(TEACHER, "cancel_1", created.job_id, created.job_revision)
    )
    assert result.outcome == "cancelled"
    assert [hold.current for hold in h.fences.holds] == [False, True]
    events = [e.event_type for e in h.store.snapshot().audit_intents.values()]
    assert events.count("job.cancelled") == 1


def test_owner_fence_fixture_is_labelled_assumed_contract_and_versioned() -> None:
    assert FixtureFenceHold.label == OwnerFixture.label == "ASSUMED_CONTRACT"
    assert FixtureFenceHold.contract_version == OWNER_FENCE_CONTRACT


def test_fixture_ddl_guard_accepts_only_disposable_database_names() -> None:
    assert DISPOSABLE_DATABASE.match("be2_b2_0123456789abcdef")
    for name in ("be2_synthetic", "postgres", "be2_b2_x", "sketch2life"):
        assert not DISPOSABLE_DATABASE.match(name)
