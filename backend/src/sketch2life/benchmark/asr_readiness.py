"""Non-CLI, no-GPU readiness planning for the P2-T2 ASR Round-1 benchmark.

The planner validates only versioned metadata and fixed profile settings.  It never imports
or calls ``faster-whisper``, loads a model, touches a device, reads an audio payload, or
produces a measurement.  Every measurement in a plan is therefore explicitly
``NOT_MEASURED``.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.asr import (
    AsrErrorCode,
    AsrErrorDetail,
    AsrProfileId,
    AsrProfileV1,
    AsrSpeechDiagnostic,
    asr_profile_catalog,
    profile_config_hash,
)
from sketch2life.contracts.schemas.asr_benchmark import (
    AsrFixtureScenario,
    AsrFixtureSplit,
    AsrRound1FixtureManifestV1,
    AsrRound1ManifestStatus,
    asr_round1_manifest_hash,
)

from .asr_scoring import VIETNAMESE_ASR_NORMALIZER_VERSION


class BenchmarkMeasurementStatus(StrEnum):
    NOT_MEASURED = "NOT_MEASURED"
    MEASURED = "MEASURED"


ROUND1_PROFILE_IDS: tuple[AsrProfileId, AsrProfileId] = (
    AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
    AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1,
)
_ROUND1_COMPUTE_PROFILES: dict[AsrProfileId, str] = {
    AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1: "GPU_INT8_FLOAT16",
    AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1: "GPU_FLOAT16",
}


class AsrBenchmarkMeasurementV1(BaseModel):
    """A metric value or an explicit unavailable marker.

    The current readiness package can only create the unavailable state. Keeping a value
    field makes the report contract ready for the controlled measurement runner while
    preventing a missing result from being represented as zero.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: BenchmarkMeasurementStatus = BenchmarkMeasurementStatus.NOT_MEASURED
    value: float | int | None = None
    reason: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def _value_matches_measurement_status(self) -> AsrBenchmarkMeasurementV1:
        if self.status is BenchmarkMeasurementStatus.NOT_MEASURED and self.value is not None:
            raise ValueError("NOT_MEASURED metrics must not contain a numeric value")
        if self.status is BenchmarkMeasurementStatus.MEASURED and self.value is None:
            raise ValueError("MEASURED metrics must contain a numeric value")
        return self


def _not_measured(reason: str = "live benchmark has not run") -> AsrBenchmarkMeasurementV1:
    return AsrBenchmarkMeasurementV1(reason=reason)


def _measured(value: float | int, reason: str) -> AsrBenchmarkMeasurementV1:
    return AsrBenchmarkMeasurementV1(
        status=BenchmarkMeasurementStatus.MEASURED, value=value, reason=reason
    )


class AsrRound1BenchmarkSettingsV1(BaseModel):
    """The immutable control set for this preparation package's Round-1 candidates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    round_id: Literal["ASR_ROUND_1"] = "ASR_ROUND_1"
    round_version: Literal["1.0"] = "1.0"
    profile_ids: tuple[AsrProfileId, AsrProfileId] = ROUND1_PROFILE_IDS
    language_mode: Literal["AUTO_DETECT"] = "AUTO_DETECT"
    beam_size: Literal[5] = 5
    vad_enabled: Literal[False] = False
    word_timestamps_enabled: Literal[False] = False
    language_hint_policy: Literal["NOT_USED"] = "NOT_USED"

    @model_validator(mode="after")
    def _requires_fixed_round_1_values(self) -> AsrRound1BenchmarkSettingsV1:
        if tuple(self.profile_ids) != ROUND1_PROFILE_IDS:
            raise ValueError("Round 1 must compare Turbo INT8 and Turbo FP16 only")
        return self


class AsrRound1MetricSetV1(BaseModel):
    """Metric coverage for a planned profile; all fields start as NOT_MEASURED."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_runs: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    schema_validity_rate: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    wer: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    cer: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    cold_start_ms: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    language_accuracy: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    speech_presence_match_rate: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    latency_p50_ms: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    latency_p95_ms: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    peak_vram_mb: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    success_count: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    failure_count: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    vad_alternatives: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    beam_size_alternatives: AsrBenchmarkMeasurementV1 = Field(default_factory=_not_measured)
    word_timestamp_alternatives: AsrBenchmarkMeasurementV1 = Field(
        default_factory=_not_measured
    )


