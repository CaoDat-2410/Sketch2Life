"""Focused, no-GPU tests for the dedicated v3 mapping-validation runner.

Mirrors ``test_vision_c1_prompt_mapping_study.py``'s fake-adapter/fake-generation-runner test
doubles and ``test_vision_v3_mapping_fixtures.py``'s ``monkeypatch.chdir(tmp_path)`` scratch-safety
pattern, but is fully self-contained (no cross-file test-helper imports, matching this project's
existing per-file convention).
"""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from struct import pack
from typing import Any
from zlib import compress, crc32

import pytest

from sketch2life.benchmark import vision_v3_mapping_validation_study as _module
from sketch2life.benchmark.vision_b3_mapping_study import B3RawOutputCollector, B3RawOutputMode
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1PromptProtocol,
    c1_prompt_protocol_id_v3,
    c1_prompt_schema_target,
    c1_prompt_sha256_v3,
    c1_prompt_text,
    c1_prompt_text_v2,
    c1_prompt_text_v3,
)
from sketch2life.benchmark.vision_v3_mapping_fixtures import author_v3_map_fixture_package
from sketch2life.benchmark.vision_v3_mapping_validation_study import (
    NoRealV3P2T1PassAvailableError,
    V3BlockingReason,
    V3FixtureRunResult,
    V3ManifestIntegrityError,
    V3MappingSummary,
    V3PassReport,
    V3PromptBindingError,
    V3RunLabel,
    evaluate_v3_readiness,
    load_and_verify_v3_fixtures,
    qwen_v3_adapter_factory,
    run_v3_pass,
)
from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionProfileV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_EXECUTED_AT = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
_EXPECTED_PROFILE_ID = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
_EXPECTED_CATALOG_HASH = vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
_EMPTY_OBSERVATIONS = {
    "entities": [],
    "actions": [],
    "relations": [],
    "themes": [],
    "ambiguous_regions": [],
}
_SOURCE_REF = VisionImageReferenceV1(artifact_ref="fixture:vision:v3:drawing.bin", sha256="a" * 64)
_V3_FIXTURE_IDS = tuple(f"v3-map-fixture-{index:02d}" for index in range(1, 9))


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "v3-mapping-validation-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": _EXPECTED_CATALOG_HASH,
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "PASSED",
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash_v2(profile),
        "model_provenance": profile.model_provenance,
        **_EMPTY_OBSERVATIONS,
    }
    values.update(overrides)
    return VisionUnderstandingSuccessV2(**values)


class _ScriptedAdapter:
    """Fixed outcome/raw-output pair per call; invokes the hook only when raw output exists."""

    def __init__(
        self,
        outcomes: list[VisionUnderstandingResultV2],
        raw_outputs: list[str | None],
        hook: Any,
    ) -> None:
        assert len(outcomes) == len(raw_outputs)
        self._outcomes = outcomes
        self._raw_outputs = raw_outputs
        self._hook = hook
        self.calls = 0

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        index = self.calls
        self.calls += 1
        raw = self._raw_outputs[index]
        if raw is not None:
            self._hook(raw)
        return self._outcomes[index]


class _RaisingAfterNAdapter:
    """Raises on the Nth call (0-indexed), proving scratch cleanup survives a mid-pass failure."""

    def __init__(self, hook: Any, *, raise_at_call: int) -> None:
        self._hook = hook
        self._raise_at_call = raise_at_call
        self.calls = 0

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        index = self.calls
        self.calls += 1
        if index == self._raise_at_call:
            raise RuntimeError("simulated mid-pass adapter failure")
        self._hook(json.dumps(_EMPTY_OBSERVATIONS))
        return _success()


class _RecordingAdapterFactory:
    """Records the exact prompt/hook received; the only way these tests obtain a report."""

    def __init__(
        self, outcomes: list[VisionUnderstandingResultV2], raw_outputs: list[str | None]
    ) -> None:
        self._outcomes = outcomes
        self._raw_outputs = raw_outputs
        self.calls = 0
        self.received_prompt: str | None = None
        self.received_hook: Any = None
        self.built_adapter: _ScriptedAdapter | None = None

    def __call__(self, prompt: str, on_raw_output: Any) -> _ScriptedAdapter:
        self.calls += 1
        self.received_prompt = prompt
        self.received_hook = on_raw_output
        self.built_adapter = _ScriptedAdapter(self._outcomes, self._raw_outputs, on_raw_output)
        return self.built_adapter


class _RecordingGenerationRunner:
    """Records every prompt received; returns a fixed valid V2 JSON payload per call."""

    def __init__(self, outcomes: list[str]) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0
        self.received_prompts: list[str] = []

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        del profile, runtime_config, image_path
        self.calls += 1
        self.received_prompts.append(prompt)
        return self._outcomes[self.calls - 1]


