"""Candidate09 current-authority/intent/BE1 receipt adoption boundaries, CR09-02 OPEN."""

from contextlib import AbstractContextManager
from typing import Literal, Protocol

from sketch2life.domain.video_review.model import ReviewHead
from sketch2life.domain.video_review.playback import (
    PlaybackIntent,
    PlaybackReceipt,
    PlaybackRequest,
)

PlaybackPhase = Literal["prepare", "commit_intent", "dispatch", "recover", "record_receipt"]


class PlaybackAccess(Protocol):
    def review_head(self, request: PlaybackRequest) -> ReviewHead:
        """Resolve CURRENT canonical09 head/08 final bytes/pin/audience, not client
        assertions or stale cached projection. Actual adoption is CR09-01.
        """
        ...

    def check(self, intent: PlaybackIntent, phase: PlaybackPhase) -> None:
        """Actual action-specific Teacher/session/grant, source/moderation/recall/
        purpose-specific consent/audience/policy and deadlines. Hold invalidation/
        owner fences through intent commit/external effect. dispatch MUST verify
        exact expected session revision and effective review; no precheck-only race.
        recover/record_receipt authenticate original backend recovery scope, not
        current teaching eligibility; historical receipt is not live access grant.
        No network work/acquiring outer locks during own transaction confirmation.
        """
        ...


class PlaybackBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str, session_id: str
    ) -> AbstractContextManager[PlaybackAccess]:
        """No permissive binding. Pre-acquire actual subject/review/owner guards;
        hold through own UoW and authorized effect, no DB tx over provider calls.
        Access fetch/range/resume still reauthorize at actual BE1 gateway each use.
        """
        ...


class PlaybackTransaction(Protocol):
    def get(self, principal_id: str, client_key: str) -> PlaybackIntent | None: ...

    def insert(self, intent: PlaybackIntent) -> None:
        """Scoped unique key/body, atomic intent+audit/outbox. No duplicate dispatch.
        Concurrent loser rolls back then recovers under new authorized read.
        """
        ...

    def save(self, intent: PlaybackIntent, *, expected_revision: int) -> None:
        """Own CAS/immutable receipt/history/audit/outbox; NEVER mutates BE1 tables."""
        ...


class PlaybackStore(Protocol):
    def transaction(
        self, organization_id: str, session_id: str
    ) -> AbstractContextManager[PlaybackTransaction]: ...


class PlaybackBridge(Protocol):
    def lookup(self, intent: PlaybackIntent) -> PlaybackReceipt | None:
        """Authenticate original-scope receipt; None KNOWN absent, outage raises.
        Historical reference isn't current mediated access or playback permission.
        """
        ...

    def start(self, intent: PlaybackIntent) -> PlaybackReceipt:
        """Outside09 DB tx. Actual authorized BE1 atomic session/access effect+
        receipt using ORIGINAL operation key and exact body for durable dedup.
        Verify current expected session/review/source/audience/consent at effect,
        immutable same-key/body replay, conflict different body. No new grant TTL,
        raw URL, inferred session advance or sequential commits advertised atomic.
        Lost ACK requires lookup, NOT an automatic repeat. Binding remains OPEN.
        """
        ...
