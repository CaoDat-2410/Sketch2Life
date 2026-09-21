"""P2-T5 fixture-only evaluation contracts and canonical serialization helpers."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

P2T5_MANIFEST_IDENTITY: Final = "P2T5.P2T5FixtureManifestV1@1.0"
P2T5_RUN_IDENTITY: Final = "P2T5.P2T5RunRecordV1@1.0"
P2T5_SUMMARY_IDENTITY: Final = "P2T5.P2T5ValidationSummaryV1@1.0"
P2T5_CASE_IDENTITY: Final = "P2T5.P2T5FixtureCaseResultV1@1.0"
P2T5_MEASUREMENT_IDENTITY: Final = "P2T5.P2T5MeasurementV1@1.0"
P2T5_FAILURE_IDENTITY: Final = "P2T5.P2T5FailureV1@1.0"
P2T5_COMMAND_IDENTITY: Final = "P2T5.P2T5CommandEnvelopeV1@1.0"
P2T5_CORRELATION_IDENTITY: Final = "P2T5.CorrelationIdV1@1.0"
P2T5_REPORT_IDENTITY: Final = "P2T5.P2T5EvaluationReportV1@1.0"
P2T5_CANONICAL_JSON_IDENTITY: Final = "P2T5-REPORT-CANONICAL-JSON-V1"
P2T5_POLICY_HASH: Final = "4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c"
P2T5_PLAN_IDENTITY: Final = "P2-T5-EVALUATION-HARNESS-PLAN@0.15"
P2T5_IMPLEMENTATION_COMMIT: Final = "9d6340672c5d1bbdd7a95004f5fad811718ec4a0"

_RUN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_RELATIVE = re.compile(r"^[^/\\\x00]+(?:/[^/\\\x00]+)*$")
_UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
_SIX_PLACES = Decimal("0.000001")


class Split(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    HELD_OUT = "HELD_OUT"


class StageExecutionState(StrEnum):
    NOT_EXECUTED = "NOT_EXECUTED"
    EXECUTED = "EXECUTED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class CaseRunStatus(StrEnum):
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_TYPED_FAILURES = "COMPLETED_WITH_TYPED_FAILURES"
    EXPECTED_TERMINAL = "EXPECTED_TERMINAL"
    SKIPPED = "SKIPPED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class MeasurementStatus(StrEnum):
    MEASURED = "MEASURED"
    NOT_MEASURED = "NOT_MEASURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class P2T5ErrorCode(StrEnum):
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER"
    CONTRACT_OR_ORACLE_REJECTED = "CONTRACT_OR_ORACLE_REJECTED"
    REPORT_WRITE_FAILED = "REPORT_WRITE_FAILED"
    UNEXPECTED_HARNESS_ERROR = "UNEXPECTED_HARNESS_ERROR"
    T4_POLICY_INTEGRITY_FAILURE = "T4_POLICY_INTEGRITY_FAILURE"


class P2T5FailureReason(StrEnum):
    MISSING_POLICY_HASH = "MISSING_POLICY_HASH"
    MISMATCHED_POLICY_HASH = "MISMATCHED_POLICY_HASH"
    ORACLE_HASH_MISMATCH = "ORACLE_HASH_MISMATCH"
    MANIFEST_HASH_MISMATCH = "MANIFEST_HASH_MISMATCH"
    PRIVACY_SENTINEL = "PRIVACY_SENTINEL"
    NO_ELIGIBLE_CASES = "NO_ELIGIBLE_CASES"
    FIXTURE_ONLY_LATENCY_DISABLED = "FIXTURE_ONLY_LATENCY_DISABLED"
    UNEXPECTED_HARNESS_ERROR = "UNEXPECTED_HARNESS_ERROR"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class P2T5FailureV1(FrozenModel):
    contract_name: Literal["P2T5FailureV1"] = "P2T5FailureV1"
    contract_version: Literal["1.0"] = "1.0"
    code: P2T5ErrorCode
    phase: str = Field(min_length=1, max_length=32)
    case_id: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$")
    reason_code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Z0-9_]+$")


class P2T5MeasurementV1(FrozenModel):
    contract_name: Literal["P2T5MeasurementV1"] = "P2T5MeasurementV1"
    contract_version: Literal["1.0"] = "1.0"
    metric_id: str = Field(min_length=1, pattern=r"^[a-z0-9_:-]+$")
    status: MeasurementStatus
    value: str | None = None
    numerator: int | None = Field(default=None, ge=0)
    denominator: int | None = Field(default=None, ge=0)
    unit: str = Field(min_length=1)
    reason_code: str | None = Field(default=None, pattern=r"^[A-Z0-9_]+$")
    eligibility_rule_id: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def _value_is_canonical_decimal(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            decimal = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("measurement value must be a decimal string") from exc
        if not decimal.is_finite() or decimal != decimal.quantize(_SIX_PLACES):
            raise ValueError("measurement value must have exactly six finite decimal places")
        return format(decimal, ".6f")

    @model_validator(mode="after")
    def _state_is_coherent(self) -> P2T5MeasurementV1:
        if self.status is MeasurementStatus.MEASURED:
            if self.value is None or self.denominator is None:
                raise ValueError("MEASURED requires value and denominator")
            if self.reason_code is not None:
                raise ValueError("MEASURED must not carry reason_code")
        elif self.value is not None:
            raise ValueError("unavailable measurements require null value")
        if self.status is not MeasurementStatus.MEASURED and self.reason_code is None:
            raise ValueError("unavailable measurements require a closed reason")
        return self


class P2T5StageStateV1(FrozenModel):
    state: StageExecutionState
    status: str | None = Field(default=None, pattern=r"^[A-Z0-9_]+$")
    identity: str | None = None
    error_code: str | None = Field(default=None, pattern=r"^[A-Z0-9_]+$")
    rejection_phase: str | None = Field(default=None, pattern=r"^[A-Z0-9_]+$")
    rejection_code: str | None = Field(default=None, pattern=r"^[A-Z0-9_]+$")
    field_code: str | None = Field(default=None, pattern=r"^[A-Z0-9_]+$")
    result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class P2T5FixtureManifestEntryV1(FrozenModel):
    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    split: Split
    image_ref: str = Field(min_length=1)
    audio_ref: str = Field(min_length=1)
    image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_t1_decision: Literal["PASS", "RECAPTURE"]
    expected_t1_reasons: tuple[str, ...] = ()
    asr_scenario: str = Field(min_length=1)
    vision_scenario: str = Field(min_length=1)
    t4_input_mutation: str = Field(min_length=1)
    coverage_tags: tuple[str, ...] = ()
    wer_eligible: bool = False
    cer_eligible: bool = False
    synthetic_data: Literal[True] = True

    @field_validator("image_ref", "audio_ref")
    @classmethod
    def _relative_ref(cls, value: str) -> str:
        if not _RELATIVE.fullmatch(value) or ".." in value.split("/"):
            raise ValueError("media references must be repository-relative POSIX paths")
        return value


class P2T5FixtureManifestV1(FrozenModel):
    contract_name: Literal["P2T5FixtureManifestV1"] = "P2T5FixtureManifestV1"
    contract_version: Literal["1.0"] = "1.0"
    manifest_id: str = Field(min_length=1, pattern=r"^[a-z0-9-]+$")
    manifest_version: str = Field(min_length=1)
    data_policy: Literal["SYNTHETIC_ONLY"] = "SYNTHETIC_ONLY"
    matching_rule_id: str = Field(min_length=1)
    matching_rule_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    oracle_ref: str = Field(min_length=1)
    oracle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    entries: tuple[P2T5FixtureManifestEntryV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _requires_exact_split_and_unique_ids(self) -> P2T5FixtureManifestV1:
        ids = [entry.fixture_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("fixture IDs must be unique")
        if len(self.entries) != 20:
            raise ValueError("P2-T5 v1 requires exactly 20 fixtures")
        if sum(entry.split is Split.DEVELOPMENT for entry in self.entries) != 12:
            raise ValueError("P2-T5 v1 requires exactly 12 DEVELOPMENT fixtures")
        if sum(entry.split is Split.HELD_OUT for entry in self.entries) != 8:
            raise ValueError("P2-T5 v1 requires exactly 8 HELD_OUT fixtures")
        return self


class P2T5RunRecordV1(FrozenModel):
    contract_name: Literal["P2T5RunRecordV1"] = "P2T5RunRecordV1"
    contract_version: Literal["1.0"] = "1.0"
    run_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    manifest_id: str
    manifest_version: str
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    oracle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fixture_split: Split
    executed_at: str
    implementation_plan_identity: str = P2T5_PLAN_IDENTITY
    implementation_commit: str = P2T5_IMPLEMENTATION_COMMIT
    environment_identity: str = "CPython-3.13.5"
    dependency_identity: str = "NO_PYTHON_LOCKFILE"

    @field_validator("executed_at")
    @classmethod
    def _utc_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.strptime(value, _UTC_FORMAT).replace(tzinfo=UTC)
        except ValueError as exc:
            raise ValueError("executed_at must be UTC with six fractional digits") from exc
        return parsed.strftime(_UTC_FORMAT)


class P2T5FixtureCaseResultV1(FrozenModel):
    contract_name: Literal["P2T5FixtureCaseResultV1"] = "P2T5FixtureCaseResultV1"
    contract_version: Literal["1.0"] = "1.0"
    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    split: Split
    case_status: CaseRunStatus
    correlation_id: str = Field(min_length=1)
    t1: P2T5StageStateV1
    asr: P2T5StageStateV1
    vision: P2T5StageStateV1
    fusion: P2T5StageStateV1
    source_media_sha256: tuple[str, str]
    t1_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    asr_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    vision_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    t4_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    t4_rejection_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    measurements: tuple[P2T5MeasurementV1, ...] = ()
    typed_failure_codes: tuple[str, ...] = ()
    case_outcome_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class P2T5ValidationSummaryV1(FrozenModel):
    contract_name: Literal["P2T5ValidationSummaryV1"] = "P2T5ValidationSummaryV1"
    contract_version: Literal["1.0"] = "1.0"
    manifest_id: str
    entry_count: int = Field(ge=0)
    development_count: int = Field(ge=0)
    held_out_count: int = Field(ge=0)
    case_summaries: tuple[dict[str, Any], ...] = ()


class P2T5EvaluationReportV1(FrozenModel):
    contract_name: Literal["P2T5EvaluationReportV1"] = "P2T5EvaluationReportV1"
    contract_version: Literal["1.0"] = "1.0"
    deterministic_core: dict[str, Any]
    deterministic_core_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    volatile_run_metadata: dict[str, Any]

    @model_validator(mode="after")
    def _hash_matches_core(self) -> P2T5EvaluationReportV1:
        if canonical_sha256(self.deterministic_core) != self.deterministic_core_sha256:
            raise ValueError("deterministic_core_sha256 does not match deterministic_core")
        if set(self.volatile_run_metadata) != {
            "started_at",
            "finished_at",
            "stage_durations_ms",
            "harness_overhead_ms",
            "timing_sample_counts",
        }:
            raise ValueError("volatile_run_metadata has undeclared fields")
        return self


class P2T5CommandEnvelopeV1(FrozenModel):
    contract_name: Literal["P2T5CommandEnvelopeV1"] = "P2T5CommandEnvelopeV1"
    contract_version: Literal["1.0"] = "1.0"
    command: str = Field(min_length=1)
    success: bool
    payload: dict[str, Any] | None = None
    failure: P2T5FailureV1 | None = None

    @model_validator(mode="after")
    def _success_failure_exclusive(self) -> P2T5CommandEnvelopeV1:
        if self.success == (self.failure is not None):
            raise ValueError("command envelope must contain exactly one success/failure branch")
        if self.success and self.payload is None:
            raise ValueError("successful command requires payload")
        return self


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize stable values under P2T5-REPORT-CANONICAL-JSON-V1."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC).strftime(_UTC_FORMAT)


def correlation_id(
    *, manifest_id: str, manifest_version: str, fixture_id: str, split: Split
) -> str:
    metadata = {
        "feature_task": "FEAT003-P2T5",
        "manifest_id": manifest_id,
        "manifest_version": manifest_version,
        "fixture_id": fixture_id,
        "split": split.value,
    }
    return "p2t5-corr-" + canonical_sha256(metadata)


def decimal_value(value: Decimal | str | float) -> str:
    try:
        parsed = Decimal(str(value)).quantize(_SIX_PLACES, rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError("value is not a finite decimal") from exc
    if not parsed.is_finite():
        raise ValueError("value is not a finite decimal")
    return format(parsed, ".6f")


def reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number is not allowed")
    if isinstance(value, dict):
        for child in value.values():
            reject_non_finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_non_finite(child)


def stable_case_projection(case: P2T5FixtureCaseResultV1) -> dict[str, Any]:
    """Return the closed redacted case domain; raw text and paths never enter it."""

    payload = case.model_dump(mode="json", exclude={"case_outcome_sha256"})
    reject_non_finite(payload)
    return payload


def report_core(
    *,
    run: P2T5RunRecordV1,
    manifest: P2T5FixtureManifestV1,
    cases: tuple[P2T5FixtureCaseResultV1, ...],
    measurements: tuple[P2T5MeasurementV1, ...],
    typed_failure_summary: dict[str, int],
) -> dict[str, Any]:
    return {
        "contract_name": "P2T5EvaluationReportV1",
        "contract_version": "1.0",
        "mode": "fixture",
        "run": run.model_dump(mode="json"),
        "manifest": {
            "manifest_id": manifest.manifest_id,
            "manifest_version": manifest.manifest_version,
            "manifest_sha256": run.manifest_sha256,
            "oracle_sha256": manifest.oracle_sha256,
            "fixture_split": run.fixture_split.value,
            "fixture_ids": sorted(case.fixture_id for case in cases),
            "data_policy": manifest.data_policy,
            "matching_rules": [
                {
                    "scope": "COLLECTION",
                    "rule_id": manifest.matching_rule_id,
                    "sha256": manifest.matching_rule_sha256,
                }
            ],
            "normalizers": [],
        },
        "fixture_split": run.fixture_split.value,
        "upstream_contracts": {
            "t1": "MediaValidationResultV1@1.0",
            "asr": "P2.AsrResultV1@1.0",
            "vision": "P2.VisionUnderstandingResultV1@1.0",
            "fusion": "P2T4.P2T4FusedResultV1@1.0",
            "rejection": "P2T4.P2T4FusionInputRejectionV2@2.0",
        },
        "profile_and_policy_identities": {
            "asr_profile": "FAKE_DETERMINISTIC_V1",
            "vision_profile": "FAKE_DETERMINISTIC_V1",
            "fusion_policy_config_hash": P2T5_POLICY_HASH,
        },
        "case_results": [
            stable_case_projection(case) for case in sorted(cases, key=lambda item: item.fixture_id)
        ],
        "measurements": [
            item.model_dump(mode="json")
            for item in sorted(measurements, key=lambda item: item.metric_id)
        ],
        "typed_failure_summary": dict(sorted(typed_failure_summary.items())),
        "interpretation_id": "P2T5-FIXTURE-ONLY-INTERPRETATION-V1",
        "limitations_id": "P2T5-FIXTURE-ONLY-LIMITATIONS-V1",
    }


def report_model(
    *,
    run: P2T5RunRecordV1,
    manifest: P2T5FixtureManifestV1,
    cases: tuple[P2T5FixtureCaseResultV1, ...],
    measurements: tuple[P2T5MeasurementV1, ...],
    typed_failure_summary: dict[str, int],
    volatile_run_metadata: dict[str, Any] | None = None,
) -> P2T5EvaluationReportV1:
    core = report_core(
        run=run,
        manifest=manifest,
        cases=cases,
        measurements=measurements,
        typed_failure_summary=typed_failure_summary,
    )
    return P2T5EvaluationReportV1(
        deterministic_core=core,
        deterministic_core_sha256=canonical_sha256(core),
        volatile_run_metadata=volatile_run_metadata
        or {
            "started_at": None,
            "finished_at": None,
            "stage_durations_ms": None,
            "harness_overhead_ms": None,
            "timing_sample_counts": None,
        },
    )
