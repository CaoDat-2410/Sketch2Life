"""Bind approved BE2-07 assertions to the final offline JUnit receipt."""

from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FEATURE = ROOT / "features/FEAT-056-be2-knowledge-script"
LOCAL = FEATURE / "evidence/local"
METRICS = FEATURE / "evidence/metrics"
REQUIREMENTS = (
    *(f"P{i:02d}" for i in range(1, 11)),
    *(f"N{i:02d}" for i in range(1, 15)),
    *(f"R{i:02d}" for i in range(1, 11)),
    *(f"C{i:02d}" for i in range(1, 6)),
    *(f"X{i:02d}" for i in range(1, 4)),
)

ADDITIONAL_NODES: dict[str, tuple[str, ...]] = {
    "P03": (
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_actual_knowledge_flows_call_no_job_provider_or_network_and_invent_no_approval",
    ),
    "P06": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_exact_producer_resolve_supersession_before_event_delivery_and_recording_consumer",
    ),
    "P09": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_actual_producer_examples_are_deterministic_and_saved_artifact_json_equal",
    ),
    "P10": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_exact_producer_resolve_supersession_before_event_delivery_and_recording_consumer",
    ),
    "N07": (
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_existing_other_session_bundle_read_edit_denial_is_safe_and_scoped",
    ),
    "N13": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_actual_producer_read_withholds_tampered_storage_content[bytes]",
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_actual_producer_read_withholds_tampered_storage_content[hash]",
    ),
    "N14": (
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_actual_knowledge_flows_call_no_job_provider_or_network_and_invent_no_approval",
    ),
    "R09": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_exact_producer_resolve_supersession_before_event_delivery_and_recording_consumer",
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_exact_resolve_and_edit_are_linearized_without_event_delivery[resolve]",
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_exact_resolve_and_edit_are_linearized_without_event_delivery[edit]",
    ),
    "C03": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_actual_producer_examples_are_deterministic_and_saved_artifact_json_equal",
    ),
    "C04": (
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_actual_downstream_meaning_is_not_an_enriched_authority_adapter",
    ),
    "C05": (
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_candidate_video_pin_material_matches_pinned_consumer_shape_and_known_digest",
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_native_normalized_vectors_and_nfd_digest_difference_are_explicit",
        "backend/tests/unit/test_knowledge_bundle_adapters.py::"
        "test_candidate_pin_sources_are_exact_sorted_set_and_draft_not_pinnable",
    ),
    "X01": (
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_actual_knowledge_flows_call_no_job_provider_or_network_and_invent_no_approval",
    ),
    "X02": (
        "backend/tests/unit/test_knowledge_bundle_chain.py::"
        "test_derived_script_edits_preserve_original_facts_snapshots_and_v1_bytes",
    ),
}

POST_CLAUDE_TESTS: dict[str, tuple[str, ...]] = {
    "P04": (
        "test_unchanged_claim_resubmission_is_noop_and_mixed_edit_preserves_original_attestor",
    ),
    "P08": ("test_fact_fragment_of_longer_imagined_literal_rejects_without_writes",),
    "N02": (
        "test_tiny_imagined_literal_variants_cannot_become_facts",
        "test_full_basis_record_rejects_tiny_imagined_literal_variants",
        "test_imagined_fact_tiny_variants_reject_after_selection_removed",
        "test_fact_fragment_of_longer_imagined_literal_rejects_without_writes",
        "test_literal_overlap_token_boundaries_empty_signatures_and_diacritics",
    ),
    "N03": ("test_recalled_bundle_requires_new_bundle_with_eligible_sources",),
    "N08": ("test_edit_expected_revision_mismatch_rejects_atomically",),
    "N10": (
        "test_mutation_only_pause_preserves_current_reads_and_replay_but_denies_new_writes",
        "test_mutation_pause_preserves_every_other_current_read_and_exact_guard",
    ),
    "N11": (
        "test_unchanged_claim_resubmission_is_noop_and_mixed_edit_preserves_original_attestor",
    ),
    "N13": ("test_actual_exact_resolver_rejects_mismatched_requested_pins_without_writes",),
    "R01": ("test_recalled_bundle_requires_new_bundle_with_eligible_sources",),
    "R02": ("test_same_revision_fact_changes_deny_current_read_and_edit_without_writes",),
    "C01": (
        "test_content_action_pair_is_strict_for_each_nonready_structure",
        "test_record_producer_derives_required_content_action",
        "test_record_rejects_contradictory_readiness_action",
        "test_unavailable_record_requires_explicit_bounded_action_and_default_never_emits_it",
        "test_story_only_record_and_resolver_return_fact_section_content_action",
        "test_literal_comparison_does_not_rewrite_stored_text_or_canonical_nfc",
    ),
    "C02": ("test_corrupt_accepted_receipt_is_rejected_without_writes",),
    "C05": ("test_actual_exact_resolver_rejects_mismatched_requested_pins_without_writes",),
}

