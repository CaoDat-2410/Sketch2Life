"""Organization scoped artifact ingress and mediated delivery for local development."""

# FastAPI dependency and multipart declarations intentionally use framework defaults.
# ruff: noqa: B008

from __future__ import annotations

import hashlib
import hmac
import io
import tempfile
import warnings
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018ImageAdmission,
)
from sketch2life.domain.understanding.image_admission import AdmissionOutcome
from sketch2life.infrastructure.canvas_render import limits
from sketch2life.infrastructure.canvas_render.renderer import (
    CanvasAdmissionReceiptV1,
    CanvasRenderHandoffV1,
    render_canvas_source,
)
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder
from sketch2life.infrastructure.persistence.be1_models import (
    ConsentRecordModel,
    ManagedProfileModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    VerifiedDeviceContext,
    get_db,
    get_runtime,
    get_verified_adult,
)
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    audit,
    commit,
    deny_pending_consent,
    failure,
    get_session,
    require_assignment,
    session_event,
)

router = APIRouter(prefix="/api/be1/v1", tags=["BE1 artifacts"], responses=BE1_ERROR_RESPONSES)
_MAX_UPLOAD_BYTES = 12 * 1024 * 1024
_MAX_IMAGE_PIXELS = 12_000_000
_ALLOWED_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp"}


def create_canvas_render_handoff(
    db: Session,
    runtime: Be1Runtime,
    device: VerifiedDeviceContext,
) -> CanvasRenderHandoffV1:
    """Apply one total cooperative budget, including source export and render-slot wait."""
    deadline = limits.monotonic() + limits.RENDER_DEADLINE_SECONDS
    try:
        return _create_canvas_render_handoff(db, runtime, device, deadline=deadline)
    except limits.CanvasSourceTooLarge:
        raise failure(
            409, "CANVAS_SOURCE_TOO_LARGE", "Canvas source exceeds pilot capacity"
        ) from None
    except limits.CanvasRenderBusy:
        raise failure(503, "CANVAS_RENDER_BUSY", "Canvas renderer is busy") from None
    except limits.CanvasRenderDeadlineExceeded:
        raise failure(
            503, "CANVAS_RENDER_DEADLINE_EXCEEDED", "Canvas render budget expired"
        ) from None


