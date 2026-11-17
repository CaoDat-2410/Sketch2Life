"""The synthetic basis covers exactly one audience member at all three BE2 gates.

The assistance gate, the vision gate and the BE1 fact reader each decide independently.
These tests pin that they agree: one valid synthetic member is allowed everywhere, two
synthetic members (each with its own exact scope) are refused everywhere, and a multi-member
legal audience keeps its existing behavior.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sketch2life.application.ports.vision_analysis import ContextDecision
from sketch2life.application.services.vision_analysis import eligibility_code
from sketch2life.domain import assistance as assistance_domain
from sketch2life.domain.assistance import MemberFact, audience_refusal
from sketch2life.domain.eligibility import (
    BASIS_VERSION,
    PROOF_VERSION,
    SYNTHETIC_AUDIENCE_SIZE,
    EligibilityScope,
    ProvisionalDataOrigin,
)
from sketch2life.domain.vision_analysis import AnalysisScope, ProviderContextMode
from sketch2life.infrastructure.assistance.be1_fact_reader import (
    BE1FactReader,
    BE1FactRequest,
    BE1FactSnapshot,
    BE1SyntheticProofFact,
    FactReaderReason,
)

_ORG = "synthetic-org"
_CLASS = "synthetic-class"
_SESSION = "synthetic-session"
_PURPOSE = "synthetic-purpose"
_FIRST = "synthetic-child-1"
_SECOND = "synthetic-child-2"
_NOW = datetime(2026, 11, 1, 12, tzinfo=UTC)


def _scope(child: str) -> EligibilityScope:
    return EligibilityScope(_ORG, _CLASS, child, _PURPOSE)


def _synthetic_member(child: str) -> MemberFact:
    return MemberFact(
        participant_id=child,
        completed_age_months=60,
        age_provenance_ref=f"synthetic-age:{child}",
        age_revision=1,
        consent_record_ref=None,
        consent_revision=None,
        consent_effective=False,
        purpose_granted=False,
        eligibility_basis="SYNTHETIC_DEV",
        basis_version=BASIS_VERSION,
        evidence_ref=f"synthetic-evidence:{child}",
        eligibility_scope=_scope(child),
    )


def _legal_member(child: str) -> MemberFact:
    return MemberFact(
        participant_id=child,
        completed_age_months=60,
        age_provenance_ref=f"age:{child}",
        age_revision=1,
        consent_record_ref=f"consent:{child}",
        consent_revision=1,
        consent_effective=True,
        purpose_granted=True,
        eligibility_basis="LEGAL_CONSENT",
        basis_version=BASIS_VERSION,
    )


def _assist(audience: tuple[str, ...], members: tuple[MemberFact, ...]) -> str | None:
    return audience_refusal(
        audience, members, organization_id=_ORG, class_id=_CLASS, purpose_code=_PURPOSE
    )


def _analysis_scope(audience: tuple[str, ...]) -> AnalysisScope:
    return AnalysisScope(
        organization_id=_ORG,
        class_id=_CLASS,
        session_id=_SESSION,
        canvas_id="synthetic-canvas",
        group_id=None if len(audience) == 1 else "synthetic-group",
        contributor_participant_id=audience[0],
        audience_participant_ids=audience,
        purpose_code=_PURPOSE,
    )


def _synthetic_context(audience: tuple[str, ...]) -> ContextDecision:
    return ContextDecision(
        context_revision=1,
        context_digest="sha256:" + "a" * 64,
        consent_effective=False,
        purpose_granted=False,
        session_active=True,
        audience_age_months=tuple((child, 60) for child in audience),
        eligibility_basis="SYNTHETIC_DEV",
        basis_version=BASIS_VERSION,
        evidence_ref="synthetic-evidence",
        eligibility_scope=_scope(audience[0]),
    )


def _legal_context(audience: tuple[str, ...]) -> ContextDecision:
    return ContextDecision(
        context_revision=1,
        consent_effective=True,
        purpose_granted=True,
        session_active=True,
        audience_age_months=tuple((child, 60) for child in audience),
        eligibility_basis="LEGAL_CONSENT",
        basis_version=BASIS_VERSION,
    )


def _snapshot(child: str) -> BE1FactSnapshot:
    proof = BE1SyntheticProofFact(
        evidence_id="synthetic-proof",
        schema_version=PROOF_VERSION,
        data_origin="SYNTHETIC_DEV",
        scope=_scope(child),
        run_ref="synthetic-run",
        session_id=_SESSION,
        issued_at=_NOW - timedelta(minutes=1),
        expires_at=_NOW + timedelta(hours=1),
        revoked_at=None,
        revocation_revision=0,
    )
    return BE1FactSnapshot(
        organization_id=_ORG,
        class_id=_CLASS,
        session_id=_SESSION,
        session_state="active",
        session_run_ref="synthetic-run",
        environment="test",
        pilot_enabled=True,
        purpose_ref=_PURPOSE,
        child_id=child,
        profile_origin=ProvisionalDataOrigin.SYNTHETIC_DEV,
        profile_state="active",
        age_months=60,
        age_revision=1,
        age_source="SYNTHETIC_FIXTURE",
        consent_record_ref=None,
        consent_revision=None,
        consent_state=None,
        legal_consent_effective=False,
        purpose_granted=False,
        membership_state="admitted",
        group_id="synthetic-group",
        proof=proof,
        evaluated_at=_NOW,
    )


class _Source:
    def __init__(self, snapshot: BE1FactSnapshot) -> None:
        self.snapshot = snapshot

    def current_facts(self, request: BE1FactRequest) -> BE1FactSnapshot | None:
        del request
        return self.snapshot


def _read(audience: tuple[str, ...]) -> FactReaderReason:
    request = BE1FactRequest(
        organization_id=_ORG,
        class_id=_CLASS,
        session_id=_SESSION,
        child_id=_FIRST,
        purpose_ref=_PURPOSE,
        audience_participant_ids=audience,
        context_mode=ProviderContextMode.IMAGE_ONLY,
    )
    return BE1FactReader(_Source(_snapshot(_FIRST))).read(request).reason


def test_the_shared_limit_is_exactly_one_member() -> None:
    assert SYNTHETIC_AUDIENCE_SIZE == 1


def test_one_valid_synthetic_member_is_allowed_at_all_three_gates() -> None:
    audience = (_FIRST,)

    assert _assist(audience, (_synthetic_member(_FIRST),)) is None
    assert eligibility_code(_synthetic_context(audience), _analysis_scope(audience)) is None
    assert _read(audience) is FactReaderReason.ALLOWED


def test_two_synthetic_members_are_refused_at_all_three_gates() -> None:
    audience = (_FIRST, _SECOND)

    # Each member carries a valid, exactly scoped synthetic basis of its own.
    assert (
        _assist(audience, (_synthetic_member(_FIRST), _synthetic_member(_SECOND)))
        == "CONSENT_REQUIRED"
    )
    assert (
        eligibility_code(_synthetic_context(audience), _analysis_scope(audience))
        == "CONSENT_REQUIRED"
    )
    assert _read(audience) is FactReaderReason.AUDIENCE_UNSUPPORTED


def test_a_synthetic_member_in_a_mixed_audience_is_refused_in_either_order() -> None:
    audience = (_FIRST, _SECOND)

    assert _assist(audience, (_synthetic_member(_FIRST), _legal_member(_SECOND))) == (
        "CONSENT_REQUIRED"
    )
    assert _assist(audience, (_legal_member(_SECOND), _synthetic_member(_FIRST))) == (
        "CONSENT_REQUIRED"
    )


def test_each_single_synthetic_member_stays_allowed_alone() -> None:
    for child in (_FIRST, _SECOND):
        assert _assist((child,), (_synthetic_member(child),)) is None


def test_multi_member_legal_audience_behaves_as_before() -> None:
    audience = (_FIRST, _SECOND)

    assert _assist(audience, (_legal_member(_FIRST), _legal_member(_SECOND))) is None
    assert eligibility_code(_legal_context(audience), _analysis_scope(audience)) is None
    # The legacy legal facts carry no basis metadata at all.
    legacy = tuple(
        replace(
            _legal_member(child),
            eligibility_basis=None,
            basis_version=None,
        )
        for child in audience
    )
    assert audience_refusal(audience, legacy) is None


def test_assistance_reads_the_single_shared_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    audience = (_FIRST, _SECOND)
    members = (_synthetic_member(_FIRST), _synthetic_member(_SECOND))
    assert _assist(audience, members) == "CONSENT_REQUIRED"

    monkeypatch.setattr(assistance_domain, "SYNTHETIC_AUDIENCE_SIZE", 2)

    assert _assist(audience, members) is None


@pytest.mark.parametrize("audience", ((), (_FIRST, _FIRST)))
def test_reader_keeps_refusing_empty_and_duplicate_audiences(audience: tuple[str, ...]) -> None:
    assert _read(audience) is FactReaderReason.AUDIENCE_UNSUPPORTED
