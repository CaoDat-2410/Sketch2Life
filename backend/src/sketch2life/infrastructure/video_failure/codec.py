"""Closed JSONB codec, fixed dataclass graph only; native invariants rechecked."""

from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from types import UnionType
from typing import Any, cast, get_args, get_origin, get_type_hints

from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.domain.video_failure.model import (
    Choice,
    Context,
    EffectReceipt,
    FailureTarget,
    Intent,
    NewLifecycle,
    RetryAuthorization,
)

_TYPES = (
    Choice,
    Context,
    EffectReceipt,
    FailureTarget,
    Intent,
    NewLifecycle,
    RetryAuthorization,
    ExactRef,
)
FORMAT = "BE2-10.Intent/0.1-candidate"


def _write(value: object) -> object:
    if type(value) in _TYPES and is_dataclass(value):
        return {field.name: _write(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, int):
        return value
    raise ValueError("unsupported")


def _read(value: object, annotation: Any, depth: int = 0) -> Any:
    # Any stays inside fixed annotation-driven graph, not persistence API.
    if depth > 32:
        raise ValueError("depth")
    if get_origin(annotation) is UnionType:
        for alternative in get_args(annotation):
            try:
                return _read(value, alternative, depth + 1)
            except (ValueError, TypeError, AttributeError):
                pass
        raise ValueError("union")
    if annotation is type(None):
        if value is None:
            return None
        raise ValueError("null")
    if annotation in (str, int):
        if type(value) is annotation:
            return value
        raise ValueError("scalar")
    if annotation is datetime:
        if type(value) is not str:
            raise ValueError("datetime")
        return datetime.fromisoformat(value)
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not str:
            raise ValueError("enum")
        return annotation(value)
    if annotation in _TYPES:
        if type(value) is not dict or set(value) != {field.name for field in fields(annotation)}:
            raise ValueError("fields")
        hints = get_type_hints(annotation)
        return annotation(
            **{key: _read(item, hints[key], depth + 1) for key, item in value.items()}
        )
    raise ValueError("type")


def decode(payload: object) -> Intent:
    try:
        if (
            type(payload) is not dict
            or set(payload) != {"format", "value"}
            or (payload["format"] != FORMAT)
        ):
            raise ValueError("envelope")
        return cast(Intent, _read(payload["value"], Intent))
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        raise VideoError("VIDEO_DISPOSITION_STORAGE_CORRUPT") from None


def encode(intent: Intent) -> dict[str, object]:
    try:
        if type(intent) is not Intent:
            raise ValueError("intent")
        payload = {"format": FORMAT, "value": _write(intent)}
        decode(payload)
        return payload
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        raise VideoError("VIDEO_DISPOSITION_STORAGE_CORRUPT") from None
