"""Candidate own09 lifecycle UoW/current owner notice boundaries, CR09-01 OPEN."""

from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from typing import Literal, Protocol

from sketch2life.application.ports.video_review_write import ReviewWriteContext
from sketch2life.domain.knowledge_video.model import VideoError, canonical_digest
from sketch2life.domain.video_review.lifecycle import ReviewChange, ReviewChangeRequest
from sketch2life.domain.video_review.model import ReviewHead


def change_fingerprint(context: ReviewWriteContext, request: ReviewChangeRequest) -> str:
    context, request = replace(context), replace(request)
    return canonical_digest(
        {
            "schema": "BE2-09.ReviewChange/0.1-candidate",
            "principal": context.principal_id,
            "org": context.organization_id,
            "session": context.session_id,
            "video": context.video_id,
            "expected_review_revision": context.expected_review_revision,
            "action": request.action.value,
            "reason": request.reason.value,
            "target": request.target.digest() if request.target is not None else None,
        }
    )


@dataclass(frozen=True, slots=True)
class ReviewChangeReceipt:
    context: ReviewWriteContext
    request: ReviewChangeRequest
    change: ReviewChange

    def __post_init__(self) -> None:
        if (
            type(self.context) is not ReviewWriteContext
            or type(self.request) is not ReviewChangeRequest
            or type(self.change) is not ReviewChange
        ):
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE_RECEIPT")
        context, request, change = (
            replace(self.context),
            replace(self.request),
            replace(self.change),
        )
        subject = change.before.subject
        if (
            context.organization_id,
            context.session_id,
            context.video_id,
            context.principal_id,
            context.expected_review_revision,
        ) != (
            subject.organization_id,
            subject.audience.session_id,
            subject.video_id,
            change.principal_id,
            change.before.revision,
        ) or request != change.request:
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE_RECEIPT")


class ReviewLifecycleAccess(Protocol):
    def resolve(self, context: ReviewWriteContext, request: ReviewChangeRequest) -> ReviewHead:
        """Resolve current canonical09 head/current ready08 target lineage and exact
        authenticated source/policy/audience notice. Request target not authority.
        No fabricated consent for generic media. Existing history never imported.
        """
        ...

    def check(
        self, receipt: ReviewChangeReceipt, phase: Literal["prepare", "commit", "replay"]
    ) -> None:
        """Actual authorized source-owner/current Teacher action as applicable,
        org/session/subject/source/moderation/recall/policy/deadline guards. Rebind
        from revoked/stale target requires separate CURRENT new-target eligibility;
        historical effective flag is insufficient. Replay authenticates original
        operation but grants no permission to use old or new media. Hold actual
        invalidation/dispatch/fetch fences through own commit, no network/outer
        lock acquisition inside transaction checks. Don't broaden policy epochs.
        """
        ...


class ReviewLifecycleBoundary(Protocol):
    def guard(
        self, context: ReviewWriteContext
    ) -> AbstractContextManager[ReviewLifecycleAccess]: ...


class ReviewLifecycleTransaction(Protocol):
    def head(self) -> ReviewHead | None: ...

    def change_receipt(self, principal_id: str, client_key: str) -> ReviewChangeReceipt | None: ...

    def change(self, receipt: ReviewChangeReceipt) -> None:
        """One own scoped CAS UoW: immutable before/archived/after history, new
        canonical head, unique actor/key/body receipt +audit/outbox invalidation
        notice. Review-write and change keys MUST share a namespace (or conflict
        across operation kinds), preventing a key from executing two operations.
        Preserve original24 review entries/receipts; never rewrite08/BE1 rows.
        Actual start and fetch/range/resume must observe adopted revocation fence,
        not just eventual delivery. No false claim existing player was stopped.
        """
        ...


class ReviewLifecycleStore(Protocol):
    def transaction(
        self, organization_id: str, session_id: str, video_id: str
    ) -> AbstractContextManager[ReviewLifecycleTransaction]: ...
