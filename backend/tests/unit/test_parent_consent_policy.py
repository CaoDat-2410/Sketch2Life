"""Unit checks for the immutable synthetic-only consent-policy placeholder."""

from __future__ import annotations

import ast
import re
from dataclasses import FrozenInstanceError, is_dataclass
from hashlib import sha256
from pathlib import Path

import pytest

from sketch2life.domain import parent_consent_policy

BR27_TEXT = (
    "Mọi luồng demo chỉ dùng profile, tranh và audio tổng hợp. Dữ liệu trẻ thật nằm ngoài demo, "
    "cần chính sách riêng về mục đích, quyền, phân quyền, chuyển dữ liệu cho provider và lifecycle."
)


def test_current_policy_is_the_immutable_synthetic_placeholder() -> None:
    policy = parent_consent_policy.CURRENT_PARENT_CONSENT_POLICY
    repository_root = Path(__file__).resolve().parents[3]
    srs_path = (
        repository_root
        / "features"
        / "FEAT-063-system-architecture-rearchitecture"
        / "artifacts"
        / "SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md"
    )
    br27_line = next(
        line
        for line in srs_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("| BR-27 |")
    )
    srs_text = br27_line.split("|", maxsplit=3)[2].strip()

    assert is_dataclass(policy)
    assert policy.consent_text == srs_text == BR27_TEXT
    assert policy.consent_text_sha256 == sha256(policy.consent_text.encode("utf-8")).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", policy.consent_text_sha256)
    assert policy.policy_version == "parent-consent-placeholder-v0"
    assert policy.effective_from is None
    assert policy.policy_state == "PLACEHOLDER_NOT_APPROVED"
    assert policy.purpose_code == "SYNTHETIC_TEST_ONLY"
    assert policy.data_origin_scope == "SYNTHETIC_TEST"
    assert policy.acceptance_recording == "NOT_AVAILABLE"
    assert policy.purposes == (
        ("SYNTHETIC_TEST_ONLY", "parent.consent.placeholder.synthetic_test_only"),
    )
    assert policy.links == ()

    with pytest.raises(FrozenInstanceError):
        setattr(policy, "policy_version", "changed")  # noqa: B010


def test_domain_policy_module_does_not_import_settings() -> None:
    source_path = Path(parent_consent_policy.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert not any("settings" in module.lower() for module in imported_modules)
