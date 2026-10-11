"""Session readiness and runtime-inventory observation producers for FEAT-018 A-LIVE-W1.

Readiness wraps the existing no-model-load inspector with explicitly supplied probes.
The inventory measures an interpreter, installed distributions and an explicitly bound
module list, and can assemble the Section 3A manifest from explicitly supplied probe
facts. Neither producer revalidates the D4 sanitized manifest, stages a fixture, loads a
model, probes hardware by default or authorizes a run.
"""

from __future__ import annotations

import re
import stat
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import get_args

from sketch2life.contracts.schemas.feat018_live_binding import (
    ArtifactIdentityV1,
    DistributionIdentityV1,
    InterpreterIdentityV1,
    ManifestCudaV1,
    ManifestDriverV1,
    ManifestGpuV1,
    ManifestPythonV1,
    SanitizedRuntimeManifestV1,
)
from sketch2life.contracts.schemas.feat018_live_wiring import (
    INTERNAL_MODULE_PREFIX,
    MAX_INVENTORY_ENTRIES,
    DeviceClassValue,
    InventoryEnvironment,
    LiveObservationInputError,
    LiveRuntimeInventoryObservationV1,
    LiveSessionReadinessObservationV1,
    ReadinessStatusValue,
    RevisionStateValue,
    RuntimeInventoryFailureCode,
    SessionReadinessFailureCode,
)
from sketch2life.contracts.schemas.vision_v2 import VisionProfileIdV2
from sketch2life.infrastructure.ai.qwen_vision_environment_readiness import (
    HardwareProbe,
    QwenVisionDeviceClass,
    QwenVisionEnvironmentReadinessV1,
    QwenVisionEnvironmentStatus,
    QwenVisionHardwareFacts,
    QwenVisionRevisionState,
    RevisionVerifier,
    VersionLookup,
    inspect_qwen_vision_environment,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

MAX_MODULE_BYTES_CEILING = 16 * 1024 * 1024
MANIFEST_PACKAGES = ("accelerate", "qwen-vl-utils", "torch", "transformers")
_REPARSE_POINT_ATTRIBUTE = 0x400
_MODULE_PATH = re.compile(r"^backend/src/sketch2life/[A-Za-z0-9_/]+\.py$")
_DISTRIBUTION_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SAFE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,95}$")
_SAFE_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_NAME_SEPARATORS = re.compile(r"[-_.]+")
_INVENTORY_CODE_ORDER: tuple[RuntimeInventoryFailureCode, ...] = get_args(
    RuntimeInventoryFailureCode
)
_STATUS_VALUES: dict[QwenVisionEnvironmentStatus, ReadinessStatusValue] = {
    QwenVisionEnvironmentStatus.READY: "READY",
    QwenVisionEnvironmentStatus.NOT_READY: "NOT_READY",
}
_REVISION_VALUES: dict[QwenVisionRevisionState, RevisionStateValue] = {
    QwenVisionRevisionState.VERIFIED: "VERIFIED",
    QwenVisionRevisionState.NOT_VERIFIABLE: "NOT_VERIFIABLE",
    QwenVisionRevisionState.MISMATCH: "MISMATCH",
}
_DEVICE_VALUES: dict[QwenVisionDeviceClass, DeviceClassValue] = {
    QwenVisionDeviceClass.NVIDIA_L4: "NVIDIA_L4",
    QwenVisionDeviceClass.OTHER: "OTHER",
    QwenVisionDeviceClass.NOT_AVAILABLE: "NOT_AVAILABLE",
}


@dataclass(frozen=True, slots=True)
class InterpreterFacts:
    """Interpreter identity values; the build string is a digest, never a path."""

    implementation: str
    full_version: str
    build_identity: str
    abi_identity: str


@dataclass(frozen=True, slots=True)
class RuntimeManifestFacts:
    """Explicit probe results for the Section 3A manifest; W1 provides no default probe."""

    hardware: QwenVisionHardwareFacts
    device_index: int
    cuda_runtime_version: str
    driver_version: str
    vram_mib: int


def _readiness_failure(
    profile_id: VisionProfileIdV2, code: SessionReadinessFailureCode
) -> LiveSessionReadinessObservationV1:
    return LiveSessionReadinessObservationV1(
        profile_id=profile_id.value,
        readiness_status="NOT_RUN",
        issue_codes=(),
        model_revision_state=None,
        observed_device_class=None,
        cuda_available=None,
        bf16_supported=None,
        dependencies_match=None,
        accepted=False,
        failure_codes=(code,),
    )


