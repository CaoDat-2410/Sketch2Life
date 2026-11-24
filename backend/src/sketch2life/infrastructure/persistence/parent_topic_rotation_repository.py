"""PostgreSQL adapter for durable, account-scoped Parent card rotation."""

from __future__ import annotations

import hashlib
import hmac
import json
import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_topic_rotation import (
    ParentTopicRotationAllocation,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentTopicRotationReceiptModel,
    ParentTopicRotationStateModel,
)


class SqlParentTopicRotationRepository:
    """Serialize per-account allocations and persist replayable card batches."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def allocate(
        self,
        *,
        account_id: str,
        request_id: UUID,
        draft_id: UUID,
        rotation_kind: str,
        scope_id: str,
        catalog_revision: str,
        candidate_ids: tuple[str, ...],
        request_fingerprint: str,
        batch_size: int = 3,
    ) -> ParentTopicRotationAllocation:
        if (
            rotation_kind not in {"TOPIC", "SUBJECT"}
            or not account_id
            or not scope_id
            or len(candidate_ids) < batch_size
            or len(candidate_ids) % batch_size != 0
            or len(candidate_ids) != len(set(candidate_ids))
        ):
            raise ValueError("PARENT_TOPIC_ROTATION_INPUT_INVALID")
        try:
            fingerprint_bytes = bytes.fromhex(request_fingerprint)
        except ValueError:
            raise ValueError("PARENT_TOPIC_ROTATION_FINGERPRINT_INVALID") from None
        if len(fingerprint_bytes) != 32:
            raise ValueError("PARENT_TOPIC_ROTATION_FINGERPRINT_INVALID")

        self._lock_account(account_id)
        receipt = self._session.scalar(
            select(ParentTopicRotationReceiptModel).where(
                ParentTopicRotationReceiptModel.account_id == account_id,
                ParentTopicRotationReceiptModel.request_id == request_id,
            )
        )
        if receipt is not None:
            if not hmac.compare_digest(receipt.request_fingerprint, fingerprint_bytes):
                raise ValueError("PARENT_TOPIC_ROTATION_IDEMPOTENCY_CONFLICT")
            return ParentTopicRotationAllocation(
                request_id=request_id,
                draft_id=receipt.draft_id,
                catalog_revision=receipt.catalog_revision,
                cycle_number=receipt.cycle_number,
                set_id=receipt.set_id,
                selected_ids=tuple(receipt.selected_ids),
                replayed=True,
            )

        state = self._session.scalar(
            select(ParentTopicRotationStateModel)
            .where(
                ParentTopicRotationStateModel.account_id == account_id,
                ParentTopicRotationStateModel.catalog_revision == catalog_revision,
                ParentTopicRotationStateModel.rotation_kind == rotation_kind,
                ParentTopicRotationStateModel.scope_id == scope_id,
            )
            .with_for_update()
        )
        now = datetime.now(UTC)
        if state is None:
            ordered_ids = list(candidate_ids)
            random.SystemRandom().shuffle(ordered_ids)
            state = ParentTopicRotationStateModel(
                rotation_state_id=uuid4(),
                account_id=account_id,
                catalog_revision=catalog_revision,
                rotation_kind=rotation_kind,
                scope_id=scope_id,
                ordered_ids=ordered_ids,
                cycle_number=1,
                cursor_position=0,
                updated_at=now,
            )
            self._session.add(state)
            self._session.flush()
        elif set(state.ordered_ids) != set(candidate_ids):
            raise ValueError("PARENT_TOPIC_ROTATION_CATALOG_MISMATCH")

        if state.cursor_position + batch_size > len(state.ordered_ids):
            state.cycle_number += 1
            state.cursor_position = 0
            state.ordered_ids = list(candidate_ids)
            random.SystemRandom().shuffle(state.ordered_ids)

        selected_ids = tuple(
            state.ordered_ids[state.cursor_position : state.cursor_position + batch_size]
        )
        cycle_number = state.cycle_number
        set_material = json.dumps(
            [account_id, catalog_revision, rotation_kind, scope_id, cycle_number, selected_ids],
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
        prefix = "pts" if rotation_kind == "TOPIC" else "pds"
        set_id = f"{prefix}_{hashlib.sha256(set_material).hexdigest()[:24]}"
        state.cursor_position += batch_size
        state.updated_at = now
        self._session.add(
            ParentTopicRotationReceiptModel(
                rotation_receipt_id=uuid4(),
                account_id=account_id,
                request_id=request_id,
                draft_id=draft_id,
                catalog_revision=catalog_revision,
                rotation_kind=rotation_kind,
                scope_id=scope_id,
                request_fingerprint=fingerprint_bytes,
                cycle_number=cycle_number,
                set_id=set_id,
                selected_ids=list(selected_ids),
                created_at=now,
            )
        )
        self._session.flush()
        return ParentTopicRotationAllocation(
            request_id=request_id,
            draft_id=draft_id,
            catalog_revision=catalog_revision,
            cycle_number=cycle_number,
            set_id=set_id,
            selected_ids=selected_ids,
            replayed=False,
        )

    def _lock_account(self, account_id: str) -> None:
        digest = hashlib.sha256(f"parent-topic-rotation:{account_id}".encode("ascii")).digest()
        lock_key = int.from_bytes(digest[:8], "big", signed=True)
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
        )


__all__ = ["SqlParentTopicRotationRepository"]
