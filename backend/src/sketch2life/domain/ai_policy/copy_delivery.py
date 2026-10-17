"""Pure delivery fencing; not copy deletion, cancellation confirmation or authorization."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.ai_policy.model import PolicyError

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_.:-]{1,120}\Z")
_REASON = re.compile(r"[A-Z][A-Z0-9_]{1,79}\Z")


def _text(value: str, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")


def _time(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise PolicyError("AI_POLICY_INVALID_TIME")


def _revision(value: int) -> None:
    if type(value) is not int or value < 0:
        raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")


class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    IN_FLIGHT = "in_flight"
    PENDING = "pending"
    UNSUPPORTED = "unsupported"
    EXCEPTION = "exception"
    RECEIPT_AVAILABLE = "receipt_available"


class HookOutcome(StrEnum):
    PENDING = "pending"
    UNSUPPORTED = "unsupported"
    EXCEPTION = "exception"
    RECEIPT_AVAILABLE = "receipt_available"


@dataclass(frozen=True, slots=True)
class DeliveryResponse:
    operation_key: str
    binding_digest: str
    outcome: HookOutcome
    reference: str | None = None
    reference_hash: str | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        _text(self.operation_key, _HASH)
        _text(self.binding_digest, _HASH)
        if not isinstance(self.outcome, HookOutcome):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.reason_code is not None:
            _text(self.reason_code, _REASON)
        if self.outcome is HookOutcome.RECEIPT_AVAILABLE:
            if self.reference is None or self.reference_hash is None:
                raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
            _text(self.reference, _ID)
            _text(self.reference_hash, _HASH)
        elif (
            self.reference is not None
            or self.reference_hash is not None
            or self.reason_code is None
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")


@dataclass(frozen=True, slots=True)
class DeliveryState:
    operation_key: str
    binding_digest: str
    revision: int = 0
    status: DeliveryStatus = DeliveryStatus.QUEUED
    claim_token: str | None = None
    claim_started_at: datetime | None = None
    claim_expires_at: datetime | None = None
    used_tokens: tuple[str, ...] = ()
    last_response: DeliveryResponse | None = None

    def __post_init__(self) -> None:
        _text(self.operation_key, _HASH)
        _text(self.binding_digest, _HASH)
        _revision(self.revision)
        if not isinstance(self.status, DeliveryStatus) or type(self.used_tokens) is not tuple:
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        for token in self.used_tokens:
            _text(token, _ID)
        if len(set(self.used_tokens)) != len(self.used_tokens):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.status is DeliveryStatus.QUEUED and (
            self.revision != 0 or self.used_tokens or self.last_response is not None
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.status is DeliveryStatus.IN_FLIGHT:
            if (
                self.claim_token is None
                or self.claim_expires_at is None
                or self.claim_started_at is None
            ):
                raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
            _text(self.claim_token, _ID)
            _time(self.claim_expires_at)
            _time(self.claim_started_at)
            if self.claim_expires_at <= self.claim_started_at:
                raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
            if not self.used_tokens or self.used_tokens[-1] != self.claim_token:
                raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        elif any(
            value is not None
            for value in (self.claim_token, self.claim_started_at, self.claim_expires_at)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.last_response is not None and (
            not isinstance(self.last_response, DeliveryResponse)
            or (
                self.last_response.operation_key,
                self.last_response.binding_digest,
            )
            != (self.operation_key, self.binding_digest)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.status not in {DeliveryStatus.QUEUED, DeliveryStatus.IN_FLIGHT} and (
            self.last_response is None or self.status.value != self.last_response.outcome.value
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if (
            self.status is DeliveryStatus.IN_FLIGHT
            and self.last_response is not None
            and (self.last_response.outcome not in {HookOutcome.PENDING, HookOutcome.EXCEPTION})
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.status is not DeliveryStatus.QUEUED and (
            not self.used_tokens or self.revision < len(self.used_tokens)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        if self.status not in {DeliveryStatus.QUEUED, DeliveryStatus.IN_FLIGHT} and (
            self.revision <= len(self.used_tokens)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")


def claim_delivery(
    state: DeliveryState, *, expected_revision: int, token: str, now: datetime, expires_at: datetime
) -> DeliveryState:
    _revision(expected_revision)
    _text(token, _ID)
    _time(now)
    _time(expires_at)
    if expected_revision != state.revision:
        raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
    if expires_at <= now:
        raise PolicyError("AI_POLICY_COPY_DELIVERY_EXPIRED")
    if state.status is DeliveryStatus.IN_FLIGHT:
        assert state.claim_expires_at is not None
        if state.claim_expires_at > now:
            raise PolicyError("AI_POLICY_COPY_DELIVERY_BUSY")
    elif state.status not in {
        DeliveryStatus.QUEUED,
        DeliveryStatus.PENDING,
        DeliveryStatus.EXCEPTION,
    }:
        raise PolicyError("AI_POLICY_COPY_DELIVERY_NOT_RETRYABLE")
    if token in state.used_tokens:
        raise PolicyError("AI_POLICY_COPY_DELIVERY_TOKEN_REUSED")
    return replace(
        state,
        revision=state.revision + 1,
        status=DeliveryStatus.IN_FLIGHT,
        claim_token=token,
        claim_started_at=now,
        claim_expires_at=expires_at,
        used_tokens=state.used_tokens + (token,),
    )


def finish_delivery(
    state: DeliveryState,
    response: DeliveryResponse,
    *,
    expected_revision: int,
    token: str,
    now: datetime,
) -> DeliveryState:
    _revision(expected_revision)
    _text(token, _ID)
    _time(now)
    if not isinstance(response, DeliveryResponse) or (
        response.operation_key,
        response.binding_digest,
    ) != (state.operation_key, state.binding_digest):
        raise PolicyError("AI_POLICY_COPY_DELIVERY_RESPONSE_MISMATCH")
    if state.status is not DeliveryStatus.IN_FLIGHT:
        if (
            state.last_response == response
            and state.used_tokens
            and state.used_tokens[-1] == token
            and expected_revision + 1 == state.revision
        ):
            return state  # Recorded response replay only, never a fresh execution grant.
        raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
    if state.revision != expected_revision or state.claim_token != token:
        raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
    assert state.claim_expires_at is not None
    assert state.claim_started_at is not None
    if state.claim_expires_at <= now or now < state.claim_started_at:
        raise PolicyError("AI_POLICY_COPY_DELIVERY_EXPIRED")
    return replace(
        state,
        revision=state.revision + 1,
        status=DeliveryStatus(response.outcome.value),
        claim_token=None,
        claim_started_at=None,
        claim_expires_at=None,
        last_response=response,
    )