def observe_session_readiness(
    runtime_config: QwenVisionRuntimeConfig,
    profile_id: VisionProfileIdV2,
    *,
    version_lookup: VersionLookup,
    hardware_probe: HardwareProbe,
    revision_verifier: RevisionVerifier,
) -> LiveSessionReadinessObservationV1:
    """Run the existing readiness inspector with explicit probes; never load a model."""

    if (
        type(runtime_config) is not QwenVisionRuntimeConfig
        or type(profile_id) is not VisionProfileIdV2
        or not callable(version_lookup)
        or not callable(hardware_probe)
        or not callable(revision_verifier)
    ):
        raise LiveObservationInputError()
    try:
        result = inspect_qwen_vision_environment(
            runtime_config,
            profile_id,
            version_lookup=version_lookup,
            hardware_probe=hardware_probe,
            revision_verifier=revision_verifier,
        )
        if type(result) is not QwenVisionEnvironmentReadinessV1:
            raise TypeError
        checked = QwenVisionEnvironmentReadinessV1.model_validate(result.model_dump())
        codes: list[SessionReadinessFailureCode] = []
        if checked.profile_id is not profile_id:
            codes.append("READINESS_PROFILE_MISMATCH")
        if checked.status is not QwenVisionEnvironmentStatus.READY:
            codes.append("READINESS_NOT_READY")
        return LiveSessionReadinessObservationV1(
            profile_id=profile_id.value,
            readiness_status=_STATUS_VALUES[checked.status],
            issue_codes=tuple(issue.value for issue in checked.issues),
            model_revision_state=_REVISION_VALUES[checked.model_revision_state],
            observed_device_class=_DEVICE_VALUES[checked.observed_device_class],
            cuda_available=checked.cuda_available,
            bf16_supported=checked.bf16_supported,
            dependencies_match=bool(checked.dependencies)
            and all(item.matches for item in checked.dependencies),
            accepted=not codes,
            failure_codes=tuple(codes),
        )
    except Exception:  # noqa: BLE001 - only a closed code leaves this boundary
        return _readiness_failure(profile_id, "READINESS_EXCEPTION")


def current_interpreter_facts() -> InterpreterFacts:
    """Measure the running interpreter without recording a path or the raw build string."""

    implementation = {"cpython": "CPython", "pypy": "PyPy"}.get(
        sys.implementation.name, sys.implementation.name
    )
    info = sys.version_info
    full_version = f"{info.major}.{info.minor}.{info.micro}"
    if info.releaselevel != "final":
        full_version = f"{full_version}{info.releaselevel}{info.serial}"
    return InterpreterFacts(
        implementation=implementation,
        full_version=full_version,
        build_identity="sha256:" + sha256(sys.version.encode("utf-8")).hexdigest(),
        abi_identity=sys.implementation.cache_tag or "",
    )


def installed_distributions() -> tuple[tuple[str, str], ...]:
    """Return raw (name, version) pairs of the running environment's distributions."""

    return tuple((dist.name, dist.version) for dist in metadata.distributions())


def _check_inventory_inputs(
    environment: object,
    interpreter: object,
    repository_root: object,
    module_paths: object,
    max_module_bytes: object,
    manifest_facts: object,
) -> None:
    if environment not in ("HOST", "SESSION") or type(environment) is not str:
        raise LiveObservationInputError()
    if type(interpreter) is not InterpreterFacts:
        raise LiveObservationInputError()
    if (
        not isinstance(repository_root, Path)
        or "\x00" in str(repository_root)
        or not repository_root.is_absolute()
    ):
        raise LiveObservationInputError()
    if type(module_paths) is not tuple or not 0 < len(module_paths) <= MAX_INVENTORY_ENTRIES:
        raise LiveObservationInputError()
    for path in module_paths:
        if (
            type(path) is not str
            or len(path) > 256
            or _MODULE_PATH.fullmatch(path) is None
            or PurePosixPath(path).as_posix() != path
        ):
            raise LiveObservationInputError()
    if module_paths != tuple(sorted(set(module_paths))):
        raise LiveObservationInputError()
    if type(max_module_bytes) is not int or not 0 < max_module_bytes <= MAX_MODULE_BYTES_CEILING:
        raise LiveObservationInputError()
    if manifest_facts is not None and type(manifest_facts) is not RuntimeManifestFacts:
        raise LiveObservationInputError()


