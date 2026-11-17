from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest
from sketch2life.application.ports.ai_jobs import (
    AuthorizationAction,
    DispatchMessage,
    Principal,
    PrincipalRole,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.vision_analysis import VisionObservationPort
from sketch2life.application.services.ai_jobs import QueueUnavailable
from sketch2life.application.services.vision_analysis import VisionAnalysisService
from sketch2life.domain.ai_jobs.completion import OutcomeKind
from sketch2life.domain.ai_jobs.model import JobScope, RequestRef
from sketch2life.domain.assistance import MemberFact, TargetKind, TargetScope
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityBasis, EligibilityScope
from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker, WorkerOutcome
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_G,
    CHILD_A,
    CLASS,
    ORG,
    PURPOSE,
    TEACHER,
    build_assistance_harness,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.vision_analysis.invocation_guard import (
    InvocationGuardedVisionObservationPort,
    InvocationLedgerGuard,
)
from sketch2life.infrastructure.vision_analysis.pilot_composition import (
    CurrentFactsBe1PilotEligibility,
    GuardedVisionJobProvider,
    PilotFakeArtifacts,
    PilotFakeIds,
    PilotObservationBinding,
    PostgresBe1PilotAuthorization,
    build_pilot_vision_composition,
)
from sketch2life.infrastructure.vision_analysis.pilot_queue import InProcessDispatchQueue
from sketch2life.interfaces.http import be1_runtime
from sqlalchemy import create_engine


def _settings(*, synthetic_pilot_enabled: bool = False) -> Settings:
    # BaseSettings accepts _env_file at runtime; keep tests independent from workstation files.
    return Settings(
        env="test",
        synthetic_pilot_enabled=synthetic_pilot_enabled,
        _env_file=None,  # type: ignore[call-arg]
    )


def _envelope(message_id: str) -> WorkerDispatchEnvelope:
    request_ref = RequestRef("synthetic-assistance", 1, "a" * 64, 3)
    message = DispatchMessage(
        message_id,
        "synthetic-job",
        "synthetic-attempt",
        1,
        "vision_analysis",
        request_ref,
    )
    return WorkerDispatchEnvelope(message, "synthetic-capability")


def test_in_process_queue_is_bounded_fifo_and_delivers_each_item_once() -> None:
    queue = InProcessDispatchQueue(capacity=2)
    first = _envelope("first")
    second = _envelope("second")
    queue.enqueue(first)
    queue.enqueue(second)
    with pytest.raises(QueueUnavailable):
        queue.enqueue(_envelope("overflow"))

    worker = Mock()
    worker.handle.side_effect = [
        WorkerOutcome("completed", None),
        WorkerOutcome("not_started", None),
    ]
    assert queue.run_one(cast(DispatchWorker, worker)) == WorkerOutcome("completed", None)
    assert queue.run_one(cast(DispatchWorker, worker)) == WorkerOutcome("not_started", None)
    assert queue.run_one(cast(DispatchWorker, worker)) is None
    assert [call.args[0].message.message_id for call in worker.handle.call_args_list] == [
        "first",
        "second",
    ]
    assert len(queue) == 0


def test_pilot_composition_is_default_off_and_never_calls_builders_when_disabled() -> None:
    engine = create_engine("sqlite://")
    never = Mock(side_effect=AssertionError("disabled pilot must not resolve dependencies"))
    try:
        composition = build_pilot_vision_composition(
            settings=_settings(),
            engine=engine,
            resolve_current_request=never,
            resolve_owner_facts=never,
            resolve_observation_binding=never,
            vision_service_factory=never,
        )
    finally:
        engine.dispose()

    assert composition is None
    never.assert_not_called()


def test_pilot_composition_rejects_non_postgres_engine_when_explicitly_enabled() -> None:
    engine = create_engine("sqlite://")
    never = Mock(side_effect=AssertionError("a composition dependency must not run"))
    try:
        with pytest.raises(ValueError, match="requires the PostgreSQL"):
            build_pilot_vision_composition(
                settings=_settings(synthetic_pilot_enabled=True),
                engine=engine,
                resolve_current_request=never,
                resolve_owner_facts=never,
                resolve_observation_binding=never,
                vision_service_factory=never,
            )
    finally:
        engine.dispose()
    never.assert_not_called()


def test_be1_authorization_fails_closed_before_database_access_for_invalid_scope() -> None:
    engine = Mock()
    authorization = PostgresBe1PilotAuthorization(engine)
    principal = Principal("teacher", "org", PrincipalRole.TEACHER)
    scope = JobScope("org", None, (), "wrong-purpose", "assistance")

    decision = authorization.decide(principal, action=AuthorizationAction.CREATE_JOB, scope=scope)

    assert decision.allowed is False
    assert decision.reason_code == "FORBIDDEN_SCOPE"
    engine.connect.assert_not_called()


def test_current_facts_eligibility_fails_closed_without_a_current_request() -> None:
    eligibility = CurrentFactsBe1PilotEligibility(lambda _org, _request: None)
    decision = eligibility.check(
        scope=JobScope("org", "session", ("child",), "purpose", "request"),
        request_ref=RequestRef("request", 1, "a" * 64, 3),
        job_type="vision_analysis",
    )

    assert decision.eligible is False
    assert decision.reason_code == "STALE_CONTEXT"


def test_current_facts_eligibility_accepts_only_the_matching_synthetic_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = build_assistance_harness()
    member = MemberFact(
        CHILD_A,
        60,
        "synthetic-age-source",
        1,
        None,
        None,
        False,
        False,
        eligibility_basis=EligibilityBasis.SYNTHETIC_DEV,
        basis_version=BASIS_VERSION,
        evidence_ref="synthetic-proof",
        eligibility_scope=EligibilityScope(ORG, CLASS, CHILD_A, PURPOSE),
    )
    monkeypatch.setattr(harness.owner, "members", lambda *_args, **_kwargs: (member,))
    request = harness.submit(
        harness.command(
            TEACHER,
            canvas=CANVAS_G,
            target=TargetScope(TargetKind.INDIVIDUAL, CHILD_A),
        )
    ).request
    facts = harness.service.current_resolved_facts(request.assistance_id)
    assert facts is not None
    scope = JobScope(
        ORG,
        request.facts.session_id,
        request.facts.audience,
        request.facts.purpose_code,
        request.assistance_id,
    )
    request_ref = RequestRef(
        request.assistance_id,
        request.request_revision,
        request.facts.source.input_hash,
        request.facts.context_revision,
    )

    eligibility = CurrentFactsBe1PilotEligibility(lambda _org, _request_id: (request, facts))
    decision = eligibility.check(scope=scope, request_ref=request_ref, job_type="vision_analysis")
    assert decision.eligible is True
    assert decision.fence is not None

    changed_request = replace(request, assistance_context_digest="0" * 64)
    stale = CurrentFactsBe1PilotEligibility(
        lambda _org, _request_id: (changed_request, facts)
    ).check(scope=scope, request_ref=request_ref, job_type="vision_analysis")
    assert stale.eligible is False
    assert stale.reason_code == "STALE_CONTEXT"

    personal_request = harness.submit().request
    personal_facts = harness.service.current_resolved_facts(personal_request.assistance_id)
    assert personal_facts is not None
    personal_scope = JobScope(
        ORG,
        personal_request.facts.session_id,
        personal_request.facts.audience,
        personal_request.facts.purpose_code,
        personal_request.assistance_id,
    )
    personal_ref = RequestRef(
        personal_request.assistance_id,
        personal_request.request_revision,
        personal_request.facts.source.input_hash,
        personal_request.facts.context_revision,
    )
    no_group = CurrentFactsBe1PilotEligibility(
        lambda _org, _request_id: (personal_request, personal_facts)
    ).check(scope=personal_scope, request_ref=personal_ref, job_type="vision_analysis")
    assert no_group.eligible is False
    assert no_group.reason_code == "STALE_CONTEXT"


def test_guarded_provider_does_not_accept_an_uninvoked_success_result() -> None:
    message = _envelope("guarded-provider").message
    binding = PilotObservationBinding(
        "org",
        message.request_ref.request_id,
        "snapshot",
        message.request_ref.request_revision,
        message.request_ref.input_hash,
        message.request_ref.context_revision,
        "correlation",
    )
    ledger = Mock()
    artifacts = PilotFakeArtifacts()
    services: list[SimpleNamespace] = []

    def service_factory(
        _binding: PilotObservationBinding, guard: InvocationLedgerGuard
    ) -> VisionAnalysisService:
        guarded_inner = SimpleNamespace(
            invocation_guard_identity=guard,
            supported_context_modes=frozenset(),
            context_capability=None,
        )
        service = SimpleNamespace(
            _d=SimpleNamespace(provider=None),
            record_observation=Mock(
                return_value=SimpleNamespace(authoritative=True, analysis_id="analysis-id")
            ),
        )
        services.append(service)
        service._d.provider = InvocationGuardedVisionObservationPort(
            cast(VisionObservationPort, guarded_inner), guard
        )
        return cast(VisionAnalysisService, service)

    provider = GuardedVisionJobProvider(
        ledger=ledger,
        resolve_binding=lambda _message: binding,
        service_factory=service_factory,
        artifacts=artifacts,
        ids=PilotFakeIds(),
    )

    claim = provider.run(message)

    assert claim.kind is OutcomeKind.FAILURE
    assert claim.failure_code == "PROVIDER_UNAVAILABLE"
    assert claim.retryable is False
    assert claim.outputs == ()
    assert len(services) == 1
    services[0].record_observation.assert_called_once()
    ledger.claim.assert_not_called()


def test_runtime_invokes_pilot_factory_only_behind_local_synthetic_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine("sqlite://")
    monkeypatch.setattr(
        be1_runtime,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    monkeypatch.setattr(be1_runtime, "create_core_engine", lambda _url: engine)
    monkeypatch.setattr(be1_runtime, "create_core_session_factory", lambda _engine: None)
    factory = Mock(return_value=object())

    try:
        disabled = be1_runtime.build_be1_runtime(_settings(), pilot_vision_factory=factory)
        assert disabled.pilot_vision is None
        factory.assert_not_called()

        enabled = be1_runtime.build_be1_runtime(
            _settings(synthetic_pilot_enabled=True),
            pilot_vision_factory=factory,
        )
    finally:
        engine.dispose()

    assert enabled.pilot_vision is factory.return_value
    factory.assert_called_once()
