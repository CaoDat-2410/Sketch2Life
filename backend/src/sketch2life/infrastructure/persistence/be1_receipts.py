"""Receipt purge for a child (FEAT-066 T-7c-fix, O-1; SRS FR-C-10 l.502, BR-35 l.279).

The profile create and move receipts keep the child id in ``response_json`` (and the create
receipt keeps a keyed fingerprint of the name and age). This helper deletes those rows for one
child so a future deletion path can purge them. It is deliberately NOT wired to any route: the
role and route that delete a Teacher-managed profile are OPEN (l.502, OD-06, X-19).

Notes for the future wiring: the predicate reads ``response_json->>'child_id'`` (no index, one
scan per call, acceptable for a rare operation); after a purge a retry with the same
Idempotency-Key is a new command, so the deleting route must reject or tombstone the old keys;
the caller owns the transaction (no commit here).
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel


def purge_child_receipts(db: Session, organization_id: str, child_id: str) -> int:
    """Delete the command receipts of one organization that reference ``child_id``."""
    result = db.execute(
        delete(Be1CommandReceiptModel).where(
            Be1CommandReceiptModel.organization_id == organization_id,
            Be1CommandReceiptModel.response_json["child_id"].astext == child_id,
        )
    )
    return int(getattr(result, "rowcount", 0) or 0)