class AsrRound1PlannedRunV1(BaseModel):
    """One deterministic fixture/profile work item, not an inference result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(pattern=r"^asr-round1-[a-f0-9]{64}$")
    fixture_id: str = Field(min_length=1)
    profile_id: AsrProfileId
    profile_config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["PLANNED"] = "PLANNED"
    measurement_status: BenchmarkMeasurementStatus = BenchmarkMeasurementStatus.NOT_MEASURED
    metrics: AsrRound1MetricSetV1 = Field(default_factory=AsrRound1MetricSetV1)


class AsrRound1ReadinessPlanV1(BaseModel):
    """Deterministic metadata-only plan for the fixed Round-1 comparison."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_id: str = Field(pattern=r"^asr-round1-plan-[a-f0-9]{64}$")
    contract_name: Literal["AsrRound1ReadinessPlanV1"] = "AsrRound1ReadinessPlanV1"
    contract_version: Literal["1.0"] = "1.0"
    round_id: Literal["ASR_ROUND_1"] = "ASR_ROUND_1"
    manifest_version: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalizer_version: str = Field(min_length=1)
    settings: AsrRound1BenchmarkSettingsV1
    candidate_profile_ids: tuple[AsrProfileId, AsrProfileId]
    runs: tuple[AsrRound1PlannedRunV1, ...]
    aggregate_metrics: AsrRound1MetricSetV1 = Field(default_factory=AsrRound1MetricSetV1)
    measurement_status: BenchmarkMeasurementStatus = BenchmarkMeasurementStatus.NOT_MEASURED

    @model_validator(mode="after")
    def _requires_deterministic_unmeasured_runs(self) -> AsrRound1ReadinessPlanV1:
        if tuple(self.candidate_profile_ids) != ROUND1_PROFILE_IDS:
            raise ValueError("readiness plans must use the fixed Round-1 candidate profiles")
        run_ids = tuple(run.run_id for run in self.runs)
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("planned run IDs must be unique")
        if any(run.measurement_status != "NOT_MEASURED" for run in self.runs):
            raise ValueError("readiness plans cannot contain measured runs")
        return self


def validate_round1_manifest(
    manifest: AsrRound1FixtureManifestV1 | Mapping[str, Any],
) -> AsrRound1FixtureManifestV1:
    """Parse and validate a Round-1 manifest without inspecting its referenced payloads."""

    manifest_input: Mapping[str, Any] = (
        manifest.model_dump(mode="json")
        if isinstance(manifest, AsrRound1FixtureManifestV1)
        else manifest
    )
    parsed = AsrRound1FixtureManifestV1.model_validate(manifest_input)
    if parsed.status is not AsrRound1ManifestStatus.READY:
        raise ValueError("only a READY manifest can produce a runnable Round-1 plan")
    if parsed.normalizer_version != VIETNAMESE_ASR_NORMALIZER_VERSION:
        raise ValueError(
            "Round 1 must use the frozen Vietnamese normalizer "
            f"{VIETNAMESE_ASR_NORMALIZER_VERSION}"
        )
    return parsed


def validate_round1_settings(
    settings: AsrRound1BenchmarkSettingsV1 | Mapping[str, Any] | None = None,
) -> AsrRound1BenchmarkSettingsV1:
    """Parse settings and verify candidate profiles against the static ASR catalog."""

    parsed = (
        settings
        if isinstance(settings, AsrRound1BenchmarkSettingsV1)
        else AsrRound1BenchmarkSettingsV1.model_validate(settings or {})
    )
    if (
        parsed.round_id != "ASR_ROUND_1"
        or parsed.round_version != "1.0"
        or parsed.language_mode != "AUTO_DETECT"
        or parsed.beam_size != 5
        or parsed.vad_enabled is not False
        or parsed.word_timestamps_enabled is not False
        or parsed.language_hint_policy != "NOT_USED"
        or tuple(parsed.profile_ids) != ROUND1_PROFILE_IDS
    ):
        raise ValueError("Round 1 settings do not match the fixed readiness contract")
    catalog = asr_profile_catalog()
    for profile_id in parsed.profile_ids:
        profile = catalog.resolve(profile_id)
        _validate_round1_profile(profile)
    return parsed


def _validate_round1_profile(profile: AsrProfileV1) -> None:
    if profile.profile_id not in ROUND1_PROFILE_IDS:
        raise ValueError("profile is not a Round-1 Turbo candidate")
    if profile.adapter_kind != "FASTER_WHISPER":
        raise ValueError("Round 1 requires a faster-whisper profile")
    if profile.language_mode != "AUTO_DETECT":
        raise ValueError("Round 1 does not allow HONOR_HINT")
    if profile.beam_size != 5:
        raise ValueError("Round 1 requires beam size 5")
    if profile.vad_enabled or profile.word_timestamps_enabled:
        raise ValueError("Round 1 disables VAD and word timestamps")
    if profile.compute_profile != _ROUND1_COMPUTE_PROFILES[profile.profile_id]:
        raise ValueError("Round 1 profile has an unexpected compute profile")
    if profile.idempotent_timeout_retry:
        raise ValueError("Round 1 profiles must not retry a timed-out worker")


