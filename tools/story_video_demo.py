"""Run the local cat story-video demo with a single, checked command.

The provider and backend must already be running. The preflight stops before
creating a session if a required local runtime is unavailable.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND = "http://127.0.0.1:8000"
PROVIDER = "http://127.0.0.1:8001"
IMAGE = Path(__file__).resolve().parents[1] / "upload" / "cat.png"
ZERO = "0" * 64
TEXTS = (
    "Mèo có ria dài bên má vì những sợi ria này rất quan trọng đối với cách chúng khám phá "
    "thế giới xung quanh. Ria không chỉ giúp mèo trông đáng yêu mà còn hoạt động như "
    "những chiếc cảm biến đặc biệt trên khuôn mặt.",
    "Ria mèo hoạt động giống như những chiếc cảm biến nhỏ. Chúng giúp mèo biết khoảng "
    "trống phía trước có đủ rộng để cơ thể đi qua hay không. Nhờ vậy, mèo có thể tránh "
    "bị mắc kẹt khi chui qua gầm bàn, hộp nhỏ hoặc những lối đi hẹp.",
    "Khi mèo di chuyển trong bóng tối hoặc nơi chật hẹp, ria còn cảm nhận chuyển động "
    "của không khí và giúp nó phát hiện vật thể ở gần. Điều này đặc biệt hữu ích khi "
    "mèo săn mồi, leo trèo hoặc khám phá một căn phòng hoàn toàn mới.",
    "Nhờ có ria, mèo có thể di chuyển an toàn hơn, săn mồi chính xác hơn và bảo vệ "
    "khuôn mặt khỏi va chạm. Vì vậy, chúng ta không nên cắt ria của mèo, bởi ria là "
    "một phần quan trọng giúp mèo hiểu và tương tác với môi trường xung quanh.",
)


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


def preflight() -> None:
    request_json(f"{BACKEND}/health")
    report = request_json(f"{PROVIDER}/v1/story-video/preflight")
    for name, check in report["checks"].items():
        print(f"{'OK' if check['ready'] else 'MISSING'} {name}: {check['detail']}", flush=True)
    if not report["ready"]:
        raise RuntimeError("Provider preflight failed; no session or job was created")
    if not IMAGE.is_file():
        raise RuntimeError(f"Image is missing: {IMAGE}")


def upload(session_id: str) -> dict:
    boundary = "----Sketch2Life" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="image"; filename="cat.png"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode() + IMAGE.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    result = request_json(
        f"{BACKEND}/v1/sessions/{session_id}/media/image",
        body,
        {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Request-ID": "upload-" + session_id,
            "X-Expected-Session-Version": "0",
            "Idempotency-Key": "upload-" + session_id,
            "X-Actor-Ref": "demo:local",
            "X-Synthetic-Non-Child-Confirmed": "true",
        },
    )
    if result.get("status") != "SUCCEEDED":
        raise RuntimeError(f"Image upload failed: {result.get('failure')}")
    return result["payload"]["source_image_ref"]


def create_job(session_id: str, image: dict) -> dict:
    package_id = "pkg-cat-demo-" + uuid.uuid4().hex[:8]
    package = {
        "contract": "ApprovedStoryPackageV1",
        "version": "1.0",
        "package_id": package_id,
        "session_id": session_id,
        "session_version": 1,
        "source_image_ref": image["artifact_ref"],
        "source_image_sha256": image["sha256"],
        "source_audio_ref": None,
        "source_audio_sha256": None,
        "locale": "vi-VN",
        "narration_profile_ref": "edge-tts:vi-VN-HoaiMyNeural",
        "target_duration_min_seconds": 40,
        "target_duration_max_seconds": 60,
        "story_script_revision": 1,
        "content_validator_version": "1.0",
        "content_validator_result": "PASSED",
        "created_at": datetime.now(UTC).isoformat(),
        "package_hash": ZERO,
    }
    refs = {
        "confirmed_understanding_ref": "understanding:cat-whiskers",
        "experience_spec_ref": "experience:story-video",
        "story_script_ref": "script:cat-whiskers-demo",
        "audience_profile_ref": "audience:children",
        "evidence_set_ref": "evidence:cat-whiskers",
        "narration_profile_sha256": ZERO,
        "approval_ref": "approval:approved",
    }
    package.update(refs)
    package.update(
        {name.replace("_ref", "_sha256"): ZERO for name in refs if name.endswith("_ref")}
    )
    segments = [
        {
            "segment_id": f"segment-{index}",
            "text": text,
            "approved_fact_ids": [f"fact-whiskers-{index}"],
            "confirmed_anchor_ids": [f"anchor-cat-{index}"],
            "scene_purpose": purpose,
        }
        for index, (text, purpose) in enumerate(
            zip(TEXTS, ("INTRO", "EXPLAIN", "DEMONSTRATE", "RECAP"), strict=True), 1
        )
    ]
    return post_json(
        f"{BACKEND}/v1/sessions/{session_id}/story-video-jobs",
        {
            "contract": "StoryVideoCreateRequestV1",
            "version": "1.0",
            "idempotency_key": "job-" + str(uuid.uuid4()),
            "package": package,
            "segments": segments,
        },
    )


def main() -> None:
    preflight()
    session_id = str(uuid.uuid4())
    created = post_json(
        f"{BACKEND}/v1/sessions",
        {
            "contract_name": "MobileWorkflowCommandV1",
            "contract_version": "1.0",
            "request_id": "create-" + session_id,
            "idempotency_key": "create-" + session_id,
            "session_id": session_id,
            "expected_session_version": 0,
            "actor_ref": "demo:local",
            "payload": {"operation": "CREATE_SESSION"},
        },
    )
    if created.get("status") != "SUCCEEDED":
        raise RuntimeError(f"Session creation failed: {created.get('failure')}")
    image = upload(session_id)
    job = create_job(session_id, image)
    status_url = f"{BACKEND}/v1/sessions/{session_id}/story-video/{job['job_id']}"
    print(f"Job: {job['job_id']}\nStatus URL: {status_url}", flush=True)

    last_stage = None
    deadline = time.monotonic() + 7500
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
            return
        time.sleep(10)
    raise RuntimeError("Polling timed out; use the printed Status URL to check later")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
