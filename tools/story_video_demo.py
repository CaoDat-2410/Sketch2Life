"""Submit a reviewed story-video request to running backend/provider services.

The JSON file must contain ``StoryVideoCreateRequestV1`` for an existing
session and uploaded source image. This tool never fabricates approvals,
facts, hashes, source media or a child identity.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(
    url: str, data: bytes | None = None, headers: dict[str, str] | None = None
) -> dict:
    request = Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=120) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} at {url}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Cannot reach {url}: {error.reason}") from error


def post_json(url: str, payload: dict) -> dict:
    return request_json(
        url,
        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json"},
    )


def load_approved_request(path: Path) -> tuple[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("contract") != "StoryVideoCreateRequestV1":
        raise ValueError("request file must contain StoryVideoCreateRequestV1")
    package = payload.get("package")
    segments = payload.get("segments")
    if not isinstance(package, dict) or not isinstance(segments, list) or len(segments) < 3:
        raise ValueError("reviewed package and at least three script segments are required")
    session_id = package.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("approved package must contain an existing session_id")
    if package.get("content_validator_result") != "PASSED":
        raise ValueError("content validation must pass before story rendering")
    for name in ("source_image_sha256", "approval_sha256", "package_hash"):
        digest = package.get(name)
        if not isinstance(digest, str) or len(digest) != 64 or digest == "0" * 64:
            raise ValueError(f"{name} must be a real, non-placeholder SHA-256")
    return session_id, payload


def preflight(backend: str, provider: str) -> None:
    request_json(f"{backend}/health")
    report = request_json(f"{provider}/v1/story-video/preflight")
    for name, check in report["checks"].items():
        print(f"{'OK' if check['ready'] else 'MISSING'} {name}: {check['detail']}", flush=True)
    if not report["ready"]:
        raise RuntimeError("Provider preflight failed; no story job was created")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True, help="Reviewed request JSON")
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    parser.add_argument("--provider", default="http://127.0.0.1:8001")
    parser.add_argument("--timeout-seconds", type=int, default=7500)
    args = parser.parse_args(argv)

    session_id, payload = load_approved_request(args.request)
    backend = args.backend.rstrip("/")
    provider = args.provider.rstrip("/")
    preflight(backend, provider)
    job = post_json(f"{backend}/v1/sessions/{session_id}/story-video-jobs", payload)
    status_url = f"{backend}/v1/sessions/{session_id}/story-video/{job['job_id']}"
    print(f"Job: {job['job_id']}\nStatus URL: {status_url}", flush=True)

    last_stage = None
    deadline = time.monotonic() + args.timeout_seconds
    while time.monotonic() < deadline:
        status = request_json(status_url)
        if status.get("stage") != last_stage:
            print(json.dumps(status, ensure_ascii=False), flush=True)
            last_stage = status.get("stage")
        if status.get("state") in {
            "READY", "FAILED", "BLOCKED", "RETRYABLE_FAILURE", "CANCELLED", "EXPIRED"
        }:
            if status["state"] != "READY":
                raise RuntimeError(f"Job stopped: {status['public_message']}")
            artifact = status.get("video_artifact_ref")
            if not artifact:
                raise RuntimeError("Job reported READY without a downloadable MP4")
            print(f"MP4: {artifact}", flush=True)
            return
        time.sleep(10)
    raise RuntimeError("Polling timed out; use the printed Status URL to check later")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
