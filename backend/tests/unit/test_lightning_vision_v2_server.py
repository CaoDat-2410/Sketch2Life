from __future__ import annotations

import base64
import hashlib
import hmac
import json
from io import BytesIO
from pathlib import Path
from typing import cast

import pytest
import tools.lightning_vision_v2_server as vision_server
from fastapi import HTTPException
from PIL import Image
from tools.lightning_vision_v2_server import (
    _repair_prompt_with_diagnostics,
    _vision_runtime_environment,
)

from sketch2life.contracts.schemas.pixi_show import PixiShowPlannerRequestV3
from sketch2life.contracts.schemas.vision_v2 import (
    VisionMappingDiagnosticV2,
    VisionUnderstandingRequestV2,
)


def test_live_repair_prompt_uses_only_closed_diagnostic_tokens() -> None:
    prompt = _repair_prompt_with_diagnostics(
        cast(VisionUnderstandingRequestV2, object()),
        (
            VisionMappingDiagnosticV2.STRICT_JSON_PARSE_FAILED,
            VisionMappingDiagnosticV2.STRICT_JSON_PARSE_FAILED,
        ),
    )

    assert "STRICT_JSON_PARSE_FAILED" in prompt
    assert prompt.count("STRICT_JSON_PARSE_FAILED") == 1
    assert "previous response failed the output contract" in prompt
    assert "emit only the canonical JSON object" not in prompt


def test_live_repair_prompt_falls_back_to_closed_schema_token() -> None:
    prompt = _repair_prompt_with_diagnostics(
        cast(VisionUnderstandingRequestV2, object()),
        (),
    )

    assert "SCHEMA_TYPE_OR_CONSTRAINT_INVALID" in prompt


def test_blank_model_dir_uses_legacy_root_fallback() -> None:
    runtime_env = _vision_runtime_environment(
        {
            "SKETCH2LIFE_VISION_MODEL_DIR": "   ",
            "SKETCH2LIFE_VISION_MODEL_CACHE_DIR": "",
            "SKETCH2LIFE_VLM_ROOT": "/teamspace/studios/this_studio/models/qwen3-vl-8b-instruct",
        }
    )

    assert (
        runtime_env["SKETCH2LIFE_VISION_MODEL_DIR"]
        == "/teamspace/studios/this_studio/models/qwen3-vl-8b-instruct"
    )


def test_operator_model_dir_alias_wins_over_placeholder_legacy_root() -> None:
    runtime_env = _vision_runtime_environment(
        {
            "SKETCH2LIFE_VISION_MODEL_DIR": "",
            "MODEL_DIR": "/teamspace/studios/this_studio/models/qwen3-vl-8b-instruct",
            "SKETCH2LIFE_VLM_ROOT": "/path/to/qwen3-vl-8b-instruct",
        }
    )

    assert (
        runtime_env["SKETCH2LIFE_VISION_MODEL_DIR"]
        == "/teamspace/studios/this_studio/models/qwen3-vl-8b-instruct"
    )


def test_explicit_model_dir_is_not_overridden() -> None:
    runtime_env = _vision_runtime_environment(
        {
            "SKETCH2LIFE_VISION_MODEL_DIR": "/models/explicit-qwen",
            "SKETCH2LIFE_VLM_ROOT": "/models/legacy-qwen",
        }
    )

    assert runtime_env["SKETCH2LIFE_VISION_MODEL_DIR"] == "/models/explicit-qwen"


