"""Lazy-imported local Qwen vision adapter for the approved Phase B B1 slice.

The adapter owns ingress integrity checks and maps every provider/runtime outcome
to the V2 contract.  The default generation runner isolates synchronous model
generation in a killable subprocess; this avoids abandoning an in-flight GPU
thread when the deadline expires.  Test callers can inject an in-process runner
or model factory without importing optional Qwen dependencies.
"""

from __future__ import annotations

import importlib
import json
import multiprocessing
import re
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import ValidationError

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    collect_observed_texts_v2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    QwenVisionRuntimeConfig,
)

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n(.*)\n```$", re.DOTALL)
_ALLOWED_PROVIDER_KEYS = frozenset(
    {"entities", "actions", "relations", "themes", "ambiguous_regions"}
)
_DEVICE_ERROR_KEYWORDS = (
    "cuda",
    "cudnn",
    "cublas",
    "device",
    "gpu",
    "out of memory",
    "oom",
)


class QwenModelLoadError(Exception):
    """Optional runtime, model, or weight loading failed."""


class QwenDeviceUnavailableError(Exception):
    """The configured device cannot be used for model loading."""


class QwenTimeoutError(TimeoutError):
    """The generation subprocess was terminated at the configured deadline."""


class QwenTransientRuntimeError(Exception):
    """A sanitized transient runtime classification used by injected test runners."""


class QwenPermanentRuntimeError(Exception):
    """A sanitized permanent runtime classification."""


class QwenModelLike(Protocol):
    device: Any

    def generate(self, **kwargs: Any) -> Any: ...


class QwenProcessorLike(Protocol):
    def apply_chat_template(self, messages: Any, **kwargs: Any) -> Any: ...

    def batch_decode(self, token_ids: Any, **kwargs: Any) -> Any: ...


@dataclass(frozen=True, slots=True)
class QwenModelBundle:
    """The two optional-runtime objects needed for one local generation call."""

    model: QwenModelLike
    processor: QwenProcessorLike


ModelFactory = Callable[[VisionProfileV2, QwenVisionRuntimeConfig], QwenModelBundle]
PromptBuilder = Callable[[VisionUnderstandingRequestV2], str]
TransientClassifier = Callable[[BaseException], bool]
RawOutputHook = Callable[[str], None]


class QwenGenerationRunner(Protocol):
    """Provider execution seam; raw output remains in memory inside the adapter."""

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str: ...


def _never_transient(_exc: BaseException) -> bool:
    """Do not infer retryability until B2 observes the provider's failure taxonomy."""

    return False


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _looks_like_device_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(keyword in message for keyword in _DEVICE_ERROR_KEYWORDS)


def _default_model_factory(
    profile: VisionProfileV2, runtime_config: QwenVisionRuntimeConfig
) -> QwenModelBundle:
    """Load Qwen lazily; missing optional packages become sanitized typed errors."""

    try:
        torch_module = cast(Any, importlib.import_module("torch"))
        transformers_module = cast(Any, importlib.import_module("transformers"))
        auto_processor = transformers_module.AutoProcessor
        model_class = transformers_module.Qwen3VLForConditionalGeneration
    except Exception as exc:  # noqa: BLE001 - raw optional-runtime detail never crosses boundary
        if _looks_like_device_error(exc):
            raise QwenDeviceUnavailableError from None
        raise QwenModelLoadError from None

    if runtime_config.device != "cuda":
        raise QwenDeviceUnavailableError
    try:
        if not bool(torch_module.cuda.is_available()):
            raise QwenDeviceUnavailableError
    except QwenDeviceUnavailableError:
        raise
    except Exception as exc:  # noqa: BLE001 - sanitized below
        if _looks_like_device_error(exc):
            raise QwenDeviceUnavailableError from None
        raise QwenModelLoadError from None

    model_identifier = profile.model_provenance.model_identifier
    model_reference = runtime_config.model_reference(model_identifier)
    shared_kwargs: dict[str, object] = {
        "revision": profile.model_provenance.model_revision,
        "dtype": torch_module.bfloat16,
        "device_map": "auto",
        "local_files_only": not runtime_config.allow_model_download,
    }
    if runtime_config.model_cache_dir is not None:
        shared_kwargs["cache_dir"] = str(runtime_config.model_cache_dir)

    try:
        model = model_class.from_pretrained(model_reference, **shared_kwargs)
        processor = auto_processor.from_pretrained(model_reference, **shared_kwargs)
        eval_method = getattr(model, "eval", None)
        if callable(eval_method):
            eval_method()
    except QwenDeviceUnavailableError:
        raise
    except Exception as exc:  # noqa: BLE001 - model text/paths never cross the port
        if _looks_like_device_error(exc):
            raise QwenDeviceUnavailableError from None
        raise QwenModelLoadError from None

    return QwenModelBundle(
        model=cast(QwenModelLike, model),
        processor=cast(QwenProcessorLike, processor),
    )


def _coerce_model_bundle(
    value: QwenModelBundle | tuple[QwenModelLike, QwenProcessorLike]
) -> QwenModelBundle:
    if isinstance(value, QwenModelBundle):
        return value
    if isinstance(value, tuple) and len(value) == 2:
        return QwenModelBundle(model=value[0], processor=value[1])
    raise QwenModelLoadError


def _generate_from_bundle(
    bundle: QwenModelBundle,
    profile: VisionProfileV2,
    image_path: Path,
    prompt: str,
) -> str:
    """Use only the provider calls whose exact parameter mapping is B2-verifiable."""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    try:
        inputs = bundle.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        to_method = getattr(inputs, "to", None)
        if callable(to_method):
            inputs = to_method(bundle.model.device)
        if not isinstance(inputs, Mapping):
            raise QwenPermanentRuntimeError

        input_ids = inputs.get("input_ids")
        if input_ids is None:
            raise QwenPermanentRuntimeError
        generated_ids = bundle.model.generate(
            **dict(inputs),
            do_sample=profile.decoding.sampling_enabled,
            num_beams=profile.decoding.beam_count,
            max_new_tokens=profile.decoding.max_new_tokens,
            repetition_penalty=profile.decoding.repetition_penalty,
        )
        trimmed_ids = [
            output_ids[len(input_sequence) :]
            for input_sequence, output_ids in zip(input_ids, generated_ids, strict=True)
        ]
        decoded = bundle.processor.batch_decode(
            trimmed_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
    except (QwenPermanentRuntimeError, QwenTimeoutError):
        raise
    except TimeoutError:
        raise QwenTimeoutError from None
    except Exception as exc:  # noqa: BLE001 - sanitized by the caller
        if _looks_like_device_error(exc):
            raise QwenPermanentRuntimeError from None
        raise QwenPermanentRuntimeError from None

    if not isinstance(decoded, (list, tuple)) or len(decoded) != 1:
        raise QwenPermanentRuntimeError
    raw_output = decoded[0]
    if not isinstance(raw_output, str):
        raise QwenPermanentRuntimeError
    return raw_output


class TransformersQwenGenerationRunner:
    """In-process testable runner; real default calls use the killable subprocess runner."""

    def __init__(self, model_factory: ModelFactory = _default_model_factory) -> None:
        self._model_factory = model_factory

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        try:
            bundle_value = self._model_factory(profile, runtime_config)
            bundle = _coerce_model_bundle(bundle_value)
        except (QwenModelLoadError, QwenDeviceUnavailableError):
            raise
        except Exception as exc:  # noqa: BLE001 - no raw model exception crosses the adapter
            if _looks_like_device_error(exc):
                raise QwenDeviceUnavailableError from None
            raise QwenModelLoadError from None
        return _generate_from_bundle(bundle, profile, image_path, prompt)


def _send_worker_message(connection: Connection, kind: str, value: object = None) -> None:
    with suppress(BrokenPipeError, EOFError, OSError):
        connection.send((kind, value))


def _qwen_worker_entry(
    connection: Connection,
    profile: VisionProfileV2,
    runtime_config: QwenVisionRuntimeConfig,
    image_path: str,
    prompt: str,
) -> None:
    """Load and run the optional model inside a process the parent can terminate."""

    try:
        bundle = _default_model_factory(profile, runtime_config)
    except QwenDeviceUnavailableError:
        _send_worker_message(connection, "device_unavailable")
        return
    except QwenModelLoadError:
        _send_worker_message(connection, "model_load_failed")
        return
    except Exception:
        _send_worker_message(connection, "model_load_failed")
        return

    try:
        raw_output = _generate_from_bundle(bundle, profile, Path(image_path), prompt)
    except QwenTimeoutError:
        _send_worker_message(connection, "timeout")
    except Exception:
        _send_worker_message(connection, "provider_failure")
    else:
        _send_worker_message(connection, "success", raw_output)


def _terminate_worker(process: BaseProcess) -> None:
    if process.is_alive():
        process.terminate()
        process.join(timeout=1.0)
    if process.is_alive():
        kill_method = getattr(process, "kill", None)
        if callable(kill_method):
            kill_method()
        process.join(timeout=1.0)


class KillableSubprocessQwenGenerationRunner:
    """Default runner: deadline expiry terminates the process that owns model state."""

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        context = multiprocessing.get_context("spawn")
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(
            target=_qwen_worker_entry,
            args=(sender, profile, runtime_config, str(image_path), prompt),
            daemon=True,
        )
        try:
            process.start()
        except Exception:
            receiver.close()
            sender.close()
            raise QwenModelLoadError from None
        sender.close()

        try:
            if not receiver.poll(profile.timeout_seconds):
                _terminate_worker(process)
                raise QwenTimeoutError
            message = receiver.recv()
            process.join(timeout=1.0)
        except (EOFError, OSError):
            raise QwenPermanentRuntimeError from None
        finally:
            if process.is_alive():
                _terminate_worker(process)
            receiver.close()

        if not isinstance(message, tuple) or len(message) != 2:
            raise QwenPermanentRuntimeError
        kind, value = message
        if kind == "success" and isinstance(value, str):
            return value
        if kind == "model_load_failed":
            raise QwenModelLoadError
        if kind == "device_unavailable":
            raise QwenDeviceUnavailableError
        if kind == "timeout":
            raise QwenTimeoutError
        raise QwenPermanentRuntimeError


def _default_prompt_builder(_request: VisionUnderstandingRequestV2) -> str:
    """No prompt text is committed; B2 callers inject the reviewed prompt explicitly."""

    return ""


class QwenVisionAdapter(VisionUnderstandingPortV2):
    """Real Qwen V2 adapter with typed failures and no raw-output leakage.

    ``on_raw_output``, when supplied, is an internal diagnostic seam only (used by the
    P2-T3 Phase B B3 mapping study): it is invoked with the raw provider string once a
    generation call succeeds, before any parsing/classification happens here. It never
    changes this adapter's return value, is never wired into any default/production
    construction, and adds no field to any public V1/V2 contract. A hook exception is
    swallowed so a diagnostic failure can never turn a real understanding call into an
    uncaught exception.
    """

    def __init__(
        self,
        runtime_config: QwenVisionRuntimeConfig,
        *,
        content_policy: ObservableContentPolicyV1,
        prompt_builder: PromptBuilder | None = None,
        prompt: str | None = None,
        generation_runner: QwenGenerationRunner | None = None,
        model_factory: ModelFactory | None = None,
        classify_transient: TransientClassifier = _never_transient,
        clock: Callable[[], datetime] = _utc_now,
        on_raw_output: RawOutputHook | None = None,
    ) -> None:
        if prompt is not None and prompt_builder is not None:
            raise ValueError("provide prompt or prompt_builder, not both")
        self._runtime_config = runtime_config
        self._policy = content_policy
        self._catalog = vision_profile_catalog_v2()
        self._prompt_builder: PromptBuilder = prompt_builder or _default_prompt_builder
        if prompt is not None:
            self._prompt_builder = lambda _request: prompt
        if generation_runner is not None and model_factory is not None:
            raise ValueError("provide generation_runner or model_factory, not both")
        if generation_runner is not None:
            self._generation_runner = generation_runner
        elif model_factory is not None:
            self._generation_runner = TransformersQwenGenerationRunner(model_factory)
        else:
            self._generation_runner = KillableSubprocessQwenGenerationRunner()
        self._classify_transient = classify_transient
        self._clock = clock
        self._on_raw_output = on_raw_output

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        catalog_hash = vision_profile_catalog_hash_v2(self._catalog)
        try:
            profile = self._catalog.resolve(request.requested_profile_id)
        except (TypeError, ValueError):
            return self._input_failure(
                request,
                request.requested_profile_id,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE,
            )

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
            image_path = self._resolve_verified_input_image(request)
        except _InputImageIntegrityError as exc:
            return self._input_failure(request, profile.profile_id, catalog_hash, exc.detail)

        try:
            prompt = self._prompt_builder(request)
        except Exception:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_PROVIDER_FAILURE,
                VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                attempt_number=1,
                retryable=False,
            )
        if not isinstance(prompt, str):
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_PROVIDER_FAILURE,
                VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                attempt_number=1,
                retryable=False,
            )

        attempt_number = 1
        while True:
            try:
                raw_output = self._generation_runner.generate(
                    profile, self._runtime_config, image_path, prompt
                )
            except QwenModelLoadError:
                if attempt_number == 1:
                    return self._runtime_failure(
                        request,
                        profile,
                        catalog_hash,
                        VisionErrorCode.VISION_MODEL_UNAVAILABLE,
                        VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED,
                        attempt_number=1,
                        retryable=False,
                    )
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_PROVIDER_FAILURE,
                    VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                    attempt_number=attempt_number,
                    retryable=False,
                )
            except QwenDeviceUnavailableError:
                if attempt_number == 1:
                    return self._runtime_failure(
                        request,
                        profile,
                        catalog_hash,
                        VisionErrorCode.VISION_MODEL_UNAVAILABLE,
                        VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE,
                        attempt_number=1,
                        retryable=False,
                    )
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_PROVIDER_FAILURE,
                    VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                    attempt_number=attempt_number,
                    retryable=False,
                )
            except (QwenTimeoutError, TimeoutError):
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_TIMEOUT,
                    VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED,
                    attempt_number=attempt_number,
                    retryable=False,
                )
            except QwenTransientRuntimeError:
                if attempt_number == 1:
                    attempt_number = 2
                    continue
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_PROVIDER_FAILURE,
                    VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE,
                    attempt_number=2,
                    retryable=True,
                )
            except QwenPermanentRuntimeError:
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_PROVIDER_FAILURE,
                    VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                    attempt_number=attempt_number,
                    retryable=False,
                )
            except Exception as exc:  # noqa: BLE001 - typed mapping is the public boundary
                if _looks_like_device_error(exc) and attempt_number == 1:
                    return self._runtime_failure(
                        request,
                        profile,
                        catalog_hash,
                        VisionErrorCode.VISION_MODEL_UNAVAILABLE,
                        VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE,
                        attempt_number=1,
                        retryable=False,
                    )
                try:
                    transient = self._classify_transient(exc)
                except Exception:  # noqa: BLE001 - classifier detail is not a public outcome
                    transient = False
                if transient and attempt_number == 1:
                    attempt_number = 2
                    continue
                detail = (
                    VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE
                    if transient
                    else VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE
                )
                return self._runtime_failure(
                    request,
                    profile,
                    catalog_hash,
                    VisionErrorCode.VISION_PROVIDER_FAILURE,
                    detail,
                    attempt_number=attempt_number,
                    retryable=transient,
                )

            if self._on_raw_output is not None:
                with suppress(Exception):
                    self._on_raw_output(raw_output)

            return self._map_raw_output(
                request, profile, catalog_hash, raw_output, attempt_number
            )

    def _map_raw_output(
        self,
        request: VisionUnderstandingRequestV2,
        profile: VisionProfileV2,
        catalog_hash: str,
        raw_output: str,
        attempt_number: int,
    ) -> VisionUnderstandingResultV2:
        if not isinstance(raw_output, str):
            payload, repair_attempted = None, False
        else:
            payload, repair_attempted = _parse_raw_output(raw_output)
        if payload is None or not set(payload).issubset(_ALLOWED_PROVIDER_KEYS):
            return self._schema_failure(
                request,
                profile,
                catalog_hash,
                VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
                attempt_number=attempt_number,
                repair_attempted=repair_attempted,
            )

        merged: dict[str, Any] = {
            **payload,
            "correlation_id": request.correlation_id,
            "executed_at": self._clock(),
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
            "config_hash": vision_profile_config_hash_v2(profile),
            "model_provenance": profile.model_provenance,
        }
        try:
            success = VisionUnderstandingSuccessV2.model_validate(merged)
        except ValidationError as error:
            return self._schema_failure(
                request,
                profile,
                catalog_hash,
                _classify_schema_error(error),
                attempt_number=attempt_number,
                repair_attempted=repair_attempted,
            )

        try:
            category = self._policy.evaluate(collect_observed_texts_v2(success))
        except Exception:
            return self._runtime_failure(
                request,
                profile,
                catalog_hash,
                VisionErrorCode.VISION_PROVIDER_FAILURE,
                VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
                attempt_number=attempt_number,
                retryable=False,
            )
        if category is not None:
            return VisionUnderstandingFailureV2(
                correlation_id=request.correlation_id,
                executed_at=self._clock(),
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
                model_provenance=profile.model_provenance,
            )
        return success

    def _resolve_verified_input_image(self, request: VisionUnderstandingRequestV2) -> Path:
        _verify_image_reference(
            request.source_image_ref.artifact_ref, request.source_image_ref.sha256
        )
        if request.processing_image_ref is not None:
            _verify_image_reference(
                request.processing_image_ref.artifact_ref, request.processing_image_ref.sha256
            )
            return Path(request.processing_image_ref.artifact_ref)
        return Path(request.source_image_ref.artifact_ref)

    def _input_failure(
        self,
        request: VisionUnderstandingRequestV2,
        profile_id: Any,
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
        attempt_number: int,
        retryable: bool,
    ) -> VisionUnderstandingFailureV2:
        return VisionUnderstandingFailureV2(
            correlation_id=request.correlation_id,
            executed_at=self._clock(),
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
            model_provenance=profile.model_provenance,
        )

    def _schema_failure(
        self,
        request: VisionUnderstandingRequestV2,
        profile: VisionProfileV2,
        catalog_hash: str,
        detail: VisionNonPolicyErrorDetailV2,
        *,
        attempt_number: int,
        repair_attempted: bool,
    ) -> VisionUnderstandingFailureV2:
        return VisionUnderstandingFailureV2(
            correlation_id=request.correlation_id,
            executed_at=self._clock(),
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
            model_provenance=profile.model_provenance,
        )


class _InputImageIntegrityError(Exception):
    def __init__(self, detail: VisionNonPolicyErrorDetailV2) -> None:
        self.detail = detail


def _verify_image_reference(artifact_ref: str, expected_sha256: str) -> None:
    digest = sha256()
    try:
        with Path(artifact_ref).open("rb") as image_file:
            while chunk := image_file.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise _InputImageIntegrityError(
            VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE
        ) from exc
    if digest.hexdigest() != expected_sha256:
        raise _InputImageIntegrityError(
            VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH
        )


def _parse_raw_output(raw_output: str) -> tuple[dict[str, Any] | None, bool]:
    """Unwrap one complete Markdown fence; never complete or extract JSON."""

    fence_match = _FENCE_PATTERN.match(raw_output.strip())
    if fence_match is not None:
        try:
            parsed = _loads_strict_json(fence_match.group(1))
        except ValueError:
            return None, False
        return (parsed, True) if isinstance(parsed, dict) else (None, False)

    try:
        parsed = _loads_strict_json(raw_output)
    except ValueError:
        return None, False
    return (parsed, False) if isinstance(parsed, dict) else (None, False)


def _loads_strict_json(value: str) -> object:
    return json.loads(
        value,
        object_pairs_hook=_reject_duplicate_object_keys,
        parse_constant=_reject_non_finite_number,
    )


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_non_finite_number(value: str) -> object:
    raise ValueError(f"non-finite JSON number is not permitted: {value}")


def _classify_schema_error(error: ValidationError) -> VisionNonPolicyErrorDetailV2:
    for item in error.errors():
        message = str(item.get("msg", ""))
        if "DUPLICATE_OBSERVATION_ID" in message:
            return VisionNonPolicyErrorDetailV2.DUPLICATE_OBSERVATION_ID
        if "REFERENCE_INTEGRITY_VIOLATION" in message:
            return VisionNonPolicyErrorDetailV2.REFERENCE_INTEGRITY_VIOLATION
    return VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED


# Descriptive aliases for callers that use the model-family spelling.
Qwen3VLVisionAdapter = QwenVisionAdapter
QwenVisionUnderstandingAdapter = QwenVisionAdapter


__all__ = [
    "KillableSubprocessQwenGenerationRunner",
    "Qwen3VLVisionAdapter",
    "QwenDeviceUnavailableError",
    "QwenGenerationRunner",
    "QwenModelBundle",
    "QwenModelLoadError",
    "QwenPermanentRuntimeError",
    "QwenProcessorLike",
    "QwenTimeoutError",
    "QwenTransientRuntimeError",
    "QwenVisionAdapter",
    "QwenVisionUnderstandingAdapter",
    "QwenModelLike",
    "RawOutputHook",
    "TransformersQwenGenerationRunner",
]
