"""JSON storage for a fixed, statically imported set of pilot contract types."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from sketch2life.application.ports import assistance as assistance_ports
from sketch2life.domain import assistance, vision_analysis, vision_context

_registry: dict[str, type[Any]] = {}
for _module in (assistance_ports, assistance, vision_analysis, vision_context):
    for _value in vars(_module).values():
        if isinstance(_value, type) and (is_dataclass(_value) or issubclass(_value, Enum)):
            _registry[f"{_value.__module__}.{_value.__qualname__}"] = _value


def _encode(value: object) -> Any:
    if isinstance(value, Enum):
        key = f"{type(value).__module__}.{type(value).__qualname__}"
        if key not in _registry:
            raise ValueError("unregistered enum")
        return {"$type": key, "value": value.value}
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite JSON value")
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("storage timestamps must be aware")
        return {"$type": "datetime", "value": value.isoformat()}
    if is_dataclass(value) and not isinstance(value, type):
        key = f"{type(value).__module__}.{type(value).__qualname__}"
        if key not in _registry:
            raise ValueError("unregistered dataclass")
        return {
            "$type": key,
            "fields": {
                item.name: _encode(getattr(value, item.name)) for item in fields(value) if item.init
            },
        }
    if isinstance(value, tuple | frozenset):
        items = [_encode(item) for item in value]
        if isinstance(value, frozenset):
            items.sort(key=lambda item: json.dumps(item, sort_keys=True))
        return {"$type": "tuple" if isinstance(value, tuple) else "frozenset", "items": items}
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("mapping keys must be strings")
        return {"$type": "mapping", "items": {key: _encode(item) for key, item in value.items()}}
    if isinstance(value, list):
        return {"$type": "list", "items": [_encode(item) for item in value]}
    raise ValueError("unsupported storage type")


def to_payload(value: object) -> dict[str, Any]:
    encoded = _encode(value)
    if not isinstance(encoded, dict):
        raise ValueError("storage root must be a tagged object")
    # Also validates JSON serialization without accepting NaN or arbitrary object hooks.
    json.dumps(encoded, allow_nan=False)
    return encoded


def _decode(value: Any) -> Any:
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if not isinstance(value, dict) or not isinstance(value.get("$type"), str):
        raise ValueError("invalid tagged storage value")
    tag = value["$type"]
    if tag == "datetime":
        if set(value) != {"$type", "value"} or not isinstance(value["value"], str):
            raise ValueError("invalid datetime storage value")
        result = datetime.fromisoformat(value["value"])
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("storage timestamps must be aware")
        return result
    if tag in {"tuple", "frozenset", "list"}:
        if set(value) != {"$type", "items"} or not isinstance(value["items"], list):
            raise ValueError("invalid collection storage value")
        decoded = [_decode(item) for item in value["items"]]
        if tag == "tuple":
            return tuple(decoded)
        if tag == "frozenset":
            try:
                return frozenset(decoded)
            except TypeError as exc:
                raise ValueError("invalid frozenset storage value") from exc
        return decoded
    if tag == "mapping":
        if set(value) != {"$type", "items"} or not isinstance(value["items"], dict):
            raise ValueError("invalid mapping storage value")
        return {str(key): _decode(item) for key, item in value["items"].items()}
    cls = _registry.get(tag)
    if cls is None:
        raise ValueError("unregistered storage type")
    if issubclass(cls, Enum):
        if set(value) != {"$type", "value"}:
            raise ValueError("invalid enum storage value")
        return cls(value["value"])
    expected = {field.name for field in fields(cls) if field.init}
    if (
        set(value) != {"$type", "fields"}
        or not isinstance(value["fields"], dict)
        or set(value["fields"]) != expected
    ):
        raise ValueError("invalid dataclass storage fields")
    return cls(**{key: _decode(item) for key, item in value["fields"].items()})


def from_payload[T](payload: object, expected: type[T]) -> T:
    result = _decode(payload)
    if type(result) is not expected:
        raise ValueError("storage root has the wrong contract type")
    return result
