"""BE2 gates accept only current, scope-bound synthetic eligibility metadata."""

from __future__ import annotations

from dataclasses import replace

import pytest
from sketch2life.application.ports.vision_analysis import ContextDecision
from sketch2life.application.services.vision_analysis import (
    _context_eligibility_ready,
    eligibility_code,
)
from sketch2life.domain.assistance import MemberFact, audience_refusal
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityScope
from sketch2life.domain.vision_analysis import AnalysisScope

_ORG = "synthetic-org"
_CLASS = "synthetic-class"
_CHILD = "synthetic-child"
_PURPOSE = "synthetic-purpose"
_SCOPE = EligibilityScope(_ORG, _CLASS, _CHILD, _PURPOSE)


def _member(**changes: object) -> MemberFact:
    base = MemberFact(
        participant_id=_CHILD,
        completed_age_months=60,
        age_provenance_ref="synthetic-age-proof",
        age_revision=1,
        consent_record_ref=None,
        consent_revision=None,
        consent_effective=False,
        purpose_granted=False,
        eligibility_basis="SYNTHETIC_DEV",
        basis_version=BASIS_VERSION,
        evidence_ref="synthetic-evidence-001",
        eligibility_scope=_SCOPE,
    )
    changes = dict(changes)
    if changes.get("eligibility_basis", base.eligibility_basis) != "SYNTHETIC_DEV":
        # Non-synthetic facts must carry a consent reference and revision (A2).
        changes.setdefault("consent_record_ref", "legal-consent-ref")
        changes.setdefault("consent_revision", 1)
    return replace(base, **changes)  # type: ignore[arg-type]


def _analysis_scope(audience: tuple[str, ...] = (_CHILD,)) -> AnalysisScope:
    return AnalysisScope(
        organization_id=_ORG,
        class_id=_CLASS,
        session_id="synthetic-session",
        canvas_id="synthetic-canvas",
        group_id=None,
        contributor_participant_id=audience[0],
        audience_participant_ids=audience,
        purpose_code=_PURPOSE,
    )


def _context(scope: AnalysisScope, **changes: object) -> ContextDecision:
    base = ContextDecision(
        context_revision=1,
        context_digest="sha256:" + "a" * 64,
        consent_effective=False,
        purpose_granted=False,
        session_active=True,
        audience_age_months=tuple(
            (participant, 60) for participant in scope.audience_participant_ids
        ),
        eligibility_basis="SYNTHETIC_DEV",
        basis_version=BASIS_VERSION,
        evidence_ref="synthetic-evidence-001",
        eligibility_scope=EligibilityScope(
            scope.organization_id,
            scope.class_id,
            scope.audience_participant_ids[0],
            scope.purpose_code,
        )
        if len(scope.audience_participant_ids) == 1
        else None,
    )
    return replace(base, **changes)  # type: ignore[arg-type]


def test_assistance_accepts_valid_synthetic_basis_with_legal_flags_false() -> None:
    assert (
        audience_refusal(
            (_CHILD,),
            (_member(),),
            organization_id=_ORG,
            class_id=_CLASS,
            purpose_code=_PURPOSE,
        )
        is None
    )


@pytest.mark.parametrize(
    "changes",
    (
        {"eligibility_basis": "REAL"},
        {"eligibility_basis": "PENDING"},
        {"eligibility_basis": "REVOKED"},
        {"eligibility_basis": "LEGACY_UNCLASSIFIED"},
        {"eligibility_basis": "SYNTHETIC_DEV", "basis_version": "unknown"},
        {"eligibility_basis": "SYNTHETIC_DEV", "evidence_ref": "  "},
        {"eligibility_basis": "SYNTHETIC_DEV", "eligibility_scope": None},
        {"eligibility_basis": "SYNTHETIC_DEV", "consent_effective": True},
        {"eligibility_basis": "SYNTHETIC_DEV", "purpose_granted": True},
        {
            "eligibility_basis": "SYNTHETIC_DEV",
            "eligibility_scope": EligibilityScope(_ORG, _CLASS, _CHILD, "foreign-purpose"),
        },
        {
            "eligibility_basis": "SYNTHETIC_DEV",
            "eligibility_scope": EligibilityScope("foreign-org", _CLASS, _CHILD, _PURPOSE),
        },
    ),
)
def test_assistance_rejects_unknown_or_mismatched_synthetic_basis(
    changes: dict[str, object],
) -> None:
    assert (
        audience_refusal(
            (_CHILD,),
            (_member(**changes),),
            organization_id=_ORG,
            class_id=_CLASS,
            purpose_code=_PURPOSE,
        )
        == "CONSENT_REQUIRED"
    )


