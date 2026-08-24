from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend/src/sketch2life"
MOBILE = ROOT / "apps/mobile/src"
DOMAIN_BANNED = {"fastapi", "pydantic", "sqlalchemy", "redis", "rq", "boto3", "httpx"}


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def main() -> int:
    errors: list[str] = []
    for path in (BACKEND / "domain").rglob("*.py"):
        for module in imports(path):
            if module.split(".")[0] in DOMAIN_BANNED:
                errors.append(f"domain imports framework/provider {module}: {path.relative_to(ROOT)}")

    for path in (BACKEND / "application").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "sketch2life.infrastructure" in text or "sketch2life.interfaces" in text:
            errors.append(f"application imports an outer layer: {path.relative_to(ROOT)}")

    feature_import = re.compile(r"from ['\"]@features/([^/]+)/")
    for path in (MOBILE / "features").rglob("*.ts*"):
        owner = path.relative_to(MOBILE / "features").parts[0]
        for imported in feature_import.findall(path.read_text(encoding="utf-8")):
            if imported != owner:
                errors.append(f"cross-feature private import {owner} -> {imported}: {path.relative_to(ROOT)}")

    for path in MOBILE.rglob("*.ts*"):
        text = path.read_text(encoding="utf-8")
        if "assets/generated" in text:
            errors.append(f"runtime references unapproved generated asset: {path.relative_to(ROOT)}")
        if re.search(
            r"lightning[._ -]?ai|runpod|SKETCH2LIFE_(?:LIGHTNING|RUNPOD)|AWS_ACCESS_KEY|S3_ACCESS_KEY",
            text,
            re.IGNORECASE,
        ):
            errors.append(f"mobile references forbidden AI provider boundary: {path.relative_to(ROOT)}")
        if re.search(
            r"@react-native-firebase/(?:storage|firestore|database)",
            text,
            re.IGNORECASE,
        ):
            errors.append(f"mobile references forbidden Firebase data product: {path.relative_to(ROOT)}")

    if errors:
        print("ARCHITECTURE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("ARCHITECTURE_VALID")
    print("python_dependency_direction=valid")
    print("mobile_feature_isolation=valid")
    print("frontend_asset_gate=valid")
    print("mobile_ai_boundary=valid")
    print("firebase_data_products=absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
