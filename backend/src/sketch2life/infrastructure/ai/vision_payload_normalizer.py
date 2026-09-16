"""Conservative normalization for real VLM observation payloads.

The normalizer is deliberately provider-agnostic and only runs when the real
CLI opts into bounded repair. It converts common JSON-shape drift into the
canonical observation payload, drops unsafe optional claims, and leaves the
final contract validation to ``VisionUnderstandingSuccessV2``.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

_COLLECTIONS = ("entities", "actions", "relations", "themes", "ambiguous_regions")
_COLLECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "entities": ("entity", "objects", "object"),
    "actions": ("action", "activities", "activity"),
    "relations": ("relation",),
    "themes": ("theme", "topics", "topic"),
    "ambiguous_regions": ("ambiguous_region", "ambiguous", "uncertain_regions"),
}
_ROOT_WRAPPERS = ("result", "output", "response", "analysis", "observations", "data")
_SUPPORTED_COLLECTION_KEYS = frozenset(
    key
    for collection in _COLLECTIONS
    for key in (collection, *_COLLECTION_ALIASES[collection])
)
_TEXT_FIELD: dict[str, str] = {
    "entities": "label",
    "actions": "label",
    "relations": "predicate",
    "themes": "label",
    "ambiguous_regions": "note",
}
_TEXT_ALIASES: dict[str, tuple[str, ...]] = {
    "label": (
        "name",
        "text",
        "description",
        "entity",
        "object",
        "action",
        "activity",
        "verb",
        "theme",
        "topic",
    ),
    "predicate": ("relation", "label", "text", "description"),
    "note": ("description", "text", "label", "region"),
}
_KNOWN_FIELDS: dict[str, frozenset[str]] = {
    "entities": frozenset({"observation_id", "id", "label", "name", "text", "confidence"}),
    "actions": frozenset(
        {
            "observation_id",
            "id",
            "label",
            "name",
            "text",
            "actor_ref",
            "actor",
            "object_ref",
            "object",
            "confidence",
        }
    ),
    "relations": frozenset(
        {
            "observation_id",
            "id",
            "predicate",
            "relation",
            "label",
            "text",
            "subject_ref",
            "subject",
            "object_ref",
            "object",
            "confidence",
        }
    ),
    "themes": frozenset(
        {
            "observation_id",
            "id",
            "label",
            "name",
            "text",
            "evidence_refs",
            "evidence",
            "confidence",
        }
    ),
    "ambiguous_regions": frozenset(
        {"observation_id", "id", "note", "description", "text"}
    ),
}
_ID_PATTERN = re.compile(r"[^a-z0-9]+")
_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2,32}(?:-[a-z0-9]{2,8})?$", re.IGNORECASE)


def normalize_provider_payload(
    payload: dict[str, Any], *, enable_structural_repair: bool = False
) -> tuple[dict[str, Any], bool]:
    """Return a canonical payload and whether bounded normalization changed it."""

    if not enable_structural_repair:
        return dict(payload), False

    payload, unwrapped = _unwrap_root_payload(payload)
    if payload and not _has_supported_collection_key(payload):
        # Do not turn an arbitrary provider envelope or metadata-only object
        # into a false empty observation. Returning it unchanged lets the
        # contract validator emit the normal typed mapping failure.
        return dict(payload), unwrapped

    repaired = unwrapped
    normalized: dict[str, Any] = {}
    records_by_collection: dict[str, list[dict[str, Any]]] = {}
    id_map: dict[str, str] = {}
    ambiguous_ids: set[str] = set()
    used_ids: set[str] = set()

    for collection in _COLLECTIONS:
        source_key, raw_value = _source_collection(payload, collection)
        if collection not in payload or source_key != collection:
            repaired = True
        records = _coerce_records(raw_value)
        if raw_value is not None and not isinstance(raw_value, list):
            repaired = True
        prepared: list[dict[str, Any]] = []
        for index, raw_record in enumerate(records):
            if not isinstance(raw_record, dict):
                repaired = True
                continue
            record, record_changed = _prepare_record(
                collection,
                raw_record,
                index,
                used_ids,
                id_map,
                ambiguous_ids,
            )
            repaired = repaired or record_changed
            if record is not None:
                prepared.append(record)
            else:
                repaired = True
        records_by_collection[collection] = prepared

    if set(payload) - set(_COLLECTIONS) - {
        alias for aliases in _COLLECTION_ALIASES.values() for alias in aliases
    }:
        repaired = True

    # Entities and actions are the only valid roots for relation endpoints.
    # Build this set from retained records, not raw input records, so a
    # malformed entity/action cannot keep an otherwise-invalid relation alive.
    for collection in ("entities", "actions"):
        safe_records: list[dict[str, Any]] = []
        for record in records_by_collection[collection]:
            candidate, changed, keep = _resolve_record_references(
                collection,
                record,
                id_map=id_map,
                ambiguous_ids=ambiguous_ids,
                referenceable_ids=set(),
                evidence_ids=set(),
            )
            repaired = repaired or changed
            if keep:
                safe_records.append(candidate)
            else:
                repaired = True
        normalized[collection] = safe_records

    referenceable_ids = {
        record["observation_id"]
        for collection in ("entities", "actions")
        for record in normalized[collection]
    }
    safe_relations: list[dict[str, Any]] = []
    for record in records_by_collection["relations"]:
        candidate, changed, keep = _resolve_record_references(
            "relations",
            record,
            id_map=id_map,
            ambiguous_ids=ambiguous_ids,
            referenceable_ids=referenceable_ids,
            evidence_ids=set(),
        )
        repaired = repaired or changed
        if keep:
            safe_relations.append(candidate)
        else:
            repaired = True
    normalized["relations"] = safe_relations

    evidence_ids = referenceable_ids | {
        record["observation_id"] for record in normalized["relations"]
    }
    for collection in ("themes", "ambiguous_regions"):
        safe_records = []
        for record in records_by_collection[collection]:
            candidate, changed, keep = _resolve_record_references(
                collection,
                record,
                id_map=id_map,
                ambiguous_ids=ambiguous_ids,
                referenceable_ids=referenceable_ids,
                evidence_ids=evidence_ids,
            )
            repaired = repaired or changed
            if keep:
                safe_records.append(candidate)
            else:
                repaired = True
        normalized[collection] = safe_records

    return normalized, repaired


def _source_collection(payload: dict[str, Any], collection: str) -> tuple[str, Any]:
    if collection in payload and payload[collection] is not None:
        return collection, payload[collection]
    for alias in _COLLECTION_ALIASES[collection]:
        if alias in payload:
            return alias, payload[alias]
    return collection, None


def _has_supported_collection_key(payload: dict[str, Any]) -> bool:
    return bool(set(payload) & _SUPPORTED_COLLECTION_KEYS)


def _unwrap_root_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    current = payload
    changed = False
    for _ in range(2):
        nested = [
            value
            for key, value in current.items()
            if key in _ROOT_WRAPPERS
            and isinstance(value, dict)
            and _has_supported_collection_key(value)
        ]
        if len(nested) != 1:
            break
        current = nested[0]
        changed = True
    return current, changed


def _coerce_records(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "observations", "records", "data"):
            nested = value.get(key)
            if isinstance(nested, list):
                return nested
        return [value]
    return []


def _prepare_record(
    collection: str,
    raw_record: dict[str, Any],
    index: int,
    used_ids: set[str],
    id_map: dict[str, str],
    ambiguous_ids: set[str],
) -> tuple[dict[str, Any] | None, bool]:
    changed = False
    candidate: dict[str, Any] = {}
    raw_id = raw_record.get("observation_id", raw_record.get("id"))
    normalized_id = _normalize_id(raw_id)
    if normalized_id is None:
        normalized_id = _new_id(collection, index, used_ids)
        changed = True
    elif normalized_id in used_ids:
        original = _reference_key(raw_id)
        if original:
            ambiguous_ids.add(original)
            id_map.pop(original, None)
        normalized_id = _new_id(collection, index, used_ids)
        changed = True
    if raw_id != normalized_id:
        changed = True
    used_ids.add(normalized_id)
    _remember_id(raw_id, normalized_id, id_map, ambiguous_ids)
    candidate["observation_id"] = normalized_id

    text_field = _TEXT_FIELD[collection]
    text_value = _first_value(raw_record, (text_field, *_TEXT_ALIASES[text_field]))
    normalized_text = _normalize_text(text_value)
    if normalized_text is None:
        return None, True
    if normalized_text != text_value:
        changed = True
    candidate[text_field] = normalized_text

    if collection != "ambiguous_regions":
        candidate["confidence"] = _normalize_confidence(raw_record.get("confidence"))
        if (
            "confidence" not in raw_record
            or raw_record.get("confidence") != candidate["confidence"]
        ):
            changed = True
    if collection == "actions":
        if "actor_ref" not in raw_record and "actor" not in raw_record:
            changed = True
        candidate["actor_ref"] = _reference_key(
            _first_value(raw_record, ("actor_ref", "actor"))
        )
        if "object_ref" not in raw_record and "object" not in raw_record:
            changed = True
        candidate["object_ref"] = _reference_key(
            _first_value(raw_record, ("object_ref", "object"))
        )
    elif collection == "relations":
        if "subject_ref" not in raw_record and "subject" not in raw_record:
            changed = True
        if "object_ref" not in raw_record and "object" not in raw_record:
            changed = True
        candidate["subject_ref"] = _reference_key(
            _first_value(raw_record, ("subject_ref", "subject"))
        )
        candidate["object_ref"] = _reference_key(
            _first_value(raw_record, ("object_ref", "object"))
        )
    elif collection == "themes":
        evidence = _first_value(raw_record, ("evidence_refs", "evidence"))
        if isinstance(evidence, str):
            evidence = [evidence]
            changed = True
        if not isinstance(evidence, list):
            evidence = []
            changed = True
        candidate["evidence_refs"] = [
            reference
            for item in evidence
            if (reference := _reference_key(item)) is not None
        ]
        if candidate["evidence_refs"] != evidence:
            changed = True

    if set(raw_record) - _KNOWN_FIELDS[collection]:
        changed = True
    return candidate, changed


def _resolve_record_references(
    collection: str,
    record: dict[str, Any],
    *,
    id_map: dict[str, str],
    ambiguous_ids: set[str],
    referenceable_ids: set[str],
    evidence_ids: set[str],
) -> tuple[dict[str, Any], bool, bool]:
    changed = False
    candidate = dict(record)
    if collection == "actions":
        for field in ("actor_ref", "object_ref"):
            value = _resolve_reference(candidate.get(field), id_map, ambiguous_ids)
            if value != candidate.get(field):
                changed = True
            candidate[field] = value
        return candidate, changed, True
    if collection == "relations":
        subject = _resolve_reference(candidate.get("subject_ref"), id_map, ambiguous_ids)
        obj = _resolve_reference(candidate.get("object_ref"), id_map, ambiguous_ids)
        if subject not in referenceable_ids or obj not in referenceable_ids or subject == obj:
            return candidate, True, False
        candidate["subject_ref"] = subject
        candidate["object_ref"] = obj
        changed = changed or subject != record.get("subject_ref") or obj != record.get("object_ref")
        return candidate, changed, True
    if collection == "themes":
        resolved = tuple(
            reference
            for reference in (
                _resolve_reference(item, id_map, ambiguous_ids)
                for item in candidate.get("evidence_refs", [])
            )
            if reference in evidence_ids
        )
        if not resolved:
            return candidate, True, False
        candidate["evidence_refs"] = list(dict.fromkeys(resolved))
        changed = changed or tuple(candidate["evidence_refs"]) != tuple(record["evidence_refs"])
    return candidate, changed, True


def _first_value(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def _normalize_text(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        text = value
        language: Any = None
    elif isinstance(value, dict):
        text = _first_value(value, ("value", "text", "content"))
        language = value.get("language")
    else:
        return None
    if not isinstance(text, str) or not text.strip():
        return None
    return {"value": text, "language": _normalize_language(language)}


def _normalize_language(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        tag = value.strip().lower()
        if tag == "vi-vn":
            tag = "vi"
        if _LANGUAGE_PATTERN.fullmatch(tag):
            return {"status": "DECLARED", "tags": [tag]}
    if isinstance(value, dict):
        status = value.get("status")
        tags = value.get("tags")
        if status == "DECLARED" and isinstance(tags, list):
            clean_tags = _clean_tags(tags)
            if len(clean_tags) == 1:
                return {"status": "DECLARED", "tags": clean_tags}
        if status == "MIXED" and isinstance(tags, list):
            clean_tags = _clean_tags(tags)
            if len(clean_tags) >= 2:
                return {"status": "MIXED", "tags": clean_tags}
        if status == "NOT_DETERMINED":
            return {"status": "NOT_DETERMINED", "tags": []}
    return {"status": "NOT_DETERMINED", "tags": []}


def _clean_tags(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(value.strip().lower() for value in values if isinstance(value, str)))


def _normalize_confidence(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        return None
    return number


def _normalize_id(value: Any) -> str | None:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return None
    raw = str(value).strip()
    if not raw:
        return None
    decomposed = unicodedata.normalize("NFKD", raw)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii").lower()
    normalized = _ID_PATTERN.sub("-", ascii_text).strip("-")
    return normalized or None


def _new_id(collection: str, index: int, used_ids: set[str]) -> str:
    prefix = {
        "entities": "entity",
        "actions": "action",
        "relations": "relation",
        "themes": "theme",
        "ambiguous_regions": "region",
    }[collection]
    candidate = f"{prefix}-{index + 1}"
    while candidate in used_ids:
        candidate += "-repair"
    return candidate


def _reference_key(value: Any) -> str | None:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return str(value).strip()
    if isinstance(value, dict):
        nested = _first_value(value, ("observation_id", "id"))
        if isinstance(nested, (str, int)) and not isinstance(nested, bool):
            return str(nested).strip()
    return None


def _remember_id(
    raw_id: Any,
    normalized_id: str,
    id_map: dict[str, str],
    ambiguous_ids: set[str],
) -> None:
    for key in (str(raw_id).strip() if raw_id is not None else "", normalized_id):
        if not key or key in ambiguous_ids:
            continue
        previous = id_map.get(key)
        if previous is not None and previous != normalized_id:
            ambiguous_ids.add(key)
            id_map.pop(key, None)
        else:
            id_map[key] = normalized_id


def _resolve_reference(
    value: Any, id_map: dict[str, str], ambiguous_ids: set[str]
) -> str | None:
    key = _reference_key(value)
    if key is None or key in ambiguous_ids:
        return None
    normalized = _normalize_id(key)
    return id_map.get(key) or (id_map.get(normalized) if normalized is not None else None)


__all__ = ["normalize_provider_payload"]
