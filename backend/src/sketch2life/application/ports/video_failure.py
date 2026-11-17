"""Owned10 candidate ports. Actual owner/budget/session/checkpoint adoption OPEN."""

from contextlib import AbstractContextManager
from typing import Literal, Protocol

from sketch2life.domain.video_failure.model import (
    Choice,
    Context,
    EffectReceipt,
    FailureTarget,
    Intent,
    RetryAuthorization,
)

Phase = Literal["prepare", "commit_intent", "dispatch", "recover", "record_receipt"]


class FailureAccess(Protocol):
    def resolve(self, context: Context, choice: Choice) -> FailureTarget:
        """Authenticate final01/08 failure/current source/context/history/policy.
        Missing/queued/running/retryable/unsafe/cancelled not exhaustion. NOT a client
        assertion or stale09 approved artifact. CR10-01 authenticates projection.
        """
        ...

    def authorize_retry(self, context: Context, target: FailureTarget) -> RetryAuthorization:
        """Current bounded authorization from14/01/08; no reservation implied by
        eligibility alone. Actual bridge must consume same proof exactly once with
        new-run submission, rechecking expiry/current budget/kill/purpose/rights.
        Never authorize from retry_authorization_note. CR10-03 remains OPEN.
        """
        ...

    def check(self, intent: Intent, phase: Phase) -> None:
        """Actual Teacher action/session current nonterminal control, exact failure/
        source/audience/policy/purpose-specific consent/rights/profile. Hold fences
        through commit/effect; dispatch verifies expected session revision and retry
        authorization currentness. recover/record authenticate historical recovery
        scope, not a new effect or revival of current eligibility. No network or
        outer-lock acquisition in own UoW; late result/dispatch fenced by owners.
        """
        ...


class FailureBoundary(Protocol):
    def guard(self, context: Context) -> AbstractContextManager[FailureAccess]:
        """Pre-acquire real owner fences before own store lock; no default binding.
        Missing current authority fails closed. Cross-owner adoption CR10-01/02/03.
        """
        ...


class FailureTransaction(Protocol):
    def get(self, principal_id: str, client_key: str) -> Intent | None: ...

    def insert(self, intent: Intent) -> None:
        """Atomic pending intent+history+event +unique claim over failed lifecycle,
        not just per-key unique. Different actors/actions cannot both win. Unique
        loser rolls back, no effect. No08/01/BE1 writes or terminal resets.
        """
        ...

    def save(self, intent: Intent, *, expected_revision: int) -> None:
        """Only exact original pending1->receipt2; CAS/history/event in same UoW."""
        ...


class FailureStore(Protocol):
    def transaction(
        self, organization_id: str, session_id: str
    ) -> AbstractContextManager[FailureTransaction]: ...


class FailureBridge(Protocol):
    def execute(self, intent: Intent) -> EffectReceipt:
        """Outside10 DB tx, ORIGINAL key/body; current owner fences valid at effect.
        Retry atomically consumes bounded authorization +deduplicated new01/08
        lifecycle (new video/job IDs, same content version, queued/pending review).
        Skip explicit permitted stage only; end early outcome+checkpoint ACK.
        Receipt authenticated at this port, not trusted due to booleans/type alone.
        Actual adopted atomic/recoverable protocol required; sequential commits are
        not atomic. No automatic compensation/reset/approval/late-result autoplay.
        """
        ...

    def lookup(self, intent: Intent) -> EffectReceipt | None:
        """Original authenticated outcome lookup; None known absent, outage raises.
        Neither permits auto resend/new key. Explicit adopter reconciliation required.
        """
        ...
