"""Local/test admission adapters for the Parent video saga (FEAT-066 T-1a; OD-03, R3, T-2z).

These doubles let a local or test run exercise the saga without Billing or AI Policy. They are
**accept-all and in-memory**: the reservation and the admission answer ``RESERVED`` and ``ACCEPTED``
for every request, and are idempotent on ``(request_ref, idempotency_key)`` as the real ports must
be. They hold no counter, unit, balance, grant, price or month logic, and ``VideoAdmissionScript``
can only return a fixed outcome per call (no counting by scope). Both classes refuse to be built
unless the environment is ``local`` or ``test``; ``Settings`` refuses the flag
``story_video_adapters = local_test`` outside those environments as well (two layers). A production
adapter for either port belongs to its owner (Platform Admin lane for the compute budget, Billing
for the quota); until it exists the route answers 503 ``PROVIDER_UNAVAILABLE``.
"""

from __future__ import annotations

import hashlib
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Final

from sketch2life.application.ports.story_video import (
    AckStatus,
    QuotaResult,
    QuotaStatus,
    ReservationResult,
    ReservationStatus,
    StoryVideoAdapters,
    VideoRequestScope,
)
from sketch2life.infrastructure.documents.local_test_adapters import LocalAdapterRefused

LOCAL_ENVIRONMENTS: Final = frozenset({"local", "test"})


def _require_local(env: str) -> None:
    if env not in LOCAL_ENVIRONMENTS:
        raise LocalAdapterRefused("local test video adapters are available only in local/test")


def _ref(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:24]}"


@dataclass
class VideoAdmissionScript:
    """Fixed outcomes for the next calls of a test; an empty queue means accept-all.

    One entry is used per call, whatever the scope; nothing is counted or remembered here.
    """

    reservations: deque[ReservationStatus] = field(default_factory=deque)
    quotas: deque[QuotaStatus] = field(default_factory=deque)
    releases: deque[AckStatus] = field(default_factory=deque)
    settlements: deque[AckStatus] = field(default_factory=deque)

    def next_reservation(self) -> ReservationStatus | None:
        return self.reservations.popleft() if self.reservations else None

    def next_quota(self) -> QuotaStatus | None:
        return self.quotas.popleft() if self.quotas else None

    def next_release(self) -> AckStatus:
        return self.releases.popleft() if self.releases else AckStatus.DONE

    def next_settlement(self) -> AckStatus:
        return self.settlements.popleft() if self.settlements else AckStatus.DONE


class LocalVideoComputeReservation:
    """Accept-all compute reservation with idempotent in-memory receipts."""

    def __init__(self, *, env: str, script: VideoAdmissionScript | None = None) -> None:
        _require_local(env)
        self._script = script or VideoAdmissionScript()
        self._lock = threading.Lock()
        self._receipts: dict[tuple[str, str], str] = {}
        self.calls: list[tuple[str, str]] = []

    def reserve(
        self, *, scope: VideoRequestScope, request_ref: str, idempotency_key: str, fingerprint: str
    ) -> ReservationResult:
        with self._lock:
            self.calls.append(("reserve", request_ref))
            existing = self._receipts.get((request_ref, idempotency_key))
            if existing is not None:
                return ReservationResult(ReservationStatus.RESERVED, existing)
            scripted = self._script.next_reservation()
            if scripted in (ReservationStatus.COST_LIMIT_REACHED, ReservationStatus.UNAVAILABLE):
                return ReservationResult(scripted)
            reference = _ref("lres", request_ref, idempotency_key)
            self._receipts[(request_ref, idempotency_key)] = reference
            return ReservationResult(ReservationStatus.RESERVED, reference)

    def release(
        self, *, scope: VideoRequestScope, reservation_ref: str, idempotency_key: str
    ) -> AckStatus:
        with self._lock:
            self.calls.append(("release", reservation_ref))
            return self._script.next_release()

    def settle(
        self, *, scope: VideoRequestScope, reservation_ref: str, outcome: str, idempotency_key: str
    ) -> AckStatus:
        with self._lock:
            self.calls.append((f"settle:{outcome}", reservation_ref))
            return self._script.next_settlement()


class LocalVideoQuotaAdmission:
    """Accept-all quota admission with idempotent in-memory receipts; no quota logic."""

    def __init__(self, *, env: str, script: VideoAdmissionScript | None = None) -> None:
        _require_local(env)
        self._script = script or VideoAdmissionScript()
        self._lock = threading.Lock()
        self._receipts: dict[tuple[str, str], tuple[str, str]] = {}
        self.calls: list[str] = []

    def admit_video_request(
        self,
        *,
        scope: VideoRequestScope,
        request_ref: str,
        idempotency_key: str,
        fingerprint: str,
        contract_version: str,
    ) -> QuotaResult:
        with self._lock:
            self.calls.append(request_ref)
            existing = self._receipts.get((request_ref, idempotency_key))
            if existing is not None:
                if existing[0] != fingerprint:
                    return QuotaResult(QuotaStatus.IDEMPOTENCY_MISMATCH)
                return QuotaResult(QuotaStatus.ACCEPTED, existing[1], _ref("lgrt", request_ref))
            scripted = self._script.next_quota()
            if scripted is not None and scripted is not QuotaStatus.ACCEPTED:
                return QuotaResult(scripted)
            usage = _ref("lusg", request_ref, idempotency_key)
            self._receipts[(request_ref, idempotency_key)] = (fingerprint, usage)
            return QuotaResult(QuotaStatus.ACCEPTED, usage, _ref("lgrt", request_ref))


def build_local_video_adapters(
    *, env: str, script: VideoAdmissionScript | None = None
) -> StoryVideoAdapters:
    """The local/test pair; refused outside local/test."""

    shared = script or VideoAdmissionScript()
    return StoryVideoAdapters(
        reservation=LocalVideoComputeReservation(env=env, script=shared),
        quota=LocalVideoQuotaAdmission(env=env, script=shared),
    )


__all__ = [
    "LOCAL_ENVIRONMENTS",
    "LocalAdapterRefused",
    "LocalVideoComputeReservation",
    "LocalVideoQuotaAdmission",
    "VideoAdmissionScript",
    "build_local_video_adapters",
]
