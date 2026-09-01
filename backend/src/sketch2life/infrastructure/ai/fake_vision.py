"""Deterministic, fixture-driven Phase A vision-understanding adapter.

Owns all input-integrity verification at ingress (profile resolution, linked P2-T1
`PASS`, source image readability and hash) before any simulated inference, per
`plan/P2_T3_VISION_RESEARCH_PLAN.md`, "Input integrity ownership". The interface-only
`VisionUnderstandingPort` performs no file or hash operation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.ports.vision_understanding import VisionUnderstandingPort
from sketch2life.contracts.schemas.vision import (
    ObservedTextV1,
    VisionErrorCode,
    VisionNonPolicyErrorDetail,
    VisionProfileCatalogV1,
    VisionProfileV1,
    VisionUnderstandingFailureV1,
    VisionUnderstandingRequestV1,
    VisionUnderstandingResultV1,
    VisionUnderstandingSuccessV1,
    vision_profile_catalog,
    vision_profile_catalog_hash,
    vision_profile_config_hash,
)

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n(.*)\n```$", re.DOTALL)


class FakeVisionScenario(StrEnum):
    RAW_OUTPUT = "RAW_OUTPUT"
    PROVIDER_TRANSIENT_SUCCESS = "PROVIDER_TRANSIENT_SUCCESS"
    PROVIDER_TRANSIENT_FAILURE = "PROVIDER_TRANSIENT_FAILURE"
    PROVIDER_PERMANENT_FAILURE = "PROVIDER_PERMANENT_FAILURE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True, slots=True)
class FakeVisionFixture:
    """`image_path` is opened and hashed for real; `raw_output` simulates model text."""

    scenario: FakeVisionScenario
    image_path: Path
    raw_output: str = ""


class DeterministicFixtureVisionAdapter(VisionUnderstandingPort):
    """Maps synthetic fixture references to contracts without loading or invoking a model."""

    _EXECUTED_AT = datetime(2026, 8, 31, tzinfo=UTC)

    def __init__(
        self,
        fixtures: dict[str, FakeVisionFixture],
        *,
        content_policy: ObservableContentPolicyV1,
        catalog: VisionProfileCatalogV1 | None = None,
    ) -> None:
        self._fixtures = dict(fixtures)
        self._policy = content_policy
        self._catalog = catalog if catalog is not None else vision_profile_catalog()

    def understand(self, request: VisionUnderstandingRequestV1) -> VisionUnderstandingResultV1:
        profile = self._catalog.resolve(request.requested_profile_id)
        catalog_hash = vision_profile_catalog_hash(self._catalog)

        if request.media_validation is None:
            return self._input_failure(
                request,
                catalog_hash,
                VisionNonPolicyErrorDetail.MEDIA_VALIDATION_PROVENANCE_MISSING,
            )
        if request.media_validation.decision != "PASS":
            return self._input_failure(
                request, catalog_hash, VisionNonPolicyErrorDetail.MEDIA_VALIDATION_NOT_PASSED
            )

        fixture = self._fixtures.get(request.source_image_ref.artifact_ref)
        if fixture is None:
            return self._input_failure(
                request, catalog_hash, VisionNonPolicyErrorDetail.SOURCE_IMAGE_UNREADABLE
            )

        try:
            image_bytes = fixture.image_path.read_bytes()
        except OSError:
            return self._input_failure(
                request, catalog_hash, VisionNonPolicyErrorDetail.SOURCE_IMAGE_UNREADABLE
            )
        if sha256(image_bytes).hexdigest() != request.source_image_ref.sha256:
            return self._input_failure(
                request, catalog_hash, VisionNonPolicyErrorDetail.SOURCE_IMAGE_HASH_MISMATCH
            )

        if fixture.scenario is FakeVisionScenario.MODEL_UNAVAILABLE:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_MODEL_UNAVAILABLE,
                VisionNonPolicyErrorDetail.MODEL_LOAD_FAILED,
                attempt_number=1,
                retryable=False,
            )
        if fixture.scenario is FakeVisionScenario.DEVICE_UNAVAILABLE:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_MODEL_UNAVAILABLE,
                VisionNonPolicyErrorDetail.DEVICE_UNAVAILABLE,
                attempt_number=1,
                retryable=False,
            )
        if fixture.scenario is FakeVisionScenario.TIMEOUT:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_TIMEOUT,
                VisionNonPolicyErrorDetail.TIMEOUT_BUDGET_EXCEEDED,
                attempt_number=1,
                retryable=False,
            )
        if fixture.scenario is FakeVisionScenario.PROVIDER_TRANSIENT_FAILURE:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_PROVIDER_FAILURE,
                VisionNonPolicyErrorDetail.TRANSIENT_RUNTIME_FAILURE,
                attempt_number=2,
                retryable=True,
            )
        if fixture.scenario is FakeVisionScenario.PROVIDER_PERMANENT_FAILURE:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_PROVIDER_FAILURE,
                VisionNonPolicyErrorDetail.PERMANENT_RUNTIME_FAILURE,
                attempt_number=1,
                retryable=False,
            )

        attempt_number = (
            2 if fixture.scenario is FakeVisionScenario.PROVIDER_TRANSIENT_SUCCESS else 1
        )
        return self._map_raw_output(
            request, profile, catalog_hash, fixture.raw_output, attempt_number
        )

    def _map_raw_output(
        self,
        request: VisionUnderstandingRequestV1,
        profile: VisionProfileV1,
        catalog_hash: str,
        raw_output: str,
        attempt_number: int,
    ) -> VisionUnderstandingResultV1:
        payload, repair_attempted = _parse_raw_output(raw_output)
        if payload is None:
            return self._schema_failure(
                request,
                profile,
                catalog_hash,
                VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED,
                attempt_number=attempt_number,
                repair_attempted=repair_attempted,
            )

        merged: dict[str, Any] = {
            **payload,
            "correlation_id": request.correlation_id,
            "executed_at": self._EXECUTED_AT,
            "source_image_ref": request.source_image_ref,
            "profile_id": profile.profile_id,
            "profile_catalog_hash": catalog_hash,
            "attempt_number": attempt_number,
            "repair_attempted": repair_attempted,
            "content_policy_version": self._policy.content_policy_version,
            "policy_match_view_version": self._policy.policy_match_view_version,
            "policy_execution_state": "PASSED",
            "status": "SUCCEEDED",
            "adapter_version": profile.adapter_version,
            "config_hash": vision_profile_config_hash(profile),
        }
        try:
            success = VisionUnderstandingSuccessV1.model_validate(merged)
        except ValidationError as error:
            return self._schema_failure(
                request,
                profile,
                catalog_hash,
                _classify_schema_error(error),
                attempt_number=attempt_number,
                repair_attempted=repair_attempted,
            )

        category = self._policy.evaluate(_collect_observed_texts(success))
        if category is not None:
            return VisionUnderstandingFailureV1(
                correlation_id=request.correlation_id,
                executed_at=self._EXECUTED_AT,
                source_image_ref=request.source_image_ref,
                profile_id=profile.profile_id,
                profile_catalog_hash=catalog_hash,
                attempt_number=attempt_number,
                repair_attempted=repair_attempted,
                content_policy_version=self._policy.content_policy_version,
                policy_match_view_version=self._policy.policy_match_view_version,
                policy_execution_state="BLOCKED",
                error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
                error_detail=category,
                retryable=False,
            )
        return success

    def _input_failure(
        self,
        request: VisionUnderstandingRequestV1,
        catalog_hash: str,
        detail: VisionNonPolicyErrorDetail,
    ) -> VisionUnderstandingFailureV1:
        profile = self._catalog.resolve(request.requested_profile_id)
        return VisionUnderstandingFailureV1(
            correlation_id=request.correlation_id,
            executed_at=self._EXECUTED_AT,
            source_image_ref=request.source_image_ref,
            profile_id=profile.profile_id,
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
        request: VisionUnderstandingRequestV1,
        profile: VisionProfileV1,
        catalog_hash: str,
        error_code: VisionErrorCode,
        detail: VisionNonPolicyErrorDetail,
        *,
        attempt_number: int,
        retryable: bool,
    ) -> VisionUnderstandingFailureV1:
        return VisionUnderstandingFailureV1(
            correlation_id=request.correlation_id,
            executed_at=self._EXECUTED_AT,
            source_image_ref=request.source_image_ref,
            profile_id=profile.profile_id,
            profile_catalog_hash=catalog_hash,
            attempt_number=attempt_number,
            repair_attempted=False,
            content_policy_version=self._policy.content_policy_version,
            policy_match_view_version=self._policy.policy_match_view_version,
            policy_execution_state="NOT_EXECUTED",
            error_code=error_code,
            error_detail=detail,
            retryable=retryable,
        )

    def _schema_failure(
        self,
        request: VisionUnderstandingRequestV1,
        profile: VisionProfileV1,
        catalog_hash: str,
        detail: VisionNonPolicyErrorDetail,
        *,
        attempt_number: int,
        repair_attempted: bool,
    ) -> VisionUnderstandingFailureV1:
        return VisionUnderstandingFailureV1(
            correlation_id=request.correlation_id,
            executed_at=self._EXECUTED_AT,
            source_image_ref=request.source_image_ref,
            profile_id=profile.profile_id,
            profile_catalog_hash=catalog_hash,
            attempt_number=attempt_number,
            repair_attempted=repair_attempted,
            content_policy_version=self._policy.content_policy_version,
            policy_match_view_version=self._policy.policy_match_view_version,
            policy_execution_state="NOT_EXECUTED",
            error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
            error_detail=detail,
            retryable=False,
        )


def _parse_raw_output(raw_output: str) -> tuple[dict[str, Any] | None, bool]:
    """Lossless-only repair: a Markdown fence is unwrapped only when it encloses complete JSON.

    Never completes truncated JSON, closes delimiters, fills defaults, or coerces values.
    """

    fence_match = _FENCE_PATTERN.match(raw_output.strip())
    if fence_match is not None:
        try:
            parsed = json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            return None, False
        return (parsed, True) if isinstance(parsed, dict) else (None, False)

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return None, False
    return (parsed, False) if isinstance(parsed, dict) else (None, False)


def _classify_schema_error(error: ValidationError) -> VisionNonPolicyErrorDetail:
    for item in error.errors():
        message = str(item.get("msg", ""))
        if "DUPLICATE_OBSERVATION_ID" in message:
            return VisionNonPolicyErrorDetail.DUPLICATE_OBSERVATION_ID
        if "REFERENCE_INTEGRITY_VIOLATION" in message:
            return VisionNonPolicyErrorDetail.REFERENCE_INTEGRITY_VIOLATION
    return VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED


def _collect_observed_texts(success: VisionUnderstandingSuccessV1) -> tuple[ObservedTextV1, ...]:
    texts: list[ObservedTextV1] = []
    texts.extend(entity.label for entity in success.entities)
    texts.extend(action.label for action in success.actions)
    texts.extend(relation.predicate for relation in success.relations)
    texts.extend(theme.label for theme in success.themes)
    texts.extend(region.note for region in success.ambiguous_regions)
    return tuple(texts)
