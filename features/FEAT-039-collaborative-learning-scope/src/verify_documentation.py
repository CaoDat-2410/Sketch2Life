"""Static handoff checks for FEAT-039 documentation; no product/runtime tests."""

from __future__ import annotations

import hashlib
import json
import re
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features/FEAT-039-collaborative-learning-scope"
CANONICAL = ROOT / "features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md"
SRS = FEATURE / "artifacts/Collaborative_Learning_SRS_v3.1.md"
BACKUP = FEATURE / "artifacts/Sketch2Life_Master_SRS_v2.0_preserved_20261010.md"
EXPECTED_BACKUP = "28eb8b890d8e950fec6aa0df87f9b29851a7e41aa871c3dd6eb4205cd807801e"
BACKUP_V3 = FEATURE / "artifacts/Sketch2Life_Master_SRS_v3.0_preserved_20261010.md"
EXPECTED_BACKUP_V3 = "c69fd96ba9e5cd0ec85fcaa516c67ad73aafa02a45768dc2d93e29b7a756e2cf"


def digest(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    text = SRS.read_text(encoding="utf-8")
    canonical_text = CANONICAL.read_text(encoding="utf-8")
    if SRS.read_bytes() != CANONICAL.read_bytes():
        errors.append("canonical SRS differs from feature artifact")
    if digest(BACKUP) != EXPECTED_BACKUP:
        errors.append("preserved working-copy SRS v2.0 hash differs")
    if digest(BACKUP_V3) != EXPECTED_BACKUP_V3:
        errors.append("preserved SRS v3.0 hash differs")
    modules = re.findall(r"^\| (M\d{2}) \|", text, re.M)
    acceptance = re.findall(r"^\| (AC\d{2}) \|", text, re.M)
    functional = re.findall(r"^\| (FR\d{3}) \|", text, re.M)
    expected_modules = {f"M{i:02}" for i in range(1, 15)}
    expected_ac = {f"AC{i:02}" for i in range(1, 19)}
    expected_fr = {f"FR{i:03}" for i in range(1, 67)}
    for label, actual, expected in (
        ("modules", modules, expected_modules),
        ("acceptance", acceptance, expected_ac),
        ("functional", functional, expected_fr),
    ):
        if set(actual) != expected or len(actual) != len(expected):
            errors.append(f"{label} coverage or duplicate ID mismatch")
    for ref in re.findall(r"\bFR\d{3}\b", text):
        if ref not in expected_fr:
            errors.append(f"unknown functional reference {ref}")
    sections = re.findall(r"^## B(\d+)\.", text, re.M)
    if sections != [str(i) for i in range(1, 27)]:
        errors.append("B1-B26 section ordering or duplicate mismatch")
    cases = list(re.finditer(r"^### (UC-\d{3}) —", text, re.M))
    expected_uc = {f"UC-{i:03}" for i in range(1, 39)}
    if {m.group(1) for m in cases} != expected_uc or len(cases) != 38:
        errors.append("detailed use case coverage mismatch")
    for index, match in enumerate(cases):
        stop = cases[index + 1].start() if index + 1 < len(cases) else text.index("### B20.3")
        case_text = text[match.start():stop]
        for label in ("Actor / FR", "Preconditions", "Trigger/input", "Main flow", "Alternatives/errors", "Persistent postconditions"):
            if label not in case_text:
                errors.append(f"{match.group(1)} missing {label}")
        for suffix in ("P", "N"):
            acceptance_id = f"AT-{match.group(1)}-{suffix}"
            if acceptance_id not in case_text or not all(word in case_text for word in ("Given", "When", "Then")):
                errors.append(f"{match.group(1)} missing structured acceptance {suffix}")
    defined_at = set(re.findall(r"^- \*\*(AT-UC-\d{3}-[PN]):?\*\*", text, re.M))
    expected_at = {f"AT-{uc}-{suffix}" for uc in expected_uc for suffix in ("P", "N")}
    if defined_at != expected_at:
        errors.append("76 detailed acceptance ID declarations mismatch")
    data_ids = re.findall(r"^\*\*(DATA-\d{2})\b", text, re.M)
    command_ids = re.findall(r"^\| (CMD-\d{2}) \|", text, re.M)
    quality_ids = re.findall(r"^\| (P-NFR-\d{2}) \|", text, re.M)
    fixtures = re.findall(r"^\| (FIX-(?:UX|PRIV|GOV|NFR)-\d{2}) \|", text, re.M)
    for label, actual, expected in (
        ("logical DTO", data_ids, {f"DATA-{i:02}" for i in range(1, 36)}),
        ("route proposal", command_ids, {f"CMD-{i:02}" for i in range(1, 67)}),
        ("quality target", quality_ids, {f"P-NFR-{i:02}" for i in range(1, 18)}),
        ("fixture family", fixtures, {f"FIX-{p}-{i:02}" for p, n in (("UX", 7), ("PRIV", 5), ("GOV", 1), ("NFR", 3)) for i in range(1, n + 1)}),
    ):
        if set(actual) != expected or len(actual) != len(expected):
            errors.append(f"{label} coverage or duplicates mismatch")
        for ref in re.findall(rf"\b{re.escape(actual[0].rsplit('-', 1)[0])}-\d{{2}}\b", text) if actual else []:
            if ref not in expected and label != "fixture family":
                errors.append(f"unknown {label} reference {ref}")
    for ref in re.findall(r"\bAT-UC-\d{3}-[PN]\b", text):
        if ref not in defined_at:
            errors.append(f"undefined acceptance reference {ref}")
    for ref in re.findall(r"\bUC-\d{3}\b", text):
        if ref not in expected_uc:
            errors.append(f"undefined detailed use case {ref}")
    ui_section = text.split("## B23.", 1)[1].split("## B24.", 1)[0]
    screen_ids = re.findall(r"^\| ([CTA]\d{2}) \|", ui_section, re.M)
    expected_ui = {f"{p}{i:02}" for p, n in (("C", 10), ("T", 14), ("A", 10)) for i in range(1, n + 1)}
    if set(screen_ids) != expected_ui or len(screen_ids) != 34:
        errors.append("34-screen coverage mismatch")
    trace_section = text.split("### B26.2", 1)[1].split("### B26.3", 1)[0]
    trace_rows = re.findall(r"^\| `(FR\d{3})` \| (.+)$", trace_section, re.M)
    if {ref for ref, _ in trace_rows} != expected_fr or len(trace_rows) != 66:
        errors.append("per-FR integrated traceability mismatch")
    for ref, row in trace_rows:
        if not all(prefix in row for prefix in ("UC-", "DATA-", "CMD-")):
            errors.append(f"incomplete integrated traceability {ref}")
    for label, pattern, expected in (
        ("data", r"\bDATA-\d{2}\b", set(data_ids)),
        ("commands", r"\bCMD-\d{2}\b", set(command_ids)),
        ("use cases", r"\bUC-\d{3}\b", expected_uc),
    ):
        if set(re.findall(pattern, trace_section)) != expected:
            errors.append(f"integrated trace misses or invents {label}")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', text))
    for target in re.findall(r"\[[^\]]+\]\((#[^)]+)\)", text):
        if target[1:] not in anchors:
            errors.append(f"undefined reader-navigation anchor {target}")
    json_blocks = re.findall(r"```json\s*\n(.*?)\n```", text, re.S)
    for index, block in enumerate(json_blocks, 1):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON fixture block {index}: {exc}")
    if len(json_blocks) != 14:
        errors.append("expected 14 structured JSON examples")
    if "\ufffd" in text or text.count("```") % 2:
        errors.append("encoding replacement or unbalanced code fence")
    feature_required = (
        "CONTEXT.md", "DECISIONS.md", "plan/PLAN.md", "approvals/TASK_APPROVAL.md",
        "evidence/README.md", "evidence/raw", "evidence/screenshots",
        "evidence/metrics", "evidence/notes", "status/STATUS.md", "assets/REVIEW.md",
    )
    for ref in feature_required:
        if not (FEATURE / ref).exists():
            errors.append(f"missing own feature harness path {ref}")
    approval = (FEATURE / "approvals/TASK_APPROVAL.md").read_text(encoding="utf-8")
    if "- Status: APPROVED" not in approval or "- Plan revision: 3" not in approval:
        errors.append("documentation approval/revision mismatch")
    files = list(FEATURE.rglob("*.md")) + [CANONICAL]
    files = [file for file in files if file not in (BACKUP, BACKUP_V3)]
    link_count = 0
    for file in files:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#", "mailto:", "codex:")):
                continue
            relative = target.split("#", 1)[0].strip("<>")
            if not relative:
                continue
            resolved = (file.parent / relative).resolve()
            link_count += 1
            if not resolved.exists():
                errors.append(f"missing link {file.relative_to(ROOT)} -> {target}")
    security = runpy.run_path(str(ROOT / "tools/validate_repository_security.py"))
    own_security_errors: list[str] = []
    security_files = [file for file in FEATURE.rglob("*") if file.is_file()]
    security_files += [CANONICAL, ROOT / "docs/adr/ADR-0014-collaborative-learning-scope-replacement.md"]
    for file in security_files:
        relative = file.relative_to(ROOT).as_posix()
        if file.suffix.lower() in security["BANNED_SUFFIXES"]:
            own_security_errors.append(f"banned suffix: {relative}")
        try:
            content = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in security["CONTENT_RULES"].items():
            if pattern.search(content):
                own_security_errors.append(f"{label}: {relative}")
        for match in security["SENSITIVE_ASSIGNMENT"].finditer(content):
            value = match.group(1).strip().strip("'\"")
            if value.lower() not in security["ALLOWED_EXAMPLE_VALUES"] and not value.startswith("${"):
                own_security_errors.append(f"non-placeholder assignment: {relative}")
    errors.extend(own_security_errors)
    outcome = {
        "status": "DOCUMENTATION_VALID" if not errors else "DOCUMENTATION_INVALID",
        "date": "2026-10-10",
        "scope": "static documentation coverage/link/provenance checks only",
        "module_rows": len(modules), "source_acceptance_rows": len(acceptance),
        "functional_requirement_rows": len(functional), "local_links_checked": link_count,
        "srs_version": "3.1", "sections": len(sections),
        "detailed_use_cases": len(cases), "detailed_acceptance_criteria": len(defined_at),
        "logical_dtos": len(data_ids), "route_contract_proposals": len(command_ids),
        "screen_specifications": len(screen_ids), "quality_targets": len(quality_ids),
        "fixture_families": len(fixtures), "json_example_blocks": len(json_blocks),
        "integrated_fr_trace_rows": len(trace_rows), "srs_lines": len(text.splitlines()),
        "own_feature_harness": "VALID" if all((FEATURE / p).exists() for p in feature_required) else "INVALID",
        "canonical_sha256": digest(CANONICAL), "preserved_v2_sha256": digest(BACKUP),
        "preserved_v3_sha256": digest(BACKUP_V3),
        "canonical_text_matches": text == canonical_text,
        "new_feature_security_content": "VALID" if not own_security_errors else "INVALID",
        "errors": errors,
    }
    (FEATURE / "evidence/metrics/DOCUMENTATION_CHECK.json").write_text(
        json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