ASSERTIONS: dict[str, str] = {
    "P03": (
        "Missing and mixed missing-source selections remain zero-claim drafts; sentinels prove "
        "zero AiJobService, FakeProvider/model, and socket calls, with no invented approval fields."
    ),
    "P06": (
        "Actual current resolver returns the v1 exact export before edit and withholds the old "
        "version/hash after v2; the exported script and exact pins are asserted."
    ),
    "P09": (
        "Two actual producer flows yield equal JSON values; parsed saved artifact equals the "
        "producer value and representative version, replay, consumer, no-op, draft and recall "
        "outcomes are asserted. No byte-equality claim is made."
    ),
    "P10": (
        "The actual supersession event applies once, replay is idempotently rejected, and old, "
        "new and unrelated exact pins have the expected current state."
    ),
    "N07": (
        "A Teacher authorized only in session A receives the same safe 404/read result for an "
        "existing session-B bundle and a missing target; edit attempts leave the store unchanged."
    ),
    "N13": (
        "Actual resolver denies the superseded exact version and rejects both changed stored "
        "canonical bytes and changed stored hash, without a store write."
    ),
    "N14": (
        "Actual missing-source, sourced and child flows trigger no job/provider/model/network "
        "sentinel; no pre-render or final-video approval fields are invented."
    ),
    "R09": (
        "Actual resolve/edit operations contend on the held shared boundary "
        "in both first-operation "
        "orders; a superseded old exact export is denied before consumer delivery."
    ),
    "C03": (
        "Strict factual/story projection checks plus actual producer examples and parsed artifact "
        "JSON equality prove the response contract."
    ),
    "C04": (
        "The current DownstreamMeaning type is asserted to lack org/session/contributors/source "
        "snapshots; the enriched scoped values come only from the explicit fixture."
    ),
    "C05": (
        "Actual producer export maps to the pinned candidate consumer material and fixed digest; "
        "sorted exact source pins, consumer-native vectors and the NFD canonicalization boundary "
        "are asserted."
    ),
    "X01": (
        "The evidence runner profile_gate, collection and pytest receipts prove the frozen50 "
        "baseline plus all current07 modules ran together. The product node supports actual07 "
        "behavior; it does not freeze repository-file hashes or test inventory."
    ),
    "X02": (
        "The product node proves original trusted inputs and v1 bytes stay immutable during "
        "actual edits. Separate evidence-only invariants verify572 baseline files, tracked "
        "history, prior authorization/plan/reviews/metrics, frozen A17, main/shared worktrees, "
        "routing tails, empty index and unchanged HEAD. No permanent shared-file freeze remains "
        "in the product unit suite."
    ),
}

ASSERTIONS.update(
    {
        "P04": (
            "Actual claim edits attribute changed/new claims to their Teacher while unchanged "
            "claim-list resubmission retains the original attestor and is a no-op; mixed old/new "
            "claims keep both authors."
        ),
        "N02": (
            "Unknown/duplicate refs reject. Comparison-only NFKC/casefold/Cf and punctuation "
            "token signatures reject tiny imagined variants and reverse containment after "
            "deselection; empty signatures and unrelated token boundaries have controls. Stored "
            "text/canonical NFC stay unchanged; no semantic/paraphrase or general homoglyph claim."
        ),
        "N10": (
            "Disclosure withdrawal denies accepted replay. Mutation-only pause preserves current "
            "authorized reads/exact export and historical replay, denies unseen writes, and does "
            "not bypass any of the 14 other tested current guard families."
        ),
        "N13": (
            "Actual resolver rejects a wrong well-formed requested hash, unknown/other bundle id, "
            "wrong version, superseded pins and tampered stored bytes/hash; denies export and "
            "leaves full state/commit count unchanged."
        ),
        "R02": (
            "Each visible current guard is checked by the actual handler before its write unit; "
            "body expected revisions and same-revision audience/source-record changes reject "
            "atomically. Reads retain every current guard except mutation-only pause."
        ),
        "R03": (
            "Every queued publication stays invisible inside the held unit and drains after "
            "commit/rollback. Non-mutation revocations withhold current content afterward; queued "
            "mutation-only pause preserves eligible reads but denies subsequent unseen writes."
        ),
        "C01": (
            "Strict domain/DTO/hash vectors and unchanged canonical NFC pass. Structural "
            "readiness/action pairs are exact: no claims/NO_ELIGIBLE_SOURCE, claims without "
            "facts/FACT_SECTION_REQUIRED, ready/no action; unavailable requires an explicit "
            "bounded reason and is not emitted by the default producer."
        ),
        "C02": (
            "Actual CMD38/39 key/ETag/server guards plus stale edit expected revisions reject "
            "atomically. Replay derives expected record/readiness/action from trusted immutable "
            "version and expected status from the requested contract; corrupted response "
            "body/readiness/status is rejected."
        ),
    }
)


