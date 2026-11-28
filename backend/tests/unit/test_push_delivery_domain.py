from __future__ import annotations

from datetime import timedelta

import pytest

from sketch2life.domain.push_delivery import push_pointer, retry_delay


@pytest.mark.parametrize(
    ("attempt", "seconds"),
    ((1, 60), (2, 120), (3, 240), (4, 480), (5, 900), (6, 900), (1000, 900)),
)
def test_retry_delay_is_bounded_exponential(attempt: int, seconds: int) -> None:
    assert retry_delay(attempt) == timedelta(seconds=seconds)


@pytest.mark.parametrize("attempt", (0, -1, True))
def test_retry_delay_rejects_invalid_attempts(attempt: int) -> None:
    with pytest.raises(ValueError):
        retry_delay(attempt)


def test_pointer_has_only_the_three_content_free_fields() -> None:
    pointer = push_pointer("12345678-1234-1234-1234-123456789abc")

    assert pointer == {
        "v": 1,
        "kind": "INBOX_POINTER",
        "inbox_item_id": "12345678-1234-1234-1234-123456789abc",
    }
    assert set(pointer) == {"v", "kind", "inbox_item_id"}


@pytest.mark.parametrize("inbox_item_id", ("", "x" * 37, None))
def test_pointer_rejects_missing_or_oversized_item_ids(inbox_item_id: object) -> None:
    with pytest.raises(ValueError):
        push_pointer(inbox_item_id)  # type: ignore[arg-type]
