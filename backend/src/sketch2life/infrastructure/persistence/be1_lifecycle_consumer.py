"""BE1 lifecycle consumer for the FR-C-08 StoryRun purge (DTR Draft 6 §5.1, §6.2-§6.3).

The consumer is the coordinator of the three owner modules. The run's own owner scope decides
the rows it writes: ``PARENT_ACCOUNT`` with no organization (unchanged), or ``ORGANIZATION`` with
``organization_id`` = the scope ref for a Teacher run (FEAT-066 T-13a). It claims one Story
lifecycle event from the Core outbox, keeps the BE1 receipt in ``be1_data_lifecycle_requests`` and
runs the purge steps through owner ports only:

0. insert the receipt if absent, then ``running``;
1. Core uploads that name the run (plan, close, verify);
2. the AI Jobs lifecycle notice (insert-if-absent, verify);
3. Core assets: closure, Story's cross-run answer, all-or-nothing plan, objects, sweep, Story
   re-ask, rows, verification. A retained plan writes no entry and runs no sweep;
4. Story content purge (one Story transaction);
5. ``verify_run_purged`` (sweep and re-verify once), then Story ``finalize_deleted``;
6. verify once more, then ``process_local_once`` whose effect writes the final token.

The receipt token (``result_ref``) follows rules T1-T7: every step writes a pending entry with
a compare-and-set before it acts and flips it to verified afterwards, keeping the recorded
values. Every receipt update is a compare-and-set on the previous ``state`` and ``result_ref``;
a zero-row update outside an effect stops the worker, inside an effect it raises so the outbox
transaction rolls back. Failed attempts set ``awaiting_external_purge`` and defer with a
doubling delay; the tenth claim does no purge work and records ``exception``.

The same module holds the SQL adapters for the BE1 receipt store and the insert-if-absent
lifecycle audit write. Only typed error codes are logged; never a key, a cause or a traceback.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, Final, cast

from sqlalchemy import Table, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.core_foundation import (
    ORGANIZATION_SCOPE_KIND,
    PARENT_SCOPE_KIND,
    CoreAssetPurgeError,
    LifecycleAuditWriterPort,
    LifecycleNoticePort,
    LifecycleOutboxPort,
    LifecycleReceipt,
    LifecycleReceiptStorePort,
    LifecycleScope,
    OutboxEnvelope,
    RunAssetPurgePlan,
    RunAssetPurgePort,
    RunUploadClosePort,
    validate_run_ref,
)
from sketch2life.application.ports.story_run_lifecycle import (
    AUDIT_EXCEPTION,
    AUDIT_RESOURCE_TYPE,
    LIFECYCLE_EVENT_TYPES,
    LIFECYCLE_WORKER_ACTOR,
    PURGE_STATES,
    RunAssetReferencePort,
    StoryLifecyclePort,
    canonical_json,
    lifecycle_exception_audit_id,
    lifecycle_request_id,
    lifecycle_target_ref,
    sha256_hex,
)
from sketch2life.infrastructure.persistence.be1_models import DataLifecycleRequestModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel

_LOGGER = logging.getLogger("sketch2life.be1.lifecycle")

STEPS: Final = ("upload", "ai", "asset", "story")
TOKEN_PREFIX: Final = "lcr1"
DEFAULT_CONSUMER_NAME: Final = "be1-lifecycle-consumer"
RETRY_BOUND: Final = 10
DEFAULT_LEASE_SECONDS: Final = 900
STEP_DEADLINE_SECONDS: Final = 300
NOTICE_REASON_CODE: Final = "PARENT_STORY_RUN_DELETED"
# T-13a (review note N2): the reason code names the scope that asked for the purge.
NOTICE_REASON_CODES: Final = {
    PARENT_SCOPE_KIND: NOTICE_REASON_CODE,
    ORGANIZATION_SCOPE_KIND: "TEACHER_STORY_RUN_DELETED",
}
_LIFECYCLE_SCOPE_KINDS: Final = frozenset({PARENT_SCOPE_KIND, ORGANIZATION_SCOPE_KIND})

_ENTRY = re.compile(r"^(upload|ai|asset|story)=([pv]):([0-9]+):([0-9a-f]{16})@([0-9a-f]{8})$")
_SHA = re.compile(r"^sha256=([0-9a-f]{64})$")
_ORPH = re.compile(r"^orph=([0-9]+)$")


# =============================================================================== token rule
class LifecycleTokenError(ValueError):
    """The persisted token does not follow DTR Draft 6 §5.1."""


@dataclass(frozen=True, slots=True)
class TokenEntry:
    step: str
    status: str  # "p" pending or "v" verified
    count: int
    h16: str
    p8: str

    def render(self) -> str:
        return f"{self.step}={self.status}:{self.count}:{self.h16}@{self.p8}"

    @property
    def verified(self) -> bool:
        return self.status == "v"


@dataclass(frozen=True, slots=True)
class LifecycleToken:
    entries: dict[str, TokenEntry] = field(default_factory=dict)
    sha256: str | None = None
    orph: int | None = None

    @classmethod
    def parse(cls, text: str | None) -> LifecycleToken:
        if text is None or text == "":
            return cls()
        parts = text.split(";")
        if parts[0] != TOKEN_PREFIX:
            raise LifecycleTokenError("TOKEN_PREFIX_INVALID")
        entries: dict[str, TokenEntry] = {}
        sha: str | None = None
        orph: int | None = None
        last_index = -1
        for part in parts[1:]:
            entry = _ENTRY.fullmatch(part)
            if entry is not None and sha is None:
                step = entry.group(1)
                index = STEPS.index(step)
                if step in entries or index <= last_index:
                    raise LifecycleTokenError("TOKEN_ORDER_INVALID")
                last_index = index
                entries[step] = TokenEntry(
                    step, entry.group(2), int(entry.group(3)), entry.group(4), entry.group(5)
                )
                continue
            sha_match = _SHA.fullmatch(part)
            if sha_match is not None and sha is None:
                sha = sha_match.group(1)
                continue
            orph_match = _ORPH.fullmatch(part)
            if orph_match is not None and sha is not None and orph is None:
                orph = int(orph_match.group(1))
                continue
            raise LifecycleTokenError("TOKEN_SEGMENT_INVALID")
        return cls(entries=entries, sha256=sha, orph=orph)

    def segments(self) -> list[str]:
        return [self.entries[step].render() for step in STEPS if step in self.entries]

    def render(self) -> str:
        parts = [TOKEN_PREFIX, *self.segments()]
        if self.sha256 is not None:
            parts.append("sha256=" + self.sha256)
            if self.orph is not None:
                parts.append(f"orph={self.orph}")
        return ";".join(parts)

    def with_entry(self, entry: TokenEntry) -> LifecycleToken:
        if self.sha256 is not None:
            raise LifecycleTokenError("TOKEN_FINAL")
        entries = dict(self.entries)
        entries[entry.step] = entry
        return LifecycleToken(entries=entries)

    @property
    def verified_count(self) -> int:
        return sum(1 for entry in self.entries.values() if entry.verified)

    @property
    def unresolved_items(self) -> int:
        return len(STEPS) - self.verified_count


def _ids_entry(step: str, ids: Sequence[str]) -> TokenEntry:
    ordered = sorted(ids)
    return TokenEntry(
        step=step,
        status="p",
        count=len(ordered),
        h16=sha256_hex(canonical_json(ordered))[:16],
        p8=sha256_hex(canonical_json({"step": step, "ids": ordered}))[:8],
    )


def plan_entry(step: str, ids: Sequence[str]) -> TokenEntry:
    """T1/T2 entry for the ``upload``, ``ai`` and ``story`` steps."""

    if step not in {"upload", "ai", "story"}:
        raise LifecycleTokenError("TOKEN_STEP_INVALID")
    return _ids_entry(step, ids)


def asset_plan_entry(plan: RunAssetPurgePlan) -> TokenEntry:
    """Port design §6.4: ``n`` = removable count, ``h16`` from the digest, ``p8`` from the hash."""

    if plan.retained:
        raise LifecycleTokenError("TOKEN_RETAINED_PLAN")
    return TokenEntry(
        step="asset",
        status="p",
        count=plan.removable_key_count,
        h16=plan.removable_digest[:16],
        p8=plan.plan_sha256[:8],
    )


def write_pending(
    token: LifecycleToken, entry: TokenEntry, *, plan_empty: bool
) -> LifecycleToken | None:
    """T3. ``None`` means the persisted token stays as it is."""

    existing = token.entries.get(entry.step)
    if existing is None:
        return token.with_entry(entry)
    if existing.verified:
        return None
    if entry.p8 == existing.p8 or plan_empty:
        return None
    return token.with_entry(entry)


def flip(token: LifecycleToken, step: str) -> LifecycleToken:
    """T4: only ``p`` becomes ``v``; the recorded ``n``, ``h16`` and ``p8`` are kept."""

    existing = token.entries.get(step)
    if existing is None:
        raise LifecycleTokenError("TOKEN_ENTRY_MISSING")
    if existing.verified:
        return token
    return token.with_entry(replace(existing, status="v"))


def final_token(token: LifecycleToken, orph: int) -> str:
    """T6: hash the four persisted segments exactly as stored, keys included."""

    if token.sha256 is not None:
        raise LifecycleTokenError("TOKEN_FINAL")
    if set(token.entries) != set(STEPS) or not all(e.verified for e in token.entries.values()):
        raise LifecycleTokenError("TOKEN_NOT_VERIFIED")
    if orph < 0:
        raise LifecycleTokenError("TOKEN_ORPH_INVALID")
    segments = token.segments()
    digest = sha256_hex(";".join(segments))
    return ";".join([TOKEN_PREFIX, *segments, "sha256=" + digest, f"orph={orph}"])


# =============================================================================== coordinator
class _AttemptFailed(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _Stop(Exception):
    """Another worker progressed or the lease was lost: stop without deferring."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ConsumerConfig:
    worker_id: str
    consumer_name: str = DEFAULT_CONSUMER_NAME
    lease_seconds: int = DEFAULT_LEASE_SECONDS
    step_deadline_seconds: float = STEP_DEADLINE_SECONDS
    retry_bound: int = RETRY_BOUND

    def __post_init__(self) -> None:
        if not 1 <= self.lease_seconds <= 3600:
            raise ValueError("lifecycle lease must be between 1 and 3600 seconds")
        if not 0 < self.step_deadline_seconds <= 3600:
            raise ValueError("lifecycle step deadline is outside the allowed bounds")
        if not 1 <= self.retry_bound <= 100:
            raise ValueError("lifecycle retry bound is outside the allowed bounds")
        if not self.worker_id or len(self.worker_id) > 128:
            raise ValueError("lifecycle worker id must be 1-128 characters")


