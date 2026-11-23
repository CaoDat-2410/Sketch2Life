"""PostgreSQL creation of a Teacher StoryRun (FEAT-066 goal v3, T-4b2; SRS l.1445-1449, l.1663).

One transaction per create, serialised by the locks of the plan (D8): the occurrence ``FOR SHARE``,
its class ``FOR SHARE``, the selection ``FOR UPDATE``, then the new run (the lock order shared with
T-4b1 and T-5a). The caller is the responsible Teacher of the occurrence with an exact-class
``teacher`` row (``decide_child_data`` of T-4b1), decided on the current rows and decided again
under
the locks (FR-T-14). Only a confirmed selection of the CURRENT approved plan, for a child that is
still a candidate, creates a run: the run holds the Teacher lock (``active_owner_teacher_id``), the
occurrence pin and the plan and activity pins, and consumes the selection in the same transaction.

Nothing here claims the sample slot (OD-14: the claim is the first projection confirmation, T-5a),
calls a provider, enqueues a job or an outbox event, or touches quota or capacity. No child name,
media, seed or drawn index is stored (BR-34). The Story receipt follows the T-4a1 command scope
(``ORGANIZATION`` plus the principal digest), so two Teachers never collide on a key.
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import insert, or_, select, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import TEACHER_COMMAND_SCOPE_KIND
from sketch2life.application.ports.story_run_lifecycle import AUDIT_RESOURCE_TYPE
from sketch2life.contracts.schemas.teacher_story_runs import TeacherStoryRunCreateRequestV1
from sketch2life.domain.lesson_occurrences.child_selection import (
    decide_child_data,
    selection_sha256,
)
from sketch2life.domain.lesson_occurrences.model import AccessOutcome
from sketch2life.domain.lesson_occurrences.plan import PRE_APPROVAL_STATES
from sketch2life.domain.story_teacher import (
    build_context_snapshot,
    build_pin_snapshot,
    canonical_json,
    create_fingerprint,
    sha256_json,
)
from sketch2life.domain.story_video.model import has_ready_output
from sketch2life.infrastructure.lesson_occurrences.child_selection import (
    SyntheticGate,
    child_is_candidate,
    consume_child_selection,
    stale_child_selection,
)
from sketch2life.infrastructure.lesson_occurrences.scope import (
    class_is_read_only,
    load_caller_facts,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    CHILD_SELECTIONS,
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
)
from sketch2life.infrastructure.persistence.be1_models import ManagedProfileModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

OPERATION = "CREATE_RUN"
RECEIPT_SCOPE_KIND = "COLLECTION"
AUDIT_CREATE_ACTION = "story.run.create"
_NO_SLOT_STATES = ("DELETE_PENDING", "DELETED")
_UNAVAILABLE = (503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class TeacherCreateOutcome:
    run_id: str
    replayed: bool


def _principal_digest(principal: VerifiedPrincipal) -> str:
    """The command-scope reference of a Teacher: the same digest T-4a1 stamps on its receipts."""

    claims = {"issuer": principal.issuer, "subject": principal.subject}
    return hashlib.sha256(canonical_json(claims).encode("utf-8")).hexdigest()


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(getattr(error, "orig", None), "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None


def _stale(current_version: int) -> ParentStoryRunError:
    return ParentStoryRunError(409, "STALE_REVISION", current_version=current_version)


class TeacherStoryRunCreator:
    def __init__(self, session: Session, *, gate: SyntheticGate, clock: Clock = _utcnow) -> None:
        self._session = session
        self._gate = gate
        self._clock = clock

    # ------------------------------------------------------------------ entry point
    def create(
        self,
        *,
        principal: VerifiedPrincipal,
        body: TeacherStoryRunCreateRequestV1,
        idempotency_key: str,
    ) -> TeacherCreateOutcome:
        """Create the run of the confirmed selection, or replay the one the key already made.

        A database conflict rolls back and runs the pre-checks once more, so the answer of two
        racing creates is deterministic (``ACTIVE_RUN_EXISTS`` for the Teacher's own run); only a
        second conflict is mapped by its constraint name, never a 500 (R2 N-4).
        """

        for attempt in (1, 2):
            try:
                return self._create_once(principal, body, idempotency_key)
            except IntegrityError as error:
                self._session.rollback()
                if attempt == 1:
                    continue
                raise self._conflict(error) from None
            except SQLAlchemyError:
                self._session.rollback()
                raise ParentStoryRunError(*_UNAVAILABLE) from None
            except BaseException:
                self._session.rollback()
                raise
        raise ParentStoryRunError(*_UNAVAILABLE)  # pragma: no cover - the loop returns or raises

    @staticmethod
    def _conflict(error: IntegrityError) -> ParentStoryRunError:
        name = _constraint_name(error)
        if name == "uq_story_run_active_teacher":
            return ParentStoryRunError(409, "ACTIVE_RUN_EXISTS")
        if name == "uq_story_run_active_occurrence":
            return ParentStoryRunError(409, "TEACHER_ACTIVE_RUN_CONFLICT")
        if name in {"uq_sel_consumed_run", "uq_story_command_receipt_identity"}:
            return ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        return ParentStoryRunError(*_UNAVAILABLE)

    # ------------------------------------------------------------------ the transaction
    def _create_once(
        self, principal: VerifiedPrincipal, body: TeacherStoryRunCreateRequestV1, key: str
    ) -> TeacherCreateOutcome:
        session = self._session
        now = self._clock()
        wire = body.model_dump(mode="json")
        fingerprint = create_fingerprint(wire)
        key_hash = _key_hash(key)

        occurrence, account = self._authorize(principal, body.occurrence_id)
        if occurrence["state"] == "ARCHIVED":
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        organization = str(occurrence["organization_ref"])

        # (2) replay by key, after the caller was authorized again (FR-T-14, SRS l.1697)
        self._lock_key(principal, key_hash, account)
        receipt = self._find_receipt(principal, key_hash, account)
        if receipt is not None:
            if not hmac.compare_digest(str(receipt["request_fingerprint_sha256"]), fingerprint):
                raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
            session.commit()
            return TeacherCreateOutcome(str(receipt["resource_ref"]), replayed=True)

        # (3) the approved plan of the occurrence
        plan = self._approved_plan(occurrence)
        # (4) the requested revision and hash are the CURRENT approved plan
        if (
            int(plan["revision_no"]) != body.plan.revision_no
            or str(plan["content_hash"]) != body.plan.plan_hash
        ):
            raise _stale(int(plan["revision_no"]))
        # (5) one successful sample per occurrence (FR-T-13, OD-14)
        if occurrence["sample_slot_state"] != "AVAILABLE" or self._holds_ready_sample(
            str(occurrence["occurrence_id"])
        ):
            raise ParentStoryRunError(409, "SAMPLE_VIDEO_ALREADY_EXISTS")
        # (6) one activity of THAT plan
        activity = self._activity(str(plan["plan_revision_id"]), body.activity_id)
        # (8, before 7) the Teacher's own run and the occurrence's run: a clear 409 for a retry
        self._refuse_active_runs(account, str(occurrence["occurrence_id"]))
        # (7) the confirmed selection, bound to this plan, this body and the one child
        selection = self._selection(body, account, plan)
        child = self._child(organization, str(selection["selected_child_ref"]))
        if not child_is_candidate(
            session,
            self._gate,
            organization,
            str(occurrence["class_ref"]),
            str(selection["selected_child_ref"]),
        ):
            revision = stale_child_selection(session, str(selection["selection_id"]))
            session.commit()  # the STALE write is kept (l.346, l.348)
            raise _stale(int(revision) if revision is not None else int(selection["revision"]) + 1)

        # (9) the run, its first input revision, the receipt, the consumed selection, the audit row
        run_id = str(uuid4())
        context = build_context_snapshot(
            selection_id=str(selection["selection_id"]),
            age_months=int(child["age_months"]),
            age_revision=int(child["age_revision"]),
            objectives=list(plan["objectives"] or []),
            teacher_direction=str(plan["teacher_direction"]),
            activity_title=_activity_title(activity),
            activity_snapshot_hash=_text(activity["activity_snapshot_hash"]),
        )
        pin = build_pin_snapshot(
            occurrence_id=str(occurrence["occurrence_id"]),
            plan_revision_id=str(plan["plan_revision_id"]),
            plan_revision_no=int(plan["revision_no"]),
            plan_hash=str(plan["content_hash"]),
            activity={
                "plan_activity_id": str(activity["plan_activity_id"]),
                "kind": str(activity["activity_kind"]),
                "catalog_activity_ref": _text(activity["catalog_activity_ref"]),
                "activity_version": activity["activity_version"],
                "snapshot_hash": _text(activity["activity_snapshot_hash"]),
            },
            lesson=_lesson_lineage(plan),
        )
        session.execute(
            insert(story_tables.story_runs).values(
                run_id=run_id,
                actor_scope_kind=TEACHER_COMMAND_SCOPE_KIND,
                actor_scope_ref=organization,
                profile_ref=str(selection["selected_child_ref"]),
                child_age_months=int(child["age_months"]),
                run_state="INPUT_PROCESSING",
                revision=1,
                version=1,
                retryable=False,
                active_owner_teacher_id=account,
                occurrence_ref=str(occurrence["occurrence_id"]),
                created_by_actor_ref=account,
                current_input_revision=1,
                created_at=now,
                updated_at=now,
            )
        )
        session.execute(
            insert(story_tables.run_inputs).values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                # The selection id is a canonical uuid4 (ck_sel_id_uuid); the column is named for a
                # profile revision, which a Managed Profile does not have until DDL-D (DEC-3).
                source_profile_revision_ref=str(selection["selection_id"]),
                context_revision=1,
                context_snapshot=context,
                context_snapshot_sha256=sha256_json(context),
                lesson_pin_snapshot=pin,
                lesson_pin_snapshot_sha256=sha256_json(pin),
                context_confirmed_by=None,
                context_confirmed_at=None,
                created_at=now,
            )
        )
        self._store_receipt(principal, key_hash, account, fingerprint, run_id, now)
        if not consume_child_selection(
            session, str(selection["selection_id"]), run_ref=run_id, now=now
        ):
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        session.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=organization,
                actor_ref=account,
                action=AUDIT_CREATE_ACTION,
                resource_type=AUDIT_RESOURCE_TYPE,
                resource_id=run_id,
                # No child ref, no name: the selection id alone (BR-34).
                decision=str(selection["selection_id"]),
            )
        )
        session.commit()
        return TeacherCreateOutcome(run_id, replayed=False)

    # ------------------------------------------------------------------ authorization and locks
    def _occurrence(self, occurrence_id: str, *, lock: bool) -> RowMapping:
        statement = select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id)
        if lock:
            statement = statement.with_for_update(read=True)
        row = self._session.execute(statement).mappings().one_or_none()
        if row is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        return row

    def _decide(self, principal: VerifiedPrincipal, occurrence: RowMapping) -> str:
        facts = load_caller_facts(self._session, principal, str(occurrence["organization_ref"]))
        if facts is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        outcome = decide_child_data(
            facts.rows,
            str(occurrence["class_ref"]),
            caller_account_ref=facts.account_ref,
            responsible_teacher_ref=str(occurrence["responsible_teacher_ref"]),
        )
        if outcome is AccessOutcome.PROCEED:
            return facts.account_ref
        if outcome is AccessOutcome.FORBIDDEN:
            raise ParentStoryRunError(403, "ACTION_NOT_ALLOWED")
        raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    def _authorize(
        self, principal: VerifiedPrincipal, occurrence_id: str
    ) -> tuple[RowMapping, str]:
        """Decide on the current rows, lock the occurrence and its class ``FOR SHARE`` and decide
        again under the locks, so a revoked assignment is 404 at this call (FR-T-14)."""

        if not 0 < len(occurrence_id) <= 36:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        self._decide(principal, self._occurrence(occurrence_id, lock=False))
        occurrence = self._occurrence(occurrence_id, lock=True)
        read_only = class_is_read_only(self._session, occurrence, lock=True)
        self._session.expire_all()
        account = self._decide(principal, occurrence)
        if read_only:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        return occurrence, account

    # ------------------------------------------------------------------ the facts
    def _approved_plan(self, occurrence: RowMapping) -> RowMapping:
        """The approved plan of the occurrence, else 422 ``LESSON_PLAN_NOT_APPROVED`` (l.871)."""

        pointer = occurrence["approved_plan_revision_id"]
        if pointer is None or occurrence["state"] in PRE_APPROVAL_STATES:
            raise ParentStoryRunError(422, "LESSON_PLAN_NOT_APPROVED")
        plan = (
            self._session.execute(
                select(PLAN_REVISIONS).where(PLAN_REVISIONS.c.plan_revision_id == pointer)
            )
            .mappings()
            .one_or_none()
        )
        if plan is None or plan["state"] != "APPROVED":
            raise ParentStoryRunError(422, "LESSON_PLAN_NOT_APPROVED")
        return plan

    def _holds_ready_sample(self, occurrence_id: str) -> bool:
        """OD-14 window: a run that was completed without being projected still holds a ready,
        safety-passed sample. A cancelled or deleted run, a failed generation and a safety block do
        not hold the slot (SRS l.552, l.1449)."""

        generations = story_tables.video_generations
        runs = story_tables.story_runs
        rows = self._session.execute(
            select(
                generations.c.state,
                generations.c.technical_validation_state,
                generations.c.consistency_validation_state,
                generations.c.safety_validation_state,
                generations.c.output_asset_ref,
            )
            .join(runs, runs.c.current_video_generation_id == generations.c.video_generation_id)
            .where(
                runs.c.occurrence_ref == occurrence_id,
                runs.c.run_state.not_in(_NO_SLOT_STATES),
            )
        ).all()
        return any(
            has_ready_output(
                generation_state=str(row[0]),
                technical=str(row[1]),
                consistency=str(row[2]),
                safety=str(row[3]),
                has_output=row[4] is not None,
            )
            for row in rows
        )

    def _activity(self, plan_revision_id: str, activity_id: str) -> RowMapping:
        row = (
            self._session.execute(
                select(PLAN_ACTIVITIES).where(
                    PLAN_ACTIVITIES.c.plan_activity_id == activity_id,
                    PLAN_ACTIVITIES.c.plan_revision_id == plan_revision_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise ParentStoryRunError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "activity_id", "code": "INVALID_FORMAT"}],
            )
        return row

    def _refuse_active_runs(self, account: str, occurrence_id: str) -> None:
        """One statement for the Teacher's own run and the occurrence's run (R1 F-1).

        Two statements could see two states of a concurrent winner in READ COMMITTED. With one, the
        Teacher's own run always wins: ``ACTIVE_RUN_EXISTS`` (SRS l.1698); the reserved
        ``TEACHER_ACTIVE_RUN_CONFLICT`` only when every hit is another owner's run.
        """

        runs = story_tables.story_runs
        owners = (
            self._session.execute(
                select(runs.c.active_owner_teacher_id).where(
                    runs.c.active_owner_teacher_id.is_not(None),
                    or_(
                        runs.c.active_owner_teacher_id == account,
                        runs.c.occurrence_ref == occurrence_id,
                    ),
                )
            )
            .scalars()
            .all()
        )
        if not owners:
            return
        if account in owners:
            raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS")
        raise ParentStoryRunError(409, "TEACHER_ACTIVE_RUN_CONFLICT")

    def _selection(
        self, body: TeacherStoryRunCreateRequestV1, account: str, plan: RowMapping
    ) -> RowMapping:
        """The confirmed selection of this occurrence and this Teacher, loaded ``FOR UPDATE`` and
        bound to the approved plan, to ``selection_sha256`` and to the one child (R1 F-2)."""

        row = (
            self._session.execute(
                select(CHILD_SELECTIONS)
                .where(
                    CHILD_SELECTIONS.c.selection_id == body.selection_id,
                    CHILD_SELECTIONS.c.occurrence_id == body.occurrence_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None or str(row["teacher_ref"]) != account or row["selected_child_ref"] is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        # Again, now that the row is ours: a loser that waited for the winner's selection lock sees
        # the winner's run and answers ACTIVE_RUN_EXISTS, not a dead selection (R1 F-1, l.1698).
        self._refuse_active_runs(account, body.occurrence_id)
        if str(row["plan_revision_id"]) != str(plan["plan_revision_id"]):
            raise _stale(int(plan["revision_no"]))
        expected = selection_sha256(
            selection_id=str(row["selection_id"]),
            occurrence_id=body.occurrence_id,
            plan_revision_id=str(row["plan_revision_id"]),
            plan_hash=str(plan["content_hash"]),
            selected_child_ref=str(row["selected_child_ref"]),
            candidate_set_hash=str(row["candidate_set_hash"]),
            policy_version=str(row["policy_version"]),
        )
        if not hmac.compare_digest(expected, body.selection_sha256):
            raise _stale(int(plan["revision_no"]))
        if body.profile_ref.id != str(row["selected_child_ref"]):
            # No Teacher branch picks a child (FR-T-10): another single child is a bad request.
            raise ParentStoryRunError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "profile_ref.id", "code": "INVALID_FORMAT"}],
            )
        confirmation_deadline = row["confirmation_expires_at"]
        if (
            row["state"] != "CONFIRMED"
            or confirmation_deadline is None
            or self._clock() >= confirmation_deadline
        ):
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        return row

    def _child(self, organization: str, child_ref: str) -> RowMapping:
        row = (
            self._session.execute(
                select(ManagedProfileModel.age_months, ManagedProfileModel.age_revision).where(
                    ManagedProfileModel.organization_id == organization,
                    ManagedProfileModel.child_id == child_ref,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        return row

    # ------------------------------------------------------------------ the receipt
    def _lock_key(self, principal: VerifiedPrincipal, key_hash: str, account: str) -> None:
        material = canonical_json(
            {
                "issuer": principal.issuer,
                "subject": principal.subject,
                "operation": OPERATION,
                "scope_kind": RECEIPT_SCOPE_KIND,
                "scope_ref": account,
                "key_hash": key_hash,
            }
        ).encode("utf-8")
        lock_key = int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=True)
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
        )

    def _find_receipt(
        self, principal: VerifiedPrincipal, key_hash: str, account: str
    ) -> RowMapping | None:
        receipts = story_tables.story_command_receipts
        return (
            self._session.execute(
                select(receipts).where(
                    receipts.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND,
                    receipts.c.actor_scope_ref == _principal_digest(principal),
                    receipts.c.operation == OPERATION,
                    receipts.c.idempotency_scope_kind == RECEIPT_SCOPE_KIND,
                    receipts.c.idempotency_scope_ref == account,
                    receipts.c.idempotency_key_sha256 == key_hash,
                )
            )
            .mappings()
            .one_or_none()
        )

    def _store_receipt(
        self,
        principal: VerifiedPrincipal,
        key_hash: str,
        account: str,
        fingerprint: str,
        run_id: str,
        now: datetime,
    ) -> None:
        self._session.execute(
            insert(story_tables.story_command_receipts).values(
                receipt_id=str(uuid4()),
                actor_scope_kind=TEACHER_COMMAND_SCOPE_KIND,
                actor_scope_ref=_principal_digest(principal),
                operation=OPERATION,
                idempotency_scope_kind=RECEIPT_SCOPE_KIND,
                idempotency_scope_ref=account,
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="FINAL",
                response_status=201,
                response_resource_version=1,
                response_body={"run_id": run_id},
                resource_ref=run_id,
                resource_version=1,
                state_version=1,
                created_at=now,
                finalized_at=now,
            )
        )


def _key_hash(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 256:
        raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _text(value: object) -> str | None:
    return None if value is None else str(value)


def _activity_title(activity: RowMapping) -> str | None:
    if activity["custom_title"]:
        return str(activity["custom_title"])
    snapshot = activity["activity_snapshot"]
    if isinstance(snapshot, dict) and isinstance(snapshot.get("title"), str):
        return str(snapshot["title"])
    return None


def _lesson_lineage(plan: RowMapping) -> dict[str, Any] | None:
    if plan["source_lesson_id"] is None or plan["source_lesson_version_id"] is None:
        return None
    return {
        "lesson_id": str(plan["source_lesson_id"]),
        "version_id": str(plan["source_lesson_version_id"]),
        "version_no": int(plan["source_lesson_version_no"]),
        "version_hash": str(plan["source_lesson_version_hash"]),
    }


__all__ = ["TeacherCreateOutcome", "TeacherStoryRunCreator"]
