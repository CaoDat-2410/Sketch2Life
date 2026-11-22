"""Class projection confirmation, the sample-slot claim and the projection token facts
(FEAT-066 goal v3, T-5a; SRS l.396, l.552-555, l.777, l.1449, l.1661-1662, l.1691-1693; OD-14).

Three entry points of the Lesson side, all decided on the CURRENT assignment (FR-T-14, FR-T-16:
"only the current responsible Teacher"; ``decide_child_data`` of T-4b1: uncovered, revoked, Manager,
Parent and Platform Admin are the uniform 404; a covered caller who is not the exact-class
responsible Teacher is 403):

* ``ProjectionService.confirm``: the keyed command. One transaction, serialised by the occurrence
  ``FOR UPDATE``; lock order occurrence, class ``FOR SHARE``, caller facts and decision re-read
  under the locks, then the Story run row ``FOR SHARE`` through ``sample_facts`` (the one Story
  read of this module; no Story row is written). The first confirmation claims the sample slot in
  one compare-and-set (OD-14); the slot never reopens (FR-T-13).
* ``ProjectionService.grant``: the read that precedes a projection token (no database write, no
  lock). The token itself is minted by the route.
* ``SqlProjectionAuthorization``: the Lesson half of every projection stream request, a boolean.

The occurrence row stores the confirming Teacher and the confirmation time but no generation, so a
confirmation covers a generation only when it was given after that generation became ready
(``confirmation_covers``): a regenerated sample needs its own confirmation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_video import SampleFacts
from sketch2life.contracts.schemas.lesson_occurrences import ProjectionConfirmationRequestV1
from sketch2life.domain.lesson_occurrences import projection as rules
from sketch2life.domain.lesson_occurrences.child_selection import decide_child_data
from sketch2life.domain.lesson_occurrences.model import AccessOutcome
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    load_caller_facts,
    not_found,
)
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES, PLAN_REVISIONS
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ClassroomModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_video.repository import sample_facts
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref

RECEIPT_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/projection-confirmation"
AUDIT_CONFIRM_ACTION = "lesson.occurrence.projection.confirm"
AUDIT_CLAIM_ACTION = "lesson.occurrence.sample.claim"
AUDIT_RESOURCE_TYPE = "lesson_occurrence"
_CLASS_ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class ProjectionResult:
    """A confirmation answer: the receipt body (JSON-safe) and the replay flag."""

    body: dict[str, Any]
    replayed: bool


@dataclass(frozen=True, slots=True)
class ProjectionGrantFacts:
    """What the route needs to mint a projection token after the Lesson checks passed."""

    run_id: str
    generation_id: str
    occurrence_id: str
    confirmed_ms: int
    actor_scope_ref: str


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _db_failure() -> LessonOccurrenceError:
    """A database fault is never a 500."""
    return LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE")


def _stale(current_version: int) -> LessonOccurrenceError:
    return LessonOccurrenceError(409, "STALE_REVISION", current_version=current_version)


def _refused() -> LessonOccurrenceError:
    return LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")


def _occurrence_row(db: Session, occurrence_id: str, *, lock: bool) -> RowMapping | None:
    statement = select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id)
    if lock:
        statement = statement.with_for_update()
    return db.execute(statement).mappings().one_or_none()


def _decide(db: Session, principal: VerifiedPrincipal, occurrence: RowMapping) -> str:
    """The responsible Teacher's account ref, or the refusal (T-4b1 ``decide_child_data``)."""

    facts = load_caller_facts(db, principal, str(occurrence["organization_ref"]))
    if facts is None:
        raise not_found()
    outcome = decide_child_data(
        facts.rows,
        str(occurrence["class_ref"]),
        caller_account_ref=facts.account_ref,
        responsible_teacher_ref=str(occurrence["responsible_teacher_ref"]),
    )
    if outcome is AccessOutcome.PROCEED:
        return facts.account_ref
    if outcome is AccessOutcome.FORBIDDEN:
        raise LessonOccurrenceError(403, "ACTION_NOT_ALLOWED")
    raise not_found()


