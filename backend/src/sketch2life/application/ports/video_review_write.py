"""Owned09 CMD-41 held authority and atomic review/history/receipt ports; adopters OPEN."""

from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from typing import Literal, Protocol

from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    ExactContentReviewRecordV1,
)
from sketch2life.domain.knowledge_video.model import (
    VideoError,
    require_hash,
    require_id,
    require_revision,
)
from sketch2life.domain.video_review.model import ReviewEntry, ReviewHead


@dataclass(frozen=True, slots=True)
class ReviewWriteContext:
    """Server identity/authorized target + HTTP review If-Match, not body authority."""

    principal_id: str
    organization_id: str
    session_id: str
    video_id: str
    client_key: str
    expected_review_revision: int

    def __post_init__(self) -> None:
        for item in (
            self.principal_id,
            self.organization_id,
            self.session_id,
            self.video_id,
            self.client_key,
        ):
            require_id(item)
        require_revision(self.expected_review_revision)


@dataclass(frozen=True, slots=True)
class ReviewWriteSnapshot:
    head: ReviewHead
    policy_version: str

    def __post_init__(self) -> None:
        if type(self.head) is not ReviewHead:
            raise VideoError("VIDEO_REVIEW_INVALID_HEAD")
        replace(self.head)
        require_id(self.policy_version)


@dataclass(frozen=True, slots=True)
class ReviewWriteReceipt:
    context: ReviewWriteContext
    fingerprint: str
    entry: ReviewEntry
    record: ExactContentReviewRecordV1

    def __post_init__(self) -> None:
        if type(self.context) is not ReviewWriteContext or type(self.entry) is not ReviewEntry:
            raise VideoError("VIDEO_REVIEW_INVALID_RECEIPT")
        context, entry = replace(self.context), replace(self.entry)
        require_hash(self.fingerprint)
        try:
            record = ExactContentReviewRecordV1.model_validate(
                self.record.model_dump(mode="python"), strict=True
            )
        except (TypeError, ValueError, AttributeError):
            raise VideoError("VIDEO_REVIEW_INVALID_RECEIPT") from None
        if (
            (
                entry.subject.organization_id,
                entry.subject.audience.session_id,
                entry.subject.video_id,
                entry.reviewer_id,
            )
            != (context.organization_id, context.session_id, context.video_id, context.principal_id)
            or entry.revision != context.expected_review_revision + 1
            or (
                record.review_id,
                record.review_revision,
                record.reviewer_principal_id,
                record.reviewed_at,
                record.state,
            )
            != (entry.review_id, entry.revision, entry.reviewer_id, entry.recorded_at, "effective")
        ):
            raise VideoError("VIDEO_REVIEW_INVALID_RECEIPT")
        object.__setattr__(self, "record", record)


class ReviewWriteAccess(Protocol):
    def resolve(
        self, context: ReviewWriteContext, command: ExactContentReviewCommandV1
    ) -> ReviewWriteSnapshot:
        """Authenticate exact ready08 artifact/pin/source/context and current
        resolved audience subset/purpose-specific consent/policy; canonical09 head
        from adopted CR09-01. Initial revision explicit, NEVER guessed from job/run.
        Existing external canonical entry without matching own rows must not be
        silently imported/overwritten. No DB writes/network inside own UoW.
        """
        ...

    def check(
        self,
        context: ReviewWriteContext,
        command: ExactContentReviewCommandV1,
        snapshot: ReviewWriteSnapshot,
        phase: Literal["prepare", "commit", "replay"],
    ) -> None:
        """Actual current action-specific Teacher/org/session/grant/rights and
        moderation (approve requires passed), publication/recall/profile/source/
        audience/consent/deadline fences. Replay reauthorizes, never a cached grant.
        All commit/replay checks use already-held guards, no outer lock acquisition
        or network under own transaction. Fence invalidation through actual commit.
        """
        ...


class ReviewWriteBoundary(Protocol):
    def guard(self, context: ReviewWriteContext) -> AbstractContextManager[ReviewWriteAccess]:
        """Pre-acquire actual BE1/07/08/14/current review/subject owner fences,
        held through own transaction commit. Missing adoption fails closed; neither
        role name, mutex nor precheck alone constitutes durable authorization.
        """
        ...


class ReviewWriteTransaction(Protocol):
    def head(self) -> ReviewHead | None: ...

    def receipt(self, principal_id: str, client_key: str) -> ReviewWriteReceipt | None: ...

    def write(
        self, before: ReviewHead | None, after: ReviewHead, receipt: ReviewWriteReceipt
    ) -> None:
        """One scoped own UoW: CAS head, append immutable shared review/entry/history,
        unique actor/key/body receipt and audit/outbox. No overwrite or separate
        commit of review and receipt, no direct08/BE1 writes. Concurrent unique/CAS
        loser rolls back wholly; no implicit application retry/new operation key.
        """
        ...


class ReviewWriteStore(Protocol):
    def transaction(
        self, organization_id: str, session_id: str, video_id: str
    ) -> AbstractContextManager[ReviewWriteTransaction]: ...
