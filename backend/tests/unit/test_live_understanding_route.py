from __future__ import annotations

from pathlib import Path

from sketch2life.infrastructure.ai.fixture_inputs import FixtureInputs
from sketch2life.infrastructure.ai.lightning_client import (
    LightningAsrAdapter,
    LightningVisionAdapter,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.routers.live_understanding import (
    LiveUnderstandingRequest,
    execute_live_understanding,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1"
)


def test_live_route_keeps_gate_a_and_returns_both_contracts() -> None:
    fixture = FixtureInputs.load(FIXTURE_ROOT, "integration-fixture-v1")

    class Transport:
        def post_json(self, path: str, payload: object) -> dict[str, object]:
            if path == "/v1/asr":
                return {"transcript": "butterfly", "segments": [], "quality": {"segment_count": 0}}
            return {
                "entities": [{"label": "butterfly", "confidence": 0.94}],
                "actions": [],
                "relations": [],
                "themes": [],
                "ambiguous_regions": [],
                "uncertainty": 0.06,
            }

    from sketch2life.contracts.schemas.understanding import ModelProvenanceV1

    provenance = ModelProvenanceV1(
        provider="lightning", model="live", adapter_version="1.0", config_version="test"
    )
    result = execute_live_understanding(
        LiveUnderstandingRequest(
            fixture_id="integration-fixture-v1",
            session_id="session-fixture-001",
            expected_session_version=1,
        ),
        Settings(ai_provider="lightning_dev", live_fixture_root=FIXTURE_ROOT),
        asr_adapter=LightningAsrAdapter(Transport(), fixture.read, provenance),
        vision_adapter=LightningVisionAdapter(Transport(), fixture.read, provenance),
    )

    assert result["status"] == "PROPOSAL"
    assert result["gate_a_required"] is True
    assert result["proposal_label"] == "butterfly"
    assert result["asr"]["source_audio"]["sha256"] == fixture.audio.sha256  # type: ignore[index]
    assert result["vision"]["source_image"]["sha256"] == fixture.image.sha256  # type: ignore[index]


def test_live_route_rejects_stale_session_version() -> None:
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        execute_live_understanding(
            LiveUnderstandingRequest(
                fixture_id="integration-fixture-v1",
                session_id="session-fixture-001",
                expected_session_version=2,
            ),
            Settings(ai_provider="lightning_dev", live_fixture_root=FIXTURE_ROOT),
        )

    assert error.value.status_code == 409
    assert error.value.detail == "STALE_SESSION_VERSION"
