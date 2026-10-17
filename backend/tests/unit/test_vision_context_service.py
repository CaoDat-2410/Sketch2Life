"""BE2-02 C2 typed-context application flow over the synthetic fixture world (C2-A02/A03/
A06/A08/A09/A10/A13). No provider, network, model, database or queue is involved."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from sketch2life.application.ports.vision_analysis import AnalysisRevisionConflict
from sketch2life.application.services.vision_analysis import (
    CorrectionCommand,
    MeaningState,
    ObservationDisposition,
    VisionAnalysisError,
    child_correction_view,
)
from sketch2life.contracts.schemas.analysis_results import AnalysisCorrectionChildReceiptV1
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.vision_analysis import (
    AcceptedStatus,
    AnalysisHead,
    ProviderContextMode,
    provider_result_ref,
)
from sketch2life.domain.vision_context import (
    C2_CONTEXT_CAPABILITY,
    FIXTURE_AGE_BAND_POLICY,
    ContextRuleViolation,
    VisionContextSnapshot,
)
from sketch2life.infrastructure.vision_analysis.fakes import (
    FakeVisionObservationProvider,
    synthetic_success,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    TEACHER,
    AnalysisHarness,
    build_analysis_harness,
)


def _typed() -> AnalysisHarness:
    return build_analysis_harness(required_context_mode=ProviderContextMode.TYPED_CONTEXT)


def _group(h: AnalysisHarness) -> AnalysisHarness:
    h.pin = replace(h.pin, scope=replace(h.pin.scope, group_id="group_fx_1",
                                         audience_participant_ids=(CHILD_A, CHILD_B)))
    h.requests.add(h.pin)
    h.set_job()
    return h


def _provider(h: AnalysisHarness) -> FakeVisionObservationProvider:
    assert isinstance(h.provider, FakeVisionObservationProvider)
    return h.provider


def _stored(h: AnalysisHarness) -> tuple[int, int, int, int]:
    state = h.store.snapshot()
    return (len(state.heads), len(state.observations), len(state.provider_results),
            len(state.corrections))


def _head(h: AnalysisHarness, analysis_id: str) -> AnalysisHead:
    with h.store.transaction() as tx:
        head = tx.get_head(analysis_id)
    assert head is not None
    return head


# ------------------------------------------------------- happy path + pinned binding
def test_c2_typed_observation_pins_binding_on_head_evidence_and_record() -> None:
    h = _typed()
    analysis_id = h.accepted_analysis()
    (request,) = _provider(h).requests
    assert request.typed_context is not None
    head = _head(h, analysis_id)
    with h.store.transaction() as tx:
        observation = tx.get_observation(analysis_id)
    assert observation is not None
    assert head.typed_binding == request.typed_context.binding
    assert observation.evidence.context_binding == head.typed_binding
    record = h.service.analysis_record(TEACHER, analysis_id)
    assert record["contract_version"] == "0.2-candidate"
    assert record["context_binding"] == head.typed_binding.canonical()


# ------------------------------------------------- C2-A02 scope/port refusals pre-call
@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda s: replace(s, organization_id="org_fx_school_b"), "CONTEXT_SCOPE_MISMATCH"),
        (lambda s: replace(s, canvas_id="canvas_fx_002"), "CONTEXT_SCOPE_MISMATCH"),
        (lambda s: replace(s, purpose_code="other_purpose"), "CONTEXT_SCOPE_MISMATCH"),
        (lambda s: replace(s, assistance_id="assistance_fx_002"), "CONTEXT_REQUEST_MISMATCH"),
        (lambda s: replace(s, snapshot_ref="snapshot_fx_002"), "CONTEXT_REQUEST_MISMATCH"),
        (lambda s: replace(s, render_sha256="f" * 64), "CONTEXT_SOURCE_MISMATCH"),
        (lambda s: replace(s, members=(*s.members, s.members[0])),
         "CONTEXT_AUDIENCE_DUPLICATE"),
        (lambda s: replace(s, members=s.members[:1],
                           audience_participant_ids=s.audience_participant_ids[:1]),
         "CONTEXT_AUDIENCE_MISMATCH"),
        (lambda s: replace(s, context_revision=4), "CONTEXT_REVISION_MISMATCH"),
    ],
)
def test_c2_a02_untrusted_or_incoherent_context_refuses_before_invocation(
    mutation: object, code: str
) -> None:
    h = _group(_typed())
    h.context_sources.mutate = mutation  # type: ignore[assignment]
    result = h.observe()
    assert result.disposition is ObservationDisposition.REFUSED and result.code == code
    assert _provider(h).requests == [] and _stored(h) == (0, 0, 0, 0)


def test_c2_a02_conflicting_old_and_new_ports_refuse_before_invocation() -> None:
    h = _group(_typed())
    h.context_sources.age_overrides[CHILD_B] = 121  # same band, different exact age
    assert h.observe().code == "CONTEXT_PORT_DISAGREEMENT"
    h.context_sources.age_overrides.clear()
    h.context_sources.revision_override = 4
    assert h.observe().code in {"CONTEXT_REVISION_MISMATCH", "CONTEXT_PORT_DISAGREEMENT"}
    assert _provider(h).requests == []


def test_c2_a02_unavailable_or_malformed_owner_context_refuses() -> None:
    h = _typed()
    h.context_sources.unavailable = True
    assert h.observe().code == "CONTEXT_UNAVAILABLE"

    def malformed(_: VisionContextSnapshot) -> VisionContextSnapshot:
        raise ContextRuleViolation("bool age")

    h.context_sources.unavailable = False
    h.context_sources.mutate = malformed
    assert h.observe().code == "CONTEXT_MALFORMED"
    assert _provider(h).requests == []


def test_c2_a02_old_port_duplicate_age_facts_are_refused_in_c1_gate_too() -> None:
    # A duplicate (participant, age) pair is refused before dict conversion instead of
    # letting the last duplicate win (C2 hardening of the shared eligibility gate).
    for mode in (ProviderContextMode.IMAGE_ONLY, ProviderContextMode.TYPED_CONTEXT):
        h = build_analysis_harness(required_context_mode=mode)
        current = h.context.current

        def duplicated(scope, _current=current):  # type: ignore[no-untyped-def]
            decision = _current(scope)
            return replace(decision, audience_age_months=(
                (CHILD_A, 200), *decision.audience_age_months))

        h.context.current = duplicated  # type: ignore[method-assign]
        result = h.observe()
        assert result.code == "AGE_NOT_SUPPORTED"
        assert _provider(h).requests == []


# ---------------------------------------------------- C2-A03 every member individually
@pytest.mark.parametrize(
    ("setup", "code"),
    [
        (lambda h: h.context.set_participant(CHILD_B, age_months=156,
                                             purposes=frozenset({h.pin.scope.purpose_code})),
         "AGE_NOT_SUPPORTED"),
        (lambda h: h.context.set_participant(CHILD_B, age_months=None,
                                             purposes=frozenset({h.pin.scope.purpose_code})),
         "AGE_NOT_SUPPORTED"),
        (lambda h: h.context_sources.revoke_transfer(CHILD_B), "TRANSFER_NOT_PERMITTED"),
        (lambda h: h.context_sources.fields.__setitem__(
            CHILD_B, frozenset({"audience_age_bands", "request_enums"})),
         "CONTEXT_FIELD_NOT_PERMITTED"),
    ],
)
def test_c2_a03_one_ineligible_member_refuses_the_call(setup: object, code: str) -> None:
    h = _group(_typed())
    setup(h)  # type: ignore[operator]
    result = h.observe()
    assert result.disposition is ObservationDisposition.REFUSED and result.code == code
    assert _provider(h).requests == []


def test_c2_a03_group_projection_keeps_one_band_per_member() -> None:
    h = _group(_typed())
    assert h.observe().authoritative
    (request,) = _provider(h).requests
    assert request.typed_context is not None
    assert request.typed_context.projection.audience_age_bands == (
        "completed-years-10", "completed-years-5")


# ----------------------------------------------------- C2-A06 capability fails closed
def test_c2_a06_capability_mismatch_or_missing_dependencies_refuse_without_call() -> None:
    for capability in (None, replace(C2_CONTEXT_CAPABILITY, contract_version="0.2-candidate"),
                       replace(C2_CONTEXT_CAPABILITY, fields=("teacher_topic",)),
                       replace(C2_CONTEXT_CAPABILITY, transport_kind="http")):
        h = _typed()
        _provider(h).capability = capability
        result = h.observe()
        assert result.code == "CONTEXT_MODE_UNSUPPORTED" and _provider(h).requests == []
        assert h.context_sources.calls == 0  # refused before even reading context
    h = _typed()
    h.service._d = replace(h.service._d, age_band_policy=None)
    assert h.observe().code == "CONTEXT_UNAVAILABLE" and _provider(h).requests == []


# ------------------------------------------ C2-A08 in-flight drift: stale vs rejection
def _in_flight(h: AnalysisHarness, change: object) -> None:
    _provider(h).on_observe = change  # type: ignore[assignment]


def test_c2_a08_same_revision_same_band_exact_age_drift_is_stale() -> None:
    h = _typed()
    _in_flight(h, lambda: h.context.ages.__setitem__(CHILD_A, 61))  # still completed-years-5
    result = h.observe()
    assert result.disposition is ObservationDisposition.STALE
    assert result.code == "context_changed"
    head = _head(h, result.analysis_id or "")
    assert head.accepted_status is AcceptedStatus.STALE
    # The original binding is recorded, never rebound to the moved facts.
    (request,) = _provider(h).requests
    assert request.typed_context is not None
    assert head.typed_binding == request.typed_context.binding


@pytest.mark.parametrize(
    "change",
    [
        lambda h: h.context.bump(h.pin.scope.session_id, h.pin.scope.canvas_id),
        lambda h: setattr(h.context_sources, "field_policy_revision", 2),
        lambda h: h.context_sources.permission_revisions.__setitem__(CHILD_A, 2),
        lambda h: setattr(h.context_sources, "topic", None),
    ],
)
def test_c2_a08_revision_or_digest_movement_stores_stale(change: object) -> None:
    h = _typed()
    _in_flight(h, lambda: change(h))  # type: ignore[operator]
    result = h.observe()
    assert result.disposition is ObservationDisposition.STALE
    assert _stored(h)[:3] == (1, 1, 1)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (lambda h: h.context_sources.revoke_transfer(CHILD_A), "TRANSFER_NOT_PERMITTED"),
        (lambda h: h.context_sources.fields.__setitem__(CHILD_A, frozenset()),
         "CONTEXT_FIELD_NOT_PERMITTED"),
        (lambda h: h.context.revoke_consent(CHILD_A), "CONSENT_REQUIRED"),
        (lambda h: h.context.end_session(h.pin.scope.session_id), "INVALID_STATE"),
        (lambda h: h.context.ages.__setitem__(CHILD_A, 156), "AGE_NOT_SUPPORTED"),
        (lambda h: setattr(h.context_sources, "unavailable", True), "CONTEXT_UNAVAILABLE"),
        (lambda h: h.context_sources.age_overrides.__setitem__(CHILD_A, 61),
         "CONTEXT_PORT_DISAGREEMENT"),
    ],
)
def test_c2_a08_revocation_or_ineligibility_after_the_call_discards_everything(
    change: object, code: str
) -> None:
    h = _typed()
    _in_flight(h, lambda: change(h))  # type: ignore[operator]
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED and result.code == code
    assert result.provider_invoked and _stored(h) == (0, 0, 0, 0)


def test_c2_a08_source_and_lineage_movement_keep_c1_behaviour() -> None:
    h = _typed()

    def move_source() -> None:
        h.sources.add(replace(h.snapshot, checkpoint=replace(
            h.snapshot.checkpoint, checkpoint_revision=5)))

    _in_flight(h, move_source)
    assert h.observe().code == "source_changed"
    h2 = _typed()
    _in_flight(h2, lambda: h2.set_job(state=JobState.CANCELLED))
    result = h2.observe()
    assert result.disposition is ObservationDisposition.REJECTED
    assert result.code == "JOB_CANCELLED" and _stored(h2) == (0, 0, 0, 0)


def test_c2_a07_a10_provider_must_echo_the_pinned_binding() -> None:
    h = _typed()

    def other_binding() -> None:
        (request,) = _provider(h).requests
        assert request.typed_context is not None
        moved = replace(request.typed_context, binding=replace(
            request.typed_context.binding, context_digest="c" * 64))
        _provider(h).scripted = [synthetic_success(replace(request, typed_context=moved),
                                                   executed_at=h.clock.now())]

    _in_flight(h, other_binding)
    result = h.observe()
    assert result.code == "OUTPUT_MALFORMED" and _stored(h) == (0, 0, 0, 0)


# ------------------------------------------ C2-A09 post-acceptance drift and receipts
def _accepted_with_receipts(
    h: AnalysisHarness,
) -> tuple[str, CorrectionCommand, CorrectionCommand]:
    analysis_id = h.accepted_analysis()
    proposal_cmd = h.correction(DEVICE_A, analysis_id, explanation="It has stripes")
    proposal = h.service.submit_correction(proposal_cmd)
    confirm_cmd = h.correction(TEACHER, analysis_id, revision=2,
                               basis=proposal.correction.correction_id)
    h.service.submit_correction(confirm_cmd)
    assert h.service.downstream_meaning(TEACHER, analysis_id).state is MeaningState.CONFIRMED
    return analysis_id, proposal_cmd, confirm_cmd


def test_c2_a09_same_revision_digest_drift_blocks_current_authority_not_history() -> None:
    h = _typed()
    analysis_id, proposal_cmd, confirm_cmd = _accepted_with_receipts(h)
    h.context.ages[CHILD_A] = 61  # same band, same revision: only the digest moves
    replay = h.observe()
    assert replay.replayed and replay.disposition is ObservationDisposition.STALE
    assert replay.code == "context_changed" and len(_provider(h).requests) == 1
    meaning = h.service.downstream_meaning(TEACHER, analysis_id)
    assert meaning.state is MeaningState.NOT_APPLICABLE and meaning.confirmed_concepts == ()
    with pytest.raises(VisionAnalysisError) as exc:
        h.service.submit_correction(h.correction(TEACHER, analysis_id, revision=3))
    assert exc.value.code == "STALE_CONTEXT"
    # Accepted receipts replay unchanged as history after the current disclosure check...
    assert h.service.submit_correction(proposal_cmd).replayed
    again = h.service.submit_correction(confirm_cmd)
    assert again.replayed and again.receipt.analysis_revision_after == 3
    # ...and replay does not revive the old meaning.
    assert h.service.downstream_meaning(TEACHER, analysis_id).state is (
        MeaningState.NOT_APPLICABLE)


def test_c2_a09_transfer_revocation_after_acceptance_rejects_current_authority() -> None:
    h = _typed()
    analysis_id, proposal_cmd, _ = _accepted_with_receipts(h)
    h.context_sources.revoke_transfer(CHILD_A)
    replay = h.observe()
    assert replay.disposition is ObservationDisposition.REJECTED
    assert replay.code == "TRANSFER_NOT_PERMITTED" and len(_provider(h).requests) == 1
    assert h.service.downstream_meaning(TEACHER, analysis_id).state is (
        MeaningState.NOT_APPLICABLE)
    # Transfer permission is not disclosure: the Child's own receipt still replays.
    assert h.service.submit_correction(proposal_cmd).replayed


def test_c2_a09_revoked_disclosure_blocks_receipt_replay() -> None:
    h = _typed()
    _, proposal_cmd, _ = _accepted_with_receipts(h)
    h.context.revoke_consent(CHILD_A)
    with pytest.raises(VisionAnalysisError) as exc:
        h.service.submit_correction(proposal_cmd)
    assert exc.value.code == "CONSENT_REQUIRED"
    assert h.observe().disposition is ObservationDisposition.REJECTED


def test_c2_a10_child_projection_stays_0_1_refs_only_for_typed_analyses() -> None:
    h = _typed()
    analysis_id = h.accepted_analysis()
    proposal = h.service.submit_correction(
        h.correction(DEVICE_A, analysis_id, explanation="It has stripes"))
    child = child_correction_view(proposal)
    AnalysisCorrectionChildReceiptV1.model_validate_json(json.dumps(child))
    text = json.dumps(child)
    for leaked in ("completed-years", "digest", "topic", "Animals", "age", "binding"):
        assert leaked not in text
    # The whole retained provider result stays Teacher/internal and hash-bound.
    record = h.service.resolve_provider_result(TEACHER, provider_result_ref(analysis_id))
    with h.store.transaction() as tx:
        observation = tx.get_observation(analysis_id)
    assert observation is not None
    assert record.result_sha256 == observation.evidence.result_sha256
    with pytest.raises(VisionAnalysisError):
        h.service.resolve_provider_result(DEVICE_A, provider_result_ref(analysis_id))


# ------------------------------------------------------ C2-A13 atomicity and replay
def test_c2_a13_failed_commit_leaves_no_partial_binding_or_record() -> None:
    h = _typed()
    h.store.fail_next_commit = True
    with pytest.raises(VisionAnalysisError) as exc:
        h.observe()
    assert exc.value.code == "DEPENDENCY_UNAVAILABLE" and _stored(h) == (0, 0, 0, 0)


def test_c2_a13_binding_is_immutable_under_cas() -> None:
    h = _typed()
    analysis_id = h.accepted_analysis()
    head = _head(h, analysis_id)
    assert head.typed_binding is not None
    moved = replace(head, analysis_revision=2,
                    typed_binding=replace(head.typed_binding, context_digest="d" * 64))
    with (
        pytest.raises(AnalysisRevisionConflict, match="immutable"),
        h.store.transaction() as tx,
    ):
        tx.cas_head(expected_revision=1, head=moved)
    assert _head(h, analysis_id).typed_binding == head.typed_binding


def test_c2_a13_sequential_replay_makes_zero_new_calls() -> None:
    h = _typed()
    first = h.observe()
    second = h.observe()
    assert first.authoritative and second.replayed and second.authoritative
    assert second.analysis_id == first.analysis_id and not second.provider_invoked
    assert len(_provider(h).requests) == 1 and h.context_sources.calls >= 2


def test_c2_a13_concurrent_first_submissions_keep_one_atomic_winner() -> None:
    h = _typed()
    inner: list[object] = []
    _in_flight(h, lambda: inner.append(h.observe()))
    outer = h.observe()
    (winner,) = inner
    assert winner.authoritative and not winner.replayed  # type: ignore[attr-defined]
    # Each submission called the provider at most once; the loser's result is discarded.
    assert len(_provider(h).requests) == 2
    assert outer.replayed and outer.provider_invoked
    assert outer.analysis_id == winner.analysis_id  # type: ignore[attr-defined]
    assert _stored(h)[:3] == (1, 1, 1)


def test_c2_policy_is_fixture_only() -> None:
    assert FIXTURE_AGE_BAND_POLICY.status == "FIXTURE_ONLY_NOT_PEDAGOGICALLY_ADOPTED"
