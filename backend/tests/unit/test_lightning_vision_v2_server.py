from __future__ import annotations

import hmac
from typing import cast

import pytest
import tools.lightning_vision_v2_server as vision_server
from fastapi import HTTPException
from tools.lightning_vision_v2_server import (
    _repair_prompt_with_diagnostics,
    _vision_runtime_environment,
)

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
