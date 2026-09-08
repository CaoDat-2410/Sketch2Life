"""Real `faster-whisper` ASR adapter.

Provider SDK objects, raw provider output, and unbounded exception text never cross the
`AsrPort` boundary — every outcome is mapped into `AsrSuccessV1`/`AsrFailureV1`. The model
factory is injected (defaulting to a real `faster_whisper.WhisperModel` loader, imported
lazily so this module — and its contract-level tests — never require the dependency to be
installed) so the adapter's retry/repair/mapping logic is unit-testable without a GPU.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import ValidationError

from sketch2life.application.ports.asr import AsrPort
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrProfileV1,
    AsrQualityMetadataV1,
    AsrRequestV1,
    AsrResultV1,
    AsrSegmentV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
    asr_profile_catalog,
    profile_config_hash,
)
from sketch2life.infrastructure.ai.faster_whisper_runtime_config import (
    FasterWhisperRuntimeConfig,
)

_COMPUTE_TYPE_BY_PROFILE: dict[str, str] = {
    "GPU_INT8_FLOAT16": "int8_float16",
    "GPU_FLOAT16": "float16",
}

_LOCAL_TURBO_MODEL_IDENTIFIER = "deepdml/faster-whisper-large-v3-turbo-ct2"

_DEVICE_ERROR_KEYWORDS = (
    "cuda",
    "cudnn",
    "cublas",
    "device",
    "gpu",
    "out of memory",
    "oom",
)


class _InputAudioIntegrityError(Exception):
    """A bounded input-side failure which must become a typed contract result."""

    def __init__(self, detail: AsrErrorDetail) -> None:
        self.detail = detail


class TranscriptionSegmentLike(Protocol):
    start: float
    end: float
    text: str
    avg_logprob: float | None
    compression_ratio: float | None
    no_speech_prob: float | None


class TranscriptionInfoLike(Protocol):
    language: str
    language_probability: float
    duration: float


class WhisperModelLike(Protocol):
    def transcribe(
        self, audio: str, **kwargs: Any
    ) -> tuple[Any, TranscriptionInfoLike]: ...


ModelFactory = Callable[[AsrProfileV1, FasterWhisperRuntimeConfig], WhisperModelLike]
TransientClassifier = Callable[[BaseException], bool]


def _default_model_factory(
    profile: AsrProfileV1, runtime_config: FasterWhisperRuntimeConfig
) -> WhisperModelLike:
    runtime_config.enable_native_libraries_for_current_process()
    from faster_whisper import WhisperModel  # deferred: only needed to load a real model

    assert profile.model_identifier is not None
    assert profile.compute_profile in _COMPUTE_TYPE_BY_PROFILE
    if runtime_config.model_dir is not None:
        if profile.model_identifier != _LOCAL_TURBO_MODEL_IDENTIFIER:
            raise RuntimeError(
                "the configured local model directory only supports the installed Turbo snapshot"
            )
        model_reference = str(runtime_config.model_dir)
        model_kwargs: dict[str, object] = {}
    else:
        assert runtime_config.model_cache_dir is not None
        model_reference = profile.model_identifier
        model_kwargs = {
            "revision": profile.model_revision,
            "download_root": str(runtime_config.model_cache_dir),
        }
    return cast(
        WhisperModelLike,
        WhisperModel(
            model_reference,
            device=runtime_config.device,
            device_index=runtime_config.device_index,
            compute_type=_COMPUTE_TYPE_BY_PROFILE[profile.compute_profile],
            **model_kwargs,
        ),
    )


def _never_transient(_exc: BaseException) -> bool:
    """Conservative default: no exception is retried until real operational evidence exists.

    faster-whisper/CTranslate2's exception taxonomy for a local synchronous GPU call has not
    been observed in production; defaulting to "no retry" avoids masking a real failure behind
    an incorrect transient classification. See `plan/P2_T2_ASR_RESEARCH_PLAN.md` B6/R4.
    """

    return False


def _looks_like_device_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(keyword in message for keyword in _DEVICE_ERROR_KEYWORDS)


class FasterWhisperAsrAdapter(AsrPort):
    """Constructor-injected real adapter; no shared `Settings`, no HTTP/API/provider wiring."""

    def __init__(
        self,
        runtime_config: FasterWhisperRuntimeConfig,
        *,
        model_factory: ModelFactory = _default_model_factory,
        classify_transient: TransientClassifier = _never_transient,
        adapter_version: str = "faster-whisper-asr-adapter-v1",
    ) -> None:
        self._runtime_config = runtime_config
        self._model_factory = model_factory
        self._classify_transient = classify_transient
        self._adapter_version = adapter_version
        self._models: dict[str, WhisperModelLike] = {}

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1:
        profile = asr_profile_catalog().resolve(request.requested_profile_id)

        if request.media_validation is None:
            return self._failure(
                request,
                profile,
                AsrErrorCode.INPUT_NOT_VALIDATED,
                AsrErrorDetail.MEDIA_VALIDATION_PROVENANCE_MISSING,
                attempt_number=0,
                retryable=False,
            )
        if request.media_validation.decision != "PASS":
            return self._failure(
                request,
                profile,
                AsrErrorCode.INPUT_NOT_VALIDATED,
                AsrErrorDetail.MEDIA_VALIDATION_NOT_PASSED,
                attempt_number=0,
                retryable=False,
            )
        if profile.language_mode == "HONOR_HINT":
            # Out of Round 1 scope by construction: no catalog entry currently sets this,
            # so reaching here would be a programming error, not a runtime/user condition.
            raise NotImplementedError(
                "HONOR_HINT is deferred beyond Round 1; no such candidate is in the catalog"
            )

        try:
            audio_path = self._resolve_verified_input_audio(request)
        except _InputAudioIntegrityError as exc:
            return self._failure(
                request,
                profile,
                AsrErrorCode.INPUT_NOT_VALIDATED,
                exc.detail,
                attempt_number=0,
                retryable=False,
            )

        try:
            model = self._load_model(profile)
        except Exception as exc:  # noqa: BLE001 - classified and bounded below, never re-raised raw
            detail = (
                AsrErrorDetail.DEVICE_UNAVAILABLE
                if _looks_like_device_error(exc)
                else AsrErrorDetail.MODEL_LOAD_FAILED
            )
            return self._failure(
                request,
                profile,
                AsrErrorCode.ASR_MODEL_UNAVAILABLE,
                detail,
                attempt_number=1,
                retryable=False,
            )

        return self._transcribe_with_retry(request, profile, model, audio_path)

    def _transcribe_with_retry(
        self,
        request: AsrRequestV1,
        profile: AsrProfileV1,
        model: WhisperModelLike,
        audio_path: str,
    ) -> AsrResultV1:
        attempt_number = 1
        while True:
            try:
                segments_raw, info = self._run_with_timeout(model, profile, audio_path)
            except FutureTimeoutError:
                if profile.idempotent_timeout_retry and attempt_number < 2:
                    attempt_number += 1
                    continue
                return self._failure(
                    request,
                    profile,
                    AsrErrorCode.ASR_TIMEOUT,
                    AsrErrorDetail.TIMEOUT_BUDGET_EXCEEDED,
                    attempt_number=attempt_number,
                    retryable=profile.idempotent_timeout_retry,
                )
            except Exception as exc:  # noqa: BLE001 - classified and bounded below
                if _looks_like_device_error(exc):
                    return self._failure(
                        request,
                        profile,
                        AsrErrorCode.ASR_MODEL_UNAVAILABLE,
                        AsrErrorDetail.DEVICE_UNAVAILABLE,
                        attempt_number=attempt_number,
                        retryable=False,
                    )
                transient = self._classify_transient(exc)
                if transient and attempt_number < 2:
                    attempt_number += 1
                    continue
                detail = (
                    AsrErrorDetail.TRANSIENT_RUNTIME_FAILURE
                    if transient
                    else AsrErrorDetail.PERMANENT_RUNTIME_FAILURE
                )
                return self._failure(
                    request,
                    profile,
                    AsrErrorCode.ASR_PROVIDER_FAILURE,
                    detail,
                    attempt_number=attempt_number,
                    retryable=transient,
                )

            return self._map_success(request, profile, segments_raw, info, attempt_number)

    def _run_with_timeout(
        self, model: WhisperModelLike, profile: AsrProfileV1, audio_path: str
    ) -> tuple[list[TranscriptionSegmentLike], TranscriptionInfoLike]:
        def call() -> tuple[list[TranscriptionSegmentLike], TranscriptionInfoLike]:
            segments_generator, info = model.transcribe(
                audio_path,
                beam_size=profile.beam_size,
                language=None,
                vad_filter=profile.vad_enabled,
                word_timestamps=profile.word_timestamps_enabled,
            )
            return list(segments_generator), info

        # Do not use a context manager here: its implicit shutdown(wait=True) turns a
        # FutureTimeoutError into an unbounded wait for the provider call to complete.
        # CTranslate2 does not expose cancellation for an in-flight synchronous call, so a
        # timed-out worker may finish in the background; current real catalog profiles never
        # opt into timeout retry, preventing a second concurrent call for the same request.
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(call)
        try:
            return future.result(timeout=profile.timeout_seconds)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _resolve_verified_input_audio(self, request: AsrRequestV1) -> str:
        """Verify immutable source and optional derived working copy before inference."""

        self._verify_audio_reference(request.source_audio_ref)
        if request.processing_audio_ref is not None:
            self._verify_audio_reference(request.processing_audio_ref)
            return request.processing_audio_ref.artifact_ref
        return request.source_audio_ref.artifact_ref

    @staticmethod
    def _verify_audio_reference(audio_ref: AsrAudioReferenceV1) -> None:
        try:
            digest = sha256()
            with Path(audio_ref.artifact_ref).open("rb") as audio_file:
                while chunk := audio_file.read(1024 * 1024):
                    digest.update(chunk)
        except OSError as exc:
            raise _InputAudioIntegrityError(AsrErrorDetail.SOURCE_AUDIO_UNREADABLE) from exc
        if digest.hexdigest() != audio_ref.sha256:
            raise _InputAudioIntegrityError(AsrErrorDetail.SOURCE_AUDIO_HASH_MISMATCH)

    def _load_model(self, profile: AsrProfileV1) -> WhisperModelLike:
        cache_key = f"{profile.profile_id}:{profile.model_revision}:{profile.compute_profile}"
        if cache_key not in self._models:
            self._models[cache_key] = self._model_factory(profile, self._runtime_config)
        return self._models[cache_key]

    def _map_success(
        self,
        request: AsrRequestV1,
        profile: AsrProfileV1,
        segments_raw: list[TranscriptionSegmentLike],
        info: TranscriptionInfoLike,
        attempt_number: int,
    ) -> AsrResultV1:
        try:
            return self._build_success(
                request, profile, segments_raw, info, attempt_number, repair_attempted=False
            )
        except ValidationError:
            try:
                return self._build_success(
                    request,
                    profile,
                    segments_raw,
                    info,
                    attempt_number,
                    repair_attempted=True,
                )
            except ValidationError:
                return self._failure(
                    request,
                    profile,
                    AsrErrorCode.ASR_SCHEMA_INVALID,
                    AsrErrorDetail.OUTPUT_MAPPING_FAILED,
                    attempt_number=attempt_number,
                    retryable=False,
                    repair_attempted=True,
                )

    def _build_success(
        self,
        request: AsrRequestV1,
        profile: AsrProfileV1,
        segments_raw: list[TranscriptionSegmentLike],
        info: TranscriptionInfoLike,
        attempt_number: int,
        *,
        repair_attempted: bool,
    ) -> AsrSuccessV1:
        mapped: list[AsrSegmentV1] = []
        for seg in segments_raw:
            text = (seg.text or "").strip()
            if not text:
                continue
            start = max(0.0, float(seg.start))
            end = max(start, float(seg.end))
            no_speech = seg.no_speech_prob
            clamped_no_speech = None if no_speech is None else min(max(no_speech, 0.0), 1.0)
            mapped.append(
                AsrSegmentV1(
                    index=len(mapped),
                    start_seconds=start,
                    end_seconds=end,
                    text=text,
                    average_log_probability=seg.avg_logprob,
                    compression_ratio=seg.compression_ratio,
                    no_speech_probability=clamped_no_speech,
                )
            )
        duration = max(float(info.duration), 1e-6)
        if repair_attempted:
            # Bounded local repair over already-received output only — never re-invokes the
            # model. Clamps timestamps that are internally inconsistent with the reported
            # total duration (e.g. a segment ending after `info.duration`). `clamped_start`
            # is always <= `clamped_end` by construction, so this can only shrink a segment,
            # never invert one.
            repaired: list[AsrSegmentV1] = []
            for mapped_seg in mapped:
                clamped_end = min(mapped_seg.end_seconds, duration)
                clamped_start = min(mapped_seg.start_seconds, clamped_end)
                repaired.append(
                    mapped_seg.model_copy(
                        update={
                            "index": len(repaired),
                            "start_seconds": clamped_start,
                            "end_seconds": clamped_end,
                        }
                    )
                )
            mapped = repaired

        segments = tuple(mapped)
        speech_diagnostic = (
            AsrSpeechDiagnostic.DETECTED if segments else AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED
        )
        transcript_raw = " ".join(seg.text for seg in segments)

        validation = request.media_validation
        assert validation is not None
        no_speech_values = [
            s.no_speech_probability for s in segments if s.no_speech_probability is not None
        ]
        log_prob_values = [
            s.average_log_probability for s in segments if s.average_log_probability is not None
        ]

        return AsrSuccessV1(
            correlation_id=request.correlation_id,
            executed_at=datetime.now(UTC),
            source_audio_ref=request.source_audio_ref,
            profile_id=profile.profile_id,
            attempt_number=attempt_number,
            repair_attempted=repair_attempted,
            transcript_raw=transcript_raw,
            speech_diagnostic=speech_diagnostic,
            detected_language=info.language,
            language_probability=info.language_probability,
            language_hint_echo=request.language_hint,
            language_hint_applied=False,
            segments=segments,
            input_duration_seconds=duration,
            vad_enabled=profile.vad_enabled,
            duration_after_vad_seconds=None,
            model_identifier=profile.model_identifier or "",
            model_revision=profile.model_revision or "",
            adapter_version=profile.adapter_version or self._adapter_version,
            runtime_version=profile.runtime_version or "unknown",
            config_hash=profile_config_hash(profile),
            quality_metadata=AsrQualityMetadataV1(
                media_validation_artifact_ref=validation.validation_artifact_ref,
                media_validation_artifact_sha256=validation.validation_artifact_sha256,
                mean_segment_log_probability=(
                    sum(log_prob_values) / len(log_prob_values) if log_prob_values else None
                ),
                mean_no_speech_probability=(
                    sum(no_speech_values) / len(no_speech_values) if no_speech_values else None
                ),
            ),
        )

    def _failure(
        self,
        request: AsrRequestV1,
        profile: AsrProfileV1,
        error_code: AsrErrorCode,
        error_detail: AsrErrorDetail,
        *,
        attempt_number: int,
        retryable: bool,
        repair_attempted: bool = False,
    ) -> AsrFailureV1:
        return AsrFailureV1(
            correlation_id=request.correlation_id,
            executed_at=datetime.now(UTC),
            source_audio_ref=request.source_audio_ref,
            profile_id=profile.profile_id,
            attempt_number=attempt_number,
            repair_attempted=repair_attempted,
            error_code=error_code,
            retryable=retryable,
            error_detail=error_detail,
        )