def _interpreter_identity(facts: InterpreterFacts) -> InterpreterIdentityV1 | None:
    if (
        facts.implementation not in ("CPython", "PyPy")
        or type(facts.full_version) is not str
        or _SAFE_VERSION.fullmatch(facts.full_version) is None
        or type(facts.build_identity) is not str
        or _SAFE_IDENTITY.fullmatch(facts.build_identity) is None
        or type(facts.abi_identity) is not str
        or _SAFE_IDENTITY.fullmatch(facts.abi_identity) is None
    ):
        return None
    try:
        return InterpreterIdentityV1(
            implementation="CPython" if facts.implementation == "CPython" else "PyPy",
            full_version=facts.full_version,
            build_identity=facts.build_identity,
            abi_identity=facts.abi_identity,
        )
    except Exception:  # noqa: BLE001 - an unusable identity is UNKNOWN
        return None


def _distribution_identities(
    pairs: Iterable[tuple[str, str]],
) -> tuple[tuple[DistributionIdentityV1, ...], RuntimeInventoryFailureCode | None]:
    seen: dict[str, str] = {}
    try:
        for count, pair in enumerate(pairs, start=1):
            if count > MAX_INVENTORY_ENTRIES:
                return (), "DISTRIBUTION_LIMIT"
            if type(pair) is not tuple or len(pair) != 2:
                return (), "DISTRIBUTION_INVALID"
            name, version = pair
            if type(name) is not str or type(version) is not str:
                return (), "DISTRIBUTION_INVALID"
            normalized = _NAME_SEPARATORS.sub("-", name).lower()
            if (
                len(normalized) > 96
                or _DISTRIBUTION_NAME.fullmatch(normalized) is None
                or _SAFE_VERSION.fullmatch(version) is None
            ):
                return (), "DISTRIBUTION_INVALID"
            if normalized in seen:
                return (), "DISTRIBUTION_DUPLICATE"
            seen[normalized] = version
    except Exception:  # noqa: BLE001 - an unreadable distribution source is invalid
        return (), "DISTRIBUTION_INVALID"
    if not seen:
        return (), "DISTRIBUTION_INVALID"
    return (
        tuple(
            DistributionIdentityV1(package=name, version=seen[name]) for name in sorted(seen)
        ),
        None,
    )


def _is_link_or_reparse(info: object) -> bool:
    mode = getattr(info, "st_mode", 0)
    attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISLNK(mode) or bool(attributes & _REPARSE_POINT_ATTRIBUTE)


def _module_identities(
    root: Path, module_paths: tuple[str, ...], limit: int
) -> tuple[tuple[ArtifactIdentityV1, ...], RuntimeInventoryFailureCode | None]:
    try:
        resolved_root = root.resolve(strict=True)
    except RuntimeError:
        # Python 3.12 reports a symlink loop as RuntimeError with the path in its text.
        return (), "MODULE_UNSAFE"
    except (OSError, ValueError):
        return (), "MODULE_UNREADABLE"
    identities: list[ArtifactIdentityV1] = []
    for relative in module_paths:
        parts = PurePosixPath(relative).parts
        candidate = root.joinpath(*parts)
        try:
            info = candidate.lstat()
            if _is_link_or_reparse(info) or not stat.S_ISREG(info.st_mode):
                return (), "MODULE_UNSAFE"
            # A resolved path differing from the lexical path means a link in an ancestor.
            if candidate.resolve(strict=True) != resolved_root.joinpath(*parts):
                return (), "MODULE_UNSAFE"
            with candidate.open("rb") as source:
                content = source.read(limit + 1)
        except RuntimeError:
            return (), "MODULE_UNSAFE"
        except (OSError, ValueError):
            return (), "MODULE_UNREADABLE"
        if len(content) > limit:
            return (), "MODULE_TOO_LARGE"
        identities.append(
            ArtifactIdentityV1(relative_path=relative, sha256=sha256(content).hexdigest())
        )
    return tuple(identities), None


def _manifest_sku(device_name: str | None) -> str:
    if device_name is None:
        return "NOT_AVAILABLE"
    if "_".join(device_name.upper().split()) in {"L4", "NVIDIA_L4"}:
        return "NVIDIA_L4"
    return "OTHER"


