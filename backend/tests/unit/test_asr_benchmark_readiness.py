from __future__ import annotations

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.benchmark.asr_readiness import (
    ROUND1_PROFILE_IDS,
    AsrBenchmarkMeasurementV1,
    AsrRound1BenchmarkSettingsV1,
    BenchmarkMeasurementStatus,
    build_round1_readiness_plan,
    validate_round1_settings,
)
from sketch2life.benchmark.asr_scoring import VIETNAMESE_ASR_NORMALIZER_VERSION
from sketch2life.contracts.schemas.asr import AsrProfileId
from sketch2life.contracts.schemas.asr_benchmark import (
    AsrFixtureDataProvenance,
    AsrFixtureDurationBand,
    AsrFixtureScenario,
    AsrFixtureSplit,
    AsrRound1FixtureEntryV1,
    AsrRound1FixtureManifestV1,
    AsrRound1ManifestStatus,
)


def test_empty_template_cannot_produce_a_runnable_plan() -> None:
    template = _manifest(status=AsrRound1ManifestStatus.TEMPLATE)

    with pytest.raises(ValueError, match="only a READY manifest"):
        build_round1_readiness_plan(template)


def test_unvalidated_ready_copy_is_revalidated_before_planning() -> None:
    template = _manifest(status=AsrRound1ManifestStatus.TEMPLATE)
    spoofed_ready = template.model_copy(update={"status": AsrRound1ManifestStatus.READY})

    with pytest.raises(ValidationError, match="missing required scenarios"):
        build_round1_readiness_plan(spoofed_ready)


def test_minimal_ready_manifest_produces_two_deterministic_runs_per_fixture() -> None:
    manifest = _ready_manifest()

    first = build_round1_readiness_plan(manifest)
    second = build_round1_readiness_plan(manifest.model_dump(mode="json"))

    assert first == second
    assert first.candidate_profile_ids == ROUND1_PROFILE_IDS
    assert first.settings.language_mode == "AUTO_DETECT"
    assert first.settings.beam_size == 5
    assert first.settings.vad_enabled is False
    assert first.settings.word_timestamps_enabled is False
    assert len(first.runs) == len(manifest.fixtures) * 2
    assert Counter(run.fixture_id for run in first.runs) == Counter(
        {fixture.fixture_id: 2 for fixture in manifest.fixtures}
    )
    assert {run.profile_id for run in first.runs} == set(ROUND1_PROFILE_IDS)
    assert all(
        metric["status"] is BenchmarkMeasurementStatus.NOT_MEASURED
        and metric["value"] is None
        for run in first.runs
        for metric in run.metrics.model_dump(mode="python").values()
    )


@pytest.mark.parametrize(
    "missing_scenario",
    tuple(scenario.value for scenario in AsrFixtureScenario),
)
def test_ready_manifest_rejects_each_missing_required_slice(missing_scenario: str) -> None:
    entries = tuple(
        entry
        for entry in _ready_entries()
        if entry.scenario.value != missing_scenario
    )

    with pytest.raises(ValidationError, match="missing required scenarios"):
        _manifest(*entries)


def test_versioned_empty_template_is_valid_and_schema_is_strict() -> None:
    project_root = Path(__file__).resolve().parents[3]
    template_path = (
        project_root
        / "features/FEAT-003-multimodal-understanding/fixtures/asr-round1/manifest.example.json"
    )
    manifest = AsrRound1FixtureManifestV1.model_validate(
        json.loads(template_path.read_text(encoding="utf-8"))
    )

    assert manifest.status is AsrRound1ManifestStatus.TEMPLATE
    assert manifest.fixtures == ()
    assert AsrRound1FixtureManifestV1.model_config["extra"] == "forbid"
    invalid = manifest.model_dump(mode="json")
    invalid["unexpected"] = True
    with pytest.raises(ValidationError):
        AsrRound1FixtureManifestV1.model_validate(invalid)


