"""Host preflight observation producer for FEAT-018 A-LIVE-W1.

The producer takes explicit inputs only. It reads one bounded snapshot of the host fixture,
calls the injected D2 admission and image-only validation services, recomputes the bound
validation-artifact digest, and compares the prompt, typed runtime-config and
content-policy identities. Each service performs its own bounded read, so every digest
must agree with the producer's snapshot.

The result is a closed observation. It authorizes no run, reads no Git state, checks no
evidence destination and never returns fixture bytes, paths, prompt text or exception
text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Protocol, get_args

from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018AdmissionResult,
)
from sketch2life.application.services.media_validation import ImageOnlyValidationRequest
from sketch2life.benchmark.feat018_live_lightning_binding import runtime_config_sha256
from sketch2life.contracts.schemas.feat018_live_wiring import (
    AdmissionOutcomeValue,
    HostPreflightFailureCode,
    LiveHostPreflightObservationV1,
    LiveObservationInputError,
    ValidationDecisionValue,
)
from sketch2life.contracts.schemas.media_validation import (
    ImageOnlyValidationResultV1,
    canonical_image_only_validation_bytes,
    image_only_validation_artifact_sha256,
    try_create_image_only_artifact_reference,
)
from sketch2life.domain.understanding.image_admission import AdmissionOutcome, AdmissionReason
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

MAX_FIXTURE_BYTES_CEILING = 64 * 1024 * 1024
_READ_CHUNK_BYTES = 1024 * 1024
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_SAFE_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_CODE_ORDER: tuple[HostPreflightFailureCode, ...] = get_args(HostPreflightFailureCode)
_OUTCOME_VALUES: dict[AdmissionOutcome, AdmissionOutcomeValue] = {
    AdmissionOutcome.ADMITTED: "ADMITTED",
    AdmissionOutcome.REJECTED: "REJECTED",
    AdmissionOutcome.UNSUPPORTED: "UNSUPPORTED",
    AdmissionOutcome.INVALID_SOURCE: "INVALID_SOURCE",
    AdmissionOutcome.PROCESSING_FAILURE: "PROCESSING_FAILURE",
}


class AdmissionService(Protocol):
    def admit(self, request: Feat018AdmissionRequest) -> Feat018AdmissionResult: ...


class ImageOnlyValidationService(Protocol):
    def validate(self, request: ImageOnlyValidationRequest) -> ImageOnlyValidationResultV1: ...


@dataclass(frozen=True, slots=True)
class HostPreflightInputs:
    """Explicit expectations; repr hides the fixture path, prompt and private objects."""

    fixture_path: Path = field(repr=False)
    max_fixture_bytes: int
    expected_source_sha256: str
    validation_artifact_ref: str
    expected_validator_identity: str
    expected_validator_policy_version: str
    expected_validation_artifact_sha256: str | None
    prompt: str = field(repr=False)
    expected_prompt_sha256: str
    runtime_config: QwenVisionRuntimeConfig = field(repr=False)
    expected_runtime_config_sha256: str
    content_policy: object = field(repr=False)
    expected_content_policy_version: str
    expected_policy_match_view_version: str


@dataclass(frozen=True, slots=True)
class _AdmissionFacts:
    outcome: AdmissionOutcomeValue = "NOT_RUN"
    reason: str | None = None
    digest: str | None = None


@dataclass(frozen=True, slots=True)
class _ValidationFacts:
    decision: ValidationDecisionValue = "NOT_RUN"
    failure_code: str | None = None
    identity_verified: bool = False
    artifact_sha256: str | None = None
    source_sha256: str | None = None


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _is_safe_identity(value: object) -> bool:
    return type(value) is str and _SAFE_IDENTITY.fullmatch(value) is not None


def _check_inputs(inputs: HostPreflightInputs) -> None:
    if type(inputs) is not HostPreflightInputs:
        raise LiveObservationInputError()
    if not isinstance(inputs.fixture_path, Path) or "\x00" in str(inputs.fixture_path):
        raise LiveObservationInputError()
    limit = inputs.max_fixture_bytes
    if type(limit) is not int or not 0 < limit <= MAX_FIXTURE_BYTES_CEILING:
        raise LiveObservationInputError()
    digests: tuple[object, ...] = (
        inputs.expected_source_sha256,
        inputs.expected_prompt_sha256,
        inputs.expected_runtime_config_sha256,
    )
    if not all(_is_sha256(value) for value in digests):
        raise LiveObservationInputError()
    expected_artifact = inputs.expected_validation_artifact_sha256
    if expected_artifact is not None and not _is_sha256(expected_artifact):
        raise LiveObservationInputError()
    reference = inputs.validation_artifact_ref
    if (
        not _is_safe_identity(reference)
        or try_create_image_only_artifact_reference(reference) is None
    ):
        raise LiveObservationInputError()
    identities: tuple[object, ...] = (
        inputs.expected_validator_identity,
        inputs.expected_validator_policy_version,
        inputs.expected_content_policy_version,
        inputs.expected_policy_match_view_version,
    )
    if not all(_is_safe_identity(value) for value in identities):
        raise LiveObservationInputError()
    if type(inputs.runtime_config) is not QwenVisionRuntimeConfig:
        raise LiveObservationInputError()


def _read_snapshot(
    path: Path, limit: int
) -> tuple[bytes | None, HostPreflightFailureCode | None]:
    chunks: list[bytes] = []
    total = 0
    try:
        with path.open("rb") as source:
            while total <= limit:
                chunk = source.read(min(_READ_CHUNK_BYTES, limit + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
    except FileNotFoundError:
        return None, "FIXTURE_MISSING"
    except (OSError, RuntimeError, ValueError):
        return None, "FIXTURE_UNREADABLE"
    if total > limit:
        return None, "FIXTURE_TOO_LARGE"
    return b"".join(chunks), None


def _observe_admission(
    admission: AdmissionService, path: Path, reference: str
) -> tuple[_AdmissionFacts, list[HostPreflightFailureCode]]:
    try:
        result = admission.admit(Feat018AdmissionRequest(path=path, artifact_ref=reference))
        if type(result) is not Feat018AdmissionResult:
            raise TypeError
        decision = result.decision
        outcome = AdmissionOutcome(decision.outcome)
        outcome_value = _OUTCOME_VALUES[outcome]
        reason = None if decision.reason is None else AdmissionReason(decision.reason)
        digest = decision.digest
        if (outcome is AdmissionOutcome.ADMITTED) != (reason is None):
            raise ValueError
        if digest is not None and not _is_sha256(digest):
            raise ValueError
        if outcome is AdmissionOutcome.ADMITTED and (
            result.source is None
            or result.source.artifact_ref != reference
            or result.source.sha256 != digest
            or digest is None
        ):
            raise ValueError
    except Exception:  # noqa: BLE001 - only a closed code leaves this boundary
        return _AdmissionFacts(), ["ADMISSION_EXCEPTION"]
    facts = _AdmissionFacts(
        outcome=outcome_value,
        reason=None if reason is None else reason.value,
        digest=digest,
    )
    codes: list[HostPreflightFailureCode] = []
    if outcome is not AdmissionOutcome.ADMITTED:
        codes.append("ADMISSION_NOT_ADMITTED")
    return facts, codes


def _observe_validation(
    validator: ImageOnlyValidationService,
    path: Path,
    reference: str,
    inputs: HostPreflightInputs,
) -> tuple[_ValidationFacts, list[HostPreflightFailureCode]]:
    request = ImageOnlyValidationRequest(
        image_path=path,
        image_artifact_ref=reference,
        expected_source_sha256=inputs.expected_source_sha256,
    )
    try:
        result = validator.validate(request)
        if type(result) is not ImageOnlyValidationResultV1:
            raise TypeError
        # Re-parse through the protected ingress: unchecked instances cannot pass.
        payload = canonical_image_only_validation_bytes(result)
        checked = ImageOnlyValidationResultV1.model_validate_json(payload)
        if canonical_image_only_validation_bytes(checked) != payload:
            raise ValueError
    except Exception:  # noqa: BLE001 - only a closed code leaves this boundary
        return _ValidationFacts(), ["VALIDATION_EXCEPTION"]
    identity_verified = (
        checked.validator_identity == inputs.expected_validator_identity
        and checked.policy_identity == inputs.expected_validator_policy_version
        and checked.source_artifact_ref == reference
    )
    decision: ValidationDecisionValue = "PASS" if checked.status.value == "PASS" else "FAIL"
    facts = _ValidationFacts(
        decision=decision,
        failure_code=None if checked.failure_code is None else checked.failure_code.value,
        identity_verified=identity_verified,
        artifact_sha256=image_only_validation_artifact_sha256(checked),
        source_sha256=checked.source_sha256,
    )
    codes: list[HostPreflightFailureCode] = []
    if decision != "PASS":
        codes.append("VALIDATION_NOT_PASS")
    if not identity_verified:
        codes.append("VALIDATION_IDENTITY_MISMATCH")
    return facts, codes


def _prompt_check(prompt: object, expected: str) -> HostPreflightFailureCode | None:
    if type(prompt) is not str or not prompt:
        return "PROMPT_INVALID"
    try:
        digest = sha256(prompt.encode("utf-8")).hexdigest()
    except UnicodeError:
        return "PROMPT_INVALID"
    return None if digest == expected else "PROMPT_HASH_MISMATCH"


def _runtime_config_verified(config: QwenVisionRuntimeConfig, expected: str) -> bool:
    try:
        return runtime_config_sha256(config) == expected
    except Exception:  # noqa: BLE001 - a failed identity computation is a mismatch
        return False


def _policy_verified(policy: object, version: str, view_version: str) -> bool:
    try:
        declared_version = getattr(policy, "content_policy_version", None)
        declared_view = getattr(policy, "policy_match_view_version", None)
        evaluate = getattr(policy, "evaluate", None)
    except Exception:  # noqa: BLE001 - an unreadable policy identity is a mismatch
        return False
    return (
        type(declared_version) is str
        and type(declared_view) is str
        and declared_version == version
        and declared_view == view_version
        and callable(evaluate)
    )


def observe_host_preflight(
    inputs: HostPreflightInputs,
    *,
    admission: AdmissionService,
    validator: ImageOnlyValidationService,
) -> LiveHostPreflightObservationV1:
    """Observe one host fixture and the caller identities; fail closed on every mismatch."""

    _check_inputs(inputs)
    codes: list[HostPreflightFailureCode] = []
    snapshot, read_code = _read_snapshot(inputs.fixture_path, inputs.max_fixture_bytes)
    observed = None if snapshot is None else sha256(snapshot).hexdigest()
    del snapshot
    source_matches = observed is not None and observed == inputs.expected_source_sha256
    admission_facts = _AdmissionFacts()
    validation_facts = _ValidationFacts()
    source_stable: bool | None = None
    if read_code is not None:
        codes.append(read_code)
    elif not source_matches:
        codes.append("SOURCE_DIGEST_MISMATCH")
    else:
        reference = inputs.validation_artifact_ref
        admission_facts, admission_codes = _observe_admission(
            admission, inputs.fixture_path, reference
        )
        validation_facts, validation_codes = _observe_validation(
            validator, inputs.fixture_path, reference, inputs
        )
        codes.extend(admission_codes)
        codes.extend(validation_codes)
        # Stability is a comparison: it is reported only when a service returned a digest.
        service_digests = [
            digest
            for digest in (admission_facts.digest, validation_facts.source_sha256)
            if digest is not None
        ]
        if service_digests:
            source_stable = all(digest == observed for digest in service_digests)
            if not source_stable:
                codes.append("SOURCE_UNSTABLE")

    expected_artifact = inputs.expected_validation_artifact_sha256
    artifact_matches: bool | None = None
    if expected_artifact is not None and validation_facts.artifact_sha256 is not None:
        artifact_matches = validation_facts.artifact_sha256 == expected_artifact
        if not artifact_matches:
            codes.append("VALIDATION_ARTIFACT_MISMATCH")

    prompt_code = _prompt_check(inputs.prompt, inputs.expected_prompt_sha256)
    if prompt_code is not None:
        codes.append(prompt_code)
    runtime_verified = _runtime_config_verified(
        inputs.runtime_config, inputs.expected_runtime_config_sha256
    )
    if not runtime_verified:
        codes.append("RUNTIME_CONFIG_IDENTITY_MISMATCH")
    policy_verified = _policy_verified(
        inputs.content_policy,
        inputs.expected_content_policy_version,
        inputs.expected_policy_match_view_version,
    )
    if not policy_verified:
        codes.append("POLICY_IDENTITY_MISMATCH")

    ordered = tuple(code for code in _CODE_ORDER if code in codes)
    return LiveHostPreflightObservationV1(
        validation_artifact_ref=inputs.validation_artifact_ref,
        expected_source_sha256=inputs.expected_source_sha256,
        observed_source_sha256=observed,
        source_matches=source_matches,
        source_stable=source_stable,
        admission_outcome=admission_facts.outcome,
        admission_reason=admission_facts.reason,
        validation_decision=validation_facts.decision,
        validation_failure_code=validation_facts.failure_code,
        validator_identity_verified=validation_facts.identity_verified,
        validation_artifact_sha256=validation_facts.artifact_sha256,
        expected_validation_artifact_sha256=expected_artifact,
        validation_artifact_matches=artifact_matches,
        prompt_hash_verified=prompt_code is None,
        runtime_config_identity_verified=runtime_verified,
        policy_identity_verified=policy_verified,
        accepted=not ordered,
        failure_codes=ordered,
    )


__all__ = [
    "MAX_FIXTURE_BYTES_CEILING",
    "AdmissionService",
    "HostPreflightInputs",
    "ImageOnlyValidationService",
    "observe_host_preflight",
]
