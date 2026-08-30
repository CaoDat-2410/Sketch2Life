"""Internal (non-CLI) executor for the approved P2-T2 Phase B Round-1 ASR benchmark.

This module is imported and called directly (e.g. from a script/test), never exposed as a
CLI — the ~20-fixture end-to-end CLI/report remains P2-T5's scope, not this one. It:

- resolves every fixture path relative to the caller-supplied fixtures root (never a
  hard-coded absolute path);
- independently re-verifies audio and transcript SHA-256 before touching the adapter, on top
  of the adapter's own source-hash verification;
- requires a real per-fixture P2-T1 `PASS` (via `DeterministicMediaValidator`, not a fabricated
  provenance record) before ever calling the ASR adapter for that fixture;
- runs exactly the two fixed Round-1 Turbo profiles through the real `FasterWhisperAsrAdapter`;
- measures latency (cold start separate from per-audio inference), peak VRAM when `nvidia-smi`
  is available, schema-valid/success/failure counts, and WER/CER via the frozen normalizer;
- never fabricates a metric — an unavailable measurement stays `NOT_MEASURED`.

Raw audio bytes and raw transcript text are read only to hash-verify them and, for the
transcript, to score WER/CER in memory; neither is ever written into a result, report, or log.
"""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from statistics import fmean
from tempfile import TemporaryDirectory
from threading import Event, Thread
from typing import Literal
from wave import open as wave_open

