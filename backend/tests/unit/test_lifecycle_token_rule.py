"""Receipt token rule T1-T7 and every crash point of DTR Draft 6 §5.1 and §10.

Each crash scenario kills the worker (a ``BaseException``) at one point of one step, lets the
lease expire, reruns, and compares the four persisted entries and the final ``sha256`` with a
crash-free run (``orph`` is ignored, T6).
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from sketch2life.application.ports.story_run_lifecycle import canonical_json, sha256_hex
from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
    LifecycleToken,
    LifecycleTokenError,
    TokenEntry,
    final_token,
    flip,
    plan_entry,
    write_pending,
)
from tests.unit.test_be1_lifecycle_consumer import (
    COMPLETED_PATTERN,
    Crash,
    Harness,
    make_harness,
)

H16 = "0123456789abcdef"


def _entry(step: str, status: str = "p", count: int = 1, p8: str = "aaaaaaaa") -> TokenEntry:
    return TokenEntry(step, status, count, H16, p8)


# ------------------------------------------------------------------------------ pure rules
def test_t1_entry_values_come_from_the_sorted_identifier_list() -> None:
    entry = plan_entry("story", ["run:b", "receipt:a"])
    ordered = ["receipt:a", "run:b"]
    assert entry.count == 2
    assert entry.h16 == sha256_hex(canonical_json(ordered))[:16]
    assert entry.p8 == sha256_hex(canonical_json({"step": "story", "ids": ordered}))[:8]
    empty = plan_entry("upload", [])
    assert (empty.count, empty.h16) == (0, sha256_hex("[]")[:16])
    with pytest.raises(LifecycleTokenError):
        plan_entry("asset", [])  # the asset entry comes from the Core plan facts


def test_entries_are_inserted_at_their_fixed_position_whatever_the_write_order() -> None:
    token = LifecycleToken()
    for step in ("story", "ai", "upload"):
        written = write_pending(token, _entry(step), plan_empty=False)
        assert written is not None
        token = written
    written = write_pending(token, _entry("asset"), plan_empty=False)
    assert written is not None
    rendered = written.render()
    assert [part.split("=")[0] for part in rendered.split(";")[1:]] == [
        "upload",
        "ai",
        "asset",
        "story",
    ]
    assert LifecycleToken.parse(rendered) == written


def test_t3_an_empty_plan_never_overwrites_and_a_verified_entry_is_never_rewritten() -> None:
    token = LifecycleToken().with_entry(_entry("upload", p8="11111111"))
    assert write_pending(token, _entry("upload", count=0, p8="22222222"), plan_empty=True) is None
    assert write_pending(token, _entry("upload", p8="11111111"), plan_empty=False) is None
    replaced = write_pending(token, _entry("upload", count=3, p8="33333333"), plan_empty=False)
    assert replaced is not None and replaced.entries["upload"].count == 3
    verified = flip(token, "upload")
    rewrite = _entry("upload", count=9, p8="44444444")
    assert write_pending(verified, rewrite, plan_empty=False) is None
    empty_first = write_pending(LifecycleToken(), _entry("asset", count=0), plan_empty=True)
    assert empty_first is not None  # with no entry, an empty plan writes p:0


def test_t4_the_flip_keeps_the_recorded_values() -> None:
    token = LifecycleToken().with_entry(_entry("ai", count=1, p8="12345678"))
    flipped = flip(token, "ai")
    assert flipped.entries["ai"] == TokenEntry("ai", "v", 1, H16, "12345678")
    assert flip(flipped, "ai") == flipped
    with pytest.raises(LifecycleTokenError):
        flip(LifecycleToken(), "story")


def test_t6_the_final_string_hashes_the_four_persisted_segments() -> None:
    token = LifecycleToken()
    for step in ("upload", "ai", "asset", "story"):
        token = flip(token.with_entry(_entry(step, count=0 if step == "upload" else 1)), step)
    final = final_token(token, 3)
    persisted = token.render().split(";", 1)[1]
    assert final == f"lcr1;{persisted};sha256={sha256_hex(persisted)};orph=3"
    assert re.fullmatch(COMPLETED_PATTERN, final)
    parsed = LifecycleToken.parse(final)
    assert parsed.sha256 == sha256_hex(persisted) and parsed.orph == 3
    with pytest.raises(LifecycleTokenError):
        final_token(parsed, 0)  # already final
    missing = LifecycleToken().with_entry(_entry("upload", status="v"))
    with pytest.raises(LifecycleTokenError):
        final_token(missing, 0)
    pending = token.with_entry(_entry("story"))
    with pytest.raises(LifecycleTokenError):
        final_token(pending, 0)


@pytest.mark.parametrize(
    "text",
    (
        "lcr2",
        "lcr1;ai=p:1:" + H16 + "@aaaaaaaa;upload=p:1:" + H16 + "@aaaaaaaa",  # order
        "lcr1;upload=x:1:" + H16 + "@aaaaaaaa",
        "lcr1;upload=p:1:" + H16.upper() + "@aaaaaaaa",
        "lcr1;orph=1",
        "lcr1;upload=p:1:" + H16 + "@aaaaaaaa;upload=p:1:" + H16 + "@aaaaaaaa",
    ),
)
def test_a_malformed_token_is_refused(text: str) -> None:
    with pytest.raises(LifecycleTokenError):
        LifecycleToken.parse(text)


# ------------------------------------------------------------------------------ crash matrix
class _CrashingReceipts:
    """Kill the worker on the CAS that writes a step entry (pending) or flips it."""

    def __init__(self, harness: Harness, step: str, phase: str, when: str) -> None:
        self._inner = harness.receipts
        self._step, self._phase, self._when = step, phase, when
        self._armed = True
        harness.consumer._receipts = self  # type: ignore[assignment]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def compare_and_set(self, **kwargs: Any) -> bool:
        old = LifecycleToken.parse(kwargs["expected_result_ref"])
        new = LifecycleToken.parse(kwargs["result_ref"])
        before, after = old.entries.get(self._step), new.entries.get(self._step)
        hit = (
            self._armed
            and after is not None
            and after != before
            and after.status == ("p" if self._phase == "pending" else "v")
        )
        if hit and self._when == "before":
            self._armed = False
            raise Crash("before")
        result = bool(self._inner.compare_and_set(**kwargs))
        if hit and self._when == "after":
            self._armed = False
            raise Crash("after")
        return result


def _reference() -> LifecycleToken:
    harness = make_harness(uploads={"u1": "PENDING"})
    assert harness.consumer.run_once() == "completed"
    return harness.token()


def _finish(harness: Harness) -> LifecycleToken:
    outcomes = harness.run_until_idle()
    assert "crash" in outcomes or "deferred" in outcomes
    assert harness.receipt()["state"] == "completed", outcomes
    return harness.token()


def _same_as_reference(token: LifecycleToken, reference: LifecycleToken) -> None:
    assert token.segments() == reference.segments()
    assert token.sha256 == reference.sha256


@pytest.mark.parametrize("step", ("upload", "ai", "asset", "story"))
@pytest.mark.parametrize(
    ("phase", "when"),
    (
        ("pending", "before"),  # before the entry
        ("pending", "after"),  # after the entry, before the act
        ("verified", "before"),  # after the act, before the flip
        ("verified", "after"),  # after the flip
    ),
)
def test_every_crash_point_of_every_step_reruns_to_the_same_token(
    step: str, phase: str, when: str
) -> None:
    reference = _reference()
    harness = make_harness(uploads={"u1": "PENDING"})
    _CrashingReceipts(harness, step, phase, when)
    _same_as_reference(_finish(harness), reference)


@pytest.mark.parametrize(
    "point",
    (
        "upload.after_act",
        "ai.after_act",
        "story.after_act",
        "asset.after_objects",
        "asset.after_sweep",
        "asset.after_rows",
    ),
)
def test_a_crash_after_the_act_or_inside_the_asset_step_reruns_to_the_same_token(
    point: str,
) -> None:
    reference = _reference()
    harness = make_harness(uploads={"u1": "PENDING"})
    harness.world.crash_at = point
    _same_as_reference(_finish(harness), reference)


def test_a_failing_asset_verification_reruns_to_the_same_token() -> None:
    reference = _reference()
    harness = make_harness(uploads={"u1": "PENDING"})
    storage = harness.world.storage
    original = storage.list_keys
    calls = {"n": 0}

    def flaky(prefix: str) -> tuple[str, ...]:
        calls["n"] += 1
        if calls["n"] == 3:  # the step-3 verification listing (after the two sweep listings)
            return (f"{prefix}not-yet-deleted",)
        return original(prefix)

    storage.list_keys = flaky  # type: ignore[method-assign]
    _same_as_reference(_finish(harness), reference)


def test_a_run_without_artwork_ends_with_an_empty_verified_asset_entry_after_a_crash() -> None:
    harness = make_harness(artwork=False)
    harness.world.crash_at = "asset.after_sweep"
    token = _finish(harness)
    assert token.entries["asset"].render().startswith("asset=v:0:" + sha256_hex("[]")[:16])


def test_the_canonical_string_hashed_is_the_persisted_four_segments() -> None:
    token = _reference()
    persisted = ";".join(token.segments())
    assert token.sha256 == sha256_hex(persisted)