def test_duplicate_fixture_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="fixture IDs must be unique"):
        _manifest(
            _entry("duplicate", AsrFixtureScenario.VI_CLEAR, expected_language="vi"),
            _entry("duplicate", AsrFixtureScenario.NON_VI_CLEAR, expected_language="en"),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source_audio_sha256", "not-a-sha256"),
        ("reference_transcript_sha256", "F" * 64),
    ),
)
def test_invalid_sha256_is_rejected(field: str, value: str) -> None:
    values = _entry(
        "bad-hash",
        AsrFixtureScenario.VI_CLEAR,
        expected_language="vi",
        eligible=True,
    ).model_dump()
    values[field] = value

    with pytest.raises(ValidationError):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_speech_without_expected_language_is_rejected() -> None:
    values = _entry(
        "missing-language", AsrFixtureScenario.VI_CLEAR, expected_language="vi"
    ).model_dump()
    values["expected_language"] = None

    with pytest.raises(ValidationError, match="expected language metadata"):
        AsrRound1FixtureEntryV1.model_validate(values)


@pytest.mark.parametrize("language", ("vi", "vi-vn"))
def test_non_vi_clear_rejects_vietnamese_primary_language_subtag(language: str) -> None:
    values = _entry(
        "vietnamese-non-vi-clear", AsrFixtureScenario.NON_VI_CLEAR, expected_language="en"
    ).model_dump()
    values["expected_language"] = language

    with pytest.raises(ValidationError, match="primary language subtag"):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_non_vi_clear_accepts_locale_qualified_non_vietnamese_language() -> None:
    fixture = _entry(
        "english-us-clear", AsrFixtureScenario.NON_VI_CLEAR, expected_language="en-us"
    )

    assert fixture.expected_language == "en-us"


@pytest.mark.parametrize("field", ("reference_transcript_ref", "reference_transcript_sha256"))
def test_speech_without_a_complete_transcript_reference_is_rejected(field: str) -> None:
    values = _entry(
        "missing-reference", AsrFixtureScenario.NON_VI_CLEAR, expected_language="en"
    ).model_dump()
    values[field] = None

    with pytest.raises(ValidationError, match="reference transcript ref/hash"):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_code_switch_requires_vi_and_en_metadata() -> None:
    values = _entry(
        "bad-code-switch",
        AsrFixtureScenario.VI_EN_CODE_SWITCH,
        expected_language="vi",
        expected_languages=("vi", "en"),
        eligible=True,
    ).model_dump()
    values["expected_languages"] = ("vi", "fr")

    with pytest.raises(ValidationError, match="code-switch"):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_code_switch_cannot_be_language_accuracy_eligible() -> None:
    values = _entry(
        "code-switch-language-metric",
        AsrFixtureScenario.VI_EN_CODE_SWITCH,
        expected_language="vi",
        expected_languages=("vi", "en"),
        eligible=True,
    ).model_dump()
    values["language_accuracy_eligible"] = True

    with pytest.raises(ValidationError, match="language-accuracy"):
        AsrRound1FixtureEntryV1.model_validate(values)


@pytest.mark.parametrize("scenario", (AsrFixtureScenario.SILENCE, AsrFixtureScenario.NOISE))
def test_silence_and_noise_reject_language_or_transcript_metadata(
    scenario: AsrFixtureScenario,
) -> None:
    values = _entry(
        f"bad-{scenario.value}",
        scenario,
        noise_condition_id="room-noise-v1" if scenario is AsrFixtureScenario.NOISE else None,
    ).model_dump()
    values["expected_language"] = "vi"
    values["reference_transcript_ref"] = "transcripts/not-allowed.txt"
    values["reference_transcript_sha256"] = "a" * 64

    with pytest.raises(ValidationError, match="silence/noise"):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_silence_cannot_claim_wer_or_cer_eligibility() -> None:
    values = _entry("silent", AsrFixtureScenario.SILENCE).model_dump()
    values["wer_eligible"] = True
    values["cer_eligible"] = True

    with pytest.raises(ValidationError, match="silence/noise"):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_ready_manifest_requires_noise_coverage_for_benchmarked_languages() -> None:
    entries = []
    for entry in _ready_entries():
        if entry.fixture_id == "en-noisy":
            values = entry.model_dump()
            values["wer_eligible"] = False
            values["cer_eligible"] = False
            values["language_accuracy_eligible"] = False
            entry = AsrRound1FixtureEntryV1.model_validate(values)
        entries.append(entry)

    with pytest.raises(ValidationError, match="noise coverage"):
        _manifest(*entries)


