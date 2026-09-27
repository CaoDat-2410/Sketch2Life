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


def test_storyboard_preview_accepts_adult_supplied_age_months() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/whiteboard/storyboards/preview",
        json={
            "subject_claim": "con mèo",
            "feature_claim": "ria mèo",
            "age_months": 120,
        },
    )

    assert response.status_code == 200
    assert response.json()["audience_age_min"] == 9


def test_storyboard_preview_rejects_age_without_reviewed_audience_band() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/whiteboard/storyboards/preview",
        json={
            "subject_claim": "con mèo",
            "feature_claim": "ria mèo",
            "age_months": 60,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "AGE_BAND_NOT_SUPPORTED"
