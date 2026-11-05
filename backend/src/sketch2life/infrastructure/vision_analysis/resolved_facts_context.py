"""Request-bound Vision context adapter over recomputed BE2-03 ``ResolvedFacts``."""

from __future__ import annotations

from collections.abc import Callable

from sketch2life.application.ports.vision_analysis import (
    AnalysisContextPort,
    ContextDecision,
)
from sketch2life.domain.assistance import ResolvedFacts
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityBasis, EligibilityScope
from sketch2life.domain.vision_analysis import AnalysisScope, AssistancePin

ResolvedFactsResolver = Callable[[str], ResolvedFacts | None]


class ResolvedFactsAnalysisContext:
    """Supply freshness from the current request facts, not the BE1 reader's local digest.

    ``current`` delegates to an optional legacy context for callers that do not have an
    assistance request identity. Vision observation/replay paths use the request-bound
    methods and recompute ``ResolvedFacts`` for that request.
    """

    def __init__(
        self,
        resolver: ResolvedFactsResolver,
        *,
        fallback: AnalysisContextPort | None = None,
    ) -> None:
        self._resolver = resolver
        self._fallback = fallback

    def current(self, scope: AnalysisScope) -> ContextDecision:
        if self._fallback is not None:
            return self._fallback.current(scope)
        return _denied_context(scope)

    def current_for_pin(self, pin: AssistancePin) -> ContextDecision:
        return self.current_for_assistance(pin.assistance_id, pin.scope)

    def current_for_assistance(self, assistance_id: str, scope: AnalysisScope) -> ContextDecision:
        facts = self._resolver(assistance_id)
        if facts is None or not facts.members or not _facts_match_scope(facts, scope):
            return _denied_context(scope)
        if (
            all(member.eligibility_basis is None for member in facts.members)
            and self._fallback is not None
        ):
            return self._fallback.current(scope)
        return _context_from_facts(facts, scope)


def _facts_match_scope(facts: ResolvedFacts, scope: AnalysisScope) -> bool:
    return (
        facts.organization_id == scope.organization_id
        and facts.class_id == scope.class_id
        and facts.session_id == scope.session_id
        and facts.canvas_id == scope.canvas_id
        and facts.group_id == scope.group_id
        and facts.contributor_participant_id == scope.contributor_participant_id
        and facts.audience == scope.audience_participant_ids
        and facts.purpose_code == scope.purpose_code
    )


def _context_from_facts(facts: ResolvedFacts, scope: AnalysisScope) -> ContextDecision:
    members = facts.members
    if not members or tuple(member.participant_id for member in members) != facts.audience:
        return _denied_context(scope)
    expected_scope = (
        EligibilityScope(
            facts.organization_id,
            facts.class_id,
            facts.audience[0],
            facts.purpose_code,
        )
        if len(facts.audience) == 1
        else None
    )

    basis: str | None
    synthetic = all(
        member.eligibility_basis == EligibilityBasis.SYNTHETIC_DEV for member in members
    )
    if synthetic:
        if len(members) != 1:
            return _denied_context(scope)
        member = members[0]
        if (
            member.consent_effective
            or member.purpose_granted
            or member.consent_record_ref is not None
            or member.consent_revision is not None
            or member.eligibility_scope != expected_scope
            or member.basis_version != BASIS_VERSION
            or not member.evidence_ref
        ):
            return _denied_context(scope)
        basis = EligibilityBasis.SYNTHETIC_DEV
        basis_version = member.basis_version
        evidence_ref = member.evidence_ref
        eligibility_scope = member.eligibility_scope
        consent_effective = False
        purpose_granted = False
    else:
        if any(member.eligibility_basis == EligibilityBasis.SYNTHETIC_DEV for member in members):
            return _denied_context(scope)
        explicit_legal = all(
            member.eligibility_basis == EligibilityBasis.LEGAL_CONSENT for member in members
        )
        if explicit_legal:
            if any(
                member.basis_version != BASIS_VERSION
                or member.evidence_ref is not None
                or member.eligibility_scope not in (None, expected_scope)
                for member in members
            ):
                return _denied_context(scope)
            basis = str(EligibilityBasis.LEGAL_CONSENT)
            basis_version = BASIS_VERSION
            evidence_ref = None
            eligibility_scope = expected_scope
        else:
            if any(
                member.eligibility_basis is not None
                or member.basis_version is not None
                or member.evidence_ref is not None
                or member.eligibility_scope is not None
                for member in members
            ):
                return _denied_context(scope)
            basis = None
            basis_version = None
            evidence_ref = None
            eligibility_scope = None
        consent_effective = all(member.consent_effective for member in members)
        purpose_granted = all(member.purpose_granted for member in members)

    return ContextDecision(
        context_revision=facts.context_revision,
        consent_effective=consent_effective,
        purpose_granted=purpose_granted,
        session_active=True,
        audience_age_months=tuple(
            (member.participant_id, member.completed_age_months) for member in members
        ),
        age_policy_ref=facts.age_policy_ref,
        eligibility_basis=basis,
        basis_version=basis_version,
        evidence_ref=evidence_ref,
        eligibility_scope=eligibility_scope,
        context_digest=f"sha256:{facts.digest()}",
    )


def _denied_context(scope: AnalysisScope) -> ContextDecision:
    expected_scope = (
        EligibilityScope(
            scope.organization_id,
            scope.class_id,
            scope.audience_participant_ids[0],
            scope.purpose_code,
        )
        if len(scope.audience_participant_ids) == 1
        else None
    )
    return ContextDecision(
        context_revision=0,
        consent_effective=False,
        purpose_granted=False,
        session_active=False,
        audience_age_months=(),
        eligibility_basis=str(EligibilityBasis.DENIED),
        eligibility_scope=expected_scope,
    )


__all__ = ["ResolvedFactsAnalysisContext", "ResolvedFactsResolver"]
