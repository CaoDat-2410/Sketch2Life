"""Atomic Story adapter for Manager emergency force-close and durable receipts."""

from __future__ import annotations

import hmac
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.story_run_force_close import (
    ManagerStoryRunConflict,
    ManagerStoryRunForceClosed,
    ManagerStoryRunForceCloseFailure,
)
from sketch2life.domain.teacher_run_force_close import (
    FORCE_CLOSE_RUN_OPERATION,
    StoryRunForceCloseReceiptIdentity,
    StoryRunForceCloseRuleError,
    force_close_transition,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_RECEIPT_CONTRACT = "ManagerForceClosedStoryRunV1"
_RECEIPT_SCOPE_KIND = "STORY_RUN"
_AUDIT_ACTION = "TEACHER_STORY_RUN_FORCE_CLOSED"


class SqlManagerStoryRunForceCloseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_active_conflict(
        self, *, organization_id: str, teacher_ref: str
    ) -> ManagerStoryRunConflict | None:
        runs = story_tables.story_runs
        statement = (
            select(runs.c.run_id, runs.c.run_state, runs.c.revision)
            .where(
                runs.c.organization_ref == organization_id,
                runs.c.actor_scope_kind == "ORGANIZATION",
                runs.c.actor_scope_ref == organization_id,
                runs.c.active_owner_teacher_id == teacher_ref,
            )
            .limit(2)
        )
        try:
            rows = self._session.execute(statement).mappings().all()
        except SQLAlchemyError:
            self._session.rollback()
            raise ManagerStoryRunForceCloseFailure(
                503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
            ) from None
        if len(rows) > 1:
            raise ManagerStoryRunForceCloseFailure(409, "RESOURCE_CONFLICT")
        if not rows:
            return None
        row = rows[0]
        return ManagerStoryRunConflict(
            run_id=str(row["run_id"]),
            run_state=str(row["run_state"]),
            revision=int(row["revision"]),
        )

    def force_close(
        self,
        *,
        organization_id: str,
        run_id: str,
        expected_revision: int,
        identity: StoryRunForceCloseReceiptIdentity,
        audit_actor_ref: str,
    ) -> ManagerStoryRunForceClosed:
        runs = story_tables.story_runs
        receipts = story_tables.story_command_receipts
        run_statement = (
            select(
                runs.c.run_id,
                runs.c.actor_scope_kind,
                runs.c.actor_scope_ref,
                runs.c.run_state,
                runs.c.revision,
                runs.c.version,
                runs.c.active_owner_teacher_id,
            )
            .where(
                runs.c.run_id == run_id,
                runs.c.organization_ref == organization_id,
                runs.c.actor_scope_kind == "ORGANIZATION",
                runs.c.actor_scope_ref == organization_id,
            )
            .with_for_update()
        )
        try:
            run = self._session.execute(run_statement).mappings().one_or_none()
            if run is None:
                raise ManagerStoryRunForceCloseFailure(404, "RESOURCE_NOT_FOUND")

            receipt = self._session.execute(
                select(receipts).where(
                    receipts.c.actor_scope_kind == "ORGANIZATION",
                    receipts.c.actor_scope_ref == organization_id,
                    receipts.c.operation == FORCE_CLOSE_RUN_OPERATION,
                    receipts.c.idempotency_scope_kind == _RECEIPT_SCOPE_KIND,
                    receipts.c.idempotency_scope_ref == identity.idempotency_scope_ref,
                    receipts.c.idempotency_key_sha256 == identity.idempotency_key_sha256,
                )
            ).mappings().one_or_none()
            if receipt is not None:
                result = _replay_receipt(
                    receipt,
                    expected_fingerprint=identity.request_fingerprint_sha256,
                    run_id=run_id,
                )
                self._session.commit()
                return result

            try:
                transition = force_close_transition(
                    run_state=str(run["run_state"]),
                    active_owner_teacher_id=run["active_owner_teacher_id"],
                    expected_revision=expected_revision,
                    current_revision=int(run["revision"]),
                    current_version=int(run["version"]),
                )
            except StoryRunForceCloseRuleError as exc:
                status = (
                    409
                    if exc.code in {"STALE_REVISION", "INVALID_STATE_TRANSITION"}
                    else 400
                )
                raise ManagerStoryRunForceCloseFailure(
                    status,
                    exc.code,
                    current_version=exc.current_version,
                ) from None

            now = datetime.now(UTC)
            updated = self._session.execute(
                update(runs)
                .where(
                    runs.c.run_id == run_id,
                    runs.c.organization_ref == organization_id,
                    runs.c.actor_scope_kind == "ORGANIZATION",
                    runs.c.actor_scope_ref == organization_id,
                    runs.c.revision == int(run["revision"]),
                    runs.c.version == int(run["version"]),
                    runs.c.active_owner_teacher_id == run["active_owner_teacher_id"],
                )
                .values(
                    run_state=transition.run_state,
                    revision=transition.revision,
                    version=transition.version,
                    finished_at=now,
                    updated_at=now,
                )
                .returning(
                    runs.c.run_id,
                    runs.c.run_state,
                    runs.c.revision,
                    runs.c.active_owner_teacher_id,
                )
            ).mappings().one_or_none()
            if updated is None:
                raise ManagerStoryRunForceCloseFailure(409, "RESOURCE_CONFLICT")
            if (
                updated["run_state"] != "ABANDONED"
                or updated["active_owner_teacher_id"] is not None
                or int(updated["revision"]) != transition.revision
            ):
                raise ManagerStoryRunForceCloseFailure(
                    503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
                )

            response_body = {
                "contract": _RECEIPT_CONTRACT,
                "run_id": run_id,
                "run_state": "ABANDONED",
                "revision": transition.revision,
            }
            self._session.execute(
                receipts.insert().values(
                    receipt_id=str(uuid4()),
                    actor_scope_kind="ORGANIZATION",
                    actor_scope_ref=organization_id,
                    operation=FORCE_CLOSE_RUN_OPERATION,
                    idempotency_scope_kind=_RECEIPT_SCOPE_KIND,
                    idempotency_scope_ref=identity.idempotency_scope_ref,
                    idempotency_key_sha256=identity.idempotency_key_sha256,
                    request_fingerprint_sha256=identity.request_fingerprint_sha256,
                    state="FINAL",
                    response_status=200,
                    response_resource_version=transition.revision,
                    response_body=response_body,
                    resource_ref=run_id,
                    resource_version=transition.revision,
                    state_version=1,
                    created_at=now,
                    finalized_at=now,
                )
            )
            self._record_audit(
                organization_id=organization_id,
                run_id=run_id,
                actor_ref=audit_actor_ref,
            )
            self._session.commit()
            return ManagerStoryRunForceClosed(run_id=run_id, revision=transition.revision)
        except ManagerStoryRunForceCloseFailure:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise ManagerStoryRunForceCloseFailure(409, "RESOURCE_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ManagerStoryRunForceCloseFailure(
                503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
            ) from None

    def _record_audit(
        self, *, organization_id: str, run_id: str, actor_ref: str
    ) -> None:
        self._session.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=organization_id,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=organization_id,
                actor_ref=actor_ref,
                action=_AUDIT_ACTION,
                resource_type="STORY_RUN",
                resource_id=run_id,
                decision="ALLOWED",
            )
        )


def _replay_receipt(
    receipt: RowMapping,
    *,
    expected_fingerprint: str,
    run_id: str,
) -> ManagerStoryRunForceClosed:
    if not hmac.compare_digest(
        str(receipt["request_fingerprint_sha256"]), expected_fingerprint
    ):
        raise ManagerStoryRunForceCloseFailure(400, "INVALID_IDEMPOTENCY_KEY")
    body = receipt["response_body"]
    if (
        receipt["state"] != "FINAL"
        or receipt["response_status"] != 200
        or receipt["resource_ref"] != run_id
        or not isinstance(body, dict)
        or set(body) != {"contract", "run_id", "run_state", "revision"}
        or body.get("contract") != _RECEIPT_CONTRACT
        or body.get("run_id") != run_id
        or body.get("run_state") != "ABANDONED"
        or type(body.get("revision")) is not int
        or body["revision"] < 1
    ):
        raise ManagerStoryRunForceCloseFailure(409, "RESOURCE_CONFLICT")
    return ManagerStoryRunForceClosed(run_id=run_id, revision=body["revision"])


__all__ = ["SqlManagerStoryRunForceCloseRepository"]
