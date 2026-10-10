import base64

import pytest

from sketch2life.application.services.whiteboard_video_job import WhiteboardVideoPipelineError
from sketch2life.infrastructure.ai.lightning_whiteboard import (
    LightningWhiteboardLocalizationAdapter,
)
from test_whiteboard_video_job import HASH, SuccessfulPipeline, make_job, make_service


PNG = b"\x89PNG\r\n\x1a\nsynthetic-image"


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.path = None
        self.payload = None

    def post_json(self, path, payload):
        self.path = path
        self.payload = payload
        return self.response


def make_localization(response):
    transport = FakeTransport(response)
    adapter = LightningWhiteboardLocalizationAdapter(
        transport=transport,
        artifact_loader=lambda _: PNG,
    )
    return adapter, transport


def test_lightning_localization_sends_bounded_source_payload():
    import hashlib

    source_hash = hashlib.sha256(PNG).hexdigest()
    adapter, transport = make_localization(
        {"source_hash": source_hash, "regions": [{"region_ref": "region-001", "confidence": 0.9}]}
    )
    service = make_service(SuccessfulPipeline())
    job = make_job(service).model_copy(update={"source_hash": source_hash})

    result = adapter.localize(job)

    assert result.region_refs == ("region-001",)
    assert transport.path == "/v1/whiteboard/localize"
    assert transport.payload["source_image"]["content_base64"] == base64.b64encode(PNG).decode()


def test_lightning_localization_rejects_low_confidence():
    import hashlib

    source_hash = hashlib.sha256(PNG).hexdigest()
    adapter, _ = make_localization(
        {"source_hash": source_hash, "regions": [{"region_ref": "region-001", "confidence": 0.5}]}
    )
    service = make_service(SuccessfulPipeline())
    job = make_job(service).model_copy(update={"source_hash": source_hash})

    with pytest.raises(WhiteboardVideoPipelineError, match="LOCALIZATION_SCHEMA_INVALID"):
        adapter.localize(job)


def test_lightning_localization_rejects_source_hash_mismatch():
    import hashlib

    source_hash = hashlib.sha256(PNG).hexdigest()
    adapter, _ = make_localization(
        {"source_hash": "b" * 64, "regions": [{"region_ref": "region-001", "confidence": 0.9}]}
    )
    service = make_service(SuccessfulPipeline())
    job = make_job(service).model_copy(update={"source_hash": source_hash})

    with pytest.raises(WhiteboardVideoPipelineError, match="SOURCE_HASH_MISMATCH"):
        adapter.localize(job)
