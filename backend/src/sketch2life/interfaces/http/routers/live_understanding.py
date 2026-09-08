"""Live understanding route for local synthetic-fixture smoke tests."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.understanding import (
    AsrRequestV1,
    ModelProvenanceV1,
    VisionRequestV1,
)
from sketch2life.infrastructure.ai.fixture_inputs import FixtureInputs
from sketch2life.infrastructure.ai.lightning_client import (
    LightningAsrAdapter,
    LightningVisionAdapter,
    UrllibJsonTransport,
    read_secret_file,
)
from sketch2life.infrastructure.config.settings import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["live-ai"])


class LiveUnderstandingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["live-lightning"] = "live-lightning"
    fixture_id: Literal["integration-fixture-v1"]
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=120)


def execute_live_understanding(
    request: LiveUnderstandingRequest,
    settings: Settings,
    *,
    asr_adapter: LightningAsrAdapter | None = None,
    vision_adapter: LightningVisionAdapter | None = None,
) -> dict[str, object]:
    if settings.ai_provider != "lightning_dev":
        raise HTTPException(status_code=503, detail="live Lightning development mode is disabled")
    if request.expected_session_version != 1:
        raise HTTPException(status_code=409, detail="STALE_SESSION_VERSION")
    if settings.live_fixture_root is None:
        raise HTTPException(status_code=503, detail="synthetic live fixture root is not configured")
    fixture = FixtureInputs.load(settings.live_fixture_root, request.fixture_id)
    if asr_adapter is None or vision_adapter is None:
        if not settings.lightning_ai_base_url or settings.lightning_ai_token_file is None:
            raise HTTPException(
                status_code=503, detail="live Lightning runtime settings are incomplete"
            )
        transport = UrllibJsonTransport(
            settings.lightning_ai_base_url,
            read_secret_file(settings.lightning_ai_token_file),
            request_timeout_seconds=settings.ai_request_timeout_seconds,
        )
        provenance = ModelProvenanceV1(
            provider="lightning",
            model=settings.lightning_model_profile,
            adapter_version="1.0",
            config_version="live-lightning-v1",
        )
        asr_adapter = LightningAsrAdapter(
            transport=transport,
            artifact_loader=fixture.read,
            provenance=provenance,
            endpoint_path=settings.lightning_asr_path,
        )
        vision_adapter = LightningVisionAdapter(
            transport=transport,
            artifact_loader=fixture.read,
            provenance=provenance,
            endpoint_path=settings.lightning_vision_path,
        )
    asr = asr_adapter.transcribe(AsrRequestV1(source_audio=fixture.audio, media_validation="PASS"))
    vision = vision_adapter.understand(
        VisionRequestV1(source_image=fixture.image, media_validation="PASS")
    )
    succeeded = asr.status == "SUCCEEDED" and vision.status == "SUCCEEDED"
    proposal_label = (
        vision.entities[0].label if vision.status == "SUCCEEDED" and vision.entities else None
    )
    return {
        "contract_name": "LiveUnderstandingResultV1",
        "contract_version": "1.0",
        "status": "PROPOSAL" if succeeded else "FAILED",
        "request_id": request.request_id,
        "session_id": request.session_id,
        "expected_session_version": request.expected_session_version,
        "fixture_id": fixture.fixture_id,
        "proposal_label": proposal_label,
        "gate_a_required": True,
        "asr": asr.model_dump(mode="json"),
        "vision": vision.model_dump(mode="json"),
    }


@router.post("/live-understanding")
def live_understanding(request: LiveUnderstandingRequest) -> dict[str, object]:
    return execute_live_understanding(request, get_settings())
