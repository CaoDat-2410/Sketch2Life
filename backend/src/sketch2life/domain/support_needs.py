"""Domain rules for encrypted profile support needs (T-12c, DDL-D).

A support need is an adult-entered, optional category and a free-text note about how a child is
best supported (SRS l.264 BR-20, l.499 FR-C-07, l.1922). It is never a diagnosis and nothing here
infers one. The record is a singleton per profile, encrypted at rest, and never part of an
ordinary profile projection, a run snapshot or an AI input (l.932).

This module is pure: no framework, no key and no clock. The cipher and the receipt MAC are ports
(``sketch2life.application.ports.support_needs``); here live the bounds, the canonical plaintext,
the associated data that binds a ciphertext to its record, and the fingerprint message.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Final, Literal

from sketch2life.domain.diagnosis_screen import looks_like_diagnosis

SupportNeedsFamily = Literal["parent", "be1"]

FAMILIES: Final[tuple[SupportNeedsFamily, ...]] = ("parent", "be1")
ALGORITHM_VERSION: Final = 1
NONCE_BYTES: Final = 12
KEY_BYTES: Final = 32
TAG_BYTES: Final = 16
MAX_CIPHERTEXT_BYTES: Final = 16_384
MAX_REVISION: Final = 2**31 - 1
MAX_CATEGORY_CHARS: Final = 80
MAX_CATEGORY_BYTES: Final = 320
MAX_NOTE_CHARS: Final = 2_000
MAX_NOTE_BYTES: Final = 8_000
# NUL, the C0 controls and DEL are refused; a newline and a tab stay legal (a multi-line note).
FORBIDDEN_CONTROLS: Final = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

FINGERPRINT_DOMAIN: Final = "support-needs.put.receipt"
FINGERPRINT_VERSION: Final = 1
_AAD_MAGIC: Final = b"s2l.support-needs.aad"


class SupportNeedsRuleViolation(ValueError):
    """A bound or rule was broken. ``field`` and ``code`` never carry the submitted value."""

    def __init__(self, field: str, code: str) -> None:
        super().__init__(f"{field}:{code}")
        self.field = field
        self.code = code


@dataclass(frozen=True, slots=True)
class SupportNeedsPayload:
    category: str | None
    note: str | None

    def plaintext(self) -> bytes:
        """The canonical plaintext that is encrypted: both fields, UTF-8, no ASCII escaping."""
        return json.dumps(
            {"category": self.category, "note": self.note},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def as_public(self) -> dict[str, str | None]:
        return {"category": self.category, "note": self.note}


EMPTY_PAYLOAD: Final = SupportNeedsPayload(category=None, note=None)


def _check_text(field: str, value: str, *, max_chars: int, max_bytes: int) -> None:
    if not value.strip():
        raise SupportNeedsRuleViolation(field, "EMPTY")
    if len(value) > max_chars or len(value.encode("utf-8")) > max_bytes:
        raise SupportNeedsRuleViolation(field, "TOO_LONG")
    if FORBIDDEN_CONTROLS.search(value) is not None:
        raise SupportNeedsRuleViolation(field, "INVALID_FORMAT")
    if looks_like_diagnosis(value):
        # BR-20 (SRS l.266): a support need is not a diagnosis. Input only; a stored record is
        # never screened again, and the text is not echoed.
        raise SupportNeedsRuleViolation(field, "DIAGNOSIS_LIKE")


def check_category(value: str) -> None:
    _check_text("category", value, max_chars=MAX_CATEGORY_CHARS, max_bytes=MAX_CATEGORY_BYTES)


def check_note(value: str) -> None:
    _check_text("note", value, max_chars=MAX_NOTE_CHARS, max_bytes=MAX_NOTE_BYTES)


def validate_payload(category: str | None, note: str | None) -> SupportNeedsPayload:
    """Bounds of the adult input. Text is kept exactly as sent (no trim, no Unicode folding)."""
    if category is not None:
        check_category(category)
    if note is not None:
        check_note(note)
    if category is None and note is None:
        raise SupportNeedsRuleViolation("note", "REQUIRED")
    return SupportNeedsPayload(category=category, note=note)


def parse_plaintext(raw: bytes) -> SupportNeedsPayload:
    """Read a decrypted plaintext back; a shape that is not ours fails (never silently)."""
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SupportNeedsRuleViolation("record", "INVALID_FORMAT") from None
    if (
        not isinstance(decoded, dict)
        or set(decoded) != {"category", "note"}
        or not all(value is None or isinstance(value, str) for value in decoded.values())
    ):
        raise SupportNeedsRuleViolation("record", "INVALID_FORMAT")
    return SupportNeedsPayload(category=decoded["category"], note=decoded["note"])


def check_revision(value: int, *, allow_zero: bool) -> int:
    """Revisions are positive; zero is the API-only "no record yet" (``expected_revision``)."""
    if type(value) is not int or value < (0 if allow_zero else 1) or value > MAX_REVISION:
        raise SupportNeedsRuleViolation("expected_revision", "OUT_OF_RANGE")
    return value


def _field(value: bytes) -> bytes:
    return len(value).to_bytes(4, "big") + value


def build_aad(
    *,
    family: SupportNeedsFamily,
    tenant: str,
    profile_id: str,
    revision: int,
    key_id: str,
    algorithm_version: int = ALGORITHM_VERSION,
) -> bytes:
    """Length-delimited, versioned associated data: a ciphertext opens only for its own record.

    Family, tenant (the organization for BE1, empty for the Parent family), profile, revision,
    key id and algorithm version are all authenticated, so a ciphertext copied to another
    profile, family, revision or key label fails to open.
    """
    return b"".join(
        (
            _AAD_MAGIC,
            bytes((algorithm_version,)),
            _field(family.encode("ascii")),
            _field(tenant.encode("utf-8")),
            _field(profile_id.encode("utf-8")),
            _field(str(revision).encode("ascii")),
            _field(key_id.encode("utf-8")),
        )
    )


def fingerprint_message(
    *,
    family: SupportNeedsFamily,
    tenant: str,
    profile_id: str,
    principal: str,
    expected_revision: int,
    payload: SupportNeedsPayload,
) -> bytes:
    """The bytes the keyed receipt MAC covers: actor, resource, expected revision and both values.

    Domain and version live inside the message. The value derives from the note, so it is only
    ever used as the input of a keyed MAC and is never logged, stored or returned.
    """
    return json.dumps(
        {
            "domain": FINGERPRINT_DOMAIN,
            "v": FINGERPRINT_VERSION,
            "family": family,
            "tenant": tenant,
            "profile_id": profile_id,
            "principal": principal,
            "expected_revision": expected_revision,
            "category": payload.category,
            "note": payload.note,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


__all__ = [
    "ALGORITHM_VERSION",
    "EMPTY_PAYLOAD",
    "FAMILIES",
    "FINGERPRINT_DOMAIN",
    "FINGERPRINT_VERSION",
    "FORBIDDEN_CONTROLS",
    "KEY_BYTES",
    "MAX_CATEGORY_BYTES",
    "MAX_CATEGORY_CHARS",
    "MAX_CIPHERTEXT_BYTES",
    "MAX_NOTE_BYTES",
    "MAX_NOTE_CHARS",
    "MAX_REVISION",
    "NONCE_BYTES",
    "SupportNeedsFamily",
    "SupportNeedsPayload",
    "SupportNeedsRuleViolation",
    "TAG_BYTES",
    "build_aad",
    "check_category",
    "check_note",
    "check_revision",
    "fingerprint_message",
    "parse_plaintext",
    "validate_payload",
]