def test_ready_manifest_rejects_an_unbenchmarked_noise_condition() -> None:
    entries = (*_ready_entries(), _entry(
        "unused-noise", AsrFixtureScenario.NOISE, noise_condition_id="unused-v1"
    ))

    with pytest.raises(ValidationError, match="every noise fixture"):
        _manifest(*entries)


def test_invalid_profile_or_round_settings_are_rejected() -> None:
    manifest = _ready_manifest()

    with pytest.raises((ValidationError, ValueError), match="Turbo|Round 1"):
        build_round1_readiness_plan(
            manifest,
            {
                "profile_ids": [
                    AsrProfileId.WHISPER_LARGE_V3_INT8_AUTO_V1,
                    AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1,
                ]
            },
        )
    with pytest.raises(ValidationError):
        validate_round1_settings({"beam_size": 4})
    invalid_settings = AsrRound1BenchmarkSettingsV1().model_copy(update={"beam_size": 4})
    with pytest.raises(ValueError, match="fixed readiness contract"):
        validate_round1_settings(invalid_settings)
    with pytest.raises(ValidationError):
        AsrRound1BenchmarkSettingsV1.model_validate({"language_mode": "HONOR_HINT"})


def test_not_measured_rejects_a_zero_value_and_covers_all_planned_metrics() -> None:
    with pytest.raises(ValidationError, match="must not contain a numeric value"):
        AsrBenchmarkMeasurementV1(value=0, reason="not run")

    plan = build_round1_readiness_plan(_ready_manifest())
    metric_values = plan.aggregate_metrics.model_dump(mode="json").values()
    assert all(metric["status"] == "NOT_MEASURED" for metric in metric_values)
    assert all(metric["value"] is None for metric in metric_values)
    assert all(
        run.metrics.wer.status is BenchmarkMeasurementStatus.NOT_MEASURED
        for run in plan.runs
    )


def test_speech_fixture_rejects_expected_speech_present_false() -> None:
    values = _entry(
        "silent-speech-claim", AsrFixtureScenario.VI_CLEAR, expected_language="vi"
    ).model_dump()
    values["expected_speech_present"] = False

    with pytest.raises(ValidationError, match="expected_speech_present=true"):
        AsrRound1FixtureEntryV1.model_validate(values)


@pytest.mark.parametrize("scenario", (AsrFixtureScenario.SILENCE, AsrFixtureScenario.NOISE))
def test_silence_and_noise_reject_expected_speech_present_true(
    scenario: AsrFixtureScenario,
) -> None:
    values = _entry(
        f"speech-claim-{scenario.value}",
        scenario,
        noise_condition_id="room-noise-v1" if scenario is AsrFixtureScenario.NOISE else None,
    ).model_dump()
    values["expected_speech_present"] = True

    with pytest.raises(ValidationError, match="expected_speech_present=false"):
        AsrRound1FixtureEntryV1.model_validate(values)


def test_duration_band_and_split_round_trip() -> None:
    fixture = _entry(
        "held-out-clear",
        AsrFixtureScenario.VI_CLEAR,
        expected_language="vi",
        duration_band=AsrFixtureDurationBand.UNDER_3S,
        split=AsrFixtureSplit.DEVELOPMENT,
    )

    assert fixture.duration_band is AsrFixtureDurationBand.UNDER_3S
    assert fixture.split is AsrFixtureSplit.DEVELOPMENT


