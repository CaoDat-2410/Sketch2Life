"""Safe loader for the P2-T5 synthetic fixture package."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sketch2life.contracts.schemas.p2_t5_evaluation import (
    P2T5FixtureManifestV1,
    raw_sha256,
)


class FixturePackageError(ValueError):
    """A closed, user-safe fixture package validation error."""


@dataclass(frozen=True, slots=True)
class FixtureCase:
    descriptor: dict[str, Any]
    expected: dict[str, Any]
    image_path: Path
    audio_path: Path

    @property
    def fixture_id(self) -> str:
        return str(self.descriptor["fixture_id"])

    @property
    def split(self) -> str:
        return str(self.descriptor["split"])


@dataclass(frozen=True, slots=True)
class FixturePackage:
    root: Path
    manifest_path: Path
    cases_path: Path
    oracle_path: Path
    matching_rule_path: Path
    manifest: P2T5FixtureManifestV1
    cases: tuple[FixtureCase, ...]
    manifest_sha256: str
    cases_sha256: str
    oracle_sha256: str
    matching_rule_sha256: str

    def selected(self, split: str) -> tuple[FixtureCase, ...]:
        return tuple(case for case in self.cases if case.split == split)


def _safe_relative(root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in value:
        raise FixturePackageError("INVALID_ARGUMENT")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise FixturePackageError("INVALID_ARGUMENT") from exc
    if resolved.is_symlink():
        raise FixturePackageError("INVALID_ARGUMENT")
    return resolved


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED") from exc


def load_fixture_package(root: Path, manifest_ref: str, fixture_root_ref: str) -> FixturePackage:
    """Load and verify all package bytes before any adapter is invoked."""

    manifest_path = _safe_relative(root, manifest_ref)
    fixture_root = _safe_relative(root, fixture_root_ref)
    if not manifest_path.is_file() or not fixture_root.is_dir():
        raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED")
    manifest_data = _read_json(manifest_path)
    try:
        manifest = P2T5FixtureManifestV1.model_validate(manifest_data)
    except ValueError as exc:
        raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED") from exc

    package_dir = manifest_path.parent
    cases_path = _safe_relative(root, f"{package_dir.relative_to(root).as_posix()}/cases-v1.json")
    oracle_path = _safe_relative(root, manifest.oracle_ref)
    matching_rule_path = _safe_relative(
        root, f"{package_dir.relative_to(root).as_posix()}/matching-rule-v1.json"
    )
    cases_data = _read_json(cases_path)
    oracle_data = _read_json(oracle_path)
    rule_data = _read_json(matching_rule_path)
    if not isinstance(cases_data, list) or not isinstance(oracle_data, list):
        raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED")
    expected_ids = {str(row.get("fixture_id")) for row in oracle_data if isinstance(row, dict)}
    case_ids = {str(row.get("fixture_id")) for row in cases_data if isinstance(row, dict)}
    manifest_ids = {entry.fixture_id for entry in manifest.entries}
    if manifest_ids != case_ids or manifest_ids != expected_ids:
        raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED")
    if raw_sha256(oracle_path) != manifest.oracle_sha256:
        raise FixturePackageError("ORACLE_HASH_MISMATCH")
    if raw_sha256(matching_rule_path) != manifest.matching_rule_sha256:
        raise FixturePackageError("MANIFEST_HASH_MISMATCH")
    if not isinstance(rule_data, dict) or rule_data.get("identity") != manifest.matching_rule_id:
        raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED")

    oracle_by_id = {str(row["fixture_id"]): row for row in oracle_data}
    cases: list[FixtureCase] = []
    for entry in manifest.entries:
        descriptor = next(
            (
                row
                for row in cases_data
                if isinstance(row, dict) and row.get("fixture_id") == entry.fixture_id
            ),
            None,
        )
        if descriptor is None:
            raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED")
        image_path = _safe_relative(root, entry.image_ref)
        audio_path = _safe_relative(root, entry.audio_ref)
        if not image_path.is_file() or not audio_path.is_file():
            raise FixturePackageError("CONTRACT_OR_ORACLE_REJECTED")
        if (
            raw_sha256(image_path) != entry.image_sha256
            or raw_sha256(audio_path) != entry.audio_sha256
        ):
            raise FixturePackageError("MANIFEST_HASH_MISMATCH")
        cases.append(
            FixtureCase(
                descriptor=descriptor,
                expected=oracle_by_id[entry.fixture_id],
                image_path=image_path,
                audio_path=audio_path,
            )
        )
    return FixturePackage(
        root=root,
        manifest_path=manifest_path,
        cases_path=cases_path,
        oracle_path=oracle_path,
        matching_rule_path=matching_rule_path,
        manifest=manifest,
        cases=tuple(cases),
        manifest_sha256=raw_sha256(manifest_path),
        cases_sha256=raw_sha256(cases_path),
        oracle_sha256=raw_sha256(oracle_path),
        matching_rule_sha256=raw_sha256(matching_rule_path),
    )