def _canonical_json(value: object) -> str:
    return dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _planned_run_id(
    manifest_hash: str, fixture_id: str, profile: AsrProfileV1
) -> str:
    seed = {
        "manifest_sha256": manifest_hash,
        "fixture_id": fixture_id,
        "profile_id": profile.profile_id,
        "profile_config_hash": profile_config_hash(profile),
    }
    digest = sha256(_canonical_json(seed).encode("utf-8")).hexdigest()
    return f"asr-round1-{digest}"


def _planned_plan_id(
    manifest_hash: str,
    settings: AsrRound1BenchmarkSettingsV1,
    runs: tuple[AsrRound1PlannedRunV1, ...],
) -> str:
    seed = {
        "round_id": settings.round_id,
        "round_version": settings.round_version,
        "manifest_sha256": manifest_hash,
        "settings": settings.model_dump(mode="json"),
        "runs": [run.model_dump(mode="json") for run in runs],
    }
    digest = sha256(_canonical_json(seed).encode("utf-8")).hexdigest()
    return f"asr-round1-plan-{digest}"


def build_round1_readiness_plan(
    manifest: AsrRound1FixtureManifestV1 | Mapping[str, Any],
    settings: AsrRound1BenchmarkSettingsV1 | Mapping[str, Any] | None = None,
) -> AsrRound1ReadinessPlanV1:
    """Build deterministic planned runs for every fixture and the two Turbo profiles."""

    parsed_manifest = validate_round1_manifest(manifest)
    parsed_settings = validate_round1_settings(settings)
    manifest_hash = asr_round1_manifest_hash(parsed_manifest)
    catalog = asr_profile_catalog()

    runs_list: list[AsrRound1PlannedRunV1] = []
    for fixture in sorted(parsed_manifest.fixtures, key=lambda item: item.fixture_id):
        for profile_id in parsed_settings.profile_ids:
            profile = catalog.resolve(profile_id)
            runs_list.append(
                AsrRound1PlannedRunV1(
                    run_id=_planned_run_id(manifest_hash, fixture.fixture_id, profile),
                    fixture_id=fixture.fixture_id,
                    profile_id=profile.profile_id,
                    profile_config_hash=profile_config_hash(profile),
                )
            )
    runs = tuple(runs_list)
    plan_id = _planned_plan_id(manifest_hash, parsed_settings, runs)
    return AsrRound1ReadinessPlanV1(
        plan_id=plan_id,
        manifest_version=parsed_manifest.manifest_version,
        manifest_sha256=manifest_hash,
        normalizer_version=parsed_manifest.normalizer_version,
        settings=parsed_settings,
        candidate_profile_ids=parsed_settings.profile_ids,
        runs=runs,
    )


# Naming alias for callers that treat the result as a benchmark plan rather than a runner.
build_round1_plan = build_round1_readiness_plan


class AsrRound1RunOutcome(StrEnum):
    """A completed run's terminal shape; mirrors `AsrResultV1`'s two-branch discriminator."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class AsrSpeechPresenceOutcome(StrEnum):
    """Structured comparison of a fixture's declared `expected_speech_present` vs. the ASR
    model's own `speech_diagnostic` for a succeeded run — never free-form prose.

    `expected_speech_present=True`: `DETECTED` -> MATCH, `NO_SPEECH_SUSPECTED` -> MISMATCH,
    `INDETERMINATE` -> NOT_MEASURED. `expected_speech_present=False`: `NO_SPEECH_SUSPECTED` ->
    MATCH, `DETECTED` -> MISMATCH, `INDETERMINATE` -> NOT_MEASURED. Absent (`None` on the run)
    only when the run itself is `FAILED` — P2-T1 rejection means ASR never evaluated the audio,
    which is a distinct state from a model producing an inconclusive diagnostic.
    """

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_MEASURED = "NOT_MEASURED"


def speech_presence_outcome_for(
    expected_speech_present: bool, diagnostic: AsrSpeechDiagnostic
) -> AsrSpeechPresenceOutcome:
    if diagnostic is AsrSpeechDiagnostic.INDETERMINATE:
        return AsrSpeechPresenceOutcome.NOT_MEASURED
    detected = diagnostic is AsrSpeechDiagnostic.DETECTED
    return (
        AsrSpeechPresenceOutcome.MATCH
        if detected == expected_speech_present
        else AsrSpeechPresenceOutcome.MISMATCH
    )


class AsrRound1RunResultV1(BaseModel):
    """One completed fixture/profile Round-1 run. Never carries raw audio or transcript text.

    This is a measured counterpart to `AsrRound1PlannedRunV1`: same fixture/profile identity,
    but recording what actually happened rather than a `NOT_MEASURED` placeholder.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(pattern=r"^asr-round1-[a-f0-9]{64}$")
    fixture_id: str = Field(min_length=1)
    scenario: AsrFixtureScenario
    split: AsrFixtureSplit
    profile_id: AsrProfileId
    profile_config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    outcome: AsrRound1RunOutcome
    attempt_number: int = Field(ge=0, le=2)
    repair_attempted: bool
    is_cold_start: bool
    inference_latency_ms: float | None = Field(default=None, ge=0)
    error_code: AsrErrorCode | None = None
    error_detail: AsrErrorDetail | None = None
    speech_diagnostic: AsrSpeechDiagnostic | None = None
    detected_language: str | None = None
    language_correct: bool | None = None
    speech_presence_outcome: AsrSpeechPresenceOutcome | None = None
    wer: float | None = Field(default=None, ge=0)
    cer: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _requires_coherent_outcome_fields(self) -> AsrRound1RunResultV1:
        if self.outcome is AsrRound1RunOutcome.SUCCEEDED:
            if self.error_code is not None or self.error_detail is not None:
                raise ValueError("a succeeded run must not carry an error code/detail")
            if self.speech_diagnostic is None:
                raise ValueError("a succeeded run requires a speech diagnostic")
            if self.speech_presence_outcome is None:
                raise ValueError("a succeeded run requires a speech-presence outcome")
        else:
            if self.error_code is None or self.error_detail is None:
                raise ValueError("a failed run requires an error code and error detail")
            if any(
                value is not None
                for value in (
                    self.speech_diagnostic,
                    self.detected_language,
                    self.language_correct,
                    self.speech_presence_outcome,
                    self.wer,
                    self.cer,
                )
            ):
                raise ValueError("a failed run must not carry success-only measurements")
        if self.attempt_number == 0 and self.inference_latency_ms is not None:
            raise ValueError("a rejected-before-inference run cannot report inference latency")
        return self


