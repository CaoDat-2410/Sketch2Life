"""Domain rules for Parent profile context entries and the selected-context snapshot (T-12a).

An entry is an adult-entered observation, achievement or out-of-app experience attached to a
stable profile (SRS l.263-265 BR-19 to BR-21, l.497-499 FR-C-05 to FR-C-07). Only the kind and the
text of an entry the adult chose at confirmation ever reach a Story snapshot or a worker input
(BR-21, FR-P-06 l.2349): never the id, the source, the date or the creator.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from sketch2life.domain.parent_profiles import ParentProfileError

CONTEXT_ENTRY_KINDS: tuple[str, ...] = ("OBSERVATION", "ACHIEVEMENT", "OUTSIDE_EXPERIENCE")
MAX_SHORT_TEXT_CHARS = 500
MAX_SHORT_TEXT_BYTES = 2_000
MAX_SOURCE_REF_CHARS = 256
MAX_SELECTED_ENTRIES = 10
SNAPSHOT_MAX_BYTES = 32_768
SOURCE_KIND_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,31}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Policy (impl review P2-1): NUL, the C0 controls and DEL are refused (PostgreSQL text cannot
# hold NUL, and each other control costs six bytes in ``jsonb::text``). ``short_text`` may hold
# a newline and a tab (a multi-line note); ``source_ref`` is an opaque reference with none.
FORBIDDEN_TEXT_CONTROLS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
FORBIDDEN_REF_CONTROLS = re.compile(r"[\x00-\x1f\x7f]")

PARENT_CONTEXT_V1_SCHEMA = "sketch2life.parent-context.v1"
PARENT_CONTEXT_V2_SCHEMA = "sketch2life.parent-context.v2"


@dataclass(frozen=True, slots=True)
class ContextEntryDraft:
    entry_kind: str
    short_text: str
    source_kind: str
    source_ref: str | None
    approximate_date: date | None

    def normalized(self) -> ContextEntryDraft:
        return ContextEntryDraft(
            entry_kind=self.entry_kind,
            short_text=self.short_text.strip(),
            source_kind=self.source_kind,
            source_ref=self.source_ref.strip() if self.source_ref is not None else None,
            approximate_date=self.approximate_date,
        )

    def normalized_payload(self) -> dict[str, object]:
        """The request fingerprint payload: the stored values, in a stable form."""

        entry = self.normalized()
        return {
            "approximate_date": (
                entry.approximate_date.isoformat() if entry.approximate_date is not None else None
            ),
            "entry_kind": entry.entry_kind,
            "short_text": entry.short_text,
            "source_kind": entry.source_kind,
            "source_ref": entry.source_ref,
        }


@dataclass(frozen=True, slots=True)
class SelectedContextEntry:
    """What the adult chose to send: the kind and the text of one entry, nothing else."""

    kind: str
    text: str

    def as_snapshot_item(self) -> dict[str, str]:
        return {"kind": self.kind, "text": self.text}


def _invalid(field: str, code: str) -> ParentProfileError:
    return ParentProfileError(
        400,
        "INVALID_REQUEST",
        "The request is invalid",
        field_errors=[{"field": field, "code": code}],
    )


def validate_entry(draft: ContextEntryDraft) -> ContextEntryDraft:
    """Validate and normalise (trim) a new entry; never truncates."""

    entry = draft.normalized()
    if entry.entry_kind not in CONTEXT_ENTRY_KINDS:
        raise _invalid("entry_kind", "INVALID_FORMAT")
    if not entry.short_text:
        raise _invalid("short_text", "EMPTY")
    if len(entry.short_text) > MAX_SHORT_TEXT_CHARS:
        raise _invalid("short_text", "TOO_LONG")
    if len(entry.short_text.encode("utf-8")) > MAX_SHORT_TEXT_BYTES:
        raise _invalid("short_text", "TOO_LONG")
    if FORBIDDEN_TEXT_CONTROLS.search(entry.short_text) is not None:
        raise _invalid("short_text", "INVALID_FORMAT")
    if SOURCE_KIND_PATTERN.fullmatch(entry.source_kind) is None:
        raise _invalid("source_kind", "INVALID_FORMAT")
    if entry.source_ref is not None:
        if not entry.source_ref:
            raise _invalid("source_ref", "EMPTY")
        if len(entry.source_ref) > MAX_SOURCE_REF_CHARS:
            raise _invalid("source_ref", "TOO_LONG")
        if FORBIDDEN_REF_CONTROLS.search(entry.source_ref) is not None:
            raise _invalid("source_ref", "INVALID_FORMAT")
    return entry


def parse_approximate_date(value: str) -> date:
    """``YYYY-MM-DD`` only (the ISO calendar date); anything else is a format error."""

    if DATE_PATTERN.fullmatch(value) is None:
        raise ValueError("approximate_date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def build_selected_context_snapshot(
    base: Mapping[str, Any], entries: Sequence[SelectedContextEntry]
) -> dict[str, Any]:
    """The v2 context snapshot: every v1 field plus the selected ``{kind, text}`` entries."""

    if base.get("schema_version") != PARENT_CONTEXT_V1_SCHEMA:
        raise ValueError("only a v1 Parent context can take a selection")
    return {
        **base,
        "schema_version": PARENT_CONTEXT_V2_SCHEMA,
        "selected_entries": [entry.as_snapshot_item() for entry in entries],
    }


def jsonb_text_size(value: Any) -> int:
    """Byte length of the PostgreSQL ``jsonb::text`` form (``", "`` and ``": "`` separators), the
    form ``ck_story_run_input_parent_context`` bounds at 32,768 bytes."""

    return len(json.dumps(value, ensure_ascii=False, separators=(", ", ": ")).encode("utf-8"))


def context_entries_for_worker(context: Mapping[str, Any]) -> list[dict[str, str]]:
    """The ``context_entries`` key of a worker input: the ``{kind, text}`` list of a v2 Parent
    snapshot; ``[]`` for a v1 snapshot, an empty selection and any Teacher snapshot."""

    if context.get("schema_version") != PARENT_CONTEXT_V2_SCHEMA:
        return []
    items = context.get("selected_entries")
    if not isinstance(items, list):
        return []
    return [
        {"kind": str(item["kind"]), "text": str(item["text"])}
        for item in items
        if isinstance(item, Mapping) and "kind" in item and "text" in item
    ]


__all__ = [
    "CONTEXT_ENTRY_KINDS",
    "FORBIDDEN_REF_CONTROLS",
    "FORBIDDEN_TEXT_CONTROLS",
    "MAX_SELECTED_ENTRIES",
    "MAX_SHORT_TEXT_BYTES",
    "MAX_SHORT_TEXT_CHARS",
    "MAX_SOURCE_REF_CHARS",
    "PARENT_CONTEXT_V1_SCHEMA",
    "PARENT_CONTEXT_V2_SCHEMA",
    "SNAPSHOT_MAX_BYTES",
    "ContextEntryDraft",
    "SelectedContextEntry",
    "build_selected_context_snapshot",
    "context_entries_for_worker",
    "jsonb_text_size",
    "parse_approximate_date",
    "validate_entry",
]
