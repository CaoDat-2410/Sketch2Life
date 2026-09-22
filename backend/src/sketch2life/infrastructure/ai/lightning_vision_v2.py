"""Single-attempt Lightning transport for the approved FEAT-003 Vision V2 boundary."""

from __future__ import annotations

import base64
from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256

from pydantic import TypeAdapter, ValidationError

from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    VisionProfileV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    collect_observed_texts_v2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_MAX_IMAGE_BYTES = 5_000_000
VisionV2Result = VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2
_RESULT_ADAPTER: TypeAdapter[VisionV2Result] = TypeAdapter(VisionV2Result)


class LightningVisionV2Adapter:
    """Validate opaque artifact bytes, make one explicit provider request, and check V2 identity.

    The adapter has no retry loop. Callers control whether a human explicitly retries; provider
    requests are never repeated automatically because the remote call may consume credits.
    """

    def __init__(
        self,
        *,
        transport: JsonTransport,
        artifact_loader: Callable[[str], bytes],
        endpoint_path: str = "/v2/vision",
        max_input_bytes: int = _MAX_IMAGE_BYTES,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if not endpoint_path.startswith("/"):
            raise ValueError("Lightning Vision V2 endpoint path must be absolute")
        if not 1 <= max_input_bytes <= _MAX_IMAGE_BYTES:
            raise ValueError("Lightning Vision V2 input limit cannot exceed the frozen 5 MB cap")
        self._transport = transport
        self._artifact_loader = artifact_loader
        self._endpoint_path = endpoint_path
        self._max_input_bytes = max_input_bytes
        self._clock = clock
        self._policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
        self._catalog = vision_profile_catalog_v2()

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionV2Result:
        return self._understand(request, narration_context=None)

    def understand_with_narration(
        self,
        request: VisionUnderstandingRequestV2,
        *,
        narration_context: str,
    ) -> VisionV2Result:
        context = narration_context.strip()
        if not context:
            return self._understand(request, narration_context=None)
        return self._understand(request, narration_context=context[:2_000])

    def _understand(
        self,
        request: VisionUnderstandingRequestV2,
        *,
        narration_context: str | None,
    ) -> VisionV2Result:
        profile = self._catalog.resolve(request.requested_profile_id)
        catalog_hash = vision_profile_catalog_hash_v2(self._catalog)
        if request.media_validation is None:
            return self._input_failure(
                request,
                profile.profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_PROVENANCE_MISSING,
            )
        if request.media_validation.decision != "PASS":
            return self._input_failure(
                request,
                profile.profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_NOT_PASSED,
            )
        try:
            image = self._artifact_loader(request.source_image_ref.artifact_ref)
        except (KeyError, OSError, ValueError):
            return self._input_failure(
                request,
                profile.profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
            )
        if not image or len(image) > self._max_input_bytes:
            return self._input_failure(
                request,
                profile.profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
            )
        digest = sha256(image).hexdigest()
        if digest != request.source_image_ref.sha256:
            return self._input_failure(
                request,
                profile.profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH,
            )
        content_type = _image_content_type(image)
        if content_type is None:
            return self._input_failure(
                request,
                profile.profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE,
            )

        payload = {
            "contract_name": "LightningVisionRequestV2",
            "contract_version": "2.0",
            "request": request.model_dump(mode="json"),
            "source_image": {
                "artifact_ref": request.source_image_ref.artifact_ref,
                "sha256": digest,
                "content_type": content_type,
                "content_base64": base64.b64encode(image).decode("ascii"),
            },
        }
        if narration_context is not None:
            payload["narration_context"] = narration_context
        try:
            raw_result = self._transport.post_json(self._endpoint_path, payload)
        except TimeoutError:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_TIMEOUT,
                VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED,
                retryable=False,
            )
        except LightningProviderError:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_PROVIDER_FAILURE,
                VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                retryable=False,
            )

        try:
            result = _RESULT_ADAPTER.validate_python(raw_result)
        except ValidationError:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_SCHEMA_INVALID,
                VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
                retryable=False,
            )
        if (
            result.correlation_id != request.correlation_id
            or result.source_image_ref != request.source_image_ref
            or result.profile_id != request.requested_profile_id
        ):
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_SCHEMA_INVALID,
                VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
                retryable=False,
            )
        if isinstance(result, VisionUnderstandingSuccessV2):
            try:
                blocked = self._policy.evaluate(collect_observed_texts_v2(result))
            except Exception:  # noqa: BLE001 - policy failure must fail closed
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_PROVIDER_FAILURE,
                    VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                    retryable=False,
                )
            if blocked is not None:
                return VisionUnderstandingFailureV2(
                    correlation_id=request.correlation_id,
                    executed_at=self._clock(),
                    source_image_ref=request.source_image_ref,
                    profile_id=profile.profile_id,
                    profile_catalog_hash=catalog_hash,
                    attempt_number=1,
                    repair_attempted=result.repair_attempted,
                    content_policy_version=self._policy.content_policy_version,
                    policy_match_view_version=self._policy.policy_match_view_version,
                    policy_execution_state="BLOCKED",
                    error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
                    error_detail=blocked,
                    retryable=False,
                    model_provenance=profile.model_provenance,
                )
        return result

    def _input_failure(
        self,
        request: VisionUnderstandingRequestV2,
        profile_id: VisionProfileIdV2,
        catalog_hash: str,
        detail: VisionNonPolicyErrorDetailV2,
    ) -> VisionUnderstandingFailureV2:
        return VisionUnderstandingFailureV2(
            correlation_id=request.correlation_id,
            executed_at=self._clock(),
            source_image_ref=request.source_image_ref,
            profile_id=profile_id,
            profile_catalog_hash=catalog_hash,
            attempt_number=0,
            repair_attempted=False,
            content_policy_version=self._policy.content_policy_version,
            policy_match_view_version=self._policy.policy_match_view_version,
            policy_execution_state="NOT_EXECUTED",
            error_code=VisionErrorCode.INPUT_NOT_VALIDATED,
            error_detail=detail,
            retryable=False,
        )

    def _runtime_failure(
        self,
        request: VisionUnderstandingRequestV2,
        profile: VisionProfileV2,
        catalog_hash: str,
        error_code: VisionErrorCode,
        detail: VisionNonPolicyErrorDetailV2,
        *,
        retryable: bool,
    ) -> VisionUnderstandingFailureV2:
        return VisionUnderstandingFailureV2(
            correlation_id=request.correlation_id,
            executed_at=self._clock(),
            source_image_ref=request.source_image_ref,
            profile_id=profile.profile_id,
            profile_catalog_hash=catalog_hash,
            attempt_number=1,
            repair_attempted=False,
            content_policy_version=self._policy.content_policy_version,
            policy_match_view_version=self._policy.policy_match_view_version,
            policy_execution_state="NOT_EXECUTED",
            error_code=error_code,
            error_detail=detail,
            retryable=retryable,
            model_provenance=profile.model_provenance,
        )


def _image_content_type(image: bytes) -> str | None:
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


__all__ = ["LightningVisionV2Adapter"]