class AsrRound1BenchmarkReportV1(BaseModel):
    """One profile-comparison report for a single split. Splits are never blended."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(pattern=r"^asr-round1-report-[a-f0-9]{64}$")
    contract_name: Literal["AsrRound1BenchmarkReportV1"] = "AsrRound1BenchmarkReportV1"
    contract_version: Literal["1.0"] = "1.0"
    round_id: Literal["ASR_ROUND_1"] = "ASR_ROUND_1"
    manifest_version: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalizer_version: str = Field(min_length=1)
    settings: AsrRound1BenchmarkSettingsV1
    split: AsrFixtureSplit
    runs: tuple[AsrRound1RunResultV1, ...]
    metrics_by_profile: dict[AsrProfileId, AsrRound1MetricSetV1]

    @model_validator(mode="after")
    def _requires_single_split_and_matching_profiles(self) -> AsrRound1BenchmarkReportV1:
        if any(run.split != self.split for run in self.runs):
            raise ValueError("a Round-1 report must not mix development and held-out runs")
        run_ids = tuple(run.run_id for run in self.runs)
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("report run IDs must be unique")
        observed_profiles = {run.profile_id for run in self.runs}
        if observed_profiles - set(self.settings.profile_ids):
            raise ValueError("a report run used a profile outside the fixed Round-1 settings")
        if set(self.metrics_by_profile) != set(self.settings.profile_ids):
            raise ValueError("metrics_by_profile must cover exactly the fixed Round-1 profiles")
        for profile_id, metrics in self.metrics_by_profile.items():
            profile_run_count = sum(1 for run in self.runs if run.profile_id == profile_id)
            total_runs_value = metrics.total_runs.value
            if total_runs_value is not None and total_runs_value != profile_run_count:
                raise ValueError(
                    f"{profile_id} total_runs does not match its own run count "
                    "(a per-profile denominator must never borrow another profile's runs)"
                )
            success_value = metrics.success_count.value
            failure_value = metrics.failure_count.value
            if (
                success_value is not None
                and failure_value is not None
                and success_value + failure_value != profile_run_count
            ):
                raise ValueError(
                    f"{profile_id} success_count + failure_count must equal its own run count"
                )
        return self


def report_id_for(
    manifest_hash: str,
    settings: AsrRound1BenchmarkSettingsV1,
    split: AsrFixtureSplit,
    runs: tuple[AsrRound1RunResultV1, ...],
) -> str:
    """Deterministic report identity, mirroring `_planned_plan_id`'s seeding approach."""

    seed = {
        "round_id": settings.round_id,
        "round_version": settings.round_version,
        "manifest_sha256": manifest_hash,
        "split": split.value,
        "settings": settings.model_dump(mode="json"),
        "runs": [run.model_dump(mode="json") for run in runs],
    }
    digest = sha256(_canonical_json(seed).encode("utf-8")).hexdigest()
    return f"asr-round1-report-{digest}"
