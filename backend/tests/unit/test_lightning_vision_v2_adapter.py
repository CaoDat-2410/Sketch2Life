from __future__ import annotations

import base64
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256

from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionErrorCodeV2,
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.lightning_client import JsonTransport
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.ai.vision_lexical_policy import synthetic_prohibited_lexicon

_IMAGE = b"\x89PNG\r\n\x1a\nsynthetic non-child test image"


class FakeTransport(JsonTransport):
    def __init__(self, response: Mapping[str, object] | None = None) -> None:
        self.response = response
        self.calls: list[tuple[str, Mapping[str, object]]] = []
        self.raise_timeout = False

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls.append((path, payload))
        if self.raise_timeout:
            raise TimeoutError
        assert self.response is not None
        return self.response


def _request() -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id="vision-request-1",
        source_image_ref=VisionImageReferenceV1(
            artifact_ref="artifact:session-1:image-1",
            sha256=sha256(_IMAGE).hexdigest(),
        ),
        media_validation=VisionMediaValidationProvenanceV1(
            validation_artifact_ref="artifact:session-1:validation-1",
            validation_artifact_sha256=sha256(b"admission-pass").hexdigest(),
            decision="PASS",
            validator_policy_version="feat018-image-admission-v1",
        ),
        requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    )


def _success(request: VisionUnderstandingRequestV2) -> VisionUnderstandingSuccessV2:
    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(request.requested_profile_id)
    policy = synthetic_prohibited_lexicon()
    return VisionUnderstandingSuccessV2(
        correlation_id=request.correlation_id,
        executed_at=datetime(2026, 9, 18, 13, 0, tzinfo=UTC),
        source_image_ref=request.source_image_ref,
        profile_id=profile.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        attempt_number=1,
        repair_attempted=False,
        content_policy_version=policy.lexicon_version,
        policy_match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
        policy_execution_state="PASSED",
        status="SUCCEEDED",
        entities=(),
        actions=(),
        relations=(),
        themes=(),
        ambiguous_regions=(),
        adapter_version=profile.adapter_version,
        config_hash=vision_profile_config_hash_v2(profile),
        model_provenance=profile.model_provenance,
    )


def test_adapter_sends_one_v2_request_with_verified_image_and_checks_identity() -> None:
    request = _request()
    response = _success(request).model_dump(mode="json")
    transport = FakeTransport(response)
    adapter = LightningVisionV2Adapter(
        transport=transport,
        artifact_loader=lambda ref: _IMAGE if ref == request.source_image_ref.artifact_ref else b"",
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert len(transport.calls) == 1
    path, payload = transport.calls[0]
    assert path == "/v2/vision"
    assert payload["contract_name"] == "LightningVisionRequestV2"
    image_payload = payload["source_image"]
    assert isinstance(image_payload, dict)
    assert image_payload["content_type"] == "image/png"
    assert base64.b64decode(image_payload["content_base64"]) == _IMAGE
    assert result.source_image_ref == request.source_image_ref


def test_adapter_rejects_hash_mismatch_before_network_call() -> None:
    request = _request()
    transport = FakeTransport(_success(request).model_dump(mode="json"))
    adapter = LightningVisionV2Adapter(
        transport=transport,
        artifact_loader=lambda _ref: b"different bytes",
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCodeV2.INPUT_NOT_VALIDATED
    assert result.error_detail is VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH
    assert transport.calls == []


def test_adapter_does_not_retry_credit_consuming_timeout() -> None:
    request = _request()
    transport = FakeTransport()
    transport.raise_timeout = True
    adapter = LightningVisionV2Adapter(
        transport=transport,
        artifact_loader=lambda _ref: _IMAGE,
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCodeV2.VISION_TIMEOUT
    assert result.error_detail is VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED
    assert len(transport.calls) == 1
