"""FEAT-093 Amendment D: the pinned checkpoint is verified once per render container, not before every scene."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))


def _video_app() -> Any:
    spec = importlib.util.spec_from_file_location("sketch2life_video_app_cache", MODAL_DIR / "video_app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_verified_checkpoint_is_not_verified_again(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _video_app()
    calls: list[str] = []
    monkeypatch.setattr(app, "model_volume", type("V", (), {"reload": lambda self: calls.append("reload")})())
    monkeypatch.setattr(app, "_read_model_manifest", lambda _path: calls.append("read") or {"total_bytes": 1})
    monkeypatch.setattr(app, "_verify_model_manifest", lambda _root, _marker: calls.append("verify") or True)

    assert app._require_model_ready() == app._require_model_ready() == {"total_bytes": 1}
    assert calls == ["reload", "read", "verify"]


def test_a_failed_verification_is_tried_again(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _video_app()
    monkeypatch.setattr(app, "model_volume", type("V", (), {"reload": lambda self: None})())
    monkeypatch.setattr(app, "_read_model_manifest", lambda _path: None)

    for _ in range(2):
        with pytest.raises(RuntimeError, match="LTX_MODEL_NOT_STAGED"):
            app._require_model_ready()
