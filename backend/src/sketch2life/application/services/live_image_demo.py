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
from typing import Literal, Protocol
from uuid import uuid4

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
from sketch2life.application.services.raw_understanding_mapper import map_vision_result_to_raw
from sketch2life.contracts.schemas.image_demo import ImageAdmissionReceiptV1
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
    WorkflowResultProvenanceV1,
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
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts
        self._idempotency = idempotency
        self._admission = admission
        self._vision = vision
        self._renderer_source_grants = renderer_source_grants
        self._now = now
        self._lock = RLock()

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
        if command.payload != {"operation": "RUN_UNDERSTANDING", "user_initiated": True}:
            raise _workflow_error(
                "EXPLICIT_USER_ACTION_REQUIRED",
                422,
                "Start image understanding from the Run button; automatic analysis is disabled.",
            )
        scope = f"{command.session_id}:RUN_UNDERSTANDING"
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
            if snapshot.state != "CREATED":
                raise _workflow_error(
                    "IMAGE_NOT_READY_FOR_UNDERSTANDING",
                    409,
                    "Admit one synthetic image before starting understanding.",
                )
            workflow = self._sessions.workflow_record(command.session_id)
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
            vision_request = VisionUnderstandingRequestV2(
                correlation_id=correlation_id,
                source_image_ref=source,
                media_validation=media_validation,
                requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
            )
            # One provider call only. A retry requires a new explicit command from the user.
            vision_result = self._vision.understand(vision_request)
            raw_result = map_vision_result_to_raw(
                vision_result,
                session_id=command.session_id,
                expected_source_sha256=source.sha256,
                expected_correlation_id=correlation_id,
            )
            succeeded = isinstance(raw_result, RawUnderstandingSuccessV1)
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=command.expected_session_version,
                allowed_states=("CREATED",),
                next_state="GATE_A_PENDING" if succeeded else "CREATED",
                workflow_updates={
                    "raw_understanding": raw_result.model_dump(mode="json"),
                    "gate_a_confirmation": None,
                    "p1_context": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "journey": _append_journey(
                        workflow.values.get("journey"),
                        stage="UNDERSTANDING",
                        status="COMPLETED" if succeeded else "BLOCKED",
                        artifact_refs=(source.artifact_ref,),
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED" if succeeded else "BLOCKED",
                request_id=command.request_id,
                session_id=command.session_id,
                expected_version=command.expected_session_version,
                observed_version=updated.version,
                payload=raw_result.model_dump(mode="json"),
                provenance=_VISION_VERSION,
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

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
