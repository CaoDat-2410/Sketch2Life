from __future__ import annotations

from dataclasses import replace

import pytest
from sketch2life.application.ports import vision_analysis as vision_port
from sketch2life.application.services.vision_analysis import (
    ObservationDisposition,
    eligibility_code,
)
from sketch2life.domain import vision_analysis as vision_domain
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityScope
from sketch2life.domain.vision_analysis import AnalysisScope
from sketch2life.infrastructure.assistance import context_revision as revision_module
from sketch2life.infrastructure.vision_analysis.harness import build_analysis_harness


def test_context_digest_is_full_versioned_sha256_and_order_independent() -> None:
    make_digest = getattr(revision_module, "context_digest", None)
    assert callable(make_digest)
    payload = {
        "schema_version": "be1-fact-context-v2",
        "age_revision": 2,
        "age_source": "SYNTHETIC_FIXTURE",
    }
    digest = make_digest(payload)
    assert isinstance(digest, str)
    assert len(digest) == len("sha256:") + 64
    assert digest.startswith("sha256:")
    assert digest[7:] == digest[7:].lower()
    assert make_digest(dict(reversed(list(payload.items())))) == digest


def test_context_revision_is_derived_from_the_same_full_digest() -> None:
    make_digest = getattr(revision_module, "context_digest", None)
    get_revision = getattr(revision_module, "context_revision", None)
    assert callable(make_digest) and callable(get_revision)
    payload = {"schema_version": "be1-fact-context-v2", "age_months": 60, "age_revision": 1}
    digest = make_digest(payload)
    expected = int.from_bytes(bytes.fromhex(digest[7:])[:4], "big") & 0x7FFFFFFF
    assert get_revision(payload) == (expected or 1)


def test_context_freshness_requires_equal_digest_when_either_peer_has_one() -> None:
    matches = getattr(vision_domain, "context_freshness_matches", None)
    assert callable(matches)
    digest = "sha256:" + "a" * 64
    assert matches(7, 7, None, None)
    assert matches(7, 7, digest, digest)
    assert not matches(7, 7, digest, None)
    assert not matches(7, 7, None, digest)
    assert not matches(7, 7, digest, "sha256:" + "b" * 64)
    assert not matches(7, 8, digest, digest)


def test_synthetic_context_without_digest_is_refused_but_legal_legacy_is_compatible() -> None:
    context_type = vision_port.ContextDecision
    fields = getattr(context_type, "__dataclass_fields__", {})
    assert "context_digest" in fields
    scope = AnalysisScope(
        organization_id="org-1",
        class_id="class-1",
        session_id="session-1",
        canvas_id="canvas-1",
        group_id="group-1",
        contributor_participant_id="child-1",
        audience_participant_ids=("child-1",),
        purpose_code="purpose-1",
    )
    synthetic = context_type(
        context_revision=1,
        consent_effective=False,
        purpose_granted=False,
        session_active=True,
        audience_age_months=(("child-1", 60),),
        eligibility_basis="SYNTHETIC_DEV",
        basis_version=BASIS_VERSION,
        evidence_ref="synthetic-proof",
        eligibility_scope=EligibilityScope("org-1", "class-1", "child-1", "purpose-1"),
    )
    assert eligibility_code(synthetic, scope) == "STALE_CONTEXT"

    digest = "sha256:" + "c" * 64
    assert eligibility_code(replace(synthetic, context_digest=digest), scope) is None

    # Keep legal ContextDecision construction compatible when the optional digest is absent.
    legal = context_type(
        context_revision=1,
        consent_effective=True,
        purpose_granted=True,
        session_active=True,
        audience_age_months=(("child-1", 60),),
        eligibility_basis="LEGAL_CONSENT",
    )
    assert legal.context_digest is None


def test_digest_bearing_context_cannot_match_integer_only_observation_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = build_analysis_harness()
    original_current = harness.context.current
    digest = "sha256:" + "d" * 64
    monkeypatch.setattr(
        harness.context,
        "current",
        lambda scope: replace(original_current(scope), context_digest=digest),
    )

    result = harness.observe()

    assert result.disposition is ObservationDisposition.REFUSED
    assert result.code == "STALE_CONTEXT"
    assert not result.provider_invoked


def test_provider_time_digest_movement_marks_observation_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = build_analysis_harness()
    original_current = harness.context.current
    calls = 0

    def current(scope: AnalysisScope) -> vision_port.ContextDecision:
        nonlocal calls
        calls += 1
        context = original_current(scope)
        if calls == 1:
            return context
        return replace(context, context_digest="sha256:" + "e" * 64)

    monkeypatch.setattr(harness.context, "current", current)

    result = harness.observe()

    assert result.disposition is ObservationDisposition.STALE
    assert result.provider_invoked


def test_replay_fails_closed_when_current_digest_appears_after_legacy_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = build_analysis_harness()
    analysis_id = harness.accepted_analysis()
    original_current = harness.context.current
    monkeypatch.setattr(
        harness.context,
        "current",
        lambda scope: replace(original_current(scope), context_digest="sha256:" + "f" * 64),
    )

    result = harness.observe()

    assert result.disposition is ObservationDisposition.STALE
    assert result.analysis_id == analysis_id
    assert result.replayed
