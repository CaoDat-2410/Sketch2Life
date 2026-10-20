"""Verify portable historical evidence without importing the application or installing anything."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FEATURE = ROOT / "features/FEAT-056-be2-knowledge-script"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_safe_relative(relative: str) -> None:
    assert relative and not Path(relative).is_absolute(), relative
    assert ".." not in Path(relative).parts and not re.match(r"^[A-Za-z]:", relative), relative


def junit_cases(path: Path) -> tuple[dict[str, str], dict[str, int]]:
    tree = ET.parse(path).getroot()
    result: dict[str, str] = {}
    counts = {"collected": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for suite in tree.iter("testsuite"):
        assert "hostname" not in suite.attrib, "hostname must be removed from export"
    for case in tree.iter("testcase"):
        key = case.attrib["classname"] + "::" + case.attrib["name"]
        assert key not in result, f"duplicate JUnit identity: {key}"
        status = "passed"
        if case.find("error") is not None:
            status = "errors"
        elif case.find("failure") is not None:
            status = "failed"
        elif case.find("skipped") is not None:
            status = "skipped"
        result[key] = status
        counts[status] += 1
        counts["collected"] += 1
    return result, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-commit", help="Also require the current Git HEAD to equal this commit."
    )
    args = parser.parse_args()
    if not __debug__:
        parser.error("Python optimization disables required checks; rerun without -O or -OO.")
    provenance = read_json(HERE / "EXPORT_PROVENANCE.json")
    entries = provenance["exported_files"]
    for relative, expected in entries.items():
        assert_safe_relative(relative)
        content = (HERE / relative).read_bytes()
        assert len(content) == expected["export_bytes"], f"export size mismatch: {relative}"
        assert sha(content) == expected["export_sha256"], f"export hash mismatch: {relative}"
        # Fail for machine paths even where the project scanner's narrower rule would allow them.
        text = content.decode("utf-8")
        assert not re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", text), relative
        assert not re.search(r"(?:^|[\s'\"])/(?:Users|home)/[^/\s]+/", text), relative
    assert (HERE / "batch/source-before.json").read_bytes() == (
        HERE / "batch/source-after.json"
    ).read_bytes()
    original_manifest = read_json(HERE / "batch/source-before.json")
    assert len(original_manifest) == 601
    assert (
        sha((HERE / "batch/source-before.json").read_bytes())
        == provenance["historical_snapshot_sha256"]
    )

    pins = read_json(HERE / "current-product-pins.json")
    assert len(pins["product_source_and_tests"]) == 16
    for group in ["product_source_and_tests", "example_and_frozen_authorization"]:
        for relative, expected in pins[group].items():
            assert_safe_relative(relative)
            content = (ROOT / relative).read_bytes()
            assert sha(content) == expected["sha256"], f"reviewed current file changed: {relative}"
            assert len(content) == expected["bytes"], relative
            if relative in original_manifest:
                assert expected == original_manifest[relative], (
                    f"pin did not originate in historical snapshot: {relative}"
                )
    original_approval = "features/FEAT-056-be2-knowledge-script/approvals/TASK_APPROVAL.md"
    assert (
        pins["example_and_frozen_authorization"][original_approval]["sha256"]
        == "0010271d9db68dbbe8b9675021540df3e2cd420f636c0f7a8113ea9b91da2078"
    )

    selected = read_json(HERE / "batch/selected-files.json")
    profile = read_json(FEATURE / "artifacts/OFFLINE_BATCH_PROFILE.json")
    assert len(selected) == len(set(selected)) == 56
    assert set(selected) == set(profile["baseline_01_06"] + profile["required_07"])
    assert all((ROOT / path).is_file() for path in selected)
    assert len(profile["baseline_01_06"]) == 50 and len(profile["required_07"]) == 6

    cases, counts = junit_cases(HERE / "batch/junit.xml")
    summary = read_json(HERE / "batch/junit-summary.json")
    assert (
        counts
        == summary["counts"]
        == {"collected": 1587, "passed": 1584, "failed": 0, "errors": 0, "skipped": 3}
    )
    summarized = {}
    for case in summary["cases"]:
        key = case["classname"] + "::" + case["name"]
        assert key not in summarized
        summarized[key] = case["status"]
    assert summarized == cases, "export XML identities/outcomes differ from original summary"
    assert (
        summary["junit_sha256"] == provenance["exported_files"]["batch/junit.xml"]["source_sha256"]
    )
    assert sha((HERE / "batch/junit.xml").read_bytes()) != summary["junit_sha256"], (
        "sanitized XML needs its own hash"
    )

    acceptance = read_json(
        FEATURE / "evidence/metrics/ACCEPTANCE_MAP_BE207_20261020_POST_CLAUDE.json"
    )
    assert (
        sha(
            (
                FEATURE / "evidence/metrics/ACCEPTANCE_MAP_BE207_20261020_POST_CLAUDE.json"
            ).read_bytes()
        )
        == provenance["published_metric_pins"]["acceptance_map_sha256"]
    )
    rows = acceptance["rows"]
    assert len(rows) == len({row["id"] for row in rows}) == 42
    assert sum(len(row["final_junit_nodes"]) for row in rows) == 354
    for row in rows:
        assert row["status"] == row["assessment"] == "PASS_OFFLINE"
        assert len(row["executed_nodes"]) == len(row["final_junit_nodes"])
        for node in row["final_junit_nodes"]:
            assert cases.get(node) == "passed", f"missing/nonpassed map node: {row['id']} {node}"

    aggregate = read_json(HERE / "batch/checks.json")
    assert len(aggregate) == 11
    for name, receipt in aggregate.items():
        assert receipt["exit"] == 0, name
        individual = read_json(HERE / f"batch/{name}-receipt.json")
        assert receipt == individual, f"receipt differs from aggregate: {name}"
        log_meta = provenance["exported_files"][f"batch/{name}.log"]
        # Stored historical log hashes refer to the original local bytes, not sanitized derivatives.
        assert receipt["log_sha256"] == log_meta["source_sha256"], name

    mutant_summary = read_json(HERE / "mutants/SUMMARY.json")
    baseline, baseline_counts = junit_cases(HERE / "mutants/baseline/junit.xml")
    assert baseline_counts == {
        "collected": 262,
        "passed": 262,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
    }
    _, harmless_counts = junit_cases(HERE / "mutants/harmless-comment/junit.xml")
    assert harmless_counts == baseline_counts
    assert len(mutant_summary["mutants"]) == 6
    for name, expected in mutant_summary["mutants"].items():
        observed, mutated_counts = junit_cases(HERE / f"mutants/{name}/junit.xml")
        assert set(observed) == set(baseline), name
        assert (
            mutated_counts["collected"] == 262
            and mutated_counts["errors"] == mutated_counts["skipped"] == 0
        ), name
        assert (
            mutated_counts["failed"] > 0
            and expected["exit"] == 1
            and expected["killed_by_assertion"]
        ), name
        failures = {node for node, outcome in observed.items() if outcome == "failed"}
        expected_failures = set()
        for node in expected["failed_nodes"]:
            path, test = node.split("::", 1)
            expected_failures.add(path.removesuffix(".py").replace("/", ".") + "::" + test)
        assert failures == expected_failures, name
        delta = read_json(HERE / f"mutants/{name}-source.json")
        service = (ROOT / delta["changed_file"]).read_bytes()
        assert sha(service) == delta["before_sha256"], name
        old, new = delta["old"].encode(), delta["new"].encode()
        assert service.count(old) == 1, f"mutation target not unique: {name}"
        assert sha(service.replace(old, new, 1)) == delta["after_sha256"], name

    if args.expected_commit:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        assert head == args.expected_commit, "Git HEAD differs from requested review commit"
    print("PORTABLE_EVIDENCE_VALID")
    print(f"exported_files={len(entries)}")
    print("current_product_source_tests=16; example_and_frozen_authorization=3")
    print("historical_batch=1587_collected/1584_passed/3_skipped; focused07=262_passed")
    print("acceptance_map=42_rows/354_passed_node_references; killed_mutants=6")
    print("omitted_external_snapshots=NOT_VERIFIABLE_ON_CLOUD; runtime_adoption=NOT_RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
