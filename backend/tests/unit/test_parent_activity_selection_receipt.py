"""The stored selection receipt is JSON: its ISO timestamp must validate (it answered 500)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sketch2life.contracts.schemas.parent_activity_selection import (
    ParentActivitySelectionReceiptV1,
)


def test_receipt_accepts_the_json_body_the_repository_stores() -> None:
    now = datetime(2026, 11, 26, 8, 0, tzinfo=UTC)

    receipt = ParentActivitySelectionReceiptV1.model_validate(
        {
            "contract": "ParentActivitySelectionReceiptV1",
            "request_id": str(uuid4()),
            "story_run_id": str(uuid4()),
            "suggestion_set_id": str(uuid4()),
            "activity_selection_id": str(uuid4()),
            "selection_revision": 1,
            "understanding_revision": 1,
            "activity_index": 0,
            "activity_snapshot_sha256": "a" * 64,
            "persisted_at": now.isoformat(),
        }
    )

    assert receipt.persisted_at == now