def organization_id_of(scope: LifecycleScope) -> str | None:
    """The ``organization_id`` column of a lifecycle row: NULL for a Parent scope (the typed scope
    carries it), the scope ref for an ``ORGANIZATION`` scope (the CHECK needs it, T-13a-DEC-3)."""

    return scope.ref if scope.kind == ORGANIZATION_SCOPE_KIND else None


def _foreign_receipt(receipt: LifecycleReceipt, scope: LifecycleScope, run_ref: str) -> str | None:
    """The code when the receipt is not this run's receipt in this owner scope, else None."""

    if receipt.owner_scope_kind != scope.kind or receipt.owner_scope_ref != scope.ref:
        return "RECEIPT_SCOPE_MISMATCH"
    if receipt.target_ref is not None and receipt.target_ref != lifecycle_target_ref(run_ref):
        return "RECEIPT_TARGET_MISMATCH"
    return None


def retry_delay_seconds(attempt_count: int) -> int:
    """30, 60, 120, … seconds, doubling, capped at 3600 (DTR §6.3)."""

    exponent = max(attempt_count - 1, 0)
    return int(min(30 * (2 ** min(exponent, 12)), 3600))


@dataclass
class _Attempt:
    envelope: OutboxEnvelope
    run_ref: str
    scope: LifecycleScope
    request_id: str
    receipt: LifecycleReceipt
    orph: int = 0


