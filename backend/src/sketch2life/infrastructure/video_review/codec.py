"""Closed JSONB codec: fixed type graph, exact fields/scalars, native domain recheck.

Never import a class named in stored input or deserialize arbitrary Python objects.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from types import UnionType
from typing import Any, Union, cast, get_args, get_origin, get_type_hints

from sketch2life.application.ports.video_review_lifecycle import ReviewChangeReceipt
from sketch2life.application.ports.video_review_write import ReviewWriteContext, ReviewWriteReceipt
from sketch2life.contracts.schemas.ai_contract_candidates import ExactContentReviewRecordV1
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.domain.video_review.lifecycle import ReviewChange, ReviewChangeRequest
from sketch2life.domain.video_review.model import (
    ReviewEntry,
    ReviewHead,
    ReviewSubject,
    TeachingAudience,
)
from sketch2life.domain.video_review.playback import (
    PlaybackIntent,
    PlaybackReceipt,
    PlaybackRequest,
)

StoredValue = ReviewHead | ReviewWriteReceipt | ReviewChangeReceipt | PlaybackIntent
ROOTS = {
    "head": ReviewHead,
    "write": ReviewWriteReceipt,
    "change": ReviewChangeReceipt,
    "playback": PlaybackIntent,
}
_CLASSES = (
    ReviewHead,
    ReviewWriteReceipt,
    ReviewChangeReceipt,
    PlaybackIntent,
    ReviewWriteContext,
    ReviewChange,
    ReviewChangeRequest,
    ReviewEntry,
    ReviewSubject,
    TeachingAudience,
    ExactRef,
    PlaybackReceipt,
    PlaybackRequest,
)
FORMAT = "BE2-09.Store/0.1-candidate"


def _write(value: object, depth: int = 0) -> object:
    if depth > 64:
        raise ValueError("depth")
    if type(value) in _CLASSES and is_dataclass(value):
        return {item.name: _write(getattr(value, item.name), depth + 1) for item in fields(value)}
    if type(value) is ExactContentReviewRecordV1:
        return value.model_dump(mode="json")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_write(item, depth + 1) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("unsupported")


def _read(value: object, annotation: Any, depth: int = 0) -> Any:
    """Any stays inside this closed recursive typed constructor, not application API."""
    if depth > 64:
        raise ValueError("depth")
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (UnionType, Union):
        for alternative in args:
            try:
                return _read(value, alternative, depth + 1)
            except (ValueError, TypeError, AttributeError):
                pass
        raise ValueError("union")
    if annotation is type(None):
        if value is None:
            return None
        raise ValueError("null")
    if annotation in (str, int, bool):
        if type(value) is annotation:
            return value
        raise ValueError("scalar")
    if annotation is datetime:
        if type(value) is not str:
            raise ValueError("time")
        return datetime.fromisoformat(value)
    if origin is tuple:
        if type(value) is not list:
            raise ValueError("tuple")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_read(item, args[0], depth + 1) for item in value)
        if len(value) != len(args):
            raise ValueError("tuple length")
        return tuple(_read(item, tp, depth + 1) for item, tp in zip(value, args, strict=True))
    if annotation is ExactContentReviewRecordV1:
        return annotation.model_validate_json(json.dumps(value, allow_nan=False), strict=True)
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not str:
            raise ValueError("enum")
        return annotation(value)
    if annotation in _CLASSES:
        if type(value) is not dict:
            raise ValueError("object")
        hints = get_type_hints(annotation)
        if set(value) != {item.name for item in fields(annotation)}:
            raise ValueError("fields")
        return annotation(
            **{name: _read(item, hints[name], depth + 1) for name, item in value.items()}
        )
    raise ValueError("unregistered type")


def decode(kind: str, payload: object) -> StoredValue:
    try:
        if (
            kind not in ROOTS
            or type(payload) is not dict
            or set(payload) != {"format", "kind", "value"}
            or payload["format"] != FORMAT
            or payload["kind"] != kind
        ):
            raise ValueError("envelope")
        return cast(StoredValue, _read(payload["value"], ROOTS[kind]))
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT") from None


def encode(kind: str, value: StoredValue) -> dict[str, object]:
    try:
        if kind not in ROOTS or type(value) is not ROOTS[kind]:
            raise ValueError("kind")
        payload = {"format": FORMAT, "kind": kind, "value": _write(value)}
        decode(kind, payload)  # Domain invariants even for forged native values.
        return payload
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT") from None
