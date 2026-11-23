"""FEAT-066 T-7c-fix unit tests: the bounded account/IP sliding-window limiter (O-2, NFR-12 l.637).

An injected clock drives every case; no sleeping and no database.
"""

from __future__ import annotations

import inspect
from threading import Barrier, Thread
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import HTTPException, Request
from pydantic import SecretStr

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.be1_runtime import Be1Runtime
from sketch2life.interfaces.http.rate_limit import MAX_TRACKED_KEYS, SlidingWindowLimiter
from sketch2life.interfaces.http.routers import be1_registry

OP = "profile_create_real_gate"


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _limiter(
    clock: Clock, *, account_limit: int = 3, ip_limit: int = 5, window: int = 60, max_keys: int = 8
) -> SlidingWindowLimiter:
    return SlidingWindowLimiter(
        account_limit=account_limit,
        ip_limit=ip_limit,
        window_seconds=window,
        max_keys=max_keys,
        clock=clock,
    )


def test_attempts_up_to_the_limit_pass_then_the_next_is_refused() -> None:
    limiter = _limiter(Clock())
    assert [limiter.acquire(OP, account="a", ip="1") for _ in range(3)] == [None, None, None]
    wait = limiter.acquire(OP, account="a", ip="1")
    assert isinstance(wait, int) and wait >= 1


def test_the_window_expires_with_the_injected_clock() -> None:
    clock = Clock()
    limiter = _limiter(clock)
    for _ in range(3):
        assert limiter.acquire(OP, account="a", ip="1") is None
    assert limiter.acquire(OP, account="a", ip="1") is not None
    clock.now += 59.0
    assert limiter.acquire(OP, account="a", ip="1") is not None
    clock.now += 1.0  # the oldest hit is exactly one window old
    assert limiter.acquire(OP, account="a", ip="1") is None


def test_accounts_and_addresses_are_counted_separately() -> None:
    limiter = _limiter(Clock(), account_limit=2, ip_limit=100)
    assert limiter.acquire(OP, account="a", ip="1") is None
    assert limiter.acquire(OP, account="a", ip="2") is None
    assert limiter.acquire(OP, account="a", ip="3") is not None  # account a is full
    assert limiter.acquire(OP, account="b", ip="1") is None  # another account is not limited
    other = _limiter(Clock(), account_limit=100, ip_limit=2)
    assert other.acquire(OP, account="a", ip="1") is None
    assert other.acquire(OP, account="b", ip="1") is None
    assert other.acquire(OP, account="c", ip="1") is not None  # the address is full
    assert other.acquire(OP, account="c", ip="2") is None  # another address is not limited


def test_operations_are_counted_separately() -> None:
    limiter = _limiter(Clock(), account_limit=1, ip_limit=1)
    assert limiter.acquire("op-one", account="a", ip="1") is None
    assert limiter.acquire("op-two", account="a", ip="1") is None
    assert limiter.acquire("op-one", account="a", ip="1") is not None


def test_a_refused_call_charges_neither_bucket() -> None:
    limiter = _limiter(Clock(), account_limit=1, ip_limit=2)
    assert limiter.acquire(OP, account="a", ip="1") is None
    for _ in range(10):  # refused by the account bucket: the address bucket must not fill up
        assert limiter.acquire(OP, account="a", ip="1") is not None
    assert limiter.acquire(OP, account="b", ip="1") is None  # the address held one hit only
    assert limiter.acquire(OP, account="c", ip="1") is not None  # now it holds two


def test_retry_after_is_an_int_of_at_least_one_and_shrinks_with_time() -> None:
    clock = Clock()
    limiter = _limiter(clock, account_limit=1)
    assert limiter.acquire(OP, account="a", ip="1") is None
    first = limiter.acquire(OP, account="a", ip="1")
    clock.now += 20.0
    later = limiter.acquire(OP, account="a", ip="1")
    clock.now += 39.5
    last = limiter.acquire(OP, account="a", ip="1")
    assert (first, later, last) == (60, 40, 1)
    assert all(isinstance(value, int) for value in (first, later, last))


def test_retry_after_is_the_longest_wait_when_both_buckets_refuse() -> None:
    clock = Clock()
    limiter = _limiter(clock, account_limit=1, ip_limit=2, window=60)
    assert limiter.acquire(OP, account="a", ip="1") is None  # t=0: account a, address 1
    clock.now += 30.0
    assert limiter.acquire(OP, account="b", ip="1") is None  # t=30: account b, address 1 is full
    clock.now += 10.0  # t=40
    # Both refuse: account b frees at t=90 (50 s), address 1 at t=60 (20 s): the longer wins.
    assert limiter.acquire(OP, account="b", ip="1") == 50
    # Only the address refuses (account c is fresh): its own wait.
    assert limiter.acquire(OP, account="c", ip="1") == 20
    # Only the account refuses (address 2 is fresh): its own wait.
    assert limiter.acquire(OP, account="b", ip="2") == 50