def test_assistance_rejects_a_mixed_audience_with_one_ineligible_member() -> None:
    other_scope = EligibilityScope(_ORG, _CLASS, "synthetic-child-2", _PURPOSE)
    other = _member(
        participant_id="synthetic-child-2",
        eligibility_scope=other_scope,
        eligibility_basis="REAL",
    )

    assert (
        audience_refusal(
            (_CHILD, "synthetic-child-2"),
            (_member(), other),
            organization_id=_ORG,
            class_id=_CLASS,
            purpose_code=_PURPOSE,
        )
        == "CONSENT_REQUIRED"
    )


def test_assistance_legacy_legal_path_keeps_existing_behavior() -> None:
    legal = MemberFact(
        participant_id=_CHILD,
        completed_age_months=60,
        age_provenance_ref="age-source",
        age_revision=1,
        consent_record_ref="consent-source",
        consent_revision=1,
        consent_effective=True,
        purpose_granted=True,
    )

    assert audience_refusal((_CHILD,), (legal,)) is None
    assert audience_refusal((_CHILD,), (replace(legal, consent_effective=False),)) == (
        "CONSENT_REQUIRED"
    )


def test_assistance_accepts_versioned_legal_basis() -> None:
    legal = MemberFact(
        participant_id=_CHILD,
        completed_age_months=60,
        age_provenance_ref="age-source",
        age_revision=1,
        consent_record_ref="consent-source",
        consent_revision=1,
        consent_effective=True,
        purpose_granted=True,
        eligibility_basis="LEGAL_CONSENT",
        basis_version=BASIS_VERSION,
    )

    assert (
        audience_refusal(
            (_CHILD,),
            (legal,),
            organization_id=_ORG,
            class_id=_CLASS,
            purpose_code=_PURPOSE,
        )
        is None
    )


def test_assistance_canonical_facts_bind_synthetic_basis_and_scope() -> None:
    base = _member()
    assert base.canonical()["eligibility_basis"] == "SYNTHETIC_DEV"
    assert base.canonical()["eligibility_scope"] == {
        "organization_id": _ORG,
        "class_id": _CLASS,
        "child_id": _CHILD,
        "purpose_ref": _PURPOSE,
    }


def test_vision_accepts_single_child_synthetic_scope_and_legacy_legal_path() -> None:
    scope = _analysis_scope()
    assert eligibility_code(_context(scope), scope) is None
    assert eligibility_code(_context(scope, context_digest=None), scope) == "STALE_CONTEXT"
    legal = ContextDecision(
        context_revision=1,
        consent_effective=True,
        purpose_granted=True,
        session_active=True,
        audience_age_months=((_CHILD, 60),),
    )
    assert eligibility_code(legal, scope) is None
    assert legal.context_digest is None


def test_vision_accepts_versioned_legal_basis() -> None:
    scope = _analysis_scope()
    legal = ContextDecision(
        context_revision=1,
        consent_effective=True,
        purpose_granted=True,
        session_active=True,
        audience_age_months=((_CHILD, 60),),
        eligibility_basis="LEGAL_CONSENT",
        basis_version=BASIS_VERSION,
    )

    assert eligibility_code(legal, scope) is None


def test_vision_legal_disclosure_preserves_consent_only_gate() -> None:
    scope = _analysis_scope()
    legal = ContextDecision(
        context_revision=1,
        consent_effective=True,
        purpose_granted=False,
        session_active=True,
        audience_age_months=((_CHILD, 60),),
        eligibility_basis="LEGAL_CONSENT",
        basis_version=BASIS_VERSION,
    )

    assert _context_eligibility_ready(legal, scope, require_purpose=False)
    assert not _context_eligibility_ready(legal, scope, require_purpose=True)


@pytest.mark.parametrize(
    "changes",
    (
        {"eligibility_basis": "REAL"},
        {"eligibility_basis": "PENDING"},
        {"eligibility_basis": "REVOKED"},
        {"eligibility_basis": "LEGACY_UNCLASSIFIED"},
        {"eligibility_basis": "SYNTHETIC_DEV", "basis_version": "unknown"},
        {"eligibility_basis": "SYNTHETIC_DEV", "evidence_ref": ""},
        {"eligibility_basis": "SYNTHETIC_DEV", "eligibility_scope": None},
        {"eligibility_basis": "SYNTHETIC_DEV", "consent_effective": True},
        {"eligibility_basis": "SYNTHETIC_DEV", "purpose_granted": True},
        {
            "eligibility_basis": "SYNTHETIC_DEV",
            "eligibility_scope": EligibilityScope(_ORG, _CLASS, _CHILD, "foreign-purpose"),
        },
        {"eligibility_basis": "LEGAL_CONSENT", "basis_version": "unknown"},
    ),
)
def test_vision_rejects_unknown_or_mismatched_basis(
    changes: dict[str, object],
) -> None:
    scope = _analysis_scope()
    assert eligibility_code(_context(scope, **changes), scope) == "CONSENT_REQUIRED"


def test_vision_rejects_synthetic_basis_for_mixed_audience() -> None:
    scope = _analysis_scope((_CHILD, "synthetic-child-2"))
    assert eligibility_code(_context(scope), scope) == "CONSENT_REQUIRED"
