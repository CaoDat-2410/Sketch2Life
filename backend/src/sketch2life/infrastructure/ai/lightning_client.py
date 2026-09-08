"""Backend-only Lightning development transport and contract adapters.

The provider endpoint is intentionally generic: a Lightning Studio/deployment must
expose the two small JSON operations documented in FEAT-017's notebook guide.
"""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from sketch2life.contracts.schemas.understanding import (
    AdapterFailureV1,
    AsrQualityV1,
    AsrRequestV1,
    AsrResultV1,
    AsrSegmentV1,
    ModelProvenanceV1,
    VisionCandidateV1,
    VisionRegionV1,
    VisionRelationV1,
    VisionRequestV1,
    VisionUnderstandingResultV1,
)


class LightningProviderError(Exception):
    """Sanitized provider failure; response bodies never cross this boundary."""

    def __init__(self, code: str, message: str, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class JsonTransport(Protocol):
    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]: ...


def _provider_items(value: object) -> tuple[object, ...]:
    """Narrow an untrusted provider collection before iterating over it."""

    if not isinstance(value, (list, tuple)):
        raise TypeError("provider collection must be an array")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class UrllibJsonTransport:
    base_url: str
    token: str
    request_timeout_seconds: float = 120.0
    max_response_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("live Lightning endpoint must use HTTPS outside local development")
        if not self.token.strip():
            raise ValueError("live Lightning token cannot be empty")

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        url = urljoin(f"{self.base_url.rstrip('/')}/", path.lstrip("/"))
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.request_timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            if exc.code in {408, 504}:
                raise TimeoutError("Lightning request timed out") from None
            if exc.code == 429:
                raise LightningProviderError(
                    "RATE_LIMITED", "Lightning rate limit reached", True
                ) from None
            raise LightningProviderError(
                "PROVIDER_ERROR", "Lightning request failed", exc.code >= 500
            ) from None
        except TimeoutError:
            raise TimeoutError("Lightning request timed out") from None
        except URLError:
            raise LightningProviderError(
                "PROVIDER_ERROR", "Lightning connection failed", True
            ) from None
        if len(raw) > self.max_response_bytes:
            raise LightningProviderError(
                "MALFORMED_OUTPUT", "Lightning response exceeded size limit", False
            )
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise LightningProviderError(
                "MALFORMED_OUTPUT", "Lightning response was not JSON", False
            ) from None
        if not isinstance(decoded, dict):
            raise LightningProviderError(
                "MALFORMED_OUTPUT", "Lightning response was not an object", False
            )
        return decoded


def read_secret_file(path: Path) -> str:
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("configured Lightning token file is empty")
    return value


def _artifact_payload(
    source: Any,
    artifact_loader: Callable[[str], bytes],
    max_input_bytes: int,
) -> dict[str, object]:
    data = artifact_loader(source.artifact_ref)
    if len(data) > max_input_bytes:
        raise ValueError("source artifact exceeds live input limit")
    digest = hashlib.sha256(data).hexdigest()
    if source.sha256 != digest:
        raise ValueError("source artifact hash mismatch")
    return {
        "artifact_ref": source.artifact_ref,
        "sha256": source.sha256,
        "content_base64": base64.b64encode(data).decode("ascii"),
    }


def _post_with_retry(
    transport: JsonTransport,
    path: str,
    payload: Mapping[str, object],
    max_retries: int,
) -> Mapping[str, object]:
    attempts = min(max(max_retries, 0), 1) + 1
    for attempt in range(attempts):
        try:
            return transport.post_json(path, payload)
        except TimeoutError:
            if attempt + 1 < attempts:
                continue
            raise
        except LightningProviderError as exc:
            if exc.retryable and attempt + 1 < attempts:
                continue
            raise
    raise LightningProviderError("PROVIDER_ERROR", "Lightning request failed", True)


