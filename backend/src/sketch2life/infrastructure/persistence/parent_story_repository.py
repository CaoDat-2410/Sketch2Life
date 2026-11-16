"""PostgreSQL adapter for Parent StoryRuns, immutable context, artwork, and reviews."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import insert, select, text, update
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import ParentStoryProfileReference
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryInputRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
_PARENT_CONTEXT_SCHEMA = "sketch2life.parent-context.v1"
_PARENT_CONTEXT_MAX_BYTES = 32_768


class SqlParentStoryRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        profile: ParentStoryProfileReference,
        idempotency_key: str,
        run_id: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_version_ref: dict[str, str] | None = None,
        lesson_pin_snapshot: dict[str, Any] | None = None,
    ) -> ParentStoryRunRecord:
        owner_scope_ref = _principal_scope_ref(principal)
        scope_kind = "COLLECTION"
        scope_ref = account_id
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _create_run_fingerprint(
            parent_profile_id=profile.profile_id,
            topic=topic,
            adult_confirmed_idea=adult_confirmed_idea,
            lesson_version_ref=lesson_version_ref,
        )
        self._lock_idempotency(
            principal=principal,
            operation="CREATE_RUN",
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation="CREATE_RUN",
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            replay_run_id = str(replay["resource_ref"])
            self._session.commit()
            return self.get_run(principal=principal, run_id=replay_run_id)

        existing_run = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                story_tables.story_runs.c.actor_scope_ref == owner_scope_ref,
                story_tables.story_runs.c.active_owner_parent_account_id == account_id,
            )
        )
        if existing_run is not None:
            raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS")

        now = datetime.now(UTC)
        context = {
            "schema_version": _PARENT_CONTEXT_SCHEMA,
            "profile_revision_ref": str(profile.profile_revision_id),
            "age_months": profile.age_months,
            "interests_summary": profile.interests_summary or "",
            "topic": topic,
            "adult_confirmed_idea": adult_confirmed_idea,
        }
        context_hash = _sha256_json(context)
        if len(_canonical_json(context).encode("utf-8")) > _PARENT_CONTEXT_MAX_BYTES:
            raise ParentStoryRunError(422, "INVALID_REQUEST")
        lesson_pin = dict(lesson_pin_snapshot) if lesson_pin_snapshot is not None else None
        lesson_pin_hash = _sha256_json(lesson_pin) if lesson_pin is not None else None
        run_input_id = str(uuid4())
        try:
            self._session.execute(
                insert(story_tables.story_runs).values(
                    run_id=run_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_scope_ref,
                    profile_ref=str(profile.profile_id),
                    child_age_months=profile.age_months,
                    run_state="INPUT_PROCESSING",
                    revision=1,
                    version=1,
                    retryable=False,
                    active_owner_parent_account_id=account_id,
                    current_input_revision=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._session.execute(
                insert(story_tables.run_inputs).values(
                    run_input_id=run_input_id,
                    run_id=run_id,
                    input_revision=1,
                    typed_idea=adult_confirmed_idea or None,
                    idea_source="TEXT" if adult_confirmed_idea else None,
                    source_profile_revision_ref=str(profile.profile_revision_id),
                    context_revision=1,
                    context_snapshot=context,
                    context_snapshot_sha256=context_hash,
                    lesson_pin_snapshot=lesson_pin,
                    lesson_pin_snapshot_sha256=lesson_pin_hash,
                    context_confirmed_by=None,
                    context_confirmed_at=None,
                    created_at=now,
                )
            )
            self._store_idempotency_receipt(
                principal=principal,
                operation="CREATE_RUN",
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=1,
                response_body={"run_id": run_id},
                now=now,
                response_status=201,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if _integrity_constraint_name(exc) == "uq_story_run_active_parent":
                raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS") from None
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            principal=principal,
            run_id=run_id,
        )

    def replay_create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        parent_profile_id: UUID,
        idempotency_key: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_version_ref: dict[str, str] | None = None,
    ) -> ParentStoryRunRecord | None:
        scope_kind = "COLLECTION"
        scope_ref = account_id
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _create_run_fingerprint(
            parent_profile_id=parent_profile_id,
            topic=topic,
            adult_confirmed_idea=adult_confirmed_idea,
            lesson_version_ref=lesson_version_ref,
        )
        try:
            self._lock_idempotency(
                principal=principal,
                operation="CREATE_RUN",
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
            )
            replay = self._find_idempotency_receipt(
                principal=principal,
                operation="CREATE_RUN",
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
                fingerprint=fingerprint,
            )
            if replay is None:
                return None
            replay_run_id = str(replay["resource_ref"])
            self._session.commit()
        except ParentStoryRunError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(principal=principal, run_id=replay_run_id)

    def get_run(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentStoryRunRecord:
        run = self._owned_run(principal, run_id)
        input_row = self._current_input(run)
        latest_story = self._session.execute(
            select(story_tables.story_revisions)
            .where(story_tables.story_revisions.c.run_id == run_id)
            .order_by(story_tables.story_revisions.c.revision_no.desc())
            .limit(1)
        ).mappings().one_or_none()
        latest_understanding = self._latest_understanding(run_id)
        candidate = None
        if latest_understanding is not None:
            snapshot = latest_understanding["result_snapshot"]
            result = snapshot.get("result") if isinstance(snapshot, dict) else None
            candidate = dict(result) if isinstance(result, dict) else None
        story_content = None
        if latest_story is not None and latest_story["story_content"] is not None:
            sections = latest_story["story_content"]
            scenes = self._session.execute(
                select(story_tables.story_scenes)
                .where(
                    story_tables.story_scenes.c.story_revision_id
                    == latest_story["story_revision_id"]
                )
                .order_by(story_tables.story_scenes.c.scene_index)
            ).mappings().all()
            story_content = {
                "schema_version": latest_story["schema_version"],
                "language": latest_story["language"],
                "title": latest_story["title"],
                "story": sections,
                "duration_ms": latest_story["duration_ms"],
                "scenes": [
                    {
                        "scene_index": scene["scene_index"],
                        "title": scene["title"],
                        "action": scene["action"],
                        "narration": scene["narration"],
                        "start_ms": scene["start_ms"],
                        "duration_ms": scene["duration_ms"],
                    }
                    for scene in scenes
                ],
            }
        return ParentStoryRunRecord(
            run_id=run_id,
            run_state=str(run["run_state"]),
            parent_profile_id=UUID(str(run["profile_ref"])),
            profile_revision_ref=UUID(str(input_row["source_profile_revision_ref"])),
            context_revision=int(input_row["context_revision"]),
            context_confirmed=(
                input_row["context_confirmed_by"] is not None
                and input_row["context_confirmed_at"] is not None
            ),
            context_snapshot=dict(input_row["context_snapshot"]),
            context_snapshot_sha256=str(input_row["context_snapshot_sha256"]),
            lesson_pin_snapshot=(
                dict(input_row["lesson_pin_snapshot"])
                if input_row["lesson_pin_snapshot"] is not None
                else None
            ),
            current_input_revision=(
                int(run["current_input_revision"])
                if run["current_input_revision"] is not None
                else None
            ),
            understanding_revision=(
                int(run["understanding_revision"])
                if run["understanding_revision"] is not None
                else None
            ),
            subject_label=run["subject_label"],
            candidate=candidate,
            story_revision_id=(
                str(latest_story["story_revision_id"]) if latest_story is not None else None
            ),
            story_revision_no=(
                int(latest_story["revision_no"]) if latest_story is not None else None
            ),
            story_status=str(latest_story["status"]) if latest_story is not None else None,
            story_sha256=latest_story["story_sha256"] if latest_story is not None else None,
            story_content=story_content,
            job_state=run["job_state"],
            retryable=bool(run["retryable"]),
            error_code=run["error_code"],
            created_at=run["created_at"],
            updated_at=run["updated_at"],
        )

    def get_active_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunRecord | None:
        run_id = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                story_tables.story_runs.c.actor_scope_ref == _principal_scope_ref(principal),
                story_tables.story_runs.c.active_owner_parent_account_id == account_id,
            )
        )
        if run_id is None:
            return None
        return self.get_run(
            principal=principal,
            run_id=str(run_id),
        )

    def confirm_context(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_context_revision: int,
        expected_context_snapshot_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunRecord:
        operation = "CONFIRM_CONTEXT"
        scope_kind = "STORY_RUN"
        scope_ref = run_id
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_context_revision": expected_context_revision,
                "context_snapshot_sha256": expected_context_snapshot_sha256,
                "confirmed": True,
            }
        )
        run = self._owned_run(principal, run_id, lock=True)
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            self._session.commit()
            return self.get_run(principal=principal, run_id=run_id)

        input_row = self._current_input(run)
        context_revision = int(input_row["context_revision"] or 0)
        context_hash = str(input_row["context_snapshot_sha256"] or "")
        if (
            context_revision != expected_context_revision
            or not hmac.compare_digest(context_hash, expected_context_snapshot_sha256)
        ):
            raise ParentStoryRunError(409, "STALE_REVISION")
        if run["run_state"] not in {
            "INPUT_PROCESSING",
            "SUBJECT_REVIEW",
            "PREPARATION_REVIEW",
        }:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

        now = datetime.now(UTC)
        new_version = int(run["version"])
        if input_row["context_confirmed_by"] is None:
            new_version += 1
            self._session.execute(
                update(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_input_id == input_row["run_input_id"])
                .values(
                    context_confirmed_by=_principal_scope_ref(principal),
                    context_confirmed_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
        try:
            self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind=scope_kind,
                scope_ref=scope_ref,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={"context_revision": context_revision},
                now=now,
                response_status=200,
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "INVALID_IDEMPOTENCY_KEY") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(principal=principal, run_id=run_id)

    def attach_artwork(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        original_asset_ref: str,
        original_sha256: str,
        original_media_type: str,
        original_size_bytes: int,
        derived_asset_ref: str,
        derived_sha256: str,
        derived_size_bytes: int,
        scanner_name: str,
        scanner_version: str,
    ) -> ParentStoryInputRecord:
        run = self._owned_run(principal, run_id, lock=True)
        if run["run_state"] != "INPUT_PROCESSING":
            raise ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_ACCEPTING_ARTWORK")
        previous = self._current_input(run)
        if previous["original_asset_ref"] is not None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_ALREADY_ATTACHED")
        now = datetime.now(UTC)
        new_input_revision = int(previous["input_revision"]) + 1
        lineage = story_tables.asset_lineage
        scanner_hash = hashlib.sha256(
            f"{scanner_name}\0{scanner_version}".encode("utf-8")
        ).hexdigest()
        try:
            self._session.add_all(
                [
                    CoreAssetMetadataModel(
                        asset_ref=original_asset_ref,
                        asset_version=1,
                        organization_id=None,
                        owner_scope_kind=_OWNER_SCOPE_KIND,
                        owner_scope_ref=_principal_scope_ref(principal),
                        content_sha256=original_sha256,
                        media_type=original_media_type,
                        source_refs=[run_id],
                        derived_from_ref=None,
                    ),
                    CoreAssetMetadataModel(
                        asset_ref=derived_asset_ref,
                        asset_version=1,
                        organization_id=None,
                        owner_scope_kind=_OWNER_SCOPE_KIND,
                        owner_scope_ref=_principal_scope_ref(principal),
                        content_sha256=derived_sha256,
                        media_type="image/png",
                        source_refs=[run_id],
                        derived_from_ref=original_asset_ref,
                    ),
                ]
            )
            self._session.execute(
                insert(lineage).values(
                    lineage_id=str(uuid4()),
                    source_asset_ref=original_asset_ref,
                    source_asset_version=1,
                    derived_asset_ref=derived_asset_ref,
                    derived_asset_version=1,
                    source_sha256=original_sha256,
                    derived_sha256=derived_sha256,
                    source_size_bytes=original_size_bytes,
                    derived_size_bytes=derived_size_bytes,
                    transform_kind="NORMALIZE_DRAWING_IMAGE",
                    transform_version="PILLOW_RGB_PNG_V1",
                    scanner_name=scanner_name,
                    scanner_version=scanner_version,
                    scanner_sha256=scanner_hash,
                    created_at=now,
                )
            )
            input_id = str(uuid4())
            self._session.execute(
                insert(story_tables.run_inputs).values(
                    run_input_id=input_id,
                    run_id=run_id,
                    input_revision=new_input_revision,
                    typed_idea=previous["typed_idea"],
                    idea_source=previous["idea_source"],
                    original_asset_ref=original_asset_ref,
                    original_asset_version=1,
                    original_sha256=original_sha256,
                    original_media_type=original_media_type,
                    original_size_bytes=original_size_bytes,
                    derived_asset_ref=derived_asset_ref,
                    derived_asset_version=1,
                    derived_sha256=derived_sha256,
                    derived_media_type="image/png",
                    derived_size_bytes=derived_size_bytes,
                    source_profile_revision_ref=previous["source_profile_revision_ref"],
                    context_revision=previous["context_revision"],
                    context_snapshot=previous["context_snapshot"],
                    context_snapshot_sha256=previous["context_snapshot_sha256"],
                    lesson_pin_snapshot=(
                        None
                        if previous["lesson_pin_snapshot"] is None
                        else dict(previous["lesson_pin_snapshot"])
                    ),
                    lesson_pin_snapshot_sha256=previous["lesson_pin_snapshot_sha256"],
                    context_confirmed_by=previous["context_confirmed_by"],
                    context_confirmed_at=previous["context_confirmed_at"],
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    current_input_revision=new_input_revision,
                    asset_ref=original_asset_ref,
                    derived_asset_ref=derived_asset_ref,
                    job_state="RUNNING",
                    retryable=False,
                    error_code=None,
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.read_current_input(
            principal=principal, run_id=run_id
        )

    def read_current_input(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentStoryInputRecord:
        run = self._owned_run(principal, run_id)
        row = self._current_input(run)
        return self._input_record(row)

    def record_understanding(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        result_snapshot: dict[str, Any],
        candidate_subject: str,
        confidence: float,
    ) -> int:
        run = self._owned_run(principal, run_id, lock=True)
        if run["run_state"] != "INPUT_PROCESSING":
            raise ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING")
        input_row = self._current_input(run)
        if input_row["original_asset_ref"] is None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_REQUIRED")
        self._check_json_bound(result_snapshot)
        latest_revision = self._session.scalar(
            select(story_tables.understanding_revisions.c.revision_no)
            .where(story_tables.understanding_revisions.c.run_id == run_id)
            .order_by(story_tables.understanding_revisions.c.revision_no.desc())
            .limit(1)
        )
        revision_no = int(latest_revision or 0) + 1
        result_hash = _sha256_json(result_snapshot)
        now = datetime.now(UTC)
        try:
            self._session.execute(
                insert(story_tables.understanding_revisions).values(
                    understanding_revision_id=str(uuid4()),
                    run_id=run_id,
                    run_input_id=input_row["run_input_id"],
                    revision_no=revision_no,
                    subject_label=candidate_subject,
                    confidence=confidence,
                    canonical_result_sha256=result_hash,
                    raw_body_sha256=None,
                    result_snapshot=result_snapshot,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    run_state="SUBJECT_REVIEW",
                    understanding_revision=revision_no,
                    subject_label=candidate_subject,
                    confidence=confidence,
                    result_sha256=result_hash,
                    raw_body_sha256=None,
                    job_state="SUCCEEDED",
                    error_code=None,
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return revision_no

    def confirm_subject(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
        idempotency_key: str,
    ) -> int:
        run = self._owned_run(principal, run_id, lock=True)
        operation = "CONFIRM_SUBJECT"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_understanding_revision": expected_understanding_revision,
                "confirmed_subject": confirmed_subject,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            result = replay["response_body"].get("understanding_revision")
            self._session.commit()
            if not isinstance(result, int):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            return result
        if run["run_state"] != "SUBJECT_REVIEW":
            raise ParentStoryRunError(409, "PARENT_SUBJECT_REVIEW_NOT_ACTIVE")
        latest = self._latest_understanding(run_id)
        if latest is None or int(latest["revision_no"]) != expected_understanding_revision:
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE")
        snapshot = latest["result_snapshot"]
        candidate = snapshot.get("result") if isinstance(snapshot, dict) else None
        if not isinstance(candidate, dict):
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_UNAVAILABLE")
        suggested = str(candidate.get("candidate_subject") or "").strip()
        now = datetime.now(UTC)
        target_revision = expected_understanding_revision
        if confirmed_subject != suggested:
            corrected = dict(candidate)
            corrected["candidate_subject"] = confirmed_subject
            corrected["decision"] = "CORRECTED_BY_ADULT"
            updated_snapshot = {"result": corrected}
            result_hash = _sha256_json(updated_snapshot)
            target_revision += 1
            try:
                self._session.execute(
                    insert(story_tables.understanding_revisions).values(
                        understanding_revision_id=str(uuid4()),
                        run_id=run_id,
                        run_input_id=latest["run_input_id"],
                        revision_no=target_revision,
                        subject_label=confirmed_subject,
                        confidence=latest["confidence"],
                        canonical_result_sha256=result_hash,
                        raw_body_sha256=latest["raw_body_sha256"],
                        result_snapshot=updated_snapshot,
                        created_at=now,
                    )
                )
            except SQLAlchemyError:
                self._session.rollback()
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        new_version = int(run["version"]) + 1
        try:
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={"decision": "CONFIRMED", "understanding_revision": target_revision},
                now=now,
                response_status=200,
            )
            self._session.execute(
                insert(story_tables.review_decisions).values(
                    decision_id=str(uuid4()),
                    run_id=run_id,
                    command_receipt_id=receipt_id,
                    stage="SUBJECT",
                    decision="CONFIRM",
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=_principal_scope_ref(principal),
                    target_understanding_revision=target_revision,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    run_state="PREPARATION_REVIEW",
                    understanding_revision=target_revision,
                    subject_label=confirmed_subject,
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_SUBJECT_CONFIRMATION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return target_revision

    def reserve_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        idempotency_key: str,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation:
        run = self._owned_run(principal, run_id, lock=True)
        operation = "GENERATE_STORY_REVISION"
        scope_kind = "STORY_RUN"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_understanding_revision": expected_understanding_revision,
                "rewrite_instruction": rewrite_instruction,
                "model_id": model_id,
                "model_revision": model_revision,
                "prompt_version": prompt_version,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind=scope_kind,
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            if replay["state"] == "PENDING":
                raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
            replay_body = replay["response_body"]
            if not isinstance(replay_body, dict):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            replay_error = replay_body.get("error_code")
            if isinstance(replay_error, str):
                replay_status = replay["response_status"]
                if type(replay_status) is not int or replay_status not in {502, 504}:
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
                raise ParentStoryRunError(replay_status, replay_error)
            try:
                replay_reservation = ParentStoryRevisionReservation(
                    run_id=run_id,
                    story_revision_id=str(replay_body["story_revision_id"]),
                    revision_no=int(replay_body["revision_no"]),
                    understanding_revision=int(replay_body["understanding_revision"]),
                    context_revision=int(replay_body["context_revision"]),
                    source_asset_sha256=str(replay_body["source_asset_sha256"]),
                    worker_input={},
                    request_sha256=fingerprint,
                    receipt_id=str(replay["receipt_id"]),
                    replayed=True,
                    replay_body=replay_body,
                )
            except (KeyError, TypeError, ValueError):
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
            self._session.commit()
            return replay_reservation

        if run["run_state"] not in {"PREPARATION_REVIEW", "SCRIPT_REVIEW"}:
            raise ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT")
        understanding = self._latest_understanding(run_id)
        if (
            understanding is None
            or int(understanding["revision_no"]) != expected_understanding_revision
            or int(run["understanding_revision"] or 0) != expected_understanding_revision
        ):
            raise ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE")
        subject_decision = self._session.scalar(
            select(story_tables.review_decisions.c.decision_id).where(
                story_tables.review_decisions.c.run_id == run_id,
                story_tables.review_decisions.c.stage == "SUBJECT",
                story_tables.review_decisions.c.decision == "CONFIRM",
                story_tables.review_decisions.c.actor_scope_ref == _principal_scope_ref(principal),
                story_tables.review_decisions.c.target_understanding_revision
                == expected_understanding_revision,
            )
        )
        if subject_decision is None:
            raise ParentStoryRunError(409, "PARENT_SUBJECT_CONFIRMATION_REQUIRED")
        input_row = self._current_input(run)
        if input_row["context_confirmed_by"] is None or input_row["context_confirmed_at"] is None:
            raise ParentStoryRunError(422, "PROFILE_CONTEXT_NOT_CONFIRMED")
        if input_row["original_sha256"] is None:
            raise ParentStoryRunError(409, "PARENT_STORY_ARTWORK_REQUIRED")
        context = input_row["context_snapshot"]
        candidate_snapshot = understanding["result_snapshot"]
        candidate = (
            candidate_snapshot.get("result")
            if isinstance(candidate_snapshot, dict)
            else None
        )
        visible_features = candidate.get("visible_features") if isinstance(candidate, dict) else None
        if not isinstance(visible_features, list):
            visible_features = []
        visible_features = [str(value).strip()[:160] for value in visible_features[:4] if str(value).strip()]
        if not visible_features:
            raise ParentStoryRunError(409, "PARENT_VISIBLE_FEATURES_UNAVAILABLE")

        revisions = self._session.execute(
            select(story_tables.story_revisions)
            .where(story_tables.story_revisions.c.run_id == run_id)
            .order_by(story_tables.story_revisions.c.revision_no.desc())
        ).mappings().all()
        latest_story = revisions[0] if revisions else None
        if len(revisions) >= 4:
            raise ParentStoryRunError(409, "STORY_REWRITE_LIMIT_REACHED")
        if latest_story is None and rewrite_instruction is not None:
            raise ParentStoryRunError(409, "PARENT_INITIAL_STORY_CANNOT_BE_REWRITE")
        if latest_story is not None and (
            rewrite_instruction is None or latest_story["status"] not in {"DRAFT", "FAILED"}
        ):
            raise ParentStoryRunError(409, "PARENT_STORY_REWRITE_NOT_ALLOWED")

        worker_input = {
            "schema_version": "sketch2life.story-generation-input.v1",
            "role": "PARENT",
            "language": "vi",
            "confirmed_subject": str(run["subject_label"] or "").strip(),
            "understanding_revision": expected_understanding_revision,
            "drawing_sha256": str(input_row["original_sha256"]),
            "visible_features": visible_features,
            "child_age_months": int(context["age_months"]),
            "context_revision": int(input_row["context_revision"]),
            "adult_confirmed_idea": str(input_row["typed_idea"] or ""),
            "rewrite_instruction": rewrite_instruction,
            "lesson_direction": None,
        }
        request_hash = _sha256_json(worker_input)
        revision_no = int(latest_story["revision_no"]) + 1 if latest_story is not None else 1
        now = datetime.now(UTC)
        new_version = int(run["version"]) + 1
        try:
            receipt_id = self._store_pending_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind=scope_kind,
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                now=now,
            )
            if latest_story is not None and latest_story["status"] == "DRAFT":
                self._session.execute(
                    update(story_tables.story_revisions)
                    .where(
                        story_tables.story_revisions.c.story_revision_id
                        == latest_story["story_revision_id"]
                    )
                    .values(status="SUPERSEDED")
                )
            self._session.execute(
                insert(story_tables.story_revisions).values(
                    story_revision_id=story_revision_id,
                    run_id=run_id,
                    revision_no=revision_no,
                    status="GENERATING",
                    source_asset_sha256=str(input_row["original_sha256"]),
                    understanding_revision=expected_understanding_revision,
                    context_revision=int(input_row["context_revision"]),
                    schema_version="sketch2life.story-revision.v1",
                    prompt_version=prompt_version,
                    model_id=model_id,
                    model_revision=model_revision,
                    request_sha256=request_hash,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    run_state="SCRIPT_GENERATING",
                    job_state="RUNNING",
                    retryable=False,
                    error_code=None,
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return ParentStoryRevisionReservation(
            run_id=run_id,
            story_revision_id=story_revision_id,
            revision_no=revision_no,
            understanding_revision=expected_understanding_revision,
            context_revision=int(input_row["context_revision"]),
            source_asset_sha256=str(input_row["original_sha256"]),
            worker_input=worker_input,
            request_sha256=request_hash,
            receipt_id=receipt_id,
        )

    def complete_story_revision(
        self,
        *,
        reservation: ParentStoryRevisionReservation,
        principal: VerifiedPrincipal,
        story: dict[str, Any],
        story_sha256: str,
        provider_call_id: str,
        model_id: str,
        model_revision: str,
    ) -> ParentStoryRunRecord:
        run = self._owned_run(principal, reservation.run_id, lock=True)
        revision_id = self._session.scalar(
            select(story_tables.story_revisions.c.story_revision_id).where(
                story_tables.story_revisions.c.story_revision_id == reservation.story_revision_id,
                story_tables.story_revisions.c.run_id == reservation.run_id,
                story_tables.story_revisions.c.status == "GENERATING",
            )
        )
        if revision_id is None:
            raise ParentStoryRunError(409, "PARENT_STORY_REVISION_NOT_GENERATING")
        now = datetime.now(UTC)
        sections = story["story"]
        new_version = int(run["version"]) + 1
        try:
            self._session.execute(
                update(story_tables.story_revisions)
                .where(
                    story_tables.story_revisions.c.story_revision_id
                    == reservation.story_revision_id
                )
                .values(
                    status="DRAFT",
                    story_sha256=story_sha256,
                    language=story["language"],
                    title=story["title"],
                    duration_ms=story["duration_ms"],
                    story_content=sections,
                    model_id=model_id,
                    model_revision=model_revision,
                    provider_call_id=provider_call_id,
                )
            )
            for scene in story["scenes"]:
                self._session.execute(
                    insert(story_tables.story_scenes).values(
                        scene_id=str(uuid4()),
                        story_revision_id=reservation.story_revision_id,
                        scene_index=scene["scene_index"],
                        title=scene["title"],
                        action=scene["action"],
                        visual_prompt=scene["visual_prompt"],
                        narration=scene["narration"],
                        start_ms=scene["start_ms"],
                        duration_ms=scene["duration_ms"],
                        character_anchors=scene["character_anchors"],
                    )
                )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == reservation.run_id)
                .values(
                    run_state="SCRIPT_REVIEW",
                    job_state="SUCCEEDED",
                    retryable=False,
                    result_sha256=story_sha256,
                    error_code=None,
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            receipt_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_command_receipts)
                    .where(
                        story_tables.story_command_receipts.c.receipt_id
                        == reservation.receipt_id,
                        story_tables.story_command_receipts.c.state == "PENDING",
                    )
                    .values(
                        state="FINAL",
                        response_status=200,
                        response_resource_version=new_version,
                        response_body={
                            "story_revision_id": reservation.story_revision_id,
                            "revision_no": reservation.revision_no,
                            "understanding_revision": reservation.understanding_revision,
                            "context_revision": reservation.context_revision,
                            "source_asset_sha256": reservation.source_asset_sha256,
                            "story_sha256": story_sha256,
                            "modal_call_id": provider_call_id,
                            "model_id": model_id,
                            "model_revision": model_revision,
                        },
                        resource_ref=reservation.run_id,
                        resource_version=new_version,
                        state_version=story_tables.story_command_receipts.c.state_version + 1,
                        finalized_at=now,
                    )
                ),
            )
            if receipt_update.rowcount != 1:
                self._session.rollback()
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
        except ParentStoryRunError:
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            principal=principal,
            run_id=reservation.run_id,
        )

    def fail_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentStoryRevisionReservation,
        error_code: str,
        outcome_unknown: bool,
    ) -> None:
        run = self._owned_run(principal, reservation.run_id, lock=True)
        now = datetime.now(UTC)
        revision_state = "AWAITING_RECONCILIATION" if outcome_unknown else "FAILED"
        run_state = "SCRIPT_GENERATION_UNKNOWN" if outcome_unknown else "FAILED"
        job_state = "AWAITING_RECONCILIATION" if outcome_unknown else "FAILED"
        new_version = int(run["version"]) + 1
        values: dict[str, Any] = {
            "status": revision_state,
            "updated_at": now,
        }
        try:
            self._session.execute(
                update(story_tables.story_revisions)
                .where(
                    story_tables.story_revisions.c.story_revision_id
                    == reservation.story_revision_id
                )
                .values(**values)
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == reservation.run_id)
                .values(
                    run_state=run_state,
                    job_state=job_state,
                    retryable=False,
                    error_code=error_code,
                    active_owner_parent_account_id=(
                        run["active_owner_parent_account_id"] if outcome_unknown else None
                    ),
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            receipt_update = cast(
                CursorResult[Any],
                self._session.execute(
                    update(story_tables.story_command_receipts)
                    .where(
                        story_tables.story_command_receipts.c.receipt_id
                        == reservation.receipt_id,
                        story_tables.story_command_receipts.c.state == "PENDING",
                    )
                    .values(
                        state="FINAL",
                        response_status=504 if outcome_unknown else 502,
                        response_resource_version=new_version,
                        response_body={"error_code": error_code},
                        resource_ref=reservation.run_id,
                        resource_version=new_version,
                        state_version=story_tables.story_command_receipts.c.state_version + 1,
                        finalized_at=now,
                    )
                ),
            )
            if receipt_update.rowcount != 1:
                self._session.rollback()
                raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            self._session.commit()
        except ParentStoryRunError:
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def fail_drawing_analysis(
        self, *, principal: VerifiedPrincipal, run_id: str, error_code: str, outcome_unknown: bool
    ) -> None:
        run = self._owned_run(principal, run_id, lock=True)
        now = datetime.now(UTC)
        try:
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    run_state="INPUT_PROCESSING" if outcome_unknown else "FAILED",
                    job_state="AWAITING_RECONCILIATION" if outcome_unknown else "FAILED",
                    retryable=False,
                    error_code=error_code,
                    active_owner_parent_account_id=(
                        run["active_owner_parent_account_id"] if outcome_unknown else None
                    ),
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def confirm_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunRecord:
        run = self._owned_run(principal, run_id, lock=True)
        operation = "CONFIRM_STORY_REVISION"
        key_hash = _idempotency_key_hash(idempotency_key)
        fingerprint = _sha256_json(
            {
                "expected_revision": expected_revision,
                "expected_story_sha256": expected_story_sha256,
            }
        )
        self._lock_idempotency(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
        )
        replay = self._find_idempotency_receipt(
            principal=principal,
            operation=operation,
            scope_kind="STORY_RUN",
            scope_ref=run_id,
            key_hash=key_hash,
            fingerprint=fingerprint,
        )
        if replay is not None:
            self._session.commit()
            return self.get_run(principal=principal, run_id=run_id)
        story_revision = self._session.execute(
            select(story_tables.story_revisions).where(
                story_tables.story_revisions.c.run_id == run_id,
                story_tables.story_revisions.c.revision_no == expected_revision,
            )
        ).mappings().one_or_none()
        if (
            story_revision is None
            or story_revision["status"] != "DRAFT"
            or story_revision["story_sha256"] != expected_story_sha256
            or run["run_state"] != "SCRIPT_REVIEW"
        ):
            raise ParentStoryRunError(409, "PARENT_STORY_REVISION_STALE")
        now = datetime.now(UTC)
        new_version = int(run["version"]) + 1
        try:
            receipt_id = self._store_idempotency_receipt(
                principal=principal,
                operation=operation,
                scope_kind="STORY_RUN",
                scope_ref=run_id,
                key_hash=key_hash,
                fingerprint=fingerprint,
                run_id=run_id,
                resource_version=new_version,
                response_body={"decision": "CONFIRMED", "revision": expected_revision},
                now=now,
                response_status=200,
            )
            self._session.execute(
                insert(story_tables.story_revision_reviews).values(
                    review_id=str(uuid4()),
                    run_id=run_id,
                    story_revision_id=story_revision["story_revision_id"],
                    command_receipt_id=receipt_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=_principal_scope_ref(principal),
                    decision="CONFIRM",
                    target_story_sha256=expected_story_sha256,
                    created_at=now,
                )
            )
            self._session.execute(
                update(story_tables.story_revisions)
                .where(
                    story_tables.story_revisions.c.story_revision_id
                    == story_revision["story_revision_id"]
                )
                .values(status="CONFIRMED")
            )
            self._session.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(
                    run_state="SCRIPT_REVIEW",
                    job_state="SUCCEEDED",
                    version=new_version,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_STORY_CONFIRMATION_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            principal=principal,
            run_id=run_id,
        )

    def _owned_run(self, principal: VerifiedPrincipal, run_id: str, *, lock: bool = False):
        query = select(story_tables.story_runs).where(
            story_tables.story_runs.c.run_id == run_id,
            story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
            story_tables.story_runs.c.actor_scope_ref == _principal_scope_ref(principal),
        )
        if lock:
            query = query.with_for_update()
        row = self._session.execute(query).mappings().one_or_none()
        if row is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        return row

    def _lock_idempotency(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
    ) -> None:
        lock_material = _canonical_json(
            {
                "issuer": principal.issuer,
                "subject": principal.subject,
                "operation": operation,
                "scope_kind": scope_kind,
                "scope_ref": scope_ref,
                "key_hash": key_hash,
            }
        ).encode("utf-8")
        lock_key = int.from_bytes(hashlib.sha256(lock_material).digest()[:8], "big", signed=True)
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
        )

    def _find_idempotency_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
    ) -> RowMapping | None:
        receipt = self._session.execute(
            select(story_tables.story_command_receipts).where(
                story_tables.story_command_receipts.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                story_tables.story_command_receipts.c.actor_scope_ref
                == _principal_scope_ref(principal),
                story_tables.story_command_receipts.c.operation == operation,
                story_tables.story_command_receipts.c.idempotency_scope_kind == scope_kind,
                story_tables.story_command_receipts.c.idempotency_scope_ref == scope_ref,
                story_tables.story_command_receipts.c.idempotency_key_sha256 == key_hash,
            )
        ).mappings().one_or_none()
        if receipt is None:
            return None
        if not hmac.compare_digest(str(receipt["request_fingerprint_sha256"]), fingerprint):
            raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
        return receipt

    def _store_idempotency_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
        run_id: str,
        resource_version: int,
        response_body: dict[str, Any],
        now: datetime,
        response_status: int,
    ) -> str:
        receipt_id = str(uuid4())
        self._session.execute(
            insert(story_tables.story_command_receipts).values(
                receipt_id=receipt_id,
                actor_scope_kind=_OWNER_SCOPE_KIND,
                actor_scope_ref=_principal_scope_ref(principal),
                operation=operation,
                idempotency_scope_kind=scope_kind,
                idempotency_scope_ref=scope_ref,
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="FINAL",
                response_status=response_status,
                response_resource_version=resource_version,
                response_body=response_body,
                resource_ref=run_id,
                resource_version=resource_version,
                state_version=1,
                created_at=now,
                finalized_at=now,
            )
        )
        return receipt_id

    def _store_pending_idempotency_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        operation: str,
        scope_kind: str,
        scope_ref: str,
        key_hash: str,
        fingerprint: str,
        run_id: str,
        resource_version: int,
        now: datetime,
    ) -> str:
        receipt_id = str(uuid4())
        self._session.execute(
            insert(story_tables.story_command_receipts).values(
                receipt_id=receipt_id,
                actor_scope_kind=_OWNER_SCOPE_KIND,
                actor_scope_ref=_principal_scope_ref(principal),
                operation=operation,
                idempotency_scope_kind=scope_kind,
                idempotency_scope_ref=scope_ref,
                idempotency_key_sha256=key_hash,
                request_fingerprint_sha256=fingerprint,
                state="PENDING",
                response_status=None,
                response_resource_version=None,
                response_body=None,
                resource_ref=run_id,
                resource_version=resource_version,
                state_version=1,
                created_at=now,
                finalized_at=None,
            )
        )
        return receipt_id

    def _current_input(self, run: Mapping[str, Any]) -> RowMapping:
        revision = run["current_input_revision"]
        if revision is None:
            raise ParentStoryRunError(409, "PARENT_STORY_CONTEXT_UNAVAILABLE")
        row = self._session.execute(
            select(story_tables.run_inputs).where(
                story_tables.run_inputs.c.run_id == run["run_id"],
                story_tables.run_inputs.c.input_revision == revision,
            )
        ).mappings().one_or_none()
        if row is None:
            raise ParentStoryRunError(503, "PARENT_STORY_CONTEXT_UNAVAILABLE")
        return row

    def _latest_understanding(self, run_id: str):
        return self._session.execute(
            select(story_tables.understanding_revisions)
            .where(story_tables.understanding_revisions.c.run_id == run_id)
            .order_by(story_tables.understanding_revisions.c.revision_no.desc())
            .limit(1)
        ).mappings().one_or_none()

    @staticmethod
    def _input_record(row) -> ParentStoryInputRecord:
        return ParentStoryInputRecord(
            run_input_id=str(row["run_input_id"]),
            input_revision=int(row["input_revision"]),
            original_asset_ref=row["original_asset_ref"],
            original_sha256=row["original_sha256"],
            original_media_type=row["original_media_type"],
            original_size_bytes=(
                int(row["original_size_bytes"])
                if row["original_size_bytes"] is not None
                else None
            ),
            derived_asset_ref=row["derived_asset_ref"],
            derived_sha256=row["derived_sha256"],
            derived_size_bytes=(
                int(row["derived_size_bytes"])
                if row["derived_size_bytes"] is not None
                else None
            ),
            source_profile_revision_ref=UUID(str(row["source_profile_revision_ref"])),
            context_revision=int(row["context_revision"]),
            context_snapshot=dict(row["context_snapshot"]),
            context_snapshot_sha256=str(row["context_snapshot_sha256"]),
            context_confirmed_by=(
                str(row["context_confirmed_by"])
                if row["context_confirmed_by"] is not None
                else None
            ),
            context_confirmed_at=row["context_confirmed_at"],
        )

    @staticmethod
    def _check_json_bound(value: dict[str, Any]) -> None:
        if len(_canonical_json(value).encode("utf-8")) > 262_144:
            raise ParentStoryRunError(422, "PARENT_UNDERSTANDING_RESULT_TOO_LARGE")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _create_run_fingerprint(
    *,
    parent_profile_id: UUID,
    topic: str,
    adult_confirmed_idea: str,
    lesson_version_ref: dict[str, str] | None,
) -> str:
    return _sha256_json(
        {
            "parent_profile_id": str(parent_profile_id),
            "topic": topic,
            "adult_confirmed_idea": adult_confirmed_idea,
            "lesson_version": lesson_version_ref,
        }
    )


def _integrity_constraint_name(exc: IntegrityError) -> str | None:
    original = getattr(exc, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    return constraint_name if isinstance(constraint_name, str) else None


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _idempotency_key_hash(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 256:
        raise ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _principal_scope_ref(principal: VerifiedPrincipal) -> str:
    principal_claims = {"issuer": principal.issuer, "subject": principal.subject}
    return hashlib.sha256(_canonical_json(principal_claims).encode("utf-8")).hexdigest()


__all__ = ["SqlParentStoryRunRepository"]