def test_adaptive_pixi_planner_uses_one_visual_contact_sheet_call(monkeypatch) -> None:
    def png(color: tuple[int, int, int, int]) -> bytes:
        output = BytesIO()
        Image.new("RGBA", (24, 18), color).save(output, format="PNG")
        return output.getvalue()

    source = png((250, 248, 242, 255))
    preview = png((60, 170, 80, 255))
    response = {
        "visualSubjectHintId": "BIRD",
        "behaviorClass": "FLYER",
        "confidence": 0.91,
        "selectedAssetIds": [],
        "durationSeconds": 20,
        "beats": [
            {
                "beatId": "notice",
                "startSeconds": 0,
                "endSeconds": 4,
                "action": "NOTICE",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "approach",
                "startSeconds": 5,
                "endSeconds": 10,
                "action": "APPROACH",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "settle",
                "startSeconds": 12,
                "endSeconds": 17,
                "action": "SETTLE",
                "targetRole": "SOURCE_SUBJECT",
            },
        ],
        "endingStill": True,
        "renderStrategy": "CUTOUT_TOPIC_SCENE",
        "sceneThemeAssetId": "asset-meadow",
    }
    payload = PixiShowPlannerRequestV3(
        contractName="PixiShowPlannerRequestV3",
        contractVersion="3.0",
        requestId="00000000-0000-4000-8000-000000000001",
        sourceCrop={
            "contentType": "image/png",
            "sha256": hashlib.sha256(source).hexdigest(),
            "contentBase64": base64.b64encode(source).decode("ascii"),
        },
        sourceSubjectRegion={"x": 0.3, "y": 0.2, "width": 0.4, "height": 0.5},
        rendererDurationSeconds=20,
        confirmedSubjectLabel="chim",
        subjectTags=("bird",),
        activityId="ACT-1",
        activityLabel="Quan sát chim",
        objectiveIds=("OBJ-1",),
        objectiveLabels=("Nhận biết môi trường sống",),
        rigTier="CUTOUT_MICRO_MOTION",
        partRoles=(),
        chosenTopicLabels=("Chim ở đồng cỏ",),
        candidateAssets=(
            {
                "assetId": "asset-meadow",
                "label": "Đồng cỏ",
                "role": "ENVIRONMENT",
                "visualDescription": "Đồng cỏ xanh dịu.",
                "topicTags": ("chim", "đồng cỏ"),
                "previewContentType": "image/png",
                "previewSha256": hashlib.sha256(preview).hexdigest(),
                "previewContentBase64": base64.b64encode(preview).decode("ascii"),
            },
        ),
    )

    calls: list[tuple[tuple[int, int], str]] = []

    class FakeRunner:
        def generate(self, _profile, _runtime, image_path: Path, prompt: str) -> str:
            with Image.open(image_path) as image_file:
                size = image_file.size
            calls.append((size, prompt))
            return json.dumps(response)

    monkeypatch.setenv("SKETCH2LIFE_LIGHTNING_PIXI_SHOW_ENABLED", "true")
    monkeypatch.setattr(vision_server, "EXPECTED_AUTH", "synthetic-token")
    monkeypatch.setattr(vision_server, "_QWEN_GENERATION_RUNNER", FakeRunner())
    monkeypatch.setattr(vision_server.QwenVisionRuntimeConfig, "from_env", lambda _env: object())
    class FakeProfileCatalog:
        def resolve(self, _profile_id):
            return object()

    monkeypatch.setattr(vision_server, "vision_profile_catalog_v2", FakeProfileCatalog)

    result = vision_server.plan_pixi_show_v4(payload, "Bearer synthetic-token")

    assert result["renderStrategy"] == "CUTOUT_TOPIC_SCENE"
    assert len(calls) == 1
    prompt = calls[0][1]
    assert "Chim ở đồng cỏ" in prompt
    assert "asset-meadow" in prompt
    assert base64.b64encode(preview).decode("ascii") not in prompt
    assert calls[0][0] == (1200, 860)


def test_provider_auth_uses_constant_time_comparison(monkeypatch) -> None:
    calls: list[tuple[bytes, bytes]] = []
    original = hmac.compare_digest

    def record_comparison(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return original(left, right)

    monkeypatch.setattr(vision_server, "EXPECTED_AUTH", "synthetic-token")
    monkeypatch.setattr(vision_server.hmac, "compare_digest", record_comparison)

    vision_server._require_auth("Bearer synthetic-token")
    with pytest.raises(HTTPException) as raised:
        vision_server._require_auth("Bearer wrong-token")
    with pytest.raises(HTTPException) as unicode_raised:
        vision_server._require_auth("Bearer tøkén")

    assert raised.value.status_code == 401
    assert unicode_raised.value.status_code == 401
    assert calls == [
        (b"Bearer synthetic-token", b"Bearer synthetic-token"),
        (b"Bearer wrong-token", b"Bearer synthetic-token"),
        ("Bearer tøkén".encode(), b"Bearer synthetic-token"),
    ]
