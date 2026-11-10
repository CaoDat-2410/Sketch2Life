"""PostgreSQL adapter for Parent StoryRuns, immutable context, artwork, and reviews."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_story_runs import (
    ParentStoryInputRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentDataAuthorizationModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
_PARENT_CONTEXT_SCHEMA = "sketch2life.parent-context.v1"


class SqlParentStoryRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_run(
        self,
        *,
        owner_subject: str,
        account_id: str,
        parent_profile_id: str,
        expected_profile_revision_ref: str,
        policy_version: str,
        run_id: str,
        topic: str,
        adult_confirmed_idea: str,
    ) -> ParentStoryRunRecord:
        self._require_policy(policy_version)
        profile = self._session.scalar(
            select(ParentChildProfileModel)
            .where(
                ParentChildProfileModel.parent_profile_id == parent_profile_id,
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state == "ACTIVE",
            )
            .with_for_update()
        )
        if profile is None:
            raise ParentStoryRunError(404, "PARENT_PROFILE_NOT_FOUND")
        revision = self._session.scalar(
            select(ParentProfileRevisionModel).where(
                ParentProfileRevisionModel.parent_profile_id == parent_profile_id,
                ParentProfileRevisionModel.profile_revision_id
                == profile.current_revision_ref,
            )
        )
        if revision is None:
            raise ParentStoryRunError(503, "PARENT_PROFILE_REVISION_UNAVAILABLE")
        if revision.profile_revision_id != expected_profile_revision_ref:
            raise ParentStoryRunError(409, "PARENT_PROFILE_REVISION_STALE")
        authorization = self._active_authorization(
            owner_subject, parent_profile_id, policy_version
        )
        existing_run = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.active_owner_parent_account_id == account_id
            )
        )
        if existing_run is not None:
            raise ParentStoryRunError(409, "PARENT_ACTIVE_STORY_RUN_EXISTS")

        now = datetime.now(UTC)
        context = {
            "schema_version": _PARENT_CONTEXT_SCHEMA,
            "profile_revision_ref": revision.profile_revision_id,
            "age_months": revision.age_months,
            "interests_summary": revision.interests_summary,
            "topic": topic,
            "adult_confirmed_idea": adult_confirmed_idea,
            "consent_policy_version": policy_version,
        }
        context_hash = _sha256_json(context)
        run_input_id = str(uuid4())
        try:
            self._session.execute(
                insert(story_tables.story_runs).values(
                    run_id=run_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_subject,
                    profile_ref=parent_profile_id,
                    child_age_months=revision.age_months,
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
                    source_profile_revision_ref=revision.profile_revision_id,
                    data_authorization_id=authorization.authorization_id,
                    context_revision=1,
                    context_snapshot=context,
                    context_snapshot_sha256=context_hash,
                    context_confirmed_by=owner_subject,
                    context_confirmed_at=now,
                    created_at=now,
                )
            )
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ParentStoryRunError(409, "PARENT_ACTIVE_STORY_RUN_EXISTS") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
        )

    def get_run(
        self, *, owner_subject: str, policy_version: str, run_id: str
    ) -> ParentStoryRunRecord:
        run = self._owned_run(owner_subject, run_id)
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
            parent_profile_id=str(run["profile_ref"]),
            profile_revision_ref=str(input_row["source_profile_revision_ref"]),
            context_revision=int(input_row["context_revision"]),
            context_snapshot=dict(input_row["context_snapshot"]),
            context_snapshot_sha256=str(input_row["context_snapshot_sha256"]),
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
        self, *, owner_subject: str, account_id: str, policy_version: str
    ) -> ParentStoryRunRecord | None:
        run_id = self._session.scalar(
            select(story_tables.story_runs.c.run_id).where(
                story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                story_tables.story_runs.c.actor_scope_ref == owner_subject,
                story_tables.story_runs.c.active_owner_parent_account_id == account_id,
            )
        )
        if run_id is None:
            return None
        return self.get_run(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=str(run_id),
        )

    def attach_artwork(
        self,
        *,
        owner_subject: str,
        policy_version: str,
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
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, run_id, lock=True)
        self._require_active_authorization(owner_subject, str(run["profile_ref"]), policy_version)
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
                        owner_scope_ref=owner_subject,
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
                        owner_scope_ref=owner_subject,
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
                    data_authorization_id=previous["data_authorization_id"],
                    context_revision=previous["context_revision"],
                    context_snapshot=previous["context_snapshot"],
                    context_snapshot_sha256=previous["context_snapshot_sha256"],
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
            owner_subject=owner_subject, policy_version=policy_version, run_id=run_id
        )

    def read_current_input(
        self, *, owner_subject: str, policy_version: str, run_id: str
    ) -> ParentStoryInputRecord:
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, run_id)
        self._require_active_authorization(owner_subject, str(run["profile_ref"]), policy_version)
        row = self._current_input(run)
        return self._input_record(row)

    def record_understanding(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        result_snapshot: dict[str, Any],
        candidate_subject: str,
        confidence: float,
    ) -> int:
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, run_id, lock=True)
        self._require_active_authorization(owner_subject, str(run["profile_ref"]), policy_version)
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
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
    ) -> int:
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, run_id, lock=True)
        self._require_active_authorization(owner_subject, str(run["profile_ref"]), policy_version)
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
        fingerprint = _sha256_json(
            {
                "operation": "CONFIRM_SUBJECT",
                "run_id": run_id,
                "expected_revision": expected_understanding_revision,
                "confirmed_subject": confirmed_subject,
            }
        )
        receipt_id = str(uuid4())
        new_version = int(run["version"]) + 1
        try:
            self._session.execute(
                insert(story_tables.story_command_receipts).values(
                    receipt_id=receipt_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_subject,
                    operation="CONFIRM_SUBJECT",
                    idempotency_scope_kind="STORY_RUN",
                    idempotency_scope_ref=run_id,
                    idempotency_key_sha256=fingerprint,
                    request_fingerprint_sha256=fingerprint,
                    state="FINAL",
                    response_status=200,
                    response_resource_version=new_version,
                    response_body={"decision": "CONFIRMED", "understanding_revision": target_revision},
                    resource_ref=run_id,
                    resource_version=new_version,
                    state_version=1,
                    created_at=now,
                    finalized_at=now,
                )
            )
            self._session.execute(
                insert(story_tables.review_decisions).values(
                    decision_id=str(uuid4()),
                    run_id=run_id,
                    command_receipt_id=receipt_id,
                    stage="SUBJECT",
                    decision="CONFIRM",
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_subject,
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
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation:
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, run_id, lock=True)
        self._require_active_authorization(owner_subject, str(run["profile_ref"]), policy_version)
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
                story_tables.review_decisions.c.actor_scope_ref == owner_subject,
                story_tables.review_decisions.c.target_understanding_revision
                == expected_understanding_revision,
            )
        )
        if subject_decision is None:
            raise ParentStoryRunError(409, "PARENT_SUBJECT_CONFIRMATION_REQUIRED")
        input_row = self._current_input(run)
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
        )

    def complete_story_revision(
        self,
        *,
        reservation: ParentStoryRevisionReservation,
        owner_subject: str,
        policy_version: str,
        story: dict[str, Any],
        story_sha256: str,
        provider_call_id: str,
        model_id: str,
        model_revision: str,
    ) -> ParentStoryRunRecord:
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, reservation.run_id, lock=True)
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
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
        return self.get_run(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=reservation.run_id,
        )

    def fail_story_revision(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        reservation: ParentStoryRevisionReservation,
        error_code: str,
        outcome_unknown: bool,
    ) -> None:
        run = self._owned_run(owner_subject, reservation.run_id, lock=True)
        now = datetime.now(UTC)
        revision_state = "AWAITING_RECONCILIATION" if outcome_unknown else "FAILED"
        run_state = "SCRIPT_GENERATION_UNKNOWN" if outcome_unknown else "FAILED"
        job_state = "AWAITING_RECONCILIATION" if outcome_unknown else "FAILED"
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
                    version=story_tables.story_runs.c.version + 1,
                    revision=story_tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def fail_drawing_analysis(
        self, *, owner_subject: str, run_id: str, error_code: str, outcome_unknown: bool
    ) -> None:
        run = self._owned_run(owner_subject, run_id, lock=True)
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
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
    ) -> ParentStoryRunRecord:
        self._require_policy(policy_version)
        run = self._owned_run(owner_subject, run_id, lock=True)
        self._require_active_authorization(owner_subject, str(run["profile_ref"]), policy_version)
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
        receipt_id = str(uuid4())
        new_version = int(run["version"]) + 1
        fingerprint = _sha256_json(
            {
                "operation": "CONFIRM_STORY_REVISION",
                "run_id": run_id,
                "revision": expected_revision,
                "story_sha256": expected_story_sha256,
            }
        )
        try:
            self._session.execute(
                insert(story_tables.story_command_receipts).values(
                    receipt_id=receipt_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_subject,
                    operation="CONFIRM_STORY_REVISION",
                    idempotency_scope_kind="STORY_RUN",
                    idempotency_scope_ref=run_id,
                    idempotency_key_sha256=fingerprint,
                    request_fingerprint_sha256=fingerprint,
                    state="FINAL",
                    response_status=200,
                    response_resource_version=new_version,
                    response_body={"decision": "CONFIRMED", "revision": expected_revision},
                    resource_ref=run_id,
                    resource_version=new_version,
                    state_version=1,
                    created_at=now,
                    finalized_at=now,
                )
            )
            self._session.execute(
                insert(story_tables.story_revision_reviews).values(
                    review_id=str(uuid4()),
                    run_id=run_id,
                    story_revision_id=story_revision["story_revision_id"],
                    command_receipt_id=receipt_id,
                    actor_scope_kind=_OWNER_SCOPE_KIND,
                    actor_scope_ref=owner_subject,
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
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
        )

    def _owned_run(self, owner_subject: str, run_id: str, *, lock: bool = False):
        query = select(story_tables.story_runs).where(
            story_tables.story_runs.c.run_id == run_id,
            story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
            story_tables.story_runs.c.actor_scope_ref == owner_subject,
        )
        if lock:
            query = query.with_for_update()
        row = self._session.execute(query).mappings().one_or_none()
        if row is None:
            raise ParentStoryRunError(404, "PARENT_STORY_RUN_NOT_FOUND")
        return row

    def _current_input(self, run):
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

    def _active_authorization(
        self, owner_subject: str, profile_id: str, policy_version: str
    ):
        profile = self._session.scalar(
            select(ParentChildProfileModel).where(
                ParentChildProfileModel.parent_profile_id == profile_id,
                ParentChildProfileModel.owner_subject == owner_subject,
                ParentChildProfileModel.state == "ACTIVE",
            )
        )
        if profile is None:
            raise ParentStoryRunError(403, "PARENT_PROFILE_INACTIVE")
        authorization = self._session.scalar(
            select(ParentDataAuthorizationModel).where(
                ParentDataAuthorizationModel.parent_profile_id == profile_id,
                ParentDataAuthorizationModel.purpose_code == "PARENT_STORY_PERSONALIZATION",
                ParentDataAuthorizationModel.policy_version == policy_version,
                ParentDataAuthorizationModel.state == "GRANTED",
            )
        )
        if authorization is None:
            raise ParentStoryRunError(403, "PARENT_DATA_AUTHORIZATION_REQUIRED")
        return authorization

    def _require_active_authorization(
        self, owner_subject: str, profile_id: str, policy_version: str
    ) -> None:
        self._require_policy(policy_version)
        self._active_authorization(owner_subject, profile_id, policy_version)

    @staticmethod
    def _require_policy(policy_version: str) -> None:
        if not policy_version.strip():
            raise ParentStoryRunError(503, "PARENT_CONSENT_POLICY_UNAVAILABLE")

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
            source_profile_revision_ref=str(row["source_profile_revision_ref"]),
            data_authorization_id=str(row["data_authorization_id"]),
            context_revision=int(row["context_revision"]),
            context_snapshot=dict(row["context_snapshot"]),
            context_snapshot_sha256=str(row["context_snapshot_sha256"]),
            context_confirmed_by=str(row["context_confirmed_by"]),
            context_confirmed_at=row["context_confirmed_at"],
        )

    @staticmethod
    def _check_json_bound(value: dict[str, Any]) -> None:
        if len(_canonical_json(value).encode("utf-8")) > 262_144:
            raise ParentStoryRunError(422, "PARENT_UNDERSTANDING_RESULT_TOO_LARGE")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["SqlParentStoryRunRepository"]
