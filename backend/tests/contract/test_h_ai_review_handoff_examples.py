"""BE2-02 C1 H-AI-REVIEW consumer examples stay in sync with the code and contracts (V16)."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from sketch2life.contracts.schemas.ai_contract_candidates import check_shape
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisCorrectionChildReceiptV1,
    AnalysisCorrectionReceiptV1,
    AnalysisRecordV1,
    AnalysisWorkerCandidateV1,
)
from sketch2life.contracts.schemas.vision_v2 import VisionUnderstandingSuccessV2
from sketch2life.infrastructure.vision_analysis.harness import build_handoff_examples

EXAMPLES = (
    Path(__file__).resolve().parents[3]
    / "features/FEAT-048-be2-vision-correction/fixtures/h_ai_review"
)
NAMES = ("analysis_worker_candidate", "correction_child_receipt", "correction_teacher_receipt",
         "analysis_record", "invalidation_intents", "downstream_meaning",
         "provider_result_record")


def _load(name: str) -> Any:
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built() -> dict[str, Any]:
    examples: dict[str, Any] = json.loads(json.dumps(build_handoff_examples()))
    return examples


@pytest.mark.parametrize("name", NAMES)
def test_v16_committed_example_matches_deterministic_build(name: str,
                                                           built: dict[str, Any]) -> None:
    assert _load(name) == built[name]


def test_v16_examples_validate_against_the_candidate_contracts() -> None:
    candidate = _load("analysis_worker_candidate")
    AnalysisWorkerCandidateV1.model_validate_json(json.dumps(candidate))
    assert check_shape("DATA-22", candidate) == []
    assert candidate["provenance"]["provider_context_mode"] == "image_only"
    AnalysisCorrectionChildReceiptV1.model_validate_json(
        json.dumps(_load("correction_child_receipt")))
    teacher = AnalysisCorrectionReceiptV1.model_validate_json(
        json.dumps(_load("correction_teacher_receipt")))
    record = AnalysisRecordV1.model_validate_json(json.dumps(_load("analysis_record")))
    assert teacher.current_meaning_ref == record.current_meaning_ref
    assert record.original_observation.entities[0].label.value == "cat"
    assert [c.kind for c in record.corrections] == ["child_proposal", "teacher_confirmation"]
    meaning = _load("downstream_meaning")
    assert meaning["state"] == "confirmed" and meaning["confirmed_concepts"] == ["tiger"]
    assert [i["reason"] for i in _load("invalidation_intents")] == [
        "child_intent_proposed", "teacher_meaning_confirmed"]


def test_v16_r06_provider_result_example_resolves_the_emitted_ref() -> None:
    result = _load("provider_result_record")
    candidate = _load("analysis_worker_candidate")
    ref = next(r for r in candidate["evidence_refs"] if r["kind"] == "provider_result")
    assert (result["result_ref"], result["result_sha256"]) == (ref["ref"], ref["sha256"])
    assert sha256(result["canonical_json"].encode("utf-8")).hexdigest() == ref["sha256"]
    typed = VisionUnderstandingSuccessV2.model_validate_json(result["canonical_json"])
    assert typed.correlation_id == "corr_fx_1" and typed.entities[0].label.value == "cat"


def test_v16_examples_are_synthetic_and_path_free() -> None:
    for name in NAMES:
        text = (EXAMPLES / f"{name}.json").read_text(encoding="utf-8")
        assert not re.search(r"\b[A-Za-z]:\\\\", text), name  # no Windows drive path in JSON
        assert "/Users/" not in text and "/home/" not in text
        assert "_fx" in text
