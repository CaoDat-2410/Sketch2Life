import base64
import json

import pytest

from sketch2life.infrastructure.identity.firebase_token_verifier import (
    _decode_firebase_admin_json,
)


def test_decodes_admin_service_account_json_for_matching_project() -> None:
    service_account = {
        "type": "service_account",
        "project_id": "sketch2life-dev",
        "client_email": "synthetic@example.invalid",
        "private_key": "synthetic-test-only",
    }
    encoded = base64.b64encode(json.dumps(service_account).encode()).decode()

    assert _decode_firebase_admin_json(encoded, "sketch2life-dev") == service_account


def test_rejects_invalid_base64_without_echoing_credential() -> None:
    with pytest.raises(ValueError, match="valid Base64 JSON"):
        _decode_firebase_admin_json("not-base64!", "sketch2life-dev")


def test_rejects_service_account_from_another_project() -> None:
    service_account = {"type": "service_account", "project_id": "other-project"}
    encoded = base64.b64encode(json.dumps(service_account).encode()).decode()

    with pytest.raises(ValueError, match="does not match configured project"):
        _decode_firebase_admin_json(encoded, "sketch2life-dev")
