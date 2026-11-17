from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import requests

FEATURE = Path(__file__).resolve().parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103"
RESULT = ASSET_DIR / "storyrun_recovery_seed.json"
BASE_URL = "http://127.0.0.1:8002"


def main() -> int:
    if RESULT.exists():
        raise SystemExit("Recovery run creation already attempted; refusing to send again.")
    started_at = datetime.now().astimezone().isoformat()
    start = time.perf_counter()
    try:
        response = requests.post(
            f"{BASE_URL}/v1/story-runs",
            headers={"Idempotency-Key": "parent-generated-image-aligned-run-20261103"},
            json={"profile_ref": "synthetic-parent-demo"},
            timeout=15,
        )
    except requests.RequestException as exc:
        RESULT.write_text(
            json.dumps(
                {
                    "started_at": started_at,
                    "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                    "transport_outcome": "UNKNOWN_NO_RETRY",
                    "exception_type": type(exc).__name__,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise SystemExit("Run creation outcome unknown; no retry sent.") from None
    try:
        body = response.json()
    except ValueError:
        body = {"body_prefix": response.text[:500]}
    record = {
        "started_at": started_at,
        "ended_at": datetime.now().astimezone().isoformat(),
        "method": "POST",
        "path": "/v1/story-runs",
        "http_status": response.status_code,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
        "headers": {
            key: response.headers[key]
            for key in ("ETag", "Location", "X-Correlation-ID")
            if key in response.headers
        },
        "response": body,
    }
    RESULT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=True))
    if response.status_code != 201:
        raise SystemExit(f"Replacement run creation failed: HTTP {response.status_code}; no further run creation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
