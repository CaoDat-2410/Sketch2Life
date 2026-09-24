"""Explicit, ephemeral image upload and Lightning Vision use cases for FEAT-018."""

from __future__ import annotations

import json
import secrets
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Literal, Protocol, cast
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.asr import AsrPort
from sketch2life.application.ports.renderer_source_storage import (
    RendererSourceGrant,
    RendererSourceGrantStore,
)
from sketch2life.application.ports.session_storage import (
    ArtifactStore,
    IdempotencyReceipt,
    IdempotencyStore,
)
from sketch2life.application.services.ephemeral_sessions import (
    DEMO_ACTOR_REF,
    EphemeralSessionService,
    SessionWorkflowError,
)
from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018AdmissionResult,
    Feat018ImageAdmission,
)
from sketch2life.application.services.raw_understanding_mapper import (
    RawUnderstandingMappingError,
    map_vision_result_to_raw,
)
from sketch2life.application.services.topic_semantics import (
    build_topic_directions,
    claims_from_raw,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrFailureV1,
    AsrProfileId,
    AsrRequestV1,
    AsrResultV1,
    AsrSuccessV1,
    MediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.image_demo import ImageAdmissionReceiptV1
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
    WorkflowResultProvenanceV1,
)
from sketch2life.contracts.schemas.narration import (
    NarrationAudioContentType,
    NarrationAudioV1,
    NarrationInputV1,
    NarrationNoneV1,
    NarrationReceiptV1,
    NarrationTextV1,
)
from sketch2life.contracts.schemas.p1_experience import ExperienceSpecV1
from sketch2life.contracts.schemas.raw_understanding import RawUnderstandingSuccessV1
from sketch2life.contracts.schemas.vision import (
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
)

_MAX_IMAGE_BYTES = 5_000_000
_MAX_AUDIO_BYTES = 20_000_000
_NARRATION_INPUT_ADAPTER: TypeAdapter[NarrationInputV1] = TypeAdapter(NarrationInputV1)
_ADMISSION_POLICY_VERSION = "FEAT018_P2_T1_D1_20260910"
_VISION_VERSION = WorkflowResultProvenanceV1(
    producer="VISION",
    component="lightning-vision-v2-mapper",
    component_version="1.0",
    source_contracts=("VisionUnderstandingResultV2", "RawUnderstandingResultV1"),
)
_ADMISSION_VERSION = WorkflowResultProvenanceV1(
    producer="APPLICATION",
    component="feat018-image-admission",
    component_version="1.0",
    source_contracts=("Feat018ImageAdmission", "ImageAdmissionReceiptV1"),
)
_NARRATION_VERSION = WorkflowResultProvenanceV1(
    producer="APPLICATION",
    component="feat018-narration-ingress",
    component_version="1.0",
    source_contracts=("NarrationInputV1", "NarrationReceiptV1"),
)


class VisionV2Port(Protocol):
    def understand(
        self, request: VisionUnderstandingRequestV2
    ) -> VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2: ...