class ProjectionService:
    def __init__(self, db: Session, *, clock: Callable[[], datetime] | None = None) -> None:
        self.db = db
        self._clock = clock or (lambda: datetime.now(UTC))

    # ------------------------------------------------------------------ access and locks
    def _authorize_for_write(
        self, principal: VerifiedPrincipal, occurrence_id: str
    ) -> tuple[RowMapping, str, int, str | None]:
        """Decide on the current rows, lock the occurrence and its class and decide again under
        the locks (a revoked assignment is 404 at this call). Returns the locked occurrence, the
        caller's account ref, the class revision and the class state (``None`` when the opaque
        class ref names no class)."""

        occurrence = _occurrence_row(self.db, occurrence_id, lock=False)
        if occurrence is None:
            raise not_found()
        _decide(self.db, principal, occurrence)
        locked = _occurrence_row(self.db, occurrence_id, lock=True)
        if locked is None:  # pragma: no cover - occurrences are never deleted
            raise not_found()
        klass = self.db.execute(
            select(ClassroomModel.revision, ClassroomModel.state)
            .where(ClassroomModel.class_id == locked["class_ref"])
            .with_for_update(read=True)
        ).one_or_none()
        # A fresh read of the identity and assignment rows under the locks.
        self.db.expire_all()
        account = _decide(self.db, principal, locked)
        revision = int(klass[0]) if klass is not None else 1
        return locked, account, revision, None if klass is None else str(klass[1])

    # ------------------------------------------------------------------ confirm
    def confirm(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        payload: ProjectionConfirmationRequestV1,
        expected_revision: int,
        idempotency_key: str,
    ) -> ProjectionResult:
        for attempt in (1, 2):
            try:
                return self._confirm_once(
                    principal, occurrence_id, payload, expected_revision, idempotency_key
                )
            except IntegrityError as error:
                self.db.rollback()
                if getattr(error.orig, "sqlstate", None) != "23505":
                    raise _db_failure() from None
                if attempt == 2:
                    raise _refused() from None
            except SQLAlchemyError:
                self.db.rollback()
                raise _db_failure() from None
            except BaseException:
                self.db.rollback()
                raise
        raise _db_failure()  # pragma: no cover - the loop returns or raises

    def _confirm_once(
        self,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        payload: ProjectionConfirmationRequestV1,
        expected_revision: int,
        key: str,
    ) -> ProjectionResult:
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        scope = RECEIPT_SCOPE.format(occurrence_id=occurrence_id)
        fingerprint = rules.request_fingerprint(
            expected_revision=expected_revision,
            run_id=payload.run_id,
            generation_id=payload.generation_id,
        )
        occurrence, account, class_revision, class_state = self._authorize_for_write(
            principal, occurrence_id
        )
        receipt = self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))
        if receipt is not None:
            if receipt.request_fingerprint != fingerprint:
                raise LessonOccurrenceError(400, "INVALID_IDEMPOTENCY_KEY")
            replayed = dict(receipt.response_json)
            self.db.rollback()
            return ProjectionResult(replayed, True)
        revision = int(occurrence["revision"])
        if occurrence["state"] == "ARCHIVED" or (
            class_state is not None and class_state != _CLASS_ACTIVE
        ):
            raise _refused()
        if revision != expected_revision:
            raise _stale(revision)
        if (
            occurrence["state"] not in rules.CONFIRMABLE_STATES
            or occurrence["approved_plan_revision_id"] is None
        ):
            raise _refused()
        decision = rules.decide_claim(
            slot_state=str(occurrence["sample_slot_state"]),
            successful_run_ref=occurrence["successful_sample_run_ref"],
            run_id=payload.run_id,
        )
        if decision is rules.ClaimDecision.REFUSED:
            raise LessonOccurrenceError(409, "SAMPLE_VIDEO_ALREADY_EXISTS")
        facts = sample_facts(self.db, payload.run_id, lock=True)
        if facts is None or facts.occurrence_ref != occurrence_id:
            raise _stale(revision)
        if not facts.playable or facts.generation_id is None:
            raise _refused()
        if facts.generation_id != payload.generation_id:
            raise _stale(revision)
        plan = self._pinned_plan(occurrence_id, facts)
        if plan is None:
            raise _stale(revision)
        now = self._clock()
        write = rules.decide_write(
            decision,
            confirmed_by=occurrence["class_projection_confirmed_by_ref"],
            confirmed_at=occurrence["class_projection_confirmed_at"],
            caller_account=account,
            ready_at=facts.ready_at,
        )
        if write is rules.WriteKind.CLAIM:
            self._write_claim(occurrence, account, payload.run_id, expected_revision, now)
        elif write is rules.WriteKind.REFRESH:
            self._write_refresh(occurrence, account, payload.run_id, expected_revision, now)
        if write is not rules.WriteKind.NONE:
            self._audit(occurrence, account, AUDIT_CONFIRM_ACTION, rules.AUDIT_CONFIRM_DECISION)
            if write is rules.WriteKind.CLAIM:
                self._audit(occurrence, account, AUDIT_CLAIM_ACTION, rules.AUDIT_CLAIM_DECISION)
            self.db.flush()
        current = _occurrence_row(self.db, occurrence_id, lock=False)
        if current is None or current["class_projection_confirmed_at"] is None:
            raise _db_failure()  # pragma: no cover - the row was just written
        body = rules.receipt_body(
            rules.ReceiptFacts(
                occurrence_id=occurrence_id,
                run_id=payload.run_id,
                generation_id=payload.generation_id,
                confirmed_at=current["class_projection_confirmed_at"],
                confirmed_by_ref=str(current["class_projection_confirmed_by_ref"]),
                class_revision=class_revision,
                plan_revision_no=int(plan["revision_no"]),
                plan_hash=str(plan["content_hash"]),
                plan_is_current=(
                    str(plan["plan_revision_id"]) == str(current["approved_plan_revision_id"])
                ),
                occurrence_revision=int(current["revision"]),
                slot_state=str(current["sample_slot_state"]),
                claimed_at=current["sample_claimed_at"],
                slot_run_ref=current["successful_sample_run_ref"],
            )
        )
        safe = _json_safe(body)
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=str(occurrence["organization_ref"]),
                request_fingerprint=fingerprint,
                response_json=safe,
            )
        )
        self.db.commit()
        return ProjectionResult(safe, False)

    def _pinned_plan(self, occurrence_id: str, facts: SampleFacts) -> RowMapping | None:
        """The plan revision the run is pinned to, when it is a plan of THIS occurrence that was
        approved at some time and the pin's number and hash agree with it (SRS l.2697: the run is
        not compared with the CURRENT plan)."""

        if facts.plan_revision_id is None:
            return None
        plan = (
            self.db.execute(
                select(
                    PLAN_REVISIONS.c.plan_revision_id,
                    PLAN_REVISIONS.c.revision_no,
                    PLAN_REVISIONS.c.content_hash,
                    PLAN_REVISIONS.c.state,
                ).where(
                    PLAN_REVISIONS.c.plan_revision_id == facts.plan_revision_id,
                    PLAN_REVISIONS.c.occurrence_id == occurrence_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if plan is None:
            return None
        matches = rules.pin_matches_plan(
            pin_plan_revision_id=facts.plan_revision_id,
            pin_revision_no=facts.plan_revision_no,
            pin_hash=facts.plan_hash,
            plan_revision_id=str(plan["plan_revision_id"]),
            plan_revision_no=int(plan["revision_no"]),
            plan_hash=str(plan["content_hash"]),
            plan_state=str(plan["state"]),
        )
        return plan if matches else None

    def _write_claim(
        self,
        occurrence: RowMapping,
        account: str,
        run_id: str,
        expected_revision: int,
        now: datetime,
    ) -> None:
        """OD-14: one compare-and-set on the occurrence; the plan pointer is not changed."""

        updated = self.db.execute(
            update(OCCURRENCES)
            .where(
                OCCURRENCES.c.occurrence_id == occurrence["occurrence_id"],
                OCCURRENCES.c.sample_slot_state == rules.SLOT_AVAILABLE,
                OCCURRENCES.c.revision == expected_revision,
            )
            .values(
                sample_slot_state=rules.SLOT_CLAIMED,
                sample_claimed_at=now,
                successful_sample_run_ref=run_id,
                state=rules.STATE_SAMPLE_USED,
                class_projection_confirmed_by_ref=account,
                class_projection_confirmed_at=now,
                revision=OCCURRENCES.c.revision + 1,
                updated_at=now,
            )
        )
        if getattr(updated, "rowcount", 0) != 1:  # pragma: no cover - the occurrence lock holds
            raise self._current_stale(str(occurrence["occurrence_id"]))

    def _write_refresh(
        self,
        occurrence: RowMapping,
        account: str,
        run_id: str,
        expected_revision: int,
        now: datetime,
    ) -> None:
        """The claim never changes; another Teacher or a newer generation rewrites the pair, which
        ends every token minted before (their ``c`` no longer matches)."""

        updated = self.db.execute(
            update(OCCURRENCES)
            .where(
                OCCURRENCES.c.occurrence_id == occurrence["occurrence_id"],
                OCCURRENCES.c.sample_slot_state == rules.SLOT_CLAIMED,
                OCCURRENCES.c.successful_sample_run_ref == run_id,
                OCCURRENCES.c.revision == expected_revision,
            )
            .values(
                class_projection_confirmed_by_ref=account,
                class_projection_confirmed_at=now,
                revision=OCCURRENCES.c.revision + 1,
                updated_at=now,
            )
        )
        if getattr(updated, "rowcount", 0) != 1:  # pragma: no cover - the occurrence lock holds
            raise self._current_stale(str(occurrence["occurrence_id"]))

    def _current_stale(self, occurrence_id: str) -> LessonOccurrenceError:
        current = _occurrence_row(self.db, occurrence_id, lock=False)
        return _stale(int(current["revision"]) if current is not None else 0)

    def _audit(self, occurrence: RowMapping, account: str, action: str, decision: str) -> None:
        # Refs and the acknowledged literals only: no child, no name, no media (SRS l.555, BR-37).
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=str(occurrence["organization_ref"]),
                actor_ref=account,
                action=action,
                resource_type=AUDIT_RESOURCE_TYPE,
                resource_id=str(occurrence["occurrence_id"]),
                decision=decision,
            )
        )

    # ------------------------------------------------------------------ token facts
    def grant(self, *, principal: VerifiedPrincipal, occurrence_id: str) -> ProjectionGrantFacts:
        """The facts a projection token needs (SRS l.1449, l.1662): a current confirmation by the
        caller, the confirmed sample still the slot's run, playable and covered, the class active.
        Read only: no write, no lock (the stream re-checks everything on every request)."""

        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        occurrence = _occurrence_row(self.db, occurrence_id, lock=False)
        if occurrence is None:
            raise not_found()
        account = _decide(self.db, principal, occurrence)
        grant = _current_grant(self.db, occurrence, account)
        self.db.rollback()
        if grant is None:
            raise _refused()
        return ProjectionGrantFacts(
            run_id=grant[0],
            generation_id=grant[1],
            occurrence_id=occurrence_id,
            confirmed_ms=rules.confirmed_ms(occurrence["class_projection_confirmed_at"]),
            actor_scope_ref=parent_scope_ref(principal),
        )


def _class_is_active(db: Session, occurrence: RowMapping) -> bool:
    state = db.scalar(
        select(ClassroomModel.state).where(ClassroomModel.class_id == occurrence["class_ref"])
    )
    return state is None or state == _CLASS_ACTIVE


def _current_grant(db: Session, occurrence: RowMapping, account: str) -> tuple[str, str] | None:
    """``(run_id, generation_id)`` of the sample the stored confirmation covers, else ``None``.

    The occurrence must not be archived, its class active, the slot claimed by a run, the
    confirmation given by ``account`` and the run the occurrence's own, ``VIDEO_READY`` and
    playable, with a confirmation given after its current generation became ready."""

    run_id = occurrence["successful_sample_run_ref"]
    confirmed_at = occurrence["class_projection_confirmed_at"]
    if (
        occurrence["state"] == "ARCHIVED"
        or occurrence["sample_slot_state"] != rules.SLOT_CLAIMED
        or run_id is None
        or confirmed_at is None
        or occurrence["class_projection_confirmed_by_ref"] != account
        or not _class_is_active(db, occurrence)
    ):
        return None
    facts = sample_facts(db, str(run_id), lock=False)
    if (
        facts is None
        or facts.occurrence_ref != occurrence["occurrence_id"]
        or not facts.playable
        or facts.generation_id is None
        or not rules.confirmation_covers(confirmed_at, facts.ready_at)
    ):
        return None
    return str(run_id), facts.generation_id


class SqlProjectionAuthorization:
    """The Lesson half of every projection stream request (``ProjectionAuthorizationPort``).

    Read only, no lock, nothing cached: the occurrence is the token's, the caller is the CURRENT
    responsible Teacher with an exact-class ``teacher`` row, the class is active, the confirmation
    is the caller's and has the token's millisecond, the sample is the slot's run and covered.
    Every doubt, including a database fault, is ``False`` (the stream answers the uniform 404)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def confirmation_is_current(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        generation_id: str,
        occurrence_id: str,
        confirmed_ms: int,
    ) -> bool:
        try:
            occurrence = _occurrence_row(self._session, occurrence_id, lock=False)
            if occurrence is None:
                return False
            account = _decide(self._session, principal, occurrence)
            confirmed_at = occurrence["class_projection_confirmed_at"]
            if confirmed_at is None or rules.confirmed_ms(confirmed_at) != confirmed_ms:
                return False
            if occurrence["successful_sample_run_ref"] != run_id:
                return False
            grant = _current_grant(self._session, occurrence, account)
        except (LessonOccurrenceError, SQLAlchemyError):
            return False
        return grant is not None and grant == (run_id, generation_id)


__all__ = [
    "AUDIT_CLAIM_ACTION",
    "AUDIT_CONFIRM_ACTION",
    "RECEIPT_SCOPE",
    "ProjectionGrantFacts",
    "ProjectionResult",
    "ProjectionService",
    "SqlProjectionAuthorization",
]
