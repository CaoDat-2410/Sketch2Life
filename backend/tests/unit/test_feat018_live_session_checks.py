from __future__ import annotations

import os
import stat
import sys
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from sketch2life.benchmark.feat018_live_session_checks import (
    InterpreterFacts,
    RuntimeManifestFacts,
    current_interpreter_facts,
    installed_distributions,
    observe_runtime_inventory,
    observe_session_readiness,
)
from sketch2life.contracts.schemas.feat018_live_wiring import (
    LiveObservationInputError,
    LiveRuntimeInventoryObservationV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_environment_readiness import (
    QwenVisionHardwareFacts,
    QwenVisionRevisionState,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

_PROFILE_ID = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1
_PINNED_VERSIONS = {
    pin.package: pin.version
    for pin in vision_profile_catalog_v2().resolve(_PROFILE_ID).model_provenance.dependency_pins
}
_REQUIRED_FILES = (
    "chat_template.json",
    "config.json",
    "generation_config.json",
    "merges.txt",
    "preprocessor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "video_preprocessor_config.json",
    "vocab.json",
)
_SHARD = "model-00001-of-00001.safetensors"
_MODULES = (
    "backend/src/sketch2life/alpha.py",
    "backend/src/sketch2life/beta/gamma.py",
)
_INTERPRETER = InterpreterFacts(
    implementation="CPython",
    full_version="3.12.10",
    build_identity="sha256:" + "c" * 64,
    abi_identity="cpython-312",
)
_DISTRIBUTIONS = (
    ("Transformers", "4.57.6"),
    ("torch", "2.8.0+cu128"),
    ("qwen_vl_utils", "0.0.14"),
    ("accelerate", "1.10.1"),
    ("pydantic", "2.11.7"),
)


def _snapshot(model_dir: Path) -> None:
    model_dir.mkdir()
    for name in _REQUIRED_FILES:
        (model_dir / name).write_text("{}", encoding="utf-8")
    (model_dir / _SHARD).write_bytes(b"synthetic")
    (model_dir / "model.safetensors.index.json").write_text(
        f'{{"weight_map":{{"weight":"{_SHARD}"}}}}', encoding="utf-8"
    )


def _l4(_index: int) -> QwenVisionHardwareFacts:
    return QwenVisionHardwareFacts(
        cuda_available=True, device_count=1, device_name="NVIDIA L4", bf16_supported=True
    )


def _verified(_model_dir: Path, _revision: str) -> QwenVisionRevisionState:
    return QwenVisionRevisionState.VERIFIED


def _runtime(tmp_path: Path, **overrides: object) -> QwenVisionRuntimeConfig:
    model_dir = tmp_path / "model"
    if not model_dir.exists():
        _snapshot(model_dir)
    values: dict[str, object] = {
        "model_dir": model_dir,
        "device": "cuda",
        "device_index": 0,
        "allow_model_download": False,
    }
    values.update(overrides)
    return QwenVisionRuntimeConfig(**values)  # type: ignore[arg-type]


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    for relative in _MODULES:
        target = root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"# synthetic {relative}\n".encode())
    return root


def _manifest_facts(**overrides: object) -> RuntimeManifestFacts:
    values: dict[str, object] = {
        "hardware": _l4(0),
        "device_index": 0,
        "cuda_runtime_version": "12.8",
        "driver_version": "570.124.06",
        "vram_mib": 23034,
    }
    values.update(overrides)
    return RuntimeManifestFacts(**values)  # type: ignore[arg-type]


def _inventory(root: Path, **overrides: object) -> LiveRuntimeInventoryObservationV1:
    values: dict[str, object] = {
        "environment": "SESSION",
        "interpreter": _INTERPRETER,
        "distributions": _DISTRIBUTIONS,
        "repository_root": root,
        "module_paths": _MODULES,
        "max_module_bytes": 4096,
        "manifest_facts": None,
    }
    values.update(overrides)
    return observe_runtime_inventory(**values)  # type: ignore[arg-type]


def test_ready_session_is_accepted_without_model_load(tmp_path: Path) -> None:
    observation = observe_session_readiness(
        _runtime(tmp_path),
        _PROFILE_ID,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4,
        revision_verifier=_verified,
    )

    assert observation.accepted is True
    assert observation.readiness_status == "READY"
    assert observation.issue_codes == ()
    assert observation.model_load_performed is False
    assert observation.inference_performed is False
    assert observation.stopped_before == "STAGING"
    assert observation.d4_manifest_revalidation == "NOT_PERFORMED"
    assert observation.live_authorized is False
    assert str(tmp_path) not in observation.model_dump_json()


@pytest.mark.parametrize(
    ("probe", "revision", "expected_issue"),
    [
        (
            lambda _index: QwenVisionHardwareFacts(False, 0, None, False),
            _verified,
            "CUDA_NOT_AVAILABLE",
        ),
        (_l4, lambda _dir, _rev: QwenVisionRevisionState.MISMATCH, "MODEL_REVISION_MISMATCH"),
        (
            _l4,
            lambda _dir, _rev: QwenVisionRevisionState.NOT_VERIFIABLE,
            "MODEL_REVISION_NOT_VERIFIABLE",
        ),
        (
            lambda _index: QwenVisionHardwareFacts(True, 1, "NVIDIA A10G", True),
            _verified,
            "DEVICE_CLASS_MISMATCH",
        ),
    ],
)
def test_not_ready_sessions_report_closed_issues(
    tmp_path: Path, probe: object, revision: object, expected_issue: str
) -> None:
    observation = observe_session_readiness(
        _runtime(tmp_path),
        _PROFILE_ID,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=probe,  # type: ignore[arg-type]
        revision_verifier=revision,  # type: ignore[arg-type]
    )

    assert observation.accepted is False
    assert observation.readiness_status == "NOT_READY"
    assert expected_issue in observation.issue_codes
    assert observation.failure_codes == ("READINESS_NOT_READY",)


def test_dependency_and_download_issues_are_not_ready(tmp_path: Path) -> None:
    versions = {**_PINNED_VERSIONS, "torch": "0.0.1"}
    observation = observe_session_readiness(
        _runtime(tmp_path, allow_model_download=True),
        _PROFILE_ID,
        version_lookup=versions.get,
        hardware_probe=_l4,
        revision_verifier=_verified,
    )

    assert observation.accepted is False
    assert observation.dependencies_match is False
    assert "DEPENDENCY_VERSION_MISMATCH" in observation.issue_codes
    assert "MODEL_DOWNLOAD_MUST_BE_DISABLED" in observation.issue_codes


def test_probe_exceptions_fail_closed_without_text(tmp_path: Path) -> None:
    def broken(_index: int) -> QwenVisionHardwareFacts:
        raise RuntimeError("private-marker-text")

    observation = observe_session_readiness(
        _runtime(tmp_path),
        _PROFILE_ID,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=broken,
        revision_verifier=_verified,
    )

    assert observation.accepted is False
    assert observation.readiness_status == "NOT_RUN"
    assert observation.failure_codes == ("READINESS_EXCEPTION",)
    assert "private-marker-text" not in observation.model_dump_json()


@pytest.mark.parametrize(
    "arguments",
    [
        {"runtime_config": object()},
        {"profile_id": "QWEN3_VL_8B_INSTRUCT_BF16_V1"},
        {"version_lookup": None},
        {"hardware_probe": "probe"},
        {"revision_verifier": 3},
    ],
)
def test_readiness_structural_inputs_raise(tmp_path: Path, arguments: dict[str, object]) -> None:
    values: dict[str, object] = {
        "runtime_config": _runtime(tmp_path),
        "profile_id": _PROFILE_ID,
        "version_lookup": _PINNED_VERSIONS.get,
        "hardware_probe": _l4,
        "revision_verifier": _verified,
    }
    values.update(arguments)
    runtime_config = values.pop("runtime_config")
    profile_id = values.pop("profile_id")

    with pytest.raises(LiveObservationInputError):
        observe_session_readiness(runtime_config, profile_id, **values)  # type: ignore[arg-type]


def test_inventory_measures_bound_modules_and_normalizes_distributions(tmp_path: Path) -> None:
    root = _repository(tmp_path)

    observation = _inventory(root)

    assert observation.accepted is True
    assert observation.closure_basis == "BOUND_MODULE_LIST"
    assert observation.manifest is None
    assert [item.package for item in observation.distributions] == [
        "accelerate",
        "pydantic",
        "qwen-vl-utils",
        "torch",
        "transformers",
    ]
    for module in observation.internal_modules:
        expected = sha256(root.joinpath(*module.relative_path.split("/")).read_bytes())
        assert module.sha256 == expected.hexdigest()
    assert str(tmp_path) not in observation.model_dump_json()


def test_inventory_assembles_the_manifest_from_explicit_facts(tmp_path: Path) -> None:
    observation = _inventory(_repository(tmp_path), manifest_facts=_manifest_facts())

    assert observation.accepted is True
    manifest = observation.manifest
    assert manifest is not None
    assert manifest.python.version == "3.12.10"
    assert [item.package for item in manifest.dependencies] == [
        "accelerate",
        "qwen-vl-utils",
        "torch",
        "transformers",
    ]
    assert manifest.gpu.sku == "NVIDIA_L4"
    assert manifest.gpu.vram_mib == 23034


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"distributions": (*_DISTRIBUTIONS, ("pydantic", "2.0.0"))}, "DISTRIBUTION_DUPLICATE"),
        ({"distributions": (("bad name!", "1.0"),)}, "DISTRIBUTION_INVALID"),
        ({"distributions": (("ok", "bad version"),)}, "DISTRIBUTION_INVALID"),
        ({"distributions": (("ok", None),)}, "DISTRIBUTION_INVALID"),
        ({"distributions": ("not-a-pair",)}, "DISTRIBUTION_INVALID"),
        ({"distributions": ()}, "DISTRIBUTION_INVALID"),
        (
            {"distributions": tuple((f"package-{index}", "1.0") for index in range(513))},
            "DISTRIBUTION_LIMIT",
        ),
        (
            {"interpreter": InterpreterFacts("Jython", "3.12.10", "build", "abi")},
            "INTERPRETER_UNKNOWN",
        ),
        (
            {"interpreter": InterpreterFacts("CPython", "3.12.10", "has space", "abi")},
            "INTERPRETER_UNKNOWN",
        ),
        ({"max_module_bytes": 4}, "MODULE_TOO_LARGE"),
        (
            {"manifest_facts": _manifest_facts(cuda_runtime_version="twelve")},
            "MANIFEST_INVALID",
        ),
        ({"manifest_facts": _manifest_facts(vram_mib=-1)}, "MANIFEST_INVALID"),
        ({"manifest_facts": _manifest_facts(device_index=5)}, "MANIFEST_INVALID"),
        (
            {
                "manifest_facts": _manifest_facts(),
                "distributions": (("accelerate", "1.10.1"), ("torch", "2.8.0")),
            },
            "MANIFEST_INVALID",
        ),
    ],
)
def test_inventory_failures_carry_no_partial_facts(
    tmp_path: Path, overrides: dict[str, object], code: str
) -> None:
    observation = _inventory(_repository(tmp_path), **overrides)

    assert observation.accepted is False
    assert observation.failure_codes == (code,)
    assert observation.interpreter is None
    assert observation.distributions == ()
    assert observation.internal_modules == ()
    assert observation.manifest is None


