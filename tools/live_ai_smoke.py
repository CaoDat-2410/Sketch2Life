import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test the live AI backend with synthetic fixture data."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic_data"] is True
    hashes = {}
    for source in manifest["source_media"]:
        content = (FIXTURE / source["path"]).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        assert digest == source["sha256"], source["artifact_id"]
        hashes[source["artifact_id"]] = digest
    payload = {
        "mode": "live-lightning",
        "fixture_id": manifest["fixture_id"],
        "session_id": "session-fixture-001",
        "expected_session_version": 1,
    }
    request = urllib.request.Request(
        f"{args.base_url.rstrip('/')}/v1/live-understanding",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"LIVE_SMOKE_FAILED category=transport detail={type(exc).__name__}")
        return 2
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    if result.get("status") != "PROPOSAL" or result.get("gate_a_required") is not True:
        print(f"LIVE_SMOKE_FAILED category=contract status={result.get('status')}")
        return 3
    asr = result.get("asr", {})
    vision = result.get("vision", {})
    if asr.get("status") != "SUCCEEDED" or vision.get("status") != "SUCCEEDED":
        print("LIVE_SMOKE_FAILED category=typed_provider_failure")
        return 4
    if asr.get("source_audio", {}).get("sha256") != hashes["child-narration-001"]:
        print("LIVE_SMOKE_FAILED category=audio_hash_mismatch")
        return 5
    if vision.get("source_image", {}).get("sha256") != hashes["child-drawing-001"]:
        print("LIVE_SMOKE_FAILED category=image_hash_mismatch")
        return 6
    print(
        json.dumps(
            {
                "status": result["status"],
                "gate_a_required": result["gate_a_required"],
                "proposal_label": result.get("proposal_label"),
                "request_id": result.get("request_id"),
                "asr_contract": asr.get("contract_name"),
                "vision_contract": vision.get("contract_name"),
                "provider": asr.get("provenance", {}).get("provider"),
                "model": asr.get("provenance", {}).get("model"),
                "latency_ms": latency_ms,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
