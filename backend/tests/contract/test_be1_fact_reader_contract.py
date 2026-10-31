from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from sketch2life.application.services.assistance import teacher_view
from sketch2life.application.services.vision_analysis import (
    _context_eligibility_ready,
    eligibility_code,
)
from sketch2life.contracts.schemas.assistance_requests import ConsentRevisionRefV1
from sketch2life.domain.assistance import MemberFact, _member_eligibility_ready
from sketch2life.domain.eligibility import (
    BASIS_VERSION,
    PROOF_VERSION,
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
from sketch2life.infrastructure.assistance.harness import build_assistance_harness


def test_reader_facts_pass_existing_image_only_be2_gates_without_legal_consent() -> None:
    now = datetime(2026, 10, 31, 12, tzinfo=UTC)
    scope = EligibilityScope("org-1", "class-1", "child-1", "purpose-1")
    proof = BE1SyntheticProofFact(
        evidence_id="proof-1",
        schema_version=PROOF_VERSION,
        data_origin="SYNTHETIC_DEV",
        scope=scope,
        run_ref="run-1",
        session_id="session-1",
        issued_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=5),
        revoked_at=None,
        revocation_revision=0,
    )
    snapshot = BE1FactSnapshot(
        organization_id="org-1",
        class_id="class-1",
        session_id="session-1",
        session_state="active",
        session_run_ref="run-1",
        environment="test",
        pilot_enabled=True,
        purpose_ref="purpose-1",
        child_id="child-1",
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
        group_id="group-1",
        proof=proof,
        evaluated_at=now,
    )
    reader = BE1FactReader(type("Source", (), {"current_facts": lambda self, request: snapshot})())
    request = BE1FactRequest(
        organization_id="org-1",
        class_id="class-1",
        session_id="session-1",
        child_id="child-1",
        purpose_ref="purpose-1",
        audience_participant_ids=("child-1",),
        context_mode=ProviderContextMode.IMAGE_ONLY,
    )
    result = reader.read(request)
    assert result.reason is FactReaderReason.ALLOWED
    assert result.member is not None and result.context is not None
    assert _member_eligibility_ready(result.member, expected_scope=scope)

    analysis_scope = AnalysisScope(
        organization_id="org-1",
        class_id="class-1",
        session_id="session-1",
        canvas_id="canvas-1",
        group_id="group-1",
        contributor_participant_id="child-1",
        audience_participant_ids=("child-1",),
        purpose_code="purpose-1",
    )
    assert _context_eligibility_ready(result.context, analysis_scope, require_purpose=True)
    assert eligibility_code(result.context, analysis_scope) is None
    assert result.member.consent_effective is False
    assert result.member.purpose_granted is False
    assert result.member.age_provenance_ref == "be1-profile-age-v2:SYNTHETIC_FIXTURE:1"
    assert result.context.context_digest is not None


def test_typed_context_request_is_denied_before_any_typed_context_projection() -> None:
    reader = BE1FactReader(type("Source", (), {"current_facts": lambda self, request: None})())
    request = BE1FactRequest(
        organization_id="org-1",
        class_id="class-1",
        session_id="session-1",
        child_id="child-1",
        purpose_ref="purpose-1",
        audience_participant_ids=("child-1",),
        context_mode=ProviderContextMode.TYPED_CONTEXT,
    )
    result = reader.read(request)
    assert result.reason is FactReaderReason.CONTEXT_MODE_UNSUPPORTED
    assert result.member is None and result.context is None


def test_teacher_projection_keeps_legal_pair_and_marks_synthetic_null_pair() -> None:
    harness = build_assistance_harness(auto_schedule=False)
    request = harness.submit().request
    legal_refs = teacher_view(request)["consent_revision_refs"]
    assert isinstance(legal_refs, list)
    ConsentRevisionRefV1.model_validate(legal_refs[0])

    synthetic = MemberFact(
        participant_id="p_a",
        completed_age_months=60,
        age_provenance_ref="age-p-a",
        age_revision=1,
        consent_record_ref=None,
        consent_revision=None,
        consent_effective=False,
        purpose_granted=False,
        eligibility_basis="SYNTHETIC_DEV",
        basis_version=BASIS_VERSION,
        evidence_ref="proof-p-a",
        eligibility_scope=EligibilityScope("org", "class", "p_a", "purpose"),
    )
    synthetic_request = replace(
        request,
        facts=replace(request.facts, audience=("p_a",), members=(synthetic,)),
    )
    synthetic_refs = teacher_view(synthetic_request)["consent_revision_refs"]
    assert isinstance(synthetic_refs, list)
    parsed = ConsentRevisionRefV1.model_validate(synthetic_refs[0])
    assert parsed.eligibility_basis == "SYNTHETIC_DEV"
    assert parsed.consent_record_ref is None and parsed.revision is None