from sketch2life.application.ports.asr import AsrPort
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrProfileId,
    AsrRequestV1,
    AsrSuccessV1,
    MediaValidationProvenanceV1,
    asr_profile_catalog,
    profile_config_hash,
)
from sketch2life.contracts.schemas.asr_benchmark import (
    AsrFixtureSplit,
    AsrRound1FixtureEntryV1,
    AsrRound1FixtureManifestV1,
    asr_round1_manifest_hash,
    duration_band_for_seconds,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.ai.faster_whisper_asr import FasterWhisperAsrAdapter
from sketch2life.infrastructure.ai.faster_whisper_runtime_config import (
    FasterWhisperRuntimeConfig,
)
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

from .asr_readiness import (
    AsrRound1BenchmarkReportV1,
    AsrRound1BenchmarkSettingsV1,
    AsrRound1MetricSetV1,
    AsrRound1RunOutcome,
    AsrRound1RunResultV1,
    AsrSpeechPresenceOutcome,
    _measured,
    _not_measured,
    _planned_run_id,
    report_id_for,
    speech_presence_outcome_for,
    validate_round1_manifest,
    validate_round1_settings,
)
from .asr_scoring import character_error_rate, word_error_rate


class FixtureIntegrityError(RuntimeError):
    """A fixture payload does not match its manifest-declared hash. Never silently skipped."""


@dataclass(frozen=True, slots=True)
class Round1RunnerConfig:
    fixtures_root: Path
    runtime_config: FasterWhisperRuntimeConfig
    sample_vram: bool = True
    # Narrow injection seam only: lets tests exercise `run_round1_benchmark`'s own control
    # flow (warmup capture, per-run wiring) against a fake `AsrPort`, without a GPU or the
    # real `faster-whisper` dependency. The default is the real adapter; this does not widen
    # or change the shared `AsrPort`/`AsrResultV1` contract.
    adapter_factory: Callable[[FasterWhisperRuntimeConfig], AsrPort] = FasterWhisperAsrAdapter


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _wav_duration_seconds(path: Path) -> float:
    with wave_open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def _verify_fixture_payloads(fixtures_root: Path, fixture: AsrRound1FixtureEntryV1) -> Path:
    """Resolve and hash-verify this fixture's audio (and transcript, if declared).

    Also re-derives the actual decoded duration band from the audio itself and requires it to
    match the manifest's declared `duration_band` — metadata the manifest merely asserts is
    verified against what the payload actually is, before any adapter call.
    """

    audio_path = fixtures_root / fixture.source_audio_ref
    if not audio_path.is_file():
        raise FixtureIntegrityError(f"fixture audio payload is missing: {fixture.fixture_id}")
    actual_audio_hash = _sha256_of(audio_path)
    if actual_audio_hash != fixture.source_audio_sha256:
        raise FixtureIntegrityError(f"fixture audio hash mismatch: {fixture.fixture_id}")

    actual_duration = _wav_duration_seconds(audio_path)
    actual_band = duration_band_for_seconds(actual_duration)
    if actual_band != fixture.duration_band:
        raise FixtureIntegrityError(
            f"fixture duration_band mismatch: {fixture.fixture_id} declares "
            f"{fixture.duration_band.value}, decoded audio is {actual_duration:.3f}s "
            f"({actual_band.value})"
        )

    if fixture.reference_transcript_ref is not None:
        transcript_path = fixtures_root / fixture.reference_transcript_ref
        if not transcript_path.is_file():
            raise FixtureIntegrityError(
                f"fixture transcript payload is missing: {fixture.fixture_id}"
            )
        actual_transcript_hash = _sha256_of(transcript_path)
        if actual_transcript_hash != fixture.reference_transcript_sha256:
            raise FixtureIntegrityError(
                f"fixture transcript hash mismatch: {fixture.fixture_id}"
            )
    return audio_path


def _read_reference_transcript(fixtures_root: Path, fixture: AsrRound1FixtureEntryV1) -> str | None:
    if fixture.reference_transcript_ref is None:
        return None
    return (fixtures_root / fixture.reference_transcript_ref).read_text(encoding="utf-8")


# A single reusable synthetic PNG used only to satisfy P2-T1's joint image+audio validation
# boundary for an audio-only ASR benchmark. Never written into fixtures/ or evidence/.
def _write_p2t1_companion_image(path: Path) -> None:
    from struct import pack
    from zlib import compress, crc32

    width, height = 160, 160
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            # A light border keeps `IMAGE_FRAMING_RISK` clear; interior stripes give the
            # edge strength and contrast P2-T1 requires.
            in_interior = 30 < x < 130 and 30 < y < 130
            shade = 30 if in_interior and (x // 8) % 2 == 0 else 235
            rows.extend((shade, shade, shade))
    compressed = compress(bytes(rows), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return pack(">I", len(data)) + tag + data + pack(">I", crc32(tag + data) & 0xFFFFFFFF)

    ihdr = pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def _p2t1_validation_provenance(
    fixture_id: str, image_path: Path, audio_path: Path
) -> MediaValidationProvenanceV1:
    """Run the real P2-T1 validator (never a fabricated PASS) and narrow it to provenance."""

    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref=f"asr-round1-benchmark-companion-image:{fixture_id}",
            audio_artifact_ref=f"asr-round1-fixture:{fixture_id}",
        )
    )
    artifact_payload = result.model_dump_json().encode("utf-8")
    decision: Literal["PASS", "RECAPTURE"] = (
        "PASS" if result.decision is MediaDecision.PASS else "RECAPTURE"
    )
    return MediaValidationProvenanceV1(
        validation_artifact_ref=f"asr-round1-p2t1-validation:{fixture_id}",
        validation_artifact_sha256=sha256(artifact_payload).hexdigest(),
        decision=decision,
        validator_policy_version=result.validator_policy_version,
    )


class NoWarmupFixtureAvailableError(RuntimeError):
    """No manifest fixture received a real P2-T1 `PASS`; refuse to warm up any profile.

    A warmup call must use a real, earned `MediaValidationProvenanceV1` — never a fabricated
    one — so if the manifest contains no fixture P2-T1 actually passes, there is no audio this
    runner is allowed to warm up with, and the whole benchmark run must not proceed silently.
    """


@dataclass(frozen=True, slots=True)
class _WarmupFixture:
    fixture_id: str
    audio_path: Path
    media_validation: MediaValidationProvenanceV1


def _select_warmup_fixture(
    fixtures_root: Path,
    fixtures: tuple[AsrRound1FixtureEntryV1, ...],
    companion_image_path: Path,
) -> _WarmupFixture:
    """Deterministically pick the first (by `fixture_id`) manifest fixture with a real P2-T1
    `PASS`, verified the same way every normal run verifies its own fixture. Never fabricates
    provenance — a fixture that would legitimately fail P2-T1 (e.g. `silence`) is skipped, not
    forced to `PASS`.
    """

    for fixture in sorted(fixtures, key=lambda item: item.fixture_id):
        audio_path = _verify_fixture_payloads(fixtures_root, fixture)
        media_validation = _p2t1_validation_provenance(
            fixture.fixture_id, companion_image_path, audio_path
        )
        if media_validation.decision == "PASS":
            return _WarmupFixture(
                fixture_id=fixture.fixture_id,
                audio_path=audio_path,
                media_validation=media_validation,
            )
    raise NoWarmupFixtureAvailableError(
        "no manifest fixture received a real P2-T1 PASS; refusing to warm up with a "
        "fabricated PASS"
    )


class WarmupTranscriptionFailedError(RuntimeError):
    """The warmup transcription itself returned a typed `AsrFailureV1`.

    A failed warmup is not evidence of a successful model load, so recording a numeric
    `cold_start_ms` for it would misrepresent an error as a timing measurement. This stops the
    whole benchmark run before any cold-start value is recorded and before any normal fixture
    run executes — it is deliberately not caught or downgraded to a per-run typed failure,
    because a warmup failure means this profile's model/runtime state is not known-good for any
    of the timed runs that would follow it.

    The message contains only the closed `AsrErrorCode`/`AsrErrorDetail` identifiers already
    present on the adapter's typed `AsrFailureV1` contract — never raw provider text, a stack
    trace, or any other unbounded detail.
    """

    def __init__(
        self,
        *,
        profile_id: AsrProfileId,
        fixture_id: str,
        error_code: AsrErrorCode,
        error_detail: AsrErrorDetail,
    ) -> None:
        self.profile_id = profile_id
        self.fixture_id = fixture_id
        self.error_code = error_code
        self.error_detail = error_detail
        super().__init__(
            f"warmup transcription failed for profile={profile_id.value} "
            f"fixture={fixture_id}: error_code={error_code.value} "
            f"error_detail={error_detail.value}"
        )


class _VramSampler:
    """Background `nvidia-smi` poller. Silently inert (never fabricates) if unavailable."""

    def __init__(self, device_index: int = 0, interval_seconds: float = 0.1) -> None:
        self._device_index = device_index
        self._interval_seconds = interval_seconds
        self._stop = Event()
        self._thread: Thread | None = None
        self._peak_mb: float | None = None
        self._available = self._probe()

    def _probe(self) -> bool:
        sample = self._sample_once()
        return sample is not None

    def _sample_once(self) -> float | None:
        try:
            completed = subprocess.run(
                [
                    "nvidia-smi",
                    f"--id={self._device_index}",
                    "--query-gpu=memory.used",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        try:
            return float(completed.stdout.strip().splitlines()[0])
        except (ValueError, IndexError):
            return None

    def _loop(self) -> None:
        while not self._stop.is_set():
            sample = self._sample_once()
            if sample is not None:
                self._peak_mb = sample if self._peak_mb is None else max(self._peak_mb, sample)
            self._stop.wait(self._interval_seconds)

    def start(self) -> None:
        if not self._available:
            return
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_and_get_peak_mb(self) -> float | None:
        if not self._available:
            return None
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        return self._peak_mb


def _percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _language_matches(detected_language: str, expected_language: str) -> bool:
    return detected_language.split("-")[0].lower() == expected_language.split("-")[0].lower()


def run_round1_benchmark(
    manifest: AsrRound1FixtureManifestV1,
    config: Round1RunnerConfig,
    *,
    settings: AsrRound1BenchmarkSettingsV1 | None = None,
) -> AsrRound1BenchmarkReportV1:
    """Execute the fixed Round-1 comparison for every fixture in `manifest`.

    Every fixture must belong to the same `split` — the report contract rejects a mix, per
    R3's "do not mix development and held-out results."
    """

    parsed_manifest = validate_round1_manifest(manifest)
    parsed_settings = validate_round1_settings(settings)
    manifest_hash = asr_round1_manifest_hash(parsed_manifest)

    splits = {fixture.split for fixture in parsed_manifest.fixtures}
    if len(splits) != 1:
        raise ValueError("Round 1 execution requires every fixture to share one split")
    (split,) = tuple(splits)

    catalog = asr_profile_catalog()
    adapter = config.adapter_factory(config.runtime_config)

    # A real OS temp directory, never a repository path — this is scratch data (a companion
    # image to satisfy P2-T1's joint image+audio boundary), not a fixture.
    runner_tmp_dir = TemporaryDirectory(prefix="asr-round1-runner-")
    companion_image_path = Path(runner_tmp_dir.name) / "companion.png"
    _write_p2t1_companion_image(companion_image_path)

    # The warmup call must use real, earned P2-T1 provenance — never a fabricated PASS — so
    # a real manifest fixture is selected deterministically up front. If none of this
    # manifest's fixtures actually pass P2-T1, this raises before any model is loaded.
    warmup_fixture = _select_warmup_fixture(
        config.fixtures_root, parsed_manifest.fixtures, companion_image_path
    )

    runs: list[AsrRound1RunResultV1] = []
    latencies_by_profile: dict[str, list[float]] = {
        pid.value: [] for pid in parsed_settings.profile_ids
    }
    cold_start_by_profile: dict[str, float | None] = {}
    peak_vram_by_profile: dict[str, float | None] = {}

    for profile_id in parsed_settings.profile_ids:
        profile = catalog.resolve(profile_id)
        sampler = _VramSampler() if config.sample_vram else None
        if sampler is not None:
            sampler.start()

        warmup_request = AsrRequestV1(
            correlation_id=f"asr-round1-warmup-{profile_id.value}-{warmup_fixture.fixture_id}",
            source_audio_ref=AsrAudioReferenceV1(
                artifact_ref=str(warmup_fixture.audio_path),
                sha256=_sha256_of(warmup_fixture.audio_path),
            ),
            media_validation=warmup_fixture.media_validation,
            requested_profile_id=profile_id,
        )
        warmup_started = time.perf_counter()
        # The warmup call exists only to pay the model-load cost separately from the timed
        # per-fixture inferences below; on success its transcription payload is discarded and
        # it is never added to `runs`, so it never counts toward denominators, WER/CER,
        # language accuracy, speech-presence outcomes, or p50/p95 latency. But a failed warmup
        # is not evidence of a successful model load — recording a numeric cold_start_ms for it
        # would misrepresent an error as a timing measurement, so this stops the whole run
        # before any cold-start value is recorded or any fixture is executed.
        warmup_result = adapter.transcribe(warmup_request)
        if isinstance(warmup_result, AsrFailureV1):
            raise WarmupTranscriptionFailedError(
                profile_id=profile_id,
                fixture_id=warmup_fixture.fixture_id,
                error_code=warmup_result.error_code,
                error_detail=warmup_result.error_detail,
            )
        cold_start_ms = (time.perf_counter() - warmup_started) * 1000.0
        cold_start_by_profile[profile_id.value] = cold_start_ms

        for fixture in sorted(parsed_manifest.fixtures, key=lambda item: item.fixture_id):
            run = _execute_one(
                fixtures_root=config.fixtures_root,
                fixture=fixture,
                profile_id=profile_id,
                profile_config_hash_value=profile_config_hash(profile),
                manifest_hash=manifest_hash,
                split=split,
                adapter=adapter,
                companion_image_path=companion_image_path,
            )
            runs.append(run)
            if run.inference_latency_ms is not None:
                latencies_by_profile[profile_id.value].append(run.inference_latency_ms)

        if sampler is not None:
            peak_vram_by_profile[profile_id.value] = sampler.stop_and_get_peak_mb()
        else:
            peak_vram_by_profile[profile_id.value] = None

    runner_tmp_dir.cleanup()

    metrics_by_profile = {
        profile_id: _aggregate_profile_metrics(
            runs=[run for run in runs if run.profile_id == profile_id],
            latencies_ms=latencies_by_profile[profile_id.value],
            cold_start_ms=cold_start_by_profile.get(profile_id.value),
            peak_vram_mb=peak_vram_by_profile.get(profile_id.value),
        )
        for profile_id in parsed_settings.profile_ids
    }

    report_id = report_id_for(manifest_hash, parsed_settings, split, tuple(runs))
    return AsrRound1BenchmarkReportV1(
        report_id=report_id,
        manifest_version=parsed_manifest.manifest_version,
        manifest_sha256=manifest_hash,
        normalizer_version=parsed_manifest.normalizer_version,
        settings=parsed_settings,
        split=split,
        runs=tuple(runs),
        metrics_by_profile=metrics_by_profile,
    )


def _execute_one(
    *,
    fixtures_root: Path,
    fixture: AsrRound1FixtureEntryV1,
    profile_id: AsrProfileId,
    profile_config_hash_value: str,
    manifest_hash: str,
    split: AsrFixtureSplit,
    adapter: AsrPort,
    companion_image_path: Path,
) -> AsrRound1RunResultV1:
    profile = asr_profile_catalog().resolve(profile_id)
    audio_path = _verify_fixture_payloads(fixtures_root, fixture)
    reference_transcript = _read_reference_transcript(fixtures_root, fixture)
    media_validation = _p2t1_validation_provenance(
        fixture.fixture_id, companion_image_path, audio_path
    )

    request = AsrRequestV1(
        correlation_id=f"asr-round1-{fixture.fixture_id}-{profile_id.value}",
        source_audio_ref=AsrAudioReferenceV1(
            artifact_ref=str(audio_path), sha256=fixture.source_audio_sha256
        ),
        media_validation=media_validation,
        requested_profile_id=profile_id,
    )

    run_id = _planned_run_id(manifest_hash, fixture.fixture_id, profile)
    started = time.perf_counter()
    result = adapter.transcribe(request)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    if isinstance(result, AsrSuccessV1):
        language_correct = (
            _language_matches(result.detected_language, fixture.expected_language)
            if fixture.language_accuracy_eligible and fixture.expected_language is not None
            else None
        )
        wer = (
            word_error_rate(reference_transcript, result.transcript_raw)
            if fixture.wer_eligible and reference_transcript is not None
            else None
        )
        cer = (
            character_error_rate(reference_transcript, result.transcript_raw)
            if fixture.cer_eligible and reference_transcript is not None
            else None
        )
        speech_presence_outcome = speech_presence_outcome_for(
            fixture.expected_speech_present, result.speech_diagnostic
        )
        return AsrRound1RunResultV1(
            run_id=run_id,
            fixture_id=fixture.fixture_id,
            scenario=fixture.scenario,
            split=split,
            profile_id=profile_id,
            profile_config_hash=profile_config_hash_value,
            outcome=AsrRound1RunOutcome.SUCCEEDED,
            attempt_number=result.attempt_number,
            repair_attempted=result.repair_attempted,
            is_cold_start=False,
            inference_latency_ms=elapsed_ms if result.attempt_number > 0 else None,
            speech_diagnostic=result.speech_diagnostic,
            detected_language=result.detected_language,
            language_correct=language_correct,
            speech_presence_outcome=speech_presence_outcome,
            wer=wer,
            cer=cer,
        )

    assert isinstance(result, AsrFailureV1)
    return AsrRound1RunResultV1(
        run_id=run_id,
        fixture_id=fixture.fixture_id,
        scenario=fixture.scenario,
        split=split,
        profile_id=profile_id,
        profile_config_hash=profile_config_hash_value,
        outcome=AsrRound1RunOutcome.FAILED,
        attempt_number=result.attempt_number,
        repair_attempted=result.repair_attempted,
        is_cold_start=False,
        inference_latency_ms=elapsed_ms if result.attempt_number > 0 else None,
        error_code=result.error_code,
        error_detail=result.error_detail,
    )


def _aggregate_profile_metrics(
    *,
    runs: list[AsrRound1RunResultV1],
    latencies_ms: list[float],
    cold_start_ms: float | None,
    peak_vram_mb: float | None,
) -> AsrRound1MetricSetV1:
    total = len(runs)
    success = [run for run in runs if run.outcome is AsrRound1RunOutcome.SUCCEEDED]
    failure = [run for run in runs if run.outcome is AsrRound1RunOutcome.FAILED]
    wer_values = [run.wer for run in success if run.wer is not None]
    cer_values = [run.cer for run in success if run.cer is not None]
    language_flags = [run.language_correct for run in success if run.language_correct is not None]
    speech_presence_flags = [
        run.speech_presence_outcome
        for run in success
        if run.speech_presence_outcome is not None
        and run.speech_presence_outcome is not AsrSpeechPresenceOutcome.NOT_MEASURED
    ]

    return AsrRound1MetricSetV1(
        total_runs=(
            _measured(float(total), "this profile's own run count (never another profile's)")
            if total
            else _not_measured("no runs were executed for this profile")
        ),
        schema_validity_rate=(
            _measured(1.0, f"{len(success) + len(failure)}/{total} runs schema-valid")
            if total
            else _not_measured("no runs were executed for this profile")
        ),
        wer=(
            _measured(fmean(wer_values), f"mean over {len(wer_values)} WER-eligible fixtures")
            if wer_values
            else _not_measured("no WER-eligible fixture succeeded for this profile")
        ),
        cer=(
            _measured(fmean(cer_values), f"mean over {len(cer_values)} CER-eligible fixtures")
            if cer_values
            else _not_measured("no CER-eligible fixture succeeded for this profile")
        ),
        cold_start_ms=(
            _measured(cold_start_ms, "elapsed time for the warmup transcription call")
            if cold_start_ms is not None
            else _not_measured("no warmup call was executed for this profile")
        ),
        language_accuracy=(
            _measured(
                sum(language_flags) / len(language_flags),
                f"over {len(language_flags)} language-accuracy-eligible fixtures",
            )
            if language_flags
            else _not_measured("no language-accuracy-eligible fixture succeeded for this profile")
        ),
        speech_presence_match_rate=(
            _measured(
                sum(1 for flag in speech_presence_flags if flag is AsrSpeechPresenceOutcome.MATCH)
                / len(speech_presence_flags),
                f"over {len(speech_presence_flags)} succeeded, diagnostically-conclusive fixtures",
            )
            if speech_presence_flags
            else _not_measured(
                "no succeeded fixture had a conclusive (non-INDETERMINATE) speech diagnostic"
            )
        ),
        latency_p50_ms=(
            _measured(_percentile(latencies_ms, 0.5), f"p50 over {len(latencies_ms)} inferences")
            if latencies_ms
            else _not_measured("no attempted inference produced a latency sample")
        ),
        latency_p95_ms=(
            _measured(_percentile(latencies_ms, 0.95), f"p95 over {len(latencies_ms)} inferences")
            if latencies_ms
            else _not_measured("no attempted inference produced a latency sample")
        ),
        peak_vram_mb=(
            _measured(peak_vram_mb, "peak nvidia-smi memory.used sample during this profile's run")
            if peak_vram_mb is not None
            else _not_measured("nvidia-smi was unavailable or returned no sample")
        ),
        success_count=_measured(float(len(success)), "count of SUCCEEDED runs"),
        failure_count=_measured(float(len(failure)), "count of FAILED runs"),
        vad_alternatives=_not_measured(
            "Round 1 fixes VAD disabled; alternatives are out of scope"
        ),
        beam_size_alternatives=_not_measured(
            "Round 1 fixes beam size 5; alternatives are out of scope"
        ),
        word_timestamp_alternatives=_not_measured(
            "Round 1 fixes word timestamps disabled; alternatives are out of scope"
        ),
    )
