"""Controlled lifecycle purge of one managed BE1 profile (T-12b-fix, SRS FR-C-10 and BR-35).

The work is done by the SQL function ``public.be1_purge_profile`` (migration
``20261123_ppg_0001``): it deletes the support needs, the synthetic eligibility proofs, the
immutable revisions, the command receipts that belong to the child and the profile row inside the
caller's transaction. It does NOT purge the other child-keyed tables (enrollments, consent
records, group memberships, turns, observations, device-grant admitted ids) or decide audit
retention: those stay with the FR-C-10 lifecycle executor (open item). The function holds the
only door through the append-only triggers: it sets a transaction-local setting that names the
one child being purged.

This module does not commit and does not decide *when* a profile is deleted (the FR-C-08 lifecycle
executor does not call it yet). The answer holds counts only, never a name or another value.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class ProfilePurgeCounts:
    profiles: int
    revisions: int
    support_needs: int
    proofs: int
    receipts: int

    @property
    def purged(self) -> bool:
        return self.profiles > 0


def purge_managed_profile(
    db: Session, *, organization_id: str, child_id: str
) -> ProfilePurgeCounts:
    """Purge the BE1 profile in ``organization_id`` with its revisions, support needs and receipts.

    Idempotent: an unknown profile returns zero counts. The caller commits (or rolls back).
    """
    row = db.execute(
        text("SELECT public.be1_purge_profile(:organization_id, :child_id)"),
        {"organization_id": organization_id, "child_id": child_id},
    ).scalar_one()
    return ProfilePurgeCounts(
        profiles=int(row["profiles"]),
        revisions=int(row["revisions"]),
        support_needs=int(row["support_needs"]),
        proofs=int(row["proofs"]),
        receipts=int(row["receipts"]),
    )
