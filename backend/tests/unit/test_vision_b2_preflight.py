from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from struct import pack
from typing import Any
from wave import open as wave_open

import pytest

from sketch2life.benchmark import vision_b2_preflight as _module
from sketch2life.benchmark.vision_b2_preflight import (
    NoRealP2T1PassAvailableError,
    UnsafeFixturePathError,
    UnsafeFixturesDirectoryError,
    _write_synthetic_preflight_audio,
    _write_synthetic_preflight_image,
    run_b2_preflight,
)
from sketch2life.contracts.schemas.vision import VisionErrorCode, VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)

_SOURCE_REF = VisionImageReferenceV1(artifact_ref="fixture:vision:b2:drawing.bin", sha256="a" * 64)
_EXECUTED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "b2-preflight-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "PASSED",
        "entities": (),
        "actions": (),
        "relations": (),
        "themes": (),
        "ambiguous_regions": (),
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash_v2(profile),
        "model_provenance": profile.model_provenance,
    }
    values.update(overrides)
    return VisionUnderstandingSuccessV2(**values)


def _failure(**overrides: Any) -> VisionUnderstandingFailureV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "b2-preflight-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "NOT_EXECUTED",
        "error_code": VisionErrorCode.VISION_PROVIDER_FAILURE,
        "error_detail": VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE,
        "retryable": False,
        "model_provenance": profile.model_provenance,
    }
    values.update(overrides)
    if overrides.get("model_provenance", object()) is None:
        values.pop("model_provenance", None)
    return VisionUnderstandingFailureV2(**values)


class _FakeVisionAdapter:
    def __init__(self, result: VisionUnderstandingResultV2) -> None:
        self._result = result
        self.calls = 0
        self.last_request: VisionUnderstandingRequestV2 | None = None

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        self.calls += 1
        self.last_request = request
        return self._result


def _write_silent_wav(path: Path) -> None:
    sample_rate = 16000
    seconds = 0.2
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pack("<h", 0) * int(sample_rate * seconds))


def test_success_call_reports_typed_result_with_vram_sampling_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    result = run_b2_preflight(adapter, fixtures_dir=Path("scratch"), sample_vram=False)

    assert adapter.calls == 1
    assert result.status == "SUCCEEDED"
    assert result.error_code is None
    assert result.error_detail is None
    assert result.model_identifier == "Qwen/Qwen3-VL-8B-Instruct"
    assert result.model_revision
    assert result.wall_latency_ms >= 0.0
    assert result.peak_vram_mb is None
    assert result.baseline_vram_mb is None
    assert result.vram_not_measured_reason == "VRAM sampling was disabled for this call"


def test_failure_call_with_no_provenance_reports_null_model_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    failure = _failure(
        policy_execution_state="NOT_EXECUTED",
        error_code=VisionErrorCode.INPUT_NOT_VALIDATED,
        error_detail=VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE,
        attempt_number=0,
        retryable=False,
        model_provenance=None,
    )
    adapter = _FakeVisionAdapter(failure)

    result = run_b2_preflight(adapter, fixtures_dir=Path("scratch"), sample_vram=False)

    assert result.status == "FAILED"
    assert result.error_code == "INPUT_NOT_VALIDATED"
    assert result.error_detail == "PROFILE_NOT_RESOLVABLE"
    assert result.model_identifier is None
    assert result.model_revision is None


def test_adapter_receives_a_real_earned_p2t1_pass_with_relative_artifact_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    run_b2_preflight(adapter, fixtures_dir=Path("scratch"), sample_vram=False)

    assert adapter.last_request is not None
    media_validation = adapter.last_request.media_validation
    assert media_validation is not None
    assert media_validation.decision == "PASS"
    assert media_validation.validator_policy_version
    artifact_ref = adapter.last_request.source_image_ref.artifact_ref
    assert not artifact_ref.startswith("/")
    assert ":" not in artifact_ref


def test_fixtures_are_deleted_after_the_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    run_b2_preflight(adapter, fixtures_dir=Path("scratch"), sample_vram=False)

    assert not (tmp_path / "scratch").exists()


def test_fixtures_are_deleted_even_when_the_adapter_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    class _RaisingAdapter:
        def understand(
            self, request: VisionUnderstandingRequestV2
        ) -> VisionUnderstandingResultV2:
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        run_b2_preflight(_RaisingAdapter(), fixtures_dir=Path("scratch"), sample_vram=False)

    assert not (tmp_path / "scratch").exists()


def test_no_real_pass_available_refuses_to_call_the_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    def _build_bad_fixtures(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        image_path = fixtures_dir / "preflight.png"
        audio_path = fixtures_dir / "preflight.wav"
        _write_synthetic_preflight_image(image_path)
        _write_silent_wav(audio_path)
        return image_path, audio_path

    with pytest.raises(NoRealP2T1PassAvailableError):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_bad_fixtures,
        )

    assert adapter.calls == 0


