"""Focused, no-GPU tests for the Phase 3 prompt-v3 mapping-validation fixture authoring module.

Mirrors ``test_vision_b3_mapping_study.py``'s scratch-safety test pattern
(``monkeypatch.chdir(tmp_path)`` plus relative subdirectory names) so every test stays inside a
guarded, disposable temporary directory. No adapter, model, provider, or GPU object is constructed
anywhere in this file.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from struct import unpack

import pytest

from sketch2life.benchmark import vision_v3_mapping_fixtures as _module
from sketch2life.benchmark.vision_b3_mapping_study import _default_fixture_builder
from sketch2life.benchmark.vision_v3_mapping_fixtures import (
    TAXONOMY,
    UnsafeFixturePathError,
    V3MapAuthoringResult,
    author_v3_map_fixture_package,
    build_manifest,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_B4_MANIFEST_PATH = (
    _REPO_ROOT
    / "features/FEAT-003-multimodal-understanding/fixtures/vision-b4/manifest-v1.json"
)


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def test_taxonomy_has_exactly_eight_unique_ordered_ids() -> None:
    assert len(TAXONOMY) == 8
    ids = [spec.fixture_id for spec in TAXONOMY]
    assert ids == [f"v3-map-fixture-{index:02d}" for index in range(1, 9)]
    assert len(set(ids)) == 8


def test_authors_exactly_eight_unique_files_inside_guarded_images_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    assert len(result.fixtures) == 8
    assert len({fixture.fixture_id for fixture in result.fixtures}) == 8
    assert sorted(path.name for path in (tmp_path / "images").iterdir()) == [
        f"v3-map-fixture-{index:02d}.png" for index in range(1, 9)
    ]
    images_root = (tmp_path / "images").resolve()
    for fixture in result.fixtures:
        written_path = tmp_path / "images" / f"{fixture.fixture_id}.png"
        assert written_path.is_file()
        assert images_root in written_path.resolve().parents


def test_every_authored_png_declares_the_fixed_192_square_canvas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    for image_path in (tmp_path / "images").glob("*.png"):
        payload = image_path.read_bytes()
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")
        assert unpack(">II", payload[16:24]) == (192, 192)


def test_two_clean_regenerations_produce_identical_per_fixture_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    first = author_v3_map_fixture_package(
        images_dir=Path("images-a"), scratch_audio_dir=Path("scratch-audio-a")
    )
    second = author_v3_map_fixture_package(
        images_dir=Path("images-b"), scratch_audio_dir=Path("scratch-audio-b")
    )
    first_hashes = {f.fixture_id: f.image_sha256 for f in first.fixtures}
    second_hashes = {f.fixture_id: f.image_sha256 for f in second.fixtures}
    assert first_hashes == second_hashes
    assert len(set(first_hashes.values())) == 8


def test_zero_hash_overlap_with_b3_regenerated_in_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    v3_result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    v3_hashes = {fixture.image_sha256 for fixture in v3_result.fixtures}

    b3_image_paths, _b3_audio_path = _default_fixture_builder(Path("b3-scratch"))
    b3_hashes = {_sha256_of(path) for path in b3_image_paths}

    assert v3_hashes.isdisjoint(b3_hashes)
    assert len(v3_hashes) == 8
    assert len(b3_hashes) == 8


def test_zero_hash_overlap_with_committed_b4_manifest_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    b4_manifest = json.loads(_B4_MANIFEST_PATH.read_text(encoding="utf-8"))
    b4_hashes = {fixture["image_sha256"] for fixture in b4_manifest["fixtures"]}
    assert len(b4_hashes) == 8

    monkeypatch.chdir(tmp_path)
    v3_result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    v3_hashes = {fixture.image_sha256 for fixture in v3_result.fixtures}

    assert v3_hashes.isdisjoint(b4_hashes)


def test_all_eight_images_earn_a_real_p2t1_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    assert result.all_p2t1_pass is True
    assert all(fixture.p2t1_pass for fixture in result.fixtures)


def test_companion_audio_is_scratch_only_and_deleted_after_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    assert result.scratch_audio_deleted is True
    assert not (tmp_path / "scratch-audio").exists()


def test_scratch_audio_is_deleted_even_when_authoring_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    original_writer = _module._write_v3_fixture_image

    def _raising_writer(path: Path, index: int) -> None:
        if index == 3:
            raise RuntimeError("simulated mid-authoring failure")
        original_writer(path, index)

    monkeypatch.setattr(_module, "_write_v3_fixture_image", _raising_writer)

    with pytest.raises(RuntimeError, match="simulated mid-authoring failure"):
        author_v3_map_fixture_package(
            images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
        )

    assert not (tmp_path / "scratch-audio").exists()


def test_default_paths_work_only_from_the_verified_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    monkeypatch.setattr(_module, "_REPOSITORY_ROOT", repository_root.resolve())
    monkeypatch.chdir(repository_root)

    result = author_v3_map_fixture_package()

    assert len(result.fixtures) == 8
    assert result.all_p2t1_pass is True
    assert sorted(
        path.name
        for path in (
            repository_root
            / "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-map/images"
        ).iterdir()
    ) == [f"v3-map-fixture-{index:02d}.png" for index in range(1, 9)]


def test_default_paths_fail_closed_from_backend_without_creating_backend_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_root = tmp_path / "repo"
    backend_root = repository_root / "backend"
    backend_root.mkdir(parents=True)
    monkeypatch.setattr(_module, "_REPOSITORY_ROOT", repository_root.resolve())
    monkeypatch.chdir(backend_root)

    with pytest.raises(UnsafeFixturePathError, match="repository root"):
        author_v3_map_fixture_package()

    assert not (backend_root / "features").exists()
    assert not (backend_root / "data/runtime/vision-v3-map-authoring-audio").exists()


def test_images_dir_rejects_an_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(UnsafeFixturePathError, match="images_dir"):
        author_v3_map_fixture_package(
            images_dir=tmp_path / "images", scratch_audio_dir=Path("scratch-audio")
        )


def test_images_dir_rejects_escaping_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    with pytest.raises(UnsafeFixturePathError, match="images_dir"):
        author_v3_map_fixture_package(
            images_dir=Path("../escaped-images"), scratch_audio_dir=Path("scratch-audio")
        )


def test_scratch_audio_dir_rejects_an_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(UnsafeFixturePathError, match="scratch_audio_dir"):
        author_v3_map_fixture_package(
            images_dir=Path("images"), scratch_audio_dir=tmp_path / "scratch-audio"
        )


def test_scratch_audio_dir_rejects_escaping_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    with pytest.raises(UnsafeFixturePathError, match="scratch_audio_dir"):
        author_v3_map_fixture_package(
            images_dir=Path("images"), scratch_audio_dir=Path("../escaped-scratch-audio")
        )


@pytest.mark.parametrize(
    "unsafe_path",
    (
        Path("C:/fixture-images"),
        Path("D:\\fixture-images"),
        Path("\\fixture-images"),
        Path("\\\\server\\share\\fixture-images"),
    ),
)
def test_images_dir_rejects_machine_absolute_paths_host_independently(
    unsafe_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(UnsafeFixturePathError, match="images_dir"):
        author_v3_map_fixture_package(
            images_dir=unsafe_path, scratch_audio_dir=Path("scratch-audio")
        )


def test_no_model_adapter_provider_or_gpu_path_is_reachable() -> None:
    source_text = Path(_module.__file__).read_text(encoding="utf-8")
    forbidden_substrings = (
        "QwenVisionAdapter",
        "VisionUnderstandingPortV2",
        "VisionUnderstandingRequestV2",
        "requested_profile_id",
        "adapter.understand",
        "Lightning",
        "nvidia-smi",
        "import torch",
        "import transformers",
    )
    for forbidden in forbidden_substrings:
        assert forbidden not in source_text, f"forbidden reference found: {forbidden}"


def test_manifest_has_relative_refs_matching_hashes_and_no_forbidden_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result: V3MapAuthoringResult = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    manifest = build_manifest(
        result,
        recipe_module_sha256="f" * 64,
        b3_disjointness_verified=True,
        b4_disjointness_verified=True,
    )

    assert manifest["status"] == "AWAITING_OWNER_IMAGE_REVIEW"
    assert manifest["has_ground_truth"] is False
    assert manifest["data_policy"] == "synthetic-only"
    local_validation = manifest["local_authoring_validation"]
    assert isinstance(local_validation, dict)
    assert local_validation["model_or_gpu_called"] is False
    assert local_validation["p2t1_result"] == "PASS_FOR_ALL_8_FIXTURES"
    assert set(manifest) == {
        "contract_name",
        "contract_version",
        "manifest_version",
        "status",
        "purpose",
        "has_ground_truth",
        "data_policy",
        "author",
        "authoring_boundary",
        "prompt_protocol",
        "image_generation",
        "disjointness",
        "local_authoring_validation",
        "fixtures",
    }

    manifest_fixtures = manifest["fixtures"]
    assert isinstance(manifest_fixtures, list)
    assert len(manifest_fixtures) == 8
    for entry in manifest_fixtures:
        assert set(entry) == {
            "fixture_id",
            "image_ref",
            "image_sha256",
            "dimensions",
            "taxonomy_token",
            "p2t1_pass",
        }
        image_ref = entry["image_ref"]
        assert image_ref.startswith("images/")
        assert not Path(image_ref).is_absolute()
        assert ":" not in image_ref
        written_path = tmp_path / "images" / Path(image_ref).name
        assert entry["image_sha256"] == _sha256_of(written_path)

    serialized = json.dumps(manifest)
    assert str(tmp_path) not in serialized
    assert "raw_output" not in serialized
    assert "predicted_text" not in serialized
    assert '"ground_truth":' not in serialized
    assert "prompt_text" not in serialized


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("incomplete", "exact ordered eight-fixture taxonomy"),
        ("p2t1", "all fixtures need P2-T1 PASS"),
        ("cleanup", "confirmed cleanup"),
        ("disjointness", "hash disjointness"),
        ("recipe_hash", "recipe_module_sha256"),
        ("metadata", "fixture metadata"),
    ),
)
def test_manifest_fails_closed_until_every_authoring_gate_passes(
    mutation: str, message: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = author_v3_map_fixture_package(
        images_dir=Path("images"), scratch_audio_dir=Path("scratch-audio")
    )
    recipe_hash = "f" * 64
    b3_verified = True
    if mutation == "incomplete":
        result = replace(result, fixtures=result.fixtures[:-1])
    elif mutation == "p2t1":
        changed = replace(result.fixtures[0], p2t1_pass=False)
        result = replace(result, fixtures=(changed, *result.fixtures[1:]), all_p2t1_pass=False)
    elif mutation == "cleanup":
        result = replace(result, scratch_audio_deleted=False)
    elif mutation == "disjointness":
        b3_verified = False
    elif mutation == "recipe_hash":
        recipe_hash = "not-a-hash"
    elif mutation == "metadata":
        changed = replace(result.fixtures[0], image_ref="images/wrong.png")
        result = replace(result, fixtures=(changed, *result.fixtures[1:]))

    with pytest.raises(_module.V3MapManifestIntegrityError, match=message):
        build_manifest(
            result,
            recipe_module_sha256=recipe_hash,
            b3_disjointness_verified=b3_verified,
            b4_disjointness_verified=True,
        )


def test_git_check_ignore_passes_for_all_eight_default_image_paths() -> None:
    for spec in TAXONOMY:
        relative_path = (
            "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-map/images/"
            f"{spec.fixture_id}.png"
        )
        completed = subprocess.run(
            ["git", "check-ignore", "-q", relative_path],
            cwd=_REPO_ROOT,
            check=False,
        )
        assert completed.returncode == 0, f"{relative_path} is not covered by .gitignore"
