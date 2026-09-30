"""Single-request Lightning adapter for bounded preference tag proposals."""

from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.child_preference_classifier import (
    ChildPreferenceClassifierPort,
)
from sketch2life.contracts.schemas.child_preference_classification import (
    ChildPreferenceClassificationRequestV1,
    ChildPreferenceClassificationV1,
)
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)

_RESULT_ADAPTER: TypeAdapter[ChildPreferenceClassificationV1] = TypeAdapter(
    ChildPreferenceClassificationV1
)


class ChildPreferenceClassificationUnavailable(Exception):
    """Sanitized classification failure; never carries provider text or user input."""

    def __init__(self, code: str, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class LightningChildPreferenceClassifier(ChildPreferenceClassifierPort):
    def __init__(
        self,
        *,
        transport: JsonTransport,
        endpoint_path: str = "/v2/profile/preferences/classify",
    ) -> None:
        if not endpoint_path.startswith("/"):
            raise ValueError("preference classification path must be absolute")
        self._transport = transport
        self._endpoint_path = endpoint_path

    def classify(
        self, request: ChildPreferenceClassificationRequestV1
    ) -> ChildPreferenceClassificationV1:
        try:
            raw = self._transport.post_json(
                self._endpoint_path,
                {
                    "contract_name": request.contract_name,
                    "contract_version": request.contract_version,
                    "request_id": request.request_id,
                    "interest_text": request.interest_text,
                    "avoid_text": request.avoid_text,
                },
            )
        except TimeoutError:
            raise ChildPreferenceClassificationUnavailable("CLASSIFICATION_TIMEOUT", True) from None
        except LightningProviderError as error:
            if error.code == "ENDPOINT_NOT_FOUND":
                raise ChildPreferenceClassificationUnavailable(
                    "CLASSIFIER_ENDPOINT_UNAVAILABLE", False
                ) from None
            raise ChildPreferenceClassificationUnavailable(
                "CLASSIFIER_UNAVAILABLE", error.retryable
            ) from None
        except OSError:
            # urllib/http.client can surface a dropped upstream socket as
            # RemoteDisconnected/ConnectionResetError rather than URLError.
            # Keep those transport details outside the HTTP/API boundary.
            raise ChildPreferenceClassificationUnavailable(
                "CLASSIFIER_UNAVAILABLE", True
            ) from None
        try:
            result = _RESULT_ADAPTER.validate_python(raw)
        except ValidationError:
            raise ChildPreferenceClassificationUnavailable(
                "CLASSIFIER_INVALID_RESULT", False
            ) from None
        if result.request_id != request.request_id:
            raise ChildPreferenceClassificationUnavailable("CLASSIFIER_INVALID_RESULT", False)
        return result


__all__ = [
    "ChildPreferenceClassificationUnavailable",
    "LightningChildPreferenceClassifier",
]
