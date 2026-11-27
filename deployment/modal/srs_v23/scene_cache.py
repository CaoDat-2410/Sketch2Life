"""FEAT-098: scene pictures prepared while the adult reviews the script, kept on the scratch volume for a short while.

The key is the hash of the preparation request (the drawing, the scene and its prompts) and the plate model revision, so
the video run finds a picture only when it would have asked for exactly the same one.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

TTL_SECONDS = 2 * 60 * 60
_KEYFRAME = "keyframe.png"
_META = "meta.json"


def cache_key(manifest_sha256: str, model_revision: str) -> str:
    return hashlib.sha256(f"{manifest_sha256}:{model_revision}".encode()).hexdigest()


def lookup(root: Path, key: str, *, now: float) -> tuple[bytes, dict[str, Any]] | None:
    """The kept picture and how its background was made; ``None`` when absent, expired or damaged."""

    entry = Path(root) / key
    meta = _meta(entry)
    if meta is None or now - meta["stored_at"] > TTL_SECONDS:
        shutil.rmtree(entry, ignore_errors=True)
        return None
    try:
        keyframe = (entry / _KEYFRAME).read_bytes()
    except OSError:
        return None
    if hashlib.sha256(keyframe).hexdigest() != meta["sha256"]:
        return None
    return keyframe, {"background": meta["background"], "reason": meta["reason"]}


def store(root: Path, key: str, keyframe: bytes, prepare: dict[str, Any], *, now: float) -> None:
    """Keep a picture and remove every expired or half-written one."""

    root = Path(root)
    _purge(root, now)
    entry = root / key
    entry.mkdir(parents=True, exist_ok=True)
    (entry / _KEYFRAME).write_bytes(keyframe)
    # Written last: an entry without it is not complete.
    (entry / _META).write_text(
        json.dumps(
            {
                "background": prepare["background"],
                "reason": prepare["reason"],
                "sha256": hashlib.sha256(keyframe).hexdigest(),
                "stored_at": now,
            }
        ),
        encoding="utf-8",
    )


def _meta(entry: Path) -> dict[str, Any] | None:
    try:
        meta = json.loads((entry / _META).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(meta, dict) or not {"background", "reason", "sha256", "stored_at"} <= meta.keys():
        return None
    return meta


def _purge(root: Path, now: float) -> None:
    if not root.is_dir():
        return
    for entry in root.iterdir():
        meta = _meta(entry)
        if meta is None or now - meta["stored_at"] > TTL_SECONDS:
            shutil.rmtree(entry, ignore_errors=True)