class LiveImageDemoService:
    """Use the P2 admission boundary before any explicitly requested provider call.

    The adapter is injected and never invoked during session creation, image upload, app startup,
    or retries internal to this service. A caller must send a fresh explicit command to analyze.
    """

    def __init__(
        self,
        *,
        sessions: EphemeralSessionService,
        artifacts: ArtifactStore,
        idempotency: IdempotencyStore,
        admission: Feat018ImageAdmission,
        vision: VisionV2Port | None,
        renderer_source_grants: RendererSourceGrantStore,
        asr: AsrPort | None = None,
        asr_profile_id: AsrProfileId = AsrProfileId.WHISPER_TURBO_FP16_AUTO_V1,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts
        self._idempotency = idempotency
        self._admission = admission
        self._vision = vision
        self._asr = asr
        self._asr_profile_id = asr_profile_id
        self._renderer_source_grants = renderer_source_grants
        self._now = now
        self._lock = RLock()

    @property
    def artifact_store(self) -> ArtifactStore:
        """Expose the store used by image admission to downstream pipelines."""
        return self._artifacts

    def upload_image(
        self,
        *,
        session_id: str,
        request_id: str,
        expected_session_version: int,
        idempotency_key: str,
        actor_ref: str,
        synthetic_non_child_confirmed: bool,
        filename: str,
        body: bytes,
    ) -> tuple[MobileWorkflowResultV1, bool]:
        if actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        if not synthetic_non_child_confirmed:
            raise _workflow_error(
                "SYNTHETIC_NON_CHILD_CONFIRMATION_REQUIRED",
                422,
                "Use a synthetic, non-child image and confirm that before upload.",
            )
        if not filename or len(filename) > 200:
            raise _workflow_error("IMAGE_FILENAME_INVALID", 422, "Choose a valid image file.")

        fingerprint = sha256(
            b"FEAT018_IMAGE_UPLOAD_V1\0" + body + b"\0synthetic-non-child-confirmed"
        ).hexdigest()
        scope = f"{session_id}:UPLOAD_IMAGE"
        with self._lock:
            if replay := self._replay(scope, idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(session_id)
            if snapshot.version != expected_session_version:
                raise _stale_version()
            if snapshot.state not in {"CREATED", "MEDIA_RECAPTURE"}:
                raise _workflow_error(
                    "IMAGE_UPLOAD_NOT_ALLOWED",
                    409,
                    "Retake is required before replacing this image.",
                )
            prior = self._sessions.workflow_record(session_id)
            if (
                prior.values.get("source_image_ref") is not None
                and snapshot.state != "MEDIA_RECAPTURE"
            ):
                raise _workflow_error(
                    "IMAGE_ALREADY_ATTACHED",
                    409,
                    "Use the retake action before choosing another image.",
                )

            admission_result = self._admit(body)
            admitted = admission_result.decision.outcome.value == "ADMITTED"
            source_ref: VisionImageReferenceV1 | None = None
            content_type = _sniff_content_type(body)
            if admitted:
                if content_type is None or admission_result.source is None:
                    raise _workflow_error(
                        "IMAGE_ADMISSION_INCONSISTENT",
                        500,
                        "Image admission could not be verified.",
                    )
                stored = self._artifacts.put(
                    session_id=session_id,
                    content_type=content_type,
                    body=body,
                )
                if stored.sha256 != admission_result.source.sha256:
                    self._artifacts.delete_session(session_id)
                    raise _workflow_error(
                        "IMAGE_HASH_MISMATCH", 500, "The uploaded image failed its integrity check."
                    )
                source_ref = VisionImageReferenceV1(
                    artifact_ref=stored.artifact_ref,
                    sha256=stored.sha256,
                )

            receipt = ImageAdmissionReceiptV1(
                session_id=session_id,
                decision="ADMITTED" if admitted else "RECAPTURE",
                outcome=admission_result.decision.outcome.value,
                reason=(
                    admission_result.decision.reason.value
                    if admission_result.decision.reason is not None
                    else None
                ),
                source_image_ref=source_ref,
                content_type=content_type if admitted else None,
                byte_length=len(body),
                width=(
                    admission_result.decision.metadata.width
                    if admission_result.decision.metadata is not None
                    else None
                ),
                height=(
                    admission_result.decision.metadata.height
                    if admission_result.decision.metadata is not None
                    else None
                ),
                guidance=_admission_guidance(admission_result.decision.reason),
            )
            evidence_body = json.dumps(
                {
                    "contract_name": "Feat018ImageAdmissionEvidenceV1",
                    "policy_version": _ADMISSION_POLICY_VERSION,
                    "receipt": receipt.model_dump(mode="json"),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            validation_artifact = self._artifacts.put(
                session_id=session_id,
                content_type="application/json",
                body=evidence_body,
            )
            validation = VisionMediaValidationProvenanceV1(
                validation_artifact_ref=validation_artifact.artifact_ref,
                validation_artifact_sha256=validation_artifact.sha256,
                decision="PASS" if admitted else "RECAPTURE",
                validator_policy_version=_ADMISSION_POLICY_VERSION,
            )
            updated = self._sessions.advance(
                session_id=session_id,
                expected_version=expected_session_version,
                allowed_states=("CREATED", "MEDIA_RECAPTURE"),
                next_state="CREATED" if admitted else "MEDIA_RECAPTURE",
                workflow_updates={
                    "source_image_ref": (
                        source_ref.model_dump(mode="json") if source_ref is not None else None
                    ),
                    "media_validation": validation.model_dump(mode="json"),
                    "narration_audio_ref": None,
                    "narration_result": None,
                    "raw_understanding": None,
                    "gate_a_confirmation": None,
                    "p1_context": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "handoff": None,
                    "feedback": None,
                    "journey": _append_journey(
                        prior.values.get("journey"),
                        stage="MEDIA",
                        status="COMPLETED" if admitted else "BLOCKED",
                        artifact_refs=(source_ref.artifact_ref,) if source_ref is not None else (),
                        reason_codes=(
                            (admission_result.decision.reason.value,)
                            if admission_result.decision.reason is not None
                            else ()
                        ),
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED" if admitted else "BLOCKED",
                request_id=request_id,
                session_id=session_id,
                expected_version=expected_session_version,
                observed_version=updated.version,
                payload=receipt.model_dump(mode="json"),
                provenance=_ADMISSION_VERSION,
            )
            self._remember(scope, idempotency_key, fingerprint, result)
            return result, False

    def upload_audio(
        self,
        *,
        session_id: str,
        request_id: str,
        expected_session_version: int,
        idempotency_key: str,
        actor_ref: str,
        filename: str,
        declared_content_type: str | None,
        body: bytes,
    ) -> tuple[MobileWorkflowResultV1, bool]:
        """Store one session-local narration recording after image admission.

        Audio is never sent to Lightning at this boundary. It is retained only in the
        process-local artifact store until the explicit understanding command requests ASR.
        """

        if actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        if not filename or len(filename) > 200:
            raise _workflow_error("AUDIO_FILENAME_INVALID", 422, "Choose a valid audio file.")
        if not body or len(body) > _MAX_AUDIO_BYTES:
            raise _workflow_error(
                "AUDIO_TOO_LARGE", 413, "Narration audio must be between 1 byte and 20 MB."
            )
        content_type = _sniff_audio_content_type(body, declared_content_type)
        if content_type is None:
            raise _workflow_error(
                "AUDIO_FORMAT_UNSUPPORTED",
                422,
                "Use an m4a, wav, webm, or ogg narration recording.",
            )

        fingerprint = sha256(
            b"FEAT018_AUDIO_UPLOAD_V1\0"
            + body
            + b"\0"
            + content_type.encode("ascii")
        ).hexdigest()
        scope = f"{session_id}:UPLOAD_AUDIO"
        with self._lock:
            if replay := self._replay(scope, idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(session_id)
            if snapshot.version != expected_session_version:
                raise _stale_version()
            if snapshot.state != "CREATED":
                raise _workflow_error(
                    "AUDIO_UPLOAD_NOT_ALLOWED",
                    409,
                    "Upload narration after one image has passed admission and before analysis.",
                )
            prior = self._sessions.workflow_record(session_id)
            if not isinstance(prior.values.get("source_image_ref"), dict):
                raise _workflow_error(
                    "IMAGE_REQUIRED_BEFORE_AUDIO",
                    409,
                    "Admit the required image before adding narration.",
                )
            stored = self._artifacts.put(
                session_id=session_id,
                content_type=content_type,
                body=body,
            )
            receipt = NarrationReceiptV1(
                session_id=session_id,
                artifact_ref=stored.artifact_ref,
                sha256=stored.sha256,
                content_type=content_type,
                byte_length=stored.byte_length,
                guidance="Narration đã lưu trong phiên tạm; nút phân tích tiếp theo mới gọi ASR.",
            )
            updated = self._sessions.advance(
                session_id=session_id,
                expected_version=expected_session_version,
                allowed_states=("CREATED",),
                next_state="CREATED",
                workflow_updates={
                    "narration_audio_ref": receipt.model_dump(mode="json"),
                    "narration_result": None,
                    "raw_understanding": None,
                    "gate_a_confirmation": None,
                    "p1_context": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "handoff": None,
                    "feedback": None,
                    "journey": _append_journey(
                        prior.values.get("journey"),
                        stage="NARRATION",
                        status="COMPLETED",
                        artifact_refs=(stored.artifact_ref,),
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED",
                request_id=request_id,
                session_id=session_id,
                expected_version=expected_session_version,
                observed_version=updated.version,
                payload=receipt.model_dump(mode="json"),
                provenance=_NARRATION_VERSION,
            )
            self._remember(scope, idempotency_key, fingerprint, result)
            return result, False

    def issue_renderer_source_capability(
        self,
        *,
        session_id: str,
        expected_session_version: int,
        actor_ref: str,
        experience_spec_id: str,
        experience_spec_version: int,
    ) -> tuple[str, datetime]:
        if actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        snapshot = self._sessions.snapshot(session_id)
        if snapshot.version != expected_session_version:
            raise _stale_version()
        if snapshot.status != "ACTIVE" or snapshot.state not in {
            "EXPERIENCE_READY",
            "HANDOFF_READY",
            "FEEDBACK_RECORDED",
        }:
            raise _workflow_error(
                "RENDERER_NOT_READY", 409, "The adult-approved image experience is not ready."
            )
        workflow = self._sessions.workflow_record(session_id)
        spec_value = workflow.values.get("experience_spec")
        source_value = workflow.values.get("source_image_ref")
        if not isinstance(spec_value, dict) or not isinstance(source_value, dict):
            raise _workflow_error(
                "RENDERER_SOURCE_MISSING", 409, "The approved source image is unavailable."
            )
        try:
            spec = ExperienceSpecV1.model_validate(spec_value)
            source = VisionImageReferenceV1.model_validate(source_value)
        except ValueError as exc:
            raise _workflow_error(
                "RENDERER_SOURCE_INVALID", 409, "The approved image provenance is invalid."
            ) from exc
        if (
            spec.session_id != session_id
            or spec.spec_id != experience_spec_id
            or spec.spec_version != experience_spec_version
            or spec.source_artifact_id != source.artifact_ref
            or spec.source_artifact_sha256 != source.sha256
        ):
            raise _workflow_error(
                "RENDERER_IDENTITY_MISMATCH",
                409,
                "The renderer request must match the exact approved experience and image.",
            )
        stored = self._artifacts.get(source.artifact_ref)
        if (
            stored is None
            or stored[0].session_id != session_id
            or stored[0].sha256 != source.sha256
        ):
            raise _workflow_error(
                "RENDERER_SOURCE_MISSING", 410, "The original source image is no longer available."
            )
        now = self._now()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("renderer capability clock must be timezone-aware")
        expires_at = now + timedelta(seconds=90)
        token = secrets.token_urlsafe(32)
        self._renderer_source_grants.purge_expired(now=now)
        self._renderer_source_grants.put(
            RendererSourceGrant(
                capability_sha256=sha256(token.encode("ascii")).hexdigest(),
                session_id=session_id,
                artifact_ref=source.artifact_ref,
                artifact_sha256=source.sha256,
                expires_at=expires_at,
                remaining_reads=2,
            )
        )
        return token, expires_at

    def read_renderer_source(self, capability: str) -> tuple[str, bytes]:
        if len(capability) < 40 or len(capability) > 200:
            raise _workflow_error(
                "RENDERER_CAPABILITY_INVALID", 404, "The renderer source is unavailable."
            )
        now = self._now()
        grant = self._renderer_source_grants.consume(
            sha256(capability.encode("ascii", errors="ignore")).hexdigest(),
            now=now,
        )
        if grant is None:
            raise _workflow_error(
                "RENDERER_CAPABILITY_INVALID", 404, "The renderer source is unavailable."
            )
        snapshot = self._sessions.snapshot(grant.session_id)
        if snapshot.status != "ACTIVE":
            raise _workflow_error(
                "RENDERER_SOURCE_EXPIRED", 410, "The renderer source is no longer available."
            )
        stored = self._artifacts.get(grant.artifact_ref)
        if (
            stored is None
            or stored[0].session_id != grant.session_id
            or stored[0].sha256 != grant.artifact_sha256
        ):
            raise _workflow_error(
                "RENDERER_SOURCE_MISSING", 410, "The renderer source is no longer available."
            )
        return stored[0].content_type, stored[1]

    def run_understanding(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        if command.actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        operation = command.payload.get("operation")
        is_requery = operation == "REQUERY_UNDERSTANDING"
        allowed_keys = (
            {"operation", "user_initiated", "narration"}
            if not is_requery
            else {
                "operation",
                "user_initiated",
                "prior_run_id",
                "direction_revision",
                "selected_direction",
                "correction",
            }
        )
        if (
            operation not in {"RUN_UNDERSTANDING", "REQUERY_UNDERSTANDING"}
            or command.payload.get("user_initiated") is not True
            or set(command.payload) - allowed_keys
        ):
            raise _workflow_error(
                "EXPLICIT_USER_ACTION_REQUIRED",
                422,
                "Start image understanding from the Run button; automatic analysis is disabled.",
            )
        if is_requery and (
            not isinstance(command.payload.get("selected_direction"), str)
            or not isinstance(command.payload.get("prior_run_id"), str)
            or not str(command.payload.get("prior_run_id")).strip()
        ):
            raise _workflow_error(
                "DIRECTION_REQUERY_INVALID",
                422,
                "Choose a different direction before requesting a new understanding.",
            )
        scope = f"{command.session_id}:{operation}"
        fingerprint = sha256(
            json.dumps(
                command.model_dump(mode="json", exclude={"created_at"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            if self._vision is None:
                raise _workflow_error(
                    "LIGHTNING_VISION_NOT_CONFIGURED",
                    503,
                    "Lightning Vision is not configured on the backend. No image was sent.",
                )
            snapshot = self._sessions.snapshot(command.session_id)
            if snapshot.version != command.expected_session_version:
                raise _stale_version()
            allowed_states = ("GATE_A_PENDING",) if is_requery else ("CREATED",)
            if snapshot.state not in allowed_states:
                raise _workflow_error(
                    "IMAGE_NOT_READY_FOR_UNDERSTANDING",
                    409,
                    "Admit one synthetic image before starting understanding.",
                )
            workflow = self._sessions.workflow_record(command.session_id)
            previous_raw = workflow.values.get("raw_understanding")
            if is_requery:
                stored_progress = workflow.values.get("understanding_progress")
                stored_run_id = (
                    stored_progress.get("run_id")
                    if isinstance(stored_progress, dict)
                    else None
                )
                if stored_run_id != command.payload.get("prior_run_id"):
                    raise _workflow_error(
                        "DIRECTION_REQUERY_STALE",
                        409,
                        "The understanding proposal changed. Review the latest proposal first.",
                    )
            direction = str(command.payload.get("selected_direction", "")).strip()
            correction = str(command.payload.get("correction", "")).strip()
            direction_signature = _direction_signature(direction, correction)
            direction_revision_value = workflow.values.get("direction_revision", 0)
            direction_revision = (
                direction_revision_value if isinstance(direction_revision_value, int) else 0
            )
            if is_requery:
                previous_signature = str(
                    workflow.values.get("understanding_direction_signature", "")
                )
                if direction_signature == previous_signature and isinstance(previous_raw, dict):
                    replay_payload = _stored_understanding_payload(workflow.values)
                    replay_result = _result(
                        status="SUCCEEDED",
                        request_id=command.request_id,
                        session_id=command.session_id,
                        expected_version=command.expected_session_version,
                        observed_version=snapshot.version,
                        payload=replay_payload,
                        provenance=_VISION_VERSION,
                    )
                    self._remember(scope, command.idempotency_key, fingerprint, replay_result)
                    return replay_result, False
                if direction_revision >= 1:
                    raise _workflow_error(
                        "DIRECTION_REQUERY_LIMIT_REACHED",
                        409,
                        "This demo allows one explicit direction re-query per session.",
                    )
                direction_revision += 1
                narration_value = workflow.values.get("narration_input", {"kind": "NONE"})
            else:
                narration_value = command.payload.get("narration", {"kind": "NONE"})
            try:
                narration = _NARRATION_INPUT_ADAPTER.validate_python(narration_value)
            except ValidationError as exc:
                raise _workflow_error(
                    "NARRATION_CONTRACT_INVALID",
                    422,
                    "Narration must be NONE, typed text, or a previously uploaded recording.",
                ) from exc
            source_value = workflow.values.get("source_image_ref")
            validation_value = workflow.values.get("media_validation")
            if not isinstance(source_value, dict) or not isinstance(validation_value, dict):
                raise _workflow_error(
                    "IMAGE_ADMISSION_PROVENANCE_MISSING",
                    409,
                    "Admit a synthetic image before starting understanding.",
                )
            source = VisionImageReferenceV1.model_validate(source_value)
            media_validation = VisionMediaValidationProvenanceV1.model_validate(validation_value)
            if media_validation.decision != "PASS":
                raise _workflow_error(
                    "IMAGE_ADMISSION_NOT_PASSED",
                    409,
                    "This image must be replaced before analysis.",
                )
            correlation_id = command.request_id
            asr_result: AsrResultV1 | None = None
            typed_narration: str | None = None
            narration_context: str | None = None
            if is_requery:
                narration_context = _append_direction_context(
                    None, direction=direction, correction=correction
                )
            narration_payload = _narration_payload(narration)
            if isinstance(narration, NarrationTextV1):
                typed_narration = narration.text.strip()
                narration_context = _append_direction_context(
                    typed_narration,
                    direction=direction if is_requery else None,
                    correction=correction,
                )
                narration_payload = _narration_payload(narration, transcript=typed_narration)
            elif isinstance(narration, NarrationAudioV1):
                stored_audio = workflow.values.get("narration_audio_ref")
                if not isinstance(stored_audio, dict):
                    raise _workflow_error(
                        "NARRATION_AUDIO_NOT_UPLOADED",
                        409,
                        "Record and upload narration before starting analysis.",
                    )
                try:
                    stored_audio_contract = NarrationReceiptV1.model_validate(stored_audio)
                except ValueError as exc:
                    raise _workflow_error(
                        "NARRATION_AUDIO_PROVENANCE_INVALID",
                        409,
                        "The selected narration recording is no longer valid.",
                    ) from exc
                if (
                    stored_audio_contract.artifact_ref != narration.artifact_ref
                    or stored_audio_contract.sha256 != narration.sha256
                    or stored_audio_contract.content_type != narration.content_type
                    or stored_audio_contract.byte_length != narration.byte_length
                ):
                    raise _workflow_error(
                        "NARRATION_AUDIO_MISMATCH",
                        409,
                        "The selected narration does not match the uploaded recording.",
                    )
                if self._asr is None:
                    raise _workflow_error(
                        "LIGHTNING_ASR_NOT_CONFIGURED",
                        503,
                        "Lightning ASR is not configured on the backend. No audio was sent.",
                    )
                asr_request = AsrRequestV1(
                    correlation_id=correlation_id,
                    source_audio_ref=AsrAudioReferenceV1(
                        artifact_ref=narration.artifact_ref,
                        sha256=narration.sha256,
                    ),
                    media_validation=MediaValidationProvenanceV1(
                        validation_artifact_ref=media_validation.validation_artifact_ref,
                        validation_artifact_sha256=media_validation.validation_artifact_sha256,
                        decision="PASS",
                        validator_policy_version=media_validation.validator_policy_version,
                    ),
                    requested_profile_id=self._asr_profile_id,
                )
                # One explicit ASR call; a retry requires a new user command.
                asr_result = self._asr.transcribe(asr_request)
                if isinstance(asr_result, AsrSuccessV1):
                    transcript = asr_result.transcript_raw.strip()
                    narration_context = _append_direction_context(
                        transcript,
                        direction=direction if is_requery else None,
                        correction=correction,
                    )
                    narration_payload = _narration_payload(
                        narration,
                        transcript=transcript,
                        asr_result=asr_result,
                    )
                else:
                    narration_payload = _narration_payload(narration, asr_result=asr_result)
                    updated = self._sessions.advance(
                        session_id=command.session_id,
                        expected_version=command.expected_session_version,
                        allowed_states=allowed_states,
                        next_state="GATE_A_PENDING" if is_requery else "CREATED",
                        workflow_updates={
                            "raw_understanding": previous_raw if is_requery else None,
                            "narration_result": narration_payload,
                            "understanding_progress": _progress_payload(
                                run_id=command.request_id,
                                stage="FAILED",
                                stage_status="BLOCKED",
                                direction_revision=direction_revision,
                                narration=narration_payload,
                                reason_codes=("ASR_FAILED",),
                                gate_a_ready=is_requery and isinstance(previous_raw, dict),
                            ),
                            "journey": _append_journey(
                                workflow.values.get("journey"),
                                stage="ASR",
                                status="BLOCKED",
                                artifact_refs=(source.artifact_ref, narration.artifact_ref),
                            ),
                        },
                    )
                    result = _result(
                        status="BLOCKED",
                        request_id=command.request_id,
                        session_id=command.session_id,
                        expected_version=command.expected_session_version,
                        observed_version=updated.version,
                        payload={"narration": narration_payload},
                        provenance=_NARRATION_VERSION,
                    )
                    self._remember(scope, command.idempotency_key, fingerprint, result)
                    return result, False
            vision_request = VisionUnderstandingRequestV2(
                correlation_id=correlation_id,
                source_image_ref=source,
                media_validation=media_validation,
                requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
            )
            # One provider call only. A retry requires a new explicit command from the user.
            vision_result = self._call_vision(
                vision_request,
                narration_context=narration_context,
            )
            mapping_error: RawUnderstandingMappingError | None = None
            try:
                raw_result = map_vision_result_to_raw(
                    vision_result,
                    session_id=command.session_id,
                    expected_source_sha256=source.sha256,
                    expected_correlation_id=correlation_id,
                    asr_result=asr_result,
                    typed_narration=typed_narration,
                )
            except RawUnderstandingMappingError as exc:
                raw_result = None
                mapping_error = exc
            grounded = isinstance(raw_result, RawUnderstandingSuccessV1) and _has_grounded_claims(
                raw_result
            )
            succeeded = grounded
            reason_codes: tuple[str, ...] = ()
            if mapping_error is not None:
                reason_codes = ("MAPPING_REJECTED",)
            elif isinstance(raw_result, RawUnderstandingSuccessV1) and not grounded:
                reason_codes = ("NO_GROUNDED_CLAIMS",)
            elif not succeeded:
                reason_codes = ("VISION_RESULT_FAILED",)
            topic = (
                _topic_from_raw(raw_result)
                if succeeded and isinstance(raw_result, RawUnderstandingSuccessV1)
                else None
            )
            progress_stage = (
                "TOPIC_READY"
                if succeeded
                else "BLOCKED_NO_GROUNDED_CLAIMS"
                if "NO_GROUNDED_CLAIMS" in reason_codes
                else "FAILED"
            )
            progress = _progress_payload(
                run_id=command.request_id,
                stage=progress_stage,
                stage_status="COMPLETED" if succeeded else "BLOCKED",
                direction_revision=direction_revision,
                narration=narration_payload,
                raw=raw_result,
                topic=topic,
                reason_codes=reason_codes,
                gate_a_ready=succeeded,
                provider_attempt_count=getattr(vision_result, "attempt_number", 0),
                repair_attempted=getattr(vision_result, "repair_attempted", False),
                requery=is_requery,
            )
            next_state = (
                "GATE_A_PENDING"
                if succeeded or (is_requery and isinstance(previous_raw, dict))
                else "CREATED"
            )
            stored_raw = (
                raw_result.model_dump(mode="json")
                if succeeded and raw_result is not None
                else previous_raw
                if is_requery
                else None
            )
            output_payload: dict[str, object]
            if succeeded and isinstance(raw_result, RawUnderstandingSuccessV1):
                topic_directions = [
                    item.as_payload()
                    for item in build_topic_directions(
                        claims_from_raw(raw_result),
                        narration_available=not isinstance(narration, NarrationNoneV1),
                    )
                ]
                output_payload = {
                    **raw_result.model_dump(mode="json"),
                    "narration": narration_payload,
                    "understanding_progress": progress,
                    "topic_directions": topic_directions,
                }
            else:
                previous_directions = workflow.values.get("topic_directions", [])
                output_payload = {
                    "narration": narration_payload,
                    "understanding_progress": progress,
                    "topic_directions": previous_directions if is_requery else [],
                    "reason_codes": list(reason_codes),
                }
                if raw_result is not None:
                    output_payload.update(raw_result.model_dump(mode="json"))
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=command.expected_session_version,
                allowed_states=allowed_states,
                next_state=next_state,
                workflow_updates={
                    "raw_understanding": stored_raw,
                    "narration_result": narration_payload,
                    "narration_input": narration.model_dump(mode="json"),
                    "understanding_direction_signature": direction_signature,
                    "direction_revision": direction_revision,
                    "understanding_progress": progress,
                    "topic_directions": output_payload.get("topic_directions", []),
                    "gate_a_confirmation": None,
                    "p1_context": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "journey": _append_journey(
                        workflow.values.get("journey"),
                        stage="UNDERSTANDING",
                        status="COMPLETED" if succeeded else "BLOCKED",
                        artifact_refs=(source.artifact_ref,),
                        reason_codes=reason_codes,
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED" if succeeded else "BLOCKED",
                request_id=command.request_id,
                session_id=command.session_id,
                expected_version=command.expected_session_version,
                observed_version=updated.version,
                payload=output_payload,
                provenance=_VISION_VERSION,
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def read_understanding_progress(
        self, *, session_id: str, request_id: str, expected_version: int
    ) -> MobileWorkflowResultV1:
        """Read the last sanitized stage projection without invoking any provider."""

        snapshot = self._sessions.snapshot(session_id)
        workflow = self._sessions.workflow_record(session_id)
        progress = workflow.values.get("understanding_progress")
        if not isinstance(progress, dict):
            progress = {
                "stage": "QUEUED",
                "stage_status": "NOT_STARTED",
                "gate_a_ready": False,
                "reason_codes": ["UNDERSTANDING_NOT_STARTED"],
            }
        return _result(
            status="SUCCEEDED",
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_version,
            observed_version=snapshot.version,
            payload={
                "session_state": snapshot.state,
                "understanding_progress": progress,
            },
            provenance=_VISION_VERSION,
        )

    def _call_vision(
        self,
        request: VisionUnderstandingRequestV2,
        *,
        narration_context: str | None,
    ) -> VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2:
        if narration_context:
            narration_aware = getattr(self._vision, "understand_with_narration", None)
            if callable(narration_aware):
                return cast(
                    VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2,
                    narration_aware(request, narration_context=narration_context),
                )
        if self._vision is None:
            raise _workflow_error(
                "LIGHTNING_VISION_NOT_CONFIGURED",
                503,
                "Lightning Vision is not configured on the backend. No image was sent.",
            )
        return self._vision.understand(request)

    def _admit(self, body: bytes) -> Feat018AdmissionResult:
        with tempfile.TemporaryDirectory(prefix="sketch2life-image-") as folder:
            source_path = Path(folder) / "source-image"
            source_path.write_bytes(body)
            return self._admission.admit(
                Feat018AdmissionRequest(path=source_path, artifact_ref="pending")
            )

    def _replay(self, scope: str, key: str, fingerprint: str) -> MobileWorkflowResultV1 | None:
        receipt = self._idempotency.get(scope=scope, key=key)
        if receipt is None:
            return None
        if receipt.request_sha256 != fingerprint:
            raise _workflow_error(
                "IDEMPOTENCY_KEY_CONFLICT", 409, "This retry key was used for a different request."
            )
        return MobileWorkflowResultV1.model_validate_json(receipt.response_body)

    def _remember(
        self,
        scope: str,
        key: str,
        fingerprint: str,
        result: MobileWorkflowResultV1,
    ) -> None:
        self._idempotency.record(
            IdempotencyReceipt(
                scope=scope,
                key=key,
                request_sha256=fingerprint,
                response_body=result.model_dump_json().encode("utf-8"),
            )
        )


def _workflow_error(code: str, status_code: int, message: str) -> SessionWorkflowError:
    return SessionWorkflowError(code=code, status_code=status_code, safe_message=message)


def _stale_version() -> SessionWorkflowError:
    return _workflow_error(
        "STALE_SESSION_VERSION", 409, "The session changed. Refresh it before continuing."
    )


def _direction_signature(direction: str, correction: str) -> str:
    canonical = json.dumps(
        {"direction": direction.strip(), "correction": correction.strip()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _append_direction_context(
    narration: str | None, *, direction: str | None, correction: str | None
) -> str | None:
    parts = [narration.strip()] if narration and narration.strip() else []
    if direction and direction.strip():
        parts.append(
            "Người lớn chọn hướng xem xét khác: "
            + direction.strip()[:200]
            + ". Đây chỉ là gợi ý định hướng, không phải bằng chứng thay cho nét vẽ."
        )
    if correction and correction.strip():
        parts.append(
            "Ghi chú chỉnh sửa của người lớn: "
            + correction.strip()[:200]
            + ". Chỉ dùng để kiểm tra lại với ảnh."
        )
    return "\n".join(parts)[:2_000] or None


def _has_grounded_claims(raw: RawUnderstandingSuccessV1) -> bool:
    return bool(raw.entities or raw.actions or raw.relations or raw.themes)


_TOPIC_LABELS = {
    "butterfly": "con bướm",
    "flower": "bông hoa",
    "flowers": "những bông hoa",
    "grass": "bãi cỏ",
    "tree": "cây xanh",
    "sun": "mặt trời",
    "bird": "con chim",
    "cat": "con mèo",
    "dog": "con chó",
    "flying": "bay",
    "running": "chạy",
    "moving": "chuyển động",
}


def _topic_label(value: str) -> str:
    return _TOPIC_LABELS.get(value.strip().casefold(), value.strip())


def _bounded_topic(text: str) -> tuple[str, int]:
    words = text.split()
    if len(words) < 10:
        words.extend(("cùng", "người", "lớn", "quan", "sát"))
    words = words[:18]
    return " ".join(words), len(words)


def _topic_from_raw(raw: RawUnderstandingSuccessV1) -> dict[str, object]:
    subject = next((item for item in raw.entities if item.confidence >= 0.35), None)
    action = next((item for item in raw.actions if item.confidence >= 0.35), None)
    theme = next((item for item in raw.themes if item.confidence >= 0.35), None)
    subject_label = _topic_label(subject.label.value) if subject is not None else None
    action_label = _topic_label(action.label.value) if action is not None else None
    theme_label = _topic_label(theme.label.value) if theme is not None else None
    if subject_label and action_label and theme_label:
        text = (
            f"Cùng khám phá {subject_label} đang {action_label} trong {theme_label} "
            "qua những nét vẽ nổi bật hôm nay"
        )
    elif subject_label and action_label:
        text = (
            f"Cùng khám phá {subject_label} đang {action_label} qua những nét vẽ nổi bật "
            "trong bức tranh"
        )
    elif subject_label and theme_label:
        text = (
            f"Cùng khám phá {subject_label} trong {theme_label} qua những nét vẽ nổi bật "
            "của bức tranh"
        )
    elif subject_label:
        text = f"Cùng khám phá {subject_label} qua những nét vẽ nổi bật trong bức tranh hôm nay"
    elif action_label:
        text = f"Cùng khám phá hoạt động {action_label} qua những nét vẽ nổi bật trong bức tranh"
    else:
        text = "Cùng khám phá những chi tiết nổi bật qua các nét vẽ trong bức tranh hôm nay"
    bounded, word_count = _bounded_topic(text)
    support_ids = tuple(
        item.observation_id
        for item in (subject, action, theme)
        if item is not None
    )
    return {
        "text": bounded,
        "word_count": word_count,
        "support_state": "GROUNDED",
        "support_claim_ids": list(support_ids),
        "source_kinds": ["VISION"]
        + (["ASR_OR_TEXT"] if raw.asr_claims else [])
        + (["FUSED_PROPOSAL"] if raw.fused_claims else []),
        "requires_adult_choice": bool(raw.conflicts),
    }


def _progress_payload(
    *,
    run_id: str,
    stage: str,
    stage_status: str,
    direction_revision: int,
    narration: dict[str, object],
    raw: object | None = None,
    topic: dict[str, object] | None = None,
    reason_codes: tuple[str, ...] = (),
    gate_a_ready: bool,
    provider_attempt_count: int = 0,
    repair_attempted: bool = False,
    requery: bool = False,
) -> dict[str, object]:
    success_raw = raw if isinstance(raw, RawUnderstandingSuccessV1) else None
    image_ids = (
        [item.observation_id for item in success_raw.entities]
        + [item.observation_id for item in success_raw.actions]
        + [item.observation_id for item in success_raw.relations]
        + [item.observation_id for item in success_raw.themes]
        if success_raw is not None
        else []
    )
    narration_ids = (
        [item.claim_id for item in success_raw.asr_claims] if success_raw is not None else []
    )
    stages: list[dict[str, object]] = [
        {"stage": "QUEUED", "stage_status": "COMPLETED", "sequence": 1},
        {
            "stage": "NARRATION_READY",
            "stage_status": "COMPLETED",
            "sequence": 2,
            "source_status": narration.get("status", "NOT_SUPPLIED"),
        },
    ]
    if image_ids:
        stages.append(
            {
                "stage": "IMAGE_CLAIMS_READY",
                "stage_status": "COMPLETED",
                "sequence": 3,
                "claim_count": len(image_ids),
            }
        )
        stages.append(
            {
                "stage": "FUSION_READY",
                "stage_status": "COMPLETED",
                "sequence": 4,
                "fused_claim_count": len(success_raw.fused_claims) if success_raw else 0,
                "conflict_count": len(success_raw.conflicts) if success_raw else 0,
            }
        )
    if requery:
        stages.insert(0, {"stage": "REQUERY_RUNNING", "stage_status": "COMPLETED", "sequence": 0})
    if stage in {"TOPIC_READY", "BLOCKED_NO_GROUNDED_CLAIMS", "FAILED"}:
        stages.append({"stage": stage, "stage_status": stage_status, "sequence": len(stages) + 1})
    return {
        "run_id": run_id,
        "stage": stage,
        "stage_status": stage_status,
        "sequence": len(stages),
        "direction_revision": direction_revision,
        "source_status": {
            "image": "ADMITTED",
            "narration": narration.get("status", "NOT_SUPPLIED"),
            "image_claim_ids": image_ids,
            "narration_claim_ids": narration_ids,
        },
        "image_claims": {"count": len(image_ids), "claim_ids": image_ids},
        "narration_claims": {"count": len(narration_ids), "claim_ids": narration_ids},
        "fused_claims": (
            [item.model_dump(mode="json") for item in success_raw.fused_claims]
            if success_raw is not None
            else []
        ),
        "conflicts": (
            [item.model_dump(mode="json") for item in success_raw.conflicts]
            if success_raw is not None
            else []
        ),
        "topic": topic,
        "reason_codes": list(reason_codes),
        "repair_attempted": repair_attempted,
        "provider_attempt_count": provider_attempt_count,
        "gate_a_ready": gate_a_ready,
        "terminal_failure": None if gate_a_ready else (reason_codes[0] if reason_codes else None),
        "stages": stages,
    }


def _stored_understanding_payload(values: dict[str, object]) -> dict[str, object]:
    raw = values.get("raw_understanding")
    payload = dict(raw) if isinstance(raw, dict) else {}
    narration = values.get("narration_result")
    if isinstance(narration, dict):
        payload["narration"] = narration
    progress = values.get("understanding_progress")
    if isinstance(progress, dict):
        payload["understanding_progress"] = progress
    directions = values.get("topic_directions")
    if isinstance(directions, list):
        payload["topic_directions"] = directions
    return payload


def _result(
    *,
    status: str,
    request_id: str,
    session_id: str,
    expected_version: int,
    observed_version: int,
    payload: dict[str, object],
    provenance: WorkflowResultProvenanceV1,
) -> MobileWorkflowResultV1:
    return MobileWorkflowResultV1(
        status=status,  # type: ignore[arg-type]
        request_id=request_id,
        session_id=session_id,
        expected_session_version=expected_version,
        observed_session_version=observed_version,
        provenance=provenance,
        payload=payload,
    )


def _append_journey(
    current: object,
    *,
    stage: str,
    status: str,
    artifact_refs: tuple[str, ...] = (),
    reason_codes: tuple[str, ...] = (),
) -> list[object]:
    entries = list(current) if isinstance(current, (list, tuple)) else []
    entries.append(
        {
            "entry_id": f"journey-{uuid4()}",
            "stage": stage,
            "status": status,
            "occurred_at": datetime.now(UTC).isoformat(),
            "artifact_refs": list(artifact_refs),
            "reason_codes": list(reason_codes),
        }
    )
    return entries[-64:]


def _sniff_content_type(body: bytes) -> Literal["image/jpeg", "image/png"] | None:
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if body.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


def _sniff_audio_content_type(
    body: bytes, declared_content_type: str | None
) -> NarrationAudioContentType | None:
    """Accept only recognized audio magic bytes; client MIME is advisory metadata."""

    if body.startswith(b"RIFF") and body[8:12] == b"WAVE":
        return "audio/wav"
    if body.startswith(b"OggS"):
        return "audio/ogg"
    if body.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio/webm"
    if len(body) >= 12 and body[4:8] == b"ftyp":
        return "audio/mp4"
    return None


def _narration_payload(
    narration: NarrationNoneV1 | NarrationTextV1 | NarrationAudioV1,
    *,
    transcript: str | None = None,
    asr_result: AsrResultV1 | None = None,
) -> dict[str, object]:
    if isinstance(narration, NarrationNoneV1):
        return {
            "kind": "NONE",
            "status": "NOT_SUPPLIED",
            "transcript": None,
            "language": None,
            "provenance": "NONE",
        }
    if isinstance(narration, NarrationTextV1):
        return {
            "kind": "TEXT",
            "status": "TEXT_SUPPLIED",
            "transcript": transcript or narration.text,
            "language": narration.language,
            "provenance": narration.provenance,
        }
    payload: dict[str, object] = {
        "kind": "AUDIO",
        "status": (
            "ASR_SUCCEEDED"
            if isinstance(asr_result, AsrSuccessV1)
            else "ASR_FAILED"
            if isinstance(asr_result, AsrFailureV1)
            else "ASR_PENDING"
        ),
        "transcript": transcript,
        "language": (
            asr_result.detected_language
            if isinstance(asr_result, AsrSuccessV1)
            else None
        ),
        "provenance": narration.provenance,
    }
    if asr_result is not None:
        payload["asr"] = asr_result.model_dump(mode="json")
    return payload


def _admission_guidance(reason: object) -> str:
    if reason is None:
        return "Image admitted"
    reason_value = getattr(reason, "value", "")
    from sketch2life.domain.understanding.image_admission import (
        AdmissionReason,
        admission_message,
    )

    try:
        return admission_message(AdmissionReason(reason_value))
    except ValueError:
        return "Choose or export a valid JPEG or PNG image"


__all__ = ["LiveImageDemoService", "VisionV2Port"]
