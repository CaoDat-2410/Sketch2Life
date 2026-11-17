"""BE2-04 SK1 DATA-23 contracts and H-AI-REVIEW examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.ai_contract_candidates import (
    SHAPE_SPECS,
    ProviderCopyLifecycleReportV1,
    check_shape,
)
from sketch2life.contracts.schemas.sketch_proposals import (
    SketchProposalDeviceViewV1,
    SketchProposalEventV1,
    SketchProposalRecordV1,
)
from sketch2life.infrastructure.assistance.harness import DEVICE_A, ORG, TEACHER
from sketch2life.infrastructure.sketch_generation.harness import (
    EXAMPLES_FIXTURE_ID,
    build_sketch_chain_harness,
    build_sketch_examples,
)

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "features/FEAT-050-be2-sketch-generation/fixtures/h_ai_review" / (
    "sketch_proposal_examples.json")


def _examples() -> dict[str, object]:
    return cast(dict[str, object], json.loads(EXAMPLES.read_text(encoding="utf-8")))


def test_c01_record_device_contracts_round_trip_and_reject_extra_fields() -> None:
    chain = build_sketch_chain_harness()
    proposal_id = chain.open_ready(chain.h.command())
    chain.run_sketch(proposal_id)
    assistance_id = chain.proposal(proposal_id).binding.assistance_id

    record = chain.service.get_record(TEACHER, proposal_id)
    assert check_shape("DATA-23", record) == []
    parsed_record = SketchProposalRecordV1.model_validate_json(json.dumps(record), strict=True)
    assert parsed_record.pipeline_state == "pending_teacher_review"
    assert parsed_record.text_or_question is not None

    device = chain.service.device_view(DEVICE_A, assistance_id)
    parsed_device = SketchProposalDeviceViewV1.model_validate_json(
        json.dumps(device), strict=True)
    assert parsed_device.status == "pending"
    assert set(device) == {"contract_name", "contract_version", "assistance_id", "status"}
    assert not {"proposal_id", "text_or_question", "overlay_asset_ref", "reason"} & set(device)

    with pytest.raises(ValidationError):
        SketchProposalRecordV1.model_validate_json(
            json.dumps({**record, "unexpected_internal_field": "must be rejected"}), strict=True)
    with pytest.raises(ValidationError):
        SketchProposalDeviceViewV1.model_validate_json(
            json.dumps({**device, "proposal_id": proposal_id}), strict=True)


def test_c02_data23_shape_remains_shallow_and_accepts_record_projection() -> None:
    record = _examples()["record_pending"]
    assert isinstance(record, dict)
    assert check_shape("DATA-23", record) == []
    assert SHAPE_SPECS["DATA-23"].required == (
        "proposal_id", "proposal_version", "review_revision", "assistance_id",
        "request_revision", "source_snapshot_ref", "context_revision", "assistance_level",
        "display_mode", "moderation_state", "pipeline_state", "created_at")


def test_c04_event_contract_contains_no_proposal_content_or_child_text() -> None:
    event = _examples()["notice_blocked"]
    assert isinstance(event, dict)
    parsed = SketchProposalEventV1.model_validate_json(json.dumps(event), strict=True)
    assert parsed.event_type == "sketch.blocked_unsafe"
    forbidden = {"text_or_question", "child_intent", "provider_log", "model_profile",
                 "asset_url", "signing_key", "raw_output"}
    assert not forbidden & set(event)


def test_c05_fixture_copy_report_never_claims_provider_deletion() -> None:
    report = _examples()["provider_copy_report"]
    assert isinstance(report, dict)
    parsed = ProviderCopyLifecycleReportV1.model_validate_json(json.dumps(report), strict=True)
    assert parsed.fixture_marker
    assert all(copy.evidence_kind == "fixture" and not copy.actual_deletion_proven
               for copy in parsed.copies)
    assert all(copy.report_label != "deleted" for copy in parsed.copies)


def test_c05_registry_copy_report_projects_live_fixture_lifecycle() -> None:
    chain = build_sketch_chain_harness()
    proposal_id = chain.open_ready(chain.h.command())
    routed = chain.run_sketch(proposal_id)
    assert routed is not None and routed.started
    scope_ref = f"sketch_proposal:{proposal_id}"
    chain.copies.purge_scope(ORG, scope_ref, "c05_registry_report")
    outcomes = chain.copies.discover(ORG, scope_ref)
    assert outcomes

    report = ProviderCopyLifecycleReportV1.model_validate({
        "fixture_marker": True,
        "organization_id": ORG,
        "scope_ref": scope_ref,
        "copies": tuple(
            {
                "copy_id": copy.copy_id,
                "kind": copy.kind,
                "status": copy.status,
                "report_label": copy.report_label,
                "receipt_id": copy.receipt_id,
                "evidence_kind": copy.evidence_kind,
                "reason_code": copy.reason_code,
                "actual_deletion_proven": copy.actual_deletion_proven,
            }
            for copy in outcomes
        ),
    }, strict=True)
    assert report.fixture_marker
    assert {copy.copy_id for copy in report.copies} == {copy.copy_id for copy in outcomes}
    assert all(not copy.actual_deletion_proven for copy in report.copies)
    assert all(copy.report_label != "deleted" for copy in report.copies)
    assert any(copy.evidence_kind == "fixture" for copy in report.copies)
    assert any(copy.report_label == "fixture_deleted_not_actual" for copy in report.copies)


def test_c06_h_ai_review_example_bundle_is_valid_and_synthetic() -> None:
    examples = _examples()
    assert examples["fixture_id"] == EXAMPLES_FIXTURE_ID == "FEAT-050-SK1-H-AI-REVIEW"
    assert examples["synthetic_data"] is True
    SketchProposalRecordV1.model_validate_json(
        json.dumps(examples["record_pending"]), strict=True)
    SketchProposalEventV1.model_validate_json(
        json.dumps(examples["notice_blocked"]), strict=True)
    SketchProposalDeviceViewV1.model_validate_json(
        json.dumps(examples["device_view"]), strict=True)
    ProviderCopyLifecycleReportV1.model_validate_json(
        json.dumps(examples["provider_copy_report"]), strict=True)


def test_c06_committed_examples_match_deterministic_producer_build() -> None:
    """C06: the pinned example bundle is exactly what the chain producer emits (no drift)."""

    built = json.loads(json.dumps(build_sketch_examples()))
    assert built == json.loads(json.dumps(build_sketch_examples()))  # deterministic
    assert _examples() == built
    record = built["record_pending"]
    assert record["pipeline_state"] == "pending_teacher_review"
    assert record["display_mode"] == "overlay" and record["overlay_asset_ref"] is not None
    assert built["notice_blocked"]["event_type"] == "sketch.blocked_unsafe"
    assert built["notice_blocked"]["reason"] == "UNSAFE_CONTENT"
    assert built["device_view"]["status"] == "pending"
    assert built["device_view"]["assistance_id"] == record["assistance_id"]
    assert built["provider_copy_report"]["scope_ref"] == f"sketch_proposal:{record['proposal_id']}"
