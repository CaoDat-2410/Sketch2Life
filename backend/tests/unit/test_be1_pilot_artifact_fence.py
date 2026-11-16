from __future__ import annotations

import json
from typing import cast

import pytest
from sketch2life.application.ports.ai_jobs import (
    ArtifactDescriptor,
    FenceResult,
    OwnerFence,
    QuarantineIntent,
)
from sketch2life.infrastructure.assistance.owner_fence import (
    decode_owner_fence_scope as _decode_owner_fence_scope,
)
from sketch2life.infrastructure.vision_analysis import pilot_composition as pilot
from sqlalchemy.engine import Connection

_ARTIFACT_FENCE_PREFIX = "be1-pilot-artifact-v1:"


class _Connection:
    def __init__(self, *, active: bool) -> None:
        self.active = active
        self.executed = 0

    def in_transaction(self) -> bool:
        return self.active

    def execute(self, *_args: object, **_kwargs: object) -> None:
        self.executed += 1


class _FactsFence:
    def __init__(self, connection: _Connection, *, current: bool) -> None:
        self.connection = connection
        self.current = current
        self.received: tuple[OwnerFence, ...] = ()

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        self.received = fences
        if not self.connection.in_transaction() or not self.current:
            return FenceResult(False, fences)
        return FenceResult(True)


def _artifact_scope(artifact_ref: str, organization_id: str, digest: str) -> str:
    payload = json.dumps(
        {
            "artifact_ref": artifact_ref,
            "organization_id": organization_id,
            "sha256": digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return _ARTIFACT_FENCE_PREFIX + payload


def _artifact_descriptor(
    artifacts: pilot.PilotFakeArtifacts,
) -> tuple[str, ArtifactDescriptor]:
    output = artifacts.write_output("org-1", b"synthetic image", job_id="job-1", attempt_id="a-1")
    descriptor = artifacts.describe(output.artifact_ref)
    assert descriptor is not None
    return output.artifact_ref, descriptor


def _combined(
    monkeypatch: pytest.MonkeyPatch,
    artifacts: pilot.PilotFakeArtifacts,
    *,
    connection_active: bool = False,
    facts_current: bool = True,
    authorization_current: bool = True,
) -> tuple[pilot._CombinedBe1OwnerFence, _Connection, _FactsFence]:
    connection = _Connection(active=connection_active)
    facts_port = _FactsFence(connection, current=facts_current)
    decode = _decode_owner_fence_scope
    monkeypatch.setattr(
        pilot,
        "PostgresBE1OwnerFence",
        lambda *_args, **_kwargs: facts_port,
    )
    monkeypatch.setattr(
        "sketch2life.infrastructure.vision_analysis.pilot_composition.decode_owner_fence_scope",
        lambda scope: object() if scope == "facts:valid" else decode(scope),
    )
    monkeypatch.setattr(
        pilot,
        "_hold_authorization_fence",
        lambda *_args, **_kwargs: authorization_current,
    )
    combined = pilot._CombinedBe1OwnerFence(
        cast(Connection, connection),
        lambda *_args: None,
        lock_timeout_ms=1000,
        artifacts=artifacts,
    )
    return combined, connection, facts_port


def test_write_and_describe_issue_bound_integer_artifact_fence() -> None:
    artifacts = pilot.PilotFakeArtifacts()
    artifact_ref, descriptor = _artifact_descriptor(artifacts)

    fence = descriptor.fence
    assert fence is not None
    assert fence.fence_scope.startswith(_ARTIFACT_FENCE_PREFIX)
    payload = json.loads(fence.fence_scope.removeprefix(_ARTIFACT_FENCE_PREFIX))
    assert payload == {
        "artifact_ref": artifact_ref,
        "organization_id": "org-1",
        "sha256": descriptor.sha256,
    }
    assert type(fence.epoch) is int


def test_artifact_only_fence_is_current_without_database_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    _artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None
    combined, connection, facts_port = _combined(monkeypatch, artifacts)

    result = combined.hold((descriptor.fence,))

    assert result.current is True
    assert connection.executed == 0
    assert facts_port.received == ()


def test_combined_routes_auth_facts_and_artifact_fences_to_their_owners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    _artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None
    auth = OwnerFence(pilot._AUTH_FENCE_PREFIX + "{}", 1)
    facts = OwnerFence("facts:valid", 3)
    combined, connection, facts_port = _combined(monkeypatch, artifacts, connection_active=True)

    result = combined.hold((auth, facts, descriptor.fence))

    assert result.current is True
    assert connection.executed == 1
    assert facts_port.received == (facts,)


@pytest.mark.parametrize(
    "mutation",
    [
        "quarantine",
        "missing",
        "organization",
        "sha256",
        "sha256_valid_mismatch",
        "epoch_type",
        "unknown_scope",
    ],
)
def test_artifact_fence_rejects_stale_or_malformed_state(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None
    fence = descriptor.fence

    if mutation == "quarantine":
        artifacts.quarantine(
            QuarantineIntent(
                event_id="event-1",
                organization_id="org-1",
                job_id="job-1",
                attempt_id="a-1",
                artifact_refs=(artifact_ref,),
                reason_code="TEST_QUARANTINE",
            )
        )
    elif mutation == "missing":
        fence = OwnerFence(_artifact_scope("missing-ref", "org-1", descriptor.sha256), 0)
    elif mutation in {"organization", "sha256"}:
        payload = json.loads(fence.fence_scope.removeprefix(_ARTIFACT_FENCE_PREFIX))
        payload["organization_id" if mutation == "organization" else "sha256"] = "forged"
        fence = OwnerFence(
            _ARTIFACT_FENCE_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":")),
            fence.epoch,
        )
    elif mutation == "sha256_valid_mismatch":
        payload = json.loads(fence.fence_scope.removeprefix(_ARTIFACT_FENCE_PREFIX))
        replacement = "0" * 64
        if replacement == descriptor.sha256:
            replacement = "1" * 64
        payload["sha256"] = replacement
        fence = OwnerFence(
            _ARTIFACT_FENCE_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":")),
            fence.epoch,
        )
    elif mutation == "epoch_type":
        fence = OwnerFence(fence.fence_scope, cast(int, "not-an-int"))
    else:
        fence = OwnerFence("unknown-owner-scope", 0)

    combined, _connection, _facts_port = _combined(monkeypatch, artifacts)

    assert combined.hold((fence,)).current is False