def _all_success_scripted() -> tuple[_RecordingAdapterFactory, B3RawOutputCollector]:
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [json.dumps(_EMPTY_OBSERVATIONS) for _ in range(8)]
    return _RecordingAdapterFactory(outcomes, raw_outputs), collector


def _write_flat_png(path: Path, *, size: int = 192, shade: int = 200) -> None:
    """A uniform, textureless PNG: reliably fails the real P2-T1 edge-strength/contrast gate
    (``minimum_edge_strength``/``minimum_luminance_standard_deviation`` in
    ``domain/understanding/media_quality.py``), unlike every fixture image this project's
    recipe modules author (which all use a periodic interior shading pattern specifically to
    clear that gate).
    """

    rows = bytearray()
    for _ in range(size):
        rows.append(0)
        rows.extend((shade, shade, shade) * size)
    compressed = compress(bytes(rows), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return pack(">I", len(data)) + tag + data + pack(">I", crc32(tag + data) & 0xFFFFFFFF)

    ihdr = pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def _author_and_write_manifest(
    tmp_path: Path,
    *,
    status: str = "OWNER_IMAGE_REVIEW_APPROVED",
    protocol_id: str | None = None,
    prompt_sha256: str | None = None,
    schema_target: str | None = None,
) -> tuple[Path, Path]:
    """Authors real, deterministic v3 images and writes a manifest matching their real hashes.

    Returns ``(manifest_path, images_root)`` where ``images_root`` is the *parent* of the
    ``images/`` directory (matching the real manifest's ``image_ref`` convention:
    ``"images/<fixture_id>.png"`` resolved against ``images_root``).
    """

    result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    manifest: dict[str, Any] = {
        "author": "Person 2",
        "authoring_boundary": "test-authored fixture set",
        "contract_name": "VisionV3MapFixtureManifestV1",
        "contract_version": "1.0",
        "data_policy": "synthetic-only",
        "disjointness": {
            "b3_regenerated_hash_comparison_status": "VERIFIED_NO_OVERLAP",
            "b4_manifest_hash_comparison_status": "VERIFIED_NO_OVERLAP",
        },
        "fixtures": [
            {
                "dimensions": {"height": fixture.height, "width": fixture.width},
                "fixture_id": fixture.fixture_id,
                "image_ref": fixture.image_ref,
                "image_sha256": fixture.image_sha256,
                "p2t1_pass": fixture.p2t1_pass,
                "taxonomy_token": fixture.taxonomy_token,
            }
            for fixture in result.fixtures
        ],
        "has_ground_truth": False,
        "image_generation": {
            "deterministic": True,
            "dimensions": {"height": 192, "width": 192},
            "palette_id": "vision-v3-map-palette-v1",
            "recipe_module_ref": (
                "backend/src/sketch2life/benchmark/vision_v3_mapping_fixtures.py"
            ),
            "recipe_module_sha256": "0" * 64,
        },
        "local_authoring_validation": {
            "model_or_gpu_called": False,
            "p2t1_result": "PASS_FOR_ALL_8_FIXTURES",
            "scratch_cleanup": "CONFIRMED",
        },
        "manifest_version": "vision-v3-map-manifest-v1",
        "prompt_protocol": {
            "protocol_id": protocol_id or c1_prompt_protocol_id_v3(),
            "schema_target": schema_target or c1_prompt_schema_target(),
            "sha256": prompt_sha256 or c1_prompt_sha256_v3(),
        },
        "purpose": "MAPPING_VALIDATION_ONLY",
        "status": status,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, tmp_path


def _corrupt_one_fixture_to_fail_real_p2t1(images_root: Path, manifest_path: Path) -> str:
    """Overwrites fixture 01's on-disk image with a flat PNG that fails real P2-T1, and re-pins
    the manifest's declared hash to match -- so ``load_and_verify_v3_fixtures`` (which never runs
    P2-T1 itself) still passes, and only the runner's own pre-adapter P2-T1 pre-check can fail.
    Returns the corrupted fixture's ID.
    """

    fixture_id = "v3-map-fixture-01"
    target = images_root / "images" / f"{fixture_id}.png"
    _write_flat_png(target)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixtures"][0]["image_sha256"] = sha256(target.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return fixture_id


# ---------------------------------------------------------------------------
# load_and_verify_v3_fixtures: manifest/fixture integrity (all fail closed)
# ---------------------------------------------------------------------------


def test_valid_manifest_and_fixtures_verify_successfully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)

    verified = load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)

    assert len(verified) == 8
    assert [fixture.fixture_id for fixture in verified] == list(_V3_FIXTURE_IDS)
    for fixture in verified:
        assert fixture.image_path.is_file()
        assert fixture.sha256 == sha256(fixture.image_path.read_bytes()).hexdigest()