def test_missing_module_is_unreadable(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    root.joinpath(*_MODULES[0].split("/")).unlink()

    observation = _inventory(root)

    assert observation.failure_codes == ("MODULE_UNREADABLE",)


def test_directory_in_place_of_module_is_unsafe(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    target = root.joinpath(*_MODULES[0].split("/"))
    target.unlink()
    target.mkdir()

    observation = _inventory(root)

    assert observation.failure_codes == ("MODULE_UNSAFE",)


def test_symlinked_module_is_unsafe(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("# outside\n", encoding="utf-8")
    target = root.joinpath(*_MODULES[0].split("/"))
    target.unlink()
    try:
        os.symlink(outside, target)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are unavailable to this test process")

    observation = _inventory(root)

    assert observation.failure_codes == ("MODULE_UNSAFE",)


@pytest.mark.parametrize(
    "fake_stat",
    [
        SimpleNamespace(st_mode=stat.S_IFREG | 0o644, st_file_attributes=0x400),
        SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_file_attributes=0),
    ],
)
def test_final_component_link_or_reparse_is_unsafe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_stat: SimpleNamespace
) -> None:
    # Exercises the module-level lstat branch on any platform, including Windows,
    # where creating a real file symlink needs privileges.
    root = _repository(tmp_path)
    target = root.joinpath(*_MODULES[0].split("/"))
    original_lstat = Path.lstat

    def fake_lstat(self: Path) -> object:
        if self == target:
            return fake_stat
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", fake_lstat)

    observation = _inventory(root)

    assert observation.failure_codes == ("MODULE_UNSAFE",)
    assert observation.internal_modules == ()


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (RuntimeError, "MODULE_UNSAFE"),
        (ValueError, "MODULE_UNREADABLE"),
        (OSError, "MODULE_UNREADABLE"),
    ],
)
def test_root_resolution_failures_map_to_closed_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[Exception], code: str
) -> None:
    root = _repository(tmp_path)
    original_resolve = Path.resolve

    def failing_resolve(self: Path, strict: bool = False) -> Path:
        if self == root:
            raise error(f"Symlink loop from 'private-marker-text {root}'")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", failing_resolve)

    observation = _inventory(root)

    assert observation.failure_codes == (code,)
    serialized = observation.model_dump_json()
    assert "private-marker-text" not in serialized
    assert str(tmp_path) not in serialized