def _node_key(node: str) -> str:
    path, test = node.split("::", 1)
    module = path.removeprefix("backend/").removesuffix(".py").replace("/", ".")
    return f"{module}::{test}"


def finalize(run_name: str) -> Path:
    from run_execution_checks import manifest as current_manifest

    run = LOCAL / run_name
    interim = json.loads(
        (LOCAL / "reviewer-parts1-4/coverage_interim_175.json").read_text(encoding="utf-8")
    )
    junit = json.loads((run / "junit-summary.json").read_text(encoding="utf-8"))
    checks = json.loads((run / "checks.json").read_text(encoding="utf-8"))
    source_before = run / "source-before.json"
    source_after = run / "source-after.json"
    selected_files = json.loads((run / "selected-files.json").read_text(encoding="utf-8"))
    environment = json.loads((run / "environment.json").read_text(encoding="utf-8"))
    invariants = json.loads((run / "invariants.json").read_text(encoding="utf-8"))
    external_invariants = json.loads((run / "external-invariants.json").read_text(encoding="utf-8"))
    profile = json.loads((FEATURE / "artifacts/OFFLINE_BATCH_PROFILE.json").read_text())
    profile_checks = json.loads((run / "batch-profile-checks.json").read_text())
    hygiene = json.loads((run / "text-hygiene.json").read_text())
    assert profile_checks["passed"] and hygiene["passed"]
    summary = junit["counts"]
    assert checks["pytest"]["exit"] == 0
    assert checks["collection"]["exit"] == 0
    assert summary["failed"] == summary["errors"] == 0
    assert all(receipt["exit"] == 0 for receipt in checks.values())
    source_manifest = json.loads(source_before.read_text(encoding="utf-8"))
    assert source_manifest == json.loads(source_after.read_text(encoding="utf-8"))
    assert source_manifest == current_manifest(), "batch source/config/tooling changed"
    for relative, entry in source_manifest.items():
        path = ROOT / relative
        assert path.is_file() and path.stat().st_size == entry["bytes"], relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], relative
    generator = Path(__file__).resolve()
    assert source_manifest[generator.relative_to(ROOT).as_posix()]["sha256"] == hashlib.sha256(
        generator.read_bytes()
    ).hexdigest()
    assert hashlib.sha256((run / "junit.xml").read_bytes()).hexdigest() == junit["junit_sha256"]
    raw_cases = ET.parse(run / "junit.xml").findall(".//testcase")
    raw_status = {
        f"{case.get('classname')}::{case.get('name')}": next(
            (tag for tag in ("failure", "error", "skipped") if case.find(tag) is not None),
            "passed",
        )
        for case in raw_cases
    }
    stored_status = {
        f"{case['classname']}::{case['name']}": case["status"] for case in junit["cases"]
    }
    assert len(raw_status) == len(raw_cases) == len(junit["cases"])
    assert raw_status == stored_status
    assert summary == {
        "collected": len(raw_cases),
        "passed": sum(status == "passed" for status in raw_status.values()),
        "failed": sum(status == "failure" for status in raw_status.values()),
        "errors": sum(status == "error" for status in raw_status.values()),
        "skipped": sum(status == "skipped" for status in raw_status.values()),
    }
    for name, receipt in checks.items():
        assert json.loads((run / f"{name}-receipt.json").read_text()) == receipt, name
        assert hashlib.sha256((run / f"{name}.log").read_bytes()).hexdigest() == receipt[
            "log_sha256"
        ], name
        assert Path(receipt["cwd"]).resolve() == ROOT.resolve(), name
    assert profile_checks["profile_sha256"] == hashlib.sha256(
        (FEATURE / "artifacts/OFFLINE_BATCH_PROFILE.json").read_bytes()
    ).hexdigest()
    assert profile_checks["baseline_selection_sha256"] == hashlib.sha256(
        (FEATURE / profile_checks["baseline_selection_ref"]).read_bytes()
    ).hexdigest()
    assert external_invariants["external_baseline_sha256"] == hashlib.sha256(
        (FEATURE / external_invariants["external_baseline_ref"]).read_bytes()
    ).hexdigest()
    assert len(selected_files) == len(set(selected_files))
    assert len(selected_files) == len(profile["baseline_01_06"]) + len(profile["required_07"])
    assert set(selected_files) == set(profile["baseline_01_06"] + profile["required_07"])
    assert profile["final_receipt_directory"] == (
        "features/FEAT-056-be2-knowledge-script/evidence/local/" + run_name
    )
    assert invariants["baseline_backend_unchanged"] == 572
    assert invariants["staged"] == 0 and invariants["head_unchanged"]
    assert external_invariants["a17_unchanged_files"] > 0

    case_status = {
        f"{case['classname']}::{case['name']}": case["status"] for case in junit["cases"]
    }
    rows = {row["id"]: row for row in interim["rows"]}
    assert set(rows) == set(REQUIREMENTS)
    for requirement, nodes in ADDITIONAL_NODES.items():
        row = rows[requirement]
        row["executed_nodes"] = list(dict.fromkeys([*row["executed_nodes"], *nodes]))
        row["concrete_assertions"] = ASSERTIONS[requirement]
    for requirement, names in POST_CLAUDE_TESTS.items():
        found = [case for case in junit["cases"] if case["name"].split("[", 1)[0] in names]
        assert {case["name"].split("[", 1)[0] for case in found} == set(names), requirement
        nodes = [
            "backend/" + case["classname"].replace(".", "/") + ".py::" + case["name"]
            for case in found
        ]
        rows[requirement]["executed_nodes"] = list(
            dict.fromkeys([*rows[requirement]["executed_nodes"], *nodes])
        )
    for requirement, assertions in ASSERTIONS.items():
        rows[requirement]["concrete_assertions"] = assertions
    for requirement, row in rows.items():
        row["status"] = "PASS_OFFLINE"
        row["assessment"] = "PASS_OFFLINE"
        row["residual"] = ""
        mapped = [_node_key(node) for node in row["executed_nodes"]]
        assert mapped, requirement
        assert all(node in case_status for node in mapped), (requirement, mapped)
        assert all(case_status[node] == "passed" for node in mapped), requirement
        row["final_junit_nodes"] = mapped
        row["execution_kind"] = "product_tests"
        evidence_refs = [
            f"evidence/local/{run_name}/junit-summary.json",
            f"evidence/local/{run_name}/checks.json",
        ]
        if requirement == "P09":
            evidence_refs.extend(
                [
                    "artifacts/KNOWLEDGE_BUNDLE_EXAMPLES.json",
                    "evidence/local/part8-examples-generation.json",
                ]
            )
        if requirement == "X01":
            row["execution_kind"] = "evidence_gate_with_product_support"
            row["executed_checks"] = [
                "run_execution_checks.py::profile_gate",
                "collection receipt",
                "pytest receipt",
            ]
            evidence_refs.extend(
                [
                    f"evidence/local/{run_name}/selected-files.json",
                    f"evidence/local/{run_name}/collection.log",
                    f"evidence/local/{run_name}/pytest-receipt.json",
                    f"evidence/local/{run_name}/batch-profile-checks.json",
                ]
            )
        if requirement == "X02":
            row["execution_kind"] = "evidence_gate_with_product_support"
            row["executed_checks"] = [
                "run_execution_checks.py::invariants",
                "run_execution_checks.py::external_invariants",
                "run_execution_checks.py::text_hygiene",
            ]
            evidence_refs.extend(
                [
                    f"evidence/local/{run_name}/source-before.json",
                    f"evidence/local/{run_name}/source-after.json",
                    f"evidence/local/{run_name}/invariants.json",
                    f"evidence/local/{run_name}/external-invariants.json",
                    f"evidence/local/{run_name}/text-hygiene.json",
                    external_invariants["external_baseline_ref"],
                    invariants["pre_remediation_baseline_ref"],
                ]
            )
        row["evidence_refs"] = evidence_refs
        assert all(
            not Path(reference).is_absolute() and (FEATURE / reference).is_file()
            for reference in evidence_refs
        ), (requirement, evidence_refs)

    map_document = {
        "kind": "BE207_FINAL_OFFLINE_ACCEPTANCE_MAP",
        "evidence_revision": "POST_CLAUDE",
        "supersedes": "evidence/metrics/ACCEPTANCE_MAP_BE207_20261020.json",
        "approval_plan_revision": 1,
        "approval_plan_sha256": "6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36",
        "profile": "BE207_REQUIRED_OFFLINE_01_07",
        "final_run": f"evidence/local/{run_name}",
        "evidence_ref_base": "feature root",
        "source_manifest_sha256": hashlib.sha256(source_before.read_bytes()).hexdigest(),
        "junit_sha256": junit["junit_sha256"],
        "batch_counts": summary,
        "mapped_cases": {"pass": len(rows), "partial": 0, "not_run": 0},
        "rows": [rows[requirement] for requirement in REQUIREMENTS],
        "offline_limits": [
            (
                "This map proves offline fixture behavior, not component acceptance "
                "or runtime adoption."
            ),
            "The three observed Pillow live-app skips remain NOT_RUN and are not mapped as passes.",
            (
                "backend/tests/unit/test_lightning_vision_v2_server.py is excluded "
                "because collection imports missing Pillow."
            ),
            (
                "No live source/provider/database/HTTP/Lightning or actual08 held-fence "
                "execution is claimed."
            ),
            (
                "P3-4 intentional R01 limitation: recalled old bundles cannot be repaired in "
                "place; create a new bundle from eligible sources."
            ),
            (
                "Literal normalization is conservative token matching with possible short-phrase "
                "false positives; it is not semantic/paraphrase/general homoglyph detection."
            ),
            (
                "P3-6 preserves one frozen-approval trailing-blank-line exception; its exact hash "
                "is checked and all other scanned new publishable text passes hygiene."
            ),
        ],
    }
    assert map_document["mapped_cases"] == {"pass": 42, "partial": 0, "not_run": 0}
    METRICS.mkdir(parents=True, exist_ok=True)
    destination = METRICS / "ACCEPTANCE_MAP_BE207_20261020_POST_CLAUDE.json"
    metrics_destination = METRICS / "BE207_FINAL_OFFLINE_CHECKS_20261020_POST_CLAUDE.json"
    assert not destination.exists() and not metrics_destination.exists(), (
        "preserve earlier receipts"
    )
    destination.write_text(
        json.dumps(map_document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    source_manifest = json.loads(source_before.read_text(encoding="utf-8"))
    public_checks = {
        name: {
            key: receipt[key]
            for key in ("exit", "seconds", "started_utc", "ended_utc", "log_sha256")
        }
        for name, receipt in checks.items()
    }
    metrics = {
        "kind": "BE207_FINAL_OFFLINE_CHECKS",
        "evidence_revision": "POST_CLAUDE",
        "supersedes": "evidence/metrics/BE207_FINAL_OFFLINE_CHECKS_20261020.json",
        "profile": profile["profile"],
        "final_run": f"evidence/local/{run_name}",
        "source_manifest_sha256": map_document["source_manifest_sha256"],
        "acceptance_map_generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_manifest_files": len(source_manifest),
        "junit_sha256": junit["junit_sha256"],
        "junit_counts": summary,
        "mapped_acceptance_cases": map_document["mapped_cases"],
        "selected_test_files": {
            "baseline_01_06": len(profile["baseline_01_06"]),
            "required_07": len(profile["required_07"]),
            "total": len(selected_files),
            "selection_sha256": hashlib.sha256(
                (run / "selected-files.json").read_bytes()
            ).hexdigest(),
        },
        "packages": environment["packages"],
        "checks": public_checks,
        "invariants": invariants,
        "external_invariants": external_invariants,
        "batch_profile_checks": profile_checks,
        "text_hygiene": hygiene,
        "skipped_cases": [
            {
                "classname": case["classname"],
                "name": case["name"],
                "reason": case["detail"],
            }
            for case in junit["cases"]
            if case["status"] == "skipped"
        ],
        "excluded": profile["excluded"],
        "runtime_executed": False,
        "dependency_installation": False,
        "owner_component_acceptance": "NOT_ACCEPTED",
        "card_status": "IN_PROGRESS / NOT_DONE",
    }
    metrics_destination.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(destination.relative_to(FEATURE).as_posix())
    print(metrics_destination.relative_to(FEATURE).as_posix())
    print(json.dumps(map_document["mapped_cases"], ensure_ascii=False))
    print(json.dumps(summary, ensure_ascii=False))
    return destination


if __name__ == "__main__":
    raise SystemExit(0 if finalize(sys.argv[1]).is_file() else 1)
