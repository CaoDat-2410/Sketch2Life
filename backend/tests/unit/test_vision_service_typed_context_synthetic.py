"""Synthetic Vision stays closed while its worker claim carries only an integer revision.

The synthetic context has a valid digest, but the current observation claim cannot carry it.
The pre-provider freshness gate therefore refuses both IMAGE_ONLY and TYPED_CONTEXT requests
as STALE_CONTEXT. This is the intentional fail-closed boundary pending the digest-bearing
Vision claim contract (T8); no provider call or analysis head may be created.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import pytest
from sketch2life.application.ports.vision_analysis import ContextDecision
from sketch2life.application.services.vision_analysis import ObservationDisposition
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityScope
from sketch2life.domain.vision_analysis import AnalysisScope, ProviderContextMode
from sketch2life.infrastructure.vision_analysis.fakes import FakeVisionObservationProvider
from sketch2life.infrastructure.vision_analysis.harness import (
    AnalysisHarness,
    build_analysis_harness,
)


def _as_synthetic(
    original: Callable[[AnalysisScope], ContextDecision],
) -> Callable[[AnalysisScope], ContextDecision]:
    def current(scope: AnalysisScope) -> ContextDecision:
        legal = original(scope)
        return ContextDecision(
            context_revision=legal.context_revision,
            context_digest="sha256:" + "a" * 64,
            consent_effective=False,
            purpose_granted=False,
            session_active=True,
            audience_age_months=legal.audience_age_months,
            eligibility_basis="SYNTHETIC_DEV",
            basis_version=BASIS_VERSION,
            evidence_ref="synthetic-evidence-001",
            eligibility_scope=EligibilityScope(
                scope.organization_id,
                scope.class_id,
                scope.audience_participant_ids[0],
                scope.purpose_code,
            ),
        )

    return current


def _harness(mode: ProviderContextMode) -> AnalysisHarness:
    harness = build_analysis_harness(required_context_mode=mode)
    harness.context.current = _as_synthetic(  # type: ignore[method-assign,assignment]
        harness.context.current
    )
    return harness


def _provider(harness: AnalysisHarness) -> FakeVisionObservationProvider:
    assert isinstance(harness.provider, FakeVisionObservationProvider)
    return harness.provider


def _stored_counts(harness: AnalysisHarness) -> tuple[int, int, int, int]:
    state = harness.store.snapshot()
    return (
        len(state.heads),
        len(state.observations),
        len(state.provider_results),
        len(state.corrections),
    )


def test_typed_context_synthetic_digest_is_stale_at_integer_claim_boundary() -> None:
    harness = _harness(ProviderContextMode.TYPED_CONTEXT)

    result = harness.observe()

    assert result.disposition is ObservationDisposition.REFUSED
    assert result.code == "STALE_CONTEXT"
    assert result.provider_invoked is False
    assert result.analysis_id is None
    assert len(_provider(harness).requests) == 0
    assert _stored_counts(harness) == (0, 0, 0, 0)


def test_typed_context_synthetic_digest_refusal_is_repeatable_and_never_stores_a_head() -> None:
    harness = _harness(ProviderContextMode.TYPED_CONTEXT)

    codes = [harness.observe().code for _ in range(3)]

    assert codes == ["STALE_CONTEXT"] * 3
    assert len(_provider(harness).requests) == 0
    assert _stored_counts(harness) == (0, 0, 0, 0)


def test_image_only_synthetic_digest_is_stale_at_integer_claim_boundary() -> None:
    harness = _harness(ProviderContextMode.IMAGE_ONLY)

    result = harness.observe()

    assert result.disposition is ObservationDisposition.REFUSED
    assert result.code == "STALE_CONTEXT"
    assert result.provider_invoked is False
    assert len(_provider(harness).requests) == 0
    assert _stored_counts(harness) == (0, 0, 0, 0)


@pytest.mark.parametrize(
    ("consent_effective", "purpose_granted"),
    ((True, False), (False, True), (True, True)),
)
def test_a_synthetic_basis_that_claims_legal_flags_is_refused_by_the_domain_gate_first(
    consent_effective: bool, purpose_granted: bool
) -> None:
    harness = build_analysis_harness(required_context_mode=ProviderContextMode.TYPED_CONTEXT)
    synthetic = _as_synthetic(harness.context.current)

    def contradictory(scope: AnalysisScope) -> ContextDecision:
        return replace(
            synthetic(scope), consent_effective=consent_effective, purpose_granted=purpose_granted
        )

    harness.context.current = contradictory  # type: ignore[method-assign]

    result = harness.observe()

    assert result.disposition is ObservationDisposition.REFUSED
    assert result.code == "CONSENT_REQUIRED"
    assert len(_provider(harness).requests) == 0
    assert _stored_counts(harness) == (0, 0, 0, 0)