def test_missing_manifest_file_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(V3ManifestIntegrityError, match="not found"):
        load_and_verify_v3_fixtures(manifest_path=tmp_path / "missing.json", images_root=tmp_path)


def test_malformed_json_manifest_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(V3ManifestIntegrityError, match="not valid JSON"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=tmp_path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("contract_name", "contract_name"),
        ("manifest_version", "manifest_version"),
        ("status", "review status"),
        ("purpose", "purpose"),
        ("has_ground_truth", "has_ground_truth"),
        ("data_policy", "data_policy"),
        ("model_or_gpu_called", "no model/GPU action"),
        ("p2t1_result", "P2-T1 pass"),
        ("disjointness", "disjointness"),
    ),
)
def test_manifest_identity_fields_fail_closed(
    mutation: str, message: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if mutation == "contract_name":
        manifest["contract_name"] = "WrongContract"
    elif mutation == "manifest_version":
        manifest["manifest_version"] = "vision-v3-map-manifest-v2"
    elif mutation == "status":
        manifest["status"] = "AWAITING_OWNER_IMAGE_REVIEW"
    elif mutation == "purpose":
        manifest["purpose"] = "SOMETHING_ELSE"
    elif mutation == "has_ground_truth":
        manifest["has_ground_truth"] = True
    elif mutation == "data_policy":
        manifest["data_policy"] = "not-synthetic"
    elif mutation == "model_or_gpu_called":
        manifest["local_authoring_validation"]["model_or_gpu_called"] = True
    elif mutation == "p2t1_result":
        manifest["local_authoring_validation"]["p2t1_result"] = "NOT_ALL_FIXTURES_PASSED"
    elif mutation == "disjointness":
        manifest["disjointness"]["b3_regenerated_hash_comparison_status"] = "NOT_YET_VERIFIED"

    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(V3ManifestIntegrityError, match=message):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_prompt_protocol_id_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(
        tmp_path, protocol_id="vision-v2-structured-output-prompt-v2"
    )

    with pytest.raises(V3ManifestIntegrityError, match="prompt_protocol"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_prompt_sha256_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path, prompt_sha256="0" * 64)

    with pytest.raises(V3ManifestIntegrityError, match="prompt_protocol"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_wrong_fixture_count_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixtures"] = manifest["fixtures"][:-1]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(V3ManifestIntegrityError, match="exactly 8 fixtures"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_wrong_fixture_order_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixtures = manifest["fixtures"]
    fixtures[0], fixtures[1] = fixtures[1], fixtures[0]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(V3ManifestIntegrityError, match="order/IDs"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_duplicate_declared_hash_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixtures"][1]["image_sha256"] = manifest["fixtures"][0]["image_sha256"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(V3ManifestIntegrityError, match="duplicate declared image_sha256"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_missing_image_file_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    (images_root / "images" / "v3-map-fixture-01.png").unlink()

    with pytest.raises(V3ManifestIntegrityError, match="not found on disk"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_on_disk_hash_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    target = images_root / "images" / "v3-map-fixture-01.png"
    target.write_bytes(target.read_bytes() + b"\x00")

    with pytest.raises(V3ManifestIntegrityError, match="hash does not match"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


def test_on_disk_dimension_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    target = images_root / "images" / "v3-map-fixture-01.png"
    # Forge the IHDR width field to 100 (still valid PNG framing, wrong declared dimension), then
    # re-pin the manifest's declared hash to the corrupted bytes so only the dimension check --
    # not the hash check -- can fail here.
    corrupt = bytearray(target.read_bytes())
    corrupt[16:20] = (100).to_bytes(4, "big")
    target.write_bytes(bytes(corrupt))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixtures"][0]["image_sha256"] = sha256(bytes(corrupt)).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(V3ManifestIntegrityError, match="dimensions do not match"):
        load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)


# ---------------------------------------------------------------------------
# Prompt binding: v3-only, no forgery/default/v1/v2 substitution possible
# ---------------------------------------------------------------------------


def test_v3_prompt_binding_error_fires_when_the_shared_constant_is_corrupted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forged = C1PromptProtocol(
        protocol_id="vision-v2-structured-output-prompt-v3",
        prompt_sha256="0" * 64,
        prompt_text_provider=c1_prompt_text_v3,
    )
    monkeypatch.setattr(_module, "C1_PROMPT_V3", forged)

    with pytest.raises(V3PromptBindingError, match="self-check failed"):
        _module._verified_v3_prompt_text()


def test_v3_prompt_binding_error_fires_on_unexpected_protocol_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forged = C1PromptProtocol(
        protocol_id="unexpected-protocol-id",
        prompt_sha256=c1_prompt_sha256_v3(),
        prompt_text_provider=c1_prompt_text_v3,
    )
    monkeypatch.setattr(_module, "C1_PROMPT_V3", forged)

    with pytest.raises(V3PromptBindingError, match="protocol_id"):
        _module._verified_v3_prompt_text()


# ---------------------------------------------------------------------------
# run_v3_pass: happy path, v3 fixture-identity binding, P2-T1 ordering, cleanup, no leakage
# ---------------------------------------------------------------------------


def test_run_v3_pass_dispatches_verified_v3_text_exactly_eight_times(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    factory, collector = _all_success_scripted()

    report = run_v3_pass(
        factory,
        collector,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.calls == 1
    assert factory.built_adapter is not None
    assert factory.built_adapter.calls == 8
    assert factory.received_prompt == c1_prompt_text_v3()
    assert report.run_label == "V3_PASS_1"
    assert report.prompt_protocol_id == c1_prompt_protocol_id_v3()
    assert report.prompt_sha256 == c1_prompt_sha256_v3()
    assert report.fixture_manifest_version == "vision-v3-map-manifest-v1"
    assert report.mapping.attempted_runs == 8
    assert report.mapping.schema_valid_count == 8
    assert not (tmp_path / "scratch").exists()


def test_persistent_fixture_images_are_never_modified_by_a_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    before_hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted((images_root / "images").glob("*.png"))
    }
    factory, collector = _all_success_scripted()

    run_v3_pass(
        factory,
        collector,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    after_hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted((images_root / "images").glob("*.png"))
    }
    assert after_hashes == before_hashes
    assert len(after_hashes) == 8


def test_v3_pass_report_exposes_v3_fixture_ids_never_b3_fixture_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    verified = load_and_verify_v3_fixtures(manifest_path=manifest_path, images_root=images_root)
    expected_hash_by_id = {fixture.fixture_id: fixture.sha256 for fixture in verified}
    factory, collector = _all_success_scripted()

    report = run_v3_pass(
        factory,
        collector,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert len(report.runs) == 8
    assert [run.fixture_id for run in report.runs] == list(_V3_FIXTURE_IDS)
    for run in report.runs:
        assert run.fixture_id.startswith("v3-map-fixture-")
        assert not run.fixture_id.startswith("b3-fixture")
        assert run.fixture_sha256 == expected_hash_by_id[run.fixture_id]
        assert run.status == "SUCCEEDED"

    serialized = json.dumps(
        {
            "run_label": report.run_label,
            "prompt_protocol_id": report.prompt_protocol_id,
            "prompt_sha256": report.prompt_sha256,
            "fixture_manifest_version": report.fixture_manifest_version,
            "mapping": dataclasses.asdict(report.mapping),
            "runs": [dataclasses.asdict(run) for run in report.runs],
        },
        default=str,
    )
    assert "b3-fixture" not in serialized
    assert str(images_root) not in serialized


def test_v3_pass_report_never_carries_prompt_body_or_raw_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    marker = "UNMISTAKABLE_V3_RAW_MARKER"
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [json.dumps({"note_marker": marker}) for _ in range(8)]
    factory = _RecordingAdapterFactory(outcomes, raw_outputs)

    report = run_v3_pass(
        factory,
        collector,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    serialized = json.dumps(
        {
            "run_label": report.run_label,
            "prompt_protocol_id": report.prompt_protocol_id,
            "prompt_sha256": report.prompt_sha256,
            "mapping": dataclasses.asdict(report.mapping),
            "runs": [dataclasses.asdict(run) for run in report.runs],
        },
        default=str,
    )
    assert marker not in serialized
    assert c1_prompt_text_v3() not in serialized


def test_default_empty_and_v1_v2_prompt_never_reach_the_real_adapter_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Integration proof, through the real ``qwen_v3_adapter_factory`` + ``QwenVisionAdapter``,
    that a v3 run never lets the adapter's empty default, or v1/v2 text, reach generation."""

    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    runner = _RecordingGenerationRunner([json.dumps(_EMPTY_OBSERVATIONS) for _ in range(8)])
    factory = qwen_v3_adapter_factory(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        generation_runner=runner,
    )
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)

    report = run_v3_pass(
        factory,
        collector,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert runner.calls == 8
    assert runner.received_prompts == [c1_prompt_text_v3()] * 8
    assert "" not in runner.received_prompts
    assert c1_prompt_text() not in runner.received_prompts
    assert c1_prompt_text_v2() not in runner.received_prompts
    assert report.mapping.schema_valid_count == 8
    assert not (tmp_path / "scratch").exists()


def test_pass_and_repeat_use_distinct_default_scratch_dirs_and_both_clean_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    factory_1, collector_1 = _all_success_scripted()
    factory_2, collector_2 = _all_success_scripted()

    pass_1 = run_v3_pass(
        factory_1,
        collector_1,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        sample_vram=False,
    )
    repeat_1 = run_v3_pass(
        factory_2,
        collector_2,
        run_label="V3_REPEAT_1",
        manifest_path=manifest_path,
        images_root=images_root,
        sample_vram=False,
    )

    assert pass_1.run_label != repeat_1.run_label
    assert pass_1.mapping.attempted_runs == 8
    assert repeat_1.mapping.attempted_runs == 8
    assert not (tmp_path / "data" / "runtime" / "vision-v3-pass-1").exists()
    assert not (tmp_path / "data" / "runtime" / "vision-v3-repeat-1").exists()


def test_scratch_cleans_up_even_when_the_adapter_raises_mid_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)

    def factory(prompt: str, on_raw_output: Any) -> _RaisingAfterNAdapter:
        return _RaisingAfterNAdapter(on_raw_output, raise_at_call=3)

    with pytest.raises(RuntimeError, match="simulated mid-pass adapter failure"):
        run_v3_pass(
            factory,
            collector,
            run_label="V3_PASS_1",
            manifest_path=manifest_path,
            images_root=images_root,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert not (tmp_path / "scratch").exists()


def test_scratch_and_collector_clean_up_when_adapter_factory_itself_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: a real P2-T1 pass on all eight copies must not be enough on its own -- if
    ``adapter_factory`` itself raises (before ``run_b3_mapping_study`` is ever reached, so its own
    ``finally`` cleanup never runs), the scratch directory must still be removed, the original
    exception must propagate unchanged, and the persistent fixture images must stay untouched.
    """

    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    before_hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted((images_root / "images").glob("*.png"))
    }
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    calls = 0

    def factory(prompt: str, on_raw_output: Any) -> Any:
        nonlocal calls
        calls += 1
        raise RuntimeError("simulated adapter_factory construction failure")

    with pytest.raises(RuntimeError, match="simulated adapter_factory construction failure"):
        run_v3_pass(
            factory,
            collector,
            run_label="V3_PASS_1",
            manifest_path=manifest_path,
            images_root=images_root,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert calls == 1
    assert not (tmp_path / "scratch").exists()
    after_hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted((images_root / "images").glob("*.png"))
    }
    assert after_hashes == before_hashes


def test_scratch_cleans_up_when_the_fixture_copy_step_itself_raises_partway(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: a failure inside the scratch-copy step itself (``mkdir``/``copy2``), after the
    directory already exists and at least one fixture was already copied into it, must still be
    cleaned up -- not just failures that happen after copying has already completed (P2-T1
    pre-check or ``adapter_factory``). ``adapter_factory`` must never be reached in this case.
    """

    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    before_hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted((images_root / "images").glob("*.png"))
    }
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    factory_calls = 0

    def factory(prompt: str, on_raw_output: Any) -> Any:
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("adapter_factory must never be called after a copy failure")

    def _failing_copy(
        verified_fixtures: tuple[Any, ...], fixtures_dir: Path
    ) -> tuple[tuple[Path, ...], Path]:
        # Real partial progress: the directory is created and exactly one of the eight fixtures
        # is actually copied -- proving a *partial* scratch state (dir exists, one file present)
        # is exactly what the cleanup boundary must remove -- then the copy fails before the
        # remaining seven images and the companion audio are written.
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        first = verified_fixtures[0]
        (fixtures_dir / first.image_path.name).write_bytes(first.image_path.read_bytes())
        raise RuntimeError("simulated scratch copy failure")

    monkeypatch.setattr(_module, "_copy_v3_fixtures_into_scratch", _failing_copy)

    with pytest.raises(RuntimeError, match="simulated scratch copy failure"):
        run_v3_pass(
            factory,
            collector,
            run_label="V3_PASS_1",
            manifest_path=manifest_path,
            images_root=images_root,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory_calls == 0
    assert not (tmp_path / "scratch").exists()
    after_hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted((images_root / "images").glob("*.png"))
    }
    assert after_hashes == before_hashes


def test_run_v3_pass_fails_closed_before_adapter_factory_on_manifest_integrity_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(
        tmp_path, status="AWAITING_OWNER_IMAGE_REVIEW"
    )
    factory, collector = _all_success_scripted()

    with pytest.raises(V3ManifestIntegrityError, match="review status"):
        run_v3_pass(
            factory,
            collector,
            run_label="V3_PASS_1",
            manifest_path=manifest_path,
            images_root=images_root,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0
    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "data").exists()


def test_real_p2t1_preflight_failure_yields_zero_factory_calls_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A copied fixture that fails a *real* P2-T1 check must block before any adapter action,
    even though it already passed every static manifest/hash/dimension check."""

    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    corrupted_id = _corrupt_one_fixture_to_fail_real_p2t1(images_root, manifest_path)
    factory, collector = _all_success_scripted()

    with pytest.raises(NoRealV3P2T1PassAvailableError, match=corrupted_id):
        run_v3_pass(
            factory,
            collector,
            run_label="V3_PASS_1",
            manifest_path=manifest_path,
            images_root=images_root,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0
    assert factory.built_adapter is None
    assert not (tmp_path / "scratch").exists()


def test_run_v3_pass_uses_the_injected_clock_for_started_and_completed_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest_path, images_root = _author_and_write_manifest(tmp_path)
    factory, collector = _all_success_scripted()
    timestamps = iter(
        [datetime(2026, 9, 8, 10, 0, tzinfo=UTC), datetime(2026, 9, 8, 10, 4, tzinfo=UTC)]
    )

    report = run_v3_pass(
        factory,
        collector,
        run_label="V3_PASS_1",
        manifest_path=manifest_path,
        images_root=images_root,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
        clock=lambda: next(timestamps),
    )

    assert report.started_at == datetime(2026, 9, 8, 10, 0, tzinfo=UTC)
    assert report.completed_at == datetime(2026, 9, 8, 10, 4, tzinfo=UTC)


def test_v3_text_reaches_the_real_qwen_adapter_at_the_smallest_seam(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No-GPU proof at the smallest real seam: the production factory + adapter never lets the
    empty default, or v1/v2 text, reach generation -- independent of the run_v3_pass wrapper."""

    monkeypatch.chdir(tmp_path)
    image_path = tmp_path / "drawing.bin"
    image_bytes = b"synthetic-v3-seam-image"
    image_path.write_bytes(image_bytes)
    runner = _RecordingGenerationRunner([json.dumps(_EMPTY_OBSERVATIONS)])
    factory = qwen_v3_adapter_factory(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        generation_runner=runner,
    )

    adapter = factory(c1_prompt_text_v3(), lambda _raw: None)
    result = adapter.understand(
        VisionUnderstandingRequestV2(
            correlation_id="v3-seam-check",
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=image_path.name, sha256=sha256(image_bytes).hexdigest()
            ),
            media_validation=VisionMediaValidationProvenanceV1(
                validation_artifact_ref="fixture:vision:v3:validation-pass",
                validation_artifact_sha256="c" * 64,
                decision="PASS",
                validator_policy_version="media-quality-policy-v1",
            ),
            requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        )
    )

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert runner.calls == 1
    assert runner.received_prompts == [c1_prompt_text_v3()]
    assert c1_prompt_text() not in runner.received_prompts
    assert c1_prompt_text_v2() not in runner.received_prompts
    assert "" not in runner.received_prompts


# ---------------------------------------------------------------------------
# evaluate_v3_readiness: gate, manifest identity, comparability window, non-pooling
# ---------------------------------------------------------------------------


def _run_result(
    fixture_id: str,
    status: str,
    *,
    error_code: str | None = None,
    error_detail: str | None = None,
) -> V3FixtureRunResult:
    return V3FixtureRunResult(
        fixture_id=fixture_id,
        fixture_sha256="a" * 64,
        status=status,
        error_code=error_code,
        error_detail=error_detail,
        attempt_number=1,
        repair_attempted=False,
        wall_latency_ms=10.0,
        peak_vram_mb=None,
        vram_not_measured_reason="VRAM sampling was disabled for this call",
        fenced=False,
        truncated=False,
        extra_key=False,
        invalid_enum=False,
    )


def _succeeded_and_failed_runs(succeeded: int, total: int = 8) -> tuple[V3FixtureRunResult, ...]:
    good = tuple(
        _run_result(_V3_FIXTURE_IDS[index], "SUCCEEDED") for index in range(succeeded)
    )
    bad = tuple(
        _run_result(
            _V3_FIXTURE_IDS[index],
            "FAILED",
            error_code=VisionErrorCode.VISION_SCHEMA_INVALID.value,
            error_detail="OUTPUT_MAPPING_FAILED",
        )
        for index in range(succeeded, total)
    )
    return good + bad


def _mapping_summary(
    runs: tuple[V3FixtureRunResult, ...],
    *,
    truncated_count: int = 0,
    profile_id: str = _EXPECTED_PROFILE_ID,
    profile_catalog_hash: str = _EXPECTED_CATALOG_HASH,
    attempted_runs: int | None = None,
) -> V3MappingSummary:
    return V3MappingSummary(
        profile_id=profile_id,
        profile_catalog_hash=profile_catalog_hash,
        raw_output_mode="CLASSIFY_ONLY",
        attempted_runs=attempted_runs if attempted_runs is not None else len(runs),
        schema_valid_count=sum(1 for run in runs if run.status == "SUCCEEDED"),
        typed_failure_counts={},
        lossless_unwrap_recovered_count=0,
        fenced_count=0,
        truncated_count=truncated_count,
        extra_key_count=0,
        invalid_enum_count=0,
    )


_BASE_TIME = datetime(2026, 9, 8, 9, 0, tzinfo=UTC)


def _pass_report(
    run_label: V3RunLabel,
    runs: tuple[V3FixtureRunResult, ...],
    *,
    truncated_count: int = 0,
    prompt_sha256: str | None = None,
    prompt_protocol_id: str | None = None,
    fixture_manifest_version: str = "vision-v3-map-manifest-v1",
    profile_id: str = _EXPECTED_PROFILE_ID,
    profile_catalog_hash: str = _EXPECTED_CATALOG_HASH,
    attempted_runs: int | None = None,
    started_at: datetime = _BASE_TIME,
    completed_at: datetime | None = None,
) -> V3PassReport:
    return V3PassReport(
        run_label=run_label,
        prompt_protocol_id=prompt_protocol_id or c1_prompt_protocol_id_v3(),
        prompt_sha256=prompt_sha256 or c1_prompt_sha256_v3(),
        fixture_manifest_version=fixture_manifest_version,
        started_at=started_at,
        completed_at=completed_at or (started_at + timedelta(minutes=5)),
        mapping=_mapping_summary(
            runs,
            truncated_count=truncated_count,
            profile_id=profile_id,
            profile_catalog_hash=profile_catalog_hash,
            attempted_runs=attempted_runs,
        ),
        runs=runs,
    )


def test_seven_of_eight_in_both_passes_with_comparable_timing_is_ready() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(7))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(7),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_READY"
    assert verdict.blocking_reasons == ()
    assert verdict.pass_1.mapping_valid_count == 7
    assert verdict.repeat_1.mapping_valid_count == 7


def test_six_of_eight_mapping_valid_is_not_ready() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(6))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(7),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert V3BlockingReason.MAPPING_VALID_BELOW_THRESHOLD in verdict.blocking_reasons


def test_repeat_is_never_pooled_with_pass_and_is_independently_evaluated() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(6),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert verdict.pass_1.mapping_valid_ok is True
    assert verdict.repeat_1.mapping_valid_ok is False


def test_systemic_truncation_at_two_of_eight_blocks_readiness() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8), truncated_count=2)
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert (
        V3BlockingReason.SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS
        in verdict.blocking_reasons
    )


def test_one_of_eight_truncation_is_not_systemic() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8), truncated_count=1)
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_READY"


