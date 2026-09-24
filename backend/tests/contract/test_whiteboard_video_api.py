from fastapi.testclient import TestClient

from sketch2life.interfaces.http.app import create_app


SOURCE_HASH = "a" * 64


def body(idempotency_key: str = "idem-001") -> dict[str, str]:
    return {
        "experience_spec_id": "spec-001",
        "source_artifact_id": "artifact-source-001",
        "source_hash": SOURCE_HASH,
        "learning_thread_ref": "thread-001",
        "idempotency_key": idempotency_key,
    }


def test_create_and_poll_whiteboard_video_job() -> None:
    client = TestClient(create_app())

    created = client.post("/v1/sessions/session-001/whiteboard-video-jobs", json=body())

    assert created.status_code == 201
    assert created.headers["Idempotency-Replayed"] == "false"
    assert created.json()["status"] == "QUEUED"
    assert created.json()["progress"] == 0

    status = client.get("/v1/sessions/session-001/whiteboard-video")

    assert status.status_code == 200
    assert status.json()["status"] == "NOT_STARTED"
    assert status.json()["retryable"] is False
    assert status.json()["video_artifact_ref"] is None


def test_repeated_create_with_same_key_replays_job() -> None:
    client = TestClient(create_app())
    first = client.post("/v1/sessions/session-001/whiteboard-video-jobs", json=body())
    second = client.post("/v1/sessions/session-001/whiteboard-video-jobs", json=body())

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.headers["Idempotency-Replayed"] == "true"
    assert second.json()["job_id"] == first.json()["job_id"]


def test_reusing_key_with_different_payload_is_rejected() -> None:
    client = TestClient(create_app())
    client.post("/v1/sessions/session-001/whiteboard-video-jobs", json=body())
    changed = body()
    changed["source_hash"] = "b" * 64

    response = client.post("/v1/sessions/session-001/whiteboard-video-jobs", json=changed)

    assert response.status_code == 409
    assert response.json()["detail"] == "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH"
