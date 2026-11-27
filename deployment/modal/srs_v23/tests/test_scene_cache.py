"""FEAT-098 S2: scene pictures prepared during script review are kept for a short while."""

from __future__ import annotations

import sys
from pathlib import Path

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import scene_cache  # noqa: E402

PNG = b"\x89PNG-keyframe"
AI = {"background": "AI", "reason": None}


def test_a_stored_picture_is_found_by_its_request_and_model(tmp_path: Path) -> None:
    key = scene_cache.cache_key("a" * 64, "rev1")

    scene_cache.store(tmp_path, key, PNG, AI, now=100.0)

    assert scene_cache.lookup(tmp_path, key, now=101.0) == (PNG, AI)
    assert scene_cache.lookup(tmp_path, scene_cache.cache_key("a" * 64, "rev2"), now=101.0) is None
    assert scene_cache.cache_key("a" * 64, "rev1") != scene_cache.cache_key("b" * 64, "rev1")


def test_expired_pictures_are_removed(tmp_path: Path) -> None:
    old, new = scene_cache.cache_key("a" * 64, "r"), scene_cache.cache_key("b" * 64, "r")
    scene_cache.store(tmp_path, old, PNG, AI, now=0.0)

    scene_cache.store(tmp_path, new, PNG, AI, now=scene_cache.TTL_SECONDS + 1)

    assert not (tmp_path / old).exists() and (tmp_path / new).exists()
    assert scene_cache.lookup(tmp_path, new, now=2 * scene_cache.TTL_SECONDS + 2) is None
    assert not (tmp_path / new).exists()


def test_a_damaged_entry_is_ignored(tmp_path: Path) -> None:
    key = scene_cache.cache_key("a" * 64, "r")
    scene_cache.store(tmp_path, key, PNG, AI, now=1.0)
    (tmp_path / key / "meta.json").write_text("{", encoding="utf-8")

    assert scene_cache.lookup(tmp_path, key, now=2.0) is None