def test_config_drift_between_passes_is_non_comparable() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        prompt_sha256="0" * 64,
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons
    assert V3BlockingReason.MAPPING_VALID_BELOW_THRESHOLD not in verdict.blocking_reasons


def test_unexpected_profile_catalog_hash_is_non_comparable() -> None:
    pass_1 = _pass_report(
        "V3_PASS_1", _succeeded_and_failed_runs(8), profile_catalog_hash="0" * 64
    )
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons


def test_input_integrity_failure_blocks_within_a_comparable_pair() -> None:
    runs = _succeeded_and_failed_runs(7, total=7) + (
        _run_result(
            _V3_FIXTURE_IDS[7],
            "FAILED",
            error_code=VisionErrorCode.INPUT_NOT_VALIDATED.value,
            error_detail="SOURCE_IMAGE_HASH_MISMATCH",
        ),
    )
    pass_1 = _pass_report("V3_PASS_1", runs)
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert V3BlockingReason.INPUT_INTEGRITY_FAILURE in verdict.blocking_reasons


def test_runtime_or_device_failure_blocks_within_a_comparable_pair() -> None:
    runs = _succeeded_and_failed_runs(7, total=7) + (
        _run_result(
            _V3_FIXTURE_IDS[7],
            "FAILED",
            error_code=VisionErrorCode.VISION_TIMEOUT.value,
            error_detail="TIMEOUT_BUDGET_EXCEEDED",
        ),
    )
    pass_1 = _pass_report("V3_PASS_1", runs)
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert V3BlockingReason.RUNTIME_OR_DEVICE_FAILURE in verdict.blocking_reasons