def _create_canvas_render_handoff(
    db: Session,
    runtime: Be1Runtime,
    device: VerifiedDeviceContext,
    *,
    deadline: float,
) -> CanvasRenderHandoffV1:
    """Render and privately persist the verified device's current authoritative canvas.

    This is an internal BE1 helper for a later approved request path. It is not an HTTP route;
    its caller must already have obtained `VerifiedDeviceContext` through the current BE1 device
    guard. T4 source construction and group eligibility are rechecked in the same scoped session.
    """

    if (
        runtime.settings.env not in {"local", "test"}
        or not runtime.settings.synthetic_pilot_enabled
    ):
        raise failure(503, "CANVAS_RENDER_PILOT_DISABLED", "Canvas rendering is unavailable")
    group_id = device.membership.group_id
    if (
        group_id is None
        or device.turn.canvas_id != group_id
        or device.scope.organization_id != device.grant.organization_id
        or device.scope.session_id != device.session.session_id
    ):
        raise failure(404, "CANVAS_SOURCE_UNAVAILABLE", "Canvas source is unavailable")

    from sketch2life.interfaces.http.routers.be1_canvas import (
        _require_group_eligibility,
        build_canvas_source_export,
    )

    _require_group_eligibility(
        db,
        settings=runtime.settings,
        organization_id=device.grant.organization_id,
        session_id=device.session.session_id,
        group_id=group_id,
        actor=f"device:{device.grant.grant_id}",
        action="canvas.render",
    )
    limits.check_render_deadline(deadline)
    source_export = build_canvas_source_export(
        db,
        organization_id=device.grant.organization_id,
        session_id=device.session.session_id,
        canvas_id=device.turn.canvas_id,
        document_epoch=device.turn.document_epoch,
    )
    limits.check_render_deadline(deadline)
    if source_export.document_revision != device.turn.revision:
        raise failure(409, "STALE_CANVAS_REVISION", "Canvas changed; reload before rendering")

    rendered = render_canvas_source(source_export, deadline=deadline)
    created_refs: list[str] = []
    try:
        render_ref, render_content_sha256 = runtime.artifact_store.put(rendered.png_bytes)
        created_refs.append(render_ref)
        if render_content_sha256 != rendered.derivation.render_sha256:
            raise failure(
                500, "CANVAS_RENDER_INTEGRITY_FAILED", "Canvas render failed integrity checks"
            )
        stored_render_bytes = runtime.artifact_store.get(render_ref)
        if stored_render_bytes is None or not hmac.compare_digest(
            hashlib.sha256(stored_render_bytes).hexdigest(), render_content_sha256
        ):
            raise failure(
                500, "CANVAS_RENDER_INTEGRITY_FAILED", "Canvas render failed integrity checks"
            )

        limits.check_render_deadline(deadline)
        with tempfile.TemporaryDirectory(prefix="sketch2life-canvas-admission-") as scratch:
            image_path = Path(scratch) / "canvas-render.png"
            image_path.write_bytes(stored_render_bytes)
            admission = Feat018ImageAdmission(AvImageDecoder()).admit(
                Feat018AdmissionRequest(path=image_path, artifact_ref=render_ref)
            )

        limits.check_render_deadline(deadline)
        admitted_source = admission.source
        metadata = admission.decision.metadata
        if (
            admission.decision.outcome is not AdmissionOutcome.ADMITTED
            or admitted_source is None
            or metadata is None
            or admitted_source.artifact_ref != render_ref
            or admitted_source.sha256 != render_content_sha256
            or admission.decision.digest != render_content_sha256
        ):
            raise failure(
                422, "CANVAS_IMAGE_NOT_ADMITTED", "Rendered canvas did not pass image admission"
            )

        receipt = CanvasAdmissionReceiptV1.create(
            derivation=rendered.derivation,
            render_artifact_ref=render_ref,
            admitted_content_sha256=admission.decision.digest,
            decoder_container=metadata.container,
            decoder_codec=metadata.codec,
            decoder_pixel_format=metadata.pixel_format or "",
            decoded_width=metadata.width,
            decoded_height=metadata.height,
        )
        receipt_bytes = receipt.to_json_bytes()
        receipt_ref, receipt_content_sha256 = runtime.artifact_store.put(receipt_bytes)
        created_refs.append(receipt_ref)

        source_refs = [
            f"be1-session:{source_export.session_id}",
            f"be1-canvas:{source_export.canvas_id}",
            f"be1-canvas-source:{source_export.source_sha256}",
            *(
                f"be1-child:{child_id}"
                for child_id in sorted(
                    {operation.participant_id for operation in source_export.operations}
                )
            ),
        ]
        db.add(
            CoreAssetMetadataModel(
                asset_ref=render_ref,
                asset_version=1,
                organization_id=source_export.organization_id,
                content_sha256=render_content_sha256,
                media_type="image/png",
                source_refs=source_refs,
                derived_from_ref=source_export.source_ref,
            )
        )
        db.add(
            CoreAssetMetadataModel(
                asset_ref=receipt_ref,
                asset_version=1,
                organization_id=source_export.organization_id,
                content_sha256=receipt_content_sha256,
                media_type="application/vnd.sketch2life.canvas-admission-receipt+json",
                source_refs=source_refs,
                derived_from_ref=render_ref,
            )
        )
        limits.check_render_deadline(deadline)
        commit(db)
    except Exception:
        db.rollback()
        for artifact_ref in created_refs:
            runtime.artifact_store.delete(artifact_ref)
        raise

    limits.check_render_deadline(deadline)
    return CanvasRenderHandoffV1(
        contract="CanvasRenderHandoffV1",
        organization_id=source_export.organization_id,
        session_id=source_export.session_id,
        canvas_id=source_export.canvas_id,
        document_epoch=source_export.document_epoch,
        document_revision=source_export.document_revision,
        source_ref=source_export.source_ref,
        source_sha256=source_export.source_sha256,
        render_artifact_ref=render_ref,
        render_sha256=render_content_sha256,
        render_source_binding_sha256=rendered.derivation.render_source_binding_sha256,
        receipt_artifact_ref=receipt_ref,
        receipt_sha256=receipt_content_sha256,
    )


def _decode_image(content: bytes, declared_type: str) -> None:
    if declared_type not in _ALLOWED_MEDIA_TYPES:
        raise failure(415, "UNSUPPORTED_MEDIA_TYPE", "Only PNG, JPEG, and WebP artwork is accepted")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(content))
            actual_format = image.format
            if image.width * image.height > _MAX_IMAGE_PIXELS:
                raise failure(
                    413, "IMAGE_DIMENSIONS_EXCEEDED", "Image dimensions exceed the supported limit"
                )
            image.verify()
    except HTTPException:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise failure(422, "IMAGE_INVALID", "Image could not be validated") from None
    expected = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}[declared_type]
    if actual_format != expected:
        raise failure(415, "MEDIA_TYPE_MISMATCH", "Declared media type does not match image bytes")