def test_quarantine_bumps_epoch_and_rejects_the_pre_quarantine_fence() -> None:
    artifacts = pilot.PilotFakeArtifacts()
    artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None
    before = descriptor.fence

    artifacts.quarantine(
        QuarantineIntent(
            event_id="event-1",
            organization_id="org-1",
            job_id="job-1",
            attempt_id="a-1",
            artifact_refs=(artifact_ref,),
            reason_code="TEST_QUARANTINE",
        )
    )
    after = artifacts.describe(artifact_ref)

    assert after is not None and after.fence is not None
    assert after.fence.epoch == before.epoch + 1
    assert after.quarantine_reason == "TEST_QUARANTINE"


def test_artifact_fence_is_point_in_time_not_locked_through_sql_commit() -> None:
    """A later quarantine makes a previously current fence stale; this is not a commit lock."""
    artifacts = pilot.PilotFakeArtifacts()
    artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None

    before_quarantine = artifacts.hold_fences((descriptor.fence,))
    assert before_quarantine.current is True

    artifacts.quarantine(
        QuarantineIntent(
            event_id="event-2",
            organization_id="org-1",
            job_id="job-1",
            attempt_id="a-1",
            artifact_refs=(artifact_ref,),
            reason_code="TEST_QUARANTINE",
        )
    )

    after_quarantine = artifacts.hold_fences((descriptor.fence,))
    assert after_quarantine.current is False


def test_duplicate_artifact_scope_is_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    _artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None
    combined, _connection, _facts_port = _combined(monkeypatch, artifacts)

    assert combined.hold((descriptor.fence, descriptor.fence)).current is False


@pytest.mark.parametrize(
    ("auth_fence", "facts_current", "authorization_current"),
    [(True, True, True), (False, True, True), (False, False, True), (True, True, False)],
)
def test_auth_and_facts_fences_keep_transaction_and_stale_behavior(
    monkeypatch: pytest.MonkeyPatch,
    auth_fence: bool,
    facts_current: bool,
    authorization_current: bool,
) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    combined, connection, facts_port = _combined(
        monkeypatch,
        artifacts,
        connection_active=True,
        facts_current=facts_current,
        authorization_current=authorization_current,
    )
    auth = OwnerFence(pilot._AUTH_FENCE_PREFIX + "{}", 1) if auth_fence else None
    facts = OwnerFence("facts:valid", 3) if not auth_fence else None
    fences = tuple(fence for fence in (auth, facts) if fence is not None)

    result = combined.hold(fences)

    assert result.current is (facts_current and authorization_current)
    if auth_fence:
        assert connection.executed == 1
    else:
        assert connection.executed == 0
    if facts is not None:
        assert facts_port.received == (facts,)


def test_auth_fence_requires_transaction() -> None:
    artifacts = pilot.PilotFakeArtifacts()
    connection = _Connection(active=False)
    combined = pilot._CombinedBe1OwnerFence(
        cast(Connection, connection),
        lambda *_args: None,
        lock_timeout_ms=1000,
        artifacts=artifacts,
    )

    assert combined.hold((OwnerFence(pilot._AUTH_FENCE_PREFIX + "{}", 1),)).current is False
    assert connection.executed == 0


def test_facts_fence_requires_transaction(monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    combined, connection, _facts_port = _combined(monkeypatch, artifacts)

    result = combined.hold((OwnerFence("facts:valid", 3),))

    assert result.current is False
    assert connection.executed == 0


def test_artifact_store_exception_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    _artifact_ref, descriptor = _artifact_descriptor(artifacts)
    assert descriptor.fence is not None
    monkeypatch.setattr(
        artifacts,
        "hold_fences",
        lambda _fences: (_ for _ in ()).throw(RuntimeError()),
    )
    combined, _connection, _facts_port = _combined(monkeypatch, artifacts)

    assert combined.hold((descriptor.fence,)).current is False


def test_factory_shares_the_artifact_store_with_each_unit_of_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = pilot.PilotFakeArtifacts()
    connection = _Connection(active=False)
    factory = pilot._CombinedBe1OwnerFenceFactory(
        lambda *_args: None, lock_timeout_ms=1000, artifacts=artifacts
    )

    port = cast(pilot._CombinedBe1OwnerFence, factory(cast(Connection, connection)))

    assert port._artifacts is artifacts
