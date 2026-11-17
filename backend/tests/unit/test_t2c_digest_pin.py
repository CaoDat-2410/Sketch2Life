"""The synthetic pilot pins full resolved facts without changing legacy fixture callers."""

import json
from dataclasses import replace
from hashlib import sha256

import pytest
from sketch2life.domain.assistance import MemberFact, RequestStatus
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityBasis, EligibilityScope
from sketch2life.domain.vision_analysis import AnalysisRuleViolation, InvalidationReason
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CLASS,
    ORG,
    PURPOSE,
    build_assistance_harness,
)
from sketch2life.infrastructure.vision_analysis.resolved_facts_context import (
    ResolvedFactsAnalysisContext,
)


def test_synthetic_pin_matches_recomputed_context_and_accepts_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = build_assistance_harness()
    scope = EligibilityScope(ORG, CLASS, CHILD_A, PURPOSE)
    member = MemberFact(
        CHILD_A,
        60,
        "synthetic-age",
        1,
        None,
        None,
        False,
        False,
        eligibility_basis=EligibilityBasis.SYNTHETIC_DEV,
        basis_version=BASIS_VERSION,
        evidence_ref="synthetic-proof",
        eligibility_scope=scope,
    )
    monkeypatch.setattr(h.owner, "members", lambda *args, **kwargs: (member,))
    request = h.submit().request
    pin = h.service.pin(request.assistance_id)
    assert pin is not None
    assert pin.context_digest == "sha256:" + request.assistance_context_digest
    context = ResolvedFactsAnalysisContext(h.service.current_resolved_facts).current_for_pin(pin)
    assert context.context_digest == pin.context_digest
    assert context.context_revision == pin.context_revision
    assert context.consent_effective is False and context.purpose_granted is False
    assert context.eligibility_basis == EligibilityBasis.SYNTHETIC_DEV
    assert h.run_vision(request.assistance_id).status is RequestStatus.ANALYSIS_READY
    assert len(h.vision_provider.requests) == 1


