"""B1 contract tests: additive Phase B catalog change over the approved Phase A contract.

Proves two things required by the approved Phase B scope
(plan/P2_T2_ASR_RESEARCH_PLAN.md, "Phase B approval request / B1"):
1. every Phase A fake profile's value/behavior is unchanged after the catalog rename; and
2. Whisper (FASTER_WHISPER) candidates resolve deterministically through the same catalog.

No model SDK, dependency, GPU, or network access is used here.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.asr import (
    AsrProfileId,
    AsrProfileV1,
    AsrWeightProvenanceV1,
    asr_profile_catalog,
    profile_config_hash,
)


def test_phase_a_fake_profiles_are_unchanged_after_the_catalog_rename() -> None:
    catalog = asr_profile_catalog()

    deterministic = catalog.resolve(AsrProfileId.FAKE_DETERMINISTIC_V1)
    assert deterministic.adapter_kind == "DETERMINISTIC_FAKE"
    assert deterministic.beam_size == 1
    assert deterministic.timeout_seconds == 5.0
    assert deterministic.idempotent_timeout_retry is False
    assert deterministic.compute_profile == "NONE"
    assert deterministic.model_identifier is None
    assert deterministic.model_revision is None
    assert deterministic.weight_provenance is None
    assert deterministic.adapter_version is None
    assert deterministic.runtime_version is None

    idempotent = catalog.resolve(AsrProfileId.FAKE_IDEMPOTENT_TIMEOUT_V1)
    assert idempotent.adapter_kind == "DETERMINISTIC_FAKE"
    assert idempotent.idempotent_timeout_retry is True
    assert idempotent.model_identifier is None


@pytest.mark.parametrize(
    ("profile_id", "compute_profile", "model_identifier"),
    (
        (
            AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            "GPU_INT8_FLOAT16",
            "deepdml/faster-whisper-large-v3-turbo-ct2",
        ),
        (
            AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1,
            "GPU_FLOAT16",
            "deepdml/faster-whisper-large-v3-turbo-ct2",
        ),
        (
            AsrProfileId.WHISPER_LARGE_V3_INT8_AUTO_V1,
            "GPU_INT8_FLOAT16",
            "Systran/faster-whisper-large-v3",
        ),
    ),
)
def test_whisper_round1_profiles_resolve_deterministically(
    profile_id: AsrProfileId, compute_profile: str, model_identifier: str
) -> None:
    first = asr_profile_catalog().resolve(profile_id)
    second = asr_profile_catalog().resolve(profile_id)

    assert first == second
    assert first.adapter_kind == "FASTER_WHISPER"
    assert first.language_mode == "AUTO_DETECT"
    assert first.vad_enabled is False
    assert first.word_timestamps_enabled is False
    assert first.beam_size == 5
    assert first.compute_profile == compute_profile
    assert first.model_identifier == model_identifier
    assert first.model_revision is not None
    assert first.weight_provenance is not None
    assert first.weight_provenance.license == "MIT"
    assert first.adapter_version is not None
    assert first.runtime_version is not None


def test_whisper_and_fake_profiles_get_distinct_reproducible_config_hashes() -> None:
    catalog = asr_profile_catalog()
    turbo_int8 = catalog.resolve(AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1)
    turbo_fp16 = catalog.resolve(AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1)
    fake = catalog.resolve(AsrProfileId.FAKE_DETERMINISTIC_V1)

    assert profile_config_hash(turbo_int8) == profile_config_hash(turbo_int8)
    assert profile_config_hash(turbo_int8) != profile_config_hash(turbo_fp16)
    assert profile_config_hash(turbo_int8) != profile_config_hash(fake)


def test_faster_whisper_profile_requires_all_provenance_fields() -> None:
    with pytest.raises(ValidationError, match="requires model_identifier"):
        AsrProfileV1(
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            adapter_kind="FASTER_WHISPER",
            beam_size=5,
            compute_profile="GPU_INT8_FLOAT16",
            timeout_seconds=120.0,
        )


def test_faster_whisper_profile_requires_a_real_compute_profile() -> None:
    with pytest.raises(ValidationError, match="requires a real compute_profile"):
        AsrProfileV1(
            profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
            adapter_kind="FASTER_WHISPER",
            beam_size=5,
            compute_profile="NONE",
            timeout_seconds=120.0,
            model_identifier="deepdml/faster-whisper-large-v3-turbo-ct2",
            model_revision="4df90f75321148c3a29a9e2351b7ddf8f5b115a8",
            weight_provenance=AsrWeightProvenanceV1(
                source="huggingface:deepdml/faster-whisper-large-v3-turbo-ct2", license="MIT"
            ),
            adapter_version="faster-whisper-asr-adapter-v1",
            runtime_version="faster-whisper==1.2.1",
        )


def test_deterministic_fake_profile_rejects_whisper_provenance_fields() -> None:
    with pytest.raises(ValidationError, match="must not set Whisper provenance fields"):
        AsrProfileV1(
            profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1,
            beam_size=1,
            timeout_seconds=5.0,
            model_identifier="deepdml/faster-whisper-large-v3-turbo-ct2",
        )


def test_catalog_still_rejects_an_out_of_catalog_profile_id() -> None:
    with pytest.raises(ValueError, match="profile is absent from catalog"):
        asr_profile_catalog().resolve("NOT_A_REAL_PROFILE_ID")  # type: ignore[arg-type]
