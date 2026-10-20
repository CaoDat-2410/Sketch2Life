"""Closed typed JSON graph; exact fields and scalar types, no dynamic class imports."""

from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from types import UnionType
from typing import Any, cast, get_args, get_origin, get_type_hints

from sketch2life.application.ports.preset_automation import Decision, LocalReceipt, Stored
from sketch2life.domain.preset_automation.model import (
    Body,
    EffectReceipt,
    Intent,
    Library,
    Review,
    Rule,
    Source,
    Stamp,
    Version,
    fail,
)

ROOTS = {
    "library": Library,
    "intent": Intent,
    "local_receipt": LocalReceipt,
    "effect_receipt": EffectReceipt,
    "decision": Decision,
}
CLASSES = (*ROOTS.values(), Body, Review, Rule, Source, Stamp, Version)
FORMAT = "BE2-13.Store/0.1-candidate"


def _write(value: Any) -> Any:
    if type(value) in CLASSES and is_dataclass(value):
        return {f.name: _write(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is tuple:
        return [_write(v) for v in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("type")


def _read(value: Any, annotation: Any, depth: int = 0) -> Any:
    if depth > 64:
        raise ValueError("depth")
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is UnionType:
        for tp in args:
            try:
                return _read(value, tp, depth + 1)
            except (ValueError, TypeError, AttributeError):
                pass
        raise ValueError("union")
    if annotation is type(None):
        if value is not None:
            raise ValueError("null")
        return None
    if annotation in (str, int, bool):
        if type(value) is not annotation:
            raise ValueError("scalar")
        return value
    if annotation is datetime:
        if type(value) is not str:
            raise ValueError("time")
        return datetime.fromisoformat(value)
    if origin is tuple:
        if type(value) is not list:
            raise ValueError("tuple")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_read(v, args[0], depth + 1) for v in value)
        if len(value) != len(args):
            raise ValueError("arity")
        return tuple(_read(v, tp, depth + 1) for v, tp in zip(value, args, strict=True))
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not str:
            raise ValueError("enum")
        return annotation(value)
    if annotation in CLASSES:
        if type(value) is not dict or set(value) != {f.name for f in fields(annotation)}:
            raise ValueError("fields")
        hints = get_type_hints(annotation)
        return annotation(**{k: _read(v, hints[k], depth + 1) for k, v in value.items()})
    raise ValueError("annotation")


def decode(payload: object) -> Stored:
    try:
        if (
            type(payload) is not dict
            or set(payload) != {"format", "kind", "value"}
            or payload["format"] != FORMAT
            or payload["kind"] not in ROOTS
        ):
            raise ValueError("envelope")
        return cast(Stored, _read(payload["value"], ROOTS[payload["kind"]]))
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        fail("STORAGE_CORRUPT")


def encode(value: Stored) -> dict[str, object]:
    try:
        kind = next(k for k, cls in ROOTS.items() if type(value) is cls)
        payload = {"format": FORMAT, "kind": kind, "value": _write(value)}
        decode(payload)
        return payload
    except (StopIteration, ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        fail("STORAGE_CORRUPT")
