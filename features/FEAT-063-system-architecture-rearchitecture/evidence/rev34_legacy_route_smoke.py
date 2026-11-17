"""Safe dispatch-only smoke for active legacy non-AI API operations.

Requests intentionally omit credentials and valid mutation bodies. A 4xx is an
expected rejection for this smoke; a 5xx is reported as a dispatch failure.
This does not establish business-flow correctness.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from sketch2life.interfaces.http.app import create_app  # noqa: E402

CATALOG = (
    ROOT
    / "features"
    / "FEAT-063-system-architecture-rearchitecture"
    / "artifacts"
    / "API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md"
)
RESULTS = Path(__file__).with_name("REV34_LEGACY_ROUTE_SMOKE_20261029.csv")
LEGACY_SURFACES = {"BE1 / classroom", "Demo / local flow"}
AI_ROUTE_IDS = {57, 58, 59, 60, 61, 64, 65, 66, 67, 82, 87, 89, 90, 91}


def catalog_routes() -> list[tuple[int, str, str, str]]:
    routes: list[tuple[int, str, str, str]] = []
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        fields = [value.strip() for value in line.strip("|").split("|")]
        if len(fields) < 6 or not fields[0].isdigit():
            continue
        route_id = int(fields[0])
        surface = fields[1]
        if surface not in LEGACY_SURFACES or route_id in AI_ROUTE_IDS:
            continue
        method = fields[3].strip("`").upper()
        path = fields[4].strip("`")
        routes.append((route_id, method, path, surface))
    return routes


def safe_path(template: str) -> str:
    return re.sub(r"\{[^{}]+\}", lambda _: str(uuid4()), template)


def main() -> int:
    routes = catalog_routes()
    if len(routes) != 77:
        raise SystemExit(f"Unexpected legacy non-AI route count: {len(routes)}")

    outcomes: list[dict[str, object]] = []
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        for route_id, method, template, surface in routes:
            path = safe_path(template)
            response = client.request(method, path)
            outcomes.append(
                {
                    "catalog_id": route_id,
                    "surface": surface,
                    "method": method,
                    "path": template,
                    "smoke_status": response.status_code,
                    "result": "HTTP_5XX" if response.status_code >= 500 else "HTTP_RESPONSE",
                }
            )

    with RESULTS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(outcomes[0]))
        writer.writeheader()
        writer.writerows(outcomes)

    counts = Counter(str(item["result"]) for item in outcomes)
    print(f"active_legacy_non_ai_routes={len(outcomes)}")
    print(f"http_responses={counts['HTTP_RESPONSE']}")
    print(f"http_5xx={counts['HTTP_5XX']}")
    print(f"route_matrix={RESULTS}")
    for item in outcomes:
        if item["result"] == "HTTP_5XX":
            print(
                f"FAIL {item['catalog_id']} {item['method']} {item['path']} "
                f"=> {item['smoke_status']}"
            )
    return 1 if counts["HTTP_5XX"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
