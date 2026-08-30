"""Strict, provider-neutral contracts for the P2-T2 ASR benchmark inputs.

The manifest contains references and hashes only. Audio and transcript payloads stay
outside this contract and are supplied by the selected local fixture source.
"""

from __future__ import annotations

import re
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SHA256_PATTERN = r"^[a-f0-9]{64}$"
_SHA256_RE = re.compile(SHA256_PATTERN)
_FIXTURE_ID_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,94}[a-z0-9])?$"
_VERSION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
_LANGUAGE_TAG_PATTERN = r"^[a-z]{2,16}(?:-[a-z0-9]{2,16})?$"
_NOISE_CONDITION_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")
LanguageTag = Annotated[str, Field(pattern=_LANGUAGE_TAG_PATTERN)]


class AsrFixtureScenario(StrEnum):
    """Round-1 slices whose interpretation is stable before audio is selected."""

    VI_CLEAR = "vi_clear"
    NON_VI_CLEAR = "non_vi_clear"
    VI_EN_CODE_SWITCH = "vi_en_code_switch"
    SILENCE = "silence"
    NOISE = "noise"
    NOISY_SPEECH = "noisy_speech"


class AsrFixtureDataProvenance(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    LICENSED = "LICENSED"


class AsrRound1ManifestStatus(StrEnum):
    TEMPLATE = "TEMPLATE"
    READY = "READY"


class AsrFixtureSplit(StrEnum):
    """Round-1 results from different splits are never aggregated together."""

    DEVELOPMENT = "DEVELOPMENT"
    HELD_OUT = "HELD_OUT"


class AsrFixtureDurationBand(StrEnum):
    """Coarse, versioned duration buckets recorded before any measurement exists."""

    UNDER_3S = "under_3s"
    FROM_3S_TO_8S = "3s_to_8s"
    FROM_8S_TO_15S = "8s_to_15s"
    OVER_15S = "over_15s"


def duration_band_for_seconds(seconds: float) -> AsrFixtureDurationBand:
    """Classify a decoded duration into the same bands a manifest entry declares.

    Shared by fixture generation and by the Round-1 runner's pre-inference duration check, so
    "the manifest says X" and "the audio actually is X" can never silently drift apart.
    """

    if seconds < 3:
        return AsrFixtureDurationBand.UNDER_3S
    if seconds < 8:
        return AsrFixtureDurationBand.FROM_3S_TO_8S
    if seconds < 15:
        return AsrFixtureDurationBand.FROM_8S_TO_15S
    return AsrFixtureDurationBand.OVER_15S


class AsrRound1FixtureEntryV1(BaseModel):
    """One ASR-only fixture declaration; no media or transcript content is embedded."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, revalidate_instances="always"
    )

    fixture_id: str = Field(pattern=_FIXTURE_ID_PATTERN, max_length=96)
    scenario: AsrFixtureScenario
    expected_language: LanguageTag | None = None
    expected_languages: tuple[LanguageTag, ...] | None = Field(
        default=None, min_length=1, max_length=4
    )
    source_audio_ref: str = Field(min_length=1, max_length=512)
    source_audio_sha256: str = Field(pattern=SHA256_PATTERN)
    reference_transcript_ref: str | None = Field(default=None, max_length=512)
    reference_transcript_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    data_provenance: AsrFixtureDataProvenance
    wer_eligible: bool = False
    cer_eligible: bool = False
    language_accuracy_eligible: bool = False
    noise_condition_id: str | None = Field(
        default=None, pattern=_NOISE_CONDITION_PATTERN, max_length=64
    )
    fixture_version: str = Field(pattern=_VERSION_PATTERN)
    expected_speech_present: bool
    duration_band: AsrFixtureDurationBand
    split: AsrFixtureSplit
    notes: str = Field(min_length=1, max_length=512)

    @field_validator("source_audio_ref", "reference_transcript_ref")
    @classmethod
    def _references_are_non_absolute(cls, value: str | None) -> str | None:
        """Reject machine-local paths while allowing opaque fixture/provider references."""

        if value is None:
            return None
        normalized = value.replace("\\", "/")
        if (
            "\x00" in value
            or value.startswith(("/", "\\"))
            or normalized.startswith("//")
            or _WINDOWS_DRIVE_PATTERN.match(value) is not None
            or any(part == ".." for part in normalized.split("/"))
        ):
            raise ValueError("fixture references must not be absolute or traverse parent paths")
        return value

    @model_validator(mode="after")
    def _requires_coherent_transcript_and_eligibility(self) -> AsrRound1FixtureEntryV1:
        transcript_ref_set = self.reference_transcript_ref is not None
        transcript_hash_set = self.reference_transcript_sha256 is not None
        if transcript_ref_set != transcript_hash_set:
            raise ValueError(
                "reference transcript ref/hash must be set together"
            )
        non_speech = {AsrFixtureScenario.SILENCE, AsrFixtureScenario.NOISE}
        if self.scenario in non_speech:
            if self.expected_language is not None:
                raise ValueError("silence/noise fixtures must not declare an expected language")
            if self.expected_languages is not None:
                raise ValueError("silence/noise fixtures must not declare expected languages")
            if self.wer_eligible or self.cer_eligible:
                raise ValueError("silence/noise fixtures cannot be WER/CER eligible")
            if self.language_accuracy_eligible:
                raise ValueError("silence/noise fixtures cannot be language-accuracy eligible")
            if transcript_ref_set:
                raise ValueError("silence/noise fixtures must not require a transcript")
            if self.expected_speech_present:
                raise ValueError(
                    "silence/noise fixtures must declare expected_speech_present=false"
                )
            if self.scenario is AsrFixtureScenario.NOISE and self.noise_condition_id is None:
                raise ValueError("noise fixtures require a noise condition ID")
            if self.scenario is AsrFixtureScenario.SILENCE and self.noise_condition_id is not None:
                raise ValueError("silence fixtures must not declare a noise condition ID")
            return self

        if not self.expected_speech_present:
            raise ValueError("speech fixtures must declare expected_speech_present=true")
        if self.expected_language is None:
            raise ValueError("speech fixtures require expected language metadata")
        if not transcript_ref_set:
            raise ValueError("speech fixtures require a reference transcript ref/hash")
        if self.wer_eligible != self.cer_eligible:
            raise ValueError("speech WER and CER eligibility must match")

        declared_languages = self.expected_languages or (self.expected_language,)
        if self.scenario is AsrFixtureScenario.VI_EN_CODE_SWITCH:
            if self.expected_language != "vi" or declared_languages != ("vi", "en"):
                raise ValueError(
                    "code-switch fixtures must declare expected_language=vi and languages vi,en"
                )
            if self.language_accuracy_eligible:
                raise ValueError("code-switch fixtures cannot be language-accuracy eligible")
        else:
            if len(declared_languages) != 1 or declared_languages[0] != self.expected_language:
                raise ValueError(
                    "single-language speech metadata must declare exactly one language"
                )
            if self.scenario is AsrFixtureScenario.VI_CLEAR and self.expected_language != "vi":
                raise ValueError("vi_clear fixtures must declare expected_language=vi")
            if (
                self.scenario is AsrFixtureScenario.NON_VI_CLEAR
                and self.expected_language.split("-", 1)[0] == "vi"
            ):
                raise ValueError(
                    "non_vi_clear fixtures must declare a non-Vietnamese primary language subtag"
                )
        if self.scenario is AsrFixtureScenario.NOISY_SPEECH:
            if self.noise_condition_id is None:
                raise ValueError("noisy_speech fixtures require a noise condition ID")
        elif self.noise_condition_id is not None:
            raise ValueError("only noisy_speech/noise fixtures may declare a noise condition ID")
        return self


class AsrRound1FixtureManifestV1(BaseModel):
    """Versioned Round-1 manifest with deterministic entry-level validation."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, revalidate_instances="always"
    )

    contract_name: Literal["AsrRound1FixtureManifestV1"] = "AsrRound1FixtureManifestV1"
    contract_version: Literal["1.0"] = "1.0"
    manifest_version: str = Field(pattern=_VERSION_PATTERN)
    data_policy: Literal["synthetic-or-licensed-only"] = "synthetic-or-licensed-only"
    normalizer_version: str = Field(min_length=1, max_length=64)
    status: AsrRound1ManifestStatus = AsrRound1ManifestStatus.TEMPLATE
    fixtures: tuple[AsrRound1FixtureEntryV1, ...] = ()
    notes: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def _requires_unique_fixture_ids(self) -> AsrRound1FixtureManifestV1:
        fixture_ids = tuple(fixture.fixture_id for fixture in self.fixtures)
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("fixture IDs must be unique")
        if self.status is AsrRound1ManifestStatus.READY:
            _validate_ready_manifest(self)
        return self


