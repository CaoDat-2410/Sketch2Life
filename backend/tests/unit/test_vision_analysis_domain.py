"""BE2-02 C1 pure domain rules (V02/V03/V04/V07/V10/V11/V15 component level)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.vision_analysis import (
    AcceptedStatus,
    ActorRef,
    ActorRole,
    AdmissionReceipt,
    AnalysisHead,
    AnalysisLineage,
    AnalysisRuleViolation,
    AssistancePin,
    CorrectionKind,
    EntityObservation,
    EvidenceKind,
    InvalidationReason,
    JobLineageView,
    LexicalOutcome,
    LineageVerdict,
    MeaningCorrection,
    MeaningStatus,
    ModerationOutcome,
    ObservationClaim,
    ObservationEvidence,
    ObservedLabel,
    OriginalObservation,
    ProviderContextMode,
    SourceSnapshot,
    SourceVerdict,
    VisionObservation,
    analysis_etag,
    apply_correction,
    check_input_hash,
    check_lineage,
    derive_uncertainty,
    mark_stale,
    new_head,
    new_observation,
    normalize_intended_objects,
    normalize_long_text,
    normalize_short_text,
    object_candidates,
    parse_analysis_etag,
    require_confidence,
    verify_source,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    ASSISTANCE,
    ATTEMPT,
    CANVAS,
    CHECKPOINT_CHECKSUM,
    JOB,
    ORG,
    SCOPE,
    SNAPSHOT,
    synthetic_admission,
    synthetic_snapshot,
)

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
CHILD = ActorRef("device_fx_a", ActorRole.CHILD_DEVICE, "participant_fx_a", "turn_fx_01")
TEACHER = ActorRef("teacher_fx_001", ActorRole.TEACHER)


def _observation(confidence: float | None = 0.62) -> OriginalObservation:
    return OriginalObservation(
        entities=(EntityObservation("ent-1", ObservedLabel("cat", "DECLARED", ("en",)),
                                    confidence),),
        actions=(), relations=(), themes=(), ambiguous_regions=(),
    )


def _evidence() -> ObservationEvidence:
    return ObservationEvidence(EvidenceKind.SYNTHETIC_FAKE, ProviderContextMode.IMAGE_ONLY,
                               "fake", "Synthetic/0.1", "a" * 64, NOW, 0)


def _head(
    stale: InvalidationReason | None = None,
) -> tuple[VisionObservation, AnalysisHead]:
    snapshot = synthetic_snapshot()
    observation = new_observation(
        analysis_id="ana_1", organization_id=ORG, observation=_observation(),
        evidence=_evidence(),
        moderation=ModerationOutcome(LexicalOutcome.NOT_EXECUTED, None, None), now=NOW,
    )
    return observation, new_head(
        analysis_id="ana_1", scope=SCOPE,
        lineage=AnalysisLineage(ASSISTANCE, 1, JOB, ATTEMPT, snapshot.input_hash()),
        source=snapshot, admission=synthetic_admission(snapshot), context_revision=3,
        observation_sha256=observation.observation_sha256, stale_reason=stale, now=NOW,
    )


def _correction(kind: CorrectionKind, version: int, **changes: object) -> MeaningCorrection:
    base = MeaningCorrection(
        correction_id=f"cor_{version}", analysis_id="ana_1", correction_version=version,
        kind=kind, author=CHILD if kind is CorrectionKind.CHILD_PROPOSAL else TEACHER,
        intended_objects=("tiger",), child_explanation=None,
        correction_reason="Child says it is a tiger", expected_context_revision=3,
        basis_correction_ref=None, recorded_at=NOW,
    )
    return replace(base, **changes)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [True, False, "0.5", float("nan"), float("inf"), -0.01, 1.01])
def test_v01_confidence_rejects_bool_string_nonfinite_and_out_of_range(value: object) -> None:
    with pytest.raises(AnalysisRuleViolation):
        require_confidence(value)


def test_v01_null_confidence_is_preserved_never_zero() -> None:
    assert require_confidence(None) is None
    assert require_confidence(0) == 0.0
    entity = EntityObservation("ent-1", ObservedLabel("cat", "DECLARED", ("en",)), None)
    assert entity.confidence is None


def test_v01_text_bounds_follow_short_and_long_text_rules() -> None:
    assert normalize_short_text("  tiger ") == "tiger"
    assert normalize_long_text("line one\nline two") == "line one\nline two"
    for bad in ("", "   ", "x" * 129, "ti\x00ger", "a\nb", 3):
        with pytest.raises(AnalysisRuleViolation):
            normalize_short_text(bad)
    with pytest.raises(AnalysisRuleViolation):
        normalize_long_text("x" * 4001)
    with pytest.raises(AnalysisRuleViolation):
        normalize_intended_objects(["Tiger", "tiger"])
    with pytest.raises(AnalysisRuleViolation):
        normalize_intended_objects([])
    with pytest.raises(AnalysisRuleViolation):
        normalize_intended_objects([f"o{i}" for i in range(17)])


def test_v02_checkpoint_render_and_admission_are_independent_bindings() -> None:
    snapshot = synthetic_snapshot()
    receipt = synthetic_admission(snapshot)

    def verdict(snap: SourceSnapshot | None, admission: AdmissionReceipt | None,
                canvas: str = CANVAS) -> SourceVerdict:
        return verify_source(snap, admission, organization_id=ORG, canvas_id=canvas)

    assert verdict(snapshot, receipt) is SourceVerdict.PROCEED
    assert verdict(None, receipt) is SourceVerdict.SOURCE_NOT_FOUND
    assert verdict(snapshot, receipt, "canvas_fx_other") is SourceVerdict.CHECKPOINT_CANVAS_MISMATCH
    rebased = replace(snapshot, render=replace(snapshot.render,
                                               source_checkpoint_checksum="b" * 64))
    assert verdict(rebased, receipt) is SourceVerdict.RENDER_NOT_DERIVED_FROM_CHECKPOINT
    # The JSON checkpoint checksum passed off as the image hash is caught, not trusted.
    confused = synthetic_snapshot(render_sha256=CHECKPOINT_CHECKSUM)
    assert verdict(confused, synthetic_admission(confused)) is SourceVerdict.CHECKSUM_CONFUSED
    gif = replace(snapshot, render=replace(snapshot.render, media_type="image/gif"))
    assert verdict(gif, receipt) is SourceVerdict.MEDIA_TYPE_UNSUPPORTED
    assert verdict(snapshot, None) is SourceVerdict.ADMISSION_MISSING
    other_render = replace(receipt, render_sha256="c" * 64)
    assert verdict(snapshot, other_render) is SourceVerdict.ADMISSION_NOT_BOUND
    recapture = synthetic_admission(snapshot, decision="RECAPTURE")
    assert verdict(snapshot, recapture) is SourceVerdict.ADMISSION_NOT_PASSED


def test_v03_candidates_and_uncertainty_keep_null_confidence_without_intent() -> None:
    observation = OriginalObservation(
        entities=(
            EntityObservation("ent-1", ObservedLabel("cat", "DECLARED", ("en",)), 0.12),
            EntityObservation("ent-2", ObservedLabel("house", "DECLARED", ("en",)), None),
        ),
        actions=(), relations=(), themes=(), ambiguous_regions=(),
    )
    candidates = object_candidates(observation)
    assert [(c.label, c.confidence) for c in candidates] == [("cat", 0.12), ("house", None)]
    uncertainty = derive_uncertainty(observation)
    assert uncertainty.unknown_confidence_refs == ("ent-2",)
    assert uncertainty.calibration == "uncalibrated"
    assert uncertainty.requires_meaning_confirmation is True


def test_v04_child_proposal_never_moves_meaning_teacher_confirmation_does() -> None:
    observation, head = _head()
    proposal = _correction(CorrectionKind.CHILD_PROPOSAL, 2,
                           child_explanation="It has stripes")
    after_child = apply_correction(head, proposal, NOW)
    assert proposal.meaning_status is MeaningStatus.PROPOSED
    assert after_child.current_meaning_ref is None
    confirmation = _correction(CorrectionKind.TEACHER_CONFIRMATION, 3,
                               basis_correction_ref=proposal.correction_id)
    after_teacher = apply_correction(after_child, confirmation, NOW)
    assert confirmation.meaning_status is MeaningStatus.CONFIRMED
    assert after_teacher.current_meaning_ref == confirmation.correction_id
    assert after_teacher.correction_refs == (proposal.correction_id, confirmation.correction_id)
    # The original observation hash is untouched by every correction.
    assert after_teacher.observation_sha256 == observation.observation_sha256
    assert object_candidates(observation.observation)[0].label == "cat"


def test_v04_v05_author_role_rules_are_enforced_by_the_record() -> None:
    with pytest.raises(AnalysisRuleViolation):
        _correction(CorrectionKind.CHILD_PROPOSAL, 2, author=TEACHER)
    with pytest.raises(AnalysisRuleViolation):
        _correction(CorrectionKind.TEACHER_CONFIRMATION, 2, author=CHILD)
    with pytest.raises(AnalysisRuleViolation):
        _correction(CorrectionKind.TEACHER_CONFIRMATION, 2, child_explanation="words")
    with pytest.raises(AnalysisRuleViolation):
        _correction(CorrectionKind.CHILD_PROPOSAL, 2, basis_correction_ref="cor_x")
    with pytest.raises(AnalysisRuleViolation):
        ActorRef("device_fx_a", ActorRole.CHILD_DEVICE)
    with pytest.raises(AnalysisRuleViolation):
        ActorRef("teacher_fx_001", ActorRole.TEACHER, participant_id="participant_fx_a")


def test_v06_v11_stale_analysis_keeps_history_and_refuses_new_corrections() -> None:
    _, head = _head()
    confirmed = apply_correction(head, _correction(CorrectionKind.TEACHER_CONFIRMATION, 2), NOW)
    stale = mark_stale(confirmed, InvalidationReason.CONTEXT_CHANGED, NOW)
    assert stale.accepted_status is AcceptedStatus.STALE
    assert stale.analysis_revision == 3
    assert stale.correction_refs == confirmed.correction_refs
    assert stale.current_meaning_ref == confirmed.current_meaning_ref
    with pytest.raises(AnalysisRuleViolation):
        apply_correction(stale, _correction(CorrectionKind.TEACHER_CONFIRMATION, 4), NOW)
    with pytest.raises(AnalysisRuleViolation):
        mark_stale(confirmed, InvalidationReason.TEACHER_MEANING_CONFIRMED, NOW)
    _, born_stale = _head(InvalidationReason.SOURCE_CHANGED)
    assert born_stale.accepted_status is AcceptedStatus.STALE


def test_v07_lineage_guards_are_ordered_and_input_hash_bound() -> None:
    snapshot = synthetic_snapshot()
    pin = AssistancePin(ASSISTANCE, 1, SNAPSHOT, 3, SCOPE)
    job = JobLineageView(JOB, ORG, "vision_analysis", JobState.RUNNING, ATTEMPT, ASSISTANCE, 1,
                         snapshot.input_hash(), 3, SCOPE.session_id,
                         SCOPE.audience_participant_ids, SCOPE.purpose_code, ASSISTANCE)
    claim = ObservationClaim(JOB, ATTEMPT, ASSISTANCE, 1, SNAPSHOT, 3)
    assert check_lineage(claim, pin, job) is LineageVerdict.PROCEED
    assert check_lineage(claim, None, job) is LineageVerdict.REQUEST_NOT_FOUND
    assert check_lineage(replace(claim, expected_request_revision=2), pin, job) is (
        LineageVerdict.REQUEST_MISMATCH)
    assert check_lineage(claim, pin, None) is LineageVerdict.JOB_NOT_FOUND
    assert check_lineage(claim, pin, replace(job, organization_id="org_x")) is (
        LineageVerdict.JOB_NOT_FOUND)
    assert check_lineage(claim, pin, replace(job, job_type="sketch_assistance")) is (
        LineageVerdict.JOB_TYPE_MISMATCH)
    for scope_change in ({"session_id": None}, {"subject_refs": ("participant_fx_z",)},
                         {"purpose_code": "other"}, {"target_id": "assistance_fx_9"}):
        assert check_lineage(claim, pin, replace(job, **scope_change)) is (
            LineageVerdict.JOB_SCOPE_MISMATCH)
    assert check_lineage(claim, pin, replace(job, state=JobState.CANCELLED)) is (
        LineageVerdict.JOB_CANCELLED)
    assert check_lineage(claim, pin, replace(job, state=JobState.SUCCEEDED)) is (
        LineageVerdict.JOB_TERMINAL)
    assert check_lineage(claim, pin, replace(job, active_attempt_id="att_2")) is (
        LineageVerdict.ATTEMPT_SUPERSEDED)
    assert check_lineage(claim, pin, replace(job, state=JobState.QUEUED)) is (
        LineageVerdict.INVALID_STATE)
    assert check_lineage(claim, pin, replace(job, request_revision=2)) is (
        LineageVerdict.REQUEST_MISMATCH)
    assert check_input_hash(job, snapshot) is LineageVerdict.PROCEED
    assert check_input_hash(replace(job, input_hash="d" * 64), snapshot) is (
        LineageVerdict.INPUT_MISMATCH)


def test_v09_etag_family_and_revision_parsing() -> None:
    assert analysis_etag("ana_1", 2) == '"analysis:ana_1:2"'
    assert parse_analysis_etag('"analysis:ana_1:2"', "ana_1") == 2
    for wrong in ('"session:ana_1:2"', '"analysis:ana_2:2"', '"analysis:ana_1:0"', "2", "",
                  'W/"analysis:ana_1:2"', "*", '"analysis:ana_1:2", "analysis:ana_1:3"'):
        assert parse_analysis_etag(wrong, "ana_1") is None


def test_v13_legacy_bridge_evidence_must_be_image_only_with_full_provenance() -> None:
    with pytest.raises(AnalysisRuleViolation):
        ObservationEvidence(EvidenceKind.OFFLINE_LEGACY_BRIDGE, ProviderContextMode.TYPED_CONTEXT,
                            "bridge", "V2", "a" * 64, NOW, 1)
    with pytest.raises(AnalysisRuleViolation):
        ObservationEvidence(EvidenceKind.OFFLINE_LEGACY_BRIDGE, ProviderContextMode.IMAGE_ONLY,
                            "bridge", "V2", "a" * 64, NOW, 1)
    with pytest.raises(AnalysisRuleViolation):
        ObservationEvidence(EvidenceKind.SYNTHETIC_FAKE, ProviderContextMode.IMAGE_ONLY,
                            "fake", "S", "a" * 64, NOW, 2)


def test_observation_record_detects_tampering() -> None:
    observation, _ = _head()
    with pytest.raises(AnalysisRuleViolation):
        replace(observation, observation=_observation(confidence=0.99))
