"""SQL adapter for immutable Parent activity sets and Phase A activity selections."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_suggestion_sets import (
    ActivitySelectionOutcome,
    ActivitySuggestionSetReservation,
    CatalogActivityResolver,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.contracts.schemas.modal_ai import ParentSuggestedActivityV2
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _idempotency_key_hash,
    _live_run,
    _principal_scope_ref,
    _sha256_json,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_GENERATE_ACTIVITY_SET_OPERATION = "GENERATE_ACTIVITY_SET"
# Hardening (T-2e-b B-lite): at most five suggestion sets (rounds) per run.
MAX_ACTIVITY_SUGGESTION_SETS_PER_RUN = 5
_SELECT_ACTIVITY_OPERATION = "SELECT_ACTIVITY"
_ACTIVITY_PIN_SCHEMA = "sketch2life.parent-activity-pin.v1"
# Modal may run for 30 minutes; the extra five minutes lets an in-flight call finish before reuse.
PENDING_ACTIVITY_SET_RECEIPT_TIMEOUT = timedelta(minutes=35)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _snapshot_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _catalog_activity_key(item: Mapping[str, Any]) -> str | None:
    if item.get("source") not in {"PINNED_LESSON", "PUBLISHED_SHARED_LESSON"}:
        return None
    values = (
        item.get("source_lesson_id"),
        item.get("source_lesson_version_id"),
        item.get("source_content_sha256"),
        item.get("source_activity_index"),
    )
    if any(value is None for value in values):
        return None
    return f"{values[0]}:{values[1]}:{values[2]}:{values[3]}"


class SqlParentActivitySuggestionSetRepository(SqlParentStoryRunRepository):
    """Persist suggestion snapshots while reusing the Phase A run and receipt guards.

    The inherited helpers are deliberately the same ones used by the Phase A repository: owner
    scope, run locking, confirmed-subject checks, purge checks, idempotency receipts, and implicit
    first-story start all stay on the existing Story boundary.
    """

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def reserve_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        idempotency_key: str,
    ) -> ActivitySuggestionSetReservation:
        self._refuse_teacher()
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {"expected_understanding_revision": expected_understanding_revision}
        )
        try:
            run = self._owned_run(principal, run_id, lock=True)
            self._refuse_purged(run)
            now = self._now()
            self._lock_idempotency(
                principal=principal,
                operation=_GENERATE_ACTIVITY_SET_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
            )
            replay = self._find_idempotency_receipt(
                principal=principal,
                operation=_GENERATE_ACTIVITY_SET_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
            )
            reused_receipt_id: str | None = None
            if replay is not None and replay["state"] == "PENDING":
                created_at = replay["created_at"]
                if not isinstance(created_at, datetime):
                    raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)
                if now - created_at < PENDING_ACTIVITY_SET_RECEIPT_TIMEOUT:
                    raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
                reused_receipt_id = str(replay["receipt_id"])
                reclaimed = cast(
                    CursorResult[Any],
                    self._session.execute(
                        update(story_tables.story_command_receipts)
                        .where(
                            story_tables.story_command_receipts.c.receipt_id
                            == reused_receipt_id,
                            story_tables.story_command_receipts.c.operation
                            == _GENERATE_ACTIVITY_SET_OPERATION,
                            story_tables.story_command_receipts.c.state == "PENDING",
                        )
                        .values(
                            created_at=now,
                            resource_version=int(run["version"]),
                            state_version=story_tables.story_command_receipts.c.state_version
                            + 1,
                        )
                    ),
                )
                if reclaimed.rowcount != 1:
                    raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
                replay = None
            if replay is not None:
                body = replay["response_body"]
                if replay["state"] != "FINAL":
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                if not isinstance(body, dict):
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                error_code = body.get("error_code")
                if isinstance(error_code, str):
                    status = replay["response_status"]
                    if type(status) is not int or not 400 <= status <= 599:
                        raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                    raw_current_version = body.get("current_version")
                    current_version = (
                        raw_current_version
                        if isinstance(raw_current_version, int)
                        and not isinstance(raw_current_version, bool)
                        else None
                    )
                    raise ParentStoryRunError(
                        status, error_code, current_version=current_version
                    )
                try:
                    set_id = str(body["suggestion_set_id"])
                    set_revision = int(body["set_revision"])
                    snapshot_hash = str(body["activities_snapshot_sha256"])
                except (KeyError, TypeError, ValueError):
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
                replay_body = self._rebuild_activity_suggestion_set_response(
                    run=run,
                    suggestion_set_id=set_id,
                    set_revision=set_revision,
                    snapshot_hash=snapshot_hash,
                )
                self._session.commit()
                return ActivitySuggestionSetReservation(
                    receipt_id=str(replay["receipt_id"]),
                    suggestion_set_id=set_id,
                    set_revision=set_revision,
                    replay_body=replay_body,
                )

            self._require_activity_state(run)
            current_understanding = int(run["understanding_revision"] or 0)
            if current_understanding != expected_understanding_revision:
                raise ParentStoryRunError(
                    409, "STALE_REVISION", current_version=current_understanding
                )
            context = self._activity_context(principal, run)
            input_row = self._current_input(run)
            input_revision = int(input_row["input_revision"])
            raw_context_revision = input_row["context_revision"]
            if raw_context_revision is None:
                raise ParentStoryRunError(409, "PARENT_STORY_CONTEXT_UNAVAILABLE")
            context_revision = int(raw_context_revision)

            sets = story_tables.activity_suggestion_sets
            previous_sets = self._session.execute(
                select(sets.c.activities_snapshot)
                .where(
                    sets.c.run_id == run_id,
                    sets.c.understanding_revision == current_understanding,
                )
                .order_by(sets.c.set_revision)
            ).scalars().all()
            excluded_keys: set[str] = set()
            excluded_activities: list[Mapping[str, Any]] = []
            for activity_list in previous_sets:
                if not isinstance(activity_list, list):
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                for raw_activity in activity_list:
                    if not isinstance(raw_activity, dict):
                        raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                    excluded_activities.append(raw_activity)
                    candidate_key = _catalog_activity_key(raw_activity)
                    if candidate_key is not None:
                        excluded_keys.add(candidate_key)

            max_revision = int(
                self._session.scalar(
                    select(func.coalesce(func.max(sets.c.set_revision), 0)).where(
                        sets.c.run_id == run_id
                    )
                )
                or 0
            )
            if max_revision >= MAX_ACTIVITY_SUGGESTION_SETS_PER_RUN:
                # Replays of earlier sets were answered above; only a new set is refused.
                raise ParentStoryRunError(409, "RESOURCE_CONFLICT")
            set_id = str(uuid4())
            receipt_id = reused_receipt_id
            if receipt_id is None:
                receipt_id = self._store_pending_idempotency_receipt(
                    principal=principal,
                    operation=_GENERATE_ACTIVITY_SET_OPERATION,
                    scope_kind="STORY_RUN",
                    scope_ref=run_id,
                    key_hash=key_hash,
                    fingerprint=fingerprint,
                    run_id=run_id,
                    resource_version=int(run["version"]),
                    now=now,
                )
            self._session.commit()
            return ActivitySuggestionSetReservation(
                receipt_id=receipt_id,
                suggestion_set_id=set_id,
                # The final revision is assigned under the run lock when the set is appended.
                set_revision=max_revision + 1,
                context=context,
                input_revision=input_revision,
                context_revision=context_revision,
                excluded_candidate_keys=tuple(sorted(excluded_keys)),
                excluded_activities=tuple(excluded_activities),
            )
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def _rebuild_activity_suggestion_set_response(
        self,
        *,
        run: Mapping[str, Any],
        suggestion_set_id: str,
        set_revision: int,
        snapshot_hash: str,
    ) -> dict[str, Any]:
        sets = story_tables.activity_suggestion_sets
        stored = self._session.execute(
            select(sets).where(
                sets.c.run_id == str(run["run_id"]),
                sets.c.suggestion_set_id == suggestion_set_id,
            )
        ).mappings().one_or_none()
        if stored is None:
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
        activities = stored["activities_snapshot"]
        stored_hash = stored["activities_snapshot_sha256"]
        if (
            int(stored["set_revision"]) != set_revision
            or not isinstance(activities, list)
            or not 1 <= len(activities) <= 24
            or any(not isinstance(activity, dict) for activity in activities)
            or not isinstance(stored_hash, str)
            or not hmac.compare_digest(snapshot_hash, stored_hash)
            or not hmac.compare_digest(stored_hash, _snapshot_hash(activities))
        ):
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
        return {
            "contract": "ParentActivitySuggestionSetV1",
            "story_run_id": str(run["run_id"]),
            "suggestion_set_id": suggestion_set_id,
            "set_revision": set_revision,
            "understanding_revision": int(stored["understanding_revision"]),
            "selection_mode": str(stored["selection_mode"]),
            "catalog_candidate_count": int(stored["catalog_candidate_count"]),
            "activities_snapshot_sha256": stored_hash,
            "review_required": True,
            "modal_call_id": stored["provider_call_id"],
            "activities": activities,
        }

    def complete_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ActivitySuggestionSetReservation,
        response: Mapping[str, Any],
        provider_call_id: str | None,
    ) -> dict[str, Any]:
        if reservation.context is None:
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
        run_id = reservation.context.run_id
        try:
            run = self._owned_run(principal, run_id, lock=True)
            self._refuse_purged(run)
            self._require_activity_state(run)
            current_understanding = int(run["understanding_revision"] or 0)
            if current_understanding != reservation.context.understanding_revision:
                raise ParentStoryRunError(
                    409, "STALE_REVISION", current_version=current_understanding
                )
            self._activity_context(principal, run)
            input_row = self._current_input(run)
            if (
                int(input_row["input_revision"]) != reservation.input_revision
                or int(input_row["context_revision"]) != reservation.context_revision
            ):
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

            body = dict(response)
            activities = body.get("activities")
            if (
                not isinstance(activities, list)
                or not 1 <= len(activities) <= 24
                or any(not isinstance(item, dict) for item in activities)
            ):
                raise ParentStoryRunError(502, "MODAL_OUTPUT_CONTRACT_INVALID")
            if provider_call_id is not None and len(provider_call_id) > 128:
                raise ParentStoryRunError(502, "MODAL_OUTPUT_CONTRACT_INVALID")
            snapshot_sha256 = _snapshot_hash(activities)
            body["suggestion_set_id"] = reservation.suggestion_set_id
            body["activities_snapshot_sha256"] = snapshot_sha256
            body["modal_call_id"] = provider_call_id

            sets = story_tables.activity_suggestion_sets
            set_revision = int(
                self._session.scalar(
                    select(func.coalesce(func.max(sets.c.set_revision), 0)).where(
                        sets.c.run_id == run_id
                    )
                )
                or 0
            ) + 1
            if set_revision > MAX_ACTIVITY_SUGGESTION_SETS_PER_RUN:
                raise ParentStoryRunError(409, "RESOURCE_CONFLICT")
            body["set_revision"] = set_revision
            now = self._now()
            self._session.execute(
                insert(sets).values(
                    suggestion_set_id=reservation.suggestion_set_id,
                    run_id=run_id,
                    set_revision=set_revision,
                    understanding_revision=current_understanding,
                    input_revision=int(input_row["input_revision"]),
                    context_revision=int(input_row["context_revision"]),
                    selection_mode=body.get("selection_mode"),
                    catalog_candidate_count=body.get("catalog_candidate_count"),
                    activities_snapshot=activities,
                    activities_snapshot_sha256=snapshot_sha256,
                    provider_call_id=provider_call_id,
                    created_at=now,
                )
            )
            receipt_update = self._session.execute(
                update(story_tables.story_command_receipts)
                .where(
                    story_tables.story_command_receipts.c.receipt_id == reservation.receipt_id,
                    story_tables.story_command_receipts.c.operation
                    == _GENERATE_ACTIVITY_SET_OPERATION,
                    story_tables.story_command_receipts.c.state == "PENDING",
                    story_tables.story_command_receipts.c.resource_ref == run_id,
                )
                .values(
                    state="FINAL",
                    response_status=200,
                    response_resource_version=int(run["version"]),
                    response_body={
                        "suggestion_set_id": reservation.suggestion_set_id,
                        "set_revision": set_revision,
                        "activities_snapshot_sha256": snapshot_sha256,
                    },
                    resource_ref=run_id,
                    resource_version=int(run["version"]),
                    state_version=story_tables.story_command_receipts.c.state_version + 1,
                    finalized_at=now,
                )
            )
            if cast(CursorResult[Any], receipt_update).rowcount != 1:
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
            return body
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def fail_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ActivitySuggestionSetReservation,
        error_code: str,
        response_status: int,
        request_id: str,
        cache_failure: bool = False,
        current_version: int | None = None,
    ) -> None:
        try:
            command_kind, command_ref = self._command_scope(principal)
            receipts = story_tables.story_command_receipts
            receipt_filter = (
                receipts.c.receipt_id == reservation.receipt_id,
                receipts.c.actor_scope_kind == command_kind,
                receipts.c.actor_scope_ref == command_ref,
                receipts.c.operation == _GENERATE_ACTIVITY_SET_OPERATION,
                receipts.c.state == "PENDING",
            )
            if cache_failure and response_status in {409, 502}:
                response_body: dict[str, Any] = {
                    "error_code": error_code,
                    "request_id": request_id,
                }
                if current_version is not None:
                    response_body["current_version"] = current_version
                result = cast(
                    CursorResult[Any],
                    self._session.execute(
                        update(receipts)
                        .where(*receipt_filter)
                        .values(
                            state="FINAL",
                            response_status=response_status,
                            response_resource_version=receipts.c.resource_version,
                            response_body=response_body,
                            state_version=receipts.c.state_version + 1,
                            finalized_at=self._now(),
                        )
                    ),
                )
            else:
                result = cast(
                    CursorResult[Any],
                    self._session.execute(delete(receipts).where(*receipt_filter)),
                )
            if result.rowcount not in {0, 1}:
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def select_suggestion_set_activity(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        suggestion_set_id: str,
        expected_understanding_revision: int,
        activity_index: int,
        idempotency_key: str,
        resolve_catalog: CatalogActivityResolver,
    ) -> ActivitySelectionOutcome:
        self._refuse_teacher()
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "suggestion_set_id": suggestion_set_id,
                "expected_understanding_revision": expected_understanding_revision,
                "activity_index": activity_index,
            }
        )
        try:
            run = self._owned_run(principal, run_id, lock=True)
            self._refuse_purged(run)
            self._lock_idempotency(
                principal=principal,
                operation=_SELECT_ACTIVITY_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
            )
            replay = self._find_idempotency_receipt(
                principal=principal,
                operation=_SELECT_ACTIVITY_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
            )
            if replay is not None:
                body = replay["response_body"]
                if replay["state"] != "FINAL" or not isinstance(body, dict):
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                self._session.commit()
                return ActivitySelectionOutcome(receipt_body=dict(body))

            self._require_activity_state(run)
            context = self._activity_context(principal, run)
            if context.understanding_revision != expected_understanding_revision:
                raise ParentStoryRunError(
                    409,
                    "STALE_REVISION",
                    current_version=context.understanding_revision,
                )
            sets = story_tables.activity_suggestion_sets
            stored_set = self._session.execute(
                select(sets).where(
                    sets.c.run_id == run_id,
                    sets.c.suggestion_set_id == suggestion_set_id,
                )
            ).mappings().one_or_none()
            if stored_set is None:
                raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
            if int(stored_set["understanding_revision"]) != expected_understanding_revision:
                raise ParentStoryRunError(
                    409, "STALE_REVISION", current_version=context.understanding_revision
                )
            activities = stored_set["activities_snapshot"]
            if (
                not isinstance(activities, list)
                or not hmac.compare_digest(
                    str(stored_set["activities_snapshot_sha256"]), _snapshot_hash(activities)
                )
            ):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            if activity_index < 0 or activity_index >= len(activities):
                raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
            raw_item = activities[activity_index]
            if not isinstance(raw_item, dict):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            try:
                item = ParentSuggestedActivityV2.model_validate(raw_item).model_dump(mode="json")
            except (TypeError, ValueError):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

            now = self._now()
            if item["source"] == "AI_GENERATED_DRAFT":
                source_kind = "AI_DRAFT"
                lesson_id = version_id = content_sha256 = activity_index_db = None
                snapshot = {
                    "schema": _ACTIVITY_PIN_SCHEMA,
                    **item,
                    "selected_at": now.isoformat(),
                }
            else:
                pin = resolve_catalog(context, item)
                source_kind = "LESSON_ACTIVITY"
                lesson_id = pin.lesson_id
                version_id = pin.version_id
                content_sha256 = pin.content_sha256
                activity_index_db = pin.activity_index
                snapshot = {**pin.snapshot, "selected_at": now.isoformat()}

            selection_snapshot_sha256 = _snapshot_hash(snapshot)
            selections = story_tables.activity_selections
            selection_no = int(
                self._session.scalar(
                    select(func.coalesce(func.max(selections.c.selection_no), 0)).where(
                        selections.c.run_id == run_id
                    )
                )
                or 0
            ) + 1
            new_version = int(run["version"]) + 1
            new_revision = int(run["revision"]) + 1
            selection_id = str(uuid4())
            body = {
                "contract": "ParentActivitySelectionReceiptV1",
                "request_id": str(uuid4()),
                "story_run_id": run_id,
                "suggestion_set_id": suggestion_set_id,
                "activity_selection_id": selection_id,
                "selection_revision": selection_no,
                "understanding_revision": expected_understanding_revision,
                "activity_index": activity_index,
                "activity_snapshot_sha256": selection_snapshot_sha256,
                "persisted_at": now.isoformat(),
            }
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=_SELECT_ACTIVITY_OPERATION,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body=body,
                now=now,
                response_status=200,
            )
            command_kind, command_ref = self._command_scope(principal)
            self._session.execute(
                insert(selections).values(
                    selection_id=selection_id,
                    run_id=run_id,
                    selection_no=selection_no,
                    target_understanding_revision=expected_understanding_revision,
                    source_kind=source_kind,
                    lesson_id=lesson_id,
                    version_id=version_id,
                    content_sha256=content_sha256,
                    activity_index=activity_index_db,
                    activity_snapshot=snapshot,
                    activity_snapshot_sha256=selection_snapshot_sha256,
                    command_receipt_id=receipt_id,
                    actor_scope_kind=command_kind,
                    actor_scope_ref=_principal_scope_ref(principal),
                    created_at=now,
                )
            )
            run_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_runs)
                    .where(_live_run(run_id))
                    .values(version=new_version, revision=new_revision, updated_at=now)
                ),
            )
            if run_update.rowcount != 1:
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            story_reservation: ParentStoryRevisionReservation | None = (
                self._first_story_starter().start_if_ready(run_id, principal, now)
            )
            self._session.commit()
            return ActivitySelectionOutcome(
                receipt_body=body,
                story_reservation=story_reservation,
            )
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None


__all__ = ["SqlParentActivitySuggestionSetRepository"]
