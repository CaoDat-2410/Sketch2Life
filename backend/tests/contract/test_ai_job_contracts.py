"""BE2-01 Phase A candidate contract pack: DATA-25, DATA-24, ProviderCopyLifecycle, shapes."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError
from sketch2life.contracts.schemas.ai_contract_candidates import (
    FULL_SCHEMA_IDS,
    SHAPE_SPECS,
    ExactContentReviewCommandV1,
    ExactContentReviewRecordV1,
    ProviderCopyLifecycleReportV1,
    check_shape,
)
from sketch2life.contracts.schemas.ai_jobs import (
    AsyncJobChildViewV1,
    AsyncJobViewV1,
    CollaborationErrorV1,
    JobCompletionClaimV1,
    JobProgressV1,
)

FIXTURES = Path(__file__).resolve().parents[3] / "features/FEAT-044-be2-ai-job-foundation/fixtures"
GROUPS: dict[str, type[BaseModel]] = {
    "data25": AsyncJobViewV1,
    "data25_child": AsyncJobChildViewV1,
    "data24": ExactContentReviewCommandV1,
    "provider_copy": ProviderCopyLifecycleReportV1,
}


def _files(group: str, kind: str) -> list[Path]:
    return sorted((FIXTURES / group / kind).glob("*.json"))


def test_fixture_manifest_hashes_match_files() -> None:
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["synthetic_only"] is True
    assert manifest["schema_version"] == "0.1-candidate"
    for path, digest in manifest["files"].items():
        assert sha256((FIXTURES / path).read_bytes()).hexdigest() == digest, path
    on_disk = {
        p.relative_to(FIXTURES).as_posix() for p in FIXTURES.rglob("*.json")
    } - {"MANIFEST.json"}
    assert on_disk == set(manifest["files"])


@pytest.mark.parametrize(
    ("group", "path"),
    [(g, p) for g in GROUPS for p in _files(g, "positive")],
    ids=lambda v: v if isinstance(v, str) else v.stem,
)
def test_positive_fixtures_validate_strictly(group: str, path: Path) -> None:
    GROUPS[group].model_validate_json(path.read_bytes(), strict=True)


@pytest.mark.parametrize(
    ("group", "path"),
    [(g, p) for g in GROUPS for p in _files(g, "negative")],
    ids=lambda v: v if isinstance(v, str) else v.stem,
)
def test_negative_fixtures_are_rejected(group: str, path: Path) -> None:
    with pytest.raises(ValidationError):
        GROUPS[group].model_validate_json(path.read_bytes(), strict=True)


def test_every_data25_state_has_a_positive_fixture() -> None:
    states = {
        json.loads(p.read_bytes())["state"] for p in _files("data25", "positive")
    }
    assert states == {"queued", "running", "succeeded", "failed_retryable", "failed_exhausted",
                      "blocked_unsafe", "cancelled"}


def test_data25_round_trip_serialises_utc_and_is_stable() -> None:
    raw = (FIXTURES / "data25/positive/succeeded_accepted.json").read_bytes()
    model = AsyncJobViewV1.model_validate_json(raw, strict=True)
    dumped = model.model_dump(mode="json")
    assert dumped == json.loads(raw)
    assert dumped["created_at"].endswith("Z")
    plus7 = json.loads(raw)
    plus7["created_at"] = "2026-10-14T20:00:00+07:00"
    assert AsyncJobViewV1.model_validate_json(json.dumps(plus7)).model_dump(mode="json")[
        "created_at"
    ] == (
        "2026-10-14T13:00:00Z"
    )


@pytest.mark.parametrize(
    "progress",
    [
        {"kind": "unknown", "value": 0, "stage_label": None},
        {"kind": "percentage", "value": None, "stage_label": None},
        {"kind": "percentage", "value": 100.01, "stage_label": None},
        {"kind": "stages", "value": None, "stage_label": None},
        {"kind": "eta", "value": None, "stage_label": None},
    ],
)
def test_progress_schema_rejects_fabricated_or_malformed_values(
    progress: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        JobProgressV1.model_validate_json(json.dumps(progress), strict=True)


def test_progress_schema_accepts_truthful_values() -> None:
    for payload in ({"kind": "unknown", "value": None, "stage_label": None},
                    {"kind": "percentage", "value": 0, "stage_label": None},
                    {"kind": "stages", "value": None, "stage_label": "outline"}):
        JobProgressV1.model_validate_json(json.dumps(payload), strict=True)


def test_completion_claim_is_internal_worker_contract() -> None:
    claim = {
        "job_id": "job_fx0001", "attempt_id": "att_fx0001", "expected_request_revision": 1,
        "input_hash": "a" * 64, "context_revision": 1, "kind": "success",
        "outputs": [{"artifact_ref": "artifact_fx0001", "sha256": "b" * 64}],
        "moderation": "passed",
    }
    model = JobCompletionClaimV1.model_validate_json(json.dumps(claim), strict=True)
    assert model.transport == "internal_worker_port"
    for bad in ({**claim, "kind": "failure"}, {**claim, "failure_code": "PROVIDER_ERROR"},
                {**claim, "callback_url": "https://x.invalid"}):
        with pytest.raises(ValidationError):
            JobCompletionClaimV1.model_validate_json(json.dumps(bad), strict=True)


def test_error_envelope_shape_and_catalogue() -> None:
    error = CollaborationErrorV1.model_validate_json(json.dumps({
        "contract_name": "CollaborationError", "contract_version": "1.0-proposed",
        "correlation_id": "corr_1",
        "error": {"code": "RESOURCE_NOT_FOUND", "message": "Resource not found.",
                  "retryable": False, "field_errors": [], "current_revisions": None,
                  "next_actions": []},
    }), strict=True)
    assert error.error.code == "RESOURCE_NOT_FOUND"
    catalogue = json.loads((FIXTURES / "error_catalogue.json").read_bytes())
    assert catalogue["http_errors"]["IDEMPOTENCY_PAYLOAD_MISMATCH"] == 409
    assert catalogue["internal_worker_errors"] == {"WORKER_CAPABILITY_INVALID": 403,
                                                   "COMPLETION_CONFLICT": 409}


def test_named_fixture_policies_are_marked_proposed() -> None:
    for path in sorted((FIXTURES / "policies").glob("*.json")):
        policy = json.loads(path.read_bytes())
        assert policy["status"] == "PROPOSED", path.name


def test_data24_record_and_owner_metadata() -> None:
    ExactContentReviewRecordV1.model_validate_json(json.dumps({
        "review_id": "review_fx_1", "review_revision": 1, "reviewer_principal_id": "teacher_1",
        "reviewed_at": "2026-10-14T13:00:00Z", "policy_version": "policy_fx_v1",
        "state": "stale",
    }), strict=True)
    with pytest.raises(ValidationError):
        ExactContentReviewRecordV1.model_validate_json(json.dumps({
            "review_id": "r", "review_revision": 1, "reviewer_principal_id": "t",
            "reviewed_at": "2026-10-14T13:00:00Z", "policy_version": "p", "state": "approved",
        }), strict=True)
    assert FULL_SCHEMA_IDS == {"DATA-24": "ExactContentReviewCommandV1",
                               "DATA-25": "AsyncJobViewV1"}


def test_provider_copy_report_never_claims_actual_deletion_from_fixtures() -> None:
    report = ProviderCopyLifecycleReportV1.model_validate_json(
        (FIXTURES / "provider_copy/positive/fixture_scope_purge.json").read_bytes(), strict=True
    )
    assert (report.contract_owner, report.fake_support_owner) == ("BE2-14", "BE2-01")
    assert report.fixture_marker and not any(c.actual_deletion_proven for c in report.copies)
    labels = {c.copy_id: c.report_label for c in report.copies}
    assert labels["copy_fx001"] == "fixture_deleted_not_actual"
    assert {labels[k] for k in ("copy_fx002", "copy_fx003", "copy_fx004", "copy_fx005")} == {
        "pending", "unsupported", "exception"
    }
    assert labels["copy_fx_late"] == "purge_requested"


@pytest.mark.parametrize("data_id", sorted(SHAPE_SPECS))
def test_shape_fixtures_for_other_cards(data_id: str) -> None:
    spec = SHAPE_SPECS[data_id]
    assert spec.contract_version == "0.1-candidate" and spec.owner_card.startswith("BE2-")
    positive = json.loads((FIXTURES / f"shapes/positive/{data_id}.json").read_bytes())
    negative = json.loads((FIXTURES / f"shapes/negative/{data_id}.json").read_bytes())
    assert check_shape(data_id, positive) == []
    assert check_shape(data_id, negative["payload"]) != []
    assert check_shape(data_id, []) == ["payload must be an object"]


def test_shape_pack_covers_requested_data_ids() -> None:
    covered = set(SHAPE_SPECS) | set(FULL_SCHEMA_IDS)
    assert covered == {f"DATA-{n}" for n in (21, 22, 23, 24, 25, 26, 27, 28, 29, 33)}


def test_consumer_poll_example_is_valid_and_ordered() -> None:
    example = json.loads((FIXTURES / "consumer_examples/p1_job_poll_sequence.json").read_bytes())
    steps = example["sequence"]
    assert steps[0]["step"] == "queued"
    for step in steps:
        body = step["body"]
        model = AsyncJobChildViewV1 if body["contract_name"] == "AsyncJobChildView" else (
            AsyncJobViewV1
        )
        model.model_validate_json(json.dumps(body["data"]), strict=True)
        assert step["etag"].startswith('"job:')