# Short aliases keep the contract discoverable without creating a second schema identity.
AsrFixtureEntryV1 = AsrRound1FixtureEntryV1
AsrFixtureManifestV1 = AsrRound1FixtureManifestV1


def _validate_ready_manifest(manifest: AsrRound1FixtureManifestV1) -> None:
    required_scenarios = {
        AsrFixtureScenario.VI_CLEAR,
        AsrFixtureScenario.NON_VI_CLEAR,
        AsrFixtureScenario.VI_EN_CODE_SWITCH,
        AsrFixtureScenario.SILENCE,
        AsrFixtureScenario.NOISE,
        AsrFixtureScenario.NOISY_SPEECH,
    }
    present_scenarios = {fixture.scenario for fixture in manifest.fixtures}
    missing_scenarios = required_scenarios - present_scenarios
    if missing_scenarios:
        missing = ", ".join(sorted(scenario.value for scenario in missing_scenarios))
        raise ValueError(f"READY manifest is missing required scenarios: {missing}")

    single_language_clear = {
        fixture.expected_language
        for fixture in manifest.fixtures
        if fixture.scenario in {
            AsrFixtureScenario.VI_CLEAR,
            AsrFixtureScenario.NON_VI_CLEAR,
        }
        and fixture.language_accuracy_eligible
        and fixture.expected_language is not None
    }
    if "vi" not in single_language_clear:
        raise ValueError("READY manifest needs a language-accuracy-eligible vi_clear fixture")
    non_vietnamese_clear = single_language_clear - {"vi"}
    if not non_vietnamese_clear:
        raise ValueError(
            "READY manifest needs a language-accuracy-eligible non_vi_clear fixture"
        )

    noisy_languages = {
        fixture.expected_language
        for fixture in manifest.fixtures
        if fixture.scenario is AsrFixtureScenario.NOISY_SPEECH
        and fixture.expected_language is not None
        and fixture.expected_languages in (None, (fixture.expected_language,))
        and (fixture.wer_eligible or fixture.cer_eligible or fixture.language_accuracy_eligible)
    }
    missing_noisy_languages = (single_language_clear | non_vietnamese_clear) - noisy_languages
    if missing_noisy_languages:
        missing = ", ".join(sorted(missing_noisy_languages))
        raise ValueError(f"noise coverage is missing noisy_speech for language(s): {missing}")

    noise_conditions = {
        fixture.noise_condition_id
        for fixture in manifest.fixtures
        if fixture.scenario is AsrFixtureScenario.NOISE
        and fixture.noise_condition_id is not None
    }
    noisy_conditions = {
        fixture.noise_condition_id
        for fixture in manifest.fixtures
        if fixture.scenario is AsrFixtureScenario.NOISY_SPEECH
        and fixture.noise_condition_id is not None
        and (fixture.wer_eligible or fixture.cer_eligible or fixture.language_accuracy_eligible)
    }
    if noisy_conditions - noise_conditions:
        raise ValueError("every noisy_speech condition needs a matching noise fixture")
    if noise_conditions - noisy_conditions:
        raise ValueError("every noise fixture must correspond to a noisy_speech condition")


def asr_round1_manifest_hash(manifest: AsrRound1FixtureManifestV1) -> str:
    """Return the stable SHA-256 of the manifest's canonical JSON representation."""

    payload = dumps(
        manifest.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def is_sha256(value: str) -> bool:
    """Expose the contract's canonical lowercase SHA-256 check for readiness tooling."""

    return _SHA256_RE.fullmatch(value) is not None