@dataclass(frozen=True, slots=True)
class LightningAsrAdapter:
    transport: JsonTransport
    artifact_loader: Callable[[str], bytes]
    provenance: ModelProvenanceV1
    endpoint_path: str = "/v1/asr"
    request_timeout_seconds: float = 120.0
    max_retries: int = 1
    max_input_bytes: int = 5_000_000

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1:
        try:
            raw = _post_with_retry(
                self.transport,
                self.endpoint_path,
                {
                    "contract_name": request.contract_name,
                    "contract_version": request.contract_version,
                    "model_profile": self.provenance.model,
                    "source_audio": _artifact_payload(
                        request.source_audio, self.artifact_loader, self.max_input_bytes
                    ),
                },
                self.max_retries,
            )
            segments = tuple(
                AsrSegmentV1.model_validate(item)
                for item in _provider_items(raw.get("segments", ()))
            )
            quality = AsrQualityV1.model_validate(
                raw.get("quality", {"segment_count": len(segments)})
            )
            return AsrResultV1.model_validate(
                {
                    "status": "SUCCEEDED",
                    "source_audio": request.source_audio,
                    "transcript": raw.get("transcript"),
                    "language": raw.get("language"),
                    "language_confidence": raw.get("language_confidence"),
                    "segments": segments,
                    "quality": quality,
                    "provenance": self.provenance,
                }
            )
        except TimeoutError:
            return _asr_failure(request, self.provenance, "TIMEOUT", "ASR provider timed out", True)
        except LightningProviderError as exc:
            return _asr_failure(request, self.provenance, exc.code, exc.message, exc.retryable)
        except (KeyError, TypeError, ValueError):
            return _asr_failure(
                request,
                self.provenance,
                "MALFORMED_OUTPUT",
                "ASR output failed schema validation",
                False,
            )


@dataclass(frozen=True, slots=True)
class LightningVisionAdapter:
    transport: JsonTransport
    artifact_loader: Callable[[str], bytes]
    provenance: ModelProvenanceV1
    endpoint_path: str = "/v1/vision"
    max_retries: int = 1
    max_input_bytes: int = 5_000_000

    def understand(self, request: VisionRequestV1) -> VisionUnderstandingResultV1:
        try:
            raw = _post_with_retry(
                self.transport,
                self.endpoint_path,
                {
                    "contract_name": request.contract_name,
                    "contract_version": request.contract_version,
                    "response_schema_version": request.response_schema_version,
                    "model_profile": self.provenance.model,
                    "source_image": _artifact_payload(
                        request.source_image, self.artifact_loader, self.max_input_bytes
                    ),
                },
                self.max_retries,
            )
            entities = tuple(
                VisionCandidateV1.model_validate(item)
                for item in _provider_items(raw.get("entities", ()))
            )
            actions = tuple(
                VisionCandidateV1.model_validate(item)
                for item in _provider_items(raw.get("actions", ()))
            )
            relations = tuple(
                VisionRelationV1.model_validate(item)
                for item in _provider_items(raw.get("relations", ()))
            )
            themes = tuple(
                VisionCandidateV1.model_validate(item)
                for item in _provider_items(raw.get("themes", ()))
            )
            regions = tuple(
                VisionRegionV1.model_validate(item)
                for item in _provider_items(raw.get("ambiguous_regions", ()))
            )
            return VisionUnderstandingResultV1.model_validate(
                {
                    "status": "SUCCEEDED",
                    "source_image": request.source_image,
                    "entities": entities,
                    "actions": actions,
                    "relations": relations,
                    "themes": themes,
                    "ambiguous_regions": regions,
                    "uncertainty": raw.get("uncertainty", 1),
                    "provenance": self.provenance,
                }
            )
        except TimeoutError:
            return _vision_failure(
                request, self.provenance, "TIMEOUT", "Vision provider timed out", True
            )
        except LightningProviderError as exc:
            return _vision_failure(request, self.provenance, exc.code, exc.message, exc.retryable)
        except (KeyError, TypeError, ValueError):
            return _vision_failure(
                request,
                self.provenance,
                "MALFORMED_OUTPUT",
                "Vision output failed schema validation",
                False,
            )


def _asr_failure(
    request: AsrRequestV1,
    provenance: ModelProvenanceV1,
    code: str,
    message: str,
    retryable: bool,
) -> AsrResultV1:
    return AsrResultV1(
        status="FAILED",
        source_audio=request.source_audio,
        provenance=provenance,
        failure=AdapterFailureV1(code=code, message=message, retryable=retryable),  # type: ignore[arg-type]
    )


def _vision_failure(
    request: VisionRequestV1,
    provenance: ModelProvenanceV1,
    code: str,
    message: str,
    retryable: bool,
) -> VisionUnderstandingResultV1:
    return VisionUnderstandingResultV1(
        status="FAILED",
        source_image=request.source_image,
        uncertainty=1,
        provenance=provenance,
        failure=AdapterFailureV1(code=code, message=message, retryable=retryable),  # type: ignore[arg-type]
    )
