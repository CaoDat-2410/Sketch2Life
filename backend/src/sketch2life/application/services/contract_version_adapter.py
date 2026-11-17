"""Lossless version adapter for P1 integer refs and P4 ``vN`` fields."""

from __future__ import annotations

import re

_VERSION_PATTERN = re.compile(r"^v([1-9][0-9]*)$")


def to_learning_media_version(version: int) -> str:
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("contract version must be a positive integer")
    return f"v{version}"


def from_learning_media_version(version: str) -> int:
    match = _VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError("learning-media version must use canonical vN form")
    return int(match.group(1))


def to_renderer_version(version: int) -> str:
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("renderer version must be a positive integer")
    return str(version)


def from_renderer_version(version: str) -> int:
    if not isinstance(version, str) or not version.isascii() or not version.isdecimal():
        raise ValueError("renderer version must use canonical decimal form")
    parsed = int(version)
    if parsed < 1 or str(parsed) != version:
        raise ValueError("renderer version must use canonical decimal form")
    return parsed


__all__ = [
    "from_learning_media_version",
    "from_renderer_version",
    "to_learning_media_version",
    "to_renderer_version",
]
