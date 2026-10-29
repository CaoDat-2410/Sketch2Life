"""BE2-05 contract checks: Sketch binder over unchanged DATA-24 V1, views, error table, examples."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
)
from sketch2life.contracts.schemas.sketch_reviews import (
    ERROR_STATUS,
    BindTarget,
    SketchChildPayloadV0,
    SketchReviewBindError,
    SketchReviewQueueItemV0,
    SketchReviewResultV0,
    bind_sketch_review,
)
from sketch2life.infrastructure.sketch_review.harness import build_sketch_review_examples

ROOT = Path(__file__).resolve().parents[3]
DATA24 = ROOT / "features/FEAT-044-be2-ai-job-foundation/fixtures/data24"
EXAMPLES = (ROOT / "features/FEAT-052-be2-sketch-review/fixtures/h_ai_review"
            / "sketch_review_examples.json")
# Bytes of the shared DATA-24 pack at baseline 58293f1 (= consumer snapshot 76959ab).
PACK = {
    "backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py": None,
    "backend/tests/contract/test_ai_job_contracts.py": None,
}
SRS_CODES = {"MALFORMED_REQUEST", "INVALID_CURSOR", "UNAUTHENTICATED", "CAPABILITY_EXPIRED",
             "FORBIDDEN_SCOPE", "GRANT_REVOKED", "CONSENT_REQUIRED", "TOOL_NOT_ALLOWED",
             "REGION_LOCKED", "RESOURCE_NOT_FOUND", "INVALID_STATE", "TURN_CLOSED",
             "IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_PAYLOAD_MISMATCH", "SYNC_GAP",
             "CONTENT_RECALLED", "STALE_CONTEXT", "VIDEO_NOT_EXHAUSTED", "POLICY_UNRESOLVED",
             "JOIN_EXPIRED", "CURSOR_EXPIRED", "HISTORY_WINDOW_EXPIRED", "STALE_AGGREGATE",
             "PRECONDITION_REQUIRED", "PAYLOAD_TOO_LARGE", "UNSUPPORTED_MEDIA_TYPE",
             "FIELD_VALIDATION_FAILED", "FIELD_NOT_ALLOWED", "AGE_CONTEXT_CONFLICT",
             "AGE_NOT_SUPPORTED", "RATE_LIMITED", "BUDGET_EXCEEDED", "SAVE_UNAVAILABLE",
             "DEPENDENCY_UNAVAILABLE", "PROVIDER_TIMEOUT"}


def _fixture(kind: str, name: str) -> ExactContentReviewCommandV1:
    return ExactContentReviewCommandV1.model_validate_json(
        (DATA24 / kind / name).read_bytes(), strict=True)


def _target_for(command: ExactContentReviewCommandV1) -> BindTarget:
    audience = command.audience_scope
    return BindTarget(command.target_id, command.target_version, command.target_hash,
                      command.source_context_revision, audience.session_id,
                      frozenset(getattr(audience, "group_ids", ())),
                      frozenset(getattr(audience, "participant_ids", ())))


def test_rv_c01_binder_accepts_shared_positive_sketch_fixture() -> None:
    command = _fixture("positive", "session_sketch_approve.json")
    bound = bind_sketch_review(command, _target_for(command), command.target_id)
    assert bound.decision == "approve" and bound.participant_ids == ("participant_fx_001",)


def test_rv_c01_binder_rejects_library_and_mismatches() -> None:
    library = _fixture("positive", "library_request_changes.json")
    command = _fixture("positive", "session_sketch_approve.json")
    with pytest.raises(SketchReviewBindError):
        bind_sketch_review(library, _target_for(command), library.target_id)
    with pytest.raises(SketchReviewBindError) as raised:
        bind_sketch_review(command, _target_for(command), "proposal_fx_other")
    assert raised.value.code == "FIELD_VALIDATION_FAILED"
    stale = BindTarget(command.target_id, command.target_version + 1, command.target_hash,
                       command.source_context_revision, "session_fx_001", frozenset(),
                       frozenset({"participant_fx_001"}))
    with pytest.raises(SketchReviewBindError) as raised:
        bind_sketch_review(command, stale, command.target_id)
    assert raised.value.code == "STALE_CONTEXT"
    long_reason = command.model_copy(update={"decision": "reject", "reason": "x" * 150})
    with pytest.raises(SketchReviewBindError):  # V1 allows 200; the Sketch binder 128 (OD-02)
        bind_sketch_review(long_reason, _target_for(command), command.target_id)


@pytest.mark.parametrize("path", sorted((DATA24 / "negative").glob("*.json")),
                         ids=lambda p: p.stem)
def test_rv_c01_shared_negative_fixtures_never_reach_the_binder(path: Path) -> None:
    with pytest.raises(ValidationError):
        ExactContentReviewCommandV1.model_validate_json(path.read_bytes(), strict=True)


def test_rv_c02_shared_pack_bytes_unchanged_from_baseline() -> None:
    import subprocess
    for rel in PACK:
        head = subprocess.run(["git", "-C", str(ROOT), "show",
                               f"58293f1a29ec630e2603c2860b6a2337fadfa713:{rel}"],
                              capture_output=True, check=True).stdout
        assert (ROOT / rel).read_bytes() == head  # literal bytes, no EOL normalization
    manifest = json.loads((DATA24.parent / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        if name.startswith("data24/"):
            assert sha256((DATA24.parent / name).read_bytes()).hexdigest() == digest


def test_rv_c03_error_codes_exist_in_srs() -> None:
    assert set(ERROR_STATUS) <= SRS_CODES
    assert ERROR_STATUS["STALE_AGGREGATE"] == 412 and ERROR_STATUS["PRECONDITION_REQUIRED"] == 428


def test_rv_c04_examples_regenerate_byte_identically() -> None:
    generated = json.dumps(build_sketch_review_examples(), indent=2, sort_keys=True,
                           ensure_ascii=False) + "\n"
    raw = EXAMPLES.read_bytes()
    assert b"\r" not in raw
    assert raw.decode("utf-8") == generated
    data = json.loads(raw)
    assert data["synthetic_only"] is True
    assert ":\\\\" not in generated and "/Users/" not in generated
    examples = data["examples"]
    SketchReviewQueueItemV0.model_validate_json(json.dumps(examples["queue_item_pending"]))
    SketchReviewResultV0.model_validate_json(json.dumps(examples["review_result_approve"]))
    SketchChildPayloadV0.model_validate_json(json.dumps(examples["child_payload_approved"]))
    assert examples["child_payload_approved"]["status"] == "available"
    assert examples["child_payload_rejected"]["status"] == "unavailable"
    assert examples["child_payload_rejected"]["text_or_question"] is None


def test_views_are_closed_objects() -> None:
    with pytest.raises(ValidationError):
        SketchChildPayloadV0.model_validate({"proposal_id": "p1", "status": "available",
                                             "extra": 1})