def test_measured_metric_requires_a_value_and_not_measured_forbids_one() -> None:
    with pytest.raises(ValidationError, match="MEASURED metrics must contain"):
        AsrBenchmarkMeasurementV1(status=BenchmarkMeasurementStatus.MEASURED, reason="missing")
    with pytest.raises(ValidationError, match="NOT_MEASURED metrics must not contain"):
        AsrBenchmarkMeasurementV1(
            status=BenchmarkMeasurementStatus.NOT_MEASURED, value=0.1, reason="unexpected"
        )

    measured = AsrBenchmarkMeasurementV1(
        status=BenchmarkMeasurementStatus.MEASURED, value=0.12, reason="computed"
    )
    assert measured.value == pytest.approx(0.12)


def _ready_manifest() -> AsrRound1FixtureManifestV1:
    return _manifest(*_ready_entries())


def _ready_entries() -> tuple[AsrRound1FixtureEntryV1, ...]:
    return (
        _entry(
            "vi-clear",
            AsrFixtureScenario.VI_CLEAR,
            expected_language="vi",
            eligible=True,
            language_accuracy_eligible=True,
        ),
        _entry(
            "en-clear",
            AsrFixtureScenario.NON_VI_CLEAR,
            expected_language="en",
            eligible=True,
            language_accuracy_eligible=True,
        ),
        _entry(
            "vi-en-code-switch",
            AsrFixtureScenario.VI_EN_CODE_SWITCH,
            expected_language="vi",
            expected_languages=("vi", "en"),
            eligible=True,
        ),
        _entry("silence", AsrFixtureScenario.SILENCE),
        _entry(
            "room-noise",
            AsrFixtureScenario.NOISE,
            noise_condition_id="room-noise-v1",
        ),
        _entry(
            "vi-noisy",
            AsrFixtureScenario.NOISY_SPEECH,
            expected_language="vi",
            eligible=True,
            language_accuracy_eligible=True,
            noise_condition_id="room-noise-v1",
        ),
        _entry(
            "en-noisy",
            AsrFixtureScenario.NOISY_SPEECH,
            expected_language="en",
            eligible=True,
            language_accuracy_eligible=True,
            noise_condition_id="room-noise-v1",
        ),
    )


def _manifest(
    *entries: AsrRound1FixtureEntryV1,
    status: AsrRound1ManifestStatus = AsrRound1ManifestStatus.READY,
) -> AsrRound1FixtureManifestV1:
    return AsrRound1FixtureManifestV1(
        manifest_version="asr-round1-v1",
        normalizer_version=VIETNAMESE_ASR_NORMALIZER_VERSION,
        status=status,
        fixtures=entries,
        notes="metadata-only test manifest",
    )


def _entry(
    fixture_id: str,
    scenario: AsrFixtureScenario,
    *,
    expected_language: str | None = None,
    expected_languages: tuple[str, ...] | None = None,
    eligible: bool = False,
    language_accuracy_eligible: bool = False,
    noise_condition_id: str | None = None,
    duration_band: AsrFixtureDurationBand = AsrFixtureDurationBand.FROM_3S_TO_8S,
    split: AsrFixtureSplit = AsrFixtureSplit.HELD_OUT,
) -> AsrRound1FixtureEntryV1:
    speech = scenario not in {AsrFixtureScenario.SILENCE, AsrFixtureScenario.NOISE}
    transcript_ref = f"transcripts/{fixture_id}.txt" if speech else None
    transcript_hash = sha256(f"reference:{fixture_id}".encode()).hexdigest()
    return AsrRound1FixtureEntryV1(
        fixture_id=fixture_id,
        scenario=scenario,
        expected_language=expected_language,
        expected_languages=expected_languages,
        source_audio_ref=f"audio/{scenario.value}/{fixture_id}.wav",
        source_audio_sha256=sha256(f"audio:{fixture_id}".encode()).hexdigest(),
        reference_transcript_ref=transcript_ref,
        reference_transcript_sha256=transcript_hash if speech else None,
        data_provenance=AsrFixtureDataProvenance.SYNTHETIC,
        wer_eligible=eligible,
        cer_eligible=eligible,
        language_accuracy_eligible=language_accuracy_eligible,
        noise_condition_id=noise_condition_id,
        fixture_version="v1",
        expected_speech_present=speech,
        duration_band=duration_band,
        split=split,
        notes="test fixture metadata only",
    )