@router.post("/organizations/{organization_id}/sessions/{session_id}/artifacts", status_code=201)
async def upload_session_artifact(
    organization_id: str,
    session_id: str,
    file: UploadFile = File(...),
    contributor_ids: list[str] = Form(default=[]),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if runtime.settings.env not in {"local", "test"}:
        raise failure(
            503,
            "ARTIFACT_PROVIDER_UNCONFIGURED",
            "Production artifact storage has not been selected",
        )
    session = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=session.class_id
    )
    if not contributor_ids or len(contributor_ids) > 40:
        raise failure(
            422, "CONTRIBUTORS_REQUIRED", "One to forty explicit contributors are required"
        )
    for child_id in set(contributor_ids):
        profile = db.scalar(
            select(ManagedProfileModel.child_id).where(
                ManagedProfileModel.organization_id == organization_id,
                ManagedProfileModel.class_id == session.class_id,
                ManagedProfileModel.child_id == child_id,
                ManagedProfileModel.state == "active",
            )
        )
        if profile is None:
            raise failure(404, "PROFILE_NOT_FOUND", "Contributor is not in this class")
        effective = db.scalar(
            select(ConsentRecordModel.consent_id).where(
                ConsentRecordModel.organization_id == organization_id,
                ConsentRecordModel.class_id == session.class_id,
                ConsentRecordModel.child_id == child_id,
                ConsentRecordModel.purpose_ref == str(session.configuration.get("purpose_ref", "")),
                ConsentRecordModel.state == "effective",
            )
        )
        if effective is None:
            deny_pending_consent(
                db,
                organization_id=organization_id,
                actor=principal.subject,
                resource_type="artifact",
                resource_id=session_id,
                action="artifact.upload",
            )
    content = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise failure(413, "UPLOAD_TOO_LARGE", "Image exceeds the 12 MiB upload limit")
    content_type = (file.content_type or "").split(";", maxsplit=1)[0].lower()
    _decode_image(content, content_type)
    artifact_ref, content_hash = runtime.artifact_store.put(content)
    source_refs = [
        f"be1-session:{session_id}",
        *(f"be1-child:{child_id}" for child_id in sorted(set(contributor_ids))),
    ]
    try:
        metadata = CoreAssetMetadataModel(
            asset_ref=artifact_ref,
            asset_version=1,
            organization_id=organization_id,
            content_sha256=content_hash,
            media_type=content_type,
            source_refs=source_refs,
            derived_from_ref=None,
        )
        db.add(metadata)
        audit(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            action="artifact.upload",
            resource_type="artifact",
            resource_id=artifact_ref,
        )
        session_event(
            db,
            session=session,
            event_type="be1.artifact.stored.v1",
            payload={"artifact_ref": artifact_ref, "session_id": session_id},
        )
        commit(db)
    except Exception:
        runtime.artifact_store.delete(artifact_ref)
        raise
    return {
        "contract": "Be1ArtifactV1",
        "artifact_ref": artifact_ref,
        "version": 1,
        "sha256": content_hash,
        "media_type": content_type,
        "byte_length": len(content),
    }


@router.get("/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref:path}")
def download_session_artifact(
    organization_id: str,
    session_id: str,
    asset_ref: str,
    version: int = 1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> Response:
    if runtime.settings.env not in {"local", "test"}:
        raise failure(
            503,
            "ARTIFACT_PROVIDER_UNCONFIGURED",
            "Production artifact storage has not been selected",
        )
    session = get_session(db, organization_id, session_id)
    require_assignment(db, principal, organization_id, class_id=session.class_id)
    row = db.scalar(
        select(CoreAssetMetadataModel).where(
            CoreAssetMetadataModel.organization_id == organization_id,
            CoreAssetMetadataModel.asset_ref == asset_ref,
            CoreAssetMetadataModel.asset_version == version,
        )
    )
    if row is None or f"be1-session:{session_id}" not in row.source_refs:
        raise failure(404, "ARTIFACT_NOT_FOUND", "Artifact is outside the authorized session")
    for source in row.source_refs:
        if not source.startswith("be1-child:"):
            continue
        child_id = source.removeprefix("be1-child:")
        consent = db.scalar(
            select(ConsentRecordModel.consent_id).where(
                ConsentRecordModel.organization_id == organization_id,
                ConsentRecordModel.class_id == session.class_id,
                ConsentRecordModel.child_id == child_id,
                ConsentRecordModel.purpose_ref == str(session.configuration.get("purpose_ref", "")),
                ConsentRecordModel.state == "effective",
            )
        )
        if consent is None:
            deny_pending_consent(
                db,
                organization_id=organization_id,
                actor=principal.subject,
                resource_type="artifact",
                resource_id=asset_ref,
                action="artifact.read",
            )
    content = runtime.artifact_store.get(asset_ref)
    if content is None:
        raise failure(404, "ARTIFACT_BYTES_NOT_FOUND", "Artifact bytes are unavailable")
    digest = hashlib.sha256(content).hexdigest()
    if not hmac.compare_digest(digest, row.content_sha256):
        raise failure(
            410, "ARTIFACT_INTEGRITY_FAILED", "Artifact failed its stored integrity check"
        )
    return Response(
        content=content,
        media_type=row.media_type,
        headers={"ETag": f'"{digest}"', "Cache-Control": "private, no-store"},
    )


__all__ = ["router"]