@pytest.mark.parametrize(
    ("error", "code"),
    [(RuntimeError, "MODULE_UNSAFE"), (ValueError, "MODULE_UNREADABLE")],
)
def test_module_open_failures_map_to_closed_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[Exception], code: str
) -> None:
    root = _repository(tmp_path)
    target = root.joinpath(*_MODULES[1].split("/"))
    original_open = Path.open

    def failing_open(self: Path, *args: object, **kwargs: object) -> object:
        if self == target:
            raise error(f"private-marker-text {target}")
        return original_open(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "open", failing_open)

    observation = _inventory(root)

    assert observation.failure_codes == (code,)
    assert "private-marker-text" not in observation.model_dump_json()


def test_module_behind_an_ancestor_junction_is_unsafe(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("directory junctions are a Windows-only fixture")
    import _winapi

    root = _repository(tmp_path)
    linked_parent = root.joinpath("backend", "src", "sketch2life", "beta")
    outside = tmp_path / "outside-beta"
    outside.mkdir()
    (outside / "gamma.py").write_bytes((linked_parent / "gamma.py").read_bytes())
    (linked_parent / "gamma.py").unlink()
    linked_parent.rmdir()
    try:
        _winapi.CreateJunction(str(outside), str(linked_parent))
    except OSError:
        pytest.skip("directory junctions are unavailable to this test process")

    observation = _inventory(root)

    assert observation.failure_codes == ("MODULE_UNSAFE",)
    assert observation.internal_modules == ()


@pytest.mark.parametrize(
    "overrides",
    [
        {"environment": "CLOUD"},
        {"interpreter": object()},
        {"repository_root": Path("relative/root")},
        {"repository_root": "not-a-path"},
        {"repository_root": Path("C:/repository\x00private-marker-text")},
        {"module_paths": ()},
        {"module_paths": list(_MODULES)},
        {"module_paths": tuple(reversed(_MODULES))},
        {"module_paths": (*_MODULES, _MODULES[0])},
        {"module_paths": ("backend/tests/unit/test_x.py",)},
        {"module_paths": ("backend/src/sketch2life/../x.py",)},
        {"module_paths": ("backend/src/sketch2life//x.py",)},
        {"max_module_bytes": 0},
        {"max_module_bytes": True},
        {"max_module_bytes": 32 * 1024 * 1024},
        {"manifest_facts": object()},
    ],
)
def test_inventory_structural_inputs_raise(tmp_path: Path, overrides: dict[str, object]) -> None:
    with pytest.raises(LiveObservationInputError):
        _inventory(_repository(tmp_path), **overrides)


def test_real_interpreter_and_distribution_measurement() -> None:
    facts = current_interpreter_facts()
    pairs = installed_distributions()

    assert facts.implementation in {"CPython", "PyPy"}
    assert facts.full_version.startswith(f"{sys.version_info.major}.{sys.version_info.minor}.")
    assert facts.build_identity.startswith("sha256:")
    assert len(facts.build_identity) == len("sha256:") + 64
    assert sys.prefix not in facts.build_identity
    assert pairs
    assert all(isinstance(name, str) and isinstance(version, str) for name, version in pairs)
