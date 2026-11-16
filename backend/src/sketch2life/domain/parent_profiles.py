"""Domain rules for synthetic Parent-owned profile snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

MIN_PARENT_AGE_MONTHS = 36
MAX_PARENT_AGE_MONTHS = 120
MAX_DISPLAY_NAME_LENGTH = 120
MAX_INTERESTS_SUMMARY_LENGTH = 2000


class ProfileState(StrEnum):
    ACTIVE = "ACTIVE"
    DELETE_PENDING = "DELETE_PENDING"


class ParentProfileError(Exception):
    """A safe, transport-neutral Parent profile rejection."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        current_version: int | None = None,
        field_errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.current_version = current_version
        self.field_errors = field_errors
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    display_name: str
    age_months: int
    interests_summary: str | None

    def normalized_payload(self) -> dict[str, object]:
        return {
            "age_months": self.age_months,
            "display_name": self.display_name,
            "interests_summary": self.interests_summary,
        }

    def revision_hash(self) -> str:
        canonical = json.dumps(
            {
                "age_band_ref": None,
                "age_band_version": None,
                **self.normalized_payload(),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


def validate_snapshot(snapshot: ProfileSnapshot) -> None:
    if not snapshot.display_name.strip():
        raise ParentProfileError(
            400,
            "INVALID_REQUEST",
            "The profile request is invalid",
            field_errors=[{"field": "display_name", "code": "EMPTY"}],
        )
    if len(snapshot.display_name) > MAX_DISPLAY_NAME_LENGTH:
        raise ParentProfileError(
            400,
            "INVALID_REQUEST",
            "The profile request is invalid",
            field_errors=[{"field": "display_name", "code": "TOO_LONG"}],
        )
    if (
        isinstance(snapshot.age_months, bool)
        or not isinstance(snapshot.age_months, int)
    ):
        raise ParentProfileError(
            400,
            "INVALID_REQUEST",
            "The profile request is invalid",
            field_errors=[{"field": "age_months", "code": "INVALID_TYPE"}],
        )
    if not MIN_PARENT_AGE_MONTHS <= snapshot.age_months <= MAX_PARENT_AGE_MONTHS:
        raise ParentProfileError(
            400,
            "INVALID_REQUEST",
            "The profile request is invalid",
            field_errors=[{"field": "age_months", "code": "OUT_OF_RANGE"}],
        )
    if snapshot.interests_summary is not None and not isinstance(
        snapshot.interests_summary, str
    ):
        raise ParentProfileError(
            400,
            "INVALID_REQUEST",
            "The profile request is invalid",
            field_errors=[{"field": "interests_summary", "code": "INVALID_TYPE"}],
        )
    if (
        snapshot.interests_summary is not None
        and len(snapshot.interests_summary) > MAX_INTERESTS_SUMMARY_LENGTH
    ):
        raise ParentProfileError(
            400,
            "INVALID_REQUEST",
            "The profile request is invalid",
            field_errors=[{"field": "interests_summary", "code": "TOO_LONG"}],
        )


def request_fingerprint(
    *, operation: str, resource_scope: str, payload: dict[str, object]
) -> bytes:
    encoded = json.dumps(
        {"operation": operation, "resource_scope": resource_scope, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).digest()
