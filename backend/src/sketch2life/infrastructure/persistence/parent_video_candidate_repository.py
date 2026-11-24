"""PostgreSQL persistence for synthetic Parent video candidates."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.video_keyframe_plan import keyframe_inputs_from
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_video_candidates import (
    ParentVideoCandidateError,
    ParentVideoCandidateRecord,
    ParentVideoCandidateRepositoryPort,
    ParentVideoCandidateScene,
    ParentVideoCandidateSource,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_OWNER_SCOPE_KIND = "PARENT_ACCOUNT"
_PURGE_STATES = ("DELETE_PENDING", "DELETED")


class SqlParentVideoCandidateRepository(ParentVideoCandidateRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def reserve_candidate(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_profile_id: str,
        expected_story_revision: int,
        expected_story_sha256: str,
        idempotency_key_sha256: str,
        request_fingerprint_sha256: str,
        video_candidate_id: str,
        job_id: str,
        generation_id: str,
        attempt_id: str,
        attempt_prefix: str,
    ) -> tuple[ParentVideoCandidateRecord, ParentVideoCandidateSource | None, bool]:
        try:
            owner_ref = _principal_scope_ref(principal)
            run = self._owned_run(principal=principal, run_id=run_id, lock=True)
            if run["run_state"] in _PURGE_STATES or run["profile_ref"] is None:
                raise ParentVideoCandidateError(409, "INVALID_STATE_TRANSITION")

            existing = (
                self._session.execute(
                    select(story_tables.parent_video_candidate_jobs)
                    .where(
                        story_tables.parent_video_candidate_jobs.c.run_id == run_id,
                        story_tables.parent_video_candidate_jobs.c.owner_issuer == principal.issuer,
                        story_tables.parent_video_candidate_jobs.c.owner_subject
                        == principal.subject,
                        story_tables.parent_video_candidate_jobs.c.idempotency_key_sha256
                        == idempotency_key_sha256,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_fingerprint_sha256"] != request_fingerprint_sha256:
                    raise ParentVideoCandidateError(409, "VIDEO_CANDIDATE_IDEMPOTENCY_CONFLICT")
                record = self._record(existing)
                self._session.commit()
                return record, None, True

            already_reserved = (
                self._session.execute(
                    select(story_tables.parent_video_candidate_jobs)
                    .where(story_tables.parent_video_candidate_jobs.c.run_id == run_id)
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if already_reserved is not None:
                raise ParentVideoCandidateError(409, "VIDEO_CANDIDATE_ALREADY_REQUESTED")

            if (
                run["run_state"] != "SCRIPT_REVIEW"
                or str(run["profile_ref"]) != expected_profile_id
            ):
                raise ParentVideoCandidateError(409, "PARENT_VIDEO_STORY_NOT_CONFIRMED")
            if run["current_input_revision"] is None:
                raise ParentVideoCandidateError(409, "VIDEO_SOURCE_CONTEXT_STALE")

            latest_story = (
                self._session.execute(
                    select(story_tables.story_revisions)
                    .where(story_tables.story_revisions.c.run_id == run_id)
                    .order_by(story_tables.story_revisions.c.revision_no.desc())
                    .limit(1)
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if (
                latest_story is None
                or latest_story["status"] != "CONFIRMED"
                or int(latest_story["revision_no"]) != expected_story_revision
                or latest_story["story_sha256"] != expected_story_sha256
                or latest_story["story_sha256"] is None
            ):
                raise ParentVideoCandidateError(409, "PARENT_VIDEO_STORY_NOT_CONFIRMED")

            review = self._session.scalar(
                select(story_tables.story_revision_reviews.c.review_id).where(
                    story_tables.story_revision_reviews.c.run_id == run_id,
                    story_tables.story_revision_reviews.c.story_revision_id
                    == latest_story["story_revision_id"],
                    story_tables.story_revision_reviews.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                    story_tables.story_revision_reviews.c.actor_scope_ref == owner_ref,
                    story_tables.story_revision_reviews.c.decision == "CONFIRM",
                    story_tables.story_revision_reviews.c.target_story_sha256
                    == expected_story_sha256,
                )
            )
            if review is None:
                raise ParentVideoCandidateError(409, "VIDEO_SCRIPT_CONFIRMATION_REQUIRED")

            input_row = (
                self._session.execute(
                    select(story_tables.run_inputs).where(
                        story_tables.run_inputs.c.run_id == run_id,
                        story_tables.run_inputs.c.input_revision == run["current_input_revision"],
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                input_row is None
                or input_row["context_confirmed_by"] != owner_ref
                or input_row["context_confirmed_at"] is None
                or input_row["context_revision"] != latest_story["context_revision"]
                or input_row["original_asset_ref"] is None
                or input_row["original_asset_version"] is None
                or input_row["original_sha256"] is None
                or input_row["original_sha256"] != latest_story["source_asset_sha256"]
            ):
                raise ParentVideoCandidateError(409, "VIDEO_SOURCE_DRAWING_STALE")

            understanding = (
                self._session.execute(
                    select(story_tables.understanding_revisions).where(
                        story_tables.understanding_revisions.c.run_id == run_id,
                        story_tables.understanding_revisions.c.revision_no
                        == latest_story["understanding_revision"],
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                understanding is None
                or understanding["run_input_id"] != input_row["run_input_id"]
                or int(run["understanding_revision"] or 0)
                != int(latest_story["understanding_revision"])
            ):
                raise ParentVideoCandidateError(409, "VIDEO_SOURCE_CONTEXT_STALE")
            subject_review = self._session.scalar(
                select(story_tables.review_decisions.c.decision_id).where(
                    story_tables.review_decisions.c.run_id == run_id,
                    story_tables.review_decisions.c.stage == "SUBJECT",
                    story_tables.review_decisions.c.decision == "CONFIRM",
                    story_tables.review_decisions.c.actor_scope_kind == _OWNER_SCOPE_KIND,
                    story_tables.review_decisions.c.actor_scope_ref == owner_ref,
                    story_tables.review_decisions.c.target_understanding_revision
                    == latest_story["understanding_revision"],
                )
            )
            if subject_review is None or not run["subject_label"]:
                raise ParentVideoCandidateError(409, "VIDEO_SUBJECT_CONFIRMATION_REQUIRED")

            selection_id = latest_story["activity_selection_id"]
            selection = (
                self._session.execute(
                    select(story_tables.parent_activity_selections).where(
                        story_tables.parent_activity_selections.c.activity_selection_id
                        == selection_id,
                        story_tables.parent_activity_selections.c.run_id == run_id,
                        story_tables.parent_activity_selections.c.understanding_revision
                        == latest_story["understanding_revision"],
                        story_tables.parent_activity_selections.c.actor_scope_ref == owner_ref,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if selection is None or not isinstance(selection["activity_snapshot"], dict):
                raise ParentVideoCandidateError(409, "VIDEO_ACTIVITY_SELECTION_REQUIRED")
            activity_hash = _sha256_json(selection["activity_snapshot"])
            if activity_hash != selection["activity_snapshot_sha256"]:
                raise ParentVideoCandidateError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
            latest_selection = self._session.execute(
                select(story_tables.parent_activity_selections.c.activity_selection_id)
                .where(
                    story_tables.parent_activity_selections.c.run_id == run_id,
                    story_tables.parent_activity_selections.c.understanding_revision
                    == latest_story["understanding_revision"],
                )
                .order_by(story_tables.parent_activity_selections.c.selection_revision.desc())
                .limit(1)
            ).scalar_one_or_none()
            if latest_selection != selection_id:
                raise ParentVideoCandidateError(409, "VIDEO_ACTIVITY_SELECTION_STALE")

            asset = self._session.scalar(
                select(CoreAssetMetadataModel).where(
                    CoreAssetMetadataModel.asset_ref == input_row["original_asset_ref"],
                    CoreAssetMetadataModel.asset_version == input_row["original_asset_version"],
                    CoreAssetMetadataModel.owner_scope_kind == _OWNER_SCOPE_KIND,
                    CoreAssetMetadataModel.owner_scope_ref == owner_ref,
                    CoreAssetMetadataModel.content_sha256 == input_row["original_sha256"],
                    CoreAssetMetadataModel.media_type == input_row["original_media_type"],
                )
            )
            if asset is None:
                raise ParentVideoCandidateError(409, "VIDEO_SOURCE_ASSET_UNAVAILABLE")

            scene_rows = (
                self._session.execute(
                    select(story_tables.story_scenes)
                    .where(
                        story_tables.story_scenes.c.story_revision_id
                        == latest_story["story_revision_id"]
                    )
                    .order_by(story_tables.story_scenes.c.scene_index)
                )
                .mappings()
                .all()
            )
            scene_indices = [int(row["scene_index"]) for row in scene_rows]
            if not 5 <= len(scene_rows) <= 15 or scene_indices != list(
                range(1, len(scene_rows) + 1)
            ):
                raise ParentVideoCandidateError(409, "VIDEO_STORYBOARD_NOT_READY")

            source = ParentVideoCandidateSource(
                run_id=run_id,
                profile_id=str(run["profile_ref"]),
                story_revision_id=str(latest_story["story_revision_id"]),
                story_revision_no=int(latest_story["revision_no"]),
                story_sha256=str(latest_story["story_sha256"]),
                story_duration_ms=int(latest_story["duration_ms"]),
                source_asset_ref=str(input_row["original_asset_ref"]),
                source_asset_version=int(input_row["original_asset_version"]),
                source_asset_sha256=str(input_row["original_sha256"]),
                source_media_type=str(input_row["original_media_type"]),
                source_size_bytes=int(input_row["original_size_bytes"]),
                confirmed_subject=str(run["subject_label"]).strip(),
                activity_selection_id=str(selection_id),
                activity_snapshot_sha256=activity_hash,
                keyframe_inputs=keyframe_inputs_from(
                    (understanding["result_snapshot"] or {}).get("result")
                    if isinstance(understanding["result_snapshot"], dict)
                    else None,
                    latest_story["story_content"],
                ),
                scenes=tuple(
                    ParentVideoCandidateScene(
                        scene_index=int(row["scene_index"]),
                        title=str(row["title"]),
                        action=str(row["action"]),
                        visual_prompt=str(row["visual_prompt"]),
                        duration_ms=int(row["duration_ms"]),
                        character_anchors=tuple(
                            item for item in row["character_anchors"] if isinstance(item, str)
                        )
                        if isinstance(row["character_anchors"], list)
                        else (),
                    )
                    for row in scene_rows
                ),
            )
            if source.profile_id != expected_profile_id:
                raise ParentVideoCandidateError(409, "PARENT_VIDEO_STORY_NOT_CONFIRMED")

            if (
                not principal.issuer
                or len(principal.issuer) > 64
                or not principal.subject
                or len(principal.subject) > 128
            ):
                raise ParentVideoCandidateError(403, "ACTION_NOT_ALLOWED")
            now = datetime.now(UTC)
            self._session.execute(
                insert(story_tables.parent_video_candidate_jobs).values(
                    video_candidate_id=video_candidate_id,
                    run_id=run_id,
                    owner_issuer=principal.issuer,
                    owner_subject=principal.subject,
                    story_revision_id=source.story_revision_id,
                    story_revision_no=source.story_revision_no,
                    story_sha256=source.story_sha256,
                    source_asset_ref=source.source_asset_ref,
                    source_asset_version=source.source_asset_version,
                    source_asset_sha256=source.source_asset_sha256,
                    source_media_type=source.source_media_type,
                    activity_selection_id=source.activity_selection_id,
                    activity_snapshot_sha256=source.activity_snapshot_sha256,
                    idempotency_key_sha256=idempotency_key_sha256,
                    request_fingerprint_sha256=request_fingerprint_sha256,
                    state="STAGING",
                    modal_call_id=None,
                    job_id=job_id,
                    generation_id=generation_id,
                    attempt_id=attempt_id,
                    attempt_prefix=attempt_prefix,
                    output_asset_ref=None,
                    output_sha256=None,
                    output_size_bytes=None,
                    output_manifest_sha256=None,
                    output_metadata=None,
                    safe_failure_code=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._session.commit()
            created = (
                self._session.execute(
                    select(story_tables.parent_video_candidate_jobs).where(
                        story_tables.parent_video_candidate_jobs.c.video_candidate_id
                        == video_candidate_id
                    )
                )
                .mappings()
                .one()
            )
            return self._record(created), source, False
        except ParentVideoCandidateError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise ParentVideoCandidateError(409, "VIDEO_CANDIDATE_IDEMPOTENCY_CONFLICT") from None
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentVideoCandidateError(
                503, "PARENT_VIDEO_CANDIDATE_STORE_UNAVAILABLE"
            ) from None

    def get_current_candidate(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentVideoCandidateRecord | None:
        self._owned_run(principal=principal, run_id=run_id)
        row = (
            self._session.execute(
                select(story_tables.parent_video_candidate_jobs).where(
                    story_tables.parent_video_candidate_jobs.c.run_id == run_id,
                    story_tables.parent_video_candidate_jobs.c.owner_issuer == principal.issuer,
                    story_tables.parent_video_candidate_jobs.c.owner_subject == principal.subject,
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._record(row) if row is not None else None

    def get_candidate(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord:
        self._owned_run(principal=principal, run_id=run_id)
        row = (
            self._session.execute(
                select(story_tables.parent_video_candidate_jobs).where(
                    story_tables.parent_video_candidate_jobs.c.run_id == run_id,
                    story_tables.parent_video_candidate_jobs.c.video_candidate_id
                    == video_candidate_id,
                    story_tables.parent_video_candidate_jobs.c.owner_issuer == principal.issuer,
                    story_tables.parent_video_candidate_jobs.c.owner_subject == principal.subject,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise ParentVideoCandidateError(404, "VIDEO_CANDIDATE_NOT_FOUND")
        return self._record(row)

    def mark_dispatching(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord:
        return self._transition(
            principal=principal,
            run_id=run_id,
            video_candidate_id=video_candidate_id,
            expected={"STAGING"},
            values={"state": "DISPATCHING"},
            conflict_code="VIDEO_CANDIDATE_STATE_CONFLICT",
        )

    def mark_dispatched(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        modal_call_id: str,
    ) -> ParentVideoCandidateRecord:
        if not modal_call_id.startswith("fc-") or len(modal_call_id) > 128:
            raise ParentVideoCandidateError(502, "VIDEO_WORKER_CALL_REFERENCE_INVALID")
        return self._transition(
            principal=principal,
            run_id=run_id,
            video_candidate_id=video_candidate_id,
            expected={"DISPATCHING"},
            values={"state": "QUEUED", "modal_call_id": modal_call_id},
            conflict_code="VIDEO_CANDIDATE_STATE_CONFLICT",
        )

    def mark_generating(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord:
        return self._transition(
            principal=principal,
            run_id=run_id,
            video_candidate_id=video_candidate_id,
            expected={"QUEUED", "GENERATING"},
            values={"state": "GENERATING"},
            conflict_code="VIDEO_CANDIDATE_STATE_CONFLICT",
        )

    def mark_dispatch_uncertain(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord:
        return self._transition(
            principal=principal,
            run_id=run_id,
            video_candidate_id=video_candidate_id,
            expected={"DISPATCHING", "QUEUED", "GENERATING", "AWAITING_RECONCILIATION"},
            values={"state": "AWAITING_RECONCILIATION"},
            conflict_code="VIDEO_CANDIDATE_STATE_CONFLICT",
        )

    def mark_failed(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        safe_failure_code: str,
    ) -> ParentVideoCandidateRecord:
        if not safe_failure_code or len(safe_failure_code) > 80:
            raise ParentVideoCandidateError(500, "VIDEO_WORKER_FAILED")
        return self._transition(
            principal=principal,
            run_id=run_id,
            video_candidate_id=video_candidate_id,
            expected={"STAGING", "DISPATCHING", "QUEUED", "GENERATING", "AWAITING_RECONCILIATION"},
            values={"state": "FAILED", "safe_failure_code": safe_failure_code},
            conflict_code="VIDEO_CANDIDATE_STATE_CONFLICT",
        )

    def mark_candidate_ready(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        output_asset_ref: str,
        output_sha256: str,
        output_size_bytes: int,
        output_manifest_sha256: str,
        output_metadata: dict[str, Any],
    ) -> ParentVideoCandidateRecord:
        return self._transition(
            principal=principal,
            run_id=run_id,
            video_candidate_id=video_candidate_id,
            expected={"QUEUED", "GENERATING", "AWAITING_RECONCILIATION"},
            values={
                "state": "CANDIDATE_READY",
                "output_asset_ref": output_asset_ref,
                "output_sha256": output_sha256,
                "output_size_bytes": output_size_bytes,
                "output_manifest_sha256": output_manifest_sha256,
                "output_metadata": output_metadata,
            },
            conflict_code="VIDEO_CANDIDATE_STATE_CONFLICT",
        )

    def begin_output_contract_recovery(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord | None:
        """Claim one same-call revalidation after a deterministic output-contract rejection."""
        try:
            self._owned_run(principal=principal, run_id=run_id, lock=True)
            candidate = story_tables.parent_video_candidate_jobs
            row = (
                self._session.execute(
                    select(candidate)
                    .where(
                        candidate.c.run_id == run_id,
                        candidate.c.video_candidate_id == video_candidate_id,
                        candidate.c.owner_issuer == principal.issuer,
                        candidate.c.owner_subject == principal.subject,
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise ParentVideoCandidateError(404, "VIDEO_CANDIDATE_NOT_FOUND")
            call_id = row["modal_call_id"]
            prefix = row["attempt_prefix"]
            if (
                row["state"] != "FAILED"
                or row["safe_failure_code"] != "VIDEO_WORKER_OUTPUT_INVALID"
                or row["output_metadata"] is not None
                or not isinstance(call_id, str)
                or not call_id.startswith("fc-")
                or len(call_id) > 128
                or not isinstance(prefix, str)
                or not prefix.startswith("sketch2life/dev/")
                or not prefix.endswith("/")
            ):
                self._session.commit()
                return None

            recovery_marker = {
                "recovery": {
                    "kind": "same_modal_output_contract_revalidation_v1",
                    "source_failure_code": "VIDEO_WORKER_OUTPUT_INVALID",
                    "attempt_count": 1,
                }
            }
            updated = self._session.execute(
                update(candidate)
                .where(
                    candidate.c.run_id == run_id,
                    candidate.c.video_candidate_id == video_candidate_id,
                    candidate.c.owner_issuer == principal.issuer,
                    candidate.c.owner_subject == principal.subject,
                    candidate.c.state == "FAILED",
                    candidate.c.safe_failure_code == "VIDEO_WORKER_OUTPUT_INVALID",
                    candidate.c.modal_call_id == call_id,
                    candidate.c.attempt_prefix == prefix,
                    candidate.c.output_metadata.is_(None),
                )
                .values(
                    state="AWAITING_RECONCILIATION",
                    safe_failure_code=None,
                    output_metadata=recovery_marker,
                    updated_at=datetime.now(UTC),
                )
            )
            if updated.rowcount != 1:
                self._session.rollback()
                return None
            self._session.commit()
            refreshed = (
                self._session.execute(
                    select(candidate).where(
                        candidate.c.run_id == run_id,
                        candidate.c.video_candidate_id == video_candidate_id,
                        candidate.c.owner_issuer == principal.issuer,
                        candidate.c.owner_subject == principal.subject,
                    )
                )
                .mappings()
                .one()
            )
            return self._record(refreshed)
        except ParentVideoCandidateError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentVideoCandidateError(
                503, "PARENT_VIDEO_CANDIDATE_STORE_UNAVAILABLE"
            ) from None

    def _transition(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        expected: set[str],
        values: dict[str, Any],
        conflict_code: str,
    ) -> ParentVideoCandidateRecord:
        try:
            self._owned_run(principal=principal, run_id=run_id, lock=True)
            candidate = story_tables.parent_video_candidate_jobs
            query = (
                select(candidate)
                .where(
                    candidate.c.run_id == run_id,
                    candidate.c.video_candidate_id == video_candidate_id,
                    candidate.c.owner_issuer == principal.issuer,
                    candidate.c.owner_subject == principal.subject,
                )
                .with_for_update()
            )
            row = self._session.execute(query).mappings().one_or_none()
            if row is None:
                raise ParentVideoCandidateError(404, "VIDEO_CANDIDATE_NOT_FOUND")
            if row["state"] not in expected:
                if row["state"] == "FAILED" and values.get("state") == "FAILED":
                    self._session.commit()
                    return self._record(row)
                raise ParentVideoCandidateError(409, conflict_code)
            self._session.execute(
                update(candidate)
                .where(candidate.c.video_candidate_id == video_candidate_id)
                .values(**values, updated_at=datetime.now(UTC))
            )
            self._session.commit()
            updated = (
                self._session.execute(
                    select(candidate).where(candidate.c.video_candidate_id == video_candidate_id)
                )
                .mappings()
                .one()
            )
            return self._record(updated)
        except ParentVideoCandidateError:
            self._session.rollback()
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ParentVideoCandidateError(
                503, "PARENT_VIDEO_CANDIDATE_STORE_UNAVAILABLE"
            ) from None

    def _owned_run(self, *, principal: VerifiedPrincipal, run_id: str, lock: bool = False):
        query = select(story_tables.story_runs).where(
            story_tables.story_runs.c.run_id == run_id,
            story_tables.story_runs.c.actor_scope_kind == _OWNER_SCOPE_KIND,
            story_tables.story_runs.c.actor_scope_ref == _principal_scope_ref(principal),
        )
        if lock:
            query = query.with_for_update()
        row = self._session.execute(query).mappings().one_or_none()
        if row is None:
            raise ParentVideoCandidateError(404, "RESOURCE_NOT_FOUND")
        if row["run_state"] in _PURGE_STATES:
            raise ParentVideoCandidateError(409, "INVALID_STATE_TRANSITION")
        return row

    @staticmethod
    def _record(row) -> ParentVideoCandidateRecord:
        return ParentVideoCandidateRecord(
            video_candidate_id=str(row["video_candidate_id"]),
            run_id=str(row["run_id"]),
            story_revision_id=str(row["story_revision_id"]),
            story_revision_no=int(row["story_revision_no"]),
            story_sha256=str(row["story_sha256"]),
            source_asset_sha256=str(row["source_asset_sha256"]),
            activity_selection_id=str(row["activity_selection_id"]),
            activity_snapshot_sha256=str(row["activity_snapshot_sha256"]),
            state=str(row["state"]),
            modal_call_id=row["modal_call_id"],
            job_id=str(row["job_id"]),
            generation_id=str(row["generation_id"]),
            attempt_id=str(row["attempt_id"]),
            attempt_prefix=str(row["attempt_prefix"]),
            output_asset_ref=row["output_asset_ref"],
            output_sha256=row["output_sha256"],
            output_size_bytes=(
                int(row["output_size_bytes"]) if row["output_size_bytes"] is not None else None
            ),
            output_manifest_sha256=row["output_manifest_sha256"],
            output_metadata=dict(row["output_metadata"])
            if isinstance(row["output_metadata"], dict)
            else None,
            safe_failure_code=row["safe_failure_code"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _principal_scope_ref(principal: VerifiedPrincipal) -> str:
    return hashlib.sha256(
        _canonical_json({"issuer": principal.issuer, "subject": principal.subject}).encode("utf-8")
    ).hexdigest()


__all__ = ["SqlParentVideoCandidateRepository"]
