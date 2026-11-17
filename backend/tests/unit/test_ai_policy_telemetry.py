"""Synthetic health/queue source conformance; runtime-kind fixtures are not live proof."""

from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_operations import AiPolicyOperations
from sketch2life.application.ai_policy_telemetry import telemetry_view
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_telemetry import (
    OperationsTelemetryObservation,
    OperationsTelemetryView,
)
from sketch2life.domain.ai_policy.model import Capability, PolicyError
from tests.ai_policy_fixtures import harness
from tests.unit.test_ai_policy_domain import NOW
from tests.unit.test_ai_policy_operations import REQUEST

SOURCE = PolicyDefinitionRef(ref="fixture-telemetry", version=1, hash="a" * 64)


def observation(**changes):
    return OperationsTelemetryObservation.model_validate(
        dict(
            organization_id="school",
            feature_scope="fixture.feature",
            source_ref=SOURCE,
            evidence_kind="fixture",
            observed_at=NOW - timedelta(seconds=1),
            expires_at=NOW + timedelta(seconds=1),
            health_state="healthy",
            queued_jobs=0,
            running_jobs=2,
        )
        | changes
    )


class Reader:
    def __init__(self, value):
        self.value, self.calls = value, []

    def snapshot(self, org, feature):
        self.calls.append((org, feature))
        return self.value


def setup(reader=None):
    _, boundary, store = harness()
    boundary.rights["monitor"] = {Capability.OPERATIONS_READ}
    service = AiPolicyOperations(
        store,
        boundary,
        telemetry=reader,
        telemetry_source=None if reader is None else SOURCE,
        clock=lambda: NOW,
    )
    return service, boundary, store


def test_unconfigured_or_missing_observation_is_unavailable_not_healthy_or_zero():
    for reader in (None, Reader(None)):
        service, _, store = setup(reader)
        result = service.read("monitor", "school", REQUEST)
        assert result.telemetry.availability == "unavailable"
        assert result.telemetry.health_state is result.telemetry.queued_jobs is None
        assert result.telemetry.running_jobs is result.telemetry.source_ref is None
        assert not store.events and not store.scopes


@pytest.mark.parametrize("kind", ["fixture", "runtime"])
def test_fresh_report_preserves_zero_and_source_kind_not_actual_runtime_proof(kind):
    reader = Reader(observation(evidence_kind=kind))
    service, _, _ = setup(reader)
    view = service.read("monitor", "school", REQUEST).telemetry
    assert reader.calls == [("school", "fixture.feature")]
    assert view.availability == "fresh" and view.evidence_kind == kind and view.source_ref == SOURCE
    assert view.queued_jobs == 0 and view.running_jobs == 2 and view.health_state == "healthy"
    assert view.semantics == "reported_by_source_not_execution_authority"


@pytest.mark.parametrize(
    "fields",
    [
        dict(health_state=None, queued_jobs=0, running_jobs=None),
        dict(health_state="unavailable", queued_jobs=None, running_jobs=None),
    ],
)
def test_partial_observation_keeps_missing_metric_unknown(fields):
    result = telemetry_view(observation(**fields), "school", "fixture.feature", SOURCE, NOW)
    assert result.availability == "fresh"
    assert (result.health_state, result.queued_jobs, result.running_jobs) == (
        fields["health_state"],
        fields["queued_jobs"],
        fields["running_jobs"],
    )


@pytest.mark.parametrize("expiry", [NOW, NOW - timedelta(microseconds=1)])
def test_expired_values_suppressed_including_exact_boundary(expiry):
    result = telemetry_view(
        observation(expires_at=expiry), "school", "fixture.feature", SOURCE, NOW
    )
    assert result.availability == "stale" and result.evidence_kind == "fixture"
    assert result.observed_at is not None and result.expires_at == expiry
    assert result.health_state is result.queued_jobs is result.running_jobs is None


@pytest.mark.parametrize(
    "change",
    [
        dict(organization_id="other"),
        dict(feature_scope="other"),
        dict(source_ref=SOURCE.model_copy(update={"hash": "b" * 64})),
        dict(observed_at=NOW + timedelta(microseconds=1)),
        dict(queued_jobs=True),
        dict(running_jobs=-1),
        dict(health_state="unknown"),
        dict(evidence_kind="unverified"),
        dict(expires_at=NOW - timedelta(seconds=2)),
        dict(observed_at=NOW.replace(tzinfo=None)),
    ],
)
def test_wrong_binding_future_or_native_malformed_output_fails_closed(change):
    raw = observation().model_copy(update=change)
    service, _, _ = setup(Reader(raw))
    with pytest.raises(PolicyError, match="^AI_POLICY_OPERATIONS_UNAVAILABLE$"):
        service.read("monitor", "school", REQUEST)


