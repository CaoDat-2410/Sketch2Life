"""Orchestrate one local synthetic Parent candidate through the deployed LTX worker."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from contextlib import suppress
from io import BytesIO
from typing import Any
from uuid import uuid4

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupPort,
    ParentStoryProfileLookupUnavailable,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    ParentStoryRunRecord,
    ParentStoryRunRepositoryPort,
)
from sketch2life.application.ports.parent_video_candidates import (
    ParentVideoCandidateError,
    ParentVideoCandidateRecord,
    ParentVideoCandidateRepositoryPort,
    ParentVideoCandidateSource,
    SilentStoryVideoWorkerPort,
    SilentStoryWorkerOutput,
)
from sketch2life.domain.story_run_lite import StoryRunLiteError, validate_idempotency_key

_LOGGER = logging.getLogger(__name__)
_SCHEMA = "sketch2life.modal.silent-story-video-input.v2"
_WORKER_SCHEMA = "sketch2life.modal.worker-input.v1"
_WORKLOAD = "video.story.generate"
_VIDEO_PROFILE = "ltx25-distilled-bf16-fp8-cpu-offload-l40s-v1"
_MODEL_ID = "Lightricks/LTX-2.5"
_MODEL_REVISION = "49b093a39c19169a8a81721dcc541e07e945232f"
_MODEL_CODE_COMMIT = "f0f2f8607189c78a72420b2b63cb1975b5eca179"
_VIDEO_FPS = 24
_FRAME_QUANTUM = 8
_MIN_MODEL_FRAMES = 9
_MIN_SCENE_FRAMES = 25  # One second rounded to the nearest 1+8k frame count.
_MAX_SCENE_FRAMES = 473  # Largest 1+8k frame count that remains at or below 20 seconds.
_MIN_STORY_FRAMES = 30 * _VIDEO_FPS
_MAX_STORY_FRAMES = 90 * _VIDEO_FPS
_MAX_DRAWING_BYTES = 20 * 1024 * 1024
_MAX_VIDEO_BYTES = 256 * 1024 * 1024
_SAFE_CODE = re.compile(r"\b(?:LTX|VIDEO|MODAL|WORKER)_[A-Z0-9_]{3,90}\b")


class ParentVideoCandidateService:
    def __init__(
        self,
        *,
        settings: Any,
        story_repository: ParentStoryRunRepositoryPort,
        profile_lookup: ParentStoryProfileLookupPort,
        candidate_repository: ParentVideoCandidateRepositoryPort,
        storage: ObjectStoragePort,
        worker: SilentStoryVideoWorkerPort,
    ) -> None:
        self._settings = settings
        self._story_repository = story_repository
        self._profile_lookup = profile_lookup
        self._repository = candidate_repository
        self._storage = storage
        self._worker = worker

    def request(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_story_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> tuple[ParentVideoCandidateRecord, bool]:
        self._require_candidate_configuration()
        try:
            idempotency_hash = validate_idempotency_key(idempotency_key)
        except StoryRunLiteError as exc:
            raise ParentVideoCandidateError(400, exc.code) from None

        run = self._owned_current_run(principal=principal, run_id=run_id)
        if (
            run.run_state != "SCRIPT_REVIEW"
            or run.story_status != "CONFIRMED"
            or run.story_revision_no != expected_story_revision
            or run.story_sha256 != expected_story_sha256
        ):
            raise ParentVideoCandidateError(409, "PARENT_VIDEO_STORY_NOT_CONFIRMED")
        try:
            profile = self._profile_lookup.get_owned_profile_current_revision(
                principal=principal, profile_id=run.parent_profile_id
            )
        except ParentStoryProfileLookupUnavailable:
            raise ParentVideoCandidateError(503, "PARENT_PROFILE_UNAVAILABLE") from None
        if (
            profile is None
            or profile.state != "ACTIVE"
            or profile.data_origin not in {"SYNTHETIC_DEV", "SYNTHETIC_TEST"}
        ):
            raise ParentVideoCandidateError(403, "SYNTHETIC_PROFILE_REQUIRED")

        fingerprint = _sha256_json(
            {
                "contract": "sketch2life.parent-video-candidate-request.v1",
                "run_id": run_id,
                "story_revision": expected_story_revision,
                "story_sha256": expected_story_sha256,
            }
        )
        job_id, generation_id, attempt_id = (str(uuid4()) for _ in range(3))
        attempt_prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"
        try:
            record, source, replayed = self._repository.reserve_candidate(
                principal=principal,
                run_id=run_id,
                expected_profile_id=str(profile.profile_id),
                expected_story_revision=expected_story_revision,
                expected_story_sha256=expected_story_sha256,
                idempotency_key_sha256=idempotency_hash,
                request_fingerprint_sha256=fingerprint,
                video_candidate_id=str(uuid4()),
                job_id=job_id,
                generation_id=generation_id,
                attempt_id=attempt_id,
                attempt_prefix=attempt_prefix,
            )
        except ParentVideoCandidateError:
            raise
        except ParentStoryRunError as exc:
            raise ParentVideoCandidateError(exc.status_code, exc.code) from None
        if replayed:
            return record, True
        if source is None:
            self._fail(principal, run_id, record.video_candidate_id, "VIDEO_SOURCE_UNAVAILABLE")
            raise ParentVideoCandidateError(503, "VIDEO_SOURCE_UNAVAILABLE")

        started = time.monotonic()
        stage = "source_read"
        try:
            drawing = self._read_source_drawing(source)
            manifest = _build_input_manifest(source)
            manifest_bytes = _canonical_json(manifest)
            if len(drawing) + len(manifest_bytes) > 48 * 1024 * 1024:
                raise ParentVideoCandidateError(413, "VIDEO_INPUT_LIMIT_EXCEEDED")
            worker_input = _worker_input(
                job_id=record.job_id,
                generation_id=record.generation_id,
                attempt_id=record.attempt_id,
                attempt_prefix=record.attempt_prefix,
                manifest_bytes=manifest_bytes,
                input_bytes=len(drawing) + len(manifest_bytes),
            )
            self._repository.mark_dispatching(
                principal=principal,
                run_id=run_id,
                video_candidate_id=record.video_candidate_id,
            )
            stage = "modal_dispatch"
            call_id = self._worker.dispatch(
                worker_input=worker_input,
                drawing_bytes=drawing,
                manifest_bytes=manifest_bytes,
            )
            record = self._repository.mark_dispatched(
                principal=principal,
                run_id=run_id,
                video_candidate_id=record.video_candidate_id,
                modal_call_id=call_id,
            )
            _LOGGER.info(
                "parent_video_candidate_dispatched candidate_id=%s run_id=%s "
                "stage=%s story_duration_ms=%s render_duration_ms=%s elapsed_ms=%s",
                record.video_candidate_id,
                record.run_id,
                stage,
                source.story_duration_ms,
                round(float(manifest["target_duration_seconds"]) * 1_000),
                round((time.monotonic() - started) * 1000),
            )
            return record, False
        except ParentVideoCandidateError as exc:
            self._fail(principal, run_id, record.video_candidate_id, exc.code)
            raise
        except Exception as exc:  # noqa: BLE001 - provider detail stays in safe worker logs.
            self._repository.mark_dispatch_uncertain(
                principal=principal,
                run_id=run_id,
                video_candidate_id=record.video_candidate_id,
            )
            code = _safe_failure_code(exc)
            _LOGGER.error(
                "parent_video_candidate_dispatch_failed candidate_id=%s run_id=%s "
                "stage=%s error_code=%s exception_type=%s elapsed_ms=%s",
                record.video_candidate_id,
                run_id,
                stage,
                code,
                type(exc).__name__,
                round((time.monotonic() - started) * 1000),
            )
            raise ParentVideoCandidateError(503, "VIDEO_DISPATCH_OUTCOME_UNKNOWN") from None

    def get_current(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentVideoCandidateRecord | None:
        self._require_candidate_configuration()
        record = self._repository.get_current_candidate(principal=principal, run_id=run_id)
        return self._reconcile(principal=principal, run_id=run_id, record=record)

    def get(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord:
        self._require_candidate_configuration()
        record = self._repository.get_candidate(
            principal=principal, run_id=run_id, video_candidate_id=video_candidate_id
        )
        return self._reconcile(principal=principal, run_id=run_id, record=record) or record

    def get_preview_object(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ):
        self._require_candidate_configuration()
        record = self._repository.get_candidate(
            principal=principal, run_id=run_id, video_candidate_id=video_candidate_id
        )
        if record.state != "CANDIDATE_READY" or not record.output_asset_ref:
            raise ParentVideoCandidateError(409, "VIDEO_CANDIDATE_NOT_READY")
        try:
            result = self._storage.get_object(record.output_asset_ref)
        except ObjectStorageFailure:
            raise ParentVideoCandidateError(503, "VIDEO_CANDIDATE_STORAGE_UNAVAILABLE") from None
        if result is None:
            raise ParentVideoCandidateError(404, "VIDEO_CANDIDATE_NOT_FOUND")
        if (
            result.content_type != "video/mp4"
            or result.content_length != record.output_size_bytes
            or result.metadata.get("output-sha256") != record.output_sha256
        ):
            with suppress(Exception):
                result.body.close()
            raise ParentVideoCandidateError(502, "VIDEO_CANDIDATE_OUTPUT_INVALID")
        return result

    def _reconcile(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        record: ParentVideoCandidateRecord | None,
    ) -> ParentVideoCandidateRecord | None:
        if record is None:
            return record
        recovering_output_contract = False
        if (
            record.state == "FAILED"
            and record.safe_failure_code == "VIDEO_WORKER_OUTPUT_INVALID"
            and record.modal_call_id
            and record.attempt_prefix
            and not _has_output_contract_recovery_marker(record)
        ):
            recovered = self._repository.begin_output_contract_recovery(
                principal=principal,
                run_id=run_id,
                video_candidate_id=record.video_candidate_id,
            )
            if recovered is None:
                return self._repository.get_candidate(
                    principal=principal,
                    run_id=run_id,
                    video_candidate_id=record.video_candidate_id,
                )
            record = recovered
            recovering_output_contract = True
        if record.state in {"DISPATCHING", "STAGING"}:
            age_seconds = max(0.0, (time.time() - record.updated_at.timestamp()))
            if age_seconds >= 300 and record.state == "DISPATCHING":
                return self._repository.mark_dispatch_uncertain(
                    principal=principal,
                    run_id=run_id,
                    video_candidate_id=record.video_candidate_id,
                )
            if age_seconds >= 300 and record.state == "STAGING":
                return self._repository.mark_failed(
                    principal=principal,
                    run_id=run_id,
                    video_candidate_id=record.video_candidate_id,
                    safe_failure_code="VIDEO_REQUEST_INTERRUPTED_BEFORE_DISPATCH",
                )
            return record
        if record.state not in {"QUEUED", "GENERATING"} and not (
            recovering_output_contract and record.state == "AWAITING_RECONCILIATION"
        ):
            return record
        if not record.modal_call_id:
            return self._repository.mark_dispatch_uncertain(
                principal=principal, run_id=run_id, video_candidate_id=record.video_candidate_id
            )
        started = time.monotonic()
        try:
            output = self._worker.collect_if_ready(
                modal_call_id=record.modal_call_id,
                job_id=record.job_id,
                generation_id=record.generation_id,
                attempt_id=record.attempt_id,
                attempt_prefix=record.attempt_prefix,
            )
            if output is None:
                if recovering_output_contract:
                    self._fail(
                        principal,
                        run_id,
                        record.video_candidate_id,
                        "VIDEO_OUTPUT_RECOVERY_FAILED",
                    )
                    return self._repository.get_candidate(
                        principal=principal,
                        run_id=run_id,
                        video_candidate_id=record.video_candidate_id,
                    )
                if record.state == "QUEUED":
                    record = self._repository.mark_generating(
                        principal=principal,
                        run_id=run_id,
                        video_candidate_id=record.video_candidate_id,
                    )
                return record
            metadata = _validate_worker_output(output, record)
            if recovering_output_contract:
                recovery = (record.output_metadata or {}).get("recovery")
                if isinstance(recovery, dict):
                    metadata["recovery"] = recovery
            output_ref = (
                f"parent/{run_id}/video-candidates/{record.video_candidate_id}/candidate.mp4"
            )
            try:
                self._storage.put_object(
                    output_ref,
                    BytesIO(output.video_bytes),
                    content_type="video/mp4",
                    content_length=len(output.video_bytes),
                    metadata={
                        "story-sha256": record.story_sha256,
                        "source-drawing-sha256": record.source_asset_sha256,
                        "output-sha256": metadata["output_sha256"],
                        "video-candidate-id": record.video_candidate_id,
                    },
                )
            except ObjectStorageFailure:
                raise ParentVideoCandidateError(
                    503, "VIDEO_CANDIDATE_STORAGE_UNAVAILABLE"
                ) from None
            ready = self._repository.mark_candidate_ready(
                principal=principal,
                run_id=run_id,
                video_candidate_id=record.video_candidate_id,
                output_asset_ref=output_ref,
                output_sha256=metadata["output_sha256"],
                output_size_bytes=metadata["output_size_bytes"],
                output_manifest_sha256=metadata["output_manifest_sha256"],
                output_metadata=metadata,
            )
            _LOGGER.info(
                "parent_video_candidate_ready candidate_id=%s run_id=%s "
                "scene_count=%s elapsed_ms=%s safety_validation=NOT_RUN "
                "product_playable=false",
                ready.video_candidate_id,
                ready.run_id,
                metadata["scene_count"],
                round((time.monotonic() - started) * 1000),
            )
            return ready
        except ParentVideoCandidateError as exc:
            code = "VIDEO_OUTPUT_RECOVERY_FAILED" if recovering_output_contract else exc.code
            self._fail(principal, run_id, record.video_candidate_id, code)
            if recovering_output_contract:
                _LOGGER.error(
                    "parent_video_candidate_output_recovery_failed candidate_id=%s run_id=%s "
                    "error_code=%s exception_type=%s elapsed_ms=%s",
                    record.video_candidate_id,
                    run_id,
                    code,
                    type(exc).__name__,
                    round((time.monotonic() - started) * 1000),
                )
                return self._repository.get_candidate(
                    principal=principal, run_id=run_id, video_candidate_id=record.video_candidate_id
                )
            raise
        except Exception as exc:  # noqa: BLE001 - no provider exception is returned to the UI.
            code = (
                "VIDEO_OUTPUT_RECOVERY_FAILED"
                if recovering_output_contract
                else _safe_failure_code(exc)
            )
            _LOGGER.error(
                "parent_video_candidate_reconcile_failed candidate_id=%s run_id=%s "
                "stage=worker_collect error_code=%s exception_type=%s elapsed_ms=%s",
                record.video_candidate_id,
                run_id,
                code,
                type(exc).__name__,
                round((time.monotonic() - started) * 1000),
            )
            self._fail(principal, run_id, record.video_candidate_id, code)
            return self._repository.get_candidate(
                principal=principal, run_id=run_id, video_candidate_id=record.video_candidate_id
            )

    def _owned_current_run(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentStoryRunRecord:
        try:
            run = self._story_repository.get_run(principal=principal, run_id=run_id)
        except ParentStoryRunError as exc:
            raise ParentVideoCandidateError(exc.status_code, exc.code) from None
        if isinstance(run, ParentStoryLifecycleRecord):
            raise ParentVideoCandidateError(409, "INVALID_STATE_TRANSITION")
        return run

    def _read_source_drawing(self, source: ParentVideoCandidateSource) -> bytes:
        if (
            source.source_size_bytes < 1
            or source.source_size_bytes > _MAX_DRAWING_BYTES
            or source.source_media_type not in {"image/png", "image/jpeg", "image/webp"}
        ):
            raise ParentVideoCandidateError(422, "VIDEO_DRAWING_INPUT_INVALID")
        try:
            stored = self._storage.get_object(source.source_asset_ref)
        except ObjectStorageFailure:
            raise ParentVideoCandidateError(503, "VIDEO_SOURCE_STORAGE_UNAVAILABLE") from None
        if stored is None:
            raise ParentVideoCandidateError(404, "VIDEO_SOURCE_NOT_FOUND")
        try:
            raw = stored.body.read(_MAX_DRAWING_BYTES + 1)
        except Exception:
            raise ParentVideoCandidateError(503, "VIDEO_SOURCE_STORAGE_UNAVAILABLE") from None
        finally:
            with suppress(Exception):
                stored.body.close()
        if (
            len(raw) != source.source_size_bytes
            or len(raw) > _MAX_DRAWING_BYTES
            or hashlib.sha256(raw).hexdigest() != source.source_asset_sha256
        ):
            raise ParentVideoCandidateError(409, "VIDEO_SOURCE_HASH_MISMATCH")
        return raw

    def _require_candidate_configuration(self) -> None:
        if (
            self._settings.env not in {"local", "test"}
            or not self._settings.parent_video_dev_candidate_enabled
            or self._settings.ai_provider != "modal_dev"
            or not self._settings.synthetic_pilot_enabled
        ):
            raise ParentVideoCandidateError(503, "PARENT_VIDEO_CANDIDATE_DISABLED")

    def _fail(
        self, principal: VerifiedPrincipal, run_id: str, candidate_id: str, code: str
    ) -> None:
        try:
            self._repository.mark_failed(
                principal=principal,
                run_id=run_id,
                video_candidate_id=candidate_id,
                safe_failure_code=_safe_failure_code(code),
            )
        except ParentVideoCandidateError:
            raise


def _build_input_manifest(source: ParentVideoCandidateSource) -> dict[str, Any]:
    source_duration_seconds = source.story_duration_ms / 1_000
    scene_duration_seconds = sum(scene.duration_ms for scene in source.scenes) / 1_000
    if (
        not 30 <= source_duration_seconds <= 90
        or abs(scene_duration_seconds - source_duration_seconds) > 0.1
    ):
        raise ParentVideoCandidateError(422, "VIDEO_STORY_TIMELINE_INVALID")

    scenes: list[dict[str, Any]] = []
    for expected_index, scene in enumerate(source.scenes, start=1):
        title = scene.title.strip()
        action = scene.action.strip()
        visual_prompt = scene.visual_prompt.strip()
        if (
            scene.scene_index != expected_index
            or not 1 <= len(title) <= 100
            or not 1 <= len(action) <= 500
            or not visual_prompt
            or len(visual_prompt) > 1_200
        ):
            raise ParentVideoCandidateError(422, "VIDEO_STORY_SCENE_INVALID")
        model_action_instruction = visual_prompt if len(visual_prompt) >= 8 else action
        if not 8 <= len(model_action_instruction) <= 400:
            raise ParentVideoCandidateError(422, "VIDEO_STORY_SCENE_INVALID")
        duration_frames = min(
            _MAX_SCENE_FRAMES,
            max(_MIN_SCENE_FRAMES, _nearest_model_frames(scene.duration_ms / 1_000)),
        )
        seed = (
            int.from_bytes(
                hashlib.sha256(f"{source.story_sha256}:{expected_index}".encode("ascii")).digest()[
                    :4
                ],
                "big",
            )
            & 0x7FFFFFFF
        )
        scenes.append(
            {
                "scene_id": f"scene-{expected_index}",
                "scene_index": expected_index,
                "title": title,
                "action": action,
                "visual_prompt": visual_prompt,
                "duration_seconds": duration_frames / _VIDEO_FPS,
                "seed": seed,
                "confirmed_anchor_ids": _scene_anchors(
                    scene.character_anchors, source.confirmed_subject
                ),
                "_target_duration_frames": round(scene.duration_ms / 1_000 * _VIDEO_FPS),
            }
        )
    if not 5 <= len(scenes) <= 15:
        raise ParentVideoCandidateError(422, "VIDEO_STORY_TIMELINE_INVALID")

    target_frames = [int(scene.pop("_target_duration_frames")) for scene in scenes]
    total_frames = sum(round(float(scene["duration_seconds"]) * _VIDEO_FPS) for scene in scenes)
    while total_frames < _MIN_STORY_FRAMES:
        adjustable = [
            index
            for index, scene in enumerate(scenes)
            if round(float(scene["duration_seconds"]) * _VIDEO_FPS) + _FRAME_QUANTUM
            <= _MAX_SCENE_FRAMES
        ]
        if not adjustable:
            raise ParentVideoCandidateError(422, "VIDEO_STORY_TIMELINE_INVALID")
        index = min(
            adjustable,
            key=lambda item: _duration_change_cost(
                round(float(scenes[item]["duration_seconds"]) * _VIDEO_FPS),
                target_frames[item],
                _FRAME_QUANTUM,
            ),
        )
        scenes[index]["duration_seconds"] += _FRAME_QUANTUM / _VIDEO_FPS
        total_frames += _FRAME_QUANTUM
    while total_frames > _MAX_STORY_FRAMES:
        adjustable = [
            index
            for index, scene in enumerate(scenes)
            if round(float(scene["duration_seconds"]) * _VIDEO_FPS) - _FRAME_QUANTUM
            >= _MIN_SCENE_FRAMES
        ]
        if not adjustable:
            raise ParentVideoCandidateError(422, "VIDEO_STORY_TIMELINE_INVALID")
        index = min(
            adjustable,
            key=lambda item: _duration_change_cost(
                round(float(scenes[item]["duration_seconds"]) * _VIDEO_FPS),
                target_frames[item],
                -_FRAME_QUANTUM,
            ),
        )
        scenes[index]["duration_seconds"] -= _FRAME_QUANTUM / _VIDEO_FPS
        total_frames -= _FRAME_QUANTUM

    duration_seconds = total_frames / _VIDEO_FPS
    if not 30 <= duration_seconds <= 90 or any(
        abs(
            round(float(scene["duration_seconds"]) * _VIDEO_FPS)
            - float(scene["duration_seconds"]) * _VIDEO_FPS
        )
        > 0.0001
        for scene in scenes
    ):
        raise ParentVideoCandidateError(422, "VIDEO_STORY_TIMELINE_INVALID")

    for scene in scenes:
        # Keep the generated frame plan as an exact fraction so the worker's
        # nearest 1+8k frame calculation is deterministic and reproduces it.
        scene["duration_seconds"] = (
            round(float(scene["duration_seconds"]) * _VIDEO_FPS) / _VIDEO_FPS
        )

    visual_scenes = []
    for index, scene in enumerate(scenes, start=1):
        visual_scenes.append(
            {
                "scene_id": scene["scene_id"],
                "approved_action": scene["action"],
                "duration_seconds": scene["duration_seconds"],
                "visible_entity_ids": ["subject-main"],
                "introduced_entity_ids": [],
                "removed_entity_ids": [],
                "continuity_in": (
                    "Start from the original drawing; preserve its full composition."
                    if index == 1
                    else "Continue from the prior final frame; preserve the drawn subject."
                ),
                "continuity_out": (
                    "Keep the drawn subject stable and fully in frame for the next scene."
                ),
                "spatial_direction": (
                    "Preserve drawing position, scale, silhouette, colors, and texture."
                ),
                "model_action_instruction": (
                    scene["visual_prompt"] if len(scene["visual_prompt"]) >= 8 else scene["action"]
                ),
                "camera_motion": "locked",
            }
        )
    visual_plan = {
        "schema_version": "sketch2life.modal.story-visual-plan.v2",
        "source_story_sha256": source.story_sha256,
        "entities": [
            {
                "entity_id": "subject-main",
                "kind": "subject",
                "source": "source_drawing",
                "label": f"child-drawn {source.confirmed_subject[:64]}",
                "appearance": (
                    "Preserve the exact child drawing: silhouette, proportions, colors, "
                    "linework, texture, and composition. Do not redraw or restyle it."
                ),
            }
        ],
        "scenes": visual_scenes,
    }
    storyboard_payload = {
        "story_revision_id": source.story_revision_id,
        "story_sha256": source.story_sha256,
        "source_drawing_sha256": source.source_asset_sha256,
        "target_duration_seconds": float(duration_seconds),
        "scenes": scenes,
    }
    storyboard_sha256 = hashlib.sha256(_canonical_json(storyboard_payload)).hexdigest()
    render_plan_payload = {
        "schema_version": _SCHEMA,
        "story_revision_id": source.story_revision_id,
        "story_sha256": source.story_sha256,
        "storyboard_sha256": storyboard_sha256,
        "source_drawing_sha256": source.source_asset_sha256,
        "target_duration_seconds": float(duration_seconds),
        "scenes": scenes,
        "scene_visual_plan": visual_plan,
    }
    return {
        **render_plan_payload,
        "render_plan_sha256": hashlib.sha256(_canonical_json(render_plan_payload)).hexdigest(),
        "source_drawing_ref": "input/drawing.png",
        "scene_count": len(scenes),
    }


def _worker_input(
    *,
    job_id: str,
    generation_id: str,
    attempt_id: str,
    attempt_prefix: str,
    manifest_bytes: bytes,
    input_bytes: int,
) -> dict[str, Any]:
    return {
        "schema_version": _WORKER_SCHEMA,
        "environment": "dev",
        "workload": _WORKLOAD,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "input_bytes": input_bytes,
    }


def _scene_anchors(anchors: tuple[str, ...], confirmed_subject: str) -> list[str]:
    normalized = [
        value.strip()[:120] for value in anchors if isinstance(value, str) and value.strip()
    ]
    if not normalized:
        normalized = [confirmed_subject.strip()[:120]]
    return normalized[:16]


def _nearest_model_frames(duration_seconds: float) -> int:
    target_frames = round(duration_seconds * _VIDEO_FPS)
    lower = max(
        _MIN_MODEL_FRAMES,
        ((max(_MIN_MODEL_FRAMES, target_frames) - 1) // _FRAME_QUANTUM) * _FRAME_QUANTUM + 1,
    )
    upper = lower + _FRAME_QUANTUM
    return min((lower, upper), key=lambda frames: (abs(frames - target_frames), frames))


def _duration_change_cost(current_frames: int, target_frames: int, delta: int) -> int:
    return abs(current_frames + delta - target_frames) - abs(current_frames - target_frames)


def _validate_worker_output(
    output: SilentStoryWorkerOutput, record: ParentVideoCandidateRecord
) -> dict[str, Any]:
    result = output.result
    try:
        remote_manifest = json.loads(output.output_manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ParentVideoCandidateError(502, "VIDEO_WORKER_OUTPUT_INVALID") from None
    output_hash = hashlib.sha256(output.video_bytes).hexdigest()
    manifest_hash = hashlib.sha256(output.output_manifest_bytes).hexdigest()
    if not isinstance(result, dict) or not isinstance(remote_manifest, dict):
        raise ParentVideoCandidateError(502, "VIDEO_WORKER_OUTPUT_INVALID")
    media_metadata = {
        key: remote_manifest.get(key) for key in ("width", "height", "fps", "video_codec")
    }
    if any(
        key in result and result.get(key) != value
        for key, value in media_metadata.items()
    ):
        raise ParentVideoCandidateError(502, "VIDEO_WORKER_OUTPUT_INVALID")
    expected = {
        "schema_version": "sketch2life.modal.silent-story-video-output.v2",
        "workload": _WORKLOAD,
        "status": "CANDIDATE_READY",
        "product_playable": False,
        "safety_validation": "NOT_RUN",
        "audio_streams": 0,
        "job_id": record.job_id,
        "generation_id": record.generation_id,
        "attempt_id": record.attempt_id,
        "story_revision_id": record.story_revision_id,
        "story_sha256": record.story_sha256,
        "source_drawing_sha256": record.source_asset_sha256,
        "output_ref": "output/video.mp4",
    }
    model_manifest = remote_manifest.get("model")
    if (
        not isinstance(model_manifest, dict)
        or any(
            result.get(key) != value or remote_manifest.get(key) != value
            for key, value in expected.items()
        )
        or result.get("output_sha256") != output_hash
        or result.get("output_manifest_sha256") != manifest_hash
        or result.get("storyboard_sha256") != remote_manifest.get("storyboard_sha256")
        or result.get("render_plan_sha256") != remote_manifest.get("render_plan_sha256")
        or result.get("scene_visual_plan_sha256") != remote_manifest.get("scene_visual_plan_sha256")
        or remote_manifest.get("output_sha256") != output_hash
        or remote_manifest.get("output_size_bytes") != len(output.video_bytes)
        or result.get("output_size_bytes") != len(output.video_bytes)
        or remote_manifest.get("storyboard_sha256") != result.get("storyboard_sha256")
        or remote_manifest.get("render_plan_sha256") != result.get("render_plan_sha256")
        or remote_manifest.get("scene_count") != result.get("scene_count")
        or result.get("scene_count") not in range(5, 16)
        or result.get("model_profile") != _VIDEO_PROFILE
        or model_manifest.get("id") != _MODEL_ID
        or model_manifest.get("revision") != _MODEL_REVISION
        or model_manifest.get("code_commit") != _MODEL_CODE_COMMIT
        or model_manifest.get("model_profile") != _VIDEO_PROFILE
        or not 30 <= float(result.get("duration_seconds", 0)) <= 90
        or not isinstance(media_metadata["width"], int)
        or isinstance(media_metadata["width"], bool)
        or media_metadata["width"] != 1280
        or not isinstance(media_metadata["height"], int)
        or isinstance(media_metadata["height"], bool)
        or media_metadata["height"] != 720
        or isinstance(media_metadata["fps"], bool)
        or not isinstance(media_metadata["fps"], (int, float))
        or abs(float(media_metadata["fps"]) - 24) > 0.01
        or media_metadata["video_codec"] != "h264"
        or remote_manifest.get("duration_seconds") != result.get("duration_seconds")
        or not 0 < len(output.video_bytes) <= _MAX_VIDEO_BYTES
    ):
        raise ParentVideoCandidateError(502, "VIDEO_WORKER_OUTPUT_INVALID")
    return {
        "output_sha256": output_hash,
        "output_size_bytes": len(output.video_bytes),
        "output_manifest_sha256": manifest_hash,
        "duration_seconds": float(result["duration_seconds"]),
        "width": media_metadata["width"],
        "height": media_metadata["height"],
        "fps": float(media_metadata["fps"]),
        "video_codec": media_metadata["video_codec"],
        "audio_streams": 0,
        "scene_count": int(result["scene_count"]),
        "video_profile": result["model_profile"],
        "model_id": _MODEL_ID,
        "model_revision": _MODEL_REVISION,
        "technical_validation": "PASS",
        "consistency_validation": "NOT_RUN",
        "safety_validation": "NOT_RUN",
        "product_playable": False,
    }


def _has_output_contract_recovery_marker(record: ParentVideoCandidateRecord) -> bool:
    marker = (record.output_metadata or {}).get("recovery")
    return (
        isinstance(marker, dict)
        and marker.get("kind") == "same_modal_output_contract_revalidation_v1"
        and marker.get("attempt_count") == 1
    )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _safe_failure_code(error: BaseException | str) -> str:
    match = _SAFE_CODE.search(str(error))
    return match.group(0) if match else "VIDEO_WORKER_FAILED"


__all__ = ["ParentVideoCandidateService"]