class Be1LifecycleConsumer:
    """One claim at a time (``limit = 1``), steps 0-6, token rule, leases and CAS."""

    def __init__(
        self,
        *,
        outbox: LifecycleOutboxPort,
        receipts: LifecycleReceiptStorePort,
        audit: LifecycleAuditWriterPort,
        uploads: RunUploadClosePort,
        notices: LifecycleNoticePort,
        assets: RunAssetPurgePort,
        story: StoryLifecyclePort,
        story_refs: RunAssetReferencePort,
        config: ConsumerConfig,
        monotonic: Callable[[], float] = time.monotonic,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._outbox = outbox
        self._receipts = receipts
        self._audit = audit
        self._uploads = uploads
        self._notices = notices
        self._assets = assets
        self._story = story
        self._story_refs = story_refs
        self._config = config
        self._monotonic = monotonic
        self._clock = clock

    # ------------------------------------------------------------------ entry points
    def run_once(self, *, target_run_ref: str | None = None) -> str | None:
        aggregate_ids = (
            None if target_run_ref is None else (validate_run_ref(target_run_ref),)
        )
        claimed = cast(Any, self._outbox).claim_ready(
            worker_id=self._config.worker_id,
            limit=1,
            lease_seconds=self._config.lease_seconds,
            event_types=LIFECYCLE_EVENT_TYPES,
            aggregate_ids=aggregate_ids,
        )
        if not claimed:
            return None
        return self.handle(claimed[0])

    def handle(self, envelope: OutboxEnvelope) -> str:
        try:
            run_ref = validate_run_ref(envelope.aggregate_id)
            scope = LifecycleScope(envelope.owner_scope_kind, envelope.owner_scope_ref or "")
        except CoreAssetPurgeError as exc:
            return self._invalid_event(envelope, exc.code)
        if (
            scope.kind not in _LIFECYCLE_SCOPE_KINDS
            or envelope.event_type not in LIFECYCLE_EVENT_TYPES
        ):
            return self._invalid_event(envelope, "LIFECYCLE_EVENT_INVALID")
        request_id = lifecycle_request_id(run_ref)
        if envelope.attempt_count >= self._config.retry_bound:
            return self._exception(envelope, request_id, run_ref, scope, code="RETRY_BOUND")
        try:
            return self._purge(envelope, request_id, run_ref, scope)
        except _Stop as stop:
            self._log("lifecycle_attempt_stopped", stop.code, envelope)
            return "stopped"
        except _AttemptFailed as failed:
            return self._fail_attempt(envelope, request_id, failed.code, scope, run_ref)
        except (CoreAssetPurgeError, LifecycleTokenError) as exc:
            return self._fail_attempt(envelope, request_id, str(exc), scope, run_ref)
        except Exception as exc:  # owner adapters: never read an error as progress
            code = getattr(exc, "code", None)
            return self._fail_attempt(
                envelope,
                request_id,
                code if isinstance(code, str) else type(exc).__name__,
                scope,
                run_ref,
            )

    # ------------------------------------------------------------------ steps
    def _purge(
        self, envelope: OutboxEnvelope, request_id: str, run_ref: str, scope: LifecycleScope
    ) -> str:
        self._renew(envelope)
        receipt = self._receipts.ensure(request_id=request_id, run_ref=run_ref, scope=scope)
        foreign = _foreign_receipt(receipt, scope, run_ref)
        if foreign is not None:
            raise _AttemptFailed(foreign)
        if receipt.state in {"completed", "exception"}:
            # Already finished (or waiting for the owner review): deliver, change nothing.
            delivered = self._outbox.process_local_once(
                event_id=envelope.event_id,
                worker_id=self._config.worker_id,
                consumer_name=self._config.consumer_name,
                effect=lambda _tx, _env: None,
            )
            return "delivered" if delivered else "stopped"
        if self._story.lifecycle_state(run_ref) not in PURGE_STATES:
            raise _AttemptFailed("RUN_NOT_PURGEABLE")
        attempt = _Attempt(envelope, run_ref, scope, request_id, receipt)
        token = LifecycleToken.parse(receipt.result_ref)
        self._cas(attempt, "running", token)

        self._plain_step(
            attempt,
            "upload",
            plan=lambda: self._uploads.plan_close_run_uploads(scope, run_ref),
            act=lambda _ids: self._uploads.close_run_uploads(scope, run_ref),
            verified=lambda: not self._uploads.plan_close_run_uploads(scope, run_ref),
        )
        notice_id = "lifecycle:" + request_id
        self._plain_step(
            attempt,
            "ai",
            plan=lambda: (notice_id,),
            act=lambda _ids: self._notices.record_lifecycle_notice(
                notice_id=notice_id,
                scope=scope,
                story_run_ref=run_ref,
                reason_code=NOTICE_REASON_CODES[scope.kind],
            ),
            verified=lambda: self._notices.notice_exists(notice_id),
        )
        retained = self._asset_step(attempt)
        story_plans: dict[str, Any] = {}

        def story_plan() -> tuple[str, ...]:
            plan = self._story.plan_story_purge(run_ref)
            story_plans["plan"] = plan
            return plan.ids

        self._plain_step(
            attempt,
            "story",
            plan=story_plan,
            act=lambda _ids: self._story.purge_story_content(story_plans["plan"]),
            verified=lambda: self._story.plan_story_purge(run_ref).empty,
        )
        if retained:
            return self._exception(
                envelope, request_id, run_ref, scope, code="ASSET_RETAINED", attempt=attempt
            )
        self._finalize_step(attempt)
        return self._complete_step(attempt)

    def _plain_step(
        self,
        attempt: _Attempt,
        step: str,
        *,
        plan: Callable[[], Sequence[str]],
        act: Callable[[Sequence[str]], object],
        verified: Callable[[], bool],
    ) -> None:
        token = LifecycleToken.parse(attempt.receipt.result_ref)
        existing = token.entries.get(step)
        if existing is not None and existing.verified:
            return
        self._renew(attempt.envelope)
        deadline = self._monotonic() + self._config.step_deadline_seconds
        ids = tuple(plan())
        pending = write_pending(token, plan_entry(step, ids), plan_empty=not ids)
        if pending is not None:
            token = self._cas(attempt, attempt.receipt.state, pending)
        self._check(deadline, step)
        if ids:
            act(ids)
        self._check(deadline, step)
        if not verified():
            raise _AttemptFailed(step.upper() + "_NOT_VERIFIED")
        self._check(deadline, step)
        self._cas(attempt, attempt.receipt.state, flip(token, step))

    def _asset_step(self, attempt: _Attempt) -> bool:
        """Step 3; returns ``True`` for a retained plan (no entry, no sweep, nothing deleted)."""

        token = LifecycleToken.parse(attempt.receipt.result_ref)
        existing = token.entries.get("asset")
        if existing is not None and existing.verified:
            return False
        scope, run_ref = attempt.scope, attempt.run_ref
        self._renew(attempt.envelope)
        deadline = self._monotonic() + self._config.step_deadline_seconds
        candidates = self._assets.closure_candidates(scope, run_ref)
        candidate_refs = frozenset(row.asset_ref for row in candidates.assets)
        elsewhere = self._story_refs.assets_referenced_by_other_runs(
            scope, run_ref, candidate_refs
        )
        plan = self._assets.plan_run_purge(candidates, elsewhere)
        if plan.retained:
            return True
        pending = write_pending(token, asset_plan_entry(plan), plan_empty=plan.empty)
        if pending is not None:
            token = self._cas(attempt, attempt.receipt.state, pending)
        self._between_calls(attempt, deadline)
        if plan.removable:
            self._assets.purge_objects(plan)
        self._between_calls(attempt, deadline)
        attempt.orph += self._assets.sweep_run_prefix(scope, run_ref).swept_count
        self._between_calls(attempt, deadline)
        elsewhere_now = self._story_refs.assets_referenced_by_other_runs(
            scope, run_ref, candidate_refs
        )
        self._between_calls(attempt, deadline)
        if plan.removable:
            self._assets.delete_rows(plan, elsewhere_now)
        self._between_calls(attempt, deadline)
        if not self._assets.verify_run_purged(scope, run_ref).complete:
            raise _AttemptFailed("ASSET_NOT_VERIFIED")
        self._cas(attempt, attempt.receipt.state, flip(token, "asset"))
        return False

    def _verify_with_sweep(self, attempt: _Attempt, code: str) -> None:
        """Steps 5 and 6: verify; if not complete, sweep and verify again, else fail."""

        scope, run_ref = attempt.scope, attempt.run_ref
        if self._assets.verify_run_purged(scope, run_ref).complete:
            return
        attempt.orph += self._assets.sweep_run_prefix(scope, run_ref).swept_count
        if not self._assets.verify_run_purged(scope, run_ref).complete:
            raise _AttemptFailed(code)

    def _finalize_step(self, attempt: _Attempt) -> None:
        token = LifecycleToken.parse(attempt.receipt.result_ref)
        asset = token.entries.get("asset")
        if asset is None or not asset.verified:
            raise _AttemptFailed("ASSET_NOT_VERIFIED")
        if self._story.lifecycle_state(attempt.run_ref) == "DELETED":
            return
        self._renew(attempt.envelope)
        deadline = self._monotonic() + self._config.step_deadline_seconds
        self._verify_with_sweep(attempt, "FINALIZE_NOT_VERIFIED")
        self._check(deadline, "finalize")
        self._story.finalize_deleted(attempt.run_ref, attempt.request_id)
        if self._story.lifecycle_state(attempt.run_ref) != "DELETED":
            raise _AttemptFailed("FINALIZE_NOT_VERIFIED")

    def _complete_step(self, attempt: _Attempt) -> str:
        self._renew(attempt.envelope)
        deadline = self._monotonic() + self._config.step_deadline_seconds
        self._verify_with_sweep(attempt, "COMPLETION_NOT_VERIFIED")
        self._check(deadline, "complete")
        orph = attempt.orph
        request_id = attempt.request_id
        completed_at = self._clock()

        def effect(tx: Any, _envelope: OutboxEnvelope) -> None:
            current = self._receipts.read(request_id, tx=tx)
            if current is None or current.state != "running":
                raise _Stop("RECEIPT_RACED")
            final = final_token(LifecycleToken.parse(current.result_ref), orph)
            if not self._receipts.compare_and_set(
                request_id=request_id,
                expected_state=current.state,
                expected_result_ref=current.result_ref,
                state="completed",
                result_ref=final,
                unresolved_items=0,
                completed_at=completed_at,
                tx=tx,
            ):
                raise _Stop("RECEIPT_RACED")

        delivered = self._outbox.process_local_once(
            event_id=attempt.envelope.event_id,
            worker_id=self._config.worker_id,
            consumer_name=self._config.consumer_name,
            effect=effect,
        )
        if not delivered:
            raise _Stop("LEASE_LOST")
        return "completed"

    # ------------------------------------------------------------------ exception / retry
    def _exception(
        self,
        envelope: OutboxEnvelope,
        request_id: str,
        run_ref: str,
        scope: LifecycleScope,
        *,
        code: str,
        attempt: _Attempt | None = None,
    ) -> str:
        del attempt
        left_unchanged: list[str] = []

        def effect(tx: Any, processed: OutboxEnvelope) -> None:
            current = self._receipts.read(request_id, tx=tx)
            if current is None:
                # A worker that never reached step 0 would otherwise loop on a zero-row CAS.
                current = self._receipts.ensure(
                    request_id=request_id, run_ref=run_ref, scope=scope, tx=tx
                )
            foreign = _foreign_receipt(current, scope, run_ref)
            if foreign is not None:
                # Review R2 F-1: a receipt of another owner scope or target is never changed and
                # gets no audit row from this event, also at the retry bound; the event is
                # delivered without an effect.
                left_unchanged.append(foreign)
                return
            if current.state in {"completed", "exception"}:
                return
            if not self._receipts.compare_and_set(
                request_id=request_id,
                expected_state=current.state,
                expected_result_ref=current.result_ref,
                state="exception",
                result_ref=current.result_ref,
                unresolved_items=current.unresolved_items,
                tx=tx,
            ):
                raise _Stop("RECEIPT_RACED")
            self._audit.write_exception(
                tx=tx,
                request_id=request_id,
                run_ref=run_ref,
                scope=scope,
                processed_event_id=processed.event_id,
            )

        try:
            delivered = self._outbox.process_local_once(
                event_id=envelope.event_id,
                worker_id=self._config.worker_id,
                consumer_name=self._config.consumer_name,
                effect=effect,
            )
        except _Stop as stop:
            self._log("lifecycle_attempt_stopped", stop.code, envelope)
            return "stopped"
        if left_unchanged:
            self._log("lifecycle_event_delivered_receipt_unchanged", left_unchanged[0], envelope)
            return "delivered" if delivered else "stopped"
        self._log("lifecycle_exception", code, envelope)
        return "exception" if delivered else "stopped"

    def _fail_attempt(
        self,
        envelope: OutboxEnvelope,
        request_id: str,
        code: str,
        scope: LifecycleScope,
        run_ref: str,
    ) -> str:
        self._log("lifecycle_attempt_failed", code, envelope)
        current = self._receipts.read(request_id)
        if current is not None and _foreign_receipt(current, scope, run_ref) is not None:
            current = None  # review R2 F-1: never CAS a receipt of another scope or target
        needs_cas = current is not None and current.state not in {
            "completed",
            "exception",
            "awaiting_external_purge",
        }
        if (
            needs_cas
            and current is not None
            and not self._receipts.compare_and_set(
                request_id=request_id,
                expected_state=current.state,
                expected_result_ref=current.result_ref,
                state="awaiting_external_purge",
                result_ref=current.result_ref,
                unresolved_items=current.unresolved_items,
            )
        ):
            self._log("lifecycle_attempt_stopped", "RECEIPT_RACED", envelope)
            return "stopped"
        deferred = self._outbox.defer(
            event_id=envelope.event_id,
            worker_id=self._config.worker_id,
            retry_after_seconds=retry_delay_seconds(envelope.attempt_count),
        )
        return "deferred" if deferred else "stopped"

    def _invalid_event(self, envelope: OutboxEnvelope, code: str) -> str:
        """An event this consumer cannot attribute to a Parent run: never purge anything."""

        self._log("lifecycle_event_invalid", code, envelope)
        if envelope.attempt_count >= self._config.retry_bound:
            delivered = self._outbox.process_local_once(
                event_id=envelope.event_id,
                worker_id=self._config.worker_id,
                consumer_name=self._config.consumer_name,
                effect=lambda _tx, _env: None,
            )
            return "delivered" if delivered else "stopped"
        self._outbox.defer(
            event_id=envelope.event_id,
            worker_id=self._config.worker_id,
            retry_after_seconds=3600,
        )
        return "deferred"

    # ------------------------------------------------------------------ helpers
    def _cas(self, attempt: _Attempt, state: str, token: LifecycleToken) -> LifecycleToken:
        current = attempt.receipt
        new_ref = token.render()
        if current.state == state and current.result_ref == new_ref:
            return token
        if not self._receipts.compare_and_set(
            request_id=attempt.request_id,
            expected_state=current.state,
            expected_result_ref=current.result_ref,
            state=state,
            result_ref=new_ref,
            unresolved_items=token.unresolved_items,
        ):
            raise _Stop("RECEIPT_RACED")
        attempt.receipt = replace(
            current, state=state, result_ref=new_ref, unresolved_items=token.unresolved_items
        )
        return token

    def _renew(self, envelope: OutboxEnvelope) -> None:
        if not self._outbox.renew_lease(
            event_id=envelope.event_id,
            worker_id=self._config.worker_id,
            lease_seconds=self._config.lease_seconds,
        ):
            raise _Stop("LEASE_LOST")

    def _check(self, deadline: float, step: str) -> None:
        if self._monotonic() > deadline:
            raise _AttemptFailed(step.upper() + "_DEADLINE")

    def _between_calls(self, attempt: _Attempt, deadline: float) -> None:
        self._check(deadline, "asset")
        self._renew(attempt.envelope)

    @staticmethod
    def _log(event: str, code: str, envelope: OutboxEnvelope) -> None:
        safe = code if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", code) else "ERROR"
        _LOGGER.warning(
            "%s code=%s event_id=%s attempt=%s",
            event,
            safe,
            envelope.event_id,
            envelope.attempt_count,
        )


# =============================================================================== SQL adapters
_REQUESTS = cast(Table, DataLifecycleRequestModel.__table__)
_AUDIT = cast(Table, CoreAuditEntryModel.__table__)


def _receipt(row: Any) -> LifecycleReceipt:
    return LifecycleReceipt(
        request_id=str(row.request_id),
        state=str(row.state),
        result_ref=None if row.result_ref is None else str(row.result_ref),
        unresolved_items=int(row.unresolved_items),
        owner_scope_kind=str(row.owner_scope_kind),
        owner_scope_ref=None if row.owner_scope_ref is None else str(row.owner_scope_ref),
        completed_at=row.completed_at,
        target_ref=None if row.target_ref is None else str(row.target_ref),
    )


class SqlLifecycleReceiptStore:
    """BE1 receipt store over ``be1_data_lifecycle_requests`` (compare-and-set updates)."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def read(self, request_id: str, *, tx: Any = None) -> LifecycleReceipt | None:
        if tx is not None:
            return self._read(cast(Session, tx), request_id)
        with self._sessions() as session:
            return self._read(session, request_id)

    def ensure(
        self, *, request_id: str, run_ref: str, scope: LifecycleScope, tx: Any = None
    ) -> LifecycleReceipt:
        if tx is not None:
            return self._ensure(cast(Session, tx), request_id, run_ref, scope)
        with self._sessions.begin() as session:
            return self._ensure(session, request_id, run_ref, scope)

    def compare_and_set(
        self,
        *,
        request_id: str,
        expected_state: str,
        expected_result_ref: str | None,
        state: str,
        result_ref: str | None,
        unresolved_items: int,
        completed_at: datetime | None = None,
        tx: Any = None,
    ) -> bool:
        values: dict[str, Any] = {
            "state": state,
            "result_ref": result_ref,
            "unresolved_items": unresolved_items,
        }
        if completed_at is not None:
            values["completed_at"] = completed_at
        statement = (
            update(_REQUESTS)
            .where(
                _REQUESTS.c.request_id == request_id,
                _REQUESTS.c.state == expected_state,
                _REQUESTS.c.result_ref.is_not_distinct_from(expected_result_ref),
            )
            .values(**values)
        )
        if tx is not None:
            result = cast(CursorResult[Any], cast(Session, tx).execute(statement))
            return result.rowcount == 1
        with self._sessions.begin() as session:
            result = cast(CursorResult[Any], session.execute(statement))
            return result.rowcount == 1

    @staticmethod
    def _read(session: Session, request_id: str) -> LifecycleReceipt | None:
        row = session.execute(
            select(
                _REQUESTS.c.request_id,
                _REQUESTS.c.state,
                _REQUESTS.c.result_ref,
                _REQUESTS.c.unresolved_items,
                _REQUESTS.c.owner_scope_kind,
                _REQUESTS.c.owner_scope_ref,
                _REQUESTS.c.completed_at,
                _REQUESTS.c.target_ref,
            ).where(_REQUESTS.c.request_id == request_id)
        ).one_or_none()
        return None if row is None else _receipt(row)

    @classmethod
    def _ensure(
        cls, session: Session, request_id: str, run_ref: str, scope: LifecycleScope
    ) -> LifecycleReceipt:
        if scope.kind not in _LIFECYCLE_SCOPE_KINDS:
            raise CoreAssetPurgeError("SCOPE_INVALID")
        session.execute(
            pg_insert(_REQUESTS)
            .values(
                request_id=request_id,
                organization_id=organization_id_of(scope),
                owner_scope_kind=scope.kind,
                owner_scope_ref=scope.ref,
                request_type="delete",
                target_ref=lifecycle_target_ref(run_ref),
                state="requested",
                unresolved_items=len(STEPS),
                result_ref=TOKEN_PREFIX,
                requested_by=scope.ref,
                created_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(index_elements=["request_id"])
        )
        receipt = cls._read(session, request_id)
        if receipt is None:
            raise CoreAssetPurgeError("RECEIPT_UNAVAILABLE")
        target = session.scalar(
            select(_REQUESTS.c.target_ref).where(_REQUESTS.c.request_id == request_id)
        )
        if target != lifecycle_target_ref(run_ref):
            raise CoreAssetPurgeError("RECEIPT_TARGET_MISMATCH")
        return receipt


class SqlLifecycleAuditWriter:
    """Insert-if-absent ``lifecycle.exception`` audit row (metadata only, DTR §8)."""

    def write_exception(
        self,
        *,
        tx: Any,
        request_id: str,
        run_ref: str,
        scope: LifecycleScope,
        processed_event_id: str,
    ) -> None:
        cast(Session, tx).execute(
            pg_insert(_AUDIT)
            .values(
                audit_id=lifecycle_exception_audit_id(processed_event_id),
                organization_id=organization_id_of(scope),
                owner_scope_kind=scope.kind,
                owner_scope_ref=scope.ref,
                actor_ref=LIFECYCLE_WORKER_ACTOR,
                action=AUDIT_EXCEPTION,
                resource_type=AUDIT_RESOURCE_TYPE,
                resource_id=validate_run_ref(run_ref),
                decision="exception:" + request_id,
                created_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(index_elements=["audit_id"])
        )


__all__ = [
    "Be1LifecycleConsumer",
    "ConsumerConfig",
    "DEFAULT_CONSUMER_NAME",
    "LifecycleToken",
    "LifecycleTokenError",
    "NOTICE_REASON_CODES",
    "RETRY_BOUND",
    "STEPS",
    "SqlLifecycleAuditWriter",
    "SqlLifecycleReceiptStore",
    "TokenEntry",
    "asset_plan_entry",
    "final_token",
    "flip",
    "organization_id_of",
    "plan_entry",
    "retry_delay_seconds",
    "write_pending",
]