def test_the_buckets_are_bounded_by_the_key_cap() -> None:
    clock = Clock()
    limiter = _limiter(clock, max_keys=8)
    for index in range(5000):
        limiter.acquire(OP, account=f"account-{index}", ip=f"ip-{index}")
    assert limiter.tracked_keys() == (8, 8)
    assert MAX_TRACKED_KEYS == 1024
    default = SlidingWindowLimiter(clock=clock)
    for index in range(5000):
        default.acquire(OP, account=f"account-{index}", ip=f"ip-{index}")
    assert default.tracked_keys() == (1024, 1024)


def test_one_bucket_never_holds_more_than_its_limit() -> None:
    limiter = _limiter(Clock(), account_limit=3)
    for _ in range(50):
        limiter.acquire(OP, account="a", ip="1")
    hits = limiter._accounts[(OP, "a")]
    assert len(hits) == 3


def test_threads_admit_exactly_the_limit() -> None:
    limiter = SlidingWindowLimiter(account_limit=7, ip_limit=1000, window_seconds=3600)
    barrier = Barrier(40)
    results: list[int | None] = []

    def attempt() -> None:
        barrier.wait(timeout=30)
        results.append(limiter.acquire(OP, account="a", ip="1"))

    threads = [Thread(target=attempt) for _ in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert len(results) == 40
    assert results.count(None) == 7
    assert all(isinstance(value, int) and value >= 1 for value in results if value is not None)


def test_invalid_limits_are_refused() -> None:
    for kwargs in ({"account_limit": 0}, {"ip_limit": 0}, {"window_seconds": 0}, {"max_keys": 0}):
        with pytest.raises(ValueError):
            SlidingWindowLimiter(**kwargs)  # type: ignore[arg-type]


# ------------------------------------------------------------------ the call site
def test_the_gate_call_uses_the_account_and_the_address_only() -> None:
    source = inspect.getsource(be1_registry._charge_profile_gate)
    assert "principal.subject" in source and "request.client" in source
    for forbidden in ("child_id", "consent_id", "payload", "display_name"):
        assert forbidden not in source
    assert "x-forwarded" not in source.lower() and "request.headers" not in source


def _principal() -> VerifiedPrincipal:
    return VerifiedPrincipal(subject="synthetic-teacher", issuer="i", roles=frozenset())


def _runtime(limiter: SlidingWindowLimiter) -> Be1Runtime:
    return cast(
        Be1Runtime,
        SimpleNamespace(
            settings=SimpleNamespace(profile_receipt_hmac_key=SecretStr("k" * 40)),
            profile_gate_limiter=limiter,
        ),
    )


def test_a_request_without_a_client_shares_one_bucket_and_never_raises_attribute_error() -> None:
    limiter = SlidingWindowLimiter(account_limit=100, ip_limit=2, window_seconds=60)
    runtime = _runtime(limiter)
    no_client = Request({"type": "http", "headers": []})
    assert no_client.client is None
    be1_registry._charge_profile_gate(runtime, no_client, _principal())
    other = VerifiedPrincipal(subject="another", issuer="i", roles=frozenset())
    be1_registry._charge_profile_gate(runtime, no_client, other)
    with pytest.raises(HTTPException) as caught:
        be1_registry._charge_profile_gate(
            runtime, Request({"type": "http", "headers": []}), _principal()
        )
    assert caught.value.status_code == 429


def test_the_refusal_is_a_429_with_retry_after_and_the_rate_limited_code() -> None:
    limiter = SlidingWindowLimiter(account_limit=1, ip_limit=10, window_seconds=60)
    runtime = _runtime(limiter)
    request = Request({"type": "http", "headers": [], "client": ("203.0.113.9", 4000)})
    be1_registry._charge_profile_gate(runtime, request, _principal())
    with pytest.raises(HTTPException) as caught:
        be1_registry._charge_profile_gate(runtime, request, _principal())
    assert caught.value.status_code == 429
    assert cast(dict[str, str], caught.value.detail) == {"code": "RATE_LIMITED"}
    headers = caught.value.headers or {}
    assert headers["Retry-After"].isdigit() and int(headers["Retry-After"]) >= 1
    # A forwarded header is ignored: the address bucket is the peer's.
    spoofed = Request(
        {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"198.51.100.1")],
            "client": ("203.0.113.9", 4000),
        }
    )
    with pytest.raises(HTTPException):
        be1_registry._charge_profile_gate(runtime, spoofed, _principal())
