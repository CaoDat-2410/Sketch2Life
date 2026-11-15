from __future__ import annotations

import json
import sys
from pathlib import Path

import modal
import requests

APP_NAME = "sketch2life-srs23-language-audio-dev"
ENVIRONMENT = "dev"
EVIDENCE_DIR = Path(__file__).resolve().parent


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result: dict[str, object] = {
        "app": APP_NAME,
        "environment": ENVIRONMENT,
        "gpu_request_made": False,
        "inference_requested": False,
    }
    try:
        function = modal.Function.from_name(
            APP_NAME,
            "health-api",
            environment_name=ENVIRONMENT,
        )
        url = function.get_web_url()
        result["web_url_resolved"] = bool(url)
        if url is None:
            result.update(status="NO_WEB_URL")
        else:
            response = requests.get(f"{url.rstrip('/')}/health", timeout=60)
            result["http_status"] = response.status_code
            result["health_body"] = response.json()
            result["status"] = "HEALTH_OK" if response.ok else "HEALTH_HTTP_ERROR"
    except Exception as exc:
        result.update(
            status="HEALTH_PREFLIGHT_FAILED",
            exception_type=type(exc).__name__,
        )
    output_path = EVIDENCE_DIR / "health_preflight.json"
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "HEALTH_OK":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
