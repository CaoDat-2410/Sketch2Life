"""Meaningful offline-harness checks; full requirements remain independently open."""

from __future__ import annotations

import json
import socket
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import pytest

from sketch2life.benchmark import feat018_p2_t5_evaluation as evaluation
from sketch2life.infrastructure.ai.lightning_client import UrllibJsonTransport

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / (
    "features/FEAT-018-live-image-canvas-flow/fixtures/"
    "feat018-p2-t5-evaluation-manifest-v1.json"
)
HEAD = "b11bc7b870f615e493afb1bc723b888befdb58c9"


@pytest.fixture(scope="module")
def report() -> dict[str, Any]:
    return evaluation.evaluate_manifest(
        MANIFEST, repo_root=ROOT, source_head=HEAD,
        run_id="feat018-p2-t5-offline-unit-report",
        scratch_dir=ROOT / "backend/.pytest-tmp-feat018-p2t5-unit-report",
    )


def _by_kind(report: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [probe for row in report["results"] for probe in row["subprobes"]
            if probe["kind"] == kind]


def test_primary_matrix_execution_does_not_claim_full_acceptance(report: dict[str, Any]) -> None:
    assert report["execution_status"] == "SUCCEEDED"
    assert report["summary"]["primary_slots"] == 120
    assert report["summary"]["primary_execution_counts"] == {
        "SUCCEEDED": 100, "NOT_EXECUTED": 20,
    }
    assert report["summary"]["held_counted_as_coverage"] == 0
    assert report["summary"]["satisfied_full_acceptance_count"] == 0
    assert set(report["requirements"].values()) == {"OPEN"}
    assert report["task_status"] == "OPEN"
    for row in report["results"]:
        assert row["requirement_status"] in {"OPEN", "HELD"}
        assert row["evidence_id"] == f"P2T5:{row['fixture_id']}"
        if row["family"] == "adult-correction":
            assert row["execution_status"] == "NOT_EXECUTED"
            assert row["requirement_status"] == "HELD"


def test_successful_subprobes_keep_truthful_source_and_gate_a(report: dict[str, Any]) -> None:
    for kind in ("map_exact", "map_ambiguous", "map_unknown_label", "map_low_confidence"):
        probes = _by_kind(report, kind)
        assert len(probes) == 20
        for probe in probes:
            assert probe["execution_status"] == "SUCCEEDED"
            assert probe["metadata"]["gate_a_required"] is True
            assert probe["metadata"]["eligibility_computed"] is False
            assert probe["metadata"]["numeric_confidence_preserved"] is True
    for probe in _by_kind(report, "map_asr_present"):
        assert probe["metadata"]["asr_claim_count"] == 1
    for kind, expected in (("asr_missing", "NOT_SUPPLIED"), ("asr_failure", "ASR_FAILED")):
        probe = _by_kind(report, kind)[0]
        assert probe["metadata"]["narration_status"] == expected
        assert probe["metadata"]["asr_claim_count"] == 0
        assert probe["metadata"]["fabricated_text"] is False


def test_held_oserror_route_is_never_called_or_credited(report: dict[str, Any]) -> None:
    for kind in evaluation.HELD_KINDS:
        probes = _by_kind(report, kind)
        assert probes
        for probe in probes:
            assert probe["execution_status"] == "NOT_EXECUTED"
            assert probe["requirement_status"] == "HELD"
            assert "metadata" not in probe
    terminal = _by_kind(report, "vision_terminal_retry_fixture")[0]
    assert terminal["metadata"]["attempt_number"] == 2
    assert terminal["metadata"]["retry_execution_proven"] is False
    assert terminal["metadata"]["fake_transport_calls"] == 0


@pytest.mark.parametrize("kind", [
    "reject_malformed", "reject_prohibited", "reject_extra_field",
    "reject_missing_provenance", "reject_source_hash", "reject_dangling_reference",
    "reject_null_confidence",
])
def test_negative_inputs_are_rejected_without_defaulting_confidence(
    report: dict[str, Any], kind: str,
) -> None:
    probes = _by_kind(report, kind)
    assert probes
    assert all(probe["execution_status"] == "SUCCEEDED" for probe in probes)
    assert all(probe["metadata"]["rejection_observed"] is True for probe in probes)
    assert all(probe["metadata"]["default_confidence_fabricated"] is False for probe in probes)


def test_prohibited_typed_fixtures_map_without_claiming_policy_execution(
    report: dict[str, Any],
) -> None:
    metadata = _by_kind(report, "reject_prohibited")[0]["metadata"]
    assert metadata["rejection_observed"] is True
    assert metadata["typed_policy_fixture_count"] == 6
    assert metadata["raw_failure_code"] == "PROHIBITED_FIELD"
    assert metadata["raw_detail"] == "PROHIBITED_CLAIM"
    assert metadata["policy_execution_proven"] is False
    assert report["requirements"]["T5-A4"] == "OPEN"


@pytest.mark.parametrize("kind,code,http_status", [
    ("rate_limit_characterization", "RATE_LIMITED", 429),
    ("provider_error_characterization", "PROVIDER_ERROR", 503),
])
def test_characterization_preserves_current_asymmetry_without_resolving_acceptance(
    report: dict[str, Any], kind: str, code: str, http_status: int,
) -> None:
    probe = _by_kind(report, kind)[0]
    metadata = probe["metadata"]
    assert probe["execution_status"] == "SUCCEEDED"
    assert metadata["shared_error_code"] == code
    assert metadata["injected_http_status"] == http_status
    assert metadata["vision_detail"] == "PERMANENT_RUNTIME_FAILURE"
    assert metadata["vision_retryable"] is False
    assert metadata["asr_detail"] == "TRANSIENT_RUNTIME_FAILURE"
    assert metadata["asr_retryable"] is True
    assert metadata["raw_vision_code"] == metadata["raw_asr_code"] == "PROVIDER_ERROR"
    assert metadata["fake_transport_calls"] == 2
    assert metadata["real_provider_calls"] == 0
    assert metadata["task_acceptance_resolved"] is False
    row = next(row for row in report["results"] if probe in row["subprobes"])
    assert row["requirement_status"] == "HELD"


def test_quality_reference_admission_service_and_http_proof_are_separate(
    report: dict[str, Any],
) -> None:
    for kind, reasons in (("quality_valid", []), ("quality_dark", ["IMAGE_TOO_DARK"]),
                          ("quality_blur", ["IMAGE_BLURRY"]),
                          ("quality_crop", ["IMAGE_FRAMING_RISK"])):
        metadata = _by_kind(report, kind)[0]["metadata"]
        assert metadata["reason_codes"] == reasons
        assert metadata["evidence_boundary"] == "QUALITY_VALIDATOR_REFERENCE_WITH_INJECTED_SIGNALS"
        assert metadata["http_admission_proven"] is False
        assert metadata["decoder_quality_proven"] is False
    for kind, outcome in (("admission_valid", "ADMITTED"),
                          ("admission_corrupt", "INVALID_SOURCE"),
                          ("admission_unsupported", "UNSUPPORTED"),
                          ("admission_oversized", "REJECTED")):
        metadata = _by_kind(report, kind)[0]["metadata"]
        assert metadata["outcome"] == outcome
        assert metadata["evidence_boundary"] == "IMAGE_ADMISSION_SERVICE_WITH_PYAV"
        assert metadata["source_preserved"] is True
        assert metadata["http_admission_proven"] is False
        assert metadata["quality_validation_proven"] is False


def test_report_is_sanitized_candidate_evidence_not_a_live_or_clean_worktree_claim(
    report: dict[str, Any],
) -> None:
    encoded = json.dumps(report, ensure_ascii=False)
    manifest = evaluation.load_manifest(MANIFEST, ROOT)
    for row in manifest["profiles"]:
        assert row["recipe"]["exact_phrase"] not in encoded
    for forbidden in ("synthetic narration", "synthetic observation", str(ROOT),
                      "transcript_raw", "content_base64", "Authorization", "clean_worktree"):
        assert forbidden not in encoded
    assert report["source_head"] == HEAD
    assert report["source_state"] == "candidate"
    assert report["source_identity_type"] == "BASELINE_HEAD_PLUS_CANDIDATE_DIGESTS"
    assert report["provider_execution"] == report["model_execution"] == "NOT_EXECUTED"
    assert report["live_metrics"] == "NOT_MEASURED"
    assert report["guard"]["blocked_attempts"] == 0
    assert all(len(item["sha256"]) == 64 for item in report["candidate_file_digests"])


def test_source_validation_happens_before_probes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = deepcopy(evaluation.load_manifest(MANIFEST, ROOT))
    manifest["contract_locks"][0]["sha256"] = "0" * 64
    candidate = tmp_path / "bad.json"
    candidate.write_text(json.dumps(manifest), encoding="utf-8")

    def must_not_execute(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        pytest.fail("probe executed before source validation")

    monkeypatch.setattr(evaluation, "_probe", must_not_execute)
    with pytest.raises(evaluation.ManifestError, match="CONTRACT_LOCK_MISMATCH"):
        evaluation.evaluate_manifest(candidate, repo_root=ROOT, source_head=HEAD,
                                     run_id="feat018-p2-t5-offline-invalid")


def test_ordinary_and_internal_failures_never_become_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_probe(kind: str, _phrase: str, _scratch: Path) -> dict[str, Any]:
        if kind == "map_exact":
            raise AssertionError("synthetic mismatch")
        raise TypeError("SENSITIVE_RAW_MESSAGE_MUST_NOT_BE_SERIALIZED")

    monkeypatch.setattr(evaluation, "_probe", broken_probe)
    result = evaluation.evaluate_manifest(MANIFEST, repo_root=ROOT, source_head=HEAD,
                                          run_id="feat018-p2-t5-offline-broken")
    assert result["execution_status"] == "FAILED"
    assert result["summary"]["execution_counts"]["FAILED"] == 20
    assert result["summary"]["execution_counts"]["INTERNAL_ERROR"] > 0
    assert "SENSITIVE_RAW_MESSAGE" not in json.dumps(result)
    assert set(result["requirements"].values()) == {"OPEN"}


@pytest.mark.parametrize("route", ["socket", "urlopen", "subprocess", "transport"])
def test_unexpected_egress_and_process_calls_fail_closed(route: str) -> None:
    with evaluation.offline_guards() as guard:
        with pytest.raises(evaluation.OfflineAccessError, match="OFFLINE_ACCESS_REFUSED"):
            if route == "socket":
                socket.create_connection(("127.0.0.1", 1))
            elif route == "urlopen":
                # urllib's opening function may already be imported; socket guard is a backstop.
                urlopen("http://127.0.0.1:1/", timeout=0.01)  # noqa: S310
            elif route == "subprocess":
                subprocess.Popen(["unexpected-command"])
            else:
                UrllibJsonTransport("http://127.0.0.1", "").post_json("/offline", {})
        assert guard.blocked_attempts == 1


@pytest.mark.parametrize("head,state,run_id", [
    ("invalid", "candidate", "feat018-p2-t5-offline-invalid"),
    (HEAD, "committed", "feat018-p2-t5-offline-invalid"),
    (HEAD, "candidate", "unbound-run"),
    ("0" * 40, "candidate", "feat018-p2-t5-offline-wrong-head"),
])
def test_unbound_or_misleading_source_identity_is_rejected(
    head: str, state: str, run_id: str,
) -> None:
    with pytest.raises(evaluation.ManifestError):
        evaluation.evaluate_manifest(MANIFEST, repo_root=ROOT, source_head=head,
                                     run_id=run_id, source_state=state)
