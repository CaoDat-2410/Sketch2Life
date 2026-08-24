from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "README.md",
    ".env.example",
    "compose.yaml",
    "package.json",
    "pnpm-workspace.yaml",
    "pnpm-lock.yaml",
    "backend/pyproject.toml",
    "apps/mobile/package.json",
    "packages/art-renderer/package.json",
    "docs/context/PROJECT_CONTEXT.md",
    "docs/context/SOURCE_REGISTER.md",
    "docs/architecture/OVERVIEW.md",
    "docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md",
    "docs/architecture/REACT_NATIVE_ARCHITECTURE.md",
    "docs/architecture/CONTRACTS_AND_INTEGRATION.md",
    "docs/context/CONTEXT_MANAGEMENT.md",
    "docs/governance/WORKFLOW.md",
    "docs/governance/FRONTEND_ASSET_GATE.md",
    "docs/governance/EVIDENCE_MANAGEMENT.md",
    "docs/setup/LOCAL_DEVELOPMENT.md",
    "docs/setup/PROJECT_SKELETON.md",
    "docs/setup/SYSTEM_QUESTIONS.md",
    "tools/validate_skeleton.py",
    "tools/validate_architecture.py",
    "tools/new_feature.py",
    "features/README.md",
    "features/FEAT-000-harness/plan/PLAN.md",
    "features/FEAT-000-harness/approvals/TASK_APPROVAL.md",
]


def frontmatter_value(path: Path, key: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"(?mi)^-\s*{re.escape(key)}:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def validate_asset_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    status = data.get("status")
    review = data.get("review") or {}
    applied_path = data.get("applied_path")
    if applied_path and review.get("status") != "APPROVED":
        errors.append(f"{path}: applied_path requires review.status=APPROVED")
    if status == "APPLIED" and review.get("status") != "APPROVED":
        errors.append(f"{path}: APPLIED requires an approved review")
    if review.get("status") == "APPROVED":
        for field in ("reviewer", "reviewed_at"):
            if not review.get(field):
                errors.append(f"{path}: approved asset is missing review.{field}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Sketch2Life project harness")
    parser.add_argument("--feature", help="Validate one feature folder in addition to the repository")
    args = parser.parse_args()

    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")

    feature_root = ROOT / "features"
    for feature in sorted(feature_root.glob("FEAT-*") if feature_root.exists() else []):
        plan = feature / "plan" / "PLAN.md"
        approval = feature / "approvals" / "TASK_APPROVAL.md"
        evidence = feature / "evidence"
        required_feature_paths = [
            feature / "CONTEXT.md",
            feature / "DECISIONS.md",
            plan,
            approval,
            evidence / "README.md",
            evidence / "raw",
            evidence / "screenshots",
            evidence / "metrics",
            evidence / "notes",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required_feature_paths if not path.exists()]
        if missing:
            errors.append(f"{feature.relative_to(ROOT)}: missing harness paths: {', '.join(missing)}")
        if (
            plan.exists()
            and frontmatter_value(plan, "Implementation status") in {"IN_PROGRESS", "DONE"}
            and (not approval.exists() or frontmatter_value(approval, "Status") != "APPROVED")
        ):
            errors.append(f"{feature.relative_to(ROOT)}: implementation status requires approved task record")
        for manifest in feature.rglob("*.asset.json"):
            try:
                errors.extend(validate_asset_manifest(manifest))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{manifest}: invalid asset manifest ({exc})")

    if args.feature:
        selected = (ROOT / args.feature).resolve()
        features_root = (ROOT / "features").resolve()
        if not selected.is_relative_to(features_root):
            errors.append("--feature must point inside features/")
        elif not selected.exists():
            errors.append(f"feature does not exist: {args.feature}")

    if errors:
        print("HARNESS_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("HARNESS_VALID")
    print(f"root={ROOT}")
    print("approval_gate=enabled")
    print("frontend_asset_gate=enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
