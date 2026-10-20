"""Video-specific original copy control; no permissive actual provider binding."""

from contextlib import AbstractContextManager
from typing import Protocol

from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyHookResponse
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope
from sketch2life.contracts.schemas.knowledge_video_copy import VideoCopyJournalEntry


class VideoCopyHookAccess(Protocol):
    def original(self, envelope: CopyOperationEnvelope) -> VideoCopyJournalEntry:
        """Authenticate immutable journal/source bytes against exact target, original
        video/job/attempt/pin/media key, original profile version/hash and subject.
        Never latest alias, caller-asserted provenance or worker teaching consent.
        Includes stopped/terminal original attempts; cleanup is not generation.
        """
        ...

    def confirm(self, envelope: CopyOperationEnvelope, entry: VideoCopyJournalEntry) -> None:
        """Current adopted BE1 data-request authority, original profile/source and
        persisted BE2-14 delivery claim/deadline. Historical envelope is NOT grant.
        Hold generation-safe scope and actual accepted-artifact protection through
        effect; no broad purge/new-epoch cancellation or exposure grant. No DB tx
        across provider call. Actual race/deadline enforcement is adopter duty.
        """
        ...


class VideoCopyHookBoundary(Protocol):
    def guard(self, envelope: CopyOperationEnvelope) -> AbstractContextManager[VideoCopyHookAccess]:
        """Authenticated backend delivery only; cannot be replaced by an ops-role
        check or initial_authority.allowed. Pre-acquire correct owner/source guards.
        No default implementation; actual composition with14 remains gated.
        """
        ...


class VideoCopyControl(Protocol):
    def dispatch(
        self, envelope: CopyOperationEnvelope, original: VideoCopyJournalEntry
    ) -> CopyHookResponse:
        """Cancel/purge only exact ORIGINAL registered copy/profile. Use original
        envelope.operation_key and body for durable external dedup, including
        restart/lost ACK; conflict changed body, no automatic fallback/new key.
        No DB tx here. Bound runtime/timeouts are explicit provider selection duties.
        Return reference-only pending/unsupported/exception/receipt_available;
        receipt availability is NOT verification, cancellation or deletion.
        Accepted references require actual authority fences, not guessed cleanup.
        """
        ...