@pytest.mark.parametrize("when", ["before", "during"])
def test_changed_synthetic_facts_refuse_before_or_after_provider(
    monkeypatch: pytest.MonkeyPatch,
    when: str,
) -> None:
    h = build_assistance_harness()
    values = [
        MemberFact(
            CHILD_A,
            60,
            "synthetic-age",
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
    ]
    monkeypatch.setattr(h.owner, "members", lambda *args, **kwargs: tuple(values))
    request = h.submit().request
    h.dispatch()
    started, job_id, attempt_id = h.start_next()
    assert started.started

    def move() -> None:
        values[0] = replace(values[0], age_revision=2)

    if when == "before":
        move()
    else:
        h.vision_provider.on_observe = move
    from sketch2life.domain.vision_analysis import ObservationClaim

    result = h.vision.record_observation(
        ObservationClaim(
            job_id,
            attempt_id,
            request.assistance_id,
            request.request_revision,
            request.facts.source.snapshot_ref,
            request.facts.context_revision,
        ),
        correlation_id="synthetic-digest-moved",
    )
    assert not result.authoritative
    if when == "before":
        assert result.code == "STALE_CONTEXT" and not result.provider_invoked
        assert h.vision_provider.requests == []
    else:
        assert result.code == InvalidationReason.CONTEXT_CHANGED and result.provider_invoked
        assert len(h.vision_provider.requests) == 1


def test_member_fact_mutation_changes_revision_and_full_resolved_facts_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.application.services.assistance import resolved_facts_context_revision
    from sketch2life.domain.assistance import ResolvedFacts
    from sketch2life.infrastructure.assistance.context_revision import (
        CONTEXT_REVISION_DOMAIN,
        CONTEXT_REVISION_MAX,
        CONTEXT_REVISION_SCHEMA_VERSION,
        context_revision,
    )

    h = build_assistance_harness()
    member = MemberFact(
        CHILD_A,
        60,
        "synthetic-age",
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
    current_member = [member]
    monkeypatch.setattr(h.owner, "members", lambda *args, **kwargs: tuple(current_member))
    request = h.submit().request
    pinned_facts = request.facts
    assert pinned_facts.context_revision != 0
    expected_before = context_revision(
        {
            "resolved_facts_digest": replace(pinned_facts, context_revision=0).digest(),
            "schema_version": CONTEXT_REVISION_SCHEMA_VERSION,
        }
    )
    assert pinned_facts.context_revision == expected_before
    assert resolved_facts_context_revision(pinned_facts) == expected_before

    current_member[0] = replace(member, age_revision=2, evidence_ref="synthetic-proof-v2")
    current_facts = h.service.current_resolved_facts(request.assistance_id, request=request)
    assert isinstance(current_facts, ResolvedFacts)
    expected_after = context_revision(
        {
            "resolved_facts_digest": replace(current_facts, context_revision=0).digest(),
            "schema_version": CONTEXT_REVISION_SCHEMA_VERSION,
        }
    )
    assert current_facts.context_revision == expected_after
    assert current_facts.context_revision != pinned_facts.context_revision
    assert current_facts.digest() != pinned_facts.digest()

    canonical = json.dumps(
        {
            "resolved_facts_digest": replace(current_facts, context_revision=0).digest(),
            "schema_version": CONTEXT_REVISION_SCHEMA_VERSION,
        },
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    raw = sha256(CONTEXT_REVISION_DOMAIN + canonical).digest()
    expected_low_31 = int.from_bytes(raw[:4], "big") & CONTEXT_REVISION_MAX
    assert current_facts.context_revision == (expected_low_31 or 1)
    pin = h.service.pin(request.assistance_id)
    assert pin is not None and pin.context_digest == "sha256:" + request.assistance_context_digest
    context = ResolvedFactsAnalysisContext(lambda _assistance_id: current_facts).current_for_pin(
        pin
    )
    assert context.context_revision == current_facts.context_revision
    assert context.context_digest == "sha256:" + current_facts.digest()


def test_fake_assistance_owner_scoped_members_and_legacy_compatibility() -> None:
    from sketch2life.domain.eligibility import EligibilityScope

    h = build_assistance_harness()
    h.owner.set_member(CHILD_A, months=60, purposes=frozenset({PURPOSE}))
    legacy = h.owner.members(ORG, (CHILD_A,), PURPOSE)
    assert legacy
    valid = EligibilityScope(ORG, CLASS, CHILD_A, PURPOSE)
    assert h.owner.members(ORG, (CHILD_A,), PURPOSE, scope=valid) == legacy
    assert (
        h.owner.members(
            ORG,
            (CHILD_A,),
            PURPOSE,
            scope=EligibilityScope("synthetic-other-org", CLASS, CHILD_A, PURPOSE),
        )
        == ()
    )
    assert (
        h.owner.members(
            ORG,
            (CHILD_A,),
            PURPOSE,
            scope=EligibilityScope(ORG, CLASS, "synthetic-other-child", PURPOSE),
        )
        == ()
    )
    assert (
        h.owner.members(
            ORG,
            (CHILD_A,),
            PURPOSE,
            scope=EligibilityScope(ORG, CLASS, CHILD_A, "synthetic-other-purpose"),
        )
        == ()
    )
    assert h.owner.members(ORG, (CHILD_A,), PURPOSE) == legacy


def test_missing_or_cross_scope_current_facts_are_denied() -> None:
    h = build_assistance_harness()
    request = h.submit().request
    pin = h.service.pin(request.assistance_id)
    assert pin is not None
    facts = replace(request.facts, organization_id="synthetic-other-org")
    for resolver in (lambda _: None, lambda _: facts):
        context = ResolvedFactsAnalysisContext(resolver).current_for_pin(pin)
        assert not context.session_active
        assert context.eligibility_basis == EligibilityBasis.DENIED
        context = ResolvedFactsAnalysisContext(
            resolver, fallback=h.vision_context
        ).current_for_assistance(request.assistance_id, pin.scope)
        assert not context.session_active


def test_legacy_pin_and_no_scope_members_keep_existing_semantics() -> None:
    h = build_assistance_harness()
    assert h.owner.members(ORG, (CHILD_A,), PURPOSE)
    request = h.submit().request
    pin = h.service.pin(request.assistance_id)
    assert pin is not None and pin.context_digest is None
    assert h.run_vision(request.assistance_id).status is RequestStatus.ANALYSIS_READY
    with pytest.raises(AnalysisRuleViolation):
        replace(pin, context_digest="invalid")


def test_pilot_policy_is_fixed_and_only_enabled_in_local_test() -> None:
    from sketch2life.infrastructure.assistance.pilot_policy import (
        PILOT_SYNTHETIC_POLICY_V1,
        PilotSyntheticPolicy,
    )

    policy = PILOT_SYNTHETIC_POLICY_V1
    assert policy.age_policy_ref == "age-policy:36-155-months:proposed"
    assert policy.region_policy_revision == 2 and dict(policy.regions) == {"region_fx_open": None}
    assert (policy.debounce_seconds, policy.per_target_limit, policy.per_session_limit) == (
        5,
        3,
        20,
    )
    assert policy.allowed_levels == {"level_fx_1", "level_fx_2"}
    with pytest.raises(TypeError):
        policy.regions["other"] = None  # type: ignore[index]
    assert (
        PilotSyntheticPolicy(environment="test", pilot_enabled=True).current(ORG, "session")
        is policy
    )
    assert (
        PilotSyntheticPolicy(environment="staging", pilot_enabled=True).current(ORG, "session")
        is None
    )
    assert (
        PilotSyntheticPolicy(environment="test", pilot_enabled=False).current(ORG, "session")
        is None
    )