def test_incomplete_run_set_blocks_readiness_via_its_own_reason() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(7, total=7))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert V3BlockingReason.INCOMPLETE_RUN_SET in verdict.blocking_reasons
    assert V3BlockingReason.MAPPING_VALID_BELOW_THRESHOLD not in verdict.blocking_reasons


def test_repeat_starting_exactly_fifteen_minutes_after_pass_completion_is_comparable() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(7))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(7),
        started_at=pass_1.completed_at + timedelta(minutes=15),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_READY"
    assert verdict.repeat_gap == timedelta(minutes=15)


def test_repeat_starting_fifteen_minutes_and_one_second_after_pass_is_non_comparable() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=15, seconds=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.REPEAT_WINDOW_EXCEEDED in verdict.blocking_reasons


def test_negative_repeat_gap_is_non_comparable() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at - timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.REPEAT_WINDOW_EXCEEDED in verdict.blocking_reasons


def test_declared_session_reset_is_non_comparable_even_with_perfect_runs_and_timing() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=False)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.SESSION_RESET_DECLARED in verdict.blocking_reasons
    assert verdict.same_lightning_session is False


def test_matching_run_labels_are_rejected() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    duplicate = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))

    with pytest.raises(ValueError, match="distinct run labels"):
        evaluate_v3_readiness(pass_1, duplicate, same_lightning_session=True)


