"""Fixed typed JSON graph only, strict fields/scalars, recheck domain on read/write."""

from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from types import UnionType
from typing import Any, cast, get_args, get_origin, get_type_hints

from sketch2life.application.ports.activity_execution import (
    Actor,
    OutcomeAck,
    OutcomeEvent,
    Receipt,
)
from sketch2life.domain.activity_execution.model import TYPES, Assignment, fail
from sketch2life.domain.knowledge_video.model import VideoError

Stored = Assignment | Receipt | OutcomeEvent | OutcomeAck
ROOTS = {"assignment": Assignment, "receipt": Receipt, "event": OutcomeEvent, "ack": OutcomeAck}
CLASSES = (*TYPES, Actor, Receipt, OutcomeEvent, OutcomeAck)
FORMAT = "BE2-11.Store/0.1-candidate"


def _write(value: object) -> object:
    if type(value) in CLASSES and is_dataclass(value):
        return {f.name: _write(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is tuple:
        return [_write(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("unsupported")


def _read(value: object, annotation: Any, depth: int = 0) -> Any:
    if depth > 64:
        raise ValueError("depth")
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is UnionType:
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
            raise ValueError("datetime")
        return datetime.fromisoformat(value)
    if origin is tuple:
        if type(value) is not list:
            raise ValueError("tuple")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_read(item, args[0], depth + 1) for item in value)
        if len(value) != len(args):
            raise ValueError("tuple")
        return tuple(_read(item, tp, depth + 1) for item, tp in zip(value, args, strict=True))
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not str:
            raise ValueError("enum")
        return annotation(value)
    if annotation in CLASSES:
        if type(value) is not dict or set(value) != {f.name for f in fields(annotation)}:
            raise ValueError("fields")
        hints = get_type_hints(annotation)
        return annotation(
            **{key: _read(item, hints[key], depth + 1) for key, item in value.items()}
        )
    raise ValueError("type")


def decode(kind: str, payload: object) -> Stored:
    try:
        if (
            type(payload) is not dict
            or set(payload) != {"format", "kind", "value"}
            or (kind not in ROOTS or payload["format"] != FORMAT or payload["kind"] != kind)
        ):
            raise ValueError("envelope")
        return cast(Stored, _read(payload["value"], ROOTS[kind]))
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        fail("STORAGE_CORRUPT")


def encode(kind: str, value: Stored) -> dict[str, object]:
    try:
        if kind not in ROOTS or type(value) is not ROOTS[kind]:
            raise ValueError("root")
        payload = {"format": FORMAT, "kind": kind, "value": _write(value)}
        decode(kind, payload)
        return payload
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        raise VideoError("ACTIVITY_STORAGE_CORRUPT") from None
