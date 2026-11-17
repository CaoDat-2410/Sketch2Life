from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_t13_script() -> ModuleType:
    repository_root = Path(__file__).resolve().parents[3]
    script_path = (
        repository_root
        / "features"
        / "FEAT-064-current-flow-modal-vision-dev"
        / "tools"
        / "t13_synthetic_pilot_dry_run.py"
    )
    spec = importlib.util.spec_from_file_location("feat064_t13_dry_run", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load T13 dry-run script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_t13_dry_run_exercises_synthetic_flow_and_fails_closed_on_slow_stub(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    script = _load_t13_script()
    monkeypatch.setenv("OWNER_MODAL_CALL_APPROVED", "NO")
    token_file = tmp_path / "provider-token-not-read.txt"
    summary = script.run_dry_run(provider_token_file=token_file)

    assert not token_file.exists()
    assert summary["result"] == "PASS"
    assert summary["flow_steps"] == [
        "organization",
        "class",
        "session",
        "synthetic_proof",
        "accepted_stroke",
        "request",
        "child_status",
        "teacher_pending",
    ]
    assert summary["context_revision_used"] == 41
    assert summary["child_processing_state"] == "unknown"
    assert summary["teacher_processing_state"] == "unknown"
    assert summary["provider_outcome"] == "unknown"
    assert summary["provider_stub_requests"] == 1
    assert summary["external_requests"] == 0
    assert summary["provider_token_read"] is False
    assert summary["provider_token_file_supplied"] is True
    assert summary["owner_modal_call_approved"] == "NO"


def test_t13_url_and_token_arguments_accept_paths_only() -> None:
    script = _load_t13_script()
    with pytest.raises(TypeError, match="file paths"):
        script.run_dry_run(provider_token_file="token-content-is-not-a-path")


def test_t13_refuses_when_owner_modal_approval_is_not_no(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = _load_t13_script()
    monkeypatch.setenv("OWNER_MODAL_CALL_APPROVED", "YES")
    with pytest.raises(RuntimeError, match="OWNER_MODAL_CALL_APPROVED=NO"):
        script.run_dry_run()
