from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a feature harness folder")
    parser.add_argument("number", type=int)
    parser.add_argument("slug")
    args = parser.parse_args()

    slug = args.slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        parser.error("slug must be lowercase kebab-case")

    destination = ROOT / "features" / f"FEAT-{args.number:03d}-{slug}"
    if destination.exists():
        parser.error(f"feature already exists: {destination.relative_to(ROOT)}")

    shutil.copytree(ROOT / "features/_template", destination)
    print(f"FEATURE_CREATED={destination.relative_to(ROOT)}")
    print("STATUS=AWAITING_APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
