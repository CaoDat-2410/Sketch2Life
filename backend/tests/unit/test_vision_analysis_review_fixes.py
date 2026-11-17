"""Regressions for Codex C1 review findings C1-R01..R06 (BE2-02, offline component)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.vision_analysis import ObservationSucceeded
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.application.services.vision_analysis import (
    ObservationDisposition,
    VisionAnalysisError,
    teacher_correction_view,
    worker_candidate_view,
)
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisRecordV1,
    AnalysisWorkerCandidateV1,
)
from sketch2life.contracts.schemas.vision_v2 import VisionUnderstandingSuccessV2
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs.model import JobScope, RequestRef
from sketch2life.domain.vision_analysis import (
    VISION_ANALYSIS_JOB_TYPE,
    ActionObservation,
    AmbiguousRegionObservation,
    AnalysisRuleViolation,
    EntityObservation,
    ObservedLabel,
    OriginalObservation,
    RelationObservation,
    ThemeObservation,
    observation_bounds_violation,
)
from sketch2life.infrastructure.ai_jobs.fakes import InMemoryAiJobStore
from sketch2life.infrastructure.vision_analysis.fakes import (
    FakeVisionObservationProvider,
    synthetic_success,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    ASSISTANCE,
    CANVAS,
    CHILD_A,
    CHILD_B,
    CONTEXT_REVISION,
    DEVICE_A,
    ORG,
    OUTSIDER,
    PURPOSE,
    SESSION,
    TEACHER,
    AnalysisHarness,
    build_analysis_harness,
    synthetic_snapshot,
    synthetic_v2_response,
)
from sketch2life.infrastructure.vision_analysis.job_lineage import AiJobRepositoryLineage
from sketch2life.infrastructure.vision_analysis.legacy_v2 import LegacyVisionV2Bridge
from sketch2life.interfaces.http.analysis_corrections_fixture_app import (
    create_analysis_corrections_fixture_app,
)

NOW = datetime(2026, 10, 16, 11, 59, tzinfo=UTC)


class ScriptedTransport:
    def __init__(self, response: Mapping[str, object]) -> None:
        self.response = response
        self.calls = 0

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls += 1
        return self.response


def _bridge(response: Mapping[str, object]) -> tuple[AnalysisHarness, ScriptedTransport]:
    transport = ScriptedTransport(response)
    h = build_analysis_harness(
        provider_factory=lambda sources, clock: LegacyVisionV2Bridge(
            transport=transport, render_loader=sources.read_render, clock=clock.now
        )
    )
    return h, transport


def _fake(h: AnalysisHarness) -> FakeVisionObservationProvider:
    assert isinstance(h.provider, FakeVisionObservationProvider)
    return h.provider


def _counts(h: AnalysisHarness) -> tuple[int, int]:
    state = h.store.snapshot()
    return len(state.heads), len(state.observations)


def _results(h: AnalysisHarness) -> int:
    return len(h.store.snapshot().provider_results)


def _text(value: str) -> dict[str, object]:
    return {"value": value, "language": {"status": "DECLARED", "tags": ["en"]}}


# ------------------------------------------------------------------ C1-R01
@pytest.mark.parametrize(
    ("change", "disposition", "code"),
    [
        ("context", ObservationDisposition.STALE, "context_changed"),
        ("source", ObservationDisposition.STALE, "source_changed"),
        ("consent", ObservationDisposition.REJECTED, "CONSENT_REQUIRED"),
        ("session", ObservationDisposition.REJECTED, "INVALID_STATE"),
        ("age", ObservationDisposition.REJECTED, "AGE_NOT_SUPPORTED"),
    ],
)
def test_r01_early_replay_rechecks_current_applicability(
    change: str, disposition: ObservationDisposition, code: str
) -> None:
    h = build_analysis_harness()
    original = h.observe()
    assert original.authoritative
    with h.store.transaction() as tx:
        before = tx.get_head(original.analysis_id or "")
    if change == "context":
        h.context.bump(SESSION, CANVAS)
    elif change == "source":
        h.sources.add(synthetic_snapshot(render_sha256="9" * 64))
    elif change == "consent":
        h.context.revoke_consent(CHILD_A)
    elif change == "session":
        h.context.end_session(SESSION)
    else:
        h.context.set_participant(CHILD_A, age_months=156, purposes=frozenset({PURPOSE}))
    replay = h.observe()
    assert replay.replayed and not replay.authoritative
    assert replay.disposition is disposition and replay.code == code
    assert len(_fake(h).requests) == 1
    with h.store.transaction() as tx:
        after = tx.get_head(original.analysis_id or "")
    assert after == before and _counts(h) == (1, 1) and _results(h) == 1


def test_r01_unchanged_replay_stays_authoritative() -> None:
    h = build_analysis_harness()
    first = h.observe()
    again = h.observe()
    assert again.replayed and again.authoritative and again.analysis_id == first.analysis_id


def test_r01_raced_winner_replay_rechecks_applicability() -> None:
    h = build_analysis_harness()

    def competing_writer_then_context_moves() -> None:
        h.service.record_observation(h.claim(), correlation_id="corr_fx_race")
        h.context.bump(SESSION, CANVAS)

    _fake(h).on_observe = competing_writer_then_context_moves
    result = h.observe()
    assert result.replayed and not result.authoritative
    assert result.disposition is ObservationDisposition.STALE
    assert _counts(h) == (1, 1)


def test_r01_accepted_correction_receipt_replay_keeps_original_semantics() -> None:
    h = build_analysis_harness()
    analysis_id = h.accepted_analysis()
    command = h.correction(TEACHER, analysis_id, key="key_fx_r01")
    original = h.service.submit_correction(command)
    h.context.bump(SESSION, CANVAS)
    replay = h.service.submit_correction(command)  # old If-Match, context moved
    assert replay.replayed
    assert teacher_correction_view(replay) == teacher_correction_view(original)


# ------------------------------------------------------------------ C1-R02
@pytest.mark.parametrize(
    ("change", "code"),
    [("session_ended", "INVALID_STATE"), ("age_unknown", "AGE_NOT_SUPPORTED"),
     ("age_156", "AGE_NOT_SUPPORTED"), ("age_35", "AGE_NOT_SUPPORTED")],
)
def test_r02_full_eligibility_is_rechecked_after_provider(change: str, code: str) -> None:
    h = build_analysis_harness()

    def move() -> None:
        if change == "session_ended":
            h.context.end_session(SESSION)
        else:
            age = {"age_unknown": None, "age_156": 156, "age_35": 35}[change]
            h.context.set_participant(CHILD_A, age_months=age, purposes=frozenset({PURPOSE}))

    _fake(h).on_observe = move
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED and result.code == code
    assert result.provider_invoked and not result.authoritative
    assert _counts(h) == (0, 0)


@pytest.mark.parametrize("age", [36, 155])
def test_r02_age_boundaries_after_provider_stay_accepted(age: int) -> None:
    h = build_analysis_harness()
    _fake(h).on_observe = lambda: h.context.set_participant(
        CHILD_A, age_months=age, purposes=frozenset({PURPOSE}))
    assert h.observe().authoritative


def test_r02_group_audience_ineligible_after_provider_is_rejected() -> None:
    h = build_analysis_harness()
    group_scope = replace(h.pin.scope, group_id="group_fx_1",
                          audience_participant_ids=(CHILD_A, CHILD_B))
    h.pin = replace(h.pin, scope=group_scope)
    h.requests.add(h.pin)
    h.set_job()
    _fake(h).on_observe = lambda: h.context.set_participant(
        CHILD_B, age_months=None, purposes=frozenset({PURPOSE}))
    result = h.observe()
    assert result.code == "AGE_NOT_SUPPORTED" and _counts(h) == (0, 0)


# ------------------------------------------------------------------ C1-R03
def _foundation(**scope_changes: Any) -> InMemoryAiJobStore:
    scope: dict[str, Any] = {"organization_id": ORG, "session_id": SESSION,
                             "subject_refs": (CHILD_A,), "purpose_code": PURPOSE,
                             "target_id": ASSISTANCE}
    scope.update(scope_changes)
    job = jobs.create_job(
        job_id="job_fx0001", attempt_id="att_fx0001", job_type=VISION_ANALYSIS_JOB_TYPE,
        scope=JobScope(**scope),
        request_ref=RequestRef(ASSISTANCE, 1, synthetic_snapshot().input_hash(),
                               CONTEXT_REVISION),
        correlation_id="corr_fx_job", retry_policy=FIXTURE_RETRY_POLICY, now=NOW,
    )
    store = InMemoryAiJobStore()
    with store.transaction() as tx:
        tx.insert_job(jobs.start_attempt(job, "att_fx0001", NOW))
    return store


@pytest.mark.parametrize(
    "changes",
    [
        {"session_id": "session_fx_999"},
        {"session_id": None},
        {"subject_refs": ("participant_fx_z",)},
        {"subject_refs": (CHILD_A, CHILD_B)},
        {"purpose_code": "other_purpose"},
        {"target_id": "assistance_fx_999"},
    ],
)
def test_r03_foundation_job_scope_mismatch_is_rejected_before_provider(
    changes: dict[str, Any],
) -> None:
    store = _foundation(**changes)
    before = store.snapshot().jobs
    h = build_analysis_harness(jobs=AiJobRepositoryLineage(store))
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED
    assert result.code == "JOB_SCOPE_MISMATCH" and not result.provider_invoked
    assert _fake(h).requests == [] and _counts(h) == (0, 0)
    assert store.snapshot().jobs == before


def test_r03_matching_foundation_scope_is_accepted_order_insensitive() -> None:
    h = build_analysis_harness(jobs=AiJobRepositoryLineage(_foundation()))
    assert h.observe().authoritative
    group_store = _foundation(subject_refs=(CHILD_B, CHILD_A))
    g = build_analysis_harness(jobs=AiJobRepositoryLineage(group_store))
    g.pin = replace(g.pin, scope=replace(g.pin.scope, group_id="group_fx_1",
                                         audience_participant_ids=(CHILD_A, CHILD_B)))
    g.requests.add(g.pin)
    assert g.observe().authoritative


# ------------------------------------------------------------------ C1-R04
def _long_id_response(length: int) -> dict[str, Any]:
    response = synthetic_v2_response()
    long_id = "ent-" + "a" * (length - 4)
    entities: Any = response["entities"]
    entities[0]["observation_id"] = long_id
    response["actions"][0]["actor_ref"] = long_id  # type: ignore[index]
    response["relations"][0]["subject_ref"] = long_id  # type: ignore[index]
    response["themes"][0]["evidence_refs"] = [long_id]  # type: ignore[index]
    return response


def _many(kind: str, count: int, *, null: bool = False) -> dict[str, Any]:
    response = synthetic_v2_response()
    response.update(actions=[], relations=[], themes=[], ambiguous_regions=[])
    if kind == "entities":
        response["entities"] = [{"observation_id": f"ent-{i}", "label": _text("cat"),
                                 "confidence": None if null else 0.7} for i in range(count)]
    elif kind == "ambiguous":
        response["ambiguous_regions"] = [{"observation_id": f"amb-{i}", "note": _text("blob")}
                                         for i in range(count)]
    else:  # unknown confidence spread over entities and actions
        response["entities"] = [{"observation_id": f"ent-{i}", "label": _text("cat"),
                                 "confidence": None} for i in range(200)]
        response["actions"] = [{"observation_id": f"act-{i}", "label": _text("run"),
                                "actor_ref": None, "object_ref": None, "confidence": None}
                               for i in range(count - 200)]
    return response


@pytest.mark.parametrize(
    ("response", "detail"),
    [
        (_long_id_response(121), "OBSERVATION_REF_TOO_LONG"),
        (_many("entities", 257), "TOO_MANY_OBJECT_CANDIDATES"),
        (_many("unknown", 257), "TOO_MANY_UNKNOWN_CONFIDENCE_REFS"),
        (_many("ambiguous", 257), "TOO_MANY_AMBIGUOUS_REGIONS"),
    ],
)
def test_r04_contract_incompatible_mapped_output_is_malformed_before_storage(
    response: dict[str, Any], detail: str
) -> None:
    VisionUnderstandingSuccessV2.model_validate(response)  # legacy V2 accepts it
    h, transport = _bridge(response)
    outcome = h.provider.observe(_request(h))
    assert not isinstance(outcome, ObservationSucceeded)
    assert outcome.detail == detail
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED
    assert result.code == "OUTPUT_MALFORMED" and transport.calls == 2
    assert _counts(h) == (0, 0)
    # Nothing was accepted, so CMD-34 has no target: a typed 404, no commit, never a 500.
    client = TestClient(create_analysis_corrections_fixture_app(h.service, {"t": TEACHER}),
                        raise_server_exceptions=False)
    http = client.post(
        "/api/collaboration/v1/analysis-results/ana_fx0001/corrections",
        headers={"Authorization": "Fixture t", "Idempotency-Key": "key_fx_r04_bad",
                 "If-Match": '"analysis:ana_fx0001:1"', "Content-Type": "application/json"},
        content=json.dumps({"intended_objects": ["tiger"], "correction_reason": "x",
                            "expected_context_revision": CONTEXT_REVISION}),
    )
    assert http.status_code == 404
    state = h.store.snapshot()
    assert state.corrections == {} and state.receipts == {} and state.invalidations == {}


def _request(h: AnalysisHarness) -> Any:
    from sketch2life.application.ports.vision_analysis import ObservationRequest
    from sketch2life.domain.vision_analysis import ProviderContextMode

    return ObservationRequest("corr_fx_1", ORG, h.snapshot.render, h.receipt,
                              ProviderContextMode.IMAGE_ONLY)


@pytest.mark.parametrize("response", [_long_id_response(120), _many("entities", 256),
                                      _many("entities", 256, null=True),
                                      _many("ambiguous", 256)])
def test_r04_boundary_outputs_survive_cmd34_and_replay_end_to_end(
    response: dict[str, Any],
) -> None:
    h, _ = _bridge(response)
    result = h.observe()
    assert result.authoritative
    analysis_id = result.analysis_id or ""
    client = TestClient(create_analysis_corrections_fixture_app(h.service, {"t": TEACHER}),
                        raise_server_exceptions=False)
    headers = {"Authorization": "Fixture t", "Idempotency-Key": "key_fx_r04",
               "If-Match": f'"analysis:{analysis_id}:1"', "Content-Type": "application/json"}
    body = json.dumps({"intended_objects": ["tiger"], "correction_reason": "Teacher confirms",
                       "expected_context_revision": CONTEXT_REVISION})
    url = f"/api/collaboration/v1/analysis-results/{analysis_id}/corrections"
    first = client.post(url, headers=headers, content=body)
    replay = client.post(url, headers=headers, content=body)
    assert first.status_code == 200 and replay.status_code == 200
    assert replay.headers["Idempotency-Replayed"] == "true"
    record = h.service.analysis_record(TEACHER, analysis_id)
    AnalysisRecordV1.model_validate_json(json.dumps(record))
    AnalysisWorkerCandidateV1.model_validate_json(json.dumps(record["candidate"]))


def test_r04_service_rejects_contract_incompatible_output_from_any_provider() -> None:
    h = build_analysis_harness()
    too_long = OriginalObservation(
        entities=(EntityObservation("e" * 121, ObservedLabel("cat", "DECLARED", ("en",)), 0.5),),
        actions=(), relations=(), themes=(), ambiguous_regions=(),
    )
    _fake(h).observation = too_long
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED
    assert result.code == "OUTPUT_MALFORMED" and _counts(h) == (0, 0)


# --------------------------------------- C1-R04 follow-up (Codex re-review)
_LABEL = ObservedLabel("cat", "DECLARED", ("en",))


def _typed(**overrides: Any) -> OriginalObservation:
    """Every reference kind once, through the supported typed (fake) provider seam."""

    ids: dict[str, Any] = {"entity": "ent-1", "action": "act-1", "relation": "rel-1",
                           "theme": "thm-1", "ambiguous": "amb-1", "actor": "ent-1",
                           "object": "ent-2", "subject": "ent-1", "relation_object": "ent-2",
                           "evidence": "ent-1"}
    ids.update(overrides)
    return OriginalObservation(
        entities=(EntityObservation(ids["entity"], _LABEL, 0.6),
                  EntityObservation("ent-2", ObservedLabel("ball", "DECLARED", ("en",)), None)),
        actions=(ActionObservation(ids["action"], ObservedLabel("sitting", "DECLARED", ("en",)),
                                   ids["actor"], ids["object"], 0.4),),
        relations=(RelationObservation(ids["relation"], ObservedLabel("next to", "DECLARED",
                                                                      ("en",)),
                                       ids["subject"], ids["relation_object"], None),),
        themes=(ThemeObservation(ids["theme"], ObservedLabel("play", "DECLARED", ("en",)),
                                 (ids["evidence"],), 0.3),),
        ambiguous_regions=(AmbiguousRegionObservation(ids["ambiguous"],
                                                      ObservedLabel("blob", "DECLARED",
                                                                    ("en",))),),
    )


_INVALID_REFS = [
    *[{kind: "x-1\n"} for kind in ("entity", "action", "relation", "theme", "ambiguous")],
    *[{kind: "ent-1\n"} for kind in ("actor", "object", "subject", "relation_object",
                                      "evidence")],
    {"actor": ""},
    {"object": ""},
    {"subject": ""},
    {"evidence": ""},
]


@pytest.mark.parametrize("overrides", _INVALID_REFS, ids=lambda o: repr(o))
def test_r04_final_newline_or_empty_reference_is_malformed_before_storage(
    overrides: dict[str, Any],
) -> None:
    observation = _typed(**overrides)
    assert observation_bounds_violation(observation) == "OBSERVATION_REF_INVALID"
    h = build_analysis_harness()
    _fake(h).observation = observation
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED
    assert result.code == "OUTPUT_MALFORMED" and result.analysis_id is None
    assert _counts(h) == (0, 0) and _results(h) == 0
    client = TestClient(create_analysis_corrections_fixture_app(h.service, {"t": TEACHER}),
                        raise_server_exceptions=False)
    http = client.post(
        "/api/collaboration/v1/analysis-results/ana_fx0001/corrections",
        headers={"Authorization": "Fixture t", "Idempotency-Key": "key_fx_r04_ref",
                 "If-Match": '"analysis:ana_fx0001:1"', "Content-Type": "application/json"},
        content=json.dumps({"intended_objects": ["tiger"], "correction_reason": "x",
                            "expected_context_revision": CONTEXT_REVISION}),
    )
    assert http.status_code == 404
    state = h.store.snapshot()
    assert state.corrections == {} and state.receipts == {} and state.invalidations == {}


@pytest.mark.parametrize(
    "overrides",
    [{}, {"actor": None}, {"object": None}, {"actor": None, "object": None},
     {"entity": "e" * 120, "actor": "e" * 120, "subject": "e" * 120, "evidence": "e" * 120}],
    ids=["valid", "actor-none", "object-none", "both-none", "120-chars"],
)
def test_r04_none_and_valid_references_are_accepted_and_project(
    overrides: dict[str, Any],
) -> None:
    observation = _typed(**overrides)
    assert observation_bounds_violation(observation) is None
    h = build_analysis_harness()
    _fake(h).observation = observation
    result = h.observe()
    assert result.authoritative
    analysis_id = result.analysis_id or ""
    client = TestClient(create_analysis_corrections_fixture_app(h.service, {"t": TEACHER}),
                        raise_server_exceptions=False)
    headers = {"Authorization": "Fixture t", "Idempotency-Key": "key_fx_r04_ok",
               "If-Match": f'"analysis:{analysis_id}:1"', "Content-Type": "application/json"}
    body = json.dumps({"intended_objects": ["tiger"], "correction_reason": "Teacher confirms",
                       "expected_context_revision": CONTEXT_REVISION})
    url = f"/api/collaboration/v1/analysis-results/{analysis_id}/corrections"
    assert client.post(url, headers=headers, content=body).status_code == 200
    replay = client.post(url, headers=headers, content=body)
    assert replay.status_code == 200 and replay.headers["Idempotency-Replayed"] == "true"
    AnalysisRecordV1.model_validate_json(
        json.dumps(h.service.analysis_record(TEACHER, analysis_id)))


# ------------------------------------------------------------------ C1-R05
def test_r05_history_beyond_256_corrections_stays_complete_and_valid() -> None:
    h = build_analysis_harness()
    analysis_id = h.accepted_analysis()
    first_command = h.correction(TEACHER, analysis_id, key="key_fx_r05_0001")
    first = h.service.submit_correction(first_command)
    total = 260
    for index in range(2, total + 1):
        h.service.submit_correction(
            h.correction(TEACHER, analysis_id, revision=index, key=f"key_fx_r05_{index:04d}",
                         intended=(f"tiger {index}",))
        )
    record = AnalysisRecordV1.model_validate_json(
        json.dumps(h.service.analysis_record(TEACHER, analysis_id)))
    assert len(record.corrections) == total and record.analysis_revision == total + 1
    assert [c.correction_version for c in record.corrections] == list(range(2, total + 2))
    assert record.current_meaning_ref == record.corrections[-1].correction_id
    replay = h.service.submit_correction(first_command)
    assert replay.replayed
    assert teacher_correction_view(replay) == teacher_correction_view(first)
    assert len(h.store.snapshot().receipts) == total


# ------------------------------------------------------------------ C1-R06
def test_r06_full_typed_provider_result_is_retained_and_resolvable() -> None:
    raw = synthetic_v2_response()
    typed = VisionUnderstandingSuccessV2.model_validate(raw)
    h, _ = _bridge(raw)
    analysis_id = h.accepted_analysis()
    with h.store.transaction() as tx:
        head = tx.get_head(analysis_id)
        observation = tx.get_observation(analysis_id)
    assert head is not None and observation is not None
    candidate = worker_candidate_view(head, observation)
    evidence_refs: Any = candidate["evidence_refs"]
    ref = next(r for r in evidence_refs if r["kind"] == "provider_result")
    record = h.service.resolve_provider_result(TEACHER, ref["ref"])
    assert record.result_ref == ref["ref"] and record.analysis_id == analysis_id
    assert record.result_sha256 == ref["sha256"]
    assert sha256(record.canonical_json.encode("utf-8")).hexdigest() == record.result_sha256
    rebuilt = VisionUnderstandingSuccessV2.model_validate_json(record.canonical_json)
    assert rebuilt == typed and rebuilt.correlation_id == "corr_fx_1"
    proposal = h.service.submit_correction(h.correction(DEVICE_A, analysis_id))
    h.service.submit_correction(h.correction(TEACHER, analysis_id, revision=2,
                                             basis=proposal.correction.correction_id))
    assert h.service.resolve_provider_result(TEACHER, ref["ref"]) == record


def test_r06_resolver_is_teacher_only_and_concealed() -> None:
    h, _ = _bridge(synthetic_v2_response())
    analysis_id = h.accepted_analysis()
    for principal, code in ((DEVICE_A, "FORBIDDEN_SCOPE"), (OUTSIDER, "RESOURCE_NOT_FOUND")):
        with pytest.raises(VisionAnalysisError) as exc:
            h.service.resolve_provider_result(principal, f"result:{analysis_id}")
        assert exc.value.code == code
    with pytest.raises(VisionAnalysisError) as missing:
        h.service.resolve_provider_result(TEACHER, "result:ana_fx0999")
    assert missing.value.code == "RESOURCE_NOT_FOUND"


def test_r06_failed_commit_leaves_no_dangling_result_ref() -> None:
    h, _ = _bridge(synthetic_v2_response())
    h.store.fail_next_commit = True
    with pytest.raises(VisionAnalysisError) as exc:
        h.observe()
    assert exc.value.code == "DEPENDENCY_UNAVAILABLE"
    assert _counts(h) == (0, 0) and _results(h) == 0
    with pytest.raises(VisionAnalysisError) as missing:
        h.service.resolve_provider_result(TEACHER, "result:ana_fx0001")
    assert missing.value.code == "RESOURCE_NOT_FOUND"


def test_r06_result_record_hash_must_match_content() -> None:
    from sketch2life.domain.vision_analysis import ProviderResultRecord

    document = '{"a":1}'
    with pytest.raises(AnalysisRuleViolation):
        ProviderResultRecord("result:ana_1", "ana_1", ORG, "X/1", document, "0" * 64)


def test_r06_provider_document_must_match_reported_result_hash() -> None:
    h = build_analysis_harness()

    def tamper() -> None:
        request = _fake(h).requests[0]
        honest = synthetic_success(request, executed_at=h.clock.now())
        _fake(h).scripted = [replace(honest, result_document='{"tampered":true}')]

    _fake(h).on_observe = tamper
    result = h.observe()
    assert result.disposition is ObservationDisposition.FAILED
    assert result.code == "OUTPUT_MALFORMED" and _counts(h) == (0, 0)
