"""BE2-02 C1 DATA-22/CMD-34 candidate contract tests (V01, V15, V16 consumer shape)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.services.vision_analysis import (
    child_correction_view,
    teacher_correction_view,
    worker_candidate_view,
)
from sketch2life.contracts.schemas.ai_contract_candidates import check_shape
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisCorrectionChildReceiptV1,
    AnalysisCorrectionCommandV1,
    AnalysisCorrectionReceiptV1,
    AnalysisRecordV1,
    AnalysisWorkerCandidateV1,
    CorrectionRecordV1,
)
from sketch2life.infrastructure.vision_analysis.fakes import synthetic_observation
from sketch2life.infrastructure.vision_analysis.harness import (
    DEVICE_A,
    TEACHER,
    AnalysisHarness,
    build_analysis_harness,
)

SERVER_OWNED = ("author", "role", "actor", "organization_id", "analysis_revision",
                "accepted_status", "meaning_status", "kind", "participant_id", "turn_id",
                "correction_id", "recorded_at")


def _command(**changes: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "intended_objects": ["tiger"],
        "correction_reason": "Child says it is a tiger",
        "expected_context_revision": 3,
    }
    body.update(changes)
    return body


def _parse(body: dict[str, Any]) -> AnalysisCorrectionCommandV1:
    return AnalysisCorrectionCommandV1.model_validate_json(json.dumps(body))


def _candidate(h: AnalysisHarness) -> dict[str, Any]:
    analysis_id = h.accepted_analysis()
    with h.store.transaction() as tx:
        head = tx.get_head(analysis_id)
        observation = tx.get_observation(analysis_id)
    assert head is not None and observation is not None
    view: dict[str, Any] = json.loads(json.dumps(worker_candidate_view(head, observation)))
    return view


def test_v01_valid_command_normalises_text_and_treats_omitted_as_null() -> None:
    parsed = _parse(_command(intended_objects=["  tiger  ", "Striped cat"]))
    assert parsed.intended_objects == ("tiger", "Striped cat")
    assert parsed.child_explanation is None
    assert _parse(_command(child_explanation=None)) == _parse(_command())


@pytest.mark.parametrize("field", SERVER_OWNED)
def test_v01_command_rejects_server_owned_identity_status_and_author(field: str) -> None:
    with pytest.raises(ValidationError) as exc:
        _parse(_command(**{field: "teacher"}))
    assert exc.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize(
    "changes",
    [
        {"intended_objects": []},
        {"intended_objects": ["tiger", "TIGER"]},
        {"intended_objects": [f"object {i}" for i in range(17)]},
        {"intended_objects": ["   "]},
        {"intended_objects": ["x" * 129]},
        {"intended_objects": [7]},
        {"intended_objects": "tiger"},
        {"correction_reason": ""},
        {"expected_context_revision": True},
        {"expected_context_revision": "3"},
        {"expected_context_revision": -1},
        {"child_explanation": ""},
        {"child_explanation": "x" * 4001},
        {"basis_correction_ref": "bad ref!"},
    ],
)
def test_v01_command_rejects_invalid_values(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _parse(_command(**changes))


def test_v01_command_requires_reason_and_expected_context() -> None:
    for missing in ("correction_reason", "expected_context_revision", "intended_objects"):
        body = _command()
        body.pop(missing)
        with pytest.raises(ValidationError):
            _parse(body)


def test_v01_worker_candidate_is_strict_and_preserves_null_confidence() -> None:
    h = build_analysis_harness()
    h.provider.observation = synthetic_observation(  # type: ignore[attr-defined]
        (("ent-1", "cat", None), ("ent-2", "house", 0.4))
    )
    candidate = _candidate(h)
    parsed = AnalysisWorkerCandidateV1.model_validate_json(json.dumps(candidate))
    assert [c.confidence for c in parsed.object_candidates] == [None, 0.4]
    assert parsed.uncertainty.unknown_confidence_refs == ("ent-1",)
    assert parsed.provenance.evidence_kind == "synthetic_fake"
    # The foundation's shallow DATA-22 ShapeSpec still accepts the strict candidate unchanged.
    assert check_shape("DATA-22", candidate) == []


@pytest.mark.parametrize("raw", ["true", '"0.5"', "NaN", "Infinity", "1.5", "-0.1"])
def test_v01_worker_candidate_rejects_bad_confidence(raw: str) -> None:
    candidate = _candidate(build_analysis_harness())
    text = json.dumps(candidate).replace('"confidence": 0.62', f'"confidence": {raw}')
    assert raw in text
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(text)


def test_v01_worker_candidate_requires_confidence_key_and_distinct_bindings() -> None:
    candidate = _candidate(build_analysis_harness())
    no_key = json.loads(json.dumps(candidate))
    del no_key["object_candidates"][0]["confidence"]
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(json.dumps(no_key))
    confused = json.loads(json.dumps(candidate))
    render = next(r for r in confused["evidence_refs"] if r["kind"] == "source_render")
    checkpoint = next(r for r in confused["evidence_refs"] if r["kind"] == "source_checkpoint")
    render["sha256"] = checkpoint["sha256"]
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(json.dumps(confused))
    duplicate = json.loads(json.dumps(candidate))
    duplicate["evidence_refs"][1] = dict(duplicate["evidence_refs"][0])
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(json.dumps(duplicate))
    live = json.loads(json.dumps(candidate))
    live["provenance"]["evidence_kind"] = "live"
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(json.dumps(live))
    typed_bridge = json.loads(json.dumps(candidate))
    typed_bridge["provenance"].update(evidence_kind="offline_legacy_bridge",
                                      provider_context_mode="typed_context")
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(json.dumps(typed_bridge))


def test_v04_v15_projections_validate_and_child_projection_is_refs_only() -> None:
    h = build_analysis_harness()
    analysis_id = h.accepted_analysis()
    proposal = h.service.submit_correction(
        h.correction(DEVICE_A, analysis_id, explanation="It has stripes")
    )
    child = child_correction_view(proposal)
    AnalysisCorrectionChildReceiptV1.model_validate_json(json.dumps(child))
    assert set(child) == {"analysis_id", "analysis_revision", "correction_id",
                          "correction_version", "kind", "meaning_status", "recorded_at"}
    serialized = json.dumps(child)
    for leaked in ('"cat"', "0.62", "stripes", "tiger", "confidence", "uncertainty", "provenance",
                   "age", "moderation"):
        assert leaked not in serialized
    confirmation = h.service.submit_correction(
        h.correction(TEACHER, analysis_id, revision=2, basis=proposal.correction.correction_id)
    )
    teacher = AnalysisCorrectionReceiptV1.model_validate_json(
        json.dumps(teacher_correction_view(confirmation))
    )
    assert teacher.object_candidates[0].label == "cat"
    assert teacher.correction.kind == "teacher_confirmation"
    assert teacher.current_meaning_ref == confirmation.correction.correction_id
    record = AnalysisRecordV1.model_validate_json(
        json.dumps(h.service.analysis_record(TEACHER, analysis_id))
    )
    assert [c.kind for c in record.corrections] == ["child_proposal", "teacher_confirmation"]
    assert record.corrections[0].child_explanation == "It has stripes"
    assert record.original_observation.entities[0].label.value == "cat"


def test_v04_record_view_rejects_child_proposal_as_current_meaning() -> None:
    h = build_analysis_harness()
    analysis_id = h.accepted_analysis()
    h.service.submit_correction(h.correction(DEVICE_A, analysis_id))
    view = json.loads(json.dumps(h.service.analysis_record(TEACHER, analysis_id)))
    view["current_meaning_ref"] = view["corrections"][0]["correction_id"]
    with pytest.raises(ValidationError):
        AnalysisRecordV1.model_validate_json(json.dumps(view))


def test_v05_correction_record_rejects_inconsistent_author_or_status() -> None:
    h = build_analysis_harness()
    analysis_id = h.accepted_analysis()
    proposal = h.service.submit_correction(h.correction(DEVICE_A, analysis_id))
    view = json.loads(json.dumps(teacher_correction_view(proposal)))["correction"]
    CorrectionRecordV1.model_validate_json(json.dumps(view))
    for mutate in (
        {"meaning_status": "confirmed"},
        {"author": {**view["author"], "role": "teacher"}},
        {"kind": "teacher_confirmation"},
    ):
        with pytest.raises(ValidationError):
            CorrectionRecordV1.model_validate_json(json.dumps({**view, **mutate}))
