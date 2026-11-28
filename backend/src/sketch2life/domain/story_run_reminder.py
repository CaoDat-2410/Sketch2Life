"""Pure adult-wait reminder rules (FEAT-066 goal v4, T-1d2; BR-39, FR-C-11).

The reminder uses the same effective idle marker and conservative state eligibility as T-1d1, but
fires at +144 hours. The identity deliberately contains only the run id, exact wait state and UTC
deadline at database timestamp precision. No owner, revision, child content or current sweep time is
part of the identity.

OPEN before production enablement: two distinct waits could reuse the same state and timestamp at
microsecond precision. If integrated writers can do that, a durable wait generation is required.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Final

from sketch2life.domain.story_run_closeout import idle_target

REMINDER_DELAY: Final = timedelta(hours=144)
REMINDER_NOTIFICATION_TYPE: Final = "RUN_WAIT_REMINDER"
REMINDER_TEMPLATE_VERSION: Final = 1
_TRIGGER_PREFIX: Final = "run-reminder."


def require_aware_utc(value: datetime, *, field: str = "datetime") -> datetime:
    """Return a UTC-normalized instant; reject naive or non-UTC inputs."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be UTC")
    return value.astimezone(UTC)


def normalize_utc(value: datetime, *, field: str = "datetime") -> datetime:
    """Normalize a timezone-aware instant read from storage to UTC (naive is rejected).

    PostgreSQL ``timestamptz`` values come back in the session time zone; they are the same
    instant, so a non-UTC offset is converted instead of rejected. The injected ``now`` stays
    strict through ``require_aware_utc``.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def reminder_deadline(wait_since: datetime) -> datetime:
    """The stable +144-hour deadline for one adult-wait window."""

    return normalize_utc(wait_since, field="wait_since") + REMINDER_DELAY


def reminder_due(
    run_state: str,
    job_state: str | None,
    wait_since: datetime,
    now: datetime,
    *,
    transcript_pending: bool = False,
    open_generation: bool = False,
) -> bool:
    """Whether an otherwise-current run may receive its +144-hour inbox reminder."""

    instant = require_aware_utc(now, field="now")
    since = normalize_utc(wait_since, field="wait_since")
    return (
        not open_generation
        and idle_target(run_state, job_state, transcript_pending=transcript_pending) is not None
        and instant >= since + REMINDER_DELAY
    )


def canonical_deadline(deadline: datetime) -> str:
    """UTC `Z` spelling with six fractional digits, matching PostgreSQL timestamp precision."""

    instant = normalize_utc(deadline, field="deadline")
    return instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


def reminder_trigger_id(run_id: str, run_state: str, wait_since: datetime) -> str:
    """Return the stable, content-free event key for a run's current adult-wait window."""

    if not run_id:
        raise ValueError("run_id must not be empty")
    if not run_state:
        raise ValueError("run_state must not be empty")
    canonical = json.dumps(
        [run_id, run_state, canonical_deadline(reminder_deadline(wait_since))],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{_TRIGGER_PREFIX}{digest}"


__all__ = [
    "REMINDER_DELAY",
    "REMINDER_NOTIFICATION_TYPE",
    "REMINDER_TEMPLATE_VERSION",
    "canonical_deadline",
    "normalize_utc",
    "reminder_deadline",
    "reminder_due",
    "reminder_trigger_id",
    "require_aware_utc",
]