def _assemble_manifest(
    interpreter: InterpreterIdentityV1,
    distributions: tuple[DistributionIdentityV1, ...],
    facts: RuntimeManifestFacts,
) -> SanitizedRuntimeManifestV1 | None:
    versions = {item.package: item.version for item in distributions}
    if any(package not in versions for package in MANIFEST_PACKAGES):
        return None
    try:
        hardware = facts.hardware
        if type(hardware) is not QwenVisionHardwareFacts:
            return None
        return SanitizedRuntimeManifestV1.model_validate(
            {
                "python": ManifestPythonV1(
                    implementation=interpreter.implementation,
                    version=interpreter.full_version,
                ),
                "dependencies": tuple(
                    DistributionIdentityV1(package=package, version=versions[package])
                    for package in MANIFEST_PACKAGES
                ),
                "cuda": ManifestCudaV1(
                    available=hardware.cuda_available,
                    device_count=hardware.device_count,
                    runtime_version=facts.cuda_runtime_version,
                ),
                "driver": ManifestDriverV1(version=facts.driver_version),
                "gpu": ManifestGpuV1.model_validate(
                    {
                        "device_index": facts.device_index,
                        "sku": _manifest_sku(hardware.device_name),
                        "vram_mib": facts.vram_mib,
                        "bf16_supported": hardware.bf16_supported,
                    }
                ),
            }
        )
    except Exception:  # noqa: BLE001 - an invalid manifest fact fails the manifest
        return None


def _inventory_failure(
    environment: InventoryEnvironment, codes: list[RuntimeInventoryFailureCode]
) -> LiveRuntimeInventoryObservationV1:
    ordered = tuple(code for code in _INVENTORY_CODE_ORDER if code in codes)
    return LiveRuntimeInventoryObservationV1(
        environment=environment,
        interpreter=None,
        distributions=(),
        internal_modules=(),
        manifest=None,
        accepted=False,
        failure_codes=ordered,
    )


def observe_runtime_inventory(
    *,
    environment: InventoryEnvironment,
    interpreter: InterpreterFacts,
    distributions: Iterable[tuple[str, str]],
    repository_root: Path,
    module_paths: tuple[str, ...],
    max_module_bytes: int,
    manifest_facts: RuntimeManifestFacts | None,
) -> LiveRuntimeInventoryObservationV1:
    """Measure one runtime against an explicit module list; fail closed with no partials."""

    _check_inventory_inputs(
        environment, interpreter, repository_root, module_paths, max_module_bytes, manifest_facts
    )
    codes: list[RuntimeInventoryFailureCode] = []
    identity = _interpreter_identity(interpreter)
    if identity is None:
        codes.append("INTERPRETER_UNKNOWN")
    measured_distributions, distribution_code = _distribution_identities(distributions)
    if distribution_code is not None:
        codes.append(distribution_code)
    modules, module_code = _module_identities(repository_root, module_paths, max_module_bytes)
    if module_code is not None:
        codes.append(module_code)
    manifest: SanitizedRuntimeManifestV1 | None = None
    if not codes and identity is not None and manifest_facts is not None:
        manifest = _assemble_manifest(identity, measured_distributions, manifest_facts)
        if manifest is None:
            codes.append("MANIFEST_INVALID")
    if codes or identity is None:
        return _inventory_failure(environment, codes)
    if any(not module.relative_path.startswith(INTERNAL_MODULE_PREFIX) for module in modules):
        return _inventory_failure(environment, ["MODULE_UNSAFE"])
    try:
        return LiveRuntimeInventoryObservationV1(
            environment=environment,
            interpreter=identity,
            distributions=measured_distributions,
            internal_modules=modules,
            manifest=manifest,
            accepted=True,
            failure_codes=(),
        )
    except Exception:  # noqa: BLE001 - an inconsistent measurement fails closed
        return _inventory_failure(environment, ["MANIFEST_INVALID"])


__all__ = [
    "MANIFEST_PACKAGES",
    "MAX_MODULE_BYTES_CEILING",
    "InterpreterFacts",
    "RuntimeManifestFacts",
    "current_interpreter_facts",
    "installed_distributions",
    "observe_runtime_inventory",
    "observe_session_readiness",
]
