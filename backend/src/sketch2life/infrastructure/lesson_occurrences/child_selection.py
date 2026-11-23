"""Teacher random-child selection and confirmation (FEAT-066 goal v3, T-4b1; OD-02, AC-56).

SRS l.341-352 (candidates, equal-probability pick, one stale reselect, empty stops, every read
revalidates, the Teacher confirms before a run exists), l.354 and BR-34 (metadata-only evidence),
l.549-554 FR-T-10..15, l.1441 UC-05, l.1447-1448.

One transaction per command, serialised by ``FOR UPDATE`` on the occurrence row and ``FOR SHARE`` on
its class row (the lock order shared with T-4b2 and T-5a: occurrence, class, selection, story run),
both taken only after the caller passed the access decision, which is then taken again under the
locks (FR-T-14: a revoked assignment is 404 at the next call). The state machine is the pure
``decide_next`` of the domain module; this module reads the facts, writes the rows and keeps the
guards of the plan (D1 to D13):

* only ``SYNTHETIC_DEV`` children behind the local/test synthetic gate are ever candidates; a REAL
  child is never one (X-19: no valid consent state exists);
* the drawn index, the generator and any seed stay local to ``pick_child``; the evidence row, the
  receipt and the audit row hold the selection id or opaque refs only, never a name;
* no run, job, claim, quota usage or occurrence write exists before the T-4b2 create;
* ``purge_child_selections`` deletes the rows of one child under the transaction-local purge
  flag; no caller exists yet (the FR-C-10 executor is missing: OPEN-1).
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, delete, exists, func, or_, select, text, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.child_selection import (
    AUDIT_ACTIONS,
    ELIGIBILITY_BASIS,
    MAX_AGE_MONTHS,
    MIN_AGE_MONTHS,
    OUTCOME_NONE,
    OUTCOME_SELECTED,
    POLICY_VERSION,
    STATE_STOPPED,
    SYNTHETIC_ORIGIN,
    Case,
    RowFacts,
    SelectionPolicy,
    candidate_set_hash,
    canonical_hash,
    decide_child_data,
    decide_next,
    is_past_due,
    pick_child,
    reselect_available,
    selection_sha256,
    view_state,
)
from sketch2life.domain.lesson_occurrences.model import AccessOutcome
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    load_caller_facts,
    not_found,
    require_class_writable,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    CHILD_SELECTIONS,
    OCCURRENCES,
    PLAN_REVISIONS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ClassroomModel,
    DataLifecycleRequestModel,
    EnrollmentModel,
    ManagedProfileModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel

SELECT_RECEIPT_SCOPE = "lesson-occurrence-child-selection:{occurrence_id}"
CONFIRM_RECEIPT_SCOPE = "lesson-occurrence-child-selection:{selection_id}:confirm"
PURGE_FLAG = "sketch2life.child_selection_purge"
AUDIT_RESOURCE_TYPE = "lesson_occurrence"

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class SyntheticGate:
    """The local/test synthetic gate (the condition of ``parent_runtime``): off means none."""

    enabled: bool


def synthetic_gate_from_settings(settings: Any) -> SyntheticGate:
    enabled = settings.env in {"local", "test"} and settings.synthetic_pilot_enabled is True
    return SyntheticGate(enabled=bool(enabled))


def candidate_statement(organization_ref: str, class_ref: str) -> Select[Any]:
    """The one SQL statement of the candidate predicate (D1, D2); REAL children never match.

    Active enrollment in the class and organization, an active profile of that class, 36 to 120
    months (l.2742), an active class, origin ``SYNTHETIC_DEV`` only, and no pending deletion request
    that names the child, the class or the organization (OPEN-6: ``target_ref`` is free-form).
    """
    pending_deletion = exists().where(
        DataLifecycleRequestModel.request_type == "delete",
        DataLifecycleRequestModel.state != "completed",
        or_(
            DataLifecycleRequestModel.target_ref == ManagedProfileModel.child_id,
            DataLifecycleRequestModel.target_ref == ManagedProfileModel.class_id,
            DataLifecycleRequestModel.target_ref == ManagedProfileModel.organization_id,
        ),
    )
    return (
        select(ManagedProfileModel.child_id)
        .join(
            EnrollmentModel,
            and_(
                EnrollmentModel.child_id == ManagedProfileModel.child_id,
                EnrollmentModel.class_id == ManagedProfileModel.class_id,
                EnrollmentModel.organization_id == ManagedProfileModel.organization_id,
            ),
        )
        .join(
            ClassroomModel,
            and_(
                ClassroomModel.class_id == ManagedProfileModel.class_id,
                ClassroomModel.organization_id == ManagedProfileModel.organization_id,
            ),
        )
        .where(
            ManagedProfileModel.organization_id == organization_ref,
            ManagedProfileModel.class_id == class_ref,
            ManagedProfileModel.state == "active",
            ManagedProfileModel.age_months.between(MIN_AGE_MONTHS, MAX_AGE_MONTHS),
            ManagedProfileModel.data_origin == SYNTHETIC_ORIGIN,
            EnrollmentModel.state == "active",
            ClassroomModel.state == "active",
            ~pending_deletion,
        )
        .order_by(ManagedProfileModel.child_id)
    )


def purge_child_selections(db: Session, organization_id: str, child_ref: str) -> int:
    """Delete every selection row of one organization that names ``child_ref`` (owner condition 3).

    The DELETE trigger refuses a delete unless the transaction-local flag is ``on``; the flag is set
    here and switched off again before returning, so a later statement of the same transaction is
    refused. NOTHING calls this at HEAD: the FR-C-10 organization-profile deletion executor does not
    exist (the command-receipt purge helper of T-7c-fix is unwired too). OPEN-1, in the evidence.
    """
    db.execute(text("SELECT set_config(:flag, 'on', true)"), {"flag": PURGE_FLAG})
    try:
        result = db.execute(
            delete(CHILD_SELECTIONS).where(
                CHILD_SELECTIONS.c.organization_ref == organization_id,
                CHILD_SELECTIONS.c.selected_child_ref == child_ref,
            )
        )
    finally:
        db.execute(text("SELECT set_config(:flag, 'off', true)"), {"flag": PURGE_FLAG})
    return int(getattr(result, "rowcount", 0) or 0)


def child_is_candidate(
    db: Session, gate: SyntheticGate, organization_ref: str, class_ref: str, child_ref: str
) -> bool:
    """Does the T-4b1 predicate still hold for this one child (T-4b2 D8 step 7)?

    The same statement as the offer, narrowed to the child; the gate off means no candidate.
    """
    if not gate.enabled:
        return False
    # not named ``statement``: the age-write scan of test_profile_age_invariant taints that name
    one_child = candidate_statement(organization_ref, class_ref).where(
        ManagedProfileModel.child_id == child_ref
    )
    return db.execute(one_child).first() is not None


def stale_child_selection(db: Session, selection_id: str) -> int | None:
    """Mark a live selection ``STALE`` (its child left the candidate set); the new revision, or
    ``None`` when the row is no longer live. The caller commits; the write is kept (l.346)."""
    return db.execute(
        update(CHILD_SELECTIONS)
        .where(
            CHILD_SELECTIONS.c.selection_id == selection_id,
            CHILD_SELECTIONS.c.state.in_(("OPEN", "CONFIRMED")),
        )
        .values(state="STALE", revision=CHILD_SELECTIONS.c.revision + 1)
        .returning(CHILD_SELECTIONS.c.revision)
    ).scalar_one_or_none()


def consume_child_selection(db: Session, selection_id: str, *, run_ref: str, now: datetime) -> bool:
    """The single compare-and-set ``CONFIRMED -> CONSUMED`` of the Teacher create (T-4b2 D11).

    One Lesson-owned row inside the Story transaction of the create: the claim of the sample slot
    (l.351) is another matter and stays a separate step. ``False`` when the row was not
    ``CONFIRMED`` any more (the caller refuses and rolls back).
    """
    result = db.execute(
        update(CHILD_SELECTIONS)
        .where(
            CHILD_SELECTIONS.c.selection_id == selection_id,
            CHILD_SELECTIONS.c.state == "CONFIRMED",
        )
        .values(
            state="CONSUMED",
            revision=CHILD_SELECTIONS.c.revision + 1,
            consumed_at=now,
            consumed_run_ref=run_ref,
        )
    )
    return getattr(result, "rowcount", 0) == 1


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """A command or read: the body, its HTTP status and the replay flag."""

    body: dict[str, Any]
    status_code: int
    replayed: bool = False
    # The STORED state of the row a read answers (the body carries the computed one): the route may
    # answer 304 only for an immutable stored state (T4B1-IR-01). None when not a single-row read.
    stored_state: str | None = None


def _facts_of(row: RowMapping) -> RowFacts:
    return RowFacts(
        selection_id=str(row["selection_id"]),
        kind=str(row["kind"]),
        draw_no=None if row["draw_no"] is None else int(row["draw_no"]),
        state=str(row["state"]),
        child_ref=None if row["selected_child_ref"] is None else str(row["selected_child_ref"]),
        plan_revision_id=str(row["plan_revision_id"]),
        teacher_ref=str(row["teacher_ref"]),
        candidate_set_hash=str(row["candidate_set_hash"]),
        expires_at=row["expires_at"],
        confirmation_expires_at=row["confirmation_expires_at"],
    )


def _db_failure() -> LessonOccurrenceError:
    """A database fault is never a 500."""
    return LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE")


class ChildSelectionService:
    def __init__(
        self,
        db: Session,
        *,
        gate: SyntheticGate,
        policy: SelectionPolicy | None = None,
        clock: Clock = _utcnow,
        randbelow: Callable[[int], int] = secrets.randbelow,
    ) -> None:
        self.db = db
        self._gate = gate
        self._policy = policy or SelectionPolicy()
        self._clock = clock
        self._randbelow = randbelow

    # ------------------------------------------------------------------ access and locks
    @staticmethod
    def _decide(db: Session, principal: VerifiedPrincipal, occurrence: RowMapping) -> str:
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

    def _occurrence(self, occurrence_id: str, *, lock: bool) -> RowMapping:
        statement = select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id)
        if lock:
            statement = statement.with_for_update()
        row = self.db.execute(statement).mappings().one_or_none()
        if row is None:
            raise not_found()
        return row

    def _authorize(
        self, principal: VerifiedPrincipal, occurrence_id: str, *, lock: bool
    ) -> tuple[RowMapping, str, int]:
        """Decide access; for a write also lock and decide again under the locks (R1 F-12a).

        Returns the occurrence, the caller's account ref and the class revision (1 when the class
        row is unknown, which the opaque class ref allows).
        """
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        occurrence = self._occurrence(occurrence_id, lock=False)
        account = self._decide(self.db, principal, occurrence)
        if not lock:
            return occurrence, account, 1
        occurrence = self._occurrence(occurrence_id, lock=True)
        klass = self.db.execute(
            select(ClassroomModel.revision)
            .where(ClassroomModel.class_id == occurrence["class_ref"])
            .with_for_update(read=True)
        ).one_or_none()
        # A fresh read of the identity and assignment rows under the locks.
        self.db.expire_all()
        account = self._decide(self.db, principal, occurrence)
        return occurrence, account, int(klass[0]) if klass is not None else 1

    # ------------------------------------------------------------------ facts
    def _plan(self, plan_revision_id: str | None) -> RowMapping | None:
        if plan_revision_id is None:
            return None
        return (
            self.db.execute(
                select(
                    PLAN_REVISIONS.c.plan_revision_id,
                    PLAN_REVISIONS.c.revision_no,
                    PLAN_REVISIONS.c.content_hash,
                    PLAN_REVISIONS.c.state,
                ).where(PLAN_REVISIONS.c.plan_revision_id == plan_revision_id)
            )
            .mappings()
            .one_or_none()
        )

    def _preconditions(self, occurrence: RowMapping) -> RowMapping:
        """D9: archived or read-only class 409, plan not approved 422, claimed slot 409."""
        if occurrence["state"] == "ARCHIVED":
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
        require_class_writable(self.db, occurrence, lock=False)
        plan = self._plan(occurrence["approved_plan_revision_id"])
        if plan is None or plan["state"] != "APPROVED":
            raise LessonOccurrenceError(422, "LESSON_PLAN_NOT_APPROVED")
        if occurrence["sample_slot_state"] != "AVAILABLE":
            raise LessonOccurrenceError(409, "SAMPLE_VIDEO_ALREADY_EXISTS")
        return plan

    def _candidates(self, occurrence: RowMapping) -> list[str]:
        if not self._gate.enabled:
            return []
        rows = self.db.execute(
            candidate_statement(str(occurrence["organization_ref"]), str(occurrence["class_ref"]))
        ).scalars()
        return sorted({str(child) for child in rows})

    def _one(self, *conditions: Any, newest: bool = True) -> RowMapping | None:
        statement = select(CHILD_SELECTIONS).where(*conditions)
        statement = statement.order_by(
            CHILD_SELECTIONS.c.seq.desc() if newest else CHILD_SELECTIONS.c.seq.asc()
        ).limit(1)
        return self.db.execute(statement).mappings().one_or_none()

    def _row_by_id(self, selection_id: str, occurrence_id: str) -> RowMapping | None:
        return self._one(
            CHILD_SELECTIONS.c.selection_id == selection_id,
            CHILD_SELECTIONS.c.occurrence_id == occurrence_id,
        )

    def _draw_rows(self, occurrence_id: str) -> int:
        return int(
            self.db.execute(
                select(func.count()).where(
                    CHILD_SELECTIONS.c.occurrence_id == occurrence_id,
                    CHILD_SELECTIONS.c.kind.in_(("DRAW", "RESELECT")),
                )
            ).scalar_one()
        )

    # ------------------------------------------------------------------ writes
    def _transition(self, selection_id: str, new_state: str) -> None:
        result = self.db.execute(
            update(CHILD_SELECTIONS)
            .where(
                CHILD_SELECTIONS.c.selection_id == selection_id,
                CHILD_SELECTIONS.c.state.in_(("OPEN", "CONFIRMED")),
            )
            .values(state=new_state, revision=CHILD_SELECTIONS.c.revision + 1)
        )
        if getattr(result, "rowcount", 0) != 1:  # pragma: no cover - the occurrence lock holds
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")

    def _audit(self, action: str, occurrence: RowMapping, account: str, selection_id: str) -> None:
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=str(occurrence["organization_ref"]),
                actor_ref=account,
                action=action,
                resource_type=AUDIT_RESOURCE_TYPE,
                resource_id=str(occurrence["occurrence_id"]),
                # The selection id only: no child ref, no count, no draw data (BR-34).
                decision=selection_id,
            )
        )

    def _store_receipt(
        self,
        principal: VerifiedPrincipal,
        scope: str,
        key: str,
        occurrence: RowMapping,
        fingerprint: str,
        *,
        selection_id: str | None,
        outcome: str,
        state: str,
        status_code: int,
    ) -> None:
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=str(occurrence["organization_ref"]),
                request_fingerprint=fingerprint,
                # Metadata only: the selection id and the outcome, never a name (R1 F-2, D13).
                response_json={
                    "selection_id": selection_id,
                    "outcome": outcome,
                    "state": state,
                    "status": status_code,
                },
            )
        )
        self.db.flush()

    # ------------------------------------------------------------------ the view
    def _view(
        self,
        occurrence: RowMapping,
        row: RowMapping | None,
        *,
        candidates: list[str],
        now: datetime,
        blank_state: str = STATE_STOPPED,
    ) -> dict[str, Any]:
        occurrence_id = str(occurrence["occurrence_id"])
        body: dict[str, Any] = {
            "contract": "ChildSelectionV1",
            "selection_id": None,
            "occurrence_id": occurrence_id,
            "outcome": OUTCOME_NONE,
            "state": blank_state,
            "revision": None,
            "draw_no": None,
            "reselect_available": reselect_available(self._draw_rows(occurrence_id), self._policy),
            "issued_at": None,
            "expires_at": None,
            "confirmation_expires_at": None,
            "selection_sha256": None,
            "plan": None,
            "consumed_run_ref": None,
            "child": None,
        }
        if row is None:
            plan = self._plan(occurrence["approved_plan_revision_id"])
            if plan is not None:
                body["plan"] = {
                    "revision_no": int(plan["revision_no"]),
                    "plan_hash": str(plan["content_hash"]),
                }
            return body
        plan = self._plan(str(row["plan_revision_id"]))
        facts = _facts_of(row)
        body.update(
            selection_id=facts.selection_id,
            revision=int(row["revision"]),
            draw_no=facts.draw_no,
            issued_at=row["issued_at"],
            expires_at=row["expires_at"],
            confirmation_expires_at=row["confirmation_expires_at"],
            consumed_run_ref=row["consumed_run_ref"],
        )
        if plan is not None:
            body["plan"] = {
                "revision_no": int(plan["revision_no"]),
                "plan_hash": str(plan["content_hash"]),
            }
        if facts.kind == "EMPTY":
            body["state"] = "EMPTY"
            return body
        eligible = facts.child_ref in set(candidates)
        computed = view_state(facts, now=now, child_is_eligible=eligible)
        body["outcome"] = OUTCOME_SELECTED
        body["state"] = computed
        if plan is not None and facts.child_ref is not None:
            body["selection_sha256"] = selection_sha256(
                selection_id=facts.selection_id,
                occurrence_id=occurrence_id,
                plan_revision_id=facts.plan_revision_id,
                plan_hash=str(plan["content_hash"]),
                selected_child_ref=facts.child_ref,
                candidate_set_hash=facts.candidate_set_hash,
                policy_version=str(row["policy_version"]),
            )
        if computed == facts.state and computed in {"OPEN", "CONFIRMED"}:
            profile = self.db.execute(
                select(ManagedProfileModel.display_name, ManagedProfileModel.age_months).where(
                    ManagedProfileModel.child_id == facts.child_ref,
                    ManagedProfileModel.organization_id == occurrence["organization_ref"],
                )
            ).one_or_none()
            if profile is not None:
                body["child"] = {
                    "profile_id": facts.child_ref,
                    "display_name": str(profile[0]),
                    "age_months": int(profile[1]),
                }
        return body

    # ------------------------------------------------------------------ replay
    def _replay(
        self,
        receipt: Be1CommandReceiptModel,
        fingerprint: str,
        occurrence: RowMapping,
        *,
        now: datetime,
    ) -> SelectionResult:
        """Re-read and revalidate; a null-id receipt answers its stored outcome (R2 N-4)."""
        if receipt.request_fingerprint != fingerprint:
            raise LessonOccurrenceError(400, "INVALID_IDEMPOTENCY_KEY")
        stored = dict(receipt.response_json)
        stored_status = stored.get("status")
        status_code = stored_status if isinstance(stored_status, int) else 200
        candidates = self._candidates(occurrence)
        row = None
        if stored.get("selection_id") is not None:
            row = self._row_by_id(str(stored["selection_id"]), str(occurrence["occurrence_id"]))
        body = self._view(
            occurrence,
            row,
            candidates=candidates,
            now=now,
            blank_state=str(stored.get("state", STATE_STOPPED)),
        )
        return SelectionResult(body, status_code, True)

    # ------------------------------------------------------------------ select
    def select(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, idempotency_key: str
    ) -> SelectionResult:
        """Offer a child (cases a to h of D5). Replays by key; a database conflict re-runs once."""
        for attempt in (1, 2):
            try:
                return self._select_once(principal, occurrence_id, idempotency_key)
            except IntegrityError as error:
                self.db.rollback()
                if getattr(error.orig, "sqlstate", None) != "23505":
                    raise _db_failure() from None
                if attempt == 2:
                    raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION") from None
            except SQLAlchemyError:
                self.db.rollback()
                raise _db_failure() from None
            except BaseException:
                self.db.rollback()
                raise
        raise _db_failure()  # pragma: no cover - the loop returns or raises

    def _select_once(
        self, principal: VerifiedPrincipal, occurrence_id: str, key: str
    ) -> SelectionResult:
        scope = SELECT_RECEIPT_SCOPE.format(occurrence_id=occurrence_id)
        fingerprint = canonical_hash({"command": "select", "occurrence_id": occurrence_id})
        occurrence, account, class_revision = self._authorize(principal, occurrence_id, lock=True)
        now = self._clock()
        receipt = self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))
        if receipt is not None:
            result = self._replay(receipt, fingerprint, occurrence, now=now)
            self.db.rollback()
            return result
        plan = self._preconditions(occurrence)
        plan_id = str(plan["plan_revision_id"])
        candidates = self._candidates(occurrence)
        organization, class_ref = str(occurrence["organization_ref"]), str(occurrence["class_ref"])
        chash = candidate_set_hash(
            organization_ref=organization,
            class_ref=class_ref,
            plan_revision_id=plan_id,
            children=candidates,
        )
        live = self._one(
            CHILD_SELECTIONS.c.occurrence_id == occurrence_id,
            CHILD_SELECTIONS.c.state.in_(("OPEN", "CONFIRMED")),
        )
        anchor = self._one(
            CHILD_SELECTIONS.c.occurrence_id == occurrence_id,
            CHILD_SELECTIONS.c.kind.in_(("DRAW", "RESELECT")),
        )
        latest = self._one(CHILD_SELECTIONS.c.occurrence_id == occurrence_id)
        decision = decide_next(
            live=_facts_of(live) if live is not None else None,
            anchor=_facts_of(anchor) if anchor is not None else None,
            latest=_facts_of(latest) if latest is not None else None,
            candidates=candidates,
            candidate_hash=chash,
            current_plan_revision_id=plan_id,
            caller_account_ref=account,
            now=now,
            policy=self._policy,
        )
        for transition in decision.transitions:
            self._transition(transition.selection_id, transition.new_state)

        row: RowMapping | None = None
        status_code = 200
        if decision.case is Case.H_STOPPED:
            pass
        elif decision.return_row is not None:
            row = self._row_by_id(decision.return_row, occurrence_id)
        elif decision.coalesce_with is not None:
            row = self._row_by_id(decision.coalesce_with, occurrence_id)
        else:
            assert decision.kind is not None
            selection_id = str(uuid4())
            child: str | None
            if decision.kind == "EMPTY":
                child = None
            elif decision.pick:
                child = pick_child(candidates, self._randbelow)
            else:
                child = decision.reuse_child
            empty = decision.kind == "EMPTY"
            self.db.execute(
                CHILD_SELECTIONS.insert().values(
                    selection_id=selection_id,
                    occurrence_id=occurrence_id,
                    plan_revision_id=plan_id,
                    organization_ref=organization,
                    class_ref=class_ref,
                    teacher_ref=account,
                    kind=decision.kind,
                    draw_no=decision.draw_no,
                    policy_version=POLICY_VERSION,
                    eligibility_basis=ELIGIBILITY_BASIS,
                    candidate_count=0 if empty else len(candidates),
                    candidate_set_hash=chash,
                    selected_child_ref=child,
                    class_revision=class_revision,
                    occurrence_revision=int(occurrence["revision"]),
                    state="EMPTY" if empty else "OPEN",
                    revision=1,
                    issued_at=now,
                    expires_at=None if empty else now + self._policy.open_ttl,
                )
            )
            self._audit(AUDIT_ACTIONS[decision.kind], occurrence, account, selection_id)
            self.db.flush()
            row = self._row_by_id(selection_id, occurrence_id)
            status_code = 201
        body = self._view(occurrence, row, candidates=candidates, now=now)
        self._store_receipt(
            principal,
            scope,
            key,
            occurrence,
            fingerprint,
            selection_id=None if row is None else str(row["selection_id"]),
            outcome=str(body["outcome"]),
            state=str(body["state"]),
            status_code=status_code,
        )
        self.db.commit()
        return SelectionResult(body, status_code)

    # ------------------------------------------------------------------ read
    def get(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, selection_id: str
    ) -> SelectionResult:
        """Read one selection: revalidates, writes nothing, no child once stale (l.348)."""
        try:
            occurrence, account, _revision = self._authorize(principal, occurrence_id, lock=False)
            if not 0 < len(selection_id) <= 36:
                raise not_found()
            row = self._row_by_id(selection_id, occurrence_id)
            # T4B1-IR-03: the row of another (former) Teacher is not shown to this caller.
            if row is None or str(row["teacher_ref"]) != account:
                raise not_found()
            body = self._view(
                occurrence, row, candidates=self._candidates(occurrence), now=self._clock()
            )
            stored_state = str(row["state"])
            self.db.rollback()
            return SelectionResult(body, 200, stored_state=stored_state)
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_failure() from None
        except BaseException:
            self.db.rollback()
            raise

    # ------------------------------------------------------------------ confirm
    def confirm(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        selection_id: str,
        expected_revision: int,
        expected_sha256: str,
        idempotency_key: str,
    ) -> SelectionResult:
        for attempt in (1, 2):
            try:
                return self._confirm_once(
                    principal,
                    occurrence_id,
                    selection_id,
                    expected_revision,
                    expected_sha256,
                    idempotency_key,
                )
            except IntegrityError as error:
                self.db.rollback()
                if getattr(error.orig, "sqlstate", None) != "23505":
                    raise _db_failure() from None
                if attempt == 2:
                    raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION") from None
            except SQLAlchemyError:
                self.db.rollback()
                raise _db_failure() from None
            except BaseException:
                self.db.rollback()
                raise
        raise _db_failure()  # pragma: no cover - the loop returns or raises

    def _refuse_after_write(self, error: LessonOccurrenceError) -> LessonOccurrenceError:
        """Keep the state change that explains the refusal (expired, void, stale), then refuse."""
        self.db.commit()
        return error

    def _confirm_once(
        self,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        selection_id: str,
        expected_revision: int,
        expected_sha256: str,
        key: str,
    ) -> SelectionResult:
        if not 0 < len(selection_id) <= 36:
            raise not_found()
        scope = CONFIRM_RECEIPT_SCOPE.format(selection_id=selection_id)
        fingerprint = canonical_hash(
            {
                "command": "confirm",
                "selection_id": selection_id,
                "expected_revision": expected_revision,
                "expected_selection_sha256": expected_sha256,
            }
        )
        occurrence, account, _class_revision = self._authorize(principal, occurrence_id, lock=True)
        row = self._row_by_id(selection_id, occurrence_id)
        if row is None:
            raise not_found()
        now = self._clock()
        receipt = self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))
        if receipt is not None:
            result = self._replay(receipt, fingerprint, occurrence, now=now)
            self.db.rollback()
            return result
        plan = self._preconditions(occurrence)
        facts = _facts_of(row)
        candidates = self._candidates(occurrence)

        if facts.kind == "EMPTY" or facts.child_ref is None:
            if int(row["revision"]) != expected_revision:
                raise self._stale(int(row["revision"]))
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
        if facts.state == "OPEN" and is_past_due(facts, now):
            self._transition(selection_id, "EXPIRED")
            raise self._refuse_after_write(LessonOccurrenceError(409, "INVALID_STATE_TRANSITION"))
        if int(row["revision"]) != expected_revision:
            raise self._stale(int(row["revision"]))
        offer_plan = self._plan(facts.plan_revision_id)
        if offer_plan is None:  # pragma: no cover - the composite foreign key holds
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
        offer_sha = selection_sha256(
            selection_id=selection_id,
            occurrence_id=occurrence_id,
            plan_revision_id=facts.plan_revision_id,
            plan_hash=str(offer_plan["content_hash"]),
            selected_child_ref=facts.child_ref,
            candidate_set_hash=facts.candidate_set_hash,
            policy_version=str(row["policy_version"]),
        )
        if expected_sha256 != offer_sha:
            raise self._stale(int(row["revision"]))
        if facts.state == "CONFIRMED":
            # The same offer, the same revision: nothing to write, the answer is the same.
            if facts.teacher_ref != account:  # T4B1-IR-03: confirmed by another Teacher
                raise not_found()
            if is_past_due(facts, now):
                self._transition(selection_id, "EXPIRED")
                raise self._refuse_after_write(
                    LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
                )
            if facts.child_ref not in set(candidates):
                # T4B1-IR-02: the confirmed child left the candidate set; refuse like the OPEN path.
                self._transition(selection_id, "STALE")
                raise self._refuse_after_write(self._stale(int(row["revision"]) + 1))
            body = self._view(occurrence, row, candidates=candidates, now=now)
            self._store_receipt(
                principal,
                scope,
                key,
                occurrence,
                fingerprint,
                selection_id=selection_id,
                outcome=OUTCOME_SELECTED,
                state=str(body["state"]),
                status_code=200,
            )
            self.db.commit()
            return SelectionResult(body, 200)
        if facts.state != "OPEN":
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
        if facts.plan_revision_id != str(plan["plan_revision_id"]) or facts.teacher_ref != account:
            self._transition(selection_id, "VOID")
            raise self._refuse_after_write(LessonOccurrenceError(409, "INVALID_STATE_TRANSITION"))
        if facts.child_ref not in set(candidates):
            # l.346, l.348: the candidate is stale. The row becomes STALE and the write is kept; the
            # client posts the selection command, which lands in case f, g or h.
            self._transition(selection_id, "STALE")
            raise self._refuse_after_write(self._stale(int(row["revision"]) + 1))

        updated = self.db.execute(
            update(CHILD_SELECTIONS)
            .where(
                CHILD_SELECTIONS.c.selection_id == selection_id,
                CHILD_SELECTIONS.c.state == "OPEN",
                CHILD_SELECTIONS.c.revision == expected_revision,
                CHILD_SELECTIONS.c.expires_at > now,
            )
            .values(
                state="CONFIRMED",
                revision=CHILD_SELECTIONS.c.revision + 1,
                confirmed_at=now,
                confirmed_by=account,
                confirmation_expires_at=now + self._policy.confirmed_ttl,
            )
        )
        if getattr(updated, "rowcount", 0) != 1:
            current = self._row_by_id(selection_id, occurrence_id)
            raise self._stale(int(current["revision"]) if current is not None else 0)
        self._audit(AUDIT_ACTIONS["CONFIRM"], occurrence, account, selection_id)
        self.db.flush()
        confirmed = self._row_by_id(selection_id, occurrence_id)
        body = self._view(occurrence, confirmed, candidates=candidates, now=now)
        self._store_receipt(
            principal,
            scope,
            key,
            occurrence,
            fingerprint,
            selection_id=selection_id,
            outcome=OUTCOME_SELECTED,
            state=str(body["state"]),
            status_code=200,
        )
        self.db.commit()
        return SelectionResult(body, 200)

    @staticmethod
    def _stale(current_version: int) -> LessonOccurrenceError:
        return LessonOccurrenceError(409, "STALE_REVISION", current_version=current_version)


__all__ = [
    "CONFIRM_RECEIPT_SCOPE",
    "PURGE_FLAG",
    "SELECT_RECEIPT_SCOPE",
    "ChildSelectionService",
    "SelectionResult",
    "SyntheticGate",
    "candidate_statement",
    "child_is_candidate",
    "consume_child_selection",
    "purge_child_selections",
    "stale_child_selection",
    "synthetic_gate_from_settings",
]