def test_rechecks_expiry_after_own_transaction_work(monkeypatch):
    service, _, store = setup(Reader(observation()))
    clock = [NOW]
    service.clock = lambda: clock[0]
    original = store.effective_scope

    def delayed(*args, **kwargs):
        clock[0] = NOW + timedelta(seconds=1)
        return original(*args, **kwargs)

    monkeypatch.setattr(store, "effective_scope", delayed)
    result = service.read("monitor", "school", REQUEST).telemetry
    assert result.availability == "stale" and result.health_state is result.queued_jobs is None


def test_collector_outside_own_db_transaction_but_under_current_guard(monkeypatch):
    reader = Reader(observation())
    service, boundary, store = setup(reader)
    active = []
    original = store.transaction

    @contextmanager
    def transaction():
        active.append(True)
        try:
            with original() as tx:
                yield tx
        finally:
            active.pop()

    def collect(org, feature):
        assert boundary.held and not active
        return observation()

    monkeypatch.setattr(store, "transaction", transaction)
    monkeypatch.setattr(reader, "snapshot", collect)
    assert service.read("monitor", "school", REQUEST).telemetry.availability == "fresh"


def test_expiry_rechecked_after_transaction_exit_not_only_after_queries(monkeypatch):
    service, _, store = setup(Reader(observation()))
    clock = [NOW]
    service.clock = lambda: clock[0]
    original = store.transaction

    @contextmanager
    def delayed_commit():
        with original() as tx:
            yield tx
        clock[0] = NOW + timedelta(seconds=1)

    monkeypatch.setattr(store, "transaction", delayed_commit)
    result = service.read("monitor", "school", REQUEST).telemetry
    assert result.availability == "stale" and result.queued_jobs is result.health_state is None


def test_read_denial_before_collector_and_revocation_before_return(monkeypatch):
    reader = Reader(observation())
    service, boundary, store = setup(reader)
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.read("author", "school", REQUEST)
    assert not reader.calls

    def collect(org, feature):
        boundary.authority = replace(boundary.authority, capabilities=frozenset())
        return observation()

    reader.snapshot = collect

    def forbidden_transaction():
        pytest.fail("known revoked collector must not lead to a storage read")

    monkeypatch.setattr(store, "transaction", forbidden_transaction)
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.read("monitor", "school", REQUEST)


@pytest.mark.parametrize("error_type", [RuntimeError, PolicyError])
def test_private_producer_failure_is_error_not_successful_unknown(error_type):
    class Broken:
        def snapshot(self, org, feature):
            raise error_type("synthetic-private-provider-token")

    service, _, _ = setup(Broken())
    with pytest.raises(PolicyError, match="^AI_POLICY_OPERATIONS_UNAVAILABLE$"):
        service.read("monitor", "school", REQUEST)


def test_reader_and_source_profile_must_be_explicitly_bound_together():
    _, _, store = setup()
    for kwargs in (
        dict(telemetry=Reader(observation())),
        dict(telemetry_source=SOURCE),
        dict(telemetry=Reader(None), telemetry_source=SOURCE.model_copy(update={"version": True})),
    ):
        with pytest.raises(ValueError):
            AiPolicyOperations(store, store.boundary, **kwargs)


@pytest.mark.parametrize(
    "fields",
    [
        dict(health_state=None, queued_jobs=None, running_jobs=None),
        dict(provider_url="https://invalid.example/private"),
        dict(queued_jobs=True),
    ],
)
def test_observation_schema_does_not_accept_empty_private_or_coerced_values(fields):
    with pytest.raises(ValidationError):
        observation(**fields)


@pytest.mark.parametrize(
    "fields",
    [
        dict(queued_jobs=0),
        dict(health_state="healthy"),
        dict(availability="fresh"),
        dict(availability="stale"),
        dict(token="private"),
    ],
)
def test_projection_cannot_invent_available_values_or_private_fields(fields):
    with pytest.raises(ValidationError):
        OperationsTelemetryView(**fields)


def test_naive_clock_or_missing_bound_source_cannot_accept_observation():
    for source, now in ((SOURCE, NOW.replace(tzinfo=None)), (None, NOW)):
        with pytest.raises(PolicyError, match="AI_POLICY_OPERATIONS_UNAVAILABLE"):
            telemetry_view(observation(), "school", "fixture.feature", source, now)
