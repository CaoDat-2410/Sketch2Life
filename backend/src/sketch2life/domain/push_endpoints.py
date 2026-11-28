"""Domain values and safe state transitions for notification push endpoints (T-8b)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class PushEndpointState(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class PushEndpointRecord:
    endpoint_id: str
    recipient_account_id: str
    platform_kind: str
    provider_kind: str
    endpoint_ciphertext: bytes
    endpoint_fingerprint: str
    state: PushEndpointState
    version: int
    registered_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
    app_version: str | None


@dataclass(frozen=True, slots=True)
class PushEndpointReceipt:
    request_fingerprint: str
    response_json: dict[str, object]


def revoke_endpoint(
    endpoint: PushEndpointRecord, *, expected_version: int, now: datetime
) -> PushEndpointRecord:
    """Apply the only state transition in this slice, preserving an already revoked row."""
    if endpoint.version != expected_version:
        raise StalePushEndpointVersion(endpoint.version)
    if endpoint.state is PushEndpointState.REVOKED:
        return endpoint
    if endpoint.state is not PushEndpointState.ACTIVE:
        raise InvalidPushEndpointTransition()
    return replace(
        endpoint,
        state=PushEndpointState.REVOKED,
        version=endpoint.version + 1,
        revoked_at=max(now, endpoint.registered_at),
    )


class StalePushEndpointVersion(ValueError):
    def __init__(self, current_version: int) -> None:
        self.current_version = current_version
        super().__init__("stale push endpoint version")


class InvalidPushEndpointTransition(ValueError):
    pass


__all__ = [
    "InvalidPushEndpointTransition",
    "PushEndpointReceipt",
    "PushEndpointRecord",
    "PushEndpointState",
    "StalePushEndpointVersion",
    "revoke_endpoint",
]
