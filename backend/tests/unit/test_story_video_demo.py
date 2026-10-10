from __future__ import annotations

import json

import pytest
from tools.story_video_demo import load_approved_request


def _payload() -> dict:
    return {
        "contract": "StoryVideoCreateRequestV1",
        "package": {
            "session_id": "session-test",
            "content_validator_result": "PASSED",
            "source_image_sha256": "a" * 64,
            "approval_sha256": "b" * 64,
            "package_hash": "c" * 64,
        },
        "segments": [{"segment_id": f"segment-{index}"} for index in range(1, 4)],
    }


def test_demo_loader_uses_existing_reviewed_request(tmp_path) -> None:
    path = tmp_path / "request.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    session_id, payload = load_approved_request(path)
    assert session_id == "session-test"
    assert payload["package"]["approval_sha256"] == "b" * 64


def test_demo_loader_rejects_placeholder_approval(tmp_path) -> None:
    payload = _payload()
    payload["package"]["approval_sha256"] = "0" * 64
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="approval_sha256"):
        load_approved_request(path)


def test_demo_loader_rejects_two_scene_script(tmp_path) -> None:
    payload = _payload()
    payload["segments"] = payload["segments"][:2]
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="at least three"):
        load_approved_request(path)
