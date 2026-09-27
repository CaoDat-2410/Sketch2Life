from __future__ import annotations

from fastapi.testclient import TestClient

from sketch2life.interfaces.http.app import create_app


def test_storyboard_preview_returns_age_bounded_scenes() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/whiteboard/storyboards/preview",
        json={
            "subject_claim": "con mèo",
            "feature_claim": "ria mèo",
            "audience_band": "EARLY_PRIMARY",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["topic_vi"] == "Ria mèo dùng để làm gì?"
    assert payload["audience_age_min"] == 6
    assert len(payload["scenes"]) == 4


def test_storyboard_preview_rejects_unreviewed_topic() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/whiteboard/storyboards/preview",
        json={"subject_claim": "con voi", "feature_claim": "cái vòi"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "UNREVIEWED_STORYBOARD_TOPIC"