def test_vram_sampler_stays_none_when_nvidia_smi_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    def _raise_missing_binary(*_args: Any, **_kwargs: Any) -> Any:
        raise OSError("nvidia-smi not found")

    monkeypatch.setattr(subprocess, "run", _raise_missing_binary)

    result = run_b2_preflight(adapter, fixtures_dir=Path("scratch"), sample_vram=True)

    assert result.baseline_vram_mb is None
    assert result.peak_vram_mb is None
    assert result.post_call_vram_mb is None
    assert result.vram_not_measured_reason == "nvidia-smi was unavailable or returned no sample"


def test_absolute_fixtures_dir_is_rejected_before_any_fixture_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())
    unsafe_dir = tmp_path / "elsewhere" / "scratch"

    with pytest.raises(UnsafeFixturesDirectoryError):
        run_b2_preflight(adapter, fixtures_dir=unsafe_dir, sample_vram=False)

    assert adapter.calls == 0
    assert not unsafe_dir.exists()


def test_fixtures_dir_equal_to_cwd_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    with pytest.raises(UnsafeFixturesDirectoryError):
        run_b2_preflight(adapter, fixtures_dir=Path("."), sample_vram=False)

    assert adapter.calls == 0


def test_fixtures_dir_that_escapes_cwd_via_dotdot_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "workdir").mkdir()
    monkeypatch.chdir(tmp_path / "workdir")
    adapter = _FakeVisionAdapter(_success())

    with pytest.raises(UnsafeFixturesDirectoryError):
        run_b2_preflight(adapter, fixtures_dir=Path("../sibling-scratch"), sample_vram=False)

    assert adapter.calls == 0
    assert not (tmp_path / "sibling-scratch").exists()


def test_builder_partial_write_then_raise_still_cleans_up_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    def _build_then_raise(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        _write_synthetic_preflight_image(fixtures_dir / "preflight.png")
        raise RuntimeError("builder failed after partial write")

    with pytest.raises(RuntimeError, match="builder failed after partial write"):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_then_raise,
        )

    assert adapter.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_vram_sampler_thread_is_stopped_and_joined_when_adapter_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    class _FakeCompletedProcess:
        returncode = 0
        stdout = "123\n"

    def _fake_run(*_args: Any, **_kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", _fake_run)

    created_instances: list[_module._VramSampler] = []
    real_cls = _module._VramSampler

    class _TrackingVramSampler(real_cls):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            created_instances.append(self)

    monkeypatch.setattr(_module, "_VramSampler", _TrackingVramSampler)

    class _RaisingAdapter:
        def understand(
            self, request: VisionUnderstandingRequestV2
        ) -> VisionUnderstandingResultV2:
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        run_b2_preflight(_RaisingAdapter(), fixtures_dir=Path("scratch"), sample_vram=True)

    assert len(created_instances) == 1
    sampler = created_instances[0]
    assert sampler._thread is not None
    assert not sampler._thread.is_alive()


def test_builder_returning_an_absolute_path_outside_scratch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()

    def _build_outside_fixtures(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        image_path = outside_dir / "preflight.png"
        audio_path = fixtures_dir / "preflight.wav"
        _write_synthetic_preflight_image(image_path)
        _write_synthetic_preflight_audio(audio_path)
        return image_path, audio_path

    with pytest.raises(UnsafeFixturePathError):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_outside_fixtures,
        )

    assert adapter.calls == 0


def test_builder_returning_a_relative_path_that_escapes_scratch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())
    (tmp_path / "outside").mkdir()

    def _build_escaping_fixtures(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        image_path = Path("outside") / "preflight.png"
        audio_path = fixtures_dir / "preflight.wav"
        _write_synthetic_preflight_image(image_path)
        _write_synthetic_preflight_audio(audio_path)
        return image_path, audio_path

    with pytest.raises(UnsafeFixturePathError):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_escaping_fixtures,
        )

    assert adapter.calls == 0


def test_fixture_path_equal_to_fixtures_dir_itself_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    def _build_dir_as_image(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        audio_path = fixtures_dir / "preflight.wav"
        _write_synthetic_preflight_audio(audio_path)
        return fixtures_dir, audio_path

    with pytest.raises(UnsafeFixturePathError):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_dir_as_image,
        )

    assert adapter.calls == 0


def test_fixture_path_that_is_a_nested_directory_inside_scratch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    def _build_nested_dir_as_image(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        nested_dir = fixtures_dir / "nested-directory"
        nested_dir.mkdir()
        audio_path = fixtures_dir / "preflight.wav"
        _write_synthetic_preflight_audio(audio_path)
        return nested_dir, audio_path

    with pytest.raises(UnsafeFixturePathError):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_nested_dir_as_image,
        )

    assert adapter.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_fixture_path_that_does_not_exist_inside_scratch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter = _FakeVisionAdapter(_success())

    def _build_missing_file(fixtures_dir: Path) -> tuple[Path, Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        missing_image_path = fixtures_dir / "never-written.png"
        audio_path = fixtures_dir / "preflight.wav"
        _write_synthetic_preflight_audio(audio_path)
        return missing_image_path, audio_path

    with pytest.raises(UnsafeFixturePathError):
        run_b2_preflight(
            adapter,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_missing_file,
        )

    assert adapter.calls == 0
    assert not (tmp_path / "scratch").exists()
