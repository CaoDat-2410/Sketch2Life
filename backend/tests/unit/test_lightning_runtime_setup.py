from __future__ import annotations

import pytest
from tools import verify_lightning_runtime as runtime

from sketch2life.application.ports.illustration_edit import (
    IllustrationEditRequest,
    IllustrationReference,
    MockIllustrationEditAdapter,
)


def test_reference_contract_keeps_source_style_character_separate() -> None:
    refs = tuple(IllustrationReference(role=role, sha256="a" * 64, artifact_ref="fixture")
                 for role in ("SOURCE", "STYLE", "CHARACTER"))
    request = IllustrationEditRequest(prompt="synthetic demo", model_profile="unconfigured",
                                     references=refs)
    receipt = MockIllustrationEditAdapter().prepare(request)
    assert receipt.status == "MOCK_ONLY"
    assert receipt.reference_hashes == ("a" * 64,) * 3


def test_no_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="EXACTLY_ONE_SOURCE_REQUIRED"):
        IllustrationEditRequest(prompt="demo", model_profile="mock", references=())


def test_bad_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="REFERENCE_HASH_INVALID"):
        IllustrationReference(role="SOURCE", sha256="bad", artifact_ref="fixture")


def test_inventory_never_imports_models_or_runs_inference(monkeypatch) -> None:
    monkeypatch.setattr(runtime.shutil, "which", lambda _name: None)
    monkeypatch.setattr(runtime.importlib.util, "find_spec", lambda _name: None)
    result = runtime.inventory()
    assert result["inference_executed"] is False
    assert result["real_inference_ready"] is False
    assert result["wan_revision"] == "UNVERIFIED"


def test_real_mode_fails_closed(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["verify_lightning_runtime.py", "--mode", "real"])
    assert runtime.main() == 2
    assert "REAL_INFERENCE_NOT_AUTHORIZED" in capsys.readouterr().out
