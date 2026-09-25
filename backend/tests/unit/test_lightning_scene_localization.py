from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

from fastapi.testclient import TestClient
from pytest import approx
from tools.lightning_vision_v2_server import (
    _localization_fallback,
    _LocalizationRequestV1,
    _parse_localization_output,
    _resolve_localization_target_ref,
)
from tools.lightning_vision_v2_server import app as lightning_app

from sketch2life.application.ports.scene_localization import SceneLocalizationRequest
from sketch2life.infrastructure.ai.lightning_scene_localization import (
    LightningSceneLocalizationAdapter,
)


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, object]]] = []

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls.append((path, payload))
        return {
            "regions": [
                {
                    "target_ref": "entity-1",
                    "region": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
                }
            ]
        }


def _request(image: bytes) -> SceneLocalizationRequest:
    return SceneLocalizationRequest(
        session_id="session-1",
        experience_spec_ref=None,
        source_artifact_ref="artifact:session-1:image-1",
        source_artifact_sha256=sha256(image).hexdigest(),
        target_refs=("entity-1",),
        attempt_id="attempt-1",
        target_labels={"entity-1": "con chim"},
    )


def test_adapter_sends_provider_contract_for_png_and_jpeg() -> None:
    for image, expected_content_type in (
        (b"\x89PNG\r\n\x1a\nsynthetic-png", "image/png"),
        (b"\xff\xd8\xffsynthetic-jpeg", "image/jpeg"),
    ):
        transport = FakeTransport()
        adapter = LightningSceneLocalizationAdapter(
            transport=transport,
            artifact_loader=lambda _, image=image: image,
        )

        result = adapter.localize(_request(image))

        assert result == {
            "entity-1": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4}
        }
        path, payload = transport.calls[0]
        assert path == "/v2/localize"
        _LocalizationRequestV1.model_validate(payload)
        source_image = payload["source_image"]
        assert isinstance(source_image, dict)
        assert source_image["content_type"] == expected_content_type


def test_adapter_fails_closed_for_unsupported_image_without_transport_call() -> None:
    image = b"not-an-admitted-image"
    transport = FakeTransport()
    adapter = LightningSceneLocalizationAdapter(
        transport=transport,
        artifact_loader=lambda _: image,
    )

    assert adapter.localize(_request(image)) is None
    assert transport.calls == []


def test_adapter_fails_closed_when_source_digest_does_not_match() -> None:
    image = b"\x89PNG\r\n\x1a\nsynthetic-png"
    request = _request(image)
    request = SceneLocalizationRequest(
        session_id=request.session_id,
        experience_spec_ref=request.experience_spec_ref,
        source_artifact_ref=request.source_artifact_ref,
        source_artifact_sha256="0" * 64,
        target_refs=request.target_refs,
        attempt_id=request.attempt_id,
        target_labels=request.target_labels,
    )
    transport = FakeTransport()
    adapter = LightningSceneLocalizationAdapter(
        transport=transport,
        artifact_loader=lambda _: image,
    )

    assert adapter.localize(request) is None
    assert transport.calls == []


def test_lightning_validation_error_does_not_echo_request_body() -> None:
    response = TestClient(lightning_app).post(
        "/v2/localize",
        json={
            "contract_name": "SceneLocalizationRequestV1",
            "contract_version": "1.0",
            "session_id": "session-1",
            "experience_spec_ref": None,
            "source_image": {
                "artifact_ref": "artifact:session-1:image-1",
                "sha256": "a" * 64,
                "content_base64": "YQ==",
            },
            "targets": ["entity-1"],
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "request contract invalid"}


def test_localization_parser_accepts_fenced_and_nested_provider_json() -> None:
    regions = _parse_localization_output(
        """```json
        {"regions":[{"target_ref":"entity-1","region":{"x":0.1,"y":0.2,"width":0.3,"height":0.4},"confidence":0.9}]}
        ```"""
    )

    assert len(regions) == 1
    assert regions[0].target_ref == "entity-1"
    assert regions[0].x == 0.1
    assert regions[0].confidence == 0.9


def test_localization_parser_normalizes_bounded_percentage_confidence() -> None:
    regions = _parse_localization_output(
        '{"regions":[{"target_ref":"entity-1","x":0.1,"y":0.2,"width":0.3,"height":0.4,"confidence":95}]}'
    )

    assert regions[0].confidence == 0.95


def test_localization_parser_normalizes_percent_coordinates_and_clips_to_image() -> None:
    regions = _parse_localization_output(
        '{"regions":[{"target_ref":"entity-1","x":80,"y":20,"width":30,"height":90,"confidence":0.9}]}'
    )

    assert regions[0].x == 0.8
    assert regions[0].y == 0.2
    assert regions[0].width == approx(0.2)
    assert regions[0].height == 0.8


def test_localization_target_label_can_resolve_only_when_unique() -> None:
    payload = _LocalizationRequestV1(
        session_id="session-1",
        source_image={
            "artifact_ref": "artifact:session-1:image-1",
            "sha256": "a" * 64,
            "content_type": "image/png",
            "content_base64": "YQ==",
        },
        targets=["entity-1"],
        target_labels={"entity-1": "con chim"},
    )

    assert _resolve_localization_target_ref("con chim", payload) == "entity-1"


def test_localization_model_failure_is_a_typed_fallback_not_http_failure() -> None:
    assert _localization_fallback("MODEL_OUTPUT_REGION_INVALID") == {
        "contract_name": "SceneLocalizationResultV1",
        "contract_version": "1.0",
        "status": "FALLBACK_REQUIRED",
        "regions": [],
        "fallback_reason": "MODEL_OUTPUT_REGION_INVALID",
    }
