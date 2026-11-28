"""Local/test-only fake push sender; it records IDs only and never retains message contents."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass

from sketch2life.application.ports.push_delivery import (
    PushMessage,
    PushSenderPort,
    PushSendOutcome,
    PushSendResult,
)


def _require_local_test(env: str | None = None) -> None:
    environment = os.environ.get("SKETCH2LIFE_ENV", "") if env is None else env
    if environment.lower() not in {"local", "test"}:
        raise RuntimeError("fake push sender is restricted to local/test environments")


@dataclass(frozen=True, slots=True)
class LocalFakePushSendRecord:
    delivery_id: str
    push_endpoint_id: str


class LocalFakePushSender(PushSenderPort):
    """A scripted sender that retains only endpoint and delivery IDs."""

    test_only = True

    def __init__(
        self,
        outcomes: Iterable[PushSendOutcome] = (),
        *,
        env: str | None = None,
    ) -> None:
        _require_local_test(env)
        self._environment = env
        self._outcomes = iter(tuple(outcomes))
        self.records: list[LocalFakePushSendRecord] = []

    def send(self, message: PushMessage) -> PushSendResult:
        _require_local_test(self._environment)
        self.records.append(
            LocalFakePushSendRecord(
                delivery_id=message.delivery_id,
                push_endpoint_id=message.push_endpoint_id,
            )
        )
        outcome = next(self._outcomes, PushSendOutcome.SENT)
        return PushSendResult(outcome)


__all__ = ["LocalFakePushSendRecord", "LocalFakePushSender", "_require_local_test"]
