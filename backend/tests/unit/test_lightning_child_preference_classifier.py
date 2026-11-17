from __future__ import annotations

from http.client import RemoteDisconnected

import pytest

from sketch2life.contracts.schemas.child_preference_classification import (
    ChildPreferenceClassificationRequestV1,
)
from sketch2life.infrastructure.ai.lightning_child_preference_classifier import (
    ChildPreferenceClassificationUnavailable,
    LightningChildPreferenceClassifier,
)
from sketch2life.infrastructure.ai.lightning_client import LightningProviderError


class _DisconnectingTransport:
    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        del path, payload
        raise RemoteDisconnected("synthetic provider disconnect")


class _MissingEndpointTransport:
    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        del path, payload
        raise LightningProviderError(
            "ENDPOINT_NOT_FOUND", "synthetic endpoint mismatch", False
        )


def test_remote_disconnect_maps_to_sanitized_retryable_failure() -> None:
    classifier = LightningChildPreferenceClassifier(transport=_DisconnectingTransport())
    request = ChildPreferenceClassificationRequestV1(
        request_id="synthetic-preference-disconnect",
        interest_text="synthetic bird preference",
    )

    with pytest.raises(ChildPreferenceClassificationUnavailable) as raised:
        classifier.classify(request)

    assert raised.value.code == "CLASSIFIER_UNAVAILABLE"
    assert raised.value.retryable is True
    assert "synthetic provider disconnect" not in str(raised.value)
    assert request.interest_text not in str(raised.value)


def test_missing_lightning_route_maps_to_specific_non_retryable_failure() -> None:
    classifier = LightningChildPreferenceClassifier(transport=_MissingEndpointTransport())
    request = ChildPreferenceClassificationRequestV1(
        request_id="synthetic-preference-endpoint-missing",
        interest_text="synthetic butterfly preference",
    )

    with pytest.raises(ChildPreferenceClassificationUnavailable) as raised:
        classifier.classify(request)

    assert raised.value.code == "CLASSIFIER_ENDPOINT_UNAVAILABLE"
    assert raised.value.retryable is False
    assert "synthetic endpoint mismatch" not in str(raised.value)
    assert request.interest_text not in str(raised.value)