def test_swapped_pass_and_repeat_labels_are_rejected() -> None:
    mislabelled_pass = _pass_report("V3_REPEAT_1", _succeeded_and_failed_runs(8))
    mislabelled_repeat = _pass_report(
        "V3_PASS_1",
        _succeeded_and_failed_runs(8),
        started_at=mislabelled_pass.completed_at + timedelta(minutes=1),
    )

    with pytest.raises(ValueError, match="V3_PASS_1"):
        evaluate_v3_readiness(mislabelled_pass, mislabelled_repeat, same_lightning_session=True)


# ---------------------------------------------------------------------------
# evaluate_v3_readiness: fixture-manifest-version identity (forged/wrong/differing versions
# must never reach MAPPING_READY)
# ---------------------------------------------------------------------------


def test_pass_with_wrong_manifest_version_is_non_comparable() -> None:
    pass_1 = _pass_report(
        "V3_PASS_1",
        _succeeded_and_failed_runs(8),
        fixture_manifest_version="vision-v3-map-manifest-v2",
    )
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.FIXTURE_MANIFEST_MISMATCH in verdict.blocking_reasons
    assert V3BlockingReason.MAPPING_VALID_BELOW_THRESHOLD not in verdict.blocking_reasons


def test_repeat_with_wrong_manifest_version_is_non_comparable() -> None:
    pass_1 = _pass_report("V3_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        fixture_manifest_version="forged-manifest-v1",
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.FIXTURE_MANIFEST_MISMATCH in verdict.blocking_reasons


def test_both_passes_sharing_the_same_wrong_manifest_version_is_still_non_comparable() -> None:
    """Agreement between the two passes is not enough -- the version must equal the one true
    approved manifest identity, or a forged pair that merely agrees with *each other* could
    otherwise reach MAPPING_READY."""

    pass_1 = _pass_report(
        "V3_PASS_1",
        _succeeded_and_failed_runs(8),
        fixture_manifest_version="vision-v3-map-manifest-v0-draft",
    )
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        fixture_manifest_version="vision-v3-map-manifest-v0-draft",
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.FIXTURE_MANIFEST_MISMATCH in verdict.blocking_reasons


def test_differing_manifest_versions_between_passes_is_non_comparable() -> None:
    pass_1 = _pass_report(
        "V3_PASS_1",
        _succeeded_and_failed_runs(8),
        fixture_manifest_version="vision-v3-map-manifest-v1",
    )
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(8),
        fixture_manifest_version="vision-v3-map-manifest-v1-modified",
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "NON_COMPARABLE"
    assert V3BlockingReason.FIXTURE_MANIFEST_MISMATCH in verdict.blocking_reasons


def test_matching_correct_manifest_version_still_reaches_mapping_ready() -> None:
    """Confirms the manifest-identity gate has a genuine ready path, not just a blocking path."""

    pass_1 = _pass_report(
        "V3_PASS_1",
        _succeeded_and_failed_runs(7),
        fixture_manifest_version="vision-v3-map-manifest-v1",
    )
    repeat_1 = _pass_report(
        "V3_REPEAT_1",
        _succeeded_and_failed_runs(7),
        fixture_manifest_version="vision-v3-map-manifest-v1",
        started_at=pass_1.completed_at + timedelta(minutes=1),
    )

    verdict = evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)

    assert verdict.overall == "MAPPING_READY"
    assert verdict.blocking_reasons == ()
